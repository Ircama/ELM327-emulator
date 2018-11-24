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

class THREAD:
    STOPPED = 0
    STARTING = 1
    ACTIVE = 2
    PAUSED = 3

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
        'AT' : {
            r"^ATE[01]$": {
                'Descr': 'AT ECHO',
                'Exec': 'self.echo = (cmd[3] == "1")',
                'Log': '"set ECHO ON/OFF : %s", self.echo',
                'Response': ELM_R_OK
            },
            r"^ATCAF[01]$": {
                'Descr': 'AT CAF',
                'Exec': 'self.caf = (cmd[4] == "1")',
                'Log': '"set CAF ON/OFF : %s", self.caf',
                'Response': ELM_R_OK
            },
            r"^ATH[01]$": {
                'Descr': 'AT HEADERS',
                'Exec': 'self.headers = (cmd[3] == "1")',
                'Log': '"set HEADERS ON/OFF : %s", self.headers',
                'Response': ELM_R_OK
            },
            r"^ATL[01]$": {
                'Descr': 'AT LINEFEEDS',
                'Exec': 'self.linefeeds = (cmd[3] == "1")',
                'Log': '"set LINEFEEDS ON/OFF : %s", self.linefeeds',
                'Response': ELM_R_OK
            },
            r"^ATSH": {
                'Descr': 'AT SET HEADER',
                'Exec': 'self.header = cmd[4:]',
                'Log': '"set HEADER %s", self.header',
                'Response': ELM_R_OK
            },
            r"^ATSP[0-9]$": {
                'Descr': 'AT PROTO',
                'Exec': 'self.proto = cmd[4]',
                'Log': '"set PROTO %s", self.proto',
                'Response': ELM_R_OK
            },
            r"^ATRV$": {
                'Descr': 'AT read volt',
                'Log': '"Volt = 13.8"',
                'Response': b"13.8V\r"
            },
            r"^ATZ$": {
                'Descr': 'AT RESET',
                'Log': '"Sleep 0.5 seconds"',
                'Exec': 'time.sleep(0.5)',
                'Response': b"\r\rELM327 v1.5",
            },
            r"^ATDP$": {
                'Descr': 'set DESCRIBE_PROTO',
                'Exec': 'time.sleep(0.5)',
                'Response': b"ISO 15765-4 (CAN 11/500)\r"
            },
            r"^ATDPN$": {
                'Descr': 'set DESCRIBE_PROTO_N',
                'Exec': 'time.sleep(0.5)',
                'Response': b"A6\r"
            },
        },
        'default' : {
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
                'Pid': 'TempPress',
                'Descr': 'Amb temperature & pressure',
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
                'ResponseHeader': ResponsePidsA
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
    }

    ELM_VALID_CHARS = r"[a-zA-Z0-9 \n\r]*"

    # Other AT commands
    ELM_WARM_START         = r"ATWS$"
    ELM_DEFAULTS           = r"ATD$"
    ELM_VERSION            = r"ATI$"
    ELM_SET_PROTO          = r"ATSPA?[0-9A-C]$"
    ELM_ERASE_PROTO        = r"ATSP00$"
    ELM_TRY_PROTO          = r"ATTPA?[0-9A-C]$"

    def set_defaults(self):
        """ returns all settings to their defaults """
        
        self.scenario = 'default'
        
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
        self.proto = ''

    def __init__(self, protocols, ecus):
        self.set_defaults()

    def __enter__(self):
        # make a new pty
        self.master_fd, self.slave_fd = pty.openpty()
        self.slave_name = os.ttyname(self.slave_fd)

        # start the read thread
        self.threadState = THREAD.STARTING
        self.thread = threading.Thread(target=self.run)
        self.thread.daemon = True
        self.thread.start()

        return self.slave_name

    def __exit__(self, exc_type, exc_value, traceback):
        self.threadState = THREAD.STOPPED
        os.close(self.slave_fd)
        os.close(self.master_fd)
        return False  # don't suppress any exceptions

    def run(self):
        setup_logging()
        logging.info('\n\nELM327 OBD-II adapter simulator started\n')
        """ the ELM's main IO loop """
        prev_cmd = ''
        self.threadState = THREAD.ACTIVE
        while self.threadState != THREAD.STOPPED:

            if self.threadState == THREAD.PAUSED:
                time.sleep(0.1)
                continue

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

        # All other requests (different from AT...) are managed through the dictionary
        s = { **self.ObdMessage['default'], **self.ObdMessage['AT'], **self.ObdMessage[self.scenario] }
        for i in s:
            if re.match(i, cmd):
                if 'Action' in s[i] and s[i]['Action'] == 'skip':
                    continue
                if 'Descr' in s[i]:
                    logging.debug("Received %s (%s)",
                                  s[i]['Descr'], cmd)
                else:
                    logging.error(
                        "Internal error - Missing description for %s", cmd)
                if 'Log' in s[i]:
                    exec("logging.debug(" + s[i]['Log'] + ")")
                if 'Exec' in s[i]:
                    exec(s[i]['Exec'])
                if 'Response' in s[i]:
                    header = b''
                    if 'ResponseHeader' in s[i]:
                        header = s[i]['ResponseHeader'](
                            self, cmd, s[i])
                    footer = b''
                    if 'ResponseFooter' in s[i]:
                        footer = s[i]['ResponseFooter'](
                            self, cmd, s[i])
                    return (
                        header + s[i]['Response'] + footer)
                else:
                    logging.error(
                        "Internal error - Missing response for %s", cmd)
                    return self.ELM_R_OK
        logging.info("Unknown ELM command: %s, dump=%s", cmd, dump)
        return b""

    def sanitize(self, cmd):
        cmd = cmd.replace(" ", "")
        cmd = cmd.upper()
        return cmd
