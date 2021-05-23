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

MEM_RANGE = 0x3fffff


# UDS - MODE 23 - Read memory by address
class Task(Tasks):
    def run(self, cmd, *_): # cmd includes the request data

        # Extract the address and the number of bytes to read from the request
        try:
            address = int(cmd[2:-2], 16) & MEM_RANGE
            length = int(cmd[-2:], 16)
        except Exception as e:
            self.logging.error(
                'Read memory by address - wrong request: %s', e)
            return Task.RETURN.ERROR

        # Execute the command: read bytes to the memory map in the shared area
        try:
            vector = self.shared.read_mmap[address:address + length]
        except KeyError as e:
            self.logging.error('Read memory by address - '
                               'Unhandled data address %s (%s)',
                               e, cmd[2:-2])
            return Task.RETURN.ANSWER(self.NA('12')) # Sub-function not supported

        # Check that the number of saved bytes matches the length in the request
        if len(vector) != length:
            self.logging.error('Read memory by address - Memory map '
                               '%s does not match with length %s, %s',
                               vector, length, len(vector))
            return Task.RETURN.ERROR

        # Generate the hex bytestring
        data = ' '.join('{:02x}'.format(x) for x in vector).upper()

        # Add a delay if "executed_routine" is set (and log a message)
        if (hasattr(self.shared, 'executed_routine') and
                self.shared.executed_routine):
            self.logging.info(
                'Just executed routine %s.', self.shared.executed_routine)
            self.shared.executed_routine = False
            time.sleep(0.3)

        # Terminate the task returning a positive answer
        return Task.RETURN.ANSWER(self.PA(data.strip()))
