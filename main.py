"""
PhishingBot
~~~~~~~~~~~~

A bot to filter out phishing scams

:copyright: (C) 2021-present FrequencyX4, All Rights Reserved
:license: Proprietary, see LICENSE for details
"""

from typing import *
from os import path
import json
import asyncio
import traceback
import aiohttp
import re
from datetime import datetime, timedelta

import discord
from discord.commands import Option
from discord.ext import commands
import aiomysql
import pymysql

from classes.sql import Cursor


class PhishingBot(commands.Bot):
    pool: aiomysql.Pool = None

    def __init__(self):
        if not path.isfile("config.json"):
            raise FileNotFoundError("config.json doesn't exist")
        with open("config.json", "r") as f:
            self.config: Dict[str, Any] = json.load(f)

        super().__init__(
            intents=discord.Intents(messages=True, members=True, guilds=True),
            max_messages=100
        )

    async def create_pool(self) -> None:
        """ Initializes the bots MySQL pool """
        sql = self.config["mysql"]
        for _attempt in range(5):
            try:
                print("Connecting to db")
                pool = await aiomysql.create_pool(
                    host=sql["host"],
                    port=sql["port"],
                    user=sql["user"],
                    password=sql["password"],
                    db=sql["db"],
                    autocommit=True,
                    loop=self.loop,
                    minsize=1,
                    maxsize=16
                )
                self.pool = pool
                break
            except (ConnectionRefusedError, pymysql.err.OperationalError):
                print("Couldn't connect to MySQL server, retrying in 25 seconds..")
                print(traceback.format_exc())
            await asyncio.sleep(25)
        else:
            print(
                f"Couldn't connect to MySQL server, reached max attempts"
                f"\n{traceback.format_exc()}"
                f"\nLogging out.."
            )
            return await self.close()
        print(f"Initialized db {sql['db']} with {sql['user']}@{sql['host']}")

    def cursor(self) -> Cursor:
        """ Returns an SQL cursor as an async contextmanager """
        return Cursor(self)

    def run(self):
        """ Starts the bot """
        super().run(self.config["token"])


bot = PhishingBot()
link_regex = "(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9][a-z0-9-]{0,61}[a-z0-9]"


async def has_link(string) -> bool:
    """ Checks whether or not a string contains a link """
    def search():
        return re.search(link_regex, string)

    # Run the search in a separate thread to avoid blocking the loop
    if await bot.loop.run_in_executor(None, search):
        return True
    return False


@bot.event
async def on_ready():
    print(
        f"Logged in as"
        f"\n{bot.user}"
        f"\n{bot.user.id}"
        f"\nServing {len(bot.guilds)} servers"
    )
    await bot.create_pool()


@bot.event
async def on_message(msg):
    """ Check for phishing scams """
    if not bot.is_ready() or not bot.pool or not msg.content:
        return
    # Check if the message has any links before operating
    if "." not in msg.content or not await has_link(msg.content):
       return
    async with bot.cursor() as cur:
        await cur.execute(f"select action from phishing where guild_id = {msg.guild.id};")
        if cur.rowcount:
            triggered = False
            async with aiohttp.ClientSession() as session:
                method = session.post(
                    url=bot.config["api_url"],
                    json={"message": msg.content}
                )
                async with method as resp:
                    if resp.status == 200:
                        triggered = True

            if triggered:
                action, = await cur.fetchone()  # type: str
                await msg.delete()
                if action == "timeout":
                    await msg.author.timeout(
                        until=datetime.utcnow() + timedelta(days=1),
                        reason="Sending a phishing scam"
                    )
                elif action == "ban":
                    await msg.author.ban(reason="Sending a phishing scam")


@bot.slash_command(name="enable", description="Enables filtering phishing scams")
async def enable(
    ctx, action: Option(
        str, "Action To Take",
        choices=["Delete", "Delete & Timeout","Delete & Ban"]
    )
):
    if ctx.author.id != 264838866480005122:
        return await ctx.send("Only luck can run this rn", ephemeral=True)
    action: str = action.split()[-1:][0].lower()
    async with bot.cursor() as cur:
        await cur.execute(
            f"insert into phishing values "
            f"({ctx.guild.id}, '{action}') "
            f"on duplicate key update action = '{action}';"
        )
    await ctx.respond("Setup complete")


bot.run()
