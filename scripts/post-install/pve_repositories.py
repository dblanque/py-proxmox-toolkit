#!/usr/env/python3
if __name__ != "__main__":
	raise ImportError("This python script cannot be imported.")

import os
import sys
VENV_DIR = os.path.abspath(os.environ['VIRTUAL_ENV']) or None
if not VENV_DIR:
	print(VENV_DIR)
	raise Exception('Could not append VENV_DIR to PATH')
sys.path.append(VENV_DIR)

MIN_VERSION = "8.0.0"
from py_pve_toolkit.debian import os_release
from py_pve_toolkit.proxmox.pve_manager import pve_version_exists, get_pve_version
from packaging.version import Version

def main():
	# Check if proxmox version valid (>8.0)
	release_info = os_release.get_data()
	if release_info["id"] != "debian": raise Exception()
	if not pve_version_exists: raise Exception()
	if Version(get_pve_version()) < Version(MIN_VERSION): raise Exception()

	# Setting debian sources
	# Setting PVE No-Subscription or Enterprise Sources
	# Setting CEPH No-Subscription or Enterprise Sources
	# Disabling HA (Default NO)
	# Update Proxmox
	# Offer Reboot

if __name__ == "__main__": main()