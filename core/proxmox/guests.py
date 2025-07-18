# Author: Dylan Blanqué
# BR Consulting S.R.L. 2024
import os
import re
import logging
import subprocess
from .constants import PVE_CFG_NODES_DIR
from sys import getdefaultencoding
from typing import TypedDict, Literal, overload
from enum import Enum
from core.proxmox.constants import DISK_TYPES, PVE_CFG_REPLICATION

logger = logging.getLogger()

PveGuestCommand = Literal["pct", "qm"]

class PveGuestType(Enum):
	VIRTUAL_MACHINE = "vm"
	LINUX_CONTAINER = "ct"

class DiskDict(TypedDict):
	interface: str
	raw_values: str
	storage: str
	name: str


def get_guest_exists(guest_id: int):
	guest_id = int(guest_id)
	if not os.path.isdir(PVE_CFG_NODES_DIR):
		return False
	guest_list = get_all_guests()
	return guest_id in guest_list["vm"] or guest_id in guest_list["ct"]

@overload
def get_guest_cfg_path(
	guest_id, get_host=False, get_type=False, get_as_dict=True
) -> dict[str, str]: ...

@overload
def get_guest_cfg_path(
	guest_id, get_host=False, get_type=False, get_as_dict=False
) -> str: ...

@overload
def get_guest_cfg_path(
	guest_id, get_host=False, get_type=True, get_as_dict=False
) -> str: ...

@overload
def get_guest_cfg_path(
	guest_id, get_host=True, get_type=False, get_as_dict=False
) -> str: ...

def get_guest_cfg_path(
	guest_id, get_host=False, get_type=False, get_as_dict=False
) -> str | dict[str, str] | None:
	"""
	Returns config path by default

	Dict returns
	* path
	* host
	* type [ct|vm]
	* subpath [lxc|vm]
	"""
	for h in os.listdir(PVE_CFG_NODES_DIR):
		for subp in ["qemu-server", "lxc"]:
			p = f"{PVE_CFG_NODES_DIR}/{h}/{subp}/{guest_id}.conf"
			if os.path.isfile(p):
				guest_type = PveGuestType.VIRTUAL_MACHINE.value
				if subp == "lxc":
					guest_type = PveGuestType.LINUX_CONTAINER.value
				if get_as_dict:
					return {"path": p, "host": h, "type": guest_type, "subpath": subp}
				if get_host:
					return h
				if get_type:
					return subp
				return p


def get_guest_is_ct(guest_id: int) -> bool:
	guest_type = get_guest_cfg_path(guest_id=guest_id, get_host=False, get_type=True)
	if guest_type == "qemu-server":
		return False
	return True


def get_guest_status(guest_id: int, remote_args: list[str] | None = None):
	# CT
	if get_guest_is_ct(guest_id):
		cmd_args = ["pct"]
	# VM
	else:
		cmd_args = ["qm"]
	cmd_args = cmd_args + ["status", str(guest_id)]
	if remote_args:
		cmd_args = remote_args + cmd_args
	with subprocess.Popen(cmd_args, stdout=subprocess.PIPE) as proc:
		proc_o, proc_e = proc.communicate()
		if proc.returncode != 0:
			raise Exception(
				f"Bad command return code ({proc.returncode}).",
				proc_o.decode(),
				proc_e.decode(),
			)
		result = proc_o.decode().split("\n")
		return result[0].strip().split(": ")[-1]


GUEST_CONF_REGEX = r"^[0-9]+.conf$"


def get_all_guests(filter_ids: list | dict = []):
	if isinstance(filter_ids, dict):
		filter_ids = list(filter_ids.keys())
	guests = {}
	guests["vm"] = []
	guests["ct"] = []
	for host in os.listdir(PVE_CFG_NODES_DIR):
		for i in os.listdir(f"{PVE_CFG_NODES_DIR}/{host}/qemu-server/"):
			if re.match(GUEST_CONF_REGEX, i):
				guest_id = int(i.rstrip(".conf"))
				if guest_id in filter_ids or len(filter_ids) < 1:
					guests["vm"].append(guest_id)
		for i in os.listdir(f"{PVE_CFG_NODES_DIR}/{host}/lxc/"):
			if re.match(GUEST_CONF_REGEX, i):
				guest_id = int(i.rstrip(".conf"))
				if guest_id in filter_ids or len(filter_ids) < 1:
					guests["ct"].append(guest_id)
	return guests


def parse_net_opts_to_string(net_opts: dict) -> str:
	r = ""
	for k, v in net_opts.items():
		if not r:
			r = f"{k}={v}"
		else:
			r = f"{r},{k}={v},"
	return r.rstrip(",").replace(",,", ",")


def get_guest_snapshots(guest_id: int, remote_args: list | None = None) -> list:
	if not isinstance(guest_id, int) and not int(guest_id):
		raise ValueError("guest_id must be of type int.")
	else:
		guest_id = int(guest_id)
	snapshots = []
	if get_guest_is_ct(guest_id):
		proc_cmd = "pct"
	else:
		proc_cmd = "qm"
	proc_cmd = proc_cmd.split()
	if remote_args:
		proc_cmd = remote_args + proc_cmd
	proc_cmd = proc_cmd + ["listsnapshot", str(guest_id)]
	output = subprocess.check_output(proc_cmd).decode(getdefaultencoding())
	for line in output.splitlines():
		try:
			snapshot_name = line.strip().split()[1]
			if snapshot_name == "current":
				continue
			snapshots.append(snapshot_name)
		except:
			print(line)
			raise
	return snapshots


def parse_guest_cfg(
	guest_id: int,
	remote_args: list | None = None,
	debug=False,
	current=True,
	snapshot_name: str | None = None,
) -> dict:
	if not isinstance(guest_id, int) and not int(guest_id):
		raise ValueError("guest_id must be of type int.")
	else:
		guest_id = int(guest_id)

	if not snapshot_name:
		logger.info("Collecting Config for Guest %s", guest_id)
	else:
		logger.info(
			"Collecting Config for Guest %s (Snapshot %s)", guest_id, snapshot_name
		)

	guest_cfg = {}
	if get_guest_is_ct(guest_id):
		proc_cmd = "pct"
	else:
		proc_cmd = "qm"

	cmd_args = [f"/usr/sbin/{proc_cmd}", "config", str(guest_id)]
	if current and snapshot_name:
		raise ValueError(
			"The current and snapshot args cannot be used at the same time."
		)
	if snapshot_name:
		cmd_args.insert(len(cmd_args) - 1, "--snapshot")
		cmd_args.insert(len(cmd_args) - 1, snapshot_name)
	if current:
		cmd_args.append("--current")
	if remote_args:
		cmd_args = remote_args + cmd_args
	if debug:
		logger.debug(cmd_args)

	with subprocess.Popen(
		cmd_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
	) as proc:
		proc_o, proc_e = proc.communicate()
		if proc.returncode != 0:
			raise Exception(
				f"Bad command return code ({proc.returncode}).",
				proc_o.decode(),
				proc_e.decode(),
			)
		if debug:
			logger.debug("Showing parsed Guest config lines:")
		for line in proc_o.decode("utf-8").split("\n"):
			line = line.rstrip()
			if debug:
				logger.debug(line)
			if len(line.strip()) == 0:
				continue
			line_split = line.split(": ")
			option_k = line_split[0]
			option_v = line_split[-1]
			# If Option has multiple key/value pairs in it (Comma separated)
			if "," in option_v:
				if option_k not in guest_cfg:
					guest_cfg[option_k] = {}
				option_v = option_v.replace(",,", ",").split(",")
				for sub_v in option_v:
					# Guess Separator
					fs = None
					for sep in ["=", ":"]:
						if sep in sub_v and sub_v.count(sep) == 1:
							fs = sep
					# If separator is equal assume it's not a Volume/Disk path.
					if fs == "=":
						k, v = sub_v.split(fs)
						try:
							v = int(v)
						except Exception:
							pass
						guest_cfg[option_k][k] = v
					# If it's a raw value
					else:
						if not sub_v or sub_v.lower() == "none":
							continue
						if "raw_values" not in guest_cfg[option_k]:
							guest_cfg[option_k]["raw_values"] = []
						try:
							sub_v = int(sub_v)
						except Exception:
							pass
						guest_cfg[option_k]["raw_values"].append(sub_v)
			else:
				try:
					option_v = int(option_v)
				except ValueError:
					pass
				guest_cfg[option_k] = option_v
		return guest_cfg


def parse_guest_net_cfg(
	guest_id, remote=False, remote_user="root", remote_host=None, debug=False
):
	logger.info("Collecting Network Config for Guest %s", guest_id)
	if remote and not remote_host:
		raise ValueError("remote_host is required when calling as remote function")
	net_cfg = {}
	if get_guest_is_ct(guest_id):
		proc_cmd = "pct"
	else:
		proc_cmd = "qm"

	cmd_args = [f"/usr/sbin/{proc_cmd}", "config", str(guest_id), "--current"]
	if remote:
		cmd_args = ["/usr/bin/ssh", f"{remote_user}@{remote_host}"] + cmd_args
	if debug:
		logger.debug(cmd_args)
	with subprocess.Popen(cmd_args, stdout=subprocess.PIPE) as proc:
		proc_o, proc_e = proc.communicate()
		if proc.returncode != 0:
			raise Exception(
				f"Bad command return code ({proc.returncode}).",
				proc_o.decode(),
				proc_e.decode(),
			)
		for line in proc_o.decode().split("\n"):
			line = line.rstrip()
			if re.search(r"^net[0-9]+:.*$", line):
				line_split = line.split(": ")
				net_index = line_split[0].lstrip("net")
				net_opts = line_split[-1].split(",")
				net_opts_parsed = {}
				for o in net_opts:
					k, v = o.split("=")
					net_opts_parsed[k] = v
				net_cfg[int(net_index)] = net_opts_parsed
		return net_cfg


def is_valid_guest_disk_type(
	label: str,
	disk_data: dict,
	exclude_media=True
) -> bool:
	if re.sub(r"[0-9]+", "", label) not in DISK_TYPES:
		return False
	if "raw_values" in disk_data:
		is_cloudinit = "cloudinit" in " ".join(disk_data["raw_values"])
	else:
		is_cloudinit = False
	if exclude_media and "media" in disk_data and not is_cloudinit:
		return False
	return True


def rename_guest_replication_jobs(old_id: int, new_id: int) -> None:
	"""
	Renames Replication Jobs in the default PVE Replication Config File
	This function is NOT RECOMMENDED as it does not modify remote replicated disks.
	"""
	logger = logging.getLogger()
	# Rename disk in Guest Configuration
	logger.info(
		"Changing replication jobs for Guest %s to %s in %s",
		old_id,
		new_id,
		PVE_CFG_REPLICATION,
	)
	sed_regex = rf"s/^local: {old_id}-\(.*\)$/local: {new_id}-\1/g"
	rpl_cmd_args = [
		"/usr/bin/sed",
		"-i",
		sed_regex,  # Sed F String Regex
		PVE_CFG_REPLICATION,
	]
	logger.debug("Executing command:" + " ".join(rpl_cmd_args))
	with subprocess.Popen(rpl_cmd_args, stdout=subprocess.PIPE) as proc:
		proc_o, proc_e = proc.communicate()
		if proc.returncode != 0:
			raise Exception(
				f"Bad command return code ({proc.returncode}).",
				proc_o.decode(),
				proc_e.decode(),
			)
	return


def get_guest_replication_jobs(old_id: int) -> dict:
	"""
	Uses Proxmox FUSE Volume data, does not require remote/ssh arguments.
	"""
	if not isinstance(old_id, int) and not int(old_id):
		raise ValueError("old_id must be of type int.")
	else:
		old_id = int(old_id)

	logger = logging.getLogger()
	jobs = {}

	with open(PVE_CFG_REPLICATION, "r") as replication_cfg:
		replication_job = None
		vmid = None
		for line in replication_cfg.readlines():
			line = line.strip()
			if len(line) < 1:
				continue

			if line.startswith("local:"):
				replication_job = line.split(": ")[1]
				vmid = int(replication_job.split("-")[0])
				if vmid == old_id:
					jobs[replication_job] = {}

			if vmid == old_id:
				try:
					_key, _value = line.split(sep=None, maxsplit=1)
					jobs[replication_job][_key] = _value
				except:
					print(line)
					raise
	return jobs


def get_guest_replication_statuses(
	guest_id: int, remote_args: list | None = None, raise_exception=False
) -> dict:
	"""
	:return: Dictionary with id:status pairs
	:rtype: dict
	"""
	cmd = f"pvesr status --guest {guest_id}"
	if remote_args:
		cmd = remote_args + cmd.split()
	data = {}
	job_statuses = None
	if raise_exception:
		job_statuses = subprocess.check_output(cmd)
	else:
		try:
			job_statuses = subprocess.check_output(cmd)
		except:
			pass
	if job_statuses:
		job_statuses = job_statuses.decode("utf-8").splitlines()
		job_statuses.pop(0)
		for line in job_statuses:
			_job_idx = 0
			_status_idx = -1
			_parsed_line = line.split()
			data[_parsed_line[_job_idx]] = _parsed_line[_status_idx]
	return data


def parse_guest_disk(disk_name, disk_values, vmstate=False):
	logger = logging.getLogger()
	logging.info(f"Parsing disk {disk_name}")
	if "raw_values" in disk_values:
		if len(disk_values["raw_values"]) != 1:
			logger.error("Bad Parsing.")
			logger.error(
				"Disk %s has more than one path (%s).",
				disk_name,
				disk_values["raw_values"],
			)
			logger.error("Path Array Length: %s", len(disk_values["raw_values"]))
			raise ValueError(disk_values["raw_values"])
		_raw_values = disk_values["raw_values"][0]
		_split_values = _raw_values.split(":")
		logger.info("%s: %s", disk_name, _raw_values)
		return {
			"interface": disk_name,
			"raw_values": _raw_values,
			"storage": _split_values[0],
			"name": _split_values[1],
		}
	elif vmstate:
		_split_values = disk_values.split(":")
		logger.info("%s: %s", disk_name, disk_values)
		return {
			"interface": disk_name,
			"storage": _split_values[0],
			"name": _split_values[1],
		}
	return None
