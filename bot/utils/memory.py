"""
Blaze-Agent Memory System
Stores and retrieves per-user memory using SQLite.
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Optional

DB_PATH = "storage/database.sqlite"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_user_memory(guild_id: int, user_id: int) -> dict:
    """Get all memories for a specific user in a server."""
    config = _get_config()
    retention_days = config.get("memory", {}).get("retention_days", 90)
    max_entries = config.get("memory", {}).get("max_per_user", 50)

    cutoff = (datetime.now() - timedelta(days=retention_days)).isoformat()

    conn = get_db()
    c = conn.cursor()

    # Clean expired memories first
    c.execute(
        "DELETE FROM memories WHERE guild_id = ? AND user_id = ? AND updated_at < ?",
        (str(guild_id), str(user_id), cutoff)
    )
    conn.commit()

    # Fetch memories
    c.execute(
        "SELECT key, value, updated_at FROM memories WHERE guild_id = ? AND user_id = ? ORDER BY updated_at DESC LIMIT ?",
        (str(guild_id), str(user_id), max_entries)
    )
    rows = c.fetchall()
    conn.close()

    memory = {}
    for row in rows:
        memory[row["key"]] = row["value"]

    return memory

def set_memory(guild_id: int, user_id: int, key: str, value: str):
    """Set a specific memory key for a user."""
    conn = get_db()
    c = conn.cursor()

    c.execute("""
        INSERT INTO memories (guild_id, user_id, key, value, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(guild_id, user_id, key) DO UPDATE SET
            value = excluded.value,
            updated_at = excluded.updated_at
    """, (str(guild_id), str(user_id), key, value, datetime.now(), datetime.now()))

    conn.commit()
    conn.close()

def delete_memory(guild_id: int, user_id: int, key: str):
    """Delete a specific memory key."""
    conn = get_db()
    c = conn.cursor()
    c.execute(
        "DELETE FROM memories WHERE guild_id = ? AND user_id = ? AND key = ?",
        (str(guild_id), str(user_id), key)
    )
    conn.commit()
    conn.close()

def clear_user_memory(guild_id: int, user_id: int):
    """Wipe ALL memory for a user."""
    conn = get_db()
    c = conn.cursor()
    c.execute(
        "DELETE FROM memories WHERE guild_id = ? AND user_id = ?",
        (str(guild_id), str(user_id))
    )
    conn.commit()
    conn.close()

def export_memory(guild_id: int) -> str:
    """Export all memory for a server as JSON."""
    conn = get_db()
    c = conn.cursor()
    c.execute(
        "SELECT user_id, key, value, created_at, updated_at FROM memories WHERE guild_id = ?",
        (str(guild_id),)
    )
    rows = c.fetchall()
    conn.close()

    data = []
    for row in rows:
        data.append({
            "user_id": row["user_id"],
            "key": row["key"],
            "value": row["value"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"]
        })

    return json.dumps(data, indent=2)

async def extract_memory(guild_id: int, user_id: int, user_message: str, bot_response: str):
    """Use AI to extract useful memory from a conversation turn.
    This runs after each message to auto-learn about the user."""
    try:
        from bot.utils.ai import simple_ai_call

        prompt = f"""A customer sent this message: "{user_message}"

Based on this message, extract any useful personal information about the customer that should be remembered for future conversations.

Look for:
- Their name
- Preferences (likes, dislikes)
- Contact details
- Dietary restrictions / allergies
- Past orders or interests
- Any other memorable personal details

If there is nothing worth remembering, respond with: NONE

If there IS something to remember, respond with ONLY key-value pairs, one per line, like:
name: John
prefers: vegetarian
allergic_to: nuts"""

        result = await simple_ai_call(prompt, "You are a memory extraction assistant. Only extract explicitly stated facts.")

        if result and result.strip().upper() != "NONE":
            lines = result.strip().split("\n")
            for line in lines:
                if ":" in line:
                    key, _, value = line.partition(":")
                    key = key.strip().lower().replace(" ", "_")
                    value = value.strip()
                    if key and value and len(key) < 50 and len(value) < 200:
                        set_memory(guild_id, user_id, key, value)
    except Exception:
        # Silent fail -- memory extraction should never break the bot
        pass

def get_memory_count(guild_id: int = None) -> int:
    """Get total memory count, optionally filtered by server."""
    conn = get_db()
    c = conn.cursor()
    if guild_id:
        c.execute("SELECT COUNT(*) as cnt FROM memories WHERE guild_id = ?", (str(guild_id),))
    else:
        c.execute("SELECT COUNT(*) as cnt FROM memories")
    row = c.fetchone()
    conn.close()
    return row["cnt"] if row else 0

def _get_config():
    import yaml
    with open("config/config.yaml", "r") as f:
        return yaml.safe_load(f)
