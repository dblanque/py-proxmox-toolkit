#!/usr/bin/python3
# TODO - Finish this script
if __name__ == "__main__":
	raise Exception(
		"This python script cannot be executed individually, please use main.py"
	)

import signal
import re
import os
import sys
from core.parser import make_parser, ArgumentParser
from core.utils.grep import grep_r
from core.validators.ipaddress import validate_ip
from core.validators.port import validate_port
from core.signal_handlers.sigint import graceful_exit
from core.format.colors import bcolors, print_c
from core.utils.shell import is_user_root

ERR_CACHER_ALREADY_SET = 1
ERR_INVALID_CACHER_ADDRESS = 2


def argparser(**kwargs) -> ArgumentParser:
	parser = make_parser(
		prog="Script to setup APT Cacher Proxy IP/Port.",
		description="This program is used to configure your apt cacher address and port.",
		**kwargs,
	)
	parser.add_argument(
		"-o",
		"--overwrite",
		help="Overwrites pre-existing apt cacher configurations.",
		action="store_true",
	)
	parser.add_argument(
		"-c",
		"--cacher-address",
		help="Sets APT Cacher <address:port> value.",
	)
	parser.add_argument(
		"-s",
		"--https-cacher",
		help="Adds the APT Cacher as an HTTP(S) source as well.",
		action="store_true",
	)
	return parser


def is_valid_apt_cacher(value: str):
	split_value = value.rsplit(":", 1)
	if len(split_value) != 2:
		return False

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
	is_user_root(exit_on_fail=True)
	APT_CONF_DIR = "/etc/apt/apt.conf.d"
	apt_conf_files = []
	HTTP_CACHER_REGEX = re.compile(r"^\s*Acquire::http::Proxy \".*\";")
	HTTPS_CACHER_REGEX = re.compile(r"^\s*Acquire::https::Proxy \".*\";")
	HTTP_CACHER_TEMPLATE = 'Acquire::http::Proxy "http://{0}";'
	HTTPS_CACHER_TEMPLATE = 'Acquire::https::Proxy "https://{0}";'

	for conf_file in grep_r(HTTP_CACHER_REGEX, APT_CONF_DIR, return_files=True):
		apt_conf_files.append(conf_file)

	if argv_a.https_cacher:
		for conf_file in grep_r(HTTPS_CACHER_REGEX, APT_CONF_DIR, return_files=True):
			if not conf_file in apt_conf_files:
				apt_conf_files.append(conf_file)

	if len(apt_conf_files) > 0:
		if not argv_a.overwrite:
			print_c(
				bcolors.L_RED, "APT Cacher Proxy already set in one or more file(s):"
			)
		else:
			print_c(bcolors.L_YELLOW, "Overwriting Proxy in files:")

		for conf_file in apt_conf_files:
			print(f"\t- {conf_file}")

		if not argv_a.overwrite:
			print_c(
				bcolors.L_BLUE,
				"Use -o | --overwrite flag to change in pre-existing file(s).",
			)
			sys.exit(ERR_CACHER_ALREADY_SET)

	if argv_a.cacher_address:
		apt_cacher = argv_a.cacher_address
		if not is_valid_apt_cacher(apt_cacher):
			print_c(bcolors.L_RED, "Invalid APT Cacher Address.")
			sys.exit(ERR_INVALID_CACHER_ADDRESS)
	else:
		apt_cacher = input("Please enter an IP Address and Port for your APT Cacher: ")

	while not is_valid_apt_cacher(apt_cacher):
		apt_cacher = input(
			"Please enter a VALID APT Cacher <address:port> formatted string: "
		)

	HTTP_CACHER_LINE = HTTP_CACHER_TEMPLATE.format(apt_cacher) + "\n"
	HTTPS_CACHER_LINE = HTTPS_CACHER_TEMPLATE.format(apt_cacher) + "\n"

	if argv_a.overwrite and len(apt_conf_files) > 0:
		for conf_file in apt_conf_files:
			lines = None
			lines_rm = []
			with open(conf_file, "r") as file:
				http_found = False
				https_found = False
				lines = file.readlines()
				for idx, ln in enumerate(lines):
					if re.match(HTTP_CACHER_REGEX, ln):
						lines[idx] = HTTP_CACHER_LINE
						http_found = True

					if re.match(HTTPS_CACHER_REGEX, ln):
						if argv_a.https_cacher:
							lines[idx] = HTTPS_CACHER_LINE
							https_found = True
						else:
							lines_rm.append(idx)

				if not http_found:
					lines.append(HTTP_CACHER_LINE)
				if argv_a.https_cacher and not https_found:
					lines.append(HTTPS_CACHER_LINE)
				for ln_idx in lines_rm:
					del lines[ln_idx]

			if not lines:
				raise Exception()

			with open(conf_file, "w") as file:
				for ln in lines:
					file.write(ln)
	else:
		conf_file = os.path.join(APT_CONF_DIR, "99proxy.conf")
		with open(conf_file, "w") as file:
			file.write(HTTP_CACHER_LINE)
			if argv_a.https_cacher:
				file.write(HTTPS_CACHER_LINE)
		print_c(bcolors.L_GREEN, f"Wrote config file at {conf_file}")
