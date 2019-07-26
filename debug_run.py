#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
try:
    if sys.hexversion < 0x3050000:
        raise ImportError("Python version must be >= 3.5")
    import threading
    import logging
    from elm.elm import ELM, THREAD
    import time
    from cmd import Cmd
    import rlcompleter
    import glob
    import os.path
    import argparse
    try:
        import readline
    except ImportError:
        readline = None
except ImportError as detail:
    print("ELM327 OBDII adapter emulator error:\n " + str(detail))
    sys.exit(1)

class Interpreter(Cmd):

    __hiden_methods = ('do_EOF',)
    rlc = rlcompleter.Completer().complete
    histfile = os.path.expanduser('~/.ELM327_emulator_history')
    histfile_size = 1000

    def __init__(self, emulator, args):
        self.emulator = emulator
        self.prompt_active = True
        self.color_active = True
        self.__set_ps_string('CMD')
        if args.batch_mode:
            self.prompt_active = False
            self.color_active = False
            Cmd.prompt = ''
            self.use_rawinput = False
        Cmd.__init__(self)

    def __set_ps_string(self, ps_string):
        self.ps_color = '\x01\033[01;32m\x02' + ps_string + '>\x01\033[00m\x02 '
        self.ps_nocolor = ps_string + '> '
        self.__set_ps()

    def __set_ps(self):
        ps = self.ps_color if self.color_active else self.ps_nocolor
        Cmd.prompt = ps if self.prompt_active else ''

    def print_topics(self, header, cmds, cmdlen, maxcol):
        if not cmds:
            return
        if args.batch_mode:
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

    def do_EOF(self, arg):
        if args.batch_mode:
            while threading.active_count() == 2:
                time.sleep(0.5)
        sys.exit(0)

    def get_names(self):
        return [n for n in dir(self.__class__) if n not in self.__hiden_methods]

    def do_quit(self, arg):
        'Quit the emulator'
        if arg:
            print ("Invalid format")
            return
        sys.exit(0)

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
            sys.stdout.write("\u001b[36m")
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
        self.emulator.threadState = THREAD.PAUSED
        print("Backend emulator paused")

    def do_resume(self, arg):
        "Resume the execution after pausing; prints the used device."
        if arg:
            print ("Invalid format")
            return
        self.emulator.threadState = THREAD.ACTIVE
        print("Backend emulator resumed. Running on %s" % pts_name)

    def complete_scenario(self, text, line, start_index, end_index):
        if text:
            return [sc for sc in emulator.ObdMessage if sc.startswith(text)]
        else:
            return [sc for sc in emulator.ObdMessage]

    def do_scenario(self, arg):
        "Switch to the scenario specified in the argument; if the scenario is\n"\
        "missing or invalid, defaults to 'car'."
        if len(arg.split()) == 1 and arg.split()[0] in [
                sc for sc in emulator.ObdMessage]:
            self.emulator.scenario = arg.split()[0]
        else:
            if len(arg.split()) > 0:
                print("Invalid scenario '%s'" % arg)
            self.emulator.scenario = 'car'
        print("Emulator scenario switched to '%s'" % self.emulator.scenario)

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
                emulator.ObdMessage.update(ObdMessage)
                print("ObdMessage successfully imported and merged. "
                      "Available scenarios:")
                print("%s" % ', '.join([
                sc for sc in emulator.ObdMessage]))
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
        rld='.'.join(text.split('.')[:-1])
        rlb=text.split('.')[-1]
        if begidx > 0 and line[begidx-1] in ')]}' and line[begidx] == '.' and self.is_matched(line):
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
        return rl + [self.rlc(text, x) for x in range(400) if self.rlc(text, x)]

    def completenames(self, text, *ignored):
        dotext = 'do_'+text
        rld='.'.join(text.split('.')[:-1])
        rlb=text.split('.')[-1]
        if rld:
            rl = [
                rld + '.' + x for x in dir(eval(rld))
                if x.startswith(rlb) and not x.startswith('__')
            ]
        else:
            rl = ['self'] if rlb != '' and 'self'.startswith(rlb) else []
        if not text:
            return [a[3:] for a in self.get_names() if a.startswith(dotext)]
        return [a[3:] for a in self.get_names() if a.startswith(dotext)
                ] + rl + [self.rlc(text, x) for x in range(400) if self.rlc(text, x)]

    def preloop(self):
        if readline and os.path.exists(self.histfile) and not args.batch_mode:
            try:
                readline.read_history_file(self.histfile)
            except FileNotFoundError:
                pass

    def postloop(self):
        if readline and not args.batch_mode:
            readline.set_history_length(self.histfile_size)
            readline.write_history_file(self.histfile)

    # Execution of unrecognized commands
    def default(self, arg):
        try:
            print ( eval(arg) )
        except Exception:
            try:
                exec(arg, globals())
            except Exception as e:
                print("Error executing command: %s" % e)


if __name__ == '__main__':
    # Option handling
    parser = argparse.ArgumentParser(
        epilog='ELM327-emulator - ELM327 OBDII adapter emulator')
    parser.prog = "python3 -m elm"
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
        help = 'Set the virtual serial port ELM327-emulator listenning when running under windows OS',
        default = 'COM3',
        nargs = 1,
        metavar = 'PORT'
    )
    args = parser.parse_args()

    # Redirect stdout
    if args.batch_mode:
        sys.stdout = args.batch_mode[0]

    try:
        emulator = ELM(args.batch_mode, args.serial_port)
        with emulator as pts_name:
            if args.batch_mode:
                print(pts_name)
            while emulator.threadState == THREAD.STARTING:
                time.sleep(0.1)
            sys.stdout.flush()
            p_elm = Interpreter(emulator, args)
            if args.batch_mode:
                p_elm.cmdloop('ELM327-emulator batch mode STARTED\n')
            else:
                p_elm.cmdloop('Welcome to the ELM327 OBDII adapter emulator.\n'
                              'ELM327-emulator is running on %s\n'
                              'Type help or ? to list commands.\n' % pts_name)
    except (KeyboardInterrupt, SystemExit):
        if not args.batch_mode:
            p_elm.postloop()
            print('\n\nExiting.\n')
        else:
            print("\nELM327-emulator batch mode ENDED")
        sys.exit(0)
    sys.exit(1)
