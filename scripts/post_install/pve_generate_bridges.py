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
	parser.add_argument("-s", "--source", help="Source specific Interfaces file.", default=FILE_NETWORK_INTERFACES)
	parser.add_argument("-o", "--ovs-bridge", help="Generate OVS Bridges instead of Linux Bridges.", action="store_true")
	parser.add_argument("-r", "--reconfigure-all", help="Ignores existing configuration and regenerates all NIC and Bridge assignments.", action="store_true")
	parser.add_argument("-x", "--keep-offloading", help="Do not disable offloading with ethtool.", action="store_true")
	parser.add_argument("-m", "--map", help="Map port to a specific bridge. (Separated by spaces, written as 'port:bridge')", nargs="*", default={})
	return parser

def main(argv_a: argparse.ArgumentParser):
	iface_data = dict()
	vmbr_index = 0
	vmbr_map = dict()
	if argv_a.map:
		for i in argv_a.map:
			i: str = i.split(":")
			vmbr_map[i[0]] = i[1]
			if len(i) != 2: raise Exception(f"Invalid map element (Length must be 2) {i}.")
	NEW_INTERFACES_FILE = f"{argv_a.source}.auto"

	print_c(bcolors.L_YELLOW, "Scanning Network Interfaces.")
	ifaces = get_interfaces(interface_patterns=PHYSICAL_INTERFACE_PATTERNS)
	bridges = get_interfaces(interface_patterns=VIRTUAL_BRIDGE_PATTERNS)
	configured_ifaces = parse_interfaces(file=argv_a.source)
	if argv_a.reconfigure_all:
		for b in bridges:
			if b in configured_ifaces:
				del configured_ifaces[b]

	print(configured_ifaces)
	for p, b in vmbr_map.items():
		if not p in ifaces: raise Exception(f"{p} was not found in the Interface list.")
		if not b in bridges: raise Exception(f"{b} was not found in the Bridge list.")

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
				if nic in configured_ifaces and not argv_a.reconfigure_all:
					print_c(bcolors.L_YELLOW, f"{nic} is already configured, skipping.")
					continue
				else:
					current_bridge = f"vmbr{vmbr_index}"
					if not nic in argv_a.map and not current_bridge in configured_ifaces:
						print_c(bcolors.L_BLUE, f"Setting up virtual bridge {current_bridge}")
						while f"vmbr{vmbr_index}" in configured_ifaces:
							vmbr_index += 1
							current_bridge = f"vmbr{vmbr_index}"
						configured_ifaces[current_bridge] = {
							"name": current_bridge,
							"auto": True,
							"type": "static",
							"bridge-ports": [ nic ],
							"bridge-stp": [ "off" ],
							"bridge-fd": [ 0 ]
						}
					else:
						print_c(bcolors.L_BLUE, f"Linking port to virtual bridge {current_bridge}")
						configured_ifaces[current_bridge]["bridge-ports"].append(nic)

					print_c(bcolors.L_BLUE, f"Parsing NIC {nic}")
					configured_ifaces[nic] = {
						"name": nic,
						"type": "manual",
						"post-up": "/sbin/ethtool -offload eno1 tx off rx off; /sbin/ethtool -K eno1 gso off; /sbin/ethtool -K eno1 tso off;".split()
					}
			else:
				raise Exception("OVS Bridges are currently Unsupported.")
		f.write(stringify_interfaces(configured_ifaces))
