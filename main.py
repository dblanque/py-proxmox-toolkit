#!/usr/bin/python3
import argparse, sys
is_interactive = bool(getattr(sys, 'ps1', sys.flags.interactive))
if is_interactive: print("Interactive mode enabled.")
parser = argparse.ArgumentParser(
	prog='Main Program file for Python Proxmox Toolkit Execution',
	description='Use this program to execute sub-scripts from the toolkit',
	add_help=False
)
parser.add_argument('filename')
args, unknown_args = parser.parse_known_args()

# Construct sub-script name
try:
	parsed_filename = str(args.filename)
	if parsed_filename.endswith(".py"):
		parsed_filename = parsed_filename.split(".py")[0]
		parsed_filename = parsed_filename.replace("/",".")
except: raise

# Import main function from sub-script
try:
	script_func = getattr(__import__(parsed_filename, fromlist=["main"]), "main")
	script_parser = None
	if hasattr(__import__(parsed_filename, fromlist=["argparser"]), "argparser"):
		script_parser = getattr(__import__(parsed_filename, fromlist=["argparser"]), "argparser")
except:
	if is_interactive: print("No main function detected.")
	else: raise

# Import argparser function from subscript if existent.
try:
	if script_parser:
		new_parser: argparse.ArgumentParser = script_parser()
		new_parser.add_argument('filename')
		args = new_parser.parse_args()
		script_func(args)
	else: script_func()
except: 
	if is_interactive: print("No argparser function detected.")
	else: raise

if not is_interactive:
	sys.exit(0)