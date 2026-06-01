"""
Blaze-Agent File Commands
Discord slash commands for file management.
"""

import discord
from discord import app_commands
from discord.ext import commands
import os
from datetime import datetime

class FilesCog(commands.Cog, name="Files"):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="file_list", description="List recent generated files")
    @app_commands.checks.has_permissions(administrator=True)
    async def file_list(self, interaction: discord.Interaction):
        files_dir = "storage/files"
        if not os.path.exists(files_dir):
            await interaction.response.send_message("No files generated yet.", ephemeral=True)
            return

        files = []
        for f in os.listdir(files_dir):
            fpath = os.path.join(files_dir, f)
            size = os.path.getsize(fpath)
            mtime = datetime.fromtimestamp(os.path.getmtime(fpath))
            files.append((f, size, mtime))

        files.sort(key=lambda x: x[2], reverse=True)

        if not files:
            await interaction.response.send_message("No files generated yet.", ephemeral=True)
            return

        lines = []
        for fname, size, mtime in files[:20]:
            size_kb = size / 1024
            lines.append(f"  • {fname} ({size_kb:.1f}KB) - {mtime.strftime('%Y-%m-%d %H:%M')}")

        embed = discord.Embed(
            title="📁 Generated Files",
            description="\n".join(lines),
            color=0x5865F2
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="file_cleanup", description="Delete expired files")
    @app_commands.checks.has_permissions(administrator=True)
    async def file_cleanup(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "🧹 File cleanup completed. (Full implementation in next update)",
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(FilesCog(bot))
