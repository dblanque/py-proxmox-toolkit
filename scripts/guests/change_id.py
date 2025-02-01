#!/usr/bin/env python3
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
import signal
script_path = os.path.realpath(__file__)
script_dir = os.path.dirname(script_path)
if __name__ == "__main__":
	raise Exception("This python script cannot be executed individually, please use main.py")

from core.signal_handlers.sigint import graceful_exit

# IMPORTS
import logging
import socket
import subprocess
import re
from core.proxmox.guests import (
	get_guest_cfg_path,
	get_guest_status,
	get_guest_snapshots,
	get_guest_exists,
	parse_guest_cfg,
	DiskDict
)
from core.proxmox.storage import get_storage_cfg
from core.proxmox.backup import get_all_backup_jobs, set_backup_attrs, BackupJob
from core.proxmox.constants import DISK_TYPES, PVE_CFG_REPLICATION
from core.classes.ColoredFormatter import set_logger
from core.utils.prompt import yes_no_input
from core.signal_handlers.sigint import graceful_exit
from core.parser import make_parser, ArgumentParser

def argparser(**kwargs) -> ArgumentParser:
	parser = make_parser(
		prog="Batch PVE Guest Network Modifier",
		description="This program is used for scripted network modifications that might imply a network cutout or require an automatic rollback.",
		**kwargs
	)
	parser.add_argument('-l', '--remote-user', default="root")
	parser.add_argument('-i', '--origin-id', default=None)
	parser.add_argument('-t', '--target-id', default=None)
	parser.add_argument('-y', '--yes', action='store_true', default=False)
	parser.add_argument('-d', '--dry-run', action='store_true', default=False)
	parser.add_argument('--debug', action='store_true', default=False)
	parser.add_argument('-v', '--verbose', action='store_true', default=False)
	return parser

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
	logger = logging.getLogger()
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
	if "raw_values" in disk_data:
		is_cloudinit = "cloudinit" in " ".join(disk_data["raw_values"])
	else: is_cloudinit = False
	if exclude_media and "media" in disk_data and not is_cloudinit:
		return False
	return True

def rename_guest_replication(old_id: int, new_id: int) -> None:
	logger = logging.getLogger()
	# Rename disk in Guest Configuration
	logger.info("Changing replication jobs for Guest %s to %s in %s",
													old_id, new_id, PVE_CFG_REPLICATION)
	sed_regex = rf"s/^local: {old_id}-\(.*\)$/local: {new_id}-\1/g"
	rpl_cmd_args = [
		"/usr/bin/sed",
		"-i",
		sed_regex, # Sed F String Regex
		PVE_CFG_REPLICATION
	]
	logger.debug(rpl_cmd_args)
	with subprocess.Popen(rpl_cmd_args, stdout=subprocess.PIPE) as proc:
		proc_o, proc_e = proc.communicate()
		if proc.returncode != 0:
			raise Exception(f"Bad command return code ({proc.returncode}).", proc_o.decode(), proc_e.decode())
	return

def get_guest_replication_targets(old_id):
	jobs = []
	targets = []
	with open(PVE_CFG_REPLICATION, "r") as replication_cfg:
		replication_job = None
		for line in replication_cfg.readlines():
			line = line.strip()
			if len(line) < 1:
				continue
			if line.startswith("local:"):
				replication_job = line.split(": ")[1]
				vmid = int(replication_job.split("-")[0])
			elif vmid == old_id:
				try:
					_key, _value = line.split(sep=None, maxsplit=1)
					if _key == "target": targets.append(_value)
				except:
					print(line)
					raise
	return targets

def change_guest_id_on_backup_jobs(old_id: int, new_id: int, dry_run=False) -> None:
	logger = logging.getLogger()
	backup_jobs = get_all_backup_jobs()
	backup_change_errors = []
	for job in backup_jobs:
		job: BackupJob
		if "vmid" in job:
			job_id = job["id"]
			job_description = job["comment"]
			job_vmids_data = job["vmid"]
			job_vmids: list = job_vmids_data.split(",")
			if not old_id in job_vmids:
				logger.info("VM not in Backup Job %s (%s), skipping.", job_id, job_description)
				continue

			job_vmids.remove(old_id)
			job_vmids.append(new_id)
			job_vmids_data = ",".join(job_vmids)

			if not dry_run:
				if set_backup_attrs(
					job_id = job_id,
					data = {"vmid": job_vmids_data},
					raise_exception = False
				):
					backup_change_errors.append(job_id)
				else:
					logger.info("Modified backup job %s (%s).", job_id, job_description)
			else:
				logger.info("Fake modified backup job %s (%s).", job_id, job_description)
	if len(backup_change_errors) > 0:
		logger.error("Unable to re-target some backup jobs, please fix them manually.")
	return

def parse_guest_disk(disk_name, disk_values):
	logger = logging.getLogger()
	if "raw_values" in disk_values:
		if len(disk_values['raw_values']) != 1:
			logger.error("Bad Parsing.")
			logger.error("Disk %s has more than one path (%s).", disk_name, disk_values['raw_values'])
			logger.error("Path Array Length: %s", len(disk_values['raw_values']))
			raise ValueError(disk_values['raw_values'])
		_raw_values = disk_values['raw_values'][0]
		_split_values = _raw_values.split(":") 
		logger.info("%s: %s", disk_name, _raw_values)
		return {
			"interface": disk_name,
			"raw_values": _raw_values,
			"storage": _split_values[0],
			"name": _split_values[1]
		}
	return None

def main(argv_a, **kwargs):
	signal.signal(signal.SIGINT, graceful_exit)
	hostname = socket.gethostname()
	running_in_background = True

	try:
		if os.getpgrp() == os.tcgetpgrp(sys.stdout.fileno()):
			running_in_background = False
		else:
			running_in_background = True
			# Ignore SIGHUP
			signal.signal(signal.SIGHUP, signal.SIG_IGN)
	except:
		pass

	# Logging
	logger = logging.getLogger()
	log_level = "INFO"
	if argv_a.debug: log_level = "DEBUG"
	debug_verbose = (argv_a.debug and argv_a.verbose)
	log_file = f"{os.path.dirname(script_path)}/{os.path.basename(script_path)}.log"
	logger = set_logger(
		logger,
		log_console=(not running_in_background),
		log_file=log_file,
		level=log_level,
		format="%(levelname)s %(message)s"
	)

	id_origin = argv_a.origin_id
	id_target = argv_a.target_id
	remote_user = argv_a.remote_user
	if not validate_vmid(vmid=id_origin):
		id_origin = vmid_prompt()
	if not validate_vmid(vmid=id_target):
		id_target = vmid_prompt(target=True)

	if not get_guest_exists(id_origin):
		logger.error("Guest with Origin ID (%s) does not exist.", id_origin)
		sys.exit(ERR_GUEST_NOT_EXISTS)
	if get_guest_exists(id_target):
		logger.error("Guest with Target ID (%s) already exists.", id_target)
		sys.exit(ERR_GUEST_EXISTS)

	guest_snapshots = get_guest_snapshots(id_origin)
	if not argv_a.yes:
		confirm_prompt(id_origin, id_target)
		if guest_snapshots:
			print(f"Guest {id_origin} has {len(guest_snapshots)} snapshots that could be "+
		 	"irreversibly affected if the process does not finish correctly.")
			yes_no_input("Do you wish to continue?")

	if argv_a.dry_run: logger.info("Executing in dry-run mode.")
	guest_cfg_details = get_guest_cfg_path(guest_id=id_origin, get_as_dict=True)
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
	guest_cfg = parse_guest_cfg(
		guest_id=id_origin,
		remote=guest_on_remote_host,
		remote_host=guest_cfg_host,
		debug=debug_verbose,
	)

	if argv_a.verbose:
		logger.info("Guest is on Host: %s", guest_cfg_host)
		logger.info("Selected Origin ID: %s", id_origin)
		logger.info("Selected Target ID: %s", id_target)
	logger.debug("Guest Configuration: %s", guest_cfg)

	guest_state = get_guest_status(guest_id=id_origin, remote_args=args_ssh)
	if guest_state != "stopped":
		logger.error("Guest must be in stopped state (Currently %s)", guest_state)
		sys.exit(ERR_GUEST_NOT_STOPPED)
	# Change Config ID - Move config file
	old_cfg_path = guest_cfg_details['path']
	new_cfg_path = guest_cfg_details['path'].replace(f"{id_origin}.conf", f"{id_target}.conf")
	args_mv = ["/usr/bin/mv", old_cfg_path, new_cfg_path]
	if guest_on_remote_host:
		args_mv = args_ssh + args_mv

	# Rename Guest Configuration
	if argv_a.dry_run:
		logger.info(args_mv)
	else:
		with subprocess.Popen(args_mv, stdout=subprocess.PIPE) as proc:
			proc_o, proc_e = proc.communicate()
			if proc.returncode != 0:
				raise Exception(f"Bad command return code ({proc.returncode}).", proc_o.decode(), proc_e.decode())

	disk_dicts: list[dict] = []
	logger.info("The following disks will be migrated: ")
	# For each discovered disk, do pre-checks
	for key, value in guest_cfg.items():
		if not valid_pve_disk_type(key, value): continue
		parsed_disk = parse_guest_disk(disk_name=key, disk_values=value)
		if parsed_disk:
			disk_dicts.append(parsed_disk)
	
	for snapshot in guest_snapshots:
		for key, value in parse_guest_cfg(
			guest_id=id_origin,
			remote=guest_on_remote_host,
			remote_host=guest_cfg_host,
			debug=debug_verbose,
			snapshot_name=snapshot,
			current=False
		):
			if key == "vmstate":
				parsed_disk = parse_guest_disk(disk_name=key, disk_values=value)
				if parsed_disk:
					disk_dicts.append(parsed_disk)

	# Move Disks
	for disk in disk_dicts:
		disk: DiskDict
		d_storage = get_storage_cfg(disk["storage"])
		d_name: str = disk["name"]
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
	for target in get_guest_replication_targets(old_id=id_origin):
		logger.info(f"Re-adjusting replicated disks in host {target}.")
		args_ssh = ["/usr/bin/ssh", f"{remote_user}@{target}"]
		# Move Disks
		for disk in disk_dicts:
			disk: DiskDict
			d_storage = get_storage_cfg(disk["storage"])
			d_name: str = disk["name"]
			d_storage.reassign_disk(
				disk_name=d_name,
				new_guest_id=id_target,
				new_guest_cfg=new_cfg_path,
				remote_args=args_ssh,
				dry_run=argv_a.dry_run
			)

	# Alter Backup Jobs
	# see https://forum.proxmox.com/threads/create-backup-jobs-using-a-shell-command.110845/
	# pvesh get /cluster/backup --output-format json-pretty
	# pvesh usage /cluster/backup --verbose
	change_guest_id_on_backup_jobs(old_id=id_origin, new_id=id_target, dry_run=argv_a.dry_run)