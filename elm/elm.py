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
if os.name == 'nt':
    import serial
else:
    import pty
import threading
import time
import sys
import traceback
import errno
from random import randint
from .obd_message import ObdMessage, ECU_ADDR_E, ELM_R_OK
from .__version__ import __version__

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
    ELM_DEFAULTS           = r"ATD$"
    ELM_SET_PROTO          = r"ATSPA?[0-9A-C]$"
    ELM_ERASE_PROTO        = r"ATSP00$"

    class THREAD:
        STOPPED = 0
        STARTING = 1
        ACTIVE = 2
        PAUSED = 3

    def Sequence(self, pid, base, max, factor, n_bytes):
        c = self.counters[pid]
        # compute the new value [= factor * ( counter % (max * 2) )]
        p = int (factor * abs( max - ( c + max ) % (max * 2) ) ) + base
        # get its hex string
        s = ("%.X" % p).zfill(n_bytes * 2)
        # space the string into chunks of two bytes
        return (" ".join(s[i:i + 2] for i in range(0, len(s), 2)))

    def reset(self, sleep):
        """ returns all settings to their defaults """
        logging.debug("Resetting counters and sleeping for %s seconds", sleep)
        time.sleep(sleep)
        for i in [k for k in self.counters if k.startswith('cmd_')]:
            del(self.counters[i])
        self.counters['ELM_PIDS_A'] = 0
        self.counters['ELM_MIDS_A'] = 0
        self.counters["cmd_header"] = ECU_ADDR_E

    def set_defaults(self):
        self.scenario = 'default'
        self.delay = 0
        self.max_req_timeout = 1440
        self.answer = {}
        self.counters = {}

    def setSortedOBDMsg(self):
        if 'default' in self.ObdMessage and 'AT' in self.ObdMessage:
            # Perform a union of the three subdictionaries
            self.sortedOBDMsg = {
                **self.ObdMessage['default'], # highest priority
                **self.ObdMessage['AT'],
                **self.ObdMessage[self.scenario] # lowest priority ('Priority' to be checked)
                }
        else:
            self.sortedOBDMsg = { **self.ObdMessage[self.scenario] }
        # Add 'Priority' to all pids and sort basing on priority (highest = 1, lowest=10)
        self.sortedOBDMsg = sorted(
            self.sortedOBDMsg.items(), key = lambda x: x[1]['Priority'] if 'Priority' in x[1] else 10 )

    def __init__(self, batch_mode=False, serial_port=""):
        self.ObdMessage = ObdMessage
        self.set_defaults()
        self.setSortedOBDMsg()
        self.batch_mode = batch_mode
        self.serial_port = serial_port
        self.reset(0)
        self.slave_name = None
        self.thread = None

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
        if self.thread and self.threadState != self.THREAD.STOPPED:
            time.sleep(0.1)
            try:
                self.thread.join(1)
            except:
                logging.debug("Cannot join current thread.")
            self.thread = None
        self.threadState = self.THREAD.STOPPED
        try:
            if self.slave_fd:
                os.close(self.slave_fd)
            if self.master_fd:
                os.close(self.master_fd)
        except:
            logging.debug("Cannot close file descriptors.")
        self.set_defaults()
        logging.debug("Terminated.")
        return True

    def get_pty(self):
        if self.slave_name:
            return self.slave_name
        if os.name == 'nt':
            try:
                self.master_fd = serial.Serial(
                    port=self.serial_port,
                    baudrate=38400)
            except Exception as e:
                logging.critical("Error while opening %s:\n%s",
                              repr(self.serial_port), e)
                return None
            self.slave_fd = None
            self.slave_name = 'com0com serial port pair reading from ' + \
                self.serial_port
        else:
            # make a new pty
            self.master_fd, self.slave_fd = pty.openpty()
            self.slave_name = os.ttyname(self.slave_fd)
        logging.debug("Pty name: %s", self.slave_name)
        return self.slave_name

    def run(self): # daemon thread
        setup_logging()
        self.logger = logging.getLogger()
        self.get_pty()

        if self.batch_mode:
            logging.debug(
                'ELM327 OBD-II adapter emulator v%s started '
                'on pty "%s"_______________', __version__, self.slave_name)
        else:
            logging.info(
                '\n\nELM327 OBD-II adapter emulator v%s started '
                'on pty "%s".\n', __version__, self.slave_name)
        """ the ELM's main IO loop """
        
        self.threadState = self.THREAD.ACTIVE
        while self.threadState != self.THREAD.STOPPED:

            if self.threadState == self.THREAD.PAUSED:
                time.sleep(0.1)
                continue

                # get the latest command
            self.cmd = self.read()
            if self.threadState == self.THREAD.STOPPED:
                return

            # process 'fast' option
            if re.match('^ *$', self.cmd) and "last_cmd" in self.counters:
                self.cmd = self.counters["last_cmd"]
                logging.debug("repeating previous command: %s", repr(self.cmd))
            else:
                self.counters["last_cmd"] = self.cmd
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

    def read(self):
        """
            reads the next newline delimited command from the port
            filters 

            returns a normalized string command
        """
        buffer = ""
        first = True

        req_timeout = self.max_req_timeout
        try:
            req_timeout = float(self.counters['req_timeout'])
        except Exception as e:
            if 'req_timeout' in self.counters:
                logging.error("Improper configuration of\n\"self.counters"\
                              "['req_timeout']\": '%s' (%s). "
                              "Resetting it to %s",
                              self.counters['req_timeout'], e,
                              self.max_req_timeout
                             )
            self.counters['req_timeout'] = req_timeout
        while True:
            prev_time = time.time()
            try:
                if os.name == 'nt':
                    try:
                        c = self.master_fd.read(1).decode()
                    except Exception:
                        logging.debug(
                            "Error while reading from com0com serial port")
                        return('')
                    if 'cmd_echo' in self.counters and self.counters['cmd_echo'] == 1:
                        self.master_fd.write(c.encode())
                else:
                    c = os.read(self.master_fd, 1).decode()
                    if 'cmd_echo' in self.counters and self.counters['cmd_echo'] == 1:
                        try:
                            os.write(self.master_fd, c.encode())
                        except OSError as e:
                            if e.errno == errno.EBADF or e.errno == errno.EIO: # [Errno 9] Bad file descriptor/[Errno 5] Input/output error
                                logging.debug("Read interrupted. Terminating.")
                                self.terminate()
                            else:
                                logging.critical("PANIC - Internal OSError in read(): %s", e,
                                    exc_info=True)                        
                                self.terminate()
            except UnicodeDecodeError as e:
                logging.warning("Invalid character received: %s", e)
                return('')
            except OSError:
                return('')
            if prev_time + req_timeout < time.time() and first == False:
                buffer = ""
                logging.debug("'req_timeout' timeout while reading data: %s", c)
            if c == '\r':
                break
            if c == '\n':
                continue  # ignore newlines
            first = False
            buffer += c

        return buffer

    def write(self, resp):
        """ write a response to the port """

        n = "\r\n" if 'cmd_linefeeds' in self.counters and self.counters[
            'cmd_linefeeds'] == 1 else "\r"
        resp += n + ">"
        nospaces = 1 if 'cmd_spaces' in self.counters and self.counters[
            'cmd_spaces'] == 0 else 0

        j=0
        for i in re.split(r'\0([^\0]+)\0', resp):
            if j % 2:
                msg = i.strip()
                try:
                    evalmsg = eval(msg)
                    if nospaces:
                        evalmsg = re.sub(r'[ \t]+', '', evalmsg)
                    logging.debug("Evaluated command: %s", msg)
                    if evalmsg != None:
                        if os.name == 'nt':
                            self.master_fd.write(evalmsg.encode())
                        else:
                            try:
                                os.write(self.master_fd, evalmsg.encode())
                            except OSError as e:
                                if e.errno == errno.EBADF or e.errno == errno.EIO: # [Errno 9] Bad file descriptor/[Errno 5] Input/output error
                                    logging.debug(
                                        "Read interrupted. Terminating.")
                                    self.terminate()
                                else:
                                    logging.critical(
                                        'PANIC - Internal OSError in write(): '
                                        '%s', e, exc_info=True)                        
                                    self.terminate()
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
                logging.debug("Write: %s", repr(i))
                if nospaces:
                    i = re.sub(r'[ \t]+', '', i)
                if os.name == 'nt':
                    self.master_fd.write(i.encode())
                else:
                    try:
                        os.write(self.master_fd, i.encode())
                    except OSError as e:
                        if e.errno == errno.EBADF or e.errno == errno.EIO: # [Errno 9] Bad file descriptor/[Errno 5] Input/output error
                            logging.debug("Read interrupted. Terminating.")
                            self.terminate()
                        else:
                            logging.critical("PANIC - Internal OSError in write(): %s", e,
                                exc_info=True)                        
                            self.terminate()
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
                        return(self.answer[pid])
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
                    response=val['Response']
                    if isinstance(response, (list, tuple)):
                        response=response[randint(0, len(response)-1)]
                    return (header + response + footer)
                else:
                    logging.error(
                        "Internal error - Missing response for %s, PID %s",
                        cmd, pid)
                    return self.ELM_R_OK
        if "unknown_" + cmd not in self.counters:
            self.counters["unknown_" + cmd] = 0
        self.counters["unknown_" + cmd] += 1
        if cmd == '':
            logging.info("No ELM command")
            return ""
        if "cmd_header" in self.counters:
            logging.info("Unknown ELM command: %s, header=%s",
                repr(cmd), self.counters["cmd_header"])
        else:
            logging.info("Unknown ELM command: %s", repr(cmd))
        return ""

    def sanitize(self, cmd):
        cmd = cmd.replace(" ", "")
        cmd = cmd.upper()
        return cmd
