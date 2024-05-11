import settings
import asyncio
import gelbooru
import discord
import logging
from discord.ext import commands
from typing import Optional, Literal


# intents setup
intents = discord.Intents.default()
intents.message_content = True

# bot setup
bot = commands.Bot(command_prefix='\\', intents=intents)


# commands block:
# ---

# sync command (wait like 1 min to work, refresh discord on PC - Ctrl+R)
@bot.tree.command(name='sync', description='sync bot command tree')
async def sync_tree(interaction: discord.Interaction) -> None:
    _ = await bot.tree.sync()
    print('syncing:', *_)
    await interaction.response.send_message('syncing bot command tree', ephemeral=True)


@bot.tree.command(name='help', description='help instructions')
async def help_instructions(
    interaction: discord.Interaction,
    lang: Optional[Literal['en', 'ru']]
) -> None:
    if lang is not None:
        if lang == 'ru':
            await interaction.response.send_message(settings.HELP_RESPONSE_RU, ephemeral=True)
            return
    await interaction.response.send_message(settings.HELP_RESPONSE_EN, ephemeral=True)


@bot.tree.command(name='search', description='search by tags')
@discord.app_commands.describe( 
    tags='tags to search from (write with a space)',
    offset='number of searched post, only from 1 to 20000',
    random='randomizes search',
)
async def search_command(
    interaction: discord.Interaction,
    tags: Optional[str],
    offset: Optional[int],
    random: Optional[Literal['✅']],
) -> None:
    try:
        await interaction.response.defer()
    except Exception:
        asyncio.sleep(0.1)
        await interaction.response.defer()

    if offset is not None:
        if not 0 <= offset <= 20000:
            offset = 0
    else: offset = 0

    if random: random = True
    else: random = False

    if isinstance(interaction.channel, discord.channel.DMChannel):
        nsfw = False
    else:
        nsfw: bool = interaction.channel.nsfw
    
    await search_content(interaction, tags=tags, pid=offset, random=random, nsfw=nsfw,)
    
# ---

async def search_content(
    interaction: discord.Interaction,
    *,
    tags: Optional[str],
    pid: int = 0,
    random: bool = False,
    nsfw: bool = False,
) -> None:
    try:
        content: dict[str, ] = await gelbooru.connect_to_gelbooru(
            api_key=settings.API_KEY,
            user_id=settings.USER_ID,
            tags=tags,
            nsfw=nsfw,
            random=random,
            pid=pid,
        )
        
    except gelbooru.NoPostsFound:
        await interaction.followup.send('no posts found, try different tags', ephemeral=True)
        return
    
    except gelbooru.NotNSFWchannel:
        await interaction.followup.send("tag 'rating' available only on nsfw channels", ephemeral=True)
        return
    
    except ConnectionError as _:
        await interaction.followup.send('connection error', ephemeral=True)
        logging.warning(_)
        return

    except Exception as e:
        await interaction.followup.send('error', ephemeral=True)
        logging.critical(e.__context__)
        return

    post_url = f'https://gelbooru.com/index.php?page=post&s=view&id={content['id']}'
    
    """
    nextButton = discord.ui.Button(label='next', style=discord.ButtonStyle.green)
    randomButton = discord.ui.Button(label='random', style=discord.ButtonStyle.blurple)
    """
    urlButton = discord.ui.Button(label='url', url=post_url)
    
    Buttons = discord.ui.View()

    Buttons.add_item(urlButton)

    
    await interaction.followup.send(content['content_url'], view=Buttons)
    return

# bot startup terminal output
@bot.event
async def on_ready() -> None:
    color = '\033[93m'
    end = '\033[0m'
    print(f'{color}{bot.user.name}{end} bot is now running!')

# main entry point
def main() -> None:
    bot.run(token=settings.TOKEN)


if __name__ == '__main__':
    main()
