import os
from core.format.colors import print_c, bcolors
from core.debian.apt import apt_dist_upgrade, apt_update
from typing import TypedDict, Required

class YesNoChoicesDict(TypedDict):
	yes: Required[ list[str] ]
	no: Required[ list[str] ]

DEFAULT_CHOICES: YesNoChoicesDict = {
	"yes":["yes","y"],
	"no":["no","n"]
}

def yes_no_input(
		msg: str,
		input_default: str = None,
		input_choices: YesNoChoicesDict = DEFAULT_CHOICES,
		yes_msg: str = None,
		no_msg: str = None,
		show_choices = True
	):
	if show_choices:
		choices_str = ','.join(input_choices["yes"]) + "|" + ','.join(input_choices["no"])
		choices_str = f"({choices_str})"
	else:
		choices_str = ""
	if input_default is not None:
		if (
			input_default.lower() in input_choices["yes"] or
			input_default.lower() in input_choices["no"]
		):
			default_str = f" [{input_default}]"
		elif input_default == True:
			default_str = f" [{input_choices['yes'][0].upper()}]"
		else:
			default_str = f" [{input_choices['no'][0].upper()}]"
	else: default_str = ""
	while True:
		r = input(f"{msg} {choices_str}{default_str}: ")
		if r.lower() in input_choices["yes"]:
			if yes_msg: print(yes_msg)
			return True
		elif r.lower() in input_choices["no"]:
			if no_msg: print(no_msg)
			return False
		elif input_default == True or input_default in input_choices["yes"]:
			if yes_msg: print(yes_msg)
			return True
		elif input_default == False or input_default in input_choices["no"]:
			if no_msg: print(no_msg)
			return False
		else:
			print(f"Please enter a valid choice {choices_str}.")

def prompt_update(dist_upgrade=True):
	if yes_no_input(
		msg="Do you wish to perform an update?",
		input_default=True
	):
		apt_update()
		if dist_upgrade:
			apt_dist_upgrade()
	print_c(bcolors.L_GREEN, "Update Complete.")

def prompt_reboot():
	if yes_no_input(
		msg="Do you wish to reboot now?",
		input_default=False
	):
		print_c(bcolors.L_YELLOW, "Rebooting System.")
		os.system("reboot")