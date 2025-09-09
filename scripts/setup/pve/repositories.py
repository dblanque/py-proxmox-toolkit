#!/usr/bin/python3
if __name__ == "__main__":
	raise Exception(
		"This python script cannot be executed individually, please use main.py"
	)

import os
import sys
import subprocess
import signal
from core.signal_handlers.sigint import graceful_exit
from core.proxmox.manager import pve_version_exists, get_pve_version
from core.exceptions.base import DependencyMissing
from core.utils.prompt import yes_no_input, prompt_reboot, prompt_update
from core.format.colors import bcolors, print_c
from ..debian.repositories import pre_checks, set_debian_sources
from ..apt.sources.ceph import CEPH_SOURCES
from ..apt.sources.pve import SRC_PVE_APT_FORMAT_MAP
from enum import StrEnum, auto

MIN_VERSION = "8.0.0"

SOURCES_LIST = "/etc/apt/sources.list"
SOURCES_LIST_DIR = "/etc/apt/sources.list.d"
SOURCES_LIST_PVE_NS = f"{SOURCES_LIST_DIR}/pve-no-subscription.list"
SOURCES_LIST_PVE_EN = f"{SOURCES_LIST_DIR}/pve-enterprise.list"
SOURCES_LIST_CEPH = f"{SOURCES_LIST_DIR}/ceph.list"

class SupportedCephVersion(StrEnum):
	QUINCY = auto()
	REEF = auto()
	SQUID = auto()

def prompt_ceph_version() -> SupportedCephVersion:
	"""Prompts user for required CEPH Version Codename.

	Returns:
		SupportedCephVersion: Enum containing the codename as 
		key-value pair (upper-case, lower-case respectively)
	"""
	CEPH_CHOICES = SupportedCephVersion.__members__.values()
	CEPH_CHOICES_STR = ", ".join(CEPH_CHOICES)
	print("Available CEPH Versions: %s" % (CEPH_CHOICES_STR))
	while True:
		r = input("Please enter the desired CEPH Version: ")
		try:
			r = SupportedCephVersion(r)
			return r
		except ValueError:
			print(f"Please enter a valid choice (one of {CEPH_CHOICES_STR}).")

def main(**kwargs):
	signal.signal(signal.SIGINT, graceful_exit)
	debian_distribution = pre_checks()
	set_debian_sources(debian_distribution)

	# Check if proxmox version valid (>8.0)
	if not pve_version_exists:
		raise DependencyMissing()
	pve_version = get_pve_version().split(".")
	min_pve_version = MIN_VERSION.split(".")
	if int(pve_version[0]) < int(min_pve_version[0]) or int(pve_version[1]) < int(
		min_pve_version[1]
	):
		print_c(
			bcolors.L_RED, f"Unsupported Proxmox VE Version ({'.'.join(pve_version)})."
		)
		sys.exit(1)

	###################################### CHOICES #######################################
	# Setting PVE No-Subscription or Enterprise Sources
	pve_src_no_subscription = yes_no_input(
		msg="Do you wish to use the PVE No-Subscription Repositories?",
		input_default=True,
	)
	# Setting CEPH No-Subscription or Enterprise Sources
	use_ceph = yes_no_input(
		msg="Do you wish to add the CEPH Repositories?", input_default=False
	)
	if use_ceph:
		ceph_version = prompt_ceph_version()
		ceph_src_no_subscription = yes_no_input(
			msg="Do you wish to use the CEPH No-Subscription Repositories?",
			input_default=True,
		)
	# Disabling HA (Default NO)
	if yes_no_input(
		msg="Do you wish to disable High-Availability Services?", input_default=False
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
	sources_formats = SRC_PVE_APT_FORMAT_MAP[debian_distribution]
	if pve_src_no_subscription:
		pve_list_file = SOURCES_LIST_PVE_NS
		pve_list_data = sources_formats["no-subscription"]
		pve_list_delete = SOURCES_LIST_PVE_EN
	else:
		pve_list_file = SOURCES_LIST_PVE_EN
		pve_list_data = sources_formats["enterprise"]
		pve_list_delete = SOURCES_LIST_PVE_NS

	with open(pve_list_file, "w") as pve_apt_lists:
		pve_apt_lists.write(pve_list_data.format(debian_distribution))
	if os.path.exists(pve_list_delete):
		os.remove(pve_list_delete)
	print_c(bcolors.L_GREEN, "Proxmox VE Sources Set.")

	# CEPH SRCs
	if use_ceph:
		_ceph_sources = CEPH_SOURCES[ceph_version.name]
		with open(SOURCES_LIST_CEPH, "w") as ceph_apt_lists:
			if ceph_src_no_subscription:
				ceph_list_data = _ceph_sources["no-subscription"]
			else:
				ceph_list_data = _ceph_sources["enterprise"]
			ceph_apt_lists.write(ceph_list_data)
		print_c(bcolors.L_GREEN, "CEPH Sources Set.")
	else:
		if os.path.exists(SOURCES_LIST_CEPH):
			os.remove(SOURCES_LIST_CEPH)
		print_c(bcolors.L_BLUE, "CEPH Sources Skipped.")

	# Update Proxmox
	prompt_update()

	# Offer Reboot
	prompt_reboot()
