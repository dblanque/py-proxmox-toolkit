def get_data() -> dict:
	os_data = dict()
	try:
		for line in open("/etc/os-release", "r"):
			line_data = line.strip().split("=")
			key = line_data[0]
			val = line_data[1].strip('"')
			os_data[key.lower()] = val
		return os_data
	except: raise
