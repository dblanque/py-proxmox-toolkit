if __name__ == "__main__":
	raise Exception("This python script cannot be executed individually, please use main.py")

import argparse
from core.network.interfaces import get_physical_interfaces

def argparser():
	parser = argparse.ArgumentParser(
		prog="Proxmox VE VMBR Generation Script",
		description="This program is used to generate a Network Interfaces file with new VMBRs."
	)
	parser.add_argument('-e', '--extra-iface', help="Extra interface regexes to select as physical interfaces.", nargs="+")
	parser.add_argument('-v', '--verbose', action='store_true', default=False)
	return parser

def main(argv_a):
	print(get_physical_interfaces(verbose=argv_a.verbose))