
import os
import signal
script_path = os.path.realpath(__file__)
script_dir = os.path.dirname(script_path)
if __name__ == "__main__":
	raise Exception("This python script cannot be executed individually, please use main.py")

# IMPORTS
import subprocess
import json
import ipaddress
from core.proxmox.guests import get_guest_exists
from core.signal_handlers.sigint import graceful_exit
from core.parser import make_parser, ArgumentParser

def argparser(**kwargs) -> ArgumentParser:
	parser = make_parser(
		prog="Set IP Address through Cloud-Init based on Host Data",
		description="This program is used for scripted network modifications.",
		**kwargs
	)
	parser.add_argument('guest_id', default=None, type=int)  # Bool
	parser.add_argument('-d', '--dry-run', action='store_true', default=False)  # Bool
	parser.add_argument('--debug', action='store_true', default=False)  # Bool
	parser.add_argument('-v', '--verbose', action='store_true', default=False)  # Bool
	return parser

def main(argv_a, **kwargs):
	signal.signal(signal.SIGINT, graceful_exit)
	reserved_ip_addresses = []
	network = None
	cmd = None
	if not argv_a.guest_id:
		raise ValueError("Please input a Guest ID.")
	assert get_guest_exists(argv_a.guest_id), f"Guest ID {argv_a.guest_id} does not exist."

	PVE_NODE_LIST_CMD = "pvesh get /nodes --output-format json"
	cmd = PVE_NODE_LIST_CMD.split()
	PVE_NODE_DATA: list[dict] = json.loads(subprocess.check_output(cmd))
	PVE_NODE_LIST = tuple([ d["node"] for d in PVE_NODE_DATA ])

	PVE_NETWORK_CMD = "pvesh get /nodes/{0}/network --output-format json"
	for node in PVE_NODE_LIST:
		cmd = PVE_NETWORK_CMD.format(node).split()
		PVE_NETWORK_DATA: list[dict] = json.loads(subprocess.check_output(cmd))
		for iface_dict in PVE_NETWORK_DATA:
			assert "iface" in iface_dict, f"Missing critical key in Interface Dictionary.\n{iface_dict}"
			if not iface_dict["iface"].startswith("vmbr0"):
				continue
			if not "cidr" in iface_dict:
				continue
			if network is None:
				network = ipaddress.ip_network(iface_dict["cidr"], False)
			reserved_ip_addresses.append(ipaddress.ip_address(iface_dict["address"]))

	reserved_ip_addresses.sort()
	cloudinit_guest_address = reserved_ip_addresses[-1] + 1

	print(cloudinit_guest_address)