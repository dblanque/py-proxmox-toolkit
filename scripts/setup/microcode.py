#!/usr/bin/python3
if __name__ == "__main__":
	raise Exception(
		"This python script cannot be executed individually, please use main.py"
	)

import signal
import subprocess
import json
import sys
from core.format.colors import print_c, bcolors
from core.signal_handlers.sigint import graceful_exit
from core.debian.apt import apt_install, apt_update, apt_search
from typing import TypedDict, Required, NotRequired

class SupportedVendorDict(TypedDict):
	label: Required[str]
	deb: Required[str]
	supplementary_deb: NotRequired[list[str] | set[str] | tuple | str]

VENDOR_AMD: SupportedVendorDict = {
	"label": "AMD",
	"deb": "amd64-microcode",
}
VENDOR_INTEL: SupportedVendorDict = {
	"label": "Intel",
	"deb": "intel-microcode",
	"supplementary_deb": ["iucode-tool"],
}
SUPPORTED_CPU_VENDORS: dict[str, SupportedVendorDict] = {
	"authenticamd": VENDOR_AMD,
	"genuineintel": VENDOR_INTEL,
}

def get_cpu_vendor():
	lscpu = subprocess.Popen(["lscpu"], stdout=subprocess.PIPE)
	grep = subprocess.Popen(
		["grep", "-oP", r"Vendor ID:\s*\K\S+"],
		stdin=lscpu.stdout,
		stdout=subprocess.PIPE,
	)
	output = subprocess.check_output(["head", "-n", "1"], stdin=grep.stdout)
	lscpu.wait()
	grep.wait()
	return output.decode("utf-8").strip()


def get_cpu_vendor_json(raise_exception = False) -> str:
	try:
		output = subprocess.check_output(["lscpu", "--json"])
		json_output: list = json.loads(output)["lscpu"]
		for d in json_output:
			d: dict
			field: str = d["field"]
			field = field.lower().rstrip(":")
			value = d["data"]
			if "vendor" in field:
				return value
	except Exception as e:
		if raise_exception:
			raise e
		print_c(bcolors.L_RED, str(e))
	return "Unknown"

def main(**kwargs):
	signal.signal(signal.SIGINT, graceful_exit)

	# Check CPU Vendor is supported
	cpu_vendor = get_cpu_vendor()
	bad_vendor_msg = None
	if not cpu_vendor:
		bad_vendor_msg = (bcolors.L_RED, "CPU Vendor not found.")
	elif cpu_vendor.lower() not in SUPPORTED_CPU_VENDORS:
		bad_vendor_msg = (
			bcolors.L_YELLOW,
			f"CPU Vendor is not supported ({cpu_vendor})."
		)

	if bad_vendor_msg:
		print_c(bad_vendor_msg[0], bad_vendor_msg[1])
		sys.exit(1)

	cpu_vendor_data = SUPPORTED_CPU_VENDORS[cpu_vendor.lower()]
	cpu_microcode_deb = cpu_vendor_data["deb"]
	try:
		ec = subprocess.check_call(
			["dpkg", "-l", cpu_microcode_deb],
			stdout=subprocess.DEVNULL,
			stderr=subprocess.STDOUT,
		)
		if ec == 0:
			print_c(
				bcolors.L_GREEN,
				"%s Microcode is already installed." % (
					cpu_vendor_data["label"]
				),
			)
			sys.exit(0)
	except Exception:
		pass

	apt_update()
	print_c(
		bcolors.L_BLUE,
		"Downloading and Installing %s Processor Microcode." % (
			cpu_vendor_data["label"]
		),
	)
	search_res = apt_search(package=cpu_microcode_deb)
	if cpu_microcode_deb not in search_res:
		print_c(
			bcolors.L_RED,
			"Package not found, please add non-free-firmware "
			"APT Debian Repository.",
		)
		sys.exit(1)
	try:
		deb_to_install = [cpu_microcode_deb]
		deb_extras = cpu_vendor_data.get("supplementary_deb", [])
		if deb_extras:
			if isinstance(deb_extras, (list, set, tuple)):
				deb_to_install = deb_to_install + list(deb_extras)
			elif isinstance(deb_extras, str):
				deb_to_install.append(deb_extras)
		apt_install(packages=deb_to_install, do_update=False)
	except:
		raise
	print_c(bcolors.L_GREEN, "Microcode Installed.")
	sys.exit(0)
