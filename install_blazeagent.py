#!/usr/bin/env python3
"""
Blaze-Agent Installer v2.0
==========================
Downloads and sets up Blaze-Agent on any machine.

Usage:
    python install_blazeagent.py              interactive install
    python install_blazeagent.py --yes        non-interactive
    python install_blazeagent.py --uninstall  remove Blaze-Agent
    python install_blazeagent.py --status     check if installed
"""

import sys
import os
import subprocess
import platform
import shutil
import threading
import time
import zipfile

# ═══════════════════════════════════════════════════
#  CONFIG
# ═══════════════════════════════════════════════════

REPO_OWNER  = "Phantom-Nuggie"
REPO_NAME   = "Blaze-Discord-Agent"
RELEASE_TAG = "v1.0"
ZIP_NAME    = "Blaze-Agent.zip"
MIN_PYTHON  = (3, 10)

RELEASE_URL = (
    f"https://github.com/{REPO_OWNER}/{REPO_NAME}"
    f"/releases/latest/download/{ZIP_NAME}"
)

CORE_PACKAGES = [
    "discord.py>=2.3.0",
    "fastapi>=0.100.0",
    "uvicorn>=0.23.0",
    "pyyaml>=6.0",
    "aiohttp>=3.8.0",
    "python-dotenv>=1.0.0",
    "jinja2>=3.1.0",
    "reportlab>=4.0.0",
    "python-docx>=0.8.11",
    "openpyxl>=3.1.0",
    "aiosqlite>=0.19.0",
]

# ═══════════════════════════════════════════════════
#  COLORS
# ═══════════════════════════════════════════════════

_use_color = True

def _check_color():
    global _use_color
    if os.getenv("NO_COLOR"):
        _use_color = False
        return
    if platform.system() == "Windows":
        _use_color = bool(os.getenv("ANSICON") or os.getenv("WT_SESSION"))
    else:
        _use_color = hasattr(sys.stdout, "isatty") and sys.stdout.isatty()

_check_color()

class _C:
    R0   = "\033[38;2;255;0;60m"
    G0   = "\033[38;2;0;255;136m"
    Y0   = "\033[38;2;255;204;0m"
    B0   = "\033[38;2;64;156;255m"
    M0   = "\033[38;2;170;68;255m"
    C0   = "\033[38;2;0;204;204m"
    D0   = "\033[38;2;90;90;90m"
    D1   = "\033[38;2;60;60;60m"
    L0   = "\033[38;2;170;170;170m"
    W0   = "\033[38;2;255;255;255m"
    BLD  = "\033[1m"
    DIM  = "\033[2m"
    RST  = "\033[0m"

def clr(code):
    return code if _use_color else ""

# shortcuts
R0  = lambda: clr(_C.R0)
G0  = lambda: clr(_C.G0)
Y0  = lambda: clr(_C.Y0)
D0  = lambda: clr(_C.D0)
D1  = lambda: clr(_C.D1)
L0  = lambda: clr(_C.L0)
W0  = lambda: clr(_C.W0)
BLD = lambda: clr(_C.BLD)
DIM = lambda: clr(_C.DIM)
RST = lambda: clr(_C.RST)
C0  = lambda: clr(_C.C0)
M0  = lambda: clr(_C.M0)
B0  = lambda: clr(_C.B0)

# ═══════════════════════════════════════════════════
#  UI HELPERS
# ═══════════════════════════════════════════════════

def twidth():
    try:
        return max(40, min(80, os.get_terminal_size().columns - 2))
    except OSError:
        return 56

def clear():
    sys.stdout.write("\033[2J\033[H" if _use_color else "\n")
    sys.stdout.flush()

def rule(char="═", color=None):
    w = twidth()
    c = color or D0
    print(f"  {c()}{char * (w - 4)}{RST()}")

# ═══════════════════════════════════════════════════
#  BANNER
# ═══════════════════════════════════════════════════

def banner():
    r = R0(); b = BLD(); d = D0(); rst = RST()
    print(f"""
  {r}{b}  ██████╗ ██╗      █████╗ ███████╗███████╗{rst}
  {r}{b}  ██╔══██╗██║     ██╔══██╗╚══███╔╝██╔════╝{rst}
  {r}{b}  ██████╔╝██║     ███████║  ███╔╝ █████╗  {rst}
  {r}{b}  ██╔══██╗██║     ██╔══██║ ███╔╝  ██╔══╝  {rst}
  {r}{b}  ██████╔╝███████╗██║  ██║███████╗███████╗{rst}
  {r}{b}  ╚═════╝ ╚══════╝╚═╝  ╚═╝╚══════╝╚══════╝{rst}
  {d}{'─' * 44}{rst}
  {W0()}{b}  Self-Service AI Discord Agent{rst}
  {d}  Installer v2.0{rst}
  {d}{'─' * 44}{rst}""")

# ═══════════════════════════════════════════════════
#  STATUS LABELS
# ═══════════════════════════════════════════════════

def step(num, total, text):
    print(f"\n  {R0()}{BLD()}[{num}/{total}]{RST()}  {W0()}{text}{RST()}")
    rule("─", D1)

def ok(msg, indent=4):
    print(f"{' '*indent}{G0()}✔{RST()}  {msg}")

def info(msg, indent=4):
    print(f"{' '*indent}{L0()}{msg}{RST()}")

def warn(msg, indent=4):
    print(f"{' '*indent}{Y0()}▸  {msg}{RST()}")

def fail(msg, indent=4):
    print(f"{' '*indent}{R0()}✘{RST()}  {R0()}{msg}{RST()}")

def bullet(num, text, indent=6):
    print(f"{' '*indent}{R0()}{BLD()}⦿ {num}{RST()}  {text}")

# ═══════════════════════════════════════════════════
#  SPINNER
# ═══════════════════════════════════════════════════

class Spinner:
    FRAMES = ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"]

    def __init__(self, msg=""):
        self.msg = msg
        self._stop = threading.Event()
        self._thread = None
        self._ok = False
        self._err = None

    def _run(self):
        i = 0
        while not self._stop.is_set():
            f = self.FRAMES[i % len(self.FRAMES)]
            line = f"    {R0()}{f}{RST()} {self.msg}  "
            sys.stdout.write("\r" + line)
            sys.stdout.flush()
            i += 1
            time.sleep(0.08)
        # clear
        sys.stdout.write("\r" + " " * (len(self.msg) + 12) + "\r")
        sys.stdout.flush()

    def __enter__(self):
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, *exc):
        self._stop.set()
        if self._thread:
            self._thread.join(1)
        if self._err:
            fail(str(self._err))
        elif self._ok:
            ok(self.msg)

    def finish(self, ok=True, msg=None, err=None):
        self._ok = ok
        self._err = err
        if msg:
            self.msg = msg

# ═══════════════════════════════════════════════════
#  PROGRESS BAR
# ═══════════════════════════════════════════════════

def download_progress(current, total, label="Downloading"):
    if total <= 0:
        return
    pct = current / total
    filled = int(30 * pct)
    bar = (f"{R0()}{'█' * filled}{RST()}"
           f"{D0()}{'░' * (30 - filled)}{RST()}")
    s = _human(current)
    t = _human(total)
    line = (f"\r    {label}: {bar} "
            f"{L0()}{pct*100:5.1f}%{RST()} "
            f"{D0()}({s}/{t}){RST()}  ")
    sys.stdout.write(line)
    sys.stdout.flush()
    if current >= total:
        print()

def _human(n):
    for u in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f}{u}"
        n /= 1024
    return f"{n:.1f}TB"

# ═══════════════════════════════════════════════════
#  SYSTEM CHECKS
# ═══════════════════════════════════════════════════

def check_python():
    v = sys.version_info[:2]
    if v < MIN_PYTHON:
        fail(f"Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+ required. Found {v[0]}.{v[1]}")
        return False
    ok(f"Python {v[0]}.{v[1]}")
    return True

def check_pip():
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "--version"],
            capture_output=True, check=True
        )
        ok("pip available")
        return True
    except subprocess.CalledProcessError:
        fail("pip not found")
        info("Fix: sudo apt install python3-pip")
        return False

def check_git():
    try:
        subprocess.run(
            ["git", "--version"], capture_output=True, check=True
        )
        ok("git available")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        warn("git not found — will use zip download")
        return False

def check_internet():
    import urllib.request
    try:
        urllib.request.urlopen("https://github.com", timeout=5)
        ok("Internet connection")
        return True
    except Exception:
        fail("No internet connection")
        return False

# ═══════════════════════════════════════════════════
#  DOWNLOAD + EXTRACT
# ═══════════════════════════════════════════════════

def download_source(target_dir):
    """Download Blaze-Agent from GitHub release, verify, extract."""
    import urllib.request

    if os.path.exists(target_dir):
        warn(f"Directory exists: {target_dir}")
        try:
            resp = input(f"    Replace? [{G0()}Y{RST()}/{D0()}n{RST()}]: ").strip().lower()
        except EOFError:
            print()
            resp = "y"
        if resp == "n":
            info("Using existing installation.")
            return target_dir
        info("Removing old files...")
        shutil.rmtree(target_dir)

    os.makedirs(target_dir, exist_ok=True)

    info(f"Source: github.com/{REPO_OWNER}/{REPO_NAME}/releases")

    tmp_zip = os.path.join("/tmp", "blaze_download.zip")

    try:
        _dl(RELEASE_URL, tmp_zip)
    except Exception as e:
        try:
            urllib.request.urlretrieve(RELEASE_URL, tmp_zip)
        except Exception as e2:
            fail(f"Download failed: {e2}")
            info(f"Manual: {RELEASE_URL}")
            sys.exit(1)

    # Verify
    try:
        with zipfile.ZipFile(tmp_zip, "r") as zf:
            bad = zf.testzip()
            if bad:
                fail(f"Corrupt zip (bad: {bad})")
                sys.exit(1)
        ok(f"Download verified ({_human(os.path.getsize(tmp_zip))})")
    except zipfile.BadZipFile:
        fail("Not a valid zip archive")
        sys.exit(1)

    # Extract
    info("Extracting...")
    try:
        with zipfile.ZipFile(tmp_zip, "r") as zf:
            # GitHub release zips may or may not wrap files in a top-level
            # folder.  Detect and handle both cases.
            names = zf.namelist()
            top_items = set(n.split("/")[0] for n in names if n.strip())

            tmp_extract = tmp_zip + "_extract"
            os.makedirs(tmp_extract, exist_ok=True)
            zf.extractall(tmp_extract)

            if len(top_items) == 1:
                # Single wrapper folder: move its contents
                wrapper = os.path.join(tmp_extract, top_items.pop())
                for item in os.listdir(wrapper):
                    src = os.path.join(wrapper, item)
                    dst = os.path.join(target_dir, item)
                    if os.path.exists(dst):
                        if os.path.isdir(dst):
                            shutil.rmtree(dst)
                        else:
                            os.unlink(dst)
                    shutil.move(src, dst)
            else:
                # Multiple root items: move everything
                for item in os.listdir(tmp_extract):
                    src = os.path.join(tmp_extract, item)
                    dst = os.path.join(target_dir, item)
                    if os.path.exists(dst):
                        if os.path.isdir(dst):
                            shutil.rmtree(dst)
                        else:
                            os.unlink(dst)
                    shutil.move(src, dst)

            shutil.rmtree(tmp_extract, ignore_errors=True)
        ok(f"Extracted to: {target_dir}")
    except Exception as e:
        fail(f"Extraction failed: {e}")
        sys.exit(1)
    finally:
        if os.path.exists(tmp_zip):
            os.unlink(tmp_zip)

    return target_dir


def _dl(url, dest):
    import urllib.request
    req = urllib.request.Request(url, headers={"User-Agent": "Blaze-Installer/2.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        total = int(resp.headers.get("Content-Length", 0))
        got = 0
        with open(dest, "wb") as f:
            while True:
                chunk = resp.read(8192)
                if not chunk:
                    break
                f.write(chunk)
                got += len(chunk)
                if total > 0:
                    download_progress(got, total)
    if total <= 0:
        ok(f"Downloaded {ZIP_NAME}")

# ═══════════════════════════════════════════════════
#  DEPENDENCIES
# ═══════════════════════════════════════════════════

def install_deps(project_dir):
    venv = os.path.join(project_dir, ".venv")
    is_win = platform.system() == "Windows"
    pip  = os.path.join(venv, "Scripts" if is_win else "bin", "pip")
    pyp  = os.path.join(venv, "Scripts" if is_win else "bin", "python")

    info("Creating virtual environment...")
    try:
        subprocess.run(
            [sys.executable, "-m", "venv", venv],
            check=True, capture_output=True
        )
        ok("Virtual environment ready")
    except subprocess.CalledProcessError:
        fail("Failed to create .venv")
        info("Fix: sudo apt install python3-venv")
        sys.exit(1)

    # Upgrade pip
    subprocess.run([pyp, "-m", "pip", "install", "--upgrade", "pip"],
                   capture_output=True)

    req = os.path.join(project_dir, "requirements.txt")
    if os.path.exists(req):
        info("Installing dependencies...")
        try:
            r = subprocess.run([pip, "install", "-r", req],
                               capture_output=True, text=True, timeout=300)
            if r.returncode != 0:
                warn("Some requirements failed, falling back to core...")
                _inst_core(pip)
            else:
                ok("Dependencies installed")
        except subprocess.TimeoutExpired:
            fail("Dependency install timed out")
            sys.exit(1)
    else:
        warn("requirements.txt missing — installing core...")
        _inst_core(pip)

    return pyp


def _inst_core(pip):
    r = subprocess.run([pip, "install"] + CORE_PACKAGES,
                       capture_output=True, text=True, timeout=300)
    if r.returncode == 0:
        ok("Core packages installed")
    else:
        fail("Some packages failed")
        info(f"Manual: {pip} install <packages>")

# ═══════════════════════════════════════════════════
#  LAUNCHERS
# ═══════════════════════════════════════════════════

def make_launchers(project_dir, python_path):
    bash = "#!/usr/bin/env bash\n# Blaze-Agent Launcher\ncd \"$(dirname \"$0\")\"\nsource .venv/bin/activate 2>/dev/null || true\npython run.py \"$@\"\n"
    sh = os.path.join(project_dir, "start.sh")
    with open(sh, "w") as f:
        f.write(bash)
    os.chmod(sh, 0o755)

    bat = "@echo off\r\nREM Blaze-Agent Launcher\r\ncd /d \"%~dp0\"\r\ncall .venv\\Scripts\\activate.bat 2>nul\r\npython run.py %*\r\n"
    with open(os.path.join(project_dir, "start.bat"), "w") as f:
        f.write(bat)

    ok("Launcher scripts created (start.sh / start.bat)")

    # Install the blzed system command
    _install_blazed(project_dir, python_path)

    # Write VERSION file for update tracking
    _write_version(project_dir, RELEASE_TAG.lstrip("v"))


def _install_blazed(project_dir, python_path):
    """Install the blzed terminal command in ~/.local/bin."""
    bin_dir = os.path.join(os.path.expanduser("~"), ".local", "bin")
    os.makedirs(bin_dir, exist_ok=True)

    is_win = platform.system() == "Windows"

    if is_win:
        cmd_path = os.path.join(bin_dir, "blzed.cmd")
        lines = [
            "@echo off",
            "REM Blaze-Agent CLI",
            f'set PROJECT_DIR={project_dir}',
            f'set PYTHON_PATH={python_path}',
            'cd /d "%PROJECT_DIR%"',
            'if "%1"=="start" goto run',
            'if "%1"=="status" goto status',
            'if "%1"=="update" goto update',
            'if "%1"=="setup" goto setup',
            'if "%1"=="version" goto version',
            'if "%1"=="" goto run',
            'echo Unknown: %1',
            'goto :eof',
            ':run',
            'call .venv\\Scripts\\activate.bat 2>nul',
            'python run.py',
            'goto :eof',
            ':status',
            'if exist config\\config.yaml (echo Config: OK) else (echo Config: missing)',
            'goto :eof',
            ':update',
            'echo Run: python install_blazeagent.py --yes',
            'goto :eof',
            ':setup',
            'call .venv\\Scripts\\activate.bat 2>nul',
            'python setup.py',
            'goto :eof',
            ':version',
            'type VERSION',
        ]
        with open(cmd_path, "w") as f:
            f.write("\r\n".join(lines) + "\r\n")
    else:
        cmd_path = os.path.join(bin_dir, "blzed")
        script = _blazed_script(project_dir, python_path)
        with open(cmd_path, "w") as f:
            f.write(script)
        os.chmod(cmd_path, 0o755)

    # Ensure ~/.local/bin in PATH
    _ensure_path(bin_dir)

    ok(f"Terminal command installed: blzed")


def _ensure_path(bin_dir):
    """Add bin_dir to PATH in shell rc if missing."""
    if os.name == "nt":
        return
    home = os.path.expanduser("~")
    shell = os.environ.get("SHELL", "")
    if "zsh" in shell:
        rc = os.path.join(home, ".zshrc")
    else:
        rc = os.path.join(home, ".bashrc")
    if not os.path.exists(rc):
        return
    marker = "# Blaze-Agent blzed CLI"
    export_line = f'export PATH="{bin_dir}:$PATH"'
    with open(rc, "r") as f:
        content = f.read()
    if ".local/bin" not in content:
        with open(rc, "a") as f:
            f.write(f"\n{marker}\n{export_line}\n")
        ok(f"Added {bin_dir} to PATH ({os.path.basename(rc)})")


def _blazed_script(project_dir, python_path):
    """Generate the blzed bash script content."""
    # Use a simple template with ^PLACEHOLDER^ substitution
    # to avoid f-string / bash quoting nightmares
    tpl = []
    tpl.append("#!/usr/bin/env bash")
    tpl.append("# Blaze-Agent CLI — blzed")
    tpl.append("PROJECT_DIR=\"^PD^\"")
    tpl.append("PYTHON=\"^PP^\"")
    tpl.append("VERSION_FILE=\"$PROJECT_DIR/VERSION\"")
    tpl.append("REPO_API=\"https://api.github.com/repos/Phantom-Nuggie/Blaze-Discord-Agent/releases/latest\"")
    tpl.append("REPO_RAW=\"https://raw.githubusercontent.com/Phantom-Nuggie/Blaze-Discord-Agent/main\"")
    tpl.append("")
    tpl.append("cd \"$PROJECT_DIR\" 2>/dev/null || {")
    tpl.append("  echo \"\"; echo \"  Error: Project dir not found: $PROJECT_DIR\"")
    tpl.append("  echo \"  Fix: reinstall with python3 install_blazeagent.py\"; echo \"\"; exit 1")
    tpl.append("}")
    tpl.append("")
    tpl.append("_gver() { [ -f \"$VERSION_FILE\" ] && cat \"$VERSION_FILE\" || echo \"unknown\"; }")
    tpl.append("")
    tpl.append("_glatest() {")
    tpl.append("  local v=\"\"")
    tpl.append("  v=$(curl -fsSL --max-time 5 \"$REPO_API\" 2>/dev/null | python3 -c \"")
    tpl.append("import sys,json")
    tpl.append("try:")
    tpl.append("  d=json.load(sys.stdin)")
    tpl.append("  print(d.get(\\'tag_name\\',\\'\\').lstrip(\\'v\\'))")
    tpl.append("except:")
    tpl.append("  print(\\'\\')")
    tpl.append("\" 2>/dev/null)")
    tpl.append("  [ -z \"$v\" ] && v=$(curl -fsSL --max-time 5 \"$REPO_RAW/VERSION\" 2>/dev/null | tr -d '[:space:]')")
    tpl.append("  echo \"$v\"")
    tpl.append("}")
    tpl.append("")
    tpl.append("case \"${1:-start}\" in")
    tpl.append("  start)")
    tpl.append("    echo \"\"; echo \"  Starting Blaze-Agent...\"; echo \"\"")
    tpl.append("    source \"$PROJECT_DIR/.venv/bin/activate\" 2>/dev/null")
    tpl.append("    exec python run.py")
    tpl.append("    ;;")
    tpl.append("  stop)")
    tpl.append("    echo \"  Stop the bot with Ctrl+C.\"")
    tpl.append("    ;;")
    tpl.append("  status)")
    tpl.append("    v=$(_gver); l=$(_glatest)")
    tpl.append("    echo \"\"; printf \"  %-12sBlaze-Agent v%s\\n\" \"\" \"$v\"")
    tpl.append("    echo \"  ───────────────────────────\"")
    tpl.append("    printf \"  %-12s%s\\n\" \"Dir:\" \"$PROJECT_DIR\"")
    tpl.append("    [ -f \"$PROJECT_DIR/config/config.yaml\" ] && printf \"  %-12s%s\\n\" \"Config:\" \"OK\" || printf \"  %-12s%s\\n\" \"Config:\" \"--missing--\"")
    tpl.append("    [ -d \"$PROJECT_DIR/.venv\" ] && printf \"  %-12s%s\\n\" \"Venv:\" \"OK\" || printf \"  %-12s%s\\n\" \"Venv:\" \"--missing--\"")
    tpl.append("    [ -n \"$l\" ] && [ \"$l\" != \"404\" ] && [ \"$v\" != \"$l\" ] && printf \"  %-12s%s\\n\" \"Update:\" \"v$l available\"")
    tpl.append("    echo \"\"")
    tpl.append("    ;;")
    tpl.append("  update)")
    tpl.append("    cur=$(_gver); lat=$(_glatest)")
    tpl.append("    [ -z \"$lat\" ] || [ \"$lat\" = \"404\" ] && { echo \"  Error: Cannot reach update server.\"; exit 1; }")
    tpl.append("    echo \"\"; echo \"  Current: v$cur\"; echo \"  Latest:  v$lat\"")
    tpl.append("    [ \"$cur\" = \"$lat\" ] && { echo \"  Already up to date.\"; echo \"\"; exit 0; }")
    tpl.append("    echo \"\"; echo \"  Updating...\"")
    tpl.append("    tmp=$(mktemp -d)")
    tpl.append("    curl -fsSL -o \"$tmp/blaze-agent.zip\" \\")
    tpl.append("      \"https://github.com/Phantom-Nuggie/Blaze-Discord-Agent/releases/latest/download/Blaze-Agent.zip\" || {")
    tpl.append("      echo \"  Download failed.\"; rm -rf \"$tmp\"; exit 1; }")
    tpl.append("    cp -r \"$PROJECT_DIR/config\" \"$tmp/bak_cfg\" 2>/dev/null")
    tpl.append("    cp -r \"$PROJECT_DIR/storage\" \"$tmp/bak_sto\" 2>/dev/null")
    tpl.append("    unzip -qo \"$tmp/blaze-agent.zip\" -d \"$tmp/ext\"")
    tpl.append("    ext=$(find \"$tmp/ext\" -maxdepth 1 -mindepth 1 -type d | head -1)")
    tpl.append("    cp -r \"$ext/.\" \"$PROJECT_DIR/\"")
    tpl.append("    cp -r \"$tmp/bak_cfg/.\" \"$PROJECT_DIR/config/\" 2>/dev/null")
    tpl.append("    cp -r \"$tmp/bak_sto/.\" \"$PROJECT_DIR/storage/\" 2>/dev/null")
    tpl.append("    echo \"  Installing dependencies...\"")
    tpl.append("    \"$PROJECT_DIR/.venv/bin/pip\" install -q -r \"$PROJECT_DIR/requirements.txt\" 2>/dev/null")
    tpl.append("    echo \"$lat\" > \"$VERSION_FILE\"")
    tpl.append("    rm -rf \"$tmp\"")
    tpl.append("    echo \"\"; echo \"  Updated: v$cur → v$lat\"")
    tpl.append("    echo \"  Run '\\''blzed start'\\'' to restart.\"; echo \"\"")
    tpl.append("    ;;")
    tpl.append("  setup)")
    tpl.append("    source \"$PROJECT_DIR/.venv/bin/activate\" 2>/dev/null")
    tpl.append("    exec python setup.py")
    tpl.append("    ;;")
    tpl.append("  version|--version|-v)")
    tpl.append("    echo \"  Blaze-Agent v$(_gver)\"")
    tpl.append("    ;;")
    tpl.append("  help|--help|-h)")
    tpl.append("    echo \"\"; echo \"  blzed — Blaze-Agent CLI\"; echo \"\"")
    tpl.append("    echo \"  start     Start bot (default)\"")
    tpl.append("    echo \"    status    Show status\"")
    tpl.append("    echo \"    update    Update to latest\"")
    tpl.append("    echo \"    setup     Config wizard\"")
    tpl.append("    echo \"    version   Show version\"")
    tpl.append("    echo \"    help      This help\"; echo \"\"")
    tpl.append("    ;;")
    tpl.append("  *) echo \"  Unknown: $1. Run '\\''blzed help'\\''\"; exit 1 ;;")
    tpl.append("esac")
    tpl.append("")

    result = "\n".join(tpl)
    result = result.replace("^PD^", project_dir)
    result = result.replace("^PP^", python_path)
    return result


def _write_version(project_dir, version):
    """Write VERSION file for update tracking."""
    with open(os.path.join(project_dir, "VERSION"), "w") as f:
        f.write(version.strip() + "\n")


# ═══════════════════════════════════════════════════
#  STATUS / UNINSTALL
# ═══════════════════════════════════════════════════

def show_status(install_dir):
    if not os.path.isdir(install_dir):
        warn("Not installed.")
        return
    ok(f"Install dir:  {install_dir}")
    ok(f"Source code:  {'yes' if os.path.isfile(os.path.join(install_dir,'setup.py')) else 'no'}")
    ok(f"Virtual env:  {'yes' if os.path.isdir(os.path.join(install_dir,'.venv')) else 'no'}")
    ok(f"Configured:  {'yes' if os.path.isfile(os.path.join(install_dir,'config','config.yaml')) else 'no'}")

def do_uninstall(install_dir):
    if not os.path.isdir(install_dir):
        warn(f"Not found: {install_dir}")
        return
    warn(f"This will delete: {install_dir}")
    resp = input(f"    Confirm? [{R0()}y{RST()}/{D0()}N{RST()}]: ").strip().lower()
    if resp != "y":
        info("Cancelled.")
        return
    try:
        shutil.rmtree(install_dir)
        ok(f"Removed: {install_dir}")
    except Exception as e:
        fail(f"Could not remove: {e}")

# ═══════════════════════════════════════════════════
#  SUMMARY BOX
# ═══════════════════════════════════════════════════

def summary(project_dir, python_path):
    bw = 50
    r = R0(); b = BLD(); d = D0(); rst = RST()
    w = W0(); g = G0()

    print()
    print(f"  {r}{b}╔{'═' * bw}╗{rst}")
    print(f"  {r}{b}║{'  INSTALLATION COMPLETE':^{bw}}║{rst}")
    print(f"  {r}{b}╠{'═' * bw}╣{rst}")

    loc = project_dir if len(project_dir) <= bw-13 else "..." + project_dir[-(bw-16):]
    print(f"  {r}{b}║{rst}  Location:  {w}{loc:<{bw-13}}{r}{b}║{rst}")

    pyp_short = python_path if len(python_path) <= bw-13 else "..." + python_path[-(bw-16):]
    print(f"  {r}{b}║{rst}  Python:    {w}{pyp_short:<{bw-13}}{r}{b}║{rst}")

    print(f"  {r}{b}╠{'═' * bw}╣{rst}")
    print(f"  {r}{b}║{rst}  {b}Next steps:{' ' * (bw-13)}{r}{b}║{rst}")

    cmds = [
        ("blzed setup", "Configure your bot"),
        ("blzed start", "Start the bot"),
        ("blzed status", "Check status"),
    ]
    for cmd, _ in cmds:
        trunc = cmd[:bw-9]
        pad = bw - 9 - len(trunc)
        print(f"  {r}{b}║{rst}    {g}→{rst} {trunc}{' '*pad}{r}{b}║{rst}")

    docs = "Docs: github.com/Blaze-Discord-Agent"
    if len(docs) > bw - 4:
        docs = docs[:bw-7] + "..."
    print(f"  {r}{b}║{rst}  {d}{docs}{rst}{' '*max(0,bw-4-len(docs))}{r}{b}║{rst}")
    print(f"  {r}{b}╚{'═' * bw}╝{rst}")
    print()

# ═══════════════════════════════════════════════════
#  INPUT
# ═══════════════════════════════════════════════════

def ask(prompt, default=""):
    if default:
        full = f"    {prompt} [{G0()}{default}{RST()}]: "
    else:
        full = f"    {prompt}: "
    try:
        resp = input(full).strip()
    except EOFError:
        print()
        resp = ""
    return resp if resp else default

# ═══════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════

def main():
    auto    = "--yes" in sys.argv or "-y" in sys.argv
    if not auto and not (hasattr(sys.stdin, "isatty") and sys.stdin.isatty()):
        auto = True 
    uninst  = "--uninstall" in sys.argv
    status  = "--status" in sys.argv
    default_dir = os.path.join(os.path.expanduser("~"), "Blaze-Agent")

    if status:
        banner()
        step(1, 1, "Status")
        show_status(default_dir)
        return

    if uninst:
        banner()
        step(1, 1, "Uninstall")
        do_uninstall(default_dir)
        return

    clear()
    banner()
    TOTAL = 5

    # ── Step 1 ──
    step(1, TOTAL, "System checks")
    if not check_python():
        sys.exit(1)
    if not check_pip():
        sys.exit(1)
    check_git()
    if not check_internet():
        sys.exit(1)

    # ── Step 2 ──
    step(2, TOTAL, "Install location")
    if auto:
        target = default_dir
        info(f"Installing to: {target}")
    else:
        info(f"Default: {default_dir}")
        resp = ask("Install here", "Y").lower()
        if resp in ("n", "no"):
            p = ask("Enter path").strip()
            target = os.path.abspath(p) if p else default_dir
        else:
            target = default_dir
    info(f"Target: {target}")

    # ── Step 3 ──
    step(3, TOTAL, "Download")
    project_dir = download_source(target)

    # ── Step 4 ──
    step(4, TOTAL, "Dependencies")
    python_path = install_deps(project_dir)

    # ── Step 5 ──
    step(5, TOTAL, "Finalizing")
    make_launchers(project_dir, python_path)

    # ── Done ──
    summary(project_dir, python_path)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n  {Y0()}Installation cancelled.{RST()}")
        sys.exit(0)
