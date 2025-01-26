import os
import subprocess
from core.format.colors import print_c, bcolors

DEFAULT_CHOICES = {
	"yes":["yes","y"],
	"no":["no","n"]
}

def yes_no_input(
		msg: str,
		input_default=None,
		input_choices=DEFAULT_CHOICES,
		yes_msg: str=None,
		no_msg: str=None
	):
	choices_str = '|'.join(input_choices)
	choices_str = f"({choices_str})"
	if input_default != None:
		if input_default == True or input_default in input_choices["yes"]:
			default_str = f" [{input_choices['yes'][0].upper()}]"
		else:
			default_str = f" [{input_choices['no'][0].upper()}]"
	else: default_str = ""
	while True:
		r = input(f"{msg} {choices_str}{default_str}:")
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

def prompt_update():
	if yes_no_input(
		msg="Do you wish to perform an update?",
		input_default=True
	):
		update_cmds = [
			"apt-get update -y",
			"apt-get dist-upgrade --fix-missing --fix-broken -y"
		]
		for c in update_cmds:
			subprocess.call(c.split())
	print_c(bcolors.L_GREEN, "Update Complete.")

def prompt_reboot():
	if yes_no_input(
		msg="Do you wish to reboot now?",
		input_default=False
	):
		print_c(bcolors.L_YELLOW, "Rebooting System.")
		os.system("reboot")