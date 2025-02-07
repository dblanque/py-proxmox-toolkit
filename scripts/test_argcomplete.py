#!/usr/bin/python3
import os
from core.parser import ArgumentParser, make_parser
from argcomplete.completers import SuppressCompleter

def argparser(**kwargs) -> ArgumentParser:
	parser = make_parser(
		prog="Auto-complete Testing Script",
		description="This program is used to test argcomplete.",
		**kwargs
	)
	parser.add_argument('-f', '--fruits', choices=["a","b"]).completer = SuppressCompleter()
	return parser

def main(argv_a, **kwargs):
	print(argv_a)
	print(kwargs)