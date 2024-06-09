from discord.ext import commands
from discord.app_commands import AppCommand

class Ping(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot: commands.Bot = bot
        
    @commands.command('ping')
    async def ping(self, ctx: commands.context.Context):
        await ctx.reply('pong')

#"""
# sync command example (refresh discord on pc - Ctrl+R)
    @commands.command('sync')
    async def sync_commands(self, ctx: commands.context.Context):
        commands_list: list[AppCommand] = await self.bot.tree.sync()
        synced_commands = ''
        for command in commands_list:
            synced_commands += f' {command.name}'
        await ctx.send(f'synced:{synced_commands}') # or just print(*commands_list)
#"""


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Ping(bot))
