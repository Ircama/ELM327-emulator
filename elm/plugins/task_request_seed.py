#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###########################################################################
# ELM327-emulator
# TASK PLUGIN: UDS request_seed
# ELM327 Emulator for testing software interfacing OBDII via ELM327 adapter
# https://github.com/Ircama/ELM327-emulator
# (C) Ircama 2021 - CC-BY-NC-SA-4.0
###########################################################################

from elm import Tasks
import time

EXECUTION_TIME = 0.5 # seconds
SEED = 'A641B5E9'


# UDS - MODE 27 - Security Access - 11=request seed
class Task(Tasks):
    def run(self, length, frame, cmd):
        ret = self.multiline_request(length, frame, cmd)
        if ret is False:
            return (None, self.TASK.TERMINATE, None)
        if ret is None:
            return (None, self.TASK.CONTINUE, None)
        if time.time() < self.time_started + EXECUTION_TIME:
            # 7F=Negative Response, SID 27, 78=requestCorrectlyReceived-ResponsePending
            return (self.HD(self.answer) + self.SZ('03') +
                    self.DT('7F 27 78'),
                    self.TASK.CONTINUE,
                    None if self.task_request_matched(ret) else cmd)
        else:
            seed_bytes = " ".join(SEED[i:i + 2] for i in range(0, len(SEED), 2))
            self.logging.warning('Seed: %s', seed_bytes)
            return (self.HD(self.answer) + self.SZ('06') +
                    self.DT('67 11 ' + seed_bytes), # Positive answer =SID 27 + 40 hex, subfunction 11
                    self.TASK.TERMINATE,
                    None if self.task_request_matched(ret) else cmd)
