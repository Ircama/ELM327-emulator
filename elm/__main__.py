try:
    import readline
except:
    pass #readline not available
import threading
import logging
from .elm import ELM, THREAD
import time
import sys
import re

def main():
    prompt = 1
    emulator = ELM(None, None)

    with emulator as pts_name:
        print("Running on %s" % pts_name)
        while True:
            if emulator.threadState == THREAD.STARTING:
                time.sleep(0.1)
                continue
            if threading.active_count() < 2:
                print("Backend emulator has ended")
                break
            try:
               if prompt:
                   command = input("CMD> ")
               else:
                   command = input()
            except EOFError:
                sys.exit(0)
            if re.match('^t$|^t \d+?(\.\d+)?$', command):
                delay = 0.5 if len(command.split()) < 2 else float(command.split()[1])
                print("Delaying each command of %d seconds" % delay)
                emulator.delay = delay
                continue
            if re.match('^w$|^w \d+?(\.\d+)?$', command):
                delay = 10 if len(command.split()) < 2 else float(command.split()[1])
                print("Sleeping for %d seconds" % delay)
                time.sleep(delay)
                continue
            if command == 'i':
                prompt = not prompt
                print("Prompt %d" % prompt)
                continue
            if command == 'q':
                sys.exit(0)
            if command == 'reset':
                emulator.set_defaults()
                print("Reset done.")
                continue
            elif command == 'c':
                if emulator.counters:
                    print("PID Counters:")
                    for i in sorted(emulator.counters):
                        print("  {:20s} = {}".format(i, emulator.counters[i]))
                else:
                    print("No counters available.")
                print("  {:20s} = {}".format("delay", emulator.delay))
                print("  {:20s} = {}".format("scenario", emulator.scenario))
            elif command == 'p':
                emulator.threadState = THREAD.PAUSED
                print("Backend emulator paused")
            elif command == 'r':
                emulator.threadState = THREAD.ACTIVE
                print("Backend emulator resumed. Running on %s" % pts_name)
            elif re.match('^(s [^ \t]+)|s$', command):
                s = command.split()
                if len(s) == 2 and s[1] in emulator.ObdMessage:
                    emulator.scenario=s[1]
                else:
                    emulator.scenario='test'
                print("Emulator scenario switched to '%s'" % emulator.scenario)
            elif command == 'o':
                emulator.scenario='engineoff'
                print("Emulator scenario switched to '%s'" % emulator.scenario)
            elif command == 'd':
                emulator.scenario='default'
                print("Emulator scenario reset to '%s'" % emulator.scenario)
            elif command:
                try:
                    exec(command)
                except Exception as e:
                    print("Error executing command: %s" % e)

if __name__ == '__main__':
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        print('\n\nExiting.\n')
        sys.exit(0)
    sys.exit(1)
