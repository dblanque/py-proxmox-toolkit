SRC_PVE_NO_SUBSCRIPTION_LIST = """
# PVE pve-no-subscription repository provided by proxmox.com
# NOT recommended for production use
deb http://download.proxmox.com/debian/pve {0} pve-no-subscription
"""

SRC_PVE_ENTERPRISE_LIST = """
# PVE pve-enterprise repository provided by proxmox.com
deb https://enterprise.proxmox.com/debian/pve {0} pve-enterprise
"""

SRC_PVE_NO_SUBSCRIPTION_SOURCES = """
# PVE pve-no-subscription repository provided by proxmox.com
# NOT recommended for production use
Types: deb
URIs: http://download.proxmox.com/debian/pve
Suites: {0}
Components: pve-no-subscription
Signed-By: /usr/share/keyrings/proxmox-archive-keyring.gpg
"""

SRC_PVE_ENTERPRISE_SOURCES = """
# PVE pve-enterprise repository provided by proxmox.com
Types: deb
URIs: https://enterprise.proxmox.com/debian/pve
Suites: {0}
Components: pve-enterprise
Signed-By: /usr/share/keyrings/proxmox-archive-keyring.gpg
"""

SRC_PVE_APT_FORMAT_MAP = {
	"bookworm": {
		"no-subscription": SRC_PVE_NO_SUBSCRIPTION_LIST,
		"enterprise": SRC_PVE_ENTERPRISE_LIST,
	},
	"trixie": {
		"no-subscription": SRC_PVE_NO_SUBSCRIPTION_SOURCES,
		"enterprise": SRC_PVE_ENTERPRISE_SOURCES,
	},
}
