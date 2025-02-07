#!/usr/bin/python3
# PYTHON_ARGCOMPLETE_OK
from argparse import ArgumentParser
import sys
import os
from core.utils.path import path_as_module
from core.parser import make_parser
from core.utils.shell import is_completion_context
from core.autocomplete import argcomplete_exists

# Import and use argcomplete if available
use_argcomplete = argcomplete_exists() and is_completion_context()
if use_argcomplete:
	from argcomplete import autocomplete

TOOLKIT_PATH=os.path.dirname(__file__)
PARSER_ARGS = {
	"use_argcomplete": use_argcomplete,
	"toolkit_path": TOOLKIT_PATH
}
python_interactive = bool(getattr(sys, 'ps1', sys.flags.interactive))
if python_interactive:
	print("Interactive mode enabled.")

if len(sys.argv) <= 1 and not use_argcomplete:
	print("Please enter a valid script path.")
	sys.exit(1)

if use_argcomplete:
	COMP_LINE = os.environ.get("COMP_LINE").split()
	if len(COMP_LINE) >= 2:
		filename = COMP_LINE[1]
	else:
		filename = ""
else:
	filename = sys.argv[1]

if filename.endswith(".py") or "/" in filename:
	parsed_filename = path_as_module(filename)
else:
	parsed_filename = filename

def _autocomplete_parser():
	parser = make_parser(add_help=False, **PARSER_ARGS)
	# Enable argcomplete
	return autocomplete(parser)

if len(filename) == 0 and use_argcomplete:
	_autocomplete_parser()

try:
	# Import sub-script module
	module = __import__(parsed_filename, fromlist=["main", "argparser"])
	script_func = getattr(module, "main")
except ImportError:
	if use_argcomplete:
		_autocomplete_parser()
	sys.exit(f"Error: Sub-script '{parsed_filename}' not found.")
except AttributeError:
	sys.exit(f"Error: Sub-script '{parsed_filename}' has no 'main' function.")

# Check if sub-script provides an argparser
script_parser = getattr(module, "argparser", None)
if script_parser:
	# Initialize sub-script's parser (inheriting main_parser)
	sub_parser: ArgumentParser = script_parser(**PARSER_ARGS)
	if use_argcomplete:
		autocomplete(sub_parser)
	# Parse remaining arguments
	sub_args = sub_parser.parse_args()
	# Execute Script
	script_func(sub_args, toolkit_path=TOOLKIT_PATH)
else:
	# Pass no arguments if no parser exists
	script_func(toolkit_path=TOOLKIT_PATH)

if not python_interactive:
	sys.exit(0)