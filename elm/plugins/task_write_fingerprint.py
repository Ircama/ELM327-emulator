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
    def run(self, cmd):
        if self.task_request_matched(cmd): # Write Fingerprint
            self.logging.warning('Decoded fingerprint: %s', cmd[6:])
            return (self.HD(self.answer) + self.SZ('03') + self.DT('6E F1 5A'),
                    self.TASK.TERMINATE, # 6E = 2E (SID) + 40 hex (positive answer)
                    None)
        else:
            self.logging.error('Invalid data %s', self.req)
            return (None, self.TASK.TERMINATE, cmd)
