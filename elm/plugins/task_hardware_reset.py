#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###########################################################################
# ELM327-emulator
# TASK PLUGIN: UDS hardware_reset
# ELM327 Emulator for testing software interfacing OBDII via ELM327 adapter
# https://github.com/Ircama/ELM327-emulator
# (C) Ircama 2021 - CC-BY-NC-SA-4.0
###########################################################################

from elm import Tasks
import time

EXECUTION_TIME = 0.5 # seconds

# UDS - MODE 11 - ECU Reset - hardReset
class Task(Tasks):
    def run(self, length, frame, cmd):
        ret = self.multiline_request(length, frame, cmd)
        if ret is False:
            return (ret, self.TASK.TERMINATE, self.PROCESS.DONT_PROCESS)
        if ret is None:
            return (ret, self.TASK.CONTINUE, self.PROCESS.DONT_PROCESS)
        if time.time() < self.time_started + EXECUTION_TIME:
            # 7F=Negative Response, SID 11, 78=requestCorrectlyReceived-ResponsePending
            return (self.HD(self.answer) + self.SZ('03') +
                    self.DT('7F 11 78'),
                    self.TASK.CONTINUE,
                    ret[:4] != '1101')
        else:
            return (self.HD(self.answer) + self.SZ('02') +
                    self.DT('51 01'), # positive response: SID=11 + 40 hex
                    self.TASK.TERMINATE,
                    ret[:8] != '1101')
