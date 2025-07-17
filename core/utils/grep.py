from os import walk, path
from re import Pattern, compile


def grep_r(pattern: Pattern, dir, return_files=False):
	if not isinstance(pattern, Pattern):
		compiled_pattern = compile(pattern)
	else:
		compiled_pattern = pattern
	for parent, dirs, files in walk(dir):
		for base_name in files:
			filename = path.join(parent, base_name)
			if path.isfile(filename):
				with open(filename) as f:
					for line in f:
						if compiled_pattern.search(line):
							if return_files:
								yield filename
							else:
								yield line
