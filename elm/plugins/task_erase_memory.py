#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###########################################################################
# ELM327-emulator
# TASK PLUGIN: UDS erase_memory
# ELM327 Emulator for testing software interfacing OBDII via ELM327 adapter
# https://github.com/Ircama/ELM327-emulator
# (C) Ircama 2021 - CC-BY-NC-SA-4.0
###########################################################################

from elm import Tasks
import time

EXECUTION_TIME = 0.5 # seconds

# UDS - MODE 31 01 - RoutineControl SF (SID=31, routineControlType 01=startRoutine)
# FF 00, erase_memory (RID)
class Task(Tasks):
    def run(self, length, frame, cmd):
        ret = self.multiline_request(length, frame, cmd)
        if ret is False or ret is None:
            return ret
        if ret[:8] == '3101FF00':
            self.logging.warning('Erase memory, Data: %s', ret[8:])
        if time.time() < self.time_started + EXECUTION_TIME:
            # 7F=Negative Response, SID 31, 78=requestCorrectlyReceived-ResponsePending
            return (self.HD(self.answer) + self.SZ('03') +
                    self.DT('7F 31 78'),
                    self.TASK.PROCESS_COMMAND)
        if ret[:2] == '3E' or ret[:8] == '3101FF00': # tester present or erase_memory
            return (self.HD(self.answer) + self.SZ('05') +
                    self.DT('71 01 FF 00 00'),
                    self.TASK.PROCESS_COMMAND) # Positive Response (SID + 40 hex)
        self.logging.error('Invalid request: %s', ret)
        return None
