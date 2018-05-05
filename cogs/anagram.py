import asyncio
import discord
import random
from utils.data import data
from discord.ext import commands


class AnagramGame:
    def __init__(self, bot, attempts=3):
        self.bot = bot
        self._attempts = attempts
        self.reset()

    def reset(self):
        self._running = False
        self._state = []
        self._solution = ''
        self._incorrect = []
        self.attempts = 0

    @property
    def state(self):
        return self._state

    @property
    def incorrect(self):
        return ', '.join(self._incorrect)

    @property
    def running(self):
        return self._running

    @running.setter
    def running(self, state):
        self._running = state

    async def start(self, ctx):
        if self.running:
            await self.bot.say(f'{ctx.author.mention}: Anagram is already running here.')
        else:
            self._solution = random.choice(data.pokemon)
            self._state = self._solution
            while self._state == self._solution:
                self._state = random.shuffle(self._solution)
            self.attempts = self._attempts
            self._incorrect = []
            self.running = True
            await self.bot.say(f'Anagram has started! You have {self.attempts:d} attempts to guess correctly before '
                               f'OLDEN corrupts your save.'
                               f'Puzzle: {self.state} | Incorrect: [{self.incorrect}]')

    async def end(self, ctx, failed=False):
        if self.running:
            if failed:
                await ctx.send(f'You were too late, welcome to Glitch Purgatory.\n'
                               f'Solution: {self._solution}')
            else:
                await ctx.send(f'{ctx.author.mention} has solved the puzzle!\n'
                               f'Solution: {self._solution}')
            self.reset()
        else:
            await ctx.send(f'{ctx.author.mention}: Anagram is not running here.')

    async def guess(self, ctx, guess):
        if self.running:
            guess = guess.upper()
            if guess in self._incorrect:
                await ctx.send(f'Character already guessed: {guess}')
            else:
                if self._solution == guess:
                    self._state = self._solution
                    await self.end(ctx)
                else:
                    self._incorrect.append(guess)
                    self.attempts -= 1
            if self.running:
                await ctx.send(f'Puzzle: {self.state} | Incorrect: {self.incorrect}')
                if self.attempts == 0:
                    await self.end(ctx, True)
        else:
            await ctx.send(f'{ctx.author.mention}: Anagram is not running here.')


class Anagram:
    def __init__(self, bot, attempts=3):
        self.bot = bot
        self._attempts = attempts
        self.channels = {}

    @commands.group(pass_context=True)
    async def anagram(self, ctx):
        """Play Anagram"""
        if ctx.invoked_subcommand is None:
            await ctx.send(f'Incorrect anagram subcommand passed. Try {ctx.prefix}help anagram')
        if ctx.channel not in self.channels:
            self.channels[ctx.channel] = AnagramGame(self.bot, self._attempts)

    @anagram.command()
    async def start(self, ctx):
        """Start a game in the current channel"""
        await self.channels[ctx.channel].start(ctx)

    @anagram.command(name='solve')
    async def guess(self, ctx, guess):
        """Solve the puzzle, if you dare"""
        await self.channels[ctx.channel].guess(ctx, guess)

    @anagram.command()
    async def end(self, ctx):
        """End the game as a loss (owner only)"""
        if self.bot.is_owner(ctx.author):
            await self.channels[ctx.channel].end(ctx, True)


def setup(bot):
    bot.add_cog(Anagram(bot))
