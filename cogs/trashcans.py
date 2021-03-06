# PikalaxBOT - A Discord bot in discord.py
# Copyright (C) 2018  PikalaxALT
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import random

from discord.ext import commands

from utils.game import GameBase, GameCogBase, BoardCoords


class TrashcansGame(GameBase):
    def __init__(self, bot):
        super().__init__(bot, timeout=180)

    def reset(self):
        super().reset()
        self.reset_locks()

    def __str__(self):
        board = '\n'.join(' '.join('\u2705' if y else chr(0x1f5d1) for y in x) for x in self.state)
        board += f'\nPlayers: {self.get_player_names()}'
        return board

    @staticmethod
    def is_valid(x, y):
        return x in range(5) and y in range(3)

    def reset_locks(self):
        self._solution = [[False for j in range(5)] for i in range(3)]
        x1 = random.randint(0, 4)
        y1 = random.randint(0, 2)
        self._solution[y1][x1] = True
        options = [
            ( 0, -1),
            ( 0,  1),
            (-1,  0),
            ( 1,  0),
            (-1, -1),
            (-1,  1),
            ( 1, -1),
            ( 1,  1)
        ]
        x2 = -1
        y2 = -1
        while not self.is_valid(x2, y2):
            dx, dy = random.choice(options)
            x2 = x1 + dx
            y2 = y1 + dy
        self._solution[y2][x2] = True
        self._state = [[False for j in range(5)] for i in range(3)]
        self.on_second_can = False

    async def start(self, ctx: commands.Context):
        if self.running:
            await ctx.send(f'{ctx.author.mention}: Trashcans is already running here.',
                           delete_after=10)
        else:
            self.reset_locks()
            await ctx.send(f'Welcome to Lt. Surge\'s Gym!  Use `!trashcans guess y x` to check a can!\n'
                           f'You have {self._timeout:d} seconds to find both switches.  Good luck!')
            await super().start(ctx)

    async def end(self, ctx: commands.Context, failed=False, aborted=False):
        if self.running:
            self._state = [[x for x in y] for y in self._solution]
            if self._task and not self._task.done():
                self._task.cancel()
                self._task = None
            await self._message.edit(content=self)
            if aborted:
                await ctx.send(f'Game terminated by {ctx.author.mention}.')
            elif failed:
                await ctx.send('Looks like you won\'t be fighting the Gym Leader today.')
            else:
                score = await self.award_points()
                await ctx.send(f'Congratulations to {ctx.author.mention} for opening the door!\n'
                               f'The following players each earn {score:d} points:\n'
                               f'```{self.get_player_names()}```')
            self.reset()
        else:
            await ctx.send(f'{ctx.author.mention}: Trashcans is not running here. '
                           f'Start a game by saying `{ctx.prefix}trashcans start`.',
                           delete_after=10)

    async def guess(self, ctx: commands.Context, x: int, y: int):
        if self.running:
            if self.on_second_can:
                if self.state[y][x] or not self._solution[y][x]:
                    self.reset_locks()
                    await ctx.send(f'Nope! There\'s only trash here.\n'
                                   f'Hey! The electric locks were reset!',
                                   delete_after=10)
                else:
                    self.add_player(ctx.author)
                    self.state[y][x] = True
                    await ctx.send(f'Hey! There\'s another switch under the trash! Turn it on!\n'
                                   f'The 2nd electric lock opened! The motorized door opened!',
                                   delete_after=10)
                    await ctx.message.add_reaction('\u2705')
                    await self.end(ctx)
            else:
                if self._solution[y][x]:
                    self.add_player(ctx.author)
                    self.state[y][x] = True
                    self.on_second_can = True
                    await ctx.send(f'Hey! There\'s a switch under the trash! Turn it on!\n'
                                   f'The 1st electric lock opened!',
                                   delete_after=10)
                    await ctx.message.add_reaction('☑')
                else:
                    await ctx.send(f'Nope, there\'s only trash here.',
                                   delete_after=10)
            if self._message:
                await self._message.edit(content=self)
        else:
            await ctx.send(f'{ctx.author.mention}: Trashcans is not running here. '
                           f'Start a game by saying `{ctx.prefix}trashcans start`.',
                           delete_after=10)

    async def show(self, ctx):
        if await super().show(ctx) is None:
            await ctx.send(f'{ctx.author.mention}: Trashcans is not running here. '
                           f'Start a game by saying `{ctx.prefix}trashcans start`.',
                           delete_after=10)


converter = BoardCoords(maxy=3)


class Trashcans(GameCogBase):
    gamecls = TrashcansGame

    def __local_check(self, ctx):
        return self._local_check(ctx)

    @commands.group(case_insensitive=True)
    async def trashcans(self, ctx):
        """Play trashcans"""
        if ctx.invoked_subcommand is None:
            await ctx.send(f'Incorrect trashcans subcommand passed. '
                           f'Try `{ctx.prefix}{self.bot.settings.help_name} trashcans`')

    @trashcans.command()
    async def start(self, ctx):
        """Start a game in the current channel"""
        await self.game_cmd('start', ctx)

    @commands.command(name='trashstart', aliases=['tst'])
    async def trashcans_start(self, ctx):
        """Start a game in the current channel"""
        await ctx.invoke(self.start)

    @trashcans.command()
    async def guess(self, ctx, *, args: converter):
        """Make a guess, if you dare"""
        await self.game_cmd('guess', ctx, *args)

    @commands.command(name='trashguess', aliases=['tgu', 'tg'])
    async def trashcans_guess(self, ctx, *, args: converter):
        """Make a guess, if you dare"""
        await ctx.invoke(self.guess, args=args)

    @trashcans.command()
    @commands.is_owner()
    async def end(self, ctx):
        """End the game as a loss (owner only)"""
        await self.game_cmd('end', ctx, aborted=True)

    @commands.command(name='trashend', aliases=['te'])
    @commands.is_owner()
    async def trashcans_end(self, ctx):
        """End the game as a loss (owner only)"""
        await ctx.invoke(self.end)

    @trashcans.command()
    async def show(self, ctx):
        """Show the board in a new message"""
        await self.game_cmd('show', ctx)

    @commands.command(name='trashshow', aliases=['tsh'])
    async def trashcans_show(self, ctx):
        """Show the board in a new message"""
        await ctx.invoke(self.show)

    async def __error(self, ctx, exc):
        await self._error(ctx, exc)


def setup(bot):
    bot.add_cog(Trashcans(bot))
