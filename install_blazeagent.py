#!/usr/bin/env python3
"""
Blaze-Agent Installer
=====================
Downloads and sets up Blaze-Agent on any machine.

Usage:
    python install_blazeagent.py

    OR download and run:
    curl -fsSL https://blze.ai/install.py | python3

What this does:
    1. Checks Python version
    2. Downloads Blaze-Agent source
    3. Creates a virtual environment
    4. Installs dependencies
    5. Provides next steps
"""

import sys
import os
import subprocess
import platform

# --- Configuration ---
REPO_URL = "https://github.com/zerochunks/Blaze-Agent/archive/refs/heads/main.zip"
PROJECT_NAME = "Blaze-Agent"
MIN_PYTHON = (3, 10)

# --- ANSI colors ---
GREEN = "\033[92m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"

def ok(msg):      print(f"  {GREEN}✓ {msg}{RESET}")
def info(msg):    print(f"  {CYAN}  {msg}{RESET}")
def warn(msg):    print(f"  {YELLOW}⚠ {msg}{RESET}")
def fail(msg):    print(f"  {RED}✗ {msg}{RESET}")

def banner():
    print(f"""
{CYAN}{BOLD}
  ____  _            _       _____ _
 |  _ \| |          | |     / ____| |
 | |_) | | __ _  __| | __ _| |    | |_
 |  _ <| |/ _' |/ _' |/ _' | |    | __|
 | |_) | | (_| | (_| | (_| | |____| |_
 |____/|_|\__,_|\__,_|\__,_|\______|
{RESET}
{BOLD}  Installer v1.0{RESET}
""")

def check_python():
    """Verify Python version."""
    version = sys.version_info[:2]
    if version < MIN_PYTHON:
        fail(f"Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+ required. You have {version[0]}.{version[1]}")
        sys.exit(1)
    ok(f"Python {version[0]}.{version[1]} detected")

def check_git():
    """Check if git is available."""
    try:
        subprocess.run(["git", "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def check_pip():
    """Check if pip is available."""
    try:
        subprocess.run([sys.executable, "-m", "pip", "--version"], capture_output=True, check=True)
        return True
    except subprocess.CalledProcessError:
        return False

def install_dependencies(project_dir):
    """Create venv and install requirements."""
    venv_dir = os.path.join(project_dir, ".venv")

    # Create virtual environment
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

    # Determine pip path
    if platform.system() == "Windows":
        pip_path = os.path.join(venv_dir, "Scripts", "pip")
        python_path = os.path.join(venv_dir, "Scripts", "python")
    else:
        pip_path = os.path.join(venv_dir, "bin", "pip")
        python_path = os.path.join(venv_dir, "bin", "python")

    # Upgrade pip
    info("Upgrading pip...")
    subprocess.run(
        [python_path, "-m", "pip", "install", "--upgrade", "pip"],
        capture_output=True
    )

    # Install requirements
    req_file = os.path.join(project_dir, "requirements.txt")
    if os.path.exists(req_file):
        info("Installing dependencies (this may take a minute)...")
        try:
            subprocess.run(
                [pip_path, "install", "-r", req_file],
                check=True, capture_output=True
            )
            ok("All dependencies installed")
        except subprocess.CalledProcessError:
            fail("Failed to install dependencies.")
            info(f"Try manually: {pip_path} install -r requirements.txt")
            sys.exit(1)
    else:
        warn("requirements.txt not found. Installing core packages...")
        subprocess.run(
            [pip_path, "install", "discord.py", "fastapi", "uvicorn", "pyyaml",
             "aiohttp", "jinja2", "python-dotenv", "reportlab", "python-docx",
             "openpyxl", "aiosqlite"],
            check_output=True
        )

    return python_path

def download_source(target_dir):
    """Download Blaze-Agent source code."""
    if os.path.exists(target_dir):
        warn(f"Directory '{target_dir}' already exists.")
        choice = input("  Overwrite? [y/N]: ").strip().lower()
        if choice != "y":
            info("Using existing directory.")
            return target_dir

    # Try git clone first
    if check_git():
        info("Downloading via git...")
        try:
            if os.path.exists(target_dir):
                import shutil
                shutil.rmtree(target_dir)
            subprocess.run(
                ["git", "clone", "--depth=1",
                 "https://github.com/zerochunks/Blaze-Agent.git",
                 target_dir],
                check=True
            )
            ok(f"Downloaded to: {target_dir}")
            return target_dir
        except subprocess.CalledProcessError:
            warn("Git download failed. Trying alternative method...")

    # Alternative: download zip
    info("Downloading source archive...")
    try:
        import urllib.request
        import zipfile
        import shutil
        import tempfile

        if os.path.exists(target_dir):
            shutil.rmtree(target_dir)

        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
            urllib.request.urlretrieve(REPO_URL, tmp.name)
            with zipfile.ZipFile(tmp.name, "r") as z:
                z.extractall(tempfile.gettempdir())

            # Rename extracted folder
            extracted = os.path.join(tempfile.gettempdir(), f"{PROJECT_NAME}-main")
            if os.path.exists(extracted):
                shutil.move(extracted, target_dir)

        ok(f"Downloaded to: {target_dir}")
        return target_dir
    except Exception as e:
        fail(f"Download failed: {e}")
        info("Download manually from: https://github.com/zerochunks/Blaze-Agent")
        sys.exit(1)

def create_launcher_scripts(project_dir, python_path):
    """Create easy launcher scripts."""
    # Bash launcher
    bash_content = f"""#!/bin/bash
# Blaze-Agent Launcher
cd "$(dirname "$0")"
source .venv/bin/activate 2>/dev/null || true
python run.py "$@"
"""
    bash_path = os.path.join(project_dir, "start.sh")
    with open(bash_path, "w") as f:
        f.write(bash_content)
    os.chmod(bash_path, 0o755)

    # Batch launcher (Windows)
    bat_content = f"""@echo off
cd /d "%~dp0"
call .venv\\Scripts\\activate.bat 2>nul
python run.py %*
"""
    bat_path = os.path.join(project_dir, "start.bat")
    with open(bat_path, "w") as f:
        f.write(bat_content)

    ok("Launcher scripts created (start.sh / start.bat)")

def main():
    banner()

    print(f"\n{BOLD}Checking system...{RESET}\n")

    # Step 1: Check Python
    check_python()

    # Step 2: Check pip
    if check_pip():
        ok("pip available")
    else:
        fail("pip not found. Install it first.")
        sys.exit(1)

    # Step 3: Check git (optional)
    if check_git():
        ok("git available")
    else:
        warn("git not found. Will use zip download.")

    # Step 4: Determine install location
    print(f"\n{BOLD}Installation{RESET}\n")
    default_dir = os.path.join(os.path.expanduser("~"), "Blaze-Agent")
    info(f"Default install location: {default_dir}")
    custom_dir = input("  Install here? [Y/n]: ").strip().lower()

    if custom_dir == "n":
        custom_path = input("  Enter full path: ").strip()
        if custom_path:
            target_dir = os.path.abspath(custom_path)
        else:
            target_dir = default_dir
    else:
        target_dir = default_dir

    # Step 5: Download source
    project_dir = download_source(target_dir)

    # Step 6: Install dependencies
    print(f"\n{BOLD}Dependencies{RESET}\n")
    python_path = install_dependencies(project_dir)

    # Step 7: Create launcher scripts
    print(f"\n{BOLD}Finalizing{RESET}\n")
    create_launcher_scripts(project_dir, python_path)

    # Done
    print(f"""
{BOLD}{GREEN}{'='*50}{RESET}
{BOLD}{GREEN}  INSTALLATION COMPLETE!{RESET}
{BOLD}{GREEN}{'='*50}{RESET}

  Location:     {project_dir}
  Python:       {python_path}

{BOLD}Next steps:{RESET}

  1. Go to the project:
     cd {project_dir}

  2. Run the setup wizard:
     {python_path} setup.py

  3. Follow the prompts to configure your bot

  4. Start the bot:
     {python_path} run.py

     Or use the launcher:
     ./start.sh          (Linux/Mac)
     start.bat           (Windows)

{BOLD}Need help?{RESET}
  Run: {python_path} setup.py --help
  Docs: https://github.com/zerochunks/Blaze-Agent/wiki

""")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n  {YELLOW}Installation cancelled.{RESET}")
        sys.exit(0)
