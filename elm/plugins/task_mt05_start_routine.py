#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###########################################################################
# ELM327-emulator
# TASK PLUGIN: UDS task_mt05_start_routine
# ELM327 Emulator for testing software interfacing OBDII via ELM327 adapter
# https://github.com/Ircama/ELM327-emulator
# (C) Ircama 2021 - CC-BY-NC-SA-4.0
###########################################################################

from elm import Tasks

MEM_RANGE = 0x3fffff


# UDS - MODE 31 01 - UDS Routine Control (31): Start (01)
class Task(Tasks):
    def run(self, cmd, *_):
        # Extract start_address and end_address from the request
        try:
            start_address = int(cmd[4:10], 16) & MEM_RANGE
            end_address = int(cmd[10:16], 16) & MEM_RANGE
        except Exception as e:
            self.logging.error(
                'Start routine - wrong address: %s', e)
            return Task.RETURN.ERROR
        self.logging.info('Start routine %s to %s',
                          hex(start_address), hex(end_address))

        # Terminate the task returning a positive answer
        return Task.RETURN.ANSWER(self.PA('00'))
