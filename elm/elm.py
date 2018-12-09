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
from random import randint


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
    ECU_ADDR_S = "7B0"  # Skid Control address ECU
    ECU_R_ADDR_S = "7B8"  # Responses sent by 7B0 Skid Control ECU 7B0/7B8

    def Sequence(self, pid, base, max, factor, n_bytes):
        c = self.counters[pid]
        # compute the new value [= factor * ( counter % (max * 2) )]
        p = int (factor * abs( max - ( c + max ) % (max * 2) ) ) + base
        # get its hex string
        s = ("%.X" % p).zfill(n_bytes * 2)
        # space the string into chunks of two bytes
        return (" ".join(s[i:i + 2] for i in range(0, len(s), 2)))

    ELM_R_OK = "OK\r"
    ELM_MAX_RESP = '[0123456]?$'

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
                'Request': '^ATDP' + ELM_MAX_RESP,
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
                'Response': ("ON\r", "OFF\r")
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
                'Response': (ECU_R_ADDR_I + ' 03 61 29 15 \r',
                             ECU_R_ADDR_I + ' 03 61 29 16 \r'),
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
                'Request': '^0100' + ELM_MAX_RESP,
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
                'Request': '^0120' + ELM_MAX_RESP,
                'Descr': 'PIDS_B',
                'Response':
                ECU_R_ADDR_H + ' 06 41 20 80 01 A0 01 \r' +
                ECU_R_ADDR_E + ' 06 41 20 90 15 B0 15 \r'
            },
            'ELM_PIDS_C': {
                'Request': '^0140' + ELM_MAX_RESP,
                'Descr': 'PIDS_C',
                'Response':
                ECU_R_ADDR_H + ' 06 41 40 44 CC 00 21 \r' +
                ECU_R_ADDR_E + ' 06 41 40 7A 1C 80 00 \r'
            },
            'ELM_MIDS_A': {
                'Request': '^0600' + ELM_MAX_RESP,
                'Descr': 'MIDS_A',
                'Response': ECU_R_ADDR_E + ' 06 46 00 C0 00 00 01 \r'
            },
            'ELM_MIDS_B': {
                'Request': '^0620' + ELM_MAX_RESP,
                'Descr': 'MIDS_B',
                'Response': ECU_R_ADDR_E + ' 06 46 20 80 00 80 01 \r'
            },
            'ELM_MIDS_C': {
                'Request': '^0640' + ELM_MAX_RESP,
                'Descr': 'MIDS_C',
                'Response': ECU_R_ADDR_E + ' 06 46 40 00 00 00 01 \r'
            },
            'ELM_MIDS_D': {
                'Request': '^0660' + ELM_MAX_RESP,
                'Descr': 'MIDS_D',
                'Response': ECU_R_ADDR_E + ' 06 46 60 00 00 00 01 \r'
            },
            'ELM_MIDS_E': {
                'Request': '^0680' + ELM_MAX_RESP,
                'Descr': 'MIDS_E',
                'Response': ECU_R_ADDR_E + ' 06 46 80 00 00 00 01 \r'
            },
            'ELM_MIDS_F': {
                'Request': '^06A0' + ELM_MAX_RESP,
                'Descr': 'MIDS_F',
                'Response': ECU_R_ADDR_E + ' 06 46 A0 F8 00 00 00 \r'
            }
        },
        'car': {
            'PIDS_A': {
                'Request': '^0100' + ELM_MAX_RESP,
                'Descr': 'Supported PIDs [01-20]',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 06 41 00 BE 3F A8 13 \r'
            },
            'STATUS': {
                'Request': '^0101' + ELM_MAX_RESP,
                'Descr': 'Status since DTCs cleared',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 06 41 01 00 07 A1 A1 \r'
            },
            'FUEL_STATUS': {
                'Request': '^0103' + ELM_MAX_RESP,
                'Descr': 'Fuel System Status',
                'Header': ECU_ADDR_E,
                'Response': [
                            ECU_R_ADDR_E + ' 04 41 03 00 00 \r',
                            ECU_R_ADDR_E + ' 04 41 03 02 00 \r',
                            ECU_R_ADDR_E + ' 04 41 03 04 00 \r'
                            ]
            },
            'ENGINE_LOAD': {
                'Request': '^0104' + ELM_MAX_RESP,
                'Descr': 'Calculated Engine Load',
                'Header': ECU_ADDR_E,
                'Response': [
                            ECU_R_ADDR_E + ' 03 41 04 00 \r',
                            ECU_R_ADDR_E + ' 03 41 04 55 \r',
                            ECU_R_ADDR_E + ' 03 41 04 F0 \r',
                            ECU_R_ADDR_E + ' 03 41 04 FF \r',
                            ECU_R_ADDR_E + ' 03 41 04 3B \r',
                            ECU_R_ADDR_E + ' 03 41 04 E8 \r',
                            ECU_R_ADDR_E + ' 03 41 04 37 \r'
                            ]
                # 21.568627451 percent
                # 33.3333333333 percent
                # 100.0 percent
                # 23.137254902 percent
                # 90.9803921569 percent
                # 94.1176470588 percent
            },
            'COOLANT_TEMP': {
                'Request': '^0105' + ELM_MAX_RESP,
                'Descr': 'Engine Coolant Temperature',
                'Header': ECU_ADDR_E,
                'Response': [
                            ECU_R_ADDR_E + ' 03 41 05 51 \r',
                            ECU_R_ADDR_E + ' 03 41 05 54 \r',
                            ECU_R_ADDR_E + ' 03 41 05 55 \r',
                            ECU_R_ADDR_E + ' 03 41 05 58 \r',
                            ECU_R_ADDR_E + ' 03 41 05 57 \r'
                            ]
                # 44 degC
                # 47 degC
                # 41 degC
                # 48 degC
                # 45 degC
            },
            'SHORT_FUEL_TRIM_1': {
                'Request': '^0106' + ELM_MAX_RESP,
                'Descr': 'Short Term Fuel Trim - Bank 1',
                'Header': ECU_ADDR_E,
                'Response': [
                            ECU_R_ADDR_E + ' 03 41 06 7E \r',
                            ECU_R_ADDR_E + ' 03 41 06 80 \r'
                            ]
                # -1.5625 percent
            },
            'LONG_FUEL_TRIM_1': {
                'Request': '^0107' + ELM_MAX_RESP,
                'Descr': 'Long Term Fuel Trim - Bank 1',
                'Header': ECU_ADDR_E,
                'Response': [
                            ECU_R_ADDR_E + ' 03 41 07 7A \r',
                            ECU_R_ADDR_E + ' 03 41 07 79 \r',
                            ECU_R_ADDR_E + ' 03 41 07 7C \r',
                            ECU_R_ADDR_E + ' 03 41 07 7E \r',
                            ECU_R_ADDR_E + ' 03 41 07 7B \r'
                            ]
                # -5.46875 percent
                # -3.90625 percent
                # -4.6875 percent
                # -1.5625 percent
                # -3.125 percent
            },
            'INTAKE_PRESSURE': {
                'Request': '^010B' + ELM_MAX_RESP,
                'Descr': 'Intake Manifold Pressure',
                'Header': ECU_ADDR_E,
                'Response': [
                            ECU_R_ADDR_E + ' 03 41 0B 18 \r',
                            ECU_R_ADDR_E + ' 03 41 0B 60 \r',
                            ECU_R_ADDR_E + ' 03 41 0B 52 \r',
                            ECU_R_ADDR_E + ' 03 41 0B 63 \r',
                            ECU_R_ADDR_E + ' 03 41 0B 16 \r',
                            ECU_R_ADDR_E + ' 03 41 0B 5D \r',
                            ECU_R_ADDR_E + ' 03 41 0B 1F \r'
                            ]
                # 99 kilopascal
                # 31 kilopascal
                # 22 kilopascal
                # 24 kilopascal
                # 96 kilopascal
                # 82 kilopascal
                # 93 kilopascal
            },
            'RPM': {
                'Request': '^010C' + ELM_MAX_RESP,
                'Descr': 'Engine RPM',
                'Header': ECU_ADDR_E,
                'Response': [
                            ECU_R_ADDR_E + ' 04 41 0C 18 F9 \r',
                            ECU_R_ADDR_E + ' 04 41 0C 27 D4 \r',
                            ECU_R_ADDR_E + ' 04 41 0C 12 E8 \r',
                            ECU_R_ADDR_E + ' 04 41 0C 0C 80 \r',
                            ECU_R_ADDR_E + ' 04 41 0C 15 24 \r',
                            ECU_R_ADDR_E + ' 04 41 0C 00 00 \r',
                            ECU_R_ADDR_E + ' 04 41 0C 19 51 \r'
                            ]
                # 1620.25 revolutions_per_minute
                # 2549.0 revolutions_per_minute
                # 1353.0 revolutions_per_minute
                # 1210.0 revolutions_per_minute
                # 800.0 revolutions_per_minute
                # 1598.25 revolutions_per_minute
            },
            'SPEED': {
                'Request': '^010D' + ELM_MAX_RESP,
                'Descr': 'Vehicle Speed',
                'Header': ECU_ADDR_E,
                'Response': [
                            ECU_R_ADDR_E + ' 03 41 0D 2A \r',
                            ECU_R_ADDR_E + ' 03 41 0D 19 \r',
                            ECU_R_ADDR_E + ' 03 41 0D 1E \r',
                            ECU_R_ADDR_E + ' 03 41 0D 29 \r',
                            ECU_R_ADDR_E + ' 03 41 0D 0D \r',
                            ECU_R_ADDR_E + ' 03 41 0D 21 \r',
                            ECU_R_ADDR_E + ' 03 41 0D 3C \r',
                            ECU_R_ADDR_E + ' 03 41 0D 1F \r',
                            ECU_R_ADDR_E + ' 03 41 0D 1B \r'
                            ]
                # 42 kph
                # 31 kph
                # 33 kph
                # 27 kph
                # 25 kph
                # 60 kph
                # 41 kph
                # 30 kph
                # 13 kph
            },
            'TIMING_ADVANCE': {
                'Request': '^010E' + ELM_MAX_RESP,
                'Descr': 'Timing Advance',
                'Header': ECU_ADDR_E,
                'Response': [
                            ECU_R_ADDR_E + ' 03 41 0E 9E \r',
                            ECU_R_ADDR_E + ' 03 41 0E 8A \r',
                            ECU_R_ADDR_E + ' 03 41 0E 9B \r',
                            ECU_R_ADDR_E + ' 03 41 0E 9D \r',
                            ECU_R_ADDR_E + ' 03 41 0E A6 \r'
                            ]
                # 15.0 degree
                # 13.5 degree
                # 19.0 degree
                # 5.0 degree
                # 14.5 degree
            },
            'INTAKE_TEMP': {
                'Request': '^010F' + ELM_MAX_RESP,
                'Descr': 'Intake Air Temp',
                'Header': ECU_ADDR_E,
                'Response': [
                            ECU_R_ADDR_E + ' 03 41 0F 3A \r',
                            ECU_R_ADDR_E + ' 03 41 0F 39 \r',
                            ECU_R_ADDR_E + ' 03 41 0F 3B \r',
                            ECU_R_ADDR_E + ' 03 41 0F 37 \r',
                            ECU_R_ADDR_E + ' 03 41 0F 38 \r'
                            ]
                # 18 degC
                # 19 degC
                # 16 degC
                # 17 degC
                # 15 degC
            },
            'MAF': {
                'Request': '^0110' + ELM_MAX_RESP,
                'Descr': 'Air Flow Rate (MAF)',
                'Header': ECU_ADDR_E,
                'Response': [
                            ECU_R_ADDR_E + ' 04 41 10 03 8B \r',
                            ECU_R_ADDR_E + ' 04 41 10 04 04 \r',
                            ECU_R_ADDR_E + ' 04 41 10 09 99 \r',
                            ECU_R_ADDR_E + ' 04 41 10 0D EC \r',
                            ECU_R_ADDR_E + ' 04 41 10 00 11 \r',
                            ECU_R_ADDR_E + ' 04 41 10 00 12 \r'
                            ]
                # 0.17 gps
                # 24.57 gps
                # 10.28 gps
                # 35.64 gps
                # 9.07 gps
                # 0.18 gps
            },
            'THROTTLE_POS': {
                'Request': '^0111' + ELM_MAX_RESP,
                'Descr': 'Throttle Position',
                'Header': ECU_ADDR_E,
                'Response': [
                            ECU_R_ADDR_E + ' 03 41 11 6E \r',
                            ECU_R_ADDR_E + ' 03 41 11 2B \r',
                            ECU_R_ADDR_E + ' 03 41 11 69 \r',
                            ECU_R_ADDR_E + ' 03 41 11 33 \r',
                            ECU_R_ADDR_E + ' 03 41 11 3A \r'
                            ]
                # 16.862745098 percent
                # 20.0 percent
                # 41.1764705882 percent
                # 43.137254902 percent
                # 22.7450980392 percent
            },
            'O2_SENSORS': {
                'Request': '^0113' + ELM_MAX_RESP,
                'Descr': 'O2 Sensors Present',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 03 41 13 03 \r'
            },
            'O2_B1S2': {
                'Request': '^0115' + ELM_MAX_RESP,
                'Descr': 'O2: Bank 1 - Sensor 2 Voltage',
                'Header': ECU_ADDR_E,
                'Response': [
                            ECU_R_ADDR_E + ' 04 41 15 B7 FF \r',
                            ECU_R_ADDR_E + ' 04 41 15 00 FF \r',
                            ECU_R_ADDR_E + ' 04 41 15 B3 FF \r',
                            ECU_R_ADDR_E + ' 04 41 15 BB FF \r',
                            ECU_R_ADDR_E + ' 04 41 15 A4 FF \r'
                            ]
                # 0.82 volt
                # 0.935 volt
                # 0.915 volt
                # 0.895 volt
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
                'Response': [
                            ECU_R_ADDR_E + ' 04 41 1F 00 E6 \r',
                            ECU_R_ADDR_E + ' 04 41 1F 00 6C \r',
                            ECU_R_ADDR_E + ' 04 41 1F 00 9A \r',
                            ECU_R_ADDR_E + ' 04 41 1F 00 7C \r',
                            ECU_R_ADDR_E + ' 04 41 1F 00 B9 \r',
                            ECU_R_ADDR_E + ' 04 41 1F 00 8B \r',
                            ECU_R_ADDR_E + ' 04 41 1F 00 F6 \r',
                            ECU_R_ADDR_E + ' 04 41 1F 00 A9 \r',
                            ECU_R_ADDR_E + ' 04 41 1F 00 D7 \r',
                            ECU_R_ADDR_E + ' 04 41 1F 00 C8 \r'
                            ]
                # 200 second
                # 108 second
                # 139 second
                # 185 second
                # 169 second
                # 246 second
                # 124 second
                # 154 second
                # 215 second
                # 230 second
            },
            'PIDS_B': {
                'Request': '^0120' + ELM_MAX_RESP,
                'Descr': 'Supported PIDs [21-40]',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 06 41 20 90 15 B0 15 \r'
            },
            'DISTANCE_W_MIL': {
                'Request': '^0121' + ELM_MAX_RESP,
                'Descr': 'Distance Traveled with MIL on',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 04 41 21 00 00 \r'
            },
            'O2_S1_WR_VOLTAGE': {
                'Request': '^0124' + ELM_MAX_RESP,
                'Descr': '02 Sensor 1 WR Lambda Voltage',
                'Header': ECU_ADDR_E,
                'Response': [
                            ECU_R_ADDR_E + ' 06 41 24 68 1C 1F 7A \r',
                            ECU_R_ADDR_E + ' 06 41 24 7B 7F 64 E9 \r',
                            ECU_R_ADDR_E + ' 06 41 24 73 CE 56 D9 \r',
                            ECU_R_ADDR_E + ' 06 41 24 68 1C 27 04 \r',
                            ECU_R_ADDR_E + ' 06 41 24 7B 11 65 89 \r',
                            ECU_R_ADDR_E + ' 06 41 24 82 0B 6D F9 \r',
                            ECU_R_ADDR_E + ' 06 41 24 7E 2A 68 A9 \r',
                            ECU_R_ADDR_E + ' 06 41 24 79 45 61 C9 \r',
                            ECU_R_ADDR_E + ' 06 41 24 72 95 54 31 \r',
                            ECU_R_ADDR_E + ' 06 41 24 68 1C 1B B6 \r'
                            ]
                # 3.05583276112 volt
                # 2.63102159152 volt
                # 3.43669794766 volt
                # 0.865980010681 volt
                # 3.17302204929 volt
                # 3.27067978943 volt
                # 0.983657587549 volt
                # 2.71403067063 volt
                # 3.15349050126 volt
                # 1.21925688563 volt
            },
            'COMMANDED_EGR': {
                'Request': '^012C' + ELM_MAX_RESP,
                'Descr': 'Commanded EGR',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 03 41 2C 00 \r'
            },
            'EVAPORATIVE_PURGE': {
                'Request': '^012E' + ELM_MAX_RESP,
                'Descr': 'Commanded Evaporative Purge',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 03 41 2E 00 \r'
            },
            'WARMUPS_SINCE_DTC_CLEAR': {
                'Request': '^0130' + ELM_MAX_RESP,
                'Descr': 'Number of warm-ups since codes cleared',
                'Header': ECU_ADDR_E,
                'Response': [
                            ECU_R_ADDR_E + ' 03 41 30 00 \r',
                            ECU_R_ADDR_E + ' 03 41 30 1A \r' +
                            ECU_R_ADDR_H + ' 03 41 30 FF \r'
                            ]
                # 26 count
            },
            'DISTANCE_SINCE_DTC_CLEAR': {
                'Request': '^0131' + ELM_MAX_RESP,
                'Descr': 'Distance traveled since codes cleared',
                'Header': ECU_ADDR_E,
                'Response': [
                            ECU_R_ADDR_E + ' 04 41 31 00 00 \r',
                            ECU_R_ADDR_E + ' 04 41 31 03 6A \r' +
                            ECU_R_ADDR_H + ' 04 41 31 CB 87 \r'
                            ]
                # 874 kilometer
            },
            'BAROMETRIC_PRESSURE': {
                'Request': '^0133' + ELM_MAX_RESP,
                'Descr': 'Barometric Pressure',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 03 41 33 61 \r'
                # 97 kilopascal
            },
            'O2_S1_WR_CURRENT': {
                'Request': '^0134' + ELM_MAX_RESP,
                'Descr': '02 Sensor 1 WR Lambda Current',
                'Header': ECU_ADDR_E,
                'Response': [
                            ECU_R_ADDR_E + ' 06 41 34 85 72 80 16 \r',
                            ECU_R_ADDR_E + ' 06 41 34 7B 8E 7F F4 \r',
                            ECU_R_ADDR_E + ' 06 41 34 79 10 7F DF \r',
                            ECU_R_ADDR_E + ' 06 41 34 68 1C 7F 35 \r',
                            ECU_R_ADDR_E + ' 06 41 34 85 E8 80 18 \r',
                            ECU_R_ADDR_E + ' 06 41 34 68 1C 7F 72 \r',
                            ECU_R_ADDR_E + ' 06 41 34 7F 3F 80 01 \r',
                            ECU_R_ADDR_E + ' 06 41 34 68 1C 7F 7F \r',
                            ECU_R_ADDR_E + ' 06 41 34 68 1C 7F 22 \r',
                            ECU_R_ADDR_E + ' 06 41 34 7F 41 80 00 \r'
                            ]
                # -0.50390625 milliampere
                # -0.79296875 milliampere
                # 0.00390625 milliampere
                # 0.0859375 milliampere
                # -0.8671875 milliampere
                # -0.5546875 milliampere
                # 0.09375 milliampere
                # -0.12890625 milliampere
                # -0.046875 milliampere
            },
            'CATALYST_TEMP_B1S1': {
                'Request': '^013C' + ELM_MAX_RESP,
                'Descr': 'Catalyst Temperature: Bank 1 - Sensor 1',
                'Header': ECU_ADDR_E,
                'Response': [
                            ECU_R_ADDR_E + ' 04 41 3C 18 7F \r',
                            ECU_R_ADDR_E + ' 04 41 3C 16 9F \r',
                            ECU_R_ADDR_E + ' 04 41 3C 17 58 \r',
                            ECU_R_ADDR_E + ' 04 41 3C 17 BF \r',
                            ECU_R_ADDR_E + ' 04 41 3C 0F 7E \r',
                            ECU_R_ADDR_E + ' 04 41 3C 18 EC \r',
                            ECU_R_ADDR_E + ' 04 41 3C 12 D0 \r',
                            ECU_R_ADDR_E + ' 04 41 3C 18 C9 \r',
                            ECU_R_ADDR_E + ' 04 41 3C 18 A6 \r',
                            ECU_R_ADDR_E + ' 04 41 3C 18 78 \r'
                            ]
                # 594.5 degC
                # 356.6 degC
                # 557.6 degC
                # 586.4 degC
                # 441.6 degC
                # 539.1 degC
                # 567.9 degC
                # 587.1 degC
                # 598.0 degC
                # 591.0 degC
            },
            'CATALYST_TEMP_B1S2': {
                'Request': '^013E' + ELM_MAX_RESP,
                'Descr': 'Catalyst Temperature: Bank 1 - Sensor 2',
                'Header': ECU_ADDR_E,
                'Response': [
                            ECU_R_ADDR_E + ' 04 41 3E 0A 6B \r',
                            ECU_R_ADDR_E + ' 04 41 3E 11 7F \r',
                            ECU_R_ADDR_E + ' 04 41 3E 0E 4C \r',
                            ECU_R_ADDR_E + ' 04 41 3E 11 84 \r',
                            ECU_R_ADDR_E + ' 04 41 3E 10 A4 \r',
                            ECU_R_ADDR_E + ' 04 41 3E 11 7C \r',
                            ECU_R_ADDR_E + ' 04 41 3E 11 BE \r',
                            ECU_R_ADDR_E + ' 04 41 3E 0D 0D \r',
                            ECU_R_ADDR_E + ' 04 41 3E 10 E8 \r',
                            ECU_R_ADDR_E + ' 04 41 3E 11 A1 \r'
                            ]
                # 386.0 degC
                # 226.7 degC
                # 407.9 degC
                # 294.1 degC
                # 392.8 degC
                # 411.3 degC
                # 414.2 degC
                # 407.6 degC
                # 408.4 degC
                # 326.0 degC
            },
            'PIDS_C': {
                'Request': '^0140' + ELM_MAX_RESP,
                'Descr': 'Supported PIDs [41-60]',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 06 41 40 7A 1C 80 00 \r'
            },
            'CONTROL_MODULE_VOLTAGE': {
                'Request': '^0142' + ELM_MAX_RESP,
                'Descr': 'Control module voltage',
                'Header': ECU_ADDR_E,
                'Response': [
                            ECU_R_ADDR_E + ' 04 41 42 39 AD \r',
                            ECU_R_ADDR_E + ' 04 41 42 39 9A \r',
                            ECU_R_ADDR_E + ' 04 41 42 39 5F \r'
                            ]
                # 14.765 volt
                # 14.746 volt
                # 14.687 volt
            },
            'ABSOLUTE_LOAD': {
                'Request': '^0143' + ELM_MAX_RESP,
                'Descr': 'Absolute load value',
                'Header': ECU_ADDR_E,
                'Response': [
                            ECU_R_ADDR_E + ' 04 41 43 00 B5 \r',
                            ECU_R_ADDR_E + ' 04 41 43 00 00 \r',
                            ECU_R_ADDR_E + ' 04 41 43 00 31 \r',
                            ECU_R_ADDR_E + ' 04 41 43 00 5D \r'
                            ]
                # 70.9803921569 percent
                # 36.4705882353 percent
                # 19.2156862745 percent
            },
            'COMMANDED_EQUIV_RATIO': {
                'Request': '^0144' + ELM_MAX_RESP,
                'Descr': 'Commanded equivalence ratio',
                'Header': ECU_ADDR_E,
                'Response': [
                            ECU_R_ADDR_E + ' 04 41 44 70 FD \r',
                            ECU_R_ADDR_E + ' 04 41 44 76 B8 \r',
                            ECU_R_ADDR_E + ' 04 41 44 7F F2 \r',
                            ECU_R_ADDR_E + ' 04 41 44 7F 20 \r',
                            ECU_R_ADDR_E + ' 04 41 44 7D 8A \r'
                            ]
                # 0.926956 ratio
                # 0.8822125 ratio
                # 0.992592 ratio
                # 0.998997 ratio
                # 0.980209 ratio
            },
            'RELATIVE_THROTTLE_POS': {
                'Request': '^0145' + ELM_MAX_RESP,
                'Descr': 'Relative throttle position',
                'Header': ECU_ADDR_E,
                'Response': [
                            ECU_R_ADDR_E + ' 03 41 45 11 \r',
                            ECU_R_ADDR_E + ' 03 41 45 14 \r',
                            ECU_R_ADDR_E + ' 03 41 45 00 \r',
                            ECU_R_ADDR_E + ' 03 41 45 21 \r'
                            ]
                # 12.9411764706 percent
                # 6.66666666667 percent
                # 7.8431372549 percent
            },
            'THROTTLE_POS_B': {
                'Request': '^0147' + ELM_MAX_RESP,
                'Descr': 'Absolute throttle position B',
                'Header': ECU_ADDR_E,
                'Response': [
                            ECU_R_ADDR_E + ' 03 41 47 CD \r',
                            ECU_R_ADDR_E + ' 03 41 47 89 \r',
                            ECU_R_ADDR_E + ' 03 41 47 7D \r',
                            ECU_R_ADDR_E + ' 03 41 47 7F \r'
                            ]
                # 80.3921568627 percent
                # 49.0196078431 percent
                # 53.7254901961 percent
                # 49.8039215686 percent
            },
            'THROTTLE_ACTUATOR': {
                'Request': '^014C' + ELM_MAX_RESP,
                'Descr': 'Commanded throttle actuator',
                'Header': ECU_ADDR_E,
                'Response': [
                            ECU_R_ADDR_E + ' 03 41 4C 6B \r',
                            ECU_R_ADDR_E + ' 03 41 4C 2C \r',
                            ECU_R_ADDR_E + ' 03 41 4C 2B \r',
                            ECU_R_ADDR_E + ' 03 41 4C 33 \r'
                            ]
                # 16.862745098 percent
                # 17.2549019608 percent
                # 20.0 percent
                # 41.9607843137 percent
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
                'Response': [
                            ECU_R_ADDR_E + ' 04 41 4E 00 00 \r',
                            ECU_R_ADDR_E + ' 04 41 4E 04 C2 \r'
                            ]
                # 1218 minute
            },
            'FUEL_TYPE': {
                'Request': '^0151' + ELM_MAX_RESP,
                'Descr': 'Fuel Type',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 03 41 51 01 \r'
            },
            'DTC_STATUS': {
                'Request': '^0201' + ELM_MAX_RESP,
                'Descr': 'DTC Status since DTCs cleared',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 03 7F 02 12 \r'
            },
            'DTC_FUEL_STATUS': {
                'Request': '^0203' + ELM_MAX_RESP,
                'Descr': 'DTC Fuel System Status',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 03 7F 02 12 \r'
            },
            'DTC_ENGINE_LOAD': {
                'Request': '^0204' + ELM_MAX_RESP,
                'Descr': 'DTC Calculated Engine Load',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 03 7F 02 12 \r'
                # 7.05882352941 percent
            },
            'DTC_COOLANT_TEMP': {
                'Request': '^0205' + ELM_MAX_RESP,
                'Descr': 'DTC Engine Coolant Temperature',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 03 7F 02 12 \r'
                # -22 degC
            },
            'DTC_SHORT_FUEL_TRIM_1': {
                'Request': '^0206' + ELM_MAX_RESP,
                'Descr': 'DTC Short Term Fuel Trim - Bank 1',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 03 7F 02 12 \r'
                # -85.9375 percent
            },
            'DTC_LONG_FUEL_TRIM_1': {
                'Request': '^0207' + ELM_MAX_RESP,
                'Descr': 'DTC Long Term Fuel Trim - Bank 1',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 03 7F 02 12 \r'
                # -85.9375 percent
            },
            'DTC_INTAKE_PRESSURE': {
                'Request': '^020B' + ELM_MAX_RESP,
                'Descr': 'DTC Intake Manifold Pressure',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 03 7F 02 12 \r'
                # 18 kilopascal
            },
            'DTC_RPM': {
                'Request': '^020C' + ELM_MAX_RESP,
                'Descr': 'DTC Engine RPM',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 03 7F 02 12 \r'
                # 1152.0 revolutions_per_minute
            },
            'DTC_SPEED': {
                'Request': '^020D' + ELM_MAX_RESP,
                'Descr': 'DTC Vehicle Speed',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 03 7F 02 12 \r'
                # 18 kph
            },
            'DTC_TIMING_ADVANCE': {
                'Request': '^020E' + ELM_MAX_RESP,
                'Descr': 'DTC Timing Advance',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 03 7F 02 12 \r'
                # -55.0 degree
            },
            'DTC_INTAKE_TEMP': {
                'Request': '^020F' + ELM_MAX_RESP,
                'Descr': 'DTC Intake Air Temp',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 03 7F 02 12 \r'
                # -22 degC
            },
            'DTC_MAF': {
                'Request': '^0210' + ELM_MAX_RESP,
                'Descr': 'DTC Air Flow Rate (MAF)',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 03 7F 02 12 \r'
                # 46.08 gps
            },
            'DTC_THROTTLE_POS': {
                'Request': '^0211' + ELM_MAX_RESP,
                'Descr': 'DTC Throttle Position',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 03 7F 02 12 \r'
                # 7.05882352941 percent
            },
            'DTC_O2_SENSORS': {
                'Request': '^0213' + ELM_MAX_RESP,
                'Descr': 'DTC O2 Sensors Present',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 03 7F 02 12 \r'
            },
            'DTC_O2_B1S2': {
                'Request': '^0215' + ELM_MAX_RESP,
                'Descr': 'DTC O2: Bank 1 - Sensor 2 Voltage',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 03 7F 02 12 \r'
                # 0.09 volt
            },
            'DTC_OBD_COMPLIANCE': {
                'Request': '^021C' + ELM_MAX_RESP,
                'Descr': 'DTC OBD Standards Compliance',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 03 7F 02 12 \r'
            },
            'DTC_RUN_TIME': {
                'Request': '^021F' + ELM_MAX_RESP,
                'Descr': 'DTC Engine Run Time',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 03 7F 02 12 \r'
                # 4608 second
            },
            'DTC_PIDS_B': {
                'Request': '^0220' + ELM_MAX_RESP,
                'Descr': 'DTC Supported PIDs [21-40]',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 03 7F 02 12 \r'
            },
            'DTC_DISTANCE_W_MIL': {
                'Request': '^0221' + ELM_MAX_RESP,
                'Descr': 'DTC Distance Traveled with MIL on',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 03 7F 02 12 \r'
                # 4608 kilometer
            },
            'DTC_O2_S1_WR_VOLTAGE': {
                'Request': '^0224' + ELM_MAX_RESP,
                'Descr': 'DTC 02 Sensor 1 WR Lambda Voltage',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 03 7F 02 12 \r'
            },
            'DTC_COMMANDED_EGR': {
                'Request': '^022C' + ELM_MAX_RESP,
                'Descr': 'DTC Commanded EGR',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 03 7F 02 12 \r'
                # 7.05882352941 percent
            },
            'DTC_EVAPORATIVE_PURGE': {
                'Request': '^022E' + ELM_MAX_RESP,
                'Descr': 'DTC Commanded Evaporative Purge',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 03 7F 02 12 \r'
                # 7.05882352941 percent
            },
            'DTC_WARMUPS_SINCE_DTC_CLEAR': {
                'Request': '^0230' + ELM_MAX_RESP,
                'Descr': 'DTC Number of warm-ups since codes cleared',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 03 7F 02 12 \r'
                # 18 count
            },
            'DTC_DISTANCE_SINCE_DTC_CLEAR': {
                'Request': '^0231' + ELM_MAX_RESP,
                'Descr': 'DTC Distance traveled since codes cleared',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 03 7F 02 12 \r'
                # 4608 kilometer
            },
            'DTC_BAROMETRIC_PRESSURE': {
                'Request': '^0233' + ELM_MAX_RESP,
                'Descr': 'DTC Barometric Pressure',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 03 7F 02 12 \r'
                # 18 kilopascal
            },
            'DTC_O2_S1_WR_CURRENT': {
                'Request': '^0234' + ELM_MAX_RESP,
                'Descr': 'DTC 02 Sensor 1 WR Lambda Current',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 03 7F 02 12 \r'
                # -128.0 milliampere
            },
            'DTC_CATALYST_TEMP_B1S1': {
                'Request': '^023C' + ELM_MAX_RESP,
                'Descr': 'DTC Catalyst Temperature: Bank 1 - Sensor 1',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 03 7F 02 12 \r'
                # 420.8 degC
            },
            'DTC_CATALYST_TEMP_B1S2': {
                'Request': '^023E' + ELM_MAX_RESP,
                'Descr': 'DTC Catalyst Temperature: Bank 1 - Sensor 2',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 03 7F 02 12 \r'
                # 420.8 degC
            },
            'DTC_PIDS_C': {
                'Request': '^0240' + ELM_MAX_RESP,
                'Descr': 'DTC Supported PIDs [41-60]',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 03 7F 02 12 \r'
            },
            'DTC_CONTROL_MODULE_VOLTAGE': {
                'Request': '^0242' + ELM_MAX_RESP,
                'Descr': 'DTC Control module voltage',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 03 7F 02 12 \r'
                # 4.608 volt
            },
            'DTC_ABSOLUTE_LOAD': {
                'Request': '^0243' + ELM_MAX_RESP,
                'Descr': 'DTC Absolute load value',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 03 7F 02 12 \r'
                # 1807.05882353 percent
            },
            'DTC_COMMANDED_EQUIV_RATIO': {
                'Request': '^0244' + ELM_MAX_RESP,
                'Descr': 'DTC Commanded equivalence ratio',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 03 7F 02 12 \r'
                # 0.140544 ratio
            },
            'DTC_RELATIVE_THROTTLE_POS': {
                'Request': '^0245' + ELM_MAX_RESP,
                'Descr': 'DTC Relative throttle position',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 03 7F 02 12 \r'
                # 7.05882352941 percent
            },
            'DTC_THROTTLE_POS_B': {
                'Request': '^0247' + ELM_MAX_RESP,
                'Descr': 'DTC Absolute throttle position B',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 03 7F 02 12 \r'
                # 7.05882352941 percent
            },
            'DTC_THROTTLE_ACTUATOR': {
                'Request': '^024C' + ELM_MAX_RESP,
                'Descr': 'DTC Commanded throttle actuator',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 03 7F 02 12 \r'
                # 7.05882352941 percent
            },
            'DTC_RUN_TIME_MIL': {
                'Request': '^024D' + ELM_MAX_RESP,
                'Descr': 'DTC Time run with MIL on',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 03 7F 02 12 \r'
                # 4608 minute
            },
            'DTC_TIME_SINCE_DTC_CLEARED': {
                'Request': '^024E' + ELM_MAX_RESP,
                'Descr': 'DTC Time since trouble codes cleared',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 03 7F 02 12 \r'
                # 4608 minute
            },
            'DTC_FUEL_TYPE': {
                'Request': '^0251' + ELM_MAX_RESP,
                'Descr': 'DTC Fuel Type',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 03 7F 02 12 \r'
            },
            'GET_DTC': {
                'Request': '^03' + ELM_MAX_RESP,
                'Descr': 'Get DTCs',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 02 43 00 \r'
            },
            'CLEAR_DTC': {
                'Request': '^04' + ELM_MAX_RESP,
                'Descr': 'Clear DTCs and Freeze data',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 01 44 \r'
            },
            'MIDS_A': {
                'Request': '^0600' + ELM_MAX_RESP,
                'Descr': 'Supported MIDs [01-20]',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 06 46 00 C0 00 00 01 \r'
            },
            'MONITOR_O2_B1S1': {
                'Request': '^0601' + ELM_MAX_RESP,
                'Descr': 'O2 Sensor Monitor Bank 1 - Sensor 1',
                'Header': ECU_ADDR_E,
                'Response': [
                            '7E8101346018E0B0280\r7E82100A94DBA01918D\r7E82201A000B4022F00 \r',
                            '7E8101346018E0B0000\r7E8210000000001918D\r7E82200000000000000 \r'
                            ]
            },
            'MONITOR_O2_B1S2': {
                'Request': '^0602' + ELM_MAX_RESP,
                'Descr': 'O2 Sensor Monitor Bank 1 - Sensor 2',
                'Header': ECU_ADDR_E,
                'Response': [
                            '7E8101C4602070B0000\r7E8210000000002080B\r7E82200000000000002\r7E8238F860000000000\r7E82400000000000000 \r',
                            '7E8101C4602070B0088\r7E821000000D602080B\r7E8220334024903E302\r7E8238F86098000001A\r7E824E0000000000000 \r'
                            ]
            },
            'MIDS_B': {
                'Request': '^0620' + ELM_MAX_RESP,
                'Descr': 'Supported MIDs [21-40]',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 06 46 20 80 00 80 01 \r'
            },
            'MONITOR_CATALYST_B1': {
                'Request': '^0621' + ELM_MAX_RESP,
                'Descr': 'Catalyst Monitor Bank 1',
                'Header': ECU_ADDR_E,
                'Response': '7E8100A4621A9860000\r7E82100000000000000 \r'
            },
            'MONITOR_EGR_B1': {
                'Request': '^0631' + ELM_MAX_RESP,
                'Descr': 'EGR Monitor Bank 1',
                'Header': ECU_ADDR_E,
                'Response': '7E8100A4631BD170000\r7E82100000000000000 \r'
            },
            'MIDS_C': {
                'Request': '^0640' + ELM_MAX_RESP,
                'Descr': 'Supported MIDs [41-60]',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 06 46 40 00 00 00 01 \r'
            },
            'MIDS_D': {
                'Request': '^0660' + ELM_MAX_RESP,
                'Descr': 'Supported MIDs [61-80]',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 06 46 60 00 00 00 01 \r'
            },
            'MIDS_E': {
                'Request': '^0680' + ELM_MAX_RESP,
                'Descr': 'Supported MIDs [81-A0]',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 06 46 80 00 00 00 01 \r'
            },
            'MIDS_F': {
                'Request': '^06A0' + ELM_MAX_RESP,
                'Descr': 'Supported MIDs [A1-C0]',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 06 46 A0 F8 00 00 00 \r'
            },
            'MONITOR_MISFIRE_GENERAL': {
                'Request': '^06A1' + ELM_MAX_RESP,
                'Descr': 'Misfire Monitor General Data',
                'Header': ECU_ADDR_E,
                'Response': [
                            '7E8101346A10B240000\r7E82100000000A10C24\r7E82200000000FFFF00 \r',
                            '7E8101346A10B240000\r7E8210000FFFFA10C24\r7E82200000000FFFF00 \r',
                            '7E8101346A10B240000\r7E82100000000A10C24\r7E82200000000000000 \r'
                            ]
            },
            'MONITOR_MISFIRE_CYLINDER_1': {
                'Request': '^06A2' + ELM_MAX_RESP,
                'Descr': 'Misfire Cylinder 1 Data',
                'Header': ECU_ADDR_E,
                'Response': [
                            '7E8101346A20B240000\r7E82100000000A20C24\r7E82200000000FFFF00 \r',
                            '7E8101346A20B240000\r7E82100000000A20C24\r7E82200000000000000 \r',
                            '7E8101346A20B240000\r7E8210000FFFFA20C24\r7E82200000000FFFF00 \r'
                            ]
            },
            'MONITOR_MISFIRE_CYLINDER_2': {
                'Request': '^06A3' + ELM_MAX_RESP,
                'Descr': 'Misfire Cylinder 2 Data',
                'Header': ECU_ADDR_E,
                'Response': [
                            '7E8101346A30B240000\r7E82100000000A30C24\r7E82200000000FFFF00 \r',
                            '7E8101346A30B240000\r7E8210000FFFFA30C24\r7E82200000000FFFF00 \r',
                            '7E8101346A30B240000\r7E82100000000A30C24\r7E82200000000000000 \r'
                            ]
            },
            'MONITOR_MISFIRE_CYLINDER_3': {
                'Request': '^06A4' + ELM_MAX_RESP,
                'Descr': 'Misfire Cylinder 3 Data',
                'Header': ECU_ADDR_E,
                'Response': [
                            '7E8101346A40B240000\r7E82100000000A40C24\r7E82200000000FFFF00 \r',
                            '7E8101346A40B240000\r7E82100000000A40C24\r7E82200000000000000 \r',
                            '7E8101346A40B240000\r7E8210000FFFFA40C24\r7E82200000000FFFF00 \r'
                            ]
            },
            'MONITOR_MISFIRE_CYLINDER_4': {
                'Request': '^06A5' + ELM_MAX_RESP,
                'Descr': 'Misfire Cylinder 4 Data',
                'Header': ECU_ADDR_E,
                'Response': [
                            '7E8101346A50B240000\r7E82100000000A50C24\r7E82200000000000000 \r',
                            '7E8101346A50B240000\r7E8210000FFFFA50C24\r7E82200000000FFFF00 \r',
                            '7E8101346A50B240000\r7E82100000000A50C24\r7E82200000000FFFF00 \r'
                            ]
            },
            'GET_CURRENT_DTC': {
                'Request': '^07' + ELM_MAX_RESP,
                'Descr': 'Get DTCs from the current/last driving cycle',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 02 47 00 \r'
            },
            'CUSTOM_CAL_D_LOAD': {
                'Request': '^2101' + ELM_MAX_RESP,
                'Descr': 'Calculated Load',
                'Equation': 'A * 20 / 51',
                'Min': '0',
                'Max': '100',
                'Unit': '%',
                'Header': ECU_ADDR_E,
                'Response': [
                            '7E8101B6101EC008D06\r7E821C7593861571B86\r7E82210009A1A469F46\r7E8230000000000395F \r',
                            '7E8101B6101EF009806\r7E8219F5737615618F0\r7E82240008A1B439B43\r7E8230000000000394B \r',
                            '7E8101B610100000000\r7E82111633A61560000\r7E8222200C8002B7D2B\r7E8230000000000399A \r',
                            '7E8101B610100000000\r7E82112633961580000\r7E8222400B8002B7D2B\r7E823000000000039AD \r',
                            '7E8101B610100000000\r7E82112633961550000\r7E8222100E6002B7D2C\r7E8230000000000399A \r',
                            '7E8101B610100000000\r7E82111633A61540000\r7E8221D00F5002B7D2C\r7E8230000000000399A \r',
                            '7E8101B6101F7009F08\r7E8219C5B3761571F04\r7E8222800A9224DA84E\r7E8230000000000394B \r',
                            '7E8101B61013C000700\r7E82138123861531181\r7E82233006B00227121\r7E823000000000039AD \r',
                            '7E8101B610100000001\r7E82170483961550000\r7E8221D00D7002B7D2C\r7E823000000000039AD \r',
                            '7E8101B6101C0003801\r7E821F53E386153140B\r7E82219007B002C7E2C\r7E82300000000003973 \r'
                            ]
            },
            'ELM_IGNITION': {
                'Request': '^AT IGN' + ELM_MAX_RESP,
                'Descr': 'IgnMon input level',
                'Header': ECU_ADDR_E,
                'Response': [
                            '? \r',
                            'ON \r'
                            ]
            },
            'ELM_DESCR': {
                'Request': '^AT@1' + ELM_MAX_RESP,
                'Descr': 'Device description',
                'Header': ECU_ADDR_E,
                'Response': [
                            '? \r',
                            'OBDII to RS232 Interpreter \r'
                            ]
            },
            'ELM_ID': {
                'Request': '^AT@2' + ELM_MAX_RESP,
                'Descr': 'Device identifier',
                'Header': ECU_ADDR_E,
                'Response': '? \r'
            },
            'ELM_VERSION': {
                'Request': '^ATI' + ELM_MAX_RESP,
                'Descr': 'ELM327 version string',
                'Header': ECU_ADDR_E,
                'Response': 'ELM327 v1.5 \r'
            },
            'ELM_VOLTAGE': {
                'Request': '^ATRV' + ELM_MAX_RESP,
                'Descr': 'Voltage detected by OBD-II adapter',
                'Header': ECU_ADDR_E,
                'Response': '14.7V \r'
                # 14.7 volt
            },
            'CUSTOM_SOC': {
                'Request': '^015B' + ELM_MAX_RESP,
                'Descr': 'State of Charge',
                'Equation': 'A * 20 / 51',
                'Min': '30',
                'Max': '90',
                'Unit': '%',
                'Header': ECU_ADDR_H,
                'Response': [
                            ECU_R_ADDR_H + ' 03 41 5B A0 \r',
                            ECU_R_ADDR_H + ' 03 41 5B 9E \r',
                            ECU_R_ADDR_H + ' 03 41 5B A1 \r',
                            ECU_R_ADDR_H + ' 03 41 5B 9F \r',
                            ECU_R_ADDR_H + ' 03 41 5B A3 \r'
                            ]
            },
            'CUSTOM_MG1T': {
                'Request': '^2161' + ELM_MAX_RESP,
                'Descr': 'MG1 temperature',
                'Equation': 'A - 40',
                'Min': '-40',
                'Max': '120',
                'Unit': 'C',
                'Header': ECU_ADDR_H,
                'Response': [
                            ECU_R_ADDR_H + ' 07 61 61 3E 3D 3E 89 C0 \r',
                            ECU_R_ADDR_H + ' 07 61 61 42 3D 42 76 F7 \r',
                            ECU_R_ADDR_H + ' 07 61 61 3F 3D 3F 7D 82 \r',
                            ECU_R_ADDR_H + ' 07 61 61 3E 3D 3E 79 16 \r',
                            ECU_R_ADDR_H + ' 07 61 61 41 3D 41 87 FB \r',
                            ECU_R_ADDR_H + ' 07 61 61 41 3D 41 76 38 \r',
                            ECU_R_ADDR_H + ' 07 61 61 41 3D 41 76 98 \r',
                            ECU_R_ADDR_H + ' 07 61 61 3F 3D 3F 8E 5B \r',
                            ECU_R_ADDR_H + ' 07 61 61 3D 3D 3D 83 A1 \r',
                            ECU_R_ADDR_H + ' 07 61 61 40 3D 40 74 82 \r'
                            ]
            },
            'CUSTOM_MG2T': {
                'Request': '^2162' + ELM_MAX_RESP,
                'Descr': 'MG2 temperature',
                'Equation': 'A - 40',
                'Min': '-40',
                'Max': '120',
                'Unit': 'C',
                'Header': ECU_ADDR_H,
                'Response': [
                            ECU_R_ADDR_H + ' 07 61 62 40 3B 40 8E CD \r',
                            ECU_R_ADDR_H + ' 07 61 62 41 3B 41 82 83 \r',
                            ECU_R_ADDR_H + ' 07 61 62 44 3B 44 89 1B \r',
                            ECU_R_ADDR_H + ' 07 61 62 43 3B 43 8B 9D \r',
                            ECU_R_ADDR_H + ' 07 61 62 43 3B 43 89 8B \r',
                            ECU_R_ADDR_H + ' 07 61 62 41 3B 41 92 28 \r',
                            ECU_R_ADDR_H + ' 07 61 62 40 3B 40 86 DE \r',
                            ECU_R_ADDR_H + ' 07 61 62 43 3B 43 89 3D \r',
                            ECU_R_ADDR_H + ' 07 61 62 42 3B 42 8A D2 \r',
                            ECU_R_ADDR_H + ' 07 61 62 44 3B 44 89 F8 \r'
                            ]
            },
            'CUSTOM_MG1_TORQ': {
                'Request': '^2167' + ELM_MAX_RESP,
                'Descr': 'MG1 torque',
                'Equation': '(A * 256 + B) / 8 - 4096',
                'Min': '-4096',
                'Max': '4095.875',
                'Unit': 'Nm',
                'Header': ECU_ADDR_H,
                'Response': [
                            ECU_R_ADDR_H + ' 07 61 67 7E FA 7F 13 00 \r',
                            ECU_R_ADDR_H + ' 07 61 67 80 00 80 01 00 \r',
                            ECU_R_ADDR_H + ' 07 61 67 80 00 80 00 00 \r',
                            ECU_R_ADDR_H + ' 07 61 67 80 00 7F FC 00 \r',
                            ECU_R_ADDR_H + ' 07 61 67 80 00 7F FD 00 \r',
                            ECU_R_ADDR_H + ' 07 61 67 7F A5 7F 87 00 \r',
                            ECU_R_ADDR_H + ' 07 61 67 7F 51 7F 5E 00 \r',
                            ECU_R_ADDR_H + ' 07 61 67 7F 1A 7F 2B 00 \r'
                            ]
            },
            'CUSTOM_INV1T': {
                'Request': '^2170' + ELM_MAX_RESP,
                'Descr': 'Inverter MG1 Temp',
                'Equation': 'A - 40',
                'Min': '15',
                'Max': '150',
                'Unit': 'C',
                'Header': ECU_ADDR_H,
                'Response': [
                            ECU_R_ADDR_H + ' 06 61 70 37 37 43 00 \r',
                            ECU_R_ADDR_H + ' 06 61 70 41 37 43 00 \r',
                            ECU_R_ADDR_H + ' 06 61 70 39 37 40 00 \r',
                            ECU_R_ADDR_H + ' 06 61 70 37 37 43 80 \r'
                            ]
            },
            'CUSTOM_INV2T': {
                'Request': '^2171' + ELM_MAX_RESP,
                'Descr': 'Inverter MG2 Temp',
                'Equation': 'A - 40',
                'Min': '15',
                'Max': '150',
                'Unit': 'C',
                'Header': ECU_ADDR_H,
                'Response': [
                            ECU_R_ADDR_H + ' 06 61 71 3A 37 46 00 \r',
                            ECU_R_ADDR_H + ' 06 61 71 3B 37 46 00 \r',
                            ECU_R_ADDR_H + ' 06 61 71 3E 37 46 00 \r',
                            ECU_R_ADDR_H + ' 06 61 71 37 37 46 00 \r'
                            ]
            },
            'CUSTOM_BC_U': {
                'Request': '^2174' + ELM_MAX_RESP,
                'Descr': 'Boost converter temperature (upper)',
                'Equation': 'A - 40',
                'Min': '15',
                'Max': '150',
                'Unit': 'C',
                'Header': ECU_ADDR_H,
                'Response': [
                            '7EA100B61744F3A3854\r7EA210001F3031F0000 \r',
                            '7EA100B617438373854\r7EA210001BE02B90000 \r',
                            '7EA100B617439373854\r7EA210001C801CB0000 \r',
                            '7EA100B617439413854\r7EA210001A404070000 \r',
                            '7EA100B61743F3C384A\r7EA210001C003E80000 \r',
                            '7EA100B617438373854\r7EA210001BA01B70000 \r',
                            '7EA100B61744339384F\r7EA210001DD03EA0000 \r',
                            '7EA100B61743A373854\r7EA210001DA01DD0000 \r',
                            '7EA100B617438373854\r7EA210001AE03630000 \r',
                            '7EA100B61743C39384F\r7EA210001CC02150000 \r'
                            ]
            },
            'CUSTOM_P_DCDC': {
                'Request': '^2175' + ELM_MAX_RESP,
                'Descr': 'Prohibit DC/DC converter signal',
                'Equation': '{A:6}',
                'Min': '0',
                'Max': '1',
                'Unit': 'Off/On',
                'Header': ECU_ADDR_H,
                'Response': [
                            '7EA10086175200D2F38\r7EA21C5C00000000000 \r',
                            '7EA10086175200D2F39\r7EA21C5800000000000 \r',
                            '7EA10086175200D2F39\r7EA21C5C00000000000 \r',
                            '7EA10086175200D2F3A\r7EA21C5800000000000 \r'
                            ]
            },
            'CUSTOM_INV1_S/D': {
                'Request': '^2178' + ELM_MAX_RESP,
                'Descr': 'MG1 Inverter Shutdown',
                'Equation': '{A:7}',
                'Min': '0',
                'Max': '1',
                'Unit': 'Off/On',
                'Header': ECU_ADDR_H,
                'Response': [
                            ECU_R_ADDR_H + ' 04 61 78 00 00 \r',
                            ECU_R_ADDR_H + ' 04 61 78 80 00 \r'
                            ]
            },
            'CUSTOM_DCTPD': {
                'Request': '^2179' + ELM_MAX_RESP,
                'Descr': 'DCDC Cnv Target Pulse Duty',
                'Equation': '(A * 256 + B) * 399.9 / 65535',
                'Min': '0',
                'Max': '100',
                'Unit': '%',
                'Header': ECU_ADDR_H,
                'Response': ECU_R_ADDR_H + ' 06 61 79 2E 13 0A 00 \r'
            },
            'CUSTOM_MG1_CF': {
                'Request': '^217C' + ELM_MAX_RESP,
                'Descr': 'MG1 Carrier Frequency',
                'Equation': 'A / 20',
                'Min': '0.75',
                'Max': '10',
                'Unit': 'kHz',
                'Header': ECU_ADDR_H,
                'Response': [
                            ECU_R_ADDR_H + ' 04 61 7C 64 32 \r',
                            ECU_R_ADDR_H + ' 04 61 7C 4B 32 \r',
                            ECU_R_ADDR_H + ' 04 61 7C 64 64 \r',
                            ECU_R_ADDR_H + ' 04 61 7C 4B 64 \r'
                            ]
            },
            'CUSTOM_B_RATIO': {
                'Request': '^217D' + ELM_MAX_RESP,
                'Descr': 'Boost Ratio',
                'Equation': 'A / 2',
                'Min': '0',
                'Max': '100',
                'Unit': '%',
                'Header': ECU_ADDR_H,
                'Response': [
                            ECU_R_ADDR_H + ' 05 61 7D 69 00 00 \r',
                            ECU_R_ADDR_H + ' 05 61 7D 71 05 00 \r',
                            ECU_R_ADDR_H + ' 05 61 7D 6C 05 00 \r',
                            ECU_R_ADDR_H + ' 05 61 7D 00 00 00 \r',
                            ECU_R_ADDR_H + ' 05 61 7D 48 00 00 \r',
                            ECU_R_ADDR_H + ' 05 61 7D 73 00 00 \r',
                            ECU_R_ADDR_H + ' 05 61 7D 2B 00 00 \r'
                            ]
            },
            'CUSTOM_V01': {
                'Request': '^2181' + ELM_MAX_RESP,
                'Descr': 'Battery Block Voltage -V01',
                'Equation': '(A * 256 + B) * 79.99 / 65535',
                'Min': '12',
                'Max': '20',
                'Unit': 'V',
                'Header': ECU_ADDR_H,
                'Response': [
                            '7EA10226181341033CE\r7EA2133BE33AE33AE33\r7EA22AE3385336C3385\r7EA23338533BE33CE33\r7EA24AE33E7AF4B08D4 \r',
                            '7EA10226181341033CE\r7EA2133CE33AE33AE33\r7EA22AE33AE339533AE\r7EA2333AE33BE33BE33\r7EA24F73420AF4B08DE \r',
                            '7EA1022618131CA31A1\r7EA21321C3204321C32\r7EA221C3168316831CA\r7EA2331C23168316831\r7EA24B231B2AF3B088E \r',
                            '7EA10226181361435DB\r7EA2135DB35CA35B235\r7EA22A135B235B235B2\r7EA2335A135DB35DB35\r7EA24DB362DAF4B092E \r',
                            '7EA1022618131B23191\r7EA2131CA31A1319131\r7EA227831B231B23191\r7EA23319931B231B231\r7EA24A131B2AF4B087A \r',
                            '7EA10226181363D35DB\r7EA2135DB35DB358935\r7EA2278358935893578\r7EA2335683589358936\r7EA24043656AF4B0924 \r',
                            '7EA1022618134AC3449\r7EA21341033E7343934\r7EA2220342034103420\r7EA2334393439343933\r7EA24F73439AF4B08F2 \r',
                            '7EA10226181344933F7\r7EA2133F733E733CE33\r7EA22CE33E733E733F7\r7EA23340033F733F734\r7EA24203449AF4B08DE \r',
                            '7EA10226181312630FD\r7EA2130ED30ED30DD30\r7EA22C4313F313F30FD\r7EA23310E313F312630\r7EA24DD30EDAF2B0866 \r',
                            '7EA1022618132663256\r7EA21328F328F32E132\r7EA22E132B832A732E1\r7EA2332D932B832B833\r7EA240A3333AF3B0898 \r'
                            ]
            },
            'CUSTOM_TB_INTAKE': {
                'Request': '^2187' + ELM_MAX_RESP,
                'Descr': 'HV battery intake air temperature',
                'Equation': '(A * 256 + B) * 255.9 / 65535 - 50',
                'Min': '-50',
                'Max': '60',
                'Unit': 'C',
                'Header': ECU_ADDR_H,
                'Response': [
                            '7EA100A61874217479E\r7EA214B28474F000000 \r',
                            '7EA100A618741E347D4\r7EA214B424785000000 \r',
                            '7EA100A618741E347EE\r7EA214B5E479E000000 \r',
                            '7EA100A6187424C476B\r7EA214B0C4735000000 \r',
                            '7EA100A618741E3480A\r7EA214B78479E000000 \r',
                            '7EA100A618742304785\r7EA214B0C474F000000 \r',
                            '7EA100A618741FD47BA\r7EA214B28476B000000 \r',
                            '7EA100A618741E34823\r7EA214B9447BA000000 \r',
                            '7EA100A618741FD4859\r7EA214BAE47EE000000 \r',
                            '7EA100A618741E3483D\r7EA214B9447D4000000 \r'
                            ]
            },
            'CUSTOM_IB': {
                'Request': '^218A' + ELM_MAX_RESP,
                'Descr': 'Power Resource IB',
                'Equation': '(A * 256 + B) / 100 - 327.68',
                'Min': '-200',
                'Max': '200',
                'Unit': 'Amperes',
                'Header': ECU_ADDR_H,
                'Response': [
                            ECU_R_ADDR_H + ' 06 61 8A 89 21 00 00 \r',
                            ECU_R_ADDR_H + ' 06 61 8A 7F C6 00 00 \r',
                            ECU_R_ADDR_H + ' 06 61 8A 7E 70 00 00 \r',
                            ECU_R_ADDR_H + ' 06 61 8A 8E 49 00 00 \r',
                            ECU_R_ADDR_H + ' 06 61 8A 7F 33 00 00 \r',
                            ECU_R_ADDR_H + ' 06 61 8A 7B 62 00 00 \r',
                            ECU_R_ADDR_H + ' 06 61 8A 7C E9 00 00 \r',
                            ECU_R_ADDR_H + ' 06 61 8A 7F F7 00 00 \r',
                            ECU_R_ADDR_H + ' 06 61 8A 80 BA 00 00 \r'
                            ]
            },
            'CUSTOM_C_FAN_0': {
                'Request': '^218E' + ELM_MAX_RESP,
                'Descr': 'Cooling Fan 0',
                'Equation': 'A / 2',
                'Min': '0',
                'Max': '100',
                'Unit': '%',
                'Header': ECU_ADDR_H,
                'Response': ECU_R_ADDR_H + ' 04 61 8E 00 80 \r'
            },
            'CUSTOM_VMIN': {
                'Request': '^2192' + ELM_MAX_RESP,
                'Descr': 'Battery block minimum voltage',
                'Equation': '(A * 256 + B) * 79.99 / 65535',
                'Min': '12',
                'Max': '20',
                'Unit': 'V',
                'Header': ECU_ADDR_H,
                'Response': [
                            '7EA1011619235890536\r7EA2114000E00000000\r7EA2200000000000000 \r',
                            '7EA1011619234830735\r7EA21160D0E00000000\r7EA2200000000000000 \r',
                            '7EA1011619233CE0434\r7EA2183000E00000000\r7EA2200000000000000 \r',
                            '7EA10116192322D0532\r7EA218F000E00000000\r7EA2200000000000000 \r',
                            '7EA1011619235890536\r7EA212D0D0E00000000\r7EA2200000000000000 \r',
                            '7EA1011619233CE0534\r7EA21620D0E00000000\r7EA2200000000000000 \r',
                            '7EA1011619233F70434\r7EA219B0D0E00000000\r7EA2200000000000000 \r',
                            '7EA1011619233850734\r7EA2110000E00000000\r7EA2200000000000000 \r',
                            '7EA1011619231DB0432\r7EA21450D0E00000000\r7EA2200000000000000 \r',
                            '7EA1011619234390334\r7EA21D4000E00000000\r7EA2200000000000000 \r'
                            ]
            },
            'CUSTOM_R01': {
                'Request': '^2195' + ELM_MAX_RESP,
                'Descr': 'Internal Resistance R01',
                'Equation': 'A / 1000',
                'Min': '0',
                'Max': '0.255',
                'Unit': 'ohm',
                'Header': ECU_ADDR_H,
                'Response': '7EA1010619514131413\r7EA2113131313131313\r7EA2213141500000000 \r'
            },
            'CUSTOM_BTY_CURR': {
                'Request': '^2198' + ELM_MAX_RESP,
                'Descr': 'Batt Pack Current Val',
                'Equation': '(A * 256 + B) / 100 - 327.68',
                'Min': '-200',
                'Max': '200',
                'Unit': 'Amperes',
                'Header': ECU_ADDR_H,
                'Response': [
                            '7EA100A61987CD755A7\r7EA21007D8077000000 \r',
                            '7EA100A61988DEA55A7\r7EA21007D8077000000 \r',
                            '7EA100A61987AB056A7\r7EA21007D8077000000 \r',
                            '7EA100A61987B3455A7\r7EA21007D8077000000 \r',
                            '7EA100A619882F355A7\r7EA21007D8077000000 \r',
                            '7EA100A61987C7355A7\r7EA21007D8077000000 \r',
                            '7EA100A61987E4356A7\r7EA21007D7E77000000 \r',
                            '7EA100A6198846056A7\r7EA21007D8077000000 \r',
                            '7EA100A61987F5D56A7\r7EA21007D7D77000000 \r',
                            '7EA100A61987B7156A7\r7EA21007D7E77000000 \r'
                            ]
            },
            'CUSTOM_ECU_MODE': {
                'Request': '^219B' + ELM_MAX_RESP,
                'Descr': 'ECU Control Mode (Driving control mode=1,Current sensor offset mode=2,External charge control mode=3,Power supply end mode=4)',
                'Equation': 'A',
                'Min': '1',
                'Max': '4',
                'Unit': 'Number',
                'Header': ECU_ADDR_H,
                'Response': [
                            ECU_R_ADDR_H + ' 06 61 9B 00 00 00 D2 \r',
                            ECU_R_ADDR_H + ' 06 61 9B 00 00 00 CD \r',
                            ECU_R_ADDR_H + ' 06 61 9B 00 00 00 D8 \r',
                            ECU_R_ADDR_H + ' 06 61 9B 00 00 00 D4 \r',
                            ECU_R_ADDR_H + ' 06 61 9B 00 00 00 D0 \r',
                            ECU_R_ADDR_H + ' 06 61 9B 00 00 00 D1 \r',
                            ECU_R_ADDR_H + ' 06 61 9B 00 00 00 FF \r'
                            ]
            },
            'CUSTOM_MODEL_CODE': {
                'Request': '^21C1' + ELM_MAX_RESP,
                'Descr': 'Model Code (ZVW3##)',
                'Equation': 'ABCDEFG',
                'Min': '0',
                'Max': '0',
                'Unit': 'Number',
                'Header': ECU_ADDR_H,
                'Response': ECU_R_ADDR_H + ' 03 7F 21 12 \r'
            },
            'CUSTOM_ECU_CODE': {
                'Request': '^21C2' + ELM_MAX_RESP,
                'Descr': 'ECU Code',
                'Equation': 'ABCDE',
                'Min': '0',
                'Max': '0',
                'Unit': 'Number',
                'Header': ECU_ADDR_H,
                'Response': '7EA100F61C230323035\r7EA2130002205040000\r7EA2200010000000000 \r'
            },
            'CUSTOM_#CURR_CODE': {
                'Request': '^21E1' + ELM_MAX_RESP,
                'Descr': 'Number of Current Code',
                'Equation': 'A',
                'Min': '0',
                'Max': '255',
                'Unit': 'Number',
                'Header': ECU_ADDR_H,
                'Response': [
                            '7EA100A61E100000EA1\r7EA212000079C000000 \r',
                            '7EA100A61E100000EA1\r7EA2120000822000000 \r',
                            '7EA100A61E100000EA1\r7EA212000068D000000 \r',
                            '7EA100A61E100000EA1\r7EA21200004F8000000 \r',
                            '7EA100A61E100000EA1\r7EA2120000472000000 \r',
                            '7EA100A61E100000EA1\r7EA2120000715000000 \r',
                            '7EA100A61E100000EA1\r7EA21200003E0000000 \r',
                            '7EA100A61E100000EA1\r7EA21200008AA000000 \r',
                            '7EA100A61E100000EA1\r7EA2120000608000000 \r',
                            '7EA100A61E100000EA1\r7EA2120000580000000 \r'
                            ]
            },
            'CUSTOM_TAIL_CANCEL': {
                'Request': '^2112' + ELM_MAX_RESP,
                'Descr': 'Tail Cancel SW',
                'Equation': '{A:5}',
                'Min': '0',
                'Max': '1',
                'Unit': 'Off/On',
                'Header': ECU_ADDR_I,
                'Response': [
                            '7C81008611200000710\r7C82100000000000000 \r',
                            '7C81008611200000701\r7C82100000000000000 \r',
                            '7C81008611200000712\r7C82100000000000000 \r',
                            '7C81008611200000700\r7C82100000000000000 \r'
                            ]
            },
            'CUSTOM_AUX_B_VOLT': {
                'Request': '^2113' + ELM_MAX_RESP,
                'Descr': '+B Voltage Value',
                'Equation': 'A / 10',
                'Min': '0',
                'Max': '20',
                'Unit': 'V',
                'Header': ECU_ADDR_I,
                'Response': [
                            ECU_R_ADDR_I + ' 03 61 13 96 \r',
                            ECU_R_ADDR_I + ' 03 61 13 95 \r'
                            ]
            },
            'CUSTOM_FUEL_LEVEL': {
                'Request': '^2129' + ELM_MAX_RESP,
                'Descr': 'Fuel Input',
                'Equation': 'A / 2',
                'Min': '0',
                'Max': '50',
                'Unit': 'Liter',
                'Header': ECU_ADDR_I,
                'Response': [
                            ECU_R_ADDR_I + ' 03 61 29 0F \r',
                            ECU_R_ADDR_I + ' 03 61 29 02 \r',
                            ECU_R_ADDR_I + ' 03 61 29 0D \r',
                            ECU_R_ADDR_I + ' 03 61 29 0B \r',
                            ECU_R_ADDR_I + ' 03 61 29 0C \r'
                            ]
            },
            'CUSTOM_OIL_CHG_DIST': {
                'Request': '^2141' + ELM_MAX_RESP,
                'Descr': 'Distance Since Oil Change for U.S.A. (reset)',
                'Equation': 'A * 2514600 / 15625',
                'Min': '0',
                'Max': '41038',
                'Unit': 'km',
                'Header': ECU_ADDR_I,
                'Response': ECU_R_ADDR_I + ' 03 7F 21 12 \r'
            },
            'CUSTOM_RHEOSTAT': {
                'Request': '^2168' + ELM_MAX_RESP,
                'Descr': 'Rheostat value (dark=0,bright=255)',
                'Equation': 'A',
                'Min': '0',
                'Max': '255',
                'Unit': 'Number',
                'Header': ECU_ADDR_I,
                'Response': ECU_R_ADDR_I + ' 03 7F 21 12 \r'
            },
            'CUSTOM_SBB_QUERY': {
                'Request': '^21A7' + ELM_MAX_RESP,
                'Descr': 'Seat Belt Beep Query (Dis A=0,Ena R=32,Ena P=64,Dis D=96,Ena D=128,Dis P=160,192=Dis R,Ena A=160)',
                'Equation': 'A',
                'Min': '0',
                'Max': '192',
                'Unit': 'Number',
                'Header': ECU_ADDR_I,
                'Response': ECU_R_ADDR_I + ' 03 61 A7 20 \r'
            },
            'CUSTOM_RB_QUERY': {
                'Request': '^21AC' + ELM_MAX_RESP,
                'Descr': 'Reverse Beep Query (Ena=0,Dis=64)',
                'Equation': 'A',
                'Min': '0',
                'Max': '64',
                'Unit': 'Number',
                'Header': ECU_ADDR_I,
                'Response': ECU_R_ADDR_I + ' 03 61 AC 40 \r'
            },
            'CUSTOM_ROOM': {
                'Request': '^2121' + ELM_MAX_RESP,
                'Descr': 'Room Temp Sensor',
                'Equation': 'A * 63.75 / 255 - 6.5',
                'Min': '-6.5',
                'Max': '57.25',
                'Unit': 'C',
                'Header': ECU_ADDR_P,
                'Response': [
                            ECU_R_ADDR_P + ' 03 61 21 57 \r',
                            ECU_R_ADDR_P + ' 03 61 21 5D \r',
                            ECU_R_ADDR_P + ' 03 61 21 59 \r',
                            ECU_R_ADDR_P + ' 03 61 21 5C \r',
                            ECU_R_ADDR_P + ' 03 61 21 5A \r',
                            ECU_R_ADDR_P + ' 03 61 21 60 \r',
                            ECU_R_ADDR_P + ' 03 61 21 5E \r'
                            ]
            },
            'CUSTOM_AMBIENT': {
                'Request': '^2122' + ELM_MAX_RESP,
                'Descr': 'Ambient Temp Sensor',
                'Equation': 'A * 89.25 / 255 - 23.3',
                'Min': '-23.3',
                'Max': '65.95',
                'Unit': 'C',
                'Header': ECU_ADDR_P,
                'Response': [
                            ECU_R_ADDR_P + ' 03 61 22 59 \r',
                            ECU_R_ADDR_P + ' 03 61 22 57 \r',
                            ECU_R_ADDR_P + ' 03 61 22 5B \r',
                            ECU_R_ADDR_P + ' 03 61 22 5A \r',
                            ECU_R_ADDR_P + ' 03 61 22 58 \r'
                            ]
            },
            'CUSTOM_SOLAR_D': {
                'Request': '^2124' + ELM_MAX_RESP,
                'Descr': 'Solar Sensor (D side)',
                'Equation': 'A',
                'Min': '0',
                'Max': '255',
                'Unit': 'Number',
                'Header': ECU_ADDR_P,
                'Response': [
                            ECU_R_ADDR_P + ' 03 61 24 06 \r',
                            ECU_R_ADDR_P + ' 03 61 24 08 \r',
                            ECU_R_ADDR_P + ' 03 61 24 07 \r'
                            ]
            },
            'CUSTOM_COOLANT': {
                'Request': '^2126' + ELM_MAX_RESP,
                'Descr': 'Engine Coolant Temp',
                'Equation': 'A * 89.25 / 255 + 1.3',
                'Min': '1.3',
                'Max': '90.55',
                'Unit': 'C',
                'Header': ECU_ADDR_P,
                'Response': [
                            ECU_R_ADDR_P + ' 03 61 26 77 \r',
                            ECU_R_ADDR_P + ' 03 61 26 7F \r',
                            ECU_R_ADDR_P + ' 03 61 26 83 \r',
                            ECU_R_ADDR_P + ' 03 61 26 88 \r',
                            ECU_R_ADDR_P + ' 03 61 26 85 \r',
                            ECU_R_ADDR_P + ' 03 61 26 7C \r',
                            ECU_R_ADDR_P + ' 03 61 26 80 \r',
                            ECU_R_ADDR_P + ' 03 61 26 7D \r'
                            ]
            },
            'CUSTOM_BLOWER_LEVEL': {
                'Request': '^213C' + ELM_MAX_RESP,
                'Descr': 'Blower Motor Speed Level',
                'Equation': 'A * 31 / 255',
                'Min': '0',
                'Max': '31',
                'Unit': 'Number',
                'Header': ECU_ADDR_P,
                'Response': [
                            ECU_R_ADDR_P + ' 03 61 3C 0C \r',
                            ECU_R_ADDR_P + ' 03 61 3C 0B \r',
                            ECU_R_ADDR_P + ' 03 61 3C 07 \r',
                            ECU_R_ADDR_P + ' 03 61 3C 09 \r',
                            ECU_R_ADDR_P + ' 03 61 3C 0A \r'
                            ]
            },
            'CUSTOM_ADJAMBIENT': {
                'Request': '^213D' + ELM_MAX_RESP,
                'Descr': 'Adjusted Ambient Temp',
                'Equation': 'A * 81.6 / 255 - 30.8',
                'Min': '-30.8',
                'Max': '50.8',
                'Unit': 'C',
                'Header': ECU_ADDR_P,
                'Response': [
                            ECU_R_ADDR_P + ' 03 61 3D 78 \r',
                            ECU_R_ADDR_P + ' 03 61 3D 7B \r',
                            ECU_R_ADDR_P + ' 03 61 3D 79 \r',
                            ECU_R_ADDR_P + ' 03 61 3D 7A \r',
                            ECU_R_ADDR_P + ' 03 61 3D 7C \r'
                            ]
            },
            'CUSTOM_A/O_SP_D': {
                'Request': '^2143' + ELM_MAX_RESP,
                'Descr': 'Air Outlet Servo Pulse (D)',
                'Equation': 'A',
                'Min': '0',
                'Max': '255',
                'Unit': 'Number',
                'Header': ECU_ADDR_P,
                'Response': ECU_R_ADDR_P + ' 06 61 43 09 09 00 00 \r'
            },
            'CUSTOM_A/I_DTP': {
                'Request': '^2144' + ELM_MAX_RESP,
                'Descr': 'Air Inlet Damper Targ Pulse',
                'Equation': 'A',
                'Min': '0',
                'Max': '255',
                'Unit': 'Number',
                'Header': ECU_ADDR_P,
                'Response': ECU_R_ADDR_P + ' 06 61 44 07 07 00 00 \r'
            },
            'CUSTOM_COMP_SPD': {
                'Request': '^2149' + ELM_MAX_RESP,
                'Descr': 'Compressor Speed',
                'Equation': 'A * 256 + B',
                'Min': '0',
                'Max': '10000',
                'Unit': 'RPM',
                'Header': ECU_ADDR_P,
                'Response': ECU_R_ADDR_P + ' 04 61 49 00 00 \r'
            },
            'CUSTOM_COMP_T_SPD': {
                'Request': '^214A' + ELM_MAX_RESP,
                'Descr': 'Compressor Target Speed',
                'Equation': 'A * 256 + B',
                'Min': '0',
                'Max': '10000',
                'Unit': 'RPM',
                'Header': ECU_ADDR_P,
                'Response': ECU_R_ADDR_P + ' 04 61 4A 00 00 \r'
            },
            'CUSTOM_EVAP_FIN': {
                'Request': '^214B' + ELM_MAX_RESP,
                'Descr': 'Evaporator Fin Thermistor',
                'Equation': 'A * 89.25 / 255 - 29.7',
                'Min': '-29.7',
                'Max': '59.55',
                'Unit': 'C',
                'Header': ECU_ADDR_P,
                'Response': [
                            ECU_R_ADDR_P + ' 03 61 4B 79 \r',
                            ECU_R_ADDR_P + ' 03 61 4B 76 \r',
                            ECU_R_ADDR_P + ' 03 61 4B 75 \r',
                            ECU_R_ADDR_P + ' 03 61 4B 77 \r',
                            ECU_R_ADDR_P + ' 03 61 4B 7B \r'
                            ]
            },
            'CUSTOM_EVAP_TGT': {
                'Request': '^214C' + ELM_MAX_RESP,
                'Descr': 'Evaporator Target Temp',
                'Equation': '(A * 256 + B) / 100 - 327.68',
                'Min': '-29.7',
                'Max': '59.55',
                'Unit': 'C',
                'Header': ECU_ADDR_P,
                'Response': ECU_R_ADDR_P + ' 04 61 4C 84 4C \r'
            },
            'CUSTOM_REG_PRES': {
                'Request': '^2153' + ELM_MAX_RESP,
                'Descr': 'Regulator Pressure Sensor',
                'Equation': 'A * 3.75105 / 255 - 0.45668',
                'Min': '-0.45668',
                'Max': '3.29437',
                'Unit': 'MPaG',
                'Header': ECU_ADDR_P,
                'Response': [
                            ECU_R_ADDR_P + ' 03 61 53 37 \r',
                            ECU_R_ADDR_P + ' 03 61 53 38 \r',
                            ECU_R_ADDR_P + ' 03 61 53 36 \r'
                            ]
            },
            'CUSTOM_FR_WS': {
                'Request': '^2103' + ELM_MAX_RESP,
                'Descr': 'FR Wheel Speed',
                'Equation': 'A * 32 / 25',
                'Min': '0',
                'Max': '200',
                'Unit': 'km/h',
                'Header': ECU_ADDR_S,
                'Response': [
                            ECU_R_ADDR_S + ' 06 61 03 20 20 20 1F \r',
                            ECU_R_ADDR_S + ' 06 61 03 16 16 16 16 \r',
                            ECU_R_ADDR_S + ' 06 61 03 0E 0D 0D 0D \r',
                            ECU_R_ADDR_S + ' 06 61 03 14 14 14 14 \r',
                            ECU_R_ADDR_S + ' 06 61 03 1C 1C 1C 1C \r',
                            ECU_R_ADDR_S + ' 06 61 03 27 27 27 27 \r',
                            ECU_R_ADDR_S + ' 06 61 03 32 32 32 32 \r',
                            ECU_R_ADDR_S + ' 06 61 03 1B 1B 1B 1B \r',
                            ECU_R_ADDR_S + ' 06 61 03 1A 1A 1A 1A \r',
                            ECU_R_ADDR_S + ' 06 61 03 17 16 17 17 \r'
                            ]
            },
            'CUSTOM_YR1': {
                'Request': '^2106' + ELM_MAX_RESP,
                'Descr': 'Yaw Rate Sensor',
                'Equation': 'A - 128',
                'Min': '-128',
                'Max': '127',
                'Unit': 'degrees/s',
                'Header': ECU_ADDR_S,
                'Response': [
                            ECU_R_ADDR_S + ' 06 61 06 7F 7F 7F F1 \r',
                            ECU_R_ADDR_S + ' 06 61 06 7E 7E 7F 4C \r',
                            ECU_R_ADDR_S + ' 06 61 06 80 80 80 0F \r',
                            ECU_R_ADDR_S + ' 06 61 06 80 80 80 3C \r',
                            ECU_R_ADDR_S + ' 06 61 06 7F 7F 7F E2 \r',
                            ECU_R_ADDR_S + ' 06 61 06 85 85 80 E1 \r',
                            ECU_R_ADDR_S + ' 06 61 06 80 80 80 2D \r',
                            ECU_R_ADDR_S + ' 06 61 06 80 80 80 1E \r'
                            ]
            },
            'CUSTOM_WC_PRES': {
                'Request': '^2107' + ELM_MAX_RESP,
                'Descr': 'Wheel Cylinder Pressure Sensor',
                'Equation': 'A / 51',
                'Min': '0',
                'Max': '5',
                'Unit': 'V',
                'Header': ECU_ADDR_S,
                'Response': ECU_R_ADDR_S + ' 03 61 07 19 \r'
            },
            'CUSTOM_LATERAL_G': {
                'Request': '^2147' + ELM_MAX_RESP,
                'Descr': 'Lateral G',
                'Equation': 'A * 50.02 / 255 - 25.11',
                'Min': '-25.11',
                'Max': '24.91',
                'Unit': 'm/s2',
                'Header': ECU_ADDR_S,
                'Response': [
                            ECU_R_ADDR_S + ' 07 61 47 F8 00 7C 7E FD \r',
                            ECU_R_ADDR_S + ' 07 61 47 00 FE 80 80 15 \r',
                            ECU_R_ADDR_S + ' 07 61 47 11 00 98 84 B3 \r',
                            ECU_R_ADDR_S + ' 07 61 47 00 FE 80 80 00 \r',
                            ECU_R_ADDR_S + ' 07 61 47 00 00 81 80 4B \r',
                            ECU_R_ADDR_S + ' 07 61 47 00 E8 7F 7F C7 \r',
                            ECU_R_ADDR_S + ' 07 61 47 00 07 80 7F F1 \r',
                            ECU_R_ADDR_S + ' 07 61 47 FF 05 7F 7F D8 \r',
                            ECU_R_ADDR_S + ' 07 61 47 00 00 80 80 01 \r',
                            ECU_R_ADDR_S + ' 07 61 47 06 03 84 81 2C \r'
                            ]
            },
            'CUSTOM_REGENCOOP': {
                'Request': '^2158' + ELM_MAX_RESP,
                'Descr': 'Regen Cooperation',
                'Equation': '{A:7}',
                'Min': '0',
                'Max': '1',
                'Unit': 'Off/On',
                'Header': ECU_ADDR_S,
                'Response': [
                            ECU_R_ADDR_S + ' 03 61 58 80 \r',
                            ECU_R_ADDR_S + ' 03 61 58 00 \r'
                            ]
            },
            'CUSTOM_SLA_CURR': {
                'Request': '^21A3' + ELM_MAX_RESP,
                'Descr': 'SLA Solenoid Current',
                'Equation': 'A * 3 / 255',
                'Min': '0',
                'Max': '3',
                'Unit': 'A',
                'Header': ECU_ADDR_S,
                'Response': [
                            '7B8100861A300002433\r7B8214A4B0000000000 \r',
                            '7B8100861A300602433\r7B8214A4A0000000000 \r',
                            '7B8100861A300002433\r7B82100000000000000 \r'
                            ]
            },
            'CUSTOM_INSP_MODE': {
                'Request': '^21A6' + ELM_MAX_RESP,
                'Descr': 'Inspection Mode (Other=Off,Inspect=On)',
                'Equation': '{A:7}',
                'Min': '0',
                'Max': '1',
                'Unit': 'Off/On',
                'Header': ECU_ADDR_S,
                'Response': ECU_R_ADDR_S + ' 03 61 A6 00 \r'
            },
            'CUSTOM_HAZ_HIST': {
                'Request': '^21BC' + ELM_MAX_RESP,
                'Descr': 'Hazard Switch History (Incomplete=Off,Complete=On)',
                'Equation': '{A:5}',
                'Min': '0',
                'Max': '1',
                'Unit': 'Off/On',
                'Header': ECU_ADDR_S,
                'Response': ECU_R_ADDR_S + ' 03 61 BC 00 \r'
            },
            'CUSTOM_FRS_OPEN': {
                'Request': '^21BE' + ELM_MAX_RESP,
                'Descr': 'FR Speed Open (Normal=0,Error=1)',
                'Equation': '{A:7}',
                'Min': '0',
                'Max': '1',
                'Unit': 'Off/On',
                'Header': ECU_ADDR_S,
                'Response': ECU_R_ADDR_S + ' 05 61 BE 00 00 00 \r'
            },
        },
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
        time.sleep(0.1)
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
            if self.threadState == THREAD.STOPPED:
                return

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
            try:
                c = os.read(self.master_fd, 1).decode()
            except OSError:
                return('')

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
            **self.ObdMessage['default'], # highest priority
            **self.ObdMessage['AT'],
            **self.ObdMessage[self.scenario] # lowest priority ('Priority' to be checked)
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
                    response=val['Response']
                    if isinstance(response, (list, tuple)):
                        response=response[randint(0, len(response)-1)]
                    return (header + response + footer)
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
