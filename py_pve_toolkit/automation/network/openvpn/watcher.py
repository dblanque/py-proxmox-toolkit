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

# Imports
import subprocess
from py_pve_toolkit.parser import ColoredArgParser
from py_pve_toolkit.format.colors import print_c, bcolors
from py_pve_toolkit.network.ping import ping
from controller import VPNController
from time import sleep

prog_name = "OpenVPN Watcher"
parser = ColoredArgParser(
	prog=prog_name,
	description='This script allows for ping-based VPN Tunnel restoration',
	epilog='If you use systemctl for OpenVPN, drop the certificate in\
		/etc/openvpn and rename the suffix to *.conf')
parser.add_argument('-g', '--gateway', required=True)
parser.add_argument('-c', '--connection-name', required=True,
		    help='OpenVPN Connection or Certificate Name')
parser.add_argument('-pc', '--ping-count', default=3)
parser.add_argument('-t', '--timeout', default=3,
		    help='How long to wait until ping is considered a fail')
parser.add_argument('-i', '--interval', default=30,
			help='How often to check Gateway Availability')
parser.add_argument('-n', '--use-network-manager',
			help='How often to check Gateway Availability',
			action='store_true',
			default=False)
parser.add_argument('-pa', '--ping-args',
			default=None,
			help='Extra Args to pass to Ping Command, separated by spaces.'
)
parser.add_argument('-s', '--script',
			default=None,
			help='Extra Script to execute after VPN Restart (Must be a file).'
)
parser.add_argument('-sa', '--script-args',
			default=None,
			help='Args to pass to Extra Script'
)
parser.add_argument('-sh', '--shell',
			default='bash',
			help='Shell to use for Extra Script.',
			choices=['sh', 'bash', 'zsh', 'ksh', 'csh']
)
args = parser.parse_args()

gateway=args.gateway
connection=args.connection_name
use_network_manager=args.use_network_manager
ping_timeout=args.timeout
ping_count=args.timeout
interval=args.interval
ping_args=args.ping_args
script=args.script
script_args=args.script_args
shell=args.shell

script_file_exists=os.path.isfile(script)

if interval <= ping_timeout:
	msg=f"The gateway check Interval cannot be shorter than the Ping Timeout"
	print_c(bcolors.RED, msg)
	raise ValueError(interval, ping_timeout)

def main():
	if len(gateway) < 1:
		raise ValueError(gateway)
	print_c(bcolors.L_GREEN, f"{prog_name} started")
	if ping_args and len(ping_args) > 0: ping_args_array = ping_args.split(" ") 
	else: ping_args_array=list()
	while True:
		ping_success = False
		if ping(gateway, ping_count, ping_timeout, args=ping_args_array) == 0:
			ping_success = True
			msg=f"Ping to gateway successful"
			print_c(bcolors.L_GREEN, msg)

		if not ping_success:
			msg=f"Did not get ping response for {ping_timeout} seconds"
			print_c(bcolors.RED, msg)

			if use_network_manager:
				command = 'nmcli'
			else:
				command = 'systemctl'

			openvpn = VPNController(
				net_command=command, 
				connection_name=connection
			)

			msg=f'Deactivating Connection for 5 seconds'
			print_c(bcolors.YELLOW, msg)

			try:
				openvpn.deactivate()
			except Exception as e:
				print_c(bcolors.YELLOW, f"VPN Handler Exception")
				print(e)
				pass
				# if isinstance(e, ChildProcessError):
				# 	sys.exit(2)
				# raise
			sleep(5)

			msg=f'Attempting Re-connection'
			print_c(bcolors.BLUE, msg)
			sleep(5)

			vpn_activated=True
			try:
				openvpn.activate()
			except Exception as e:
				print_c(bcolors.YELLOW, f"VPN Handler Exception")
				print(e)
				vpn_activated=False
				pass
				# if isinstance(e, ChildProcessError):
				# 	sys.exit(2)
				# raise

			# Execute Post Script
			if script_file_exists and vpn_activated:
				command = [f"/bin/{shell}", script]
				if script_args:
					for a in script_args.split(' '):
						command.append(a)
				try:
					subprocess.call(command)
				except:
					raise
			elif script:
				print_c(bcolors.RED, "Could not activate VPN, skipping script execution")

		msg=f'Checking again in {interval} seconds'
		print_c(bcolors.BLUE, msg)
		sleep(interval)

if __name__ == "__main__":
	try:
		main()
	except KeyboardInterrupt:
		sys.path.remove(VENV_DIR)
		msg=f"{prog_name} stopped"
		print_c(bcolors.BLUE, msg)
		try:
			sys.exit(130)
		except SystemExit:
			os._exit(130)
