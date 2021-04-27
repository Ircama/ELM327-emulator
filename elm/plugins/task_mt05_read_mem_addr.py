#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###########################################################################
# ELM327-emulator
# TASK PLUGIN: UDS task_mt05_read_mem_addr
# ELM327 Emulator for testing software interfacing OBDII via ELM327 adapter
# https://github.com/Ircama/ELM327-emulator
# (C) Ircama 2021 - CC-BY-NC-SA-4.0
###########################################################################

from elm import Tasks

mt05_memory_map = {
0xC00000: 'FA ',
0xC03F00: '00 00 00 00 30 01 AE 1E F5 39 31 35 36 30 30 37 '
          '34 39 31 35 36 30 30 37 34 01 AF 4C 1A 00 00 00 ',
0xC05000: '31 30 53 48 37 32 31 31 04 0F 00 00 00 00 00 00 ',
#0xC05000: '42 4A 32 35 30 31 38 46',
0xC1FFE0: '0F 00 04 00 04 0F 68 74 30 30 37 72 31 35 30 34 '
          '00 00 00 00 32 38 30 39 37 33 34 34 00 00 11 34 ',
0xC1FFF0: '00 00 00 00 32 38 30 39'
}


# UDS - MODE 23 - Read memory by address
class Task(Tasks):
    def run(self, cmd, *_):
        try:
            address = int(cmd[2:-2], 16)
            length = int(cmd[-2:], 16)
        except Exception as e:
            self.logging.error('Read memory by address - wrong request: %s', e)
            return Task.TASK.ERROR
        try:
            value = mt05_memory_map[address][:length * 3]
        except KeyError as e:
            self.logging.error('Unhandled data address %s (%s)', e, cmd[2:-2])
            return Task.TASK.ANSWER(self.NA('12')) # Subfunction not supported
        if len(value)/3 != length:
            self.logging.error('Memory map %s does not match with length %s',
                               value, length)
            return Task.TASK.ERROR
        if (hasattr(self.shared, 'fail_next_read_mem') and
                self.shared.fail_next_read_mem):
            self.shared.fail_next_read_mem = False
            return Task.TASK.ERROR
        else:
            return Task.TASK.ANSWER(self.PA(value.strip()))
