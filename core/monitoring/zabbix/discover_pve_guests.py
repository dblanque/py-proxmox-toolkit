#!/usr/bin/python3
import subprocess, sys, argparse, os, socket, json

GUEST_STOPPED=0
GUEST_RUNNING=1
GUEST_NOT_ON_HOST=2
GUEST_CONFIG_MISSING=3

parser = argparse.ArgumentParser(
	prog='discover_pve_guests.py',
	description='This script allows for local automatic guest discovery by Zabbix'
	)
parser.add_argument('-s', '--status', required=False, nargs=2, help="Returns Guest Status [GUEST_ID] [GUEST_TYPE]")
parser.add_argument('-d', '--discovery', required=False, action="store_true")
args = parser.parse_args()

if not args.discovery and not args.status:
	parser.error("No arguments entered, please enter a valid argument. (Use --h|--help for more information)")

def discover_guests(command):
	if command != "qm" and command != "pct":
		raise ValueError("Valid get_status commands: qm | pct")
	if command == "qm":
		guest_type = "VM"
	else:
		guest_type = "CT"
	args = [f"/usr/sbin/{command}", "list"]
	proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=sys.stderr)
	proc_out_parsed = []
	for i, l_out in enumerate(proc.stdout):
		ln = l_out.decode('utf-8'.strip())
		ln = ln.split()
		if i == 0:
			if (command == "qm" and len(ln) != 6) or (command == "pct" and len(ln) != 4):
				raise Exception(f"Column length has changed for command {command}")
			cols = [c.lower() for c in ln]
			continue
		if ln and len(ln) > 0: proc_out_parsed.append(ln)

	result = []
	for guest in proc_out_parsed:
		if "lock" in cols and len(guest) < len(cols):
			cols.remove("lock")
		result.append({
			"{#GUEST_ID}": guest[cols.index("vmid")], 
			"{#GUEST_NAME}": guest[cols.index("name")], 
			# "{#GUEST_STATUS}": guest[cols.index("status")],
			"{#GUEST_TYPE}": guest_type
		})
	return result

def get_status(guest_id: int, guest_type: str):
	guest_type = guest_type.lower()
	if guest_type == "vm":
		command = "qm"
	elif guest_type == "ct":
		command = "pct"
	else: raise ValueError(f"Invalid Guest Type for Guest {guest_id}")
	args = [f"/usr/sbin/{command}", "status", guest_id]
	proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=sys.stderr)
	out, err = proc.communicate()
	return out.decode('utf-8'.strip()).split(": ")[-1].rstrip('\n').lstrip()

def main():
	if args.status and type(args.status) == list:
		guest_id = args.status[0]
		guest_type = args.status[1].lower()
		subpath = "qemu-server"
		if guest_type == "ct": subpath = "lxc"
		try: hostname = socket.gethostname()
		except: raise Exception("Could not get Hostname")
		if not os.path.exists(f"/etc/pve/nodes/{hostname}/{subpath}/{guest_id}.conf"):
			for pve_host in os.listdir("/etc/pve/nodes/"):
				if os.path.exists(f"/etc/pve/nodes/{pve_host}/{subpath}/{guest_id}.conf"):
					print(GUEST_NOT_ON_HOST)
					sys.exit()
			print(GUEST_CONFIG_MISSING)
			sys.exit()
		status = get_status(guest_id, guest_type)
		if status == "running": print(GUEST_RUNNING)
		else: print(GUEST_STOPPED)
		sys.exit()
	statuses = []
	statuses.extend(discover_guests("qm"))
	statuses.extend(discover_guests("pct"))
	print(json.dumps({"data": statuses}))

if __name__ == "__main__":
	main()
