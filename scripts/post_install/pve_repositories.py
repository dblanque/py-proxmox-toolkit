#!/usr/env/python3
if __name__ != "__main__":
	raise ImportError("This python script cannot be imported.")

import os, sys, subprocess, signal
VENV_DIR = os.path.abspath(os.environ['VIRTUAL_ENV']) or None
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
if not VENV_DIR:
	print(VENV_DIR)
	raise Exception('Could not append VENV_DIR to PATH')
sys.path.append(VENV_DIR)
sys.path.append(SCRIPT_DIR)

MIN_VERSION = "8.0.0"
from py_pve_toolkit.debian import os_release
from py_pve_toolkit.proxmox.pve_manager import pve_version_exists, get_pve_version
from py_pve_toolkit.exceptions.base import DependencyMissing
from py_pve_toolkit.utils.yes_no_input import yes_no_input
from apt_sources.ceph import CEPH_SOURCES
from apt_sources.pve import SRC_PVE_ENTERPRISE,	SRC_PVE_NO_SUBSCRIPTION
from apt_sources.debian import SRC_DEB_BOOKWORM_SYNTAX
SOURCES_LIST = "/etc/apt/sources.list"
SOURCES_LIST_DIR = "/etc/apt/sources.list.d"
SOURCES_LIST_PVE_NS = f"{SOURCES_LIST_DIR}/pve-no-subscription.list"
SOURCES_LIST_PVE_EN = f"{SOURCES_LIST_DIR}/pve-enterprise.list"
SOURCES_LIST_CEPH = f"{SOURCES_LIST_DIR}/ceph.list"

def sigint_handler(sig, frame):
	print('\nCtrl+C Received, cancelling script.')
	sys.exit(0)
signal.signal(signal.SIGINT, sigint_handler)

def main():
	# Check if proxmox version valid (>8.0)
	release_info = os_release.get_data()
	if release_info["id"] != "debian":
		print(f'Unsupported OS Distribution ({release_info["id"].capitalize()}).')
		sys.exit(1)
	debian_distribution = release_info["version_codename"]
	if not pve_version_exists: raise DependencyMissing()
	pve_version = get_pve_version().split(".")
	min_pve_version = MIN_VERSION.split(".")
	if (
		int(pve_version[0]) < int(min_pve_version[0]) or
		int(pve_version[1]) < int(min_pve_version[1])
	):
		print(f'Unsupported Proxmox VE Version ({".".join(pve_version)}).')
		sys.exit(1)
	###################################### CHOICES #######################################
	# Setting debian sources
	reset_debian_sources = yes_no_input(
		msg="Do you wish check the Debian Sources?",
		input_default=True
	)
	# Setting PVE No-Subscription or Enterprise Sources
	pve_src_no_subscription = yes_no_input(
		msg="Do you wish to use the PVE No-Subscription Repositories?",
		input_default=True
	)
	# Setting CEPH No-Subscription or Enterprise Sources
	use_ceph = yes_no_input(
		msg="Do you wish to add the CEPH Repositories?",
		input_default=False
	)
	if use_ceph:
		ceph_reef = yes_no_input(
			msg="Do you wish to use CEPH REEF instead of CEPH QUINCY?",
			input_default=True
		)
		ceph_src_no_subscription = yes_no_input(
			msg="Do you wish to use the CEPH No-Subscription Repositories?",
			input_default=True
		)
	# Disabling HA (Default NO)
	if yes_no_input(
		msg="Do you wish to disable High-Availability Services?",
		input_default=False
	): 
		ha_cmds = [
			"systemctl disable --now pve-ha-lrm",
			"systemctl disable --now pve-ha-crm",
			"systemctl disable --now corosync",
		]
		print("Running commands:")
		for c in ha_cmds:
			print(c)
			try: subprocess.call(c.split())
			except: raise
	######################################################################################

	# Debian SRCs
	if reset_debian_sources:
		with open("/etc/apt/sources.list", "w") as debian_apt_lists:
			debian_apt_lists.write(SRC_DEB_BOOKWORM_SYNTAX.format(debian_distribution))

	# PVE SRCs
	if pve_src_no_subscription:
		pve_list_file = SOURCES_LIST_PVE_NS
		pve_list_data = SRC_PVE_NO_SUBSCRIPTION
		pve_list_delete = SOURCES_LIST_PVE_EN
	else:
		pve_list_file = SOURCES_LIST_PVE_EN
		pve_list_data = SRC_PVE_ENTERPRISE
		pve_list_delete = SOURCES_LIST_PVE_NS
	
	with open(pve_list_file, "w") as pve_apt_lists:
		pve_apt_lists.write(pve_list_data.format(debian_distribution))
	if os.path.exists(pve_list_delete): os.remove(pve_list_delete)

	# CEPH SRCs
	if use_ceph:
		with open(SOURCES_LIST_CEPH, "w") as ceph_apt_lists:
			if ceph_reef: # REEF
				if ceph_src_no_subscription:
					ceph_list_data = CEPH_SOURCES["REEF"]["NO_SUBSCRIPTION"]
				else:
					ceph_list_data = CEPH_SOURCES["REEF"]["ENTERPRISE"]
			else: # QUINCY
				if ceph_src_no_subscription:
					ceph_list_data = CEPH_SOURCES["QUINCY"]["NO_SUBSCRIPTION"]
				else:
					ceph_list_data = CEPH_SOURCES["QUINCY"]["ENTERPRISE"]
			ceph_apt_lists.write(ceph_list_data)
	else:
		if os.path.exists(SOURCES_LIST_CEPH): os.remove(SOURCES_LIST_CEPH)

	# Update Proxmox
	if yes_no_input(
		msg="Do you wish to perform an update?",
		input_default=True
	):
		update_cmds = [
			"apt-get update -y",
			"apt-get dist-upgrade --fix-missing --fix-broken -y"
		]
		for c in update_cmds:
			proc = subprocess.Popen(
				c.split(), 
				stdout=subprocess.PIPE
			)
			while proc.poll() is None:
				l = proc.stdout.readline() # This blocks until it receives a newline.
				print(l)
			proc_o, proc_e = proc.communicate()
			if proc.returncode != 0:
				raise Exception(f"Bad command return code ({proc.returncode}).", proc_e.decode())

	# Offer Reboot
	if yes_no_input(
		msg="Do you wish to reboot now?",
		input_default=False
	): os.system("reboot")

if __name__ == "__main__": main()