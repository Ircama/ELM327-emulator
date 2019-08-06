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

ELM_R_OK = "OK\r"
ELM_MAX_RESP = '[0123456]?$'

# This dictionary uses the ISO 15765-4 CAN 11 bit ID 500 kbaud protocol

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
            'Descr': 'AT TRY PROTO',
            'Log': '"Try protocol %s", cmd[4:]',
            'Response': ELM_R_OK
        },
        'AT_WARM_START': {
            'Request': '^ATWS$',
            'Descr': 'AT WARM START',
            'Log': '"Sleep 0.1 seconds"',
            'Exec': 'self.reset(0.1)',
            'Response': "\r\rELM327 v1.5\r"
        },
        'AT_RESET': {
            'Request': '^ATZ$',
            'Descr': 'AT RESET',
            'Log': '"Sleep 0.5 seconds"',
            'Exec': 'self.reset(0.5)',
            'Response': "\r\rELM327 v1.5\r"
        },
        'AT_SET_TIMEOUT': {
            'Request': '^ATST[0-9A-F][0-9A-F]$',
            'Descr': 'AT SET TIMEOUT',
            'Exec': 'self.counters["cmd_timeout"] = int(cmd[4:], 16)',
            'Log': '"Set timeout %s", cmd[4:]',
            'Response': ELM_R_OK
        },
    },
    # OBD Commands
    'engineoff' : {
        'ELM_PIDS_A': {
            'Request': '^0100$',
            'Descr': 'PIDS_A',
            'ResponseHeader': \
            lambda self, cmd, pid, val: \
                'SEARCHING...\0 time.sleep(4.5) \0\rUNABLE TO CONNECT\r' \
                if self.counters[pid] == 1 else 'NO DATA\r',
            'Response': '',
            'Priority': 5
        },
        'ELM_MIDS_A': {
            'Request': '^0600$',
            'Descr': 'MIDS_A',
            'ResponseHeader': \
            lambda self, cmd, pid, val: \
                'SEARCHING...\0 time.sleep(4.5) \0\rUNABLE TO CONNECT\r' \
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
                ECU_R_ADDR_E + ' 04 41 0C ' \
                + self.Sequence(pid, base=2400, max=200, factor=80, n_bytes=2) \
                + ' \r' + ECU_R_ADDR_H + ' 04 41 0C ' \
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
                ECU_R_ADDR_E + ' 03 41 0D ' \
                + self.Sequence(pid, base=0, max=30, factor=4, n_bytes=1) \
                + ' \r' + ECU_R_ADDR_H + ' 03 41 0D ' \
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
        'FUEL_INJECT_TIMING': {
            'Request': '^015D' + ELM_MAX_RESP,
            'Descr': 'Fuel injection timing',
            'Header': ECU_ADDR_E,
            'Response': ECU_R_ADDR_E + ' 04 41 5D 66 00 \r'
        },
        # Supported PIDs for protocols
        'ELM_PIDS_A': {
            'Request': '^0100' + ELM_MAX_RESP,
            'Descr': 'PIDS_A',
            'ResponseHeader': \
            lambda self, cmd, pid, val: \
                'SEARCHING...\0 time.sleep(3) \0\r' if self.counters[pid] == 1 else "",
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
        },
        'ELM_PIDS_9A': {
            'Request': '^0900' + ELM_MAX_RESP,
            'Descr': 'PIDS_9A',
            'Response': ECU_R_ADDR_E + ' 06 49 00 FF FF FF FF \r'
        },
        'VIN_MESSAGE_COUNT': {
            'Request': '^0901' + ELM_MAX_RESP,
            'Descr': 'VIN Message Count',
            'Response': ECU_R_ADDR_E + ' 03 49 01 01 \r'
        },
        'VIN': { # Check this also: https://stackoverflow.com/a/26752855/10598800, https://www.autocheck.com/vehiclehistory/autocheck/en/vinbasics
            'Request': '^0902' + ELM_MAX_RESP,
            'Descr': 'Get Vehicle Identification Number',
            'Response': [
                        ECU_R_ADDR_E + ' 10 14 49 02 01 57 50 30 \r' +
                        ECU_R_ADDR_E + ' 21 5A 5A 5A 39 39 5A 54 \r' +
                        ECU_R_ADDR_E + ' 22 53 33 39 30 30 30 30 \r', # https://www.autodna.com/vin/WP0ZZZ99ZTS390000, https://it.vin-info.com/libro-denuncia/WP0ZZZ99ZTS390000
                        ECU_R_ADDR_E + ' 10 14 49 02 01 4D 41 54 \r' + # https://community.carloop.io/t/how-to-request-vin/153/11
                        ECU_R_ADDR_E + ' 21 34 30 33 30 39 36 42 \r' +
                        ECU_R_ADDR_E + ' 22 4E 4C 30 30 30 30 30 \r'
                        ]
        },
        'CALIBRATION_ID_MESSAGE_COUNT': {
            'Request': '^0903' + ELM_MAX_RESP,
            'Descr': 'Calibration ID message count for PID 04',
            'Response': ECU_R_ADDR_E + ' 03 49 03 01 \r'
        }
    },
    'car': {
    # AT Commands
        'ELM_DP': {
            'Request': '^AT DP' + ELM_MAX_RESP,
            'Descr': 'Current protocol',
            'Header': ECU_ADDR_E,
            'Response': [
                        '? \r',
                        'AUTO, ISO 15765-4 (CAN 11/500) \r'
                        ]
        },
        'ELM_IGNITION': {
            'Request': '^AT IGN' + ELM_MAX_RESP,
            'Descr': 'IgnMon input level',
            'Header': ECU_ADDR_E,
            'Response': [
                        'ON \r',
                        '? \r'
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
    # OBD Commands
    # MODE 1 - returns values for sensors characterised by PID
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
            'Response': ECU_R_ADDR_E + ' 06 41 01 00 07 A1 00 \r'
        },
        'FUEL_STATUS': {
            'Request': '^0103' + ELM_MAX_RESP,
            'Descr': 'Fuel System Status',
            'Header': ECU_ADDR_E,
            'Response': [
                        ECU_R_ADDR_E + ' 04 41 03 00 00 \r',
                        ECU_R_ADDR_E + ' 04 41 03 04 00 \r',
                        ECU_R_ADDR_E + ' 04 41 03 02 00 \r'
                        ]
        },
        'ENGINE_LOAD': {
            'Request': '^0104' + ELM_MAX_RESP,
            'Descr': 'Calculated Engine Load',
            'Header': ECU_ADDR_E,
            'Response': [
                        ECU_R_ADDR_E + ' 03 41 04 FF \r',
                        ECU_R_ADDR_E + ' 03 41 04 57 \r',
                        ECU_R_ADDR_E + ' 03 41 04 96 \r',
                        ECU_R_ADDR_E + ' 03 41 04 00 \r' +
                        ECU_R_ADDR_H + ' 03 41 04 00 \r',
                        ECU_R_ADDR_E + ' 03 41 04 56 \r',
                        ECU_R_ADDR_E + ' 03 41 04 64 \r',
                        ECU_R_ADDR_E + ' 03 41 04 67 \r',
                        ECU_R_ADDR_E + ' 03 41 04 9F \r',
                        ECU_R_ADDR_E + ' 03 41 04 00 \r',
                        ECU_R_ADDR_E + ' 03 41 04 98 \r',
                        ECU_R_ADDR_E + ' 03 41 04 73 \r',
                        ECU_R_ADDR_E + ' 03 41 04 69 \r',
                        ECU_R_ADDR_E + ' 03 41 04 D6 \r',
                        ECU_R_ADDR_E + ' 03 41 04 41 \r'
                        ]
            # 100.0 percent
            # 34.11764705882353 percent
            # 58.8235294117647 percent
            # 33.72549019607843 percent
            # 39.21568627450981 percent
            # 40.3921568627451 percent
            # 62.35294117647059 percent
            # 59.6078431372549 percent
            # 45.09803921568628 percent
            # 41.1764705882353 percent
            # 83.92156862745098 percent
            # 25.49019607843137 percent
        },
        'COOLANT_TEMP': {
            'Request': '^0105' + ELM_MAX_RESP,
            'Descr': 'Engine Coolant Temperature',
            'Header': ECU_ADDR_E,
            'Response': [
                        ECU_R_ADDR_E + ' 03 41 05 5F \r',
                        ECU_R_ADDR_E + ' 03 41 05 44 \r',
                        ECU_R_ADDR_E + ' 03 41 05 4C \r',
                        ECU_R_ADDR_E + ' 03 41 05 64 \r',
                        ECU_R_ADDR_E + ' 03 41 05 55 \r',
                        ECU_R_ADDR_E + ' 03 41 05 5B \r',
                        ECU_R_ADDR_E + ' 03 41 05 48 \r',
                        ECU_R_ADDR_E + ' 03 41 05 45 \r',
                        ECU_R_ADDR_E + ' 03 41 05 56 \r',
                        ECU_R_ADDR_E + ' 03 41 05 50 \r',
                        ECU_R_ADDR_E + ' 03 41 05 54 \r',
                        ECU_R_ADDR_E + ' 03 41 05 42 \r',
                        ECU_R_ADDR_E + ' 03 41 05 66 \r'
                        ]
            # 55 degC
            # 28 degC
            # 36 degC
            # 60 degC
            # 45 degC
            # 51 degC
            # 32 degC
            # 29 degC
            # 46 degC
            # 40 degC
            # 44 degC
            # 26 degC
            # 62 degC
        },
        'SHORT_FUEL_TRIM_1': {
            'Request': '^0106' + ELM_MAX_RESP,
            'Descr': 'Short Term Fuel Trim - Bank 1',
            'Header': ECU_ADDR_E,
            'Response': [
                        ECU_R_ADDR_E + ' 03 41 06 80 \r',
                        ECU_R_ADDR_E + ' 03 41 06 78 \r',
                        ECU_R_ADDR_E + ' 03 41 06 84 \r',
                        ECU_R_ADDR_E + ' 03 41 06 88 \r',
                        ECU_R_ADDR_E + ' 03 41 06 79 \r',
                        ECU_R_ADDR_E + ' 03 41 06 8B \r',
                        ECU_R_ADDR_E + ' 03 41 06 7F \r',
                        ECU_R_ADDR_E + ' 03 41 06 7D \r'
                        ]
            # -6.25 percent
            # 3.125 percent
            # 6.25 percent
            # -5.46875 percent
            # 8.59375 percent
            # -0.78125 percent
            # -2.34375 percent
        },
        'LONG_FUEL_TRIM_1': {
            'Request': '^0107' + ELM_MAX_RESP,
            'Descr': 'Long Term Fuel Trim - Bank 1',
            'Header': ECU_ADDR_E,
            'Response': [
                        ECU_R_ADDR_E + ' 03 41 07 79 \r',
                        ECU_R_ADDR_E + ' 03 41 07 7E \r',
                        ECU_R_ADDR_E + ' 03 41 07 7C \r',
                        ECU_R_ADDR_E + ' 03 41 07 7F \r',
                        ECU_R_ADDR_E + ' 03 41 07 78 \r'
                        ]
            # -5.46875 percent
            # -1.5625 percent
            # -3.125 percent
            # -0.78125 percent
            # -6.25 percent
        },
        'INTAKE_PRESSURE': {
            'Request': '^010B' + ELM_MAX_RESP,
            'Descr': 'Intake Manifold Pressure',
            'Header': ECU_ADDR_E,
            'Response': [
                        ECU_R_ADDR_E + ' 03 41 0B 26 \r',
                        ECU_R_ADDR_E + ' 03 41 0B 35 \r',
                        ECU_R_ADDR_E + ' 03 41 0B 1E \r',
                        ECU_R_ADDR_E + ' 03 41 0B 63 \r',
                        ECU_R_ADDR_E + ' 03 41 0B 28 \r',
                        ECU_R_ADDR_E + ' 03 41 0B 52 \r',
                        ECU_R_ADDR_E + ' 03 41 0B 61 \r',
                        ECU_R_ADDR_E + ' 03 41 0B 60 \r',
                        ECU_R_ADDR_E + ' 03 41 0B 63 \r' +
                        ECU_R_ADDR_H + ' 03 41 0B 63 \r',
                        ECU_R_ADDR_E + ' 03 41 0B 36 \r',
                        ECU_R_ADDR_E + ' 03 41 0B 25 \r',
                        ECU_R_ADDR_E + ' 03 41 0B 14 \r'
                        ]
            # 38 kilopascal
            # 53 kilopascal
            # 30 kilopascal
            # 99 kilopascal
            # 40 kilopascal
            # 82 kilopascal
            # 97 kilopascal
            # 96 kilopascal
            # 99 kilopascal
            # 54 kilopascal
            # 37 kilopascal
            # 20 kilopascal
        },
        'RPM': {
            'Request': '^010C' + ELM_MAX_RESP,
            'Descr': 'Engine RPM',
            'Header': ECU_ADDR_E,
            'Response': [
                        ECU_R_ADDR_E + ' 04 41 0C 14 5F \r',
                        ECU_R_ADDR_E + ' 04 41 0C 00 00 \r',
                        ECU_R_ADDR_E + ' 04 41 0C 41 C2 \r',
                        ECU_R_ADDR_E + ' 04 41 0C 35 CB \r',
                        ECU_R_ADDR_E + ' 04 41 0C 14 46 \r',
                        ECU_R_ADDR_E + ' 04 41 0C 12 87 \r',
                        ECU_R_ADDR_E + ' 04 41 0C 3B 2E \r',
                        ECU_R_ADDR_E + ' 04 41 0C 15 2A \r',
                        ECU_R_ADDR_E + ' 04 41 0C 09 F6 \r',
                        ECU_R_ADDR_E + ' 04 41 0C 23 82 \r',
                        ECU_R_ADDR_E + ' 04 41 0C 26 25 \r',
                        ECU_R_ADDR_E + ' 04 41 0C 18 9F \r',
                        ECU_R_ADDR_E + ' 04 41 0C 13 FB \r',
                        ECU_R_ADDR_E + ' 04 41 0C 3F 7A \r'
                        ]
            # 1303.75 revolutions_per_minute
            # 4208.5 revolutions_per_minute
            # 3442.75 revolutions_per_minute
            # 1297.5 revolutions_per_minute
            # 1185.75 revolutions_per_minute
            # 3787.5 revolutions_per_minute
            # 1354.5 revolutions_per_minute
            # 637.5 revolutions_per_minute
            # 2272.5 revolutions_per_minute
            # 2441.25 revolutions_per_minute
            # 1575.75 revolutions_per_minute
            # 1278.75 revolutions_per_minute
            # 4062.5 revolutions_per_minute
        },
        'SPEED': {
            'Request': '^010D' + ELM_MAX_RESP,
            'Descr': 'Vehicle Speed',
            'Header': ECU_ADDR_E,
            'Response': [
                        ECU_R_ADDR_E + ' 03 41 0D 0A \r',
                        ECU_R_ADDR_E + ' 03 41 0D 37 \r',
                        ECU_R_ADDR_E + ' 03 41 0D 27 \r',
                        ECU_R_ADDR_E + ' 03 41 0D 33 \r',
                        ECU_R_ADDR_E + ' 03 41 0D 00 \r',
                        ECU_R_ADDR_E + ' 03 41 0D 44 \r',
                        ECU_R_ADDR_E + ' 03 41 0D 5C \r',
                        ECU_R_ADDR_E + ' 03 41 0D 1D \r',
                        ECU_R_ADDR_E + ' 03 41 0D 72 \r',
                        ECU_R_ADDR_E + ' 03 41 0D 48 \r',
                        ECU_R_ADDR_E + ' 03 41 0D 20 \r',
                        ECU_R_ADDR_E + ' 03 41 0D 29 \r',
                        ECU_R_ADDR_E + ' 03 41 0D 0E \r'
                        ]
            # 10 kph
            # 55 kph
            # 39 kph
            # 51 kph
            # 68 kph
            # 92 kph
            # 29 kph
            # 114 kph
            # 72 kph
            # 32 kph
            # 41 kph
            # 14 kph
        },
        'TIMING_ADVANCE': {
            'Request': '^010E' + ELM_MAX_RESP,
            'Descr': 'Timing Advance',
            'Header': ECU_ADDR_E,
            'Response': [
                        ECU_R_ADDR_E + ' 03 41 0E 75 \r',
                        ECU_R_ADDR_E + ' 03 41 0E 76 \r',
                        ECU_R_ADDR_E + ' 03 41 0E 8E \r',
                        ECU_R_ADDR_E + ' 03 41 0E A2 \r',
                        ECU_R_ADDR_E + ' 03 41 0E 8F \r',
                        ECU_R_ADDR_E + ' 03 41 0E 99 \r',
                        ECU_R_ADDR_E + ' 03 41 0E 8A \r',
                        ECU_R_ADDR_E + ' 03 41 0E A6 \r',
                        ECU_R_ADDR_E + ' 03 41 0E 95 \r',
                        ECU_R_ADDR_E + ' 03 41 0E 9A \r',
                        ECU_R_ADDR_E + ' 03 41 0E A8 \r',
                        ECU_R_ADDR_E + ' 03 41 0E AB \r'
                        ]
            # -5.5 degree
            # -5.0 degree
            # 7.0 degree
            # 17.0 degree
            # 7.5 degree
            # 12.5 degree
            # 5.0 degree
            # 19.0 degree
            # 10.5 degree
            # 13.0 degree
            # 20.0 degree
            # 21.5 degree
        },
        'INTAKE_TEMP': {
            'Request': '^010F' + ELM_MAX_RESP,
            'Descr': 'Intake Air Temp',
            'Header': ECU_ADDR_E,
            'Response': [
                        ECU_R_ADDR_E + ' 03 41 0F 39 \r',
                        ECU_R_ADDR_E + ' 03 41 0F 3C \r',
                        ECU_R_ADDR_E + ' 03 41 0F 36 \r',
                        ECU_R_ADDR_E + ' 03 41 0F 37 \r',
                        ECU_R_ADDR_E + ' 03 41 0F 34 \r',
                        ECU_R_ADDR_E + ' 03 41 0F 3A \r',
                        ECU_R_ADDR_E + ' 03 41 0F 38 \r',
                        ECU_R_ADDR_E + ' 03 41 0F 35 \r'
                        ]
            # 17 degC
            # 20 degC
            # 14 degC
            # 15 degC
            # 12 degC
            # 18 degC
            # 16 degC
            # 13 degC
        },
        'MAF': {
            'Request': '^0110' + ELM_MAX_RESP,
            'Descr': 'Air Flow Rate (MAF)',
            'Header': ECU_ADDR_E,
            'Response': [
                        ECU_R_ADDR_E + ' 04 41 10 18 1F \r',
                        ECU_R_ADDR_E + ' 04 41 10 01 46 \r',
                        ECU_R_ADDR_E + ' 04 41 10 03 0A \r',
                        ECU_R_ADDR_E + ' 04 41 10 11 5B \r',
                        ECU_R_ADDR_E + ' 04 41 10 00 14 \r',
                        ECU_R_ADDR_E + ' 04 41 10 02 86 \r',
                        ECU_R_ADDR_E + ' 04 41 10 03 05 \r',
                        ECU_R_ADDR_E + ' 04 41 10 10 16 \r',
                        ECU_R_ADDR_E + ' 04 41 10 00 12 \r',
                        ECU_R_ADDR_E + ' 04 41 10 10 05 \r',
                        ECU_R_ADDR_E + ' 04 41 10 01 3B \r',
                        ECU_R_ADDR_E + ' 04 41 10 00 51 \r',
                        ECU_R_ADDR_E + ' 04 41 10 10 20 \r',
                        ECU_R_ADDR_E + ' 04 41 10 04 93 \r'
                        ]
            # 61.75 gps
            # 3.2600000000000002 gps
            # 7.78 gps
            # 44.43 gps
            # 0.2 gps
            # 6.46 gps
            # 7.73 gps
            # 41.18 gps
            # 0.18 gps
            # 41.01 gps
            # 3.15 gps
            # 0.81 gps
            # 41.28 gps
            # 11.71 gps
        },
        'THROTTLE_POS': {
            'Request': '^0111' + ELM_MAX_RESP,
            'Descr': 'Throttle Position',
            'Header': ECU_ADDR_E,
            'Response': [
                        ECU_R_ADDR_E + ' 03 41 11 2B \r',
                        ECU_R_ADDR_E + ' 03 41 11 70 \r',
                        ECU_R_ADDR_E + ' 03 41 11 44 \r',
                        ECU_R_ADDR_E + ' 03 41 11 50 \r',
                        ECU_R_ADDR_E + ' 03 41 11 32 \r',
                        ECU_R_ADDR_E + ' 03 41 11 72 \r',
                        ECU_R_ADDR_E + ' 03 41 11 2E \r',
                        ECU_R_ADDR_E + ' 03 41 11 36 \r',
                        ECU_R_ADDR_E + ' 03 41 11 2A \r',
                        ECU_R_ADDR_E + ' 03 41 11 2F \r'
                        ]
            # 16.862745098039216 percent
            # 43.92156862745098 percent
            # 26.666666666666668 percent
            # 31.372549019607842 percent
            # 19.607843137254903 percent
            # 44.705882352941174 percent
            # 18.03921568627451 percent
            # 21.176470588235293 percent
            # 16.470588235294116 percent
            # 18.431372549019606 percent
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
                        ECU_R_ADDR_E + ' 04 41 15 07 FF \r',
                        ECU_R_ADDR_E + ' 04 41 15 00 FF \r',
                        ECU_R_ADDR_E + ' 04 41 15 84 FF \r',
                        ECU_R_ADDR_E + ' 04 41 15 03 FF \r',
                        ECU_R_ADDR_E + ' 04 41 15 94 FF \r',
                        ECU_R_ADDR_E + ' 04 41 15 2A FF \r',
                        ECU_R_ADDR_E + ' 04 41 15 46 FF \r'
                        ]
            # 0.035 volt
            # 0.66 volt
            # 0.015 volt
            # 0.74 volt
            # 0.21 volt
            # 0.35 volt
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
                        ECU_R_ADDR_E + ' 04 41 1F 00 75 \r',
                        ECU_R_ADDR_E + ' 04 41 1F 00 26 \r',
                        ECU_R_ADDR_E + ' 04 41 1F 00 1A \r',
                        ECU_R_ADDR_E + ' 04 41 1F 00 5F \r',
                        ECU_R_ADDR_E + ' 04 41 1F 00 A1 \r',
                        ECU_R_ADDR_E + ' 04 41 1F 00 96 \r',
                        ECU_R_ADDR_E + ' 04 41 1F 00 80 \r',
                        ECU_R_ADDR_E + ' 04 41 1F 00 3D \r',
                        ECU_R_ADDR_E + ' 04 41 1F 00 0E \r',
                        ECU_R_ADDR_E + ' 04 41 1F 00 00 \r',
                        ECU_R_ADDR_E + ' 04 41 1F 00 53 \r',
                        ECU_R_ADDR_E + ' 04 41 1F 00 8B \r',
                        ECU_R_ADDR_E + ' 04 41 1F 00 32 \r',
                        ECU_R_ADDR_E + ' 04 41 1F 00 48 \r',
                        ECU_R_ADDR_E + ' 04 41 1F 00 6A \r'
                        ]
            # 117 second
            # 38 second
            # 26 second
            # 95 second
            # 161 second
            # 150 second
            # 128 second
            # 61 second
            # 14 second
            # 83 second
            # 139 second
            # 50 second
            # 72 second
            # 106 second
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
                        ECU_R_ADDR_E + ' 06 41 24 7B A8 65 D9 \r',
                        ECU_R_ADDR_E + ' 06 41 24 81 BA 6D 81 \r',
                        ECU_R_ADDR_E + ' 06 41 24 80 4A 6B F1 \r',
                        ECU_R_ADDR_E + ' 06 41 24 80 71 6B F1 \r',
                        ECU_R_ADDR_E + ' 06 41 24 7E 87 69 71 \r',
                        ECU_R_ADDR_E + ' 06 41 24 7F F5 6B 29 \r',
                        ECU_R_ADDR_E + ' 06 41 24 91 2A 7C 31 \r',
                        ECU_R_ADDR_E + ' 06 41 24 7E 28 68 A9 \r',
                        ECU_R_ADDR_E + ' 06 41 24 7E DC 69 99 \r',
                        ECU_R_ADDR_E + ' 06 41 24 82 B4 6E E9 \r',
                        ECU_R_ADDR_E + ' 06 41 24 9D CF 9F FF \r',
                        ECU_R_ADDR_E + ' 06 41 24 84 32 70 29 \r',
                        ECU_R_ADDR_E + ' 06 41 24 7F B5 69 49 \r',
                        ECU_R_ADDR_E + ' 06 41 24 81 46 6C E1 \r'
                        ]
            # 3.1827878233005262 volt
            # 3.422049286640726 volt
            # 3.373220416571298 volt
            # 3.373220416571298 volt
            # 3.295094224460212 volt
            # 3.3488059815365836 volt
            # 3.8810406652933547 volt
            # 3.2706797894254978 volt
            # 3.2999771114671548 volt
            # 3.465995269703212 volt
            # 4.99995422293431 volt
            # 3.505058365758755 volt
            # 3.290211337453269 volt
            # 3.402517738612955 volt
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
            'Response': ECU_R_ADDR_E + ' 03 41 30 04 \r'
            # 4 count
        },
        'DISTANCE_SINCE_DTC_CLEAR': {
            'Request': '^0131' + ELM_MAX_RESP,
            'Descr': 'Distance traveled since codes cleared',
            'Header': ECU_ADDR_E,
            'Response': [
                        ECU_R_ADDR_E + ' 04 41 31 00 32 \r',
                        ECU_R_ADDR_E + ' 04 41 31 00 31 \r',
                        ECU_R_ADDR_E + ' 04 41 31 00 33 \r'
                        ]
            # 50 kilometer
            # 49 kilometer
            # 51 kilometer
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
                        ECU_R_ADDR_E + ' 06 41 34 7A F9 7F F1 \r',
                        ECU_R_ADDR_E + ' 06 41 34 69 9E 7F 9F \r',
                        ECU_R_ADDR_E + ' 06 41 34 7E EB 80 01 \r',
                        ECU_R_ADDR_E + ' 06 41 34 7E 84 80 00 \r',
                        ECU_R_ADDR_E + ' 06 41 34 80 9D 80 07 \r',
                        ECU_R_ADDR_E + ' 06 41 34 7E 17 7F FE \r',
                        ECU_R_ADDR_E + ' 06 41 34 9D CF 81 6D \r',
                        ECU_R_ADDR_E + ' 06 41 34 81 81 80 0B \r',
                        ECU_R_ADDR_E + ' 06 41 34 7A AC 7F EF \r',
                        ECU_R_ADDR_E + ' 06 41 34 99 CC 80 47 \r',
                        ECU_R_ADDR_E + ' 06 41 34 7E 9C 80 00 \r',
                        ECU_R_ADDR_E + ' 06 41 34 7E A1 80 00 \r',
                        ECU_R_ADDR_E + ' 06 41 34 9D CF 81 96 \r',
                        ECU_R_ADDR_E + ' 06 41 34 83 FD 80 14 \r',
                        ECU_R_ADDR_E + ' 06 41 34 74 77 7F CD \r'
                        ]
            # -0.05859375 milliampere
            # -0.37890625 milliampere
            # 0.00390625 milliampere
            # 0.02734375 milliampere
            # -0.0078125 milliampere
            # 1.42578125 milliampere
            # 0.04296875 milliampere
            # -0.06640625 milliampere
            # 0.27734375 milliampere
            # 1.5859375 milliampere
            # 0.078125 milliampere
            # -0.19921875 milliampere
        },
        'CATALYST_TEMP_B1S1': {
            'Request': '^013C' + ELM_MAX_RESP,
            'Descr': 'Catalyst Temperature: Bank 1 - Sensor 1',
            'Header': ECU_ADDR_E,
            'Response': [
                        ECU_R_ADDR_E + ' 04 41 3C 15 9A \r',
                        ECU_R_ADDR_E + ' 04 41 3C 1D 7C \r',
                        ECU_R_ADDR_E + ' 04 41 3C 1C 1C \r',
                        ECU_R_ADDR_E + ' 04 41 3C 04 76 \r',
                        ECU_R_ADDR_E + ' 04 41 3C 0E 43 \r',
                        ECU_R_ADDR_E + ' 04 41 3C 0D 71 \r',
                        ECU_R_ADDR_E + ' 04 41 3C 15 C5 \r',
                        ECU_R_ADDR_E + ' 04 41 3C 15 B3 \r',
                        ECU_R_ADDR_E + ' 04 41 3C 05 82 \r',
                        ECU_R_ADDR_E + ' 04 41 3C 23 0F \r',
                        ECU_R_ADDR_E + ' 04 41 3C 06 9E \r',
                        ECU_R_ADDR_E + ' 04 41 3C 22 36 \r',
                        ECU_R_ADDR_E + ' 04 41 3C 22 E0 \r',
                        ECU_R_ADDR_E + ' 04 41 3C 20 4E \r',
                        ECU_R_ADDR_E + ' 04 41 3C 1C 66 \r'
                        ]
            # 513.0 degC
            # 714.8000000000001 degC
            # 679.6 degC
            # 74.2 degC
            # 325.1 degC
            # 304.1 degC
            # 517.3000000000001 degC
            # 515.5 degC
            # 101.0 degC
            # 857.5 degC
            # 129.4 degC
            # 835.8000000000001 degC
            # 852.8000000000001 degC
            # 787.0 degC
            # 687.0 degC
        },
        'CATALYST_TEMP_B1S2': {
            'Request': '^013E' + ELM_MAX_RESP,
            'Descr': 'Catalyst Temperature: Bank 1 - Sensor 2',
            'Header': ECU_ADDR_E,
            'Response': [
                        ECU_R_ADDR_E + ' 04 41 3E 02 B9 \r',
                        ECU_R_ADDR_E + ' 04 41 3E 09 44 \r',
                        ECU_R_ADDR_E + ' 04 41 3E 06 B7 \r',
                        ECU_R_ADDR_E + ' 04 41 3E 0E 77 \r',
                        ECU_R_ADDR_E + ' 04 41 3E 03 69 \r',
                        ECU_R_ADDR_E + ' 04 41 3E 20 A1 \r',
                        ECU_R_ADDR_E + ' 04 41 3E 18 1B \r',
                        ECU_R_ADDR_E + ' 04 41 3E 15 A0 \r',
                        ECU_R_ADDR_E + ' 04 41 3E 11 3E \r',
                        ECU_R_ADDR_E + ' 04 41 3E 1E 38 \r',
                        ECU_R_ADDR_E + ' 04 41 3E 10 C4 \r',
                        ECU_R_ADDR_E + ' 04 41 3E 20 3F \r',
                        ECU_R_ADDR_E + ' 04 41 3E 02 83 \r',
                        ECU_R_ADDR_E + ' 04 41 3E 16 DD \r',
                        ECU_R_ADDR_E + ' 04 41 3E 1B 27 \r'
                        ]
            # 29.700000000000003 degC
            # 197.20000000000002 degC
            # 131.9 degC
            # 330.3 degC
            # 47.30000000000001 degC
            # 795.3000000000001 degC
            # 577.1 degC
            # 513.6 degC
            # 401.40000000000003 degC
            # 733.6 degC
            # 389.20000000000005 degC
            # 785.5 degC
            # 24.299999999999997 degC
            # 545.3000000000001 degC
            # 655.1 degC
        },
        'PIDS_C': {
            'Request': '^0140' + ELM_MAX_RESP,
            'Descr': 'Supported PIDs [41-60]',
            'Header': ECU_ADDR_E,
            'Response': [
                        ECU_R_ADDR_E + ' 06 41 40 7A 1C 80 00 \r' +
                        ECU_R_ADDR_H + ' 06 41 40 44 CC 00 21 \r',
                        ECU_R_ADDR_E + ' 06 41 40 7A 1C 80 00 \r'
                        ]
        },
        'CONTROL_MODULE_VOLTAGE': {
            'Request': '^0142' + ELM_MAX_RESP,
            'Descr': 'Control module voltage',
            'Header': ECU_ADDR_E,
            'Response': [
                        ECU_R_ADDR_E + ' 04 41 42 39 4B \r',
                        ECU_R_ADDR_E + ' 04 41 42 39 C1 \r',
                        ECU_R_ADDR_E + ' 04 41 42 39 73 \r',
                        ECU_R_ADDR_E + ' 04 41 42 39 5F \r',
                        ECU_R_ADDR_E + ' 04 41 42 39 9A \r',
                        ECU_R_ADDR_E + ' 04 41 42 39 38 \r'
                        ]
            # 14.667 volt
            # 14.785 volt
            # 14.707 volt
            # 14.687000000000001 volt
            # 14.746 volt
            # 14.648 volt
        },
        'ABSOLUTE_LOAD': {
            'Request': '^0143' + ELM_MAX_RESP,
            'Descr': 'Absolute load value',
            'Header': ECU_ADDR_E,
            'Response': [
                        ECU_R_ADDR_E + ' 04 41 43 00 54 \r',
                        ECU_R_ADDR_E + ' 04 41 43 00 3C \r',
                        ECU_R_ADDR_E + ' 04 41 43 00 39 \r',
                        ECU_R_ADDR_E + ' 04 41 43 00 29 \r',
                        ECU_R_ADDR_E + ' 04 41 43 00 BB \r',
                        ECU_R_ADDR_E + ' 04 41 43 00 66 \r',
                        ECU_R_ADDR_E + ' 04 41 43 00 C0 \r',
                        ECU_R_ADDR_E + ' 04 41 43 00 6F \r',
                        ECU_R_ADDR_E + ' 04 41 43 00 1B \r',
                        ECU_R_ADDR_E + ' 04 41 43 00 BE \r',
                        ECU_R_ADDR_E + ' 04 41 43 00 00 \r',
                        ECU_R_ADDR_E + ' 04 41 43 00 55 \r'
                        ]
            # 32.94117647058823 percent
            # 23.52941176470588 percent
            # 22.352941176470587 percent
            # 16.07843137254902 percent
            # 73.33333333333333 percent
            # 40.0 percent
            # 75.29411764705883 percent
            # 43.529411764705884 percent
            # 10.588235294117647 percent
            # 74.50980392156863 percent
            # 33.333333333333336 percent
        },
        'COMMANDED_EQUIV_RATIO': {
            'Request': '^0144' + ELM_MAX_RESP,
            'Descr': 'Commanded equivalence ratio',
            'Header': ECU_ADDR_E,
            'Response': [
                        ECU_R_ADDR_E + ' 04 41 44 7E 71 \r',
                        ECU_R_ADDR_E + ' 04 41 44 7E 82 \r',
                        ECU_R_ADDR_E + ' 04 41 44 7F 20 \r',
                        ECU_R_ADDR_E + ' 04 41 44 80 C5 \r',
                        ECU_R_ADDR_E + ' 04 41 44 7F F2 \r',
                        ECU_R_ADDR_E + ' 04 41 44 75 A8 \r',
                        ECU_R_ADDR_E + ' 04 41 44 7E 07 \r',
                        ECU_R_ADDR_E + ' 04 41 44 62 8C \r',
                        ECU_R_ADDR_E + ' 04 41 44 7E 4E \r'
                        ]
            # 0.9872545 ratio
            # 0.987773 ratio
            # 0.992592 ratio
            # 1.0054325 ratio
            # 0.998997 ratio
            # 0.91866 ratio
            # 0.9840215 ratio
            # 0.769454 ratio
            # 0.9861869999999999 ratio
        },
        'RELATIVE_THROTTLE_POS': {
            'Request': '^0145' + ELM_MAX_RESP,
            'Descr': 'Relative throttle position',
            'Header': ECU_ADDR_E,
            'Response': [
                        ECU_R_ADDR_E + ' 03 41 45 19 \r',
                        ECU_R_ADDR_E + ' 03 41 45 42 \r',
                        ECU_R_ADDR_E + ' 03 41 45 10 \r',
                        ECU_R_ADDR_E + ' 03 41 45 46 \r',
                        ECU_R_ADDR_E + ' 03 41 45 27 \r',
                        ECU_R_ADDR_E + ' 03 41 45 03 \r',
                        ECU_R_ADDR_E + ' 03 41 45 02 \r',
                        ECU_R_ADDR_E + ' 03 41 45 00 \r'
                        ]
            # 9.803921568627452 percent
            # 25.88235294117647 percent
            # 6.2745098039215685 percent
            # 27.45098039215686 percent
            # 15.294117647058824 percent
            # 1.1764705882352942 percent
            # 0.7843137254901961 percent
        },
        'THROTTLE_POS_B': {
            'Request': '^0147' + ELM_MAX_RESP,
            'Descr': 'Absolute throttle position B',
            'Header': ECU_ADDR_E,
            'Response': [
                        ECU_R_ADDR_E + ' 03 41 47 92 \r',
                        ECU_R_ADDR_E + ' 03 41 47 7B \r',
                        ECU_R_ADDR_E + ' 03 41 47 7D \r',
                        ECU_R_ADDR_E + ' 03 41 47 81 \r',
                        ECU_R_ADDR_E + ' 03 41 47 AD \r',
                        ECU_R_ADDR_E + ' 03 41 47 E9 \r',
                        ECU_R_ADDR_E + ' 03 41 47 D3 \r',
                        ECU_R_ADDR_E + ' 03 41 47 95 \r',
                        ECU_R_ADDR_E + ' 03 41 47 85 \r',
                        ECU_R_ADDR_E + ' 03 41 47 7C \r'
                        ]
            # 57.254901960784316 percent
            # 48.23529411764706 percent
            # 49.01960784313726 percent
            # 50.588235294117645 percent
            # 67.84313725490196 percent
            # 91.37254901960785 percent
            # 82.74509803921569 percent
            # 58.431372549019606 percent
            # 52.15686274509804 percent
            # 48.627450980392155 percent
        },
        'THROTTLE_ACTUATOR': {
            'Request': '^014C' + ELM_MAX_RESP,
            'Descr': 'Commanded throttle actuator',
            'Header': ECU_ADDR_E,
            'Response': [
                        ECU_R_ADDR_E + ' 03 41 4C 71 \r',
                        ECU_R_ADDR_E + ' 03 41 4C 33 \r',
                        ECU_R_ADDR_E + ' 03 41 4C 6F \r',
                        ECU_R_ADDR_E + ' 03 41 4C 3D \r',
                        ECU_R_ADDR_E + ' 03 41 4C 74 \r',
                        ECU_R_ADDR_E + ' 03 41 4C 2F \r',
                        ECU_R_ADDR_E + ' 03 41 4C 2A \r',
                        ECU_R_ADDR_E + ' 03 41 4C 6B \r',
                        ECU_R_ADDR_E + ' 03 41 4C 32 \r',
                        ECU_R_ADDR_E + ' 03 41 4C 22 \r',
                        ECU_R_ADDR_E + ' 03 41 4C 2B \r',
                        ECU_R_ADDR_E + ' 03 41 4C 75 \r'
                        ]
            # 44.31372549019608 percent
            # 20.0 percent
            # 43.529411764705884 percent
            # 23.92156862745098 percent
            # 45.490196078431374 percent
            # 18.431372549019606 percent
            # 16.470588235294116 percent
            # 41.96078431372549 percent
            # 19.607843137254903 percent
            # 13.333333333333334 percent
            # 16.862745098039216 percent
            # 45.88235294117647 percent
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
                        ECU_R_ADDR_E + ' 04 41 4E 00 5B \r',
                        ECU_R_ADDR_E + ' 04 41 4E 00 5C \r',
                        ECU_R_ADDR_E + ' 04 41 4E 00 5D \r'
                        ]
            # 91 minute
            # 92 minute
            # 93 minute
        },
        'FUEL_TYPE': {
            'Request': '^0151' + ELM_MAX_RESP,
            'Descr': 'Fuel Type',
            'Header': ECU_ADDR_E,
            'Response': ECU_R_ADDR_E + ' 03 41 51 01 \r'
        },
    # MODE 2 - freeze frame (or instantaneous) data of a fault
        'DTC_STATUS': {
            'Request': '^0201' + ELM_MAX_RESP,
            'Descr': 'DTC Status since DTCs cleared',
            'Header': ECU_ADDR_E,
            'Response': ECU_R_ADDR_E + ' 03 7F 02 12 \r'
            # invalid data returned by diagnostic request (mode 02)
        },
        'DTC_FUEL_STATUS': {
            'Request': '^0203' + ELM_MAX_RESP,
            'Descr': 'DTC Fuel System Status',
            'Header': ECU_ADDR_E,
            'Response': ECU_R_ADDR_E + ' 03 7F 02 12 \r'
            # invalid data returned by diagnostic request (mode 02)
        },
        'DTC_ENGINE_LOAD': {
            'Request': '^0204' + ELM_MAX_RESP,
            'Descr': 'DTC Calculated Engine Load',
            'Header': ECU_ADDR_E,
            'Response': ECU_R_ADDR_E + ' 03 7F 02 12 \r'
            # invalid data returned by diagnostic request (mode 02)
        },
        'DTC_COOLANT_TEMP': {
            'Request': '^0205' + ELM_MAX_RESP,
            'Descr': 'DTC Engine Coolant Temperature',
            'Header': ECU_ADDR_E,
            'Response': ECU_R_ADDR_E + ' 03 7F 02 12 \r'
            # invalid data returned by diagnostic request (mode 02)
        },
        'DTC_SHORT_FUEL_TRIM_1': {
            'Request': '^0206' + ELM_MAX_RESP,
            'Descr': 'DTC Short Term Fuel Trim - Bank 1',
            'Header': ECU_ADDR_E,
            'Response': ECU_R_ADDR_E + ' 03 7F 02 12 \r'
            # invalid data returned by diagnostic request (mode 02)
        },
        'DTC_LONG_FUEL_TRIM_1': {
            'Request': '^0207' + ELM_MAX_RESP,
            'Descr': 'DTC Long Term Fuel Trim - Bank 1',
            'Header': ECU_ADDR_E,
            'Response': ECU_R_ADDR_E + ' 03 7F 02 12 \r'
            # invalid data returned by diagnostic request (mode 02)
        },
        'DTC_INTAKE_PRESSURE': {
            'Request': '^020B' + ELM_MAX_RESP,
            'Descr': 'DTC Intake Manifold Pressure',
            'Header': ECU_ADDR_E,
            'Response': ECU_R_ADDR_E + ' 03 7F 02 12 \r'
            # invalid data returned by diagnostic request (mode 02)
        },
        'DTC_RPM': {
            'Request': '^020C' + ELM_MAX_RESP,
            'Descr': 'DTC Engine RPM',
            'Header': ECU_ADDR_E,
            'Response': ECU_R_ADDR_E + ' 03 7F 02 12 \r'
            # invalid data returned by diagnostic request (mode 02)
        },
        'DTC_SPEED': {
            'Request': '^020D' + ELM_MAX_RESP,
            'Descr': 'DTC Vehicle Speed',
            'Header': ECU_ADDR_E,
            'Response': ECU_R_ADDR_E + ' 03 7F 02 12 \r'
            # invalid data returned by diagnostic request (mode 02)
        },
        'DTC_TIMING_ADVANCE': {
            'Request': '^020E' + ELM_MAX_RESP,
            'Descr': 'DTC Timing Advance',
            'Header': ECU_ADDR_E,
            'Response': ECU_R_ADDR_E + ' 03 7F 02 12 \r'
            # invalid data returned by diagnostic request (mode 02)
        },
        'DTC_INTAKE_TEMP': {
            'Request': '^020F' + ELM_MAX_RESP,
            'Descr': 'DTC Intake Air Temp',
            'Header': ECU_ADDR_E,
            'Response': ECU_R_ADDR_E + ' 03 7F 02 12 \r'
            # invalid data returned by diagnostic request (mode 02)
        },
        'DTC_MAF': {
            'Request': '^0210' + ELM_MAX_RESP,
            'Descr': 'DTC Air Flow Rate (MAF)',
            'Header': ECU_ADDR_E,
            'Response': ECU_R_ADDR_E + ' 03 7F 02 12 \r'
            # invalid data returned by diagnostic request (mode 02)
        },
        'DTC_THROTTLE_POS': {
            'Request': '^0211' + ELM_MAX_RESP,
            'Descr': 'DTC Throttle Position',
            'Header': ECU_ADDR_E,
            'Response': ECU_R_ADDR_E + ' 03 7F 02 12 \r'
            # invalid data returned by diagnostic request (mode 02)
        },
        'DTC_O2_SENSORS': {
            'Request': '^0213' + ELM_MAX_RESP,
            'Descr': 'DTC O2 Sensors Present',
            'Header': ECU_ADDR_E,
            'Response': ECU_R_ADDR_E + ' 03 7F 02 12 \r'
            # invalid data returned by diagnostic request (mode 02)
        },
        'DTC_O2_B1S2': {
            'Request': '^0215' + ELM_MAX_RESP,
            'Descr': 'DTC O2: Bank 1 - Sensor 2 Voltage',
            'Header': ECU_ADDR_E,
            'Response': ECU_R_ADDR_E + ' 03 7F 02 12 \r'
            # invalid data returned by diagnostic request (mode 02)
        },
        'DTC_OBD_COMPLIANCE': {
            'Request': '^021C' + ELM_MAX_RESP,
            'Descr': 'DTC OBD Standards Compliance',
            'Header': ECU_ADDR_E,
            'Response': ECU_R_ADDR_E + ' 03 7F 02 12 \r'
            # invalid data returned by diagnostic request (mode 02)
        },
        'DTC_RUN_TIME': {
            'Request': '^021F' + ELM_MAX_RESP,
            'Descr': 'DTC Engine Run Time',
            'Header': ECU_ADDR_E,
            'Response': ECU_R_ADDR_E + ' 03 7F 02 12 \r'
            # invalid data returned by diagnostic request (mode 02)
        },
        'DTC_PIDS_B': {
            'Request': '^0220' + ELM_MAX_RESP,
            'Descr': 'DTC Supported PIDs [21-40]',
            'Header': ECU_ADDR_E,
            'Response': [
                        'NO DATA \r',
                        ECU_R_ADDR_E + ' 03 7F 02 12 \r'
                        ]
            # invalid data returned by diagnostic request (mode 02)
        },
        'DTC_DISTANCE_W_MIL': {
            'Request': '^0221' + ELM_MAX_RESP,
            'Descr': 'DTC Distance Traveled with MIL on',
            'Header': ECU_ADDR_E,
            'Response': ECU_R_ADDR_E + ' 03 7F 02 12 \r'
            # invalid data returned by diagnostic request (mode 02)
        },
        'DTC_O2_S1_WR_VOLTAGE': {
            'Request': '^0224' + ELM_MAX_RESP,
            'Descr': 'DTC 02 Sensor 1 WR Lambda Voltage',
            'Header': ECU_ADDR_E,
            'Response': ECU_R_ADDR_E + ' 03 7F 02 12 \r'
            # invalid data returned by diagnostic request (mode 02)
        },
        'DTC_COMMANDED_EGR': {
            'Request': '^022C' + ELM_MAX_RESP,
            'Descr': 'DTC Commanded EGR',
            'Header': ECU_ADDR_E,
            'Response': ECU_R_ADDR_E + ' 03 7F 02 12 \r'
            # invalid data returned by diagnostic request (mode 02)
        },
        'DTC_EVAPORATIVE_PURGE': {
            'Request': '^022E' + ELM_MAX_RESP,
            'Descr': 'DTC Commanded Evaporative Purge',
            'Header': ECU_ADDR_E,
            'Response': ECU_R_ADDR_E + ' 03 7F 02 12 \r'
            # invalid data returned by diagnostic request (mode 02)
        },
        'DTC_WARMUPS_SINCE_DTC_CLEAR': {
            'Request': '^0230' + ELM_MAX_RESP,
            'Descr': 'DTC Number of warm-ups since codes cleared',
            'Header': ECU_ADDR_E,
            'Response': [
                        'NO DATA \r',
                        ECU_R_ADDR_E + ' 03 7F 02 12 \r'
                        ]
            # invalid data returned by diagnostic request (mode 02)
        },
        'DTC_DISTANCE_SINCE_DTC_CLEAR': {
            'Request': '^0231' + ELM_MAX_RESP,
            'Descr': 'DTC Distance traveled since codes cleared',
            'Header': ECU_ADDR_E,
            'Response': ECU_R_ADDR_E + ' 03 7F 02 12 \r'
            # invalid data returned by diagnostic request (mode 02)
        },
        'DTC_BAROMETRIC_PRESSURE': {
            'Request': '^0233' + ELM_MAX_RESP,
            'Descr': 'DTC Barometric Pressure',
            'Header': ECU_ADDR_E,
            'Response': ECU_R_ADDR_E + ' 03 7F 02 12 \r'
            # invalid data returned by diagnostic request (mode 02)
        },
        'DTC_O2_S1_WR_CURRENT': {
            'Request': '^0234' + ELM_MAX_RESP,
            'Descr': 'DTC 02 Sensor 1 WR Lambda Current',
            'Header': ECU_ADDR_E,
            'Response': ECU_R_ADDR_E + ' 03 7F 02 12 \r'
            # invalid data returned by diagnostic request (mode 02)
        },
        'DTC_CATALYST_TEMP_B1S1': {
            'Request': '^023C' + ELM_MAX_RESP,
            'Descr': 'DTC Catalyst Temperature: Bank 1 - Sensor 1',
            'Header': ECU_ADDR_E,
            'Response': ECU_R_ADDR_E + ' 03 7F 02 12 \r'
            # invalid data returned by diagnostic request (mode 02)
        },
        'DTC_CATALYST_TEMP_B1S2': {
            'Request': '^023E' + ELM_MAX_RESP,
            'Descr': 'DTC Catalyst Temperature: Bank 1 - Sensor 2',
            'Header': ECU_ADDR_E,
            'Response': ECU_R_ADDR_E + ' 03 7F 02 12 \r'
            # invalid data returned by diagnostic request (mode 02)
        },
        'DTC_PIDS_C': {
            'Request': '^0240' + ELM_MAX_RESP,
            'Descr': 'DTC Supported PIDs [41-60]',
            'Header': ECU_ADDR_E,
            'Response': ECU_R_ADDR_E + ' 03 7F 02 12 \r'
            # invalid data returned by diagnostic request (mode 02)
        },
        'DTC_CONTROL_MODULE_VOLTAGE': {
            'Request': '^0242' + ELM_MAX_RESP,
            'Descr': 'DTC Control module voltage',
            'Header': ECU_ADDR_E,
            'Response': ECU_R_ADDR_E + ' 03 7F 02 12 \r'
            # invalid data returned by diagnostic request (mode 02)
        },
        'DTC_ABSOLUTE_LOAD': {
            'Request': '^0243' + ELM_MAX_RESP,
            'Descr': 'DTC Absolute load value',
            'Header': ECU_ADDR_E,
            'Response': ECU_R_ADDR_E + ' 03 7F 02 12 \r'
            # invalid data returned by diagnostic request (mode 02)
        },
        'DTC_COMMANDED_EQUIV_RATIO': {
            'Request': '^0244' + ELM_MAX_RESP,
            'Descr': 'DTC Commanded equivalence ratio',
            'Header': ECU_ADDR_E,
            'Response': ECU_R_ADDR_E + ' 03 7F 02 12 \r'
            # invalid data returned by diagnostic request (mode 02)
        },
        'DTC_RELATIVE_THROTTLE_POS': {
            'Request': '^0245' + ELM_MAX_RESP,
            'Descr': 'DTC Relative throttle position',
            'Header': ECU_ADDR_E,
            'Response': ECU_R_ADDR_E + ' 03 7F 02 12 \r'
            # invalid data returned by diagnostic request (mode 02)
        },
        'DTC_THROTTLE_POS_B': {
            'Request': '^0247' + ELM_MAX_RESP,
            'Descr': 'DTC Absolute throttle position B',
            'Header': ECU_ADDR_E,
            'Response': ECU_R_ADDR_E + ' 03 7F 02 12 \r'
            # invalid data returned by diagnostic request (mode 02)
        },
        'DTC_THROTTLE_ACTUATOR': {
            'Request': '^024C' + ELM_MAX_RESP,
            'Descr': 'DTC Commanded throttle actuator',
            'Header': ECU_ADDR_E,
            'Response': ECU_R_ADDR_E + ' 03 7F 02 12 \r'
            # invalid data returned by diagnostic request (mode 02)
        },
        'DTC_RUN_TIME_MIL': {
            'Request': '^024D' + ELM_MAX_RESP,
            'Descr': 'DTC Time run with MIL on',
            'Header': ECU_ADDR_E,
            'Response': ECU_R_ADDR_E + ' 03 7F 02 12 \r'
            # invalid data returned by diagnostic request (mode 02)
        },
        'DTC_TIME_SINCE_DTC_CLEARED': {
            'Request': '^024E' + ELM_MAX_RESP,
            'Descr': 'DTC Time since trouble codes cleared',
            'Header': ECU_ADDR_E,
            'Response': ECU_R_ADDR_E + ' 03 7F 02 12 \r'
            # invalid data returned by diagnostic request (mode 02)
        },
        'DTC_FUEL_TYPE': {
            'Request': '^0251' + ELM_MAX_RESP,
            'Descr': 'DTC Fuel Type',
            'Header': ECU_ADDR_E,
            'Response': [
                        'NO DATA \r',
                        ECU_R_ADDR_E + ' 03 7F 02 12 \r'
                        ]
            # invalid data returned by diagnostic request (mode 02)
        },
    # MODE 3 - diagnostic trouble codes
        'GET_DTC': {
            'Request': '^03' + ELM_MAX_RESP,
            'Descr': 'Get DTCs',
            'Header': ECU_ADDR_E,
            'Response': ECU_R_ADDR_E + ' 02 43 00 \r'
        },
    # MODE 6 - results of self-diagnostics
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
            'Response': ECU_R_ADDR_E + ' 10 13 46 01 8E 0B 02 27 \r' +
                        ECU_R_ADDR_E + ' 21 00 A9 4D BA 01 91 8D \r' +
                        ECU_R_ADDR_E + ' 22 01 9D 00 B4 02 2F 00 \r'
        },
        'MONITOR_O2_B1S2': {
            'Request': '^0602' + ELM_MAX_RESP,
            'Descr': 'O2 Sensor Monitor Bank 1 - Sensor 2',
            'Header': ECU_ADDR_E,
            'Response': [
                        ECU_R_ADDR_E + ' 10 1C 46 02 07 0B 00 88 \r' +
                        ECU_R_ADDR_E + ' 21 00 00 00 D6 02 08 0B \r' +
                        ECU_R_ADDR_E + ' 22 02 F9 02 49 03 E3 02 \r' +
                        ECU_R_ADDR_E + ' 23 8F 86 03 C2 00 00 1A \r' +
                        ECU_R_ADDR_E + ' 24 E0 00 00 00 00 00 00 \r',
                        ECU_R_ADDR_E + ' 10 1C 46 02 07 0B 00 88 \r' +
                        ECU_R_ADDR_E + ' 21 00 00 00 D6 02 08 0B \r' +
                        ECU_R_ADDR_E + ' 22 02 F9 02 49 03 E3 02 \r' +
                        ECU_R_ADDR_E + ' 23 8F 86 03 C2 00 00 1A \r'
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
            'Response': ECU_R_ADDR_E + ' 10 0A 46 21 A9 86 02 E5 \r' +
                        ECU_R_ADDR_E + ' 21 02 D0 7F FF 00 00 00 \r'
        },
        'MONITOR_EGR_B1': {
            'Request': '^0631' + ELM_MAX_RESP,
            'Descr': 'EGR Monitor Bank 1',
            'Header': ECU_ADDR_E,
            'Response': ECU_R_ADDR_E + ' 10 0A 46 31 BD 17 07 47 \r' +
                        ECU_R_ADDR_E + ' 21 00 63 FF FF 00 00 00 \r'
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
            'Response': ECU_R_ADDR_E + ' 10 13 46 A1 0B 24 00 00 \r' +
                        ECU_R_ADDR_E + ' 21 00 00 FF FF A1 0C 24 \r' +
                        ECU_R_ADDR_E + ' 22 00 00 00 00 FF FF 00 \r'
        },
        'MONITOR_MISFIRE_CYLINDER_1': {
            'Request': '^06A2' + ELM_MAX_RESP,
            'Descr': 'Misfire Cylinder 1 Data',
            'Header': ECU_ADDR_E,
            'Response': ECU_R_ADDR_E + ' 10 13 46 A2 0B 24 00 00 \r' +
                        ECU_R_ADDR_E + ' 21 00 00 FF FF A2 0C 24 \r' +
                        ECU_R_ADDR_E + ' 22 00 00 00 00 FF FF 00 \r'
        },
        'MONITOR_MISFIRE_CYLINDER_2': {
            'Request': '^06A3' + ELM_MAX_RESP,
            'Descr': 'Misfire Cylinder 2 Data',
            'Header': ECU_ADDR_E,
            'Response': ECU_R_ADDR_E + ' 10 13 46 A3 0B 24 00 00 \r' +
                        ECU_R_ADDR_E + ' 21 00 00 FF FF A3 0C 24 \r' +
                        ECU_R_ADDR_E + ' 22 00 00 00 00 FF FF 00 \r'
        },
        'MONITOR_MISFIRE_CYLINDER_3': {
            'Request': '^06A4' + ELM_MAX_RESP,
            'Descr': 'Misfire Cylinder 3 Data',
            'Header': ECU_ADDR_E,
            'Response': ECU_R_ADDR_E + ' 10 13 46 A4 0B 24 00 00 \r' +
                        ECU_R_ADDR_E + ' 21 00 00 FF FF A4 0C 24 \r' +
                        ECU_R_ADDR_E + ' 22 00 00 00 00 FF FF 00 \r'
        },
        'MONITOR_MISFIRE_CYLINDER_4': {
            'Request': '^06A5' + ELM_MAX_RESP,
            'Descr': 'Misfire Cylinder 4 Data',
            'Header': ECU_ADDR_E,
            'Response': ECU_R_ADDR_E + ' 10 13 46 A5 0B 24 00 00 \r' +
                        ECU_R_ADDR_E + ' 21 00 00 FF FF A5 0C 24 \r' +
                        ECU_R_ADDR_E + ' 22 00 00 00 00 FF FF 00 \r'
        },
    # MODE 7 - unconfirmed fault codes
        'GET_CURRENT_DTC': {
            'Request': '^07' + ELM_MAX_RESP,
            'Descr': 'Get DTCs from the current/last driving cycle',
            'Header': ECU_ADDR_E,
            'Response': ECU_R_ADDR_E + ' 02 47 00 \r'
        },
    # Custom OBD Commands
        "CUSTOM_CAL'D_LOAD": {
            'Request': '^2101' + ELM_MAX_RESP,
            'Descr': 'Calculated Load',
            'Equation': 'A * 20 / 51',
            'Min': '0',
            'Max': '100',
            'Unit': '%',
            'Header': ECU_ADDR_E,
            'Response': [
                        ECU_R_ADDR_E + ' 10 1B 61 01 66 00 29 01 \r' +
                        ECU_R_ADDR_E + ' 21 3B 24 37 61 66 11 26 \r' +
                        ECU_R_ADDR_E + ' 22 53 00 9B 00 2A 7B 2A \r' +
                        ECU_R_ADDR_E + ' 23 04 00 33 00 5D 39 73 \r',
                        ECU_R_ADDR_E + ' 10 1B 61 01 98 00 57 03 \r' +
                        ECU_R_ADDR_E + ' 21 13 35 3A 61 44 14 3D \r' +
                        ECU_R_ADDR_E + ' 22 00 00 13 02 32 85 32 \r' +
                        ECU_R_ADDR_E + ' 23 04 00 31 00 5B 39 38 \r',
                        ECU_R_ADDR_E + ' 10 1B 61 01 A5 00 61 03 \r' +
                        ECU_R_ADDR_E + ' 21 8A 3D 37 61 59 14 EC \r' +
                        ECU_R_ADDR_E + ' 22 4C 00 63 07 33 87 33 \r' +
                        ECU_R_ADDR_E + ' 23 04 00 32 00 5C 39 5F \r',
                        ECU_R_ADDR_E + ' 10 1B 61 01 00 00 00 00 \r' +
                        ECU_R_ADDR_E + ' 21 14 63 38 61 65 00 00 \r' +
                        ECU_R_ADDR_E + ' 22 2D 00 A6 00 2A 7C 2A \r' +
                        ECU_R_ADDR_E + ' 23 04 00 33 00 5D 39 C1 \r',
                        ECU_R_ADDR_E + ' 10 1B 61 01 96 00 55 03 \r' +
                        ECU_R_ADDR_E + ' 21 07 35 3A 61 47 14 65 \r' +
                        ECU_R_ADDR_E + ' 22 09 00 1F 02 32 85 32 \r' +
                        ECU_R_ADDR_E + ' 23 04 00 31 00 5B 39 4B \r',
                        ECU_R_ADDR_E + ' 10 1B 61 01 00 00 25 00 \r' +
                        ECU_R_ADDR_E + ' 21 1D 5C 3E 61 42 00 00 \r' +
                        ECU_R_ADDR_E + ' 22 03 00 05 00 2B 7C 2B \r' +
                        ECU_R_ADDR_E + ' 23 04 00 31 00 5B 39 38 \r',
                        ECU_R_ADDR_E + ' 10 1B 61 01 00 00 00 00 \r' +
                        ECU_R_ADDR_E + ' 21 12 63 3A 61 5B 00 00 \r' +
                        ECU_R_ADDR_E + ' 22 2B 00 6F 00 2B 7D 2B \r' +
                        ECU_R_ADDR_E + ' 23 04 00 32 00 5C 39 AD \r',
                        ECU_R_ADDR_E + ' 10 1B 61 01 71 00 3C 02 \r' +
                        ECU_R_ADDR_E + ' 21 29 29 38 61 55 14 5C \r' +
                        ECU_R_ADDR_E + ' 22 34 00 4D 03 2E 81 2F \r' +
                        ECU_R_ADDR_E + ' 23 04 00 32 00 5C 39 5F \r',
                        ECU_R_ADDR_E + ' 10 1B 61 01 EE 00 94 06 \r' +
                        ECU_R_ADDR_E + ' 21 94 5B 39 61 56 19 6D \r' +
                        ECU_R_ADDR_E + ' 22 1C 00 58 1B 47 9F 47 \r' +
                        ECU_R_ADDR_E + ' 23 04 00 32 00 5C 39 4B \r',
                        ECU_R_ADDR_E + ' 10 1B 61 01 F9 00 BF 12 \r' +
                        ECU_R_ADDR_E + ' 21 D9 60 36 61 5B 38 7E \r' +
                        ECU_R_ADDR_E + ' 22 41 00 7A 46 71 D5 71 \r' +
                        ECU_R_ADDR_E + ' 23 04 00 32 00 5D 39 38 \r',
                        ECU_R_ADDR_E + ' 10 1B 61 01 95 00 54 03 \r' +
                        ECU_R_ADDR_E + ' 21 02 35 38 61 4E 14 78 \r' +
                        ECU_R_ADDR_E + ' 22 16 00 37 02 31 85 31 \r' +
                        ECU_R_ADDR_E + ' 23 04 00 31 00 5B 39 4B \r',
                        ECU_R_ADDR_E + ' 10 1B 61 01 F3 00 B9 12 \r' +
                        ECU_R_ADDR_E + ' 21 B6 5D 35 61 62 39 C6 \r' +
                        ECU_R_ADDR_E + ' 22 69 00 90 43 6E D1 6E \r' +
                        ECU_R_ADDR_E + ' 23 04 00 33 00 5D 39 4B \r',
                        ECU_R_ADDR_E + ' 10 1B 61 01 3E 00 1B 01 \r' +
                        ECU_R_ADDR_E + ' 21 8C 15 38 61 52 20 9A \r' +
                        ECU_R_ADDR_E + ' 22 41 00 42 00 2C 7D 2C \r' +
                        ECU_R_ADDR_E + ' 23 04 00 31 00 5C 39 5F \r',
                        ECU_R_ADDR_E + ' 10 1B 61 01 6F 00 44 02 \r' +
                        ECU_R_ADDR_E + ' 21 C6 28 38 61 4B 17 21 \r' +
                        ECU_R_ADDR_E + ' 22 31 00 2B 01 30 83 31 \r' +
                        ECU_R_ADDR_E + ' 23 04 00 31 00 5B 39 5F \r',
                        ECU_R_ADDR_E + ' 10 1B 61 01 E8 00 AD 0F \r' +
                        ECU_R_ADDR_E + ' 21 EF 59 35 61 5E 34 C8 \r' +
                        ECU_R_ADDR_E + ' 22 59 00 85 2D 58 B5 58 \r' +
                        ECU_R_ADDR_E + ' 23 04 00 32 00 5D 39 4B \r'
                        ]
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
                        ECU_R_ADDR_H + ' 03 41 5B 95 \r',
                        ECU_R_ADDR_H + ' 03 41 5B 97 \r',
                        ECU_R_ADDR_H + ' 03 41 5B 96 \r',
                        ECU_R_ADDR_H + ' 03 41 5B 94 \r',
                        ECU_R_ADDR_H + ' 03 41 5B 99 \r',
                        ECU_R_ADDR_H + ' 03 41 5B 93 \r',
                        ECU_R_ADDR_H + ' 03 41 5B 9E \r',
                        ECU_R_ADDR_H + ' 03 41 5B 92 \r',
                        ECU_R_ADDR_H + ' 03 41 5B 98 \r',
                        ECU_R_ADDR_H + ' 03 41 5B 9A \r'
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
                        ECU_R_ADDR_H + ' 07 61 61 3D 3C 3D 8F 4D \r',
                        ECU_R_ADDR_H + ' 07 61 61 3D 3C 3D 85 8E \r',
                        ECU_R_ADDR_H + ' 07 61 61 3E 3C 3E 7C 2C \r',
                        ECU_R_ADDR_H + ' 07 61 61 3D 3C 3D 87 95 \r',
                        ECU_R_ADDR_H + ' 07 61 61 42 3C 42 79 0E \r',
                        ECU_R_ADDR_H + ' 07 61 61 3F 3C 3F 74 61 \r',
                        ECU_R_ADDR_H + ' 07 61 61 3D 3C 3D 90 0E \r',
                        ECU_R_ADDR_H + ' 07 61 61 40 3C 40 90 0A \r',
                        ECU_R_ADDR_H + ' 07 61 61 40 3C 40 9B 9F \r',
                        ECU_R_ADDR_H + ' 07 61 61 3D 3C 3D 92 86 \r',
                        ECU_R_ADDR_H + ' 07 61 61 41 3C 41 A3 EB \r',
                        ECU_R_ADDR_H + ' 07 61 61 43 3C 43 76 FB \r',
                        ECU_R_ADDR_H + ' 07 61 61 3E 3C 3E 9C 2E \r',
                        ECU_R_ADDR_H + ' 07 61 61 3D 3C 3D 8F BF \r',
                        ECU_R_ADDR_H + ' 07 61 61 3E 3C 3E 87 70 \r'
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
                        ECU_R_ADDR_H + ' 07 61 62 3F 3A 3F 8E 13 \r',
                        ECU_R_ADDR_H + ' 07 61 62 43 3A 43 9F EA \r',
                        ECU_R_ADDR_H + ' 07 61 62 3A 3A 3A 80 99 \r',
                        ECU_R_ADDR_H + ' 07 61 62 40 3A 40 8A 22 \r',
                        ECU_R_ADDR_H + ' 07 61 62 3D 3A 3D 87 FB \r',
                        ECU_R_ADDR_H + ' 07 61 62 44 3A 44 8A F1 \r',
                        ECU_R_ADDR_H + ' 07 61 62 3B 3A 3B 82 6D \r',
                        ECU_R_ADDR_H + ' 07 61 62 3E 3A 3E 91 BC \r',
                        ECU_R_ADDR_H + ' 07 61 62 42 3A 42 95 3E \r',
                        ECU_R_ADDR_H + ' 07 61 62 40 3A 40 95 EC \r',
                        ECU_R_ADDR_H + ' 07 61 62 44 3A 44 97 85 \r',
                        ECU_R_ADDR_H + ' 07 61 62 3A 3A 3A 80 75 \r',
                        ECU_R_ADDR_H + ' 07 61 62 41 3A 41 8C 1B \r',
                        ECU_R_ADDR_H + ' 07 61 62 42 3A 42 9A CD \r',
                        ECU_R_ADDR_H + ' 07 61 62 3C 3A 3C 8D 81 \r'
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
                        ECU_R_ADDR_H + ' 07 61 67 7F FD 7F FA 00 \r',
                        ECU_R_ADDR_H + ' 07 61 67 7F C9 7F C7 00 \r',
                        ECU_R_ADDR_H + ' 07 61 67 80 00 80 00 00 \r',
                        ECU_R_ADDR_H + ' 07 61 67 7F 5A 7F 60 00 \r',
                        ECU_R_ADDR_H + ' 07 61 67 7F E8 7F EB 00 \r',
                        ECU_R_ADDR_H + ' 07 61 67 7F 67 7F 7B 00 \r',
                        ECU_R_ADDR_H + ' 07 61 67 80 00 80 04 00 \r',
                        ECU_R_ADDR_H + ' 07 61 67 7F CF 7F CD 00 \r',
                        ECU_R_ADDR_H + ' 07 61 67 7E E3 7F 04 02 \r',
                        ECU_R_ADDR_H + ' 07 61 67 7E E2 7E F2 01 \r',
                        ECU_R_ADDR_H + ' 07 61 67 80 22 80 1C 00 \r',
                        ECU_R_ADDR_H + ' 07 61 67 7F DD 7F E0 00 \r',
                        ECU_R_ADDR_H + ' 07 61 67 7F AC 7F C6 00 \r',
                        ECU_R_ADDR_H + ' 07 61 67 7F EE 7F ED 02 \r',
                        ECU_R_ADDR_H + ' 07 61 67 80 00 7F FE 00 \r'
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
                        ECU_R_ADDR_H + ' 06 61 70 37 37 41 00 \r',
                        ECU_R_ADDR_H + ' 06 61 70 37 37 39 00 \r',
                        ECU_R_ADDR_H + ' 06 61 70 40 37 41 00 \r',
                        ECU_R_ADDR_H + ' 06 61 70 38 37 47 00 \r',
                        ECU_R_ADDR_H + ' 06 61 70 44 37 44 00 \r',
                        ECU_R_ADDR_H + ' 06 61 70 3C 37 41 00 \r',
                        ECU_R_ADDR_H + ' 06 61 70 41 37 40 00 \r',
                        ECU_R_ADDR_H + ' 06 61 70 3D 37 41 00 \r',
                        ECU_R_ADDR_H + ' 06 61 70 37 37 47 80 \r',
                        ECU_R_ADDR_H + ' 06 61 70 3E 37 41 00 \r',
                        ECU_R_ADDR_H + ' 06 61 70 44 37 47 00 \r',
                        ECU_R_ADDR_H + ' 06 61 70 37 37 37 80 \r'
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
                        ECU_R_ADDR_H + ' 06 61 71 3D 37 46 00 \r',
                        ECU_R_ADDR_H + ' 06 61 71 39 37 3C 00 \r',
                        ECU_R_ADDR_H + ' 06 61 71 37 37 46 00 \r',
                        ECU_R_ADDR_H + ' 06 61 71 3B 37 46 00 \r',
                        ECU_R_ADDR_H + ' 06 61 71 3F 37 46 00 \r',
                        ECU_R_ADDR_H + ' 06 61 71 38 37 46 00 \r',
                        ECU_R_ADDR_H + ' 06 61 71 43 37 46 00 \r',
                        ECU_R_ADDR_H + ' 06 61 71 37 37 39 00 \r'
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
                        ECU_R_ADDR_H + ' 10 0B 61 74 46 39 37 50 \r' +
                        ECU_R_ADDR_H + ' 21 00 01 C8 03 E8 00 00 \r',
                        ECU_R_ADDR_H + ' 10 0B 61 74 43 3B 37 56 \r' +
                        ECU_R_ADDR_H + ' 21 00 01 D1 03 E8 00 00 \r',
                        ECU_R_ADDR_H + ' 10 0B 61 74 3E 46 37 50 \r' +
                        ECU_R_ADDR_H + ' 21 00 01 9B 05 12 00 00 \r',
                        ECU_R_ADDR_H + ' 10 0B 61 74 3D 41 37 50 \r' +
                        ECU_R_ADDR_H + ' 21 00 01 9E 05 10 00 00 \r',
                        ECU_R_ADDR_H + ' 10 0B 61 74 49 39 37 56 \r' +
                        ECU_R_ADDR_H + ' 21 00 01 E1 03 E8 00 00 \r',
                        ECU_R_ADDR_H + ' 10 0B 61 74 38 3C 37 56 \r' +
                        ECU_R_ADDR_H + ' 21 00 01 9E 05 0D 00 00 \r',
                        ECU_R_ADDR_H + ' 10 0B 61 74 42 39 37 50 \r' +
                        ECU_R_ADDR_H + ' 21 00 01 CD 01 D0 00 00 \r',
                        ECU_R_ADDR_H + ' 10 0B 61 74 4D 39 37 50 \r' +
                        ECU_R_ADDR_H + ' 21 00 01 F8 03 E8 00 00 \r',
                        ECU_R_ADDR_H + ' 10 0B 61 74 4F 3A 37 50 \r' +
                        ECU_R_ADDR_H + ' 21 00 01 E6 03 E9 00 00 \r',
                        ECU_R_ADDR_H + ' 10 0B 61 74 4A 3F 37 56 \r' +
                        ECU_R_ADDR_H + ' 21 00 01 E4 04 3B 00 00 \r',
                        ECU_R_ADDR_H + ' 10 0B 61 74 38 37 37 3A \r' +
                        ECU_R_ADDR_H + ' 21 00 01 AA 01 A8 00 00 \r',
                        ECU_R_ADDR_H + ' 10 0B 61 74 37 37 37 37 \r' +
                        ECU_R_ADDR_H + ' 21 00 01 BA 01 BB 00 00 \r',
                        ECU_R_ADDR_H + ' 10 0B 61 74 39 37 37 3F \r' +
                        ECU_R_ADDR_H + ' 21 00 01 9C 01 99 00 00 \r',
                        ECU_R_ADDR_H + ' 10 0B 61 74 47 3B 37 56 \r' +
                        ECU_R_ADDR_H + ' 21 00 01 DA 03 E8 00 00 \r',
                        ECU_R_ADDR_H + ' 10 0B 61 74 38 37 37 3A \r' +
                        ECU_R_ADDR_H + ' 21 00 01 BA 01 BD 00 00 \r'
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
                        ECU_R_ADDR_H + ' 10 08 61 75 20 0D 2F 3A \r' +
                        ECU_R_ADDR_H + ' 21 C5 C0 00 00 00 00 00 \r',
                        ECU_R_ADDR_H + ' 10 08 61 75 20 0D 2F 38 \r' +
                        ECU_R_ADDR_H + ' 21 C5 80 00 00 00 00 00 \r',
                        ECU_R_ADDR_H + ' 10 08 61 75 20 0D 2F 39 \r' +
                        ECU_R_ADDR_H + ' 21 C5 80 00 00 00 00 00 \r',
                        ECU_R_ADDR_H + ' 10 08 61 75 20 0D 2F 39 \r' +
                        ECU_R_ADDR_H + ' 21 C5 C0 00 00 00 00 00 \r',
                        ECU_R_ADDR_H + ' 10 08 61 75 20 0D 2F 38 \r' +
                        ECU_R_ADDR_H + ' 21 C5 C0 00 00 00 00 00 \r',
                        ECU_R_ADDR_H + ' 10 08 61 75 20 0D 2F 3A \r' +
                        ECU_R_ADDR_H + ' 21 C5 80 00 00 00 00 00 \r'
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
                        ECU_R_ADDR_H + ' 04 61 78 80 00 \r',
                        ECU_R_ADDR_H + ' 04 61 78 00 00 \r'
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
                        ECU_R_ADDR_H + ' 04 61 7C 64 64 \r',
                        ECU_R_ADDR_H + ' 04 61 7C 64 32 \r',
                        ECU_R_ADDR_H + ' 04 61 7C 4B 64 \r',
                        ECU_R_ADDR_H + ' 04 61 7C 4B 32 \r'
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
                        ECU_R_ADDR_H + ' 05 61 7D 59 00 00 \r',
                        ECU_R_ADDR_H + ' 05 61 7D 6F 05 00 \r',
                        ECU_R_ADDR_H + ' 05 61 7D 6B 00 00 \r',
                        ECU_R_ADDR_H + ' 05 61 7D 00 00 00 \r',
                        ECU_R_ADDR_H + ' 05 61 7D 77 05 00 \r',
                        ECU_R_ADDR_H + ' 05 61 7D 86 05 00 \r',
                        ECU_R_ADDR_H + ' 05 61 7D 95 05 00 \r',
                        ECU_R_ADDR_H + ' 05 61 7D 64 00 00 \r',
                        ECU_R_ADDR_H + ' 05 61 7D 5C 00 00 \r',
                        ECU_R_ADDR_H + ' 05 61 7D 6D 00 00 \r',
                        ECU_R_ADDR_H + ' 05 61 7D 6A 05 00 \r',
                        ECU_R_ADDR_H + ' 05 61 7D 00 05 00 \r',
                        ECU_R_ADDR_H + ' 05 61 7D 57 00 00 \r'
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
                        ECU_R_ADDR_H + ' 10 22 61 81 37 7C 37 1A \r' +
                        ECU_R_ADDR_H + ' 21 38 08 38 08 38 BC 38 \r' +
                        ECU_R_ADDR_H + ' 22 BC 37 95 37 95 37 33 \r' +
                        ECU_R_ADDR_H + ' 23 37 22 38 49 38 5A 37 \r' +
                        ECU_R_ADDR_H + ' 24 53 37 95 AF 3B 09 74 \r',
                        ECU_R_ADDR_H + ' 10 22 61 81 38 72 38 20 \r' +
                        ECU_R_ADDR_H + ' 21 38 08 38 08 38 08 38 \r' +
                        ECU_R_ADDR_H + ' 22 20 37 F7 37 F7 38 31 \r' +
                        ECU_R_ADDR_H + ' 23 38 39 38 31 38 49 38 \r' +
                        ECU_R_ADDR_H + ' 24 72 38 BC AF 4B 09 92 \r',
                        ECU_R_ADDR_H + ' 10 22 61 81 2D 58 2D 58 \r' +
                        ECU_R_ADDR_H + ' 21 2E 1C 2E 0C 2D 81 2D \r' +
                        ECU_R_ADDR_H + ' 22 91 2E 0C 2E 0C 2E A7 \r' +
                        ECU_R_ADDR_H + ' 23 2E B8 2E 6E 2E 7E 2D \r' +
                        ECU_R_ADDR_H + ' 24 16 2D 2F AF 3B 07 BC \r',
                        ECU_R_ADDR_H + ' 10 22 61 81 30 DD 30 B4 \r' +
                        ECU_R_ADDR_H + ' 21 31 3F 31 3F 31 4F 31 \r' +
                        ECU_R_ADDR_H + ' 22 3F 30 C4 30 DD 31 26 \r' +
                        ECU_R_ADDR_H + ' 23 31 37 30 C4 30 C4 31 \r' +
                        ECU_R_ADDR_H + ' 24 4F 31 68 AF 3B 08 52 \r',
                        ECU_R_ADDR_H + ' 10 22 61 81 30 72 30 49 \r' +
                        ECU_R_ADDR_H + ' 21 30 49 30 49 30 49 30 \r' +
                        ECU_R_ADDR_H + ' 22 49 30 28 30 28 30 39 \r' +
                        ECU_R_ADDR_H + ' 23 30 20 30 49 30 49 30 \r' +
                        ECU_R_ADDR_H + ' 24 49 30 72 AF 3B 08 3E \r',
                        ECU_R_ADDR_H + ' 10 22 61 81 33 CE 33 AE \r' +
                        ECU_R_ADDR_H + ' 21 33 CE 33 CE 34 49 34 \r' +
                        ECU_R_ADDR_H + ' 22 62 33 E7 33 E7 34 49 \r' +
                        ECU_R_ADDR_H + ' 23 34 5A 33 F7 33 F7 34 \r' +
                        ECU_R_ADDR_H + ' 24 49 34 72 AF 2B 08 D4 \r',
                        ECU_R_ADDR_H + ' 10 22 61 81 37 CE 37 6C \r' +
                        ECU_R_ADDR_H + ' 21 37 33 37 1A 37 7C 37 \r' +
                        ECU_R_ADDR_H + ' 22 6C 37 6C 37 6C 37 53 \r' +
                        ECU_R_ADDR_H + ' 23 37 5C 37 7C 37 A5 37 \r' +
                        ECU_R_ADDR_H + ' 24 7C 37 BE AF 4B 09 7E \r',
                        ECU_R_ADDR_H + ' 10 22 61 81 33 1A 32 F9 \r' +
                        ECU_R_ADDR_H + ' 21 32 E1 32 D0 32 8F 32 \r' +
                        ECU_R_ADDR_H + ' 22 A7 32 B8 32 A7 32 D0 \r' +
                        ECU_R_ADDR_H + ' 23 32 D9 32 8F 32 A7 32 \r' +
                        ECU_R_ADDR_H + ' 24 E1 33 33 AF 3B 08 AC \r',
                        ECU_R_ADDR_H + ' 10 22 61 81 3A 66 3A 24 \r' +
                        ECU_R_ADDR_H + ' 21 3A 24 3A 24 3A 24 3A \r' +
                        ECU_R_ADDR_H + ' 22 24 3A 14 3A 14 3A 24 \r' +
                        ECU_R_ADDR_H + ' 23 3A 2D 3A 24 3A 3D 3A \r' +
                        ECU_R_ADDR_H + ' 24 76 3A C8 AF 4B 09 EC \r',
                        ECU_R_ADDR_H + ' 10 22 61 81 32 1C 32 04 \r' +
                        ECU_R_ADDR_H + ' 21 32 04 31 F3 31 F3 31 \r' +
                        ECU_R_ADDR_H + ' 22 DB 31 DB 31 DB 31 F3 \r' +
                        ECU_R_ADDR_H + ' 23 31 DB 31 DB 32 04 32 \r' +
                        ECU_R_ADDR_H + ' 24 1C 32 45 AF 3B 08 8E \r',
                        ECU_R_ADDR_H + ' 10 22 61 81 2C 62 2C 8B \r' +
                        ECU_R_ADDR_H + ' 21 2C A3 2C 8B 2C 39 2C \r' +
                        ECU_R_ADDR_H + ' 22 51 2D 06 2D 06 2C 18 \r' +
                        ECU_R_ADDR_H + ' 23 2C 18 2C 8B 2C 8B 2C \r' +
                        ECU_R_ADDR_H + ' 24 8B 2C 8B AF 0A 07 A8 \r',
                        ECU_R_ADDR_H + ' 10 22 61 81 3A 24 39 FB \r' +
                        ECU_R_ADDR_H + ' 21 38 FD 38 E5 39 60 39 \r' +
                        ECU_R_ADDR_H + ' 22 70 39 26 39 0E 39 89 \r' +
                        ECU_R_ADDR_H + ' 23 39 81 39 26 39 26 39 \r' +
                        ECU_R_ADDR_H + ' 24 99 39 DB AF 4B 09 C4 \r',
                        ECU_R_ADDR_H + ' 10 22 61 81 36 F1 36 B8 \r' +
                        ECU_R_ADDR_H + ' 21 35 37 35 26 36 8F 36 \r' +
                        ECU_R_ADDR_H + ' 22 8F 35 B2 35 A1 36 B8 \r' +
                        ECU_R_ADDR_H + ' 23 36 C0 35 89 35 78 36 \r' +
                        ECU_R_ADDR_H + ' 24 C8 37 1A AF 1A 09 6A \r',
                        ECU_R_ADDR_H + ' 10 22 61 81 34 AC 34 83 \r' +
                        ECU_R_ADDR_H + ' 21 34 72 34 72 34 72 34 \r' +
                        ECU_R_ADDR_H + ' 22 72 34 72 34 62 34 72 \r' +
                        ECU_R_ADDR_H + ' 23 34 6A 34 72 34 72 34 \r' +
                        ECU_R_ADDR_H + ' 24 9B 34 AC AF 4B 08 F2 \r',
                        ECU_R_ADDR_H + ' 10 22 61 81 32 D0 32 B8 \r' +
                        ECU_R_ADDR_H + ' 21 32 A7 32 8F 32 8F 32 \r' +
                        ECU_R_ADDR_H + ' 22 8F 32 8F 32 7E 32 8F \r' +
                        ECU_R_ADDR_H + ' 23 32 9F 32 8F 32 A7 32 \r' +
                        ECU_R_ADDR_H + ' 24 B8 32 E1 AF 3B 08 AC \r'
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
                        ECU_R_ADDR_H + ' 10 0A 61 87 3D C2 40 73 \r' +
                        ECU_R_ADDR_H + ' 21 41 5E 40 8C 00 00 00 \r',
                        ECU_R_ADDR_H + ' 10 0A 61 87 3D A8 3F D4 \r' +
                        ECU_R_ADDR_H + ' 21 40 DC 3F EE 00 00 00 \r',
                        ECU_R_ADDR_H + ' 10 0A 61 87 3D A8 3F D4 \r' +
                        ECU_R_ADDR_H + ' 21 40 DC 40 07 00 00 00 \r',
                        ECU_R_ADDR_H + ' 10 0A 61 87 3D A8 40 57 \r' +
                        ECU_R_ADDR_H + ' 21 41 45 40 73 00 00 00 \r',
                        ECU_R_ADDR_H + ' 10 0A 61 87 3E 11 40 C2 \r' +
                        ECU_R_ADDR_H + ' 21 41 94 40 C2 00 00 00 \r',
                        ECU_R_ADDR_H + ' 10 0A 61 87 3D 8F 40 07 \r' +
                        ECU_R_ADDR_H + ' 21 40 F5 40 23 00 00 00 \r',
                        ECU_R_ADDR_H + ' 10 0A 61 87 3D A8 40 3D \r' +
                        ECU_R_ADDR_H + ' 21 41 2B 40 57 00 00 00 \r',
                        ECU_R_ADDR_H + ' 10 0A 61 87 3D 8F 3F EE \r' +
                        ECU_R_ADDR_H + ' 21 40 F5 40 07 00 00 00 \r',
                        ECU_R_ADDR_H + ' 10 0A 61 87 3D F8 40 8C \r' +
                        ECU_R_ADDR_H + ' 21 41 7A 40 A8 00 00 00 \r',
                        ECU_R_ADDR_H + ' 10 0A 61 87 3D 8F 40 23 \r' +
                        ECU_R_ADDR_H + ' 21 41 11 40 3D 00 00 00 \r',
                        ECU_R_ADDR_H + ' 10 0A 61 87 3D A8 3F B8 \r' +
                        ECU_R_ADDR_H + ' 21 40 C2 3F EE 00 00 00 \r',
                        ECU_R_ADDR_H + ' 10 0A 61 87 3D A8 3F D4 \r' +
                        ECU_R_ADDR_H + ' 21 40 C2 3F EE 00 00 00 \r'
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
                        ECU_R_ADDR_H + ' 06 61 8A 82 17 00 00 \r',
                        ECU_R_ADDR_H + ' 06 61 8A 7F 6A 00 00 \r',
                        ECU_R_ADDR_H + ' 06 61 8A 78 29 00 00 \r',
                        ECU_R_ADDR_H + ' 06 61 8A 83 3C 00 00 \r',
                        ECU_R_ADDR_H + ' 06 61 8A 61 40 00 00 \r',
                        ECU_R_ADDR_H + ' 06 61 8A 8B 71 00 00 \r',
                        ECU_R_ADDR_H + ' 06 61 8A 81 53 00 00 \r',
                        ECU_R_ADDR_H + ' 06 61 8A 7C BE 00 00 \r',
                        ECU_R_ADDR_H + ' 06 61 8A 82 78 00 00 \r',
                        ECU_R_ADDR_H + ' 06 61 8A 65 A4 00 00 \r',
                        ECU_R_ADDR_H + ' 06 61 8A 7F 39 00 00 \r',
                        ECU_R_ADDR_H + ' 06 61 8A 62 C7 00 00 \r',
                        ECU_R_ADDR_H + ' 06 61 8A 67 EF 00 00 \r',
                        ECU_R_ADDR_H + ' 06 61 8A A3 B1 00 00 \r',
                        ECU_R_ADDR_H + ' 06 61 8A 66 68 00 00 \r'
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
                        ECU_R_ADDR_H + ' 10 11 61 92 33 F7 04 35 \r' +
                        ECU_R_ADDR_H + ' 21 26 0D 0E 00 00 00 00 \r' +
                        ECU_R_ADDR_H + ' 22 00 00 00 00 00 00 00 \r',
                        ECU_R_ADDR_H + ' 10 11 61 92 3B 64 06 3C \r' +
                        ECU_R_ADDR_H + ' 21 83 0D 0E 00 00 00 00 \r' +
                        ECU_R_ADDR_H + ' 22 00 00 00 00 00 00 00 \r',
                        ECU_R_ADDR_H + ' 10 11 61 92 32 66 08 32 \r' +
                        ECU_R_ADDR_H + ' 21 E1 00 0E 00 00 00 00 \r' +
                        ECU_R_ADDR_H + ' 22 00 00 00 00 00 00 00 \r',
                        ECU_R_ADDR_H + ' 10 11 61 92 31 B2 06 32 \r' +
                        ECU_R_ADDR_H + ' 21 8F 0D 0E 00 00 00 00 \r' +
                        ECU_R_ADDR_H + ' 22 00 00 00 00 00 00 00 \r',
                        ECU_R_ADDR_H + ' 10 11 61 92 32 7E 07 32 \r' +
                        ECU_R_ADDR_H + ' 21 E1 0D 0E 00 00 00 00 \r' +
                        ECU_R_ADDR_H + ' 22 00 00 00 00 00 00 00 \r',
                        ECU_R_ADDR_H + ' 10 11 61 92 2E 97 04 2F \r' +
                        ECU_R_ADDR_H + ' 21 74 06 0E 00 00 00 00 \r' +
                        ECU_R_ADDR_H + ' 22 00 00 00 00 00 00 00 \r',
                        ECU_R_ADDR_H + ' 10 11 61 92 32 7E 07 32 \r' +
                        ECU_R_ADDR_H + ' 21 F9 0D 0E 00 00 00 00 \r' +
                        ECU_R_ADDR_H + ' 22 00 00 00 00 00 00 00 \r',
                        ECU_R_ADDR_H + ' 10 11 61 92 35 C2 09 36 \r' +
                        ECU_R_ADDR_H + ' 21 66 00 0E 00 00 00 00 \r' +
                        ECU_R_ADDR_H + ' 22 00 00 00 00 00 00 00 \r',
                        ECU_R_ADDR_H + ' 10 11 61 92 34 C4 04 35 \r' +
                        ECU_R_ADDR_H + ' 21 CA 00 0E 00 00 00 00 \r' +
                        ECU_R_ADDR_H + ' 22 00 00 00 00 00 00 00 \r',
                        ECU_R_ADDR_H + ' 10 11 61 92 31 EB 09 32 \r' +
                        ECU_R_ADDR_H + ' 21 7E 0D 0E 00 00 00 00 \r' +
                        ECU_R_ADDR_H + ' 22 00 00 00 00 00 00 00 \r',
                        ECU_R_ADDR_H + ' 10 11 61 92 35 EB 06 36 \r' +
                        ECU_R_ADDR_H + ' 21 56 00 0E 00 00 00 00 \r' +
                        ECU_R_ADDR_H + ' 22 00 00 00 00 00 00 00 \r',
                        ECU_R_ADDR_H + ' 10 11 61 92 32 2D 0B 32 \r' +
                        ECU_R_ADDR_H + ' 21 A7 00 0E 00 00 00 00 \r' +
                        ECU_R_ADDR_H + ' 22 00 00 00 00 00 00 00 \r',
                        ECU_R_ADDR_H + ' 10 11 61 92 31 91 02 31 \r' +
                        ECU_R_ADDR_H + ' 21 DB 0D 0E 00 00 00 00 \r' +
                        ECU_R_ADDR_H + ' 22 00 00 00 00 00 00 00 \r',
                        ECU_R_ADDR_H + ' 10 11 61 92 33 33 04 33 \r' +
                        ECU_R_ADDR_H + ' 21 E7 0D 0E 00 00 00 00 \r' +
                        ECU_R_ADDR_H + ' 22 00 00 00 00 00 00 00 \r',
                        ECU_R_ADDR_H + ' 10 11 61 92 2E C0 04 2F \r' +
                        ECU_R_ADDR_H + ' 21 22 00 0E 00 00 00 00 \r' +
                        ECU_R_ADDR_H + ' 22 00 00 00 00 00 00 00 \r'
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
            'Response': ECU_R_ADDR_H + ' 10 10 61 95 17 16 15 16 \r' +
                        ECU_R_ADDR_H + ' 21 16 16 16 16 16 16 16 \r' +
                        ECU_R_ADDR_H + ' 22 16 16 17 00 00 00 00 \r'
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
                        ECU_R_ADDR_H + ' 10 0A 61 98 74 E9 5A A1 \r' +
                        ECU_R_ADDR_H + ' 21 00 79 79 72 00 00 00 \r',
                        ECU_R_ADDR_H + ' 10 0A 61 98 7F 4D 5A A1 \r' +
                        ECU_R_ADDR_H + ' 21 00 79 79 77 00 00 00 \r',
                        ECU_R_ADDR_H + ' 10 0A 61 98 62 57 5A A1 \r' +
                        ECU_R_ADDR_H + ' 21 00 79 79 72 00 00 00 \r',
                        ECU_R_ADDR_H + ' 10 0A 61 98 9C 1A 5A A1 \r' +
                        ECU_R_ADDR_H + ' 21 00 79 79 72 00 00 00 \r',
                        ECU_R_ADDR_H + ' 10 0A 61 98 87 10 5A A1 \r' +
                        ECU_R_ADDR_H + ' 21 00 79 79 72 00 00 00 \r',
                        ECU_R_ADDR_H + ' 10 0A 61 98 9C AB 5A A1 \r' +
                        ECU_R_ADDR_H + ' 21 00 79 79 73 00 00 00 \r',
                        ECU_R_ADDR_H + ' 10 0A 61 98 A2 58 59 A1 \r' +
                        ECU_R_ADDR_H + ' 21 00 79 79 72 00 00 00 \r',
                        ECU_R_ADDR_H + ' 10 0A 61 98 72 15 59 A1 \r' +
                        ECU_R_ADDR_H + ' 21 00 79 7B 72 00 00 00 \r',
                        ECU_R_ADDR_H + ' 10 0A 61 98 81 5C 5A A1 \r' +
                        ECU_R_ADDR_H + ' 21 00 79 79 78 00 00 00 \r',
                        ECU_R_ADDR_H + ' 10 0A 61 98 63 40 59 A1 \r' +
                        ECU_R_ADDR_H + ' 21 00 79 79 72 00 00 00 \r',
                        ECU_R_ADDR_H + ' 10 0A 61 98 7D 8E 5A A1 \r' +
                        ECU_R_ADDR_H + ' 21 00 79 79 72 00 00 00 \r',
                        ECU_R_ADDR_H + ' 10 0A 61 98 85 EF 5A A1 \r' +
                        ECU_R_ADDR_H + ' 21 00 79 79 72 00 00 00 \r',
                        ECU_R_ADDR_H + ' 10 0A 61 98 A0 1B 5A A1 \r' +
                        ECU_R_ADDR_H + ' 21 00 79 79 72 00 00 00 \r',
                        ECU_R_ADDR_H + ' 10 0A 61 98 7C CE 5A A1 \r' +
                        ECU_R_ADDR_H + ' 21 00 79 79 72 00 00 00 \r',
                        ECU_R_ADDR_H + ' 10 0A 61 98 91 31 5A A1 \r' +
                        ECU_R_ADDR_H + ' 21 00 79 79 76 00 00 00 \r'
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
                        ECU_R_ADDR_H + ' 06 61 9B 00 00 00 D3 \r',
                        ECU_R_ADDR_H + ' 06 61 9B 00 00 00 D1 \r',
                        ECU_R_ADDR_H + ' 06 61 9B 00 00 00 DA \r',
                        ECU_R_ADDR_H + ' 06 61 9B 00 00 00 D7 \r',
                        ECU_R_ADDR_H + ' 06 61 9B 00 00 00 D4 \r',
                        ECU_R_ADDR_H + ' 06 61 9B 00 00 00 CB \r',
                        ECU_R_ADDR_H + ' 06 61 9B 00 00 00 E4 \r',
                        ECU_R_ADDR_H + ' 06 61 9B 00 00 00 C7 \r',
                        ECU_R_ADDR_H + ' 06 61 9B 00 00 00 D2 \r'
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
            'Response': ECU_R_ADDR_H + ' 10 0F 61 C2 30 32 30 35 \r' +
                        ECU_R_ADDR_H + ' 21 30 00 22 05 04 00 00 \r' +
                        ECU_R_ADDR_H + ' 22 00 01 00 00 00 00 00 \r'
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
                        ECU_R_ADDR_H + ' 10 0A 61 E1 00 00 0E B1 \r' +
                        ECU_R_ADDR_H + ' 21 20 00 04 07 00 00 00 \r',
                        ECU_R_ADDR_H + ' 10 0A 61 E1 00 00 0E B1 \r' +
                        ECU_R_ADDR_H + ' 21 20 00 05 2E 00 00 00 \r',
                        ECU_R_ADDR_H + ' 10 0A 61 E1 00 00 0E B1 \r' +
                        ECU_R_ADDR_H + ' 21 20 00 04 69 00 00 00 \r',
                        ECU_R_ADDR_H + ' 10 0A 61 E1 00 00 0E B1 \r' +
                        ECU_R_ADDR_H + ' 21 20 00 02 D0 00 00 00 \r',
                        ECU_R_ADDR_H + ' 10 0A 61 E1 00 00 0E B1 \r' +
                        ECU_R_ADDR_H + ' 21 20 00 01 DD 00 00 00 \r',
                        ECU_R_ADDR_H + ' 10 0A 61 E1 00 00 0E B1 \r' +
                        ECU_R_ADDR_H + ' 21 20 00 06 56 00 00 00 \r',
                        ECU_R_ADDR_H + ' 10 0A 61 E1 00 00 0E B1 \r' +
                        ECU_R_ADDR_H + ' 21 20 00 07 7D 00 00 00 \r',
                        ECU_R_ADDR_H + ' 10 0A 61 E1 00 00 0E B1 \r' +
                        ECU_R_ADDR_H + ' 21 20 00 04 CA 00 00 00 \r',
                        ECU_R_ADDR_H + ' 10 0A 61 E1 00 00 0E B1 \r' +
                        ECU_R_ADDR_H + ' 21 20 00 05 F4 00 00 00 \r',
                        ECU_R_ADDR_H + ' 10 0A 61 E1 00 00 0E B1 \r' +
                        ECU_R_ADDR_H + ' 21 20 00 03 A4 00 00 00 \r',
                        ECU_R_ADDR_H + ' 10 0A 61 E1 00 00 0E B1 \r' +
                        ECU_R_ADDR_H + ' 21 20 00 05 90 00 00 00 \r',
                        ECU_R_ADDR_H + ' 10 0A 61 E1 00 00 0E B1 \r' +
                        ECU_R_ADDR_H + ' 21 20 00 03 3C 00 00 00 \r',
                        ECU_R_ADDR_H + ' 10 0A 61 E1 00 00 0E B1 \r' +
                        ECU_R_ADDR_H + ' 21 20 00 07 1D 00 00 00 \r',
                        ECU_R_ADDR_H + ' 10 0A 61 E1 00 00 0E B1 \r' +
                        ECU_R_ADDR_H + ' 21 20 00 02 63 00 00 00 \r',
                        ECU_R_ADDR_H + ' 10 0A 61 E1 00 00 0E B1 \r' +
                        ECU_R_ADDR_H + ' 21 20 00 06 B8 00 00 00 \r'
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
                        ECU_R_ADDR_I + ' 10 08 61 12 00 00 07 00 \r' +
                        ECU_R_ADDR_I + ' 21 00 00 00 00 00 00 00 \r',
                        ECU_R_ADDR_I + ' 10 08 61 12 00 00 07 10 \r' +
                        ECU_R_ADDR_I + ' 21 00 00 00 00 00 00 00 \r'
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
                        ECU_R_ADDR_I + ' 03 61 13 95 \r',
                        ECU_R_ADDR_I + ' 03 61 13 96 \r'
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
                        ECU_R_ADDR_I + ' 03 61 29 02 \r',
                        ECU_R_ADDR_I + ' 03 61 29 0A \r',
                        ECU_R_ADDR_I + ' 03 61 29 06 \r'
                        ]
        },
        'CUSTOM_SUB_TANK': {
            'Request': '^212A' + ELM_MAX_RESP,
            'Descr': 'Sub tank level',
            'Response': ECU_R_ADDR_I + ' 03 7F 21 12 \r',
            'Header': ECU_ADDR_I
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
                        ECU_R_ADDR_P + ' 03 61 21 54 \r',
                        ECU_R_ADDR_P + ' 03 61 21 50 \r',
                        ECU_R_ADDR_P + ' 03 61 21 52 \r',
                        ECU_R_ADDR_P + ' 03 61 21 53 \r',
                        ECU_R_ADDR_P + ' 03 61 21 51 \r',
                        ECU_R_ADDR_P + ' 03 61 21 56 \r',
                        ECU_R_ADDR_P + ' 03 61 21 55 \r',
                        ECU_R_ADDR_P + ' 03 61 21 58 \r'
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
                        ECU_R_ADDR_P + ' 03 61 22 60 \r',
                        ECU_R_ADDR_P + ' 03 61 22 62 \r',
                        ECU_R_ADDR_P + ' 03 61 22 5F \r',
                        ECU_R_ADDR_P + ' 03 61 22 63 \r',
                        ECU_R_ADDR_P + ' 03 61 22 61 \r',
                        ECU_R_ADDR_P + ' 03 61 22 5E \r'
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
                        ECU_R_ADDR_P + ' 03 61 24 01 \r',
                        ECU_R_ADDR_P + ' 03 61 24 00 \r'
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
                        ECU_R_ADDR_P + ' 03 61 26 5E \r',
                        ECU_R_ADDR_P + ' 03 61 26 98 \r',
                        ECU_R_ADDR_P + ' 03 61 26 6B \r',
                        ECU_R_ADDR_P + ' 03 61 26 A4 \r',
                        ECU_R_ADDR_P + ' 03 61 26 7E \r',
                        ECU_R_ADDR_P + ' 03 61 26 B0 \r',
                        ECU_R_ADDR_P + ' 03 61 26 4C \r',
                        ECU_R_ADDR_P + ' 03 61 26 91 \r',
                        ECU_R_ADDR_P + ' 03 61 26 8E \r',
                        ECU_R_ADDR_P + ' 03 61 26 55 \r',
                        ECU_R_ADDR_P + ' 03 61 26 81 \r',
                        ECU_R_ADDR_P + ' 03 61 26 AF \r',
                        ECU_R_ADDR_P + ' 03 61 26 84 \r',
                        ECU_R_ADDR_P + ' 03 61 26 75 \r',
                        ECU_R_ADDR_P + ' 03 61 26 4B \r'
                        ]
        },
        'CUSTOM_SET_TEMP_D': {
            'Request': '^2129[012]?$',
            'Descr': 'Set Temperature (D side)',
            'Response': ECU_R_ADDR_P + ' 03 7F 21 12 \r',
            'Header': ECU_ADDR_P
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
                        ECU_R_ADDR_P + ' 03 61 3C 04 \r',
                        ECU_R_ADDR_P + ' 03 61 3C 0B \r',
                        ECU_R_ADDR_P + ' 03 61 3C 0F \r',
                        ECU_R_ADDR_P + ' 03 61 3C 0E \r',
                        ECU_R_ADDR_P + ' 03 61 3C 09 \r',
                        ECU_R_ADDR_P + ' 03 61 3C 05 \r',
                        ECU_R_ADDR_P + ' 03 61 3C 10 \r',
                        ECU_R_ADDR_P + ' 03 61 3C 00 \r'
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
                        ECU_R_ADDR_P + ' 03 61 3D 81 \r',
                        ECU_R_ADDR_P + ' 03 61 3D 83 \r',
                        ECU_R_ADDR_P + ' 03 61 3D 85 \r',
                        ECU_R_ADDR_P + ' 03 61 3D 80 \r',
                        ECU_R_ADDR_P + ' 03 61 3D 7F \r',
                        ECU_R_ADDR_P + ' 03 61 3D 82 \r',
                        ECU_R_ADDR_P + ' 03 61 3D 84 \r'
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
            'Response': [
                        ECU_R_ADDR_P + ' 06 61 43 09 09 00 00 \r',
                        ECU_R_ADDR_P + ' 06 61 43 05 05 00 00 \r'
                        ]
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
                        ECU_R_ADDR_P + ' 03 61 4B 77 \r',
                        ECU_R_ADDR_P + ' 03 61 4B 76 \r',
                        ECU_R_ADDR_P + ' 03 61 4B 79 \r',
                        ECU_R_ADDR_P + ' 03 61 4B 7A \r',
                        ECU_R_ADDR_P + ' 03 61 4B 7B \r',
                        ECU_R_ADDR_P + ' 03 61 4B 78 \r'
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
                        ECU_R_ADDR_P + ' 03 61 53 39 \r',
                        ECU_R_ADDR_P + ' 03 61 53 37 \r',
                        ECU_R_ADDR_P + ' 03 61 53 38 \r'
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
                        ECU_R_ADDR_S + ' 06 61 03 3E 3E 3D 3D \r',
                        ECU_R_ADDR_S + ' 06 61 03 06 06 06 06 \r',
                        ECU_R_ADDR_S + ' 06 61 03 33 33 32 32 \r',
                        ECU_R_ADDR_S + ' 06 61 03 31 31 31 31 \r',
                        ECU_R_ADDR_S + ' 06 61 03 02 02 02 02 \r',
                        ECU_R_ADDR_S + ' 06 61 03 19 19 19 19 \r',
                        ECU_R_ADDR_S + ' 06 61 03 28 28 27 27 \r',
                        ECU_R_ADDR_S + ' 06 61 03 4D 4D 4D 4D \r',
                        ECU_R_ADDR_S + ' 06 61 03 16 14 16 14 \r',
                        ECU_R_ADDR_S + ' 06 61 03 29 29 29 29 \r',
                        ECU_R_ADDR_S + ' 06 61 03 4A 4A 4B 4B \r',
                        ECU_R_ADDR_S + ' 06 61 03 38 38 37 37 \r',
                        ECU_R_ADDR_S + ' 06 61 03 00 00 00 00 \r',
                        ECU_R_ADDR_S + ' 06 61 03 13 12 12 12 \r'
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
                        ECU_R_ADDR_S + ' 06 61 06 80 80 8A 5F \r',
                        ECU_R_ADDR_S + ' 06 61 06 80 80 80 0F \r',
                        ECU_R_ADDR_S + ' 06 61 06 7E 7E 7F D3 \r',
                        ECU_R_ADDR_S + ' 06 61 06 7E 7E 7F 01 \r',
                        ECU_R_ADDR_S + ' 06 61 06 7D 7D 7F 97 \r',
                        ECU_R_ADDR_S + ' 06 61 06 80 80 80 2D \r',
                        ECU_R_ADDR_S + ' 06 61 06 80 80 80 00 \r',
                        ECU_R_ADDR_S + ' 06 61 06 82 82 86 09 \r',
                        ECU_R_ADDR_S + ' 06 61 06 99 99 85 82 \r',
                        ECU_R_ADDR_S + ' 06 61 06 80 80 80 1E \r',
                        ECU_R_ADDR_S + ' 06 61 06 8C 8C 83 57 \r'
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
            'Response': [
                        ECU_R_ADDR_S + ' 03 61 07 1B \r',
                        ECU_R_ADDR_S + ' 03 61 07 1C \r',
                        ECU_R_ADDR_S + ' 03 61 07 19 \r'
                        ]
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
                        ECU_R_ADDR_S + ' 07 61 47 F5 00 65 70 79 \r',
                        ECU_R_ADDR_S + ' 07 61 47 0C FF A0 8C 80 \r',
                        ECU_R_ADDR_S + ' 07 61 47 FD F8 7B 7F 13 \r',
                        ECU_R_ADDR_S + ' 07 61 47 F8 FB 75 7D EE \r',
                        ECU_R_ADDR_S + ' 07 61 47 FE FA 7E 7F CC \r',
                        ECU_R_ADDR_S + ' 07 61 47 00 FF 80 89 24 \r',
                        ECU_R_ADDR_S + ' 07 61 47 FC 0A 7B 7F 30 \r',
                        ECU_R_ADDR_S + ' 07 61 47 01 00 80 80 0B \r',
                        ECU_R_ADDR_S + ' 07 61 47 FD 09 7D 7F 91 \r',
                        ECU_R_ADDR_S + ' 07 61 47 00 F4 80 80 0B \r',
                        ECU_R_ADDR_S + ' 07 61 47 00 FF 80 8A 5F \r',
                        ECU_R_ADDR_S + ' 07 61 47 00 FC 80 80 0B \r',
                        ECU_R_ADDR_S + ' 07 61 47 FE FE 7F 7F D9 \r',
                        ECU_R_ADDR_S + ' 07 61 47 03 00 83 80 84 \r',
                        ECU_R_ADDR_S + ' 07 61 47 00 FE 80 80 07 \r'
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
                        ECU_R_ADDR_S + ' 03 61 58 00 \r',
                        ECU_R_ADDR_S + ' 03 61 58 80 \r'
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
                        ECU_R_ADDR_S + ' 10 08 61 A3 25 00 24 33 \r' +
                        ECU_R_ADDR_S + ' 21 4A 4A 00 00 00 00 00 \r',
                        ECU_R_ADDR_S + ' 10 08 61 A3 00 25 24 33 \r' +
                        ECU_R_ADDR_S + ' 21 4A 4A 00 00 00 00 00 \r',
                        ECU_R_ADDR_S + ' 10 08 61 A3 30 00 24 34 \r' +
                        ECU_R_ADDR_S + ' 21 4A 4A 00 00 00 00 00 \r',
                        ECU_R_ADDR_S + ' 10 08 61 A3 00 00 24 33 \r' +
                        ECU_R_ADDR_S + ' 21 00 00 00 00 00 00 00 \r',
                        ECU_R_ADDR_S + ' 10 08 61 A3 00 00 24 34 \r' +
                        ECU_R_ADDR_S + ' 21 00 00 00 00 00 00 00 \r',
                        ECU_R_ADDR_S + ' 10 08 61 A3 18 00 24 33 \r' +
                        ECU_R_ADDR_S + ' 21 4A 4A 00 00 00 00 00 \r'
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
    # New custom OBD Commands
        'CUSTOM_FSS1': {
            'Request': '^2103' + ELM_MAX_RESP,
            'Descr': 'Fuel System Status #1 (OL=1,CL=2,OLDrive=4,OLFault=8,CLFault=16)',
            'Equation': 'A',
            'Min': '1',
            'Max': '16',
            'Unit': '',
            'Header': ECU_ADDR_E,
            'Response': [
                        ECU_R_ADDR_E + ' 10 0A 61 03 01 00 80 7C \r' +
                        ECU_R_ADDR_E + ' 21 9F 00 00 01 00 00 00 \r',
                        ECU_R_ADDR_E + ' 10 0A 61 03 00 00 80 7D \r' +
                        ECU_R_ADDR_E + ' 21 8A 00 00 01 00 00 00 \r',
                        ECU_R_ADDR_E + ' 10 0A 61 03 02 00 84 7C \r' +
                        ECU_R_ADDR_E + ' 21 A2 00 00 01 00 00 00 \r'
                        ]
        },
        'CUSTOM_TAFR': {
            'Request': '^2104' + ELM_MAX_RESP,
            'Descr': 'Target Air-Fuel Ratio',
            'Equation': '(A * 256 + B) * 1.99 / 65535',
            'Min': '0',
            'Max': '1.99',
            'Unit': '',
            'Header': ECU_ADDR_E,
            'Response': [
                        ECU_R_ADDR_E + ' 10 0E 61 04 7F F2 7F 73 \r' +
                        ECU_R_ADDR_E + ' 21 6A 11 7F 73 80 01 00 \r' +
                        ECU_R_ADDR_E + ' 22 FF 00 00 00 00 00 00 \r',
                        ECU_R_ADDR_E + ' 10 0E 61 04 7F F2 68 1C \r' +
                        ECU_R_ADDR_E + ' 21 27 04 68 1C 7F 39 00 \r' +
                        ECU_R_ADDR_E + ' 22 FF 00 00 00 00 00 00 \r',
                        ECU_R_ADDR_E + ' 10 0E 61 04 60 17 7F FB \r' +
                        ECU_R_ADDR_E + ' 21 6A D9 7F FB 80 03 00 \r' +
                        ECU_R_ADDR_E + ' 22 FF 00 00 00 00 00 00 \r'
                        ]
        },
        'CUSTOM_CAT_B1S1_SG': {
            'Request': '^2105' + ELM_MAX_RESP,
            'Descr': 'Catalyst Temp B1 S1 (Singapore)',
            'Equation': '(A * 256 + B) / 10 - 40',
            'Min': '-40',
            'Max': '6513.5',
            'Unit': 'C',
            'Header': ECU_ADDR_E,
            'Response': [
                        ECU_R_ADDR_E + ' 06 61 05 0F 26 0B 79 \r',
                        ECU_R_ADDR_E + ' 06 61 05 0F 54 0B A7 \r',
                        ECU_R_ADDR_E + ' 06 61 05 0F 2D 0B 80 \r',
                        ECU_R_ADDR_E + ' 06 61 05 0F 46 0B 99 \r',
                        ECU_R_ADDR_E + ' 06 61 05 0F 3D 0B 90 \r',
                        ECU_R_ADDR_E + ' 06 61 05 0F 4D 0B A0 \r',
                        ECU_R_ADDR_E + ' 06 61 05 0F 28 0B 6D \r',
                        ECU_R_ADDR_E + ' 06 61 05 0F 1E 0B 71 \r',
                        ECU_R_ADDR_E + ' 06 61 05 0F 91 0B 95 \r',
                        ECU_R_ADDR_E + ' 06 61 05 0F 35 0B 88 \r'
                        ]
        },
        'CUSTOM_MIL': {
            'Request': '^2106' + ELM_MAX_RESP,
            'Descr': 'MIL',
            'Equation': '{A:7}',
            'Min': '0',
            'Max': '1',
            'Unit': 'Off/On',
            'Header': ECU_ADDR_E,
            'Response': ECU_R_ADDR_E + ' 10 0C 61 06 00 07 A1 00 \r' +
                        ECU_R_ADDR_E + ' 21 03 06 00 00 00 00 00 \r'
        },
        'CUSTOM_HV_COMM': {
            'Request': '^2124' + ELM_MAX_RESP,
            'Descr': 'Communication with HV',
            'Equation': '{A:5}',
            'Min': '0',
            'Max': '1',
            'Unit': 'Off/On',
            'Header': ECU_ADDR_E,
            'Response': ECU_R_ADDR_E + ' 03 61 24 28 \r'
        },
        'CUSTOM_INIT_ECT': {
            'Request': '^2137' + ELM_MAX_RESP,
            'Descr': 'Initial Engine Coolant Temp',
            'Equation': 'A * 159.3 / 255 - 40',
            'Min': '-40',
            'Max': '119.3',
            'Unit': 'C',
            'Header': ECU_ADDR_E,
            'Response': [
                        ECU_R_ADDR_E + ' 10 11 61 37 59 58 83 46 \r' +
                        ECU_R_ADDR_E + ' 21 7F A0 80 00 00 00 00 \r' +
                        ECU_R_ADDR_E + ' 22 00 1A DC 00 00 00 00 \r',
                        ECU_R_ADDR_E + ' 10 11 61 37 59 58 83 46 \r' +
                        ECU_R_ADDR_E + ' 21 7F A0 80 00 00 00 00 \r' +
                        ECU_R_ADDR_E + ' 22 00 1A DC 04 00 00 00 \r',
                        ECU_R_ADDR_E + ' 10 11 61 37 59 58 83 46 \r' +
                        ECU_R_ADDR_E + ' 21 7F A0 80 00 00 00 00 \r' +
                        ECU_R_ADDR_E + ' 22 00 1A DC 44 00 00 00 \r'
                        ]
        },
        'CUSTOM_INJ_VOL': {
            'Request': '^213C' + ELM_MAX_RESP,
            'Descr': 'Injection volume (Cylinder 1) for 10 times',
            'Equation': '(A * 256 + B) * 2.047 / 65535',
            'Min': '0',
            'Max': '2.047',
            'Unit': 'ml',
            'Header': ECU_ADDR_E,
            'Response': [
                        ECU_R_ADDR_E + ' 07 61 3C 09 82 09 43 80 \r',
                        ECU_R_ADDR_E + ' 07 61 3C 15 8F 10 D1 80 \r',
                        ECU_R_ADDR_E + ' 07 61 3C 08 65 07 B3 80 \r'
                        ]
        },
        'CUSTOM_EGR_STEP': {
            'Request': '^2147' + ELM_MAX_RESP,
            'Descr': 'EGR Step Position',
            'Equation': 'A',
            'Min': '0',
            'Max': '120',
            'Unit': 'step',
            'Header': ECU_ADDR_E,
            'Response': ECU_R_ADDR_E + ' 03 61 47 00 \r'
        },
        'CUSTOM_REQENGTORQ': {
            'Request': '^2149' + ELM_MAX_RESP,
            'Descr': 'Requested Engine Torque',
            'Equation': '(A * 256 + B) / 4',
            'Min': '0',
            'Max': '73',
            'Unit': 'kW',
            'Header': ECU_ADDR_E,
            'Response': [
                        ECU_R_ADDR_E + ' 10 0E 61 49 00 00 37 80 \r' +
                        ECU_R_ADDR_E + ' 21 00 FF 77 1D 00 08 A9 \r' +
                        ECU_R_ADDR_E + ' 22 62 00 00 00 00 00 00 \r',
                        ECU_R_ADDR_E + ' 10 0E 61 49 00 14 34 80 \r' +
                        ECU_R_ADDR_E + ' 21 32 FF 77 1D 00 08 A9 \r' +
                        ECU_R_ADDR_E + ' 22 42 00 00 00 00 00 00 \r',
                        ECU_R_ADDR_E + ' 10 0E 61 49 00 00 00 80 \r' +
                        ECU_R_ADDR_E + ' 21 00 FF 77 1D 00 08 A9 \r' +
                        ECU_R_ADDR_E + ' 22 0A 00 00 00 00 00 00 \r'
                        ]
        },
        'CUSTOM_MCODE_7E0': {
            'Request': '^21C1' + ELM_MAX_RESP,
            'Descr': 'Model Code_7E0',
            'Equation': 'ABCDEFG',
            'Min': '0',
            'Max': '0',
            'Unit': '',
            'Header': ECU_ADDR_E,
            'Response': ECU_R_ADDR_E + ' 10 15 61 C1 5A 57 45 31 \r' +
                        ECU_R_ADDR_E + ' 21 38 23 20 32 5A 52 46 \r' +
                        ECU_R_ADDR_E + ' 22 58 45 04 00 57 74 21 \r' +
                        ECU_R_ADDR_E + ' 23 00 00 00 00 00 00 00 \r'
        },
        'CUSTOM_CLOAD_7E2': {
            'Request': '^2101' + ELM_MAX_RESP,
            'Descr': 'Calculated Load_7E2',
            'Equation': 'A * 20 / 51',
            'Min': '0',
            'Max': '100',
            'Unit': '%',
            'Header': ECU_ADDR_H,
            'Response': [
                        ECU_R_ADDR_H + ' 10 18 61 01 00 63 55 36 \r' +
                        ECU_R_ADDR_H + ' 21 63 4B 00 00 00 05 BC \r' +
                        ECU_R_ADDR_H + ' 22 2B 28 51 FF E2 FB FF \r' +
                        ECU_R_ADDR_H + ' 23 FF 38 FD 9E 00 00 00 \r',
                        ECU_R_ADDR_H + ' 10 18 61 01 00 63 55 36 \r' +
                        ECU_R_ADDR_H + ' 21 63 4B 00 00 00 05 A0 \r' +
                        ECU_R_ADDR_H + ' 22 2B 28 51 FF E2 FB FF \r' +
                        ECU_R_ADDR_H + ' 23 FF 39 11 9E 00 00 00 \r',
                        ECU_R_ADDR_H + ' 10 18 61 01 00 63 55 36 \r' +
                        ECU_R_ADDR_H + ' 21 63 4B 00 00 00 05 8C \r' +
                        ECU_R_ADDR_H + ' 22 2B 28 51 FF E2 FB FF \r' +
                        ECU_R_ADDR_H + ' 23 FF 39 11 9F 00 00 00 \r',
                        ECU_R_ADDR_H + ' 10 18 61 01 00 63 55 36 \r' +
                        ECU_R_ADDR_H + ' 21 63 4B 00 00 00 05 92 \r' +
                        ECU_R_ADDR_H + ' 22 2B 28 51 FF E2 FB FF \r' +
                        ECU_R_ADDR_H + ' 23 FF 38 FD 9F 00 00 00 \r',
                        ECU_R_ADDR_H + ' 10 18 61 01 00 63 55 36 \r' +
                        ECU_R_ADDR_H + ' 21 63 4B 00 00 00 05 B5 \r' +
                        ECU_R_ADDR_H + ' 22 2B 28 51 FF E2 FB FF \r' +
                        ECU_R_ADDR_H + ' 23 FF 39 11 9E 00 00 00 \r',
                        ECU_R_ADDR_H + ' 10 18 61 01 DA 26 55 36 \r' +
                        ECU_R_ADDR_H + ' 21 63 4B 17 00 00 05 C3 \r' +
                        ECU_R_ADDR_H + ' 22 2D 3F 68 FF E2 FB FF \r' +
                        ECU_R_ADDR_H + ' 23 FF 38 FD 9D 00 00 00 \r',
                        ECU_R_ADDR_H + ' 10 18 61 01 00 63 55 36 \r' +
                        ECU_R_ADDR_H + ' 21 63 4B 00 00 00 05 99 \r' +
                        ECU_R_ADDR_H + ' 22 2B 28 51 FF E2 FB FF \r' +
                        ECU_R_ADDR_H + ' 23 FF 39 11 9F 00 00 00 \r',
                        ECU_R_ADDR_H + ' 10 18 61 01 A1 37 4B 36 \r' +
                        ECU_R_ADDR_H + ' 21 63 4B 14 80 00 05 CA \r' +
                        ECU_R_ADDR_H + ' 22 32 28 51 FF E2 FB FF \r' +
                        ECU_R_ADDR_H + ' 23 FF 39 11 9E 00 00 00 \r',
                        ECU_R_ADDR_H + ' 10 18 61 01 00 63 55 36 \r' +
                        ECU_R_ADDR_H + ' 21 63 4B 00 00 00 05 AE \r' +
                        ECU_R_ADDR_H + ' 22 2B 28 51 FF E2 FB FF \r' +
                        ECU_R_ADDR_H + ' 23 FF 39 11 9E 00 00 00 \r',
                        ECU_R_ADDR_H + ' 10 18 61 01 00 63 55 36 \r' +
                        ECU_R_ADDR_H + ' 21 63 4B 00 00 00 05 A7 \r' +
                        ECU_R_ADDR_H + ' 22 2B 28 51 FF E2 FB FF \r' +
                        ECU_R_ADDR_H + ' 23 FF 39 11 9E 00 00 00 \r'
                        ]
        },
        'CUSTOM_CCS_SPD': {
            'Request': '^2121' + ELM_MAX_RESP,
            'Descr': 'CCS Vehicle Spd & Cruise & Park & Brakes',
            'Header': ECU_ADDR_H,
            'Response': [ # 07 61 21 = Header
                          # A=Cruise Control System speed, 0-200 km/h
                          # B=CCS memorized speed, 0-200 km/h
                          # 81 = normal (10000001); 7D = "R" Shift (01111101); 7E = "R" Shift transitory (01111110)
                          #
                          # {D:7}=Cruise Operation Status; Shift level in "D": 0/1=No/Yes
                          # {D:6}=Cruise Control, 0/1=Off/On
                          # {D:5}=Cruise active, 0/1=Off/On [TBV]
                          # {D:4}=Cruise active, 0/1=Off/On [TBV]
                          # {D:3}=Cruise active, 0/1=Off/On [TBV]
                          # {D:2}=Cruise active, 0/1=Off/On [TBV]
                          # {D:1}=Cruise transitory state?, 0/1=Off/On [TBV]
                          # {D:0}=Cruise transitory state?, 0/1=Off/On [TBV]
                          #
                          # {E:7}=Stop Light Switch 1, 0/1=Off/On (only full brake)
                          # {E:6}=Stop Light Switch 2, 0/1=Off/On (light or full brake)
                          # {E:5}=Brake, 0/1=Off/On (light or full brake)
                          # {E:4}=RES/ACC Switch, 0/1=Off/On
                          # {E:3}=SET/COAST Switch, 0/1=Off/On
                          # {E:2}=Cancel Switch, 0/1=Off/On
                          #                        A  B  C  D  E
                        ECU_R_ADDR_H + ' 07 61 21 00 00 81 00 00 \r', # Park + No brakes
                        ECU_R_ADDR_H + ' 07 61 21 00 00 81 3F 00 \r', # Cruise on (transitory)
                        ECU_R_ADDR_H + ' 07 61 21 00 00 7D 00 00 \r', # "R" shift (reverse)
                        ECU_R_ADDR_H + ' 07 61 21 00 00 81 80 00 \r', # "D" shift (ahead)
                        ECU_R_ADDR_H + ' 07 61 21 00 00 81 03 00 \r',
                        ECU_R_ADDR_H + ' 07 61 21 00 00 81 00 E0 \r', # Park + Brakes
                        ECU_R_ADDR_H + ' 07 61 21 00 00 81 00 60 \r', # Park + Light brakes
                        ECU_R_ADDR_H + ' 07 61 21 00 00 81 00 04 \r', # Cruise control Cancel
                        ECU_R_ADDR_H + ' 07 61 21 00 00 81 00 10 \r', # Cruise control Up
                        ECU_R_ADDR_H + ' 07 61 21 00 00 81 00 08 \r', # Cruise control Down
                        ECU_R_ADDR_H + ' 07 61 21 00 00 81 3C 00 \r'  # Cruise on
                        ]
        },
        'CUSTOM_P': {
            'Request': '^2125' + ELM_MAX_RESP,
            'Descr': 'Shift Sensor SW - P',
            'Equation': '{A:7}',
            'Min': '0',
            'Max': '1',
            'Unit': 'Off/On',
            'Header': ECU_ADDR_H,
            'Response': [
                        ECU_R_ADDR_H + ' 04 61 25 00 40 \r',
                        ECU_R_ADDR_H + ' 04 61 25 02 00 \r',
                        ECU_R_ADDR_H + ' 04 61 25 00 00 \r'
                        ]
        },
        'CUSTOM_ODO': {
            'Request': '^2128' + ELM_MAX_RESP,
            'Descr': 'Total Distance Traveled',
            'Equation': 'A * 256 * 256 + B * 256 + C',
            'Min': '0',
            'Max': '16777215',
            'Unit': 'km',
            'Header': ECU_ADDR_H,
            'Response': ECU_R_ADDR_H + ' 05 61 28 00 EA 5C \r'
        },
        'CUSTOM_SHIFT_J': {
            'Request': '^2141' + ELM_MAX_RESP,
            'Descr': 'Shift Joystick',
            'Header': ECU_ADDR_H,
            'Response': [
                        # UD: 6x (6D, 6E), 7x = centre; Cx = down; 1x = up. LR: 4A = right, B5 = left)
                        # LR1: 4a/49 (right), b3, b2, b5, b6 (left)
                        # First group:               UD UD LR LR1 [UD=up-down-centre, LR=left-right]
                        # Second group:     AA BB
                        # AA = 36, 38, 3A
                        # BB = (Park button pressed) 3A, 3B, 3C, 43, 75 (off), 88, 89, 90 (Park released)
                        ECU_R_ADDR_H + ' 10 08 61 41 6D 6D 4A 4A \r' + # default position (center, right)
                        ECU_R_ADDR_H + ' 21 38 89 00 00 00 00 00 \r',  # park button released
                        ECU_R_ADDR_H + ' 10 08 61 41 6D 6D 4A 4A \r' + # default position
                        ECU_R_ADDR_H + ' 21 38 3B 00 00 00 00 00 \r',  # park button pressed
                        ECU_R_ADDR_H + ' 10 08 61 41 6D 6D 4A 49 \r' + # center, middle
                        ECU_R_ADDR_H + ' 21 38 89 00 00 00 00 00 \r',
                        ECU_R_ADDR_H + ' 10 08 61 41 6D 6D 4A B3 \r' + # center, middle
                        ECU_R_ADDR_H + ' 21 38 89 00 00 00 00 00 \r',
                        ECU_R_ADDR_H + ' 10 08 61 41 6D 6D B5 B2 \r' + # moved to "N" position (center, left)
                        ECU_R_ADDR_H + ' 21 38 89 00 00 00 00 00 \r',
                        ECU_R_ADDR_H + ' 10 08 61 41 BE BE 4A 4A \r' + # moved to "B" position (down, right)
                        ECU_R_ADDR_H + ' 21 38 89 00 00 00 00 00 \r',
                        ECU_R_ADDR_H + ' 10 08 61 41 C5 C6 B5 B2 \r' + # moved to "D" position (down, left)
                        ECU_R_ADDR_H + ' 21 38 89 00 00 00 00 00 \r',
                        ECU_R_ADDR_H + ' 10 08 61 41 1A 1B B5 B2 \r' + # moved to "R" position (up, left)
                        ECU_R_ADDR_H + ' 21 38 89 00 00 00 00 00 \r',
                        ECU_R_ADDR_H + ' 10 08 61 41 6D 6D 4B 4A \r' + # default (center, right)
                        ECU_R_ADDR_H + ' 21 36 89 00 00 00 00 00 \r',
                        ECU_R_ADDR_H + ' 10 08 61 41 C4 C4 4A 49 \r' + # moved to "B" position (down, right)
                        ECU_R_ADDR_H + ' 21 38 89 00 00 00 00 00 \r',
                        ECU_R_ADDR_H + ' 10 08 61 41 1B 1B B5 B2 \r' + # moved to "R" position (up, left)
                        ECU_R_ADDR_H + ' 21 38 89 00 00 00 00 00 \r',
                        ECU_R_ADDR_H + ' 10 08 61 41 C4 C4 B5 B2 \r' + # moved to "D" position (down, left)
                        ECU_R_ADDR_H + ' 21 38 89 00 00 00 00 00 \r',
                        ECU_R_ADDR_H + ' 10 08 61 41 70 70 B5 B2 \r' + # moved to "N" position (center, left)
                        ECU_R_ADDR_H + ' 21 38 89 00 00 00 00 00 \r',
                        ECU_R_ADDR_H + ' 10 08 61 41 6E 6E B5 B2 \r' + # moved to "N" position (center, left)
                        ECU_R_ADDR_H + ' 21 38 89 00 00 00 00 00 \r',
                        ECU_R_ADDR_H + ' 10 08 61 41 6E 6E 4A 4A \r' + # default (center, right)
                        ECU_R_ADDR_H + ' 21 38 89 00 00 00 00 00 \r'
                        ]
        },
        'CUSTOM_SMRP': {
            'Request': '^2144' + ELM_MAX_RESP,
            'Descr': 'SMRP Status',
            'Equation': '{A:7}',
            'Min': '0',
            'Max': '1',
            'Unit': 'Off/On',
            'Header': ECU_ADDR_H,
            'Response': ECU_R_ADDR_H + ' 05 61 44 60 00 60 \r'
        },
        'CUSTOM_MG2_TORQ': {
            'Request': '^2168' + ELM_MAX_RESP,
            'Descr': 'MG2 torque',
            'Equation': '(A * 256 + B) / 8 - 4096',
            'Min': '-4096',
            'Max': '4095.875',
            'Unit': 'Nm',
            'Header': ECU_ADDR_H,
            'Response': [
                        ECU_R_ADDR_H + ' 07 61 68 80 00 80 00 00 \r',
                        ECU_R_ADDR_H + ' 07 61 68 7F 9B 7F AA 00 \r',
                        ECU_R_ADDR_H + ' 07 61 68 80 00 7F FC 00 \r',
                        ECU_R_ADDR_H + ' 07 61 68 80 2F 80 34 00 \r'
                        ]
        },
        'CUSTOM_KPH_7C0': {
            'Request': '^2121' + ELM_MAX_RESP,
            'Descr': 'Vehicle Speed Meter_7C0',
            'Equation': 'A',
            'Min': '0',
            'Max': '199',
            'Unit': 'km/h',
            'Header': ECU_ADDR_I,
            'Response': ECU_R_ADDR_I + ' 03 61 21 00 \r'
        },
        'CUSTOM_COOLANT_7C0': {
            'Request': '^2123' + ELM_MAX_RESP,
            'Descr': 'Coolant Temperature_7C0',
            'Equation': 'A / 2',
            'Min': '0',
            'Max': '127.5',
            'Unit': 'C',
            'Header': ECU_ADDR_I,
            'Response': ECU_R_ADDR_I + ' 03 61 23 47 \r'
        },
        'CUSTOM_H_S_I': {
            'Request': '^212B' + ELM_MAX_RESP,
            'Descr': 'HV System Indicator',
            'Equation': '{A:0} * 256 + B - {A:1} * 512',
            'Min': '-512',
            'Max': '511',
            'Unit': '%',
            'Header': ECU_ADDR_I,
            'Response': ECU_R_ADDR_I + ' 04 61 2B 02 00 \r'
        },
        'CUSTOM_KEYBUZ': {
            'Request': '^21A1' + ELM_MAX_RESP,
            'Descr': 'Key Remind Sound (buzzer/Normal, Fast, Slow)',
            'Equation': 'A',
            'Min': '0',
            'Max': '255',
            'Unit': '',
            'Header': ECU_ADDR_I,
            'Response': ECU_R_ADDR_I + ' 03 61 A1 18 \r'
        },
        'CUSTOM_A/M_STP_D': {
            'Request': '^2141' + ELM_MAX_RESP,
            'Descr': 'Air Mix Servo Targ Pulse (D)',
            'Equation': 'A + 128',
            'Min': '128',
            'Max': '383',
            'Unit': '',
            'Header': ECU_ADDR_P,
            'Response': ECU_R_ADDR_P + ' 06 61 41 1A 1A 00 00 \r'
        },
        'CUSTOM_STROKE': {
            'Request': '^2104' + ELM_MAX_RESP,
            'Descr': 'Stroke Sensor',
            'Equation': 'A / 51',
            'Min': '0',
            'Max': '5',
            'Unit': 'V',
            'Header': ECU_ADDR_S,
            'Response': [
                        ECU_R_ADDR_S + ' 06 61 04 29 D6 BF 19 \r',
                        ECU_R_ADDR_S + ' 06 61 04 29 D6 B8 19 \r',
                        ECU_R_ADDR_S + ' 06 61 04 29 D6 BE 19 \r',
                        ECU_R_ADDR_S + ' 06 61 04 3F BF B4 41 \r',
                        ECU_R_ADDR_S + ' 06 61 04 29 D6 B9 19 \r'
                        ]
        },
        'CUSTOM_DECELSEN': {
            'Request': '^2105' + ELM_MAX_RESP,
            'Descr': 'Deceleration Sensor',
            'Equation': 'A * 36.912 / 255 - 18.525',
            'Min': '-18.525',
            'Max': '18.387',
            'Unit': 'm/s2',
            'Header': ECU_ADDR_S,
            'Response': [
                        ECU_R_ADDR_S + ' 05 61 05 7F 80 1F \r',
                        ECU_R_ADDR_S + ' 05 61 05 7F 80 00 \r',
                        ECU_R_ADDR_S + ' 05 61 05 7E 80 00 \r'
                        ]
        },
        'CUSTOM_BRKFLUID': {
            'Request': '^211D' + ELM_MAX_RESP,
            'Descr': 'Reservoir Warning SW',
            'Equation': '{A:6}',
            'Min': '0',
            'Max': '1',
            'Unit': 'Off/On',
            'Header': ECU_ADDR_S,
            'Response': [
                        ECU_R_ADDR_S + ' 03 61 1D 00 \r',
                        ECU_R_ADDR_S + ' 03 61 1D 20 \r'
                        ]
        },
        'CUSTOM_STPSW': {
            'Request': '^211F' + ELM_MAX_RESP,
            'Descr': 'Stop Light SW',
            'Equation': '{A:7}',
            'Min': '0',
            'Max': '1',
            'Unit': 'Off/On',
            'Header': ECU_ADDR_S,
            'Response': [
                        ECU_R_ADDR_S + ' 03 61 1F 00 \r',
                        ECU_R_ADDR_S + ' 03 61 1F 80 \r'
                        ]
        },
        'CUSTOM_KPH_7B0': {
            'Request': '^2121' + ELM_MAX_RESP,
            'Descr': 'Vehicle Speed_7B0',
            'Equation': 'A * 326.4 / 255',
            'Min': '0',
            'Max': '200',
            'Unit': 'km/h',
            'Header': ECU_ADDR_S,
            'Response': ECU_R_ADDR_S + ' 03 61 21 00 \r'
        },
        'CUSTOM_STPRELAY': {
            'Request': '^213C' + ELM_MAX_RESP,
            'Descr': 'Stop Light Relay Output',
            'Equation': '{A:7}',
            'Min': '0',
            'Max': '1',
            'Unit': 'Off/On',
            'Header': ECU_ADDR_S,
            'Response': ECU_R_ADDR_S + ' 03 61 3C 00 \r'
        },
        'CUSTOM_ABS': {
            'Request': '^213D' + ELM_MAX_RESP,
            'Descr': 'ABS Warning Light',
            'Equation': '{A:7}',
            'Min': '0',
            'Max': '1',
            'Unit': 'Off/On',
            'Header': ECU_ADDR_S,
            'Response': ECU_R_ADDR_S + ' 04 61 3D 00 00 \r'
        },
        'CUSTOM_FR_WA': {
            'Request': '^2142' + ELM_MAX_RESP,
            'Descr': 'FR Wheel Acceleration',
            'Equation': '( A - {A:7} * 256 ) * 199.27 / 127',
            'Min': '-10',
            'Max': '10',
            'Unit': 'm/s2',
            'Header': ECU_ADDR_S,
            'Response': ECU_R_ADDR_S + ' 06 61 42 00 00 00 00 \r'
        },
        'CUSTOM_0DECEL': {
            'Request': '^2146' + ELM_MAX_RESP,
            'Descr': 'Zero Point of Decele',
            'Equation': 'A * 50.02 / 255 - 25.11',
            'Min': '-25.11',
            'Max': '24.91',
            'Unit': 'm/s2',
            'Header': ECU_ADDR_S,
            'Response': ECU_R_ADDR_S + ' 10 09 61 46 00 00 80 80 \r' +
                        ECU_R_ADDR_S + ' 21 00 01 14 00 00 00 00 \r'
        },
        'CUSTOM_REGENREQ': {
            'Request': '^2148' + ELM_MAX_RESP,
            'Descr': 'FR Regenerative Request',
            'Equation': '(A * 256 + B) * 16',
            'Min': '0',
            'Max': '400',
            'Unit': 'Nm',
            'Header': ECU_ADDR_S,
            'Response': ECU_R_ADDR_S + ' 06 61 48 00 00 00 00 \r'
        },
        'CUSTOM_TRAC': {
            'Request': '^215A' + ELM_MAX_RESP,
            'Descr': 'TRC(TRAC) Ctrl Status',
            'Equation': '{A:7}',
            'Min': '0',
            'Max': '1',
            'Unit': 'Off/On',
            'Header': ECU_ADDR_S,
            'Response': [
                        ECU_R_ADDR_S + ' 04 61 5A 00 00 \r',
                        ECU_R_ADDR_S + ' 04 61 5A 18 00 \r',
                        ECU_R_ADDR_S + ' 04 61 5A 10 00 \r'
                        ]
        },
        'CUSTOM_FR_ABS': {
            'Request': '^215F' + ELM_MAX_RESP,
            'Descr': 'FR Wheel ABS Ctrl Status',
            'Equation': '{A:7}',
            'Min': '0',
            'Max': '1',
            'Unit': 'Off/On',
            'Header': ECU_ADDR_S,
            'Response': ECU_R_ADDR_S + ' 04 61 5F 00 00 \r'
        },
        'CUSTOM_0YAW2': {
            'Request': '^21A1' + ELM_MAX_RESP,
            'Descr': 'Zero Point of Yaw Rate2',
            'Equation': 'A -128',
            'Min': '-128',
            'Max': '127',
            'Unit': 'degrees/s',
            'Header': ECU_ADDR_S,
            'Response': ECU_R_ADDR_S + ' 03 61 A1 80 \r'
        },
    }
}
