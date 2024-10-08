#!/usr/bin/env python3
if __name__ == "__main__":
	raise Exception("This python script cannot be executed individually, please use main.py")

import signal, subprocess, json, sys
from core.format.colors import print_c, bcolors
from core.signal_handlers.sigint import graceful_exit
signal.signal(signal.SIGINT, graceful_exit)

SUPPORTED_CPU_VENDORS = {
	"authenticamd":{
		"label":"AMD",
		"deb":"amd64-microcode"
	},
	"genuineintel":{
		"label":"Intel",
		"deb":"intel-microcode",
		"supplementary_packages":["iucode-tool"]
	}
}

def get_cpu_vendor():
	lscpu = subprocess.Popen(['lscpu'], stdout=subprocess.PIPE)
	grep = subprocess.Popen(["grep", "-oP", r'Vendor ID:\s*\K\S+'], stdin=lscpu.stdout, stdout=subprocess.PIPE)
	output = subprocess.check_output("head -n 1".split(), stdin=grep.stdout)
	lscpu.wait()
	grep.wait()
	return output.decode("utf-8").strip()

def get_cpu_vendor_json():
	output = subprocess.check_output("lscpu --json".split())
	json_output: list = json.loads(output)['lscpu']
	for d in json_output:
		d: dict
		f: str = d["field"]
		f = f.lower().rstrip(":")
		v = d["data"]
		if "vendor" in f: return v

def main():
	cpu_vendor = get_cpu_vendor()
	if not cpu_vendor:
		print_c(bcolors.L_RED, f"CPU Vendor not found.")
		sys.exit(1)
	if not cpu_vendor.lower() in SUPPORTED_CPU_VENDORS:
		print_c(bcolors.L_YELLOW, f"CPU Vendor is not supported ({cpu_vendor}).")
		sys.exit(1)

	cpu_vendor_data = SUPPORTED_CPU_VENDORS[cpu_vendor.lower()]
	cpu_microcode_deb = cpu_vendor_data["deb"]
	try:
		ec = subprocess.check_call(
			["dpkg", "-l", cpu_microcode_deb],
			stdout=subprocess.DEVNULL,
			stderr=subprocess.STDOUT
		)
		if ec == 0:
			print_c(bcolors.L_GREEN, f"{cpu_vendor_data['label']} Microcode is already installed.")
			sys.exit(0)
	except: pass

	print_c(bcolors.L_BLUE, f"Downloading and Installing {cpu_vendor_data['label']} Processor Microcode.")
	apt_search = subprocess.check_output(f"apt-cache search ^{cpu_microcode_deb}$".split())
	if not apt_search.decode().strip().split(" - ")[0] == cpu_microcode_deb:
		print_c(bcolors.L_RED, "Package not found, please add non-free-firmware APT Debian Repository.")
		sys.exit(1)
	try:
		deb_to_install = [ cpu_microcode_deb ]
		if "supplementary_packages" in cpu_vendor_data:
			deb_to_install = deb_to_install + cpu_vendor_data["supplementary_packages"]
		subprocess.call("apt-get install -y".split() + deb_to_install)
	except:
		raise
	print_c(bcolors.L_GREEN, "Microcode Installed.")
	sys.exit(0)
