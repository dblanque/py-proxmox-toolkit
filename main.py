#!/usr/bin/python3
import argparse, sys
parser = argparse.ArgumentParser(
	prog='Main Program file for Python Proxmox Toolkit Execution',
	description='Use this program to execute sub-scripts from the toolkit',
	add_help=False
)
parser.add_argument('filename')
args, unknown_args = parser.parse_known_args()
try:
	parsed_filename = str(args.filename)
	if parsed_filename.endswith(".py"):
		parsed_filename = parsed_filename.split(".py")[0]
		parsed_filename = parsed_filename.replace("/",".")
except: raise
script_func = getattr(__import__(parsed_filename, fromlist=["main"]), "main")
script_parser = None
if hasattr(__import__(parsed_filename, fromlist=["argparser"]), "argparser"):
	script_parser = getattr(__import__(parsed_filename, fromlist=["argparser"]), "argparser")
try:
	if script_parser:
		new_parser: argparse.ArgumentParser = script_parser()
		new_parser.add_argument('filename')
		args = new_parser.parse_args()
		script_func(args)
	else: script_func()
except: raise
sys.exit(0)