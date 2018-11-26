try:
    import readline
except:
    pass #readline not available
import threading
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
                   command = input("Enter command: ")
               else:
                   command = input()
            except EOFError:
                sys.exit(0)
            if re.match('^s [0-9]+$', command):
                numbers = [int(s) for s in command.split() if s.isdigit()]
                delay = 10 if numbers == [] else numbers[0]
                print("Sleeping for %d seconds" % delay)
                time.sleep(delay)
                continue
            if command == 'i':
                prompt = not prompt
                print("Prompt %d" % prompt)
                continue
            if command == 'q':
                sys.exit(0)
            elif command == 'c':
                print("Number of executed commands: %s" % emulator.commandCounter)
            elif command == 'p':
                emulator.threadState = THREAD.PAUSED
                print("Backend emulator paused")
            elif command == 'r':
                emulator.threadState = THREAD.ACTIVE
                print("Backend emulator resumed. Running on %s" % pts_name)
            elif command == 't':
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
