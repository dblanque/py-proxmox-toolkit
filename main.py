#!/usr/bin/python3
# PYTHON_ARGCOMPLETE_OK
from argparse import ArgumentParser
import sys
import os
import importlib.util
from core.utils.path import path_as_module
from core.utils.shell import is_completion_context

# Import and use argcomplete if available
argcomplete_spec = importlib.util.find_spec("argcomplete")
use_argcomplete = argcomplete_spec is not None and is_completion_context()
if use_argcomplete:
	from argcomplete import autocomplete
	from core.autocomplete import ToolkitCompleter

TOOLKIT_PATH=os.path.dirname(__file__)
main_parser = ArgumentParser(
	prog='Python Proxmox Toolkit Parser',
	description='Use this program to execute sub-scripts from the toolkit',
	add_help=False
)

if use_argcomplete:
	main_parser.add_argument(
		'filename',
		help="Script name or path to execute."
	).completer = ToolkitCompleter(TOOLKIT_PATH)
	# Enable argcomplete
	autocomplete(main_parser)
else:
	main_parser.add_argument(
		'filename',
		help="Script name or path to execute."
	)

args, unknown_args = main_parser.parse_known_args()

is_interactive = bool(getattr(sys, 'ps1', sys.flags.interactive))
if is_interactive:
	print("Interactive mode enabled.")

if args.filename.endswith(".py") or "/" in args.filename:
	parsed_filename = path_as_module(args.filename)
else:
	parsed_filename = args.filename

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
	# Initialize sub-script's parser (inheriting main_parser)
	sub_parser = script_parser()
	# Parse remaining arguments
	sub_args = sub_parser.parse_args(unknown_args)
	# Execute Script
	script_func(sub_args, toolkit_path=TOOLKIT_PATH)
else:
	# Pass no arguments if no parser exists
	script_func(toolkit_path=TOOLKIT_PATH)

if not is_interactive:
	sys.exit(0)