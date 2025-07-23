#!/usr/bin/python3
if __name__ == "__main__":
	raise Exception(
		"This python script cannot be executed individually, please use main.py"
	)

from core.network.interfaces import (
	get_interfaces,
	PHYSICAL_INTERFACE_PATTERNS,
	VIRTUAL_INTERFACE_PATTERNS,
	VIRTUAL_BRIDGE_PATTERNS,
)
from core.format.colors import bcolors, print_c, colorize
from core.parser import make_parser, ArgumentParser


def argparser(**kwargs) -> ArgumentParser:
	parser = make_parser(
		prog="Proxmox VE Network Interface Listing Script",
		description="This program is used to list network interfaces.",
		**kwargs,
	)
	parser.add_argument(
		"-p",
		"--physical",
		help="Physical Interface Filtering ONLY.",
		action="store_true",
	)
	parser.add_argument(
		"-v", "--virtual", help="Virtual Interface Filtering ONLY.", action="store_true"
	)
	parser.add_argument(
		"-e",
		"--exclude",
		help="Regexes to exclude from physical interface discovery.",
		nargs="+",
		default=None,
	)
	parser.add_argument(
		"-r",
		"--regex",
		help="Regexes to select in physical interfaces discovery.",
		nargs="+",
		default=None,
	)
	parser.add_argument(
		"-o",
		"--only-regex",
		help="Use only specified regexes to detect network interfaces.",
		action="store_true",
	)
	parser.add_argument(
		"-s", "--sort", help="Sort network interfaces output.", action="store_true"
	)
	parser.add_argument("-d", "--verbose", action="store_true")
	return parser

class LocalParser(ArgumentParser):
	physical: bool
	virtual: bool
	regex: list[str]
	exclude: list[str]
	only_regex: bool
	sort: bool
	verbose: bool

def main(argv_a: LocalParser, **kwargs):
	print_c(bcolors.L_YELLOW, "Scanning Network Interfaces.")
	regex_list = []
	if not argv_a.physical and not argv_a.virtual and not argv_a.regex:
		regex_list = [r"^.*$"]

	if argv_a.physical:
		regex_list = regex_list + list(PHYSICAL_INTERFACE_PATTERNS)
	if argv_a.virtual:
		regex_list = (
			regex_list
			+ list(VIRTUAL_INTERFACE_PATTERNS)
			+ list(VIRTUAL_BRIDGE_PATTERNS)
		)
	if argv_a.regex:
		regex_list = regex_list + argv_a.regex

	if argv_a.verbose:
		print_c(bcolors.L_BLUE, "Using the following regex patterns:")
		print(regex_list)

	interfaces = get_interfaces(
		interface_patterns=regex_list,
		override_patterns=any([argv_a.only_regex, argv_a.physical, argv_a.virtual]),
		verbose=argv_a.verbose,
	)
	if len(interfaces) > 0:
		print_c(bcolors.L_BLUE, "Discovered Network interfaces:")
		if argv_a.sort:
			interfaces = sorted(interfaces)
		for iface in interfaces:
			print(
				"\t -> %s" % (
					colorize(bcolors.L_GREEN, iface)
				)
			)
	else:
		print_c(bcolors.L_YELLOW, "No network interfaces detected.")
