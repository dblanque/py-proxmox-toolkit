if __name__ == "__main__":
	raise Exception(
		"This python script cannot be executed individually, please use main.py"
	)

from .utils.path import get_all_allowed_paths, EXCLUDED_FILES
import importlib.util
import os


class PathCompleter(object):
	def __init__(self, toolkit_path, scripts_subdir="scripts", **kwargs):
		self.toolkit_path = toolkit_path
		self.scripts_subdir = scripts_subdir
		self.choices = get_all_allowed_paths(
			project_root=toolkit_path, subdirectory=scripts_subdir
		)

	def __call__(self, **kwargs):
		return self.choices


class SingleLevelPathCompleter(object):
	def __init__(self, toolkit_path, scripts_subdir="scripts", **kwargs):
		self.toolkit_path = toolkit_path
		self.scripts_subdir = scripts_subdir
		self.choices = []

	def __add_slash_if_dir__(self, _path: str) -> str:
		if os.path.isdir(_path):
			return _path + "/"
		return _path

	def __is_valid_file__(self, file: str):
		file = os.path.basename(file)
		if file.startswith("__"):
			return False
		if file in EXCLUDED_FILES:
			return False
		return True

	def __call__(self, **kwargs):
		prefix: str = kwargs.pop("prefix")
		if len(prefix) == 0 or not "/" in prefix:
			for file in os.listdir(
				os.path.join(self.toolkit_path, self.scripts_subdir)
			):
				file_relpath = os.path.join(self.scripts_subdir, file)
				file_relpath = self.__add_slash_if_dir__(file_relpath)
				if self.__is_valid_file__(file):
					self.choices.append(file_relpath)
		else:
			current_directory = prefix.split("/")
			subdir = ""
			if len(current_directory) != 1:
				current_directory = current_directory[0:-1]

			for i, v in enumerate(current_directory):
				subdir = os.path.join(subdir, current_directory[i])
			current_directory = os.path.join(self.toolkit_path, subdir)

			if os.path.isdir(current_directory):
				for file in os.listdir(current_directory):
					file_relpath = os.path.join(subdir, file)
					file_relpath = self.__add_slash_if_dir__(file_relpath)
					if self.__is_valid_file__(file):
						self.choices.append(file_relpath)
		return self.choices


def argcomplete_exists() -> bool:
	argcomplete_spec = importlib.util.find_spec("argcomplete")
	return argcomplete_spec is not None
