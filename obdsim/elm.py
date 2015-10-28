
import os
import pty
import threading

class ELM:

    # constant AT commands
    ELM_ECHO = "E[01]"
    ELM_HEADERS = "H[01]"
    ELM_LINEFEEDS = "L[01]"

    def __init__(self, protocols, ecus):

        # ELM state
        self.echo = True
        self.headers = True
        self.linefeeds = True


    def __enter__(self):

        # make a new pty
        self.master, self.slave = pty.openpty()

        # start the thread
        self.running = True
        self.thread = threading.Thread(target=self.run)
        self.thread.daemon = True
        self.thread.start()

        return os.ttyname(self.master)


    def __exit__(self):
        self.running = False
        self.thread.join()
        os.close(self.master)


    def run(self):
        """ the ELM's main IO loop """
        while self.running:
            # read the 
            r = os.read(self.master, 1024).decode()
