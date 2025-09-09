#!/usr/bin/python3
if __name__ == "__main__":
	raise Exception(
		"This python script cannot be executed individually, please use main.py"
	)

import sys
import signal
from core.signal_handlers.sigint import graceful_exit

from core.debian import os_release
from core.utils.prompt import yes_no_input, prompt_reboot, prompt_update
from core.format.colors import bcolors, print_c
from ..apt.sources.debian import DEB_LISTS, DEB_FILENAMES

SOURCES_LIST = "/etc/apt/sources.list"
SOURCES_LIST_DIR = "/etc/apt/sources.list.d"


def pre_checks() -> str:
	"""Performs Debian Release and Version Pre-checks

	Returns:
		str: Debian Distribution Name.
	"""
	release_info = os_release.get_data()
	if not os_release.is_valid_version(release_info, max_version=13):
		print_c(
			bcolors.L_RED,
			"Unsupported OS Distribution or Version (%s, %s, %s)." % (
				release_info["id"].capitalize(),
				str(release_info.get("version", "Unknown Version")),
				str(release_info.get("version_codename", "Unknown Codename")),
			),
		)
		sys.exit(1)
	debian_distribution = release_info.get(
		"version_codename",
		os_release.DEBIAN_CODENAMES[
			int(release_info["version_id"].split(".")[0])
		]
	)
	return debian_distribution


def set_debian_sources(debian_distribution) -> None:
	# Setting debian sources
	reset_debian_sources = yes_no_input(
		msg="Do you wish to reset the Debian Sources?", input_default=True
	)

	# Debian SRCs
	if reset_debian_sources:
		with open(DEB_FILENAMES[debian_distribution], "w") as debian_apt_lists:
			debian_apt_lists.write(
				DEB_LISTS[debian_distribution].format(debian_distribution)
			)
		print_c(bcolors.BLUE, "Debian Sources Set.")
	else:
		print_c(bcolors.BLUE, "Debian Sources Skipped.")


def main(**kwargs):
	signal.signal(signal.SIGINT, graceful_exit)
	debian_distribution = pre_checks()
	set_debian_sources(debian_distribution)

	# Update Proxmox
	prompt_update()

	# Offer Reboot
	prompt_reboot()
