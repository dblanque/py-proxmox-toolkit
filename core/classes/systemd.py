from typing import Literal
from sys import getdefaultencoding
import subprocess

UNIT_STATUSES = Literal[
	"UNKNOWN",
	"INACTIVE",
	"ENABLED",
	"DISABLED",
	"STATIC",
	"MASKED",
	"ALIAS",
	"LINKED",
	"ACTIVE_RUNNING",
	"ACTIVE_WAITING",
	"ACTIVE_EXITED",
]

UNIT_TYPES = Literal[
	"service",
	"swap",
	"socket",
	"target",
	"device",
	"automount",
	"path",
	"slice",
	"scope",
]

UNIT_COMMANDS = Literal[
	"start",
	"stop",
	"restart",
	"enable",
	"disable",
	"list-unit-files",
	"list-units",
]

UNIT_STATE_COMMANDS = Literal[
	"is-active",
	"is-failed",
	"is-enabled"
]

class Unit():
	def __init__(self, name: str, service_type: UNIT_TYPES, **kwargs):
		self.name = name
		self.status: UNIT_STATUSES = "UNKNOWN"
		if not service_type in UNIT_TYPES:
			raise ValueError(f"{service_type} is not in {UNIT_TYPES}")
		self.service_type = service_type

	def exists(self):
		return self._command("list-unit-files")

	def is_active(self):
		return self._stat_command("is-active") == "active"

	def is_failed(self):
		return self._stat_command("is-failed") == "failed"

	def is_enabled(self) -> bool:
		return self._stat_command("is-enabled") == "enabled"

	def is_disabled(self) -> bool:
		return not self.is_enabled()

	def _stat_command(self, action: UNIT_STATE_COMMANDS, extra_args=None) -> str:
		if not action in UNIT_STATE_COMMANDS:
			raise ValueError(f"{action} not in {UNIT_STATE_COMMANDS}")
		cmd = f"systemctl {action}"
		if extra_args:
			cmd = cmd + " " + " ".join(extra_args)
		cmd = f"{cmd} {self.name}.{self.service_type}".split()
		return subprocess.check_output(args=cmd).decode(getdefaultencoding()).strip()

	def _command(self, action: UNIT_COMMANDS, extra_args=None) -> int:
		if not action in UNIT_COMMANDS:
			raise ValueError(f"{action} not in {UNIT_COMMANDS}")
		cmd = f"systemctl {action}"
		if extra_args:
			cmd = cmd + " " + " ".join(extra_args)
		cmd = f"{cmd} {self.name}.{self.service_type}".split()
		return subprocess.call(args=cmd)

	def start(self) -> int:
		return self._command("start")

	def restart(self) -> int:
		return self._command("restart")

	def stop(self) -> int:
		return self._command("stop")

	def enable(self) -> int:
		return self._command("enable")

	def disable(self) -> int:
		return self._command("disable")