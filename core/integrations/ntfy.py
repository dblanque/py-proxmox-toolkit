import requests, logging
# TODO - replace requests with urllib3 or httplib2
from ..validators.url import url_validator
logger = logging.getLogger()

priority: int
message: str
NTFY_PRIORITY_CHOICES=[
	"max", "urgent",
	"high",
	"default",
	"low",
	"min"
]

def validate_ntfy_settings(ntfy_server, ntfy_token):
	if not url_validator(ntfy_server):
		try:
			if len(ntfy_server) < 1:
				v = "Zero Length URL"
			else: v = str(ntfy_server)
		except: pass
		raise ValueError(f"Invalid NTFY Server URL ({v}).")
	if not ntfy_token or len(ntfy_token) < 1:
		raise ValueError("Invalid NTFY Token (Zero Length or None).")

def priority_valid_int(priority):
	try: priority = int(priority)
	except: return False
	if priority < 0 or priority > 5: return priority
	return False

# Check NTFY Documentation for more info
# src: https://docs.ntfy.sh/publish/
def emit_ntfy(ntfy_server, ntfy_token, message: str, title: str=None, priority="default"):
	if not str(priority) in NTFY_PRIORITY_CHOICES and not priority_valid_int(priority=priority):
		raise ValueError("Invalid Priority Tag on NTFY Emit.", priority)

	# Set headers
	r_headers = dict()
	if priority_valid_int(priority=priority):
		r_headers["X-Priority"] = int(priority)
	else:
		r_headers["Priority"] = str(priority)
	if title: r_headers["Title"] = title
	r_headers["Authorization"] = f"Bearer {ntfy_token}"

	return requests.post(
		url=str(ntfy_server),
		headers=r_headers,
		data=str(message).encode("utf-8")
	)
