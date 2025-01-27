#!/usr/bin/env python3
if __name__ == "__main__":
	raise Exception("This python script cannot be executed individually, please use main.py")

import os
import sys
import subprocess
import signal
from core.signal_handlers.sigint import graceful_exit
from core.format.colors import print_c, bcolors
from core.parser import make_parser, ArgumentParser
signal.signal(signal.SIGINT, graceful_exit)

def argparser(**kwargs) -> ArgumentParser:
	parser = make_parser(
		prog="Useful Tools Installation Script",
		description="This program is used to install system administration tools that might be useful long term.",
		**kwargs
	)
	parser.add_argument('-l', '--light', action="store_true")
	return parser

def main(argv_a):
	already_installed = []
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
	if not argv_a.light:
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
		subprocess.check_call(
			"apt-get update -y".split(),
			stdout=open(os.devnull, 'wb'),
			stderr=subprocess.STDOUT
		)
	except subprocess.CalledProcessError as e:
		print_c(bcolors.L_RED, f"Could not do apt update (non-zero exit status {e.returncode}).")
		sys.exit(0)

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
				already_installed.append(pkg)
		except: pass

	print(f"{bcolors.L_YELLOW}The following packages will be installed:{bcolors.NC}")
	for package in tools:
		print(f"\t- {package}")

	print(f"{bcolors.L_GREEN}The following packages are already installed:{bcolors.NC}")
	for package in already_installed:
		print(f"\t- {package}")

	try:
		subprocess.call("apt-get install".split() + tools)
	except: raise
