# Blaze-Discord-Agent 🔥

### Your Business Deserves an AI Employee That Never Sleeps

Stop losing customers to slow responses. Stop answering the same questions 50 times a day. **Blaze-Discord-Agent** puts a smart, tireless AI assistant right inside your Discord server — and it runs on YOUR machine, with YOUR API keys, under YOUR control.

> **You bring:** A Discord bot token + an AI API key
> **We provide:** Everything else. The bot, the brain, the dashboard, the magic.
> **Zero ongoing costs.** We host nothing. We see nothing. We take nothing.

---

## ⚡ Install in 30 Seconds

### One-liner (Linux/Mac)

```bash
curl -fsSL https://raw.githubusercontent.com/Phantom-Nuggie/Blaze-Discord-Agent/main/install_blazeagent.py | python3
```

That's it. Seriously. The installer handles everything — download, setup, dependencies, the works. Go grab a coffee. ☕

### Windows / Manual

```bash
# Download the installer
curl -fsSL -o install_blazeagent.py https://raw.githubusercontent.com/Phantom-Nuggie/Blaze-Discord-Agent/main/install_blazeagent.py

# Run it
python install_blazeagent.py
```

---

## 🚀 Get Running

After install, you get a brand new terminal command: **`blzed`**

```bash
blzed setup      # Configure your bot (Discord token, AI key, personality)
blzed start      # Fire it up 🔥
blzed status     # Check everything's healthy
```

**Three commands. Your bot is live.** 🎉

---

## 🛠️ The blzed CLI — Your New Best Friend

Blaze-Agent installs a system-wide `blzed` command. Here's everything it does:

| Command | What it does |
|---------|-------------|
| `blzed` or `blzed start` | Start the bot and web dashboard |
| `blzed status` | Show version, config status, and whether an update is available |
| `blzed update` | Downloads the latest version, preserves your config, reinstall deps |
| `blzed setup` | Run the configuration wizard |
| `blzed version` | Show installed version |
| `blzed uninstall` | Remove Blaze-Agent completely |
| `blzed help` | Show all commands |

### Updating is painless ✨

```bash
blzed update
```

Downloads the latest release, merges the new code, **keeps your config and data safe**, reinstalls dependencies. Done. No reconfiguration needed.

---

## 🎯 What Can It Do?

- 💬 **AI Chat** — Natural conversation powered by YOUR chosen AI model
- 🧠 **Soul.md** — Give your bot a personality, business info, and knowledge (edit from the dashboard)
- 💾 **Memory** — Remembers each customer's name, preferences, and history
- 📋 **FAQ** — Answers questions from your knowledge base instantly (no AI cost for known answers)
- 🛒 **Order Taking** — Guides customers through placing orders step by step
- 📅 **Booking** — Handles appointment scheduling
- 📧 **Lead Capture** — Collects customer contact info automatically
- 📄 **File Creation** — Generates invoices, receipts, menus as PDFs
- 😤 **Complaint Handler** — Detects upset customers and escalates appropriately
- 💰 **Spend Limits** — Daily and monthly AI budget caps so you never get surprised
- 🔀 **Multi-Provider** — Works with OpenRouter, OpenAI, Anthropic, Google, or Ollama (local, free)
- 🌐 **Web Dashboard** — Manage everything from `http://localhost:8080`

---

## 🤖 Discord Commands

| Command | Access | Description |
|---------|--------|-------------|
| `/help` | Everyone | Show available commands |
| `/status` | Everyone | Bot status and stats |
| `/memory` | Everyone | View what the bot knows about you |
| `/forget` | Everyone | Delete your stored data |
| `/contact` | Everyone | Escalate to a human |
| `/pause` | Admin | Stop bot from responding |
| `/resume` | Admin | Resume bot |
| `/stats` | Admin | View detailed statistics |
| `/soul` | Admin | Open Soul.md editor |
| `/skills` | Admin | View/enable/disable skills |
| `/cost` | Admin | View AI spend |
| `/restart` | Admin | Restart the bot |

---

## 🌐 Dashboard

Runs at `http://localhost:8080` by default.

- **Home** — Bot status, today's stats, quick links
- **Soul Editor** — Edit personality and knowledge (changes apply instantly)
- **Memory** — See what the bot has learned about each customer
- **Skills** — Enable/disable bot capabilities
- **Files** — Manage generated documents
- **Settings** — Change AI model, spend limits, bot name, personality

---

## 📦 What's Inside

```
Blaze-Agent/
├── .venv/                  # Python virtual environment
├── bot/
│   ├── main.py             # Bot entry point
│   ├── cogs/               # Discord command modules
│   └── utils/              # AI, memory, skills, Soul.md engine
├── config/
│   ├── config.yaml         # Your configuration (preserved on update)
│   ├── soul.md             # Bot personality (preserved on update)
│   └── skills.yaml         # Skills config (preserved on update)
├── dashboard/
│   ├── server.py           # Web dashboard (FastAPI)
│   └── templates/          # Dashboard HTML pages
├── storage/
│   ├── database.sqlite     # Conversations, memory, usage stats
│   └── files/              # Generated PDFs, docs, etc.
├── templates/              # Bot response templates
├── template_skins/         # UI skin templates
├── install_blazeagent.py   # The installer
├── setup.py                # Configuration wizard
├── run.py                  # Start bot + dashboard
├── requirements.txt        # Python dependencies
├── VERSION                 # Current version tracker
├── start.sh                # Quick launcher (Linux/Mac)
└── start.bat               # Quick launcher (Windows)
```

---

## ✅ Requirements

- **Python 3.10+**
- **A Discord account** (to create a bot — free)
- **An AI API key** (pick one):
  - **OpenRouter** (recommended): https://openrouter.ai/keys
  - OpenAI: https://platform.openai.com/api-keys
  - Anthropic: https://console.anthropic.com/settings/keys
  - Google Gemini: https://aistudio.google.com/app/apikey
  - Ollama (local, no key needed): https://ollama.com

---

## 🔧 Creating a Discord Bot

1. Go to https://discord.com/developers/applications
2. Click **"New Application"** — give it a name
3. Click **"Bot"** in the left sidebar
4. Click **"Add Bot"**
5. Under **"Privileged Gateway Intents"**, turn ON:
   - MESSAGE CONTENT INTENT
   - SERVER MEMBERS INTENT
   - PRESENCE INTENT
6. Click **"Reset Token"** and copy it
7. Run `blzed setup` — it builds the invite link for you

---

## 🔄 Updating

```bash
blzed update
```

That's it. Your config, data, and customizations are preserved. Always.

---

## 🗑️ Uninstalling

```bash
blzed uninstall
```

Removes everything — the project, the `blzed` command, the PATH entry. Clean.

---

## 📜 License

MIT
