import discord
from aiohttp.client_exceptions import ClientConnectionError
from discord.ext import commands
from typing import Optional, Literal
from bot_response import GelbooruResponse, NoPostsFound


__all__ = ('SlashCommands', 'ButtonsCallback', 'ButtonsView')

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
    
    @discord.app_commands.command(name='recent', description='get popular recent tags')
    async def recent(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()
        # //get tags
        await interaction.followup.send('tags')
    
    # bot primary command
    @discord.app_commands.command(name='search', description='search for posts by tags', nsfw=True)
    @discord.app_commands.describe( 
        tags='tags to search from (write with a space)',
        pid='offset of searched post (from 0 to 20000)',
        random='randomizes searching',
        ephemeral='makes post ephemeral',)
    async def search_command(
        self,
        interaction: discord.Interaction,
        tags: Optional[str] = '*',
        pid: Optional[int] = 0,
        random: Optional[Literal['✅']] = None,
        ephemeral: Optional[Literal['✅']] = None
    ) -> None:
        if ephemeral is None:
            ephemeral: bool = False
        else:
            ephemeral: bool = True
        # defer response to await http request
        try:
            await interaction.response.defer(ephemeral=ephemeral)
        except discord.errors.NotFound:
            return
        if random is None:
            random: bool = False
        else:
            random: bool = True
        if not (0 <= pid <= 20000):
            pid = 0
        
        content: dict[str, ] = await self.request(interaction, tags=tags, pid=pid, random=random)
        post_url: str = f'https://gelbooru.com/index.php?page=post&s=view&id={content['id']}'

        data = {'tags': content['tags'], 'pid': content['pid']}
        post_embed: discord.Embed = await self.construct_embed(data, content['file_url'], content['is_video'])
        Buttons = ButtonsView(post_url)
        
        if content['is_video']:
            await interaction.channel.send(content['file_url'])
        
        await interaction.followup.send(embed=post_embed, view=Buttons)
    
    @staticmethod
    async def request(
        interaction: discord.Interaction,
        *,
        tags: str = '*',
        pid: int = 0,
        random: bool = False
        ) -> dict[str, ]:
        try:
            request = GelbooruResponse(tags=tags, pid=pid, random=random)
            content: dict[str, ] = await request.get_post()
        except NoPostsFound:
            await interaction.channel.send('no posts found')
            return
        except ClientConnectionError:
            await interaction.channel.send('no connection to Gelbooru')
        return content
        
    @staticmethod
    async def construct_embed(data: dict, file_url: str, is_video: bool) -> discord.Embed:
        if is_video:
            fields: dict = {'fields': []}
        else:
            fields: dict = {'image': {'url': file_url}, 'fields': []}
        for key in data:
            fields['fields'].append({'name': key, 'value': data[key], 'inline' : True})
        return discord.Embed.from_dict(fields)


class ButtonsCallback:
    def __new__(cls) -> None:
        pass
    def __init__(self) -> None:
        pass

    async def button_callback(interaction: discord.Interaction) -> None:
        fields: list[discord.embeds._EmbedFieldProxy] = interaction.message.embeds[0].fields
        tags = fields[0].value
        pid = int(fields[1].value) + 1
        content: dict[str, ] = await SlashCommands.request(interaction, tags=tags, pid=pid, random=False)
        post_url: str = f'https://gelbooru.com/index.php?page=post&s=view&id={content['id']}'
        data = {'tags': content['tags'], 'pid': content['pid']}
        post_embed: discord.Embed = await SlashCommands.construct_embed(data, content['file_url'], content['is_video'])
        
        if content['is_video']:
            await interaction.channel.send(content['file_url'])
            
        Buttons = ButtonsView(post_url)
        await interaction.channel.send(embed=post_embed, view=Buttons)

    async def random_button_callback(interaction: discord.Interaction) -> None:
        fields: list[discord.embeds._EmbedFieldProxy] = interaction.message.embeds[0].fields
        tags = fields[0].value
        pid = fields[1].value
        content: dict[str, ] = await SlashCommands.request(interaction, tags=tags, pid=pid, random=True)
        post_url: str = f'https://gelbooru.com/index.php?page=post&s=view&id={content['id']}'
        data = {'tags': content['tags'], 'pid': content['pid']}
        post_embed: discord.Embed = await SlashCommands.construct_embed(data, content['file_url'], content['is_video'])
        Buttons = ButtonsView(post_url)
        if content['is_video']:
            await interaction.channel.send(content['file_url'])
        
        await interaction.channel.send(embed=post_embed, view=Buttons)


class ButtonsView(discord.ui.View):
    nextButton = discord.ui.Button(label='next', style=discord.ButtonStyle.green)
    nextButton.callback = ButtonsCallback.button_callback
    randomButton = discord.ui.Button(label='random', style=discord.ButtonStyle.blurple)
    randomButton.callback = ButtonsCallback.random_button_callback
    
    def __init__(self, post_url: str) -> None:
        super().__init__(timeout=None)
        urlButton = discord.ui.Button(label='url', url=post_url)
        self.add_item(__class__.nextButton)
        self.add_item(__class__.randomButton)
        self.add_item(urlButton)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(SlashCommands(bot))
