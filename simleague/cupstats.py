import discord
from redbot.core import checks, commands

from .abc import MixinMeta
from .utils import mergeDict


class CupStatsMixin(MixinMeta):
    """Stats Settings"""

    @checks.admin_or_permissions(manage_guild=True)
    @commands.command()
    async def clearcupstats(self, ctx, user: discord.Member = None):
        """Clear statistics for a user."""
        if user is not None:
            userid = str(user.id)
            async with self.config.guild(ctx.guild).cupstats() as stats:
                stats["goals"].pop(userid, None)
                stats["assists"].pop(userid, None)
                stats["yellows"].pop(userid, None)
                stats["reds"].pop(userid, None)
                stats["motm"].pop(userid, None)
                stats["penalties"].pop(userid, None)
        await ctx.tick()

    @commands.group(invoke_without_command=True)
    async def cupstats(self, ctx, user: discord.Member = None):
        """Sim Cup Statistics."""
        if user is not None:
            stats = await self.config.guild(ctx.guild).cupstats()
            userid = str(user.id)
            pens = stats["penalties"].get(userid)
            statistics = [
                stats["goals"].get(userid),
                stats["assists"].get(userid),
                stats["yellows"].get(userid),
                stats["reds"].get(userid),
                stats["motm"].get(userid),
                pens.get("missed") if pens else None,
                pens.get("scored") if pens else None,
            ]
            headers = [
                "goals",
                "assists",
                "yellows",
                "reds",
                "motms",
                "penalties missed",
                "penalties scored",
            ]
            embed = discord.Embed(
                color=ctx.author.color, title="Statistics for {}".format(user.display_name)
            )
            for i, stat in enumerate(statistics):
                if stat is not None:
                    embed.add_field(name=headers[i].title(), value=stat)
                else:
                    embed.add_field(name=headers[i].title(), value="0")
            await ctx.send(embed=embed)

        else:
            await ctx.send_help()
            stats = await self.config.guild(ctx.guild).cupstats()
            goalscorer = sorted(stats["goals"], key=stats["goals"].get, reverse=True)
            assists = sorted(stats["assists"], key=stats["assists"].get, reverse=True)
            yellows = sorted(stats["yellows"], key=stats["yellows"].get, reverse=True)
            reds = sorted(stats["reds"], key=stats["reds"].get, reverse=True)
            motms = sorted(stats["motm"], key=stats["motm"].get, reverse=True)
            cleansheets = sorted(stats["cleansheets"], key=stats["cleansheets"].get, reverse=True)
            penscored = sorted(
                stats["penalties"], key=lambda x: stats["penalties"][x]["scored"], reverse=True
            )
            penmissed = sorted(
                stats["penalties"], key=lambda x: stats["penalties"][x]["missed"], reverse=True
            )
            msg = ""
            msg += "**Top Goalscorer**: {} - {}\n".format(
                await self.statsmention(ctx, goalscorer),
                stats["goals"][goalscorer[0]] if len(goalscorer) else "",
            )
            msg += "**Most Assists**: {} - {}\n".format(
                await self.statsmention(ctx, assists),
                stats["assists"][assists[0]] if len(assists) else "",
            )
            msg += "**Most Yellow Cards**: {} - {}\n".format(
                await self.statsmention(ctx, yellows),
                stats["yellows"][yellows[0]] if len(yellows) else "",
            )
            msg += "**Most Red Cards**: {} - {}\n".format(
                await self.statsmention(ctx, reds), stats["reds"][reds[0]] if len(reds) else ""
            )
            msg += "**Penalties Scored**: {} - {}\n".format(
                await self.statsmention(ctx, penscored),
                stats["penalties"][penscored[0]]["scored"] if len(penscored) else "",
            )
            msg += "**Penalties Missed**: {} - {}\n".format(
                await self.statsmention(ctx, penmissed),
                stats["penalties"][penmissed[0]]["missed"] if len(penmissed) else "",
            )
            msg += "**MOTMs**: {} - {}\n".format(
                await self.statsmention(ctx, motms), stats["motm"][motms[0]] if len(motms) else ""
            )
            if cleansheets:
                msg += "**Cleansheets**: _{}_ - {}\n".format(
                    cleansheets[0], stats["cleansheets"][cleansheets[0]]
                )
            else:
                msg += "**Cleansheets**: {}\n".format(await self.statsmention(ctx, cleansheets))
            await ctx.maybe_send_embed(msg)

    async def statsmention(self, ctx, stats):
        if stats:
            user = ctx.guild.get_member(int(stats[0]))
            if not user:
                return "Invalid User {}".format(stats[0])
            return f"_{user.name}_"
        else:
            return "None"

    @cupstats.command(name="ga", alias=["ga", "contributions"])
    async def _cupgoals_assists(self, ctx):
        """Players with the most combined goals and assists."""
        teams = await self.config.guild(ctx.guild).teams()
        stats = await self.config.guild(ctx.guild).cupstats()
        goals = stats["goals"]
        assists = stats["assists"]
        contributions = mergeDict(goals, assists)
        stats = contributions
        if contributions:
            a = []
            for i, k in enumerate(sorted(stats, key=stats.get, reverse=True)):
                user = self.bot.get_user(int(k))
                team = ""
                for t in teams:
                    print(teams[t]["members"])
                    if k in teams[t]["members"]:
                        team = t
                        pass
                a.append(f"{i+1}. {user.name if user else 'Invalid User {}'.format(k)} ({team.upper()[:3]}) - {stats[k]}")
            embed = discord.Embed(
                title="Top goal involvements (goals + assists)",
                description="\n".join(a[:10]),
                colour=0xFF0000,
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send("No stats available.")

    @cupstats.command(name="goals", alias=["topscorer", "topscorers"])
    async def _cupgoals(self, ctx):
        """Players with the most goals."""
        teams = await self.config.guild(ctx.guild).teams()
        stats = await self.config.guild(ctx.guild).cupstats()
        stats = stats["goals"]
        if stats:
            a = []
            for i, k in enumerate(sorted(stats, key=stats.get, reverse=True)):
                user = self.bot.get_user(int(k))
                team = ""
                for t in teams:
                    print(teams[t]["members"])
                    if k in teams[t]["members"]:
                        team = t
                        pass
                a.append(f"{i+1}. {user.name if user else 'Invalid User {}'.format(k)} ({team.upper()[:3]}) - {stats[k]}")
            embed = discord.Embed(
                title="Top Scorers", description="\n".join(a[:10]), colour=0xFF0000
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send("No stats available.")

    @cupstats.command(name="yellows", aliases=["yellowcards"])
    async def _yellows(self, ctx):
        """Players with the most yellow cards."""
        teams = await self.config.guild(ctx.guild).teams()
        stats = await self.config.guild(ctx.guild).cupstats()
        stats = stats["yellows"]
        if stats:
            a = []
            for i, k in enumerate(sorted(stats, key=stats.get, reverse=True)):
                user = self.bot.get_user(int(k))
                team = ""
                for t in teams:
                    print(teams[t]["members"])
                    if k in teams[t]["members"]:
                        team = t
                        pass
                a.append(f"{i+1}. {user.name if user else 'Invalid User {}'.format(k)} ({team.upper()[:3]}) - {stats[k]}")
            embed = discord.Embed(
                title="Most Yellow Cards", description="\n".join(a[:10]), colour=0xFF0000
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send("No stats available.")

    @cupstats.command(name="reds", aliases=["redcards"])
    async def _reds(self, ctx):
        """Players with the most red cards."""
        teams = await self.config.guild(ctx.guild).teams()
        stats = await self.config.guild(ctx.guild).cupstats()
        stats = stats["reds"]
        if stats:
            a = []
            for i, k in enumerate(sorted(stats, key=stats.get, reverse=True)):
                user = self.bot.get_user(int(k))
                team = ""
                for t in teams:
                    print(teams[t]["members"])
                    if k in teams[t]["members"]:
                        team = t
                        pass
                a.append(f"{i+1}. {user.name if user else 'Invalid User {}'.format(k)} ({team.upper()[:3]}) - {stats[k]}")
            embed = discord.Embed(
                title="Most Red Cards", description="\n".join(a[:10]), colour=0xFF0000
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send("No stats available.")

    @cupstats.command(name="motms", alias=["motms"])
    async def _motm(self, ctx):
        """Players with the most MOTMs."""
        teams = await self.config.guild(ctx.guild).teams()
        stats = await self.config.guild(ctx.guild).cupstats()
        stats = stats["motm"]
        if stats:
            a = []
            for i, k in enumerate(sorted(stats, key=stats.get, reverse=True)):
                user = self.bot.get_user(int(k))
                team = ""
                for t in teams:
                    print(teams[t]["members"])
                    if k in teams[t]["members"]:
                        team = t
                        pass
                a.append(f"{i+1}. {user.name if user else 'Invalid User {}'.format(k)} ({team.upper()[:3]}) - {stats[k]}")
            embed = discord.Embed(
                title="Most MOTMs", description="\n".join(a[:10]), colour=0xFF0000
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send("No stats available.")

    @cupstats.command(name="cleansheets")
    async def _cleansheets(self, ctx):
        """Teams with the most cleansheets."""
        stats = await self.config.guild(ctx.guild).cupstats()
        stats = stats["cleansheets"]
        if stats:
            a = []
            for i, k in enumerate(sorted(stats, key=stats.get, reverse=True)[:10]):
                a.append(f"{i+1}. {k} - {stats[k]}")
            embed = discord.Embed(
                title="Most Cleansheets", description="\n".join(a), colour=0xFF0000
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send("No stats available.")

    @cupstats.command(name="penalties")
    async def _penalties(self, ctx):
        """Penalties scored and missed statistics."""
        teams = await self.config.guild(ctx.guild).teams()
        stats = await self.config.guild(ctx.guild).cupstats()
        stats = stats["penalties"]
        if stats:
            a = []
            b = []
            for i, k in enumerate(sorted(stats, key=lambda x: stats[x]["scored"], reverse=True)[:10]):
                user = self.bot.get_user(int(k))
                team = ""
                for t in teams:
                    print(teams[t]["members"])
                    if k in teams[t]["members"]:
                        team = t
                        pass
                a.append(f"{i+1}. {user.name if user else 'Invalid User {}'.format(k)} ({team.upper()[:3]}) - {stats[k]['scored']}")
            for i, k in enumerate(sorted(stats, key=lambda x: stats[x]["missed"], reverse=True)[:10]):
                user = self.bot.get_user(int(k))
                team = ""
                for t in teams:
                    print(teams[t]["members"])
                    if k in teams[t]["members"]:
                        team = t
                        pass
                b.append(f"{i+1}. {user.name if user else 'Invalid User {}'.format(k)} ({team.upper()[:3]}) - {stats[k]['missed']}")
            embed = discord.Embed(title="Penalty Statistics", colour=0xFF0000, description="=== Scored and Missed penalties statistics ===")
            embed.add_field(name="Penalties Scored", value="\n".join(a))
            embed.add_field(name="Penalties Missed", value="\n".join(b))
            await ctx.send(embed=embed)
        else:
            await ctx.send("No stats available.")

    @cupstats.command(name="assists")
    async def _assists(self, ctx):
        """Players with the most assists."""
        teams = await self.config.guild(ctx.guild).teams()
        stats = await self.config.guild(ctx.guild).cupstats()
        stats = stats["assists"]
        if stats:
            a = []
            for i, k in enumerate(sorted(stats, key=stats.get, reverse=True)[:10]):
                user = self.bot.get_user(int(k))
                team = ""
                for t in teams:
                    print(teams[t]["members"])
                    if k in teams[t]["members"]:
                        team = t
                        pass
                a.append(f"{i+1}. {user.name if user else 'Invalid User {}'.format(k)} ({team.upper()[:3]}) - {stats[k]}")
            embed = discord.Embed(
                title="Assist Statistics", description="\n".join(a), colour=0xFF0000
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send("No stats available.")
