#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###########################################################################
# ELM327-emulator
# TASK PLUGIN: UDS erase_mem_result
# ELM327 Emulator for testing software interfacing OBDII via ELM327 adapter
# https://github.com/Ircama/ELM327-emulator
# (C) Ircama 2021 - CC-BY-NC-SA-4.0
###########################################################################

from elm import Tasks
import time

EXECUTION_TIME = 0.5 # seconds


# UDS - MODE 31 03 - RoutineControl SF (SID=31, routineControlType 03=Request Routine Result)
# FF 00, erase_memory (RID)
class Task(Tasks):
    def run(self, cmd, *_):
        if time.time() < self.time_started + EXECUTION_TIME:
            # 7F=Negative Response, SID 31, 78=requestCorrectlyReceived-ResponsePending
            return (self.AW('7F 31 78'),
                    self.TASK.CONTINUE,
                    None if self.task_request_matched(cmd) else cmd)
        else:
            return (self.AW('71 03 FF 00 00'), # Positive Response (SID + 40 hex)
                    self.TASK.TERMINATE,
                    None if self.task_request_matched(cmd) else cmd)
