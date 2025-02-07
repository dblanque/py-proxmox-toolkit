#!/usr/bin/python3
if __name__ == "__main__":
	raise Exception("This python script cannot be executed individually, please use main.py")

import subprocess
import logging
from core.format.colors import bcolors, print_c
from core.parser import make_parser, ArgumentParser
logger = logging.getLogger(__name__)

def argparser(**kwargs) -> ArgumentParser:
	parser = make_parser(
		prog='Interface Status Fetcher',
		description='Gets interface status with ip binary',
		**kwargs
	)
	parser.add_argument('interface')
	return parser

def get_iface_status(iface_name):
	IP_ARGS=[
		"/usr/sbin/ip",
		"link",
		"show",
		iface_name
	]
	with subprocess.Popen(IP_ARGS, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as ip_proc:
		output: list[str] = []
		errors: list[str] = []
		for l_out in ip_proc.stdout:
			output.append(l_out.decode('utf-8').strip())
		for l_err in ip_proc.stderr:
			errors.append(l_err.decode('utf-8').strip())
	iface_status_line = None
	for l in errors:
		if "does not exist" in l:
			raise ValueError(f"Interface {iface_name} does not exist")
	for l in output:
		if "state" in l:
			iface_status_line = l.split(" ")
	iface_status = iface_status_line[iface_status_line.index("state") + 1].strip()
	return iface_status

def main(argv_a, **kwargs):
	status = get_iface_status(argv_a.interface)
	if status == "UP":
		print_c(bcolors.L_GREEN, status)
	elif status == "DOWN":
		print_c(bcolors.L_RED, status)
	else:
		print_c(bcolors.L_BLUE, status)
