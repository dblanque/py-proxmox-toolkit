#!/usr/env/python3
# TODO - Finish this script
# Installs and configures Chrony
import subprocess, os, sys
prog_name = "Python Chrony NTP Installer"

VENV_DIR = os.path.abspath(os.environ['VIRTUAL_ENV']) or None
if not VENV_DIR:
	print(VENV_DIR)
	raise Exception('Could not append VENV_DIR to PATH')
sys.path.append(VENV_DIR)

from py_pve_toolkit.format.colors import bcolors, print_c

def main():
	command = ['dpkg', '-l', 'ntp']
	ntp_installed = subprocess.check_call(command, stdout=open(os.devnull, 'wb'), stderr=subprocess.STDOUT) == 0

	if not ntp_installed:
		command = ['sudo','apt', 'update']
		subprocess.check_call(command, stdout=open(os.devnull, 'wb'), stderr=subprocess.STDOUT)
		command = ['sudo','apt', 'install', 'chrony', '-y']
		ntp_install_result = subprocess.call(command) == 0

	ntp_servers = []

	input_msg = "NTP Server IP - (Press Enter to Continue): "
	new_ip = '127.0.0.1'

	while True and len(new_ip) != 0:
		new_ip = input(input_msg)
		if len(new_ip) > 0:
			ntp_servers.append(new_ip)

	for ip in ntp_servers:
		print(f"NTP Server: {ip}")

if __name__ == "__main__":
	try:
		main()
	except KeyboardInterrupt:
		msg=f"\n{prog_name} stopped"
		print_c(bcolors.BLUE, msg)
		try:
			sys.exit(130)
		except SystemExit:
			os._exit(130)