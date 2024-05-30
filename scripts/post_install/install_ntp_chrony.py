#!/usr/bin/env python3
if __name__ != "__main__":
	raise ImportError("This python script cannot be imported.")

import os, sys, subprocess, signal
VENV_DIR = os.path.abspath(os.environ['VIRTUAL_ENV']) or None
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
if not VENV_DIR:
	print(VENV_DIR)
	raise Exception('Could not append VENV_DIR to PATH')
sys.path.append(VENV_DIR)
sys.path.append(SCRIPT_DIR)

def sigint_handler(sig, frame):
	print('\nCtrl+C Received, cancelling script.')
	sys.exit(0)
signal.signal(signal.SIGINT, sigint_handler)

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

if __name__ == "__main__":
	main()