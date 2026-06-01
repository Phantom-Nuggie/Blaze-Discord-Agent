"""
Blaze-Agent Setup Wizard
Interactive terminal wizard to set up a BlazeAgent instance.
"""

import os
import sys
import subprocess
import yaml
import base64
import json
import random
import string
import aiohttp
import asyncio

def check_prerequisites():
    """Step 0: Check Python, create venv, install deps."""
    print(f"\n{BOLD}{CYAN}{'='*50}{RESET}")
    print(f"{BOLD}{CYAN}  CHECKING PREREQUISITES{RESET}")
    print(f"{BOLD}{CYAN}{'='*50}{RESET}\n")

    # Check Python version
    version = sys.version_info[:2]
    if version < (3, 10):
        fail(f"Python 3.10+ required. You have {version[0]}.{version[1]}")
        sys.exit(1)
    ok(f"Python {version[0]}.{version[1]}")

    # Check pip
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "--version"],
            capture_output=True, check=True
        )
        ok("pip available")
    except Exception:
        fail("pip not found. Install pip first.")
        sys.exit(1)

    # Create virtual environment
    venv_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".venv")
    if os.path.exists(venv_dir):
        ok(f"Virtual environment already exists: {venv_dir}")
    else:
        info("Creating virtual environment...")
        try:
            subprocess.run(
                [sys.executable, "-m", "venv", venv_dir],
                check=True, capture_output=True
            )
            ok("Virtual environment created")
        except subprocess.CalledProcessError:
            fail("Failed to create virtual environment.")
            info("Try: sudo apt install python3-venv")
            sys.exit(1)

    # Determine pip/python paths
    if sys.platform == "win32":
        pip_path = os.path.join(venv_dir, "Scripts", "pip")
        python_path = os.path.join(venv_dir, "Scripts", "python")
    else:
        pip_path = os.path.join(venv_dir, "bin", "pip")
        python_path = os.path.join(venv_dir, "bin", "python")

    # Check if dependencies are already installed
    req_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "requirements.txt")
    if os.path.exists(req_file):
        info("Installing dependencies (first time may take a minute)...")
        try:
            result = subprocess.run(
                [pip_path, "install", "-r", req_file],
                capture_output=True, text=True, timeout=120
            )
            if result.returncode == 0:
                ok("All dependencies installed")
            else:
                warn("Some dependencies may have failed. Check output above.")
                info(f"Try manually: {pip_path} install -r requirements.txt")
        except subprocess.TimeoutExpired:
            warn("Dependency installation timed out. Try manually.")
            info(f"Run: {pip_path} install -r requirements.txt")
        except Exception as e:
            warn(f"Could not install dependencies: {e}")
            info(f"Try manually: {pip_path} install -r requirements.txt")
    else:
        warn("requirements.txt not found. Install dependencies manually.")

    return python_path

CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"

def banner():
    print(f"""
{CYAN}{BOLD}
  ____  _            _       _____ _   
 |  _ \\| |          | |     / ____| |  
 | |_) | | __ _  __| | __ _| |    | |_ 
 |  _ <| |/ _` |/ _` |/ _` | |    | __|
 | |_) | | (_| | (_| | (_| | |____| |_ 
 |____/|_|\\__,_|\\__,_|\\__,_|\\______|{RESET}
{BOLD}  Self-Service AI Discord Agent{RESET}
""")

def step(num, title):
    print(f"\n{BOLD}{CYAN}{'='*50}{RESET}")
    print(f"{BOLD}{CYAN}  STEP {num}: {title}{RESET}")
    print(f"{BOLD}{CYAN}{'='*50}{RESET}\n")

def ok(msg):
    print(f"  {GREEN}✓ {msg}{RESET}")

def warn(msg):
    print(f"  {YELLOW}⚠ {msg}{RESET}")

def fail(msg):
    print(f"  {RED}✗ {msg}{RESET}")

def info(msg):
    print(f"  {CYAN}  {msg}{RESET}")

def ask(prompt):
    return input(f"  {BOLD}> {prompt}{RESET}").strip()

def generate_secret():
    return ''.join(random.choices(string.ascii_letters + string.digits + "!@#$%^&*", k=32))

def extract_client_id(token: str) -> str:
    """Extract Application Client ID from Discord bot token.
    Token format: base64(client_id).secret.token"""
    try:
        parts = token.split(".")
        if len(parts) >= 1:
            # Pad base64 if needed
            padded = parts[0] + "=" * (4 - len(parts[0]) % 4)
            decoded = base64.b64decode(padded)
            return decoded.decode("utf-8")
    except Exception:
        pass
    return ""

def build_invite_url(client_id: str, permissions: int = 8) -> str:
    return f"https://discord.com/oauth2/authorize?client_id={client_id}&permissions={permissions}&scope=bot%20applications.commands"

def ensure_dirs():
    dirs = [
        "config", "storage", "storage/files", "storage/logs",
        "templates", "bot", "bot/cogs", "bot/utils",
        "dashboard", "dashboard/templates", "dashboard/static"
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)

def write_config(config: dict, path="config/config.yaml"):
    with open(path, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    ok("config.yaml written")

def write_skills(config: dict, path="config/skills.yaml"):
    skills = config.get("_skills", {})
    with open(path, "w") as f:
        yaml.dump(skills, f, default_flow_style=False)
    ok("skills.yaml written")

def init_db(path="storage/database.sqlite"):
    import sqlite3
    conn = sqlite3.connect(path)
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            discord_id TEXT NOT NULL,
            username TEXT,
            first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS servers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id TEXT NOT NULL UNIQUE,
            name TEXT,
            soul_version INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            key TEXT NOT NULL,
            value TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id TEXT,
            user_id TEXT NOT NULL,
            message TEXT,
            response TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS files (
            id TEXT PRIMARY KEY,
            guild_id TEXT,
            filename TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_size INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS usage_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL UNIQUE,
            total_messages INTEGER DEFAULT 0,
            total_tokens INTEGER DEFAULT 0,
            total_cost REAL DEFAULT 0.0
        );
    """)
    conn.commit()
    conn.close()
    ok("database.sqlite initialized")

def load_template(business_type: str) -> str:
    """Load a Soul.md template based on business type."""
    templates = {
        "restaurant": """# Soul.md - Your AI Agent's Identity

## Identity
- Name: {bot_name}
- Role: Customer Service Assistant
- Personality: {personality}

## Business Info
- Business Name: {business_name}
- Industry: Restaurant / Food
- Location: {location}
- Hours: {hours}
- Contact: {phone}
- Email: {email}
- Website: {website}

## Menu / Services
- Starters: Add your starters here
- Mains: Add your main dishes here
- Drinks: Add your drinks here
- Desserts: Add your desserts here

## FAQ
- What are your hours? -> {hours}
- Where are you located? -> {location}
- Do you deliver? -> Yes/No -- add details
- How do I order? -> Tell me what you would like!
- What payment do you accept? -> Add payment methods
- Do you cater for allergies? -> Yes, please let me know your allergies
- Do you take reservations? -> Yes, I can help you book a table

## Policies
- Delivery: Add delivery policy
- Cancellation: Add cancellation policy
- Returns/Refunds: Add refund policy

## Behavior Rules
- Tone: {personality}
- Language: English
- Do: Be helpful, suggest items, upsell politely
- Dont: Argue with customers, make up prices, share personal info
- Fallback: "I am not sure about that. Let me connect you with a human who can help."

## Capabilities
- [x] Answer FAQs
- [x] Take orders
- [x] Book tables
- [x] Provide menu info
- [x] Handle allergies/special requests
""",
        "salon": """# Soul.md - Your AI Agent's Identity

## Identity
- Name: {bot_name}
- Role: Appointment Booking Assistant
- Personality: {personality}

## Business Info
- Business Name: {business_name}
- Industry: Salon / Beauty / Spa
- Location: {location}
- Hours: {hours}
- Contact: {phone}
- Email: {email}
- Website: {website}

## Services
- Hair: Add services and prices
- Nails: Add services and prices
- Facial: Add services and prices
- Massage: Add services and prices
- Other: Add other services

## FAQ
- What are your hours? -> {hours}
- Where are you? -> {location}
- How do I book? -> I can book for you right now!
- How much is [service]? -> Check our services above
- Can I cancel? -> Yes, 24 hours notice please
- Walk-ins welcome? -> Yes / By appointment only

## Policies
- Cancellation: 24 hours notice required
- Late policy: 15 minute grace period
- Payment: Add payment methods

## Behavior Rules
- Tone: {personality}
- Language: English
- Do: Be friendly, confirm bookups, remind of policies
- Dont: Guarantee results, give medical advice, overbook
- Fallback: "I need to check with the team. Can I get your number?"
""",
        "shop": """# Soul.md - Your AI Agent's Identity

## Identity
- Name: {bot_name}
- Role: Sales Assistant
- Personality: {personality}

## Business Info
- Business Name: {business_name}
- Industry: Retail / Shop
- Location: {location}
- Hours: {hours}
- Contact: {phone}
- Email: {email}
- Website: {website}

## Products
- Category 1: Add products and prices
- Category 2: Add products and prices
- Category 3: Add products and prices

## FAQ
- What are your hours? -> {hours}
- Where are you? -> {location}
- Do you deliver? -> Yes/No -- add details
- How do I order? -> I can help you order right now!
- What payment do you accept? -> Add payment methods
- Do you do returns? -> Add return policy
- Is [item] in stock? -> Let me check...

## Policies
- Returns: Add return policy
- Delivery: Add delivery info
- Payment: Add payment methods

## Behavior Rules
- Tone: {personality}
- Language: English
- Do: Be helpful, suggest products, confirm orders
- Dont: Make up prices, overshare, argue
- Fallback: "I will need to check that for you. One moment!"
""",
        "clinic": """# Soul.md - Your AI Agent's Identity

## Identity
- Name: {bot_name}
- Role: Patient Support Assistant
- Personality: {personality}

## Business Info
- Business Name: {business_name}
- Industry: Medical / Health
- Location: {location}
- Hours: {hours}
- Contact: {phone}
- Email: {email}
- Website: {website}

## Services
- Consultation: Add info and prices
- Check-ups: Add info and prices
- Specialized: Add specialized services

## FAQ
- What are your hours? -> {hours}
- Where are you? -> {location}
- How do I book? -> I can help you make an appointment
- Do I need a referral? -> Add policy
- What should I bring? -> ID, medical aid card, previous records
- Do you accept medical aid? -> Add accepted schemes
- Is Dr [name] available? -> Let me check the schedule

## Policies
- Cancellation: 24 hours notice required
- Late policy: Add late policy
- Payment: Add payment info

## Behavior Rules
- Tone: {personality}
- Language: English
- Do: Be empathetic, direct emergencies to call 911/10177
- Dont: Diagnose conditions, prescribe medication, give medical advice
- Fallback: "I recommend speaking directly with the doctor about this."
""",
        "realestate": """# Soul.md - Your AI Agent's Identity

## Identity
- Name: {bot_name}
- Role: Property Assistant
- Personality: {personality}

## Business Info
- Business Name: {business_name}
- Industry: Real Estate
- Location: {location}
- Hours: {hours}
- Contact: {phone}
- Email: {email}
- Website: {website}

## Property Types
- Houses: Add price ranges
- Apartments: Add price ranges
- Commercial: Add price ranges
- Land: Add price ranges

## FAQ
- What areas do you cover? -> {location}
- What is the price range? -> Depends on property type -- ask me!
- How do I schedule a viewing? -> I can arrange that for you
- Are there properties available? -> Yes! Tell me what you are looking for
- Do you do rentals? -> Add rental info / No

## Policies
- Viewing: By appointment only
- Application: Add application process
- Fees: Add fee structure

## Behavior Rules
- Tone: {personality}
- Language: English
- Do: Ask about budget, preferences, be professional
- Dont: Make promises about availability, share owner personal details
- Fallback: "Let me get an agent to call you back on this."
""",
        "generic": """# Soul.md - Your AI Agent's Identity

## Identity
- Name: {bot_name}
- Role: AI Assistant
- Personality: {personality}

## Business Info
- Business Name: {business_name}
- Industry: {industry}
- Location: {location}
- Hours: {hours}
- Contact: {phone}
- Email: {email}
- Website: {website}

## Services / Products
- Add your services or products here

## FAQ
- What are your hours? -> {hours}
- Where are you? -> {location}
- How can I contact you? -> {phone}, {email}
- Add more FAQ entries here

## Policies
- Add your policies here

## Behavior Rules
- Tone: {personality}
- Language: English
- Do: Be helpful, answer questions, connect to human when needed
- Dont: Guess answers, argue, share internal info
- Fallback: "I am not sure about that. Let me find someone who can help."
"""
    }
    return templates.get(business_type, templates["generic"])

async def test_api_key(provider: str, api_key: str) -> bool:
    """Test if an API key is valid by making a small request."""
    try:
        if provider == "openrouter":
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {api_key}"}
                data = {
                    "model": "anthropic/claude-3-haiku",
                    "messages": [{"role": "user", "content": "Hi"}],
                    "max_tokens": 10
                }
                async with session.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers, json=data, timeout=aiohttp.ClientTimeout(total=15)
                ) as resp:
                    return resp.status == 200
        elif provider == "ollama":
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "http://localhost:11434/api/tags",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    return resp.status == 200
        # For other providers, just accept the key
        return True
    except Exception:
        return False

async def run_wizard():
    banner()

    # Step 0: Check prerequisites (Python, venv, dependencies)
    check_prerequisites()

    print(f"  {BOLD}Welcome to Blaze-Agent Setup!{RESET}")
    print(f"  This wizard will set up everything you need.\\n")
    print(f"  You will need:")
    print(f"  - A Discord bot token (we will guide you)")
    print(f"  - An AI provider API key (we will guide you)")
    print(f"  - About 5 minutes\\n")

    ask("Press Enter to continue...")

    # ==========================================
    # STEP 1: Discord Bot Token
    # ==========================================
    step(1, "Discord Bot Token")

    info("First, let's create your Discord bot.")
    info("")
    info("  1. Open: https://discord.com/developers/applications")
    info("  2. Click 'New Application' (top right)")
    info("  3. Give it a name and click 'Create'")
    info("  4. Click 'Bot' in the left sidebar")
    info("  5. Click 'Add Bot' then 'Yes, do it!'")
    info("  6. Under 'Privileged Gateway Intents' turn ON:")
    info("     - MESSAGE CONTENT INTENT")
    info("     - SERVER MEMBERS INTENT")
    info("     - PRESENCE INTENT")
    info("  7. Click 'Reset Token' then 'Copy'")
    info("  8. Paste it below")
    info("")

    client_id = ""
    invite_url = ""
    for attempt in range(3):
        token = ask("Paste your Discord bot token:")
        if not token:
            fail("Token cannot be empty.")
            continue
        client_id = extract_client_id(token)
        if client_id:
            invite_url = build_invite_url(client_id)
            ok(f"Token accepted. Bot Application ID: {client_id}")
            break
        else:
            fail("Could not extract Application ID. Make sure the token is complete.")

    if not client_id:
        fail("Too many failed attempts. Try running the wizard again.")
        sys.exit(1)

    info("")
    info("Here is your bot invite link:")
    print(f"  {CYAN}{invite_url}{RESET}")
    info("")
    info("Open this link in your browser and select your server.")
    info("(Bot will appear offline until we finish setup)")
    ask("Press Enter when the bot is in your server...")

    # ==========================================
    # STEP 2: AI Provider
    # ==========================================
    step(2, "AI Provider")

    info("Which AI provider do you want to use?")
    info("")
    info("  1. OpenRouter (recommended)")
    info("     Access Claude, Gemini, GPT-4 through one key")
    info("     Website: https://openrouter.ai/keys")
    info("")
    info("  2. OpenAI (GPT-4, GPT-4o)")
    info("     Website: https://platform.openai.com/api-keys")
    info("")
    info("  3. Anthropic (Claude directly)")
    info("     Website: https://console.anthropic.com/settings/keys")
    info("")
    info("  4. Google (Gemini)")
    info("     Website: https://aistudio.google.com/app/apikey")
    info("")
    info("  5. Ollama (local models, no key needed)")
    info("     Website: https://ollama.com")
    info("")

    provider_map = {"1": "openrouter", "2": "openai", "3": "anthropic", "4": "google", "5": "ollama"}
    provider_names = {
        "openrouter": "OpenRouter",
        "openai": "OpenAI",
        "anthropic": "Anthropic",
        "google": "Google",
        "ollama": "Ollama"
    }

    provider = ""
    for attempt in range(3):
        choice = ask("Choose [1-5]:")
        provider = provider_map.get(choice, "")
        if provider:
            break
        fail("Invalid choice. Enter 1-5.")

    if not provider:
        fail("Too many failed attempts.")
        sys.exit(1)

    ok(f"Provider: {provider_names[provider]}")

    # ==========================================
    # STEP 3: API Key
    # ==========================================
    step(3, "API Key")

    api_key = ""
    model = ""

    if provider == "ollama":
        info("No API key needed for Ollama.")
        info("Make sure Ollama is installed and running on this machine.")
        info("Install: https://ollama.com/download")
        info("Run: ollama pull llama3")
        ask("Press Enter when Ollama is running...")

        # Test ollama connection
        ollama_ok = await test_api_key("ollama", "")
        if ollama_ok:
            ok("Ollama detected!")
        else:
            warn("Could not connect to Ollama. Continuing anyway.")

        # Model selection for ollama
        model = ask("Model name (default: llama3):") or "llama3"
        ok(f"Model: {model}")

    else:
        urls = {
            "openrouter": "https://openrouter.ai/keys",
            "openai": "https://platform.openai.com/api-keys",
            "anthropic": "https://console.anthropic.com/settings/keys",
            "google": "https://aistudio.google.com/app/apikey"
        }
        info(f"Get your API key: {urls[provider]}")

        for attempt in range(3):
            api_key = ask(f"Paste your {provider_names[provider]} API key:")
            if not api_key:
                fail("API key cannot be empty.")
                continue

            info("Testing API key...")
            valid = await test_api_key(provider, api_key)
            if valid:
                ok(f"API key verified. Connected to {provider_names[provider]}.")
                break
            else:
                fail(f"Could not verify key. Check and try again. ({2-attempt} attempts left)")

        if not api_key:
            fail("Could not verify API key. Continuing anyway.")

        # Model selection
        info("")
        model_options = {
            "openrouter": [
                ("1", "anthropic/claude-sonnet-4", "Claude Sonnet 4 (best quality)"),
                ("2", "anthropic/claude-haiku-3.5", "Claude Haiku 3.5 (fast + cheap)"),
                ("3", "openai/gpt-4o", "GPT-4o (balanced)"),
                ("4", "google/gemini-2.0-flash", "Gemini 2.0 Flash (fast, generous free)"),
                ("5", "openai/gpt-4o-mini", "GPT-4o Mini (cheapest)"),
            ],
            "openai": [
                ("1", "gpt-4o", "GPT-4o"),
                ("2", "gpt-4o-mini", "GPT-4o Mini"),
            ],
            "anthropic": [
                ("1", "claude-sonnet-4-20250514", "Claude Sonnet 4"),
                ("2", "claude-haiku-3-5-20241022", "Claude Haiku 3.5"),
            ],
            "google": [
                ("1", "gemini-2.0-flash", "Gemini 2.0 Flash"),
                ("2", "gemini-1.5-pro", "Gemini 1.5 Pro"),
            ],
        }

        info("Choose a model:")
        for num, mod, name in model_options.get(provider, []):
            info(f"  {num}. {name}")

        model_choices = {opt[0]: opt[1] for opt in model_options.get(provider, [])}

        for attempt in range(3):
            mchoice = ask("Choose [1-5]:")
            model = model_choices.get(mchoice, "")
            if model:
                break
            fail("Invalid choice.")

        if not model:
            # Default fallback
            defaults = {
                "openrouter": "anthropic/claude-haiku-3.5",
                "openai": "gpt-4o-mini",
                "anthropic": "claude-haiku-3-5-20241022",
                "google": "gemini-2.0-flash"
            }
            model = defaults.get(provider, "")
            warn(f"Using default model: {model}")

        ok(f"Model: {model}")

    # ==========================================
    # STEP 4: Business Type
    # ==========================================
    step(4, "Business Type")

    info("What type of business is this bot for?")
    info("  1. Restaurant / Food / Takeaway")
    info("  2. Salon / Spa / Beauty")
    info("  3. Shop / E-commerce / Retail")
    info("  4. Clinic / Medical / Health")
    info("  5. Real Estate / Property")
    info("  6. General / Other")
    info("")

    biz_map = {"1": "restaurant", "2": "salon", "3": "shop", "4": "clinic", "5": "realestate", "6": "generic"}
    biz_names = {"restaurant": "Restaurant", "salon": "Salon/Spa", "shop": "Shop", "clinic": "Clinic", "realestate": "Real Estate", "generic": "General"}

    business_type = ""
    for attempt in range(3):
        bchoice = ask("Choose [1-6]:")
        business_type = biz_map.get(bchoice, "")
        if business_type:
            break
        fail("Invalid choice.")

    if not business_type:
        business_type = "generic"
        warn("Using default: General")

    ok(f"Business type: {biz_names[business_type]}")

    # Auto-configure skills based on business type
    skill_presets = {
        "restaurant": {"faq": True, "order_taking": True, "booking": True, "lead_capture": False, "file_creation": False, "complaint_handler": True, "language_detection": False},
        "salon": {"faq": True, "order_taking": False, "booking": True, "lead_capture": True, "file_creation": False, "complaint_handler": True, "language_detection": False},
        "shop": {"faq": True, "order_taking": True, "booking": False, "lead_capture": True, "file_creation": True, "complaint_handler": True, "language_detection": False},
        "clinic": {"faq": True, "order_taking": False, "booking": True, "lead_capture": True, "file_creation": False, "complaint_handler": True, "language_detection": False},
        "realestate": {"faq": True, "order_taking": False, "booking": False, "lead_capture": True, "file_creation": True, "complaint_handler": True, "language_detection": False},
        "generic": {"faq": True, "order_taking": False, "booking": False, "lead_capture": True, "file_creation": False, "complaint_handler": True, "language_detection": False},
    }
    auto_skills = skill_presets.get(business_type, skill_presets["generic"])
    ok(f"Skills auto-configured for {biz_names[business_type]}")

    # ==========================================
    # STEP 5: Business Info
    # ==========================================
    step(5, "Business Info")

    info("Tell us about your business (press Enter to skip optional fields)")
    info("")

    business_name = ask("Business name:")
    while not business_name:
        fail("Business name is required.")
        business_name = ask("Business name:")

    location = ask("Location (or 'online'):") or "Not specified"
    hours = ask("Operating hours:") or "Mon-Fri 9am-5pm"
    phone = ask("Phone (optional):") or "N/A"
    email = ask("Email (optional):") or "N/A"
    website = ask("Website (optional):") or "N/A"

    ok("Business info saved.")

    # ==========================================
    # STEP 6: Bot Personality
    # ==========================================
    step(6, "Bot Personality")

    info("How should your bot talk to customers?")
    info("  1. Professional and formal")
    info("  2. Friendly and casual (recommended)")
    info("  3. Fun and energetic")
    info("  4. Calm and helpful")
    info("")

    pers_map = {"1": "professional", "2": "friendly", "3": "energetic", "4": "calm"}
    personality = ""
    for attempt in range(3):
        pchoice = ask("Choose [1-4]:")
        personality = pers_map.get(pchoice, "")
        if personality:
            break
        fail("Invalid choice.")

    if not personality:
        personality = "friendly"
        warn("Defaulting to: friendly")

    ok(f"Personality: {personality}")

    # ==========================================
    # STEP 7: Bot Name
    # ==========================================
    step(7, "Bot Name")

    bot_name = ask("What should customers call the bot?")
    while not bot_name:
        fail("Bot name is required.")
        bot_name = ask("What should customers call the bot?")

    ok(f"Bot name: {bot_name}")

    # ==========================================
    # STEP 8: Dashboard
    # ==========================================
    step(8, "Dashboard Setup")

    info("The web dashboard lets you manage the bot from your browser.")
    port = ask("Port (default: 8080):") or "8080"

    info("")
    dashboard_password = ""
    for attempt in range(3):
        p1 = ask("Dashboard password (min 8 chars):")
        if len(p1) < 8:
            fail("Password must be at least 8 characters.")
            continue
        p2 = ask("Confirm password:")
        if p1 != p2:
            fail("Passwords do not match.")
            continue
        dashboard_password = p1
        break

    if not dashboard_password:
        dashboard_password = generate_secret()[:12]
        warn(f"Auto-generated password: {dashboard_password}")
        warn("Change this from the dashboard after setup!")

    ok(f"Dashboard: http://localhost:{port}")

    # ==========================================
    # STEP 9: Spend Limits
    # ==========================================
    step(9, "Spend Limits")

    info("Set AI spend limits to prevent unexpected charges.")
    daily_limit = ask("Daily limit in USD (default: 2.00):") or "2.0"
    monthly_limit = ask("Monthly limit in USD (default: 10.00):") or "10.0"

    try:
        daily_limit = float(daily_limit)
    except ValueError:
        daily_limit = 2.0
        warn("Invalid number. Using $2.00/day.")

    try:
        monthly_limit = float(monthly_limit)
    except ValueError:
        monthly_limit = 10.0
        warn("Invalid number. Using $10.00/month.")

    ok(f"Limits: ${daily_limit:.2f}/day, ${monthly_limit:.2f}/month")

    # ==========================================
    # STEP 10: Channel Restriction
    # ==========================================
    step(10, "Channel Restriction")

    info("Should the bot respond in all channels or specific ones?")
    info("  1. All channels (default)")
    info("  2. Specific channels only")
    info("")

    channel_mode = "all"
    allowed_channels = []

    chchoice = ask("Choose [1-2]:") or "1"
    if chchoice == "2":
        channel_mode = "specific"
        info("Enter channel IDs (comma-separated).")
        info("Right-click a channel in Discord > Copy Channel ID")
        info("(You need Developer Mode enabled in Discord settings)")
        ch_input = ask("Channel IDs:")
        allowed_channels = [c.strip() for c in ch_input.split(",") if c.strip()]
        ok(f"Bot will respond in {len(allowed_channels)} channel(s)")
    else:
        ok("Bot will respond in all channels.")

    # ==========================================
    # STEP 11: Admin Channel
    # ==========================================
    step(11, "Admin Notification Channel")

    info("Where should the bot send admin alerts?")
    info("(complaint escalations, daily stats)")
    info("Right-click a channel > Copy Channel ID")
    admin_channel = ask("Admin channel ID (or Enter to skip):") or ""

    if admin_channel:
        ok(f"Admin channel: {admin_channel}")
    else:
        warn("No admin channel set. Alerts will not be sent.")

    # ==========================================
    # STEP 12: Review
    # ==========================================
    step(12, "Review Configuration")

    info("")
    info(f"  Discord Bot:        ✓ {client_id}")
    info(f"  AI Provider:        {provider_names[provider]}")
    info(f"  AI Model:           {model}")
    info(f"  Business Type:      {biz_names[business_type]}")
    info(f"  Business Name:      {business_name}")
    info(f"  Bot Name:           {bot_name}")
    info(f"  Personality:        {personality}")
    info(f"  Dashboard:          http://localhost:{port}")
    info(f"  Monthly Budget:     ${monthly_limit:.2f}")
    info(f"  Channels:           {'All' if channel_mode == 'all' else str(len(allowed_channels)) + ' channel(s)'}")
    info(f"  Admin Channel:      {admin_channel or 'None'}")
    info("")
    info("  Skills Enabled:")
    for skill, enabled in auto_skills.items():
        status = f"{GREEN}✓{RESET}" if enabled else f"{RED}✗{RESET}"
        info(f"    {status} {skill.replace('_', ' ').title()}")
    info("")

    confirm = ask("Looks good? [1=Yes / 2=Edit / 3=Cancel]:")
    if confirm == "3":
        info("Setup cancelled. Nothing was written.")
        sys.exit(0)
    elif confirm == "2":
        warn("Re-run the wizard to make changes. No files written yet.")
        sys.exit(0)

    # ==========================================
    # STEP 13: Generate Files
    # ==========================================
    step(13, "Generating Files")

    # Ensure directories
    ensure_dirs()
    ok("Directories created")

    # Build config
    secret_key = generate_secret()
    config = {
        "discord": {
            "token": token,
            "client_id": client_id,
            "invite_url": invite_url,
            "prefix": "!"
        },
        "ai": {
            "provider": provider,
            "api_key": api_key if provider != "ollama" else "",
            "model": model,
            "fallback_model": "",
            "max_tokens": 1000,
            "temperature": 0.7,
            "daily_spend_limit": daily_limit,
            "monthly_spend_limit": monthly_limit
        },
        "bot": {
            "name": bot_name,
            "personality": personality,
            "business_type": business_type,
            "language": "english"
        },
        "dashboard": {
            "host": "127.0.0.1",
            "port": int(port),
            "secret_key": secret_key,
            "password": dashboard_password
        },
        "skills": auto_skills,
        "memory": {
            "enabled": True,
            "max_per_user": 50,
            "auto_extract": True,
            "retention_days": 90
        },
        "files": {
            "enabled": True,
            "storage_path": "storage/files/",
            "max_file_size_mb": 25,
            "link_expiry_days": 7,
            "allowed_types": ["pdf", "docx", "xlsx", "png", "jpg", "txt", "csv"]
        },
        "channels": {
            "mode": channel_mode,
            "allowed": allowed_channels,
            "admin_channel": admin_channel
        },
        "_skills": auto_skills
    }

    write_config(config)
    write_skills(config)
    del config["_skills"]  # Remove temp key from config.yaml already written

    # Generate Soul.md from template
    template = load_template(business_type)
    soul_content = template.format(
        bot_name=bot_name,
        personality=personality,
        business_name=business_name,
        industry=biz_names[business_type].lower(),
        location=location,
        hours=hours,
        phone=phone,
        email=email,
        website=website
    )
    with open("config/soul.md", "w") as f:
        f.write(soul_content)
    ok("Soul.md generated from template")

    # Initialize database
    init_db()

    # ==========================================
    # DONE
    # ==========================================
    print(f"\n{BOLD}{GREEN}{'='*50}{RESET}")
    print(f"{BOLD}{GREEN}  SETUP COMPLETE!{RESET}")
    print(f"{BOLD}{GREEN}{'='*50}{RESET}\n")

    ok(f"Dashboard:  http://localhost:{port}")
    ok(f"Password:   {dashboard_password}")
    ok(f"")
    ok(f"To start your bot:")
    ok(f"  source .venv/bin/activate    # Linux/Mac")
    ok(f"  .venv\\Scripts\\activate        # Windows")
    ok(f"  python run.py")
    ok(f"")
    ok(f"Bot invite link:")
    print(f"  {CYAN}{invite_url}{RESET}")
    ok(f"")
    info(f"First time?")
    info(f"  1. Open the dashboard and edit Soul.md")
    info(f"  2. Add your products/services to the FAQ section")
    info(f"  3. Run: source .venv/bin/activate && python run.py")
    info(f"  4. Talk to your bot in Discord!")
    info(f"")

if __name__ == "__main__":
    asyncio.run(run_wizard())
