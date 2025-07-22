import os
import sys
import subprocess
from core.format.colors import bcolors, print_c
from typing import overload

def apt_update(extra_args: list[str] | None = None) -> int:
	print_c(bcolors.L_BLUE, "Updating Package Lists.")
	cmd = "apt-get update"
	if extra_args:
		cmd = cmd + " " + " ".join(extra_args)
	cmd = f"{cmd} -y"
	try:
		return subprocess.call(cmd.split())
	except subprocess.CalledProcessError as e:
		print_c(
			bcolors.L_RED,
			f"Could not do apt update (non-zero exit status {e.returncode}).",
		)
		sys.exit(e.returncode)


def apt_install(
	packages: list[str],
	skip_if_installed=True,
	do_update=True,
	force_yes=False,
	extra_args: list[str] | None = None,
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
					stdout=open(os.devnull, "wb"),
					stderr=subprocess.STDOUT,
				)
				if ec == 0:
					packages.remove(pkg)
					already_installed.append(pkg)
			except Exception:
				pass

		if len(already_installed) > 0:
			print(
				f"{bcolors.L_GREEN}The following packages are already installed:{bcolors.NC}"
			)
			for package in already_installed:
				print(f"\t- {package}")

	if len(packages) > 0:
		print(
			f"{bcolors.L_YELLOW}The following packages will be installed:{bcolors.NC}"
		)
		for package in packages:
			print(f"\t- {package}")
		return subprocess.call(cmd.split() + packages)
	else:
		print_c(bcolors.L_BLUE, "Nothing to install.")
		return 0


def apt_dist_upgrade(
	fix_missing=True,
	fix_broken=True,
	force_yes=True,
	extra_args: list[str] | None = None,
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


def apt_autoremove(force_yes=False) -> int:
	print_c(bcolors.L_BLUE, "Auto-removing packages.")
	cmd = "apt-get autoremove"
	if force_yes:
		cmd = f"{cmd} -y"
	return subprocess.call(cmd.split())


def apt_autoclean(force_yes=False) -> int:
	print_c(bcolors.L_BLUE, "Performing Auto-clean.")
	cmd = "apt-get autoclean"
	if force_yes:
		cmd = f"{cmd} -y"
	return subprocess.call(cmd.split())

@overload
def apt_search(s: str) -> list[str]: ...
@overload
def apt_search(s: str, return_bytes: bool = True) -> bytes: ...
@overload
def apt_search(s: str, return_bytes: bool = False) -> list[str]: ...

@overload
def apt_search(package: str) -> list[str]: ...
@overload
def apt_search(package: str, return_bytes: bool = True) -> bytes: ...
@overload
def apt_search(package: str, return_bytes: bool = False) -> list[str]: ...

@overload
def apt_search(search_args: list[str]) -> list[str]: ...
@overload
def apt_search(search_args: list[str], return_bytes = True) -> bytes: ...
@overload
def apt_search(search_args: list[str], return_bytes = False) -> list[str]: ...

def apt_search(*args, **kwargs) -> list[str] | bytes:
	"""Searches for substring or exact package name with apt-cache search."""
	s: str | None = kwargs.pop("s", None) if not args else args[0]
	if s and not isinstance(s, str):
		raise TypeError("s must be of type str.")

	package: str | None = kwargs.pop("package", None)
	return_bytes: bool = kwargs.pop("return_bytes", False)
	search_args: list[str] = kwargs.pop("search_args", [])

	args = ["apt-cache", "search"]
	if s and search_args or package and search_args:
		raise ValueError("search_args cannot be used with s or package args")
	if package and s:
		raise ValueError("s and package cannot be used simultaneously.")
	if not package and not s:
		raise ValueError("s or package args must be used.")

	if s:
		args.append(s)
	elif package:
		args.append(f"^{package}$")

	if search_args:
		args += search_args

	search_res = subprocess.check_output(args=args)
	if return_bytes:
		return search_res

	packages = []
	for line in search_res.decode().split("\n"):
		package_name = line.split(" - ")[0].strip()
		if package_name:
			packages.append(package_name)
	return packages
