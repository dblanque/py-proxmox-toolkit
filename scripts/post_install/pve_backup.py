#!/usr/env/python3
if __name__ != "__main__":
	raise ImportError("This python script cannot be imported.")

import os, sys, subprocess
VENV_DIR = os.path.abspath(os.environ['VIRTUAL_ENV']) or None
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
if not VENV_DIR:
	print(VENV_DIR)
	raise Exception('Could not append VENV_DIR to PATH')
sys.path.append(VENV_DIR)
sys.path.append(SCRIPT_DIR)