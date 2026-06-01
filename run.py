"""
Blaze-Agent Entry Point
Run this file to start the bot and dashboard.
"""

import asyncio
import sys
import os
import yaml

def check_setup():
    """Check if setup has been run."""
    if not os.path.exists("config/config.yaml"):
        print("\n  config.yaml not found. Run the setup wizard first:")
        print("  python setup.py\n")
        sys.exit(1)

    with open("config/config.yaml", "r") as f:
        config = yaml.safe_load(f)

    token = config.get("discord", {}).get("token", "")
    if not token or token == "USER_PROVIDED_TOKEN":
        print("\n  No Discord token configured. Run the setup wizard:")
        print("  python setup.py\n")
        sys.exit(1)

async def start_dashboard():
    """Start the web dashboard in the background."""
    import uvicorn
    config = yaml.safe_load(open("config/config.yaml"))
    port = config.get("dashboard", {}).get("port", 8080)
    host = config.get("dashboard", {}).get("host", "127.0.0.1")

    config_obj = uvicorn.Config(
        "dashboard.server:app",
        host=host,
        port=port,
        log_level="warning"
    )
    server = uvicorn.Server(config_obj)
    await server.serve()

async def start_bot():
    """Start the Discord bot."""
    from bot.main import bot, load_config, load_extensions
    config = load_config()
    await load_extensions()
    token = config.get("discord", {}).get("token", "")
    await bot.start(token)

async def main():
    check_setup()

    print("""
  ____  _            _       _____ _
 |  _ \| |          | |     / ____| |
 | |_) | | __ _  __| | __ _| |    | |_
 |  _ <| |/ _` |/ _` |/ _` | |    | __|
 | |_) | | (_| | (_| | (_| | |____| |_
 |____/|_|\__,_|\__,_|\__,_|\______|
  Self-Service AI Discord Agent
    """)

    # Run bot and dashboard concurrently
    await asyncio.gather(
        start_bot(),
        start_dashboard()
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n  BlazeAgent stopped.")
        sys.exit(0)
