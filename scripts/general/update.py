#!/usr/bin/python3
if __name__ == "__main__":
	raise Exception(
		"This python script cannot be executed individually, please use main.py"
	)

import signal
from core.signal_handlers.sigint import graceful_exit
from core.parser import make_parser, ArgumentParser
from core.debian.apt import apt_update, apt_dist_upgrade, apt_autoremove, apt_autoclean
from core.utils.shell import is_user_root


def argparser(**kwargs) -> ArgumentParser:
	parser = make_parser(
		prog="OS Update Script",
		description="This program is used to update system packages with APT.",
		**kwargs,
	)
	parser.add_argument(
		"-d",
		"--download-only",
		help="Execute package download only.",
		action="store_true",
	)
	parser.add_argument(
		"-df",
		"--download-first",
		help="Execute package download only first, then update.",
		action="store_true",
	)
	parser.add_argument(
		"-p",
		"--show-prompts",
		help="Show prompts from apt commands, default is auto-yes.",
		action="store_true",
	)
	return parser


def main(argv_a, **kwargs):
	signal.signal(signal.SIGINT, graceful_exit)
	is_user_root(exit_on_fail=True)

	apt_update()
	if argv_a.download_only:
		apt_dist_upgrade(extra_args=["-d"])
	elif argv_a.download_first:
		apt_dist_upgrade(extra_args=["-d"])
		apt_dist_upgrade()
	else:
		apt_dist_upgrade()
	apt_autoclean()
	apt_autoremove()
