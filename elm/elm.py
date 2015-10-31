
import re
import os
import pty
import threading


class ELM:

    ELM_VALID_CHARS = r"[a-zA-Z0-9 \n\r]*"

    # AT commands
    ELM_AT = r"^AT"

    ELM_RESET            = r"ATZ$"
    ELM_WARM_START       = r"ATWS$"
    ELM_DEFAULTS         = r"ATD$"
    ELM_VERSION          = r"ATI$"
    ELM_ECHO             = r"ATE[01]$"
    ELM_HEADERS          = r"ATH[01]$"
    ELM_LINEFEEDS        = r"ATL[01]$"
    ELM_DESCRIBE_PROTO   = r"ATDP$"
    ELM_DESCRIBE_PROTO_N = r"ATDPN$"
    ELM_SET_PROTO        = r"ATSPA?[0-9A-C]$"
    ELM_ERASE_PROTO      = r"ATSP00$"
    ELM_TRY_PROTO        = r"ATTPA?[0-9A-C]$"

    # responses
    ELM_OK = "OK"


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
            self.cmd = self.read()
            print("recv:", repr(self.cmd))

            # if it didn't contain any egregious errors, handle it
            if self.validate(self.cmd):
                resp = self.handle(self.cmd)
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

            if c == '\r':
                continue # ignore carraige returns

            buffer += c

        return buffer


    def write(self, resp):
        """ write a response to the port """

        n = "\r\n" if self.linefeeds else "\r"

        resp += n + ">"

        if self.echo:
            resp = self.cmd + n + resp

        print("write:", repr(resp))

        return os.write(self.master_fd, resp.encode())


    def validate(self, cmd):

        if not re.match(self.ELM_VALID_CHARS, cmd):
            return False

        # TODO: more tests

        return True


    def handle(self, cmd):
        """ handles all commands """

        cmd = self.sanitize(cmd)

        print("handling:", repr(cmd))

        if re.match(self.ELM_AT, cmd):
            if re.match(self.ELM_ECHO, cmd):
                self.echo = (cmd[3] == '1')
                print("set ECHO %s" % self.echo)
                return self.ELM_OK
            elif re.match(self.ELM_HEADERS, cmd):
                self.headers = (cmd[3] == '1')
                print("set HEADERS %s" % self.headers)
                return self.ELM_OK
            elif re.match(self.ELM_LINEFEEDS, cmd):
                self.linefeeds = (cmd[3] == '1')
                print("set LINEFEEDS %s" % self.linefeeds)
                return self.ELM_OK
            else:
                pass
        else:
            pass

        return ""


    def sanitize(self, cmd):
        cmd = cmd.replace(" ", "")
        cmd = cmd.upper()
        return cmd


    def set_defaults(self):
        """ returns all settings to their defaults """
        self.echo = True
        self.headers = True
        self.linefeeds = True
