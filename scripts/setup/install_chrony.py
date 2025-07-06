#!/usr/bin/python3
if __name__ == "__main__":
	raise Exception(
		"This python script cannot be executed individually, please use main.py"
	)

import os
import sys
import subprocess
import signal
from core.signal_handlers.sigint import graceful_exit
from core.debian.apt import apt_install
from core.format.colors import print_c, bcolors


def main(**kwargs):
	signal.signal(signal.SIGINT, graceful_exit)
	try:
		ec = subprocess.check_call(
			"dpkg -l chrony".split(),
			stdout=open(os.devnull, "wb"),
			stderr=subprocess.STDOUT,
		)
		if ec == 0:
			print_c(bcolors.L_GREEN, "Chrony is already installed.")
			sys.exit(0)
	except:
		pass

	apt_install(packages=["chrony"], force_yes=True)
