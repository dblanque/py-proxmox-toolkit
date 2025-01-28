#!/usr/bin/env python3
if __name__ == "__main__":
	raise Exception("This python script cannot be executed individually, please use main.py")

import os
import signal
from core.parser import make_parser, ArgumentParser
from core.signal_handlers.sigint import graceful_exit
from core.templates.shell.act_sh import SCRIPT_TEMPLATE, SCRIPT_NAME
from core.templates.shell.py_proxmox_aliases import TEMPLATE_ALIASES, TEMPLATE_COMPLETION
from core.format.colors import print_c, bcolors
from pathlib import Path

def argparser(**kwargs) -> ArgumentParser:
	parser = make_parser(
		prog="Useful Aliases Installation Script",
		description="This program is used to install system administration tools that might be useful long term.",
		**kwargs
	)
	parser.add_argument('-a', '--add-aliases', action="store_true")
	parser.add_argument('-bc', '--bash-completion', action="store_true")
	return parser

def install_actsh(toolkit_path, act_sh_path):
	if os.path.islink(act_sh_path) or os.path.isfile(act_sh_path):
		if not os.path.exists(act_sh_path + ".old"):
			os.rename(act_sh_path, f"{act_sh_path}.old")
			print(f"File{act_sh_path} already exists, renaming.")
			print_c(bcolors.L_YELLOW, f"{act_sh_path} was renamed to {act_sh_path}.old")
	elif os.path.exists(act_sh_path):
		raise ValueError(act_sh_path + "already exists and is not a link or a file?")
	with open(act_sh_path, "w") as act_sh:
		act_sh.write(
			SCRIPT_TEMPLATE.format(
				toolkit_path=toolkit_path
			).lstrip()
		)
		print_c(bcolors.L_BLUE, f"Wrote {SCRIPT_NAME} to {act_sh_path}.")
	os.chmod(act_sh_path, 0o750)

def install_aliases(user_home, bash_completion, add_aliases):
	if (
		bash_completion is not True and add_aliases is not True
	): return
	BASH_RC = os.path.join(user_home, ".bashrc")
	ALIASES_FILENAME = ".py_proxmox_aliases"
	ALIASES_PATH = os.path.join(user_home, ALIASES_FILENAME)
	source_line = f". ~/{ALIASES_FILENAME}"
	# Add alias file sourcing to bashrc if not present.
	with open(BASH_RC, "r+") as file:
		for line in file:
			if source_line in line:
				break
		else: # not found, we are at the eof
			file.write("\n" + source_line + "\n") # append missing data
	with open(ALIASES_PATH, "w") as aliases_file:
		if add_aliases is True:
			aliases_file.write(TEMPLATE_ALIASES)
			print_c(bcolors.L_BLUE, f"Wrote aliases to {ALIASES_PATH}")
		if bash_completion is True:
			aliases_file.write(TEMPLATE_COMPLETION)
			print_c(bcolors.L_YELLOW, f"Wrote bash-completion to {ALIASES_PATH}")

def main(argv_a, **kwargs):
	signal.signal(signal.SIGINT, graceful_exit)
	toolkit_path = kwargs.pop("toolkit_path")
	user_home = Path.home()
	act_sh_path = os.path.join(user_home, SCRIPT_NAME)
	install_actsh(toolkit_path=toolkit_path, act_sh_path=act_sh_path)
	install_aliases(user_home=user_home, bash_completion=argv_a.bash_completion, add_aliases=argv_a.add_aliases)
