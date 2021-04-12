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
            return (None, self.TASK.TERMINATE, None)
        if ret is None:
            return (None, self.TASK.CONTINUE, None)
        if self.task_request_matched(ret):
            self.logging.warning('Decoded VIN: %s',
                                 repr(bytearray.fromhex(ret[6:]).decode()))
            return (self.HD(self.answer) + self.SZ('03') +
                    self.DT('6E F1 90'),  # WDBI message-SF positive response (6E=2E (SID) + 40 hex)
                    self.TASK.TERMINATE,
                    None)
        else:
            return (None, self.TASK.TERMINATE, cmd)
