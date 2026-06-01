"""
Blaze-Agent Skills Commands
Discord slash commands for skills management.
"""

import discord
from discord import app_commands
from discord.ext import commands
from bot.utils.skills import get_skills_status, set_skill

class SkillsCog(commands.Cog, name="Skills"):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="skills_config", description="Configure a skill's settings")
    @app_commands.checks.has_permissions(administrator=True)
    async def skills_config(self, interaction: discord.Interaction, skill_name: str):
        import yaml
        with open("config/config.yaml", "r") as f:
            config = yaml.safe_load(f)
        port = config.get("dashboard", {}).get("port", 8080)
        await interaction.response.send_message(
            f"⚙️ Configure '{skill_name}' at: http://localhost:{port}/skills",
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(SkillsCog(bot))
