#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###########################################################################
# ELM327-emulator
# TASK PLUGIN: UDS task_hardware_reset
# ELM327 Emulator for testing software interfacing OBDII via ELM327 adapter
# https://github.com/Ircama/ELM327-emulator
# (C) Ircama 2021 - CC-BY-NC-SA-4.0
###########################################################################

from elm import Tasks
import time

EXECUTION_TIME = 0.5 # seconds


# UDS - MODE 11 - ECU Reset - hardReset
class Task(Tasks):
    def run(self, cmd, *_):
        if time.time() < self.time_started + EXECUTION_TIME:
            # 78 in negative answer = requestCorrectlyReceived-ResponsePending
            return (self.NA('78'),
                    Tasks.RETURN.CONTINUE,
                    None if self.task_request_matched(cmd) else cmd)
        else:
            return (self.PA(''),
                    Tasks.RETURN.TERMINATE,
                    None if self.task_request_matched(cmd) else cmd)
