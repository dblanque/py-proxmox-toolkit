#!/usr/bin/env python3
if __name__ == "__main__":
	raise Exception("This python script cannot be executed individually, please use main.py")

import os, sys, subprocess, signal, argparse
from core.signal_handlers.sigint import graceful_exit
from core.format.colors import print_c, bcolors
signal.signal(signal.SIGINT, graceful_exit)

def argparser():
	parser = argparse.ArgumentParser(
		prog="OS Update Script",
		description="This program is used to update system packages with APT."
	)
	parser.add_argument('-d', '--download-only', help="Execute package download only.", action="store_true")
	parser.add_argument('-df', '--download-first', help="Execute package download only first, then update.", action="store_true")
	parser.add_argument('-q', '--quiet', help="Make apt commands quiet.", action="store_true")
	parser.add_argument('-p', '--show-prompts', help="Show prompts from apt commands, might not function properly.", action="store_true")
	parser.add_argument('-w', '--windows-newline', help="Prints line endings with CRLF instead of LF.", action="store_true")
	return parser

def main(argv_a):
	if os.geteuid() != 0:
		print_c(bcolors.L_YELLOW, "Script must be executed as root.")
		exit()
	line_ending="\n"
	if argv_a.windows_newline:
		print_c(bcolors.L_YELLOW, f"[WARNING]{bcolors.NC} - Using CRLF for line-endings.")
		line_ending="\r\n"

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
			with subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE) as sp:
				for l_out in sp.stdout:
					l = l_out.decode("utf-8").strip()
					if len(l) < 1: continue
					print(l, end=line_ending)
				for l_err in sp.stderr:
					l = l_err.decode("utf-8").strip()
					if len(l) < 1: continue
					if l.startswith("E:"):
						print_c(bcolors.L_RED, l, end=line_ending)
					if l.startswith("N:"):
						print_c(bcolors.L_BLUE, l, end=line_ending)
					else:
						print_c(bcolors.L_YELLOW, l, end=line_ending)
				if sp.returncode and sp.returncode != 0:
					print_c(bcolors.L_RED, f"Could not execute \"{cmd}\" (non-zero exit status {sp.returncode}).")
					sys.exit(sp.returncode)
		except subprocess.CalledProcessError as e:
			print_c(bcolors.L_RED, f"Could not execute \"{cmd}\" (non-zero exit status {e.returncode}).")
			sys.exit(e.returncode)
		except Exception as e:
			print_c(bcolors.L_RED, f"Unhandled Exception.")
			print(e)
			sys.exit(1)
