#!/usr/bin/python3
from argparse import ArgumentParser
import sys
import os

toolkit_path=os.path.dirname(__file__)
main_parser = ArgumentParser(
	prog='Python Proxmox Toolkit Parser',
	description='Use this program to execute sub-scripts from the toolkit',
	add_help=False
)
main_parser.add_argument('filename')
args, unknown_args = main_parser.parse_known_args()

is_interactive = bool(getattr(sys, 'ps1', sys.flags.interactive))
if is_interactive:
	print("Interactive mode enabled.")

parsed_filename = args.filename.rstrip(".py").replace("/", ".")

try:
	# Import sub-script module
	module = __import__(parsed_filename, fromlist=["main", "argparser"])
	script_func = getattr(module, "main")
except ImportError:
	sys.exit(f"Error: Sub-script '{parsed_filename}' not found.")
except AttributeError:
	sys.exit(f"Error: Sub-script '{parsed_filename}' has no 'main' function.")

# Check if sub-script provides an argparser
script_parser = getattr(module, "argparser", None)
if script_parser:
	# Initialize sub-script's parser (without inheriting main_parser)
	sub_parser = script_parser()
	# Parse remaining arguments
	sub_args = sub_parser.parse_args(unknown_args)
	script_func(sub_args, toolkit_path=toolkit_path)
else:
	# Pass no arguments if no parser exists
	script_func(toolkit_path=toolkit_path)

if not is_interactive:
	sys.exit(0)