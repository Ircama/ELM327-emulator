
import os
import pty
import threading


class ELM:

    ELM_VALID_CHARS = r"[a-zA-Z0-9 \n\r]"

    # constant AT commands
    ELM_AT        = r"^AT"
    ELM_ECHO      = r"^ATE[01]$"
    ELM_HEADERS   = r"^ATH[01]$"
    ELM_LINEFEEDS = r"^ATL[01]$"


    def __init__(self, protocols, ecus):

        # ELM state
        self.echo = True
        self.headers = True
        self.linefeeds = True


    def __enter__(self):

        # make a new pty
        self.master_fd, slave_fd = pty.openpty()
        self.slave_name = os.ttyname(slave_fd)
        os.close(slave_fd)

        # start the read thread
        self.running = True
        self.thread = threading.Thread(target=self.run)
        self.thread.daemon = True
        self.thread.start()

        return self.slave_name


    def __exit__(self):
        self.running = False
        self.thread.join()
        os.close(self.master_fd)


    def run(self):
        """ the ELM's main IO loop """
        while self.running:

            # get the latest command
            cmd = self.read()

            # if it didn't contain any egregious errors, handle it
            if cmd:
                resp = self.handle(cmd)
                self.write(resp)


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

            if not re.match(ELM_VALID_CHARS, c):
                pass

            buffer += c

        return buffer


    def write(self, resp):
        return os.write(self.master_fd, resp.encode())


    def handle(self, cmd):
        """ handles all commands """
        if re.match(ELM_AT, cmd):
            if re.match(ELM_ECHO, cmd):
                self.echo = (cmd[3] == '1')
            elif re.match(ELM_HEADERS, cmd):
                self.headers = (cmd[3] == '1')
            elif re.match(ELM_LINEFEEDS, cmd):
                self.linefeeds = (cmd[3] == '1')
            else:
                pass
        else:
            pass
