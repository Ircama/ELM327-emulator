#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###########################################################################
# ELM327-emulator
# TASK PLUGIN: UDS write_fingerprint
# ELM327 Emulator for testing software interfacing OBDII via ELM327 adapter
# https://github.com/Ircama/ELM327-emulator
# (C) Ircama 2021 - CC-BY-NC-SA-4.0
###########################################################################

from elm import Tasks

# UDS - MODE 2E - writeDataByIdentifier Service (Appl. Inc.)
# F15A, write_fingerprint
class Task(Tasks):
    def run(self, length, frame, cmd):
        ret = self.multiline_request(length, frame, cmd)
        if ret is False:
            return (ret, self.TASK.TERMINATE, self.PROCESS.DONT_PROCESS)
        if ret is None:
            return (ret, self.TASK.CONTINUE, self.PROCESS.DONT_PROCESS)
        if ret[:6] == '2EF15A': # Write Fingerprint
            self.logging.warning('Decoded fingerprint: %s', ret[6:])
            return (self.HD(self.answer) + self.SZ('03') + self.DT('6E F1 5A'),
                    self.TASK.TERMINATE,
                    self.PROCESS.DONT_PROCESS)
        else:
            self.logging.error('Invalid data %s', self.req)
            return (ret, self.TASK.TERMINATE, self.PROCESS.DO_PROCESS)
