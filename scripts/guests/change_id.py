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
	DiskDict,
	get_guest_replication_statuses,
	parse_guest_disk,
	is_valid_guest_disk_type,
	get_guest_replication_jobs
)
from core.proxmox.backup import get_all_backup_jobs, set_backup_attrs, BackupJob
from core.proxmox.storage import get_storage_cfg, DiskReassignException
from core.proxmox.replication import ReplicationJobDict
from core.format.colors import bcolors, print_c
from core.classes.ColoredFormatter import set_logger
from core.utils.prompt import yes_no_input
from core.signal_handlers.sigint import graceful_exit
from core.parser import make_parser, ArgumentParser
from time import sleep

def argparser(**kwargs) -> ArgumentParser:
	parser = make_parser(
		prog="Batch PVE Guest Network Modifier",
		description="This program is used for scripted network modifications that might imply a network cutout or require an automatic rollback.",
		**kwargs
	)
	parser.add_argument('-l', '--remote-user', default="root")
	parser.add_argument('-i', '--origin-id', default=None, type=int)
	parser.add_argument('-t', '--target-id', default=None, type=int)
	parser.add_argument('-y', '--yes', action='store_true', default=False)
	parser.add_argument('-d', '--dry-run', action='store_true', default=False)
	parser.add_argument('--debug', action='store_true', default=False)
	parser.add_argument('-v', '--verbose', action='store_true', default=False)
	return parser

## ERRORS
ERR_GUEST_EXISTS=1
ERR_GUEST_NOT_EXISTS=2
ERR_GUEST_NOT_STOPPED=3
ERR_GUEST_REPLICATION_IN_PROGRESS=4
ERR_REASSIGN_MSG = "Could not re-assign disk %s, please check manually"
NORMAL_PROMPT_EXIT_MSG = "Exiting script."

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
				logger.debug("VM not in Backup Job %s (%s), skipping.", job_id, job_description)
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
	replication_statuses = get_guest_replication_statuses(guest_id=id_origin)
	if any([v != "OK" for v in replication_statuses.values()]):
		logger.error("Guest with Origin ID (%s) has a replication job in progress.", id_origin)
		sys.exit(ERR_GUEST_REPLICATION_IN_PROGRESS)

	if not argv_a.yes:
		logger.info("This might break Replication and Backup Configurations.")
		logger.info("Please ensure such tasks are reconfigured after script completion.")
		confirm = yes_no_input(
			f"Are you sure you wish to change Guest {id_origin}'s ID to {id_target}?",
			input_default="N"
		)
		if not confirm:
			print_c(bcolors.L_BLUE, NORMAL_PROMPT_EXIT_MSG)
			sys.exit(0)

	if argv_a.dry_run: logger.info("Executing in dry-run mode.")
	guest_cfg_details = get_guest_cfg_path(guest_id=id_origin, get_as_dict=True)
	guest_cfg_host = guest_cfg_details["host"]
	guest_on_remote_host = (hostname != guest_cfg_host)

	# Set SSH Args if necessary
	args_ssh = None
	if guest_on_remote_host:
		args_ssh = ["/usr/bin/ssh", f"{remote_user}@{guest_cfg_host}"]

	guest_cfg = parse_guest_cfg(
		guest_id=id_origin,
		remote_args=args_ssh,
		debug=debug_verbose,
	)
	guest_disks: list[dict] = []
	guest_snapshots = get_guest_snapshots(guest_id=id_origin, remote_args=args_ssh)

	if argv_a.verbose:
		logger.info("Guest is on Host: %s", guest_cfg_host)
		logger.info("Selected Origin ID: %s", id_origin)
		logger.info("Selected Target ID: %s", id_target)
	logger.debug("Guest Configuration: %s", guest_cfg)

	# Get Guest State
	guest_state = get_guest_status(guest_id=id_origin, remote_args=args_ssh)
	if guest_state != "stopped":
		logger.error("Guest must be in stopped state (Currently %s)", guest_state)
		sys.exit(ERR_GUEST_NOT_STOPPED)

	# Generate new config file path
	old_cfg_path = guest_cfg_details['path']
	new_cfg_path = guest_cfg_details['path'].replace(
		f"{id_origin}.conf",
		f"{id_target}.conf"
	)

	# Add snapshot vmstate disks to configuration.
	for snapshot in guest_snapshots:
		snapshot_cfg = parse_guest_cfg(
			guest_id=id_origin,
			remote_args=args_ssh,
			debug=debug_verbose,
			snapshot_name=snapshot,
			current=False
		)
		logger.debug("Snapshot Keys: %s", snapshot_cfg.keys())
		logger.debug("Snapshot Configuration: %s", snapshot_cfg)
		for key, value in snapshot_cfg.items():
			if key == "vmstate":
				parsed_disk = parse_guest_disk(
					disk_name=key,
					disk_values=value,
					vmstate=True
				)
				if parsed_disk:
					logger.debug("Parsed Snapshot VM State: %s", parsed_disk)
					guest_disks.append(parsed_disk)

	# Second prompt if snapshots present
	if not argv_a.yes and guest_snapshots:
		print(f"Guest {id_origin} has {len(guest_snapshots)} snapshots that could be "+
		"irreversibly affected if the process does not finish correctly.")
		print("If there are any replication jobs they will be deleted and re-added.")
		if not yes_no_input("Are you SURE you wish to continue?", input_default="N"):
			print_c(bcolors.L_BLUE, NORMAL_PROMPT_EXIT_MSG)
			sys.exit(0)

	# Remove old Replication Jobs
	replication_jobs = get_guest_replication_jobs(old_id=id_origin)
	if len(replication_jobs) > 0:
		logger.debug("Found replication targets: " + ", ".join(replication_jobs.keys()))

	for job_name, job in replication_jobs.items():
		job_name: str
		job: ReplicationJobDict
		target = job["target"]
		logger.info(f"Deleting job {job_name}")
		job_delete_cmd = f"pvesr delete {job_name}".split()
		if guest_on_remote_host:
			job_delete_cmd = args_ssh + job_delete_cmd
		logger.debug(" ".join(job_delete_cmd))
		if not argv_a.dry_run:
			subprocess.call(job_delete_cmd)

	_TIMEOUT = 120
	_timer = 0
	logger.info(
		"Waiting for replication jobs to finish deletion (Timeout per job: %s seconds).",
		_TIMEOUT
	)
	_previous_status_len = len(replication_statuses)
	_current_status_len = len(replication_statuses)
	while _current_status_len > 0:
		if _timer != 0 and _timer % 10 == 0:
			replication_statuses = get_guest_replication_statuses(guest_id=id_origin)
			_previous_status_len = _current_status_len
			_current_status_len = len(replication_statuses)
			logger.info("Waiting for replication jobs...")
		if _previous_status_len != _current_status_len and _current_status_len > 0:
			logger.info("A job finished, awaiting further.")
			timer = 0
		sleep(1)
		_timer += 1
		if _timer >= _TIMEOUT:
			if _current_status_len > 0:
				logger.info("Timeout reached, cannot wait any longer.")
			break

	# Rename Guest Config File
	args_mv = ["/usr/bin/mv", old_cfg_path, new_cfg_path]
	if guest_on_remote_host:
		args_mv = args_ssh + args_mv

	# Rename Guest Configuration
	if argv_a.dry_run:
		logger.info(args_mv)
	else:
		subprocess.call(args_mv, stdout=subprocess.PIPE)

	# For each discovered disk, do pre-checks
	logger.info("The following disks will be renamed: ")
	for key, value in guest_cfg.items():
		if not is_valid_guest_disk_type(key, value): continue
		parsed_disk = parse_guest_disk(disk_name=key, disk_values=value)
		if parsed_disk:
			guest_disks.append(parsed_disk)

	# Re-assign disks
	for disk in guest_disks:
		disk: DiskDict
		d_storage = get_storage_cfg(disk["storage"])
		d_name: str = disk["name"]
		try:
			d_storage.reassign_disk(
				disk_name=d_name,
				new_guest_id=id_target,
				new_guest_cfg=new_cfg_path,
				remote_args=args_ssh,
				dry_run=argv_a.dry_run
			)
		except DiskReassignException as e:
			logger.error(ERR_REASSIGN_MSG, d_name)
			logger.exception(e)
			pass

	# Add new Replication Jobs
	for job_name, job in replication_jobs.items():
		new_job_name = job_name.replace(str(id_origin), str(id_target))
		new_job_cmd = f"pvesr create-local-job {new_job_name} {target}".split()
		for arg in ["rate", "schedule", "comment"]:
			if not arg in job:
				continue

			if arg == "comment":
				v = f'"{job[arg]}"'
			else:
				v = str(job[arg])
			new_job_cmd = new_job_cmd + [ f"--{arg}", v ]
		if guest_on_remote_host:
			new_job_cmd = args_ssh + new_job_cmd
		logger.debug(" ".join(new_job_cmd))
		if not argv_a.dry_run:
			subprocess.call(new_job_cmd)

	# Alter Backup Jobs
	# see https://forum.proxmox.com/threads/create-backup-jobs-using-a-shell-command.110845/
	# pvesh get /cluster/backup --output-format json-pretty
	# pvesh usage /cluster/backup --verbose
	change_guest_id_on_backup_jobs(
		old_id=id_origin,
		new_id=id_target,
		dry_run=argv_a.dry_run
	)