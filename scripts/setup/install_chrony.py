#!/usr/bin/env python3
if __name__ == "__main__":
	raise Exception("This python script cannot be executed individually, please use main.py")

import os
import sys
import subprocess
import signal
from core.signal_handlers.sigint import graceful_exit
from core.format.colors import print_c, bcolors
signal.signal(signal.SIGINT, graceful_exit)

def main(**kwargs):
	try:
		ec = subprocess.check_call(
			"dpkg -l chrony".split(),
			stdout=open(os.devnull, 'wb'),
			stderr=subprocess.STDOUT
		)
		if ec == 0:
			print_c(bcolors.L_GREEN, "Chrony is already installed.")
			sys.exit(0)
	except: pass

	try:
		subprocess.call("apt-get update -y".split())
		subprocess.call("apt-get install chrony -y".split())
	except: raise
