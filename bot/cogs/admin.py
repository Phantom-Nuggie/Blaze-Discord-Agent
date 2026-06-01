"""
Blaze-Agent Admin Commands
Discord slash commands for bot administration.
"""

import discord
from discord import app_commands
from discord.ext import commands
from bot.utils.ai import get_usage, check_spend_limit
from bot.utils.soul import load_soul, reload_soul
from bot.utils.memory import get_user_memory, clear_user_memory, export_memory, get_memory_count

class AdminCog(commands.Cog, name="Admin"):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="Show bot commands")
    async def help(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="BlazeAgent Help",
            color=0x5865F2
        )
        embed.add_field(
            name="Public Commands",
            value=(
                "`/help` - Show this message\n"
                "`/status` - Bot status\n"
                "`/speak [msg]` - Talk to the AI\n"
                "`/memory` - View your stored data\n"
                "`/forget` - Delete your data\n"
                "`/contact` - Speak to a human"
            ),
            inline=False
        )

        # Show admin commands only to admins
        if interaction.user.guild_permissions.administrator:
            embed.add_field(
                name="Admin Commands",
                value=(
                    "`/soul` - Edit personality\n"
                    "`/soul reload` - Reload Soul.md\n"
                    "`/stats` - View statistics\n"
                    "`/skills` - View/configure skills\n"
                    "`/cost` - View AI spend\n"
                    "`/pause` / `/resume` - Control bot\n"
                    "`/broadcast [msg]` - Message all users"
                ),
                inline=False
            )

        embed.set_footer(text="Just talk to me naturally anytime!")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="status", description="Check bot status")
    async def status(self, interaction: discord.Interaction):
        import yaml
        with open("config/config.yaml", "r") as f:
            config = yaml.safe_load(f)

        ai_config = config.get("ai", {})
        usage = get_usage("today")

        embed = discord.Embed(title="BlazeAgent Status", color=0x00FF00)
        embed.add_field(name="Status", value="Online ✅", inline=True)
        embed.add_field(name="Model", value=ai_config.get("model", "N/A"), inline=True)
        embed.add_field(name="Messages Today", value=str(usage.get("total_messages", 0)), inline=True)
        embed.add_field(name="Cost Today", value=f"${usage.get('total_cost', 0):.4f}", inline=True)

        limit_status = "✅ OK" if not check_spend_limit() else "⚠️ LIMIT REACHED"
        embed.add_field(name="Spend Limit", value=limit_status, inline=True)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="soul", description="Open the Soul.md editor dashboard")
    @app_commands.checks.has_permissions(administrator=True)
    async def soul(self, interaction: discord.Interaction):
        import yaml
        with open("config/config.yaml", "r") as f:
            config = yaml.safe_load(f)
        port = config.get("dashboard", {}).get("port", 8080)
        await interaction.response.send_message(
            f"📝 Edit your bot's personality here: http://localhost:{port}/soul",
            ephemeral=True
        )

    @app_commands.command(name="soul_reload", description="Reload Soul.md from file")
    @app_commands.checks.has_permissions(administrator=True)
    async def soul_reload(self, interaction: discord.Interaction):
        soul = reload_soul()
        await interaction.response.send_message(
            f"✅ Soul.md reloaded. Sections: {', '.join(soul.keys())}",
            ephemeral=True
        )

    @app_commands.command(name="soul_preview", description="Preview current Soul.md")
    @app_commands.checks.has_permissions(administrator=True)
    async def soul_preview(self, interaction: discord.Interaction):
        soul = load_soul()
        biz = soul.get("business", {})
        identity = soul.get("identity", {})
        faq = soul.get("faq", [])

        lines = [
            f"**Name:** {identity.get('name', 'N/A')}",
            f"**Role:** {identity.get('role', 'N/A')}",
            f"**Personality:** {identity.get('personality', 'N/A')}",
            f"**Business:** {biz.get('business_name', 'N/A')}",
            f"**Location:** {biz.get('location', 'N/A')}",
            f"**Hours:** {biz.get('hours', 'N/A')}",
            f"**FAQ Entries:** {len(faq)}",
            f"**Capabilities:** {', '.join(soul.get('capabilities', [])) or 'None'}",
        ]
        await interaction.response.send_message(
            "\n".join(lines),
            ephemeral=True
        )

    @app_commands.command(name="stats", description="View today's statistics")
    @app_commands.checks.has_permissions(administrator=True)
    async def stats(self, interaction: discord.Interaction):
        usage = get_usage("today")
        memory_count = get_memory_count()

        import yaml
        with open("config/config.yaml", "r") as f:
            config = yaml.safe_load(f)
        ai_config = config.get("ai", {})

        embed = discord.Embed(title="📊 BlazeAgent Stats (Today)", color=0x5865F2)
        embed.add_field(name="Messages", value=str(usage.get("total_messages", 0)), inline=True)
        embed.add_field(name="AI Cost", value=f"${usage.get('total_cost', 0):.4f}", inline=True)
        embed.add_field(name="Memory Entries", value=str(memory_count), inline=True)
        embed.add_field(name="Daily Limit", value=f"${ai_config.get('daily_spend_limit', 0)}", inline=True)
        embed.add_field(name="Monthly Limit", value=f"${ai_config.get('monthly_spend_limit', 0)}", inline=True)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="skills", description="View all skills and status")
    @app_commands.checks.has_permissions(administrator=True)
    async def skills(self, interaction: discord.Interaction):
        from bot.utils.skills import get_skills_status
        skills = get_skills_status()

        lines = []
        for name, enabled in skills.items():
            status = "✅" if enabled else "❌"
            lines.append(f"{status} **{name.replace('_', ' ').title()}**")

        embed = discord.Embed(
            title="🔧 Skills Status",
            description="\n".join(lines) or "No skills configured",
            color=0x5865F2
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="skills_enable", description="Enable a skill")
    @app_commands.checks.has_permissions(administrator=True)
    async def skills_enable(self, interaction: discord.Interaction, skill_name: str):
        from bot.utils.skills import set_skill
        valid_skills = ["faq", "order_taking", "booking", "lead_capture", "file_creation", "complaint_handler", "language_detection"]
        if skill_name not in valid_skills:
            await interaction.response.send_message(
                f"❌ Invalid skill. Valid: {', '.join(valid_skills)}",
                ephemeral=True
            )
            return
        set_skill(skill_name, True)
        await interaction.response.send_message(
            f"✅ Skill '{skill_name.replace('_', ' ').title()}' enabled.",
            ephemeral=True
        )

    @app_commands.command(name="skills_disable", description="Disable a skill")
    @app_commands.checks.has_permissions(administrator=True)
    async def skills_disable(self, interaction: discord.Interaction, skill_name: str):
        from bot.utils.skills import set_skill
        valid_skills = ["faq", "order_taking", "booking", "lead_capture", "file_creation", "complaint_handler", "language_detection"]
        if skill_name not in valid_skills:
            await interaction.response.send_message(
                f"❌ Invalid skill. Valid: {', '.join(valid_skills)}",
                ephemeral=True
            )
            return
        set_skill(skill_name, False)
        await interaction.response.send_message(
            f"❌ Skill '{skill_name.replace('_', ' ').title()}' disabled.",
            ephemeral=True
        )

    @app_commands.command(name="pause", description="Pause the bot from responding")
    @app_commands.checks.has_permissions(administrator=True)
    async def pause(self, interaction: discord.Interaction):
        self.bot._paused = True
        await interaction.response.send_message("⏸️ Bot paused. Use /resume to continue.", ephemeral=True)

    @app_commands.command(name="resume", description="Resume bot responses")
    @app_commands.checks.has_permissions(administrator=True)
    async def resume(self, interaction: discord.Interaction):
        self.bot._paused = False
        await interaction.response.send_message("▶️ Bot resumed.", ephemeral=True)

    @app_commands.command(name="cost", description="View AI spend for today")
    @app_commands.checks.has_permissions(administrator=True)
    async def cost(self, interaction: discord.Interaction):
        import yaml
        with open("config/config.yaml", "r") as f:
            config = yaml.safe_load(f)
        ai_config = config.get("ai", {})
        usage = get_usage("today")

        embed = discord.Embed(title="💰 AI Spend (Today)", color=0xFFCC00)
        embed.add_field(name="Spent", value=f"${usage.get('total_cost', 0):.4f}", inline=True)
        embed.add_field(name="Daily Limit", value=f"${ai_config.get('daily_spend_limit', 0)}", inline=True)
        embed.add_field(name="Monthly Limit", value=f"${ai_config.get('monthly_spend_limit', 0)}", inline=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="memory_view", description="View memory for a user")
    @app_commands.checks.has_permissions(administrator=True)
    async def memory_view(self, interaction: discord.Interaction, user: discord.Member):
        memory = get_user_memory(interaction.guild.id, user.id)
        if memory:
            lines = [f"**{k.replace('_', ' ').title()}:** {v}" for k, v in memory.items()]
            text = "\n".join(lines[:20])
        else:
            text = "No stored memory for this user."
        await interaction.response.send_message(text, ephemeral=True)

    @app_commands.command(name="memory_clear", description="Clear memory for a user")
    @app_commands.checks.has_permissions(administrator=True)
    async def memory_clear(self, interaction: discord.Interaction, user: discord.Member):
        clear_user_memory(interaction.guild.id, user.id)
        await interaction.response.send_message(
            f"🗑️ Memory cleared for {user.display_name}.",
            ephemeral=True
        )

    @app_commands.command(name="broadcast", description="Send a message to all users who interacted with the bot")
    @app_commands.checks.has_permissions(administrator=True)
    async def broadcast(self, interaction: discord.Interaction, message: str):
        await interaction.response.send_message(
            f"📢 Broadcasting: {message}\n(Feature coming in next update)",
            ephemeral=True
        )

    @app_commands.command(name="restart", description="Restart the bot")
    @app_commands.checks.has_permissions(administrator=True)
    async def restart(self, interaction: discord.Interaction):
        await interaction.response.send_message("🔄 Restarting... (this takes a few seconds)", ephemeral=True)
        import os, sys
        os.execv(sys.executable, [sys.executable] + sys.argv)

async def setup(bot):
    """Add the cog to the bot."""
    await bot.add_cog(AdminCog(bot))
