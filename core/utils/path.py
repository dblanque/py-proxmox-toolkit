from os import path

def path_as_module(_path):
	return path.splitext(_path)[0].replace("/", ".")