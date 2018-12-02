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
    ECU_ADDR_H = "7E2"  # HVECU address (Hybrid contol module)
    ECU_R_ADDR_H = "7EA"  # Responses sent by HVECU (Hybrid contol module) 7E2/7EA
    ECU_ADDR_E = "7E0"  # Engine ECU address
    ECU_R_ADDR_E = "7E8"  # Responses sent by Engine ECU - ECM (engine control module) 7E0/7E8
    ECU_ADDR_T = "7E1"  # Transmission ECU address (transmission control module)
    ECU_R_ADDR_T = "7E9"  # Responses sent by Transmission ECU - TCM (transmission control module) 7E1/7E9
    ECU_ADDR_I = "7C0"  # ICE ECU address
    ECU_R_ADDR_I = "7C8"  # Responses sent by ICE ECU address 7C0/7C8
    ECU_ADDR_B = "7E3"  # Traction Battery ECU address
    ECU_R_ADDR_B = "7EB"  # Responses sent by Traction Battery ECU - 7E3/7EB
    ECU_ADDR_P = "7C4"  # Air Conditioning
    ECU_R_ADDR_P = "7CC"  # Responses sent by Air Conditioning ECU - 7C4/7CC

    def Sequence(self, pid, base, max, factor, n_bytes):
        c = self.counters[pid]
        # compute the new value [= factor * ( counter % (max * 2) )]
        p = int (factor * abs( max - ( c + max ) % (max * 2) ) ) + base
        # get its hex string
        s = ("%.X" % p).zfill(n_bytes * 2)
        # space the string into chunks of two bytes
        return (" ".join(s[i:i + 2] for i in range(0, len(s), 2)))

    ELM_R_OK = "OK\r"
    ELM_MAX_RESP = '[01234]?$'

    # PID Dictionary
    ObdMessage = {
        # AT Commands
        'AT' : {
           'AT_DESCR': {
                'Request': '^AT@1' + ELM_MAX_RESP,
                'Descr': 'Device description',
                'Response': "OBDII to RS232 Interpreter\r"
            },
           'AT_ID': {
                'Request': '^AT@2' + ELM_MAX_RESP,
                'Descr': 'Device identifier',
                'Response': "?\r"
            },
            'AT_CAF': {
                'Request': '^ATCAF[01]$',
                'Descr': 'AT CAF',
                'Exec': 'self.counters["cmd_caf"] = (cmd[4] == "1")',
                'Log': '"set CAF ON/OFF : %s", self.counters["cmd_caf"]',
                'Response': ELM_R_OK
            },
             'AT_DESCRIBE_PROTO': {
                'Request': '^ATDP$',
                'Descr': 'set DESCRIBE_PROTO',
                'Exec': 'time.sleep(0.5)',
                'Response': "ISO 15765-4 (CAN 11/500)\r"
            },
            'AT_DESCRIBE_PROTO_N': {
                'Request': '^ATDPN$',
                'Descr': 'set DESCRIBE_PROTO_N',
                'Exec': 'time.sleep(0.5)',
                'Response': "A6\r"
            },
            'AT_ECHO': {
                'Request': '^ATE[01]$',
                'Descr': 'AT ECHO',
                'Exec': 'self.counters["cmd_echo"] = (cmd[3] == "1")',
                'Log': '"set ECHO ON/OFF : %s", self.counters["cmd_echo"]',
                'Response': ELM_R_OK
            },
            'AT_HEADERS': {
                'Request': '^ATH[01]$',
                'Descr': 'AT HEADERS',
                'Exec': 'self.counters["cmd_headers"] = (cmd[3] == "1")',
                'Log': '"set HEADERS ON/OFF : %s", self.counters["cmd_headers"]',
                'Response': ELM_R_OK
            },
            'AT_I': {
                'Request': '^ATI$',
                'Descr': 'ELM327 version string',
                'Response': "ELM327 v1.5\r"
            },
            'AT_IGN': {
                'Request': '^ATIGN' + ELM_MAX_RESP,
                'Descr': 'IgnMon input level',
                'Response': "ON\r"
            },
            'AT_LINEFEEDS': {
                'Request': '^ATL[01]$',
                'Descr': 'AT LINEFEEDS',
                'Exec': 'self.counters["cmd_linefeeds"] = (cmd[3] == "1")',
                'Log': '"set LINEFEEDS ON/OFF : %s", self.counters["cmd_linefeeds"]',
                'Response': ELM_R_OK
            },
            'AT_R_VOLT': {
                'Request': '^ATRV$',
                'Descr': 'AT read volt',
                'Log':
                '"Volt = {:.1f}".format(0.1 * abs(9 - (self.counters[pid] + 9) % 18) + 13)',
                'ResponseHeader': \
                lambda self, cmd, pid, val: \
                    "{:.1f}".format(0.1 * abs(9 - (self.counters[pid] + 9) % 18) + 13),
                'Response': "V\r"
            },
            'AT_SPACES': {
                'Request': '^ATS[01]$',
                'Descr': 'Spaces off or on',
                'Exec': 'self.counters["cmd_spaces"] = (cmd[3] == "1")',
                'Response': ELM_R_OK
            },
            'AT_SET_HEADER': {
                'Request': '^ATSH',
                'Descr': 'AT SET HEADER',
                'Exec': 'self.counters["cmd_header"] = cmd[4:]',
                'Log': '"set HEADER %s", self.counters["cmd_header"]',
                'Response': ELM_R_OK
            },
            'AT_PROTO': {
                'Request': '^ATSP[0-9A-C]$',
                'Descr': 'AT PROTO',
                'Exec': 'self.counters["cmd_proto"] = cmd[4]',
                'Log': '"set PROTO %s", self.counters["cmd_proto"]',
                'Response': ELM_R_OK
            },
            'AT_TRY_PROTO': {
                'Request': '^ATTP[0-9A-C]+$',
                'Descr': 'AT_TRY_PROTO',
                'Log': '"Try protocol %s", cmd[4:]',
                'Response': ELM_R_OK
            },
            'AT_RESET': {
                'Request': '^ATZ$',
                'Descr': 'AT RESET',
                'Log': '"Sleep 0.5 seconds"',
                'Exec': 'self.reset(0.5)',
                'Response': "\r\rELM327 v1.5\r"
            },
        },
        # OBD Commands
        'engineoff' : {
            'ELM_PIDS_A': {
                'Request': '^0100$',
                'Descr': 'PIDS_A',
                'Exec': 'time.sleep(1 if self.counters[pid] == 1 else 0)',
                'ResponseHeader': \
                lambda self, cmd, pid, val: \
                    'SEARCHING...\rUNABLE TO CONNECT\r' \
                    if self.counters[pid] == 1 else 'NO DATA\r',
                'Response': '',
                'Priority': 5
            },
            'ELM_MIDS_A': {
                'Request': '^0600$',
                'Descr': 'MIDS_A',
                'Exec': 'time.sleep(1 if self.counters[pid] == 1 else 0)',
                'ResponseHeader': \
                lambda self, cmd, pid, val: \
                    'SEARCHING...\rUNABLE TO CONNECT\r' \
                    if self.counters[pid] == 1 else 'NO DATA\r',
                'Response': '',
                'Priority': 5
            },
            'AT_DESCRIBE_PROTO_N': {
                'Request': '^ATDPN$',
                'Descr': 'set DESCRIBE_PROTO_N',
                'Exec': 'time.sleep(0.5)',
                'Response': "A0\r"
            },
            'NO_DATA': {
                'Request': '^[0-9][0-9][0-9A-F]+$',
                'Descr': 'NO_DATA',
                'Response': 'NO DATA\r',
                'Priority': 6
            },
        },
        'test' : {
            'ENGINE_LOAD': {
                'Request': '^0104' + ELM_MAX_RESP,
                'Descr': 'Calculated Engine Load',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 03 41 04 3F \r'
            },
            'COOLANT_TEMP': {
                'Request': '^0105' + ELM_MAX_RESP,
                'Descr': 'Engine Coolant Temperature',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 03 41 05 4B \r'
            },
            'INTAKE_TEMP': {
                'Request': '^010F' + ELM_MAX_RESP,
                'Descr': 'Intake Air Temp',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 03 41 0F 4B \r'
            },
            'MAF': {
                'Request': '^0110' + ELM_MAX_RESP,
                'Descr': 'Air Flow Rate (MAF)',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 04 41 10 0B F7 \r'
            },
            'RUN_TIME': {
                'Request': '^011F' + ELM_MAX_RESP,
                'Descr': 'Engine Run Time',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 04 41 1F 00 8D \r'
            },
            'DISTANCE_W_MIL': {
                'Request': '^0121' + ELM_MAX_RESP,
                'Descr': 'Distance Traveled with MIL on',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 04 41 21 00 00 \r'
            },
            'FUEL_RAIL_PRESSURE_DIRECT': {
                'Request': '^0123' + ELM_MAX_RESP,
                'Descr': 'Fuel Rail Pressure (direct inject)',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 04 41 23 10 66 \r'
            },
            'COMMANDED_EGR': {
                'Request': '^012C' + ELM_MAX_RESP,
                'Descr': 'Commanded EGR',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 03 41 2C 00 \r'
            },
            'EGR_ERROR': {
                'Request': '^012D' + ELM_MAX_RESP,
                'Descr': 'EGR Error',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 03 41 2D A9 \r'
            },
            'DISTANCE_SINCE_DTC_CLEAR': {
                'Request': '^0131' + ELM_MAX_RESP,
                'Descr': 'Distance traveled since codes cleared',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 04 41 31 01 77 \r'
            },
            'BAROMETRIC_PRESSURE': {
                'Request': '^0133' + ELM_MAX_RESP,
                'Descr': 'Barometric Pressure',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 03 41 33 63 \r'
            },
            'CATALYST_TEMP_B1S1': {
                'Request': '^013C' + ELM_MAX_RESP,
                'Descr': 'Catalyst Temperature: Bank 1 - Sensor 1',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 04 41 3C 04 4C \r'
            },
            'ELM_PIDS_C': {
                'Request': '^0140' + ELM_MAX_RESP,
                'Descr': 'PIDS_C',
                'Header': ECU_ADDR_E,
                'Response':
                ECU_R_ADDR_T + ' 06 41 40 40 0C 00 00 \r' + ECU_R_ADDR_E +
                ' 06 41 40 44 DC 00 09 \r'
            },
            'CONTROL_MODULE_VOLTAGE': {
                'Request': '^0142' + ELM_MAX_RESP,
                'Descr': 'Control module voltage',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_T + ' 04 41 42 3A 56 \r00 \r'
            },
            'ACCELERATOR_POS_E': {
                'Request': '^014A' + ELM_MAX_RESP,
                'Descr': 'Accelerator pedal position E',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 03 41 4A 00 \r'
            },
            'RUN_TIME_MIL': {
                'Request': '^014D' + ELM_MAX_RESP,
                'Descr': 'Time run with MIL on',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 04 41 4D 00 00 \r'
            },
            'TIME_SINCE_DTC_CLEARED': {
                'Request': '^014E' + ELM_MAX_RESP,
                'Descr': 'Time since trouble codes cleared',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 04 41 4E 02 00 \r'
            },
            'FUEL_INJECT_TIMING': {
                'Request': '^015D' + ELM_MAX_RESP,
                'Descr': 'Fuel injection timing',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 04 41 5D 69 00 \r'
            },
            'CUSTOM_T_P': {
                'Request': '^2101' + ELM_MAX_RESP,
                'Descr': 'Ambient temperature & pressure',
                'Response':
                '7EA 10 18 61 01 00 63 42 32 \r7EA 21 63 38 00 00 00 00 00 \r'
                + '7EA 22 2D 28 51 FF C8 1D FF \r7EA 23 FF 1C 13 99 00 00 00 \r',
                'Header': ECU_ADDR_H
            },
        },
        'default' : {
            'FUEL_STATUS': {
                'Request': '^0103' + ELM_MAX_RESP,
                'Descr': 'Fuel System Status',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 04 41 03 00 00 \r'
            },
            'ENGINE_LOAD': {
                'Request': '^0104' + ELM_MAX_RESP,
                'Descr': 'Calculated Engine Load',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 03 41 04 00 \r'
            },
            'COOLANT_TEMP': {
                'Request': '^0105' + ELM_MAX_RESP,
                'Descr': 'Engine Coolant Temperature',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 05 41 05 7B \r'
            },
            'INTAKE_PRESSURE': {
                'Request': '^010B' + ELM_MAX_RESP,
                'Descr': 'Intake Manifold Pressure',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 03 41 0B 73 \r'
            },
            'RPM': {
                'Request': '^010C' + ELM_MAX_RESP,
                'Descr': 'Engine RPM',
                'Header': ECU_ADDR_E,
                'Response': '',
                'ResponseFooter': \
                lambda self, cmd, pid, val: \
                    self.ECU_R_ADDR_E + ' 04 41 0C ' \
                    + self.Sequence(pid, base=2400, max=200, factor=80, n_bytes=2) \
                    + ' \r' + self.ECU_R_ADDR_H + ' 04 41 0C ' \
                    + self.Sequence(pid, base=2400, max=200, factor=80, n_bytes=2) \
                    + ' \r'
            },
            'SPEED': {
                'Request': '^010D' + ELM_MAX_RESP,
                'Descr': 'Vehicle Speed',
                'Header': ECU_ADDR_E,
                'Response': '',
                'ResponseFooter': \
                lambda self, cmd, pid, val: \
                    self.ECU_R_ADDR_E + ' 03 41 0D ' \
                    + self.Sequence(pid, base=0, max=30, factor=4, n_bytes=1) \
                    + ' \r' + self.ECU_R_ADDR_H + ' 03 41 0D ' \
                    + self.Sequence(pid, base=0, max=30, factor=4, n_bytes=1) \
                    + ' \r'
            },
            'INTAKE_TEMP': {
                'Request': '^010F' + ELM_MAX_RESP,
                'Descr': 'Intake Air Temp',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 03 41 0F 44 \r'
            },
            'MAF': {
                'Request': '^0110' + ELM_MAX_RESP,
                'Descr': 'Air Flow Rate (MAF)',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 04 41 10 05 1F \r'
            },
            'THROTTLE_POS': {
                'Request': '^0111' + ELM_MAX_RESP,
                'Descr': 'Throttle Position',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 03 41 11 FF \r'
            },
            'OBD_COMPLIANCE': {
                'Request': '^011C' + ELM_MAX_RESP,
                'Descr': 'OBD Standards Compliance',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 03 41 1C 06 \r'
            },
            'RUN_TIME': {
                'Request': '^011F' + ELM_MAX_RESP,
                'Descr': 'Engine Run Time',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 04 41 1F 00 8C \r'
            },
            'DISTANCE_W_MIL': {
                'Request': '^0121' + ELM_MAX_RESP,
                'Descr': 'Distance Traveled with MIL on',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 04 41 21 00 00 \r00 \r'
            },
            'FUEL_RAIL_PRESSURE_DIRECT': {
                'Request': '^0123' + ELM_MAX_RESP,
                'Descr': 'Fuel Rail Pressure (direct inject)',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 04 41 23 1A 0E \r'
            },
            'COMMANDED_EGR': {
                'Request': '^012C' + ELM_MAX_RESP,
                'Descr': 'Commanded EGR',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 03 41 2C 0D \r'
            },
            'EGR_ERROR': {
                'Request': '^012D' + ELM_MAX_RESP,
                'Descr': 'EGR Error',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 03 41 2D 80 \r'
            },
            'DISTANCE_SINCE_DTC_CLEAR': {
                'Request': '^0131' + ELM_MAX_RESP,
                'Descr': 'Distance traveled since codes cleared',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 04 41 31 C8 1F \r'
            },
            'BAROMETRIC_PRESSURE': {
                'Request': '^0133' + ELM_MAX_RESP,
                'Descr': 'Barometric Pressure',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 03 41 33 65 \r'
            },
            'CATALYST_TEMP_B1S1': {
                'Request': '^013C' + ELM_MAX_RESP,
                'Descr': 'Catalyst Temperature: Bank 1 - Sensor 1',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 04 41 3C 04 44 \r'
            },
            'CONTROL_MODULE_VOLTAGE': {
                'Request': '^0142' + ELM_MAX_RESP,
                'Descr': 'Control module voltage',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 04 41 42 39 D6 \r00 \r'
            },
            'AMBIANT_AIR_TEMP': {
                'Request': '^0146' + ELM_MAX_RESP,
                'Descr': 'Ambient air temperature',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 03 41 46 43 \r'
            },
            'ACCELERATOR_POS_D': {
                'Request': '^0149' + ELM_MAX_RESP,
                'Descr': 'Accelerator pedal position D',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 03 41 49 00 \r'
            },
            'ACCELERATOR_POS_E': {
                'Request': '^014A' + ELM_MAX_RESP,
                'Descr': 'Accelerator pedal position E',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 03 41 4A 45 \r'
            },
            'THROTTLE_ACTUATOR': {
                'Request': '^014C' + ELM_MAX_RESP,
                'Descr': 'Commanded throttle actuator',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 03 41 4C 00 \r'
            },
            'RUN_TIME_MIL': {
                'Request': '^014D' + ELM_MAX_RESP,
                'Descr': 'Time run with MIL on',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 04 41 4D 00 00 \r00 \r'
            },
            'TIME_SINCE_DTC_CLEARED': {
                'Request': '^014E' + ELM_MAX_RESP,
                'Descr': 'Time since trouble codes cleared',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 04 41 4E 4C 69 \r00 \r'
            },
            'FUEL_TYPE': {
                'Request': '^0151' + ELM_MAX_RESP,
                'Descr': 'Fuel Type',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 03 41 51 01 \r'
            },
            'UNKNOWN': {
                'Request': '^015B' + ELM_MAX_RESP,
                'Descr': 'Unknown',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 03 41 51 01 \r'
            },
            'FUEL_INJECT_TIMING': {
                'Request': '^015D' + ELM_MAX_RESP,
                'Descr': 'Fuel injection timing',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 04 41 5D 66 00 \r'
            },
           # Custom
            'CUSTOM_T_P': {
                'Request': '^2101' + ELM_MAX_RESP,
                'Descr': 'Ambient temperature & pressure',
                'Response': ECU_R_ADDR_H + ' 10 18 61 01 00 64 4B FF \r',
                'Header': ECU_ADDR_H
            },
            'CUSTOM_ATEMP': {
                'Request': '^2101' + ELM_MAX_RESP,
                'Descr': 'Ambient Temperature',
                'Response': ECU_R_ADDR_E + ' 10 1B 61 01 00 00 00 00 \r',
                'Header': ECU_ADDR_E
            },
            'CUSTOM_AUX_B_VOLT': {
                'Request': '^2113' + ELM_MAX_RESP,
                'Descr': '+B Voltage Value',
                'Response': ECU_R_ADDR_I + ' 03 61 13 95 \r',
                'Header': ECU_ADDR_I
            },
            'CUSTOM_ROOM': {
                'Request': '^2121' + ELM_MAX_RESP,
                'Descr': 'Room Temp Sensor',
                'Response': ECU_R_ADDR_P + ' 03 61 21 53 \r',
                'Header': ECU_ADDR_P
            },
            'CUSTOM_AMBIENT': {
                'Request': '^2122' + ELM_MAX_RESP,
                'Descr': 'Ambient Temp Sensor',
                'Response': ECU_R_ADDR_P + ' 03 61 22 5F \r',
                'Header': ECU_ADDR_P
            },
            'CUSTOM_SOLAR': {
                'Request': '^2124' + ELM_MAX_RESP,
                'Descr': 'Solar sensor',
                'Response': ECU_R_ADDR_P + ' 03 61 24 01 \r',
                'Header': ECU_ADDR_P
            },
            'CUSTOM_FUEL_MAIN': {
                'Request': '^2129' + ELM_MAX_RESP,
                'Descr': 'Fuel level - main tank',
                'Response': ECU_R_ADDR_I + ' 03 61 29 15 \r',
                'Header': ECU_ADDR_I
            },
            'CUSTOM_SET_TEMP_D': {
                'Request': '^2129[012]?$',
                'Descr': 'Set Temperature (D side)',
                'Response': ECU_R_ADDR_P + ' 03 7F 21 12 \r',
                'Header': ECU_ADDR_P
            },
            'CUSTOM_FUEL_SUB': {
                'Request': '^212A' + ELM_MAX_RESP,
                'Descr': 'Fuel level - sub tank',
                'Response': ECU_R_ADDR_I + ' 03 7F 21 12 \r',
                'Header': ECU_ADDR_I
            },
            'CUSTOM_ADJUSTED': {
                'Request': '^213D' + ELM_MAX_RESP,
                'Descr': 'Adjusted Ambient Temp',
                'Response': ECU_R_ADDR_P + ' 03 61 3D 81 \r',
                'Header': ECU_ADDR_P
            },
            'CUSTOM_RHEOSTAT': {
                'Request': '^2168' + ELM_MAX_RESP,
                'Descr': 'Rheostat value (dark=0,bright=255)',
                'Response': ECU_R_ADDR_I + ' 03 7F 21 12 \r',
                'Header': ECU_ADDR_I
            },
            'CUSTOM_SEAT': {
                'Request': '^21A7' + ELM_MAX_RESP,
                'Descr': 'Seat belt',
                'Response': ECU_R_ADDR_I + ' 03 61 A7 20 \r',
                'Header': ECU_ADDR_I
            },
            # Supported PIDs for protocols
            'ELM_PIDS_A': {
                'Request': '^0100$',
                'Descr': 'PIDS_A',
                'Exec': 'time.sleep(1 if self.counters["ELM_PIDS_A"] == 1 else 0)',
                'ResponseHeader': \
                lambda self, cmd, pid, val: \
                    'SEARCHING...\r' if self.counters[pid] == 1 else "",
                'Response':
                ECU_R_ADDR_H + ' 06 41 00 98 3A 80 13 \r' +
                ECU_R_ADDR_E + ' 06 41 00 BE 3F A8 13 \r'
            },
            'ELM_PIDS_B': {
                'Request': '^0120$',
                'Descr': 'PIDS_B',
                'Response':
                ECU_R_ADDR_H + ' 06 41 20 80 01 A0 01 \r' +
                ECU_R_ADDR_E + ' 06 41 20 90 15 B0 15 \r'
            },
            'ELM_PIDS_C': {
                'Request': '^0140$',
                'Descr': 'PIDS_C',
                'Response':
                ECU_R_ADDR_H + ' 06 41 40 44 CC 00 21 \r' +
                ECU_R_ADDR_E + ' 06 41 40 7A 1C 80 00 \r'
            },
            'ELM_MIDS_A': {
                'Request': '^0600$',
                'Descr': 'MIDS_A',
                'Response': ECU_R_ADDR_E + ' 06 46 00 C0 00 00 01 \r'
            },
            'ELM_MIDS_B': {
                'Request': '^0620$',
                'Descr': 'MIDS_B',
                'Response': ECU_R_ADDR_E + ' 06 46 20 80 00 80 01 \r'
            },
            'ELM_MIDS_C': {
                'Request': '^0640$',
                'Descr': 'MIDS_C',
                'Response': ECU_R_ADDR_E + ' 06 46 40 00 00 00 01 \r'
            },
            'ELM_MIDS_D': {
                'Request': '^0660$',
                'Descr': 'MIDS_D',
                'Response': ECU_R_ADDR_E + ' 06 46 60 00 00 00 01 \r'
            },
            'ELM_MIDS_E': {
                'Request': '^0680$',
                'Descr': 'MIDS_E',
                'Response': ECU_R_ADDR_E + ' 06 46 80 00 00 00 01 \r'
            },
            'ELM_MIDS_F': {
                'Request': '^06A0$',
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
        logging.debug("Resetting counters and sleeping for %s seconds", sleep)
        time.sleep(sleep)
        for i in [k for k in self.counters if k.startswith('cmd_')]:
            del(self.counters[i])
        self.counters['ELM_PIDS_A'] = 0
        self.counters['ELM_MIDS_A'] = 0
        self.counters["cmd_header"] = self.ECU_ADDR_E

    def set_defaults(self):
        """ returns all settings to their defaults """
        self.scenario = 'default'
        self.delay = 0
        self.answer = {}
        self.counters = {}

    def __init__(self, protocols, ecus):
        self.set_defaults()
        self.reset(0)

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
        self.logger = logging.getLogger()
        logging.info('\n\nELM327 OBD-II adapter simulator started\n')
        """ the ELM's main IO loop """
        
        self.threadState = THREAD.ACTIVE
        while self.threadState != THREAD.STOPPED:

            if self.threadState == THREAD.PAUSED:
                time.sleep(0.1)
                continue

                # get the latest command
            self.cmd = self.read()

            # process 'fast' option
            if re.match('^ *$', self.cmd) and "last_cmd" in self.counters:
                self.cmd = self.counters["last_cmd"]
                logging.debug("repeating previous command: %s", repr(self.cmd))
            else:
                self.counters["last_cmd"] = self.cmd
                logging.debug("received '%s'", repr(self.cmd))

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

        #n = "\r\r" if 'cmd_linefeeds' in self.counters and self.counters['cmd_linefeeds'] else "\r"
        n = "\r"
        resp += n + ">"

        if 'echo' in self.counters and self.counters['cmd_echo']:
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

        if 'commands' not in self.counters:
            self.counters['commands'] = 0
        self.counters['commands'] += 1

        dump = hexdump.dump(cmd.encode('utf-8'), sep=":")
        logging.debug("handling: %s - %s", repr(cmd), dump)
        if self.delay > 0:
            time.sleep(self.delay)

        # Perform a union of the three subdictionaries
        s = {
            **self.ObdMessage['default'],
            **self.ObdMessage['AT'],
            **self.ObdMessage[self.scenario]
            }
        # Add 'Priority' to all pids and sort basing on priority (highest = 1, lowest=10)
        for i in sorted(
                s.items(), key=lambda x: x[1]['Priority'] if 'Priority' in x[1] else 10 ):
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
                    logging.debug("Received %s, PID %s (%s)",
                                  val['Descr'], pid, cmd)
                else:
                    logging.error(
                        "Internal error - Missing description for %s, PID %s", cmd, pid)
                if pid in self.answer:
                    try:
                        return(self.answer[pid])
                    except Exception as e:
                        logging.error(
                        "Error while processing '%s' for PID %s (%s)", self.answer, pid, e)                     
                if 'Exec' in val:
                    try:
                        exec(val['Exec'])
                    except Exception as e:
                        logging.error(
                        "Cannot execute '%s' for PID %s (%s)", val['Exec'], pid, e)
                if 'Log' in val:
                    try:
                        exec("logging.debug(" + val['Log'] + ")")
                    except Exception as e:
                        logging.error(
                        "Error while logging '%s' for PID %s (%s)", val['Log'], pid, e)
                if 'Response' in val:
                    header = ''
                    if 'ResponseHeader' in val:
                        header = val['ResponseHeader'](
                            self, cmd, pid, val)
                    footer = ''
                    if 'ResponseFooter' in val:
                        footer = val['ResponseFooter'](
                            self, cmd, pid, val)
                    return (header + val['Response'] + footer)
                else:
                    logging.error(
                        "Internal error - Missing response for %s, PID %s", cmd, pid)
                    return self.ELM_R_OK
        if "unknown_" + cmd not in self.counters:
            self.counters["unknown_" + cmd] = 0
        self.counters["unknown_" + cmd] += 1
        logging.info("Unknown ELM command: %s, header=%s, dump=%s", cmd, self.counters["cmd_header"], dump)
        return ""

    def sanitize(self, cmd):
        cmd = cmd.replace(" ", "")
        cmd = cmd.upper()
        return cmd
