#!/venv/bin/python
if __name__ == "__main__":
	raise Exception("This module cannot be executed as a script")

# Source for ColoredArgParser: https://stackoverflow.com/questions/47155189/how-to-output-color-using-argparse-in-python-if-any-errors-happen
import sys
from core.format.colors import bcolors
from argparse import ArgumentParser
from gettext import gettext

class ColoredArgParser(ArgumentParser):

	# color_dict is a class attribute, here we avoid compatibility
	# issues by attempting to override the __init__ method
	# RED : Error, GREEN : Okay, YELLOW : Warning, Blue: Help/Info

	def print_usage(self, file = None):
		if file is None:
			file = sys.stdout
		self._print_message(self.format_usage()[0].upper() +
							self.format_usage()[1:],
							file, bcolors.YELLOW)

	def print_help(self, file = None):
		if file is None:
			file = sys.stdout
		self._print_message(self.format_help()[0].upper() +
							self.format_help()[1:],
							file, bcolors.BLUE)

	def _print_message(self, message, file = None, color = None):
		if message:
			if file is None:
				file = sys.stderr
			# Print messages in bold, colored text if color is given.
			if color is None:
				file.write(message)
			else:
				# \x1b[ is the ANSI Control Sequence Introducer (CSI)
				file.write('\x1b[' + color.value + message.strip() + '\x1b[0m\n')

	def exit(self, status = 0, message = None):
		if message:
			self._print_message(message, sys.stderr, bcolors.RED)
		sys.exit(status)

	def error(self, message):
		self.print_usage(sys.stderr)
		args = {'prog' : self.prog, 'message': message}
		self.exit(2, gettext('%(prog)s: Error: %(message)s\n') % args)

def make_parser(**kwargs) -> ArgumentParser:
	parser = ColoredArgParser(**kwargs)
	return parser
