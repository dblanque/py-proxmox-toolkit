
def bin_exists(name):
	"""Check whether `name` is on PATH and marked as executable."""
	from shutil import which
	return which(name) is not None

def pve_version_exists() -> bool:
	return bin_exists("pveversion")

def get_pve_version(full=False) -> str:
	import subprocess
	proc = subprocess.Popen("pveversion", stdout=subprocess.PIPE)
	proc_o, proc_e = proc.communicate()
	if proc.returncode != 0:
		raise Exception(f"Bad command return code ({proc.returncode}).", proc_o.decode(), proc_e.decode())
	if full: return proc_o.decode('utf-8').strip()
	return proc_o.decode('utf-8').strip().split("/")[1]
