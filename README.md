# Proxmox Python Toolkit

## Installation and usage (Without PIP)
All dependencies will work, pip packages are not required for any scripts for the moment.
The standard APT Python3 package will suffice.

```bash
# Update and ensure git and python3 are installed.
apt update -y
apt install git python3 -y

# Choose a preferred directory to clone the repo
cd /opt/

# Clone the Repository
git clone https://github.com/dblanque/py-pve-toolkit

# Change Directory
cd ./py-pve-toolkit

# Using pve_repositories.py as an example.
python3 main.py scripts.post_install.pve_repositories
```

## Installation (With PIP)
- Not required for any scripts as of yet.

```bash
# After executing the previous steps above, ensure python3-venv is installed.
apt install python3-venv -y

# Setup the virtual environment with the provided script.
bash setup_venv.sh ./
```

<a href='https://ko-fi.com/E1E2YQ4TG' target='_blank'><img height='36' style='border:0px;height:36px;' src='https://storage.ko-fi.com/cdn/kofi2.png?v=3' border='0' alt='Buy Me a Coffee at ko-fi.com' /></a>