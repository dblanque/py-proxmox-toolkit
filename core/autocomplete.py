import os
import glob
from .utils.path import path_as_module
from argcomplete import autocomplete, FilesCompleter

EXCLUDED_FILES = [
	"main.py",
	"template.py",
]

class ToolkitCompleter:
	def __init__(self, toolkit_path):
		self.toolkit_path = toolkit_path
		self.scripts_dir = os.path.join(toolkit_path, "scripts")
		self.allowed_paths = self._get_allowed_paths()
		self.files_completer = FilesCompleter()

	def _get_allowed_paths(self):
		"""Precompute all valid script paths relative to toolkit directory"""
		paths = []
		for path in glob.glob(os.path.join(self.scripts_dir, "**", "*.py"), recursive=True):
			rel_path = os.path.relpath(path, self.toolkit_path)
			basename = os.path.basename(rel_path)
			if basename.startswith("__") or basename in EXCLUDED_FILES:
				continue
			paths.append(rel_path)
		return paths

	def _get_compline(self):
		return os.environ.get("COMP_LINE", "")

	def __call__(self, prefix, **kwargs):
		"""Handle two-stage completion: filename then script arguments"""
		# Stage 1: Complete filenames
		if not self._is_script_selected():
			return self._complete_filename(prefix)
		
		# Stage 2: Complete script arguments
		return self._complete_sub_parser_args()

	def _is_script_selected(self):
		"""Check if user has already selected a script"""
		comp_line = self._get_compline()
		return len(comp_line.split()) > 2  # [prog, filename, ...]

	def _complete_filename(self, prefix, **kwargs):
		"""Directory-aware filename completion"""
		# Convert toolkit-relative path to filesystem path
		abs_prefix = os.path.join(self.toolkit_path, prefix)
		
		# Get raw filesystem completions
		completions = self.files_completer(abs_prefix, **kwargs)
		
		# Convert to toolkit-relative paths and filter
		valid = []
		for c in completions:
			if not os.path.exists(c):
				continue
			rel_path = os.path.relpath(c, self.toolkit_path)
			# Filter allowed paths
			if any(p.startswith(rel_path) for p in self.allowed_paths):
				# Add trailing slash for directories
				if os.path.isdir(c):
					valid.append(f"{rel_path}/")
				elif rel_path in self.allowed_paths:
					valid.append(rel_path)
		return valid

	def _complete_sub_parser_args(self):
		"""Delegate completion to sub-script's parser"""
		try:
			script_name = self._get_compline().split()[1]
			_module = __import__(
				path_as_module(script_name),
				fromlist=["argparser"]
			)
			_sub_parser = _module.argparser()
			return autocomplete(_sub_parser)
		except Exception:
			return [ "Auto-complete Exception." ]
