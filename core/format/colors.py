# For more ANSI Color Codes see:
# https://misc.flogisoft.com/bash/tip_colors_and_formatting
from enum import Enum


class bcolors(Enum):
	def __str__(self):
		return str(self.value)

	# Colors
	RED = "\033[1;31m"
	GREEN = "\033[1;32m"
	YELLOW = "\033[1;33m"
	BLUE = "\033[1;34m"
	MAGENTA = "\033[1;35m"
	CYAN = "\033[1;36m"
	L_RED = "\033[91m"
	L_GREEN = "\033[92m"
	L_YELLOW = "\033[93m"
	L_BLUE = "\033[94m"
	L_MAGENTA = "\033[95m"
	L_CYAN = "\033[96m"

	# Formatting
	NC = "\033[0m"  # No Color
	BOLD = "\033[1m"
	UNDERLINE = "\033[4m"
	BLINK = "\033[5m"


def print_c(color: bcolors, message: str, **kwargs):
	"""
	Concatenates and prints {color}{message}{nc}
	"""
	return print(f"{color}{message}{bcolors.NC}", **kwargs)


def colorize(color: bcolors, message: str):
	return f"{color}{message}{bcolors.NC}"


def main(**kwargs):
	for color in bcolors:
		print(f"{color}{color.name}{bcolors.NC}")


if __name__ == "__main__":
	try:
		main()
	except:
		raise
