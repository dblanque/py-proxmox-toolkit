#!/usr/bin/env python3
if __name__ == "__main__":
	raise Exception("This python script cannot be executed individually, please use main.py")

import subprocess
import os
import re
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
	parser.add_argument("-r", "--reconfigure-all", 
		help="Ignores existing configuration and regenerates all NIC and Bridge " +
		"assignments, also deletes non-existing or disconnected NICs.",
		action="store_true"
	)
	parser.add_argument("-x", "--keep-offloading", help="Do not disable offloading with ethtool.", action="store_true")
	parser.add_argument("-p", "--port-map", help="Map port to a specific bridge. (Separated by spaces, written as 'port:bridge')", nargs="*", default=[])
	return parser

def iface_sort(x: str):
	import re
	prefix = re.sub('\d+', '', x)
	number = x.replace(prefix, "")
	return prefix, number

def generate_bridge(name, **kwargs):
	data = {
		"name": name,
		"auto": True,
		"type": "static",
		"bridge-ports": [],
		"bridge-stp": [ "off" ],
		"bridge-fd": [ 0 ]
	}
	for kw in kwargs:
		data[kw] = kwargs[kw]
	return data

def main(argv_a, **kwargs):
	NEW_INTERFACES_FILE = f"{argv_a.source}.auto"
	OFFLOADING_CMD = "/sbin/ethtool -offload {0} tx off rx off; /sbin/ethtool -K {0} gso off; /sbin/ethtool -K {0} tso off;"
	INDENT = "\t-> "
	NON_BRIDGEABLE = [
		"lo"
	]

	print_c(bcolors.L_YELLOW, "Scanning Network Interfaces.")
	physical_interfaces = get_interfaces(interface_patterns=PHYSICAL_INTERFACE_PATTERNS)
	bridges = get_interfaces(interface_patterns=VIRTUAL_BRIDGE_PATTERNS)
	configured_ifaces, top_level_args = parse_interfaces(file=argv_a.source)
	if argv_a.reconfigure_all:
		print_c(bcolors.L_RED, "WARNING: All bridges will be reset.")
		for bridge in bridges:
			if bridge in configured_ifaces:
				del configured_ifaces[bridge]

	vmbr_map = {}
	port_map_list: dict[str] = argv_a.port_map
	if port_map_list:
		for i in port_map_list:
			i: str = i.split(":")
			port = i[0]
			bridge = i[1]
			vmbr_map[port] = bridge
			if len(i) != 2: raise Exception(f"Invalid map element (Length must be 2) {i}.")

	for port in vmbr_map.keys():
		if not port in physical_interfaces and not port in configured_ifaces:
			raise Exception(f"{port} was not found in the Interface list (Port Mapping).")

	# Add parent bridges to NICs that have it.
	# Re-concile physical interfaces with configured (in case a NIC is disconnected).
	for iface in configured_ifaces:
		# Bridges
		if any([re.match(regex, iface) for regex in VIRTUAL_BRIDGE_PATTERNS]):
			bridge = configured_ifaces[iface]
			if "bridge-ports" in bridge:
				if "none" in bridge["bridge-ports"]:
					continue
				for sub_iface in bridge["bridge-ports"]:
					configured_ifaces[sub_iface]["parent"] = iface
		# NICs
		elif (
			not iface in physical_interfaces and 
			any([re.match(regex, iface) for regex in PHYSICAL_INTERFACE_PATTERNS])
		):
			physical_interfaces.append(iface)

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

		vmbr_index = 0
		current_bridge = f"vmbr{vmbr_index}"

		if argv_a.ovs_bridge:
			raise Exception("OVS Bridges are currently Unsupported.")
		else:
			for iface in physical_interfaces:
				print_c(bcolors.L_YELLOW, f"Configuring Interface {iface}")
				is_mapped = iface in vmbr_map
				parent_bridge = None
				if iface in configured_ifaces:
					iface_config: dict = configured_ifaces[iface]
					if "parent" in iface_config:
						parent_bridge = iface_config.pop("parent")

				if not is_mapped and not parent_bridge:
					while f"vmbr{vmbr_index}" in configured_ifaces:
						vmbr_index += 1
						current_bridge = f"vmbr{vmbr_index}"

				# Generate VMBR if non-existent
				if not current_bridge in configured_ifaces and not parent_bridge:
					print_c(bcolors.L_YELLOW, f"{INDENT}Adding virtual bridge {current_bridge}")
					configured_ifaces[current_bridge] = generate_bridge(
						name=current_bridge,
						**{
							"bridge-ports": [ iface ],
							"description": "AUTOGENERATED"
						}
					)
				elif not parent_bridge:
					print_c(bcolors.L_BLUE, f"{INDENT}Linking port to virtual bridge {current_bridge}")
					configured_ifaces[current_bridge]["bridge-ports"].append(iface)
				else:
					print_c(bcolors.L_BLUE, f"{INDENT}{iface} already has a bridge configured ({parent_bridge})")

				if argv_a.keep_offloading is not True and iface in configured_ifaces:
					if not "post-up" in configured_ifaces[iface]:
						print_c(bcolors.L_YELLOW, f"{INDENT}Adding offloading to Interface {iface}.")
						configured_ifaces[iface]["post-up"] = OFFLOADING_CMD.format(iface).split()
					else:
						print_c(bcolors.L_RED, f"{INDENT}Interface {iface} already has a post-up argument, please disable offloading manually.")

				# Configure NIC
				if iface in configured_ifaces and not argv_a.reconfigure_all:
					print_c(
						bcolors.L_GREEN,
			 			f"{INDENT}{iface} is already configured, skipping other settings."
					)
					continue
				else:
					print_c(bcolors.L_GREEN, f"{INDENT}Interface {iface} configured.")
					configured_ifaces[iface] = {
						"name": iface,
						"type": "manual",
						"auto": True,
						"post-up": OFFLOADING_CMD.format(iface).split()
					}

		f.write(stringify_interfaces(configured_ifaces, top_level_args, sort_function=iface_sort))
	print(	f"New interfaces generated at {bcolors.L_YELLOW}{NEW_INTERFACES_FILE}{bcolors.NC}, "+
			f"rename it to {bcolors.L_YELLOW}{FILE_NETWORK_INTERFACES}{bcolors.NC} to apply changes.")
