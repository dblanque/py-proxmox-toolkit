#!/usr/bin/env python3
if __name__ == "__main__":
	raise Exception("This python script cannot be executed individually, please use main.py")

import os, sys, subprocess, signal
from core.signal_handlers.sigint import graceful_exit
signal.signal(signal.SIGINT, graceful_exit)

def main():
	chrony_installed = subprocess.check_call(
		"dpkg -l chrony".split(),
		stdout=open(os.devnull, 'wb'),
		stderr=subprocess.STDOUT
	) == 0

	if not chrony_installed:
		try:
			subprocess.call("apt-get update -y".split())
			subprocess.call("apt-get install chrony -y".split())
		except: raise
