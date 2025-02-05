from os import geteuid
from core.format.colors import bcolors, print_c

def is_user_root(exit_on_fail=False):
	_is_root = geteuid() == 0
	if exit_on_fail and not _is_root:
		print_c(bcolors.L_YELLOW, "Script must be executed as root.")
		exit()
	else:
		return _is_root