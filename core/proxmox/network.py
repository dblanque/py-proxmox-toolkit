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

TOP_LEVEL_LONE_ARGS = [
	"source",
	"mapping",
	"rename"
]

TOP_LEVEL_IFACE_BOOL = [
	"auto",
	"allow-auto",
	"allow-hotplug",
]

TOP_LEVEL_IFACE_ARGS = [
	"iface",
	*TOP_LEVEL_IFACE_BOOL
]

INITIAL_ARGS = [
	*TOP_LEVEL_IFACE_ARGS,
	*TOP_LEVEL_LONE_ARGS
]

class NetworkInterfacesParseException(Exception):
	pass

def parse_interfaces(file=FILE_NETWORK_INTERFACES) -> tuple[ dict[dict], dict[list[list]] ]:
	ifaces = {}
	top_level_args = {}
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
				param: str = l_args[0].strip()

				if param in TOP_LEVEL_LONE_ARGS:
					if not param in top_level_args:
						top_level_args[param] = []
					top_level_args[param].append(l_args[1:])
				elif param.startswith("#") and not iface_name:
					continue
				elif param == "iface":
					if not l_args[1] in ifaces:
						ifaces[l_args[1]] = {}
					iface_name = l_args[1]
					ifaces[iface_name]["name"] = iface_name

					if not l_args[-1] in NETWORK_INTERFACES_INET_TYPES:
						raise NetworkInterfacesParseException("Invalid network interface type.")
					else:
						ifaces[iface_name]["type"] = l_args[-1]
				elif param in TOP_LEVEL_IFACE_BOOL:
					if not l_args[1] in ifaces:
						ifaces[l_args[1]] = {}
					ifaces[l_args[1]][param] = True
				elif iface_name:
					ifaces[iface_name][param] = l_args[1:]
				elif param.startswith("#"):
					if ("description" in ifaces[iface_name] and
		 				(ifaces[iface_name]["description"] or 
						len(ifaces[iface_name]["description"]) > 1)
					):
						raise NetworkInterfacesParseException("A network interface has multiple descriptions.", ifaces[iface_name]["description"])
					ifaces[iface_name]["description"] = re.sub(r"^(#+)(.*)$", "\\2", l)
					iface_name = None
			except:
				print("Offending line:")
				print(l)
				raise
	return ifaces, top_level_args

def stringify_interfaces(network_interfaces_dict: dict, top_level_args: dict) -> str:
	output = DEFAULT_PVE_HEADER
	for iface_key, iface_dict in network_interfaces_dict.items():
		iface_dict: dict
		l = ""
		try:
			iface_name = iface_dict.pop("name")
			iface_type = iface_dict.pop("type")
		except:
			print(iface_key)
			print(iface_dict)
			raise
		for bool_arg in TOP_LEVEL_IFACE_BOOL:
			if bool_arg in iface_dict:
				iface_dict.pop(bool_arg)
				l = f"{l}\n{bool_arg} {iface_name}"

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

	output = f"{output}\n"
	for stanza, arg_values in top_level_args.items():
		for v in arg_values:
			output = f"{output}\n{stanza} {' '.join([str(e) for e in v])}"

	return f"{output}\n"
