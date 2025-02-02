import subprocess
import json
from typing import TypedDict, Required, NotRequired, Literal

# See https://pve.proxmox.com/pve-docs/api-viewer/#/cluster/backup/{id} for more arguments
BackupJob = TypedDict(
    "BackupJob",
    {
		"id": Required[str],
		"comment": NotRequired[str],
		"vmid": NotRequired[str],
		"all": NotRequired[bool],
		"mode": NotRequired[
			Literal["snapshot", "suspend", "stop"]
		],
		"bwlimit": NotRequired[int],
		"compress": NotRequired[Literal[0, 1, "gzip", "lzo", "zstd"]],
    },
)

def get_all_backup_jobs() -> list[dict]:
	"""
	PVE API Based Function, does not require remote/ssh arguments.
	"""
	jobs = subprocess.check_output(
		"pvesh get /cluster/backup --output-format json-pretty".split()
	)
	return json.loads(jobs)

def get_backup_job(job_id: str) -> dict:
	"""
	PVE API Based Function, does not require remote/ssh arguments.
	"""
	jobs = subprocess.check_output(
		f"pvesh get /cluster/backup/{job_id} --output-format json-pretty".split()
	)
	return json.loads(jobs)

def set_backup_attrs(job_id: str, data: dict, raise_exception=False) -> None | list:
	"""
	Sets a dictionary of attributes on a backup job.
	PVE API Based Function, does not require remote/ssh arguments.

	:param str job_id: Backup Job ID, contains letters and numbers.
	:param dict data: Data to set on the backup job.
	:param bool raise_exception: Whether to raise an exception on pvesh subprocess error.
	:return: Keys that returned an error
	:rtype: None | list
	"""
	errors = []
	for k, v in data.items():
		attr_call = subprocess.call(f"pvesh set /cluster/backup/{job_id} -{k} {v}".split())
		if not raise_exception and attr_call > 0:
			errors.append(k)
	if len(errors) < 1:
		return None
	return errors
