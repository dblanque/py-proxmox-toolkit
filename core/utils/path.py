import os
import glob

EXCLUDED_FILES = [
	"main.py",
	"template.py",
]


def get_all_allowed_paths(project_root: str, subdirectory: str = None):
	if not os.path.isdir(project_root):
		raise ValueError(project_root, "Must be a path.")
	if subdirectory:
		if not os.path.isdir(subdirectory):
			raise ValueError(subdirectory, "Must be a path.")
	"""Precompute all valid script paths relative to toolkit directory"""
	paths = []
	for _path in glob.glob(os.path.join(subdirectory, "**", "*.py"), recursive=True):
		_rel_path = os.path.relpath(_path, project_root)
		basename = os.path.basename(_rel_path)
		if basename.startswith("__") or basename in EXCLUDED_FILES:
			continue
		paths.append(_rel_path)
	return paths


def path_as_module(_path):
	return os.path.splitext(_path)[0].replace("/", ".")
