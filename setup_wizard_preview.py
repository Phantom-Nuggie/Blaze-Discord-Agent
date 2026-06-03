#!/usr/bin/env python3
"""Blaze-Agent Setup Wizard -- PREVIEW. Simple ASCII boxes, always aligned."""

import os, sys, time, re

_use_color = hasattr(sys.stdout, "isatty") and sys.stdout.isatty()

class _C:
    R0="\033[38;2;255;0;60m";G0="\033[38;2;0;255;136m";Y0="\033[38;2;255;204;0m"
    C0="\033[38;2;0;204;204m";D0="\033[38;2;90;90;90m";D1="\033[38;2;60;60;60m"
    D2="\033[38;2;40;40;40m";L0="\033[38;2;170;170;170m";W0="\033[38;2;255;255;255m"
    BLD="\033[1m";ITA="\033[3m";RST="\033[0m"
def clr(c): return c if _use_color else ""
R0=lambda:clr(_C.R0);G0=lambda:clr(_C.G0);Y0=lambda:clr(_C.Y0);D0=lambda:clr(_C.D0)
D1=lambda:clr(_C.D1);D2=lambda:clr(_C.D2);L0=lambda:clr(_C.L0);W0=lambda:clr(_C.W0)
BLD=lambda:clr(_C.BLD);ITA=lambda:clr(_C.ITA);RST=lambda:clr(_C.RST);C0=lambda:clr(_C.C0)

def twidth():
    try: return max(44, min(80, os.get_terminal_size().columns - 2))
    except OSError: return 56
def spacer(n=1): print("\n"*(n-1))
def len_stripped(s): return len(re.sub(r'\033\[[0-9;]*m','',s))
def fade_in(lines,delay=0.02):
    for l in lines: print(l)
    if _use_color and delay>0: time.sleep(delay)

# Box helpers: bw = content width (screen columns). Border = +--...--+ with bw dashes.
# Every line is exactly 2(indent) + 1(+) + bw(dashes/spaces) + 1(+) = bw+4 screen columns.
def box_top(bw): print(f"  {R0()}{BLD()}+{'-'*bw}+{RST()}")
def box_bot(bw): print(f"  {R0()}{BLD()}+{'-'*bw}+{RST()}")
def box_mid(bw): print(f"  {R0()}{BLD()}+{'-'*bw}+{RST()}")
def box_ln(c,bw): p=max(0,bw-len_stripped(c)); print(f"  {R0()}{BLD()}|{RST()}{c}{' '*p}{R0()}{BLD()}|{RST()}")

TOTAL=10
def step(num,title):
    w = twidth(); inner = w - 4
    dots=""
    for i in range(1,TOTAL+1):
        if i<num: dots+=f"{G0()}*{RST()}"
        elif i==num: dots+=f"{R0()}{BLD()}>{RST()}"
        else: dots+=f"{D2()}.{RST()}"
    spacer(); box_top(inner); box_ln(f" {dots}",inner)
    box_ln(f"  {W0()}{BLD()}STEP {num} of {TOTAL}  --  {title}{RST()}",inner); box_bot(inner); spacer()

def ok(m,i=4): print(f"{' '*i}{G0()}✔{RST()}  {m}")
def info(m,i=4): print(f"{' '*i}{D0()}{m}{RST()}")
def warn(m,i=4): print(f"{' '*i}{Y0()}▸{RST()}  {m}")
def fail(m,i=4): print(f"{' '*i}{R0()}✘{RST()}  {R0()}{m}{RST()}")
def bullet(n,t,i=6): print(f"{' '*i}{R0()}{BLD()}⦿ {n}{RST()}  {t}")
def sim(m,v): print(f"  {R0()}{BLD()}»{RST()}  {W0()}{m}{RST()}{D0()}: {L0()}{v}{RST()}")
def sim_h(m): print(f"  {R0()}{BLD()}»{RST()}  {W0()}{m}{RST()} {D0()}{ITA()}(hidden){RST()}{D0()}: {L0()}••••••••{RST()}")

def preview():
    if _use_color: sys.stdout.write("\033[2J\033[H"); sys.stdout.flush()
    r=R0();b=BLD();d=D0();rst=RST();w=W0();g=G0();y=Y0()
    spacer()
    fade_in([
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
        f"",f"  {r}{b}  🔥{rst}  {y}Your business. Your keys. Your control.{rst}",
        f"  {d}  Zero ongoing costs. Fully local. Privacy-first.{rst}",
    ], 0.02); spacer()

    # Prereqs
    pw=twidth(); ip=pw-4; box_top(ip); box_ln(f"  {W0()}{BLD()}⚡ CHECKING PREREQUISITES{RST()}",ip); box_bot(ip); spacer()
    ok("Python 3.12"); ok("pip available"); ok("Virtual environment already exists"); ok("All dependencies installed")
    spacer(); print(f"  {W0()}{BLD()}  Welcome to Blaze-Agent Setup!{RST()}"); spacer(); sim("Press Enter to start","↵")

    # Steps 1-8
    step(1,"Discord Bot Token"); sim_h("Paste your Discord bot token")
    ok("Token accepted. Bot Application ID: 1234567890123456789"); spacer()
    step(2,"AI Provider + API Key"); sim("Choose [1-5]","1"); ok("Provider: OpenRouter")
    spacer(); print(f"  {D1()}{'─'*(twidth()-4)}{RST()}"); sim_h("Paste your OpenRouter API key")
    ok("API key verified! Connected to OpenRouter."); sim("Choose model [1-5]","4"); ok("Model: google/gemini-2.0-flash"); spacer()
    step(3,"Business Type"); sim("Choose [1-6]","1"); ok("Business type: Restaurant"); ok("Skills auto-configured"); spacer()
    step(4,"Business Info"); sim("Business name","Patty's Kitchen"); sim("Location","Cape Town"); ok("Business info saved"); spacer()
    step(5,"Bot Personality & Name"); sim("Choose [1-4]","2"); ok("Personality: Friendly")
    spacer(); print(f"  {D1()}{'─'*(twidth()-4)}{RST()}"); sim("Bot name","PattyBot"); ok("Bot name: PattyBot"); spacer()
    step(6,"Dashboard Setup"); sim("Port (default: 8080)","↵"); ok("Dashboard: http://localhost:8080"); spacer()
    step(7,"Spend Limits"); sim("Daily limit USD","0.50"); sim("Monthly limit USD","5.00"); ok("Limits: $0.50/day, $5.00/month"); spacer()
    step(8,"Channel Settings"); sim("Choose [1-2]","1"); ok("Bot will respond in all channels"); spacer()

    # REVIEW
    step(9,"Review Configuration"); spacer()
    bw=50; box_top(bw); box_ln(f" {W0()}{BLD()}⚙  CONFIGURATION SUMMARY{RST()}",bw); box_mid(bw)
    for l,v in [("Discord Bot","ready (1234567890123456789)"),("AI Provider","OpenRouter"),
        ("AI Model","google/gemini-2.0-flash"),("Business Type","Restaurant"),
        ("Business Name","Patty's Kitchen"),("Bot Name","PattyBot"),("Personality","Friendly"),
        ("Dashboard","localhost:8080"),("Daily Budget","$0.50"),("Monthly Budget","$5.00"),
        ("Channels","All"),("Admin Channel","None")]:
        dots='·'*max(2,bw-5-len(l)-len(v)); box_ln(f"  {C0()}{l}{RST()} {dots} {W0()}{v}{RST()} ",bw)
    box_mid(bw); box_ln(f" {Y0()}Skills:{RST()}",bw)
    for sk,en in {"faq":True,"order_taking":True,"booking":True,"lead_capture":False,"file_creation":False,"complaint_handler":True,"language_detection":False}.items():
        ic=f"{G0()}ON {RST()}" if en else f"{D0()}OFF{RST()}"; box_ln(f" {ic} {L0()}{sk.replace('_',' ').title()}{RST()}",bw)
    box_bot(bw); spacer(); sim("Choose [Y/e/c]","Y")

    # GENERATE
    step(10,"Generating Files"); ok("Directories created"); ok("config.yaml written")
    ok("skills.yaml written"); ok("Soul.md generated"); ok("database initialized"); spacer()

    # FINISH
    fbw=54; box_top(fbw)
    ft="  🔥  SETUP COMPLETE!"; ftv=len_stripped(ft)
    fl=max(0,(fbw-ftv)//2); fr=max(0,fbw-ftv-fl)
    box_ln(' '*fl+ft+' '*fr,fbw); box_mid(fbw)
    for l,v in [("Dashboard","http://localhost:8080"),("Bot Name","PattyBot"),
        ("Provider","openrouter"),("Model","google/gemini-2.0-flash"),
        ("Business","Restaurant"),("Budget/day","$0.50"),("Budget/mo","$5.00")]:
        dt='.'*max(2,fbw-6-len(l)-len(v)); box_ln(f"  {R0()}{l}{RST()} {dt} {W0()}{v}{RST()} ",fbw)
    box_mid(fbw); box_ln(f"  {Y0()}{BLD()}QUICK START:{RST()}",fbw)
    for c,de in [(f"{G0()}blzed start{RST()}","Fire up the bot"),(f"{G0()}blzed status{RST()}","Check health"),(f"{G0()}blzed setup{RST()}","Re-run wizard")]:
        box_ln(f"    {c} {D0()}-- {de}{RST()}",fbw)
    box_ln(' '*fbw,fbw)
    box_ln(f"  {D0()}{ITA()}Tip: Open the dashboard to manage everything{RST()}",fbw)
    box_ln(f"  {D0()}{ITA()}     from your browser -- no terminal needed!{RST()}",fbw)
    box_bot(fbw); spacer()
    info("Preview complete -- no files were created.")

if __name__=="__main__":
    try: preview()
    except KeyboardInterrupt: print(f"\n  {Y0()}Cancelled.{RST()}")
