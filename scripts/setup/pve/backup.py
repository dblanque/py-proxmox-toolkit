#!/usr/bin/env python3
if __name__ == "__main__":
	raise Exception("This python script cannot be executed individually, please use main.py")

import signal
import os
import sys
import subprocess
from datetime import datetime, timezone
from time import perf_counter
from core.signal_handlers.sigint import graceful_exit
from core.format.colors import bcolors, print_c
from core.parser import make_parser, ArgumentParser

BKP_DIRS = [
	"/etc/pve"
]
DATE_FMT = "%Y-%m-%d_%H-%M-%S"

def argparser(**kwargs) -> ArgumentParser:
	parser = make_parser(
		prog="Proxmox VE Metadata Backup Script",
		description="This program is used to backup relevant Proxmox VE Host and Guest Configuration Metadata.",
		**kwargs
	)
	parser.add_argument('-p', '--output-path', default="/opt", help="Backup Tar output path, use without trailing slash.")
	parser.add_argument('-e', '--extra-dirs', help="Extra directories to backup.", nargs="+")
	return parser

def append_tar_dirs(in_dirs: list, out_dirs: list) -> list:
	for d in in_dirs:
		if not os.path.isdir(d):
			print_c(bcolors.L_YELLOW, f"Directory ({d}) does not exist, skipping.")
			continue
		out_dirs.append(d)
	return out_dirs

def main(argv_a, **kwargs):
	signal.signal(signal.SIGINT, graceful_exit)
	backup_date = datetime.now().astimezone(timezone.utc)
	backup_date_fmted = backup_date.strftime(DATE_FMT)
	tar_dirs = []
	if not os.path.isdir(argv_a.output_path):
		try: os.mkdir(argv_a.output_path)
		except: raise
	tar_dirs = append_tar_dirs(BKP_DIRS, tar_dirs)
	if argv_a.extra_dirs:
		tar_dirs = append_tar_dirs(argv_a.extra_dirs, tar_dirs)
	try:
		timer_s = perf_counter()
		cmd: list = f"tar -czvf {argv_a.output_path}/pve-bkp-{backup_date_fmted}.tar.gz --absolute-names".split() + tar_dirs
		print_c(bcolors.L_YELLOW, f"Executing command: {' '.join(cmd)}")
		subprocess.call(cmd)
		timer_e = perf_counter()
		print_c(bcolors.L_GREEN, f"Backup Completed in {round(timer_e-timer_s, 3)} seconds")
	except:
		print_c(bcolors.L_RED, "Could not complete backup.")
		raise
	sys.exit(0)
