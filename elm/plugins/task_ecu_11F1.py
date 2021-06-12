#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###########################################################################
# ELM327-emulator
# ECU TASK PLUGIN: UDS task_ecu_11F1 (xx11F1 header)
# ELM327 Emulator for testing software interfacing OBDII via ELM327 adapter
# https://github.com/Ircama/ELM327-emulator
# (C) Ircama 2021 - CC-BY-NC-SA-4.0
###########################################################################

from elm import Tasks, EcuTasks
import mmap

MEM_RANGE = 0x3fffff
MMAP_INPUT_FILE = "mmap-input.bin"
MMAP_OUTPUT_FILE = "mmap-output.bin"
EDIT_INPUT_MMAP_FILE = True


# 11F1 ECU task
class Task(EcuTasks):
    def start(self, cmd, *_):
        # The first time the task is instanced, open the memory map file(s)
        try:
            with open(MMAP_INPUT_FILE, "r+b") as f:
                self.shared.read_mmap = mmap.mmap(
                    f.fileno(),
                    MEM_RANGE if EDIT_INPUT_MMAP_FILE else 0)
        except Exception as e:
            self.logging.critical('Error while opening file "%s": %s',
                                  MMAP_INPUT_FILE, e)
            return Tasks.RETURN.TASK_CONTINUE(cmd)

        if EDIT_INPUT_MMAP_FILE:
            self.shared.mmap = self.shared.read_mmap
        else:
            try:
                with open(MMAP_OUTPUT_FILE, 'w'):
                    pass  # create and reset the output file
                with open(MMAP_OUTPUT_FILE, "r+b") as f:
                    self.shared.mmap = mmap.mmap(f.fileno(), MEM_RANGE)
            except Exception as e:
                self.logging.critical('Error while writing file "%s": %s',
                                      MMAP_OUTPUT_FILE, e)
        return Tasks.RETURN.TASK_CONTINUE(cmd)

    def stop(self, cmd, *_):
        self.auth_successful = False
        return Tasks.RETURN.TASK_CONTINUE(cmd)
