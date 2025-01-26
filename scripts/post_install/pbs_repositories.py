#!/usr/bin/env python3
if __name__ == "__main__":
	raise Exception("This python script cannot be executed individually, please use main.py")

import os
import sys
import subprocess
import signal
from core.signal_handlers.sigint import graceful_exit
signal.signal(signal.SIGINT, graceful_exit)

from core.utils.prompt import yes_no_input, prompt_reboot, prompt_update
from core.format.colors import bcolors, print_c
from .debian_repositories import pre_checks, set_debian_sources
from .apt.sources.pbs import SRC_PBS_ENTERPRISE, SRC_PBS_NO_SUBSCRIPTION
SOURCES_LIST = "/etc/apt/sources.list"
SOURCES_LIST_DIR = "/etc/apt/sources.list.d"
SOURCES_LIST_PBS_NS = f"{SOURCES_LIST_DIR}/pbs-no-subscription.list"
SOURCES_LIST_PBS_EN = f"{SOURCES_LIST_DIR}/pbs-enterprise.list"

def main():
	debian_distribution = pre_checks()
	set_debian_sources(debian_distribution)

	###################################### CHOICES #######################################
	# Setting PBS No-Subscription or Enterprise Sources
	pbs_src_no_subscription = yes_no_input(
		msg="Do you wish to use the PBS No-Subscription Repositories?",
		input_default=True
	)

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
	prompt_update()

	# Offer Reboot
	prompt_reboot()