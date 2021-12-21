"""
PhishingBot
~~~~~~~~~~~~

A bot to filter out phishing scams

:copyright: (C) 2019-present FrequencyX4, All Rights Reserved
:license: Proprietary, see LICENSE for details
"""

from typing import *
from os import path
import json
import asyncio
import traceback

import discord
from discord import Bot
import aiomysql
import pymysql

from classes.sql import Cursor


class PhishingBot(Bot):
    pool: aiomysql.Pool = None

    def __init__(self):
        if not path.isfile("config.json"):
            raise FileNotFoundError("config.json doesn't exist")
        with open("config.json", "r") as f:
            self.config: Dict[str, Any] = json.load(f)

        super().__init__(
            intents=discord.Intents(messages=True),
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
    async with bot.cursor() as cur:
        await cur.execute(f"select * from phishing where guild_id = {msg.guild.id};")
        if cur.rowcount:
            # do checks
            pass


@bot.slash_command(name="setup", description="Starts the configuration process")
async def setup(ctx):
    await ctx.respond("Setup complete")


bot.run()