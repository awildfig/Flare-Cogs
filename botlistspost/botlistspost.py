import asyncio
import json
import logging

import aiohttp
from redbot.core import commands
from redbot.core.utils.chat_formatting import humanize_list

DBLEL = "https://api.discordextremelist.xyz/v2/bot/{BOTID}/stats"
BFD = "https://botsfordiscord.com/api/bot/{BOTID}"
DB = "https://discord.bots.gg/api/v1/bots/{BOTID}/stats"
BSDC = "https://api.server-discord.com/v2/bots/{BOTID}/stats"
DBL = "https://discordbotlist.com/api/v1/bots/{BOTID}/stats"

log = logging.getLogger("red.flare.botlistpost")


class BotListsPost(commands.Cog):
    """Post data to bot lists. For DBL use Predas cog"""

    __version__ = "0.0.5"

    def format_help_for_context(self, ctx):
        """Thanks Sinbad."""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\nCog Version: {self.__version__}"

    def __init__(self, bot):
        self.bot = bot
        self._session = aiohttp.ClientSession(loop=self.bot.loop)
        self.dbleltoken = None
        self.bfdtoken = None
        self.dbtoken = None
        self.bsdctoken = None
        self.dbltoken = None
        self.post_stats_task = self.bot.loop.create_task(self.post_stats())

    async def red_get_data_for_user(self, *, user_id: int):
        # this cog does not story any data
        return {}

    async def red_delete_data_for_user(self, *, requester, user_id: int) -> None:
        # this cog does not story any data
        pass

    async def init(self):
        bfd = await self.bot.get_shared_api_tokens("botsfordiscord")
        self.bfdtoken = bfd.get("authorization")
        dblel = await self.bot.get_shared_api_tokens("discordextremelist")
        self.dbleltoken = dblel.get("authorization")
        db = await self.bot.get_shared_api_tokens("discordbots")
        self.dbtoken = db.get("authorization")
        sd = await self.bot.get_shared_api_tokens("serverdiscord")
        self.bsdctoken = sd.get("authorization")
        dbl = await self.bot.get_shared_api_tokens("discordbotlist")
        self.dbltoken = dbl.get("authorization")

    @commands.Cog.listener()
    async def on_red_api_tokens_update(self, service_name, api_tokens):
        if service_name == "botsfordiscord":
            self.bfdtoken = {"Authorization": api_tokens.get("authorization")}
        elif service_name == "discordextremelist":
            self.dbleltoken = {"Authorization": api_tokens.get("authorization")}
        elif service_name == "discordbots":
            self.dbtoken = {"Authorization": api_tokens.get("authorization")}
        elif service_name == "serverdiscord":
            self.bsdctoken = {"Authorization": api_tokens.get("authorization")}
        elif service_name == "discordbotlist":
            self.dbltoken = {"Authorization": api_tokens.get("authorization")}

    def cog_unload(self):
        self.bot.loop.create_task(self._session.close())
        if self.post_stats_task:
            self.post_stats_task.cancel()

    async def post_stats(self):
        await self.bot.wait_until_ready()
        await self.init()
        while True:
            success = []
            failed = []
            serverc = len(self.bot.guilds)
            shardc = self.bot.shard_count
            botid = self.bot.user.id
            if self.dbleltoken is not None:
                async with self._session.post(
                    DBLEL.format(BOTID=botid),
                    headers={"Authorization": self.dbleltoken, "Content-Type": "application/json"},
                    data=json.dumps({"guildCount": serverc, "shardCount": shardc}),
                ) as resp:
                    if resp.status == 200:
                        success.append("Discord Extreme List")
                    else:
                        failed.append(f"Discord Extreme List ({resp.status}")

            if self.dbtoken is not None:
                try:
                    async with self._session.post(
                        DB.format(BOTID=botid),
                        headers={
                            "Authorization": self.dbtoken,
                            "Content-Type": "application/json",
                        },
                        data=json.dumps({"guildCount": serverc, "shardCount": shardc}),
                    ) as resp:
                        if resp.status == 200:
                            success.append("Discord Bots")
                        else:
                            failed.append(f"Discord Bots ({resp.status}")
                except Exception as e:
                    print(e)

            if self.bfdtoken is not None:
                async with self._session.post(
                    BFD.format(BOTID=botid),
                    headers={"Authorization": self.bfdtoken, "Content-Type": "application/json"},
                    data=json.dumps({"server_count": serverc}),
                ) as resp:
                    if resp.status == 200:
                        success.append("Bots for Discord")
                    else:
                        failed.append(f"Bots for Discord ({resp.status}")

            if self.bsdctoken is not None:
                async with self._session.post(
                    BSDC.format(BOTID=botid),
                    headers={"Authorization": f"SDC {self.bsdctoken}"},
                    data={"servers": serverc, "guilds": shardc},
                ) as resp:
                    resp = await resp.json()
                    if resp.get("status"):
                        success.append("Server-Discord bot list")
                    else:
                        failed.append(f"Server-Discord bot list ({resp.get('error')})")

            if self.dbltoken is not None:
                async with self._session.post(
                    DBL.format(BOTID=botid),
                    headers={"Authorization": self.dbltoken, "Content-Type": "application/json"},
                    data=json.dumps({"guilds": serverc, "users": len(self.bot.users)}),
                ) as resp:
                    if resp.status == 200:
                        success.append("Discord Bot List")
                    else:
                        failed.append(f"Discord Bot List ({resp.status})")
            if failed:
                log.info(f"Unable to post data to {humanize_list(failed)}.")
            if success:
                log.info(f"Successfully posted servercount to {humanize_list(success)}.")
            await asyncio.sleep(1800)

    @commands.is_owner()
    @commands.command()
    async def botlistpost(self, ctx):
        """Setup for botlistposting"""
        msg = (
            "This cog currently supports [Bots for Discord](https://botsfordiscord.com), "
            "[Discord Extreme List](https://discordextremelist.xyz/en-US/), "
            "[Discord Bots](https://discord.bots.gg), "
            "[Server-Discord](https://docs.server-discord.com/) and "
            "[Discord Bot Lists](https://discordbotlist.com).\n"
            "To set this cog up, please use the following commands:\n"
            f"`{ctx.clean_prefix}set api botsfordiscord authorization <botsfordiscord apikey>`\n"
            f"`{ctx.clean_prefix}set api discordextremelist authorization <discordextremelist apikey>`\n"
            f"`{ctx.clean_prefix}set api discordbots authorization <discordbots apikey>`\n"
            f"`{ctx.clean_prefix}set api serverdiscord authorization <SDC token>`\n"
            f"`{ctx.clean_prefix}set api discordbotlist authorization <DBL token>`\n"
        )
        await ctx.maybe_send_embed(msg)
