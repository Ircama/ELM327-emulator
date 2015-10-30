
import elm
import time

e = elm.ELM(None, None)

with e as pts_name:
	print("Running on %s" % pts_name)
	while True:
		time.sleep(1)
