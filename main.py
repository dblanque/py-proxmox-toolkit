#!/usr/bin/python3
import argparse, sys
parser = argparse.ArgumentParser(
	prog='Main Program file for Python Proxmox Toolkit Execution',
	description='Use this program to execute sub-scripts from the toolkit'
)
parser.add_argument('filename')
args, unknown_args = parser.parse_known_args()
script_func = getattr(__import__(args.filename, fromlist=["main"]), "main")
try: script_func()
except: raise
sys.exit(0)