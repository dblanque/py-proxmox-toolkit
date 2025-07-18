#!/usr/bin/python3
if __name__ == "__main__":
	raise Exception(
		"This python script cannot be executed individually, please use main.py"
	)

import signal
from core.signal_handlers.sigint import graceful_exit
from core.parser import make_parser, ArgumentParser
from core.debian.apt import apt_install
from core.utils.shell import is_user_root


def argparser(**kwargs) -> ArgumentParser:
	parser = make_parser(
		prog="Useful Tools Installation Script",
		description="This program is used to install system administration tools that might be useful long term.",
		**kwargs,
	)
	parser.add_argument("-l", "--light", action="store_true")
	return parser

class LocalParser(ArgumentParser):
	light: bool

def main(argv_a: LocalParser, **kwargs):
	signal.signal(signal.SIGINT, graceful_exit)
	is_user_root(exit_on_fail=True)
	tools = [
		"sudo",
		"net-tools",
		"lvm2",
		"xfsprogs",
		"aptitude",
		"htop",
		"iotop",
		"locate",
		"lshw",
		"git",
	]
	if not argv_a.light:
		tools = tools + [
			"cifs-utils",
			"bmon",
			"ethtool",
			"rename",
			"iptraf-ng",
			"nmap",
			"arping",
			"sysstat",
		]

	apt_install(packages=tools, skip_if_installed=True, do_update=True)
