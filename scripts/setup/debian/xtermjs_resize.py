#!/usr/bin/env python3
if __name__ == "__main__":
	raise Exception("This python script cannot be executed individually, please use main.py")

import os
from core.format.colors import bcolors, print_c
from core.parser import make_parser, ArgumentParser
from core.debian.os_release import get_data

SUPPORTED_RELEASES=(
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

XTERM_RESIZE_TEMPLATE = """
#!/bin/sh
res() {

  old=$(stty -g)
  stty raw -echo min 0 time 5

  printf '\0337\033[r\033[999;999H\033[6n\0338' > /dev/tty
  IFS='[;R' read -r _ rows cols _ < /dev/tty

  stty "$old"

  # echo "cols:$cols"
  # echo "rows:$rows"
  stty cols "$cols" rows "$rows"
}

[ $(tty) = /dev/ttyS0 ] && res
""".lstrip()

def argparser(**kwargs) -> ArgumentParser:
	parser = make_parser(
		prog="XTermJS Serial Terminal Resizing fix script.",
		description="This program is used to implement the XTermJS Resize Fix for Proxmox VE Terminal Integration.",
		**kwargs
	)
	return parser

def main(argv_a, **kwargs):
	OS_RELEASE_DATA = get_data()
	OS_RELEASE = OS_RELEASE_DATA["version_codename"]
	if not OS_RELEASE in SUPPORTED_RELEASES:
		raise Exception(f"OS Release unsupported ({OS_RELEASE}).")
	PROFILE_PATH = "/etc/profile.d"
	PROFILE_FIX = os.path.join(PROFILE_PATH, "xterm_resize.sh")

	print_c(bcolors.L_YELLOW, f"Creating {PROFILE_PATH} directory if it does not exist.")
	os.makedirs(PROFILE_PATH, exist_ok=True)

	# Write XTermJS Data
	print_c(bcolors.L_BLUE, "Writing TTY Resize Fix.")
	with open(PROFILE_FIX, "w") as file:
		file.write(XTERM_RESIZE_TEMPLATE)
