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
        # Start routine procedure
        if hasattr(self.shared, 'mmap'):
            del self.shared.mmap
        if hasattr(self.shared, 'min_addr'):
            del self.shared.min_addr
        if hasattr(self.shared, 'max_addr'):
            del self.shared.max_addr
        try:
            start_address = int(cmd[4:10], 16) & MEM_RANGE
            end_address = int(cmd[10:16], 16) & MEM_RANGE
        except Exception as e:
            self.logging.error(
                'Start routine - wrong address: %s', e)
            return Task.TASK.ERROR
        self.logging.info('Start routine %s to %s',
                          hex(start_address), hex(end_address))
        return Task.TASK.ANSWER(self.PA('00'))
