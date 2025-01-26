#!/usr/bin/env python3
if __name__ == "__main__":
	raise Exception("This python script cannot be executed individually, please use main.py")

import os
import sys
import subprocess
import signal
from core.signal_handlers.sigint import graceful_exit
from core.format.colors import print_c, bcolors
from core.parser import make_parser, ArgumentParser
signal.signal(signal.SIGINT, graceful_exit)

def argparser(**kwargs) -> ArgumentParser:
	parser = make_parser(
		prog="OS Update Script",
		description="This program is used to update system packages with APT.",
		**kwargs
	)
	parser.add_argument('-d', '--download-only', help="Execute package download only.", action="store_true")
	parser.add_argument('-df', '--download-first', help="Execute package download only first, then update.", action="store_true")
	parser.add_argument('-q', '--quiet', help="Make apt commands quiet.", action="store_true")
	parser.add_argument('-p', '--show-prompts', help="Show prompts from apt commands, default is auto-yes.", action="store_true")
	return parser

def main(argv_a):
	if os.geteuid() != 0:
		print_c(bcolors.L_YELLOW, "Script must be executed as root.")
		exit()

	commands = [ "apt update" ]
	if argv_a.download_only:
		commands = [ *commands,
			"apt dist-upgrade --fix-broken --fix-missing -d"
		]
	elif argv_a.download_first:
		commands = [ *commands,
			"apt dist-upgrade --fix-broken --fix-missing -d",
			"apt dist-upgrade --fix-broken --fix-missing"
		]
	else:
		commands = [ *commands,
			"apt dist-upgrade --fix-broken --fix-missing"
		]
	commands = [ *commands,
		"apt autoclean",
		"apt autoremove"
	]

	for cmd in commands:
		if not argv_a.quiet:
			cmd = f"{cmd} --quiet=0"
		if not argv_a.show_prompts:
			cmd = f"{cmd} -y"
		print_c(bcolors.L_BLUE, f"{cmd}")
		try:
			with subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT) as sp:
				# src: https://stackoverflow.com/questions/63129698/python-subprocess-stdout-doesnt-capture-input-prompt
				while sp.poll() is None:
					out_bytes = sp.stdout.read(1).decode(sys.stdout.encoding)
					sys.stdout.write(out_bytes)
					sys.stdout.flush()

				if sp.returncode and sp.returncode != 0:
					print_c(bcolors.L_RED, f"Could not execute \"{cmd}\" (non-zero exit status {sp.returncode}).")
					sys.exit(sp.returncode)
		except subprocess.CalledProcessError as e:
			print_c(bcolors.L_RED, f"Could not execute \"{cmd}\" (non-zero exit status {e.returncode}).")
			sys.exit(e.returncode)
		except Exception as e:
			print_c(bcolors.L_RED, "Unhandled Exception.")
			print(e)
			sys.exit(1)
