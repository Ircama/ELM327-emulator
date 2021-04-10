#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###########################################################################
# ELM327-emulator
# TASK PLUGIN: UDS erase_memory
# ELM327 Emulator for testing software interfacing OBDII via ELM327 adapter
# https://github.com/Ircama/ELM327-emulator
# (C) Ircama 2021 - CC-BY-NC-SA-4.0
###########################################################################

from elm import Tasks
import time

# UDS - MODE 31 01 - RoutineControl SF
# FF 00, erase_memory
class Task(Tasks):
    def run(self, length, frame, cmd):
        ret = self.multiline_request(length, frame, cmd)
        if ret is False or ret is None:
            return ret
        if not ('counter' in dir(self)):
            self.counter = 0
        self.counter += 1
        time.sleep(0.2)
        if self.counter > 4:
            return (self.HD(self.answer) + self.SZ('05') +
                    self.DT('71 01 FF 00 00'), self.TASK_TERMINATE) # positive answer
        if ret[:8] == '3101FF00': # erase_memory
            self.logging.warning('Data: %s', ret)
            return (self.HD(self.answer) + self.SZ('03') + self.DT('7F 31 78'),
                    self.TASK_CONTINUE)
        if ret[:8] == '3103FF00':
            return (self.HD(self.answer) + self.SZ('03') + self.DT('7F 31 78'),
                    self.TASK_CONTINUE)
        if ret[:4] == '3E80': # TesterPresent message-SF
            return (self.HD(self.answer) + self.SZ('03') + self.DT('7F 31 78'),
                    self.TASK_CONTINUE)
        return None
