import os
import sys
import subprocess
from core.format.colors import bcolors, print_c

def apt_update() -> int:
	print_c(bcolors.L_BLUE, "Doing apt update.")
	try:
		return subprocess.check_call(
			"apt-get update -y".split(),
			stdout=open(os.devnull, 'wb'),
			stderr=subprocess.STDOUT
		)
	except subprocess.CalledProcessError as e:
		print_c(bcolors.L_RED, f"Could not do apt update (non-zero exit status {e.returncode}).")
		sys.exit(e.returncode)

def apt_install(packages: list[str], skip_if_installed=True, do_update=True, force_yes=False) -> int:
	if do_update:
		apt_update()
	if force_yes:
		apt_cmd = "apt-get install -y"
	else:
		apt_cmd = "apt-get install"
	already_installed = []
	if skip_if_installed:
		print_c(bcolors.L_BLUE, "Checking Installed Packages.")
		for pkg in packages:
			try:
				ec = subprocess.check_call(
					f"dpkg -l {pkg}".split(),
					stdout=open(os.devnull, 'wb'),
					stderr=subprocess.STDOUT
				)
				if ec == 0:
					packages.remove(pkg)
					already_installed.append(pkg)
			except: pass

		print(f"{bcolors.L_GREEN}The following packages are already installed:{bcolors.NC}")
		for package in already_installed:
			print(f"\t- {package}")

	print(f"{bcolors.L_YELLOW}The following packages will be installed:{bcolors.NC}")
	for package in packages:
		print(f"\t- {package}")
	return subprocess.call(apt_cmd.split() + packages)

def apt_dist_upgrade(fix_missing=True, fix_broken=True, force_yes=True) -> int:
	cmd = "apt-get dist-upgrade"
	if fix_broken:
		cmd = cmd + " --fix-broken"
	if fix_missing:
		cmd = cmd + " --fix-missing"
	if force_yes:
		cmd = cmd + " -y"

	print_c(bcolors.L_BLUE, "Doing dist-upgrade.")
	return subprocess.check_call(
		cmd.split(),
		stdout=open(os.devnull, 'wb'),
		stderr=subprocess.STDOUT
	)
