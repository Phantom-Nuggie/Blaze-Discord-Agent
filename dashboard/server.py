"""
Blaze-Agent Dashboard Server
Local web dashboard for managing the bot.
"""

from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import yaml
import os
import hashlib
import secrets

app = FastAPI(title="BlazeAgent Dashboard", version="1.0")

# Setup templates and static
templates = Jinja2Templates(directory="dashboard/templates")

# Simple session store (in-memory)
sessions = {}

def get_config():
    with open("config/config.yaml", "r") as f:
        return yaml.safe_load(f)

def save_config(config):
    with open("config/config.yaml", "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

def verify_password(password: str) -> bool:
    config = get_config()
    stored = config.get("dashboard", {}).get("password", "")
    return password == stored

def create_session() -> str:
    token = secrets.token_hex(32)
    sessions[token] = True
    return token

def is_authenticated(request: Request) -> bool:
    token = request.cookies.get("session")
    return token in sessions

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    if not is_authenticated(request):
        return RedirectResponse("/login")

    config = get_config()
    bot_name = config.get("bot", {}).get("name", "BlazeAgent")
    ai_model = config.get("ai", {}).get("model", "N/A")
    ai_provider = config.get("ai", {}).get("provider", "N/A")
    port = config.get("dashboard", {}).get("port", 8080)

    # Read Soul.md
    soul_content = ""
    if os.path.exists("config/soul.md"):
        with open("config/soul.md", "r") as f:
            soul_content = f.read()

    return templates.TemplateResponse("index.html", {
        "request": request,
        "bot_name": bot_name,
        "ai_model": ai_model,
        "ai_provider": ai_provider,
        "port": port,
        "soul_content": soul_content
    })

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head><title>BlazeAgent Login</title>
    <style>
        body { background: #1a1a2e; color: #eee; font-family: monospace;
               display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .box { background: #16213e; padding: 40px; border-radius: 8px; width: 300px; }
        h1 { color: #e94560; text-align: center; }
        input { width: 100%; padding: 10px; margin: 10px 0; border: none; border-radius: 4px;
                background: #0f3460; color: #eee; box-sizing: border-box; }
        button { width: 100%; padding: 10px; background: #e94560; color: white; border: none;
                 border-radius: 4px; cursor: pointer; font-weight: bold; }
        button:hover { background: #c81e45; }
    </style></head>
    <body>
        <div class="box">
            <h1>BlazeAgent</h1>
            <form method="post" action="/login">
                <input type="password" name="password" placeholder="Dashboard password" required>
                <button type="submit">Login</button>
            </form>
        </div>
    </body>
    </html>
    """)

@app.post("/login")
async def login_submit(password: str = Form(...)):
    if verify_password(password):
        token = create_session()
        response = RedirectResponse("/", status_code=302)
        response.set_cookie("session", token, httponly=True, max_age=86400)
        return response
    return HTMLResponse("<script>alert('Wrong password'); window.location='/login'</script>")

@app.get("/soul", response_class=HTMLResponse)
async def soul_editor(request: Request):
    if not is_authenticated(request):
        return RedirectResponse("/login")

    soul_content = ""
    if os.path.exists("config/soul.md"):
        with open("config/soul.md", "r") as f:
            soul_content = f.read()

    return templates.TemplateResponse("soul.html", {
        "request": request,
        "soul_content": soul_content
    })

@app.post("/soul/save")
async def soul_save(request: Request, content: str = Form(...)):
    if not is_authenticated(request):
        raise HTTPException(status_code=403)
    with open("config/soul.md", "w") as f:
        f.write(content)
    return RedirectResponse("/soul", status_code=302)

@app.get("/memory", response_class=HTMLResponse)
async def memory_viewer(request: Request):
    if not is_authenticated(request):
        return RedirectResponse("/login")

    import sqlite3
    conn = sqlite3.connect("storage/database.sqlite")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM memories ORDER BY updated_at DESC LIMIT 100")
    rows = c.fetchall()
    conn.close()

    return templates.TemplateResponse("memory.html", {
        "request": request,
        "memories": [dict(r) for r in rows]
    })

@app.get("/skills", response_class=HTMLResponse)
async def skills_config(request: Request):
    if not is_authenticated(request):
        return RedirectResponse("/login")

    config = get_config()
    skills = config.get("skills", {})

    return templates.TemplateResponse("skills.html", {
        "request": request,
        "skills": skills
    })

@app.post("/skills/toggle")
async def skills_toggle(request: Request, skill_name: str = Form(...), enabled: str = Form(...)):
    if not is_authenticated(request):
        raise HTTPException(status_code=403)
    config = get_config()
    if "skills" not in config:
        config["skills"] = {}
    config["skills"][skill_name] = enabled == "true"
    save_config(config)
    # Also update skills.yaml
    import yaml as _yaml
    with open("config/skills.yaml", "w") as f:
        _yaml.dump(config["skills"], f)
    return RedirectResponse("/skills", status_code=302)

@app.get("/files", response_class=HTMLResponse)
async def files_manager(request: Request):
    if not is_authenticated(request):
        return RedirectResponse("/login")

    files_dir = "storage/files"
    files_list = []
    if os.path.exists(files_dir):
        for f in os.listdir(files_dir):
            fpath = os.path.join(files_dir, f)
            if os.path.isfile(fpath):
                from datetime import datetime
                files_list.append({
                    "name": f,
                    "size": os.path.getsize(fpath),
                    "modified": datetime.fromtimestamp(os.path.getmtime(fpath)).strftime("%Y-%m-%d %H:%M")
                })

    return templates.TemplateResponse("files.html", {
        "request": request,
        "files": files_list
    })

@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    if not is_authenticated(request):
        return RedirectResponse("/login")

    config = get_config()
    return templates.TemplateResponse("settings.html", {
        "request": request,
        "config": config
    })

@app.post("/settings/save")
async def settings_save(
    request: Request,
    ai_model: str = Form(...),
    temperature: float = Form(...),
    daily_limit: float = Form(...),
    monthly_limit: float = Form(...),
    bot_name: str = Form(...),
    personality: str = Form(...)
):
    if not is_authenticated(request):
        raise HTTPException(status_code=403)
    config = get_config()
    config["ai"]["model"] = ai_model
    config["ai"]["temperature"] = temperature
    config["ai"]["daily_spend_limit"] = daily_limit
    config["ai"]["monthly_spend_limit"] = monthly_limit
    config["bot"]["name"] = bot_name
    config["bot"]["personality"] = personality
    save_config(config)
    return RedirectResponse("/settings", status_code=302)
