UDEV_BY_MAC_ADDRESS = """
[Match]
MACAddress={iface_mac_addr}
Type=ether

[Link]
Name={iface_name}
"""