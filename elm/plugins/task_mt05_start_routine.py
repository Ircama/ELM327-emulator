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


# UDS - MODE 31 01 - UDS Routine Control (31): Start (01)
class Task(Tasks):
    def run(self, cmd, *_):
        if cmd[:4] == '3102': # Routine (31) - Stop (02)
            self.logging.info('Start routine: terminating.')
            return None, Tasks.TASK.TERMINATE, cmd

        # Write memory commands (or any other different from Start and Stop)
        if not self.task_request_matched(cmd):
            return None, Tasks.TASK.CONTINUE, cmd

        # Start routine procedure
        if hasattr(self.shared, 'mmap'):
            del self.shared.mmap
        if hasattr(self.shared, 'min_addr'):
            del self.shared.min_addr
        if hasattr(self.shared, 'max_addr'):
            del self.shared.max_addr
        try:
            start_address = int(cmd[4:10], 16)
            end_address = int(cmd[10:16], 16)
        except Exception as e:
            self.logging.error(
                'Start routine - wrong address: %s', e)
            return Task.TASK.ERROR
        self.logging.info('Start routine %s (%s) to %s (%s)',
                          start_address, cmd[4:10], end_address, cmd[10:16])
        return self.PA('00'), Tasks.TASK.CONTINUE, None
