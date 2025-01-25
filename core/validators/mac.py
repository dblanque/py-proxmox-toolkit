import re

def mac_address_validator(value) -> bool:
	pattern = r"^([0-9a-fA-F][0-9a-fA-F]:){5}([0-9a-fA-F][0-9a-fA-F])$"
	try:
		if re.match(pattern, str(value)):
			return True
	except Exception as e:
		print(value)
		print(type(value))
		raise e
	return False
