VMBR_TEMPLATE_LINUX = """
auto {bridge_name}
iface {bridge_name} inet static
        address {bridge_address_cidr}
        bridge-ports {bridge_ports}
        bridge-stp off
        bridge-fd 0
#{bridge_description}
"""

VMBR_TEMPLATE_OVS = """
"""
