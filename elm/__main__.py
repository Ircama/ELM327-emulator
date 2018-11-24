import threading

from .elm import ELM, THREAD
import time
import sys

def main():
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
            command = input("Enter command: ")
            if command == 'q':
                sys.exit(0)
            elif command == 'p':
                emulator.threadState = THREAD.PAUSED
                print("Backend emulator paused")
            elif command == 'r':
                emulator.threadState = THREAD.ACTIVE
                print("Backend emulator resumed. Running on %s" % pts_name)
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
