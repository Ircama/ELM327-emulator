#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###########################################################################
# ELM327-emulator
# TASK PLUGIN: UDS write_vin
# ELM327 Emulator for testing software interfacing OBDII via ELM327 adapter
# https://github.com/Ircama/ELM327-emulator
# (C) Ircama 2021 - CC-BY-NC-SA-4.0
###########################################################################

from elm import Tasks


# UDS - MODE 2E - writeDataByIdentifier Service (Appl. Inc.)
# F190, write_VIN
class Task(Tasks):
    def run(self, length, frame, cmd):
        ret = self.multiline_request(length, frame, cmd)
        if ret is False:
            return (ret, self.TASK.TERMINATE, self.PROCESS.DONT_PROCESS)
        if ret is None:
            return (ret, self.TASK.CONTINUE, self.PROCESS.DONT_PROCESS)
        if ret[:6] == '2EF190':  # Write VIN
            self.logging.warning('Decoded VIN: %s',
                                 repr(bytearray.fromhex(ret[6:]).decode()))
            return (self.HD(self.answer) + self.SZ('03') +
                    self.DT('6E F1 90'),  # WDBI message-SF response
                    self.TASK.TERMINATE,
                    self.PROCESS.DONT_PROCESS)
        else:
            return (ret,
                    self.TASK.TERMINATE,
                    self.PROCESS.DO_PROCESS)
