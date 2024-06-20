import discord
import gelbooru
from errors import NoPostsFound
from aiohttp.client_exceptions import ClientConnectionError


__all__ = (
    'ButtonsCallback',
    'ButtonsView',
    'construct_embed',
    'ds_request'
    )

class ButtonsCallback():
    def __new__(cls) -> None:
        pass
    
    @staticmethod
    async def next_button_callback(interaction: discord.Interaction) -> None:
        await __class__.button_callback(interaction, False)

    @staticmethod
    async def random_button_callback(interaction: discord.Interaction) -> None:
        await __class__.button_callback(interaction, True)
    
    @staticmethod
    async def button_callback(interaction: discord.Interaction, random: bool) -> None:
        await interaction.response.defer()
        fields: list[discord.embeds._EmbedFieldProxy] = interaction.message.embeds[0].fields
        tags: str = fields[0].value
        if random:
            pid = int(fields[1].value)
        else:
            pid = int(fields[1].value) + 1
        
        response = await ds_request(interaction, tags=tags, pid=pid, random=random)
        if response is None:
            return
        
        content: dict[str, ] = response['content']
        post_url: str = f'https://gelbooru.com/index.php?page=post&s=view&id={content['id']}'
        Buttons = ButtonsView(post_url)
        post_embed: discord.Embed = await construct_embed(
            response['embed_data'], content['file_url'], response['is_video'])
        
        if response['is_video']:
            await interaction.channel.send(content['file_url'])
        
        await interaction.channel.send(embed=post_embed, view=Buttons)


class ButtonsView(discord.ui.View):
    nextButton = discord.ui.Button(label='next', style=discord.ButtonStyle.green)
    nextButton.callback = ButtonsCallback.next_button_callback
    randomButton = discord.ui.Button(label='random', style=discord.ButtonStyle.blurple)
    randomButton.callback = ButtonsCallback.random_button_callback
    
    def __init__(self, post_url: str) -> None:
        super().__init__(timeout=None)
        urlButton = discord.ui.Button(label='url', url=post_url)
        self.add_item(__class__.nextButton)
        self.add_item(__class__.randomButton)
        self.add_item(urlButton)

        
async def construct_embed(
    fields_data: dict[str, ], 
    file_url: str, 
    is_video: bool
    ) -> discord.Embed:
    fields = {'fields': []}
    if not is_video:
        fields['image'] = {'url': file_url}
    for key in fields_data:
        fields['fields'].append({'name': key, 'value': fields_data[key], 'inline' : True})
    return discord.Embed.from_dict(fields)
 
async def ds_request(
    interaction: discord.Interaction,
    *,
    tags: str = '*',
    pid: int = 0,
    random: bool = False
    ) -> dict[str, dict[str, ] | bool] | None:
    response: dict[str, ] = dict()
    request = gelbooru.Response(tags=tags, pid=pid, random=random)
    
    try:
        content: dict[str, ] = await request.get_post()
    except NoPostsFound:
        await interaction.followup.send('no posts found')
        return None
    except ClientConnectionError:
        await interaction.channel.send('no connection to Gelbooru')
        raise
    
    response['content'] = content
    response['embed_data'] = {'tags': content['tags'], 'pid': content['pid']}
    if content['file_url'].endswith(('.gif', '.webm', '.mp4')):
        response['is_video'] = True
    else:
        response['is_video'] = False
    return response
