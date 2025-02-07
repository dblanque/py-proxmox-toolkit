#!/usr/bin/python3
if __name__ == "__main__":
	raise Exception("This python script cannot be executed individually, please use main.py")

from core.parser import ArgumentParser, make_parser

def argparser(**kwargs) -> ArgumentParser:
	parser = make_parser(
		prog="Auto-complete Testing Script",
		description="This program is used to test argcomplete.",
		**kwargs
	)
	parser.add_argument('-f', '--fruits', choices=["apple","banana"])
	return parser

def main(argv_a, **kwargs):
	print(argv_a)
	print(kwargs)
