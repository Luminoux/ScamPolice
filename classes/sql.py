"""
Mysql Cursor Util
~~~~~~~~~~~~~~~~~~

A class for simplified use of an AioMySQL pool

Credit: https://github.com/FrequencyX4/Fate/blob/master/botutils/resources.py

Copyright (C) 2018-present FrequencyX4, All Rights Reserved
Unauthorized copying, or reuse of anything in this repository written by the owner, via any medium is strictly prohibited.
This copyright notice, and this permission notice must be included in all copies, or substantial portions of the Software
Written by FrequencyX4 <frequencyx4@gmail.com>
"""

import asyncio
import pymysql


class Cursor:
    def __init__(self, bot, max_retries: int = 10):
        self.bot = bot
        self.conn = None
        self.cursor = None
        self.retries = max_retries

    async def __aenter__(self):
        while not self.bot.pool:
            await asyncio.sleep(10)
        for _ in range(self.retries):
            try:
                self.conn = await self.bot.pool.acquire()
            except (pymysql.OperationalError, RuntimeError):
                await asyncio.sleep(1.21)
                continue
            self.cursor = await self.conn.cursor()
            break
        else:
            raise pymysql.OperationalError("Can't connect to db")
        return self.cursor

    async def __aexit__(self, _type, _value, _tb):
        with suppress(RuntimeError):
            self.bot.pool.release(self.conn)
