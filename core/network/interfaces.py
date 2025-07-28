import os
import re
from core.format.colors import print_c, bcolors

NETWORK_INTERFACES_INET_TYPES = (
	"static",
	"manual",
	"loopback",
	"dhcp",
)

PHYSICAL_INTERFACE_PATTERNS_SHORT = (
	r"^eth[0-9].*$",
	r"^eno[0-9].*$",
	r"^enp[0-9].*$",
	r"^enx[0-9a-fA-F].*$",
	r"^ens[0-9].*$",
)

PHYSICAL_INTERFACE_PATTERNS = (
	r"^eth[0-9]+$",									# Traditional Ethernet
	r"^eno[0-9]+$",									# Embedded/onboard NIC
	r"^enp[0-9]+s[0-9]+(?:f[0-9]+)?(?:d[0-9]+)?$",	# PCI geographic
	r"^ens[0-9]+$",									# Hotplug slot
	r"^enx[0-9a-fA-F]+$",							# MAC-based
	r"^en[a-z][0-9]+$",								# General embedded
	r"^ib[0-9]+$",									# Infiniband
	# r"^usb[0-9]+$",								# USB network devices
	# r"^[a-z]+[0-9]+_[0-9]+$",						# Virtual/physical hybrids

	# Driver-based interface names (common for specific NICs)
	r"^igb[0-9]+$",                # Intel Gigabit Ethernet (igb driver)
	r"^ixgbe[0-9]+$",              # Intel 10GbE (ixgbe driver)
	r"^i40e[0-9]+$",               # Intel 40GbE (i40e driver)
	r"^bnxt[0-9]+$",               # Broadcom NetXtreme
	r"^mlx[0-9]+_[0-9]+$",         # Mellanox (some variants)
	r"^eth[0-9]+_[0-9]+$",         # Some multi-port NICs
)

VIRTUAL_BRIDGE_PATTERNS = (r"^vmbr[0-9].*$",)

VIRTUAL_INTERFACE_PATTERNS = (
	r"^veth[0-9].*$",
	r"^fwbr[0-9].*$",
	r"^fwln[0-9].*$",
	r"^fwpr[0-9].*$",
	r"^tap[0-9a-fA-F].*$",
)


def get_interfaces(
	interface_patterns: tuple | list = PHYSICAL_INTERFACE_PATTERNS,
	override_patterns: bool = False,
	verbose: bool = False,
	exclude_patterns: tuple | list | None = None,
) -> list:
	"""
	Fetches physical interface names and returns them as a list.
	If override_patterns is set to True then only the patterns passed will be matched.
	"""
	if not interface_patterns and override_patterns:
		print(
			"interface_patterns should contain at least one Regex Pattern if override_patterns is used."
		)

	filtered_interfaces = []
	network_interfaces = os.listdir("/sys/class/net/")
	check_patterns = []

	if interface_patterns:
		for pattern in interface_patterns:
			check_patterns.append(re.compile(pattern))
	for iface in network_interfaces:
		iface = iface.strip()
		skip = False
		match = False

		if exclude_patterns:
			for regex in exclude_patterns:
				if re.match(regex, iface):
					skip = True
		if skip:
			continue

		for regex in check_patterns:
			if re.match(regex, iface) and iface not in filtered_interfaces:
				filtered_interfaces.append(iface)
				match = True

		if not match and verbose:
			print_c(
				bcolors.L_BLUE, f"[DEBUG] - Skipping {iface} (did not match regex)."
			)
	return filtered_interfaces
