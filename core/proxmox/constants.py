# Author: Dylan Blanqué
# BR Consulting S.R.L. 2024
PVE_CFG_ROOT = "/etc/pve"
PVE_CFG_NODES_DIR = f"{PVE_CFG_ROOT}/nodes"
PVE_CFG_STORAGE = f"{PVE_CFG_ROOT}/storage.cfg"
PVE_CFG_REPLICATION = f"{PVE_CFG_ROOT}/replication.cfg"
STORAGE_TYPES = ["lvm", "lvmthin", "zfspool", "dir", "cephfs", "rbd"]
DISK_TYPES = [
	"ide",
	"sata",
	"scsi",
	"virtio",
	"unused",
	"mp",
	"rootfs",
	"vmstate",
]
