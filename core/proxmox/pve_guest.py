# Author: Dylan Blanqué
# BR Consulting S.R.L. 2024
import os, re, logging, subprocess
from .pve_constants import PVE_CFG_NODES_DIR

logger = logging.getLogger()

def get_guest_exists(guest_id: int):
	guest_id = int(guest_id)
	if not os.path.isdir(PVE_CFG_NODES_DIR): return False
	guest_list = get_all_guests()
	return guest_id in guest_list["vm"] or guest_id in guest_list["ct"]

def get_guest_cfg(
		guest_id,
		get_host=False,
		get_type=False,
		get_as_dict=False
	) -> str:
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
				guest_type = "vm"
				if subp == "lxc": guest_type = "ct"
				if get_as_dict: 
					return {
						"path":p,
						"host":h,
						"type":guest_type,
						"subpath":subp
					}
				if get_host: return h
				if get_type: return subp
				return p

def get_guest_is_ct(guest_id):
	guest_type = get_guest_cfg(guest_id=guest_id, get_host=False, get_type=True)
	if guest_type == "qemu-server":
		return False
	return True


def get_guest_status(guest_id: int, remote_args=None):
	# CT
	if get_guest_is_ct(guest_id):
		cmd_args = ["pct"]
	# VM
	else:
		cmd_args = ["qm"]
	cmd_args = cmd_args + ["status", str(guest_id)]
	if remote_args:
		cmd_args = remote_args + cmd_args
	proc = subprocess.Popen(cmd_args, stdout=subprocess.PIPE)
	proc_o, proc_e = proc.communicate()
	if proc.returncode != 0:
		raise Exception(f"Bad command return code ({proc.returncode}).", proc_o.decode(), proc_e.decode())
	result = proc_o.decode().split("\n")
	return result[0].strip().split(": ")[-1]

GUEST_CONF_REGEX = r"^[0-9]+.conf$"
def get_all_guests(filter_ids: list | dict=list()):
	if type(filter_ids) == dict:
		filter_ids = list(filter_ids.keys())
	guests = dict()
	guests["vm"] = list()
	guests["ct"] = list()
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

def parse_net_opts_to_string(net_opts: dict):
	r = None
	for k, v in net_opts.items():
		if not r: r = f"{k}={v}"
		else: r = f"{r},{k}={v},"
	return r.rstrip(",").replace(",,",",")

def parse_guest_cfg(guest_id, remote=False, remote_user="root", remote_host=None, debug=False) -> dict:
	logger.info(f"Collecting Config for Guest {guest_id}")
	if remote and not remote_host:
		raise ValueError("remote_host is required when calling as remote function")
	guest_cfg = dict()
	if get_guest_is_ct(guest_id): proc_cmd = "pct"
	else: proc_cmd = "qm"

	cmd_args = [f'/usr/sbin/{proc_cmd}', "config", str(guest_id), "--current"]
	if remote: cmd_args = ["/usr/bin/ssh", f"{remote_user}@{remote_host}"] + cmd_args
	if debug: logger.debug(cmd_args)
	proc = subprocess.Popen(cmd_args, stdout=subprocess.PIPE)
	proc_o, proc_e = proc.communicate()
	if proc.returncode != 0:
		raise Exception(f"Bad command return code ({proc.returncode}).", proc_o.decode(), proc_e.decode())
	if debug: logger.debug("Showing parsed Guest config lines:")
	for line in proc_o.decode().split("\n"):
		line = line.rstrip()
		if debug: logger.debug(line)
		line_split = line.split(": ")
		option_k = line_split[0]
		option_v = line_split[-1]
		# If Option has multiple key/value pairs in it (Comma separated)
		if "," in option_v:
			if not option_k in guest_cfg: guest_cfg[option_k] = dict()
			option_v = option_v.replace(",,",",").split(",")
			for sub_v in option_v:
				# Guess Separator
				fs = None
				for sep in ["=", ":"]:
					if sep in sub_v and sub_v.count(sep) == 1: fs = sep
				# If separator is equal assume it's not a Volume/Disk path.
				if fs == "=":
					k, v = sub_v.split(fs)
					try: v = int(v)
					except: pass
					guest_cfg[option_k][k] = v
				# If it's a raw value
				else:
					if not sub_v or sub_v.lower() == "none": continue
					if not "raw_values" in guest_cfg[option_k]:
						guest_cfg[option_k]["raw_values"] = list()
					try: sub_v = int(sub_v)
					except: pass
					guest_cfg[option_k]["raw_values"].append(sub_v)
		else:
			try: option_v = int(option_v)
			except: pass
			guest_cfg[option_k] = option_v
	return guest_cfg

def parse_guest_netcfg(guest_id, remote=False, remote_user="root", remote_host=None, debug=False):
	logger.info(f"Collecting Network Config for Guest {guest_id}")
	if remote and not remote_host:
		raise ValueError("remote_host is required when calling as remote function")
	net_cfg = dict()
	if get_guest_is_ct(guest_id): proc_cmd = "pct"
	else: proc_cmd = "qm"

	cmd_args = [f'/usr/sbin/{proc_cmd}', "config", str(guest_id), "--current"]
	if remote: cmd_args = ["/usr/bin/ssh", f"{remote_user}@{remote_host}"] + cmd_args
	if debug: logger.debug(cmd_args)
	proc = subprocess.Popen(cmd_args, stdout=subprocess.PIPE)
	proc_o, proc_e = proc.communicate()
	if proc.returncode != 0:
		raise Exception(f"Bad command return code ({proc.returncode}).", proc_o.decode(), proc_e.decode())
	for line in proc_o.decode().split("\n"):
		line = line.rstrip()
		if re.search(r"^net[0-9]+:.*$", line):
			line_split = line.split(": ")
			net_index = line_split[0].lstrip("net")
			net_opts = line_split[-1].split(",")
			net_opts_parsed = dict()
			for o in net_opts:
				k, v = o.split("=")
				net_opts_parsed[k] = v
			net_cfg[int(net_index)] = net_opts_parsed
	return net_cfg
