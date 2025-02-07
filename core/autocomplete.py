if __name__ == "__main__":
	raise Exception("This python script cannot be executed individually, please use main.py")

from .utils.path import get_allowed_paths
import importlib.util

class PathCompleter(object):
	def __init__(self, toolkit_path, scripts_subdir="scripts", **kwargs):
		self.choices = get_allowed_paths(
			project_root=toolkit_path,
			subdirectory=scripts_subdir
		)
	def __call__(self, **kwargs):
		return self.choices

def argcomplete_exists() -> bool:
	argcomplete_spec = importlib.util.find_spec("argcomplete")
	return argcomplete_spec is not None