def validate_port(value: int, raise_exception=False):
	try:
		port = int(value)
		if 1 <= port <= 65535:
			return True
	except ValueError:
		if not raise_exception:
			return False
		else:
			raise
	return False
