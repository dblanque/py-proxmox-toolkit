import os
import argparse
from ipaddress import (
	IPv4Interface,
	IPv4Address, 
	IPv4Network,
)

dir_path = os.path.dirname(os.path.realpath(__file__))
parser = argparse.ArgumentParser(
	prog='subnetprov.py',
	description='This script allows for automatic subnet provisioning'
	)
parser.add_argument('-f', '--filename', 
			help="What file's ABSOLUTE path to save subnets to | DEFAULT: ./subnetlist.csv",
			required=True)
parser.add_argument('-s', '--subnet', required=True)
parser.add_argument('-n', '--name', required=False)
parser.add_argument('-v', '--verbose',
					action='store_true')
args = parser.parse_args()

file_exists = os.path.isfile(args.filename)
file_empty = os.stat(args.filename).st_size == 0

if not file_exists:
	raise Exception('File does not exist.')

header_list = {
	"subnet": True,
	"mask": True,
	"name": False
}

class FileHeaders:
	def __init__(self):
		self.headers = {}
		for h in header_list:
			setattr(self, h, None)

file_headers = FileHeaders

def ip_to_cidr(ip):
	iface = IPv4Interface(ip).network
	return IPv4Network(iface)

def main():
	target = dict()
	target['name'] = args.name
	target['subnet'] = ip_to_cidr(args.subnet)
	target['hosts'] = list(target['subnet'].hosts())
	target['host_count'] = len(target['hosts'])

	with open(args.filename, newline='', mode='') as csvfile:
		rows = [row.split()[0] for row in csvfile]
		header_row = rows.pop(0)
		header_row = header_row.split(',')
		network = list()

		for h in header_list:
			h_index = header_row.index(h)
			if h_index >= 0:
				setattr(file_headers, h, h_index)
			elif header_list[h]:
				raise Exception(f"Required Header ({h}) has no index in file header.")

		for r in range(len(rows)):
			current_row = rows[r].split(',')
			net = dict()
			net['name'] = current_row[file_headers.name]
			net['subnet'] = IPv4Network(current_row[file_headers.subnet])
			net_hosts = list(net['subnet'].hosts()) # Do not append
			net['host_count'] = len(net_hosts)
			network.append(net)

		for n in network:
			if target['subnet'].overlaps(n['subnet']):
				print(f"{target['subnet']} overlaps with pre-existing network {n['subnet']}")
				next_net_ip = target['hosts'][0] + target['host_count'] + 1
				target['subnet'] = IPv4Network(str(next_net_ip) + '/' + str(target['subnet'].netmask))
				target['hosts'] = list(target['subnet'].hosts())

			print(f"Use the {next_net_ip} subnet.")

# TODO - Make the script write a new CSV file with the properly sorted subnets.

if __name__ == "__main__":
	try:
		main()
	except:
		raise