import datetime
import discord
from discord.ext import commands
from cogs import BaseCog
from utils.botclass import PikalaxBOT


class SeenUser(BaseCog):
    MAX_LOOKBACK = datetime.timedelta(days=1)

    def __init__(self, bot: PikalaxBOT):
        super().__init__(bot)
        self.member_cache = {}

    async def on_message(self, message: discord.Message):
        self.member_cache[(message.guild.id, message.author.id)] = message

    async def get_last_seen_msg(self, member: discord.Member) -> discord.Message:
        last = datetime.datetime.now() - self.MAX_LOOKBACK
        seen_msg = None
        for channel in member.guild.text_channels:
            if channel.permissions_for(member.guild.me).read_message_history:
                async for message in channel.history(limit=None, after=last):
                    if message.author == member:
                        last = message.created_at
                        seen_msg = message
                        break
        return seen_msg

    @staticmethod
    def friendly_time(timestamp: datetime.datetime) -> str:
        now = datetime.datetime.now()
        daystr = 'Yesterday' if timestamp.day < now.day else 'Today'
        timestr = timestamp.strftime('%H:%M:%S')
        return f'{daystr} at {timestr} UTC'

    @commands.command()
    async def seen(self, ctx: commands.Context, *, member: discord.Member):
        """Returns the last message sent by the given member in the current server.
        Initially looks back up to 24 hours."""
        key = (ctx.guild.id, member.id)
        if key in self.member_cache:
            seen_msg = self.member_cache[key]
        else:
            async with ctx.typing():
                seen_msg = await self.get_last_seen_msg(member)
            self.member_cache[key] = seen_msg
        if seen_msg is None:
            await ctx.send(f'{member.display_name} has not said anything on this server recently.')
        else:
            await ctx.send(f'{member.display_name} was last seen chatting in {seen_msg.channel.mention} '
                           f'{self.friendly_time(seen_msg.created_at)}\n{seen_msg.jump_url}')


def setup(bot: PikalaxBOT):
    bot.add_cog(SeenUser(bot))