if __name__ == "__main__":
	raise Exception("This python script cannot be executed individually, please use main.py")

import argparse
from core.format.colors import bcolors, print_c
from core.network.interfaces import get_interfaces, PHYSICAL_INTERFACE_PATTERNS
from core.debian.constants import FILE_NETWORK_INTERFACES

def argparser():
	parser = argparse.ArgumentParser(
		prog="Proxmox VE VMBR Generator Script",
		description="This program is used to generate Proxmox VE network bridges."
	)
	parser.add_argument("-l", "--linux-bridge", help="Generate Linux Bridges.", action="store_true")
	parser.add_argument("-o", "--ovs-bridge", help="Generate OVS Bridges.", action="store_true")
	return parser

def main(argv_a):
	print_c(bcolors.L_YELLOW, "Scanning Network Interfaces.")
	ifaces = get_interfaces(interface_patterns=PHYSICAL_INTERFACE_PATTERNS)
	NEW_INTERFACES_FILE = f"{FILE_NETWORK_INTERFACES}.auto"

	# with open(NEW_INTERFACES_FILE, "w") as f: