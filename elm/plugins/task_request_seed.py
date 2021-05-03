#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###########################################################################
# ELM327-emulator
# TASK PLUGIN: UDS task_request_seed
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
    def run(self, cmd, *_):
        if time.time() < self.time_started + EXECUTION_TIME:
            # 78 in negative answer = requestCorrectlyReceived-ResponsePending
            return (self.NA('78'),
                    Tasks.RETURN.CONTINUE,
                    None if self.task_request_matched(cmd) else cmd)
        else:
            seed_bytes = " ".join(SEED[i:i + 2] for i in range(0, len(SEED), 2))
            self.logging.warning('Seed: %s', seed_bytes)
            return (self.PA(seed_bytes),
                    Tasks.RETURN.TERMINATE,
                    None if self.task_request_matched(cmd) else cmd)
