#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###########################################################################
# ELM327-emulator
# ELM327 Emulator for testing software interfacing OBDII via ELM327 adapter
# https://github.com/Ircama/ELM327-emulator
# (C) Ircama 2021 - CC-BY-NC-SA-4.0
###########################################################################

import sys
import traceback

try:
    if sys.hexversion < 0x3060000:
        raise ImportError("Python version must be >= 3.6")
    import threading
    from .elm import Elm
    import time
    from cmd import Cmd
    import rlcompleter
    import glob
    import logging
    import re
    from functools import reduce
    import os
    import os.path
    import argparse
    import datetime
    try:
        import readline
    except ImportError:
        readline = None
    if os.name == 'nt':
        try:
            import pyreadline3
        except ImportError:
            pass
    else:
        import daemon
        import daemon.pidfile
    import signal
    from lockfile.pidlockfile import PIDLockFile
    from lockfile import AlreadyLocked, NotLocked, LockFailed
    from .__version__ import __version__
    from .obd_message import ObdMessage, ECU_ADDR_E, ELM_R_OK
    from random import randint
    import xml.etree.ElementTree as ET
    import pprint
except ImportError as detail:
    print("ELM327 OBD-II adapter emulator error:\n " + str(detail))
    sys.exit(1)

DAEMON_PIDFILE_DIR_ROOT = '/var/run/'
DAEMON_PIDFILE_DIR_NON_ROOT = '/tmp/'
DAEMON_PIDFILE = 'ELM327_emulator.pid'
DAEMON_UMASK = 0o002
DAEMON_DIR = '/tmp'


class Edit:
    """
    Allow editing static answers in the `ObdMessage` dictionary on-the-fly.

    It extracts the answer from a PID, stores it into the emulator.answer
    dictionary and performs the editing in its data part.

    If the command is called with just the PID argument, it resets the
    emulator.answer dictionary for the referred PID.

    Usage in a Context Manager is supported: on the termination of the
    Context Manager, the emulator.answer dictionary for the specified PID
    is reset to its original state.
    """
    def __init__(self, emulator, pid):
        """
        When called with the Context Manager, pass the emulator instance
        and the pid to edit
        :param emulator: instance of the emulator
        :param pid: pid to edit
        """
        self.pid = pid
        self.emulator = emulator
        self.original_entry = None

    def __enter__(self):
        """
        If used with the Context Manager, do only temporary update of the
        self.emulator.answer dictionary.
        """
        if self.pid in self.emulator.answer:
            self.original_entry = self.emulator.answer[self.pid]
        return self

    def answer(self, position, replace_bytes, pid=None):
        """
        Edit the answer related to a pid. Self can be none if pid is given.
        :param position: start position to edit bytes;
               None to remove a previous editing.
        :param replace_bytes: replaced bytes (can be a sequence)
        :param pid: pid to edit (replaces the one set with the Context Mgr)
        :return: True if editing succeeded
        """
        pid_to_edit = None
        if self and hasattr(self, 'pid'):
            pid_to_edit = self.pid
        if pid:
            pid_to_edit = pid
        if not pid_to_edit:
            logging.error('Undefined pid.')
            return False
        if position == None or not replace_bytes:
            try:
                del self.emulator.answer[pid_to_edit]
                logging.debug('Removed answer for pid %s.', pid_to_edit)
                return True
            except Exception:
                logging.info('No answer configured for pid %s.', pid_to_edit)
            return False
        try:
            logging.debug('Scenario: %s. PID: %s',
                          self.emulator.scenario, pid_to_edit)
            r_response = self.emulator.ObdMessage[
                self.emulator.scenario][pid_to_edit]['Response']
        except Exception as e:
            logging.error('Unknown pid %s for scenario %s',
                          pid_to_edit, self.emulator.scenario)
            return False
        if isinstance(r_response, (list, tuple)):
            r_response = r_response[randint(0, len(r_response) - 1)]
        try:
            root = ET.fromstring('<xml>' + r_response + '</xml>')
        except ET.ParseError as e:
            logging.error(
                'Wrong response format for "%s"; %s', r_response, e)
            return False
        for i in root:
            if i.tag.lower() in ['data', 'string', 'writeln', 'neg_answer',
                                 'pos_answer', 'answer']:
                try:
                    org_ba = bytearray.fromhex(i.text)
                    replace_ba = bytearray.fromhex(replace_bytes)
                except Exception as e:
                    logging.error('Wrong hex format for %s / %s: %s',
                                  i.text, replace_bytes, e)
                    return False
                for j in replace_ba:
                    try:
                        org_ba[position] = j
                    except Exception as e:
                        logging.error(
                            'Replaced string is too long. %s / %s: %s',
                            i.text, replace_bytes, e)
                        return False
                    position += 1
                i.text = ' '.join('{:02x}'.format(x) for x in org_ba).upper()
        self.emulator.answer[pid_to_edit] = ET.tostring(root).decode()[5:-6]
        return True

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        When used with the Context Manager, resets the original answer.
        """
        if self.original_entry:
            self.emulator.answer[self.pid] = self.original_entry
        else:
            if self.pid in self.emulator.answer:
                del self.emulator.answer[self.pid]


def dump_var(var_name, value):
    """
    Used by do_tasks() to format dumped variables
    :param var_name: name of the variable
    :param value: value of the variable
    :return: (none)
    """
    if var_name in ["logging", "emulator", "shared", "__module__"]:
        return
    if var_name == "time_started":
        print("    {}: {}".format(
            var_name,
            datetime.datetime.fromtimestamp(float(value)).strftime('%c, ')) +
            str(round((float(value) % 1) * 1000000, 1)) + " microseconds.")
        return
    print("    {}: {}".format(var_name, value))


class Interpreter(Cmd):

    __hiden_methods = ('do_EOF',)
    rlc = rlcompleter.Completer().complete
    histfile = os.path.expanduser('~/.ELM327_emulator_history')
    host_lib = 'emulator' # must be declared in default(), completedefault(), completenames()
    histfile_size = 1000

    def __init__(self, emulator, args):
        self.emulator = emulator
        self.args = args

        self.traceback = None
        self.prompt_active = True
        self.color_active = True
        self.__set_ps_string('CMD')
        if self.args.batch_mode:
            self.prompt_active = False
            self.color_active = False
            Cmd.prompt = ''
            self.use_rawinput = False
        Cmd.__init__(self)

    def __set_ps_string(self, ps_string):
        self.ps_color = ('\x01\033[01;32m\x02'  # enter + green color + exit
                         + ps_string
                         + '>\x01\033[00m\x02 ')  # enter + white color + exit
        self.ps_nocolor = ps_string + '> '
        self.__set_ps()

    def __set_ps(self):
        ps = self.ps_color if self.color_active else self.ps_nocolor
        Cmd.prompt = ps if self.prompt_active else ''

    def print_topics(self, header, cmds, cmdlen, maxcol):
        if not cmds:
            return
        if self.args.batch_mode:
            return
        self.stdout.write(
        "Available commands include the following list (type help <topic>"
        "\nfor more information on each command). Besides, any Python"
        "\ncommand is accepted. Autocompletion is fully allowed."
        "\n=============================================================="
        "==\n")
        self.columnize(cmds, maxcol-1)
        self.stdout.write("\n")

    def emptyline(self):
        return

    def do_echo(self, arg):
        'Print the message in the argument.'
        print(arg)

    def do_EOF(self, arg):
        'Quit ELM327-emulator'
        if self.args.batch_mode:
            print("End of batch commands.")
            sys.stdout.flush()
            while threading.active_count() == 2:
                time.sleep(0.5)
        else:
            print("Terminating...")
        sys.exit(0)

    def do_quit(self, arg):
        "Quit ELM327-emulator. Also Control-D or interrupt \n"\
        "(Control-C) can be used."
        print("Terminating...")
        if arg:
            print ("Invalid format.")
            return
        sys.exit(0)

    def do_version(self, arg):
        "Print ELM327-emulator version."
        print(f'ELM327-emulator version {__version__}.')
    
    def do_delay(self, arg):
        "Delay each command of the seconds specified in the argument.\n"\
        "(Floating point number; default is 0.5 seconds.)"
        try:
            delay = 0.5 if len(arg) == 0 else float(arg.split()[0])
        except ValueError:
            print ("Invalid format.")
            return
        if delay > 0:
            print("Delaying each command of %s seconds" % delay)
            self.emulator.delay = delay
        else:
            print("Delay removed")
            self.emulator.delay = 0

    def do_wait(self, arg):
        "Perform an immediate sleep of the seconds specified "\
        "in the argument.\n"\
        "(Floating point number; default is 10 seconds.)"
        try:
            delay = 10 if len(arg) == 0 else float(arg.split()[0])
        except ValueError:
            print ("Invalid format.")
            return
        print("Sleeping for %s seconds" % delay)
        time.sleep(delay)

    def do_prompt(self, arg):
        "Toggle prompt off/on or change the prompt."
        if arg:
            self.__set_ps_string(arg.split()[0])
            return
        self.prompt_active = not self.prompt_active
        print("Prompt %s" % repr(self.prompt_active))
        self.__set_ps()

    def do_color(self, arg):
        "Toggle color off/on."
        if arg:
            print ("Invalid format.")
            return
        self.color_active = not self.color_active
        if not self.color_active:
            sys.stdout.write("\033[00m")  # white color
            sys.stdout.flush()
        print("Color %s" % repr(self.color_active))
        self.__set_ps()

    def do_reset(self, arg):
        "Reset the emulator (counters and variables)."
        if arg:
            print ("Invalid format.")
            return
        self.emulator.set_defaults()
        self.emulator.reset(0)
        print("Reset done.")

    def do_loglevel(self, arg):
        "If an argument is given, set the logging level,\n"\
        "otherwise show the current one.\n"\
        "CRITICAL=50, ERROR=40, WARNING=30, INFO=20, DEBUG=10."
        if arg and arg.isnumeric():  # numeric
            logging.getLogger().handlers[0].setLevel(int(arg))
            log = logging.getLogger().handlers[0].level
            if int(arg) in logging._levelToName:
                print("Logging level set to {} ({})".format(
                    log, logging._levelToName[log]))
            else:
                print("Logging level set to",
                      logging.getLogger().handlers[0].level)
        elif arg.upper() in [logging._levelToName[ll]  # literal
                             for ll in logging._levelToName]:
            logging.getLogger().handlers[0].setLevel(
                dict(zip(
                    logging._levelToName.values(),
                    logging._levelToName.keys()))[arg.upper()])
            log = logging.getLogger().handlers[0].level
            print("Logging level set to {} ({})".format(
                log, logging._levelToName[log]))
        else:
            if arg:
                print("Unknown setting:", repr(arg))
            log = logging.getLogger().handlers[0].level
            if log in logging._levelToName:
                print("Current logging level: {} ({})".format(
                    log, logging._levelToName[log]))
            else:
                print("Current logging level:",
                      logging.getLogger().handlers[0].level)

    def do_verify(
            self, arg, do_write=False, request_header=None, request_data=None):
        'Test the processing of the formatted XML response specified in\n'\
        'the argument (like "write", but without writing to the application).'
        if not arg:
            print(
                "Invalid format. Add the formatted XML response as argument.")
            return
        try:
            ret = self.emulator.handle_response(
                arg,
                do_write=do_write,
                request_header=request_header,
                request_data=request_data)
            if ret is None:
                print(
                    'Null data returned while processing XML response "{}".'.
                        format(arg))
            else:
                print(repr(ret))
        except Exception as e:
            print(traceback.format_exc())
            print("Could not process", arg, "-", repr(e))

    def do_write(self, arg):
        'Write the formatted XML response specified in the argument\n'\
        'to the connected application. (Use "verify" to avoid the \n'\
        'write operation.)'
        self.do_verify(arg, do_write=True)

    def do_test(self, arg):
        'Test the OBD-II request specified in the argument. Check also\n'\
        '"verify" and "write".'
        if not arg:
            print(
                "Invalid format. Add the OBD-II request to test as argument.")
            return
        print("______Raw command:_______________")
        try:
            (request_header,
             request_data,
             response_data) = self.emulator.handle_request(arg, do_write=False)
            if response_data is None:
                return
            if not response_data:
                print("Error in request. No data returned.")
                return
            print(repr(response_data))
        except Exception as e:
            print("Could not run test:", repr(e))
            print(traceback.format_exc())
            return
        print("\n______Command output:____________")
        self.do_verify(
            response_data,
            request_header=request_header,
            request_data=request_data)

    def do_port(self, arg):
        "Print the used TCP/IP port, or the used device,\n"\
        "or the serial COM port,\nor the serial pseudo-tty,\n"\
        "depending on the selected interface."
        if arg:
            print ("Invalid format.")
            return
        print("Using " + self.emulator.get_port_name(extended=True))

    def do_timer(self, arg):
        "Print or set the UDS timers P1, P2, P3, P4. The first argument\n"\
        "is the timer name, the second is the value in seconds. Without\n"\
        "arguments, print all timer values. Decimals are allowed."
        args = arg.split()
        usage = (
            'Usage: timer {P1|P2|P3|P4} seconds; ref. "help timer" command.')
        if not args:
            print ("P1: {} seconds "
                   "- UDS P1 timer - Inter byte time for ECU response".format(
                self.emulator.interbyte_out_delay))
            print("P2: {} seconds "
                  "- UDS P2 timer - Time between tester request and ECU "
                  "response or two ECU responses".format(
                self.emulator.delay))
            print("P3: {} seconds "
                  "- UDS P3 Timer - Time between end of ECU responses and "
                  "start of new tester request".format(
                self.emulator.multiframe_timer))
            print("P4: {} seconds "
                  "- UDS P4 timer - Inter byte time for tester request".format(
                self.emulator.counters['req_timeout']))
            return
        if len(args) != 2:
            print("Invalid format. {}. {}".format(
                repr(args[0]), usage))
            return
        try:
            if args[0].lower() == 'p1':
                self.emulator.interbyte_out_delay = float(args[1])
            elif args[0].lower() == 'p2':
                self.emulator.delay = float(args[1])
            elif args[0].lower() == 'p3':
                self.emulator.multiframe_timer = float(args[1])
            elif args[0].lower() == 'p4':
                self.emulator.counters['req_timeout'] = float(args[1])
            else:
                print ("Invalid format for timer {}. {}".format(
                        repr(args[0]), usage))
        except ValueError:
            print ("Invalid format for timer value {}. {}".format(
                repr(args[1]), usage))
            return

    def do_tasks(self, arg):
        "Print all available plugins; for each used ECU, print all active\n"\
        "tasks and dump related namespaces; dump also the shared namespaces."
        if arg:
            print ("Invalid format.")
            return
        if self.emulator.plugins:
            print("Plugins:")
            for i in sorted(self.emulator.plugins):
                print(" - {}".format(i))
        else:
            print("No plugin available.")
        if self.emulator.tasks:
            print("Active tasks:")
            for i in sorted(self.emulator.tasks):
                if len(self.emulator.tasks[i]):
                    for j in self.emulator.tasks[i]:
                        if j.__dict__:
                            print(
                                " - {}, ECU {}.".format(j.__module__, repr(i)))
                            for k, v in j.__dict__.items():
                                s = pprint.pformat(v, indent=6)
                                if '\n' in s:
                                    s = '\n' + s
                                dump_var(k, s)
                        else:
                            print(" - {}, ECU {} without namespace."
                                  .format(j.__module__, repr(i)))
                else:
                    print(" - (completed task), ECU {}.".format(repr(i)))
        else:
            print("No task available.")
        if self.emulator.task_shared_ns:
            print("Shared namespaces:")
            for i in sorted(self.emulator.task_shared_ns):
                if self.emulator.task_shared_ns[i].__dict__:
                    print(
                        " - {}, ECU {}.".format(
                            self.emulator.task_shared_ns[i].__module__,
                            repr(i)))
                    for k, v in self.emulator.task_shared_ns[
                            i].__dict__.items():
                        s = pprint.pformat(v, indent=6)
                        if '\n' in s:
                            s = '\n' + s
                        dump_var(k, s)
                else:
                    print(" - no namespace data for ECU {}.".format(repr(i)))
        else:
            print("No shared namespaces available.")

    def do_counters(self, arg):
        "Print the number of each executed PID (upper case names), "\
        "the values\n"\
        "associated to some 'AT' PIDs, the unknown requests, "\
        "the emulator response\n"\
        "delay, the total number of executed commands and the "\
        "current scenario."
        if arg:
            print ("Invalid format.")
            return
        if self.emulator.counters:
            print("PID Counters:")
            for i in sorted(self.emulator.counters):
                print("  {:22s} = {}".format(i, self.emulator.counters[i]))
        else:
            print("No counters available.")
        print("  {:22s} = {}".format("delay", self.emulator.delay))
        print("  {:22s} = {}".format("scenario", self.emulator.scenario))

    def do_pause(self, arg):
        "Pause the execution."
        if arg:
            print ("Invalid format.")
            return
        self.emulator.threadState = self.emulator.THREAD.PAUSED
        print("Backend emulator paused")

    def do_resume(self, arg):
        "Resume the execution after pausing; prints the used device."
        if arg:
            print ("Invalid format.")
            return
        self.emulator.threadState = self.emulator.THREAD.ACTIVE
        print(
            "Backend emulator resumed. Running on %s" % self.emulator.get_pty())

    def complete_loglevel(self, text, line, start_index, end_index):
        if text:
            return ([str(ll) for ll in sorted(logging._levelToName)
                           if ll > 0 and str(ll).startswith(text)] +
                    [logging._levelToName[ll]
                     for ll in sorted(logging._levelToName)
                     if logging._levelToName[ll].startswith(text.upper())])
        else:
            return ([str(ll) for ll in sorted(logging._levelToName) if ll > 0] +
                    [logging._levelToName[ll]
                     for ll in sorted(logging._levelToName)])

    def complete_scenario(self, text, line, start_index, end_index):
        if text:
            return [sc for sc in self.emulator.ObdMessage
                    if sc.startswith(text)]
        else:
            return [sc for sc in self.emulator.ObdMessage]

    def do_edit(self, arg):
        "Edit a PID answer. Arguments: PID, position, replaced bytes.\n"\
        "If only the PID is given, remove a previous editing."
        args = arg.split()
        if len(args) == 1:
            if Edit.answer(self, None, None, arg):
                print(f'{arg} answer has been reset to default.')
            else:
                print(f'No previous answer was set for pid {arg}.')
            try:
                r_response = self.emulator.ObdMessage[
                    self.emulator.scenario][arg]['Response']
                print(r_response)
            except Exception:
                print(f'Unknown response for pid {arg} in  scenario '
                      f'"{self.emulator.scenario}".')
            return
        if not args:
            print("Missing PID.")
            return
        if len(args) < 3:
            print ("Invalid format.")
            return
        try:
            position = eval(args[1])
        except Exception:
            print(f"Invalid format for position {args[1]}.")
            return
        if Edit.answer(self, position, ''.join(args[2:]), args[0]):
            print(f'Set answer for Pid {args[0]} with edited bytes:')
            print(self.emulator.answer[args[0]])
        else:
            print(f'Cannot set answer for pid {args[0]}.')
            return

    def do_scenario(self, arg):
        "Switch to the scenario specified in the argument; if the scenario "\
        "is\nmissing or invalid, defaults it to 'car'."
        if len(arg.split()) > 1:
            print ("Invalid format.")
            return
        if len(arg.split()):
            set_scenario(self.emulator, arg.split()[0])
        else:
            set_scenario(self.emulator, "")

    def complete_merge(self, text, line, start_index, end_index):
        if text:
            return [x[:-3] for x in glob.glob('*.py') if x.startswith(text)]
        else:
            return [x[:-3] for x in glob.glob('*.py')]

    def do_merge(self, arg):
        "import a scenario from an external module and merges it with\n"\
        "the emulator configuration."
        if len(arg.split()) == 1 and arg.split()[0] in [
                x[:-3] for x in glob.glob('*.py')]:
            try:
                exec('from ' + arg + ' import ObdMessage', globals())
                self.emulator.ObdMessage.update(ObdMessage)
                print("ObdMessage successfully imported and merged. "
                      "Available scenarios:")
                print("%s" % ', '.join([
                sc for sc in self.emulator.ObdMessage]))
            except Exception as e:
                print("Error merging '%s': %s." % (arg, e))
        else:
             if arg:
                print("Import error: invalid scenario '%s'." % arg)
             else:
                print("Import error: missing scenario.")

    def do_engineoff(self, arg):
        "Switch to 'engineoff' scenario."
        if arg:
            print ("Invalid format.")
            return
        self.emulator.scenario='engineoff'
        print("Emulator scenario switched to '%s'" % self.emulator.scenario)

    def do_default(self, arg):
        "Reset to 'default' scenario."
        if arg:
            print ("Invalid format.")
            return
        self.emulator.scenario='default'
        print("Emulator scenario reset to '%s'" % self.emulator.scenario)

    def do_commands(self, arg):
        "List the description of each available command."
        if arg:
            print ("Invalid format.")
            return
        formatter = "\n{0:10} "
        for name in self.get_names():
            if name[:3] == 'do_':
                print((formatter.format(name[3:]) +
                       getattr(self, name).__doc__.replace(
                           "\n", formatter.format(''))))
        print("")

    def do_history(self, arg):
        "print the command history; if an argument is given, print the last\n"\
        "n commands in the history; with argument 'clear', clears the history."
        if arg == "clear":
            readline.clear_history()
            return
        try:
            n = 20 if len(arg) == 0 else int(arg.split()[0])
        except ValueError:
            print ("Invalid format.")
            return
        num=readline.get_current_history_length() - n
        for i in range(num if num > 0 else 0,
                       readline.get_current_history_length()):
            print (readline.get_history_item(i + 1))

    def is_matched(self, expression):
        opening = tuple('({[')
        closing = tuple(')}]')
        mapping = dict(zip(opening, closing))
        queue = []
        for letter in expression:
            if letter in opening:
                queue.append(mapping[letter])
            elif letter in closing:
                if not queue or letter != queue.pop():
                    return False
        return not queue

    # completedefault and completenames manage autocompletion of Python
    # identifiers and namespaces
    def completedefault(self, text, line, begidx, endidx):
        emulator = self.emulator # ref. host_lib
        rld = '.'.join(text.split('.')[:-1])
        rlb = text.split('.')[-1]
        if (begidx > 0 and line[begidx-1] in ')]}' and
                line[begidx] == '.' and self.is_matched(line)):
            rlds = line.rstrip('.' + rlb)
            rl = [ rld + '.' + x for x in dir(eval(rlds))
                if x.startswith(rlb) and not x.startswith('__')
            ]
            return(rl)
        if rld:
            rl = [
                rld + '.' + x for x in dir(eval(rld))
                if x.startswith(rlb) and not x.startswith('__')
            ]
        else:
            rl = ['self'] if rlb != '' and 'self'.startswith(rlb) else []
            if self.host_lib.startswith(text):
                rl += [self.host_lib]
        return rl + [self.rlc(text, x) for x in range(400) if self.rlc(text, x)]

    def get_names(self):
        return [n for n in dir(self.__class__) if n not in self.__hiden_methods]

    def completenames(self, text, *ignored):
        emulator = self.emulator # ref. host_lib
        dotext = 'do_'+text
        rld = '.'.join(text.split('.')[:-1])
        rlb = text.split('.')[-1]
        if rld:
            rl = [
                rld + '.' + x for x in dir(eval(rld))
                if x.startswith(rlb) and not x.startswith('__')
            ]
        else:
            rl = ['self'] if rlb != '' and 'self'.startswith(rlb) else []
            if self.host_lib.startswith(text):
                rl += [self.host_lib]
        if not text:
            return [a[3:] for a in self.get_names() if a.startswith(dotext)]
        return ([a[3:] for a in self.get_names() if a.startswith(dotext)] +
                rl +
                [self.rlc(text, x) for x in range(400) if self.rlc(text, x)])

    def precmd(self, line):
        if self.color_active:
            sys.stdout.write("\033[36m")  # Cyan color
            sys.stdout.flush()
            line = re.sub(r"^(.*[^\\])#.*$", r"\1", line)  # strip the '#' comment if not escaped
        return Cmd.precmd(self, line)

    def postcmd(self, stop, line):
        self.emulator.set_sorted_obd_msg()
        return Cmd.postcmd(self, stop, line)

    def preloop(self):
        if self.emulator.threadState == self.emulator.THREAD.TERMINATED:
            sys.exit(0)
        if (readline and
                os.path.exists(self.histfile) and
                not self.args.batch_mode):
            try:
                readline.read_history_file(self.histfile)
            except FileNotFoundError:
                pass
            except PermissionError:
                print("No permissions to access the command line history file.")
                pass

    def postloop(self):
        if readline and not self.args.batch_mode:
            readline.set_history_length(self.histfile_size)
            readline.write_history_file(self.histfile)
        if self.color_active and not self.args.batch_mode:
            sys.stdout.write("\033[00m")  # White color
            sys.stdout.flush()

    # Execution of unrecognized commands
    def default(self, arg):
        emulator = self.emulator # ref. host_lib
        arg = '\n'.join(arg.split("\\n"))
        arg = '\t'.join(arg.split("\\t"))
        if '\n' in arg:
            print("Multiline command:\n", arg)
        try:
            print(eval(arg, {**globals(), **locals()}))
        except Exception:
            try:
                exec(arg, {**globals(), **locals()})
            except Exception as e:
                self.traceback = traceback.format_exc(chain=False)
                print("Error executing command: %s" % e)

    def cmdloop_with_keyboard_interrupt(self, arg):
        doQuit = False
        while doQuit != True:
            try:
                self.cmdloop(arg)
                doQuit = True
            except KeyboardInterrupt:
                print("Terminating...")
                sys.exit(0)


def set_scenario(emulator, scenario):
    if scenario and scenario in [
            sc for sc in emulator.ObdMessage]:
        emulator.scenario = scenario
    else:
        if scenario:
            print("Invalid scenario '%s'" % scenario)
        emulator.scenario = 'car'
    emulator.set_sorted_obd_msg()
    print("Emulator scenario switched to '%s'" % emulator.scenario)


def main():
    # Option handling
    parser = argparse.ArgumentParser(
        epilog='ELM327-emulator v' + __version__ +
        ' - ELM327 OBD-II adapter emulator')
    parser.prog = "elm"
    parser.add_argument(
        '-V',
        "--version",
        dest='version',
        action='store_true',
        help="Print ELM327-emulator version and exit")
    parser.add_argument(
        '-e',
        "--no-echo",
        dest='no_echo',
        action='store_true',
        help="Disable echo by default")
    parser.add_argument(
        '-l',
        "--newline",
        dest='newline',
        action='store_true',
        help="Use newline (<NL>) instead of carriage return <CR> "
             "for detecting a line separator")
    if os.name != 'nt':
        parser.add_argument(
            '-t',
            "--terminate",
            dest='terminate',
            action='store_true',
            help="Terminate the daemon process sending SIGTERM")
        parser.add_argument(
            "-d", "--daemon",
            dest = "daemon_mode",
            action='store_true',
            help = "Run ELM327-emulator in daemon mode. ")
    parser.add_argument(
        "-b", "--batch",
        dest="batch_mode",
        type=argparse.FileType('w'),
        help="Run ELM327-emulator in batch mode. "
             "Argument is the output file. "
             "The first line in that file will be the virtual serial device",
        default=0,
        nargs=1,
        metavar='FILE')
    parser.add_argument(
        '-p', '--port',
        dest = 'serial_port',
        help = ("Set the serial port listened by ELM327-emulator; "
                "default is COM3 (for com0com null-modem emulator)."
                if os.name == 'nt' else
                "Set a serial communication port instead of using "
               "a pseudo-tty."),
        default = ['COM3'] if os.name == 'nt' else None,
        nargs = 1,
        metavar = 'PORT'
    )
    parser.add_argument(
        '-P', '--device',
        dest = 'device_port',
        help = "Set the communication device to be opened instead of "
               "using a pseudo-tty port.",
        default = None,
        nargs = 1,
        metavar = 'DEVICE_PORT'
    )
    parser.add_argument(
        '-a', '--baudrate',
        dest = 'serial_baudrate',
        type=int,
        help = "Set the serial device baud rate used by ELM327-emulator.",
        default = None,
        nargs = 1,
        metavar = 'BAUDRATE'
    )
    parser.add_argument(
        '-v', '--log',
        dest = 'log',
        type=int,
        help = "Preset a log level in interactive mode.",
        default = None,
        nargs = 1,
        metavar = 'LOG'
    )
    parser.add_argument(
        '-s', '--scenario',
        dest = 'scenario',
        help = "Set the scenario used by ELM327-emulator.",
        default = [''],
        nargs = 1,
        metavar = 'SCENARIO'
    )
    parser.add_argument(
        '-n', '--net',
        dest = 'net_port',
        type=int,
        help = "Set the INET socket port used by ELM327-emulator.",
        default = None,
        nargs = 1,
        metavar = 'INET_PORT'
    )
    parser.add_argument(
        '-H', '--forward_host',
        dest = 'forward_net_host',
        help = "Set the INET host used by ELM327-emulator."
            "when forwarding the client interaction to a remote OBD-II port.",
        default = None,
        nargs = 1,
        metavar = 'INET_FORWARD_HOST'
    )
    parser.add_argument(
        '-N', '--forward_port',
        dest = 'forward_net_port',
        type=int,
        help = "Set the INET socket port used by ELM327-emulator "
            "when forwarding the client interaction to a remote OBD-II port.",
        default = None,
        nargs = 1,
        metavar = 'INET_FORWARD_PORT'
    )
    parser.add_argument(
        '-S', '--forward_serial_port',
        dest = 'forward_serial_port',
        help = "Set the serial device port used by ELM327-emulator "
            "when forwarding the client interaction to a serial device.",
        default = None,
        nargs = 1,
        metavar = 'FORWARD_SERIAL_PORT'
    )
    parser.add_argument(
        '-B', '--forward_serial_baudrate',
        dest = 'forward_serial_baudrate',
        type=int,
        help = "Set the device baud rate used by ELM327-emulator "
            "when forwarding the client interaction to a serial device.",
        default = None,
        nargs = 1,
        metavar = 'FORWARD_SERIAL_BAUDRATE'
    )
    parser.add_argument(
        '-T', '--forward_timeout',
        dest = 'forward_timeout',
        type=float,
        help = "Set forward timeout as floating number "
            "(default is 5 seconds).",
        default = None,
        nargs = 1,
        metavar = 'FORWARD_TIMEOUT'
    )
    args = parser.parse_args()

    if args.version:
        print(f'ELM327-emulator version {__version__}.')
        sys.exit(0)

    # Redirect stdout
    if args.batch_mode and not args.batch_mode[0].isatty():
        sys.stdout = args.batch_mode[0]

    if os.name == 'nt':
        args.daemon_mode = False
        args.terminate = False
        os.system('color')  # enable the ANSI escape sequences with Windows

    # Instantiate the class
    emulator = Elm(
        batch_mode=args.batch_mode or args.daemon_mode,
        newline=args.newline,
        no_echo=args.no_echo,
        serial_port=args.serial_port[0]
           if args.serial_port else None,
        device_port=args.device_port[0]
            if args.device_port else None,
        serial_baudrate=args.serial_baudrate[0]
            if args.serial_baudrate else None,
        net_port=args.net_port[0]
            if args.net_port else None,
        forward_net_host=args.forward_net_host[0]
            if args.forward_net_host else None,
        forward_net_port=args.forward_net_port[0]
            if args.forward_net_port else None,
        forward_serial_port=args.forward_serial_port[0]
            if args.forward_serial_port else None,
        forward_serial_baudrate = args.forward_serial_baudrate[0]
            if args.forward_serial_baudrate else None,
        forward_timeout = args.forward_timeout[0]
            if args.forward_timeout else None)

    if os.name != 'nt':
        if os.getuid() == 0:
            daemon_pid_fname = DAEMON_PIDFILE_DIR_ROOT + DAEMON_PIDFILE
        else:
            daemon_pid_fname = DAEMON_PIDFILE_DIR_NON_ROOT + DAEMON_PIDFILE
        pidfile = daemon.pidfile.PIDLockFile(daemon_pid_fname)
        pid = pidfile.read_pid()

    if args.terminate:
        if pid:
            print(f'Terminating daemon process {pid}.')
            try:
                Ret = os.kill(pid, signal.SIGTERM)
            except Exception as e:
                print(f'Error while terminating daemon process {pid}: {e}.')
                sys.exit(1)
            if Ret:
                print(f'Error while terminating daemon process {pid}.')
                sys.exit(1)
            else:
                sys.exit(0)
        else:
            print('Cannot terminate daemon process: not running.')
            sys.exit(0)

    if args.batch_mode and args.daemon_mode:
        try:
            print(emulator.get_pty())
            print('ELM327-emulator service STARTED')
            if args.scenario[0]:
                set_scenario(emulator, args.scenario[0])
            emulator.run()
        except (KeyboardInterrupt, SystemExit):
            emulator.terminate()
        print("\nELM327-emulator service ENDED")
        sys.exit(0)

    if args.daemon_mode and not args.batch_mode:
        if pid:
            try:
                pidfile.acquire()
                pidfile.release() # this might occur only in rare contention cases
            except AlreadyLocked:
                try:
                    os.kill(pid, 0)
                    print(f'Process {pid} already running. '
                        f'Check lockfile "{daemon_pid_fname}".')
                    sys.exit(1)
                except OSError:  #No process with locked PID
                    pidfile.break_lock()
                    print(f"Previous process {pid} terminated abnormally.")
            except NotLocked:
                print("Internal error: lockfile", daemon_pid_fname)
        context = daemon.DaemonContext(
            working_directory=DAEMON_DIR,
            umask=DAEMON_UMASK,
            pidfile=pidfile,
            detach_process=True,
            stdout=sys.stdout,
            stderr=sys.stderr,
            signal_map={
                signal.SIGTERM: lambda signum, frame: emulator.terminate(),
                signal.SIGINT: lambda signum, frame: emulator.terminate()
                }
            )
        try:
            with context:
                print('ELM327-emulator daemon service STARTED on ',
                    emulator.get_pty())
                if args.scenario[0]:
                    set_scenario(emulator, args.scenario[0])
                emulator.run()
                print("\nELM327-emulator daemon service ENDED")
        except LockFailed as e:
            print('Internal error: cannot start daemon', e)
            sys.exit(1)
        sys.exit(0)

    if os.name != 'nt' and pid:
        print(f'Warning: lockfile "{daemon_pid_fname}" reports pid {pid}.')

    p_elm = None
    pty_name = None
    try:
        with emulator as session:
            while session.threadState == session.THREAD.STARTING:
                time.sleep(0.1)
            if session.threadState == session.THREAD.TERMINATED:
                print('\nELM327-emulator cannot run. Exiting.\n')
                os._exit(1)  # does not raise SystemExit
            if args.net_port:
                pty_name = "TCP network port " + str(args.net_port[0]) + "."
            else:
                pty_name = session.get_pty()
                if args.batch_mode:
                    print(pty_name)
                sys.stdout.flush()
            if args.scenario[0]:
                set_scenario(session, args.scenario[0])
            if pty_name == None:
                print("\nCannot start ELM327-emulator.\n")
                os._exit(1) # does not raise SystemExit
            p_elm = Interpreter(session, args)
            if args.log:
                logging.getLogger().handlers[0].setLevel(int(args.log[0]))
            if args.batch_mode:
                p_elm.cmdloop_with_keyboard_interrupt(
                    'ELM327-emulator batch mode STARTED\n'
                    'Begin batch commands.')
            else:
                p_elm.cmdloop_with_keyboard_interrupt(
                    'Welcome to the ELM327 OBD-II adapter emulator.\n'
                    'ELM327-emulator is running on %s\n'
                    'Type help or ? to list commands.\n' % pty_name)
    except (KeyboardInterrupt, SystemExit):
        if not args.batch_mode and p_elm:
            p_elm.postloop()
            print('\n\nExiting.\n')
        else:
            print("\nELM327-emulator batch mode ENDED")
        sys.exit(1)
