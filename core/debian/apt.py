import os
import sys
import subprocess
from core.format.colors import bcolors, print_c

def apt_update(extra_args: list = None) -> int:
	print_c(bcolors.L_BLUE, "Updating Package Lists.")
	cmd = f"apt-get update"
	if extra_args:
		cmd = cmd + " " + " ".join(extra_args)
	cmd = f"{cmd} -y"
	try:
		return subprocess.call(cmd.split())
	except subprocess.CalledProcessError as e:
		print_c(bcolors.L_RED, f"Could not do apt update (non-zero exit status {e.returncode}).")
		sys.exit(e.returncode)

def apt_install(
		packages: list[str],
		skip_if_installed=True,
		do_update=True,
		force_yes=False,
		extra_args: list = None
	) -> int:
	if do_update:
		apt_update()
	cmd = "apt-get install"
	if extra_args:
		cmd = cmd + " " + " ".join(extra_args)
	if force_yes:
		cmd = f"{cmd} -y"
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
	return subprocess.call(cmd.split() + packages)

def apt_dist_upgrade(
		fix_missing=True,
		fix_broken=True,
		force_yes=True,
		extra_args: list = None
	) -> int:
	cmd = "apt-get dist-upgrade"
	if fix_broken:
		cmd = f"{cmd} --fix-broken"
	if fix_missing:
		cmd = f"{cmd} --fix-missing"
	if extra_args:
		cmd = cmd + " " + " ".join(extra_args)
	if force_yes:
		cmd = f"{cmd} -y"

	print_c(bcolors.L_BLUE, "Performing dist-upgrade.")
	return subprocess.call(cmd.split())

def apt_autoremove(force_yes=False):
	print_c(bcolors.L_BLUE, "Auto-removing packages.")
	cmd = "apt-get autoremove"
	if force_yes:
		cmd = f"{cmd} -y"
	return subprocess.call(cmd.split())

def apt_autoclean(force_yes=False):
	print_c(bcolors.L_BLUE, "Performing Auto-clean.")
	cmd = "apt-get autoclean"
	if force_yes:
		cmd = f"{cmd} -y"
	return subprocess.call(cmd.split())
