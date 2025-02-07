#!/usr/bin/python3
if __name__ == "__main__":
	raise Exception("This python script cannot be executed individually, please use main.py")

import subprocess
import os
from core.network.interfaces import get_interfaces, PHYSICAL_INTERFACE_PATTERNS
from core.format.colors import bcolors, print_c, colorize
from core.parser import make_parser, ArgumentParser
from core.templates.udev.overrides import UDEV_BY_MAC_ADDRESS, UDEV_BY_PROPERTY
from core.debian.udev import get_inet_udev_info
from core.validators.mac import mac_address_validator

def argparser(**kwargs) -> ArgumentParser:
	parser = make_parser(
		prog="Proxmox VE Physical Network Interface Pinning Script",
		description="This program is used to pin network interfaces to their corresponding MAC Address and/or Serial Number.",
		**kwargs
	)
	parser.add_argument("-i", "--interface", help="Use specific interfaces.", nargs="+", default=None)
	parser.add_argument("-f", "--fields", help="Use specific UDEV Info Properties as identifier if available instead of MAC Address.", nargs="+", default=None)
	parser.add_argument("-o", "--overwrite", help="Over-write pre-existing UDEV Link Files.", action="store_true")
	parser.add_argument("-p", "--print", help="Print data instead of writing to UDEV Link Files.", action="store_true")
	parser.add_argument("-v", "--verbose", action="store_true")
	return parser

def main(argv_a, **kwargs):
	udev_fields = argv_a.fields
	use_print = argv_a.print
	use_overwrite = argv_a.overwrite
	UDEV_PATH = "/etc/systemd/network"
	print_c(bcolors.L_YELLOW, "Scanning Network Interfaces.")
	regex_list = list(PHYSICAL_INTERFACE_PATTERNS)

	interfaces = argv_a.interface or get_interfaces(
		interface_patterns=regex_list,
		verbose=argv_a.verbose
	)
	for iface_name in interfaces:
		iface_mac_addr = None
		udev_link_name = os.path.join(UDEV_PATH, f"10-{iface_name}.link")
		with subprocess.Popen(f"cat /sys/class/net/{iface_name}/address".split(),
			stdout=subprocess.PIPE,
			stderr=subprocess.PIPE,
		) as mac_address_sp:
			out, err = mac_address_sp.communicate()
			returncode = mac_address_sp.returncode
			if returncode == 0:
				iface_mac_addr = out.decode("utf-8").strip()

			if not mac_address_validator(iface_mac_addr):
				print(f"{iface_name} has an invalid MAC Address, skipping.")
				continue

			print(f"Interface {colorize(bcolors.L_BLUE, iface_name)} will be pinned with MAC Address {colorize(bcolors.L_RED, iface_mac_addr)}")
			if os.path.isfile(udev_link_name) and not use_overwrite:
				print(f"UDEV Link File {udev_link_name} for Interface {iface_name} already exists, skipping.\n")
				continue

			data = None
			if udev_fields:
				udev_info = get_inet_udev_info(iface_name)

			# If UDEV Fields/Properties are specified.
			if udev_fields and any([f in udev_info for f in udev_fields]):
				attrs = ""
				for k, v in udev_info.items():
					if k in udev_fields:
						attrs = attrs + f"Property={k}={v}" + "\n"
						print_c(bcolors.L_YELLOW, f"Pinning interface with additional attribute {k} ({v}).")
				data = UDEV_BY_PROPERTY.format(
					iface_name=iface_name,
					iface_mac_addr=iface_mac_addr,
					attrs=attrs.strip()
				).strip()
			else:
				if udev_fields:
					print("None of the requested UDEV Fields were found.")
					print("Using standard MAC Address UDEV Link.")
				data = UDEV_BY_MAC_ADDRESS.format(
					iface_name=iface_name,
					iface_mac_addr=iface_mac_addr
				).strip()
			if use_print:
				print_c(bcolors.L_YELLOW, f"Showing UDEV Link Template {udev_link_name} for Interface {iface_name}.")
				print(data)
			else:
				with open(udev_link_name, "w") as iface_udev_link:
					print(f"Writing UDEV Link File {colorize(bcolors.L_YELLOW, udev_link_name)} for Interface {colorize(bcolors.L_BLUE, iface_name)}.")
					iface_udev_link.write(data + "\n")
					print("UDEV Link Written.")
			print("-"*12 + "\n")

	print("You may execute the command {0} to refresh the Interface UDEV Links."
		.format(
			colorize(bcolors.L_YELLOW, "systemctl restart systemd-udev-trigger")
		)
	)
