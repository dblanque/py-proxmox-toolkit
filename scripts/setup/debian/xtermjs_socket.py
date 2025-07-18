#!/usr/bin/python3
if __name__ == "__main__":
	raise Exception(
		"This python script cannot be executed individually, please use main.py"
	)

import subprocess
import os
import shutil
from core.format.colors import bcolors, print_c
from core.parser import make_parser, ArgumentParser
from core.debian.os_release import get_data

SUPPORTED_RELEASES = (
	# DEBIAN
	"stretch",
	"buster",
	"bullseye",
	"bookworm",
	# UBUNTU
	"focal",
	"xenial",
	"bionic",
	"jammy",
	"noble",
)

XTERM_TEMPLATE = """
# ttyS0 - getty
#
# This service maintains a getty on ttyS0 from the point the system is
# started until it is shut down again.

start on stopped rc RUNLEVEL=[12345]
stop on runlevel [!12345]

respawn
exec /sbin/getty -L 115200 ttyS0 vt102

sudo start ttyS0
""".lstrip()


def argparser(**kwargs) -> ArgumentParser:
	parser = make_parser(
		prog="XTermJS Serial Terminal socket setup script.",
		description="This program is used to setup the XTermJS Socket for Proxmox VE Terminal Integration.",
		**kwargs,
	)
	return parser


def main(argv_a, **kwargs):
	OS_RELEASE_DATA = get_data()
	OS_RELEASE = OS_RELEASE_DATA["version_codename"]
	if OS_RELEASE not in SUPPORTED_RELEASES:
		raise Exception(f"OS Release unsupported ({OS_RELEASE}).")
	INIT_PATH = "/etc/init"
	TTY_FILE = os.path.join(INIT_PATH, "ttyS0.conf")
	GRUB_FILE = "/etc/default/grub"

	print_c(bcolors.L_YELLOW, f"Creating {INIT_PATH} directory if it does not exist.")
	os.makedirs(INIT_PATH, exist_ok=True)

	# Write XTermJS Data
	print_c(bcolors.L_BLUE, "Writing TTYS0 Config File.")
	with open(TTY_FILE, "w") as file:
		file.write(XTERM_TEMPLATE)

	# Backup GRUB File
	if not os.path.isfile(f"{GRUB_FILE}.bkp"):
		print_c(bcolors.L_YELLOW, f"Creating backup of {GRUB_FILE}")
		shutil.copyfile(GRUB_FILE, f"{GRUB_FILE}.bkp")

	print_c(bcolors.L_YELLOW, "Updating GRUB CMDLINE with TTY0/TTYS0 Usage.")
	cmd_grep = 'grep -q "console=tty0"'.split()
	cmd_grep.append(GRUB_FILE)
	if subprocess.call(cmd_grep) > 0:
		sed_regex = r's#^\(GRUB_CMDLINE_LINUX=".*\)"$#\1 console=tty0"#'
		subprocess.call(["/usr/bin/sed", "-i", sed_regex, GRUB_FILE])

	cmd_grep = 'grep -q "console=ttyS0,115200"'.split()
	cmd_grep.append(GRUB_FILE)
	if subprocess.call(cmd_grep) > 0:
		sed_regex = r's#^\(GRUB_CMDLINE_LINUX=".*\)"$#\1 console=ttyS0,115200"#'
		subprocess.call(["/usr/bin/sed", "-i", sed_regex, GRUB_FILE])

	print_c(bcolors.L_YELLOW, "Doing update-grub.")
	subprocess.call(["update-grub"])

	print_c(
		bcolors.L_BLUE,
		"Do not forget to add the serial socket onto the VM Hardware Section in Proxmox.",
	)
	print_c(bcolors.L_GREEN, "Done!")
