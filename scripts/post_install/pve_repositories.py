#!/usr/bin/env python3
if __name__ == "__main__":
	raise Exception("This python script cannot be executed individually, please use main.py")

import os
import sys
import subprocess
import signal
from core.signal_handlers.sigint import graceful_exit
signal.signal(signal.SIGINT, graceful_exit)

MIN_VERSION = "8.0.0"
from core.debian import os_release
from core.proxmox.manager import pve_version_exists, get_pve_version
from core.exceptions.base import DependencyMissing
from core.utils.yes_no_input import yes_no_input
from core.format.colors import bcolors, print_c
from .apt.sources.ceph import CEPH_SOURCES
from .apt.sources.pve import SRC_PVE_ENTERPRISE, SRC_PVE_NO_SUBSCRIPTION
from .apt.sources.debian import SRC_DEB_BOOKWORM_SYNTAX
SOURCES_LIST = "/etc/apt/sources.list"
SOURCES_LIST_DIR = "/etc/apt/sources.list.d"
SOURCES_LIST_PVE_NS = f"{SOURCES_LIST_DIR}/pve-no-subscription.list"
SOURCES_LIST_PVE_EN = f"{SOURCES_LIST_DIR}/pve-enterprise.list"
SOURCES_LIST_CEPH = f"{SOURCES_LIST_DIR}/ceph.list"

def main():
	release_info = os_release.get_data()
	if not os_release.is_valid_version(release_info):
		print_c(bcolors.L_RED, f'Unsupported OS Distribution ({release_info["id"].capitalize()}).')
		sys.exit(1)
	debian_distribution = release_info["version_codename"]

	# Check if proxmox version valid (>8.0)
	if not pve_version_exists: raise DependencyMissing()
	pve_version = get_pve_version().split(".")
	min_pve_version = MIN_VERSION.split(".")
	if (
		int(pve_version[0]) < int(min_pve_version[0]) or
		int(pve_version[1]) < int(min_pve_version[1])
	):
		print_c(bcolors.L_RED, f'Unsupported Proxmox VE Version ({".".join(pve_version)}).')
		sys.exit(1)

	###################################### CHOICES #######################################
	# Setting debian sources
	reset_debian_sources = yes_no_input(
		msg="Do you wish to check the Debian Sources?",
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
		ha_services = [
			"pve-ha-lrm",
			"pve-ha-crm",
			"corosync",
		]
		print_c(bcolors.L_YELLOW, "Running commands:")
		for c in ha_services:
			print(f"Disabling {c}.service")
			c = f"systemctl disable --now {c}"
			print(c)
			try: subprocess.call(c.split())
			except: raise
		print_c(bcolors.BLUE, "HA Services disabled.")
	######################################################################################

	# Debian SRCs
	if reset_debian_sources:
		with open("/etc/apt/sources.list", "w") as debian_apt_lists:
			debian_apt_lists.write(SRC_DEB_BOOKWORM_SYNTAX.format(debian_distribution))
		print_c(bcolors.BLUE, "Debian Sources Set.")

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
	print_c(bcolors.BLUE, "Proxmox VE Sources Set.")

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
		print_c(bcolors.BLUE, "CEPH Sources Set.")
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
			try: subprocess.call(c.split())
			except: raise
	print_c(bcolors.L_GREEN, "Update Complete.")

	# Offer Reboot
	if yes_no_input(
		msg="Do you wish to reboot now?",
		input_default=False
	):
		print_c(bcolors.L_YELLOW, "Rebooting System.")
		os.system("reboot")
