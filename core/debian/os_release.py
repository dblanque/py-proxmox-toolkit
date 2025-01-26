def get_data() -> dict:
	os_data = {}
	try:
		with open("/etc/os-release", "r") as os_release_file:
			for line in os_release_file:
				line_data = line.strip().split("=")
				key = line_data[0]
				val = line_data[1].strip('"')
				os_data[key.lower()] = val
			return os_data
	except:
		raise

def is_valid_version(os_release_info, min_version=12) -> bool:
	major_version = int(os_release_info["version_id"].split(".")[0])
	if os_release_info["id"] != "debian" or major_version < min_version:
		return False
	return True
