"""
Blaze-Agent Soul Commands
Discord slash commands for Soul.md management.
"""

import discord
from discord import app_commands
from discord.ext import commands
from bot.utils.soul import load_soul, reload_soul

class SoulCog(commands.Cog, name="Soul"):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="soul_template", description="Load a Soul.md template")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(template="Template to load")
    @app_commands.choices(template=[
        app_commands.Choice(name="Restaurant", value="restaurant"),
        app_commands.Choice(name="Salon / Spa", value="salon"),
        app_commands.Choice(name="Shop / Retail", value="shop"),
        app_commands.Choice(name="Clinic / Medical", value="clinic"),
        app_commands.Choice(name="Real Estate", value="realestate"),
        app_commands.Choice(name="General", value="generic"),
    ])
    async def soul_template(self, interaction: discord.Interaction, template: str):
        await interaction.response.send_message(
            f"⚠️ Loading the '{template}' template will overwrite your current Soul.md. "
            "Use /soul to edit instead, or confirm in the dashboard.",
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(SoulCog(bot))
