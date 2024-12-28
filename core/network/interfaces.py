import os, re

PHYSICAL_INTERFACE_PATTERNS=[
	r"^eth[0-9].*$",
	r"^eno[0-9].*$",
	r"^enp[0-9].*$",
	r"^enx[0-9a-fA-F].*$",
	r"^ens[0-9].*$",
]

def get_physical_interfaces(interface_patterns=None, override_patterns=False):
	"""
	Fetches physical interface names and returns them as a list.
	If override_patterns is set to True then only the patterns passed will be matched.
	"""
	physical_interfaces=list()
	network_interfaces=os.listdir('/sys/class/net/')
	check_patterns: list
	if not interface_patterns and not override_patterns:
		print("interface_patterns should contain at least one Regex Pattern if override_patterns is used.")
	if not override_patterns:
		check_patterns = PHYSICAL_INTERFACE_PATTERNS
	if interface_patterns:
		for extra_iface in interface_patterns:
			if re.compile(extra_iface): check_patterns.append(extra_iface)
	for iface in network_interfaces:
		match = False
		iface = iface.strip()
		for regex in check_patterns:
			if re.match(regex, iface):
				physical_interfaces.append(iface)
				match = True
		if not match: print(f"{iface} is not a physical interface, skipping.")
	return physical_interfaces