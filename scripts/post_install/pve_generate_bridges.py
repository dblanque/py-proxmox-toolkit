if __name__ == "__main__":
	raise Exception("This python script cannot be executed individually, please use main.py")

import argparse, subprocess, os
from core.format.colors import bcolors, print_c
from core.network.interfaces import get_interfaces, PHYSICAL_INTERFACE_PATTERNS, VIRTUAL_BRIDGE_PATTERNS
from core.debian.constants import FILE_NETWORK_INTERFACES
from core.templates.proxmox.interfaces.vmbr import VMBR_TEMPLATE_LINUX, VMBR_TEMPLATE_OVS
from core.proxmox.network import parse_interfaces, DEFAULT_PVE_HEADER, stringify_interfaces

def argparser() -> argparse.ArgumentParser:
	parser = argparse.ArgumentParser(
		prog="Proxmox VE VMBR Generator Script",
		description="This program is used to generate Proxmox VE network bridges."
	)
	parser.add_argument("-o", "--ovs-bridge", help="Generate OVS Bridges instead of Linux Bridges.", action="store_true")
	parser.add_argument("-x", "--keep-offloading", help="Do not disable offloading with ethtool.", action="store_true")
	parser.add_argument("-m", "--map", help="Map port to a specific bridge.", nargs="*", default=None)
	return parser

def main(argv_a: argparse.ArgumentParser):
	iface_data = dict()
	vmbr_index = 0
	NEW_INTERFACES_FILE = f"{FILE_NETWORK_INTERFACES}.auto"

	print_c(bcolors.L_YELLOW, "Scanning Network Interfaces.")
	ifaces = get_interfaces(interface_patterns=PHYSICAL_INTERFACE_PATTERNS)
	bridges = get_interfaces(interface_patterns=VIRTUAL_BRIDGE_PATTERNS)
	configured_ifaces = parse_interfaces()

	# Check if ethtool is installed when requiring offload disabled
	if not argv_a.keep_offloading:
		pkg = "ethtool"
		try:
			ec = subprocess.check_call(
				f"dpkg -l {pkg}".split(),
				stdout=open(os.devnull, 'wb'),
				stderr=subprocess.STDOUT
			)
			if ec == 0:
				print_c(bcolors.L_GREEN, f"{pkg} is installed, proceeding.")
		except:
			raise Exception("Please install ethtool or use option -x (see help).")

	with open(NEW_INTERFACES_FILE, "w") as f:
		f.write(DEFAULT_PVE_HEADER)
		for nic in ifaces:
			if not argv_a.ovs_bridge:
				if nic in configured_ifaces:
					print_c(bcolors.L_YELLOW, f"{nic} is already configured, skipping.")
					continue
				else:
					while f"vmbr{vmbr_index}" in bridges:
						vmbr_index += 1
					current_bridge = f"vmbr{vmbr_index}"
					print_c(bcolors.L_BLUE, f"Setting up virtual bridge {current_bridge}")
					configured_ifaces[current_bridge] = {
						"name": current_bridge,
						"auto": True,
						"type": "static",
						"bridge-ports": nic,
						"bridge-fd": 0
					}
					
					print_c(bcolors.L_BLUE, f"Parsing NIC {nic}")
					configured_ifaces[nic] = {
						"name": nic,
						"type": "manual",
						"post-up": "/sbin/ethtool -offload eno1 tx off rx off; /sbin/ethtool -K eno1 gso off; /sbin/ethtool -K eno1 tso off;".split()
					}
			else:
				raise Exception("OVS Bridges are currently Unsupported.")
		f.write(stringify_interfaces(configured_ifaces))
