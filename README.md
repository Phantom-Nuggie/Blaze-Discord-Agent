# Blaze-Discord-Agent

Self-service AI Discord agent. Your bot, your server, your API keys.

## What It Is

Blaze-Discord-Agent gives you an AI-powered Discord bot for your business. The bot answers FAQs, takes orders, books appointments, remembers customer preferences, generates files, and more.

**You bring:** A Discord bot token + an AI API key (OpenRouter, OpenAI, Anthropic, Google, or Ollama for local)

**We provide:** The entire bot software, a setup wizard, and a web dashboard

**Everything runs on YOUR machine.** We host nothing, see nothing, pay for nothing.

## Quick Install

### Option 1: One-line install (Linux/Mac)

```bash
curl -fsSL https://github.com/Phantom-Nuggie/Blaze-Discord-Agent/releases/latest/download/install_blazeagent.py | python3
```

Or download and run manually:

```bash
curl -fsSL -o install_blazeagent.py https://github.com/Phantom-Nuggie/Blaze-Discord-Agent/releases/latest/download/install_blazeagent.py
python3 install_blazeagent.py
```

### Option 2: Manual install

```bash
git clone https://github.com/Phantom-Nuggie/Blaze-Discord-Agent.git
cd Blaze-Discord-Agent
python3 -m venv .venv
source .venv/bin/activate   # Linux/Mac
# OR: .venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

## First Run

### Step 1: Run the setup wizard

```bash
python setup.py
```

The wizard will guide you through:
- Creating a Discord bot
- Entering your AI API key
- Choosing your business type
- Configuring personality and settings

### Step 2: Start the bot

```bash
python run.py
```

That is it. Your bot is online.

### Step 3: Customize

Open the dashboard at `http://localhost:8080` to edit your bot's Soul.md -- its personality, business info, knowledge base, and behavior rules.

## Requirements

- Python 3.10+
- A Discord account (to create a bot)
- An AI API key:
  - **OpenRouter** (recommended): https://openrouter.ai/keys
  - OpenAI: https://platform.openai.com/api-keys
  - Anthropic: https://console.anthropic.com/settings/keys
  - Google Gemini: https://aistudio.google.com/app/apikey
  - Ollama (local, no key needed): https://ollama.com

##Creating a Discord Bot

1. Go to https://discord.com/developers/applications
2. Click "New Application" -- give it a name
3. Click "Bot" in the left sidebar
4. Click "Add Bot"
5. Under "Privileged Gateway Intents", turn ON:
   - MESSAGE CONTENT INTENT
   - SERVER MEMBERS INTENT
   - PRESENCE INTENT
6. Click "Reset Token" and copy it
7. The setup wizard will build an invite link for you

## Features

- **AI Chat** -- Natural conversation powered by your chosen AI model
- **Soul.md** -- Edit your bot's personality, business info, and knowledge from the dashboard
- **Memory** -- The bot remembers each customer's name, preferences, and history
- **FAQ** -- Answers questions from your knowledge base (no AI cost for known questions)
- **Order Taking** -- Guides customers through placing orders
- **Booking** -- Handles appointment scheduling
- **Lead Capture** -- Collects customer contact info
- **File Creation** -- Generates invoices, receipts, menus, and more as PDFs
- **Complaint Handler** -- Detects upset customers and escalates appropriately
- **Spend Limits** -- Daily and monthly AI budget caps to prevent overages
- **Multi-Provider** -- Works with OpenRouter, OpenAI, Anthropic, Google, or Ollama
- **Dashboard** -- Web-based management at localhost:8080

## Commands

| Command | Access | Description |
|---------|--------|-------------|
| /help | Everyone | Show available commands |
| /status | Everyone | Bot status and stats |
| /memory | Everyone | View what the bot knows about you |
| /forget | Everyone | Delete your stored data |
| /contact | Everyone | Escalate to a human |
| /pause | Admin | Stop bot from responding |
| /resume | Admin | Resume bot |
| /stats | Admin | View detailed statistics |
| /soul | Admin | Open Soul.md editor |
| /skills | Admin | View/enable/disable skills |
| /cost | Admin | View AI spend |
| /restart | Admin | Restart the bot |

## Dashboard

The dashboard runs on localhost:8080 by default.

- **Home** -- Bot status, today's stats, quick links
- **Soul Editor** -- Edit your bot's personality and knowledge (changes apply immediately)
- **Memory** -- View what the bot has learned about each customer
- **Skills** -- Enable/disable bot capabilities
- **Files** -- Manage generated documents
- **Settings** -- Change AI model, spend limits, bot name, personality

## Spending Limits

Set daily and monthly AI spend limits in the setup wizard. The bot will pause AI responses when limits are hit. Configurable per server from the dashboard.

## Folder Structure

```
Blaze-Agent/
├── install_blazeagent.py   # Installer script
├── setup.py                # Setup wizard
├── run.py                  # Start the bot + dashboard
├── requirements.txt        # Python dependencies
├── config/
│   ├── config.yaml         # Main configuration
│   ├── soul.md             # Bot personality and knowledge
│   └── skills.yaml         # Skills configuration
├── bot/
│   ├── main.py             # Bot entry point
│   ├── cogs/               # Discord command modules
│   └── utils/              # AI, memory, skills, Soul.md
├── dashboard/
│   ├── server.py           # Web dashboard server
│   └── templates/          # Dashboard HTML pages
└── storage/
    ├── database.sqlite     # Conversations, memory, usage stats
    ├── files/              # Generated files (PDFs, docs, etc.)
    └── logs/               # Log files
```

## License

MIT
