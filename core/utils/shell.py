import os
from core.format.colors import bcolors, print_c

def is_completion_context():
    return "COMP_LINE" in os.environ and "COMP_POINT" in os.environ

def is_user_root(exit_on_fail=False):
	_is_root = os.geteuid() == 0
	if exit_on_fail and not _is_root:
		print_c(bcolors.L_YELLOW, "Script must be executed as root.")
		exit()
	else:
		return _is_root