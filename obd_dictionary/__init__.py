#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
try:
    if sys.hexversion < 0x3050000:
        raise ImportError("Python version must be >= 3.5")
    import time
    import obd
    import re
    import csv
    from obd import OBDCommand, Unit
    from obd.protocols import ECU
    from obd.utils import bytes_to_int
    import argparse
except ImportError as detail:
    print("ObdMessage Dictionary Generator error:\n " + str(detail))
    sys.exit(1)

ecu = {
    "7B0": 'ECU_ADDR_S',   # Skid Control address ECU
    "7B8": 'ECU_R_ADDR_S', # Responses sent by 7B0 Skid Control ECU 7B0/7B8
    "7E2": 'ECU_ADDR_H',   # HVECU address (Hybrid contol module)
    "7EA": 'ECU_R_ADDR_H', # Resp. sent by HVECU (Hybrid Ctrl module) 7E2/7EA
    "7E0": 'ECU_ADDR_E',   # Engine ECU address
    "7E8": 'ECU_R_ADDR_E', # Responses sent by ECM (engine Ctrl module) 7E0/7E8
    "7E1": 'ECU_ADDR_T',   # Transmission ECU address
    "7E9": 'ECU_R_ADDR_T', # Resp.sent by TCM (transmission Ctrl module)7E1/7E9
    "7C0": 'ECU_ADDR_I',   # ICE ECU address
    "7C8": 'ECU_R_ADDR_I', # Responses sent by ICE ECU address 7C0/7C8
    "7E3": 'ECU_ADDR_B',   # Traction Battery ECU address
    "7EB": 'ECU_R_ADDR_B', # Responses sent by Traction Battery ECU - 7E3/7EB
    "7C4": 'ECU_ADDR_P',   # Air Conditioning
    "7CC": 'ECU_R_ADDR_P'  # Responses sent by Air Conditioning ECU - 7C4/7CC
}

blacklisted_pids = (
    'CLEAR_DTC', # Clear DTCs and Freeze data
    'ELM_DPN', # 'Current protocol by number' ('AT DPN')
    'CUSTOM_SFS5', # "Set Battery Cooling Fan Speed 5|A|0|0|No reply req'd" ('30810605')
    'CUSTOM_SFS2', # "Set Battery Cooling Fan Speed 2|A|0|0|No reply req'd" ('30810602')
    'CUSTOM_SFS3', # "Set Battery Cooling Fan Speed 3|A|0|0|No reply req'd" ('30810603')
    'CUSTOM_SFS0', # "Set Battery Cooling Fan Speed 0 (Off)|A|0|0|No reply req'd" ('30810600')
    'CUSTOM_TRAC_DIS', # "Disable Traction Control|A|0|0|No reply req'd" ('30610040')
    'CUSTOM_SFS4', # "Set Battery Cooling Fan Speed 4|A|0|0|No reply req'd" ('30810604')
    'CUSTOM_SFS6', # "Set Battery Cooling Fan Speed 6 (max.)|A|0|0|No reply req'd" ('30810606')
    'CUSTOM_SFS1', # "Set Battery Cooling Fan Speed 1|A|0|0|No reply req'd" ('30810601')
    'CUSTOM_SBB_ENA_P', # "Seat Belt Beep Enable Passenger Only|A|0|0|No reply req'd" ('3BA740')
    'CUSTOM_RB_ENA', # "Reverse Beep Enable|A|0|0|No reply req'd" ('3BAC00')
    'CUSTOM_SBB_DIS_R', # "Seat Belt Beep Disable Rear Only|A|0|0|No reply req'd" ('3BA7C0')
    'CUSTOM_SBB_DIS_D', # "Seat Belt Beep Disable Driver Only|A|0|0|No reply req'd" ('3BA760')
    'CUSTOM_SBB_DIS_A', # "Seat Belt Beep Disable All|A|0|0|No reply req'd" ('3BA700')
    'CUSTOM_SBB_DIS_P', # "Seat Belt Beep Disable Passenger Only|A|0|0|No reply req'd" ('3BA7A0')
    'CUSTOM_SBB_ENA_D', # "Seat Belt Beep Enable Driver Only|A|0|0|No reply req'd" ('3BA780')
    'CUSTOM_SBB_ENA_R', # "Seat Belt Beep Enable Rear Only|A|0|0|No reply req'd" ('3BA720')
    'CUSTOM_SBB_ENA_A', # "Seat Belt Beep Enable All|A|0|0|No reply req'd" ('3BA7E0')
    'CUSTOM_RB_DIS', # "Reverse Beep Disable|A|0|0|No reply req'd" ('3BAC40')
)


def add_at(data):
    stack = 0
    startIndex = 0
    stackbreak = 0
    for i, c in enumerate(data):
        if c == '{':
            if stack == 1 and re.search("'AT'[ \t]*:", data[startIndex:i]):
                startIndex = i + 1
                stackbreak = stack
            stack += 1
        elif c == '}':
            stack -= 1
            if stack == stackbreak:
                break

    if stack == 1 and i > startIndex + 1:
        try:
            print('        ' + data[startIndex:i].strip())
        except:
            obd.logger.error("Malformed 'AT' scenario in input file")
    else:
        obd.logger.error("'AT' scenario not found in input file")


def obd_dictionary():

    SEP = '|'

    # Option handling
    parser = argparse.ArgumentParser(
        epilog='ObdMessage Dictionary Generator for "ELM327-emulator".')
    parser.add_argument(
        "-i",
        dest="elm327",
        required=True,
        help="serial port connected to the ELM327 adapter (required argument)",
        metavar="DEVICE")
    parser.add_argument(
        '-c',
        "--csv",
        dest='csv_custom_pids',
        type=argparse.FileType('r'),
        help="input csv file including custom PIDs "
             "(Torque CSV Format: https://torque-bhp.com/wiki/PIDs) "
             "'-' reads data from the standard input",
        default=0,
        nargs=1,
        metavar='CSV_FILE')
    parser.add_argument(
        '-o',
        "--out",
        dest="dictionary_out",
        type=argparse.FileType('w'),
        help="output dictionary file generated after processing input "
             "data (replaced if existing). Default is to print data "
             "to the standard output",
        default=0,
        nargs=1,
        metavar='FILE')
    parser.add_argument(
        '-v',
        "--verbosity",
        dest='verbosity',
        action='store_true',
        help="print process information")
    parser.add_argument(
        '-V',
        "--verbosity_debug",
        dest='debug',
        action='store_true',
        help="print debug information")
    parser.add_argument(
        '-p',
        '--probes',
        dest='probes',
        type=int,
        help='number of probes (each probe includes querying '
             'all PIDs to the OBDII adapter)',
        default=1)
    parser.add_argument(
        '-d',
        '--delay',
        dest='delay',
        type=float,
        help='delay (in seconds) between probes',
        default=0)
    parser.add_argument(
        '-D',
        '--delay_commands',
        dest='delay_commands',
        type=float,
        help='delay (in seconds) between each PID query within all probes',
        default=0)
    parser.add_argument(
        '-n',
        '--name',
        dest='car_name',
        action="store",
        help='name of the car (dictionary label; default is "car")',
        default="car")
    parser.add_argument(
        '-b',
        '--blacklist',
        dest='with_blacklist',
        action="store_true",
        default=False,
        help='include blacklisted PIDs within probes')
    parser.add_argument(
        '-x',
        '--noautopid',
        dest='noautopid',
        action="store_true",
        default=False,
        help='do not autopopulate the pid list with the set of built-in'
             ' commands supported by the vehicle; only use csv file.')
    parser.add_argument(
        '-t',
        '--at',
        dest='at',
        default=0,
        type=argparse.FileType('r'),
        nargs="?",
        help='include AT Commands within probes. '
             'If a dictionary file is given, also extract AT Commnands'
             ' from the input file and add them to the output',
        metavar='FILE')
    parser.add_argument(
        '-m',
        '--missing',
        dest='print_missing_resp',
        action="store_true",
        default=False,
        help='add in-line comment to dictionary '
             'for PIDs with missing response')
    args = parser.parse_args()

    # Debug
    if args.verbosity:
        obd.logger.setLevel(obd.logging.INFO)
    if args.debug:
        obd.logger.setLevel(obd.logging.DEBUG)

    # Connect to OBDII and fill 'connection.supported_commands'
    obd.logger.info("Connecting to" + args.elm327)
    connection = obd.OBD(args.elm327, fast=False)
    if not connection.is_connected():
        obd.logger.error("Connection to " + repr(args.elm327) + " failed")
        return

    if args.noautopid:
        for cmd in connection.supported_commands.copy():
            connection.supported_commands.remove(cmd)

    # Enrich the dictionary with some predefined commands
    if args.at != 0:
        connection.supported_commands.add(
            OBDCommand("ELM_IGNITION", "IgnMon input level", b"AT IGN", 0,
                       lambda messages: "\n".join([m.raw() for m in messages]),
                       ECU.ALL, True))
        connection.supported_commands.add(
            OBDCommand("ELM_DESCR", "Device description", b"AT@1", 0,
                       lambda messages: "\n".join([m.raw() for m in messages]),
                       ECU.ALL, True))
        connection.supported_commands.add(
            OBDCommand("ELM_ID", "Device identifier", b"AT@2", 0,
                       lambda messages: "\n".join([m.raw() for m in messages]),
                       ECU.ALL, True))
        connection.supported_commands.add(
            OBDCommand("ELM_DP", "Current protocol", b"AT DP", 0,
                       lambda messages: "\n".join([m.raw() for m in messages]),
                       ECU.ALL, True))
        connection.supported_commands.add(
            OBDCommand("ELM_DPN", "Current protocol by number", b"AT DPN", 0,
                       lambda messages: "\n".join([m.raw() for m in messages]),
                       ECU.ALL, True))
    else:
        for cmd in connection.supported_commands.copy():
            if cmd.name.startswith('ELM_'):
                connection.supported_commands.remove(cmd)

    # Read the optional csv file of custom commands and enrich the dictionary
    if args.csv_custom_pids:
        obd.logger.info("Reading CSV file...")
        reader = csv.reader(args.csv_custom_pids[0])
        custom_pids = list(reader)
        for i in custom_pids:
            if i[0] == 'Name' or len(i) != 8 or not i[7] in ecu:
                if i[0] != 'Name':
                    if len(i) == 8 and not i[7] in ecu:
                        obd.logger.error("Unknown ECU " + repr(i[7]) +
                                         " in CSV line " + repr(i))
                    else:
                        obd.logger.error("Invalid CSV data: " + repr(i))
                continue
            Pid = 'CUSTOM_' + i[1].upper().replace(' ', '_')
            Descr = i[0] + SEP + i[3] + SEP + i[4] + SEP + i[5] + SEP + i[6]
            Request = i[2].strip()
            Header = i[7]
            connection.supported_commands.add(
                OBDCommand(
                    Pid,
                    Descr,
                    Request.encode(),
                    0,
                    lambda messages: "\n".join([m.raw() for m in messages]),
                    ECU.ALL,
                    True,
                    header=Header.encode()))
        obd.logger.info("CSV file processing complete")

    # Query all commands in the dictionary and return responses to OBDData
    OBDData = [dict() for x in range(args.probes)]
    for i in range(args.probes):
        obd.logger.info("Start probe number " + str(i))
        for cmd in connection.supported_commands:
            cmd.ecu = ECU.ALL
            if not cmd.name in blacklisted_pids or args.with_blacklist:
                OBDData[i][cmd] = connection.query(cmd)
                time.sleep(args.delay_commands)
        time.sleep(args.delay)
    obd.logger.info("End of probing process. Producing dictionary...")

    # Sort the list of supported commands
    l = list(connection.supported_commands)
    l.sort(
        key = lambda cmd: ( '0' if cmd.name.startswith('ELM_') \
                       else '2' if cmd.name.startswith('CUSTOM_') \
                       else '1' ) +\
            SEP + ( ecu[cmd.header.decode()] \
            if cmd.header.decode() in ecu else cmd.header.decode() ) + \
            SEP + cmd.command.decode())

    # Redirect stdout
    if args.dictionary_out:
        sys.stdout = args.dictionary_out[0]

    # Print header information
    print("\n".join([ecu[k] + ' = "' + k + '"' for k in ecu]))
    print('ELM_R_OK = "OK\\r"\nELM_MAX_RESP = "[0123456]?$"\n')
    print("ObdMessage = {")
    print("    '" + args.car_name + "': {")

    # Loop all sorted commands
    cmd_type = 0
    for cmd in l:
        if cmd.name.startswith('CUSTOM_') and cmd_type != 3:
            print('    # Custom OBD Commands')
            cmd_type = 3
        elif cmd.name.startswith('ELM_') and cmd_type != 2:
            print('    # AT Commands')
            cmd_type = 2
            if args.at:
                add_at(args.at.read())
        elif not cmd.name.startswith('CUSTOM_') and not cmd.name.startswith(
                'ELM_') and cmd_type != 1:
            print('    # OBD Commands')
            cmd_type = 1

        # for each command, generate the lists of responses and values
        list_resp = []
        list_vals = {} # dict of available values for each list_resp
        for response in [d[cmd] for d in OBDData if cmd in d]:
            if not response.messages:
                obd.logger.info('No data for PID %s (%s)' % (
                        repr(cmd.name), repr(cmd.command)))
                continue
            p_resp = ''
            for i in response.messages:
                for r in i.raw().splitlines():
                    h = r[:3]  # header
                    if len(r) > 4 and h in ecu and re.match('^[0-9a-fA-F\r\n]*$', r):
                        s = r[3:]  # bytes
                        p = " ".join(s[i:i + 2]
                                     for i in range(0, len(s), 2))  # spaced bytes
                        p_resp += (" +\n                        " if p_resp
                                   else '') + ecu[h] + " + ' " + p + " \\r'"
                    else: # word (not string of bytes)
                        p_resp += (" +\n                        "
                                   if p_resp else '') + "'" + r\
                            .replace('"', "\\\\'")\
                            .replace("'", "\\\'") + " \\r'"
            if p_resp:
                list_resp.append(p_resp)
                if response.value and hasattr(response.value, 'magnitude'):
                    list_vals[p_resp]='{!s}'.format(response.value)\
                        .replace('"', "\\'")\
                        .replace("'", "\\'")

        # discard PIDs with missing response
        if not list_resp:
            if not args.with_blacklist and cmd.name in blacklisted_pids:
                obd.logger.debug('Blacklisted PID %s (%s)' % (
                        repr(cmd.name), repr(cmd.command)))
            else:
                obd.logger.error('No response data for PID %s, %s (%s)' % (
                        repr(cmd.name), repr(cmd.desc), repr(cmd.command)))
                if args.print_missing_resp:
                    print('        # No response data for PID %s, %s (%s)' % (
                        repr(cmd.name), repr(cmd.desc), repr(cmd.command)))
            continue

        # discard duplicates
        list_resp = list(set(list_resp))

        # produce the final printable strings of responses and values
        if len(list_resp) > 1:
            f_resp = ('[\n                        ' +
                      ',\n                        '.join(list_resp) +
                      '\n                        ]')
        else:
            f_resp = next(iter(list_resp))
        f_val = "\n            # ".join(
            [list_vals[x] for x in list_resp if x in list_vals])

        # print all data
        print("        " + repr(cmd.name) + ": {")
        print("            'Request': '^" + cmd.command.decode() +
              "' + ELM_MAX_RESP,")
        descr_list = cmd.desc.split(SEP)
        print("            'Descr': '" + descr_list[0] + "',")
        if len(descr_list) >= 5:
            print("            'Equation': '" + descr_list[1] + "',")
            print("            'Min': '" + descr_list[2] + "',")
            print("            'Max': '" + descr_list[3] + "',")
            print("            'Unit': '" + descr_list[4] + "',")
        print("            'Header': " + ecu[cmd.header.decode()] + ","\
            if cmd.header.decode() in ecu else cmd.header.decode() + ",")
        print("            'Response': " + f_resp)
        if f_val:
            print("            # " + f_val)
        print("        },")
    print("    },")
    print("}")
    obd.logger.info("Dictionary production complete.")


'''
Sample:
            'ENGINE_LOAD': {
                'Request': '^0104' + ELM_MAX_RESP,
                'Descr': 'Calculated Engine Load',
                'Header': ECU_ADDR_E,
                'Response': ECU_R_ADDR_E + ' 03 41 04 3F \r'
            },
'''

def main():
    try:
        obd_dictionary()
    except KeyboardInterrupt:
        sys.exit("\n\n\nInterrupted.\n")
    except Exception as e:
        sys.exit("\n   Error. " + str(e) + "\n")

if __name__ == '__main__':
    main()
