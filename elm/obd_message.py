###########################################################################
# ELM327-emulator
# ELM327 Emulator for testing software interfacing OBDII via ELM327 adapter
# https://github.com/Ircama/ELM327-emulator
# (C) Ircama 2021 - CC-BY-NC-SA-4.0
###########################################################################

# List of known ECUs:
ECU_ADDR_J = "747"
ECU_R_ADDR_J = "74F"
ECU_ADDR_K = "7D2"
ECU_R_ADDR_K = "7DA"
ECU_ADDR_H = "7E2"  # HVECU address (Hybrid control module)
ECU_R_ADDR_H = "7EA"  # Responses sent by HVECU (Hybrid control module) 7E2/7EA
ECU_ADDR_E = "7E0"  # Engine control module ECU address
ECU_R_ADDR_E = "7E8"  # Responses sent by Engine ECU - ECM (engine control module) 7E0/7E8
ECU_ADDR_T = "7E1"  # Transmission control module ECU address (transmission control module)
ECU_R_ADDR_T = "7E9"  # Responses sent by Transmission ECU - TCM (transmission control module) 7E1/7E9
ECU_ADDR_U = "7E2"
ECU_R_ADDR_U = "7EA"
ECU_ADDR_M = "7E5"  # Continental power train ECU
ECU_R_ADDR_M = "7ED"  # Responses sent by the Continental power train ECU - 7E5/7ED
ECU_ADDR_I = "7C0"  # ICE ECU address
ECU_R_ADDR_I = "7C8"  # Responses sent by ICE ECU address 7C0/7C8
ECU_ADDR_B = "7E3"  # Traction Battery ECU address
ECU_R_ADDR_B = "7EB"  # Responses sent by Traction Battery ECU - 7E3/7EB
ECU_ADDR_P = "7C4"  # Air Conditioning
ECU_R_ADDR_P = "7CC"  # Responses sent by Air Conditioning ECU - 7C4/7CC
ECU_ADDR_S = "7B0"  # Skid Control address ECU
ECU_R_ADDR_S = "7B8"  # Responses sent by 7B0 Skid Control ECU 7B0/7B8

def SZ(size):
    return ('<size>' + size + '</size>')

def HD(header):
    return ('<header>' + header + '</header>')

def DT(data):
    return ('<data>' + data + '</data>')

def ST(writeln):
    return ('<writeln>' + writeln + '</writeln>')

def AW(answer):
    return ('<answer>' + answer + '</answer>')

def PA(pos_answer):
    return ('<pos_answer>' + pos_answer + '</pos_answer>')

def NA(neg_answer):
    return ('<neg_answer>' + neg_answer + '</neg_answer>')

ELM_R_OK = ST("OK")
ELM_R_UNKNOWN = ST("?")
ELM_FOOTER = r'[0123456]?$'
ELM_DATA_FOOTER = r'([0-9A-Z][0-9A-Z])+$'

# PID Dictionary


ObdMessage = {
    # AT Commands
    'AT' : {
        'AT_LONG_MSG': {
            'Request': '^ATAL$',
            'Descr': 'AT Allow long messages',
            'Exec': 'self.counters["cmd_long_msg"] = True',
            'Log': '"set Long Messages %s", self.counters["cmd_long_msg"]',
            'Response': ELM_R_OK
        },
        'AT_NORMAL_LENGTH': {
            'Request': '^ATNL$',
            'Descr': 'AT Enforce normal message length',
            'Exec': 'self.counters["cmd_long_msg"] = False',
            'Log': '"set Long Messages %s", self.counters["cmd_long_msg"]',
            'Response': ELM_R_OK
        },
        'AT_DESCR': {
            'Request': '^AT@1' + ELM_FOOTER,
            'Descr': 'AT Device description',
            'Response': ST("OBDII to RS232 Interpreter")
        },
        'AT_ID': {
            'Request': '^AT@2' + ELM_FOOTER,
            'Descr': 'AT Device identifier',
            'Response': ST('?')
        },
        'AT_STORE_ID': {
            'Request': '^AT@3' + ELM_FOOTER,
            'Descr': 'AT Store the device identifier',
            'Response': ST('?')
        },
        'AT_ADAPTIVE_TIMING': {
            'Request': '^ATAT[012]$',
            'Descr': 'AT Set adaptive timing mode',
            'Exec': 'self.counters["cmd_adaptive_t"] = cmd[4:] or None',
            'Log': '"Set adaptive timing %s", self.counters["cmd_adaptive_t"]',
            'Response': ELM_R_OK
        },
        'AT_BYPASS_INIT': {
            'Request': '^ATBI$',
            'Descr': 'AT Bypass the Initialization sequence',
            'Response': ELM_R_OK # ignored at the moment: just answer OK (to be revised)
        },
        'AT_CAF': {
            'Request': '^ATCAF[01]$',
            'Descr': 'AT CAN Automatic Formatting',
            'Exec': 'self.counters["cmd_caf"] = (cmd[5] == "1")',
            'Log': '"Set CAN Automatic Formatting ON/OFF : %s", '
                   'self.counters["cmd_caf"]',
            'Response': ELM_R_OK
        },
        'AT_CFC': {
            'Request': '^ATCFC[01]$',
            'Descr': 'AT CAN Fow Control',
            'Exec': 'self.counters["cmd_cfc"] = (cmd[5] == "1")',
            'Log': '"Set CAN Flow Control ON/OFF : %s", '
                   'self.counters["cmd_cfc"]',
            'Response': ELM_R_OK
        },
        'AT_FCSM': {
            'Request': '^ATFCSM[01]$',
            'Descr': 'AT Fow Control Set Mode',
            'Exec': 'self.counters["cmd_fcsm"] = (cmd[6] == "1")',
            'Log': '"Set Flow Control mode : %s", '
                   'self.counters["cmd_fcsm"]',
            'Response': ELM_R_OK
        },
        'AT_RESPONSES': {
            'Request': '^ATR[01]$',
            'Descr': 'AT Turn responses on or off',
            'Exec': 'self.counters["cmd_response"] = (cmd[3] == "1")',
            'Log': '"Set responses ON/OFF : %s", '
                   'self.counters["cmd_response"]',
            'Response': ELM_R_OK
        },
        'AT_SET_CAN_RX_ADDR': {
            'Request': '^ATCRA',
            'Descr': 'AT SET CAN RX Addr',
            'Exec': 'self.counters["cmd_cra"] = cmd[5:] or None',
            'Log': '"set CAN RX Addr %s", self.counters["cmd_cra"]',
            'Response': ELM_R_OK
        },
        'AT_BRD': {
            'Request': '^ATBRD',
            'Descr': 'AT Set UART baud rate divisor',
            'Exec': 'self.counters["cmd_brd"] = cmd[5:]',
            'Log': '"set UART baud rate divisor %s", '
                   'self.counters["cmd_brd"]',
            'Response': ELM_R_OK
        },
        'AT_BRT': {
            'Request': '^ATBRT',
            'Descr': 'AT Set UART baud rate timeout',
            'Exec': 'self.counters["cmd_brt"] = cmd[5:]',
            'Log': '"set UART baud rate timeout %s", '
                   'self.counters["cmd_brt"]',
            'Response': ELM_R_OK
        },
        'AT_DEFAULT': {
            'Request': '^ATD$',
            'Descr': 'AT DEFAULT',
            'Log': '"Set all configuration to defaults"',
            'Exec': 'self.reset(0.1)',
            'Response': ELM_R_OK
        },
        'AT_FI': {
            'Request': '^ATFI$',
            'Descr': 'AT FAST INIT',
            'Log': '"Perform a fast initiation"',
            'Response': ELM_R_OK
        },
        'AT_DKW': {
            'Request': '^ATKW$',
            'Descr': 'AT DISPLAY KEY WORDS',
            'Log': '"Display keywords"',
            'ResponseFooter': lambda self, cmd, pid, uc_val:
                self.counters["cmd_atkw"] if "cmd_atkw" in self.counters
                else "0"
        },
        'AT_SKW': {
            'Request': '^ATKW[01]$',
            'Descr': 'AT SET KEY WORDS',
            'Exec': 'self.counters["cmd_atkw"] = cmd[4:]',
            'Log': '"Set key words to %s", '
                   'self.counters["cmd_atkw"]',
            'Response': ELM_R_OK
        },
        'AT_V': {
            'Request': '^ATV[01]$',
            'Descr': 'AT SET VARIABLE DLC ON/OFF',
            'Exec': 'self.counters["cmd_atv"] = cmd[3:]',
            'Log': '"Set variable DLC to %s", '
                   'self.counters["cmd_atv"]',
            'Response': ELM_R_OK
        },
        'AT_DLC': {
            'Request': '^ATD[01]$',
            'Descr': 'AT Display of the DLC on/off',
            'Exec': 'self.counters["cmd_dlc"] = (cmd[3] == "1")',
            'Log': '"Set DLC %s", self.counters["cmd_dlc"]',
            'Response': ELM_R_OK # ignored at the moment: just answer OK (to be revised)
        },
        'AT_DESCRIBE_PROTO': {
            'Request': '^ATDP$',
            'Descr': 'AT set DESCRIBE PROTO',
            'Exec': 'time.sleep(0.5)',
            'Response': ST("ISO 15765-4 (CAN 11/500)")
        },
        'AT_DESCRIBE_PROTO_N': {
            'Request': '^ATDPN$',
            'Descr': 'AT Display Protocol Number',
            'Exec': 'time.sleep(0.5)',
            'Response': ST("A6")
        },
        'AT_ECHO': {
            'Request': '^ATE[01]$',
            'Descr': 'AT ECHO',
            'Exec': 'self.counters["cmd_echo"] = (not cmd[3] == "0")',
            'Log': '"set ECHO ON/OFF : %s", self.counters["cmd_echo"]',
            'Response': ELM_R_OK
        },
        'AT_USE_HEADERS': {
            'Request': '^ATH[01]$',
            'Descr': 'AT HEADERS',
            'Exec': 'self.counters["cmd_use_header"] = (cmd[3] == "1")',
            'Log': '"set HEADERS ON/OFF : %s", self.counters["cmd_use_header"]',
            'Response': ELM_R_OK
        },
        'AT_I': {
            'Request': '^ATI$',
            'Descr': 'AT ELM327 version string',
            'Response': ST("ELM327 v1.5")
        },
        'AT_IGN': {
            'Request': '^ATIGN$',
            'Descr': 'AT IgnMon input level',
            'Response': (ST("ON"), ST("OFF"))
        },
        'AT_LINEFEEDS': {
            'Request': '^ATL[01]$',
            'Descr': 'AT LINEFEEDS',
            'Exec': 'self.counters["cmd_linefeeds"] = (cmd[3] == "1")',
            'Log': '"set LINEFEEDS ON/OFF : %s", self.counters["cmd_linefeeds"]',
            'Response': ELM_R_OK
        },
        'AT_LP': {
            'Request': '^ATLP$',
            'Descr': 'AT Low Power mode',
            'Response': ELM_R_OK
        },
        'AT_MEMORY': {
            'Request': '^ATM[01]$',
            'Descr': 'AT Memory off or on',
            'Exec': 'self.counters["cmd_memory"] = (cmd[3] == "1")',
            'Log': '"set MEMORY ON/OFF : %s", self.counters["cmd_memory"]',
            'Response': ELM_R_OK
        },
        'AT_R_VOLT': {
            'Request': '^ATRV$',
            'Descr': 'AT read volt',
            'Log':
            '"Volt = {:.1f}".format('
            '0.1 * abs(9 - (self.counters[pid] + 9) % 18) + 13)',
            'ResponseHeader': \
            lambda self, cmd, pid, uc_val: \
                "<string>{:.1f}</string>".format( \
                    0.1 * abs(9 - (self.counters[pid] + 9) % 18) + 13),
            'Response': ST("V")
        },
        'AT_SPACES': {
            'Request': '^ATS[01]$',
            'Descr': 'AT Spaces off or on',
            'Exec': 'self.counters["cmd_spaces"] = (cmd[3] == "1")',
            'Log': '"set SPACES %s", self.counters["cmd_spaces"]',
            'Response': ELM_R_OK
        },
        'AT_SET_HEADER': {
            'Request': '^ATSH[0-9A-F]+$',
            'Descr': 'AT SET HEADER',
            'Exec': 'self.counters["cmd_set_header"] = '
                    're.sub(r"^0*([0-9A-F]+)$", r"\\1", cmd[4:])',
            'Log': '"Set HEADER to <%s>", self.counters["cmd_set_header"]',
            'Response': ELM_R_OK
        },
        'AT_CAN_HFM': {
            'Request': '^ATCM[0-9A-F]+$',
            'Descr': 'AT Set the CAN hardware filter mask',
            'Exec': 'self.counters["cmd_hfm"] = '
                    're.sub(r"^0*([0-9A-F]+)$", r"\\1", cmd[4:])',
            'Log': '"Set CAN hardware filter mask to <%s>", '
                   'self.counters["cmd_hfm"]',
            'Response': ELM_R_OK
        },
        'AT_CAN_FP': {
            'Request': '^ATCF[0-9A-F]+$',
            'Descr': 'AT Set the CAN hardware filter pattern',
            'Exec': 'self.counters["cmd_cfp"] = '
                    're.sub(r"^0*([0-9A-F]+)$", r"\\1", cmd[4:])',
            'Log': '"Set CAN hardware filter pattern to <%s>", '
                   'self.counters["cmd_cfp"]',
            'Response': ELM_R_OK
        },
        'AT_WAKEUP': {
            'Request': '^ATSW[0-9A-F]+$',
            'Descr': 'AT Set wakeup',
            'Exec': 'self.counters["cmd_wakeup"] = cmd[4:]',
            'Log': '"Set wakeup to <%s>", '
                   'self.counters["cmd_wakeup"]',
            'Response': ELM_R_OK
        },
        'AT_FCSH': {
            'Request': '^ATFCSH',
            'Descr': 'AT FLOW CONTROL SET HEADER',
            'Exec': 'self.counters["cmd_fcsh"] = cmd[6:] or None',
            'Log': '"set FLOW CONTROL set HEADER %s", '
                   'self.counters["cmd_fcsh"]',
            'Response': ELM_R_OK
        },
        'AT_FCSD': {
            'Request': '^ATFCSD',
            'Descr': 'AT FLOW CONTROL SET DATA',
            'Exec': 'self.counters["cmd_fcsd"] = cmd[6:] or None',
            'Log': '"set FLOW CONTROL set DATA %s", '
                   'self.counters["cmd_fcsd"]',
            'Response': ELM_R_OK
        },
        'AT_FCSM': {
            'Request': '^ATFCSM[0-2]$',
            'Descr': 'AT FLOW CONTROL SET MODE',
            'Exec': 'self.counters["cmd_fcsm"] = cmd[6:] or None',
            'Log': '"set FLOW CONTROL set MODE %s", '
                   'self.counters["cmd_fcsm"]',
            'Response': ELM_R_OK
        },
        'AT_ISO_BAUD': {
            'Request': '^ATIB[149][086]$',
            'Descr': 'AT Set ISO baud rate to 10400, 4800, or 9600 baud',
            'Exec': 'self.counters["cmd_iso_baud"] = cmd[4:] or None',
            'Log': '"Set ISO baud rate to: %s", self.counters["cmd_iso_baud"]',
            'Response': ELM_R_OK
        },
        'AT_PROTO': {
            'Request': '^ATSP[0-9A-C]$',
            'Descr': 'AT PROTO',
            'Exec': 'self.counters["cmd_proto"] = cmd[4] or None',
            'Log': '"set PROTO %s", self.counters["cmd_proto"]',
            'Response': ELM_R_OK
        },
        'AT_SET_RECEIVE_ADDR': {
            'Request': '^ATSR[0-9A-F]+$',
            'Descr': 'AT Set Receive Address',
            'Exec': 'self.counters["cmd_rec_addr"] = cmd[4:]',
            'Log': '"Set Receive Address to %s", '
                   'self.counters["cmd_rec_addr"]',
            'Response': ELM_R_OK
        },
        'AT_ISO_INIT_ADDR': {
            'Request': '^ATIIA[0-9A-F]+$',
            'Descr': 'AT Set the ISO 5-baud init address',
            'Exec': 'self.counters["cmd_iia"] = int(cmd[5:], 16)',
            'Log': '"Set init address to %s", self.counters["cmd_iia"]',
            'Response': ELM_R_OK
        },
        'AT_TRY_PROTO': {
            'Request': '^ATTP[0-9A-F]+$',
            'Descr': 'AT TRY PROTO',
            'Exec': 'self.counters["cmd_try_proto"] = int(cmd[4:], 16)',
            'Log': '"Try protocol %s", self.counters["cmd_try_proto"]',
            'Response': ELM_R_OK
        },
        'AT_TEST_ADDR': {
            'Request': '^ATTA[0-9A-F][0-9A-F]$',
            'Descr': 'AT Set tester address to hh.',
            'Exec': 'self.counters["cmd_test_add"] = cmd[4:] or None',
            'Log': '"Set tester address to %s", '
                   'self.counters["cmd_test_add"]',
            'Response': ELM_R_OK
        },
        'AT_WARM_START': {
            'Request': '^ATWS$',
            'Descr': 'AT WARM START',
            'Log': '"Warm start and sleep 0.1 seconds"',
            #'Exec': 'self.reset(0.1)',
            'Response': ST('') + ST("ELM327 v1.5")
        },
        'AT_RESET': {
            'Request': '^ATZ$',
            'Descr': 'AT RESET',
            'Log': '"Reset and sleep 0.5 seconds"',
            'Exec': 'self.reset(0.5)',
            'Response': ST('') + ST('') + ST("ELM327 v1.5")
        },
        'AT_SET_TIMEOUT': {
            'Request': '^ATST[0-9A-F]+$',
            'Descr': 'AT SET TIMEOUT',
            'Exec': 'self.counters["cmd_timeout"] = int(cmd[4:], 16)',
            'Log': '"Set timeout %s", self.counters["cmd_timeout"]',
            'Response': ELM_R_OK
        },
        'AT_CEA': {
            'Request': '^ATCEA',
            'Descr': 'AT CAN EXTENDED ADDRESS',
            'Exec': 'self.counters["cmd_cea"] = cmd[5:] or None',
            'Log': '"set CEA %s", self.counters["cmd_cea"]',
            'Response': ELM_R_OK
        },
        'AT_PC': {
            'Request': '^ATPC$',
            'Descr': 'AT PROTOCOL CLOSE',
            'Response': ELM_R_OK
        },
        'AT_SLOW_INIT': {
            'Request': '^ATSI$',
            'Descr': 'AT Slow (5-baud) initialization',
            'Response': ELM_R_OK
        },
        'AT_AR': {
            'Request': '^ATAR$',
            'Descr': 'AT Automatically set the Receive Address',
            'Response': ELM_R_OK
        },
        'AT_BD': {
            'Request': '^ATBD$',
            'Descr': 'AT Buffer dump',
            'Response': ST("00 00 00 00 00 00 00 00 00 00 00 00 00")
        },
        'AT_PPS': {
            'Request': '^ATPPS$',
            'Descr': 'AT Print programmable parameter summary.',
            'Response': ST('00:FF F 01:FF F 02:FF F 03:32 F') +
                        ST('04:01 F 05:FF F 06:F1 F 07:09 F') +
                        ST('08:FF F 09:00 F 0A:0A F 0B:FF F') +
                        ST('0C:68 F 0D:0D F 0E:FF F 0F:FF F') +
                        ST('10:0D F 11:00 F 12:FF F 13:32 F') +
                        ST('14:FF F 15:FF F 16:FF F 17:92 F') +
                        ST('18:00 F 19:FF F 1A:FF F 1B:FF F') +
                        ST('1C:FF F 1D:FF F 1E:FF F 1F:FF F') +
                        ST('20:FF F 21:FF F 22:FF F 23:FF F') +
                        ST('24:00 F 25:00 F 26:00 F 27:FF F') +
                        ST('28:FF F 29:FF F 2A:38 F 2B:02 F') +
                        ST('2C:E0 F 2D:04 F 2E:80 F 2F:0A F')
        },
        'AT_MA': {
            'Request': '^ATMA$',
            'Descr': 'AT Monitor all messages',
            'Response': ST('C4 ') + ST('245 00 ') +
                        ST('247 06 00200283 00 3127 00 ') +
                        ST('260 0262 01 00 ') + ST('020 00 ') +
                        ST('0B4 002344 000AA 1A 6F 1A 6212127 00 ') +
                        ST('2247 06 020200260 411 0040AA 1A 6F 283 00 ') +
                        ST('020 00 ') +
                        ST('0B4 00 001273F9 58 5C 560AA 1 22245 00 '
                           '3A026247020 02006262 0139B 0127 00 ') +
                        ST('1394 0020 00 ') + ST('0B4 00 ') +
                        ST('0250344 00 260 08 FF F1STOPPED') + ST('') +
                        ST('>TMA') + ST('?') + ST('') + ST('>ATMA') +
                        ST('0AA 1A 6F 1A 6F 1A 6F 1A 6F ') +
                        ST('224 00 ') + ST('127 00 ') + ST('344 00 ') +
                        ST('260 08 FF F2 00 00 FF F2 54 A3 ') + ST('020 00 ') +
                        ST('230 00 ') + ST('025 00 ') + ST('024 01 FD ') +
                        ST('1C4 06 7D 00 00 00 00 00 ') +
                        ST('48B 80 05 05 05 00 00 00 00 ') +
                        ST('245 00 ') + ST('0AA 1A 6F 1A 6F 1A 6F 1A 6F ') +
                        ST('2A4 00 ') + ST('361 80 00 00 00 01 FD 01 FB ') +
                        ST('38B 00 ') + ST('247 06 00 FF 00 00 00 00 ') +
                        ST('413 01 01 ') + ST('127 00 ') + ST('020 00 ') +
                        ST('0B4 00 ') + ST('025 00 ') +
                        ST('02266 10 342F 283 23')
        },
        #------------------------------------------------------------
        # ST Extensions used to configure the STN11xx family of OBD interpreters
        'ST_PROTO': {
            'Request': '^STP[0-9]+$',
            'Descr': 'ST Set current protocol',
            'Exec': 'self.counters["cmd_st_proto"] = int(cmd[3:])',
            'Log': '"Set current protocol %s", self.counters["cmd_st_proto"]',
            'Response': ELM_R_OK
        },
        '^ST_SLX': {
            'Request': '^STSLX',
            'Descr': 'AT Enable or disable sleep/wakeup triggers',
            'Exec': 'self.counters["cmd_st_slx"] = cmd[5:] or None',
            'Log': '"set sleep/wakeup triggers %s", '
                   'self.counters["cmd_st_slx"]',
            'Response': ELM_R_OK
        },
        'ST_SERIAL_NUMBER': {
            'Request': '^STSN$',
            'Descr': 'ST Print the device serial number.',
            'Response': ST("110012345678")
        },
        'ST_REPORT_PROTOCOL': {
            'Request': '^STPR$',
            'Descr': 'ST Report current protocol number.',
            'Exec': 'time.sleep(0.5)',
            'Response': ST("A6")
        },
        'ST_DI': {
            'Request': '^STDI$',
            'Descr': 'AT Print device hardware ID string.',
            'Response': ST("OBDLink r1.7")
        },
        'ST_ID': {
            'Request': '^STI$',
            'Descr': 'ST Print firmware ID string',
            'Response': ST("STN1100 v1.2.3")
        },
        'ST_IP4': {
            'Request': '^STIP4[ 0-9]*$',
            'Descr': 'Set Tx Interbyte delay: ms',
            'Exec': 'self.counters["cmd_stip4"] = cmd[5:]',
            'Log': '"Set Tx Interbyte delay %s", self.counters["cmd_stip4"]',
            'Response': ELM_R_OK
        },
        'ST_PTO': {
            'Request': '^STPTO[ 0-9]*$',
            'Descr': 'Set OBD Request Timeout',
            'Exec': 'self.counters["cmd_stpto"] = cmd[5:]',
            'Log': '"Set OBD Request Timeout %s", self.counters["cmd_stpto"]',
            'Response': ELM_R_OK
        },
        'ST_SET_BAUD_RATE': {
            'Request': '^STPBR *[1-9][0-9]*$',
            'Descr': 'ST Set baud rate',
            'Response': ELM_R_OK
        },
        'ST_SET_BAUD_RATE_1': {
            'Request': '^STSBR *[1-9][0-9]*$',
            'Descr': 'ST Set baud rate',
            'Response': ST("STN1101 v2.1.0")
        },
        'ST_STCCFCP': {
            'Request': '^STCCFCP$',
            'Descr': 'ST Clear all CAN flow control address pairs.',
            'Response': ELM_R_OK
        },
        'ST_STCFCPC': {
            'Request': '^STCFCPC$',
            'Descr': 'ST Clear all flow control address pairs.',
            'Response': ELM_R_OK
        },
        'ST_STCAFCP': {
            'Request': '^STCAFCP[0-9A-F, ]+$',
            'Descr': 'ST Add CAN flow control address pair.',
            'Exec': 'self.counters["cmd_st_fcap"] = cmd[7:] or None',
            'Log': '"Add CAN flow control CAN %s", self.counters["cmd_st_fcap"]',
            'Response': ELM_R_OK
        },
        'ST_STCFCPA': {
            'Request': '^STCFCPA[0-9A-F, ]+$',
            'Descr': 'ST Add a flow control CAN address pair.',
            'Exec': 'self.counters["cmd_st_fcap"] = cmd[7:] or None',
            'Log': '"Add a flow control CAN %s", self.counters["cmd_st_fcap"]',
            'Response': ELM_R_OK
        },
    },
    # OBD Commands
    'engineoff' : {
        'ELM_PIDS_A': {
            'Request': '^0100$',
            'Descr': 'PIDS_A',
            'ResponseHeader': \
            lambda self, cmd, pid, uc_val: \
                '<string>SEARCHING...</string>'
                '<exec>time.sleep(4.5)</exec>' + ST('') + \
                ST('UNABLE TO CONNECT') \
                if self.counters[pid] == 1 else \
                self.choice([ST('NO DATA'), ST('BUS INIT:ERROR')]),
            'Priority': 5
        },
        'ELM_MIDS_A': {
            'Request': '^0600$',
            'Descr': 'MIDS_A',
            'ResponseHeader': \
            lambda self, cmd, pid, uc_val: \
                '<string>SEARCHING...</string>'
                '<exec>time.sleep(4.5)</exec>' + ST('') + \
                ST('UNABLE TO CONNECT') \
                if self.counters[pid] == 1 else \
                self.choice([ST('NO DATA'), ST('BUS INIT:ERROR')]),
            'Priority': 5
        },
        'AT_DESCRIBE_PROTO_N': {
            'Request': '^ATDPN$',
            'Descr': 'set DESCRIBE_PROTO_N',
            'Exec': 'time.sleep(0.5)',
            'Response': ST("A0")
        },
        'NO_DATA': {
            'Request': '^[0-9][0-9][0-9A-F]+$',
            'Descr': 'NO_DATA',
            'Response': ST('NO DATA'),
            'Priority': 6
        },
    },
    'default' : {
        # Mode 01 Sending diagnostic data (PID data monitor/on-board system readiness test)
        'FUEL_STATUS': {
            'Request': '^0103' + ELM_FOOTER,
            'Descr': 'Fuel System Status',
            'Response': PA('00 00')
        },
        'ENGINE_LOAD': {
            'Request': '^0104' + ELM_FOOTER,
            'Descr': 'Calculated Engine Load',
            'Response': PA('00')
        },
        'COOLANT_TEMP': {
            'Request': '^0105' + ELM_FOOTER,
            'Descr': 'Engine Coolant Temperature',
            'Response': PA('7B')
        },
        'INTAKE_PRESSURE': {
            'Request': '^010B' + ELM_FOOTER,
            'Descr': 'Intake Manifold Pressure',
            'Response': PA('73')
        },
        'RPM': {
            'Request': '^010C' + ELM_FOOTER,
            'Descr': 'Engine RPM',
            'ResponseFooter': \
            lambda self, cmd, pid, uc_val: (
                PA(self.sequence(
                    pid, base=2400, max=200, factor=80, n_bytes=2))
                + ' ' + HD(ECU_R_ADDR_H) + SZ('04') + DT('41 0C '
                + self.sequence(pid, base=2400, max=200, factor=80, n_bytes=2))
            )
        },
        'SPEED': {
            'Request': '^010D' + ELM_FOOTER,
            'Descr': 'Vehicle Speed',
            'ResponseFooter': \
            lambda self, cmd, pid, uc_val: (
                PA(self.sequence(pid, base=0, max=30, factor=4, n_bytes=1))
                + ' ' + HD(ECU_R_ADDR_H) + SZ('03') + DT('41 0D '
                + self.sequence(pid, base=0, max=30, factor=4, n_bytes=1))
            )
        },
        'INTAKE_TEMP': {
            'Request': '^010F' + ELM_FOOTER,
            'Descr': 'Intake Air Temp',
            'Response': PA('44')
        },
        'MAF': {
            'Request': '^0110' + ELM_FOOTER,
            'Descr': 'Air Flow Rate (MAF)',
            'Response': PA('05 1F')
        },
        'THROTTLE_POS': {
            'Request': '^0111' + ELM_FOOTER,
            'Descr': 'Throttle Position',
            'Response': PA('FF')
        },
        'OBD_COMPLIANCE': {
            'Request': '^011C' + ELM_FOOTER,
            'Descr': 'OBD Standards Compliance',
            'Response': PA('06')
        },
        'RUN_TIME': {
            'Request': '^011F' + ELM_FOOTER,
            'Descr': 'Engine Run Time',
            'Response': PA('00 8C')
        },
        'DISTANCE_W_MIL': {
            'Request': '^0121' + ELM_FOOTER,
            'Descr': 'Distance Traveled with MIL on',
            'Response': PA('00 00')
        },
        'FUEL_RAIL_PRESSURE_DIRECT': {
            'Request': '^0123' + ELM_FOOTER,
            'Descr': 'Fuel Rail Pressure (direct inject)',
            'Response': PA('1A 0E')
        },
        'COMMANDED_EGR': {
            'Request': '^012C' + ELM_FOOTER,
            'Descr': 'Commanded EGR',
            'Response': PA('0D')
        },
        'EGR_ERROR': {
            'Request': '^012D' + ELM_FOOTER,
            'Descr': 'EGR Error',
            'Response': PA('80')
        },
        'DISTANCE_SINCE_DTC_CLEAR': {
            'Request': '^0131' + ELM_FOOTER,
            'Descr': 'Distance traveled since codes cleared',
            'Response': PA('C8 1F')
        },
        'BAROMETRIC_PRESSURE': {
            'Request': '^0133' + ELM_FOOTER,
            'Descr': 'Barometric Pressure',
            'Response': PA('65')
        },
        'CATALYST_TEMP_B1S1': {
            'Request': '^013C' + ELM_FOOTER,
            'Descr': 'Catalyst Temperature: Bank 1 - Sensor 1',
            'Response': PA('04 44')
        },
        'CONTROL_MODULE_VOLTAGE': {
            'Request': '^0142' + ELM_FOOTER,
            'Descr': 'Control module voltage',
            'Response': PA('39 D6')
        },
        'AMBIANT_AIR_TEMP': {
            'Request': '^0146' + ELM_FOOTER,
            'Descr': 'Ambient air temperature',
            'Response': PA('43')
        },
        'ACCELERATOR_POS_D': {
            'Request': '^0149' + ELM_FOOTER,
            'Descr': 'Accelerator pedal position D',
            'Response': PA('00')
        },
        'ACCELERATOR_POS_E': {
            'Request': '^014A' + ELM_FOOTER,
            'Descr': 'Accelerator pedal position E',
            'Response': PA('45')
        },
        'THROTTLE_ACTUATOR': {
            'Request': '^014C' + ELM_FOOTER,
            'Descr': 'Commanded throttle actuator',
            'Response': PA('00')
        },
        'RUN_TIME_MIL': {
            'Request': '^014D' + ELM_FOOTER,
            'Descr': 'Time run with MIL on',
            'Response': PA('00 00')
        },
        'TIME_SINCE_DTC_CLEARED': {
            'Request': '^014E' + ELM_FOOTER,
            'Descr': 'Time since trouble codes cleared',
            'Response': PA('4C 69')
        },
        'FUEL_TYPE': {
            'Request': '^0151' + ELM_FOOTER,
            'Descr': 'Fuel Type',
            'Response': PA('01')
        },
        'FUEL_INJECT_TIMING': {
            'Request': '^015D' + ELM_FOOTER,
            'Descr': 'Fuel injection timing',
            'Response': PA('66 00')
        },
        # Supported PIDs for protocols
        'ELM_PIDS_A': {
            'Request': '^0100' + ELM_FOOTER,
            'Descr': 'PIDS_A',
            'ResponseHeader': \
                lambda self, cmd, pid, uc_val: \
                    '<string>SEARCHING...</string>'
                    '<exec>time.sleep(3)</exec>' + ST('') \
                        if self.counters[pid] == 1 else "",
            'Response':
            HD(ECU_R_ADDR_H) + SZ('06') + DT('41 00 98 3A 80 13') +
            PA('BE 3F A8 13')
        },
        'ELM_PIDS_B': {
            'Request': '^0120' + ELM_FOOTER,
            'Descr': 'PIDS_B',
            'Response':
            HD(ECU_R_ADDR_H) + SZ('06') + DT('41 20 80 01 A0 01') +
            PA('90 15 B0 15')
        },
        'ELM_PIDS_C': {
            'Request': '^0140' + ELM_FOOTER,
            'Descr': 'PIDS_C',
            'Response':
            HD(ECU_R_ADDR_H) + SZ('06') + DT('41 40 44 CC 00 21') +
            PA('7A 1C 80 00')
        },
        # Mode 06 Sending intermittent monitoring system test results (DMTR)
        'ELM_MIDS_A': {
            'Request': '^0600' + ELM_FOOTER,
            'Descr': 'MIDS_A',
            'Response': PA('C0 00 00 01')
        },
        'ELM_MIDS_B': {
            'Request': '^0620' + ELM_FOOTER,
            'Descr': 'MIDS_B',
            'Response': PA('80 00 80 01')
        },
        'ELM_MIDS_C': {
            'Request': '^0640' + ELM_FOOTER,
            'Descr': 'MIDS_C',
            'Response': PA('00 00 00 01')
        },
        'ELM_MIDS_D': {
            'Request': '^0660' + ELM_FOOTER,
            'Descr': 'MIDS_D',
            'Response': PA('00 00 00 01')
        },
        'ELM_MIDS_E': {
            'Request': '^0680' + ELM_FOOTER,
            'Descr': 'MIDS_E',
            'Response': PA('00 00 00 01')
        },
        'ELM_MIDS_F': {
            'Request': '^06A0' + ELM_FOOTER,
            'Descr': 'MIDS_F',
            'Response': PA('F8 00 00 00')
        },
        # Mode 07 Sending continuous monitoring system test results (pending code)
        # Mode 09 Request vehicle information
        'ELM_PIDS_9A': {
            'Request': '^0900' + ELM_FOOTER,
            'Descr': 'PIDS_9A',
            'Response': PA('FF FF FF FF')
        },
        'VIN_MESSAGE_COUNT': {
            'Request': '^0901' + ELM_FOOTER,
            'Descr': 'VIN Message Count',
            'Response': PA('01')
        },
        'VIN': { # Check this also: https://stackoverflow.com/a/26752855/10598800, https://www.autocheck.com/vehiclehistory/autocheck/en/vinbasics
            'Request': '^0902' + ELM_FOOTER,
            'Descr': 'Vehicle Identification Number',
            'Response': [
                        PA("01 57 50 30 5A 5A 5A 39 39 "
                           "5A 54 53 33 39 30 30 30 30"), # https://www.autodna.com/vin/WP0ZZZ99ZTS390000, https://it.vin-info.com/libro-denuncia/WP0ZZZ99ZTS390000
                        PA("01 4D 41 54 34 30 33 30 39 "
                           "36 42 4E 4C 30 30 30 30 30"), # https://community.carloop.io/t/how-to-request-vin/153/11
                        ]
        },
        'CALIBRATION_ID_MESSAGE_COUNT': {
            'Request': '^0903' + ELM_FOOTER,
            'Descr': 'Calibration ID message count for PID 04',
            'Response': PA('01')
        },
        'PERF_TRACKING_COMPRESSION': {
            'Request': '^090B' + ELM_FOOTER,
            'Descr': 'In-use performance tracking (compression ignition)',
            'Response': PA('00 00')
        },
        # UDS raw
        'UNKNOWN_00': {
            'Request': '^00$',
            'Descr': 'UNKNOWN_00',
            'Response': AW('7B 00')
        },
        'UDS_STDS_FLASH': {
            'Request': '^1085' + ELM_FOOTER, # 85 = Flash Programming Session
            'Descr': 'UDS Start Diagnostic Session - ECU Prog Mode',
            'Response': PA('')
        },
        'UDS_ECU_RESET': {
            'Request': '^1101' + ELM_FOOTER,
            'Descr': 'EcuReset',
            'Response': PA('')
        },
        'CLEAR_DTC': {
            'Request': '^14' + ELM_DATA_FOOTER,
            'Descr': 'Clear DTC',
            'ResponseFooter': lambda self, cmd, pid, uc_val: (
                self.choice([NA('78'), PA(cmd[2:])])
            )
        },
        'UNKNOWN_2100_E': {
            'Request': '^2100' + ELM_FOOTER,
            'Descr': 'UNKNOWN_2100',
            'Response': PA(
                '4A4D5A424B313459323731353437303037FFFFFFFF2AFFFFFF'
                'FF033D0DA4FFFF9641FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF'
                'FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF0000FFFFFFFF'
                'FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF'
                'FFFFFFFFFFFFFFFFFFFFFFFFFFFFFF36C9FF30')
        },
        'ECU_IVN_HW': {
            'Request': '^2103' + ELM_FOOTER,
            'Descr': 'ECU internal version numbers - Hardware Part Number',
            'Response': PA('46 31'),
        },
        'DTC_CNT': {
            'Request': '^220000' + ELM_FOOTER,
            'Descr': "Number of DTC's (if any)",
            'Response': PA('00BE3FA813')
        },
        'UDS_REQ_SEED': {
            'Request': '^2701' + ELM_FOOTER,
            'Descr': 'SecurityAccess - requestSeed',
            'Response': PA('B6F1EF') # response SID
        },
        'UDS_SEND_KEY': {
            'Request': '^2702' + ELM_FOOTER,
            'Descr': 'SecurityAccess - Send Key to ECU',
            'Response': PA('')
        },
        'UNK_3B00': {
            'Request': '^3B00' + ELM_DATA_FOOTER,
            'Descr': 'UNK_3B00',
            'Response': PA(''),
        },
        'UNK_3B03': {
            'Request': '^3B03' + ELM_DATA_FOOTER,
            'Descr': 'UNK_3B03',
            'Response': PA(''),
        },
        # ----------------------------------------------------------------------
    # UDS commands used by MT05
        'UDS_START_COMM': {
            'Request': '^81' + ELM_FOOTER,
            'Descr': 'UDS Start Communication',
            'Exec': 'self.set_sorted_obd_msg("mt05")',
            'Response': PA('EF 8F')
        },
        'UDS_STOP_COMM': {
            'Request': '^82' + ELM_FOOTER,
            'Descr': 'UDS Stop Communication',
            'Exec': 'self.set_sorted_obd_msg("default")',
            'Response': PA('')
        },
    },
# --------------------------------------------------------------------------
# Pids of a Toyota Auris Hybrid car (ISO 15765-4 CAN 11 bit ID 500 kbaud protocol)

    'car': {
    # AT Commands
        'ELM_DP': {
            'Request': '^AT DP' + ELM_FOOTER,
            'Descr': 'Current protocol',
            'Header': ECU_ADDR_E,
            'Response': [
                        ST('? '),
                        ST('AUTO, ISO 15765-4 (CAN 11/500) ')
                        ]
        },
        'ELM_IGNITION': {
            'Request': '^AT IGN' + ELM_FOOTER,
            'Descr': 'IgnMon input level',
            'Header': ECU_ADDR_E,
            'Response': [
                        ST('ON '),
                        ST('? ')
                        ]
        },
        'ELM_DESCR': {
            'Request': '^AT@1' + ELM_FOOTER,
            'Descr': 'Device description',
            'Header': ECU_ADDR_E,
            'Response': [
                        ST('? '),
                        ST('OBDII to RS232 Interpreter ')
                        ]
        },
        'ELM_ID': {
            'Request': '^AT@2' + ELM_FOOTER,
            'Descr': 'Device identifier',
            'Header': ECU_ADDR_E,
            'Response': ST('? ')
        },
        'ELM_VOLTAGE': {
            'Request': '^ATRV' + ELM_FOOTER,
            'Descr': 'Voltage detected by OBD-II adapter',
            'Header': ECU_ADDR_E,
            'Response': ST('14.7V ')
            # 14.7 volt
        },
    # OBD Commands
    # ------------------------------------------------------------
    # MODE 01 - returns values for sensors characterised by PID - Sending diagnostic data (PID data monitor/on-board system readiness test)
        'PIDS_A': {
            'Request': '^0100' + ELM_FOOTER,
            'Descr': 'Supported PIDs [01-20]',
            'Header': ECU_ADDR_E,
            'Response': HD(ECU_R_ADDR_E) + SZ('06') + DT('41 00 BE 3F A8 13')
        },
        'STATUS': {
            'Request': '^0101' + ELM_FOOTER,
            'Descr': 'Status since DTCs cleared',
            'Header': ECU_ADDR_E,
            'Response': HD(ECU_R_ADDR_E) + SZ('06') + DT('41 01 00 07 A1 00')
        },
        'FUEL_STATUS': {
            'Request': '^0103' + ELM_FOOTER,
            'Descr': 'Fuel System Status',
            'Header': ECU_ADDR_E,
            'Response': [
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 03 00 00'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 03 04 00'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 03 02 00')
                        ]
        },
        'ENGINE_LOAD': {
            'Request': '^0104' + ELM_FOOTER,
            'Descr': 'Calculated Engine Load',
            'Header': ECU_ADDR_E,
            'Response': [
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 04 FF'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 04 57'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 04 96'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 04 00') +
                        HD(ECU_R_ADDR_H) + SZ('03') + DT('41 04 00'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 04 56'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 04 64'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 04 67'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 04 9F'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 04 00'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 04 98'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 04 73'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 04 69'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 04 D6'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 04 41')
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
            'Request': '^0105' + ELM_FOOTER,
            'Descr': 'Engine Coolant Temperature',
            'Header': ECU_ADDR_E,
            'Response': [
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 05 5F'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 05 44'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 05 4C'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 05 64'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 05 55'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 05 5B'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 05 48'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 05 45'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 05 56'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 05 50'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 05 54'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 05 42'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 05 66')
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
            'Request': '^0106' + ELM_FOOTER,
            'Descr': 'Short Term Fuel Trim - Bank 1',
            'Header': ECU_ADDR_E,
            'Response': [
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 06 80'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 06 78'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 06 84'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 06 88'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 06 79'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 06 8B'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 06 7F'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 06 7D')
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
            'Request': '^0107' + ELM_FOOTER,
            'Descr': 'Long Term Fuel Trim - Bank 1',
            'Header': ECU_ADDR_E,
            'Response': [
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 07 79'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 07 7E'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 07 7C'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 07 7F'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 07 78')
                        ]
            # -5.46875 percent
            # -1.5625 percent
            # -3.125 percent
            # -0.78125 percent
            # -6.25 percent
        },
        'INTAKE_PRESSURE': {
            'Request': '^010B' + ELM_FOOTER,
            'Descr': 'Intake Manifold Pressure',
            'Header': ECU_ADDR_E,
            'Response': [
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 0B 26'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 0B 35'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 0B 1E'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 0B 63'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 0B 28'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 0B 52'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 0B 61'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 0B 60'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 0B 63') +
                        HD(ECU_R_ADDR_H) + SZ('03') + DT('41 0B 63'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 0B 36'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 0B 25'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 0B 14')
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
            'Request': '^010C' + ELM_FOOTER,
            'Descr': 'Engine RPM',
            'Header': ECU_ADDR_E,
            'Response': [
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 0C 14 5F'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 0C 00 00'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 0C 41 C2'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 0C 35 CB'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 0C 14 46'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 0C 12 87'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 0C 3B 2E'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 0C 15 2A'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 0C 09 F6'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 0C 23 82'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 0C 26 25'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 0C 18 9F'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 0C 13 FB'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 0C 3F 7A')
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
            'Request': '^010D' + ELM_FOOTER,
            'Descr': 'Vehicle Speed',
            'Header': ECU_ADDR_E,
            'Response': [
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 0D 0A'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 0D 37'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 0D 27'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 0D 33'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 0D 00'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 0D 44'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 0D 5C'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 0D 1D'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 0D 72'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 0D 48'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 0D 20'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 0D 29'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 0D 0E')
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
            'Request': '^010E' + ELM_FOOTER,
            'Descr': 'Timing Advance',
            'Header': ECU_ADDR_E,
            'Response': [
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 0E 75'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 0E 76'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 0E 8E'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 0E A2'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 0E 8F'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 0E 99'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 0E 8A'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 0E A6'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 0E 95'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 0E 9A'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 0E A8'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 0E AB')
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
            'Request': '^010F' + ELM_FOOTER,
            'Descr': 'Intake Air Temp',
            'Header': ECU_ADDR_E,
            'Response': [
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 0F 39'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 0F 3C'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 0F 36'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 0F 37'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 0F 34'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 0F 3A'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 0F 38'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 0F 35')
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
            'Request': '^0110' + ELM_FOOTER,
            'Descr': 'Air Flow Rate (MAF)',
            'Header': ECU_ADDR_E,
            'Response': [
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 10 18 1F'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 10 01 46'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 10 03 0A'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 10 11 5B'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 10 00 14'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 10 02 86'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 10 03 05'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 10 10 16'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 10 00 12'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 10 10 05'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 10 01 3B'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 10 00 51'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 10 10 20'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 10 04 93')
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
            'Request': '^0111' + ELM_FOOTER,
            'Descr': 'Throttle Position',
            'Header': ECU_ADDR_E,
            'Response': [
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 11 2B'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 11 70'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 11 44'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 11 50'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 11 32'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 11 72'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 11 2E'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 11 36'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 11 2A'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 11 2F')
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
            'Request': '^0113' + ELM_FOOTER,
            'Descr': 'O2 Sensors Present',
            'Header': ECU_ADDR_E,
            'Response': HD(ECU_R_ADDR_E) + SZ('03') + DT('41 13 03')
        },
        'O2_B1S2': {
            'Request': '^0115' + ELM_FOOTER,
            'Descr': 'O2: Bank 1 - Sensor 2 Voltage',
            'Header': ECU_ADDR_E,
            'Response': [
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 15 07 FF'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 15 00 FF'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 15 84 FF'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 15 03 FF'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 15 94 FF'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 15 2A FF'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 15 46 FF')
                        ]
            # 0.035 volt
            # 0.66 volt
            # 0.015 volt
            # 0.74 volt
            # 0.21 volt
            # 0.35 volt
        },
        'OBD_COMPLIANCE': {
            'Request': '^011C' + ELM_FOOTER,
            'Descr': 'OBD Standards Compliance',
            'Header': ECU_ADDR_E,
            'Response': HD(ECU_R_ADDR_E) + SZ('03') + DT('41 1C 06')
        },
        'RUN_TIME': {
            'Request': '^011F' + ELM_FOOTER,
            'Descr': 'Engine Run Time',
            'Header': ECU_ADDR_E,
            'Response': [
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 1F 00 75'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 1F 00 26'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 1F 00 1A'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 1F 00 5F'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 1F 00 A1'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 1F 00 96'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 1F 00 80'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 1F 00 3D'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 1F 00 0E'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 1F 00 00'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 1F 00 53'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 1F 00 8B'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 1F 00 32'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 1F 00 48'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 1F 00 6A')
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
            'Request': '^0120' + ELM_FOOTER,
            'Descr': 'Supported PIDs [21-40]',
            'Header': ECU_ADDR_E,
            'Response': HD(ECU_R_ADDR_E) + SZ('06') + DT('41 20 90 15 B0 15')
        },
        'DISTANCE_W_MIL': {
            'Request': '^0121' + ELM_FOOTER,
            'Descr': 'Distance Traveled with MIL on',
            'Header': ECU_ADDR_E,
            'Response': HD(ECU_R_ADDR_E) + SZ('04') + DT('41 21 00 00')
        },
        'O2_S1_WR_VOLTAGE': {
            'Request': '^0124' + ELM_FOOTER,
            'Descr': '02 Sensor 1 WR Lambda Voltage',
            'Header': ECU_ADDR_E,
            'Response': [
                        HD(ECU_R_ADDR_E) + SZ('06') + DT('41 24 7B A8 65 D9'),
                        HD(ECU_R_ADDR_E) + SZ('06') + DT('41 24 81 BA 6D 81'),
                        HD(ECU_R_ADDR_E) + SZ('06') + DT('41 24 80 4A 6B F1'),
                        HD(ECU_R_ADDR_E) + SZ('06') + DT('41 24 80 71 6B F1'),
                        HD(ECU_R_ADDR_E) + SZ('06') + DT('41 24 7E 87 69 71'),
                        HD(ECU_R_ADDR_E) + SZ('06') + DT('41 24 7F F5 6B 29'),
                        HD(ECU_R_ADDR_E) + SZ('06') + DT('41 24 91 2A 7C 31'),
                        HD(ECU_R_ADDR_E) + SZ('06') + DT('41 24 7E 28 68 A9'),
                        HD(ECU_R_ADDR_E) + SZ('06') + DT('41 24 7E DC 69 99'),
                        HD(ECU_R_ADDR_E) + SZ('06') + DT('41 24 82 B4 6E E9'),
                        HD(ECU_R_ADDR_E) + SZ('06') + DT('41 24 9D CF 9F FF'),
                        HD(ECU_R_ADDR_E) + SZ('06') + DT('41 24 84 32 70 29'),
                        HD(ECU_R_ADDR_E) + SZ('06') + DT('41 24 7F B5 69 49'),
                        HD(ECU_R_ADDR_E) + SZ('06') + DT('41 24 81 46 6C E1')
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
            'Request': '^012C' + ELM_FOOTER,
            'Descr': 'Commanded EGR',
            'Header': ECU_ADDR_E,
            'Response': HD(ECU_R_ADDR_E) + SZ('03') + DT('41 2C 00')
        },
        'EVAPORATIVE_PURGE': {
            'Request': '^012E' + ELM_FOOTER,
            'Descr': 'Commanded Evaporative Purge',
            'Header': ECU_ADDR_E,
            'Response': HD(ECU_R_ADDR_E) + SZ('03') + DT('41 2E 00')
        },
        'WARMUPS_SINCE_DTC_CLEAR': {
            'Request': '^0130' + ELM_FOOTER,
            'Descr': 'Number of warm-ups since codes cleared',
            'Header': ECU_ADDR_E,
            'Response': HD(ECU_R_ADDR_E) + SZ('03') + DT('41 30 04')
            # 4 count
        },
        'DISTANCE_SINCE_DTC_CLEAR': {
            'Request': '^0131' + ELM_FOOTER,
            'Descr': 'Distance traveled since codes cleared',
            'Header': ECU_ADDR_E,
            'Response': [
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 31 00 32'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 31 00 31'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 31 00 33')
                        ]
            # 50 kilometer
            # 49 kilometer
            # 51 kilometer
        },
        'BAROMETRIC_PRESSURE': {
            'Request': '^0133' + ELM_FOOTER,
            'Descr': 'Barometric Pressure',
            'Header': ECU_ADDR_E,
            'Response': HD(ECU_R_ADDR_E) + SZ('03') + DT('41 33 61')
            # 97 kilopascal
        },
        'O2_S1_WR_CURRENT': {
            'Request': '^0134' + ELM_FOOTER,
            'Descr': '02 Sensor 1 WR Lambda Current',
            'Header': ECU_ADDR_E,
            'Response': [
                        HD(ECU_R_ADDR_E) + SZ('06') + DT('41 34 7A F9 7F F1'),
                        HD(ECU_R_ADDR_E) + SZ('06') + DT('41 34 69 9E 7F 9F'),
                        HD(ECU_R_ADDR_E) + SZ('06') + DT('41 34 7E EB 80 01'),
                        HD(ECU_R_ADDR_E) + SZ('06') + DT('41 34 7E 84 80 00'),
                        HD(ECU_R_ADDR_E) + SZ('06') + DT('41 34 80 9D 80 07'),
                        HD(ECU_R_ADDR_E) + SZ('06') + DT('41 34 7E 17 7F FE'),
                        HD(ECU_R_ADDR_E) + SZ('06') + DT('41 34 9D CF 81 6D'),
                        HD(ECU_R_ADDR_E) + SZ('06') + DT('41 34 81 81 80 0B'),
                        HD(ECU_R_ADDR_E) + SZ('06') + DT('41 34 7A AC 7F EF'),
                        HD(ECU_R_ADDR_E) + SZ('06') + DT('41 34 99 CC 80 47'),
                        HD(ECU_R_ADDR_E) + SZ('06') + DT('41 34 7E 9C 80 00'),
                        HD(ECU_R_ADDR_E) + SZ('06') + DT('41 34 7E A1 80 00'),
                        HD(ECU_R_ADDR_E) + SZ('06') + DT('41 34 9D CF 81 96'),
                        HD(ECU_R_ADDR_E) + SZ('06') + DT('41 34 83 FD 80 14'),
                        HD(ECU_R_ADDR_E) + SZ('06') + DT('41 34 74 77 7F CD')
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
            'Request': '^013C' + ELM_FOOTER,
            'Descr': 'Catalyst Temperature: Bank 1 - Sensor 1',
            'Header': ECU_ADDR_E,
            'Response': [
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 3C 15 9A'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 3C 1D 7C'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 3C 1C 1C'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 3C 04 76'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 3C 0E 43'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 3C 0D 71'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 3C 15 C5'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 3C 15 B3'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 3C 05 82'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 3C 23 0F'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 3C 06 9E'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 3C 22 36'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 3C 22 E0'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 3C 20 4E'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 3C 1C 66')
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
            'Request': '^013E' + ELM_FOOTER,
            'Descr': 'Catalyst Temperature: Bank 1 - Sensor 2',
            'Header': ECU_ADDR_E,
            'Response': [
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 3E 02 B9'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 3E 09 44'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 3E 06 B7'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 3E 0E 77'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 3E 03 69'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 3E 20 A1'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 3E 18 1B'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 3E 15 A0'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 3E 11 3E'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 3E 1E 38'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 3E 10 C4'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 3E 20 3F'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 3E 02 83'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 3E 16 DD'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 3E 1B 27')
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
            'Request': '^0140' + ELM_FOOTER,
            'Descr': 'Supported PIDs [41-60]',
            'Header': ECU_ADDR_E,
            'Response': [
                        HD(ECU_R_ADDR_E) + SZ('06') + DT('41 40 7A 1C 80 00') +
                        HD(ECU_R_ADDR_H) + SZ('06') + DT('41 40 44 CC 00 21'),
                        HD(ECU_R_ADDR_E) + SZ('06') + DT('41 40 7A 1C 80 00')
                        ]
        },
        'CONTROL_MODULE_VOLTAGE': {
            'Request': '^0142' + ELM_FOOTER,
            'Descr': 'Control module voltage',
            'Header': ECU_ADDR_E,
            'Response': [
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 42 39 4B'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 42 39 C1'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 42 39 73'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 42 39 5F'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 42 39 9A'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 42 39 38')
                        ]
            # 14.667 volt
            # 14.785 volt
            # 14.707 volt
            # 14.687000000000001 volt
            # 14.746 volt
            # 14.648 volt
        },
        'ABSOLUTE_LOAD': {
            'Request': '^0143' + ELM_FOOTER,
            'Descr': 'Absolute load value',
            'Header': ECU_ADDR_E,
            'Response': [
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 43 00 54'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 43 00 3C'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 43 00 39'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 43 00 29'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 43 00 BB'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 43 00 66'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 43 00 C0'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 43 00 6F'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 43 00 1B'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 43 00 BE'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 43 00 00'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 43 00 55')
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
            'Request': '^0144' + ELM_FOOTER,
            'Descr': 'Commanded equivalence ratio',
            'Header': ECU_ADDR_E,
            'Response': [
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 44 7E 71'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 44 7E 82'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 44 7F 20'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 44 80 C5'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 44 7F F2'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 44 75 A8'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 44 7E 07'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 44 62 8C'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 44 7E 4E')
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
            'Request': '^0145' + ELM_FOOTER,
            'Descr': 'Relative throttle position',
            'Header': ECU_ADDR_E,
            'Response': [
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 45 19'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 45 42'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 45 10'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 45 46'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 45 27'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 45 03'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 45 02'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 45 00')
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
            'Request': '^0147' + ELM_FOOTER,
            'Descr': 'Absolute throttle position B',
            'Header': ECU_ADDR_E,
            'Response': [
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 47 92'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 47 7B'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 47 7D'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 47 81'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 47 AD'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 47 E9'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 47 D3'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 47 95'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 47 85'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 47 7C')
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
            'Request': '^014C' + ELM_FOOTER,
            'Descr': 'Commanded throttle actuator',
            'Header': ECU_ADDR_E,
            'Response': [
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 4C 71'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 4C 33'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 4C 6F'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 4C 3D'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 4C 74'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 4C 2F'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 4C 2A'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 4C 6B'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 4C 32'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 4C 22'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 4C 2B'),
                        HD(ECU_R_ADDR_E) + SZ('03') + DT('41 4C 75')
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
            'Request': '^014D' + ELM_FOOTER,
            'Descr': 'Time run with MIL on',
            'Header': ECU_ADDR_E,
            'Response': HD(ECU_R_ADDR_E) + SZ('04') + DT('41 4D 00 00')
        },
        'TIME_SINCE_DTC_CLEARED': {
            'Request': '^014E' + ELM_FOOTER,
            'Descr': 'Time since trouble codes cleared',
            'Header': ECU_ADDR_E,
            'Response': [
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 4E 00 5B'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 4E 00 5C'),
                        HD(ECU_R_ADDR_E) + SZ('04') + DT('41 4E 00 5D')
                        ]
            # 91 minute
            # 92 minute
            # 93 minute
        },
        'FUEL_TYPE': {
            'Request': '^0151' + ELM_FOOTER,
            'Descr': 'Fuel Type',
            'Header': ECU_ADDR_E,
            'Response': HD(ECU_R_ADDR_E) + SZ('03') + DT('41 51 01')
        },
        'BATT_REM_CHARGE': {
            'Request': '^015B' + ELM_FOOTER,
            'Descr': 'Hybrid/EV Battery Pack Remaining Charge',
            'Header': ECU_ADDR_E,
            'Response': ST('NO DATA'),
        },
        'PIDS_D': {
            'Request': '^0160' + ELM_FOOTER,
            'Descr': 'Supported PIDs [61-80]',
            'Response': ST('NO DATA'),
        },
        'PIDS_E': {
            'Request': '^0180' + ELM_FOOTER,
            'Descr': 'Supported PIDs [81-A0]',
            'Response': ST('NO DATA'),
        },
        'PIDS_F': {
            'Request': '^01A0' + ELM_FOOTER,
            'Descr': 'Supported PIDs [A1-C0]',
            'Response': ST('NO DATA'),
        },
    # ------------------------------------------------------------
    # MODE 02 - freeze frame (or instantaneous) data of a fault
        'DTC_STATUS': {
            'Request': '^0201' + ELM_FOOTER,
            'Descr': 'DTC Status since DTCs cleared',
            'Header': ECU_ADDR_E,
            'Response': NA('12')
            # invalid data returned by diagnostic request (mode 02)
        },
        'INJ_MF_2': {
            'Request': '^020200' + ELM_FOOTER,
            'Descr': 'Injector Malfunction 2',
            'Header': ECU_ADDR_E,
            'Response': HD(ECU_R_ADDR_E) + SZ('05') + DT('42 02 00 00 00')
        },
        'DTC_FUEL_STATUS': {
            'Request': '^0203' + ELM_FOOTER,
            'Descr': 'DTC Fuel System Status',
            'Header': ECU_ADDR_E,
            'Response': NA('12')
            # invalid data returned by diagnostic request (mode 02)
        },
        'DTC_ENGINE_LOAD': {
            'Request': '^0204' + ELM_FOOTER,
            'Descr': 'DTC Calculated Engine Load',
            'Header': ECU_ADDR_E,
            'Response': NA('12')
            # invalid data returned by diagnostic request (mode 02)
        },
        'DTC_COOLANT_TEMP': {
            'Request': '^0205' + ELM_FOOTER,
            'Descr': 'DTC Engine Coolant Temperature',
            'Header': ECU_ADDR_E,
            'Response': NA('12')
            # invalid data returned by diagnostic request (mode 02)
        },
        'DTC_SHORT_FUEL_TRIM_1': {
            'Request': '^0206' + ELM_FOOTER,
            'Descr': 'DTC Short Term Fuel Trim - Bank 1',
            'Header': ECU_ADDR_E,
            'Response': NA('12')
            # invalid data returned by diagnostic request (mode 02)
        },
        'DTC_LONG_FUEL_TRIM_1': {
            'Request': '^0207' + ELM_FOOTER,
            'Descr': 'DTC Long Term Fuel Trim - Bank 1',
            'Header': ECU_ADDR_E,
            'Response': NA('12')
            # invalid data returned by diagnostic request (mode 02)
        },
        'DTC_INTAKE_PRESSURE': {
            'Request': '^020B' + ELM_FOOTER,
            'Descr': 'DTC Intake Manifold Pressure',
            'Header': ECU_ADDR_E,
            'Response': NA('12')
            # invalid data returned by diagnostic request (mode 02)
        },
        'DTC_RPM': {
            'Request': '^020C' + ELM_FOOTER,
            'Descr': 'DTC Engine RPM',
            'Header': ECU_ADDR_E,
            'Response': NA('12')
            # invalid data returned by diagnostic request (mode 02)
        },
        'DTC_SPEED': {
            'Request': '^020D' + ELM_FOOTER,
            'Descr': 'DTC Vehicle Speed',
            'Header': ECU_ADDR_E,
            'Response': NA('12')
            # invalid data returned by diagnostic request (mode 02)
        },
        'DTC_TIMING_ADVANCE': {
            'Request': '^020E' + ELM_FOOTER,
            'Descr': 'DTC Timing Advance',
            'Header': ECU_ADDR_E,
            'Response': NA('12')
            # invalid data returned by diagnostic request (mode 02)
        },
        'DTC_INTAKE_TEMP': {
            'Request': '^020F' + ELM_FOOTER,
            'Descr': 'DTC Intake Air Temp',
            'Header': ECU_ADDR_E,
            'Response': NA('12')
            # invalid data returned by diagnostic request (mode 02)
        },
        'DTC_MAF': {
            'Request': '^0210' + ELM_FOOTER,
            'Descr': 'DTC Air Flow Rate (MAF)',
            'Header': ECU_ADDR_E,
            'Response': NA('12')
            # invalid data returned by diagnostic request (mode 02)
        },
        'DTC_THROTTLE_POS': {
            'Request': '^0211' + ELM_FOOTER,
            'Descr': 'DTC Throttle Position',
            'Header': ECU_ADDR_E,
            'Response': NA('12')
            # invalid data returned by diagnostic request (mode 02)
        },
        'DTC_O2_SENSORS': {
            'Request': '^0213' + ELM_FOOTER,
            'Descr': 'DTC O2 Sensors Present',
            'Header': ECU_ADDR_E,
            'Response': NA('12')
            # invalid data returned by diagnostic request (mode 02)
        },
        'DTC_O2_B1S2': {
            'Request': '^0215' + ELM_FOOTER,
            'Descr': 'DTC O2: Bank 1 - Sensor 2 Voltage',
            'Header': ECU_ADDR_E,
            'Response': NA('12')
            # invalid data returned by diagnostic request (mode 02)
        },
        'DTC_OBD_COMPLIANCE': {
            'Request': '^021C' + ELM_FOOTER,
            'Descr': 'DTC OBD Standards Compliance',
            'Header': ECU_ADDR_E,
            'Response': NA('12')
            # invalid data returned by diagnostic request (mode 02)
        },
        'DTC_RUN_TIME': {
            'Request': '^021F' + ELM_FOOTER,
            'Descr': 'DTC Engine Run Time',
            'Header': ECU_ADDR_E,
            'Response': NA('12')
            # invalid data returned by diagnostic request (mode 02)
        },
        'DTC_PIDS_B': {
            'Request': '^0220' + ELM_FOOTER,
            'Descr': 'DTC Supported PIDs [21-40]',
            'Header': ECU_ADDR_E,
            'Response': [
                        ST('NO DATA'),
                        NA('12')
                        ]
            # invalid data returned by diagnostic request (mode 02)
        },
        'DTC_DISTANCE_W_MIL': {
            'Request': '^0221' + ELM_FOOTER,
            'Descr': 'DTC Distance Traveled with MIL on',
            'Header': ECU_ADDR_E,
            'Response': NA('12')
            # invalid data returned by diagnostic request (mode 02)
        },
        'DTC_O2_S1_WR_VOLTAGE': {
            'Request': '^0224' + ELM_FOOTER,
            'Descr': 'DTC 02 Sensor 1 WR Lambda Voltage',
            'Header': ECU_ADDR_E,
            'Response': NA('12')
            # invalid data returned by diagnostic request (mode 02)
        },
        'DTC_COMMANDED_EGR': {
            'Request': '^022C' + ELM_FOOTER,
            'Descr': 'DTC Commanded EGR',
            'Header': ECU_ADDR_E,
            'Response': NA('12')
            # invalid data returned by diagnostic request (mode 02)
        },
        'DTC_EVAPORATIVE_PURGE': {
            'Request': '^022E' + ELM_FOOTER,
            'Descr': 'DTC Commanded Evaporative Purge',
            'Header': ECU_ADDR_E,
            'Response': NA('12')
            # invalid data returned by diagnostic request (mode 02)
        },
        'DTC_WARMUPS_SINCE_DTC_CLEAR': {
            'Request': '^0230' + ELM_FOOTER,
            'Descr': 'DTC Number of warm-ups since codes cleared',
            'Header': ECU_ADDR_E,
            'Response': [
                        ST('NO DATA'),
                        NA('12')
                        ]
            # invalid data returned by diagnostic request (mode 02)
        },
        'DTC_DISTANCE_SINCE_DTC_CLEAR': {
            'Request': '^0231' + ELM_FOOTER,
            'Descr': 'DTC Distance traveled since codes cleared',
            'Header': ECU_ADDR_E,
            'Response': NA('12')
            # invalid data returned by diagnostic request (mode 02)
        },
        'DTC_BAROMETRIC_PRESSURE': {
            'Request': '^0233' + ELM_FOOTER,
            'Descr': 'DTC Barometric Pressure',
            'Header': ECU_ADDR_E,
            'Response': NA('12')
            # invalid data returned by diagnostic request (mode 02)
        },
        'DTC_O2_S1_WR_CURRENT': {
            'Request': '^0234' + ELM_FOOTER,
            'Descr': 'DTC 02 Sensor 1 WR Lambda Current',
            'Header': ECU_ADDR_E,
            'Response': NA('12')
            # invalid data returned by diagnostic request (mode 02)
        },
        'DTC_CATALYST_TEMP_B1S1': {
            'Request': '^023C' + ELM_FOOTER,
            'Descr': 'DTC Catalyst Temperature: Bank 1 - Sensor 1',
            'Header': ECU_ADDR_E,
            'Response': NA('12')
            # invalid data returned by diagnostic request (mode 02)
        },
        'DTC_CATALYST_TEMP_B1S2': {
            'Request': '^023E' + ELM_FOOTER,
            'Descr': 'DTC Catalyst Temperature: Bank 1 - Sensor 2',
            'Header': ECU_ADDR_E,
            'Response': NA('12')
            # invalid data returned by diagnostic request (mode 02)
        },
        'DTC_PIDS_C': {
            'Request': '^0240' + ELM_FOOTER,
            'Descr': 'DTC Supported PIDs [41-60]',
            'Header': ECU_ADDR_E,
            'Response': NA('12')
            # invalid data returned by diagnostic request (mode 02)
        },
        'DTC_CONTROL_MODULE_VOLTAGE': {
            'Request': '^0242' + ELM_FOOTER,
            'Descr': 'DTC Control module voltage',
            'Header': ECU_ADDR_E,
            'Response': NA('12')
            # invalid data returned by diagnostic request (mode 02)
        },
        'DTC_ABSOLUTE_LOAD': {
            'Request': '^0243' + ELM_FOOTER,
            'Descr': 'DTC Absolute load value',
            'Header': ECU_ADDR_E,
            'Response': NA('12')
            # invalid data returned by diagnostic request (mode 02)
        },
        'DTC_COMMANDED_EQUIV_RATIO': {
            'Request': '^0244' + ELM_FOOTER,
            'Descr': 'DTC Commanded equivalence ratio',
            'Header': ECU_ADDR_E,
            'Response': NA('12')
            # invalid data returned by diagnostic request (mode 02)
        },
        'DTC_RELATIVE_THROTTLE_POS': {
            'Request': '^0245' + ELM_FOOTER,
            'Descr': 'DTC Relative throttle position',
            'Header': ECU_ADDR_E,
            'Response': NA('12')
            # invalid data returned by diagnostic request (mode 02)
        },
        'DTC_THROTTLE_POS_B': {
            'Request': '^0247' + ELM_FOOTER,
            'Descr': 'DTC Absolute throttle position B',
            'Header': ECU_ADDR_E,
            'Response': NA('12')
            # invalid data returned by diagnostic request (mode 02)
        },
        'DTC_THROTTLE_ACTUATOR': {
            'Request': '^024C' + ELM_FOOTER,
            'Descr': 'DTC Commanded throttle actuator',
            'Header': ECU_ADDR_E,
            'Response': NA('12')
            # invalid data returned by diagnostic request (mode 02)
        },
        'DTC_RUN_TIME_MIL': {
            'Request': '^024D' + ELM_FOOTER,
            'Descr': 'DTC Time run with MIL on',
            'Header': ECU_ADDR_E,
            'Response': NA('12')
            # invalid data returned by diagnostic request (mode 02)
        },
        'DTC_TIME_SINCE_DTC_CLEARED': {
            'Request': '^024E' + ELM_FOOTER,
            'Descr': 'DTC Time since trouble codes cleared',
            'Header': ECU_ADDR_E,
            'Response': NA('12')
            # invalid data returned by diagnostic request (mode 02)
        },
        'DTC_FUEL_TYPE': {
            'Request': '^0251' + ELM_FOOTER,
            'Descr': 'DTC Fuel Type',
            'Header': ECU_ADDR_E,
            'Response': [
                        ST('NO DATA'),
                        NA('12')
                        ]
            # invalid data returned by diagnostic request (mode 02)
        },
    # -------------------------------------------------------------------
    # MODE 03 - diagnostic trouble codes - Sending emission related malfunction code (DTC)
        'GET_DTC': {
            'Request': '^03' + ELM_FOOTER,
            'Descr': 'Get DTCs (Diagnostic Trouble Codes)',
            'Header': ECU_ADDR_E,
            'Response': HD(ECU_R_ADDR_E) + SZ('02') + DT('43 00')
        },
    # -------------------------------------------------------------------
    # Mode 04 Clearing/resetting emission-related malfunction information
    # -------------------------------------------------------------------
    # MODE 06 - results of self-diagnostics - Sending intermittent monitoring system test results (DMTR)
        'MIDS_A': {
            'Request': '^0600' + ELM_FOOTER,
            'Descr': 'Supported MIDs [01-20]',
            'Header': ECU_ADDR_E,
            'Response': HD(ECU_R_ADDR_E) + SZ('06') + DT('46 00 C0 00 00 01')
        },
        'MONITOR_O2_B1S1': {
            'Request': '^0601' + ELM_FOOTER,
            'Descr': 'O2 Sensor Monitor Bank 1 - Sensor 1',
            'Header': ECU_ADDR_E,
            'Response': HD(ECU_R_ADDR_E) + SZ('10') + DT('13 46 01 8E 0B 02 27') +
                        HD(ECU_R_ADDR_E) + SZ('21') + DT('00 A9 4D BA 01 91 8D') +
                        HD(ECU_R_ADDR_E) + SZ('22') + DT('01 9D 00 B4 02 2F 00')
        },
        'MONITOR_O2_B1S2': {
            'Request': '^0602' + ELM_FOOTER,
            'Descr': 'O2 Sensor Monitor Bank 1 - Sensor 2',
            'Header': ECU_ADDR_E,
            'Response': [
                        HD(ECU_R_ADDR_E) + SZ('10') + DT('1C 46 02 07 0B 00 88') +
                        HD(ECU_R_ADDR_E) + SZ('21') + DT('00 00 00 D6 02 08 0B') +
                        HD(ECU_R_ADDR_E) + SZ('22') + DT('02 F9 02 49 03 E3 02') +
                        HD(ECU_R_ADDR_E) + SZ('23') + DT('8F 86 03 C2 00 00 1A') +
                        HD(ECU_R_ADDR_E) + SZ('24') + DT('E0 00 00 00 00 00 00'),
                        HD(ECU_R_ADDR_E) + SZ('10') + DT('1C 46 02 07 0B 00 88') +
                        HD(ECU_R_ADDR_E) + SZ('21') + DT('00 00 00 D6 02 08 0B') +
                        HD(ECU_R_ADDR_E) + SZ('22') + DT('02 F9 02 49 03 E3 02') +
                        HD(ECU_R_ADDR_E) + SZ('23') + DT('8F 86 03 C2 00 00 1A')
                        ]
        },
        'MIDS_B': {
            'Request': '^0620' + ELM_FOOTER,
            'Descr': 'Supported MIDs [21-40]',
            'Header': ECU_ADDR_E,
            'Response': HD(ECU_R_ADDR_E) + SZ('06') + DT('46 20 80 00 80 01')
        },
        'MONITOR_CATALYST_B1': {
            'Request': '^0621' + ELM_FOOTER,
            'Descr': 'Catalyst Monitor Bank 1',
            'Header': ECU_ADDR_E,
            'Response': HD(ECU_R_ADDR_E) + SZ('10') + DT('0A 46 21 A9 86 02 E5') +
                        HD(ECU_R_ADDR_E) + SZ('21') + DT('02 D0 7F FF 00 00 00')
        },
        'MONITOR_EGR_B1': {
            'Request': '^0631' + ELM_FOOTER,
            'Descr': 'EGR Monitor Bank 1',
            'Header': ECU_ADDR_E,
            'Response': HD(ECU_R_ADDR_E) + SZ('10') + DT('0A 46 31 BD 17 07 47') +
                        HD(ECU_R_ADDR_E) + SZ('21') + DT('00 63 FF FF 00 00 00')
        },
        'MIDS_C': {
            'Request': '^0640' + ELM_FOOTER,
            'Descr': 'Supported MIDs [41-60]',
            'Header': ECU_ADDR_E,
            'Response': HD(ECU_R_ADDR_E) + SZ('06') + DT('46 40 00 00 00 01')
        },
        'MIDS_D': {
            'Request': '^0660' + ELM_FOOTER,
            'Descr': 'Supported MIDs [61-80]',
            'Header': ECU_ADDR_E,
            'Response': HD(ECU_R_ADDR_E) + SZ('06') + DT('46 60 00 00 00 01')
        },
        'MIDS_E': {
            'Request': '^0680' + ELM_FOOTER,
            'Descr': 'Supported MIDs [81-A0]',
            'Header': ECU_ADDR_E,
            'Response': HD(ECU_R_ADDR_E) + SZ('06') + DT('46 80 00 00 00 01')
        },
        'MIDS_F': {
            'Request': '^06A0' + ELM_FOOTER,
            'Descr': 'Supported MIDs [A1-C0]',
            'Header': ECU_ADDR_E,
            'Response': HD(ECU_R_ADDR_E) + SZ('06') + DT('46 A0 F8 00 00 00')
        },
        'MONITOR_MISFIRE_GENERAL': {
            'Request': '^06A1' + ELM_FOOTER,
            'Descr': 'Misfire Monitor General Data',
            'Header': ECU_ADDR_E,
            'Response': HD(ECU_R_ADDR_E) + SZ('10') + DT('13 46 A1 0B 24 00 00') +
                        HD(ECU_R_ADDR_E) + SZ('21') + DT('00 00 FF FF A1 0C 24') +
                        HD(ECU_R_ADDR_E) + SZ('22') + DT('00 00 00 00 FF FF 00')
        },
        'MONITOR_MISFIRE_CYLINDER_1': {
            'Request': '^06A2' + ELM_FOOTER,
            'Descr': 'Misfire Cylinder 1 Data',
            'Header': ECU_ADDR_E,
            'Response': HD(ECU_R_ADDR_E) + SZ('10') + DT('13 46 A2 0B 24 00 00') +
                        HD(ECU_R_ADDR_E) + SZ('21') + DT('00 00 FF FF A2 0C 24') +
                        HD(ECU_R_ADDR_E) + SZ('22') + DT('00 00 00 00 FF FF 00')
        },
        'MONITOR_MISFIRE_CYLINDER_2': {
            'Request': '^06A3' + ELM_FOOTER,
            'Descr': 'Misfire Cylinder 2 Data',
            'Header': ECU_ADDR_E,
            'Response': HD(ECU_R_ADDR_E) + SZ('10') + DT('13 46 A3 0B 24 00 00') +
                        HD(ECU_R_ADDR_E) + SZ('21') + DT('00 00 FF FF A3 0C 24') +
                        HD(ECU_R_ADDR_E) + SZ('22') + DT('00 00 00 00 FF FF 00')
        },
        'MONITOR_MISFIRE_CYLINDER_3': {
            'Request': '^06A4' + ELM_FOOTER,
            'Descr': 'Misfire Cylinder 3 Data',
            'Header': ECU_ADDR_E,
            'Response': HD(ECU_R_ADDR_E) + SZ('10') + DT('13 46 A4 0B 24 00 00') +
                        HD(ECU_R_ADDR_E) + SZ('21') + DT('00 00 FF FF A4 0C 24') +
                        HD(ECU_R_ADDR_E) + SZ('22') + DT('00 00 00 00 FF FF 00')
        },
        'MONITOR_MISFIRE_CYLINDER_4': {
            'Request': '^06A5' + ELM_FOOTER,
            'Descr': 'Misfire Cylinder 4 Data',
            'Header': ECU_ADDR_E,
            'Response': HD(ECU_R_ADDR_E) + SZ('10') + DT('13 46 A5 0B 24 00 00') +
                        HD(ECU_R_ADDR_E) + SZ('21') + DT('00 00 FF FF A5 0C 24') +
                        HD(ECU_R_ADDR_E) + SZ('22') + DT('00 00 00 00 FF FF 00')
        },
    # -------------------------------------------------------------------
    # MODE 07 - unconfirmed fault codes - Sending continuous monitoring system test results (pending code)
        'GET_CURRENT_DTC': {
            'Request': '^07' + ELM_FOOTER,
            'Descr': 'Get DTCs from the current/last driving cycle',
            'Header': ECU_ADDR_E,
            'Response': HD(ECU_R_ADDR_E) + SZ('02') + DT('47 00')
        },
    # -------------------------------------------------------------------
    # Mode 08 On-board device control (simulation test, active command mode)
        'PIDS_8': {
            'Request': '^0800' + ELM_FOOTER,
            'Descr': 'PIDS_08',
            'Response': ST('NO DATA'),
        },
    # -------------------------------------------------------------------
    # Mode 09 Request vehicle information
        'ELM_PIDS_9A': {
            'Request': '^0900' + ELM_FOOTER,
            'Descr': 'Supported PIDs [01-20]',
            'Response': HD(ECU_R_ADDR_E) + SZ('06') + DT('49 00 55 40 00 00')
        },
        'VIN_MESSAGE_COUNT': {
            'Request': '^0901' + ELM_FOOTER,
            'Descr': 'VIN Message Count',
            'Response': HD(ECU_R_ADDR_E) + SZ('03') + DT('49 01 01')
        },
        'VIN': {
            # Check this also: https://stackoverflow.com/a/26752855/10598800,
            # https://www.autocheck.com/vehiclehistory/autocheck/en/vinbasics
            'Request': '^0902' + ELM_FOOTER,
            'Descr': 'Vehicle Identification Number',
            'Response': [
                PA('01 57 50 30 5A 5A 5A 39 39 5A 54 53 33 39 30 30 30 30'),
                # https://www.autodna.com/vin/WP0ZZZ99ZTS390000,
                # https://it.vin-info.com/libro-denuncia/WP0ZZZ99ZTS390000
                PA('01 4D 41 54 34 30 33 30 39 36 42 4E 4C 30 30 30 30 30'),
                # https://community.carloop.io/t/how-to-request-vin/153/11
                PA('01 53 42 31 5A 53 33 4A 45 36 30 45 32 38 32 31 30 32')
            ]
        },
        'CALIBRATION_ID_MESSAGE_COUNT': {
            'Request': '^0903' + ELM_FOOTER,
            'Descr': 'Calibration ID message count for PID 04',
            'Response': HD(ECU_R_ADDR_E) + SZ('03') + DT('49 03 01')
        },
        'CALIBRATION_ID': {
            'Request': '^0904' + ELM_FOOTER,
            'Descr': 'Calibration ID',
            'Header': ECU_ADDR_E,
            'Response': HD(ECU_R_ADDR_E) + SZ('10') + DT('23 49 04 02 33 31 32') +
                        HD(ECU_R_ADDR_E) + SZ('21') + DT('4A 36 30 30 30 00 00') +
                        HD(ECU_R_ADDR_E) + SZ('22') + DT('00 00 00 00 00 00 41') +
                        HD(ECU_R_ADDR_E) + SZ('23') + DT('34 37 30 31 30 30 30') +
                        HD(ECU_R_ADDR_E) + SZ('24') + DT('00 00 00 00 00 00 00') +
                        HD(ECU_R_ADDR_E) + SZ('25') + DT('00 00 00 00 00 00 00')
        },
        #'CVN_MESSAGE_COUNT': {
        #    'Request': '^0905' + ELM_MAX_RESP,
        #    'Descr': 'CVN Message Count for PID 06',
        #    ... (incomplete)
        #},
        'CVN': {
            'Request': '^0906' + ELM_FOOTER,
            'Descr': 'Calibration Verification Numbers',
            'Header': ECU_ADDR_E,
            'Response': HD(ECU_R_ADDR_E) + SZ('10') + DT('0B 49 06 02 69 53 CD') +
                        HD(ECU_R_ADDR_E) + SZ('21') + DT('4B 61 1F 6E F2 00 00')
        },
        'PERF_TRACKING_SPARK': {
            'Request': '^0908' + ELM_FOOTER,
            'Descr': 'In-use performance tracking (spark ignition)',
            'Header': ECU_ADDR_E,
            'Response': HD(ECU_R_ADDR_E) + SZ('10') + DT('2B 49 08 14 00 18 00') +
                        HD(ECU_R_ADDR_E) + SZ('21') + DT('9A 00 11 00 18 00 00') +
                        HD(ECU_R_ADDR_E) + SZ('22') + DT('00 00 00 14 00 18 00') +
                        HD(ECU_R_ADDR_E) + SZ('23') + DT('00 00 00 00 1C 00 18') +
                        HD(ECU_R_ADDR_E) + SZ('24') + DT('00 00 00 00 00 00 00') +
                        HD(ECU_R_ADDR_E) + SZ('25') + DT('00 00 0C 00 18 00 00') +
                        HD(ECU_R_ADDR_E) + SZ('26') + DT('00 00 00 00 00 00 00')
        },
        'ECU_NAME': {
            'Request': '^090A' + ELM_FOOTER,
            'Descr': 'ECU name',
            'Header': ECU_ADDR_E,
            'Response': HD(ECU_R_ADDR_E) + SZ('10') + DT('17 49 0A 01 45 43 4D') +
                        HD(ECU_R_ADDR_E) + SZ('21') + DT('00 2D 45 6E 67 69 6E') +
                        HD(ECU_R_ADDR_E) + SZ('22') + DT('65 43 6F 6E 74 72 6F') +
                        HD(ECU_R_ADDR_E) + SZ('23') + DT('6C 00 00 00 00 00 00')
        },
    # -------------------------------------------------------------------
    # Manage Trouble codes
        'SHOW_DIAG_TC': {
            'Request': '^03' + ELM_FOOTER,
            'Descr': 'Show stored Diagnostic Trouble Codes',
            'Response': ST('NO DATA'),
        },
        'CLEAR_DIAG_TC': {
            'Request': '^04' + ELM_FOOTER,
            'Descr': 'Clear Diagnostic Trouble Codes and stored values',
            'Header': ECU_ADDR_E,
            'Response': HD(ECU_R_ADDR_E) + SZ('01') + DT('44')
        },
        'SHOW_PENDING_TC': {
            'Request': '^07' + ELM_FOOTER,
            'Descr': 'Show pending Diagnostic Trouble Codes'
                     '(detected during current or last driving cycle)',
            'Response': ST('NO DATA'),
        },
        'UNKNOWN_0A': {
            'Request': '^0A' + ELM_FOOTER,
            'Descr': 'Permanent DTCs (Cleared DTCs)',
            'Response': ST('NO DATA'),
        },
        # -------------------------------------------------------------------
    # Unknown PIDs tested on a Toyota Prius
        'UNKNOWN_01AB': {
            'Request': '^01AB' + ELM_FOOTER,
            'Descr': 'UNKNOWN_01AB',
            'Response': ST(''),
        },
        'UNKNOWN_13_U': {
            'Request': '^13' + ELM_FOOTER,
            'Header': ECU_ADDR_U,
            'Descr': 'UNKNOWN_13',
            'Response': ST('NO DATA'),
        },
        'UNKNOWN_13_E': {
            'Request': '^13' + ELM_FOOTER,
            'Header': ECU_ADDR_E,
            'Descr': 'UNKNOWN_13',
            'Response': HD(ECU_R_ADDR_E) + SZ('02') + DT('53 00')
        },
        'UNKNOWN_1380': {
            'Request': '^1380' + ELM_FOOTER,
            'Descr': 'UNKNOWN_1380',
            'Response': ST('NO DATA'),
        },
        'UNKNOWN_1381': {
            'Request': '^1381' + ELM_FOOTER,
            'Descr': 'UNKNOWN_1381',
            'Response': ST('NO DATA'),
        },
        'UNKNOWN_1382': {
            'Request': '^1382' + ELM_FOOTER,
            'Descr': 'UNKNOWN_1382',
            'Response': ST('NO DATA'),
        },
        'UNKNOWN_13B0': {
            'Request': '^13B0' + ELM_FOOTER,
            'Descr': 'UNKNOWN_13B0',
            'Response': ST('NO DATA'),
        },
        'UNKNOWN_13FF': {
            'Request': '^13FF' + ELM_FOOTER,
            'Descr': 'UNKNOWN_13FF',
            'Response': ST('NO DATA'),
        },
        'UNKNOWN_13FF00': {
            'Request': '^13FF00' + ELM_FOOTER,
            'Descr': 'UNKNOWN_13FF00',
            'Response': ST('NO DATA'),
        },
        'CLEAR_DTC': {
            'Request': '^14' + ELM_FOOTER,
            'Descr': 'Clear DTC',
            'Header': ECU_ADDR_E,
            'Response': NA('11')
        },
        'UNKNOWN_A801_U': {
            'Request': '^A801' + ELM_FOOTER,
            'Descr': 'UNKNOWN_A801',
            'Header': ECU_ADDR_U,
            'Response': ST('NO DATA'),
        },
        'UNKNOWN_A801_E': {
            'Request': '^A801' + ELM_FOOTER,
            'Descr': 'UNKNOWN_A801',
            'Header': ECU_ADDR_E,
            'Response': HD(ECU_R_ADDR_E) + SZ('10') + DT('3E E8 01 00 04 FF FF')
        },
    # -------------------------------------------------------------------
    # UDS - MODE 10 - Diagnostic Session Control
        'UDS_DSC': {
            'Request': '^1002' + ELM_FOOTER,
            'Descr': 'DiagnosticSessionControl - Programming Session',
            'Header': ECU_ADDR_E,
            'Response': NA('22') # conditionsNotCorrect
        },
        'UDS_EDS': {
            'Request': '^1003' + ELM_FOOTER,
            'Descr': 'UDS Extended Diagnostics Session',
            'Header': ECU_ADDR_E,
            'Response': NA('12') # subFunctionNotSupported
        },
        'UDS_SESSION_REQ': {
            'Request': '^1092' + ELM_FOOTER,
            'Descr': 'UDS Session Request',
            'Header': ECU_ADDR_E,
            'Response': PA('')
        },
        # USD tests with ECU_ADDR_M are simulating a Continental ECU
        # (these pids are unrelated to the ones of a Toyota Auris Hybrid)
        # MODE 10 - Diagnostic Session Control
        'UDS_PS': {
            'Request': '^1002' + ELM_FOOTER,
            'Descr': 'UDS Programming Session',
            'Header': ECU_ADDR_M,
            'Response': PA('00 14 00 C8')
        },
        'UDS_EDS_M': {
            'Request': '^1003' + ELM_FOOTER,
            'Descr': 'UDS Extended Diagnostics Session',
            'Header': ECU_ADDR_M,
            'Response': PA('00 14 00 C8')
        },
    # -------------------------------------------------------------------
    # UDS - MODE 11 - ECU Reset - hardReset
        'UDS_ECU_RESET': {
            'Request': '^1101' + ELM_FOOTER,
            'Descr': 'EcuReset',
            'Header': ECU_ADDR_E,
            'Response': PA('')
        },
        'UDS_HR': {
            'Request': '^1101$',
            'Descr': 'UDS Hardware Reset',
            'Header': ECU_ADDR_M,
            'Task': 'task_hardware_reset'
        },
    # -------------------------------------------------------------------
    # UDS - MODE 1A (answer with 0 additional bytes)
        'UDS_SEI': {
            'Request': '^1A87' + ELM_FOOTER,
            'Descr': 'UDS Session ECU Info',
            'Header': ECU_ADDR_E,
            'Response': PA('80 00 00 00 00')
        },
        'UDS_SEI_M': {
            'Request': '^1A87' + ELM_FOOTER,
            'Descr': 'UDS Session ECU Info',
            'Header': ECU_ADDR_M,
            'Response': PA('87 01 22 05 14 FF 07 09 09 43 00 32 30 34 '
                           '35 34 35 33 38 33 32')
        },
        'UDS_SEI_1': {
            'Request': '^10165A8701220514$',
            'Descr': 'UDS Session ECU Info - 2',
            'Header': ECU_ADDR_M,
            'Response': ''
        },
    # -------------------------------------------------------------------
    # UDS - MODE 21
        'UNKNOWN_2100_E': {
            'Request': '^2100' + ELM_FOOTER,
            'Descr': 'UNKNOWN_2100',
            'Response': PA('BC 00 00 01')
        },
    # -------------------------------------------------------------------
    # UDS - Mode 22 - Read Data By Identifier (answer with 0 additional bytes)
    # All answers are wrong values at the moment
        'DTC_CNT': {
            'Request': '^220200' + ELM_FOOTER,
            'Descr': "Number of DTC's (if any)",
            'Response': PA('01')
        },
        'SPARK_ADV': {
            'Request': '^22116B' + ELM_FOOTER,
            'Descr': 'Current Spark Advance',
            'Response': PA('00 00')
        },
        'HB_SOC': {
            'Request': '^227A76' + ELM_FOOTER,
            'Descr': 'Hybrid Battery State of Charge',
            'Equation': 'A*100/255',
            'Min': '0',
            'Max': '200',
            'Unit': '%',
            'Response': PA('61 A1 80') # Wrong value! To be tested
        },
        'H_BATT': {
            'Request': '^227A53' + ELM_FOOTER,
            'Descr': 'Hybrid Battery Voltage',
            'Equation': 'D*4',
            'Min': '0',
            'Max': '1000',
            'Unit': 'Volts',
            'Response': PA('00') # Wrong value! To be tested
        },
        'INVT_CT': {
            'Request': '^221093' + ELM_FOOTER,
            'Descr': 'Inverter Coolant Temperature',
            'Equation': 'A*9/5-40',
            'Min': '-40',
            'Max': '300',
            'Unit': 'F',
            'Response': PA('00') # Wrong value! To be tested
        },
        'GN_IT': {
            'Request': '^221089' + ELM_FOOTER,
            'Descr': 'Generator Inverter Temperature',
            'Equation': 'A*9/5-40',
            'Min': '-40',
            'Max': '300',
            'Unit': 'F',
            'Response': PA('00') # Wrong value! To be tested
        },
        'B_CVT': {
            'Request': '^2210AB' + ELM_FOOTER,
            'Descr': 'Boosting Converter Temperature (Upper and Lower)',
            'Equation': 'A*9/5-40',
            'Min': '-40',
            'Max': '300',
            'Unit': 'F',
            'Header': ECU_ADDR_K,
            'Response': HD(ECU_R_ADDR_K) + SZ('03') + DT('61 A1 80') # Wrong value! To be tested
        },
    # -------------------------------------------------------------------
    # UDS - MODE 27 - Security Access
        'UDS_REQ_SEED': {
            'Request': '^2701' + ELM_FOOTER,
            'Descr': 'SecurityAccess - requestSeed',
            'Header': ECU_ADDR_E,
            'Response': PA('D6 D0 63 12') # response SID
        },
        'UDS_SEND_KEY': {
            'Request': '^2702' + ELM_FOOTER,
            'Descr': 'SecurityAccess - Send Key to ECU',
            'Header': ECU_ADDR_E,
            'Response': PA('')
        },
        'UDS_RS': {
            'Request': '^2711' + ELM_FOOTER,
            'Descr': 'UDS Request Seed',
            'Header': ECU_ADDR_E,
            'Response': NA('12')
        },
        'UDS_RS_M': {
            'Request': '^2711' + ELM_FOOTER,
            'Descr': 'UDS Request Seed',
            'Header': ECU_ADDR_M,
            'Task': 'task_request_seed'
        },
        'UDS_SK': {
            'Request': '^2712B151D58F' + ELM_FOOTER,
            'Descr': 'UDS Send Key',
            'Header': ECU_ADDR_M,
            'Response': PA('')
        },
    # -------------------------------------------------------------------
    # UDS - MODE 2E - writeDataByIdentifier Service (Appl. Inc.)
    'UDS_WF': {
        'Request': '^2EF15A' + ELM_DATA_FOOTER, # 2E,F1,5A - Write Fingerprint (Continental)
        'Descr': 'Write Fingerprint',
        'Info': '"Decoded fingerprint %s", cmd[6:]',
        'Header': ECU_ADDR_M,
        'Response': PA('')
    },
    'UDS_W_VIN': {
        'Request': '^2EF190' + ELM_DATA_FOOTER, # 2E,F1,90 - write dataIdentifier 0xF190 (VIN)
        'Descr': 'Write VIN',
        'Info': '"Decoded VIN: %s", repr(bytearray.fromhex(cmd[6:]).decode())',
        'Header': ECU_ADDR_M,
        'Response': PA('')
        },
    # -------------------------------------------------------------------
    # UDS - MODE 31 - UDS Routine Control - Start routine by local ID
        'UDS_ERASE_MEM': {
            'Request': '^3101' + ELM_DATA_FOOTER,
            # UDS Routine Control (31): Start (01), Delete Area (FF 00), Bootloader (01 00)
            'Descr': 'UDS Routine Control - Erase memory',
            'Header': ECU_ADDR_M,
            'Task': "task_erase_memory"
        },
        'UDS_RR_ERASE_MEM': {
            'Request': '^3103' + ELM_DATA_FOOTER,
            # UDS Routine Control (SID=31): routineControlType 03=Request Routine Result, Delete Area (FF 00)
            'Descr': 'UDS Routine Control - Erase memory - Request Routine Result',
            'Header': ECU_ADDR_M,
            'Task': "task_erase_mem_result"
        },
        # -------------------------------------------------------------------
    # UDS - MODE 3E - Tester Present
        'UDS_TP_AURIS': { # keep-alive function, Auris
            'Request': '^3E00' + ELM_FOOTER,
            'Descr': 'UDS Tester Present',
            'Header': ECU_ADDR_E,
            'Response': NA('12')
            # 7F=Negative Response, 3E=SID, 12=subFunctionNotSupported
        },
        'UDS_TESTER_PRESENT': { # keep-alive function, general positive answer
            'Request': '^3E00' + ELM_FOOTER, # Tester Present, Sub Function 00
            'Descr': 'UDS Tester Present',
            'Response': PA('')
        },
        'UDS_TP_NA': { # Tester present with suppression of the positive response
            'Request': '^3E80' + ELM_FOOTER, # Tester Present, Sub Function 80
            'Descr': 'UDS Tester Present - no answer',
            'Response': None
        },
    #------------------------------------------------------------
    # Custom OBD Commands - Toyota Prius
    # MODE 01
        'CUSTOM_SOC': {
            'Request': '^015B' + ELM_FOOTER,
            'Descr': 'State of Charge',
            'Equation': 'A * 20 / 51',
            'Min': '30',
            'Max': '90',
            'Unit': '%',
            'Header': ECU_ADDR_H,
            'Response': [
                HD(ECU_R_ADDR_H) + SZ('03') + DT('41 5B 95'),
                HD(ECU_R_ADDR_H) + SZ('03') + DT('41 5B 97'),
                HD(ECU_R_ADDR_H) + SZ('03') + DT('41 5B 96'),
                HD(ECU_R_ADDR_H) + SZ('03') + DT('41 5B 94'),
                HD(ECU_R_ADDR_H) + SZ('03') + DT('41 5B 99'),
                HD(ECU_R_ADDR_H) + SZ('03') + DT('41 5B 93'),
                HD(ECU_R_ADDR_H) + SZ('03') + DT('41 5B 9E'),
                HD(ECU_R_ADDR_H) + SZ('03') + DT('41 5B 92'),
                HD(ECU_R_ADDR_H) + SZ('03') + DT('41 5B 98'),
                HD(ECU_R_ADDR_H) + SZ('03') + DT('41 5B 9A')
            ]
        },
    #------------------------------------------------------------
    # UDS - MODE 21 - Read Data By Local ID - Toyota Prius
        "CUSTOM_CAL'D_LOAD": {
            'Request': '^2101' + ELM_FOOTER,
            'Descr': 'Calculated Load',
            'Equation': 'A * 20 / 51',
            'Min': '0',
            'Max': '100',
            'Unit': '%',
            'Header': ECU_ADDR_E,
            'Response': [
                        HD(ECU_R_ADDR_E) + SZ('10') + DT('1B 61 01 66 00 29 01') +
                        HD(ECU_R_ADDR_E) + SZ('21') + DT('3B 24 37 61 66 11 26') +
                        HD(ECU_R_ADDR_E) + SZ('22') + DT('53 00 9B 00 2A 7B 2A') +
                        HD(ECU_R_ADDR_E) + SZ('23') + DT('04 00 33 00 5D 39 73'),
                        HD(ECU_R_ADDR_E) + SZ('10') + DT('1B 61 01 98 00 57 03') +
                        HD(ECU_R_ADDR_E) + SZ('21') + DT('13 35 3A 61 44 14 3D') +
                        HD(ECU_R_ADDR_E) + SZ('22') + DT('00 00 13 02 32 85 32') +
                        HD(ECU_R_ADDR_E) + SZ('23') + DT('04 00 31 00 5B 39 38'),
                        HD(ECU_R_ADDR_E) + SZ('10') + DT('1B 61 01 A5 00 61 03') +
                        HD(ECU_R_ADDR_E) + SZ('21') + DT('8A 3D 37 61 59 14 EC') +
                        HD(ECU_R_ADDR_E) + SZ('22') + DT('4C 00 63 07 33 87 33') +
                        HD(ECU_R_ADDR_E) + SZ('23') + DT('04 00 32 00 5C 39 5F'),
                        HD(ECU_R_ADDR_E) + SZ('10') + DT('1B 61 01 00 00 00 00') +
                        HD(ECU_R_ADDR_E) + SZ('21') + DT('14 63 38 61 65 00 00') +
                        HD(ECU_R_ADDR_E) + SZ('22') + DT('2D 00 A6 00 2A 7C 2A') +
                        HD(ECU_R_ADDR_E) + SZ('23') + DT('04 00 33 00 5D 39 C1'),
                        HD(ECU_R_ADDR_E) + SZ('10') + DT('1B 61 01 96 00 55 03') +
                        HD(ECU_R_ADDR_E) + SZ('21') + DT('07 35 3A 61 47 14 65') +
                        HD(ECU_R_ADDR_E) + SZ('22') + DT('09 00 1F 02 32 85 32') +
                        HD(ECU_R_ADDR_E) + SZ('23') + DT('04 00 31 00 5B 39 4B'),
                        HD(ECU_R_ADDR_E) + SZ('10') + DT('1B 61 01 00 00 25 00') +
                        HD(ECU_R_ADDR_E) + SZ('21') + DT('1D 5C 3E 61 42 00 00') +
                        HD(ECU_R_ADDR_E) + SZ('22') + DT('03 00 05 00 2B 7C 2B') +
                        HD(ECU_R_ADDR_E) + SZ('23') + DT('04 00 31 00 5B 39 38'),
                        HD(ECU_R_ADDR_E) + SZ('10') + DT('1B 61 01 00 00 00 00') +
                        HD(ECU_R_ADDR_E) + SZ('21') + DT('12 63 3A 61 5B 00 00') +
                        HD(ECU_R_ADDR_E) + SZ('22') + DT('2B 00 6F 00 2B 7D 2B') +
                        HD(ECU_R_ADDR_E) + SZ('23') + DT('04 00 32 00 5C 39 AD'),
                        HD(ECU_R_ADDR_E) + SZ('10') + DT('1B 61 01 71 00 3C 02') +
                        HD(ECU_R_ADDR_E) + SZ('21') + DT('29 29 38 61 55 14 5C') +
                        HD(ECU_R_ADDR_E) + SZ('22') + DT('34 00 4D 03 2E 81 2F') +
                        HD(ECU_R_ADDR_E) + SZ('23') + DT('04 00 32 00 5C 39 5F'),
                        HD(ECU_R_ADDR_E) + SZ('10') + DT('1B 61 01 EE 00 94 06') +
                        HD(ECU_R_ADDR_E) + SZ('21') + DT('94 5B 39 61 56 19 6D') +
                        HD(ECU_R_ADDR_E) + SZ('22') + DT('1C 00 58 1B 47 9F 47') +
                        HD(ECU_R_ADDR_E) + SZ('23') + DT('04 00 32 00 5C 39 4B'),
                        HD(ECU_R_ADDR_E) + SZ('10') + DT('1B 61 01 F9 00 BF 12') +
                        HD(ECU_R_ADDR_E) + SZ('21') + DT('D9 60 36 61 5B 38 7E') +
                        HD(ECU_R_ADDR_E) + SZ('22') + DT('41 00 7A 46 71 D5 71') +
                        HD(ECU_R_ADDR_E) + SZ('23') + DT('04 00 32 00 5D 39 38'),
                        HD(ECU_R_ADDR_E) + SZ('10') + DT('1B 61 01 95 00 54 03') +
                        HD(ECU_R_ADDR_E) + SZ('21') + DT('02 35 38 61 4E 14 78') +
                        HD(ECU_R_ADDR_E) + SZ('22') + DT('16 00 37 02 31 85 31') +
                        HD(ECU_R_ADDR_E) + SZ('23') + DT('04 00 31 00 5B 39 4B'),
                        HD(ECU_R_ADDR_E) + SZ('10') + DT('1B 61 01 F3 00 B9 12') +
                        HD(ECU_R_ADDR_E) + SZ('21') + DT('B6 5D 35 61 62 39 C6') +
                        HD(ECU_R_ADDR_E) + SZ('22') + DT('69 00 90 43 6E D1 6E') +
                        HD(ECU_R_ADDR_E) + SZ('23') + DT('04 00 33 00 5D 39 4B'),
                        HD(ECU_R_ADDR_E) + SZ('10') + DT('1B 61 01 3E 00 1B 01') +
                        HD(ECU_R_ADDR_E) + SZ('21') + DT('8C 15 38 61 52 20 9A') +
                        HD(ECU_R_ADDR_E) + SZ('22') + DT('41 00 42 00 2C 7D 2C') +
                        HD(ECU_R_ADDR_E) + SZ('23') + DT('04 00 31 00 5C 39 5F'),
                        HD(ECU_R_ADDR_E) + SZ('10') + DT('1B 61 01 6F 00 44 02') +
                        HD(ECU_R_ADDR_E) + SZ('21') + DT('C6 28 38 61 4B 17 21') +
                        HD(ECU_R_ADDR_E) + SZ('22') + DT('31 00 2B 01 30 83 31') +
                        HD(ECU_R_ADDR_E) + SZ('23') + DT('04 00 31 00 5B 39 5F'),
                        HD(ECU_R_ADDR_E) + SZ('10') + DT('1B 61 01 E8 00 AD 0F') +
                        HD(ECU_R_ADDR_E) + SZ('21') + DT('EF 59 35 61 5E 34 C8') +
                        HD(ECU_R_ADDR_E) + SZ('22') + DT('59 00 85 2D 58 B5 58') +
                        HD(ECU_R_ADDR_E) + SZ('23') + DT('04 00 32 00 5D 39 4B')
                        ]
        },
        'CUSTOM_MG1T': {
            'Request': '^2161' + ELM_FOOTER,
            'Descr': 'MG1 temperature',
            'Equation': 'A - 40',
            'Min': '-40',
            'Max': '120',
            'Unit': 'C',
            'Header': ECU_ADDR_H,
            'Response': [
                        HD(ECU_R_ADDR_H) + SZ('07') + DT('61 61 3D 3C 3D 8F 4D'),
                        HD(ECU_R_ADDR_H) + SZ('07') + DT('61 61 3D 3C 3D 85 8E'),
                        HD(ECU_R_ADDR_H) + SZ('07') + DT('61 61 3E 3C 3E 7C 2C'),
                        HD(ECU_R_ADDR_H) + SZ('07') + DT('61 61 3D 3C 3D 87 95'),
                        HD(ECU_R_ADDR_H) + SZ('07') + DT('61 61 42 3C 42 79 0E'),
                        HD(ECU_R_ADDR_H) + SZ('07') + DT('61 61 3F 3C 3F 74 61'),
                        HD(ECU_R_ADDR_H) + SZ('07') + DT('61 61 3D 3C 3D 90 0E'),
                        HD(ECU_R_ADDR_H) + SZ('07') + DT('61 61 40 3C 40 90 0A'),
                        HD(ECU_R_ADDR_H) + SZ('07') + DT('61 61 40 3C 40 9B 9F'),
                        HD(ECU_R_ADDR_H) + SZ('07') + DT('61 61 3D 3C 3D 92 86'),
                        HD(ECU_R_ADDR_H) + SZ('07') + DT('61 61 41 3C 41 A3 EB'),
                        HD(ECU_R_ADDR_H) + SZ('07') + DT('61 61 43 3C 43 76 FB'),
                        HD(ECU_R_ADDR_H) + SZ('07') + DT('61 61 3E 3C 3E 9C 2E'),
                        HD(ECU_R_ADDR_H) + SZ('07') + DT('61 61 3D 3C 3D 8F BF'),
                        HD(ECU_R_ADDR_H) + SZ('07') + DT('61 61 3E 3C 3E 87 70')
                        ]
        },
        'CUSTOM_MG2T': {
            'Request': '^2162' + ELM_FOOTER,
            'Descr': 'MG2 temperature',
            'Equation': 'A - 40',
            'Min': '-40',
            'Max': '120',
            'Unit': 'C',
            'Header': ECU_ADDR_H,
            'Response': [
                        HD(ECU_R_ADDR_H) + SZ('07') + DT('61 62 3F 3A 3F 8E 13'),
                        HD(ECU_R_ADDR_H) + SZ('07') + DT('61 62 43 3A 43 9F EA'),
                        HD(ECU_R_ADDR_H) + SZ('07') + DT('61 62 3A 3A 3A 80 99'),
                        HD(ECU_R_ADDR_H) + SZ('07') + DT('61 62 40 3A 40 8A 22'),
                        HD(ECU_R_ADDR_H) + SZ('07') + DT('61 62 3D 3A 3D 87 FB'),
                        HD(ECU_R_ADDR_H) + SZ('07') + DT('61 62 44 3A 44 8A F1'),
                        HD(ECU_R_ADDR_H) + SZ('07') + DT('61 62 3B 3A 3B 82 6D'),
                        HD(ECU_R_ADDR_H) + SZ('07') + DT('61 62 3E 3A 3E 91 BC'),
                        HD(ECU_R_ADDR_H) + SZ('07') + DT('61 62 42 3A 42 95 3E'),
                        HD(ECU_R_ADDR_H) + SZ('07') + DT('61 62 40 3A 40 95 EC'),
                        HD(ECU_R_ADDR_H) + SZ('07') + DT('61 62 44 3A 44 97 85'),
                        HD(ECU_R_ADDR_H) + SZ('07') + DT('61 62 3A 3A 3A 80 75'),
                        HD(ECU_R_ADDR_H) + SZ('07') + DT('61 62 41 3A 41 8C 1B'),
                        HD(ECU_R_ADDR_H) + SZ('07') + DT('61 62 42 3A 42 9A CD'),
                        HD(ECU_R_ADDR_H) + SZ('07') + DT('61 62 3C 3A 3C 8D 81')
                        ]
        },
        'CUSTOM_MG1_TORQ': {
            'Request': '^2167' + ELM_FOOTER,
            'Descr': 'MG1 torque',
            'Equation': '(A * 256 + B) / 8 - 4096',
            'Min': '-4096',
            'Max': '4095.875',
            'Unit': 'Nm',
            'Header': ECU_ADDR_H,
            'Response': [
                        HD(ECU_R_ADDR_H) + SZ('07') + DT('61 67 7F FD 7F FA 00'),
                        HD(ECU_R_ADDR_H) + SZ('07') + DT('61 67 7F C9 7F C7 00'),
                        HD(ECU_R_ADDR_H) + SZ('07') + DT('61 67 80 00 80 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('07') + DT('61 67 7F 5A 7F 60 00'),
                        HD(ECU_R_ADDR_H) + SZ('07') + DT('61 67 7F E8 7F EB 00'),
                        HD(ECU_R_ADDR_H) + SZ('07') + DT('61 67 7F 67 7F 7B 00'),
                        HD(ECU_R_ADDR_H) + SZ('07') + DT('61 67 80 00 80 04 00'),
                        HD(ECU_R_ADDR_H) + SZ('07') + DT('61 67 7F CF 7F CD 00'),
                        HD(ECU_R_ADDR_H) + SZ('07') + DT('61 67 7E E3 7F 04 02'),
                        HD(ECU_R_ADDR_H) + SZ('07') + DT('61 67 7E E2 7E F2 01'),
                        HD(ECU_R_ADDR_H) + SZ('07') + DT('61 67 80 22 80 1C 00'),
                        HD(ECU_R_ADDR_H) + SZ('07') + DT('61 67 7F DD 7F E0 00'),
                        HD(ECU_R_ADDR_H) + SZ('07') + DT('61 67 7F AC 7F C6 00'),
                        HD(ECU_R_ADDR_H) + SZ('07') + DT('61 67 7F EE 7F ED 02'),
                        HD(ECU_R_ADDR_H) + SZ('07') + DT('61 67 80 00 7F FE 00')
                        ]
        },
        'CUSTOM_INV1T': {
            'Request': '^2170' + ELM_FOOTER,
            'Descr': 'Inverter MG1 Temp',
            'Equation': 'A - 40',
            'Min': '15',
            'Max': '150',
            'Unit': 'C',
            'Header': ECU_ADDR_H,
            'Response': [
                        HD(ECU_R_ADDR_H) + SZ('06') + DT('61 70 37 37 41 00'),
                        HD(ECU_R_ADDR_H) + SZ('06') + DT('61 70 37 37 39 00'),
                        HD(ECU_R_ADDR_H) + SZ('06') + DT('61 70 40 37 41 00'),
                        HD(ECU_R_ADDR_H) + SZ('06') + DT('61 70 38 37 47 00'),
                        HD(ECU_R_ADDR_H) + SZ('06') + DT('61 70 44 37 44 00'),
                        HD(ECU_R_ADDR_H) + SZ('06') + DT('61 70 3C 37 41 00'),
                        HD(ECU_R_ADDR_H) + SZ('06') + DT('61 70 41 37 40 00'),
                        HD(ECU_R_ADDR_H) + SZ('06') + DT('61 70 3D 37 41 00'),
                        HD(ECU_R_ADDR_H) + SZ('06') + DT('61 70 37 37 47 80'),
                        HD(ECU_R_ADDR_H) + SZ('06') + DT('61 70 3E 37 41 00'),
                        HD(ECU_R_ADDR_H) + SZ('06') + DT('61 70 44 37 47 00'),
                        HD(ECU_R_ADDR_H) + SZ('06') + DT('61 70 37 37 37 80')
                        ]
        },
        'CUSTOM_INV2T': {
            'Request': '^2171' + ELM_FOOTER,
            'Descr': 'Inverter MG2 Temp',
            'Equation': 'A - 40',
            'Min': '15',
            'Max': '150',
            'Unit': 'C',
            'Header': ECU_ADDR_H,
            'Response': [
                        HD(ECU_R_ADDR_H) + SZ('06') + DT('61 71 3A 37 46 00'),
                        HD(ECU_R_ADDR_H) + SZ('06') + DT('61 71 3D 37 46 00'),
                        HD(ECU_R_ADDR_H) + SZ('06') + DT('61 71 39 37 3C 00'),
                        HD(ECU_R_ADDR_H) + SZ('06') + DT('61 71 37 37 46 00'),
                        HD(ECU_R_ADDR_H) + SZ('06') + DT('61 71 3B 37 46 00'),
                        HD(ECU_R_ADDR_H) + SZ('06') + DT('61 71 3F 37 46 00'),
                        HD(ECU_R_ADDR_H) + SZ('06') + DT('61 71 38 37 46 00'),
                        HD(ECU_R_ADDR_H) + SZ('06') + DT('61 71 43 37 46 00'),
                        HD(ECU_R_ADDR_H) + SZ('06') + DT('61 71 37 37 39 00')
                        ]
        },
        'CUSTOM_BC_U': {
            'Request': '^2174' + ELM_FOOTER,
            'Descr': 'Boost converter temperature (upper)',
            'Equation': 'A - 40',
            'Min': '15',
            'Max': '150',
            'Unit': 'C',
            'Header': ECU_ADDR_H,
            'Response': [
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('0B 61 74 46 39 37 50') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('00 01 C8 03 E8 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('0B 61 74 43 3B 37 56') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('00 01 D1 03 E8 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('0B 61 74 3E 46 37 50') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('00 01 9B 05 12 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('0B 61 74 3D 41 37 50') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('00 01 9E 05 10 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('0B 61 74 49 39 37 56') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('00 01 E1 03 E8 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('0B 61 74 38 3C 37 56') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('00 01 9E 05 0D 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('0B 61 74 42 39 37 50') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('00 01 CD 01 D0 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('0B 61 74 4D 39 37 50') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('00 01 F8 03 E8 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('0B 61 74 4F 3A 37 50') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('00 01 E6 03 E9 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('0B 61 74 4A 3F 37 56') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('00 01 E4 04 3B 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('0B 61 74 38 37 37 3A') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('00 01 AA 01 A8 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('0B 61 74 37 37 37 37') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('00 01 BA 01 BB 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('0B 61 74 39 37 37 3F') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('00 01 9C 01 99 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('0B 61 74 47 3B 37 56') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('00 01 DA 03 E8 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('0B 61 74 38 37 37 3A') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('00 01 BA 01 BD 00 00')
                        ]
        },
        'CUSTOM_P_DCDC': {
            'Request': '^2175' + ELM_FOOTER,
            'Descr': 'Prohibit DC/DC converter signal',
            'Equation': '{A:6}',
            'Min': '0',
            'Max': '1',
            'Unit': 'Off/On',
            'Header': ECU_ADDR_H,
            'Response': [
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('08 61 75 20 0D 2F 3A') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('C5 C0 00 00 00 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('08 61 75 20 0D 2F 38') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('C5 80 00 00 00 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('08 61 75 20 0D 2F 39') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('C5 80 00 00 00 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('08 61 75 20 0D 2F 39') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('C5 C0 00 00 00 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('08 61 75 20 0D 2F 38') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('C5 C0 00 00 00 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('08 61 75 20 0D 2F 3A') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('C5 80 00 00 00 00 00')
                        ]
        },
        'CUSTOM_INV1_S/D': {
            'Request': '^2178' + ELM_FOOTER,
            'Descr': 'MG1 Inverter Shutdown',
            'Equation': '{A:7}',
            'Min': '0',
            'Max': '1',
            'Unit': 'Off/On',
            'Header': ECU_ADDR_H,
            'Response': [
                        HD(ECU_R_ADDR_H) + SZ('04') + DT('61 78 80 00'),
                        HD(ECU_R_ADDR_H) + SZ('04') + DT('61 78 00 00')
                        ]
        },
        'CUSTOM_DCTPD': {
            'Request': '^2179' + ELM_FOOTER,
            'Descr': 'DCDC Cnv Target Pulse Duty',
            'Equation': '(A * 256 + B) * 399.9 / 65535',
            'Min': '0',
            'Max': '100',
            'Unit': '%',
            'Header': ECU_ADDR_H,
            'Response': HD(ECU_R_ADDR_H) + SZ('06') + DT('61 79 2E 13 0A 00')
        },
        'CUSTOM_MG1_CF': {
            'Request': '^217C' + ELM_FOOTER,
            'Descr': 'MG1 Carrier Frequency',
            'Equation': 'A / 20',
            'Min': '0.75',
            'Max': '10',
            'Unit': 'kHz',
            'Header': ECU_ADDR_H,
            'Response': [
                        HD(ECU_R_ADDR_H) + SZ('04') + DT('61 7C 64 64'),
                        HD(ECU_R_ADDR_H) + SZ('04') + DT('61 7C 64 32'),
                        HD(ECU_R_ADDR_H) + SZ('04') + DT('61 7C 4B 64'),
                        HD(ECU_R_ADDR_H) + SZ('04') + DT('61 7C 4B 32')
                        ]
        },
        'CUSTOM_B_RATIO': {
            'Request': '^217D' + ELM_FOOTER,
            'Descr': 'Boost Ratio',
            'Equation': 'A / 2',
            'Min': '0',
            'Max': '100',
            'Unit': '%',
            'Header': ECU_ADDR_H,
            'Response': [
                        HD(ECU_R_ADDR_H) + SZ('05') + DT('61 7D 59 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('05') + DT('61 7D 6F 05 00'),
                        HD(ECU_R_ADDR_H) + SZ('05') + DT('61 7D 6B 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('05') + DT('61 7D 00 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('05') + DT('61 7D 77 05 00'),
                        HD(ECU_R_ADDR_H) + SZ('05') + DT('61 7D 86 05 00'),
                        HD(ECU_R_ADDR_H) + SZ('05') + DT('61 7D 95 05 00'),
                        HD(ECU_R_ADDR_H) + SZ('05') + DT('61 7D 64 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('05') + DT('61 7D 5C 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('05') + DT('61 7D 6D 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('05') + DT('61 7D 6A 05 00'),
                        HD(ECU_R_ADDR_H) + SZ('05') + DT('61 7D 00 05 00'),
                        HD(ECU_R_ADDR_H) + SZ('05') + DT('61 7D 57 00 00')
                        ]
        },
        'CUSTOM_V01': {
            'Request': '^2181' + ELM_FOOTER,
            'Descr': 'Battery Block Voltage -V01',
            'Equation': '(A * 256 + B) * 79.99 / 65535',
            'Min': '12',
            'Max': '20',
            'Unit': 'V',
            'Header': ECU_ADDR_H,
            'Response': [
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('22 61 81 37 7C 37 1A') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('38 08 38 08 38 BC 38') +
                        HD(ECU_R_ADDR_H) + SZ('22') + DT('BC 37 95 37 95 37 33') +
                        HD(ECU_R_ADDR_H) + SZ('23') + DT('37 22 38 49 38 5A 37') +
                        HD(ECU_R_ADDR_H) + SZ('24') + DT('53 37 95 AF 3B 09 74'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('22 61 81 38 72 38 20') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('38 08 38 08 38 08 38') +
                        HD(ECU_R_ADDR_H) + SZ('22') + DT('20 37 F7 37 F7 38 31') +
                        HD(ECU_R_ADDR_H) + SZ('23') + DT('38 39 38 31 38 49 38') +
                        HD(ECU_R_ADDR_H) + SZ('24') + DT('72 38 BC AF 4B 09 92'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('22 61 81 2D 58 2D 58') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('2E 1C 2E 0C 2D 81 2D') +
                        HD(ECU_R_ADDR_H) + SZ('22') + DT('91 2E 0C 2E 0C 2E A7') +
                        HD(ECU_R_ADDR_H) + SZ('23') + DT('2E B8 2E 6E 2E 7E 2D') +
                        HD(ECU_R_ADDR_H) + SZ('24') + DT('16 2D 2F AF 3B 07 BC'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('22 61 81 30 DD 30 B4') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('31 3F 31 3F 31 4F 31') +
                        HD(ECU_R_ADDR_H) + SZ('22') + DT('3F 30 C4 30 DD 31 26') +
                        HD(ECU_R_ADDR_H) + SZ('23') + DT('31 37 30 C4 30 C4 31') +
                        HD(ECU_R_ADDR_H) + SZ('24') + DT('4F 31 68 AF 3B 08 52'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('22 61 81 30 72 30 49') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('30 49 30 49 30 49 30') +
                        HD(ECU_R_ADDR_H) + SZ('22') + DT('49 30 28 30 28 30 39') +
                        HD(ECU_R_ADDR_H) + SZ('23') + DT('30 20 30 49 30 49 30') +
                        HD(ECU_R_ADDR_H) + SZ('24') + DT('49 30 72 AF 3B 08 3E'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('22 61 81 33 CE 33 AE') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('33 CE 33 CE 34 49 34') +
                        HD(ECU_R_ADDR_H) + SZ('22') + DT('62 33 E7 33 E7 34 49') +
                        HD(ECU_R_ADDR_H) + SZ('23') + DT('34 5A 33 F7 33 F7 34') +
                        HD(ECU_R_ADDR_H) + SZ('24') + DT('49 34 72 AF 2B 08 D4'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('22 61 81 37 CE 37 6C') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('37 33 37 1A 37 7C 37') +
                        HD(ECU_R_ADDR_H) + SZ('22') + DT('6C 37 6C 37 6C 37 53') +
                        HD(ECU_R_ADDR_H) + SZ('23') + DT('37 5C 37 7C 37 A5 37') +
                        HD(ECU_R_ADDR_H) + SZ('24') + DT('7C 37 BE AF 4B 09 7E'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('22 61 81 33 1A 32 F9') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('32 E1 32 D0 32 8F 32') +
                        HD(ECU_R_ADDR_H) + SZ('22') + DT('A7 32 B8 32 A7 32 D0') +
                        HD(ECU_R_ADDR_H) + SZ('23') + DT('32 D9 32 8F 32 A7 32') +
                        HD(ECU_R_ADDR_H) + SZ('24') + DT('E1 33 33 AF 3B 08 AC'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('22 61 81 3A 66 3A 24') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('3A 24 3A 24 3A 24 3A') +
                        HD(ECU_R_ADDR_H) + SZ('22') + DT('24 3A 14 3A 14 3A 24') +
                        HD(ECU_R_ADDR_H) + SZ('23') + DT('3A 2D 3A 24 3A 3D 3A') +
                        HD(ECU_R_ADDR_H) + SZ('24') + DT('76 3A C8 AF 4B 09 EC'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('22 61 81 32 1C 32 04') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('32 04 31 F3 31 F3 31') +
                        HD(ECU_R_ADDR_H) + SZ('22') + DT('DB 31 DB 31 DB 31 F3') +
                        HD(ECU_R_ADDR_H) + SZ('23') + DT('31 DB 31 DB 32 04 32') +
                        HD(ECU_R_ADDR_H) + SZ('24') + DT('1C 32 45 AF 3B 08 8E'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('22 61 81 2C 62 2C 8B') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('2C A3 2C 8B 2C 39 2C') +
                        HD(ECU_R_ADDR_H) + SZ('22') + DT('51 2D 06 2D 06 2C 18') +
                        HD(ECU_R_ADDR_H) + SZ('23') + DT('2C 18 2C 8B 2C 8B 2C') +
                        HD(ECU_R_ADDR_H) + SZ('24') + DT('8B 2C 8B AF 0A 07 A8'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('22 61 81 3A 24 39 FB') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('38 FD 38 E5 39 60 39') +
                        HD(ECU_R_ADDR_H) + SZ('22') + DT('70 39 26 39 0E 39 89') +
                        HD(ECU_R_ADDR_H) + SZ('23') + DT('39 81 39 26 39 26 39') +
                        HD(ECU_R_ADDR_H) + SZ('24') + DT('99 39 DB AF 4B 09 C4'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('22 61 81 36 F1 36 B8') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('35 37 35 26 36 8F 36') +
                        HD(ECU_R_ADDR_H) + SZ('22') + DT('8F 35 B2 35 A1 36 B8') +
                        HD(ECU_R_ADDR_H) + SZ('23') + DT('36 C0 35 89 35 78 36') +
                        HD(ECU_R_ADDR_H) + SZ('24') + DT('C8 37 1A AF 1A 09 6A'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('22 61 81 34 AC 34 83') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('34 72 34 72 34 72 34') +
                        HD(ECU_R_ADDR_H) + SZ('22') + DT('72 34 72 34 62 34 72') +
                        HD(ECU_R_ADDR_H) + SZ('23') + DT('34 6A 34 72 34 72 34') +
                        HD(ECU_R_ADDR_H) + SZ('24') + DT('9B 34 AC AF 4B 08 F2'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('22 61 81 32 D0 32 B8') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('32 A7 32 8F 32 8F 32') +
                        HD(ECU_R_ADDR_H) + SZ('22') + DT('8F 32 8F 32 7E 32 8F') +
                        HD(ECU_R_ADDR_H) + SZ('23') + DT('32 9F 32 8F 32 A7 32') +
                        HD(ECU_R_ADDR_H) + SZ('24') + DT('B8 32 E1 AF 3B 08 AC')
                        ]
        },
        'CUSTOM_TB_INTAKE': {
            'Request': '^2187' + ELM_FOOTER,
            'Descr': 'HV battery intake air temperature',
            'Equation': '(A * 256 + B) * 255.9 / 65535 - 50',
            'Min': '-50',
            'Max': '60',
            'Unit': 'C',
            'Header': ECU_ADDR_H,
            'Response': [
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('0A 61 87 3D C2 40 73') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('41 5E 40 8C 00 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('0A 61 87 3D A8 3F D4') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('40 DC 3F EE 00 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('0A 61 87 3D A8 3F D4') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('40 DC 40 07 00 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('0A 61 87 3D A8 40 57') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('41 45 40 73 00 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('0A 61 87 3E 11 40 C2') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('41 94 40 C2 00 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('0A 61 87 3D 8F 40 07') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('40 F5 40 23 00 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('0A 61 87 3D A8 40 3D') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('41 2B 40 57 00 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('0A 61 87 3D 8F 3F EE') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('40 F5 40 07 00 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('0A 61 87 3D F8 40 8C') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('41 7A 40 A8 00 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('0A 61 87 3D 8F 40 23') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('41 11 40 3D 00 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('0A 61 87 3D A8 3F B8') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('40 C2 3F EE 00 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('0A 61 87 3D A8 3F D4') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('40 C2 3F EE 00 00 00')
                        ]
        },
        'CUSTOM_IB': {
            'Request': '^218A' + ELM_FOOTER,
            'Descr': 'Power Resource IB',
            'Equation': '(A * 256 + B) / 100 - 327.68',
            'Min': '-200',
            'Max': '200',
            'Unit': 'Amperes',
            'Header': ECU_ADDR_H,
            'Response': [
                        HD(ECU_R_ADDR_H) + SZ('06') + DT('61 8A 82 17 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('06') + DT('61 8A 7F 6A 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('06') + DT('61 8A 78 29 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('06') + DT('61 8A 83 3C 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('06') + DT('61 8A 61 40 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('06') + DT('61 8A 8B 71 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('06') + DT('61 8A 81 53 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('06') + DT('61 8A 7C BE 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('06') + DT('61 8A 82 78 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('06') + DT('61 8A 65 A4 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('06') + DT('61 8A 7F 39 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('06') + DT('61 8A 62 C7 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('06') + DT('61 8A 67 EF 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('06') + DT('61 8A A3 B1 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('06') + DT('61 8A 66 68 00 00')
                        ]
        },
        'CUSTOM_C_FAN_0': {
            'Request': '^218E' + ELM_FOOTER,
            'Descr': 'Cooling Fan 0',
            'Equation': 'A / 2',
            'Min': '0',
            'Max': '100',
            'Unit': '%',
            'Header': ECU_ADDR_H,
            'Response': HD(ECU_R_ADDR_H) + SZ('04') + DT('61 8E 00 80')
        },
        'CUSTOM_VMIN': {
            'Request': '^2192' + ELM_FOOTER,
            'Descr': 'Battery block minimum voltage',
            'Equation': '(A * 256 + B) * 79.99 / 65535',
            'Min': '12',
            'Max': '20',
            'Unit': 'V',
            'Header': ECU_ADDR_H,
            'Response': [
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('11 61 92 33 F7 04 35') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('26 0D 0E 00 00 00 00') +
                        HD(ECU_R_ADDR_H) + SZ('22') + DT('00 00 00 00 00 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('11 61 92 3B 64 06 3C') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('83 0D 0E 00 00 00 00') +
                        HD(ECU_R_ADDR_H) + SZ('22') + DT('00 00 00 00 00 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('11 61 92 32 66 08 32') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('E1 00 0E 00 00 00 00') +
                        HD(ECU_R_ADDR_H) + SZ('22') + DT('00 00 00 00 00 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('11 61 92 31 B2 06 32') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('8F 0D 0E 00 00 00 00') +
                        HD(ECU_R_ADDR_H) + SZ('22') + DT('00 00 00 00 00 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('11 61 92 32 7E 07 32') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('E1 0D 0E 00 00 00 00') +
                        HD(ECU_R_ADDR_H) + SZ('22') + DT('00 00 00 00 00 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('11 61 92 2E 97 04 2F') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('74 06 0E 00 00 00 00') +
                        HD(ECU_R_ADDR_H) + SZ('22') + DT('00 00 00 00 00 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('11 61 92 32 7E 07 32') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('F9 0D 0E 00 00 00 00') +
                        HD(ECU_R_ADDR_H) + SZ('22') + DT('00 00 00 00 00 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('11 61 92 35 C2 09 36') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('66 00 0E 00 00 00 00') +
                        HD(ECU_R_ADDR_H) + SZ('22') + DT('00 00 00 00 00 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('11 61 92 34 C4 04 35') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('CA 00 0E 00 00 00 00') +
                        HD(ECU_R_ADDR_H) + SZ('22') + DT('00 00 00 00 00 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('11 61 92 31 EB 09 32') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('7E 0D 0E 00 00 00 00') +
                        HD(ECU_R_ADDR_H) + SZ('22') + DT('00 00 00 00 00 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('11 61 92 35 EB 06 36') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('56 00 0E 00 00 00 00') +
                        HD(ECU_R_ADDR_H) + SZ('22') + DT('00 00 00 00 00 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('11 61 92 32 2D 0B 32') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('A7 00 0E 00 00 00 00') +
                        HD(ECU_R_ADDR_H) + SZ('22') + DT('00 00 00 00 00 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('11 61 92 31 91 02 31') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('DB 0D 0E 00 00 00 00') +
                        HD(ECU_R_ADDR_H) + SZ('22') + DT('00 00 00 00 00 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('11 61 92 33 33 04 33') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('E7 0D 0E 00 00 00 00') +
                        HD(ECU_R_ADDR_H) + SZ('22') + DT('00 00 00 00 00 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('11 61 92 2E C0 04 2F') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('22 00 0E 00 00 00 00') +
                        HD(ECU_R_ADDR_H) + SZ('22') + DT('00 00 00 00 00 00 00')
                        ]
        },
        'CUSTOM_R01': {
            'Request': '^2195' + ELM_FOOTER,
            'Descr': 'Internal Resistance R01',
            'Equation': 'A / 1000',
            'Min': '0',
            'Max': '0.255',
            'Unit': 'ohm',
            'Header': ECU_ADDR_H,
            'Response': HD(ECU_R_ADDR_H) + SZ('10') + DT('10 61 95 17 16 15 16') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('16 16 16 16 16 16 16') +
                        HD(ECU_R_ADDR_H) + SZ('22') + DT('16 16 17 00 00 00 00')
        },
        'CUSTOM_BTY_CURR': {
            'Request': '^2198' + ELM_FOOTER,
            'Descr': 'Batt Pack Current Val',
            'Equation': '(A * 256 + B) / 100 - 327.68',
            'Min': '-200',
            'Max': '200',
            'Unit': 'Amperes',
            'Header': ECU_ADDR_H,
            'Response': [
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('0A 61 98 74 E9 5A A1') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('00 79 79 72 00 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('0A 61 98 7F 4D 5A A1') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('00 79 79 77 00 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('0A 61 98 62 57 5A A1') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('00 79 79 72 00 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('0A 61 98 9C 1A 5A A1') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('00 79 79 72 00 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('0A 61 98 87 10 5A A1') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('00 79 79 72 00 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('0A 61 98 9C AB 5A A1') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('00 79 79 73 00 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('0A 61 98 A2 58 59 A1') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('00 79 79 72 00 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('0A 61 98 72 15 59 A1') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('00 79 7B 72 00 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('0A 61 98 81 5C 5A A1') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('00 79 79 78 00 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('0A 61 98 63 40 59 A1') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('00 79 79 72 00 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('0A 61 98 7D 8E 5A A1') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('00 79 79 72 00 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('0A 61 98 85 EF 5A A1') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('00 79 79 72 00 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('0A 61 98 A0 1B 5A A1') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('00 79 79 72 00 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('0A 61 98 7C CE 5A A1') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('00 79 79 72 00 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('0A 61 98 91 31 5A A1') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('00 79 79 76 00 00 00')
                        ]
        },
        'CUSTOM_ECU_MODE': {
            'Request': '^219B' + ELM_FOOTER,
            'Descr': 'ECU Control Mode (Driving control mode=1,Current sensor offset mode=2,External charge control mode=3,Power supply end mode=4)',
            'Equation': 'A',
            'Min': '1',
            'Max': '4',
            'Unit': 'Number',
            'Header': ECU_ADDR_H,
            'Response': [
                        HD(ECU_R_ADDR_H) + SZ('06') + DT('61 9B 00 00 00 D3'),
                        HD(ECU_R_ADDR_H) + SZ('06') + DT('61 9B 00 00 00 D1'),
                        HD(ECU_R_ADDR_H) + SZ('06') + DT('61 9B 00 00 00 DA'),
                        HD(ECU_R_ADDR_H) + SZ('06') + DT('61 9B 00 00 00 D7'),
                        HD(ECU_R_ADDR_H) + SZ('06') + DT('61 9B 00 00 00 D4'),
                        HD(ECU_R_ADDR_H) + SZ('06') + DT('61 9B 00 00 00 CB'),
                        HD(ECU_R_ADDR_H) + SZ('06') + DT('61 9B 00 00 00 E4'),
                        HD(ECU_R_ADDR_H) + SZ('06') + DT('61 9B 00 00 00 C7'),
                        HD(ECU_R_ADDR_H) + SZ('06') + DT('61 9B 00 00 00 D2')
                        ]
        },
        'CUSTOM_MODEL_CODE': {
            'Request': '^21C1' + ELM_FOOTER,
            'Descr': 'Model Code (ZVW3##)',
            'Equation': 'ABCDEFG',
            'Min': '0',
            'Max': '0',
            'Unit': 'Number',
            'Header': ECU_ADDR_H,
            'Response': NA('12')
        },
        'CUSTOM_ECU_CODE': {
            'Request': '^21C2' + ELM_FOOTER,
            'Descr': 'ECU Code',
            'Equation': 'ABCDE',
            'Min': '0',
            'Max': '0',
            'Unit': 'Number',
            'Header': ECU_ADDR_H,
            'Response': HD(ECU_R_ADDR_H) + SZ('10') + DT('0F 61 C2 30 32 30 35') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('30 00 22 05 04 00 00') +
                        HD(ECU_R_ADDR_H) + SZ('22') + DT('00 01 00 00 00 00 00')
        },
        'CUSTOM_#CURR_CODE': {
            'Request': '^21E1' + ELM_FOOTER,
            'Descr': 'Number of Current Code',
            'Equation': 'A',
            'Min': '0',
            'Max': '255',
            'Unit': 'Number',
            'Header': ECU_ADDR_H,
            'Response': [
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('0A 61 E1 00 00 0E B1') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('20 00 04 07 00 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('0A 61 E1 00 00 0E B1') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('20 00 05 2E 00 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('0A 61 E1 00 00 0E B1') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('20 00 04 69 00 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('0A 61 E1 00 00 0E B1') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('20 00 02 D0 00 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('0A 61 E1 00 00 0E B1') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('20 00 01 DD 00 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('0A 61 E1 00 00 0E B1') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('20 00 06 56 00 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('0A 61 E1 00 00 0E B1') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('20 00 07 7D 00 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('0A 61 E1 00 00 0E B1') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('20 00 04 CA 00 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('0A 61 E1 00 00 0E B1') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('20 00 05 F4 00 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('0A 61 E1 00 00 0E B1') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('20 00 03 A4 00 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('0A 61 E1 00 00 0E B1') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('20 00 05 90 00 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('0A 61 E1 00 00 0E B1') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('20 00 03 3C 00 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('0A 61 E1 00 00 0E B1') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('20 00 07 1D 00 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('0A 61 E1 00 00 0E B1') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('20 00 02 63 00 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('0A 61 E1 00 00 0E B1') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('20 00 06 B8 00 00 00')
                        ]
        },
        'CUSTOM_TAIL_CANCEL': {
            'Request': '^2112' + ELM_FOOTER,
            'Descr': 'Tail Cancel SW',
            'Equation': '{A:5}',
            'Min': '0',
            'Max': '1',
            'Unit': 'Off/On',
            'Header': ECU_ADDR_I,
            'Response': [
                        HD(ECU_R_ADDR_I) + SZ('10') + DT('08 61 12 00 00 07 00') +
                        HD(ECU_R_ADDR_I) + SZ('21') + DT('00 00 00 00 00 00 00'),
                        HD(ECU_R_ADDR_I) + SZ('10') + DT('08 61 12 00 00 07 10') +
                        HD(ECU_R_ADDR_I) + SZ('21') + DT('00 00 00 00 00 00 00')
                        ]
        },
        'CUSTOM_AUX_B_VOLT': {
            'Request': '^2113' + ELM_FOOTER,
            'Descr': '+B Voltage Value',
            'Equation': 'A / 10',
            'Min': '0',
            'Max': '20',
            'Unit': 'V',
            'Header': ECU_ADDR_I,
            'Response': [
                        HD(ECU_R_ADDR_I) + SZ('03') + DT('61 13 95'),
                        HD(ECU_R_ADDR_I) + SZ('03') + DT('61 13 96')
                        ]
        },
        'CUSTOM_FUEL_LEVEL': {
            'Request': '^2129' + ELM_FOOTER,
            'Descr': 'Fuel Input',
            'Equation': 'A / 2',
            'Min': '0',
            'Max': '50',
            'Unit': 'Liter',
            'Header': ECU_ADDR_I,
            'Response': [
                        HD(ECU_R_ADDR_I) + SZ('03') + DT('61 29 02'),
                        HD(ECU_R_ADDR_I) + SZ('03') + DT('61 29 0A'),
                        HD(ECU_R_ADDR_I) + SZ('03') + DT('61 29 06')
                        ]
        },
        'CUSTOM_SUB_TANK': {
            'Request': '^212A' + ELM_FOOTER,
            'Descr': 'Sub tank level',
            'Response': NA('12'),
            'Header': ECU_ADDR_I
        },
        'CUSTOM_OIL_CHG_DIST': {
            'Request': '^2141' + ELM_FOOTER,
            'Descr': 'Distance Since Oil Change for U.S.A. (reset)',
            'Equation': 'A * 2514600 / 15625',
            'Min': '0',
            'Max': '41038',
            'Unit': 'km',
            'Header': ECU_ADDR_I,
            'Response': NA('12')
        },
        'CUSTOM_RHEOSTAT': {
            'Request': '^2168' + ELM_FOOTER,
            'Descr': 'Rheostat value (dark=0,bright=255)',
            'Equation': 'A',
            'Min': '0',
            'Max': '255',
            'Unit': 'Number',
            'Header': ECU_ADDR_I,
            'Response': NA('12')
        },
        'CUSTOM_SBB_QUERY': {
            'Request': '^21A7' + ELM_FOOTER,
            'Descr': 'Seat Belt Beep Query (Dis A=0,Ena R=32,Ena P=64,Dis D=96,Ena D=128,Dis P=160,192=Dis R,Ena A=160)',
            'Equation': 'A',
            'Min': '0',
            'Max': '192',
            'Unit': 'Number',
            'Header': ECU_ADDR_I,
            'Response': HD(ECU_R_ADDR_I) + SZ('03') + DT('61 A7 20')
        },
        'CUSTOM_RB_QUERY': {
            'Request': '^21AC' + ELM_FOOTER,
            'Descr': 'Reverse Beep Query (Ena=0,Dis=64)',
            'Equation': 'A',
            'Min': '0',
            'Max': '64',
            'Unit': 'Number',
            'Header': ECU_ADDR_I,
            'Response': HD(ECU_R_ADDR_I) + SZ('03') + DT('61 AC 40')
        },
        'CUSTOM_ROOM': {
            'Request': '^2121' + ELM_FOOTER,
            'Descr': 'Room Temp Sensor',
            'Equation': 'A * 63.75 / 255 - 6.5',
            'Min': '-6.5',
            'Max': '57.25',
            'Unit': 'C',
            'Header': ECU_ADDR_P,
            'Response': [
                        HD(ECU_R_ADDR_P) + SZ('03') + DT('61 21 54'),
                        HD(ECU_R_ADDR_P) + SZ('03') + DT('61 21 50'),
                        HD(ECU_R_ADDR_P) + SZ('03') + DT('61 21 52'),
                        HD(ECU_R_ADDR_P) + SZ('03') + DT('61 21 53'),
                        HD(ECU_R_ADDR_P) + SZ('03') + DT('61 21 51'),
                        HD(ECU_R_ADDR_P) + SZ('03') + DT('61 21 56'),
                        HD(ECU_R_ADDR_P) + SZ('03') + DT('61 21 55'),
                        HD(ECU_R_ADDR_P) + SZ('03') + DT('61 21 58')
                        ]
        },
        'CUSTOM_AMBIENT': {
            'Request': '^2122' + ELM_FOOTER,
            'Descr': 'Ambient Temp Sensor',
            'Equation': 'A * 89.25 / 255 - 23.3',
            'Min': '-23.3',
            'Max': '65.95',
            'Unit': 'C',
            'Header': ECU_ADDR_P,
            'Response': [
                        HD(ECU_R_ADDR_P) + SZ('03') + DT('61 22 60'),
                        HD(ECU_R_ADDR_P) + SZ('03') + DT('61 22 62'),
                        HD(ECU_R_ADDR_P) + SZ('03') + DT('61 22 5F'),
                        HD(ECU_R_ADDR_P) + SZ('03') + DT('61 22 63'),
                        HD(ECU_R_ADDR_P) + SZ('03') + DT('61 22 61'),
                        HD(ECU_R_ADDR_P) + SZ('03') + DT('61 22 5E')
                        ]
        },
        'CUSTOM_SOLAR_D': {
            'Request': '^2124' + ELM_FOOTER,
            'Descr': 'Solar Sensor (D side)',
            'Equation': 'A',
            'Min': '0',
            'Max': '255',
            'Unit': 'Number',
            'Header': ECU_ADDR_P,
            'Response': [
                        HD(ECU_R_ADDR_P) + SZ('03') + DT('61 24 01'),
                        HD(ECU_R_ADDR_P) + SZ('03') + DT('61 24 00')
                        ]
        },
        'CUSTOM_COOLANT': {
            'Request': '^2126' + ELM_FOOTER,
            'Descr': 'Engine Coolant Temp',
            'Equation': 'A * 89.25 / 255 + 1.3',
            'Min': '1.3',
            'Max': '90.55',
            'Unit': 'C',
            'Header': ECU_ADDR_P,
            'Response': [
                        HD(ECU_R_ADDR_P) + SZ('03') + DT('61 26 5E'),
                        HD(ECU_R_ADDR_P) + SZ('03') + DT('61 26 98'),
                        HD(ECU_R_ADDR_P) + SZ('03') + DT('61 26 6B'),
                        HD(ECU_R_ADDR_P) + SZ('03') + DT('61 26 A4'),
                        HD(ECU_R_ADDR_P) + SZ('03') + DT('61 26 7E'),
                        HD(ECU_R_ADDR_P) + SZ('03') + DT('61 26 B0'),
                        HD(ECU_R_ADDR_P) + SZ('03') + DT('61 26 4C'),
                        HD(ECU_R_ADDR_P) + SZ('03') + DT('61 26 91'),
                        HD(ECU_R_ADDR_P) + SZ('03') + DT('61 26 8E'),
                        HD(ECU_R_ADDR_P) + SZ('03') + DT('61 26 55'),
                        HD(ECU_R_ADDR_P) + SZ('03') + DT('61 26 81'),
                        HD(ECU_R_ADDR_P) + SZ('03') + DT('61 26 AF'),
                        HD(ECU_R_ADDR_P) + SZ('03') + DT('61 26 84'),
                        HD(ECU_R_ADDR_P) + SZ('03') + DT('61 26 75'),
                        HD(ECU_R_ADDR_P) + SZ('03') + DT('61 26 4B')
                        ]
        },
        'CUSTOM_SET_TEMP_D': {
            'Request': '^2129[012]?$',
            'Descr': 'Set Temperature (D side)',
            'Response': NA('12'),
            'Header': ECU_ADDR_P
        },
        'CUSTOM_BLOWER_LEVEL': {
            'Request': '^213C' + ELM_FOOTER,
            'Descr': 'Blower Motor Speed Level',
            'Equation': 'A * 31 / 255',
            'Min': '0',
            'Max': '31',
            'Unit': 'Number',
            'Header': ECU_ADDR_P,
            'Response': [
                        HD(ECU_R_ADDR_P) + SZ('03') + DT('61 3C 04'),
                        HD(ECU_R_ADDR_P) + SZ('03') + DT('61 3C 0B'),
                        HD(ECU_R_ADDR_P) + SZ('03') + DT('61 3C 0F'),
                        HD(ECU_R_ADDR_P) + SZ('03') + DT('61 3C 0E'),
                        HD(ECU_R_ADDR_P) + SZ('03') + DT('61 3C 09'),
                        HD(ECU_R_ADDR_P) + SZ('03') + DT('61 3C 05'),
                        HD(ECU_R_ADDR_P) + SZ('03') + DT('61 3C 10'),
                        HD(ECU_R_ADDR_P) + SZ('03') + DT('61 3C 00')
                        ]
        },
        'CUSTOM_ADJAMBIENT': {
            'Request': '^213D' + ELM_FOOTER,
            'Descr': 'Adjusted Ambient Temp',
            'Equation': 'A * 81.6 / 255 - 30.8',
            'Min': '-30.8',
            'Max': '50.8',
            'Unit': 'C',
            'Header': ECU_ADDR_P,
            'Response': [
                        HD(ECU_R_ADDR_P) + SZ('03') + DT('61 3D 81'),
                        HD(ECU_R_ADDR_P) + SZ('03') + DT('61 3D 83'),
                        HD(ECU_R_ADDR_P) + SZ('03') + DT('61 3D 85'),
                        HD(ECU_R_ADDR_P) + SZ('03') + DT('61 3D 80'),
                        HD(ECU_R_ADDR_P) + SZ('03') + DT('61 3D 7F'),
                        HD(ECU_R_ADDR_P) + SZ('03') + DT('61 3D 82'),
                        HD(ECU_R_ADDR_P) + SZ('03') + DT('61 3D 84')
                        ]
        },
        'CUSTOM_A/O_SP_D': {
            'Request': '^2143' + ELM_FOOTER,
            'Descr': 'Air Outlet Servo Pulse (D)',
            'Equation': 'A',
            'Min': '0',
            'Max': '255',
            'Unit': 'Number',
            'Header': ECU_ADDR_P,
            'Response': [
                        HD(ECU_R_ADDR_P) + SZ('06') + DT('61 43 09 09 00 00'),
                        HD(ECU_R_ADDR_P) + SZ('06') + DT('61 43 05 05 00 00')
                        ]
        },
        'CUSTOM_A/I_DTP': {
            'Request': '^2144' + ELM_FOOTER,
            'Descr': 'Air Inlet Damper Targ Pulse',
            'Equation': 'A',
            'Min': '0',
            'Max': '255',
            'Unit': 'Number',
            'Header': ECU_ADDR_P,
            'Response': HD(ECU_R_ADDR_P) + SZ('06') + DT('61 44 07 07 00 00')
        },
        'CUSTOM_COMP_SPD': {
            'Request': '^2149' + ELM_FOOTER,
            'Descr': 'Compressor Speed',
            'Equation': 'A * 256 + B',
            'Min': '0',
            'Max': '10000',
            'Unit': 'RPM',
            'Header': ECU_ADDR_P,
            'Response': HD(ECU_R_ADDR_P) + SZ('04') + DT('61 49 00 00')
        },
        'CUSTOM_COMP_T_SPD': {
            'Request': '^214A' + ELM_FOOTER,
            'Descr': 'Compressor Target Speed',
            'Equation': 'A * 256 + B',
            'Min': '0',
            'Max': '10000',
            'Unit': 'RPM',
            'Header': ECU_ADDR_P,
            'Response': HD(ECU_R_ADDR_P) + SZ('04') + DT('61 4A 00 00')
        },
        'CUSTOM_EVAP_FIN': {
            'Request': '^214B' + ELM_FOOTER,
            'Descr': 'Evaporator Fin Thermistor',
            'Equation': 'A * 89.25 / 255 - 29.7',
            'Min': '-29.7',
            'Max': '59.55',
            'Unit': 'C',
            'Header': ECU_ADDR_P,
            'Response': [
                        HD(ECU_R_ADDR_P) + SZ('03') + DT('61 4B 77'),
                        HD(ECU_R_ADDR_P) + SZ('03') + DT('61 4B 76'),
                        HD(ECU_R_ADDR_P) + SZ('03') + DT('61 4B 79'),
                        HD(ECU_R_ADDR_P) + SZ('03') + DT('61 4B 7A'),
                        HD(ECU_R_ADDR_P) + SZ('03') + DT('61 4B 7B'),
                        HD(ECU_R_ADDR_P) + SZ('03') + DT('61 4B 78')
                        ]
        },
        'CUSTOM_EVAP_TGT': {
            'Request': '^214C' + ELM_FOOTER,
            'Descr': 'Evaporator Target Temp',
            'Equation': '(A * 256 + B) / 100 - 327.68',
            'Min': '-29.7',
            'Max': '59.55',
            'Unit': 'C',
            'Header': ECU_ADDR_P,
            'Response': HD(ECU_R_ADDR_P) + SZ('04') + DT('61 4C 84 4C')
        },
        'CUSTOM_REG_PRES': {
            'Request': '^2153' + ELM_FOOTER,
            'Descr': 'Regulator Pressure Sensor',
            'Equation': 'A * 3.75105 / 255 - 0.45668',
            'Min': '-0.45668',
            'Max': '3.29437',
            'Unit': 'MPaG',
            'Header': ECU_ADDR_P,
            'Response': [
                        HD(ECU_R_ADDR_P) + SZ('03') + DT('61 53 39'),
                        HD(ECU_R_ADDR_P) + SZ('03') + DT('61 53 37'),
                        HD(ECU_R_ADDR_P) + SZ('03') + DT('61 53 38')
                        ]
        },
        'CUSTOM_FR_WS': {
            'Request': '^2103' + ELM_FOOTER,
            'Descr': 'FR Wheel Speed',
            'Equation': 'A * 32 / 25',
            'Min': '0',
            'Max': '200',
            'Unit': 'km/h',
            'Header': ECU_ADDR_S,
            'Response': [
                        HD(ECU_R_ADDR_S) + SZ('06') + DT('61 03 3E 3E 3D 3D'),
                        HD(ECU_R_ADDR_S) + SZ('06') + DT('61 03 06 06 06 06'),
                        HD(ECU_R_ADDR_S) + SZ('06') + DT('61 03 33 33 32 32'),
                        HD(ECU_R_ADDR_S) + SZ('06') + DT('61 03 31 31 31 31'),
                        HD(ECU_R_ADDR_S) + SZ('06') + DT('61 03 02 02 02 02'),
                        HD(ECU_R_ADDR_S) + SZ('06') + DT('61 03 19 19 19 19'),
                        HD(ECU_R_ADDR_S) + SZ('06') + DT('61 03 28 28 27 27'),
                        HD(ECU_R_ADDR_S) + SZ('06') + DT('61 03 4D 4D 4D 4D'),
                        HD(ECU_R_ADDR_S) + SZ('06') + DT('61 03 16 14 16 14'),
                        HD(ECU_R_ADDR_S) + SZ('06') + DT('61 03 29 29 29 29'),
                        HD(ECU_R_ADDR_S) + SZ('06') + DT('61 03 4A 4A 4B 4B'),
                        HD(ECU_R_ADDR_S) + SZ('06') + DT('61 03 38 38 37 37'),
                        HD(ECU_R_ADDR_S) + SZ('06') + DT('61 03 00 00 00 00'),
                        HD(ECU_R_ADDR_S) + SZ('06') + DT('61 03 13 12 12 12')
                        ]
        },
        'CUSTOM_YR1': {
            'Request': '^2106' + ELM_FOOTER,
            'Descr': 'Yaw Rate Sensor',
            'Equation': 'A - 128',
            'Min': '-128',
            'Max': '127',
            'Unit': 'degrees/s',
            'Header': ECU_ADDR_S,
            'Response': [
                        HD(ECU_R_ADDR_S) + SZ('06') + DT('61 06 80 80 8A 5F'),
                        HD(ECU_R_ADDR_S) + SZ('06') + DT('61 06 80 80 80 0F'),
                        HD(ECU_R_ADDR_S) + SZ('06') + DT('61 06 7E 7E 7F D3'),
                        HD(ECU_R_ADDR_S) + SZ('06') + DT('61 06 7E 7E 7F 01'),
                        HD(ECU_R_ADDR_S) + SZ('06') + DT('61 06 7D 7D 7F 97'),
                        HD(ECU_R_ADDR_S) + SZ('06') + DT('61 06 80 80 80 2D'),
                        HD(ECU_R_ADDR_S) + SZ('06') + DT('61 06 80 80 80 00'),
                        HD(ECU_R_ADDR_S) + SZ('06') + DT('61 06 82 82 86 09'),
                        HD(ECU_R_ADDR_S) + SZ('06') + DT('61 06 99 99 85 82'),
                        HD(ECU_R_ADDR_S) + SZ('06') + DT('61 06 80 80 80 1E'),
                        HD(ECU_R_ADDR_S) + SZ('06') + DT('61 06 8C 8C 83 57')
                        ]
        },
        'CUSTOM_WC_PRES': {
            'Request': '^2107' + ELM_FOOTER,
            'Descr': 'Wheel Cylinder Pressure Sensor',
            'Equation': 'A / 51',
            'Min': '0',
            'Max': '5',
            'Unit': 'V',
            'Header': ECU_ADDR_S,
            'Response': [
                        HD(ECU_R_ADDR_S) + SZ('03') + DT('61 07 1B'),
                        HD(ECU_R_ADDR_S) + SZ('03') + DT('61 07 1C'),
                        HD(ECU_R_ADDR_S) + SZ('03') + DT('61 07 19')
                        ]
        },
        'CUSTOM_LATERAL_G': {
            'Request': '^2147' + ELM_FOOTER,
            'Descr': 'Lateral G',
            'Equation': 'A * 50.02 / 255 - 25.11',
            'Min': '-25.11',
            'Max': '24.91',
            'Unit': 'm/s2',
            'Header': ECU_ADDR_S,
            'Response': [
                        HD(ECU_R_ADDR_S) + SZ('07') + DT('61 47 F5 00 65 70 79'),
                        HD(ECU_R_ADDR_S) + SZ('07') + DT('61 47 0C FF A0 8C 80'),
                        HD(ECU_R_ADDR_S) + SZ('07') + DT('61 47 FD F8 7B 7F 13'),
                        HD(ECU_R_ADDR_S) + SZ('07') + DT('61 47 F8 FB 75 7D EE'),
                        HD(ECU_R_ADDR_S) + SZ('07') + DT('61 47 FE FA 7E 7F CC'),
                        HD(ECU_R_ADDR_S) + SZ('07') + DT('61 47 00 FF 80 89 24'),
                        HD(ECU_R_ADDR_S) + SZ('07') + DT('61 47 FC 0A 7B 7F 30'),
                        HD(ECU_R_ADDR_S) + SZ('07') + DT('61 47 01 00 80 80 0B'),
                        HD(ECU_R_ADDR_S) + SZ('07') + DT('61 47 FD 09 7D 7F 91'),
                        HD(ECU_R_ADDR_S) + SZ('07') + DT('61 47 00 F4 80 80 0B'),
                        HD(ECU_R_ADDR_S) + SZ('07') + DT('61 47 00 FF 80 8A 5F'),
                        HD(ECU_R_ADDR_S) + SZ('07') + DT('61 47 00 FC 80 80 0B'),
                        HD(ECU_R_ADDR_S) + SZ('07') + DT('61 47 FE FE 7F 7F D9'),
                        HD(ECU_R_ADDR_S) + SZ('07') + DT('61 47 03 00 83 80 84'),
                        HD(ECU_R_ADDR_S) + SZ('07') + DT('61 47 00 FE 80 80 07')
                        ]
        },
        'CUSTOM_REGENCOOP': {
            'Request': '^2158' + ELM_FOOTER,
            'Descr': 'Regen Cooperation',
            'Equation': '{A:7}',
            'Min': '0',
            'Max': '1',
            'Unit': 'Off/On',
            'Header': ECU_ADDR_S,
            'Response': [
                        HD(ECU_R_ADDR_S) + SZ('03') + DT('61 58 00'),
                        HD(ECU_R_ADDR_S) + SZ('03') + DT('61 58 80')
                        ]
        },
        'CUSTOM_SLA_CURR': {
            'Request': '^21A3' + ELM_FOOTER,
            'Descr': 'SLA Solenoid Current',
            'Equation': 'A * 3 / 255',
            'Min': '0',
            'Max': '3',
            'Unit': 'A',
            'Header': ECU_ADDR_S,
            'Response': [
                        HD(ECU_R_ADDR_S) + SZ('10') + DT('08 61 A3 25 00 24 33') +
                        HD(ECU_R_ADDR_S) + SZ('21') + DT('4A 4A 00 00 00 00 00'),
                        HD(ECU_R_ADDR_S) + SZ('10') + DT('08 61 A3 00 25 24 33') +
                        HD(ECU_R_ADDR_S) + SZ('21') + DT('4A 4A 00 00 00 00 00'),
                        HD(ECU_R_ADDR_S) + SZ('10') + DT('08 61 A3 30 00 24 34') +
                        HD(ECU_R_ADDR_S) + SZ('21') + DT('4A 4A 00 00 00 00 00'),
                        HD(ECU_R_ADDR_S) + SZ('10') + DT('08 61 A3 00 00 24 33') +
                        HD(ECU_R_ADDR_S) + SZ('21') + DT('00 00 00 00 00 00 00'),
                        HD(ECU_R_ADDR_S) + SZ('10') + DT('08 61 A3 00 00 24 34') +
                        HD(ECU_R_ADDR_S) + SZ('21') + DT('00 00 00 00 00 00 00'),
                        HD(ECU_R_ADDR_S) + SZ('10') + DT('08 61 A3 18 00 24 33') +
                        HD(ECU_R_ADDR_S) + SZ('21') + DT('4A 4A 00 00 00 00 00')
                        ]
        },
        'CUSTOM_INSP_MODE': {
            'Request': '^21A6' + ELM_FOOTER,
            'Descr': 'Inspection Mode (Other=Off,Inspect=On)',
            'Equation': '{A:7}',
            'Min': '0',
            'Max': '1',
            'Unit': 'Off/On',
            'Header': ECU_ADDR_S,
            'Response': HD(ECU_R_ADDR_S) + SZ('03') + DT('61 A6 00')
        },
        'CUSTOM_HAZ_HIST': {
            'Request': '^21BC' + ELM_FOOTER,
            'Descr': 'Hazard Switch History (Incomplete=Off,Complete=On)',
            'Equation': '{A:5}',
            'Min': '0',
            'Max': '1',
            'Unit': 'Off/On',
            'Header': ECU_ADDR_S,
            'Response': HD(ECU_R_ADDR_S) + SZ('03') + DT('61 BC 00')
        },
        'CUSTOM_FRS_OPEN': {
            'Request': '^21BE' + ELM_FOOTER,
            'Descr': 'FR Speed Open (Normal=0,Error=1)',
            'Equation': '{A:7}',
            'Min': '0',
            'Max': '1',
            'Unit': 'Off/On',
            'Header': ECU_ADDR_S,
            'Response': HD(ECU_R_ADDR_S) + SZ('05') + DT('61 BE 00 00 00')
        },
    # New custom OBD Commands
        'CUSTOM_FSS1': {
            'Request': '^2103' + ELM_FOOTER,
            'Descr': 'Fuel System Status #1 (OL=1,CL=2,OLDrive=4,OLFault=8,CLFault=16)',
            'Equation': 'A',
            'Min': '1',
            'Max': '16',
            'Unit': '',
            'Header': ECU_ADDR_E,
            'Response': [
                        HD(ECU_R_ADDR_E) + SZ('10') + DT('0A 61 03 01 00 80 7C') +
                        HD(ECU_R_ADDR_E) + SZ('21') + DT('9F 00 00 01 00 00 00'),
                        HD(ECU_R_ADDR_E) + SZ('10') + DT('0A 61 03 00 00 80 7D') +
                        HD(ECU_R_ADDR_E) + SZ('21') + DT('8A 00 00 01 00 00 00'),
                        HD(ECU_R_ADDR_E) + SZ('10') + DT('0A 61 03 02 00 84 7C') +
                        HD(ECU_R_ADDR_E) + SZ('21') + DT('A2 00 00 01 00 00 00')
                        ]
        },
        'CUSTOM_TAFR': {
            'Request': '^2104' + ELM_FOOTER,
            'Descr': 'Target Air-Fuel Ratio',
            'Equation': '(A * 256 + B) * 1.99 / 65535',
            'Min': '0',
            'Max': '1.99',
            'Unit': '',
            'Header': ECU_ADDR_E,
            'Response': [
                        HD(ECU_R_ADDR_E) + SZ('10') + DT('0E 61 04 7F F2 7F 73') +
                        HD(ECU_R_ADDR_E) + SZ('21') + DT('6A 11 7F 73 80 01 00') +
                        HD(ECU_R_ADDR_E) + SZ('22') + DT('FF 00 00 00 00 00 00'),
                        HD(ECU_R_ADDR_E) + SZ('10') + DT('0E 61 04 7F F2 68 1C') +
                        HD(ECU_R_ADDR_E) + SZ('21') + DT('27 04 68 1C 7F 39 00') +
                        HD(ECU_R_ADDR_E) + SZ('22') + DT('FF 00 00 00 00 00 00'),
                        HD(ECU_R_ADDR_E) + SZ('10') + DT('0E 61 04 60 17 7F FB') +
                        HD(ECU_R_ADDR_E) + SZ('21') + DT('6A D9 7F FB 80 03 00') +
                        HD(ECU_R_ADDR_E) + SZ('22') + DT('FF 00 00 00 00 00 00')
                        ]
        },
        'CUSTOM_CAT_B1S1_SG': {
            'Request': '^2105' + ELM_FOOTER,
            'Descr': 'Catalyst Temp B1 S1 (Singapore)',
            'Equation': '(A * 256 + B) / 10 - 40',
            'Min': '-40',
            'Max': '6513.5',
            'Unit': 'C',
            'Header': ECU_ADDR_E,
            'Response': [
                        HD(ECU_R_ADDR_E) + SZ('06') + DT('61 05 0F 26 0B 79'),
                        HD(ECU_R_ADDR_E) + SZ('06') + DT('61 05 0F 54 0B A7'),
                        HD(ECU_R_ADDR_E) + SZ('06') + DT('61 05 0F 2D 0B 80'),
                        HD(ECU_R_ADDR_E) + SZ('06') + DT('61 05 0F 46 0B 99'),
                        HD(ECU_R_ADDR_E) + SZ('06') + DT('61 05 0F 3D 0B 90'),
                        HD(ECU_R_ADDR_E) + SZ('06') + DT('61 05 0F 4D 0B A0'),
                        HD(ECU_R_ADDR_E) + SZ('06') + DT('61 05 0F 28 0B 6D'),
                        HD(ECU_R_ADDR_E) + SZ('06') + DT('61 05 0F 1E 0B 71'),
                        HD(ECU_R_ADDR_E) + SZ('06') + DT('61 05 0F 91 0B 95'),
                        HD(ECU_R_ADDR_E) + SZ('06') + DT('61 05 0F 35 0B 88')
                        ]
        },
        'CUSTOM_MIL': {
            'Request': '^2106' + ELM_FOOTER,
            'Descr': 'MIL',
            'Equation': '{A:7}',
            'Min': '0',
            'Max': '1',
            'Unit': 'Off/On',
            'Header': ECU_ADDR_E,
            'Response': HD(ECU_R_ADDR_E) + SZ('10') + DT('0C 61 06 00 07 A1 00') +
                        HD(ECU_R_ADDR_E) + SZ('21') + DT('03 06 00 00 00 00 00')
        },
        'CUSTOM_HV_COMM': {
            'Request': '^2124' + ELM_FOOTER,
            'Descr': 'Communication with HV',
            'Equation': '{A:5}',
            'Min': '0',
            'Max': '1',
            'Unit': 'Off/On',
            'Header': ECU_ADDR_E,
            'Response': HD(ECU_R_ADDR_E) + SZ('03') + DT('61 24 28')
        },
        'CUSTOM_INIT_ECT': {
            'Request': '^2137' + ELM_FOOTER,
            'Descr': 'Initial Engine Coolant Temp',
            'Equation': 'A * 159.3 / 255 - 40',
            'Min': '-40',
            'Max': '119.3',
            'Unit': 'C',
            'Header': ECU_ADDR_E,
            'Response': [
                        HD(ECU_R_ADDR_E) + SZ('10') + DT('11 61 37 59 58 83 46') +
                        HD(ECU_R_ADDR_E) + SZ('21') + DT('7F A0 80 00 00 00 00') +
                        HD(ECU_R_ADDR_E) + SZ('22') + DT('00 1A DC 00 00 00 00'),
                        HD(ECU_R_ADDR_E) + SZ('10') + DT('11 61 37 59 58 83 46') +
                        HD(ECU_R_ADDR_E) + SZ('21') + DT('7F A0 80 00 00 00 00') +
                        HD(ECU_R_ADDR_E) + SZ('22') + DT('00 1A DC 04 00 00 00'),
                        HD(ECU_R_ADDR_E) + SZ('10') + DT('11 61 37 59 58 83 46') +
                        HD(ECU_R_ADDR_E) + SZ('21') + DT('7F A0 80 00 00 00 00') +
                        HD(ECU_R_ADDR_E) + SZ('22') + DT('00 1A DC 44 00 00 00')
                        ]
        },
        'CUSTOM_INJ_VOL': {
            'Request': '^213C' + ELM_FOOTER,
            'Descr': 'Injection volume (Cylinder 1) for 10 times',
            'Equation': '(A * 256 + B) * 2.047 / 65535',
            'Min': '0',
            'Max': '2.047',
            'Unit': 'ml',
            'Header': ECU_ADDR_E,
            'Response': [
                        HD(ECU_R_ADDR_E) + SZ('07') + DT('61 3C 09 82 09 43 80'),
                        HD(ECU_R_ADDR_E) + SZ('07') + DT('61 3C 15 8F 10 D1 80'),
                        HD(ECU_R_ADDR_E) + SZ('07') + DT('61 3C 08 65 07 B3 80')
                        ]
        },
        'CUSTOM_EGR_STEP': {
            'Request': '^2147' + ELM_FOOTER,
            'Descr': 'EGR Step Position',
            'Equation': 'A',
            'Min': '0',
            'Max': '120',
            'Unit': 'step',
            'Header': ECU_ADDR_E,
            'Response': HD(ECU_R_ADDR_E) + SZ('03') + DT('61 47 00')
        },
        'CUSTOM_REQENGTORQ': {
            'Request': '^2149' + ELM_FOOTER,
            'Descr': 'Requested Engine Torque',
            'Equation': '(A * 256 + B) / 4',
            'Min': '0',
            'Max': '73',
            'Unit': 'kW',
            'Header': ECU_ADDR_E,
            'Response': [
                        HD(ECU_R_ADDR_E) + SZ('10') + DT('0E 61 49 00 00 37 80') +
                        HD(ECU_R_ADDR_E) + SZ('21') + DT('00 FF 77 1D 00 08 A9') +
                        HD(ECU_R_ADDR_E) + SZ('22') + DT('62 00 00 00 00 00 00'),
                        HD(ECU_R_ADDR_E) + SZ('10') + DT('0E 61 49 00 14 34 80') +
                        HD(ECU_R_ADDR_E) + SZ('21') + DT('32 FF 77 1D 00 08 A9') +
                        HD(ECU_R_ADDR_E) + SZ('22') + DT('42 00 00 00 00 00 00'),
                        HD(ECU_R_ADDR_E) + SZ('10') + DT('0E 61 49 00 00 00 80') +
                        HD(ECU_R_ADDR_E) + SZ('21') + DT('00 FF 77 1D 00 08 A9') +
                        HD(ECU_R_ADDR_E) + SZ('22') + DT('0A 00 00 00 00 00 00')
                        ]
        },
        'CUSTOM_MCODE_7E0': {
            'Request': '^21C1' + ELM_FOOTER,
            'Descr': 'Model Code_7E0',
            'Equation': 'ABCDEFG',
            'Min': '0',
            'Max': '0',
            'Unit': '',
            'Header': ECU_ADDR_E,
            'Response': HD(ECU_R_ADDR_E) + SZ('10') + DT('15 61 C1 5A 57 45 31') +
                        HD(ECU_R_ADDR_E) + SZ('21') + DT('38 23 20 32 5A 52 46') +
                        HD(ECU_R_ADDR_E) + SZ('22') + DT('58 45 04 00 57 74 21') +
                        HD(ECU_R_ADDR_E) + SZ('23') + DT('00 00 00 00 00 00 00')
        },
        'CUSTOM_CLOAD_7E2': {
            'Request': '^2101' + ELM_FOOTER,
            'Descr': 'Calculated Load_7E2',
            'Equation': 'A * 20 / 51',
            'Min': '0',
            'Max': '100',
            'Unit': '%',
            'Header': ECU_ADDR_H,
            'Response': [
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('18 61 01 00 63 55 36') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('63 4B 00 00 00 05 BC') +
                        HD(ECU_R_ADDR_H) + SZ('22') + DT('2B 28 51 FF E2 FB FF') +
                        HD(ECU_R_ADDR_H) + SZ('23') + DT('FF 38 FD 9E 00 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('18 61 01 00 63 55 36') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('63 4B 00 00 00 05 A0') +
                        HD(ECU_R_ADDR_H) + SZ('22') + DT('2B 28 51 FF E2 FB FF') +
                        HD(ECU_R_ADDR_H) + SZ('23') + DT('FF 39 11 9E 00 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('18 61 01 00 63 55 36') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('63 4B 00 00 00 05 8C') +
                        HD(ECU_R_ADDR_H) + SZ('22') + DT('2B 28 51 FF E2 FB FF') +
                        HD(ECU_R_ADDR_H) + SZ('23') + DT('FF 39 11 9F 00 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('18 61 01 00 63 55 36') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('63 4B 00 00 00 05 92') +
                        HD(ECU_R_ADDR_H) + SZ('22') + DT('2B 28 51 FF E2 FB FF') +
                        HD(ECU_R_ADDR_H) + SZ('23') + DT('FF 38 FD 9F 00 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('18 61 01 00 63 55 36') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('63 4B 00 00 00 05 B5') +
                        HD(ECU_R_ADDR_H) + SZ('22') + DT('2B 28 51 FF E2 FB FF') +
                        HD(ECU_R_ADDR_H) + SZ('23') + DT('FF 39 11 9E 00 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('18 61 01 DA 26 55 36') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('63 4B 17 00 00 05 C3') +
                        HD(ECU_R_ADDR_H) + SZ('22') + DT('2D 3F 68 FF E2 FB FF') +
                        HD(ECU_R_ADDR_H) + SZ('23') + DT('FF 38 FD 9D 00 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('18 61 01 00 63 55 36') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('63 4B 00 00 00 05 99') +
                        HD(ECU_R_ADDR_H) + SZ('22') + DT('2B 28 51 FF E2 FB FF') +
                        HD(ECU_R_ADDR_H) + SZ('23') + DT('FF 39 11 9F 00 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('18 61 01 A1 37 4B 36') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('63 4B 14 80 00 05 CA') +
                        HD(ECU_R_ADDR_H) + SZ('22') + DT('32 28 51 FF E2 FB FF') +
                        HD(ECU_R_ADDR_H) + SZ('23') + DT('FF 39 11 9E 00 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('18 61 01 00 63 55 36') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('63 4B 00 00 00 05 AE') +
                        HD(ECU_R_ADDR_H) + SZ('22') + DT('2B 28 51 FF E2 FB FF') +
                        HD(ECU_R_ADDR_H) + SZ('23') + DT('FF 39 11 9E 00 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('18 61 01 00 63 55 36') +
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('63 4B 00 00 00 05 A7') +
                        HD(ECU_R_ADDR_H) + SZ('22') + DT('2B 28 51 FF E2 FB FF') +
                        HD(ECU_R_ADDR_H) + SZ('23') + DT('FF 39 11 9E 00 00 00')
                        ]
        },
        'CUSTOM_CCS_SPD': {
            'Request': '^2121' + ELM_FOOTER,
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
                        HD(ECU_R_ADDR_H) + SZ('07') + DT('61 21 00 00 81 00 00'), # Park + No brakes
                        HD(ECU_R_ADDR_H) + SZ('07') + DT('61 21 00 00 81 3F 00'), # Cruise on (transitory)
                        HD(ECU_R_ADDR_H) + SZ('07') + DT('61 21 00 00 7D 00 00'), # "R" shift (reverse)
                        HD(ECU_R_ADDR_H) + SZ('07') + DT('61 21 00 00 81 80 00'), # "D" shift (ahead)
                        HD(ECU_R_ADDR_H) + SZ('07') + DT('61 21 00 00 81 03 00'),
                        HD(ECU_R_ADDR_H) + SZ('07') + DT('61 21 00 00 81 00 E0'), # Park + Brakes
                        HD(ECU_R_ADDR_H) + SZ('07') + DT('61 21 00 00 81 00 60'), # Park + Light brakes
                        HD(ECU_R_ADDR_H) + SZ('07') + DT('61 21 00 00 81 00 04'), # Cruise control Cancel
                        HD(ECU_R_ADDR_H) + SZ('07') + DT('61 21 00 00 81 00 10'), # Cruise control Up
                        HD(ECU_R_ADDR_H) + SZ('07') + DT('61 21 00 00 81 00 08'), # Cruise control Down
                        HD(ECU_R_ADDR_H) + SZ('07') + DT('61 21 00 00 81 3C 00')  # Cruise on
                        ]
        },
        'CUSTOM_P': {
            'Request': '^2125' + ELM_FOOTER,
            'Descr': 'Shift Sensor SW - P',
            'Equation': '{A:7}',
            'Min': '0',
            'Max': '1',
            'Unit': 'Off/On',
            'Header': ECU_ADDR_H,
            'Response': [
                        HD(ECU_R_ADDR_H) + SZ('04') + DT('61 25 00 40'),
                        HD(ECU_R_ADDR_H) + SZ('04') + DT('61 25 02 00'),
                        HD(ECU_R_ADDR_H) + SZ('04') + DT('61 25 00 00')
                        ]
        },
        'CUSTOM_ODO': {
            'Request': '^2128' + ELM_FOOTER,
            'Descr': 'Total Distance Traveled',
            'Equation': 'A * 256 * 256 + B * 256 + C',
            'Min': '0',
            'Max': '16777215',
            'Unit': 'km',
            'Header': ECU_ADDR_H,
            'Response': HD(ECU_R_ADDR_H) + SZ('05') + DT('61 28 00 EA 5C')
        },
        'CUSTOM_SHIFT_J': {
            'Request': '^2141' + ELM_FOOTER,
            'Descr': 'Shift Joystick',
            'Header': ECU_ADDR_H,
            'Response': [
                        # UD: 6x (6D, 6E), 7x = centre; Cx = down; 1x = up. LR: 4A = right, B5 = left)
                        # LR1: 4a/49 (right), b3, b2, b5, b6 (left)
                        # First group:               UD UD LR LR1 [UD=up-down-centre, LR=left-right]
                        # Second group:     AA BB
                        # AA = 36, 38, 3A
                        # BB = (Park button pressed) 3A, 3B, 3C, 43, 75 (off), 88, 89, 90 (Park released)
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('08 61 41 6D 6D 4A 4A') + # default position (center, right)
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('38 89 00 00 00 00 00'),  # park button released
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('08 61 41 6D 6D 4A 4A') + # default position
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('38 3B 00 00 00 00 00'),  # park button pressed
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('08 61 41 6D 6D 4A 49') + # center, middle
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('38 89 00 00 00 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('08 61 41 6D 6D 4A B3') + # center, middle
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('38 89 00 00 00 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('08 61 41 6D 6D B5 B2') + # moved to "N" position (center, left)
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('38 89 00 00 00 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('08 61 41 BE BE 4A 4A') + # moved to "B" position (down, right)
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('38 89 00 00 00 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('08 61 41 C5 C6 B5 B2') + # moved to "D" position (down, left)
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('38 89 00 00 00 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('08 61 41 1A 1B B5 B2') + # moved to "R" position (up, left)
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('38 89 00 00 00 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('08 61 41 6D 6D 4B 4A') + # default (center, right)
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('36 89 00 00 00 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('08 61 41 C4 C4 4A 49') + # moved to "B" position (down, right)
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('38 89 00 00 00 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('08 61 41 1B 1B B5 B2') + # moved to "R" position (up, left)
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('38 89 00 00 00 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('08 61 41 C4 C4 B5 B2') + # moved to "D" position (down, left)
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('38 89 00 00 00 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('08 61 41 70 70 B5 B2') + # moved to "N" position (center, left)
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('38 89 00 00 00 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('08 61 41 6E 6E B5 B2') + # moved to "N" position (center, left)
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('38 89 00 00 00 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('10') + DT('08 61 41 6E 6E 4A 4A') + # default (center, right)
                        HD(ECU_R_ADDR_H) + SZ('21') + DT('38 89 00 00 00 00 00')
                        ]
        },
        'CUSTOM_SMRP': {
            'Request': '^2144' + ELM_FOOTER,
            'Descr': 'SMRP Status',
            'Equation': '{A:7}',
            'Min': '0',
            'Max': '1',
            'Unit': 'Off/On',
            'Header': ECU_ADDR_H,
            'Response': HD(ECU_R_ADDR_H) + SZ('05') + DT('61 44 60 00 60')
        },
        'CUSTOM_MG2_TORQ': {
            'Request': '^2168' + ELM_FOOTER,
            'Descr': 'MG2 torque',
            'Equation': '(A * 256 + B) / 8 - 4096',
            'Min': '-4096',
            'Max': '4095.875',
            'Unit': 'Nm',
            'Header': ECU_ADDR_H,
            'Response': [
                        HD(ECU_R_ADDR_H) + SZ('07') + DT('61 68 80 00 80 00 00'),
                        HD(ECU_R_ADDR_H) + SZ('07') + DT('61 68 7F 9B 7F AA 00'),
                        HD(ECU_R_ADDR_H) + SZ('07') + DT('61 68 80 00 7F FC 00'),
                        HD(ECU_R_ADDR_H) + SZ('07') + DT('61 68 80 2F 80 34 00')
                        ]
        },
        'CUSTOM_KPH_7C0': {
            'Request': '^2121' + ELM_FOOTER,
            'Descr': 'Vehicle Speed Meter_7C0',
            'Equation': 'A',
            'Min': '0',
            'Max': '199',
            'Unit': 'km/h',
            'Header': ECU_ADDR_I,
            'Response': HD(ECU_R_ADDR_I) + SZ('03') + DT('61 21 00')
        },
        'CUSTOM_COOLANT_7C0': {
            'Request': '^2123' + ELM_FOOTER,
            'Descr': 'Coolant Temperature_7C0',
            'Equation': 'A / 2',
            'Min': '0',
            'Max': '127.5',
            'Unit': 'C',
            'Header': ECU_ADDR_I,
            'Response': HD(ECU_R_ADDR_I) + SZ('03') + DT('61 23 47')
        },
        'CUSTOM_H_S_I': {
            'Request': '^212B' + ELM_FOOTER,
            'Descr': 'HV System Indicator',
            'Equation': '{A:0} * 256 + B - {A:1} * 512',
            'Min': '-512',
            'Max': '511',
            'Unit': '%',
            'Header': ECU_ADDR_I,
            'Response': HD(ECU_R_ADDR_I) + SZ('04') + DT('61 2B 02 00')
        },
        'CUSTOM_KEYBUZ': {
            'Request': '^21A1' + ELM_FOOTER,
            'Descr': 'Key Remind Sound (buzzer/Normal, Fast, Slow)',
            'Equation': 'A',
            'Min': '0',
            'Max': '255',
            'Unit': '',
            'Header': ECU_ADDR_I,
            'Response': HD(ECU_R_ADDR_I) + SZ('03') + DT('61 A1 18')
        },
        'CUSTOM_A/M_STP_D': {
            'Request': '^2141' + ELM_FOOTER,
            'Descr': 'Air Mix Servo Targ Pulse (D)',
            'Equation': 'A + 128',
            'Min': '128',
            'Max': '383',
            'Unit': '',
            'Header': ECU_ADDR_P,
            'Response': HD(ECU_R_ADDR_P) + SZ('06') + DT('61 41 1A 1A 00 00')
        },
        'CUSTOM_STROKE': {
            'Request': '^2104' + ELM_FOOTER,
            'Descr': 'Stroke Sensor',
            'Equation': 'A / 51',
            'Min': '0',
            'Max': '5',
            'Unit': 'V',
            'Header': ECU_ADDR_S,
            'Response': [
                        HD(ECU_R_ADDR_S) + SZ('06') + DT('61 04 29 D6 BF 19'),
                        HD(ECU_R_ADDR_S) + SZ('06') + DT('61 04 29 D6 B8 19'),
                        HD(ECU_R_ADDR_S) + SZ('06') + DT('61 04 29 D6 BE 19'),
                        HD(ECU_R_ADDR_S) + SZ('06') + DT('61 04 3F BF B4 41'),
                        HD(ECU_R_ADDR_S) + SZ('06') + DT('61 04 29 D6 B9 19')
                        ]
        },
        'CUSTOM_DECELSEN': {
            'Request': '^2105' + ELM_FOOTER,
            'Descr': 'Deceleration Sensor',
            'Equation': 'A * 36.912 / 255 - 18.525',
            'Min': '-18.525',
            'Max': '18.387',
            'Unit': 'm/s2',
            'Header': ECU_ADDR_S,
            'Response': [
                        HD(ECU_R_ADDR_S) + SZ('05') + DT('61 05 7F 80 1F'),
                        HD(ECU_R_ADDR_S) + SZ('05') + DT('61 05 7F 80 00'),
                        HD(ECU_R_ADDR_S) + SZ('05') + DT('61 05 7E 80 00')
                        ]
        },
        'CUSTOM_BRKFLUID': {
            'Request': '^211D' + ELM_FOOTER,
            'Descr': 'Reservoir Warning SW',
            'Equation': '{A:6}',
            'Min': '0',
            'Max': '1',
            'Unit': 'Off/On',
            'Header': ECU_ADDR_S,
            'Response': [
                        HD(ECU_R_ADDR_S) + SZ('03') + DT('61 1D 00'),
                        HD(ECU_R_ADDR_S) + SZ('03') + DT('61 1D 20')
                        ]
        },
        'CUSTOM_STPSW': {
            'Request': '^211F' + ELM_FOOTER,
            'Descr': 'Stop Light SW',
            'Equation': '{A:7}',
            'Min': '0',
            'Max': '1',
            'Unit': 'Off/On',
            'Header': ECU_ADDR_S,
            'Response': [
                        HD(ECU_R_ADDR_S) + SZ('03') + DT('61 1F 00'),
                        HD(ECU_R_ADDR_S) + SZ('03') + DT('61 1F 80')
                        ]
        },
        'CUSTOM_KPH_7B0': {
            'Request': '^2121' + ELM_FOOTER,
            'Descr': 'Vehicle Speed_7B0',
            'Equation': 'A * 326.4 / 255',
            'Min': '0',
            'Max': '200',
            'Unit': 'km/h',
            'Header': ECU_ADDR_S,
            'Response': HD(ECU_R_ADDR_S) + SZ('03') + DT('61 21 00')
        },
        'CUSTOM_STPRELAY': {
            'Request': '^213C' + ELM_FOOTER,
            'Descr': 'Stop Light Relay Output',
            'Equation': '{A:7}',
            'Min': '0',
            'Max': '1',
            'Unit': 'Off/On',
            'Header': ECU_ADDR_S,
            'Response': HD(ECU_R_ADDR_S) + SZ('03') + DT('61 3C 00')
        },
        'CUSTOM_ABS': {
            'Request': '^213D' + ELM_FOOTER,
            'Descr': 'ABS Warning Light',
            'Equation': '{A:7}',
            'Min': '0',
            'Max': '1',
            'Unit': 'Off/On',
            'Header': ECU_ADDR_S,
            'Response': HD(ECU_R_ADDR_S) + SZ('04') + DT('61 3D 00 00')
        },
        'CUSTOM_FR_WA': {
            'Request': '^2142' + ELM_FOOTER,
            'Descr': 'FR Wheel Acceleration',
            'Equation': '( A - {A:7} * 256 ) * 199.27 / 127',
            'Min': '-10',
            'Max': '10',
            'Unit': 'm/s2',
            'Header': ECU_ADDR_S,
            'Response': HD(ECU_R_ADDR_S) + SZ('06') + DT('61 42 00 00 00 00')
        },
        'CUSTOM_0DECEL': {
            'Request': '^2146' + ELM_FOOTER,
            'Descr': 'Zero Point of Decele',
            'Equation': 'A * 50.02 / 255 - 25.11',
            'Min': '-25.11',
            'Max': '24.91',
            'Unit': 'm/s2',
            'Header': ECU_ADDR_S,
            'Response': HD(ECU_R_ADDR_S) + SZ('10') + DT('09 61 46 00 00 80 80') +
                        HD(ECU_R_ADDR_S) + SZ('21') + DT('00 01 14 00 00 00 00')
        },
        'CUSTOM_REGENREQ': {
            'Request': '^2148' + ELM_FOOTER,
            'Descr': 'FR Regenerative Request',
            'Equation': '(A * 256 + B) * 16',
            'Min': '0',
            'Max': '400',
            'Unit': 'Nm',
            'Header': ECU_ADDR_S,
            'Response': HD(ECU_R_ADDR_S) + SZ('06') + DT('61 48 00 00 00 00')
        },
        'CUSTOM_TRAC': {
            'Request': '^215A' + ELM_FOOTER,
            'Descr': 'TRC(TRAC) Ctrl Status',
            'Equation': '{A:7}',
            'Min': '0',
            'Max': '1',
            'Unit': 'Off/On',
            'Header': ECU_ADDR_S,
            'Response': [
                        HD(ECU_R_ADDR_S) + SZ('04') + DT('61 5A 00 00'),
                        HD(ECU_R_ADDR_S) + SZ('04') + DT('61 5A 18 00'),
                        HD(ECU_R_ADDR_S) + SZ('04') + DT('61 5A 10 00')
                        ]
        },
        'CUSTOM_FR_ABS': {
            'Request': '^215F' + ELM_FOOTER,
            'Descr': 'FR Wheel ABS Ctrl Status',
            'Equation': '{A:7}',
            'Min': '0',
            'Max': '1',
            'Unit': 'Off/On',
            'Header': ECU_ADDR_S,
            'Response': HD(ECU_R_ADDR_S) + SZ('04') + DT('61 5F 00 00')
        },
        'CUSTOM_0YAW2': {
            'Request': '^21A1' + ELM_FOOTER,
            'Descr': 'Zero Point of Yaw Rate2',
            'Equation': 'A -128',
            'Min': '-128',
            'Max': '127',
            'Unit': 'degrees/s',
            'Header': ECU_ADDR_S,
            'Response': HD(ECU_R_ADDR_S) + SZ('03') + DT('61 A1 80')
        },
    },
    'mt05': {
        'RPM': {
            'Request': '^010C' + ELM_FOOTER,
            'Descr': 'Engine RPM',
            'ResponseFooter': \
                lambda self, cmd, pid, uc_val: \
                    PA(self.sequence(
                           pid, base=2400, max=200, factor=80, n_bytes=2))
        },
        'SPEED': {
            'Request': '^010D' + ELM_FOOTER,
            'Descr': 'Vehicle Speed',
            'ResponseFooter': \
                lambda self, cmd, pid, uc_val: \
                    PA(self.sequence(
                            pid, base=0, max=30, factor=4, n_bytes=1))
        },
        'O2_SENSORS': {
            'Request': '^0113' + ELM_FOOTER,
            'Descr': 'O2 Sensors Present',
            'Response': PA('01')
        },
        'OBD_COMPLIANCE': { # See https://en.wikipedia.org/wiki/OBD-II_PIDs#Service_01_PID_1C
            'Request': '^011C' + ELM_FOOTER,
            'Descr': 'OBD Compliance',
            'Response': PA('03') # OBD + OBD 2
        },
        'CLEAR_DIAG_TC': {
            'Request': '^04' + ELM_FOOTER,
            'Descr': 'Clear Diagnostic Trouble Codes, malfunction indicator and stored values',
            'Response': PA('')
        },
        'CALIBRATION_ID': {
            'Request': '^0904' + ELM_FOOTER,
            'Descr': 'Calibration ID',
            'Response': PA('42 4A 32 35 30 31 38 46')
        },
        'CVN': {
            'Request': '^0906' + ELM_FOOTER,
            'Descr': 'Calibration Verification Numbers',
            'Response': PA('00 00 F2 29')
        },
        'CLEAR_DTC': {
            'Request': '^14' + ELM_DATA_FOOTER,
            'Descr': 'Clear DTC',
            'Response': PA('')
        },
        "MONITOR": {
            'Request': '^2101' + ELM_FOOTER, # 21 (Read Data By Local Id) and 01 (Subfunction)
            'Descr': 'Monitor',
            'Response': [ # Returns a packet of 0x64 = 100 bytes: "Mode 1 Message".
                PA(
                '80 00 34 50 34 50 80 00 80 00 08 43 08 43 00 00 00 00 00 00 '
                '00 00 00 21 00 00 00 00 00 00 72 DF 6E 76 78 14 48 00 00 00 '
                '00 00 00 00 00 00 00 04 2E 04 2E 00 00 00 5E 80 00 83 60 00 '
                '00 00 00 00 00 00 64 C8 07 E0 00 00 00 00 08 82 63 2F 55 00 '
                '55 08 45 BA 19 74 FD B1 00 00 00 00 00 00 1B 40 01 AC 00 00'),
                PA(
                '7B F2 66 A9 66 A9 80 00 80 00 18 02 18 02 00 00 00 00 00 00 '
                '00 00 00 21 80 00 00 AF 01 18 45 AB 6E 76 1A 0E AD 1A 90 01 '
                '94 00 00 00 00 00 CE 07 80 07 80 00 00 00 56 00 87 9F 6F E5 '
                '02 04 00 00 00 00 64 6A 2A 20 00 00 17 CB 0E 9F 76 76 2D 44 '
                '2D 62 2D 57 2A 01 D7 8C 1C 24 00 00 00 00 1B 40 00 A9 00 00'),
                PA(
                '7B F8 66 A9 66 A9 80 00 80 00 17 FD 17 FD 00 00 00 00 00 00 '
                '00 00 00 21 80 00 00 AE 01 15 45 59 6E 76 1A 0E AD 1A 90 01 '
                '9A 00 00 00 00 00 CE 07 80 07 80 00 00 00 56 00 87 9F 6F E5 '
                '02 04 00 00 00 00 64 6A 2A 20 00 00 17 D5 0E 9F 75 A8 2D 45 '
                '2D 63 2D 59 2A 01 D7 8C 1C 2A 00 00 00 00 1B 40 00 A9 00 00'),
            ]
        },
        'ECU_IVN_HW': {
            'Request': '^2103' + ELM_FOOTER,
            'Descr': 'ECU internal version numbers - Hardware Part Number',
            'Response': PA('01 B3 D0 54'),
        },
        'ECU_IVN_SW': {
            'Request': '^2104' + ELM_FOOTER,
            'Descr': 'ECU internal version numbers - Software Part Number',
            'Response': PA('01 AF FD D4'),
        },
        'IGNITION_COUNTER': {
            'Request': '^21FF' + ELM_FOOTER,
            'Descr': 'Ignition counter',
            'Response': PA('8E 01 00 00'),
        },
        'UDS_STDS_DEF': { # Default/Std Diag/OBD II Mode
            'Request': '^1081' + ELM_FOOTER,
            'Descr': 'UDS Start Diagnostic Session - Default mode',
            'Response': PA('')
        },
        'UDS_STDS_FLASH': {
            'Request': '^1085' + ELM_FOOTER, # 85 = Flash Programming Session
            'Descr': 'UDS Start Diagnostic Session - ECU Prog Mode',
            'Response': PA('')
        },
        'UDS_SA_REQ_SEED': {
            'Request': '^2701' + ELM_FOOTER,
            'Descr': 'UDS SecurityAccess - requestSeed',
            'Response': PA('12 34') # response SID
        },
        'UDS_SA_SEND_KEY': {
            'Request': '^2702' + ELM_DATA_FOOTER,
            'Descr': 'UDS SecurityAccess - Send Key to ECU',
            'Exec': 'self.shared.auth_successful = cmd[4:] == "8474"', # Key
            'Info': '"auth_successful: %s.", self.shared.auth_successful',
            'ResponseFooter': lambda self, cmd, pid, uc_val: (
                PA('34') if self.shared.auth_successful else NA('35')
            )
        },
        'UDS_RMBA': {
            'Request': '^23' + ELM_DATA_FOOTER,
            'Descr': 'UDS Read memory by address',
            'Task': 'task_mt05_read_mem_addr'
        },
        'UDS_START_ROUTINE_ADDR': {
            'Request': '^38' + ELM_DATA_FOOTER,
            'Descr': 'UDS Start Routine by Address',
            'Exec': 'self.shared.executed_routine = cmd[2:] or None',
            'ResponseFooter': lambda self, cmd, pid, uc_val: PA(cmd[2:]) # return the address after the SID
        },
        'UDS_WRITE_MEM_ADDR': {
            'Request': '^3D' + ELM_DATA_FOOTER,
            'Descr': 'UDS Write memory by address',
            'Task': 'task_mt05_write_mem_addr'
        },
        'UDS_START_ROUTINE': {
            'Request': '^3101' + ELM_DATA_FOOTER, # UDS Routine Control (31): Start (01)
            'Descr': 'UDS Routine Control - start',
            'Task': 'task_mt05_start_routine'
        },
        'UDS_STOP_ROUTINE': {
            'Request': '^3102' + ELM_FOOTER, # UDS Routine Control (31): Stop (02)
            'Descr': 'UDS Routine Control - stop',
            'Task': 'task_mt05_stop_routine'
        },
    }
}
