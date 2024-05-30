import os
from .format.colors import bcolors
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
VENV_DIR = os.path.abspath(os.environ['VIRTUAL_ENV']) or None

if not VENV_DIR:
	print(f"{bcolors.RED}Error: Please activate the Python Virtual Environment.{bcolors.NC}")
	raise Exception()
