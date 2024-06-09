import os
from dotenv import load_dotenv
from typing import Final

load_dotenv()
DISCORD_TOKEN: Final[str] = os.getenv('DISCORD_TOKEN')
GELBOORU_API_KEY: Final[str] = os.getenv('GELBOORU_API_KEY')
GELBOORU_USER_ID: Final[str] = os.getenv('GELBOORU_USER_ID')

