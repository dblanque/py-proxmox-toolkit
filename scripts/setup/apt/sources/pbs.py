SRC_PBS_NO_SUBSCRIPTION_LIST = """
# PBS pbs-no-subscription repository provided by proxmox.com
# NOT recommended for production use
deb http://download.proxmox.com/debian/pbs {0} pbs-no-subscription
"""

SRC_PBS_ENTERPRISE_LIST = """
# PBS pbs-enterprise repository provided by proxmox.com
# deb https://enterprise.proxmox.com/debian/pbs {0} pbs-enterprise
"""

SRC_PBS_NO_SUBSCRIPTION_SOURCES = """
# PBS pbs-no-subscription repository provided by proxmox.com
# NOT recommended for production use
Types: deb
URIs: http://download.proxmox.com/debian/pbs
Suites: {0}
Components: pbs-no-subscription
Signed-By: /usr/share/keyrings/proxmox-archive-keyring.gpg
"""

SRC_PBS_ENTERPRISE_SOURCES = """
# PBS pbs-enterprise repository provided by proxmox.com
Types: deb
URIs: https://enterprise.proxmox.com/debian/pbs
Suites: {0}
Components: pbs-enterprise
Signed-By: /usr/share/keyrings/proxmox-archive-keyring.gpg
"""

SRC_PBS_APT_FORMAT_MAP = {
	"bookworm": {
		"no-subscription": SRC_PBS_NO_SUBSCRIPTION_LIST,
		"enterprise": SRC_PBS_ENTERPRISE_LIST,
	},
	"trixie": {
		"no-subscription": SRC_PBS_NO_SUBSCRIPTION_SOURCES,
		"enterprise": SRC_PBS_ENTERPRISE_SOURCES,
	},
}
