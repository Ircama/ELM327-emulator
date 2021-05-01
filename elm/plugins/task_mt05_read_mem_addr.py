#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###########################################################################
# ELM327-emulator
# TASK PLUGIN: UDS task_mt05_read_mem_addr
# ELM327 Emulator for testing software interfacing OBDII via ELM327 adapter
# https://github.com/Ircama/ELM327-emulator
# (C) Ircama 2021 - CC-BY-NC-SA-4.0
###########################################################################
import time

from elm import Tasks
import mmap

MEM_RANGE = 0x3fffff
MMAP_INPUT_FILE = "mmap-input.bin"
EDIT_INPUT_MMAP_FILE = True


# UDS - MODE 23 - Read memory by address
class Task(Tasks):
    def run(self, cmd, *_):
        if not (hasattr(self.shared, 'read_mmap')):
            try:
                with open(MMAP_INPUT_FILE, "r+b") as f:
                    self.shared.read_mmap = mmap.mmap(
                        f.fileno(),
                        MEM_RANGE if EDIT_INPUT_MMAP_FILE else 0)
            except Exception as e:
                self.logging.critical('Error while opening file "%s": %s',
                                      MMAP_INPUT_FILE, e)
                return Task.RETURN.ERROR
        try:
            address = int(cmd[2:-2], 16) & MEM_RANGE
            length = int(cmd[-2:], 16)
        except Exception as e:
            self.logging.error(
                'Read memory by address - wrong request: %s', e)
            return Task.RETURN.ERROR
        try:
            value = self.shared.read_mmap[address:address + length]
        except KeyError as e:
            self.logging.error('Read memory by address - '
                               'Unhandled data address %s (%s)',
                               e, cmd[2:-2])
            return Task.RETURN.ANSWER(self.NA('12')) # Sub-function not supported
        if len(value) != length:
            self.logging.error('Read memory by address - Memory map '
                               '%s does not match with length %s, %s',
                               value, length, len(value))
            return Task.RETURN.ERROR
        data = ' '.join('{:02x}'.format(x) for x in value).upper()
        if (hasattr(self.shared, 'fail_next_read_mem') and
                self.shared.fail_next_read_mem):
            self.logging.info(
                'Just executed routine %s.', self.shared.fail_next_read_mem)
            self.shared.fail_next_read_mem = False
            time.sleep(0.3)
        return Task.RETURN.ANSWER(self.PA(data.strip()))
