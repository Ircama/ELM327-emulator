#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###########################################################################
# ELM327-emulator
# TASK PLUGIN: UDS task_mt05_write_mem_addr
# ELM327 Emulator for testing software interfacing OBDII via ELM327 adapter
# https://github.com/Ircama/ELM327-emulator
# (C) Ircama 2021 - CC-BY-NC-SA-4.0
###########################################################################

from elm import Tasks
import mmap


# UDS - MODE 3D - Write memory by address
class Task(Tasks):
    def run(self, cmd, *_):
        if not (hasattr(self.shared, 'mmap')):
            self.shared.mmap = mmap.mmap(-1, 0xffffff)
        try:
            address = int(cmd[2:8], 16)
        except Exception as e:
            self.logging.error(
                'Write memory by address - wrong request: %s', e)
            return Task.TASK.ERROR
        if not (hasattr(self.shared, 'min_addr')):
            self.shared.min_addr = address
        elif self.shared.min_addr > address:
            self.shared.min_addr = address
        data = cmd[8:]
        try:
            length = len(bytearray.fromhex(data))
            max_addr = address + length
            self.shared.mmap[address:max_addr] = bytearray.fromhex(data)
        except KeyError as e:
            self.logging.error(
                'Write memory by address - Invalid data: %s', e)
            return Task.TASK.ERROR
        if not (hasattr(self.shared, 'max_addr')):
            self.shared.max_addr = max_addr
        elif self.shared.max_addr < max_addr:
            self.shared.max_addr = max_addr
        return Task.TASK.ANSWER(self.PA(cmd[2:8].strip()))
