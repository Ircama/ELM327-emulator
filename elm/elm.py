import logging
import logging.config
from pathlib import Path
import yaml
import re
import os
import pty
import threading
import hexdump
import time


def setup_logging(
        default_path=Path(__file__).stem + '.yaml',
        default_level=logging.INFO,
        env_key=os.path.basename(Path(__file__).stem).upper() + '_LOG_CFG'):
    path = default_path
    value = os.getenv(env_key, None)
    if value:
        path = value
    if os.path.exists(path):
        with open(path, 'rt') as f:
            config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=default_level)


class ELM:

    # List of known ECUs:
    ECU_R_ADDR_H = b"7EA"  # Responses sent by HVECU (Hybrid contol module) 7E2/7EA
    ECU_R_ADDR_E = b"7E8"  # Responses sent by Engine ECU - ECM (engine control module) 7E0/7E8
    ECU_R_ADDR_T = b"7E9"  # Responses sent by Transmission ECU - TCM (transmission control module) 7E1/7E9
    ECU_ADDR_I = b"7C0"  # ICE ECU address
    ECU_R_ADDR_I = b"7C8"  # Responses sent by ICE ECU address
    ECU_R_ADDR_B = b"7EB"  # Responses sent by Traction Battery ECU - 7E3/7EB
    ECU_R_ADDR_P = b"7CC"  # Responses sent by Air Conditioning ECU - 7C4/7CC

    # PID Response functions
    def ResponseRpm(self, cmd, parameters):
        logging.debug("Current RPM value: %s", self.rpm)
        s = ("%.X" % (self.rpm * 4)).zfill(4)
        ret = " ".join(s[i:i + 2] for i in range(0, len(s), 2)) + " \r"
        self.rpm += self.rpmIncrement
        if self.rpm > self.maxRpm:
            self.rpmIncrement = -1
        if self.rpm < self.minRpm:
            self.rpmIncrement = 1
        return (self.ECU_R_ADDR_E + b' 04 41 0C ' + ret.encode() +
                self.ECU_R_ADDR_H + b' 04 41 0C ' + ret.encode())

    def ResponseSpeed(self, cmd, parameters):
        logging.debug("Current SPEED value: %s", self.speed)
        ret = '{:02X} \r'.format(self.speed)
        self.speed += self.speedIncrement
        if self.speed > self.maxSpeed:
            self.speedIncrement = -1
        if self.speed < self.minSpeed:
            self.speedIncrement = 1
        return (self.ECU_R_ADDR_E + b' 03 41 0D ' + ret.encode() +
                self.ECU_R_ADDR_H + b' 03 41 0D ' + ret.encode())

    def ResponsePidsA(self, cmd, parameters):
        if not self.pids_a:
            self.pids_a = True
            logging.debug("first PIDS_A %s", self.pids_a)
            time.sleep(1)
            return (b'SEARCHING...\r')
        return (b'')

    ELM_R_OK = b"OK\r"

    # PID Dictionary
    ObdMessage = {
        r'^0131$': {
            'Pid': 'DISTANCE_SINCE_DTC_CLEAR',
            'Descr': 'Distance traveled since codes cleared',
            'Response': ECU_R_ADDR_E + b' 04 41 31 C8 1F \r'
        },
        r'^0133$': {
            'Pid': 'BAROMETRIC_PRESSURE',
            'Descr': 'Barometric Pressure',
            'Response': ECU_R_ADDR_E + b' 03 41 33 63 \r'
        },
        r'^0146$': {
            'Pid': 'AMBIENT_AIR_TEMP',
            'Descr': 'Ambient air temperature',
            'Response': b''
        },
        r'^2100$': {
            'Pid': 'xxxxxxx',
            'Descr': 'xxxxxxxxxxxx',
            'Response': ECU_R_ADDR_H + b' 06 61 00 84 00 00 01 \r'
        },
        r'^2101[1234]?$': {
            'Pid':
            'TempPress',
            'Descr':
            'Amb temperature & pressure',
            'Response':
            b'7EA 10 18 61 01 00 63 42 32 \r7EA 21 63 38 00 00 00 00 00 \r7EA 22 2D 28 51 FF C8 1D FF \r7EA 23 FF 1C 13 99 00 00 00 \r'
        },
        r'^2129$': {
            'Pid': 'Fuel Input',
            'Descr': 'Fuel level - main tank',
            'Response': ECU_R_ADDR_I + b' 03 61 29 15 \r',
            'Header': ECU_ADDR_I
        },
        r'^212A$': {
            'Pid': 'Fuel',
            'Descr': 'Fuel level - sub tank',
            'Response': ECU_R_ADDR_I + b' 03 7F 21 12 \r',
            'Header': ECU_ADDR_I
        },
        r'^21A7$': {
            'Pid': 'Seat',
            'Descr': 'Seat belt',
            'Response': ECU_R_ADDR_I + b' 03 61 A7 20 \r',
            'Header': ECU_ADDR_I
        },
        r'^2121$': {
            'Pid': 'Room',
            'Descr': 'Room Temp Sensor',
            'Response': ECU_R_ADDR_P + b' 03 61 21 53 \r'
        },
        r'^2122$': {
            'Pid': 'Ambient',
            'Descr': 'Ambient Temp Sensor',
            'Response': ECU_R_ADDR_P + b' 03 61 22 5F \r'
        },
        r'^213D$': {
            'Pid': 'Adjusted',
            'Descr': 'Adjusted Ambient Temp',
            'Response': ECU_R_ADDR_P + b' 03 61 3D 81 \r'
        },
        r'^010C[12]?$': {
            'Pid': 'RPM',
            'Descr': 'Engine RPM',
            'Response': b'',
            'ResponseFooter': ResponseRpm
        },
        r'^010D[12]?$': {
            'Pid': 'SPEED',
            'Descr': 'Speed',
            'Response': b'',
            'ResponseFooter': ResponseSpeed
        },
        r'^0100$': {
            'Pid':
            'ELM_PIDS_A',
            'Descr':
            'PIDS_A',
            'Response':
            ECU_R_ADDR_H + b' 06 41 00 98 3A 80 13 \r' + ECU_R_ADDR_E +
            b' 06 41 00 BE 3F A8 13 \r',
            'ResponseHeader':
            ResponsePidsA
        },
        r'^0120$': {
            'Pid':
            'ELM_PIDS_B',
            'Descr':
            'PIDS_B',
            'Response':
            ECU_R_ADDR_H + b' 06 41 20 80 01 A0 01 \r' + ECU_R_ADDR_E +
            b' 06 41 20 90 15 B0 15 \r'
        },
        r'^0140$': {
            'Pid':
            'ELM_PIDS_C',
            'Descr':
            'PIDS_C',
            'Response':
            ECU_R_ADDR_H + b' 06 41 40 44 CC 00 21 \r' + ECU_R_ADDR_E +
            b' 06 41 40 7A 1C 80 00 \r'
        },
        r'^0600$': {
            'Pid': 'ELM_MIDS_A',
            'Descr': 'MIDS_A',
            'Response': ECU_R_ADDR_E + b' 06 46 00 C0 00 00 01 \r'
        },
        r'^0620$': {
            'Pid': 'ELM_MIDS_B',
            'Descr': 'MIDS_B',
            'Response': ECU_R_ADDR_E + b' 06 46 20 80 00 80 01 \r'
        },
        r'^0640$': {
            'Pid': 'ELM_MIDS_C',
            'Descr': 'MIDS_C',
            'Response': ECU_R_ADDR_E + b' 06 46 40 00 00 00 01 \r'
        },
        r'^0660$': {
            'Pid': 'ELM_MIDS_D',
            'Descr': 'MIDS_D',
            'Response': ECU_R_ADDR_E + b' 06 46 60 00 00 00 01 \r'
        },
        r'^0680$': {
            'Pid': 'ELM_MIDS_E',
            'Descr': 'MIDS_E',
            'Response': ECU_R_ADDR_E + b' 06 46 80 00 00 00 01 \r'
        },
        r'^06A0$': {
            'Pid': 'ELM_MIDS_F',
            'Descr': 'MIDS_F',
            'Response': ECU_R_ADDR_E + b' 06 46 A0 F8 00 00 00 \r'
        },
        r'^0104$': {
            'Pid': 'ENGINE_LOAD',
            'Descr': 'Engine load',
            'Response': ECU_R_ADDR_E + b' 04 41 04 46 \r'
        }  # not valid!
    }

    ELM_VALID_CHARS = r"[a-zA-Z0-9 \n\r]*"

    # AT commands
    ELM_AT                 = r"^AT"  # 'AT' header
    ELM_RESET              = r"ATZ$"
    ELM_WARM_START         = r"ATWS$"
    ELM_DEFAULTS           = r"ATD$"
    ELM_VERSION            = r"ATI$"
    ELM_ECHO               = r"ATE[01]$"
    ELM_HEADERS            = r"ATH[01]$"
    ELM_LINEFEEDS          = r"ATL[01]$"
    ELM_DESCRIBE_PROTO     = r"ATDP$"
    ELM_DESCRIBE_PROTO_N   = r"ATDPN$"
    ELM_SET_PROTO          = r"ATSPA?[0-9A-C]$"
    ELM_ERASE_PROTO        = r"ATSP00$"
    ELM_TRY_PROTO          = r"ATTPA?[0-9A-C]$"
    ELM_PROTO              = r"ATSP[0-9]$"
    ELM_CAF                = r"ATCAF[01]$"
    ELM_SH                 = r"ATSH"
    ELM_RV                 = r"ATRV"

    # AT responses
    ELM_R_RV               = b"13.8V\r"
    ELM_R_RESET            = b"\r\rELM327 v1.5"
    ELM_R_DESCRIBE_PROTO_N = b"A6\r"
    ELM_R_DESCRIBE_PROTO   = b"ISO 15765-4 (CAN 11/500)\r"

    def set_defaults(self):
        """ returns all settings to their defaults """
        self.echo = True
        self.headers = True
        self.linefeeds = True
        self.pids_a = False

        self.speed = 40
        self.maxSpeed = 160
        self.minSpeed = 10
        self.speedIncrement = 1

        self.rpm = 1000
        self.maxRpm = 4000
        self.minRpm = 800
        self.rpmIncrement = 1

        self.caf = 0
        self.header = '7E0'

    def __init__(self, protocols, ecus):
        self.set_defaults()

    def __enter__(self):
        # make a new pty
        self.master_fd, self.slave_fd = pty.openpty()
        self.slave_name = os.ttyname(self.slave_fd)

        # start the read thread
        self.running = True
        self.thread = threading.Thread(target=self.run)
        self.thread.daemon = True
        self.thread.start()

        return self.slave_name

    def __exit__(self, exc_type, exc_value, traceback):
        self.running = False
        os.close(self.slave_fd)
        os.close(self.master_fd)
        return False  # don't suppress any exceptions

    def run(self):
        setup_logging()
        logging.info('\n\nELM327 OBD-II adapter simulator started\n')
        """ the ELM's main IO loop """
        prev_cmd = ''
        while self.running:

            # get the latest command
            self.cmd = self.read()

            # process 'fast' option
            if re.match('^ *$', self.cmd) and prev_cmd:
                self.cmd = prev_cmd
                logging.debug("repeating previous command: %s", repr(self.cmd))
            else:
                prev_cmd = self.cmd
                logging.debug("recv: %s", repr(self.cmd))

            # if it didn't contain any egregious errors, handle it
            if self.validate(self.cmd):
                resp = self.handle(self.cmd)
                self.write(resp)

    def read(self):
        """
            reads the next newline delimited command from the port
            filters 

            returns a normallized string command
        """
        buffer = ""

        while True:
            c = os.read(self.master_fd, 1).decode()

            if c == '\r':
                break

            if c == '\n':
                continue  # ignore newlines

            buffer += c

        return buffer

    def write(self, resp):
        """ write a response to the port """

        n = b"\r\n" if self.linefeeds else b"\r"
        resp += n + b">"

        if self.echo:
            resp = self.cmd.encode() + n + resp

        logging.debug("write: %s", repr(resp))

        return os.write(self.master_fd, resp)

    def validate(self, cmd):

        if not re.match(self.ELM_VALID_CHARS, cmd):
            return False

        # TODO: more tests

        return True

    def handle(self, cmd):
        """ handles all commands """

        cmd = self.sanitize(cmd)

        dump = hexdump.dump(cmd.encode('utf-8'), sep=":")
        logging.debug("handling: %s - %s", repr(cmd), dump)

        if re.match(self.ELM_AT, cmd):
            # AT commands
            if re.match(self.ELM_ECHO, cmd):
                self.echo = (cmd[3] == '1')
                logging.debug("set ECHO ON/OFF : %s", self.echo)
                return self.ELM_R_OK
            elif re.match(self.ELM_CAF, cmd):
                self.caf = (cmd[4] == '1')
                logging.debug("set CAF ON/OFF : %s", self.caf)
                return self.ELM_R_OK
            elif re.match(self.ELM_HEADERS, cmd):
                self.headers = (cmd[3] == '1')
                logging.debug("set HEADERS ON/OFF %s", self.headers)
                return self.ELM_R_OK
            elif re.match(self.ELM_LINEFEEDS, cmd):
                self.linefeeds = (cmd[3] == '1')
                logging.debug("set LINEFEEDS ON/OFF : %s", self.linefeeds)
                return self.ELM_R_OK
            elif re.match(self.ELM_SH, cmd):
                self.header = cmd[4:]
                logging.debug("set HEADER %s", self.header)
                return self.ELM_R_OK
            elif re.match(self.ELM_PROTO, cmd):
                self.proto = cmd[4]
                logging.debug("set PROTO %s", self.proto)
                if self.proto == 6:
                    logging.debug('PROTO set to "ISO 15765-4 CAN 11/500"')
                return self.ELM_R_OK
            elif re.match(self.ELM_RV, cmd):
                logging.debug("read volt")
                return self.ELM_R_RV
            elif re.match(self.ELM_RESET, cmd):
                logging.debug("reset all")
                time.sleep(0.5)
                return self.ELM_R_RESET
            elif re.match(self.ELM_DESCRIBE_PROTO, cmd):
                logging.debug("set ELM_DESCRIBE_PROTO")
                return self.ELM_R_DESCRIBE_PROTO
            elif re.match(self.ELM_DESCRIBE_PROTO_N, cmd):
                logging.debug("set ELM_DESCRIBE_PROTO_N")
                return self.ELM_R_DESCRIBE_PROTO_N
            else:
                logging.info("Unknown AT command: %s, dump=%s", cmd, dump)
        else:
            # All other requests (different from AT...) are managed through the dictionary
            for i in self.ObdMessage:
                logging.debug(i)
                if re.match(i, cmd):
                    if self.ObdMessage[i]['Descr']:
                        logging.debug("Received %s (%s)",
                                      self.ObdMessage[i]['Descr'], cmd)
                    else:
                        logging.error(
                            "Internal error - Missing description for %s", cmd)
                    if 'Response' in self.ObdMessage[i]:
                        header = b''
                        if 'ResponseHeader' in self.ObdMessage[i]:
                            header = self.ObdMessage[i]['ResponseHeader'](
                                self, cmd, self.ObdMessage[i])
                        footer = b''
                        if 'ResponseFooter' in self.ObdMessage[i]:
                            footer = self.ObdMessage[i]['ResponseFooter'](
                                self, cmd, self.ObdMessage[i])
                        return (
                            header + self.ObdMessage[i]['Response'] + footer)
                    else:
                        logging.error(
                            "Internal error - Missing response for %s", cmd)
                        return self.ELM_R_OK
            logging.info("Unknown ELM command: %s, dump=%s", cmd, dump)
        return ""

    def sanitize(self, cmd):
        cmd = cmd.replace(" ", "")
        cmd = cmd.upper()
        return cmd
