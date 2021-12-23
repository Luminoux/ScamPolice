"""
classes.views
~~~~~~~~~~~~~~

Interaction menus used within the bot

:copyright: (C) 2021-present FrequencyX4, All Rights Reserved
:license: Proprietary, see LICENSE for details
"""

from typing import *
import discord


class ChooseAction(discord.ui.View):
    """ The View for picking what action to take when triggered """

    class Dropdown(discord.ui.Select):
        def __init__(self):
            options = [
                "Delete"
                "Delete & Timeout",
                "Delete & Ban"
            ]
            super().__init__(
                placeholder="Choose an action",
                min_values=1,
                max_values=1,
                options=[discord.SelectOption(label=option) for option in options]
            )

        async def callback(self, interaction):
            v = self.view.value = interaction.data["values"][0]
            await interaction.response.edit_message(
                content=f"Alright, I'll {v.lower()} when triggered",
                view=None
            )
            self.view.stop()

    def __init__(self, ctx):
        self.ctx = ctx
        self.value = None
        super().__init__(timeout=45)

        self.add_item(self.Dropdown())

    def __await__(self) -> Generator[None, None, str]:
        return self._await(self.ctx).__await__()

    async def _await(self, ctx) -> str:
        await ctx.respond(
            "What action should I take when someone sends a phishing link?",
            view=self,
            ephemeral=True
        )
        await self.wait()
        return self.value
