#!/usr/bin/env python3
# TODO - Finish this script
if __name__ == "__main__":
	raise Exception("This python script cannot be executed individually, please use main.py")

import signal
import os
import sys
from core.parser import make_parser, ArgumentParser
from core.utils.grep import grep_r
from core.validators.ipaddress import validate_ip
from core.validators.port import validate_port
from core.signal_handlers.sigint import graceful_exit
from core.format.colors import bcolors, print_c
from core.utils.prompt import yes_no_input

def argparser(**kwargs) -> ArgumentParser:
	parser = make_parser(
		prog="Script to setup APT Cacher Proxy IP/Port.",
		description="This program is used to configure your apt cacher address and port.",
		**kwargs
	)
	parser.add_argument(
		"-i", "--ignore-existing", 
		help="Ignores if any pre-existing apt cacher configurations exists. Only prints a warning.",
		action="store_true"
	)
	return parser

def is_valid_apt_cacher(value: str):
	split_value = value.rsplit(":", 1)
	if len(split_value) != 2:
		return False
	print(split_value)

	ip_address = split_value[0]
	port = split_value[1]
	if not validate_ip(ip_address):
		print_c(bcolors.L_YELLOW, "Please enter a valid IP Address.")
		return False
	if not validate_port(port):
		print_c(bcolors.L_YELLOW, "Please enter a valid Port.")
		return False
	return True

def main(argv_a, **kwargs):
	signal.signal(signal.SIGINT, graceful_exit)
	if os.geteuid() != 0:
		print_c(bcolors.L_YELLOW, "Script must be executed as root.")
		exit()
	APT_CONF_DIR = "/etc/apt/apt.conf.d"
	files = []
	HTTP_CACHER_REGEX = r'^\s*Acquire::http::Proxy \".*\";'
	HTTPS_CACHER_REGEX = r'^\s*Acquire::https::Proxy \".*\";'
	for f in grep_r(HTTP_CACHER_REGEX, APT_CONF_DIR, return_files=True):
		files.append(f)
	if len(files) > 0:
		print_c(bcolors.L_YELLOW, "APT Cacher Proxy already set in one or more files:")
		for f in files:
			print(f"\t{f}")
		if not argv_a.ignore_existing:
			sys.exit(1)

	apt_cacher = input("Please enter an IP Address and Port for your APT Cacher: ")
	while not is_valid_apt_cacher(apt_cacher):
		apt_cacher = input("Please enter a VALID APT Cacher address:port formatted string: ")
