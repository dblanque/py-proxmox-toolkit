import sys, os
from ..exceptions.base import DependencyMissing
import importlib.util

FILE_PATH = os.path.dirname(os.path.realpath(__file__))
ROOT_DIR = os.path.join(FILE_PATH, os.pardir, os.pardir)
# Check if required dependencies exist
discord_webhook_spec = importlib.util.find_spec("discord_webhook")
discord_webhook_found = discord_webhook_spec is not None
if not discord_webhook_found:
	print("Please install the discord-webhook dependency.")
	print(f"source {ROOT_DIR}/bin/activate && pip install discord-webhook")
	raise DependencyMissing()

from typing import TypedDict
from requests import Response
from ..validators.url import url_validator
from discord_webhook import DiscordWebhook, DiscordEmbed
import logging

logger = logging.getLogger(__name__)

class DiscordFieldsDict(TypedDict):
	name: str
	value: str

class DiscordAuthorDict(TypedDict):
	name: str
	url: str
	icon_url: str

def validate_discord_settings(discord_webhook_url):
	if not url_validator(discord_webhook_url):
		try:
			if len(discord_webhook_url) < 1:
				v = "Zero Length URL"
			else: v = str(discord_webhook_url)
		except: pass
		raise ValueError(f"Invalid Discord Webhook URL ({v}).")

def emit_discord(
		discord_webhook_url,
		discord_webhook_username,
		msg_title,
		msg_desc,
		msg_fields: list[DiscordFieldsDict] = None,
		msg_author: DiscordAuthorDict = None,
		msg_footer: str = None,
		msg_color: str = "03b2f8"
	) -> Response:
	"""
	msg_fields may contain dictionaries with the following values:
	* name: str
	* value: str

	msg_author may contain dictionaries with the following values:
	* name: str
	* url: str
	* icon_url: str
	"""
	if not discord_webhook_url:
		logger.warning(f"discord_webhook_url is not configured ({discord_webhook_url}).")
		return None
	webhook = DiscordWebhook(url=discord_webhook_url, username=discord_webhook_username)

	embed = DiscordEmbed(title=msg_title, description=msg_desc, color=msg_color)
	if msg_author:
		if all(k in msg_author for k in ("name","url","icon_url")):
			embed.set_author(name=msg_author["name"], url=msg_author["url"], icon_url=msg_author["icon_url"])
	if msg_footer:
		embed.set_footer(text=msg_footer)
	embed.set_timestamp()
	if msg_fields:
		for f in msg_fields:
			if all(k in f for k in ("name","value")):
				if "inline" in f: f_inline = f["inline"]
				else: f_inline = True
				embed.add_embed_field(name=f["name"], value=f["value"], inline=f_inline)

	webhook.add_embed(embed)
	return webhook.execute()