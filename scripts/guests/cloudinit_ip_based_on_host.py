
import os
import signal
script_path = os.path.realpath(__file__)
script_dir = os.path.dirname(script_path)
if __name__ == "__main__":
	raise Exception("This python script cannot be executed individually, please use main.py")

# IMPORTS
import subprocess
import json
import socket
import ipaddress
from core.proxmox.guests import get_guest_exists, get_guest_cfg
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
	hostname = socket.gethostname()
	reserved_ip_addresses = []
	network = None
	gateway = None
	cmd = None
	if not argv_a.guest_id:
		raise ValueError("Please input a Guest ID.")
	assert get_guest_exists(argv_a.guest_id), f"Guest ID {argv_a.guest_id} does not exist."

	PVE_NODE_LIST_CMD = "pvesh get /nodes --output-format json"
	cmd = PVE_NODE_LIST_CMD.split()
	PVE_NODE_DATA: list[dict] = json.loads(subprocess.check_output(cmd))
	PVE_NODE_LIST = tuple([ d["node"] for d in PVE_NODE_DATA ])
	print("Proxmox VE Cluster Node list fetched.")

	PVE_NETWORK_CMD = "pvesh get /nodes/{0}/network --output-format json"
	for node in PVE_NODE_LIST:
		print(f"Fetching network data for {node}.")
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
				gateway = ipaddress.ip_address(iface_dict["gateway"])
			_addr = ipaddress.ip_address(iface_dict["address"])
			if _addr in network:
				reserved_ip_addresses.append(_addr)

	reserved_ip_addresses.sort()
	cloudinit_guest_address = reserved_ip_addresses[-1] + 1
	if not cloudinit_guest_address in network:
		print("Cannot increment IP Address bits, attempting to use a lower address.")
		cloudinit_guest_address = reserved_ip_addresses[0] - 1

	assert cloudinit_guest_address in network, "Could not find a valid contiguous IP within requested subnet."
	print(f"Using {cloudinit_guest_address} for guest.")

	guest_cfg_details = get_guest_cfg(guest_id=argv_a.guest_id, get_as_dict=True)
	guest_cfg_host = guest_cfg_details["host"]
	guest_is_ct = (guest_cfg_details["type"] == "ct")
	assert not guest_is_ct, "This script does not support LXC Guests."
	
	guest_on_remote_host = (hostname != guest_cfg_host)
	args_ssh = None
	if guest_on_remote_host:
		args_ssh = ["/usr/bin/ssh", f"root@{guest_cfg_host}"]

	args_qm = f"qm set {argv_a.guest_id} --ipconfig0 ip={cloudinit_guest_address}/{network.prefixlen},gw={gateway}".split()
	if guest_on_remote_host:
		args_qm = args_ssh + args_qm

	# Rename Guest Configuration
	if argv_a.dry_run:
		print(args_qm)
	else:
		with subprocess.Popen(args_qm, stdout=subprocess.PIPE) as proc:
			proc_o, proc_e = proc.communicate()
			if proc.returncode != 0:
				raise Exception(f"Bad command return code ({proc.returncode}).", proc_o.decode(), proc_e.decode())
