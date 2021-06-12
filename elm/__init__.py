#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###########################################################################
# ELM327-emulator
# ELM327 Emulator for testing software interfacing OBDII via ELM327 adapter
# https://github.com/Ircama/ELM327-emulator
# (C) Ircama 2021 - CC-BY-NC-SA-4.0
###########################################################################

from __future__ import print_function
import sys
if sys.hexversion < 0x3060000:
    print("ELM327-emulator error: Python version must be >= 3.6."
          " Current version: " + ".".join(
              map(str, sys.version_info[:3])) + ".")
    sys.exit(1)

from .elm import Elm
from .interpreter import main
