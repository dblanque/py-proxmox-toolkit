# Author: Dylan Blanqué
# BR Consulting S.R.L. 2024
import logging
import subprocess
from .constants import PVE_CFG_STORAGE
from .guests import get_guest_cfg_path
from dataclasses import dataclass

logger = logging.getLogger()

BASH_PIPE="|"
PATH_ASSOC = {
	"lvm":"vgname",
	"lvmthin":"vgname",
	"zfspool":"pool",
	"dir":"path",
	"cephfs":"path",
	"rbd":"pool",
}

@dataclass
class PVEStorage:
	"""PVE Storage Class."""
	name: str
	type: str
	path: str

	def __str__(self):
		return self.name

	def reassign_disk(self, disk_name: str, new_guest_id: int, new_guest_cfg: str=None, remote_args=None, dry_run=False):
		cmd_args = None
		lv_tags = False
		guest_id = disk_name.split("-")[1]
		guest_id = int(guest_id)
		id_prefix = False
		old_disk_path = None
		new_disk_path = None

		# CT/LXC Subvolumes have an ID Prefix in the disk name
		if f"{guest_id}/" in disk_name:
			id_prefix = True
			disk_name = disk_name.replace(f"{guest_id}/", "")
		new_disk_name = disk_name.replace(f"-{guest_id}-", f"-{new_guest_id}-")
		if self.type in ["lvm", "lvmthin"]:
			# lvrename \"$storpath\" \"$diskname\" \"$diskname_new\"
			cmd_args = [
				"/usr/sbin/lvrename",
				self.path,
				disk_name,
				new_disk_name
			]
			if hasattr(self, "tagged_only"):
				lv_tags = True if self.tagged_only else False
		elif self.type == "zfspool":
			# zfs rename \"$storpath/$diskname\" \"$storpath/$diskname_new\"
			cmd_args = [
				"/usr/sbin/zfs",
				"rename",
				f"{self.path}/{disk_name}",
				f"{self.path}/{new_disk_name}"
			]
		elif self.type in ["dir", "cephfs"]:
			# mv "$storpath/images/${!1}/$diskname" "$storpath/images/${!2}/"
			old_disk_path = f"{self.path}/images/{guest_id}"
			new_disk_path = f"{self.path}/images/{new_guest_id}"
			cmd_args = [
				"/usr/bin/mv",
				f"{self.path}/images/{guest_id}/{disk_name}",
				f"{new_disk_path}/{new_disk_name}",
			]
			# Attempt to create unexisting dir
			logger.debug("Ensuring path exists (%s).", new_disk_path)
			if dry_run:
				logger.info("mkdir %s", new_disk_path)
			else:
				mkdir_args = ["/usr/bin/mkdir", "-p", new_disk_path]
				if remote_args: mkdir_args = remote_args + mkdir_args
				with subprocess.Popen(mkdir_args, stdout=subprocess.PIPE) as proc:
					proc_o, proc_e = proc.communicate()
					if proc.returncode != 0:
						raise Exception(f"Bad command return code ({proc.returncode}).", proc_o.decode(), proc_e.decode())
		elif self.type == "rbd":
			cmd_args = [
				"/usr/bin/rbd",
				"mv",
				f"{self.path}/{disk_name}",
				f"{self.path}/{new_disk_name}",
			]
		else:
			raise Exception(f"Unsupported Storage Type {self.type}")

		if remote_args:
			cmd_args = remote_args + cmd_args
		# ! Rename disk in Storage
		logger.debug("Changing disk name in storage.")
		if dry_run:
			logger.info(" ".join(cmd_args))
		else:
			logger.debug(" ".join(cmd_args))
			with subprocess.Popen(cmd_args, stdout=subprocess.PIPE) as proc:
				proc_o, proc_e = proc.communicate()
				if proc.returncode != 0:
					raise Exception(
						f"Bad command return code ({proc.returncode}).",
						proc_o.decode(),
						proc_e.decode()
					)

		# ! Rename disk in Guest Configuration
  		# Does not require SSH
		guest_cfg_path = new_guest_cfg if new_guest_cfg else get_guest_cfg_path(guest_id=guest_id)
		sed_regex = None
		# LXC ID Prefix on Diskname
		if id_prefix:
			sed_regex = rf"s@:{guest_id}/{disk_name}@:{new_guest_id}/{new_disk_name}@g"
		# VM has no Prefix
		else:
			sed_regex = rf"s@:{disk_name}@:{new_disk_name}@g"
		sed_cmd_args = [
			"/usr/bin/sed",
			"-i",
			sed_regex,
			guest_cfg_path
		]
		sed_cmd_args = sed_cmd_args
		logger.debug("Changing disk in Guest Configuration (%s) from %s to %s.",
			   		guest_cfg_path, disk_name, new_disk_name)
		if dry_run:
			logger.info(" ".join(sed_cmd_args))
		else:
			logger.debug(" ".join(sed_cmd_args))
			with subprocess.Popen(sed_cmd_args, stdout=subprocess.PIPE) as proc:
				proc_o, proc_e = proc.communicate()
				if proc.returncode != 0:
					raise Exception(f"Bad command return code ({proc.returncode}).", proc_o.decode(), proc_e.decode())

		# ! Change LV Tags
		if lv_tags:
			suffix = "-cloudinit" if new_disk_name.endswith("-cloudinit") else "-disk-"
			lvtag_cmd_args = [
				"/usr/sbin/lvchange",
				"--deltag",
				disk_name,
				"--add-tag",
				f"{self.name}-{new_disk_name.split(suffix)[0]}",
				f"{self.name}/{new_disk_name}"
			]
			if remote_args:
				lvtag_cmd_args = remote_args + lvtag_cmd_args
			if dry_run:
				logger.info(lvtag_cmd_args)
			else:
				with subprocess.Popen(lvtag_cmd_args, stdout=subprocess.PIPE) as proc:
					proc_o, proc_e = proc.communicate()
					if proc.returncode != 0:
						logger.error("Could not change LV Tags properly, beware of checking them after the script finishes.")
		if old_disk_path:
			logger.debug("Attempting to remove %s", old_disk_path)
			try:
				rmdir_args = ["/usr/bin/rmdir", old_disk_path]
				if remote_args: rmdir_args = remote_args + rmdir_args
				with subprocess.Popen(rmdir_args, stdout=subprocess.PIPE) as proc:
					proc_o, proc_e = proc.communicate()
					if proc.returncode != 0:
						raise Exception(f"Bad command return code ({proc.returncode}).", proc_o.decode(), proc_e.decode())
			except:
				logger.error("Could not delete prior Guest ID Images Path (%s)", old_disk_path)
		return

def get_storage_cfg(storage_name: str) -> PVEStorage:
	sed_regex = rf"/.*: {storage_name}$/,/^$/p"
	cmd_args = [
		"/usr/bin/sed", "-n", sed_regex, PVE_CFG_STORAGE,
	]
	with subprocess.Popen(cmd_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as proc:
		proc_o, proc_e = proc.communicate()
		if proc.returncode != 0:
			raise Exception(f"Bad command return code ({proc.returncode}).", proc_o.decode(), proc_e.decode())
		storage = {}
		for line in proc_o.decode().split("\n"):
			line = line.rstrip()
			if len(line) < 1: continue
			# Path Definition
			if ": " in line:
				line = line.split(": ")
				storage["type"] = line[0].strip()
				storage["name"] = line[1].strip()
			# Attribute Definitions
			else:
				line = line.split(" ")
				attr_key = line[0].strip()
				attr_val = line[1].strip()
				storage[attr_key] = attr_val
		if not storage["type"] in PATH_ASSOC:
			raise Exception(f"Storage type unsupported ({storage['type']})")
		path_def = PATH_ASSOC[storage["type"]]
		if not path_def in storage:
			raise Exception("Bad storage parameters, path definition not found.", storage)
		r = PVEStorage(
			name=storage["name"],
			type=storage["type"],
			path=storage[path_def]
		)
		try:
			for k, v in storage.items():
				if k in ["name", "type", path_def]: continue
				setattr(r, k, v)
		except:
			try: print(storage.__dict__())
			except: pass
			raise
		return r
