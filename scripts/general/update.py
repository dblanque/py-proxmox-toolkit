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
	parser.add_argument('-q', '--quiet', help="Make apt commands quiet.", action="store_true")
	parser.add_argument('-p', '--show-prompts', help="Show prompts from apt commands, might not function properly.", action="store_true")
	return parser

def main(argv_a):
	if os.geteuid() != 0:
		print_c(bcolors.L_YELLOW, "Script must be executed as root.")
		exit()

	commands = [
		"apt update",
		"apt dist-upgrade --fix-broken --fix-missing",
		"apt autoclean",
		"apt autoremove"
	]
	STRIP_CHARS = [
		"\t",
		"\r\n",
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
					l = l_out.decode('utf-8').strip()
					for c in STRIP_CHARS: l = l.strip(c)
					if len(l) > 0: print(f"{l}")
				for l_err in sp.stderr:
					l = l_err.decode('utf-8').strip()
					for c in STRIP_CHARS: l = l.strip(c)
					if len(l) > 0: print_c(bcolors.L_RED, f"{l}")
		except subprocess.CalledProcessError as e:
			print_c(bcolors.L_RED, f"Could not do {cmd} (non-zero exit status {e.returncode}).")
			sys.exit(0)
