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

MEM_RANGE = 0x3fffff
MMAP_INPUT_FILE = "mmap-input.bin"
MMAP_OUTPUT_FILE = "mmap-output.bin"
EDIT_INPUT_MMAP_FILE = True


# UDS - MODE 3D - Write memory by address
class Task(Tasks):
    def run(self, cmd, *_): # cmd includes the request data

        # The first time the task is instanced, open the memory map file
        if EDIT_INPUT_MMAP_FILE:
            mmap_file = MMAP_INPUT_FILE
        else:
            mmap_file = MMAP_OUTPUT_FILE
        if not (hasattr(self.shared, 'mmap')):
            try:
                if not EDIT_INPUT_MMAP_FILE:
                    with open(mmap_file, 'w'):
                        pass # create and reset output file
                with open(mmap_file, "r+b") as f:
                    self.shared.mmap = mmap.mmap(f.fileno(), MEM_RANGE)
            except Exception as e:
                self.logging.critical('Error while writing file "%s": %s',
                                      mmap_file, e)
                return Task.RETURN.ERROR

        # Extract the byte vector and the address from the request
        try:
            byte_vector = bytearray.fromhex(cmd[8:])
            address = int(cmd[2:8], 16) & MEM_RANGE
        except Exception as e:
            self.logging.error(
                'Write memory by address - wrong request: %s', e)
            return Task.RETURN.ERROR

        # Compute max_addr
        max_addr = address + len(byte_vector)

        # Execute the command: write bytes to the memory map in the shared area
        try:
            self.shared.mmap[address:max_addr] = byte_vector
        except KeyError as e:
            self.logging.error(
                'Write memory by address - Invalid write operation: %s', e)
            return Task.RETURN.ERROR

        # Update min_addr in the shared area (for statistics)
        if not (hasattr(self.shared, 'min_addr')):
            self.shared.min_addr = address
        elif self.shared.min_addr > address:
            self.shared.min_addr = address

        # Update max_addr in the shared area (for statistics)
        if not (hasattr(self.shared, 'max_addr')):
            self.shared.max_addr = max_addr
        elif self.shared.max_addr < max_addr:
            self.shared.max_addr = max_addr

        # Terminate the task returning a positive answer
        return Task.RETURN.ANSWER(self.PA(cmd[2:8].strip()))
