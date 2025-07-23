import os
from typing import TypedDict, NotRequired

DEBIAN_CODENAMES: dict[int, str] = {
	10: "buster",
	11: "bullseye",
	12: "bookworm",
	13: "trixie",
	14: "forky",
	15: "duke",
}

class OsReleaseDict(TypedDict):
	name: str
	id: str
	version_id: str
	pretty_name: str
	version: NotRequired[str]
	version_codename: NotRequired[str]
	home_url: NotRequired[str]
	support_url: NotRequired[str]
	bug_report_url: NotRequired[str]
	__extra_items__: str  # Allows unknown keys (all values assumed to be `str`)

def get_data() -> OsReleaseDict:
	"""Parse /etc/os-release file and return its contents as a dictionary.
	
	Returns:
		Dictionary of OS release information.
		
	Raises:
		FileNotFoundError: If /etc/os-release doesn't exist.
		PermissionError: If lacking permissions to read the file.
		RuntimeError: For other parsing errors.
	"""
	os_data = {}
	file_path = "/etc/os-release"
	
	if not os.path.exists(file_path):
		raise FileNotFoundError(f"{file_path} not found")
	
	try:
		with open(file_path, "r") as os_release_file:
			for line in os_release_file:
				line = line.strip()
				if not line or line.startswith("#"):
					continue
				
				if "=" in line:
					key, val = line.split("=", 1)
					key = key.strip().lower()
					val = val.strip().strip('"\'')
					os_data[key] = val

		# Optional fields (provide defaults)
		optional_defaults = {
			"version": "unknown",
			"version_codename": "unknown",
			"home_url": "",
			"support_url": "",
			"bug_report_url": "",
		}
		
		data = {**optional_defaults, **os_data} # Merge with defaults
		return OsReleaseDict(**data)

	except (PermissionError, FileNotFoundError):
		raise
	except Exception as e:
		raise RuntimeError(f"Failed to parse {file_path}") from e

def is_valid_version(
	os_release_info: OsReleaseDict,
	min_version: int = 12,
) -> bool:
	"""Checks if OS major version is greater than min_version.

	Returns:
		bool"""
	major_version = int(os_release_info.get("version_id", "-1").split(".")[0])
	if (
		os_release_info.get("id", "unknown") != "debian" or
		major_version < min_version
	):
		return False
	return True
