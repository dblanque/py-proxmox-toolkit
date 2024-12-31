if __name__ == "__main__":
	raise Exception("This python script cannot be executed individually, please use main.py")

import argparse
from core.network.interfaces import get_interfaces, PHYSICAL_INTERFACE_PATTERNS, VIRTUAL_INTERFACE_PATTERNS
from core.format.colors import bcolors, print_c

def argparser():
	parser = argparse.ArgumentParser(
		prog="Proxmox VE Network Interface Listing Script",
		description="This program is used to list network interfaces."
	)
	parser.add_argument("-p", "--physical", help="Physical Interface Filtering.", action="store_true")
	parser.add_argument("-v", "--virtual", help="Virtual Interface Filtering.", action="store_true")
	parser.add_argument("-e", "--exclude", help="Regexes to exclude from physical interface discovery.", nargs="+", default=None)
	parser.add_argument("-r", "--regex", help="Regexes to select in physical interfaces discovery.", nargs="+", default=None)
	parser.add_argument("-o", "--only-regex", help="Use only specified regexes to detect network interfaces.", action="store_true")
	parser.add_argument("-d", "--verbose", action="store_true")
	return parser

def main(argv_a):
	print_c(bcolors.L_YELLOW, "Scanning Physical Network Interfaces.")
	regex_list = list()
	if not argv_a.physical and not argv_a.virtual and not argv_a.regex:
		regex_list = [ r"^.*$" ]

	if argv_a.physical:
		regex_list = regex_list + PHYSICAL_INTERFACE_PATTERNS
	if argv_a.virtual:
		regex_list = regex_list + VIRTUAL_INTERFACE_PATTERNS
	if argv_a.regex and len(argv_a.regex) > 0:
		regex_list = regex_list + argv_a.regex

	if argv_a.verbose:
		print_c(bcolors.L_BLUE, "Using the following regex patterns:")
		print(regex_list)

	interfaces = get_interfaces(
		interface_patterns=regex_list,
		override_patterns=argv_a.only_regex,
		verbose=argv_a.verbose
	)
	if len(interfaces) > 0:
		print_c(bcolors.L_BLUE, "Discovered Network interfaces:")
		for iface in interfaces:
			print(f"\t -> {iface}")
	else:
		print("No network interfaces detected.")