#!/usr/bin/env python3
if __name__ == "__main__":
	raise Exception("This python script cannot be executed individually, please use main.py")

import os, sys, subprocess, signal, argparse
from core.signal_handlers.sigint import graceful_exit
from core.format.colors import print_c, bcolors
signal.signal(signal.SIGINT, graceful_exit)

def argparser():
	parser = argparse.ArgumentParser(
		prog="Useful Tools Installation Script",
		description="This program is used to install system administration tools that might be useful long term."
	)
	parser.add_argument('-l', '--light', action="store_true")
	return parser

def main(argv_a):
	tools = [
		"sudo",
		"net-tools",
		"lvm2",
		"xfsprogs",
		"aptitude",
		"htop",
		"iotop",
		"locate",
		"lshw",
		"git",
	]
	if argv_a.light:
		tools = tools + [
			"cifs-utils",
			"bmon",
			"ethtool",
			"rename",
			"iptraf-ng",
			"nmap",
			"arping",
			"sysstat",
		]
		
	try: 
		ec = subprocess.check_call(
				"apt-get update -y".split(),
				stdout=open(os.devnull, 'wb'),
				stderr=subprocess.STDOUT
			)
		print(ec)
		if ec != 0:
			print_c(bcolors.L_RED, f"Could not do apt update (exited with error code {ec}).")
			sys.exit(0)
	except: pass

	for pkg in tools:
		try:
			ec = subprocess.check_call(
				f"dpkg -l {pkg}".split(),
				stdout=open(os.devnull, 'wb'),
				stderr=subprocess.STDOUT
			)
			if ec == 0:
				print_c(bcolors.L_GREEN, f"{pkg} is already installed.")
				tools.remove(pkg)
		except: pass

	try:
		subprocess.call(f"apt-get install".split() + tools)
	except: raise
