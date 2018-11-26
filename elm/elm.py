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
import sys


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
    ECU_R_ADDR_H = "7EA"  # Responses sent by HVECU (Hybrid contol module) 7E2/7EA
    ECU_R_ADDR_E = "7E8"  # Responses sent by Engine ECU - ECM (engine control module) 7E0/7E8
    ECU_R_ADDR_T = "7E9"  # Responses sent by Transmission ECU - TCM (transmission control module) 7E1/7E9
    ECU_ADDR_I = "7C0"  # ICE ECU address
    ECU_R_ADDR_I = "7C8"  # Responses sent by ICE ECU address
    ECU_R_ADDR_B = "7E"  # Responses sent by Traction Battery ECU - 7E3/7EB
    ECU_ADDR_P = "7C4"  # Air Conditioning
    ECU_R_ADDR_P = "7CC"  # Responses sent by Air Conditioning ECU - 7C4/7CC

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
        return (self.ECU_R_ADDR_E + ' 04 41 0C ' + ret +
                self.ECU_R_ADDR_H + ' 04 41 0C ' + ret)

    def ResponseSpeed(self, cmd, parameters):
        logging.debug("Current SPEED value: %s", self.speed)
        ret = '{:02X} \r'.format(self.speed)
        self.speed += self.speedIncrement
        if self.speed > self.maxSpeed:
            self.speedIncrement = -1
        if self.speed < self.minSpeed:
            self.speedIncrement = 1
        return (self.ECU_R_ADDR_E + ' 03 41 0D ' + ret +
                self.ECU_R_ADDR_H + ' 03 41 0D ' + ret)

    def ResponsePidsA(self, cmd, parameters):
        if not self.pids_a:
            self.pids_a = True
            logging.debug("first PIDS_A %s", self.pids_a)
            time.sleep(1)
            return ('SEARCHING...\r')
        return ('')

    def ResponsePidsOff(self, cmd, parameters):
        if not self.pids_a:
            self.pids_a = True
            logging.debug("first PIDS_A %s", self.pids_a)
            time.sleep(1)
            return ('SEARCHING...\rUNABLE TO CONNECT\r')
        return ('NO DATA\r')

    ELM_R_OK = "OK\r"

    # PID Dictionary
    ObdMessage = {
        # AT Commands
        'AT' : {
            r"ATTP[0-9A-C]+$": {
                'Pid': 'AT_TRY_PROTO',
                'Descr': 'AT_TRY_PROTO',
                'Log': '"Try protocol %s", cmd[4:]',
                'Response': ELM_R_OK
            },
            r"^ATE[01]$": {
                'Pid': 'AT_ECHO',
                'Descr': 'AT ECHO',
                'Exec': 'self.echo = (cmd[3] == "1")',
                'Log': '"set ECHO ON/OFF : %s", self.echo',
                'Response': ELM_R_OK
            },
            r"^ATCAF[01]$": {
                'Pid': 'AT_CAF',
                'Descr': 'AT CAF',
                'Exec': 'self.caf = (cmd[4] == "1")',
                'Log': '"set CAF ON/OFF : %s", self.caf',
                'Response': ELM_R_OK
            },
            r"^ATH[01]$": {
                'Pid': 'AT_HEADERS',
                'Descr': 'AT HEADERS',
                'Exec': 'self.headers = (cmd[3] == "1")',
                'Log': '"set HEADERS ON/OFF : %s", self.headers',
                'Response': ELM_R_OK
            },
            r"^ATL[01]$": {
                'Pid': 'AT_LINEFEEDS',
                'Descr': 'AT LINEFEEDS',
                'Exec': 'self.linefeeds = (cmd[3] == "1")',
                'Log': '"set LINEFEEDS ON/OFF : %s", self.linefeeds',
                'Response': ELM_R_OK
            },
            r"^ATSH": {
                'Pid': 'AT_SET_HEADER',
                'Descr': 'AT SET HEADER',
                'Exec': 'self.header = cmd[4:]',
                'Log': '"set HEADER %s", self.header',
                'Response': ELM_R_OK
            },
            r"^ATSP[0-9]$": {
                'Pid': 'AT_PROTO',
                'Descr': 'AT PROTO',
                'Exec': 'self.proto = cmd[4]',
                'Log': '"set PROTO %s", self.proto',
                'Response': ELM_R_OK
            },
            r"^ATRV$": {
                'Pid': 'AT_R_VOLT',
                'Descr': 'AT read volt',
                'Log': '"Volt = 13.8"',
                'Response': "13.8V\r"
            },
            r"^ATZ$": {
                'Pid': 'AT_RESET',
                'Descr': 'AT RESET',
                'Log': '"Sleep 0.5 seconds"',
                'Exec': 'self.reset(0.5)',
                'Response': "\r\rELM327 v1.5\r"
            },
            r"^ATDP$": {
                'Pid': 'AT_DESCRIBE_PROTO',
                'Descr': 'set DESCRIBE_PROTO',
                'Exec': 'time.sleep(0.5)',
                'Response': "ISO 15765-4 (CAN 11/500)\r"
            },
            r"^ATDPN$": {
                'Pid': 'AT_DESCRIBE_PROTO_N',
                'Descr': 'set DESCRIBE_PROTO_N',
                'Exec': 'time.sleep(0.5)',
                'Response': "A6\r"
            },
        },
        # OBD Commands
        'engineoff' : {
            r'^0100$': {
                'Pid': 'ELM_PIDS_A',
                'Descr': 'PIDS_A',
                'Response': '',
                'ResponseHeader': ResponsePidsOff,
                'Priority': 5
            },
            r'^0600$': {
                'Pid': 'ELM_MIDS_A',
                'Descr': 'MIDS_A',
                'Response': '',
                'ResponseHeader': ResponsePidsOff,
                'Priority': 5
            },
            r"^ATDPN$": {
                'Pid': 'AT_DESCRIBE_PROTO_N',
                'Descr': 'set DESCRIBE_PROTO_N',
                'Exec': 'time.sleep(0.5)',
                'Response': "A0\r"
            },
            r"^[0-9][0-9][0-9A-F]+$": {
                'Pid': 'NO_DATA',
                'Descr': 'NO_DATA',
                'Response': 'NO DATA\r',
                'Priority': 6
            },
        },
        'test' : {
            r'^0104[12]?$': {
                'Pid': 'ENGINE_LOAD',
                'Descr': 'Calculated Engine Load',
                'Response': ECU_R_ADDR_E + ' 03 41 04 3F \r'
            },
            r'^0105[12]?$': {
                'Pid': 'COOLANT_TEMP',
                'Descr': 'Engine Coolant Temperature',
                'Response': ECU_R_ADDR_E + ' 03 41 05 4B \r'
            },
            r'^0110[12]?$': {
                'Pid': 'MAF',
                'Descr': 'Air Flow Rate (MAF)',
                'Response': ECU_R_ADDR_E + ' 04 41 10 0B F7 \r'
            },
            r'^011F[12]?$': {
                'Pid': 'RUN_TIME',
                'Descr': 'Engine Run Time',
                'Response': ECU_R_ADDR_E + ' 04 41 1F 00 8D \r'
            },
             r'^0123[12]?$': {
                'Pid': 'FUEL_RAIL_PRESSURE_DIRECT',
                'Descr': 'Fuel Rail Pressure (direct inject)',
                'Response': ECU_R_ADDR_E + ' 04 41 23 10 66 \r'
            },
            r'^012C[12]?$': {
                'Pid': 'COMMANDED_EGR',
                'Descr': 'Commanded EGR',
                'Response': ECU_R_ADDR_E + ' 03 41 2C 00 \r'
            },
            r'^012D[12]?$': {
                'Pid': 'EGR_ERROR',
                'Descr': 'EGR Error',
                'Response': ECU_R_ADDR_E + ' 03 41 2D A9 \r'
            },
            r'^0133[12]?$': {
                'Pid': 'BAROMETRIC_PRESSURE',
                'Descr': 'Barometric Pressure',
                'Response': ECU_R_ADDR_E + ' 03 41 33 63 \r'
            },
            r'^013C[12]?$': {
                'Pid': 'CATALYST_TEMP_B1S1',
                'Descr': 'Catalyst Temperature: Bank 1 - Sensor 1',
                'Response': ECU_R_ADDR_E + ' 04 41 3C 04 4C \r'
            },
            r'^0140$': {
                'Pid': 'PIDS_C',
                'Descr': 'PIDS_C',
                'Response':
                ECU_R_ADDR_T + ' 06 41 40 40 0C 00 00 \r' + ECU_R_ADDR_E +
                ' 06 41 40 44 DC 00 09 \r'
            },
             r'^0142[12]?$': {
                'Pid': 'CONTROL_MODULE_VOLTAGE',
                'Descr': 'Control module voltage',
                'Response': ECU_R_ADDR_T + ' 04 41 42 3A 56 \r00 \r'
            },
            r'^014A[12]?$': {
                'Pid': 'ACCELERATOR_POS_E',
                'Descr': 'Accelerator pedal position E',
                'Response': ECU_R_ADDR_E + ' 03 41 4A 00 \r'
            },
             r'^015D[12]?$': {
                'Pid': 'FUEL_INJECT_TIMING',
                'Descr': 'Fuel injection timing',
                'Response': ECU_R_ADDR_E + ' 04 41 5D 69 00 \r'
            },
        },
        'default' : {
            r'^0104[12]?$': {
                'Pid': 'ENGINE_LOAD',
                'Descr': 'Calculated Engine Load',
                'Response': ECU_R_ADDR_E + ' 03 41 04 00 \r'
            },
            r'^0105[12]?$': {
                'Pid': 'COOLANT_TEMP',
                'Descr': 'Engine Coolant Temperature',
                'Response': ECU_R_ADDR_E + ' 05 41 05 7B \r'
            },
            r'^010B[12]?$': {
                'Pid': 'INTAKE_PRESSURE',
                'Descr': 'Intake Manifold Pressure',
                'Response': ECU_R_ADDR_E + ' 03 41 0B 73 \r'
            },
            r'^010C[12]?$': {
                'Pid': 'RPM',
                'Descr': 'Engine RPM',
                'Response': '',
                'ResponseFooter': ResponseRpm
            },
            r'^010D[12]?$': {
                'Pid': 'SPEED',
                'Descr': 'Vehicle Speed',
                'Response': '',
                'ResponseFooter': ResponseSpeed
            },
            r'^010F[12]?$': {
                'Pid': 'INTAKE_TEMP',
                'Descr': 'Intake Air Temp',
                'Response': ECU_R_ADDR_E + ' 03 41 0F 44 \r'
            },
            r'^0110[12]?$': {
                'Pid': 'MAF',
                'Descr': 'Air Flow Rate (MAF)',
                'Response': ECU_R_ADDR_E + ' 04 41 10 05 1F \r'
            },
            r'^0111[12]?$': {
                'Pid': 'THROTTLE_POS',
                'Descr': 'Throttle Position',
                'Response': ECU_R_ADDR_E + ' 03 41 11 FF \r'
            },
            r'^011F[12]?$': {
                'Pid': 'RUN_TIME',
                'Descr': 'Engine Run Time',
                'Response': ECU_R_ADDR_E + ' 04 41 1F 00 8C \r'
            },
             r'^0121[12]?$': {
                'Pid': 'DISTANCE_W_MIL',
                'Descr': 'Distance Traveled with MIL on',
                'Response': ECU_R_ADDR_E + ' 04 41 21 00 00 \r00 \r'
            },
             r'^0123[12]?$': {
                'Pid': 'FUEL_RAIL_PRESSURE_DIRECT',
                'Descr': 'Fuel Rail Pressure (direct inject)',
                'Response': ECU_R_ADDR_E + ' 04 41 23 1A 0E \r'
            },
            r'^012C[12]?$': {
                'Pid': 'COMMANDED_EGR',
                'Descr': 'Commanded EGR',
                'Response': ECU_R_ADDR_E + ' 03 41 2C 0D \r'
            },
            r'^012D[12]?$': {
                'Pid': 'EGR_ERROR',
                'Descr': 'EGR Error',
                'Response': ECU_R_ADDR_E + ' 03 41 2D 80 \r'
            },
            r'^0133[12]?$': {
                'Pid': 'BAROMETRIC_PRESSURE',
                'Descr': 'Barometric Pressure',
                'Response': ECU_R_ADDR_E + ' 03 41 33 65 \r'
            },
            r'^0131[12]?$': {
                'Pid': 'DISTANCE_SINCE_DTC_CLEAR',
                'Descr': 'Distance traveled since codes cleared',
                'Response': ECU_R_ADDR_E + ' 04 41 31 C8 1F \r'
            },
            r'^013C[12]?$': {
                'Pid': 'CATALYST_TEMP_B1S1',
                'Descr': 'Catalyst Temperature: Bank 1 - Sensor 1',
                'Response': ECU_R_ADDR_E + ' 04 41 3C 04 44 \r'
            },
             r'^0142[12]?$': {
                'Pid': 'CONTROL_MODULE_VOLTAGE',
                'Descr': 'Control module voltage',
                'Response': ECU_R_ADDR_T + ' 04 41 42 39 D6 \r00 \r'
            },
            r'^0146[12]?$': {
                'Pid': 'AMBIANT_AIR_TEMP',
                'Descr': 'Ambient air temperature',
                'Response': ECU_R_ADDR_E + ' 03 41 46 43 \r'
            },
            r'^0149[12]?$': {
                'Pid': 'ACCELERATOR_POS_D',
                'Descr': 'Accelerator pedal position D',
                'Response': ECU_R_ADDR_E + ' 03 41 49 00 \r'
            },
            r'^014A[12]?$': {
                'Pid': 'ACCELERATOR_POS_E',
                'Descr': 'Accelerator pedal position E',
                'Response': ECU_R_ADDR_E + ' 03 41 4A 45 \r'
            },
            r'^014C[12]?$': {
                'Pid': 'THROTTLE_ACTUATOR',
                'Descr': 'Commanded throttle actuator',
                'Response': ECU_R_ADDR_T + ' 03 41 4C 00 \r'
            },
            r'^014D[12]?$': {
                'Pid': 'RUN_TIME_MIL',
                'Descr': 'Time run with MIL on',
                'Response': ECU_R_ADDR_T + ' 04 41 4D 00 00 \r00 \r'
            },
            r'^014E[12]?$': {
                'Pid': 'TIME_SINCE_DTC_CLEARED',
                'Descr': 'Time since trouble codes cleared',
                'Response': ECU_R_ADDR_T + ' 04 41 4E 4C 69 \r00 \r'
            },
             r'^015D[12]?$': {
                'Pid': 'FUEL_INJECT_TIMING',
                'Descr': 'Fuel injection timing',
                'Response': ECU_R_ADDR_E + ' 04 41 5D 66 00 \r'
            },
           # Custom
            r'^2101[1234]?$': {
                'Pid': 'CUSTOM_T_P',
                'Descr': 'Ambient temperature & pressure',
                'Response':
                '7EA 10 18 61 01 00 63 42 32 \r7EA 21 63 38 00 00 00 00 00 \r7EA 22 2D 28 51 FF C8 1D FF \r7EA 23 FF 1C 13 99 00 00 00 \r'
            },
            r'^2113[12]?$': {
                'Pid': 'CUSTOM_AUX_B_VOLT',
                'Descr': '+B Voltage Value',
                'Response': ECU_R_ADDR_I + ' 03 61 13 95 \r',
                'Header': ECU_ADDR_I
            },
            r'^2129[12]?$': {
                'Pid': 'CUSTOM_FUEL_MAIN',
                'Descr': 'Fuel level - main tank',
                'Response': ECU_R_ADDR_I + ' 03 61 29 15 \r',
                'Header': ECU_ADDR_I
            },
            r'^212A[12]?$': {
                'Pid': 'CUSTOM_FUEL_SUB',
                'Descr': 'Fuel level - sub tank',
                'Response': ECU_R_ADDR_I + ' 03 7F 21 12 \r',
                'Header': ECU_ADDR_I
            },
            r'^21A7[12]?$': {
                'Pid': 'CUSTOM_SEAT',
                'Descr': 'Seat belt',
                'Response': ECU_R_ADDR_I + ' 03 61 A7 20 \r',
                'Header': ECU_ADDR_I
            },
            r'^2121[12]?$': {
                'Pid': 'CUSTOM_ROOM',
                'Descr': 'Room Temp Sensor',
                'Response': ECU_R_ADDR_P + ' 03 61 21 53 \r',
                'Header': ECU_ADDR_P
            },
            r'^2122[12]?$': {
                'Pid': 'CUSTOM_AMBIENT',
                'Descr': 'Ambient Temp Sensor',
                'Response': ECU_R_ADDR_P + ' 03 61 22 5F \r',
                'Header': ECU_ADDR_P
            },
            r'^2124[12]?$': {
                'Pid': 'CUSTOM_SOLAR',
                'Descr': 'Solar sensor',
                'Response': ECU_R_ADDR_P + ' 03 61 24 01 \r',
                'Header': ECU_ADDR_P
            },
            r'^213D[12]?$': {
                'Pid': 'CUSTOM_ADJUSTED',
                'Descr': 'Adjusted Ambient Temp',
                'Response': ECU_R_ADDR_P + ' 03 61 3D 81 \r',
                'Header': ECU_ADDR_P
            },
            r'^2168[12]?$': {
                'Pid': 'CUSTOM_RHEOSTAT',
                'Descr': 'Rheostat value (dark=0,bright=255)',
                'Response': ECU_R_ADDR_I + ' 03 7F 21 12 \r',
                'Header': ECU_ADDR_I
            },
            # Supported PIDs for protocols
            r'^0100$': {
                'Pid': 'ELM_PIDS_A',
                'Descr': 'PIDS_A',
                'Response':
                ECU_R_ADDR_H + ' 06 41 00 98 3A 80 13 \r' + ECU_R_ADDR_E +
                ' 06 41 00 BE 3F A8 13 \r',
                'ResponseHeader': ResponsePidsA
            },
            r'^0120$': {
                'Pid': 'ELM_PIDS_',
                'Descr': 'PIDS_',
                'Response':
                ECU_R_ADDR_H + ' 06 41 20 80 01 A0 01 \r' + ECU_R_ADDR_E +
                ' 06 41 20 90 15 B0 15 \r'
            },
            r'^0140$': {
                'Pid': 'ELM_PIDS_C',
                'Descr': 'PIDS_C',
                'Response':
                ECU_R_ADDR_H + ' 06 41 40 44 CC 00 21 \r' + ECU_R_ADDR_E +
                ' 06 41 40 7A 1C 80 00 \r'
            },
            r'^0600$': {
                'Pid': 'ELM_MIDS_A',
                'Descr': 'MIDS_A',
                'Response': ECU_R_ADDR_E + ' 06 46 00 C0 00 00 01 \r'
            },
            r'^0620$': {
                'Pid': 'ELM_MIDS_',
                'Descr': 'MIDS_',
                'Response': ECU_R_ADDR_E + ' 06 46 20 80 00 80 01 \r'
            },
            r'^0640$': {
                'Pid': 'ELM_MIDS_C',
                'Descr': 'MIDS_C',
                'Response': ECU_R_ADDR_E + ' 06 46 40 00 00 00 01 \r'
            },
            r'^0660$': {
                'Pid': 'ELM_MIDS_D',
                'Descr': 'MIDS_D',
                'Response': ECU_R_ADDR_E + ' 06 46 60 00 00 00 01 \r'
            },
            r'^0680$': {
                'Pid': 'ELM_MIDS_E',
                'Descr': 'MIDS_E',
                'Response': ECU_R_ADDR_E + ' 06 46 80 00 00 00 01 \r'
            },
            r'^06A0$': {
                'Pid': 'ELM_MIDS_F',
                'Descr': 'MIDS_F',
                'Response': ECU_R_ADDR_E + ' 06 46 A0 F8 00 00 00 \r'
            }
        }
    }

    ELM_VALID_CHARS = r"[a-zA-Z0-9 \n\r]*"

    # Other AT commands
    ELM_WARM_START         = r"ATWS$"
    ELM_DEFAULTS           = r"ATD$"
    ELM_VERSION            = r"ATI$"
    ELM_SET_PROTO          = r"ATSPA?[0-9A-C]$"
    ELM_ERASE_PROTO        = r"ATSP00$"

    def reset(self, sleep):
        """ returns all settings to their defaults """
        self.echo = True
        self.headers = True
        self.linefeeds = True
        self.pids_a = False

        self.caf = 0
        self.header = '7E0'
        self.proto = ''

        time.sleep(sleep)
        
    def set_defaults(self):
        self.scenario = 'default'
        self.answer = {}
        self.commandCounter = 0

        self.speed = 40
        self.maxSpeed = 160
        self.minSpeed = 10
        self.speedIncrement = 1

        self.rpm = 1000
        self.maxRpm = 4000
        self.minRpm = 800
        self.rpmIncrement = 1

    def __init__(self, protocols, ecus):
        self.reset(0)
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

        #n = "\r\n" if self.linefeeds else "\r"
        n = "\r"
        resp += n + ">"

        if self.echo:
            resp = self.cmd + n + resp

        logging.debug("write: %s", repr(resp))

        return os.write(self.master_fd, resp.encode())

    def validate(self, cmd):

        if not re.match(self.ELM_VALID_CHARS, cmd):
            return False

        # TODO: more tests

        return True

    def handle(self, cmd):
        """ handles all commands """

        cmd = self.sanitize(cmd)

        self.commandCounter += 1
        if self.commandCounter == sys.maxsize:
            logging.error("Rolling commandCounter")
            self.commandCounter = 0

        dump = hexdump.dump(cmd.encode('utf-8'), sep=":")
        logging.debug("handling: %s - %s", repr(cmd), dump)

        # Perform a union of the three subdictionaries
        s = { **self.ObdMessage['default'], **self.ObdMessage['AT'], **self.ObdMessage[self.scenario] }
        # Add 'Priority' to all pids and sort basing on priority (highest = 1, lowest=10)
        for i in sorted(s.items(), key=lambda x: x[1]['Priority'] if 'Priority' in x[1] else 10 ):
            if re.match(i[0], cmd):
                val=i[1]
                if 'Action' in val and val['Action'] == 'skip':
                    continue
                if 'Descr' in val:
                    logging.debug("Received %s (%s)",
                                  val['Descr'], cmd)
                else:
                    logging.error(
                        "Internal error - Missing description for %s", cmd)
                if 'Log' in val:
                    try:
                        exec("logging.debug(" + val['Log'] + ")")
                    except Exception as e:
                        logging.error(
                        "Error while logging '%s' (%s)", val['Log'], e)
                if 'Pid' in val and val['Pid'] in self.answer:
                    return(self.answer[val['Pid']])
                if 'Exec' in val:
                    try:
                        exec(val['Exec'])
                    except Exception as e:
                        logging.error(
                        "Cannot execute '%s' (%s)", val['Exec'], e)
                if 'Response' in val:
                    header = ''
                    if 'ResponseHeader' in val:
                        header = val['ResponseHeader'](
                            self, cmd, val)
                    footer = ''
                    if 'ResponseFooter' in val:
                        footer = val['ResponseFooter'](
                            self, cmd, val)
                    return (
                        header + val['Response'] + footer)
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
