
# Examples

Below you will find examples of some of the many scripts available in this
toolkit.

It is assumed you're in the directory of the toolkit itself.

You may use the `-h, --help` flag or press tab if auto-complete is enabled to
see all available args for each script.


# Generic Scripts
Generic scripts may be used in any host with an `Debian` or `Ubuntu` based
distribution, as they generally share most dependencies and paths (and Proxmox
is based on Debian).

## Update Script
Update Operating System and remove/clean-up old packages.

`./main.py scripts/general/update.py`

## Install Microcode
Installs microcode based on your CPU brand (AMD/Intel).

`./main.py scripts/setup/microcode.py`

## Setup Debian Sources
Sets up Debian sources files. Not required if you've already executed the child
script `scripts/setup/apt/sources/pve.py`.

`./main.py scripts/setup/debian/repositories.py`

## Install Bash Aliases and Auto-complete
Allows you to install some useful aliases and/or bash-completion.

`./main.py scripts/setup/install_aliases.py`

## Install Linux Utilities / Packages
Installs useful linux packages onto your system.

For a full package list you may inspect the code.

### Install All Packages
`./main.py scripts/setup/install_tools.py`

### Install Fewer Packages
`./main.py scripts/setup/install_tools.py --light`

## Installs Chrony from APT Repositories
`./main.py scripts/setup/install_chrony.py`

# Proxmox Scripts
This section includes scripts for *both* Proxmox VE and Proxmox BS.

## PVE Config Files Backup

`./main.py scripts/setup/pve/backup.py -p <backup-path>`

## Setup Proxmox VE Sources
Set-up Proxmox VE Sources including no-subscription or enterprise Proxmox
Repositories.

`./main.py scripts/setup/pve/repositories.py`

## Change Proxmox VE Guest ID
Allows you to change a Guest's ID. You may use the `--dry-run` flag to see what
it does without applying the changes.

`./main.py scripts/guests/change_id.py -i <origin-id> -t <target-id>`

## Setup CEPH Sources
Sets up CEPH Sources list files, not required if you've already executed the
parent script `scripts/setup/apt/sources/pve.py`.

`./main.py scripts/setup/apt/sources/ceph.py`

## Setup Proxmox Backup Server Sources
Sets up PBS APT Sources Files.
`./main.py scripts/setup/pbs/repositories.py`

## List Interfaces
Even if listed specifically as a Proxmox Script, this may be used in any
`Debian` or `Ubuntu` based distro.

A script to list interfaces. This may later be moved to a different directory
instead of the `pve` sub-folder.

`./main.py scripts/setup/pve/list_interfaces.py`

### List Virtual Interfaces

`./main.py scripts/setup/pve/list_interfaces.py -v`

### List Physical Interfaces

`./main.py scripts/setup/pve/list_interfaces.py -p`

## Pin Network Interfaces
Allows you to **pin interfaces** to specified attributes, binding to the
interface MAC Address by default. This script may also be used in any `Debian`
or `Ubuntu` based distro.

`./main.py scripts/setup/pve/pin_interfaces.py`

## Other Scripts

* `scripts/guests/cloudinit_ip_based_on_host.py`
* `scripts/setup/debian/set_apt_cacher.py`

### Staged Net Changer with Rollback Options

See file `scripts/guests/staged_net_change.py` help argument.

# Guest Scripts

## Enable xTermJS Socket
This is intended for VM Guests. Enables the xtermjs serial socket terminal.

`./main.py scripts/setup/debian/xtermjs_socket.py`

## xTermJS Terminal Size Patcher
This is intended for VM Guests. Patches the default `/etc/profile` with a 
xtermjs terminal size fix. 

This fix only applies on login so make sure to size the terminal to your
liking before.

`./main.py scripts/setup/debian/xtermjs_resize.py`

## Proxmox VE Bridge Generator
Utility script to automatically generate bridges for all your physical
interfaces. Useful when you have 4+ NICs/Ports.

There are some examples below but you may check the script's help args for the
full capabilities.

### Reconfigure All Bridges

`./main.py scripts/setup/pve/generate_bridges.py -r`

### Generate without removing offloading

`./main.py scripts/setup/pve/generate_bridges.py -x`
