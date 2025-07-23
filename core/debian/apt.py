import sys
import subprocess
from core.format.colors import bcolors, print_c
from typing import overload

def make_apt_args(
	initial_args: list[str],
	extra_args: list[str] | None = [],
	force_yes: bool = False,
) -> list[str]:
	if not initial_args:
		raise ValueError("initial_args is required")
	if not isinstance(initial_args, list):
		raise TypeError("initial_args must be of type list")

	if extra_args:
		# Check type for extra_args
		if not isinstance(extra_args, list):
			raise TypeError("extra_args must be of type list")
		# Validate all elements being str
		if not all(isinstance(s, str) for s in extra_args):
			raise TypeError("All elements in extra_args must be of type str.")
		# Merge onto initial
		initial_args += list(extra_args)

	if force_yes and "-y" not in initial_args:
		initial_args.append("-y")
	return initial_args

def apt_update(
	extra_args: list[str] | None = None,
	exit_on_fail = True
) -> int:
	print_c(bcolors.L_BLUE, "Updating Package Lists.")
	cmd_args = make_apt_args(
		initial_args=["apt-get", "update"],
		extra_args=extra_args,
		force_yes=True
	)

	# Do update
	ret_code = subprocess.call(cmd_args)

	# Exit or return code
	if ret_code:
		print_c(
			bcolors.L_RED,
			"Could not do apt update (non-zero exit status %s)." % (
				str(ret_code)
			),
		)
	if exit_on_fail and ret_code:
		sys.exit(ret_code)
	return ret_code

def dpkg_deb_is_installed(
	pkg: str,
	hide_stdout=False,
	hide_stderr=True
) -> bool:
	return subprocess.call(
		["dpkg","-l", pkg],
		stdout=subprocess.DEVNULL if hide_stdout else subprocess.PIPE,
		stderr=subprocess.DEVNULL if hide_stderr else subprocess.STDOUT,
	) == 0

def apt_install(
	packages: list[str],
	skip_if_installed=True,
	do_update=True,
	force_yes=False,
	extra_args: list[str] | None = None,
) -> int:
	if not packages:
		print_c(bcolors.L_BLUE, "Nothing to install.")
		return 0

	if (
		not isinstance(packages, list) or
		not all(isinstance(v, str) for v in packages)
	):
		raise TypeError("packages must be of type list[str]")

	# De-duplicate package names
	packages = list(dict.fromkeys(packages))

	# Construct args
	cmd_args = make_apt_args(
		initial_args=["apt-get", "install"],
		extra_args=extra_args,
		force_yes=force_yes
	)

	# Do update if required
	if do_update:
		apt_update()

	already_installed = set()
	if skip_if_installed:
		print_c(bcolors.L_BLUE, "Checking Installed Packages.")
		for pkg in packages:
			if dpkg_deb_is_installed(pkg):
				already_installed.add(pkg)

		if already_installed:
			print_c(
				bcolors.L_GREEN,
				"The following packages are already installed:"
			)
			for package in already_installed:
				print(f"\t- {package}")
	# Re-make list with only non-installed packages
	packages = [ pkg for pkg in packages if pkg not in already_installed ]

	if packages:
		print_c(
			bcolors.L_YELLOW,
			"The following packages will be installed:"
		)
		for package in packages:
			print(f"\t- {package}")
		return subprocess.call(cmd_args + list(packages))
	else:
		print_c(bcolors.L_BLUE, "Nothing to install.")
		return 0


def apt_dist_upgrade(
	fix_missing=True,
	fix_broken=True,
	force_yes=True,
	extra_args: list[str] | None = None,
) -> int:
	if extra_args is None:
		extra_args = []
	if fix_broken and "--fix-broken" not in extra_args:
		extra_args.append("--fix-broken")
	if fix_missing and "--fix-missing" not in extra_args:
		extra_args.append("--fix-missing")

	# Construct args
	cmd_args = make_apt_args(
		initial_args=["apt-get", "dist-upgrade"],
		extra_args=extra_args,
		force_yes=force_yes
	)

	print_c(bcolors.L_BLUE, "Performing dist-upgrade.")
	return subprocess.call(cmd_args)


def apt_autoremove(force_yes=False) -> int:
	print_c(bcolors.L_BLUE, "Auto-removing packages.")
	return subprocess.call(
		make_apt_args(
			initial_args=["apt-get", "autoremove"],
			extra_args=[],
			force_yes=force_yes
		)
	)


def apt_autoclean(force_yes=False) -> int:
	print_c(bcolors.L_BLUE, "Performing Auto-clean.")
	return subprocess.call(
		make_apt_args(
			initial_args=["apt-get", "autoclean"],
			extra_args=[],
			force_yes=force_yes
		)
	)

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
