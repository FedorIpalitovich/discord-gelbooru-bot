import asyncio
import os
import discord
from discord.ext import commands


# bot intents
intents = discord.Intents.default()
intents.message_content = True

# bot
bot = commands.Bot(command_prefix='!', intents=intents)

# default logging
discord.utils.setup_logging()

# bot startup terminal output
@bot.event
async def on_ready() -> None:
    color = '\033[93m'
    end = '\033[0m'
    print(f'{color}{bot.user.name}{end} bot is now running.')

# loading cogs via load_extension
async def load_cogs() -> None:
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py') and filename != '__init__.py':
            await bot.load_extension(f'cogs.{filename[:-3]}')

# main entry point
async def main() -> None:
    from settings import DISCORD_TOKEN
    await load_cogs()
    await bot.start(token=DISCORD_TOKEN, reconnect=True)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
