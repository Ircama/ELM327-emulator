#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###########################################################################
# ELM327-emulator
# TASK PLUGIN: UDS task_mt05_stop_routine
# ELM327 Emulator for testing software interfacing OBDII via ELM327 adapter
# https://github.com/Ircama/ELM327-emulator
# (C) Ircama 2021 - CC-BY-NC-SA-4.0
###########################################################################

from elm import Tasks


# UDS - MODE 31 02 - UDS Routine Control (31): Stop (02)
class Task(Tasks):
    def run(self, cmd, *_):

        # Check that all shared data have been created by the previous tasks
        if (not hasattr(self.shared, 'mmap') or
                not hasattr(self.shared, 'mmap') or
                not hasattr(self.shared, 'min_addr') or
                not hasattr(self.shared, 'max_addr')):
            self.logging.error('Stop routine - improper workflow')
            return Task.RETURN.ERROR

        # Log statistics
        self.logging.info(
            'Written data size: '
            '%s (%s), %s (%s) to %s (%s).',
            self.shared.max_addr - self.shared.min_addr,
            hex(self.shared.max_addr - self.shared.min_addr),
            self.shared.min_addr, hex(self.shared.min_addr),
            self.shared.max_addr, hex(self.shared.max_addr))

        # Terminate the task returning a positive answer
        return Task.RETURN.ANSWER(self.PA(''))
