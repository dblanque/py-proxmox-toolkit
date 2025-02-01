from typing import TypedDict, Required, NotRequired, Literal

class ReplicationJobDict(TypedDict):
	comment: str
	target: str
	schedule: str
	source: str
