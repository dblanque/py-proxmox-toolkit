import subprocess
import json

def get_all_backup_jobs() -> list[dict]:
	jobs = subprocess.check_output(
		"pvesh get /cluster/backup --output-format json-pretty".split()
	)
	return json.loads(jobs)

def get_backup_job(job_id: str) -> dict:
	jobs = subprocess.check_output(
		f"pvesh get /cluster/backup/{job_id} --output-format json-pretty".split()
	)
	return json.loads(jobs)

def set_backup_attrs(job_id: str, data: dict, raise_exception=False) -> None | list:
	"""
	Sets a dictionary of attributes on a backup job through the PVE API (using pvesh).

	:param str job_id: Backup Job ID, contains letters and numbers.
	:param dict data: Data to set on the backup job.
	:param bool raise_exception: Whether to raise an exception on pvesh subprocess error.
	:return: Keys that returned an error
	:rtype: None | list
	"""
	errors = []
	for k, v in data.items():
		with subprocess.call(f"pvesh set /cluster/backup/{job_id} -{k} {v}".split()) as attr_call:
			if not raise_exception and attr_call > 0:
				errors.append(k)
	if len(errors) < 1:
		return None
	return errors
