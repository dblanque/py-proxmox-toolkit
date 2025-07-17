from typing import TypedDict


class ReplicationJobDict(TypedDict):
	comment: str
	target: str
	schedule: str
	source: str
