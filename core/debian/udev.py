import subprocess

def get_inet_udev_info(device: str):
	"""Fetches dictionary or specific value within UDEV Information for a
	Linux Network Interface Device.

	:param str device: The Network Device to query information for.
	:param str field: If specified only this field will be returned.
	"""
	data = {}
	sp = subprocess.Popen(f"udevadm info /sys/class/net/{device}".split(),
		stdout=subprocess.PIPE, 
		stderr=subprocess.PIPE,
	)
	out, err = sp.communicate()
	returncode = sp.returncode
	if returncode == 0:
		out = out.decode("utf-8").split("\n")
		for l in out:
			if len(l.strip()) == 0: continue
			udev_field, l_entry = l.split(": ", 1)
			if "=" in l_entry:
				l_field, l_value = l_entry.split("=", 1)
			else:
				l_field = None
				l_value = l_entry

			if l_field:
				data[l_field] = l_value
			else: data[udev_field] = l_value
	return data