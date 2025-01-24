#!/usr/bin/env python3
if __name__ == "__main__":
	raise Exception("This python script cannot be executed individually, please use main.py")

from core.network.interfaces import get_interfaces, PHYSICAL_INTERFACE_PATTERNS, VIRTUAL_INTERFACE_PATTERNS, VIRTUAL_BRIDGE_PATTERNS
from core.format.colors import bcolors, print_c
from core.parser import make_parser, ArgumentParser
from core.templates.udev.overrides import UDEV_BY_MAC_ADDRESS
from core.validators.mac import mac_address_validator
import subprocess

def argparser(**kwargs) -> ArgumentParser:
	parser = make_parser(
		prog="Proxmox VE Physical Network Interface Pinning Script",
		description="This program is used to pin network interfaces to their corresponding MAC Address and/or Serial Number.",
		**kwargs
	)
	parser.add_argument("-v", "--verbose", action="store_true")
	return parser

def main(argv_a):
	print_c(bcolors.L_YELLOW, "Scanning Network Interfaces.")
	regex_list = list(PHYSICAL_INTERFACE_PATTERNS)

	interfaces = get_interfaces(
		interface_patterns=regex_list,
		verbose=argv_a.verbose
	)
	for iface_name in interfaces:
		iface_mac_addr = None
		mac_addr_subprocess = subprocess.Popen(f"cat /sys/class/net/{iface_name}/address".split(),
			stdout=subprocess.PIPE, 
			stderr=subprocess.PIPE,
		)
		out, err = mac_addr_subprocess.communicate()
		returncode = mac_addr_subprocess.returncode
		if returncode > 0:
			iface_mac_addr = out.decode("utf-8").strip()
		if mac_address_validator(iface_mac_addr):
			print(f"Interface {iface_name} will be pinned with MAC Address {iface_mac_addr}")

