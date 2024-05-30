SRC_CEPH_QUINCY_NO_SUBSCRIPTION = """# CEPH Quincy No Subscription Repository
deb http://download.proxmox.com/debian/ceph-quincy {debian_distribution} no-subscription
# deb http://download.proxmox.com/debian/ceph-quincy {debian_distribution} enterprise
"""
SRC_CEPH_QUINCY_ENTERPRISE = """# CEPH Quincy Enterprise Repository
# deb http://download.proxmox.com/debian/ceph-quincy {debian_distribution} no-subscription
deb http://download.proxmox.com/debian/ceph-quincy {debian_distribution} enterprise
"""

SRC_CEPH_REEF_NO_SUBSCRIPTION = """# CEPH Reef No Subscription Repository
deb http://download.proxmox.com/debian/ceph-reef {debian_distribution} no-subscription
# deb http://download.proxmox.com/debian/ceph-reef {debian_distribution} enterprise
"""
SRC_CEPH_REEF_ENTERPRISE = """# CEPH Reef Enterprise Repository
# deb http://download.proxmox.com/debian/ceph-reef {debian_distribution} no-subscription
deb http://download.proxmox.com/debian/ceph-reef {debian_distribution} enterprise
"""

CEPH_SOURCES = {
	"QUINCY":{
		"NO_SUBSCRIPTION":SRC_CEPH_QUINCY_NO_SUBSCRIPTION,
		"ENTERPRISE":SRC_CEPH_QUINCY_ENTERPRISE
	},
	"REEF":{
		"NO_SUBSCRIPTION":SRC_CEPH_REEF_NO_SUBSCRIPTION,
		"ENTERPRISE":SRC_CEPH_REEF_ENTERPRISE
	},
}