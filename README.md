# Proxmox Python Toolkit


## Installation and usage (Without PIP)
All dependencies will work, pip packages are not required for any scripts for the moment.
The standard APT `python3` package will suffice.

### Auto-complete
If auto-complete is desired you'll also require `python3-argcomplete`, and always be
in the python toolkit folder.

```bash
# Update and ensure git and python3 are installed.
apt update -y
apt install git python3 -y

# If auto-complete is desired
apt install python3-argcomplete

# Choose a preferred directory to clone the repo
cd /opt/

# Clone the Repository
git clone https://github.com/dblanque/py-proxmox-toolkit

# Change Directory
cd /opt/py-proxmox-toolkit

# If auto-complete is desired
sudo bash enable_autocomplete.sh

# Using pve_repositories.py as an example.
./main.py scripts/setup/microcode.py

# OR
./main.py scripts.post_install.pve_repositories
```

## Installation (With PIP)
- NOT REQUIRED AS OF YET.

```bash
# After executing the previous steps above, ensure python3-venv is installed.
apt install python3-venv -y

# Setup the virtual environment with the provided script.
cd /opt/py-proxmox-toolkit
bash setup_venv.sh ./
```

<a href='https://ko-fi.com/E1E2YQ4TG' target='_blank'><img height='36' style='border:0px;height:36px;' src='https://storage.ko-fi.com/cdn/kofi2.png?v=3' border='0' alt='Buy Me a Coffee at ko-fi.com' /></a>