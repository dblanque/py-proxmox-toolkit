#!/usr/bin/env python3
if __name__ == "__main__":
	raise Exception("This python script cannot be executed individually, please use main.py")

import subprocess
import os
from core.format.colors import bcolors, print_c
from core.network.interfaces import get_interfaces, PHYSICAL_INTERFACE_PATTERNS, VIRTUAL_BRIDGE_PATTERNS
from core.debian.constants import FILE_NETWORK_INTERFACES
from core.proxmox.network import parse_interfaces, DEFAULT_PVE_HEADER, stringify_interfaces
from core.parser import make_parser, ArgumentParser

def argparser(**kwargs) -> ArgumentParser:
	parser = make_parser(
		prog="Proxmox VE VMBR Generator Script",
		description="This program is used to generate Proxmox VE network bridges.",
		**kwargs
	)
	parser.add_argument("-s", "--source", help="Source specific Interfaces file.", default=FILE_NETWORK_INTERFACES)
	parser.add_argument("-o", "--ovs-bridge", help="Generate OVS Bridges instead of Linux Bridges.", action="store_true")
	parser.add_argument("-r", "--reconfigure-all", help="Ignores existing configuration and regenerates all NIC and Bridge assignments.", action="store_true")
	parser.add_argument("-x", "--keep-offloading", help="Do not disable offloading with ethtool.", action="store_true")
	parser.add_argument("-p", "--port-map", help="Map port to a specific bridge. (Separated by spaces, written as 'port:bridge')", nargs="*", default=[])
	return parser

def main(argv_a: ArgumentParser):
	iface_data = {}
	use_linux_bridge = not argv_a.ovs_bridge
	vmbr_index = 0
	NEW_INTERFACES_FILE = f"{argv_a.source}.auto"
	OFFLOADING_CMD = "/sbin/ethtool -offload {0} tx off rx off; /sbin/ethtool -K {0} gso off; /sbin/ethtool -K {0} tso off;"

	print_c(bcolors.L_YELLOW, "Scanning Network Interfaces.")
	physical_interfaces = get_interfaces(interface_patterns=PHYSICAL_INTERFACE_PATTERNS)
	bridges = get_interfaces(interface_patterns=VIRTUAL_BRIDGE_PATTERNS)
	configured_ifaces, top_level_args = parse_interfaces(file=argv_a.source)
	if argv_a.reconfigure_all:
		print_c(bcolors.L_RED, "WARNING: All bridges will be reset.")
		for b in bridges:
			if b in configured_ifaces:
				del configured_ifaces[b]

	vmbr_map = {}
	port_map_list: dict[str] = argv_a.port_map
	if port_map_list:
		for i in port_map_list:
			i: str = i.split(":")
			vmbr_map[i[0]] = i[1]
			if len(i) != 2: raise Exception(f"Invalid map element (Length must be 2) {i}.")

	for p, b in vmbr_map.items():
		if not p in physical_interfaces: raise Exception(f"{p} was not found in the Interface list (Port Mapping).")
		if not b in bridges: raise Exception(f"{b} was not found in the Bridge list (Port Mapping).")

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
		for iface in physical_interfaces:
			if use_linux_bridge:
				if iface in configured_ifaces and not argv_a.reconfigure_all:
					print_c(bcolors.L_YELLOW, f"{iface} is already configured, skipping.")
					continue
				else:
					current_bridge = f"vmbr{vmbr_index}"
					# Increase bridge index if NIC is not mapped
					if not iface in vmbr_map:
						while f"vmbr{vmbr_index}" in configured_ifaces:
							vmbr_index += 1
							current_bridge = f"vmbr{vmbr_index}"

					# Generate VMBR if non-existent
					if not current_bridge in configured_ifaces:
						print_c(bcolors.L_BLUE, f"Setting up virtual bridge {current_bridge}")
						configured_ifaces[current_bridge] = {
							"name": current_bridge,
							"auto": True,
							"type": "static",
							"bridge-ports": [ iface ],
							"bridge-stp": [ "off" ],
							"bridge-fd": [ 0 ]
						}
					else:
						print_c(bcolors.L_BLUE, f"Linking port to virtual bridge {current_bridge}")
						configured_ifaces[current_bridge]["bridge-ports"].append(iface)

					print_c(bcolors.L_BLUE, f"Parsing NIC {iface}")
					configured_ifaces[iface] = {
						"name": iface,
						"type": "manual",
						"auto": True,
						"post-up": OFFLOADING_CMD.format(iface).split()
					}
			else:
				raise Exception("OVS Bridges are currently Unsupported.")

		if not argv_a.keep_offloading:
			for iface in configured_ifaces:
				# Only on Physical Interfaces
				if not iface in physical_interfaces: continue
				if not "post-up" in configured_ifaces[iface]:
					print_c(bcolors.L_BLUE, f"Adding offloading to pre-configured Interface {iface}.")
					configured_ifaces[iface]["post-up"] = OFFLOADING_CMD.format(iface).split()

		f.write(stringify_interfaces(configured_ifaces, top_level_args))
	print(	f"New interfaces generated at {bcolors.L_YELLOW}{NEW_INTERFACES_FILE}{bcolors.NC}, "+
			f"rename it to {bcolors.L_YELLOW}{FILE_NETWORK_INTERFACES}{bcolors.NC} to apply changes.")
