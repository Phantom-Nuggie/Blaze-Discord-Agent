"""
Blaze-Agent AI Caller
Handles AI API calls across multiple providers.
"""

import aiohttp
import asyncio
import yaml
import os
import sqlite3
from datetime import datetime

def get_config():
    with open("config/config.yaml", "r") as f:
        return yaml.safe_load(f)

def get_db():
    conn = sqlite3.connect("storage/database.sqlite")
    conn.row_factory = sqlite3.Row
    return conn

def check_spend_limit() -> bool:
    """Check if daily or monthly spend limit is exceeded.
    Returns True if limit exceeded (should block), False if OK."""
    config = get_config()
    limits = config.get("ai", {})
    daily_limit = limits.get("daily_spend_limit", 2.0)
    monthly_limit = limits.get("monthly_spend_limit", 10.0)

    conn = get_db()
    c = conn.cursor()

    # Check daily
    today = datetime.now().strftime("%Y-%m-%d")
    c.execute("SELECT total_cost FROM usage_stats WHERE date = ?", (today,))
    row = c.fetchone()
    daily_cost = row["total_cost"] if row else 0.0

    if daily_cost >= daily_limit:
        conn.close()
        return True

    # Check monthly
    month = datetime.now().strftime("%Y-%m")
    c.execute(
        "SELECT SUM(total_cost) as total FROM usage_stats WHERE date LIKE ?",
        (f"{month}%",)
    )
    row = c.fetchone()
    monthly_cost = row["total"] if row and row["total"] else 0.0

    conn.close()
    if monthly_cost >= monthly_limit:
        return True

    return False

def track_usage(tokens: int = 100, cost: float = 0.0):
    """Track API usage in the database."""
    conn = get_db()
    c = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")

    c.execute("""
        INSERT INTO usage_stats (date, total_messages, total_tokens, total_cost)
        VALUES (?, 1, ?, ?)
        ON CONFLICT(date) DO UPDATE SET
            total_messages = total_messages + 1,
            total_tokens = total_tokens + ?,
            total_cost = total_cost + ?
    """, (today, tokens, cost, tokens, cost))

    conn.commit()
    conn.close()

def get_usage(period: str = "today") -> dict:
    """Get usage statistics."""
    conn = get_db()
    c = conn.cursor()

    if period == "today":
        date = datetime.now().strftime("%Y-%m-%d")
        c.execute("SELECT * FROM usage_stats WHERE date = ?", (date,))
        row = c.fetchone()
    elif period == "month":
        month = datetime.now().strftime("%Y-%m")
        c.execute("""
            SELECT
                SUM(total_messages) as total_messages,
                SUM(total_tokens) as total_tokens,
                SUM(total_cost) as total_cost
            FROM usage_stats WHERE date LIKE ?
        """, (f"{month}%",))
        row = c.fetchone()
    elif period == "week":
        # Last 7 days
        c.execute("""
            SELECT
                SUM(total_messages) as total_messages,
                SUM(total_tokens) as total_tokens,
                SUM(total_cost) as total_cost
            FROM usage_stats
            WHERE date >= date('now', '-7 days')
        """)
        row = c.fetchone()
    else:
        c.execute("SELECT * FROM usage_stats ORDER BY date DESC LIMIT 1")
        row = c.fetchone()

    conn.close()
    if row:
        return dict(row)
    return {"total_messages": 0, "total_tokens": 0, "total_cost": 0.0}

async def get_ai_response(system_prompt: str, user_message: str, conversation_history: list = None) -> str:
    """Get a response from the configured AI provider."""
    config = get_config()
    ai_config = config.get("ai", {})
    provider = ai_config.get("provider", "openrouter")
    api_key = ai_config.get("api_key", "")
    model = ai_config.get("model", "anthropic/claude-haiku-3.5")
    max_tokens = ai_config.get("max_tokens", 1000)

    messages = [{"role": "system", "content": system_prompt}]

    # Add conversation history if provided
    if conversation_history:
        messages.extend(conversation_history)

    messages.append({"role": "user", "content": user_message})

    try:
        if provider == "openrouter":
            return await _call_openrouter(api_key, model, messages, max_tokens)
        elif provider == "openai":
            return await _call_openai(api_key, model, messages, max_tokens)
        elif provider == "anthropic":
            return await _call_anthropic(api_key, model, messages, max_tokens)
        elif provider == "google":
            return await _call_google(api_key, model, messages, max_tokens)
        elif provider == "ollama":
            return await _call_ollama(model, messages)
        else:
            return "AI provider not configured correctly. Check config.yaml."
    except asyncio.TimeoutError:
        return "The AI is taking too long to respond. Please try again."
    except Exception as e:
        return f"I am having trouble connecting right now. Please try again in a moment."

async def _call_openrouter(api_key: str, model: str, messages: list, max_tokens: int) -> str:
    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens
        }
        async with session.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=aiohttp.ClientTimeout(total=30)
        ) as resp:
            if resp.status == 200:
                result = await resp.json()
                return result["choices"][0]["message"]["content"]
            else:
                error_text = await resp.text()
                return f"AI error (status {resp.status}). Please check your API key and model."

async def _call_openai(api_key: str, model: str, messages: list, max_tokens: int) -> str:
    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens
        }
        async with session.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=aiohttp.ClientTimeout(total=30)
        ) as resp:
            if resp.status == 200:
                result = await resp.json()
                return result["choices"][0]["message"]["content"]
            else:
                return f"OpenAI error (status {resp.status}). Please check your API key."

async def _call_anthropic(api_key: str, model: str, messages: list, max_tokens: int) -> str:
    # Anthropic uses a different format
    system_msg = ""
    user_messages = []
    for m in messages:
        if m["role"] == "system":
            system_msg = m["content"]
        else:
            user_messages.append(m)

    async with aiohttp.ClientSession() as session:
        headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        data = {
            "model": model,
            "max_tokens": max_tokens,
            "system": system_msg,
            "messages": user_messages
        }
        async with session.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=data,
            timeout=aiohttp.ClientTimeout(total=30)
        ) as resp:
            if resp.status == 200:
                result = await resp.json()
                return result["content"][0]["text"]
            else:
                return f"Anthropic error (status {resp.status}). Please check your API key."

async def _call_google(api_key: str, model: str, messages: list, max_tokens: int) -> str:
    # Google Gemini API
    google_model = model.replace("google/", "")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{google_model}:generateContent?key={api_key}"

    # Convert messages to Gemini format
    contents = []
    for m in messages:
        if m["role"] == "system":
            sys_text = m["content"]
            contents.append({"role": "user", "parts": [{"text": f"System: {sys_text}"}]})
        else:
            role = "user" if m["role"] == "user" else "model"
            contents.append({"role": role, "parts": [{"text": m["content"]}]})

    async with aiohttp.ClientSession() as session:
        data = {"contents": contents}
        async with session.post(
            url,
            json=data,
            timeout=aiohttp.ClientTimeout(total=30)
        ) as resp:
            if resp.status == 200:
                result = await resp.json()
                return result["candidates"][0]["content"]["parts"][0]["text"]
            else:
                return f"Google error (status {resp.status}). Please check your API key."

async def _call_ollama(model: str, messages: list) -> str:
    ollama_messages = []
    for m in messages:
        role = m["role"]
        if role == "system":
            ollama_messages.append({"role": "system", "content": m["content"]})
        else:
            ollama_messages.append({"role": m["role"], "content": m["content"]})

    async with aiohttp.ClientSession() as session:
        data = {
            "model": model,
            "messages": ollama_messages,
            "stream": False
        }
        async with session.post(
            "http://localhost:11434/api/chat",
            json=data,
            timeout=aiohttp.ClientTimeout(total=60)
        ) as resp:
            if resp.status == 200:
                result = await resp.json()
                return result["message"]["content"]
            else:
                return f"Ollama error (status {resp.status}). Is Ollama running?"

async def simple_ai_call(prompt: str, system: str = "") -> str:
    """Simple one-shot AI call. Used for memory extraction etc."""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    return await get_ai_response(system or "You are a helpful assistant.", prompt, [])
