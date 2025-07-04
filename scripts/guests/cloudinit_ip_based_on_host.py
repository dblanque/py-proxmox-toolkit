#!/usr/bin/python3
if __name__ == "__main__":
	raise Exception(
		"This python script cannot be executed individually, please use main.py"
	)

# IMPORTS
import signal
import subprocess
import json
import socket
import ipaddress
from core.proxmox.guests import get_guest_exists, get_guest_cfg_path, get_guest_status
from core.signal_handlers.sigint import graceful_exit
from core.parser import make_parser, ArgumentParser

argparser_descr = """
This program is used for scripted network modifications, recommended for situations
where you might want a Remote Access Server to auto-adjust it's network along with the
hypervisor cluster, and you don't know what subnet they'll be placed in.

CAUTION: It could use an IP of a host outside the Cluster Network and generate network
issues.
""".lstrip()


def argparser(**kwargs) -> ArgumentParser:
	parser = make_parser(
		prog="Set a single hosts' IP Address through Cloud-Init based on Host Data",
		description=argparser_descr,
		**kwargs,
	)
	parser.add_argument("guest_id", default=None, type=int)
	parser.add_argument("-d", "--dry-run", action="store_true", default=False)
	parser.add_argument("--debug", action="store_true", default=False)
	parser.add_argument(
		"-b", "--bridge", default="vmbr0", help="May also be a physical interface."
	)
	parser.add_argument("-v", "--verbose", action="store_true", default=False)
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
	if not get_guest_exists(argv_a.guest_id):
		raise Exception(f"Guest ID {argv_a.guest_id} does not exist.")

	PVE_NODE_LIST_CMD = "pvesh get /nodes --output-format json"
	cmd = PVE_NODE_LIST_CMD.split()
	PVE_NODE_DATA: list[dict] = json.loads(subprocess.check_output(cmd))
	PVE_NODE_LIST = tuple([d["node"] for d in PVE_NODE_DATA])
	print("Proxmox VE Cluster Node list fetched.")

	PVE_NETWORK_CMD = "pvesh get /nodes/{0}/network --output-format json"
	for node in PVE_NODE_LIST:
		print(f"Fetching network data for {node}.")
		cmd = PVE_NETWORK_CMD.format(node).split()
		PVE_NETWORK_DATA: list[dict] = json.loads(subprocess.check_output(cmd))
		for iface_dict in PVE_NETWORK_DATA:
			if not "iface" in iface_dict:
				raise ValueError(
					f"Missing critical key in Interface Dictionary.\n{iface_dict}"
				)
			if not iface_dict["iface"].startswith(argv_a.bridge):
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

	if not cloudinit_guest_address in network:
		raise Exception("Could not find a valid contiguous IP within requested subnet.")
	print(f"Using {cloudinit_guest_address} for guest.")

	guest_cfg_details = get_guest_cfg_path(guest_id=argv_a.guest_id, get_as_dict=True)
	guest_cfg_host = guest_cfg_details["host"]
	guest_is_ct = guest_cfg_details["type"] == "ct"
	if guest_is_ct:
		raise Exception("This script does not support LXC Guests.")

	guest_on_remote_host = hostname != guest_cfg_host
	args_ssh = None
	if guest_on_remote_host:
		args_ssh = ["/usr/bin/ssh", f"root@{guest_cfg_host}"]

	args_qm = f"qm set {argv_a.guest_id} --ipconfig0 ip={cloudinit_guest_address}/{network.prefixlen},gw={gateway}".split()
	if guest_on_remote_host:
		args_qm = args_ssh + args_qm

	# Change Guest Config
	if argv_a.dry_run:
		print(args_qm)
	else:
		subprocess.call(args_qm)

	guest_state = get_guest_status(guest_id=argv_a.guest_id, remote_args=args_ssh)
	if guest_state == "running":
		args_power = f"qm reboot {argv_a.guest_id}".split()
	else:
		args_power = f"qm start {argv_a.guest_id}".split()
	if guest_on_remote_host:
		args_power = args_ssh + args_power

	# Change Guest Config
	if argv_a.dry_run:
		print(args_power)
	else:
		subprocess.call(args_power)
