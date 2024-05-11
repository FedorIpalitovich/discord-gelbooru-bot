import os
from dotenv import load_dotenv
from typing import Final

load_dotenv()
TOKEN: Final[str] = os.getenv('DISCORD_TOKEN')
API_KEY: Final[str] = os.getenv('GELBOORU_API_KEY')
USER_ID: Final[str] = os.getenv('GELBOORU_USER_ID')

HELP_RESPONSE_EN: Final[str] = """en"""
HELP_RESPONSE_RU: Final[str] = """ru"""
