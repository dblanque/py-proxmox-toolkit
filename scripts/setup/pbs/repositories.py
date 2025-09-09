#!/usr/bin/python3
if __name__ == "__main__":
	raise Exception(
		"This python script cannot be executed individually, please use main.py"
	)

import os
import signal
from core.signal_handlers.sigint import graceful_exit

from core.utils.prompt import yes_no_input, prompt_reboot, prompt_update
from core.format.colors import bcolors, print_c
from ..debian.repositories import pre_checks, set_debian_sources
from ..apt.sources.pbs import SRC_PBS_APT_FORMAT_MAP

SOURCES_LIST_DIR = "/etc/apt/sources.list.d"
SOURCES_LIST_PBS_NS = f"{SOURCES_LIST_DIR}/pbs-no-subscription"
SOURCES_LIST_PBS_EN = f"{SOURCES_LIST_DIR}/pbs-enterprise"

def backup_old_list_format(filename):
	if os.path.isfile(filename + ".list"):
		os.rename(filename + ".list", filename + ".list.bkp")

def main(**kwargs):
	signal.signal(signal.SIGINT, graceful_exit)
	debian_distribution = pre_checks()
	set_debian_sources(debian_distribution)

	###################################### CHOICES #######################################
	# Setting PBS No-Subscription or Enterprise Sources
	pbs_src_no_subscription = yes_no_input(
		msg="Do you wish to use the PBS No-Subscription Repositories?",
		input_default=True,
	)

	# PBS SRCs
	sources_formats = SRC_PBS_APT_FORMAT_MAP[debian_distribution]
	source_file_ext = (
		".list" if debian_distribution == "bookworm"
		else ".sources"
	)
	if pbs_src_no_subscription:
		pbs_list_file = SOURCES_LIST_PBS_NS
		pbs_list_data = sources_formats["no-subscription"]
		pbs_list_delete = SOURCES_LIST_PBS_EN
	else:
		pbs_list_file = SOURCES_LIST_PBS_EN
		pbs_list_data = sources_formats["enterprise"]
		pbs_list_delete = SOURCES_LIST_PBS_NS

	with open(pbs_list_file + source_file_ext, "w") as pbs_apt_lists:
		pbs_apt_lists.write(pbs_list_data.format(debian_distribution))
	backup_old_list_format(pbs_list_file)
	if os.path.exists(pbs_list_delete):
		os.remove(pbs_list_delete)
	print_c(bcolors.L_GREEN, "Proxmox Backup Server Sources Set.")

	# Update Proxmox
	prompt_update()

	# Offer Reboot
	prompt_reboot()
