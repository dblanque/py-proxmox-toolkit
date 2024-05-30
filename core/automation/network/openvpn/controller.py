if __name__ == "__main__":
	raise Exception("This module cannot be executed as a script")

from core.classes.AttrDict import NamedDict
from core.format.colors import print_c, bcolors
import subprocess

class VPNController():
	def __init__(self, net_command: str, connection_name: str, **kwargs):
		try:
			self.command = net_command
		except:
			raise AttributeError(self, 'net_command')

		try:
			self.connection = connection_name
		except:
			raise AttributeError(self, 'connection_name')
		self.args = NamedDict()

		self.args.main = None
		if self.command == 'nmcli':
			self.args.main = 'con'
			self.args.activate = 'up'
			self.args.deactivate = 'down'
			self.args.status = 'show'
		elif self.command == 'systemctl':
			self.args.activate = 'start'
			self.args.deactivate = 'stop'
			self.args.status = 'status'

		for k in kwargs.keys():
			self.args[k] = kwargs[k]

	def status(self):
		command = [self.command, self.args.status, self.connection]
		if self.args.main:
			command.insert(1, self.args.main)
		print_c(bcolors.BLUE, f"Executing Command: {command}")
		return subprocess.call(command)

	def activate(self) -> int:
		command = [self.command, self.args.activate, self.connection]
		if self.args.main:
			command.insert(1, self.args.main)
		print_c(bcolors.BLUE, f"Executing Command: {command}")
		return subprocess.call(command)

	def deactivate(self) -> int:
		command = [self.command, self.args.deactivate, self.connection]
		if self.args.main:
			command.insert(1, self.args.main)
		print_c(bcolors.BLUE, f"Executing Command: {command}")
		return subprocess.call(command)
