#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###########################################################################
# ELM327-emulator
# ELM327 Emulator for testing software interfacing OBDII via ELM327 adapter
# https://github.com/Ircama/ELM327-emulator
# (C) Ircama 2021 - CC-BY-NC-SA-4.0
###########################################################################

import sys
try:
    if sys.hexversion < 0x3060000:
        raise ImportError("Python version must be >= 3.6")
    import threading
    from .elm import Elm
    import time
    from cmd import Cmd
    import rlcompleter
    import glob
    import os
    import os.path
    import argparse
    if os.name == 'nt':
        import tendo.ansiterm
    else:
        import daemon
        import daemon.pidfile
    import signal
    from lockfile.pidlockfile import PIDLockFile
    from lockfile import AlreadyLocked, NotLocked, LockFailed
    from .__version__ import __version__
    try:
        import readline
    except ImportError:
        readline = None
    from .obd_message import ObdMessage, ECU_ADDR_E, ELM_R_OK
except ImportError as detail:
    print("ELM327 OBDII adapter emulator error:\n " + str(detail))
    sys.exit(1)

DAEMON_PIDFILE_DIR_ROOT = '/var/run/'
DAEMON_PIDFILE_DIR_NON_ROOT = '/tmp/'
DAEMON_PIDFILE = 'ELM327_emulator.pid'
DAEMON_UMASK = 0o002
DAEMON_DIR = '/tmp'

class Interpreter(Cmd):

    __hiden_methods = ('do_EOF',)
    rlc = rlcompleter.Completer().complete
    histfile = os.path.expanduser('~/.ELM327_emulator_history')
    host_lib = 'emulator' # must be declared in default(), completedefault(), completenames()
    histfile_size = 1000

    def __init__(self, emulator, args):
        self.emulator = emulator
        self.args = args

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
        self.ps_color = '\x01\033[01;32m\x02' + ps_string + '>\x01\033[00m\x02 '
        if os.name == 'nt':
            self.ps_color = '\033[01;32m' + ps_string + '>\033[00m '
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
            print ("Invalid format")
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
            print ("Invalid format")
            return
        if delay > 0:
            print("Delaying each command of %s seconds" % delay)
            self.emulator.delay = delay
        else:
            print("Delay removed")
            self.emulator.delay = 0

    def do_wait(self, arg):
        "Perform an immediate sleep of the seconds specified in the argument.\n"\
        "(Floating point number; default is 10 seconds.)"
        try:
            delay = 10 if len(arg) == 0 else float(arg.split()[0])
        except ValueError:
            print ("Invalid format")
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
            print ("Invalid format")
            return
        self.color_active = not self.color_active
        if not self.color_active:
            sys.stdout.write("\033[00m")
            sys.stdout.flush()
        print("Color %s" % repr(self.color_active))
        self.__set_ps()

    def precmd(self, line):
        if self.color_active:
            sys.stdout.write("\033[36m")
            sys.stdout.flush()
        return Cmd.precmd(self, line)

    def postcmd(self, stop, line):
        self.emulator.setSortedOBDMsg()
        return Cmd.postcmd(self, stop, line)

    def do_reset(self, arg):
        "Reset the emulator (counters and variables)"
        if arg:
            print ("Invalid format")
            return
        self.emulator.set_defaults()
        print("Reset done.")

    def do_counters(self, arg):
        "Print the number of each executed PID (upper case names), the values\n"\
        "associated to some 'AT' PIDs, the unknown requests, the emulator response\n"\
        "delay, the total number of executed commands and the current scenario."
        if arg:
            print ("Invalid format")
            return
        if self.emulator.counters:
            print("PID Counters:")
            for i in sorted(self.emulator.counters):
                print("  {:20s} = {}".format(i, self.emulator.counters[i]))
        else:
            print("No counters available.")
        print("  {:20s} = {}".format("delay", self.emulator.delay))
        print("  {:20s} = {}".format("scenario", self.emulator.scenario))

    def do_pause(self, arg):
        "Pause the execution."
        if arg:
            print ("Invalid format")
            return
        self.emulator.threadState = self.emulator.THREAD.PAUSED
        print("Backend emulator paused")

    def do_resume(self, arg):
        "Resume the execution after pausing; prints the used device."
        if arg:
            print ("Invalid format")
            return
        self.emulator.threadState = self.emulator.THREAD.ACTIVE
        print(
            "Backend emulator resumed. Running on %s" % self.emulator.get_pty())

    def complete_scenario(self, text, line, start_index, end_index):
        if text:
            return [sc for sc in self.emulator.ObdMessage if sc.startswith(text)]
        else:
            return [sc for sc in self.emulator.ObdMessage]

    def do_scenario(self, arg):
        "Switch to the scenario specified in the argument; if the scenario is\n"\
        "missing or invalid, defaults to 'car'."
        if len(arg.split()) > 1:
            print ("Invalid format")
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
        "Switch to 'engineoff' scenario"
        if arg:
            print ("Invalid format")
            return
        self.emulator.scenario='engineoff'
        print("Emulator scenario switched to '%s'" % self.emulator.scenario)

    def do_default(self, arg):
        "Reset to 'default' scenario"
        if arg:
            print ("Invalid format")
            return
        self.emulator.scenario='default'
        print("Emulator scenario reset to '%s'" % self.emulator.scenario)

    def do_history(self, arg):
        "print the command history; if an argument is given, print the last\n"\
        "n commands in the history; with argument 'clear', clears the history"
        if arg == "clear":
            readline.clear_history()
            return
        try:
            n = 20 if len(arg) == 0 else int(arg.split()[0])
        except ValueError:
            print ("Invalid format")
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
        return [a[3:] for a in self.get_names() if a.startswith(dotext)
                ] + rl + [self.rlc(text, x) for x in range(400) if self.rlc(text, x)]

    def preloop(self):
        if readline and os.path.exists(self.histfile) and not self.args.batch_mode:
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
            sys.stdout.write("\033[00m")
            sys.stdout.flush()

    # Execution of unrecognized commands
    def default(self, arg):
        emulator = self.emulator # ref. host_lib
        try:
            print(eval(arg, locals()))
        except Exception:
            try:
                exec(arg, locals())
            except Exception as e:
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
    emulator.setSortedOBDMsg()
    print("Emulator scenario switched to '%s'" % emulator.scenario)


def main():
    # Option handling
    parser = argparse.ArgumentParser(
        epilog='ELM327-emulator v' + __version__ +
        ' - ELM327 OBDII adapter emulator')
    parser.prog = "elm"
    parser.add_argument(
        '-V',
        "--version",
        dest='version',
        action='store_true',
        help="print ELM327-emulator version and exit")
    if os.name != 'nt':
        parser.add_argument(
            '-t',
            "--terminate",
            dest='terminate',
            action='store_true',
            help="terminate the daemon process sending SIGTERM")
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
        help = "Set the com0com serial port listened by ELM327-emulator "
               "when running under windows OS. Default is COM3.",
        default = ['COM3'],
        nargs = 1,
        metavar = 'PORT'
    )
    parser.add_argument(
        '-s', '--scenario',
        dest = 'scenario',
        help = "Set the scenario used by ELM327-emulator.",
        default = [''],
        nargs = 1,
        metavar = 'SCENARIO'
    )
    args = parser.parse_args()

    if args.version:
        print(f'ELM327-emulator version {__version__}.')
        sys.exit(0)

    # Redirect stdout
    if args.batch_mode and not args.batch_mode[0].isatty():
        sys.stdout = args.batch_mode[0]

    # Instantiate the class
    if os.name == 'nt':
        args.daemon_mode = False
        args.terminate = False

    emulator = Elm(args.batch_mode or args.daemon_mode,
        args.serial_port[0])

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
    try:
        with emulator as session:
            while session.threadState == session.THREAD.STARTING:
                time.sleep(0.1)
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
            if args.batch_mode:
                p_elm.cmdloop_with_keyboard_interrupt(
                    'ELM327-emulator batch mode STARTED\n'
                    'Begin batch commands.')
            else:
                p_elm.cmdloop_with_keyboard_interrupt(
                    'Welcome to the ELM327 OBDII adapter emulator.\n'
                    'ELM327-emulator is running on %s\n'
                    'Type help or ? to list commands.\n' % pty_name)
    except (KeyboardInterrupt, SystemExit):
        if not args.batch_mode and p_elm:
            p_elm.postloop()
            print('\n\nExiting.\n')
        else:
            print("\nELM327-emulator batch mode ENDED")
        sys.exit(1)
