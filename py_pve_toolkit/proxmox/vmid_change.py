#!/usr/bin/python3
# Author: Dylan Blanqué
# Date:
# Description: Script for changing VM/CT ID in Proxmox VE
# TODO - Finish this script
# Prog Logic:
# Use arg for current id, target id
# Validate IDs as INTs
# Validate Target VM/CT ID does not exist
# Validate Origin VM/CT ID exists
# Get Type
# Change conf file to target id
# Change disks to target id
# ! Minimum support: LVM, CEPH, ZFS, DIR
# * Optionally
# * Change Replication Tasks
# * Change Backup Tasks
# * Change Backup Names

import os
import sys
script_path = os.path.realpath(__file__)
script_dir = os.path.dirname(script_path)
root_path = os.path.join(script_dir, os.path.pardir, os.path.pardir)
try:
	if not "VIRTUAL_ENV" in os.environ: raise Exception()
	VENV_DIR = os.path.abspath(os.environ['VIRTUAL_ENV']) or None
	if not VENV_DIR:
		print(VENV_DIR)
		raise Exception("No VENV_DIR variable available")
except Exception as e:
	print("Please Activate VIRTUAL ENVIRONMENT by executing:")
	print(f"source {os.path.realpath(root_path)}/bin/activate")
	sys.exit(1)
sys.path.append(VENV_DIR)

# IMPORTS
import logging, sys, os, argparse, socket, signal, subprocess, re
from pve_guest import get_guest_cfg, get_guest_status, get_guest_exists, parse_guest_cfg
from pve_storage import get_storage_cfg
from pve_constants import DISK_TYPES, PVE_CFG_REPLICATION
from py_pve_toolkit.classes.ColoredFormatter import set_logger

# SCRIPT
logger = logging.getLogger()

if __name__ != "__main__":
	logger.info("This is a script and may not be imported.")
	sys.exit()

parser = argparse.ArgumentParser(
	prog='Batch PVE Guest Network Modifier',
	description='This program is used for scripted network modifications that might imply a network cutout or require an automatic rollback.',
)
parser.add_argument('-l', '--remote-user', default="root")  # Bool
parser.add_argument('-i', '--origin-id', default=None)  # Bool
parser.add_argument('-t', '--target-id', default=None)  # Bool
parser.add_argument('-d', '--dry-run', action='store_true', default=False)  # Bool
parser.add_argument('--debug', action='store_true', default=False)  # Bool
parser.add_argument('-v', '--verbose', action='store_true', default=False)  # Bool
argv_a = parser.parse_args()
hostname = socket.gethostname()
running_in_background = True

def sigint_handler(sig, frame):
	print('\nCtrl+C pressed, hard-quitting script.')
	sys.exit(0)
signal.signal(signal.SIGINT, sigint_handler)

# Logging
log_level = "INFO"
if argv_a.debug: log_level = "DEBUG"
debug_verbose = (argv_a.debug and argv_a.verbose)
logfile = f"{os.path.dirname(script_path)}/{os.path.basename(script_path)}.log"

try:
	if os.getpgrp() == os.tcgetpgrp(sys.stdout.fileno()):
		running_in_background = False
	else:
		running_in_background = True
		# Ignore SIGHUP
		signal.signal(signal.SIGHUP, signal.SIG_IGN)
except:
	pass

logger = set_logger(
	logger, 
	log_console=(not running_in_background),
	log_file=logfile,
	level=log_level,
	format="%(levelname)s %(message)s"
)
## ERRORS
ERR_GUEST_EXISTS=1
ERR_GUEST_NOT_EXISTS=2
ERR_GUEST_NOT_STOPPED=3

def validate_vmid(vmid) -> bool:
	try: int(vmid)
	except: return False
	vmid = int(vmid)
	return vmid >= 100 and vmid < 999999999

def vmid_prompt(target=False):
	hint = "(INT. 1 - N, 9 digits max.)"
	subject = "target" if target else "origin"
	question = f"Please enter the {subject} ID:"
	sys.stdout.write(question)
	while True:
		vmid = input().lower()
		if vmid and validate_vmid(vmid):
			return int(vmid)
		else:
			sys.stdout.write(f"Please enter a valid VM/CT ID {hint}:")

def confirm_prompt(id_origin, id_target):
	hint = "(Y|N) [N]"
	question = f"Are you sure you wish to change Guest {id_origin}'s ID to {id_target}? {hint}: "
	logger.info("This might break Replication and Backup Configurations.")
	logger.info("Please ensure such tasks are reconfigured after script completion.")
	sys.stdout.write(question)
	y_choices = [ "y", "yes"]
	n_choices = [ "n", "no" ]
	valid_choices = y_choices + n_choices
	while True:
		response = input().lower()
		if any(response.startswith(v) for v in valid_choices) or len(response) < 1:
			if len(response) < 1: sys.exit(0)
			if any(response.startswith(v) for v in n_choices): sys.exit(0)
			return
		else:
			sys.stdout.write(f"Please enter a valid response {hint}:")

def valid_pve_disk_type(label: str, disk_data: str, exclude_media=True) -> bool:
	if not re.sub(r"[0-9]+", "", label) in DISK_TYPES:
		return False
	if exclude_media and "media" in disk_data:
		return False
	return True

def rename_guest_replication(old_id: int, new_id: int) -> None:
	# Rename disk in Guest Configuration
	logger.info(f"Changing replication jobs for Guest {old_id} to {new_id} in {PVE_CFG_REPLICATION}")
	rpl_cmd_args = [
		"/usr/bin/sed",
		"-i",
		f"s/^local: {old_id}-\(.*\)$/local: {new_id}-\\1/g", # Sed F String Regex
		PVE_CFG_REPLICATION
	]
	logger.debug(rpl_cmd_args)
	proc = subprocess.Popen(rpl_cmd_args, stdout=subprocess.PIPE)
	proc_o, proc_e = proc.communicate()
	if proc.returncode != 0:
		raise Exception(f"Bad command return code ({proc.returncode}).", proc_o.decode(), proc_e.decode())
	return

def main():
	id_origin = argv_a.origin_id
	id_target = argv_a.target_id
	remote_user = argv_a.remote_user
	if not validate_vmid(vmid=id_origin):
		id_origin = vmid_prompt()
	if not validate_vmid(vmid=id_target):
		id_target = vmid_prompt(target=True)

	if not get_guest_exists(id_origin):
		logger.error(f"Guest with Origin ID ({id_origin}) does not exist.")
		sys.exit(ERR_GUEST_NOT_EXISTS)
	if get_guest_exists(id_target): 
		logger.error(f"Guest with Target ID ({id_target}) already exists.")
		sys.exit(ERR_GUEST_EXISTS)
	confirm_prompt(id_origin, id_target)

	if argv_a.dry_run: logger.info("Executing in dry-run mode.")
	guest_cfg_details = get_guest_cfg(guest_id=id_origin, get_as_dict=True)
	guest_cfg_host = guest_cfg_details["host"]
	guest_is_ct = (guest_cfg_details["type"] == "ct")
	# Set command based on Guest Type	
	if guest_is_ct:
		proc_cmd = "pct"
	else: 
		proc_cmd = "qm"
	guest_on_remote_host = (hostname != guest_cfg_host)
	args_ssh = None
	if guest_on_remote_host:
		args_ssh = ["/usr/bin/ssh", f"{remote_user}@{guest_cfg_host}"]
	try:
		guest_cfg = parse_guest_cfg(
			guest_id=id_origin,
			remote=guest_on_remote_host,
			remote_host=guest_cfg_host,
			debug=debug_verbose,
		)
	except: raise

	if argv_a.verbose:
		logger.info(f"Guest is on Host: {guest_cfg_host}")
		logger.info(f"Selected Origin ID: {id_origin}")
		logger.info(f"Selected Target ID: {id_target}")
	logger.debug(f"Guest Configuration: {guest_cfg}")

	guest_state = get_guest_status(guest_id=id_origin, remote_args=args_ssh)
	if guest_state != "stopped":
		logger.error(f"Guest must be in stopped state (Currently {guest_state})")
		sys.exit(ERR_GUEST_NOT_STOPPED)
	# Change Config ID - Move config file
	old_cfg_path = guest_cfg_details['path']
	new_cfg_path = guest_cfg_details['path'].replace(f"{id_origin}.conf", f"{id_target}.conf")
	args_mv = [f"/usr/bin/mv", old_cfg_path, new_cfg_path]
	if guest_on_remote_host:
		args_mv = args_ssh + args_mv

	# Rename Guest Configuration
	if argv_a.dry_run:
		logger.info(f"{args_mv}")
	else:
		proc = subprocess.Popen(args_mv, stdout=subprocess.PIPE)
		proc_o, proc_e = proc.communicate()
		if proc.returncode != 0:
			raise Exception(f"Bad command return code ({proc.returncode}).", proc_o.decode(), proc_e.decode())

	disk_dicts: list[dict] = list()
	logger.info("The following disks will be migrated: ")
	# For each discovered disk, do pre-checks
	for i, d in guest_cfg.items():
		if not valid_pve_disk_type(i, d): continue
		if "raw_values" in d:
			if len(d['raw_values']) != 1:
				logger.error(f"Bad Parsing.")
				logger.error(f"Disk {i} has more than one path ({d['raw_values']}).")
				logger.error(f"Path Array Length: {len(d['raw_values'])}")
				raise ValueError(d['raw_values'])
			logger.info(f"{i}: {d['raw_values'][0]}")
			disk_dicts.append({
				"interface": i,
				"raw_values": d['raw_values'][0],
				"storage": d['raw_values'][0].split(":")[0],
				"name": d['raw_values'][0].split(":")[1]
			})

	# Move Disks
	for d in disk_dicts:
		d_interface: str = d["interface"]
		d_storage = get_storage_cfg(d["storage"])
		d_name: str = d["name"]
		d_storage.reassign_disk(
			disk_name=d_name,
			new_guest_id=id_target,
			new_guest_cfg=new_cfg_path,
			remote_args=args_ssh,
			dry_run=argv_a.dry_run
		)

	# Alter Replication Jobs
	if not argv_a.dry_run:
		rename_guest_replication(old_id=id_origin, new_id=id_target)

	# TODO - Alter Remote Replicated Volumes

	# TODO - Alter Backup Jobs
	# see https://forum.proxmox.com/threads/create-backup-jobs-using-a-shell-command.110845/
	# pvesh get /cluster/backup --output-format json-pretty
	# pvesh usage /cluster/backup --verbose

if __name__ == "__main__":
	main()

sys.exit(0)