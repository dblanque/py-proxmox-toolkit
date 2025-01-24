#!/usr/bin/env python3
if __name__ == "__main__":
	raise Exception("This python script cannot be executed individually, please use main.py")

from core.network.interfaces import get_interfaces, PHYSICAL_INTERFACE_PATTERNS, VIRTUAL_INTERFACE_PATTERNS, VIRTUAL_BRIDGE_PATTERNS
from core.format.colors import bcolors, print_c
from core.parser import make_parser, ArgumentParser
from core.templates.udev.overrides import UDEV_BY_MAC_ADDRESS
from core.validators.mac import mac_address_validator
import subprocess, os

def argparser(**kwargs) -> ArgumentParser:
	parser = make_parser(
		prog="Proxmox VE Physical Network Interface Pinning Script",
		description="This program is used to pin network interfaces to their corresponding MAC Address and/or Serial Number.",
		**kwargs
	)
	parser.add_argument("-p", "--print", help="Print data instead of writing to UDEV Link Files.", action="store_true")
	parser.add_argument("-v", "--verbose", action="store_true")
	return parser

def main(argv_a):
	UDEV_PATH = "/etc/systemd/network"
	print_c(bcolors.L_YELLOW, "Scanning Network Interfaces.")
	regex_list = list(PHYSICAL_INTERFACE_PATTERNS)

	interfaces = get_interfaces(
		interface_patterns=regex_list,
		verbose=argv_a.verbose
	)
	for iface_name in interfaces:
		iface_mac_addr = None
		udev_link_name = os.path.join(UDEV_PATH, f"10-{iface_name}.link")
		mac_addr_subprocess = subprocess.Popen(f"cat /sys/class/net/{iface_name}/address".split(),
			stdout=subprocess.PIPE, 
			stderr=subprocess.PIPE,
		)
		out, err = mac_addr_subprocess.communicate()
		returncode = mac_addr_subprocess.returncode
		if returncode == 0:
			iface_mac_addr = out.decode("utf-8").strip()
		if mac_address_validator(iface_mac_addr):
			print(f"Interface {iface_name} will be pinned with MAC Address {iface_mac_addr}")
			if os.path.isfile(udev_link_name):
				print(f"UDEV Link File {udev_link_name} for Interface {iface_name} already exists, skipping.")
				continue
			
			data = UDEV_BY_MAC_ADDRESS.format(
				iface_name=iface_name,
				iface_mac_addr=iface_mac_addr
			).strip()
			if argv_a.print:
				print(f"Showing UDEV Link Template {udev_link_name} for Interface {iface_name}.")
				print(data)
			else:
				with open(udev_link_name, "w") as iface_udev_link:
					print(f"Writing UDEV Link File {udev_link_name} for Interface {iface_name}.")
					iface_udev_link.write(data)
					print(f"UDEV Link Written.")

		print_c(bcolors.NC, f"You may execute the command {bcolors.L_YELLOW}systemctl restart systemd-udev-trigger{bcolors.NC} to refresh the Interface UDEV Links.")


