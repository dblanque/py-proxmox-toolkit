#!/usr/bin/python3
# Author: Dylan Blanqué
# Date: 2023-12-14
# Documentation (VM): https://pve.proxmox.com/pve-docs/qm.1.html
# Documentation (LXC): https://pve.proxmox.com/pve-docs/pct.1.html
import sys
import os
import socket
import subprocess
import signal
import time
import logging
from copy import deepcopy
from core.proxmox.constants import PVE_CFG_NODES_DIR
from core.proxmox.guests import (
	get_guest_cfg,
	get_all_guests,
	get_guest_is_ct,
	parse_guest_netcfg,
	parse_net_opts_to_string
)
from core.parser import make_parser, ArgumentParser

def argparser(**kwargs) -> ArgumentParser:
	parser = make_parser(
		prog='Proxmox VE Staged Guest Network Modifier',
		description='This program is used for scripted network modifications that might imply a network cutout and require an automatic rollback.',
		**kwargs
	)
	parser.add_argument('-c', '--config')  # Bool
	parser.add_argument('-d', '--dry-run', action='store_true')  # Bool
	parser.add_argument('--debug', action='store_true', default=False)  # Bool
	parser.add_argument('-r', '--rollback', action='store_true')  # Bool
	parser.add_argument('-rd', '--rollback-delay', type=int, help="Rollback Delay in Seconds")
	parser.add_argument('-p', '--print-original', type=int, help="Print Original Config Arguments")
	parser.add_argument('--example', action='store_true', help="Shows example config file") # Bool
	return parser

def sigint_handler(sig, frame):
	print('Ctrl+C pressed, hard-quitting script.')
	sys.exit(0)
signal.signal(signal.SIGINT, sigint_handler)

# src: https://stackoverflow.com/questions/3041986/apt-command-line-interface-like-yes-no-input
def query_yes_no(question, default="yes"):
	"""Ask a yes/no question via raw_input() and return their answer.

	"question" is a string that is presented to the user.
	"default" is the presumed answer if the user just hits <Enter>.
			It must be "yes" (the default), "no" or None (meaning
			an answer is required of the user).

	The "answer" return value is True for "yes" or False for "no".
	"""
	valid = {"yes": True, "y": True, "ye": True, "no": False, "n": False}
	if default is None:
		prompt = " [y/n] "
	elif default == "yes":
		prompt = " [Y/n] "
	elif default == "no":
		prompt = " [y/N] "
	else:
		raise ValueError("invalid default answer: '%s'" % default)

	while True:
		sys.stdout.write(question + prompt)
		choice = input().lower()
		if default is not None and choice == "":
			return valid[default]
		elif choice in valid:
			return valid[choice]
		else:
			sys.stdout.write("Please respond with 'yes' or 'no' " "(or 'y' or 'n').\n")

# src: https://stackoverflow.com/questions/44037060/how-to-set-a-timeout-for-input
def TimedInputYN(question, default="yes", timeout=30, timeoutmsg="Prompt Timed Out."):
	logger = logging.getLogger()
	def timeout_error(*_):
		raise TimeoutError
	signal.signal(signal.SIGALRM, timeout_error)
	signal.alarm(timeout)
	try:
		answer = query_yes_no(question, default)
		signal.alarm(0)
		return answer
	except TimeoutError:
		if timeoutmsg:
			logger.info("\n%s", timeoutmsg)
		signal.signal(signal.SIGALRM, signal.SIG_IGN)
		if default == "yes": return True
		else: return False

def main(argv_a):
	logger = logging.getLogger()
	logger.setLevel(logging.INFO)

	hostname = socket.gethostname()
	guest_net_map = None
	guest_net_map: dict
	running_in_background = True
	script_path = os.path.realpath(__file__)

	if argv_a.debug: logger.setLevel(logging.DEBUG)

	# Logging
	logfile = f"{os.path.dirname(script_path)}/{os.path.basename(script_path)}.log"
	with open(logfile, 'w'):
		pass
	logger.addHandler(logging.FileHandler(logfile))

	try:
		if os.getpgrp() == os.tcgetpgrp(sys.stdout.fileno()):
			running_in_background = False
			logger.addHandler(logging.StreamHandler())
		else:
			running_in_background = True
			# Ignore SIGHUP
			signal.signal(signal.SIGHUP, signal.SIG_IGN)
	except:
		pass

	if argv_a.example:
		if not running_in_background:
			logger.info(
	"""
	# example_pve_net_data
	guest_net_map={
		100:{
			# Network Interfaces
			0: {
				"bridge":"vmbr0",
				"tag":100
			}
		}
	}
	"""
			)
		sys.exit(0)

	if not os.path.isdir(PVE_CFG_NODES_DIR):
		raise Exception("PVE Nodes directory does not exist.")

	if argv_a.config:
		if not os.path.isfile(argv_a.config): raise ValueError(f"{argv_a.config} config file does not exist.")
		import importlib.util
		spec = importlib.util.spec_from_file_location("pve_net_modifier_cfg", argv_a.config)
		pve_net_modifier_cfg = importlib.util.module_from_spec(spec)
		sys.modules["pve_net_modifier_cfg"] = pve_net_modifier_cfg
		spec.loader.exec_module(pve_net_modifier_cfg)

		try:
			guest_net_map = pve_net_modifier_cfg.guest_net_map
		except: raise
		if type(guest_net_map) != dict: raise Exception("Invalid Dictionary objects in configuration file.")
	else:
		raise ValueError("Configuration File Path required. See --help arg.")

	if argv_a.dry_run: logger.info("Running in dry-run mode. Commands will only be printed.")

	all_guests = get_all_guests(filter_ids=guest_net_map)
	guest_net_orig = {}
	for guest_type in all_guests:
		for guest_id in all_guests[guest_type]:
			guest_host = get_guest_cfg(guest_id=guest_id, get_host=True)
			if guest_host != hostname:
				guest_net_orig[int(guest_id)] = parse_guest_netcfg(guest_id, remote=True, remote_host=guest_host, debug=argv_a.debug)
			else:
				guest_net_orig[int(guest_id)] = parse_guest_netcfg(guest_id, debug=argv_a.debug)

	if argv_a.print_original:
		logger.info("If you need to restore the config manually, here's the output to use in the cfg python file.")
		logger.info(guest_net_orig)

	if len(guest_net_map) < 1 or (len(all_guests["vm"]) < 1 and len(all_guests["ct"]) < 1):
		logger.info("Guest Mappings are empty. Exiting script.")
		logger.info(guest_net_map)
		logger.info(all_guests)
		sys.exit(0)

	cmd_args: list = []
	for guest_id in guest_net_map:
		logger.info("Making changes to %s", guest_id)
		guest_is_ct = get_guest_is_ct(guest_id)
		guest_host = get_guest_cfg(guest_id=guest_id, get_host=True)
		guest_is_remote = guest_host != hostname
		net_cfg = deepcopy(guest_net_orig[int(guest_id)])

		if guest_is_remote:
			logger.info("%s is located in remote host (%s)", guest_id, guest_host)
		for net_id in guest_net_map[guest_id]:
			new_net_opts = guest_net_map[guest_id][net_id]
			if net_id in net_cfg:
				for k, v in new_net_opts.items():
					if v == None:
						net_cfg[net_id].pop(k, None)
					else: net_cfg[net_id][k] = v

		for net_id, net_opts in net_cfg.items():
			# Skip network interfaces without changes
			if not net_id in guest_net_map[guest_id]: continue
			if guest_is_ct:
				cmd_args=["/usr/sbin/pct", "set", str(guest_id), f"--net{net_id}", parse_net_opts_to_string(net_opts)]
			else:
				cmd_args=["/usr/sbin/qm", "set", str(guest_id), f"--net{net_id}", parse_net_opts_to_string(net_opts)]
			if guest_is_remote:
				ssh_args = ["/usr/bin/ssh", f"root@{guest_host}"]
				cmd_args = ssh_args + cmd_args
			if argv_a.debug: logger.debug(cmd_args)
			if argv_a.dry_run:
				logger.info(" ".join(cmd_args))
			else:
				subprocess.run(cmd_args)

	# If rollback is not enabled, exit
	if not argv_a.rollback:
		sys.exit()

	do_rollback = True
	rollback_timer = 0
	if not argv_a.rollback_delay: rollback_delay = 30
	else: rollback_delay = argv_a.rollback_delay

	if not running_in_background:
		do_rollback = TimedInputYN(
			question=f"Do you wish to Rollback the changes? (Timeout in {rollback_delay} seconds)",
			default="yes",
			timeout=rollback_delay,
			timeoutmsg="Starting Rollback."
		)
	else:
		logger.info("Waiting for %s seconds until rollback.", rollback_delay)
		time.sleep(rollback_delay)
	if not do_rollback: sys.exit(0)

	logger.debug("Guest Net Map: %s", guest_net_map)
	for guest_id in guest_net_map:
		logger.info("Rolling back changes for %s.", guest_id)
		guest_cfg = get_guest_cfg(guest_id)
		guest_is_ct = get_guest_is_ct(guest_id)
		guest_host = get_guest_cfg(guest_id=guest_id, get_host=True)
		guest_is_remote = guest_host != hostname
		net_cfg = deepcopy(guest_net_orig[int(guest_id)])

		if guest_is_remote:
			logger.info("%s is located in remote host (%s)", guest_id, guest_host)
		for net_id, net_opts in net_cfg.items():
			# Skip network interfaces without changes
			if not net_id in guest_net_map[guest_id]: continue
			if guest_is_ct:
				cmd_args=["/usr/sbin/pct", "set", str(guest_id), f"--net{net_id}", parse_net_opts_to_string(net_opts)]
			else:
				cmd_args=["/usr/sbin/qm", "set", str(guest_id), f"--net{net_id}", parse_net_opts_to_string(net_opts)]
			if guest_is_remote:
				ssh_args = ["/usr/bin/ssh", f"root@{guest_host}"]
				cmd_args = ssh_args + cmd_args
			if argv_a.debug: logger.debug(cmd_args)
			if argv_a.dry_run:
				logger.info(" ".join(cmd_args))
			else:
				subprocess.run(cmd_args)

	sys.exit(0)
