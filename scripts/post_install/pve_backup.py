#!/usr/bin/env python3
if __name__ == "__main__":
	raise Exception("This python script cannot be executed individually, please use main.py")

import signal, argparse, os, sys, subprocess
from datetime import datetime, timezone
from time import perf_counter
from core.signal_handlers.sigint import graceful_exit
from core.format.colors import bcolors, print_c
signal.signal(signal.SIGINT, graceful_exit)

BKP_DIRS = [
	"/etc/pve"
]
DATE_FMT = "%Y-%m-%dT%H:%M:%S%z"

def argparser(parser: argparse.ArgumentParser):
	parser.prog = 'Proxmox VE Metadata Backup Script'
	parser.description = 'This program is used to backup relevant Proxmox VE Host and Guest Configuration Metadata.'
	parser.add_argument('-p', '--output-path', default="/opt", required=True)
	return parser

def main(argv_a):
	backup_date = datetime.now().astimezone(timezone.utc)
	backup_date_fmted = backup_date.strftime(DATE_FMT)
	tar_dirs = list()
	if not os.path.isdir(argv_a.output_path):
		try: os.mkdir(argv_a.output_path)
		except: raise
	for d in BKP_DIRS:
		if not os.path.isdir(d):
			print_c(bcolors.L_YELLOW, f"Directory ({d}) does not exist, skipping.")
			continue
		tar_dirs.append(d)
	try:
		timer_s = perf_counter()
		subprocess.call(
			f"tar -czvf '{d}-{backup_date_fmted}.tar.gz' --absolute-names".split() + tar_dirs
		)
		timer_e = perf_counter()
		print_c(bcolors.L_GREEN, f"Backup Completed in {timer_e-timer_s}")
		sys.exit(0)
	except:
		print_c(bcolors.L_RED, "Could not complete backup.")
		raise