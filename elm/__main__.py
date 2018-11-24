import threading

from .elm import ELM
import time

e = ELM(None, None)

with e as pts_name:
    print("Running on %s" % pts_name)
    try:
        while True:
          if threading.active_count() > 1:
              time.sleep(0.5)
          else:
              break
    except (KeyboardInterrupt, SystemExit):
        print('\n\nExiting.\n')