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
from core.proxmox.manager import pve_version_exists, get_pve_version
from core.exceptions.base import DependencyMissing
from core.utils.prompt import yes_no_input, prompt_reboot, prompt_update
from core.format.colors import bcolors, print_c
from .debian_repositories import pre_checks, set_debian_sources
from .apt.sources.ceph import CEPH_SOURCES
from .apt.sources.pve import SRC_PVE_ENTERPRISE, SRC_PVE_NO_SUBSCRIPTION
SOURCES_LIST = "/etc/apt/sources.list"
SOURCES_LIST_DIR = "/etc/apt/sources.list.d"
SOURCES_LIST_PVE_NS = f"{SOURCES_LIST_DIR}/pve-no-subscription.list"
SOURCES_LIST_PVE_EN = f"{SOURCES_LIST_DIR}/pve-enterprise.list"
SOURCES_LIST_CEPH = f"{SOURCES_LIST_DIR}/ceph.list"

def main():
	debian_distribution = pre_checks()
	set_debian_sources(debian_distribution)

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
		print_c(bcolors.L_YELLOW, "Executing Commands:")
		for c in ha_services:
			print(f"Disabling {c}.service")
			c = f"systemctl disable --now {c}"
			print(c)
			subprocess.call(c.split())
		print_c(bcolors.BLUE, "HA Services disabled.")
	######################################################################################

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
	print_c(bcolors.L_GREEN, "Proxmox VE Sources Set.")

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
		print_c(bcolors.L_GREEN, "CEPH Sources Set.")
	else:
		if os.path.exists(SOURCES_LIST_CEPH): os.remove(SOURCES_LIST_CEPH)
		print_c(bcolors.L_BLUE, "CEPH Sources Skipped.")

	# Update Proxmox
	prompt_update()

	# Offer Reboot
	prompt_reboot()
