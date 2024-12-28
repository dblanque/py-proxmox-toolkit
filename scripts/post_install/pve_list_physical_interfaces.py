if __name__ == "__main__":
	raise Exception("This python script cannot be executed individually, please use main.py")

import argparse
from core.network.interfaces import get_physical_interfaces
from core.format.colors import bcolors, print_c

def argparser():
	parser = argparse.ArgumentParser(
		prog="Proxmox VE VMBR Generation Script",
		description="This program is used to generate a Network Interfaces file with new VMBRs."
	)
	parser.add_argument("-e", "--exclude", help="Regexes to exclude from physical interface discovery.", nargs="+", default=None)
	parser.add_argument("-r", "--regex", help="Regexes to select in physical interfaces discovery.", nargs="+", default=None)
	parser.add_argument("-o", "--only-regex", help="Use only specified regexes to detect network interfaces.", action="store_true")
	parser.add_argument("-v", "--verbose", action="store_true")
	return parser

def main(argv_a):
	print_c(bcolors.L_YELLOW, "Scanning Physical Network Interfaces.")
	interfaces = get_physical_interfaces(
		interface_patterns=argv_a.regex,
		override_patterns=argv_a.only_regex,
		verbose=argv_a.verbose
	)
	if len(interfaces) > 0:
		print_c(bcolors.L_BLUE, "Discovered Network interfaces:")
		for iface in interfaces:
			print(iface)
	else:
		print("No network interfaces detected.")