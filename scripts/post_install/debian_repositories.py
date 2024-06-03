#!/usr/bin/env python3
if __name__ == "__main__":
	raise Exception("This python script cannot be executed individually, please use main.py")

import os, sys, subprocess, signal
from core.signal_handlers.sigint import graceful_exit
signal.signal(signal.SIGINT, graceful_exit)

from core.debian import os_release
from core.utils.yes_no_input import yes_no_input
from core.format.colors import bcolors, print_c
from .apt_sources.debian import DEB_LISTS
SOURCES_LIST = "/etc/apt/sources.list"
SOURCES_LIST_DIR = "/etc/apt/sources.list.d"

def main():
	release_info = os_release.get_data()
	if not os_release.is_valid_version(release_info):
		print_c(bcolors.L_RED, f'Unsupported OS Distribution ({release_info["id"].capitalize()}).')
		sys.exit(1)
	debian_distribution = release_info["version_codename"]

	###################################### CHOICES #######################################
	# Setting debian sources
	reset_debian_sources = yes_no_input(
		msg="Do you wish to reset the Debian Sources?",
		input_default=True
	)
	######################################################################################

	# Debian SRCs
	if reset_debian_sources:
		with open("/etc/apt/sources.list", "w") as debian_apt_lists:
			debian_apt_lists.write(DEB_LISTS[debian_distribution].format(debian_distribution))
	print_c(bcolors.BLUE, "Debian Sources Set.")

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
