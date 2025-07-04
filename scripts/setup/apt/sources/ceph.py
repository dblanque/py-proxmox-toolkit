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

CEPH_SOURCES = {
	"QUINCY": {
		"NO_SUBSCRIPTION": SRC_CEPH_QUINCY_NO_SUBSCRIPTION,
		"ENTERPRISE": SRC_CEPH_QUINCY_ENTERPRISE,
	},
	"REEF": {
		"NO_SUBSCRIPTION": SRC_CEPH_REEF_NO_SUBSCRIPTION,
		"ENTERPRISE": SRC_CEPH_REEF_ENTERPRISE,
	},
}
