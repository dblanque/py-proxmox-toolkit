#!/usr/bin/python3
if __name__ == "__main__":
	raise Exception("This python script cannot be executed individually, please use main.py")

# Imports
import os
import sys
import subprocess
from core.format.colors import print_c, bcolors
from core.network.ping import ping
from core.automation.network.openvpn.controller import VPNController
from time import sleep
from core.parser import make_parser, ArgumentParser

SCRIPT_NAME = "OpenVPN Watcher"
def argparser(**kwargs) -> ArgumentParser:
	parser = make_parser(
		prog=SCRIPT_NAME,
		description='This script allows for ping-based VPN Tunnel restoration',
		epilog='If you use systemctl for OpenVPN, drop the certificate in \
			/etc/openvpn and rename the suffix to *.conf',
		**kwargs
	)
	parser.add_argument('-g', '--gateway', required=True)
	parser.add_argument('-c', '--connection-name', required=True,
				help='OpenVPN Connection or Certificate Name')
	parser.add_argument('-pc', '--ping-count', default=3)
	parser.add_argument('-t', '--timeout', default=3,
				help='How long to wait until ping is considered a fail')
	parser.add_argument('-i', '--interval', default=30,
				help='How often to check Gateway Availability')
	parser.add_argument('-n', '--use-network-manager',
				help='Use Network Manager (nmcli) instead of SystemD',
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
	return parser

def main(argv_a, **kwargs):
	gateway=argv_a.gateway
	connection=argv_a.connection_name
	use_network_manager=argv_a.use_network_manager
	ping_timeout=argv_a.timeout
	ping_count=argv_a.timeout
	interval=argv_a.interval
	ping_args=argv_a.ping_args
	script=argv_a.script
	script_args=argv_a.script_args
	shell=argv_a.shell

	script_file_exists = os.path.isfile(script) if script else None

	if interval <= ping_timeout:
		msg="The gateway check Interval cannot be shorter than the Ping Timeout"
		print_c(bcolors.RED, msg)
		raise ValueError(interval, ping_timeout)
	if len(gateway) < 1:
		raise ValueError(gateway)
	print_c(bcolors.L_GREEN, f"{SCRIPT_NAME} started.")

	if ping_args and len(ping_args) > 0: ping_args_array = ping_args.split(" ")
	else: ping_args_array = []
	while True:
		ping_success = False
		if ping(gateway, ping_count, ping_timeout, args=ping_args_array) == 0:
			ping_success = True
			msg="Ping to gateway successful"
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

			msg='Deactivating Connection for 5 seconds'
			print_c(bcolors.YELLOW, msg)

			try:
				openvpn.deactivate()
			except Exception as e:
				print_c(bcolors.YELLOW, "VPN Handler Exception")
				print(e)
				pass
				# if isinstance(e, ChildProcessError):
				# 	sys.exit(2)
				# raise
			sleep(5)

			msg='Attempting Re-connection'
			print_c(bcolors.BLUE, msg)
			sleep(5)

			vpn_activated=True
			try:
				openvpn.activate()
			except Exception as e:
				print_c(bcolors.YELLOW, "VPN Handler Exception")
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
		msg=f"{SCRIPT_NAME} stopped"
		print_c(bcolors.BLUE, msg)
		try:
			sys.exit(130)
		except SystemExit:
			os._exit(130)
