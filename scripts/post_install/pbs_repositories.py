#!/usr/bin/env python3
if __name__ == "__main__":
	raise Exception("This python script cannot be executed individually, please use main.py")

import os, sys, subprocess, signal
from core.signal_handlers.sigint import graceful_exit
signal.signal(signal.SIGINT, graceful_exit)

from core.debian import os_release
from core.utils.yes_no_input import yes_no_input
from core.format.colors import bcolors, print_c
from .apt.sources.pbs import SRC_PBS_ENTERPRISE, SRC_PBS_NO_SUBSCRIPTION
from .apt.sources.debian import SRC_DEB_BOOKWORM_SYNTAX
SOURCES_LIST = "/etc/apt/sources.list"
SOURCES_LIST_DIR = "/etc/apt/sources.list.d"
SOURCES_LIST_PBS_NS = f"{SOURCES_LIST_DIR}/pbs-no-subscription.list"
SOURCES_LIST_PBS_EN = f"{SOURCES_LIST_DIR}/pbs-enterprise.list"

def main():
	release_info = os_release.get_data()
	if not os_release.is_valid_version(release_info):
		print_c(bcolors.L_RED, f'Unsupported OS Distribution ({release_info["id"].capitalize()}).')
		sys.exit(1)
	debian_distribution = release_info["version_codename"]

	###################################### CHOICES #######################################
	# Setting debian sources
	reset_debian_sources = yes_no_input(
		msg="Do you wish to check the Debian Sources?",
		input_default=True
	)
	# Setting PBS No-Subscription or Enterprise Sources
	pbs_src_no_subscription = yes_no_input(
		msg="Do you wish to use the PBS No-Subscription Repositories?",
		input_default=True
	)

	# Debian SRCs
	if reset_debian_sources:
		with open("/etc/apt/sources.list", "w") as debian_apt_lists:
			debian_apt_lists.write(SRC_DEB_BOOKWORM_SYNTAX.format(debian_distribution))
		print_c(bcolors.BLUE, "Debian Sources Set.")

	# PBS SRCs
	if pbs_src_no_subscription:
		pbs_list_file = SOURCES_LIST_PBS_NS
		pbs_list_data = SRC_PBS_NO_SUBSCRIPTION
		pbs_list_delete = SOURCES_LIST_PBS_EN
	else:
		pbs_list_file = SOURCES_LIST_PBS_EN
		pbs_list_data = SRC_PBS_ENTERPRISE
		pbs_list_delete = SOURCES_LIST_PBS_NS

	with open(pbs_list_file, "w") as pbs_apt_lists:
		pbs_apt_lists.write(pbs_list_data.format(debian_distribution))
	if os.path.exists(pbs_list_delete): os.remove(pbs_list_delete)
	print_c(bcolors.BLUE, "Proxmox Backup Server Sources Set.")

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
