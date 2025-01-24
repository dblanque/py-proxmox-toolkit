UDEV_BY_MAC_ADDRESS = """
[Match]
MACAddress={iface_mac_addr}
Type=ether

[Link]
Name={iface_name}
"""

UDEV_BY_PROPERTY = """
[Match]
{attrs}

[Link]
Name={iface_name}
MACAddress={iface_mac_addr}
"""