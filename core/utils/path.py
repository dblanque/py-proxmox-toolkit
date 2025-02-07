import os
import glob

EXCLUDED_FILES = [
	"main.py",
	"template.py",
]

def get_allowed_paths(toolkit_path: str, subdirectory: str = None):
	if not os.path.isdir(toolkit_path):
		raise ValueError(toolkit_path, "Must be a path.")
	if subdirectory:
		if not os.path.isdir(subdirectory):
			raise ValueError(subdirectory, "Must be a path.")
	"""Precompute all valid script paths relative to toolkit directory"""
	paths = []
	for path in glob.glob(os.path.join(subdirectory, "**", "*.py"), recursive=True):
		rel_path = os.path.relpath(path, toolkit_path)
		basename = os.path.basename(rel_path)
		if basename.startswith("__") or basename in EXCLUDED_FILES:
			continue
		paths.append(rel_path)
	return paths

def path_as_module(_path):
	return os.path.splitext(_path)[0].replace("/", ".")