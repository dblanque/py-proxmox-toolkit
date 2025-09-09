SRC_CEPH_QUINCY_NO_SUBSCRIPTION = """# CEPH Quincy No Subscription Repository
deb http://download.proxmox.com/debian/ceph-quincy {0} no-subscription
# deb http://download.proxmox.com/debian/ceph-quincy {0} enterprise
"""
SRC_CEPH_QUINCY_ENTERPRISE = """# CEPH Quincy Enterprise Repository
# deb http://download.proxmox.com/debian/ceph-quincy {0} no-subscription
deb http://download.proxmox.com/debian/ceph-quincy {0} enterprise
"""

SRC_CEPH_REEF_NO_SUBSCRIPTION = """# CEPH Reef No Subscription Repository
deb http://download.proxmox.com/debian/ceph-reef {0} no-subscription
# deb http://download.proxmox.com/debian/ceph-reef {0} enterprise
"""
SRC_CEPH_REEF_ENTERPRISE = """# CEPH Reef Enterprise Repository
# deb http://download.proxmox.com/debian/ceph-reef {0} no-subscription
deb http://download.proxmox.com/debian/ceph-reef {0} enterprise
"""

SRC_CEPH_SQUID_NO_SUBSCRIPTION = """# CEPH Reef No Subscription Repository
Types: deb
URIs: http://download.proxmox.com/debian/ceph-squid
Suites: {0}
Components: no-subscription
Signed-By: /usr/share/keyrings/proxmox-archive-keyring.gpg
"""
SRC_CEPH_SQUID_ENTERPRISE = """# CEPH Reef Enterprise Repository
Types: deb
URIs: https://enterprise.proxmox.com/debian/ceph-squid
Suites: {0}
Components: enterprise
Signed-By: /usr/share/keyrings/proxmox-archive-keyring.gpg
"""

CEPH_SOURCES = {
	"QUINCY": {
		"no-subscription": SRC_CEPH_QUINCY_NO_SUBSCRIPTION,
		"enterprise": SRC_CEPH_QUINCY_ENTERPRISE,
	},
	"REEF": {
		"no-subscription": SRC_CEPH_REEF_NO_SUBSCRIPTION,
		"enterprise": SRC_CEPH_REEF_ENTERPRISE,
	},
	"SQUID": {
		"no-subscription": SRC_CEPH_SQUID_NO_SUBSCRIPTION,
		"enterprise": SRC_CEPH_SQUID_ENTERPRISE,
	},
}
