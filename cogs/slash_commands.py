import discord
from discord.ext import commands
import utils
from typing import Optional, Literal


__all__ = None

class SlashCommands(commands.Cog):
    """cog for bot slash commands
    """
    
    def __init__(self, bot: commands.Bot) -> None:
        self.bot: commands.Bot = bot
    
    @discord.app_commands.command(name='help', description='help instructions')
    async def help_instructions(
        self,
        interaction: discord.Interaction,
        lang: Optional[Literal['en', 'ru']]
    ) -> None:
        if lang is not None:
            if lang == 'ru':
                await interaction.response.send_message('команда /search работает только на nsfw каналах', ephemeral=True,)
            elif lang == 'en':
                await interaction.response.send_message('command /search works only on nsfw channels', ephemeral=True,)
    
    # bot primary command
    @discord.app_commands.command(name='search', description='search for posts by tags', nsfw=True)
    @discord.app_commands.describe( 
        tags='tags to search from (write with a space)',
        pid='offset of searched post (from 0 to 20000)',
        random='randomizes searching',)
    async def search_command(
        self,
        interaction: discord.Interaction,
        tags: Optional[str] = '*',
        pid: Optional[int] = 0,
        random: Optional[Literal['✅']] = None
    ) -> None:
        # defer response to await http request
        try:
            await interaction.response.defer()
        except discord.errors.NotFound:
            raise ('failed to defer an interaction')
        
        if random is None: random = False
        else: random = True
        if not (0 <= pid <= 20000):
            pid = 0
        
        response = await utils.ds_request(interaction, tags=tags, pid=pid, random=random)
        if response is None:
            return
        
        content: dict[str, ] = response['content']
        post_url: str = f'https://gelbooru.com/index.php?page=post&s=view&id={content['id']}'
        Buttons = utils.ButtonsView(post_url)
        post_embed: discord.Embed = await utils.construct_embed(
            response['embed_data'], content['file_url'], response['is_video'])
        
        if response['is_video']:
            await interaction.channel.send(content['file_url'])
        
        await interaction.followup.send(embed=post_embed, view=Buttons)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(SlashCommands(bot))
