"""
Blaze-Agent Memory Commands
Discord slash commands for memory management.
"""

import discord
from discord import app_commands
from discord.ext import commands
from bot.utils.memory import (
    get_user_memory, clear_user_memory,
    export_memory, get_memory_count
)

class ForgetView(discord.ui.View):
    def __init__(self, guild_id: int, user_id: int):
        super().__init__(timeout=60)
        self.guild_id = guild_id
        self.user_id = user_id

    @discord.ui.button(label="Yes, delete everything", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not your confirmation.", ephemeral=True)
            return
        clear_user_memory(self.guild_id, self.user_id)
        await interaction.response.edit_message(
            content="✅ All your data has been deleted. I will start fresh!",
            embed=None, view=None
        )

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not your confirmation.", ephemeral=True)
            return
        await interaction.response.edit_message(
            content="Cancelled. Your data is safe.",
            embed=None, view=None
        )

class MemoryCog(commands.Cog, name="Memory"):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="memory", description="View what the bot remembers about you")
    async def memory_cmd(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id if interaction.guild else 0
        memory = get_user_memory(guild_id, interaction.user.id)

        if memory:
            lines = []
            for key, value in memory.items():
                display_key = key.replace("_", " ").title()
                lines.append(f"**{display_key}:** {value}")
            text = "\n".join(lines[:25])
            embed = discord.Embed(
                title="🧠 What I Remember About You",
                description=text,
                color=0x5865F2
            )
            embed.set_footer(text="Use /forget to delete all of this.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(
                "I do not have any stored information about you yet. "
                "Talk to me and I will start remembering!",
                ephemeral=True
            )

    @app_commands.command(name="forget", description="Delete all data the bot has about you")
    async def forget_cmd(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id if interaction.guild else 0

        embed = discord.Embed(
            title="⚠️ Confirm Delete",
            description="This will permanently delete everything I know about you. Are you sure?",
            color=0xFF0000
        )

        await interaction.response.send_message(
            embed=embed,
            view=ForgetView(guild_id, interaction.user.id),
            ephemeral=True
        )

    @app_commands.command(name="reset", description="Reset the current conversation")
    async def reset_cmd(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "🔄 Conversation reset. I have forgotten our recent chat. What can I help with?",
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(MemoryCog(bot))
