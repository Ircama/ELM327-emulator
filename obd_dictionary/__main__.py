#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###########################################################################
# ELM327-emulator obd_dictionary
# ELM327 Emulator for testing software interfacing OBDII via ELM327 adapter
# https://github.com/Ircama/ELM327-emulator
# (C) Ircama 2021 - CC-BY-NC-SA-4.0
###########################################################################

import sys
try:
    from . import main
except (ImportError, ValueError):
    print("obd_dictionary must be run as a module."
          "E.g., python3 -m obd_dictionary")
    sys.exit(1)

if __name__ == "__main__":
    main()
