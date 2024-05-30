import subprocess, logging, argparse
logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser(
	prog='Interface Status Fetcher',
	description='Gets interface status with ip binary')
parser.add_argument('interface')
args = parser.parse_args()

def get_iface_status(iface_name):
	IP_ARGS=[
		"/usr/sbin/ip",
		"link",
		"show",
		iface_name
	]
	with subprocess.Popen(IP_ARGS, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as ip_proc:
		output: list[str] = list()
		errors: list[str] = list()
		for l_out in ip_proc.stdout:
			output.append(l_out.decode('utf-8').strip())
		for l_err in ip_proc.stderr:
			errors.append(l_err.decode('utf-8').strip())
	iface_status_line = None
	for l in errors:
		if "does not exist" in l:
			raise ValueError(f"Interface {args.interface} does not exist")
	for l in output:
		if "state" in l:
			iface_status_line = l.split(" ")
	iface_status = iface_status_line[iface_status_line.index("state") + 1].strip()
	return iface_status

def main():
	try:
		bridge_status = get_iface_status(args.interface)
		print(bridge_status)
	except:
		raise

if __name__ == "__main__":
	main()