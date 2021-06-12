#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###########################################################################
# ELM327-emulator
# ELM327 Emulator for testing software interfacing OBDII via ELM327 adapter
# https://github.com/Ircama/ELM327-emulator
# (C) Ircama 2021 - CC-BY-NC-SA-4.0
###########################################################################

import logging
import logging.config
from pathlib import Path
import yaml
import re
import os
import socket
import serial
if not os.name == 'nt':
    import pty
import threading
import time
import sys
import traceback
import errno
from random import randint, choice
from .obd_message import ObdMessage, ECU_ADDR_E, ELM_R_OK, ELM_R_UNKNOWN
from .__version__ import __version__

FORWARD_READ_TIMEOUT = 5.0 # seconds
SERIAL_BAUDRATE = 38400 # bps

def setup_logging(
        default_path=Path(__file__).stem + '.yaml',
        default_level=logging.INFO,
        env_key=os.path.basename(Path(__file__).stem).upper() + '_LOG_CFG'):
    path = default_path
    if not os.path.exists(path):
        path = os.path.join(
            os.path.dirname(Path(__file__)), 'elm.yaml')
    value = os.getenv(env_key, None)
    if value:
        path = value
    if os.path.exists(path):
        with open(path, 'rt') as f:
            config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=default_level)


class Elm:
    ELM_VALID_CHARS = r"[a-zA-Z0-9 \n\r]*"

    # Other AT commands (still to be implemented...)
    ELM_DEFAULTS    = r"ATD$"
    ELM_SET_PROTO   = r"ATSPA?[0-9A-C]$"
    ELM_ERASE_PROTO = r"ATSP00$"

    def SZ(self, size):
        return(size)

    def HD(self, header):
        return(header)

    class THREAD:
        STOPPED = 0
        STARTING = 1
        ACTIVE = 2
        PAUSED = 3
        TERMINATED = 4

    def Sequence(self, pid, base, max, factor, n_bytes):
        c = self.counters[pid]
        # compute the new value [= factor * ( counter % (max * 2) )]
        p = int(factor * abs(max - (c + max) % (max * 2))) + base
        # get its hex string
        s = ("%.X" % p).zfill(n_bytes * 2)
        # space the string into chunks of two bytes
        return (" ".join(s[i:i + 2] for i in range(0, len(s), 2)))

    def reset(self, sleep):
        """ returns all settings to their defaults.
            Called by ATZ and ATD.
        """
        logging.debug("Resetting counters and sleeping for %s seconds", sleep)
        time.sleep(sleep)
        for i in [k for k in self.counters if k.startswith('cmd_')]:
            del (self.counters[i])
        self.counters['ELM_PIDS_A'] = 0
        self.counters['ELM_MIDS_A'] = 0
        self.counters['cmd_header'] = ECU_ADDR_E
        self.counters.update(self.presets)

    def set_defaults(self):
        self.scenario = 'default'
        self.delay = 0
        self.max_req_timeout = 1440
        self.answer = {}
        self.counters = {}
        self.counters.update(self.presets)

    def setSortedOBDMsg(self):
        if 'default' in self.ObdMessage and 'AT' in self.ObdMessage:
            # Perform a union of the three subdictionaries
            self.sortedOBDMsg = {
                **self.ObdMessage['default'],  # highest priority
                **self.ObdMessage['AT'],
                **self.ObdMessage[self.scenario]  # lowest priority ('Priority' to be checked)
            }
        else:
            self.sortedOBDMsg = {**self.ObdMessage[self.scenario]}
        # Add 'Priority' to all pids and sort basing on priority (highest = 1, lowest=10)
        self.sortedOBDMsg = sorted(
            self.sortedOBDMsg.items(), key=lambda x: x[1]['Priority'] if 'Priority' in x[1] else 10)

    def __init__(
            self,
            batch_mode=False,
            newline=False,
            serial_port=None,
            device_port=None,
            serial_baudrate="",
            net_port=None,
            forward_net_host=None,
            forward_net_port=None,
            forward_serial_port=None,
            forward_serial_baudrate = None,
            forward_timeout=None):
        self.presets = {}
        self.ObdMessage = ObdMessage
        self.ELM_R_UNKNOWN = ELM_R_UNKNOWN
        self.set_defaults()
        self.setSortedOBDMsg()
        self.batch_mode = batch_mode
        self.newline = newline
        self.serial_port = serial_port
        self.device_port = device_port
        self.serial_baudrate = serial_baudrate
        self.net_port = net_port
        self.forward_net_host = forward_net_host
        self.forward_net_port = forward_net_port
        self.forward_serial_port = forward_serial_port
        self.forward_serial_baudrate = forward_serial_baudrate
        self.forward_timeout = forward_timeout
        self.reset(0)
        self.slave_name = None # pty port name, if pty is used
        self.master_fd = None # pty port FD, if pty is used, or device com port FD (IO)
        self.slave_fd = None # pty side used by the client application
        self.serial_fd = None # serial COM port file descriptor (pySerial)
        self.sock_inet = None
        self.fw_sock_inet = None
        self.fw_serial_fd = None
        self.sock_conn = None
        self.sock_addr = None
        self.thread = None
        self.aaa = device_port

    def __enter__(self):
        # start the read thread
        self.threadState = self.THREAD.STARTING
        self.thread = threading.Thread(target=self.run)
        self.thread.daemon = True
        self.thread.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.terminate()
        return False  # don't suppress any exceptions

    def terminate(self):
        """ termination procedure """
        logging.debug("Start termination procedure.")
        if (self.thread and
                self.threadState != self.THREAD.STOPPED and
                self.threadState != self.THREAD.TERMINATED):
            time.sleep(0.1)
            try:
                self.thread.join(1)
            except:
                logging.debug("Cannot join current thread.")
            self.thread = None
        self.threadState = self.THREAD.TERMINATED
        try:
            if self.slave_fd:
                os.close(self.slave_fd)
            if self.master_fd: # pty or device
                os.close(self.master_fd)
            if self.serial_fd: # serial COM - pySerial
                self.serial_fd.close()
            if self.sock_inet:
                self.sock_inet.shutdown(socket.SHUT_RDWR)
                self.sock_inet.close()
        except:
            logging.debug("Cannot close file descriptors.")
        self.set_defaults()
        logging.debug("Terminated.")
        return True

    def socket_server(self):
        """
            create an INET, STREAMing socket
            set self.sock_inet
        """
        if self.sock_inet:
            self.sock_inet.shutdown(socket.SHUT_RDWR)
            self.sock_inet.close()
        self.sock_conn = None
        self.sock_addr = None
        errmsg = "Unknown error"
        HOST = "0.0.0.0"
        for res in socket.getaddrinfo(HOST, self.net_port,
                                      socket.AF_UNSPEC,
                                      socket.SOCK_STREAM, 0,
                                      socket.AI_PASSIVE):
            af, socktype, proto, canonname, sa = res
            try:
                self.sock_inet = socket.socket(af, socktype, proto)
                self.sock_inet.setsockopt(
                    socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            except OSError as msg:
                errmsg = msg
                self.sock_inet = None
                continue

            try:
                # Bind the socket to the port
                self.sock_inet.bind(("", self.net_port))
                # Become a socket server and listen for incoming connections
                self.sock_inet.listen(1)
            except OSError as msg:
                errmsg = msg
                self.sock_inet.close()
                self.sock_inet = None
                continue

            break

        if self.sock_inet is None:
            logging.error(
                "Local socket %s creation failed: %s.",
                self.net_port, errmsg)
            return False

        return True

    def connect_serial(self):
        """
        Shall be called after get_pty() and before a read operation.
        It opens the serial port, if not yet opened.
        It is expected to be blocking.
        Returns True if the serial or pty port is opened,
        or None in case of error.
        """

        # if the port is already opened, return True...
        if self.slave_name or self.master_fd or self.serial_fd:
            return True

        # else open the port
        if self.device_port: # os IO
            try:
                self.master_fd = os.open(self.device_port, os.O_RDWR)
            except Exception as e:
                logging.critical("Error while opening device %s:\n%s",
                                 repr(self.device_port), e)
                return None
            return True
        elif self.serial_port: # pySerial COM
            try:
                self.serial_fd = serial.Serial(
                    port=self.serial_port,
                    baudrate=self.serial_baudrate or SERIAL_BAUDRATE)
                self.slave_name = self.get_port_name(extended=True)
            except Exception as e:
                logging.critical("Error while opening serial COM %s:\n%s",
                                 repr(self.serial_port), e)
                return None
            return True
        else:
            return False

    def get_pty(self):
        """
        Return the opened pty port, or None if the pty port
        cannot be opened (non UNIX system).
        In case of UNIX system and if the port is not yet opened, open it.
        It is not blocking.
        """

        # if the port is already opened, return the port name...
        if self.slave_name:
            return self.slave_name
        elif self.master_fd and self.device_port:
            return self.device_port
        elif self.serial_fd and self.serial_port:
            return self.serial_port
        elif self.master_fd:
            logging.critical("Internal error, no configured device port.")
            return None
        elif self.serial_fd:
            logging.critical("Internal error, no configured COM port.")
            return None

        # ...else, with a UNIX system, make a new pty
        self.slave_fd = None

        if os.name == 'nt':
            self.slave_fd = None
            return None
        else:
            if not self.device_port and not self.serial_port:
                self.master_fd, self.slave_fd = pty.openpty()
                self.slave_name = os.ttyname(self.slave_fd)
                logging.debug("Pty name: %s", self.slave_name)

        return self.slave_name

    def run(self):  # daemon thread
        """
        This is the core procedure.

        Can be run directly or by the Context Manager through
        the thread: ref. __enter__()

        No return code.
        """
        setup_logging()
        self.logger = logging.getLogger()
        if self.net_port:
            if not self.socket_server():
                logging.critical("Net connection failed.")
                self.terminate()
                return
        else:
            if (not self.device_port and
                    not self.serial_port and
                    not self.get_pty()):
                if os.name == 'nt':
                    logging.critical("Invalid setting for Windows.")
                else:
                    logging.critical("Pseudo-tty port connection failed.")
                self.terminate()
                return
        self.choice = choice

        if self.sock_inet:
            if self.net_port:
                msg = 'at ' + self.get_port_name()
            else:
                msg = 'with no open TCP/IP port.'
        else:
            msg = 'on ' + self.get_port_name()
        if self.batch_mode:
            logging.debug(
                'ELM327 OBD-II adapter emulator v%s started '
                '%s_______________', __version__, msg)
        else:
            logging.info(
                '\n\nELM327 OBD-II adapter emulator v%s started '
                '%s\n', __version__, msg)
        """ the ELM's main IO loop """

        self.threadState = self.THREAD.ACTIVE
        while (self.threadState != self.THREAD.STOPPED and
               self.threadState != self.THREAD.TERMINATED):
            if self.threadState == self.THREAD.PAUSED:
                time.sleep(0.1)
                continue

            # get the latest command
            self.cmd = self.read()
            if (self.threadState == self.THREAD.STOPPED or
                    self.threadState == self.THREAD.TERMINATED):
                return True
            if self.cmd is None:
                continue

            # process 'fast' option (command repetition)
            if re.match('^ *$', self.cmd) and "cmd_last_cmd" in self.counters:
                self.cmd = self.counters["cmd_last_cmd"]
                logging.debug("repeating previous command: %s", repr(self.cmd))
            else:
                self.counters["cmd_last_cmd"] = self.cmd
                logging.debug("Received %s", repr(self.cmd))

            # if it didn't contain any egregious errors, handle it
            if self.validate(self.cmd):
                try:
                    resp = self.handle(self.cmd)
                except Exception as e:
                    logging.critical("Error while processing %s:\n%s\n%s",
                                     repr(self.cmd), e, traceback.format_exc())
                    continue
                self.write(resp)
            else:
                logging.warning("Invalid request: %s", repr(self.cmd))

    def accept_connection(self):
        if self.sock_conn is None or self.sock_addr is None:

            # Accept network connections
            try:
                logging.debug(
                    "Waiting for connection at %s", self.get_port_name())
                (self.sock_conn, self.sock_addr) = self.sock_inet.accept()
            except OSError as msg:
                if msg.errno == errno.EINVAL: # [Errno 22] invalid argument
                    return False
                logging.error("Failed accepting connection: %s", msg)
                return False
            logging.debug("Connected by %s", self.sock_addr)
        return True

    def serial_client(self):
        if self.fw_serial_fd:
            return
        self.fw_serial_fd = serial.Serial(
            port=self.forward_serial_port,
            baudrate=int(self.forward_serial_baudrate)
                if self.forward_serial_baudrate else SERIAL_BAUDRATE,
            timeout=self.forward_timeout or FORWARD_READ_TIMEOUT)

    def net_client(self):
        if (self.fw_sock_inet
                or self.forward_net_host is None
                or self.forward_net_port is None):
            return
        s = None
        for res in socket.getaddrinfo(
                self.forward_net_host, self.forward_net_port,
                socket.AF_UNSPEC, socket.SOCK_STREAM):
            af, socktype, proto, canonname, sa = res
            try:
                s = socket.socket(af, socktype, proto)
                self.sock_inet.setsockopt(
                    socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            except OSError as msg:
                s = None
                continue
            try:
                s.connect(sa)
                s.settimeout(self.forward_timeout or FORWARD_READ_TIMEOUT)
            except OSError as msg:
                s.close()
                s = None
                continue
            break
        if s is None:
            logging.critical(
                "Cannot connect to host %s with port %s",
                self.forward_net_host, self.forward_net_port)
            self.terminate()
            return False
        self.fw_sock_inet = s
        return True

    def send_receive_forward(self, i):
        """
            if a forwarder is active, send data if i is not None
            and try receiving data until a timeout.
            Then received data are logged and returned.
            return False: no connection
            return None: no data
            return data: decoded string
        """

        if self.forward_serial_port:
            if self.fw_serial_fd is None:
                self.serial_client()
            if self.fw_serial_fd:
                if i:
                    self.fw_serial_fd.write(i)
                    logging.info(
                        "Write forward data: %s", repr(i))
                proxy_data = self.fw_serial_fd.read(1024)
                logging.info(
                    "Read forward data: %s", repr(proxy_data))
                return repr(proxy_data)
            return False

        if not self.forward_net_host or not self.forward_net_port:
            return False
        if self.fw_sock_inet is None:
            self.net_client()
        if self.fw_sock_inet:
            if i:
                try:
                    self.fw_sock_inet.sendall(i)
                    logging.info(
                        "Write forward data: %s", repr(i))
                except BrokenPipeError:
                    logging.error(
                        "The network link of the OBDII interface dropped.")
            try:
                proxy_data = self.fw_sock_inet.recv(1024)
                logging.info(
                    "Read forward data: %s", repr(proxy_data))
                return proxy_data.decode("utf-8", "ignore")
            except socket.timeout:
                logging.info(
                    "No forward data received.")
                return None
        return False

    def get_port_name(self, extended=False):
        if self.sock_inet:
            if self.net_port:
                return 'TCP/IP network port ' + str(self.net_port) + '.'
            else:
                return ('Unopened TCP/IP network port ' +
                        str(self.net_port) + '.')

        if self.device_port:
            if os.name == 'nt':
                return ('(invalid) OS communication device "' +
                        self.device_port + '".')
            else:
                return ('OS communication device "' +
                        self.device_port + '".')

        if self.serial_port:
            postfix = ''
            baudrate = ''
            if extended:
                postfix = ' of com0com COM port pair'
                if self.serial_baudrate:
                    baudrate = " with baud rate " + str(
                        self.serial_baudrate or SERIAL_BAUDRATE)

            if os.name == 'nt':
                if self.serial_port == 'COM3':
                    return ('Windows serial COM port "' + self.serial_port + '"'
                            + postfix + baudrate + '.')
                else:
                    return ('serial COM port "' + self.serial_port + '"'
                            + baudrate + '.')
            else:
                return 'serial communication port "' + self.serial_port + '".'

        if self.slave_name:
            if os.name == 'nt':
                return "(invalid) Windows PTY " + self.slave_name + '.'
            else:
                return ('pseudo-tty port "' +
                        self.slave_name + '".')

        return 'unknown port.'

    def read_from_device(self, bytes):
        """
            read from the port; returns up to bytes characters
            (generally 1)
            and processes echo; returns None in case of error
        """

        # Process inet
        c = None
        if self.sock_inet:
            if not self.accept_connection():
                return None
            try:
                c = self.sock_conn.recv(bytes)
                if len(c) == 0:
                    logging.debug(
                        "TCP/IP communication terminated by the client.")
                    self.sock_conn = None
                    self.sock_addr = None
                    self.reset(0)
                    return None
            except ConnectionResetError:
                logging.error(
                    "Session terminated by the client.")
                self.sock_conn = None
                self.sock_addr = None
                self.reset(0)
                return None
            except UnicodeDecodeError as msg:
                logging.error(
                    "UTF8 decode error: %s", msg)
                return None
            except Exception as msg:
                logging.error(
                    "Error while reading from network: %s", msg)
                return None
            if 'cmd_echo' in self.counters and self.counters['cmd_echo'] == 1:
                self.sock_conn.sendall(c)
            return c

        # Process serial (COM or device)
        try:
            if not self.connect_serial():
                self.terminate()
                return None

            # Serial COM port (uses pySerial)
            if self.serial_fd and self.serial_port:
                try:
                    c = self.serial_fd.read(bytes)
                except Exception:
                    logging.debug(
                        'Error while reading from %s', self.get_port_name())
                    return None
                if ('cmd_echo' in self.counters and
                        self.counters['cmd_echo'] == 1):
                    self.serial_fd.write(c)

            # Device port (use os IO)
            else:
                if not self.master_fd:
                    logging.critical(
                        "PANIC - Internal error, missing device FD")
                    self.terminate()
                    return None
                c = os.read(self.master_fd, bytes)
                if ('cmd_echo' in self.counters and
                        self.counters['cmd_echo'] == 1):
                    try:
                        os.write(self.master_fd, c)
                    except OSError as e:
                        if e.errno == errno.EBADF or e.errno == errno.EIO:  # [Errno 9] Bad file descriptor/[Errno 5] Input/output error
                            logging.debug("Read interrupted. Terminating.")
                            self.terminate()
                            return None
                        else:
                            logging.critical(
                                "PANIC - Internal OSError in read(): %s",
                                e, exc_info=True)
                            self.terminate()
                            return None
        except UnicodeDecodeError as e:
            logging.warning("Invalid character received: %s", e)
            return None
        except OSError:
            return None
        return c

    def read(self):
        """
            reads the next newline delimited command
            returns a normalized string command
        """
        buffer = ""
        first = True

        req_timeout = self.max_req_timeout
        try:
            req_timeout = float(self.counters['req_timeout'])
        except Exception as e:
            if 'req_timeout' in self.counters:
                logging.error("Improper configuration of\n\"self.counters" \
                              "['req_timeout']\": '%s' (%s). "
                              "Resetting it to %s",
                              self.counters['req_timeout'], e,
                              self.max_req_timeout
                              )
            self.counters['req_timeout'] = req_timeout
        while True:
            prev_time = time.time()
            c = self.read_from_device(1)
            if c is None:
                return None
            c = c.decode("utf-8", "ignore")
            if prev_time + req_timeout < time.time() and first == False:
                buffer = ""
                logging.debug("'req_timeout' timeout while reading data: %s", c)
            if c == '\r':
                if self.newline:
                    continue
                break
            if c == '\n':
                if self.newline:
                    break
                continue  # ignore newlines
            first = False
            buffer += c

        self.send_receive_forward((buffer + '\r').encode())
        return buffer

    def write_to_device(self, i):
        """
        write a response to the port (no data returned).
        No return code.
        """

        # Process inet
        if self.sock_inet:
            if not self.accept_connection():
                self.terminate()
                return
            try:
                self.sock_conn.sendall(i)
            except BrokenPipeError:
                logging.error("Connection dropped.")
            return

        # Process serial
        if self.serial_fd:

            # Serial COM port (uses pySerial)
            try:
                self.serial_fd.write(i)
            except Exception:
                logging.debug(
                    'Error while writing to %s', self.get_port_name())
            return

        else:
            # Device port (use os IO)
            if not self.master_fd:
                logging.critical(
                    "PANIC - Internal error, missing device FD")
                self.terminate()
                return
            try:
                os.write(self.master_fd, i)
            except OSError as e:
                if e.errno == errno.EBADF or e.errno == errno.EIO:  # [Errno 9] Bad file descriptor/[Errno 5] Input/output error
                    logging.debug("Read interrupted. Terminating.")
                    self.terminate()
                    return
                else:
                    logging.critical("PANIC - Internal OSError in write(): %s", e,
                                     exc_info=True)
                    self.terminate()
                    return

    def write(self, resp):
        """ process write operation """

        if ("cmd_use_header" in self.counters and
                self.counters["cmd_use_header"]):
            resp = re.sub(r"(?s)<header>(.*?)</header>", r"\1", resp)
            resp = re.sub(r"(?s)<size>(.*?)</size>", r" \1 ", resp)
        else:
            resp = re.sub(r"(?s)<header>(.*?)</header>", r"", resp)
            resp = re.sub(r"(?s)<size>(.*?)</size>", r"", resp)
        resp = re.sub(r"(?s)<data>(.*?)</data>", r"\1 \r", resp)

        n = "\r"
        if 'cmd_linefeeds' in self.counters:
            if self.counters['cmd_linefeeds'] == 1:
                n = "\r\n"
            if self.counters['cmd_linefeeds'] == 2:
                n = "\n"
            if self.counters['cmd_linefeeds'] == 3:
                n = ""
                resp = resp.replace('\r', '\n')
            if self.counters['cmd_linefeeds'] == 4:
                n = ""
        resp += n + ">"
        nospaces = 0
        if ('cmd_spaces' in self.counters
                and self.counters['cmd_spaces'] == 0):
            nospaces = 1

        j = 0
        for i in re.split(r'\0([^\0]+)\0', resp):
            if j % 2:
                msg = i.strip()
                try:
                    evalmsg = eval(msg)
                    if nospaces:
                        evalmsg = re.sub(r'[ \t]+', '', evalmsg)
                    logging.debug("Evaluated command: %s", msg)
                    if evalmsg != None:
                        self.write_to_device(evalmsg.encode())
                        logging.debug("Written evaluated command: %s",
                                      repr(evalmsg))
                except Exception:
                    try:
                        logging.debug("Executing command: %s", msg)
                        if msg:
                            exec(msg, globals())
                    except Exception as e:
                        logging.error("Cannot execute '%s': %s", i, e)
            else:
                if nospaces:
                    i = re.sub(r' +', '', i)
                i = i.replace('^', ' ')
                logging.debug("Write: %s", repr(i))
                self.write_to_device(i.encode())
            j += 1

    def validate(self, cmd):
        if not re.match(self.ELM_VALID_CHARS, cmd):
            return False
        return True

    def handle(self, cmd):
        """ handles all commands """

        cmd = self.sanitize(cmd)

        if 'commands' not in self.counters:
            self.counters['commands'] = 0
        self.counters['commands'] += 1

        logging.debug("Handling: %s", repr(cmd))
        if self.delay > 0:
            time.sleep(self.delay)

        if not self.scenario in self.ObdMessage:
            logging.error("Unknown scenario %s", repr(self.scenario))
            return ""

        for i in self.sortedOBDMsg:
            key = i[0]
            val = i[1]
            if 'Request' in val and re.match(val['Request'], cmd):
                if 'Header' in val and val['Header'] != self.counters["cmd_header"]:
                    continue
                if key:
                    pid = key
                else:
                    pid = 'UNKNOWN'
                if pid not in self.counters:
                    self.counters[pid] = 0
                self.counters[pid] += 1
                if 'Action' in val and val['Action'] == 'skip':
                    logging.info("Received %s. PID %s. Action=%s", cmd, pid,
                                 val['Action'])
                    continue
                if 'Descr' in val:
                    logging.debug("Description: %s, PID %s (%s)",
                                  val['Descr'], pid, cmd)
                else:
                    logging.error(
                        "Internal error - Missing description for %s, PID %s",
                        cmd, pid)
                if pid in self.answer:
                    try:
                        return (self.answer[pid])
                    except Exception as e:
                        logging.error(
                            "Error while processing '%s' for PID %s (%s)",
                            self.answer, pid, e)
                if 'Exec' in val:
                    try:
                        exec(val['Exec'])
                    except Exception as e:
                        logging.error(
                            "Cannot execute '%s' for PID %s (%s)",
                            val['Exec'], pid, e)
                if 'Log' in val:
                    try:
                        exec("logging.debug(" + val['Log'] + ")")
                    except Exception as e:
                        logging.error(
                            "Error while logging '%s' for PID %s (%s)",
                            val['Log'], pid, e)
                if 'Response' in val:
                    header = ''
                    if 'ResponseHeader' in val:
                        header = val['ResponseHeader'](
                            self, cmd, pid, val)
                    footer = ''
                    if 'ResponseFooter' in val:
                        footer = val['ResponseFooter'](
                            self, cmd, pid, val)
                    response = val['Response']
                    if isinstance(response, (list, tuple)):
                        response = response[randint(0, len(response) - 1)]
                    return (header + response + footer)
                else:
                    logging.error(
                        "Internal error - Missing response for %s, PID %s",
                        cmd, pid)
                    return ELM_R_OK
        if "unknown_" + repr(cmd) not in self.counters:
            self.counters["unknown_" + repr(cmd)] = 0
        self.counters["unknown_" + repr(cmd)] += 1
        if cmd == '':
            logging.info("No ELM command")
            return ""
        fw_data = self.send_receive_forward((cmd + '\r').encode())
        if fw_data is not False:
            self.counters["unknown_" + repr(cmd) + "_R"] = repr(fw_data)
        if (fw_data is not False and
                re.match(r"^NO DATA *\r", fw_data or "") is None and
                re.match(r"^\? *\r", fw_data or "") is None and
                self.counters["unknown_" + repr(cmd)] == 1):
            logging.warning(
                'Missing data in dictionary: %s. Answer:\n%s',
                repr(cmd), repr(fw_data))
        if self.is_hex_sp(cmd):
            if "cmd_header" in self.counters:
                logging.info("Unknown request: %s, header=%s",
                             repr(cmd), self.counters["cmd_header"])
            else:
                logging.info("Unknown request: %s", repr(cmd))
            return 'NO^DATA'
        if "cmd_header" in self.counters:
            logging.info("Unknown ELM command: %s, header=%s",
                         repr(cmd), self.counters["cmd_header"])
        else:
            logging.info("Unknown ELM command: %s", repr(cmd))
        return self.ELM_R_UNKNOWN

    def is_hex_sp(self, s):
        return re.match(r"^[0-9a-fA-F \t\r\n]*$", s or "") is not None

    def sanitize(self, cmd):
        cmd = cmd.replace(" ", "")
        cmd = cmd.upper()
        return cmd
