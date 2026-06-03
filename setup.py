"""
Blaze-Agent Setup Wizard v2.0
==============================
Interactive terminal wizard to set up a BlazeAgent instance.
Styled with the Blaze brand -- neon red / dark terminal aesthetic.
Full polish: animated transitions, progress steps, re-edit loop,
smart defaults, input validation, skill toggles, impact finish.

Uses Unicode box-drawing chars with VTE terminal detection.
VTE-based terminals (QTerminal, GNOME Terminal, etc.) render these
as 2 columns wide, so we halve the fill count automatically.
"""

import os
import sys
import subprocess
import re
import yaml
import base64
import json
import random
import string
import time
import aiohttp
import asyncio

# ═══════════════════════════════════════════════════
#  VTE DETECTION
# ═══════════════════════════════════════════════════
# VTE terminals render box-drawing chars as 2 columns wide.
# We detect via VTE_VERSION env var or parent process name.

_vte_wide = False

def _detect_vte():
    global _vte_wide
    if os.getenv("VTE_VERSION"):
        _vte_wide = True; return
    try:
        ppid = os.getppid()
        for _ in range(5):
            try:
                r = subprocess.run(["ps","-o","comm=","-p",str(ppid)], capture_output=True, text=True, timeout=2)
                name = r.stdout.strip().lower()
                if name in ("qterminal","gnome-terminal","xfce4-terminal","mate-terminal","lxterminal","tilix","terminator"):
                    _vte_wide = True; return
                r2 = subprocess.run(["ps","-o","ppid=","-p",str(ppid)], capture_output=True, text=True, timeout=2)
                ppid = int(r2.stdout.strip())
            except: break
    except: pass

_detect_vte()

def fill(bw):
    """Number of box-drawing fill chars to span `bw` screen columns."""
    return bw // 2 if _vte_wide else bw

# ═══════════════════════════════════════════════════
#  BLAZE COLORS
# ═══════════════════════════════════════════════════

_use_color = True

def _detect_color():
    global _use_color
    if os.getenv("NO_COLOR"):
        _use_color = False; return
    if sys.platform == "win32":
        _use_color = bool(os.getenv("ANSICON") or os.getenv("WT_SESSION"))
    else:
        _use_color = hasattr(sys.stdout, "isatty") and sys.stdout.isatty()

_detect_color()

class _C:
    R0  = "\033[38;2;255;0;60m"
    G0  = "\033[38;2;0;255;136m"
    Y0  = "\033[38;2;255;204;0m"
    B0  = "\033[38;2;64;156;255m"
    C0  = "\033[38;2;0;204;204m"
    D0  = "\033[38;2;90;90;90m"
    D1  = "\033[38;2;60;60;60m"
    D2  = "\033[38;2;40;40;40m"
    L0  = "\033[38;2;170;170;170m"
    W0  = "\033[38;2;255;255;255m"
    BLD = "\033[1m"
    DIM = "\033[2m"
    ITA = "\033[3m"
    RST = "\033[0m"

def clr(code):
    return code if _use_color else ""

R0  = lambda: clr(_C.R0)
G0  = lambda: clr(_C.G0)
Y0  = lambda: clr(_C.Y0)
D0  = lambda: clr(_C.D0)
D1  = lambda: clr(_C.D1)
D2  = lambda: clr(_C.D2)
L0  = lambda: clr(_C.L0)
W0  = lambda: clr(_C.W0)
BLD = lambda: clr(_C.BLD)
DIM = lambda: clr(_C.DIM)
ITA = lambda: clr(_C.ITA)
RST = lambda: clr(_C.RST)
C0  = lambda: clr(_C.C0)
M0  = lambda: clr(_C.M0)
B0  = lambda: clr(_C.B0)

# ═══════════════════════════════════════════════════
#  TERMINAL HELPERS
# ═══════════════════════════════════════════════════

def twidth():
    try: return max(44, min(80, os.get_terminal_size().columns - 2))
    except OSError: return 56

def clear():
    if _use_color: sys.stdout.write("\033[2J\033[H"); sys.stdout.flush()

def rule(color=None):
    w = twidth(); c = color or D1
    # Use ─ (always 1-col) for rules, not ═
    print(f"  {c()}{'─' * (w - 4)}{RST()}")

def spacer(n=1):
    print("\n" * (n - 1))

def len_stripped(s):
    """Visible length ignoring ANSI codes. All non-ANSI chars = 1 col
    (box chars in content are handled by fill() at border level)."""
    return len(re.sub(r'\033\[[0-9;]*m', '', s))

def fade_in(lines, delay=0.015):
    for line in lines:
        print(line)
        if _use_color and delay > 0: time.sleep(delay)

# ═══════════════════════════════════════════════════
#  BOX DRAWING (Unicode with VTE correction)
# ═══════════════════════════════════════════════════

def box_top(bw):
    f = fill(bw)
    print(f"  {R0()}{BLD()}+{'-' * f}+{RST()}")

def box_bottom(bw):
    f = fill(bw)
    print(f"  {R0()}{BLD()}+{'-' * f}+{RST()}")

def box_sep(bw):
    f = fill(bw)
    print(f"  {R0()}{BLD()}+{'-' * f}+{RST()}")

def box_line(content, bw):
    pad = max(0, bw - len_stripped(content))
    print(f"  {R0()}{BLD()}|{RST()}{content}{' ' * pad}{R0()}{BLD()}|{RST()}")

# ═══════════════════════════════════════════════════
#  PROGRESS TRACKER
# ═══════════════════════════════════════════════════

TOTAL_STEPS = 10

def _step_progress(num, title):
    w = twidth()
    inner = w - 4  # screen columns for content between |...|
    f = fill(inner)  # number of - chars for border

    dots = ""
    for i in range(1, TOTAL_STEPS + 1):
        if i < num: dots += f"{G0()}*{RST()}"
        elif i == num: dots += f"{R0()}{BLD()}>{RST()}"
        else: dots += f"{D2()}.{RST()}"

    spacer()
    print(f"  {R0()}{BLD()}+{'-'*f}+{RST()}")
    dc = f" {dots}"
    dp = max(0, inner - len_stripped(dc))
    print(f"  {R0()}{BLD()}|{RST()}{dc}{' '*dp}{R0()}{BLD()}|{RST()}")
    tt = f"  {W0()}{BLD()}STEP {num} of {TOTAL_STEPS}  --  {title}{RST()}"
    tp = max(0, inner - len_stripped(tt))
    print(f"  {R0()}{BLD()}|{RST()}{tt}{' '*tp}{R0()}{BLD()}|{RST()}")
    print(f"  {R0()}{BLD()}+{'-'*f}+{RST()}")
    spacer()

# ═══════════════════════════════════════════════════
#  BANNER
# ═══════════════════════════════════════════════════

def banner():
    r = R0(); b = BLD(); d = D0(); rst = RST()
    w = W0(); g = G0(); y = Y0()
    spacer()
    lines = [
        f"  {r}{b}  ██████╗ ██╗      █████╗ ███████╗███████╗{rst}",
        f"  {r}{b}  ██╔══██╗██║     ██╔══██╗╚══███╔╝██╔════╝{rst}",
        f"  {r}{b}  ██████╔╝██║     ███████║  ███╔╝ █████╗  {rst}",
        f"  {r}{b}  ██╔══██╗██║     ██╔══██║ ███╔╝  ██╔══╝  {rst}",
        f"  {r}{b}  ██████╔╝███████╗██║  ██║███████╗███████╗{rst}",
        f"  {r}{b}  ╚═════╝ ╚══════╝╚═╝  ╚═╝╚══════╝╚══════╝{rst}",
        f"  {d}{'─' * 44}{rst}",
        f"  {w}{b}  Self-Service AI Discord Agent{rst}",
        f"  {d}  Configuration Wizard v2.0{rst}",
        f"  {d}{'─' * 44}{rst}",
        f"",
        f"  {r}{b}  🔥{rst}  {y}Your business. Your keys. Your control.{rst}",
        f"  {d}  Zero ongoing costs. Fully local. Privacy-first.{rst}",
    ]
    fade_in(lines, 0.02)
    spacer()

# ═══════════════════════════════════════════════════
#  STATUS LABELS
# ═══════════════════════════════════════════════════

def step(num, title):
    _step_progress(num, title)

def ok(msg, indent=4):
    print(f"{' ' * indent}{G0()}✔{RST()}  {msg}")

def warn(msg, indent=4):
    print(f"{' ' * indent}{Y0()}▸{RST()}  {msg}")

def fail(msg, indent=4):
    print(f"{' ' * indent}{R0()}✘{RST()}  {R0()}{msg}{RST()}")

def info(msg, indent=4):
    print(f"{' ' * indent}{D0()}{msg}{RST()}")

def bullet(num, text, indent=6):
    print(f"{' ' * indent}{R0()}{BLD()}⦿ {num}{RST()}  {text}")

def prompt(msg, hint=""):
    h = f" {D0()}{ITA()}{hint}{RST()}" if hint else ""
    return input(f"  {R0()}{BLD()}»{RST()}  {W0()}{msg}{RST()}{h}: ").strip()

def prompt_key(msg):
    import getpass
    h = f" {D0()}{ITA()}(input hidden){RST()}"
    try:
        val = getpass.getpass(f"  {R0()}{BLD()}»{RST()}  {W0()}{msg}{RST()}{h}: ")
    except Exception:
        val = input(f"  {R0()}{BLD()}»{RST()}  {W0()}{msg}{RST()}: ")
    return val.strip()

def confirm(msg):
    return input(f"  {R0()}{BLD()}»{RST()}  {W0()}{msg}{RST()} {D0()}[Y/n]{RST()}: ").strip().lower() in ("", "y", "yes")

# ═══════════════════════════════════════════════════
#  INPUT VALIDATION
# ═══════════════════════════════════════════════════

def validate_email(val):
    if not val or val == "N/A": return True
    return bool(re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', val))

def validate_url(val):
    if not val or val == "N/A": return True
    return val.startswith("http://") or val.startswith("https://") or val.startswith("www.")

def validate_phone(val):
    if not val or val == "N/A": return True
    cleaned = re.sub(r'[\s\-\(\)\+\.]', '', val)
    return cleaned.isdigit() and 7 <= len(cleaned) <= 15

# ═══════════════════════════════════════════════════
#  SMART DEFAULTS
# ═══════════════════════════════════════════════════

BUSINESS_DEFAULTS = {
    "restaurant": {"hours": "Mon-Sun 11am-10pm", "personality": "friendly"},
    "salon":      {"hours": "Mon-Sat 9am-7pm",   "personality": "friendly"},
    "shop":       {"hours": "Mon-Sat 9am-6pm, Sun 10am-2pm", "personality": "friendly"},
    "clinic":     {"hours": "Mon-Fri 8am-5pm",   "personality": "calm"},
    "realestate": {"hours": "Mon-Fri 8am-6pm, Sat 9am-1pm", "personality": "professional"},
    "generic":    {"hours": "Mon-Fri 9am-5pm",   "personality": "friendly"},
}

# ═══════════════════════════════════════════════════
#  UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════

def generate_secret():
    return ''.join(random.choices(string.ascii_letters + string.digits + "!@#$%^&*", k=32))

def extract_client_id(token: str) -> str:
    try:
        parts = token.split(".")
        if len(parts) >= 1:
            padded = parts[0] + "=" * (4 - len(parts[0]) % 4)
            decoded = base64.b64decode(padded)
            return decoded.decode("utf-8")
    except Exception: pass
    return ""

def build_invite_url(client_id: str, permissions: int = 1126400) -> str:
    return f"https://discord.com/oauth2/authorize?client_id={client_id}&permissions={permissions}&scope=bot%20applications.commands"

def ensure_dirs():
    dirs = ["config","storage","storage/files","storage/logs","templates","bot","bot/cogs","bot/utils","dashboard","dashboard/templates","dashboard/static"]
    for d in dirs: os.makedirs(d, exist_ok=True)

def write_config(config: dict, path="config/config.yaml"):
    with open(path, "w") as f: yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    ok("config.yaml written")

def write_skills(config: dict, path="config/skills.yaml"):
    skills = config.get("_skills", {})
    with open(path, "w") as f: yaml.dump(skills, f, default_flow_style=False)
    ok("skills.yaml written")

def init_db(path="storage/database.sqlite"):
    import sqlite3
    conn = sqlite3.connect(path)
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, discord_id TEXT NOT NULL, username TEXT, first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP, last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS servers (id INTEGER PRIMARY KEY AUTOINCREMENT, guild_id TEXT NOT NULL UNIQUE, name TEXT, soul_version INTEGER DEFAULT 1, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS memories (id INTEGER PRIMARY KEY AUTOINCREMENT, guild_id TEXT NOT NULL, user_id TEXT NOT NULL, key TEXT NOT NULL, value TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS conversations (id INTEGER PRIMARY KEY AUTOINCREMENT, guild_id TEXT, user_id TEXT NOT NULL, message TEXT, response TEXT, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS files (id TEXT PRIMARY KEY, guild_id TEXT, filename TEXT NOT NULL, file_path TEXT NOT NULL, file_size INTEGER, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, expires_at TIMESTAMP);
        CREATE TABLE IF NOT EXISTS usage_stats (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT NOT NULL UNIQUE, total_messages INTEGER DEFAULT 0, total_tokens INTEGER DEFAULT 0, total_cost REAL DEFAULT 0.0);
    """)
    conn.commit(); conn.close()
    ok("database.sqlite initialized")

def load_template(business_type: str) -> str:
    templates = {
        "restaurant": "# Soul.md\n\n## Identity\n- Name: {bot_name}\n- Role: Customer Service Assistant\n- Personality: {personality}\n\n## Business\n- Name: {business_name}\n- Industry: Restaurant\n- Location: {location}\n- Hours: {hours}\n- Contact: {phone}\n- Email: {email}\n- Website: {website}\n\n## Behavior\n- Tone: {personality}\n- Do: Be helpful, suggest items, upsell politely\n- Dont: Argue, make up prices\n- Fallback: \"Let me connect you with a human.\"\n",
        "generic": "# Soul.md\n\n## Identity\n- Name: {bot_name}\n- Role: AI Assistant\n- Personality: {personality}\n\n## Business\n- Name: {business_name}\n- Industry: {industry}\n- Location: {location}\n- Hours: {hours}\n- Contact: {phone}\n- Email: {email}\n- Website: {website}\n\n## Behavior\n- Tone: {personality}\n- Do: Be helpful, answer questions\n- Dont: Guess, argue\n- Fallback: \"Let me find someone who can help.\"\n",
    }
    return templates.get(business_type, templates["generic"])

async def test_api_key(provider: str, api_key: str) -> bool:
    try:
        if provider == "openrouter":
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {api_key}"}
                data = {"model": "anthropic/claude-3-haiku", "messages": [{"role": "user", "content": "Hi"}], "max_tokens": 10}
                async with session.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    return resp.status == 200
        elif provider == "ollama":
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:11434/api/tags", timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    return resp.status == 200
        return True
    except Exception: return False

# ═══════════════════════════════════════════════════
#  FINISH BOX
# ═══════════════════════════════════════════════════

def finish_box(config: dict):
    bw = 54; f = fill(bw)
    r = R0(); b = BLD(); d = D0(); rst = RST()
    w = W0(); g = G0(); y = Y0()

    spacer(2)
    print(f"  {r}{b}+{'-'*f}+{rst}")
    ft = "  🔥  SETUP COMPLETE!"
    ftv = len_stripped(ft)
    fl = max(0, (bw - ftv) // 2); fr = max(0, bw - ftv - fl)
    print(f"  {r}{b}|{rst}{' '*fl}{ft}{' '*fr}{r}{b}|{rst}")
    print(f"  {r}{b}+{'-'*f}+{rst}")

    for label, val in [
        ("Dashboard",  f"http://localhost:{config.get('dashboard', {}).get('port', 8080)}"),
        ("Bot Name",   config.get('bot', {}).get('name', '—')),
        ("Provider",   config.get('ai', {}).get('provider', '—')),
        ("Model",      config.get('ai', {}).get('model', '—')),
        ("Business",   config.get('bot', {}).get('business_type', '—').title()),
        ("Budget/day", f"${config.get('ai', {}).get('daily_spend_limit', 0):.2f}"),
        ("Budget/mo",  f"${config.get('ai', {}).get('monthly_spend_limit', 0):.2f}"),
    ]:
        trunc_val = str(val)[:bw - 10] if len(str(val)) > bw - 10 else str(val)
        dots = '.' * max(2, bw - 6 - len(label) - len(trunc_val))
        lc = f"  {r}{label}{rst} {dots} {w}{trunc_val}{rst} "
        lp = max(0, bw - len_stripped(lc))
        print(f"  {r}{b}|{rst}{lc}{' '*lp}{r}{b}|{rst}")

    print(f"  {r}{b}+{'-'*f}+{rst}")
    qs = f"  {y}{b}QUICK START:{rst}"
    print(f"  {r}{b}|{rst}{qs}{' '*(bw-len_stripped(qs))}{r}{b}|{rst}")

    for cmd, desc in [(f"{g}blzed start{rst}","Fire up the bot"),
        (f"{g}blzed status{rst}","Check health"),(f"{g}blzed setup{rst}","Re-run wizard")]:
        ci = f"    {cmd} {d}-- {desc}{rst}"
        print(f"  {r}{b}|{rst}{ci}{' '*(bw-len_stripped(ci))}{r}{b}|{rst}")

    print(f"  {r}{b}|{' '*bw}|{rst}")
    for tip in ["  Tip: Open the dashboard to manage everything",
                "       from your browser -- no terminal needed!"]:
        tc = f"  {d}{ITA()}{tip.strip()}{rst}"
        print(f"  {r}{b}|{rst}{tc}{' '*(bw-len_stripped(tc))}{r}{b}|{rst}")

    print(f"  {r}{b}+{'-'*f}+{rst}")
    spacer()

# ═══════════════════════════════════════════════════
#  PREREQUISITES
# ═══════════════════════════════════════════════════

def check_prerequisites():
    w = twidth(); inner = w - 4; f = fill(inner)
    print(f"  {R0()}{BLD()}+{'-'*f}+{RST()}")
    pc = f"  {W0()}{BLD()}⚡ CHECKING PREREQUISITES{RST()}"
    print(f"  {R0()}{BLD()}|{RST()}{pc}{' '*(inner-len_stripped(pc))}{R0()}{BLD()}|{RST()}")
    print(f"  {R0()}{BLD()}+{'-'*f}+{RST()}")
    spacer()

    version = sys.version_info[:2]
    if version < (3, 10): fail(f"Python 3.10+ required."); sys.exit(1)
    ok(f"Python {version[0]}.{version[1]}")
    try:
        subprocess.run([sys.executable, "-m", "pip", "--version"], capture_output=True, check=True)
        ok("pip available")
    except Exception: fail("pip not found."); sys.exit(1)

    venv_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".venv")
    if os.path.exists(venv_dir): ok("Virtual environment already exists")
    else:
        info("Creating virtual environment...")
        try:
            subprocess.run([sys.executable, "-m", "venv", venv_dir], check=True, capture_output=True)
            ok("Virtual environment created")
        except subprocess.CalledProcessError:
            fail("Failed to create venv."); sys.exit(1)

    if sys.platform == "win32":
        pip_path = os.path.join(venv_dir, "Scripts", "pip")
        python_path = os.path.join(venv_dir, "Scripts", "python")
    else:
        pip_path = os.path.join(venv_dir, "bin", "pip")
        python_path = os.path.join(venv_dir, "bin", "python")

    req_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "requirements.txt")
    if os.path.exists(req_file):
        info("Installing dependencies...")
        try:
            result = subprocess.run([pip_path, "install", "-r", req_file], capture_output=True, text=True, timeout=120)
            if result.returncode == 0: ok("All dependencies installed")
            else: warn("Some deps may have failed.")
        except subprocess.TimeoutExpired: warn("Install timed out.")
        except Exception as e: warn(f"Could not install: {e}")
    else: warn("requirements.txt not found.")

    return python_path

# ═══════════════════════════════════════════════════
#  MAIN WIZARD
# ═══════════════════════════════════════════════════

async def run_wizard():
    banner()
    check_prerequisites()
    spacer()
    print(f"  {W0()}{BLD()}  Welcome to Blaze-Agent Setup!{RST()}")
    print(f"  {L0()}  This wizard will configure everything in 10 quick steps.{RST()}")
    spacer()
    print(f"  {D0()}  You will need:{RST()}")
    bullet(1, "A Discord bot token (we will guide you)", indent=6)
    bullet(2, "An AI provider API key (we will guide you)", indent=6)
    bullet(3, "About 3 minutes", indent=6)
    spacer()
    prompt("Press Enter to continue")

    while True:
        result = await _run_steps()
        if result == "done": break
        continue

async def _run_steps():
    # STEP 1
    step(1, "Discord Bot Token")
    info("First, let's create your Discord bot."); spacer()
    info(f"  {G0()}1.{RST()} Open: https://discord.com/developers/applications")
    info(f"  {G0()}2.{RST()} Click {W0()}New Application{RST()} (top right)")
    info(f"  {G0()}3.{RST()} Give it a name and click {W0()}Create{RST()}")
    info(f"  {G0()}4.{RST()} Click {W0()}Bot{RST()} in the left sidebar")
    info(f"  {G0()}5.{RST()} Click {W0()}Add Bot{RST()} then {W0()}Yes, do it!{RST()}")
    info(f"  {G0()}6.{RST()} Under {W0()}Privileged Gateway Intents{RST()} turn ON:")
    info(f"     {C0()}▸{RST()} MESSAGE CONTENT INTENT")
    info(f"     {C0()}▸{RST()} SERVER MEMBERS INTENT")
    info(f"     {C0()}▸{RST()} PRESENCE INTENT")
    info(f"  {G0()}7.{RST()} Click {W0()}Reset Token{RST()} then {W0()}Copy{RST()}")
    info(f"  {G0()}8.{RST()} Paste it below"); spacer()

    client_id = ""; invite_url = ""
    for attempt in range(3):
        token = prompt_key("Paste your Discord bot token")
        if not token: fail("Token cannot be empty."); continue
        client_id = extract_client_id(token)
        if client_id:
            invite_url = build_invite_url(client_id)
            ok(f"Token accepted. Bot Application ID: {client_id}"); break
        else: fail("Could not extract Application ID.")
    if not client_id: fail("Too many failed attempts."); sys.exit(1)

    spacer()
    info("Here is your bot invite link:")
    print(f"  {R0()}{BLD()}  {invite_url}{RST()}")
    spacer()
    info("Open this link in your browser and select your server.")
    info(f"({D0()}Bot will appear offline until we finish setup{RST()})")
    prompt("Press Enter when the bot is in your server")

    # STEP 2
    step(2, "AI Provider + API Key")
    info("Which AI provider do you want to use?"); spacer()
    bullet(1, f"OpenRouter  {D0()}--{RST()}  {L0()}Recommended. All models through one key{RST()}")
    info(f"     {D0()}https://openrouter.ai/keys{RST()}"); spacer()
    bullet(2, f"OpenAI  {D0()}--{RST()}  {L0()}GPT-4o, GPT-4o Mini{RST()}"); spacer()
    bullet(3, f"Anthropic  {D0()}--{RST()}  {L0()}Claude directly{RST()}"); spacer()
    bullet(4, f"Google  {D0()}--{RST()}  {L0()}Gemini{RST()}"); spacer()
    bullet(5, f"Ollama  {D0()}--{RST()}  {L0()}Local models, no key needed{RST()}"); spacer()

    provider_map = {"1":"openrouter","2":"openai","3":"anthropic","4":"google","5":"ollama"}
    provider_names = {"openrouter":"OpenRouter","openai":"OpenAI","anthropic":"Anthropic","google":"Google","ollama":"Ollama"}
    provider = ""
    for attempt in range(3):
        choice = prompt("Choose", hint="[1-5]")
        provider = provider_map.get(choice, "")
        if provider: break
        fail("Invalid choice. Enter 1-5.")
    if not provider: fail("Too many failed attempts."); sys.exit(1)
    ok(f"Provider: {provider_names[provider]}")

    spacer(); rule()
    api_key = ""; model = ""

    if provider == "ollama":
        info("No API key needed for Ollama.")
        info(f"Install: {C0()}https://ollama.com/download{RST()}")
        info(f"Run: {C0()}ollama pull llama3{RST()}")
        prompt("Press Enter when Ollama is running")
        info("Testing Ollama connection...")
        ollama_ok = await test_api_key("ollama", "")
        if ollama_ok: ok("Ollama detected!")
        else: warn("Could not connect to Ollama. Continuing anyway.")
        model = prompt("Model name", hint="default: llama3") or "llama3"
        ok(f"Model: {model}")
    else:
        urls = {"openrouter":"https://openrouter.ai/keys","openai":"https://platform.openai.com/api-keys","anthropic":"https://console.anthropic.com/settings/keys","google":"https://aistudio.google.com/app/apikey"}
        info(f"Get your API key: {C0()}{urls[provider]}{RST()}")
        for attempt in range(3):
            api_key = prompt_key(f"Paste your {provider_names[provider]} API key")
            if not api_key: fail("API key cannot be empty."); continue
            info("Testing API key...")
            valid = await test_api_key(provider, api_key)
            if valid: ok(f"API key verified! Connected to {provider_names[provider]}."); break
            else: fail(f"Could not verify key. ({2-attempt} attempts left)")
        if not api_key: fail("Could not verify API key. Continuing anyway.")

        spacer()
        model_options = {
            "openrouter": [("1","anthropic/claude-sonnet-4","Claude Sonnet 4 (best)"),("2","anthropic/claude-haiku-3.5","Claude Haiku 3.5 (fast+cheap)"),("3","openai/gpt-4o","GPT-4o (balanced)"),("4","google/gemini-2.0-flash","Gemini 2.0 Flash (free)"),("5","openai/gpt-4o-mini","GPT-4o Mini (cheapest)")],
            "openai": [("1","gpt-4o","GPT-4o"),("2","gpt-4o-mini","GPT-4o Mini")],
            "anthropic": [("1","claude-sonnet-4-20250514","Claude Sonnet 4"),("2","claude-haiku-3-5-20241022","Claude Haiku 3.5")],
            "google": [("1","gemini-2.0-flash","Gemini 2.0 Flash"),("2","gemini-1.5-pro","Gemini 1.5 Pro")],
        }
        info("Choose a model:")
        for num, mod, name in model_options.get(provider, []):
            info(f"  {G0()}{num}.{RST()} {name}")
        model_choices = {opt[0]: opt[1] for opt in model_options.get(provider, [])}
        for attempt in range(3):
            mchoice = prompt("Choose", hint="[1-5]")
            model = model_choices.get(mchoice, "")
            if model: break
            fail("Invalid choice.")
        if not model:
            defaults = {"openrouter":"anthropic/claude-haiku-3.5","openai":"gpt-4o-mini","anthropic":"claude-haiku-3-5-20241022","google":"gemini-2.0-flash"}
            model = defaults.get(provider, ""); warn(f"Using default: {model}")
        ok(f"Model: {model}")

    # STEP 3
    step(3, "Business Type")
    info("What type of business is this bot for?"); spacer()
    bullet(1, f"Restaurant / Food / Takeaway    {D0()}{ITA()}menu, orders, bookings{RST()}")
    bullet(2, f"Salon / Spa / Beauty            {D0()}{ITA()}appointments, services{RST()}")
    bullet(3, f"Shop / E-commerce / Retail      {D0()}{ITA()}products, orders, leads{RST()}")
    bullet(4, f"Clinic / Medical / Health       {D0()}{ITA()}bookings, patient support{RST()}")
    bullet(5, f"Real Estate / Property          {D0()}{ITA()}listings, viewings, leads{RST()}")
    bullet(6, f"General / Other                 {D0()}{ITA()}FAQ, leads, basic chat{RST()}"); spacer()
    biz_map = {"1":"restaurant","2":"salon","3":"shop","4":"clinic","5":"realestate","6":"generic"}
    biz_names = {"restaurant":"Restaurant","salon":"Salon/Spa","shop":"Shop","clinic":"Clinic","realestate":"Real Estate","generic":"General"}
    business_type = ""
    for attempt in range(3):
        bchoice = prompt("Choose", hint="[1-6]")
        business_type = biz_map.get(bchoice, "")
        if business_type: break
        fail("Invalid choice.")
    if not business_type: business_type = "generic"; warn("Using default: General")
    ok(f"Business type: {biz_names[business_type]}")
    skill_presets = {
        "restaurant": {"faq":True,"order_taking":True,"booking":True,"lead_capture":False,"file_creation":False,"complaint_handler":True,"language_detection":False},
        "salon": {"faq":True,"order_taking":False,"booking":True,"lead_capture":True,"file_creation":False,"complaint_handler":True,"language_detection":False},
        "shop": {"faq":True,"order_taking":True,"booking":False,"lead_capture":True,"file_creation":True,"complaint_handler":True,"language_detection":False},
        "clinic": {"faq":True,"order_taking":False,"booking":True,"lead_capture":True,"file_creation":False,"complaint_handler":True,"language_detection":False},
        "realestate": {"faq":True,"order_taking":False,"booking":False,"lead_capture":True,"file_creation":True,"complaint_handler":True,"language_detection":False},
        "generic": {"faq":True,"order_taking":False,"booking":False,"lead_capture":True,"file_creation":False,"complaint_handler":True,"language_detection":False},
    }
    auto_skills = skill_presets.get(business_type, skill_presets["generic"])
    ok("Skills auto-configured for " + biz_names[business_type])

    # STEP 4
    step(4, "Business Info")
    defaults = BUSINESS_DEFAULTS.get(business_type, BUSINESS_DEFAULTS["generic"])
    info(f"Tell us about your business ({D0()}Enter to accept defaults{RST()})"); spacer()
    business_name = prompt("Business name")
    while not business_name: fail("Business name is required."); business_name = prompt("Business name")
    location = prompt("Location", hint="or 'online'") or "Not specified"
    hours = prompt("Operating hours", hint=f"default: {defaults['hours']}") or defaults["hours"]
    phone = prompt("Phone", hint="optional") or "N/A"
    while not validate_phone(phone): fail("Invalid phone format."); phone = prompt("Phone", hint="optional") or "N/A"
    email = prompt("Email", hint="optional") or "N/A"
    while not validate_email(email): fail("Invalid email format."); email = prompt("Email", hint="optional") or "N/A"
    website = prompt("Website", hint="optional") or "N/A"
    while not validate_url(website): fail("Website should start with http:// or https://"); website = prompt("Website", hint="optional") or "N/A"
    ok("Business info saved")

    # STEP 5
    step(5, "Bot Personality & Name")
    info("How should your bot talk to customers?"); spacer()
    bullet(1, f"Professional and formal    {D0()}corporate, legal, finance{RST()}")
    bullet(2, f"Friendly and casual        {D0()}recommended for most businesses{RST()}")
    bullet(3, f"Fun and energetic          {D0()}events, entertainment, youth{RST()}")
    bullet(4, f"Calm and helpful           {D0()}health, support, advisory{RST()}"); spacer()
    pers_map = {"1":"professional","2":"friendly","3":"energetic","4":"calm"}
    pers_names = {"professional":"Professional","friendly":"Friendly","energetic":"Energetic","calm":"Calm"}
    suggested_pers = defaults.get("personality", "friendly")
    suggested_key = next((k for k, v in pers_map.items() if v == suggested_pers), "2")
    info(f"Suggested for {biz_names[business_type]}: {G0()}{suggested_key}{RST()} ({pers_names[suggested_pers]})")
    personality = ""
    for attempt in range(3):
        pchoice = prompt("Choose", hint=f"[1-4, default: {suggested_key}]") or suggested_key
        personality = pers_map.get(pchoice, "")
        if personality: break
        fail("Invalid choice.")
    if not personality: personality = "friendly"; warn("Defaulting to: friendly")
    ok(f"Personality: {pers_names.get(personality, personality)}")
    spacer(); rule(); spacer()
    info("What should customers call the bot?")
    suggested_bot = business_name.split()[0] + "Bot" if business_name else ""
    bot_name = prompt("Bot name", hint=f"default: {suggested_bot}" if suggested_bot else "") or suggested_bot
    while not bot_name: fail("Bot name is required."); bot_name = prompt("Bot name")
    ok(f"Bot name: {bot_name}")

    # STEP 6
    step(6, "Dashboard Setup")
    info("The web dashboard lets you manage the bot from your browser."); spacer()
    port = prompt("Port", hint="default: 8080") or "8080"
    dashboard_password = ""
    for attempt in range(3):
        p1 = prompt_key("Dashboard password (min 8 chars)")
        if len(p1) < 8: fail("Password must be at least 8 characters."); continue
        p2 = prompt_key("Confirm password")
        if p1 != p2: fail("Passwords do not match."); continue
        dashboard_password = p1; break
    if not dashboard_password:
        dashboard_password = generate_secret()[:12]
        warn(f"Auto-generated password: {dashboard_password}")
        warn("Change this from the dashboard after setup!")
    ok(f"Dashboard: http://localhost:{port}")

    # STEP 7
    step(7, "Spend Limits")
    info("Set AI spend limits to prevent unexpected charges.")
    info(f"({D0()}Free-tier users: set to $0.00 for unlimited free models{RST()})"); spacer()
    daily_limit = prompt("Daily limit in USD", hint="default: 2.00") or "2.0"
    monthly_limit = prompt("Monthly limit in USD", hint="default: 10.00") or "10.0"
    try: daily_limit = float(daily_limit)
    except ValueError: daily_limit = 2.0; warn("Invalid number. Using $2.00/day.")
    try: monthly_limit = float(monthly_limit)
    except ValueError: monthly_limit = 10.0; warn("Invalid number. Using $10.00/month.")
    ok(f"Limits: ${daily_limit:.2f}/day, ${monthly_limit:.2f}/month")

    # STEP 8
    step(8, "Channel Settings")
    info("Should the bot respond in all channels or specific ones?"); spacer()
    bullet(1, "All channels (default)"); bullet(2, "Specific channels only"); spacer()
    channel_mode = "all"; allowed_channels = []
    chchoice = prompt("Choose", hint="[1-2]") or "1"
    if chchoice == "2":
        channel_mode = "specific"
        info("Enter channel IDs (comma-separated).")
        info(f"Right-click a channel in Discord > {W0()}Copy Channel ID{RST()}")
        ch_input = prompt("Channel IDs")
        allowed_channels = [c.strip() for c in ch_input.split(",") if c.strip()]
        ok(f"Bot will respond in {len(allowed_channels)} channel(s)")
    else: ok("Bot will respond in all channels")
    spacer(); rule(); spacer()
    info("Where should the bot send admin alerts?")
    info(f"(complaint escalations, daily stats)")
    info(f"Right-click a channel > {W0()}Copy Channel ID{RST()}"); spacer()
    admin_channel = prompt("Admin channel ID", hint="Enter to skip") or ""
    if admin_channel: ok(f"Admin channel: {admin_channel}")
    else: warn("No admin channel set. Alerts will not be sent.")

    # STEP 9: Review
    step(9, "Review Configuration"); spacer()
    bw = 50; f = fill(bw)
    print(f"  {R0()}{BLD()}+{'-'*f}+{RST()}")
    rt = f" {W0()}{BLD()}⚙  CONFIGURATION SUMMARY{RST()}"
    print(f"  {R0()}{BLD()}|{RST()}{rt}{' '*(bw-len_stripped(rt))}{R0()}{BLD()}|{RST()}")
    print(f"  {R0()}{BLD()}+{'-'*f}+{RST()}")

    for label, val in [
        ("Discord Bot", f"ready ({client_id})"), ("AI Provider", provider_names[provider]),
        ("AI Model", model), ("Business Type", biz_names[business_type]),
        ("Business Name", business_name), ("Bot Name", bot_name),
        ("Personality", pers_names.get(personality, personality)), ("Dashboard", f"localhost:{port}"),
        ("Daily Budget", f"${daily_limit:.2f}"), ("Monthly Budget", f"${monthly_limit:.2f}"),
        ("Channels", "All" if channel_mode == "all" else f"{len(allowed_channels)} channel(s)"),
        ("Admin Channel", admin_channel or "None"),
    ]:
        trunc_val = str(val)[:28] if len(str(val)) > 28 else str(val)
        dots = '·' * max(2, bw - 5 - len(label) - len(trunc_val))
        it = f"  {C0()}{label}{RST()} {dots} {W0()}{trunc_val}{RST()} "
        print(f"  {R0()}{BLD()}|{RST()}{it}{' '*(bw-len_stripped(it))}{R0()}{BLD()}|{RST()}")

    print(f"  {R0()}{BLD()}+{'-'*f}+{RST()}")
    sh = f" {Y0()}Skills:{RST()}"
    print(f"  {R0()}{BLD()}|{RST()}{sh}{' '*(bw-len_stripped(sh))}{R0()}{BLD()}|{RST()}")
    for skill, enabled in auto_skills.items():
        icon = f"{G0()}ON {RST()}" if enabled else f"{D0()}OFF{RST()}"
        sk = f" {icon} {L0()}{skill.replace('_', ' ').title()}{RST()}"
        print(f"  {R0()}{BLD()}|{RST()}{sk}{' '*(bw-len_stripped(sk))}{R0()}{BLD()}|{RST()}")
    print(f"  {R0()}{BLD()}+{'-'*f}+{RST()}"); spacer()

    print(f"  {W0()}{BLD()}  Proceed?{RST()}")
    print(f"    {G0()}Y{RST()} = Write config and finish")
    print(f"    {Y0()}E{RST()} = Re-edit from the beginning")
    print(f"    {R0()}C{RST()} = Cancel (nothing written)")
    spacer()
    confirm_choice = prompt("Choose", hint="[Y/e/c]") or "y"
    if confirm_choice.lower() == "c": info("Setup cancelled. Nothing was written."); sys.exit(0)
    elif confirm_choice.lower() == "e": warn("Restarting wizard..."); spacer(); return "reedit"

    # STEP 10
    step(10, "Generating Files")
    ensure_dirs(); ok("Directories created")
    secret_key = generate_secret()
    config = {
        "discord": {"token": token, "client_id": client_id, "invite_url": invite_url, "prefix": "!"},
        "ai": {"provider": provider, "api_key": api_key if provider != "ollama" else "", "model": model, "fallback_model": "", "max_tokens": 1000, "temperature": 0.7, "daily_spend_limit": daily_limit, "monthly_spend_limit": monthly_limit},
        "bot": {"name": bot_name, "personality": personality, "business_type": business_type, "language": "english"},
        "dashboard": {"host": "127.0.0.1", "port": int(port), "secret_key": secret_key, "password": dashboard_password},
        "skills": auto_skills,
        "memory": {"enabled": True, "max_per_user": 50, "auto_extract": True, "retention_days": 90},
        "files": {"enabled": True, "storage_path": "storage/files/", "max_file_size_mb": 25, "link_expiry_days": 7, "allowed_types": ["pdf", "docx", "xlsx", "png", "jpg", "txt", "csv"]},
        "channels": {"mode": channel_mode, "allowed": allowed_channels, "admin_channel": admin_channel},
        "_skills": auto_skills
    }
    write_config(config); write_skills(config); del config["_skills"]
    template = load_template(business_type)
    soul_content = template.format(bot_name=bot_name, personality=personality, business_name=business_name, industry=biz_names[business_type].lower(), location=location, hours=hours, phone=phone, email=email, website=website)
    with open("config/soul.md", "w") as f: f.write(soul_content)
    ok("Soul.md generated from template")
    init_db()
    finish_box(config)
    return "done"


if __name__ == "__main__":
    asyncio.run(run_wizard())
