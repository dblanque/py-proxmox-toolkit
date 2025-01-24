import subprocess, logging
from core.parser import make_parser, ArgumentParser
logger = logging.getLogger(__name__)

def argparser(**kwargs) -> ArgumentParser:
	parser = make_parser(
		prog='Interface Status Fetcher',
		description='Gets interface status with ip binary',
		**kwargs
	)
	parser.add_argument('interface')
	return parser

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
			raise ValueError(f"Interface {iface_name} does not exist")
	for l in output:
		if "state" in l:
			iface_status_line = l.split(" ")
	iface_status = iface_status_line[iface_status_line.index("state") + 1].strip()
	return iface_status

def main(argv_a: ArgumentParser = None):
	if not argv_a:
		argv_a = argparser().parse_args()
	try:
		print( get_iface_status(argv_a.interface) )
	except:
		raise

if __name__ == "__main__":
	main()