#!/usr/bin/env python3
if __name__ == "__main__":
	raise Exception("This python script cannot be executed individually, please use main.py")

import os
import signal
from core.parser import make_parser, ArgumentParser
from core.signal_handlers.sigint import graceful_exit
from core.templates.shell.act_sh import SCRIPT_TEMPLATE, SCRIPT_NAME
from core.format.colors import print_c, bcolors
signal.signal(signal.SIGINT, graceful_exit)
from pathlib import Path

def main(**kwargs):
	toolkit_path = kwargs.pop("toolkit_path")
	user_home = Path.home()
	act_sh_path = os.path.join(user_home, SCRIPT_NAME)
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
		print(f"Wrote {SCRIPT_NAME} to {act_sh_path}.")
	os.chmod(act_sh_path, 0o750)