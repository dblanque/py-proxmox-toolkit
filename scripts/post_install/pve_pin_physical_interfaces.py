#!/usr/bin/env python3
if __name__ == "__main__":
	raise Exception("This python script cannot be executed individually, please use main.py")

from core.network.interfaces import get_interfaces, PHYSICAL_INTERFACE_PATTERNS, VIRTUAL_INTERFACE_PATTERNS, VIRTUAL_BRIDGE_PATTERNS
from core.format.colors import bcolors, print_c
from core.parser import make_parser, ArgumentParser
from core.templates.udev.overrides import UDEV_BY_MAC_ADDRESS, UDEV_BY_PROPERTY
from core.debian.udev import get_inet_udev_info
from core.validators.mac import mac_address_validator
import subprocess, os

def argparser(**kwargs) -> ArgumentParser:
	parser = make_parser(
		prog="Proxmox VE Physical Network Interface Pinning Script",
		description="This program is used to pin network interfaces to their corresponding MAC Address and/or Serial Number.",
		**kwargs
	)
	parser.add_argument("-f", "--use-field", help="Use specific field as identifier if available instead of MAC Address.", nargs="+", default=None)
	parser.add_argument("-o", "--overwrite", help="Over-write pre-existing UDEV Link Files.", action="store_true")
	parser.add_argument("-p", "--print", help="Print data instead of writing to UDEV Link Files.", action="store_true")
	parser.add_argument("-v", "--verbose", action="store_true")
	return parser

def main(argv_a):
	use_field = argv_a.use_field
	use_print = argv_a.print
	use_overwrite = argv_a.overwrite
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
		mac_address_sp = subprocess.Popen(f"cat /sys/class/net/{iface_name}/address".split(),
			stdout=subprocess.PIPE, 
			stderr=subprocess.PIPE,
		)
		out, err = mac_address_sp.communicate()
		returncode = mac_address_sp.returncode
		if returncode == 0:
			iface_mac_addr = out.decode("utf-8").strip()
		if mac_address_validator(iface_mac_addr):
			print(f"Interface {bcolors.L_BLUE}{iface_name}{bcolors.NC} will be pinned with MAC Address {bcolors.L_RED}{iface_mac_addr}{bcolors.NC}")
			if os.path.isfile(udev_link_name) and not use_overwrite:
				print(f"UDEV Link File {udev_link_name} for Interface {iface_name} already exists, skipping.\n")
				continue

			data = None
			if use_field:
				attrs = ""
				for k, v in get_inet_udev_info(iface_name):
					if k in use_field:
						attrs = attrs + "\n" + f"Property={k}={v}" + "\n"
				data = UDEV_BY_PROPERTY.format(
					iface_name=iface_name,
					iface_mac_addr=iface_mac_addr,
					attrs=attrs.strip()
				).strip()
			else:
				data = UDEV_BY_MAC_ADDRESS.format(
					iface_name=iface_name,
					iface_mac_addr=iface_mac_addr
				).strip()
			if use_print:
				print(f"{bcolors.L_YELLOW}Showing UDEV Link Template {udev_link_name} for Interface {iface_name}.{bcolors.NC}")
				print(data)
			else:
				with open(udev_link_name, "w") as iface_udev_link:
					print(f"Writing UDEV Link File {udev_link_name} for Interface {iface_name}.")
					iface_udev_link.write(data)
					print(f"UDEV Link Written.")
			print("-"*12 + "\n")
		else: print(f"{iface_name} has an invalid MAC Address, skipping.")

	print(f"You may execute the command {bcolors.L_YELLOW}systemctl restart systemd-udev-trigger{bcolors.NC} to refresh the Interface UDEV Links.")


