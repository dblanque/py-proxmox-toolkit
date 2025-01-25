from ..debian.constants import FILE_NETWORK_INTERFACES
from ..network.interfaces import NETWORK_INTERFACES_INET_TYPES
import re
from os.path import isfile

DEFAULT_PVE_HEADER = """# network interface settings; autogenerated
# Please do NOT modify this file directly, unless you know what
# you're doing.
#
# If you want to manage parts of the network configuration manually,
# please utilize the 'source' or 'source-directory' directives to do
# so.
# PVE will preserve these directives, but will NOT read its network
# configuration from sourced files, so do not attempt to move any of
# the PVE managed interfaces into external files!"""

INITIAL_ARGS = [
	"auto",
	"allow-hotplug",
	"iface"
]

class NetworkInterfacesParseException(Exception):
	pass

def parse_interfaces(file=FILE_NETWORK_INTERFACES) -> dict[dict]:
	ifaces = dict()
	if not isfile(file):
		raise Exception(f"{file} does not exist.")
	with open(file, "r") as f:
		iface_name: str = None
		iface_type: str = None
		for l in f.readlines():
			l = l.strip()
			if len(l) <= 0: continue
			try:
				l_args = l.split()
				param = l_args[0]
				if param == "iface":
					if not l_args[1] in ifaces:
						ifaces[l_args[1]] = dict()
					iface_name = l_args[1]
					ifaces[iface_name]["name"] = iface_name

					if not l_args[-1] in NETWORK_INTERFACES_INET_TYPES:
						raise NetworkInterfacesParseException("Invalid network interface type.")
					else:
						iface_type = l_args[-1]
						ifaces[iface_name]["type"] = l_args[-1]

				elif param.startswith("#") and iface_name:
					ifaces[iface_name]["description"] = re.sub(r"^(#+)(.*)$", "\\2", l)
					iface_name = None
					iface_type = None

				elif param.startswith("auto"):
					if not l_args[1] in ifaces:
						ifaces[l_args[1]] = dict()
					ifaces[l_args[1]]["auto"] = True

				elif param.startswith("allow-hotplug"):
					if not l_args[1] in ifaces:
						ifaces[l_args[1]] = dict()
					ifaces[l_args[1]]["allow-hotplug"] = True

				elif iface_name:
					if not iface_name or not iface_type:
						raise NetworkInterfacesParseException("A network interface has multiple descriptions.")
					ifaces[iface_name][param] = l_args[1:]
			except:
				print("Offending line:")
				print(l)
				raise
	return ifaces

def stringify_interfaces(network_interfaces_dict: dict) -> str:
	output = DEFAULT_PVE_HEADER
	for iface_dict in network_interfaces_dict.values():
		iface_dict: dict
		l = ""
		iface_name = iface_dict.pop("name")
		iface_type = iface_dict.pop("type")
		if "auto" in iface_dict:
			iface_dict.pop("auto")
			l = f"{l}\nauto {iface_name}"

		if "allow-hotplug" in iface_dict:
			iface_dict.pop("allow-hotplug")
			l = f"{l}\nallow-hotplug {iface_name}"

		l = f"{l}\niface {iface_name} inet {iface_type}"
		output = f"{output}\n{l}"
		for k, v in iface_dict.items():
			if k == "description":
				output = f"{output}\n#{v}"
			else:
				try:
					output = f"{output}\n\t{k} {' '.join([str(e) for e in v])}"
				except:
					print("Offending value:")
					print(v)
					raise
	return f"{output}\n"
