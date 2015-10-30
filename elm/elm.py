
import re
import os
import pty
import threading


class ELM:

    ELM_VALID_CHARS = r"[a-zA-Z0-9 \n\r]"

    # constant AT commands
    ELM_AT = r"^AT"

    ELM_RESET            = r"Z$"
    ELM_WARM_START       = r"WS$"
    ELM_DEFAULTS         = r"D$"
    ELM_VERSION          = r"I$"
    ELM_ECHO             = r"E[01]$"
    ELM_HEADERS          = r"H[01]$"
    ELM_LINEFEEDS        = r"L[01]$"
    ELM_DESCRIBE_PROTO   = r"DP$"
    ELM_DESCRIBE_PROTO_N = r"DPN$"
    ELM_SET_PROTO        = r"SPA?[0-9A-C]$"
    ELM_ERASE_PROTO      = r"SP00$"
    ELM_TRY_PROTO        = r"TPA?[0-9A-C]$"


    def __init__(self, protocols, ecus):
        self.set_defaults()


    def __enter__(self):

        # make a new pty
        self.master_fd, self.slave_fd = pty.openpty()
        self.slave_name = os.ttyname(self.slave_fd)

        # start the read thread
        self.running = True
        self.thread = threading.Thread(target=self.run)
        self.thread.daemon = True
        self.thread.start()

        return self.slave_name


    def __exit__(self, exc_type, exc_value, traceback):
        self.running = False
        # self.thread.join()
        os.close(self.slave_fd)
        os.close(self.master_fd)
        return False # don't suppress any exceptions


    def run(self):
        """ the ELM's main IO loop """
        while self.running:

            # get the latest command
            cmd = self.read()
            print("recv: ", cmd)
            self.write("OK")

            # if it didn't contain any egregious errors, handle it
            # if cmd:
                # resp = self.handle(cmd)
                # self.write(resp)


    def read(self):
        """
            reads the next newline delimited command from the port
            filters 

            returns a normallized string command
        """
        buffer = ""

        while True:
            c = os.read(self.master_fd, 1).decode()

            if c == '\n':
                break

            if not re.match(self.ELM_VALID_CHARS, c):
                pass

            buffer += c

        return buffer


    def write(self, resp):
        resp += "\n>"
        return os.write(self.master_fd, resp.encode())


    def handle(self, cmd):
        """ handles all commands """
        if re.match(self.ELM_AT, cmd):
            if re.match(self.ELM_ECHO, cmd):
                self.echo = (cmd[3] == '1')
            elif re.match(self.ELM_HEADERS, cmd):
                self.headers = (cmd[3] == '1')
            elif re.match(self.ELM_LINEFEEDS, cmd):
                self.linefeeds = (cmd[3] == '1')
            else:
                pass
        else:
            pass

        return "OK"


    def set_defaults(self):
        """ returns all settings to their defaults """
        self.echo = True
        self.headers = True
        self.linefeeds = True
