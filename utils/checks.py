import asyncio
import discord
from discord.ext import commands


class CommandNotAllowed(commands.CheckFailure):
    pass


async def ctx_is_owner(ctx):
    if await ctx.bot.is_owner(ctx.author):
        return True
    raise CommandNotAllowed


async def ctx_markov_general_checks(ctx):
    if not ctx.bot.initialized:
        return False
    if ctx.channel.id not in ctx.bot.whitelist:
        return False
    if ctx.author.bot:
        return False
    if len(ctx.bot.markov_channels) == 0:
        return False
    if ctx.author.id == ctx.bot.user.id:
        return False
    if ctx.command is not None:
        return False
    return True


async def ctx_can_markov(ctx):
    if not await ctx_markov_general_checks(ctx):
        return False
    if ctx.bot.user.mentioned_in(ctx.message):
        return True
    words = ctx.message.clean_content.lower().split()
    if ctx.bot.user.name.lower() in words:
        return True
    if ctx.bot.get_nick(ctx.guild).lower() in words:
        return True
    return False


async def ctx_can_learn_markov(ctx, force=False):
    if not (force or await ctx_markov_general_checks(ctx)):
        return False
    if ctx.author.bot:
        return False
    return ctx.channel.id in ctx.bot.markov_channels and not ctx.message.clean_content.startswith('!')


async def ctx_is_nsfw(ctx: commands.Context):
    channel: discord.TextChannel = ctx.channel
    return channel.is_nsfw()
