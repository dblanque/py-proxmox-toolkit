#!/usr/env/python3
if __name__ != "__main__":
	raise ImportError("This python script cannot be imported.")

import os
import sys
VENV_DIR = os.path.abspath(os.environ['VIRTUAL_ENV']) or None
if not VENV_DIR:
	print(VENV_DIR)
	raise Exception('Could not append VENV_DIR to PATH')
sys.path.append(VENV_DIR)

MIN_VERSION = "8.0.0"
import subprocess
from py_pve_toolkit.debian import os_release
from py_pve_toolkit.proxmox.pve_manager import pve_version_exists, get_pve_version
from py_pve_toolkit.exceptions.base import UnsupportedRelease, DependencyMissing
from py_pve_toolkit.utils.yes_no_input import yes_no_input
from sources.ceph import (
	SRC_CEPH_QUINCY_ENTERPRISE,
	SRC_CEPH_QUINCY_NO_SUBSCRIPTION,
	SRC_CEPH_REEF_ENTERPRISE,
	SRC_CEPH_REEF_NO_SUBSCRIPTION
)
from sources.pve import (
	SRC_PVE_ENTERPRISE,
	SRC_PVE_NO_SUBSCRIPTION
)
from sources.debian import SRC_DEB_BOOKWORM_SYNTAX
from packaging.version import Version
import os
SOURCES_LIST = "/etc/apt/sources.list"
SOURCES_LIST_DIR = "/etc/apt/sources.list.d"
SOURCES_LIST_PVE_NS = f"{SOURCES_LIST_DIR}/pve-no-subscription.list"
SOURCES_LIST_PVE_EN = f"{SOURCES_LIST_DIR}/pve-enterprise.list"
SOURCES_LIST_CEPH = f"{SOURCES_LIST_DIR}/ceph.list"

def main():
	# Check if proxmox version valid (>8.0)
	release_info = os_release.get_data()
	if release_info["id"] != "debian": raise UnsupportedRelease()
	debian_distribution = release_info["version_codename"]
	if not pve_version_exists: raise DependencyMissing()
	if Version(get_pve_version()) < Version(MIN_VERSION): raise UnsupportedRelease()

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
	ceph_reef = yes_no_input(
		msg="Do you wish to use CEPH REEF instead of CEPH QUINCY?",
		input_default=True
	)
	ceph_src_no_subscription = yes_no_input(
		msg="Do you wish to use the CEPH No-Subscription Repositories?",
		input_default=True
	)
	# Disabling HA (Default NO)
	disable_ha = yes_no_input(
		msg="Do you wish to disable High-Availability Services?",
		input_default=False
	)
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
	os.remove(pve_list_delete)

	# CEPH SRCs
	if use_ceph:
		with open(SOURCES_LIST_CEPH, "w") as ceph_apt_lists:
			if ceph_reef: # REEF
				if ceph_src_no_subscription:
					ceph_list_data = SRC_CEPH_REEF_NO_SUBSCRIPTION
				else:
					ceph_list_data = SRC_CEPH_REEF_ENTERPRISE
			else: # QUINCY
				if ceph_src_no_subscription:
					ceph_list_data = SRC_CEPH_QUINCY_NO_SUBSCRIPTION
				else:
					ceph_list_data = SRC_CEPH_QUINCY_ENTERPRISE
			ceph_apt_lists.write(ceph_list_data)
	else: os.remove(SOURCES_LIST_CEPH)

	# Update Proxmox
	if yes_no_input(
		msg="Do you wish to perform an update?",
		input_default=True
	):
		proc = subprocess.Popen(
			"apt-get dist-upgrade --fix-missing --fix-broken".split(), 
			stdout=subprocess.PIPE
		)
		proc_o, proc_e = proc.communicate()
		if proc.returncode != 0:
			raise Exception(f"Bad command return code ({proc.returncode}).", proc_o.decode(), proc_e.decode())
		print(proc_o.decode('utf-8').strip())

	# Offer Reboot
	if yes_no_input(
		msg="Do you wish to reboot now?",
		input_default=False
	): os.system("reboot")

if __name__ == "__main__": main()