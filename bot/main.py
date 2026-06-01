"""
Blaze-Agent: Self-service AI Discord Agent
https://github.com/zerochunks/Blaze-Agent
"""

import discord
from discord.ext import commands
import asyncio
import yaml
import os
import sys
import logging
from datetime import datetime

# Setup logging
os.makedirs("storage/logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(f"storage/logs/blaze_{datetime.now().strftime('%Y%m%d')}.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("BlazeAgent")

# Load config
def load_config():
    config_path = os.path.join("config", "config.yaml")
    if not os.path.exists(config_path):
        logger.error("config.yaml not found. Run 'python setup.py' first.")
        sys.exit(1)
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

config = load_config()

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True

bot = commands.Bot(
    command_prefix=config.get("discord", {}).get("prefix", "!"),
    intents=intents,
    help_command=None
)

# Bot state
bot._paused = False

# Track startup time
start_time = datetime.now()

@bot.event
async def on_ready():
    logger.info(f"Connected as {bot.user} (ID: {bot.user.id})")
    logger.info(f"Connected to {len(bot.guilds)} server(s)")
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name=f"/help | {config.get('bot', {}).get('name', 'BlazeAgent')}"
        )
    )
    # Send onboarding message to admin channel if configured
    admin_channel_id = config.get("channels", {}).get("admin_channel", "")
    if admin_channel_id:
        try:
            channel = bot.get_channel(int(admin_channel_id))
            if channel:
                embed = discord.Embed(
                    title="BlazeAgent Online",
                    description=(
                        f"**{config.get('bot', {}).get('name', 'BlazeAgent')}** is now running.\n\n"
                        "Commands:\n"
                        "`/help` - See all commands\n"
                        "`/soul` - Edit personality & knowledge\n"
                        "`/skills` - Configure capabilities\n"
                        "`/stats` - View performance\n\n"
                        f"Dashboard: http://localhost:{config.get('dashboard', {}).get('port', 8080)}\n"
                        "Check your Soul.md and customize my knowledge!"
                    ),
                    color=0x5865F2
                )
                await channel.send(embed=embed)
                logger.info(f"Onboarding message sent to admin channel {admin_channel_id}")
        except Exception as e:
            logger.warning(f"Could not send onboarding message: {e}")

@bot.event
async def on_message(message):
    # Ignore bot messages
    if message.author.bot:
        return

    # Process commands first
    await bot.process_commands(message)

    # Check if bot is paused
    if getattr(bot, "_paused", False):
        return

    # Check channel restriction
    channel_mode = config.get("channels", {}).get("mode", "all")
    allowed_channels = config.get("channels", {}).get("allowed", [])
    if channel_mode == "specific" and allowed_channels:
        if str(message.channel.id) not in [str(c) for c in allowed_channels]:
            return

    # Check if bot should respond
    should_respond = False

    # Bot was mentioned
    if bot.user in message.mentions:
        should_respond = True

    # Message is in a DM
    if isinstance(message.channel, discord.DMChannel):
        should_respond = True

    if should_respond:
        # Remove the mention from the message content
        content = message.content.replace(f"<@{bot.user.id}>", "").replace(f"<@!{bot.user.id}>", "").strip()
        if not content:
            content = "Hello!"

        # Check AI spend limits
        from bot.utils.ai import check_spend_limit, track_usage
        if check_spend_limit():
            await message.reply("AI quota exceeded for today. Please check your spend limits in the dashboard.")
            return

        # Load Soul.md
        from bot.utils.soul import load_soul
        soul = load_soul()

        # Get user memory
        from bot.utils.memory import get_user_memory
        user_memory = get_user_memory(message.guild.id if message.guild else 0, message.author.id)

        # Check skills first
        from bot.utils.skills import check_skills
        skill_response, handled = await check_skills(content, soul, message)
        if handled and skill_response:
            await message.reply(skill_response)
            return

        # Build system prompt
        from bot.utils.prompt import build_system_prompt
        system_prompt = build_system_prompt(soul, user_memory, message.author.name)

        # Get AI response
        from bot.utils.ai import get_ai_response
        async with message.channel.typing():
            try:
                response = await get_ai_response(system_prompt, content)
                # Track usage
                track_usage()
                # Send response (split if too long)
                if len(response) > 2000:
                    chunks = [response[i:i+1990] for i in range(0, len(response), 1990)]
                    for chunk in chunks:
                        await message.reply(chunk)
                else:
                    await message.reply(response)

                # Extract memory from conversation
                from bot.utils.memory import extract_memory
                await extract_memory(
                    message.guild.id if message.guild else 0,
                    message.author.id,
                    content,
                    response
                )
            except Exception as e:
                logger.error(f"AI response error: {e}")
                await message.reply("Something went wrong. Please try again or contact the admin.")

async def load_extensions():
    """Load all cog extensions."""
    cogs = [
        "bot.cogs.admin",
        "bot.cogs.memory_cmd",
        "bot.cogs.soul_cmd",
        "bot.cogs.skills_cmd",
        "bot.cogs.files_cog",
    ]
    for cog in cogs:
        try:
            await bot.load_extension(cog)
            logger.info(f"Loaded cog: {cog}")
        except Exception as e:
            logger.error(f"Failed to load cog {cog}: {e}")

async def main():
    async with bot:
        await load_extensions()
        token = config.get("discord", {}).get("token", "")
        if not token or token == "USER_PROVIDED_TOKEN":
            logger.error("No Discord token found. Run 'python setup.py' first.")
            sys.exit(1)
        await bot.start(token)

if __name__ == "__main__":
    asyncio.run(main())
