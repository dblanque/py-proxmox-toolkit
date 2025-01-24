#!/usr/bin/python3
from argparse import ArgumentParser
import sys

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

# Construct sub-script name
parsed_filename = str(args.filename)
if parsed_filename.endswith(".py"):
	parsed_filename = parsed_filename.split(".py")[0]
	parsed_filename = parsed_filename.replace("/",".")

# Import main function from sub-script
script_func = getattr(__import__(parsed_filename, fromlist=["main"]), "main")
script_parser = None
if hasattr(__import__(parsed_filename, fromlist=["argparser"]), "argparser"):
	script_parser = getattr(__import__(parsed_filename, fromlist=["argparser"]), "argparser")

if script_func and script_parser:
	new_parser: ArgumentParser = script_parser(
		parents=[ main_parser ]
	)
	args = new_parser.parse_args()
	script_func(args)
else: script_func()

if not is_interactive:
	sys.exit(0)