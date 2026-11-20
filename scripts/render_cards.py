#!/usr/bin/env python3
"""Draws every card of the Antaryx profile README as an animated SVG: no third-party widget services, no trackers, no JavaScript.
Python standard library only (the font subsets are committed in assets/fonts and embedded as data URIs).

    python3 scripts/render_cards.py            # writes cards/<name>.svg (dark) and cards/<name>-light.svg

Live, public data (no token): plumbline's version, commits and weekly activity; the contribution calendar (the star map); the newest CISA
"Known Exploited Vulnerabilities" (the threat feed). If a source is unreachable the card falls back to the last known values, so the script
never writes a broken card. Everything fetched from outside is reduced to printable ASCII and length-limited before it is drawn.
Design: the Antaryx desktop palette, the Antaryx mark (hexagon, lambda, red sting), one red star (Antares). Every base style shows the FINAL picture;
animations start from "hidden" (fill-mode: backwards), so a renderer that ignores animation still draws a complete card. Reduced motion drops
the sweeping and sliding movement but keeps the gentle animation (twinkle, fade, drawing, typing).
"""
import base64
import datetime
import html
import json
import math
import os
import pathlib
import re
import sys
import time
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import mark  # noqa: E402

OUT = ROOT / "cards"
OUT.mkdir(parents=True, exist_ok=True)
OWNER = "antaryx"
W = 900            # every card is drawn 900 wide (the README column is about 870 px): text is shown at about its own size
HALF = 446         # two cards side by side

DARK = dict(name="dark", bg0="#0b0f12", bg1="#151b21", panel="#0f1418", edge="#2a3b52", text="#e6edf3", dim="#9aa7b4", faint="#6b7785",
            blue="#6aa8ff", cyan="#5ccfe6", red="#ff6b81", green="#7ee787", yellow="#f2cc60", star="#eef6ff", glow="#d7f4fb",
            plate="#17202a", plate_hi="#2d5f94", wm0="#5a98f0", wm2="#ffffff", rain=".13", scanop=".10")
LIGHT = dict(name="light", bg0="#ffffff", bg1="#e8f0f9", panel="#f3f7fb", edge="#b4c8de", text="#0f1720", dim="#44566a", faint="#6b7d90",
             blue="#0a58c9", cyan="#00798c", red="#cf2147", green="#16743a", yellow="#9a6700", star="#0a58c9", glow="#9cc4f5",
             plate="#dde9f6", plate_hi="#8fb8ec", wm0="#0a58c9", wm2="#0f1720", rain=".10", scanop=".12")
P = DARK

FONT_FILES = {400: ROOT / "assets/fonts/PlexMono-Regular.subset.woff2", 600: ROOT / "assets/fonts/PlexMono-SemiBold.subset.woff2"}
CW = 0.6           # IBM Plex Mono: every glyph is 0.6 em wide, so text widths are exact


def font_css():
    out = []
    for wt, f in FONT_FILES.items():
        if f.exists():
            out.append("@font-face{font-family:'AX Mono';font-weight:%d;src:url(data:font/woff2;base64,%s) format('woff2')}" % (wt, base64.b64encode(f.read_bytes()).decode()))
    return "".join(out)


FONTS = font_css()
MONO = "'AX Mono','IBM Plex Mono',ui-monospace,'SF Mono',Menlo,Consolas,'DejaVu Sans Mono',monospace"

# ------------------------------------------------------------------ live data
LAST = {"version": "v2.0.1", "commits": 115, "stars": 0, "checks": 112, "modules": 11, "weeks": [], "days": [], "total": 19, "kev": []}


def get(url, accept="application/json", timeout=25):
    h = {"User-Agent": "antaryx-profile-cards", "Accept": accept}
    if os.environ.get("GITHUB_TOKEN") and "api.github.com" in url:
        h["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]
    with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=timeout) as r:
        return r.status, r.read(), r.headers


def ascii_clean(s, n):
    s = re.sub(r"[^\x20-\x7e]", "", str(s)).strip()
    return (s[: n - 1] + "~") if len(s) > n else s


def live():
    d = dict(LAST)
    try:
        d["version"] = json.loads(get("https://api.github.com/repos/%s/plumbline/releases/latest" % OWNER)[1])["tag_name"]
        d["stars"] = json.loads(get("https://api.github.com/repos/%s/plumbline" % OWNER)[1])["stargazers_count"]
        _, _, h = get("https://api.github.com/repos/%s/plumbline/commits?per_page=1" % OWNER)
        m = re.search(r'page=(\d+)>; rel="last"', h.get("Link", ""))
        if m: d["commits"] = int(m.group(1))
        raw = get("https://raw.githubusercontent.com/%s/plumbline/main/README.md" % OWNER, "text/plain")[1].decode("utf-8", "ignore")
        m = re.search(r"\*\*(\d+) checks .{1,6} (\d+) modules", raw)
        if m: d["checks"], d["modules"] = int(m.group(1)), int(m.group(2))
        for _ in range(5):   # the statistics endpoint answers 202 (and no data) while GitHub computes them
            st, body, _ = get("https://api.github.com/repos/%s/plumbline/stats/commit_activity" % OWNER)
            w = json.loads(body) if body else []
            if st == 200 and isinstance(w, list) and w:
                d["weeks"] = [x["total"] for x in w]
                break
            time.sleep(4)
    except Exception as e:  # noqa: BLE001
        print("plumbline data unavailable, last known values used:", e)
    try:   # the contribution calendar, as the profile page itself loads it
        page = get("https://github.com/users/%s/contributions" % OWNER, "text/html")[1].decode("utf-8", "ignore")
        days = re.findall(r'data-date="(\d{4}-\d{2}-\d{2})"[^>]*?data-level="(\d)"', page) or [(a, b) for b, a in re.findall(r'data-level="(\d)"[^>]*?data-date="(\d{4}-\d{2}-\d{2})"', page)]
        if days:
            d["days"] = sorted((a, int(b)) for a, b in days)
        m = re.search(r"([\d,]+)\s+contributions?\s+in\s+the\s+last\s+year", page)
        if m: d["total"] = int(m.group(1).replace(",", ""))
    except Exception as e:  # noqa: BLE001
        print("contribution calendar unavailable:", e)
    try:   # CISA Known Exploited Vulnerabilities: the five newest additions
        j = json.loads(get("https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json")[1])
        v = sorted(j["vulnerabilities"], key=lambda x: (x.get("dateAdded", ""), x.get("cveID", "")), reverse=True)[:5]
        d["kev"] = [dict(date=ascii_clean(x.get("dateAdded", ""), 11), cve=ascii_clean(x.get("cveID", ""), 18), who=ascii_clean("%s %s" % (x.get("vendorProject", ""), x.get("product", "")), 30),
                         name=ascii_clean(x.get("vulnerabilityName", ""), 44)) for x in v]
        d["kev_count"] = int(j.get("count", len(j["vulnerabilities"])))
        d["kev_date"] = ascii_clean(str(j.get("dateReleased", ""))[:10], 11)
    except Exception as e:  # noqa: BLE001
        print("CISA KEV feed unavailable:", e)
    return d


# ------------------------------------------------------------------ building blocks
def esc(s):
    return html.escape(str(s), quote=True)


def style():
    return """<style>%s
text{font-family:%s}
@keyframes tw{0%%,100%%{opacity:.35}50%%{opacity:1}}
@keyframes fade{from{opacity:0}}
@keyframes rise{from{opacity:0;transform:translateY(10px)}}
@keyframes draw{from{stroke-dasharray:var(--l);stroke-dashoffset:var(--l)}to{stroke-dashoffset:0}}
@keyframes ripple{from{transform:scale(.4);opacity:.9}to{transform:scale(2.6);opacity:0}}
@keyframes blink{0%%,49%%{opacity:1}50%%,100%%{opacity:0}}
@keyframes scan{from{transform:translateY(-90px)}to{transform:translateY(480px)}}
@keyframes type{from{clip-path:inset(0 100%% 0 0)}to{clip-path:inset(0 0 0 0)}}
@keyframes segpulse{0%%,62%%,100%%{filter:brightness(1)}30%%{filter:brightness(1.9)}}
@keyframes nodepulse{0%%,9%%,100%%{stroke-opacity:.55;stroke-width:2}3%%{stroke-opacity:1;stroke-width:3.4}}
@keyframes line{from{stroke-dashoffset:var(--l)}to{stroke-dashoffset:0}}
@keyframes grow{from{transform:scaleX(0)}}
.tw{animation:tw 3.4s ease-in-out infinite}
.cur{animation:blink 1s steps(1) infinite}
.ripple{transform-box:fill-box;transform-origin:center;animation:ripple 3.4s ease-out infinite}
.scan{animation:scan 9s linear infinite}
.sc-seg{animation:segpulse 4.4s ease-in-out infinite}
.np{animation:nodepulse 12s linear infinite}
/* reduced motion removes the sweeping and sliding movement but keeps the gentle animation: twinkle, fade-in, drawing, typing, the cursor */
@media (prefers-reduced-motion:reduce){.scan,.ripple{animation:none!important}[style*="animation:rise"]{animation-name:fade!important}}
</style>""" % (FONTS, MONO)


def svg(w, h, body, title, defs=""):
    d = ('<defs>%s'
         '<linearGradient id="vio" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="900" y2="0"><stop offset="0" stop-color="%s"/><stop offset="1" stop-color="%s"/></linearGradient>'
         '<linearGradient id="wm" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="%s"/><stop offset=".55" stop-color="%s"/><stop offset="1" stop-color="%s"/></linearGradient>'
         '<radialGradient id="sg"><stop offset="0" stop-color="%s" stop-opacity=".9"/><stop offset="1" stop-color="%s" stop-opacity="0"/></radialGradient>'
         '<radialGradient id="ag"><stop offset="0" stop-color="%s" stop-opacity=".95"/><stop offset="1" stop-color="%s" stop-opacity="0"/></radialGradient>'
         '<radialGradient id="bg" cx="50%%" cy="38%%" r="85%%"><stop offset="0" stop-color="%s"/><stop offset="1" stop-color="%s"/></radialGradient>'
         '<linearGradient id="scanbar" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="%s" stop-opacity="0"/><stop offset=".5" stop-color="%s" stop-opacity="%s"/><stop offset="1" stop-color="%s" stop-opacity="0"/></linearGradient>'
         '<filter id="glow" x="-20%%" y="-40%%" width="140%%" height="180%%"><feGaussianBlur stdDeviation="6"/></filter>%s</defs>') % (
        style(), P["blue"], P["cyan"], P["wm0"], P["cyan"], P["wm2"], P["glow"], P["blue"], P["red"], P["red"], P["bg1"], P["bg0"], P["cyan"], P["cyan"], P["scanop"], P["cyan"], defs)
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" role="img" aria-label="%s"><title>%s</title>%s%s</svg>\n') % (
        w, h, w, h, esc(title), esc(title), d, body)


def clipdef(w, h, rx, cid):
    return '<clipPath id="%s"><rect x="1" y="1" width="%d" height="%d" rx="%d"/></clipPath>' % (cid, w - 2, h - 2, rx)


def panel(w, h, rx=18, scan=True):
    s = '<rect x="1" y="1" width="%d" height="%d" rx="%d" fill="url(#bg)" stroke="%s" stroke-width="2"/>' % (w - 2, h - 2, rx, P["edge"])
    return s + ('<rect class="scan" x="2" y="0" width="%d" height="90" fill="url(#scanbar)"/>' % (w - 4) if scan else "")


def card(w, h, rx, cid, inner, title, defs="", scan=True):
    body = '<g clip-path="url(#%s)">%s%s</g>' % (cid, panel(w, h, rx, scan), inner)
    return svg(w, h, body, title, clipdef(w, h, rx, cid) + defs)


def tw(x, y, text, size, fill, weight=400, extra="", anchor=None):
    a = ' text-anchor="%s"' % anchor if anchor else ""
    return '<text x="%s" y="%s" font-size="%s" fill="%s" font-weight="%d"%s %s>%s</text>' % (x, y, size, fill, weight, a, extra, esc(text))


def wrap(text, width, size):
    n = max(int(width / (CW * size)), 8)
    lines, cur = [], ""
    for wd in text.split():
        if len(cur) + len(wd) + 1 > n and cur:
            lines.append(cur); cur = wd
        else:
            cur = (cur + " " + wd).strip()
    return lines + [cur]


LETTERS = {"A": "M0 100 L40 0 L80 100", "N": "M0 100 V0 L80 100 V0", "T": "M0 0 H80 M40 0 V100", "R": "M0 100 V0 H52 Q80 0 80 25 Q80 50 52 50 H0 M46 50 L80 100",
           "Y": "M0 0 L40 50 L80 0 M40 50 V100", "X": "M0 0 L80 100 M80 0 L0 100"}


def wordmark(x, y, scale, width=13):
    inner = "".join('<path d="%s" transform="translate(%.1f 0)"/>' % (LETTERS[ch], i * 108) for i, ch in enumerate("ANTARYX"))
    return ('<g transform="translate(%s %s) scale(%.3f)" fill="none" stroke-linejoin="miter" stroke-linecap="butt">'
            '<g stroke="%s" stroke-width="%d" opacity=".5" filter="url(#glow)">%s</g><g stroke="url(#wm)" stroke-width="%d">%s</g></g>') % (x, y, scale, P["blue"], width + 6, inner, width, inner)


def rain(x0, x1, y0, y1, seed=7):
    import random
    r = random.Random(seed)
    o = []
    for cx in range(x0, x1, 28):
        col = "".join('<tspan x="%d" dy="%d">%s</tspan>' % (cx, 0 if i == 0 else 22, r.choice("0123456789")) for i in range(int((y1 - y0) / 22)))
        o.append('<text class="tw" style="animation-delay:%.1fs;animation-duration:%.1fs" x="%d" y="%d" fill="%s" fill-opacity="%s" font-size="15">%s</text>' % (
            r.random() * 4, 4 + r.random() * 4, cx, y0, P["cyan"], P["rain"], col))
    return "".join(o)


def typed(x, y, text, size, fill, delay, dur, weight=400):
    width = round(len(text) * CW * size, 1)
    return ('<text x="%s" y="%s" font-size="%s" fill="%s" font-weight="%d" xml:space="preserve" textLength="%s" lengthAdjust="spacing" '
            'style="animation:type %ss steps(%d) %ss backwards">%s</text>') % (x, y, size, fill, weight, width, dur, max(len(text), 1), delay, esc(text))


def scorp(size, uid, animate=True):
    pal = dict(edge1=P["blue"], edge2=P["cyan"], red=P["red"], flat=P["text"])
    return mark.group("neon", size, 10, pal, animate, uid)


# ------------------------------------------------------------------ cards
def hero(D):
    h = 380
    defs_sc, g = scorp(326, "sc")
    inner = rain(400, 880, 40, 360) + rain(18, 120, 40, 360, 3)
    inner += '<g style="animation:fade 1.2s ease-out backwards" transform="translate(40 26)">%s</g>' % g
    inner += '<g style="animation:rise .9s ease-out .6s backwards">%s</g>' % wordmark(400, 92, 0.64)
    inner += '<line x1="402" y1="190" x2="860" y2="190" stroke="%s" stroke-opacity=".55" stroke-width="1.5"/>' % P["cyan"]
    inner += typed(402, 232, "/  SECURITY.  RESEARCH.  ADAPTATION.", 18, P["text"], 1.4, 2.6)
    inner += '<rect class="cur" x="%d" y="216" width="11" height="22" fill="%s"/>' % (402 + int(36 * CW * 18) + 6, P["red"])
    inner += '<g style="animation:fade 1s ease-out 2.6s backwards">%s%s</g>' % (
        tw(402, 276, "hybrid security research node", 15, P["dim"]),
        '<text x="402" y="302" font-size="15" fill="%s">blue team <tspan fill="%s">+</tspan> red team <tspan fill="%s">//</tspan> authorized scope only</text>' % (P["dim"], P["red"], P["blue"]))
    for (cx, cy, sx, sy) in ((18, 18, 1, 1), (W - 18, 18, -1, 1), (18, h - 18, 1, -1), (W - 18, h - 18, -1, -1)):
        inner += '<path d="M%d %d h%d M%d %d v%d" stroke="%s" stroke-width="2" stroke-opacity=".7" fill="none"/>' % (cx, cy, 24 * sx, cx, cy, 24 * sy, P["cyan"])
    return card(W, h, 22, "hc", inner, "ANTARYX - security. research. adaptation.", defs_sc)


def term(title, lines, last_prompt=True):
    h = 46 + 28 * len(lines) + (34 if last_prompt else 18) + 20
    inner = '<rect x="1" y="1" width="%d" height="42" fill="%s"/><line x1="1" y1="43" x2="%d" y2="43" stroke="%s" stroke-width="2"/>' % (W - 2, P["panel"], W - 1, P["edge"])
    for i, c in enumerate((P["red"], P["yellow"], P["green"])):
        inner += '<circle cx="%d" cy="22" r="6.5" fill="%s" opacity=".9"/>' % (28 + i * 22, c)
    inner += tw(W / 2, 27, title, 14, P["dim"], anchor="middle")
    y, t = 80, 0.4
    for kind, text in lines:
        if kind == "p":
            inner += '<text x="30" y="%d" font-size="16.5" fill="%s" style="animation:fade .01s steps(1) %.2fs backwards"><tspan fill="%s">&gt;_</tspan> %s</text>' % (y, P["text"], t, P["red"], esc(text))
            t += 0.9
        else:
            col = {"o": P["dim"], "k": P["green"], "d": P["faint"], "r": P["red"], "w": P["text"]}[kind]
            inner += '<text x="30" y="%d" font-size="16.5" fill="%s" style="animation:fade .4s ease-out %.2fs backwards">%s</text>' % (y, col, t, esc(text))
            t += 0.5
        y += 28
    if last_prompt:
        inner += '<text x="30" y="%d" font-size="16.5" fill="%s"><tspan fill="%s">&gt;_</tspan></text><rect class="cur" x="68" y="%d" width="10" height="20" fill="%s"/>' % (y + 6, P["text"], P["red"], y - 10, P["red"])
    return inner, h


def whoami(D):
    lines = [("p", "whoami && id"), ("w", "antaryx  uid=1337(antaryx) gid=1337(operators) groups=defense,offense,research"),
             ("p", "cat /etc/mission"), ("w", "operating in the void between defensive architecture and offensive exploitation."),
             ("p", "echo $RULES_OF_ENGAGEMENT"), ("k", "authorized targets only  //  HTB  THM  CTF  own lab  //  scope before scan"),
             ("p", "plumbline scan --offline"), ("w", "%d checks  %d modules  0 network calls  evidence first" % (D["checks"], D["modules"]))]
    inner, h = term("antaryx@void: ~", lines)
    return card(W, h, 18, "wc", inner, "whoami: a hybrid security research node")


def vectors(kind):
    blue = kind == "blue"
    head = "DEFENSE_VECTORS // BLUE TEAM" if blue else "OFFENSE_VECTORS // RED TEAM"
    acc = P["cyan"] if blue else P["red"]
    items = [("Anomaly detection", "parsing the void for unauthorized telemetry"), ("Forensic architecture", "reconstructing fragmented footprints, auditing access logs"),
             ("System hardening", "impenetrable Linux / WSL and containerised infrastructure")] if blue else [
        ("Vulnerability research", "logic flaws, misconfigurations, system weaknesses"), ("Payload engineering", "silent, adaptive execution chains"),
        ("Stealth operations", "behavioural mutation, footprint reduction")]
    h = 352
    inner = tw(26, 46, "[ %s ]" % head, 15, acc, 600, 'letter-spacing="1"')
    inner += '<line x1="26" y1="62" x2="%d" y2="62" stroke="%s" stroke-opacity=".55"/>' % (HALF - 26, acc)
    y = 104
    for i, (a, b) in enumerate(items):
        g = '<path d="M28 %d l8 6 l-8 6" stroke="%s" stroke-width="3" fill="none" stroke-linecap="round"/>' % (y - 13, acc)
        g += tw(50, y, a, 18, P["text"], 600)
        lines = wrap(b, HALF - 76, 13.5)
        for j, ln in enumerate(lines):
            g += tw(50, y + 22 + j * 18, ln, 13.5, P["dim"])
        inner += '<g style="animation:rise .6s ease-out %.2fs backwards">%s</g>' % (0.3 + i * 0.25, g)
        y += 70 + (18 if len(lines) > 1 else 0)
    foot = "defence is the ground truth: measure it" if blue else "scope-gated  //  authorized targets only"
    inner += tw(26, h - 24, foot, 13.5, acc if not blue else P["dim"])
    return card(HALF, h, 18, "v" + kind, inner, head)


def heading(cmd, cid):
    h = 66
    inner = '<text x="6" y="40" font-size="21" fill="%s" font-weight="600"><tspan fill="%s">&gt;_</tspan> %s</text>' % (P["text"], P["red"], esc(cmd))
    x = 6 + (3 + len(cmd)) * CW * 21 + 18
    inner += '<line x1="%.0f" y1="35" x2="%d" y2="35" stroke="url(#vio)" stroke-width="2" stroke-opacity=".8" style="--l:%d;stroke-dasharray:%d;animation:line 1.4s ease-out backwards"/>' % (x, W - 6, W, W)
    inner += '<circle class="tw" cx="%d" cy="35" r="3.5" fill="%s"/>' % (W - 6, P["red"])
    return svg(W, h, inner, cmd)


def repo_card(name, tagline, chips, stats, cid):
    h = 292
    inner = tw(26, 52, name, 24, P["text"], 600) + '<circle cx="%d" cy="44" r="5" fill="%s"/>' % (HALF - 30, P["red"])
    for i, ln in enumerate(wrap(tagline, HALF - 52, 15)[:3]):
        inner += tw(26, 90 + i * 22, ln, 15, P["text"])
    x, y = 26, 178
    for c in chips:
        cw = 22 + len(c) * CW * 13
        if x + cw > HALF - 20: x, y = 26, y + 34
        inner += '<rect x="%.1f" y="%d" width="%.1f" height="26" rx="13" fill="none" stroke="%s" stroke-opacity=".85"/>%s' % (x, y - 18, cw, P["cyan"], tw(x + cw / 2, y, c, 13, P["cyan"], anchor="middle"))
        x += cw + 8
    inner += '<line x1="26" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-opacity=".6"/>' % (h - 76, HALF - 26, h - 76, P["edge"])
    sx, sy = 26, h - 48
    for label, val in stats:
        wst = (len(val) * CW * 16) + (len(label) + 1) * CW * 12 + 22
        if sx + wst > HALF - 20: sx, sy = 26, sy + 28
        inner += '<text x="%.1f" y="%d" font-size="16" fill="%s" font-weight="600">%s <tspan font-size="12" fill="%s" font-weight="400">%s</tspan></text>' % (sx, sy, P["text"], esc(val), P["dim"], esc(label))
        sx += wst
    return card(HALF, h, 18, cid, inner, name)


def activity(D):
    h = 240
    weeks = D["weeks"] or [0] * 52
    mx = max(max(weeks), 1)
    inner = tw(28, 44, "[ SIGNAL // plumbline commit activity, last %d weeks ]" % len(weeks), 15, P["cyan"], 600, 'letter-spacing="1"')
    inner += tw(W - 28, 44, "%d commits  //  %s" % (D["commits"], D["version"]), 14, P["dim"], anchor="end")
    x0, x1, yb, ht = 40, W - 40, 206, 120
    step = (x1 - x0) / max(len(weeks) - 1, 1)
    pts = [(x0 + i * step, yb - ht * v / mx) for i, v in enumerate(weeks)]
    area = "M%.1f %d " % (pts[0][0], yb) + " ".join("L%.1f %.1f" % p for p in pts) + " L%.1f %d Z" % (pts[-1][0], yb)
    line = "M" + " L".join("%.1f %.1f" % p for p in pts)
    defs = '<linearGradient id="ar" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="%s" stop-opacity=".5"/><stop offset="1" stop-color="%s" stop-opacity="0"/></linearGradient>' % (P["blue"], P["blue"])
    inner += '<path d="%s" fill="url(#ar)" style="animation:fade 1.4s ease-out .3s backwards"/>' % area
    inner += '<path d="%s" fill="none" stroke="url(#vio)" stroke-width="2.4" stroke-linejoin="round" style="--l:2400;animation:draw 2.2s ease-out .2s backwards"/>' % line
    if any(weeks):
        i = max(range(len(weeks)), key=lambda k: weeks[k]); px, py = pts[i]
        inner += '<circle class="ripple" cx="%.1f" cy="%.1f" r="9" fill="none" stroke="%s" stroke-width="2"/><circle cx="%.1f" cy="%.1f" r="5" fill="%s"/>' % (px, py, P["red"], px, py, P["red"])
        inner += tw(px, max(py - 16, 76), "peak %d" % weeks[i], 13, P["red"], anchor="middle")
    return card(W, h, 18, "ac", inner, "plumbline commit activity", defs)


def stack():
    items = ["Python", "Go", "Docker", "Bash", "Django", "Linux / WSLg", "Git"]
    inner = tw(28, 32, "CORE_STACK", 13, P["dim"], extra='letter-spacing="1.5"')
    x, y, rows = 28, 62, 1
    for i, t in enumerate(items):
        cw = 44 + len(t) * CW * 16
        if x + cw > W - 24: x, y, rows = 28, y + 44, rows + 1
        inner += ('<g style="animation:fade .5s ease-out %.2fs backwards"><rect x="%.1f" y="%d" width="%.1f" height="34" rx="17" fill="none" stroke="%s" stroke-opacity=".85"/>'
                  '<circle cx="%.1f" cy="%d" r="4" fill="%s"/>%s</g>') % (0.2 + i * 0.15, x, y - 22, cw, P["cyan"], x + 19, y - 5, P["red"] if t == "Go" else P["blue"], tw(x + 32, y, t, 16, P["text"]))
        x += cw + 12
    return card(W, 40 + 44 * rows + 18, 16, "sk", inner, "core stack: " + ", ".join(items))


def method():
    h = 340
    nodes = [("SCOPE", "authorization"), ("RECON", "map the surface"), ("HYPOTHESIS", "what could break"), ("TEST", "in scope only"),
             ("EVIDENCE", "reproducible"), ("REPORT", "clear and honest"), ("HARDEN", "fix, then re-test")]
    nw, nh = 184, 70
    xs = [30, 250, 470, 690]
    pos = [(xs[0], 64), (xs[1], 64), (xs[2], 64), (xs[3], 64), (xs[3], 214), (xs[2], 214), (xs[1], 214)]
    cen = [(x + nw / 2, y + nh / 2) for x, y in pos]
    loop = [cen[0], cen[1], cen[2], cen[3], cen[4], cen[5], cen[6], (cen[0][0], cen[6][1]), cen[0]]
    path = "M" + " L".join("%.0f %.0f" % p for p in loop)
    inner = tw(28, 40, "[ METHOD // the engagement loop ]", 15, P["cyan"], 600, 'letter-spacing="1"')
    inner += '<path d="%s" fill="none" stroke="%s" stroke-opacity=".55" stroke-width="1.6" stroke-dasharray="5 6"/>' % (path, P["blue"])
    d, acc = [0.0], 0.0
    for a, b in zip(loop, loop[1:]):
        acc += math.hypot(b[0] - a[0], b[1] - a[1]); d.append(acc)
    total, period = acc, 12.0
    for i, ((x, y), (name, sub)) in enumerate(zip(pos, nodes)):
        inner += ('<g><rect class="np" style="animation-delay:%.2fs" x="%d" y="%d" width="%d" height="%d" rx="14" fill="%s" stroke="%s" stroke-opacity=".55" stroke-width="2"/>%s%s</g>') % (
            d[i] / total * period, x, y, nw, nh, P["panel"], P["red"] if i == 0 else P["blue"],
            tw(x + nw / 2, y + 30, name, 17, P["text"], 600, anchor="middle", extra='letter-spacing="1"'), tw(x + nw / 2, y + 52, sub, 12.5, P["dim"], anchor="middle"))
    inner += ('<g><circle r="9" fill="url(#ag)"><animateMotion dur="%ss" repeatCount="indefinite" path="%s"/></circle>'
              '<circle r="4" fill="%s"><animateMotion dur="%ss" repeatCount="indefinite" path="%s"/></circle></g>') % (period, path, P["red"], period, path)
    inner += tw(cen[0][0] + 12, cen[6][1] + 58, "what the defence missed feeds the next scope", 13, P["dim"])
    return card(W, h, 18, "mc", inner, "method: scope, recon, hypothesis, test, evidence, report, harden")


def rules():
    items = ["AUTHORIZED TARGETS ONLY", "SCOPE BEFORE SCAN", "EVIDENCE OVER OPINION", "REPORT, NEVER WEAPONISE"]
    inner = ""
    cw = (W - 24) / len(items)
    for i, t in enumerate(items):
        cx = 12 + cw * i + cw / 2
        inner += '<g style="animation:fade .6s ease-out %.2fs backwards"><path d="M%.1f 34 l7 7 l-7 7 l-7 -7 Z" fill="%s"/>%s</g>' % (0.2 + i * 0.2, cx, P["red"] if i == 0 else P["cyan"], tw(cx, 74, t, 12.5, P["text"], 600, anchor="middle", extra='letter-spacing=".6"'))
    return card(W, 98, 16, "rc", inner, "rules of engagement")


def button(label, sub, cid):
    w, h = 290, 72
    inner = tw(22, 31, label, 17, P["text"], 600, extra='letter-spacing="1"') + tw(22, 53, sub, 13, P["dim"])
    inner += '<path d="M%d 24 l9 12 l-9 12" stroke="%s" stroke-width="3" fill="none" stroke-linecap="round"/>' % (w - 34, P["red"])
    return card(w, h, 14, cid, inner, label + " " + sub, scan=False)


def footer():
    lines = [("p", "exit"), ("k", "[ IDENTITY: VERIFIED ]"), ("d", "[ PGP FINGERPRINT: UNAVAILABLE ]"), ("d", "Connection to 127.0.0.1 closed.")]
    inner, h = term("antaryx@void: ~", lines)
    return card(W, h, 18, "fc", inner, "connection closed")


def divider():
    defs, g = mark.group("neon", 76, 2, dict(edge1=P["blue"], edge2=P["cyan"], red=P["red"]), False, "dv")
    inner = '<line x1="30" y1="42" x2="396" y2="42" stroke="url(#vio)" stroke-opacity=".6"/><line x1="504" y1="42" x2="870" y2="42" stroke="url(#vio)" stroke-opacity=".6"/><g transform="translate(412 4)">%s</g>' % g
    return svg(W, 84, inner, "divider", defs)


def starmap(D):
    h = 268
    days = D["days"]
    inner = tw(28, 42, "[ CONSTELLATION // %d contributions in the last year ]" % D["total"], 15, P["cyan"], 600, 'letter-spacing="1"')
    sdefs, sg = mark.group("neon", 185, 6, dict(edge1=P["blue"], edge2=P["cyan"], red=P["red"]), False, "sm")
    inner += '<g opacity=".16" transform="translate(62 54)">%s</g>' % sg
    if days:
        weeks = (len(days) + 6) // 7
        first = datetime.date.fromisoformat(days[0][0])
        off = (first.weekday() + 1) % 7            # GitHub's weeks start on Sunday
        x0, y0, dx, dy = 36, 84, (W - 72) / max(weeks + 1, 1), 24
        pts = []
        for i, (dstr, lvl) in enumerate(days):
            col, row = (i + off) // 7, (i + off) % 7
            x, y = x0 + col * dx, y0 + row * dy
            inner += '<circle cx="%.1f" cy="%.1f" r="1.4" fill="%s" fill-opacity=".35"/>' % (x, y, P["faint"])
            if lvl > 0: pts.append((x, y, lvl))
        for a, b in zip(pts, pts[1:]):
            inner += '<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-opacity=".45" stroke-width="1.2"/>' % (a[0], a[1], b[0], b[1], P["blue"])
        for i, (x, y, lvl) in enumerate(pts):
            r = 3.5 + lvl * 1.4
            last = i == len(pts) - 1
            inner += '<circle class="tw" style="animation-delay:%.1fs" cx="%.1f" cy="%.1f" r="%.1f" fill="url(#%s)"/>' % ((i * 0.37) % 3.2, x, y, r * 3.2, "ag" if last else "sg")
            inner += '<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s"/>' % (x, y, r, P["red"] if last else P["star"])
            if last: inner += '<circle class="ripple" cx="%.1f" cy="%.1f" r="9" fill="none" stroke="%s" stroke-width="1.6"/>' % (x, y, P["red"])
    else:
        inner += tw(W / 2, 150, "calendar unavailable", 16, P["dim"], anchor="middle")
    inner += tw(28, h - 18, "each star is a day with a contribution, joined in order; the newest star is red", 12.5, P["dim"])
    return card(W, h, 18, "sm", inner, "contribution star map", sdefs)


def threat(D):
    kev = D["kev"]
    fs = 14
    c = CW * fs
    h = 78 + 34 * max(len(kev), 1) + 30
    inner = tw(28, 44, "[ FEED // CISA known exploited vulnerabilities, newest first ]", 15, P["cyan"], 600, 'letter-spacing="1"')
    y = 86
    if kev:
        for i, k in enumerate(kev):
            row = (tw(28, y, k["date"], fs, P["dim"]) + tw(28 + 11 * c, y, k["cve"], fs, P["red"], 600) +
                   tw(28 + 27 * c, y, k["who"][:24], fs, P["text"]) + tw(28 + 52 * c, y, k["name"][:46], fs, P["dim"]))
            inner += '<g style="animation:fade .5s ease-out %.2fs backwards">%s</g>' % (0.3 + i * 0.35, row)
            y += 34
        inner += tw(28, h - 14, "%s entries, feed dated %s  //  source: cisa.gov  //  text is cut to printable ASCII" % (D.get("kev_count", "?"), D.get("kev_date", "?")), 12, P["faint"])
    else:
        inner += tw(28, 90, "feed unavailable at the last redraw", 15, P["dim"])
    return card(W, h, 18, "tk", inner, "CISA known exploited vulnerabilities feed")


def lablog():
    try:
        entries = json.load(open(ROOT / "data/lab-log.json", encoding="utf-8"))["entries"]
    except Exception:   # noqa: BLE001
        entries = []
    h = 78 + 34 * max(len(entries), 1) + 22
    inner = tw(28, 44, "[ LAB LOG // authorized platforms only ]", 15, P["cyan"], 600, 'letter-spacing="1"')
    y = 86
    for i, e in enumerate(entries[:6]):
        st = ascii_clean(e.get("status", ""), 14)
        col = P["green"] if st in ("rooted", "done", "solved") else P["yellow"]
        row = (tw(28, y, ascii_clean(e.get("date", ""), 11), 14.5, P["dim"]) + tw(28 + 12 * CW * 14.5, y, ascii_clean(e.get("platform", ""), 12), 14.5, P["cyan"], 600) +
               tw(28 + 26 * CW * 14.5, y, ascii_clean(e.get("name", ""), 34), 14.5, P["text"]) + tw(W - 28, y, st, 14.5, col, 600, anchor="end"))
        inner += '<g style="animation:fade .5s ease-out %.2fs backwards">%s</g>' % (0.3 + i * 0.3, row)
        y += 34
    if not entries:
        inner += tw(28, 90, "no entries yet: data/lab-log.json", 15, P["dim"])
    return card(W, h, 18, "lg", inner, "lab log")


def parse_scan():
    """the saved output of a real `plumbline scan` (data/plumbline-scan.txt): modules, check rows and the summary numbers"""
    try:
        raw = (ROOT / "data/plumbline-scan.txt").read_text(encoding="utf-8")
    except OSError:
        return None
    lines = raw.splitlines()
    meta = [l[2:].strip() for l in lines if l.startswith("# ")]
    target = next((l[len("TARGET:"):].strip() for l in lines if l.startswith("TARGET:")), "")
    mods, cur = [], None
    for l in lines:
        if l.startswith("[+] "):
            cur = dict(head=l[4:].strip(), rows=[]); mods.append(cur)
        elif l.startswith("[=] "):
            cur = None
        elif cur is not None:
            m = re.match(r"^\s+- (.*?)\s+\[ (OK|WARNING|UNKNOWN|SKIPPED|N/A|NOT_APPLICABLE)\s*\]\s*$", l)
            if m: cur["rows"].append((m.group(1), m.group(2)))
    num = lambda rx, grp=1: next((m.group(grp) for l in lines for m in [re.search(rx, l)] if m), None)
    pm = re.search(r"posture\s+([\d.]+)\s+coverage\s+([\d.]+)%", raw)
    counts = []
    for i, l in enumerate(lines):
        if "PASS" in l and "FAIL" in l and "UNKNOWN" in l:
            counts = [int(x) for x in re.findall(r"\u2502\s*(\d+)\s*\u2502", lines[i + 1])]
            break
    if not (mods and pm and len(counts) == 4):
        return None
    return dict(meta=meta, target=target, mods=mods, posture=float(pm.group(1)), coverage=float(pm.group(2)), pass_=counts[0], fail=counts[1], unknown=counts[2],
                skipped=counts[3], na=int(num(r"NOT_APPLICABLE\s+(\d+)") or 0), total=int(num(r"(\d+) checks evaluated") or 0), catalog=int(num(r"catalog (\d+)\s*$") or 0))


def replay():
    S = parse_scan()
    fs = 14.5
    if not S:
        return card(W, 120, 18, "rp", tw(28, 60, "no scan saved: data/plumbline-scan.txt", 15, P["dim"]), "plumbline scan replay")
    pick = [m for m in S["mods"] if m["head"].split()[0] in ("AUTH", "FILESYS", "KERNEL", "SERVICES", "SSHD")]
    rows = []
    for m in pick:
        rows.append(("head", m["head"].replace("\u00b7", "-")))
        bad = next(((t, st) for t, st in m["rows"] if st == "WARNING"), None)
        ok = next(((t, st) for t, st in m["rows"] if st == "OK"), None)
        unk = next(((t, st) for t, st in m["rows"] if st == "UNKNOWN"), None)
        for r in (bad, ok if ok else unk):
            if r: rows.append(("row", r))
    h = 44 + 62 + len(rows) * 23 + 24 + 230
    inner = '<rect x="1" y="1" width="%d" height="42" fill="%s"/><line x1="1" y1="43" x2="%d" y2="43" stroke="%s" stroke-width="2"/>' % (W - 2, P["panel"], W - 1, P["edge"])
    for i, c in enumerate((P["red"], P["yellow"], P["green"])):
        inner += '<circle cx="%d" cy="22" r="6.5" fill="%s" opacity=".9"/>' % (28 + i * 22, c)
    inner += tw(W / 2, 27, "plumbline 2.0.1  //  real scan of a stock Ubuntu container", 14, P["dim"], anchor="middle")
    cmd = "plumbline scan --no-color --redact"
    inner += '<text x="30" y="80" font-size="%s" fill="%s" style="animation:fade .01s steps(1) .3s backwards"><tspan fill="%s">&gt;_</tspan> sudo %s</text>' % (fs + 1, P["text"], P["red"], esc(cmd))
    y, t = 112, 1.0
    for kind, v in rows:
        if kind == "head":
            inner += '<text x="30" y="%d" font-size="%s" fill="%s" font-weight="600" style="animation:fade .3s ease-out %.2fs backwards">[+] %s</text>' % (y, fs, P["cyan"], t, esc(v))
        else:
            text, st = v
            text = ascii_clean(text, 70)
            col = {"OK": P["green"], "WARNING": P["red"], "UNKNOWN": P["yellow"]}.get(st, P["dim"])
            inner += ('<g style="animation:fade .3s ease-out %.2fs backwards"><text x="46" y="%d" font-size="%s" fill="%s">- %s</text>'
                      '<text x="%d" y="%d" font-size="%s" fill="%s" font-weight="600" text-anchor="end">[ %s ]</text></g>') % (t, y, fs, P["text"], esc(text), W - 30, y, fs, col, st)
        y += 23; t += 0.12
    y += 14
    inner += '<line x1="30" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-opacity=".6"/>' % (y, W - 30, y, P["edge"])
    y += 40
    inner += '<g style="animation:fade .5s ease-out %.2fs backwards">%s%s</g>' % (t, tw(30, y, "posture", 15, P["dim"]), tw(104, y, "%.1f" % S["posture"], 30, P["text"], 600))
    bw = W - 60 - 250
    inner += '<rect x="250" y="%d" width="%d" height="16" rx="8" fill="%s" stroke="%s"/>' % (y - 16, bw, P["panel"], P["edge"])
    inner += '<rect x="250" y="%d" width="%.1f" height="16" rx="8" fill="url(#vio)" style="transform-box:fill-box;transform-origin:left;animation:grow 1.6s ease-out %.2fs backwards"/>' % (y - 16, bw * S["posture"] / 100, t)
    inner += tw(W - 30, y + 28, "coverage %.1f%% of applicable checks" % S["coverage"], 13, P["dim"], anchor="end")
    y += 62
    cw = (W - 60 - 3 * 14) / 4
    for i, (lab, val, col) in enumerate((("PASS", S["pass_"], P["green"]), ("FAIL", S["fail"], P["red"]), ("UNKNOWN", S["unknown"], P["yellow"]), ("N/A", S["na"], P["dim"]))):
        x = 30 + i * (cw + 14)
        inner += ('<g style="animation:rise .5s ease-out %.2fs backwards"><rect x="%.1f" y="%d" width="%.1f" height="62" rx="12" fill="%s" stroke="%s"/>%s%s</g>') % (
            t + 0.4 + i * 0.15, x, y - 24, cw, P["panel"], col, tw(x + 16, y - 2, lab, 12.5, P["dim"], extra='letter-spacing="1"'), tw(x + 16, y + 26, str(val), 26, col, 600))
    y += 74
    inner += tw(30, y, "%d checks evaluated, catalog %d. UNKNOWN is not a pass: the scan could not tell." % (S["total"], S["catalog"]), 13, P["dim"])
    y += 24
    inner += tw(30, y, "real output, excerpt chosen by script; target: stock ubuntu:24.04 + openssh-server in a container, not this machine", 12, P["faint"])
    return card(W, y + 22, 18, "rp", inner, "A real plumbline scan of a stock Ubuntu container: posture %.1f, %d pass, %d fail, %d unknown" % (S["posture"], S["pass_"], S["fail"], S["unknown"]))


def build(theme, D):
    global P
    P = theme
    suffix = "" if theme["name"] == "dark" else "-light"
    c = {
        "hero": hero(D), "whoami": whoami(D), "blue": vectors("blue"), "red": vectors("red"),
        "h-log": heading("git log --author=antaryx --stat", "h1"), "h-method": heading("cat /etc/method", "h2"), "h-feed": heading("tail -f /var/feed/kev", "h3"),
        "h-stars": heading("star-map --contributions", "h4"), "h-scan": heading("sudo plumbline scan --redact", "h7"), "h-lab": heading("cat /var/log/lab.log", "h5"), "h-net": heading("netstat -ano | grep ESTABLISHED", "h6"),
        "plumbline": repo_card("plumbline", "A deterministic, offline, evidence-first host security auditor for Linux. Hang a line. See what's true.",
                               ["Go", "Linux", "CIS", "SARIF", "Apache-2.0"], [("checks", str(D["checks"])), ("modules", str(D["modules"])), ("network calls", "0"), ("release", D["version"])], "pc"),
        "plumbline-action": repo_card("plumbline-action", "Runs plumbline on a GitHub Actions runner and sends the findings to the Security tab as SARIF.",
                                      ["GitHub Actions", "SARIF", "DevSecOps"], [("pinned release", D["version"]), ("checksum", "verified")], "pa"),
        "activity": activity(D), "replay": replay(), "stack": stack(), "method": method(), "rules": rules(), "threat": threat(D), "starmap": starmap(D), "lablog": lablog(),
        "divider": divider(), "footer": footer(),
        "btn-htb": button("HACKTHEBOX", "/users/3514431", "b1"), "btn-thm": button("TRYHACKME", "/p/antaryx", "b2"), "btn-mail": button("SECURE COMM", "antaryx@proton.me", "b3"),
    }
    for name, text in c.items():
        (OUT / (name + suffix + ".svg")).write_text(text, encoding="utf-8", newline="\n")
    return {n: len(t) for n, t in c.items()}


def art_assets():
    """the avatar and the repository social-preview image, as SVG (assets/*.svg); the PNGs are rendered from them (rsvg-convert -w 1024 ...)"""
    global P
    P = DARK
    (ROOT / "assets").mkdir(exist_ok=True)
    defs, g = scorp(760, "av", False)
    av = ('<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="1024" viewBox="0 0 1024 1024"><title>Antaryx avatar</title><defs>%s'
          '<radialGradient id="abg" cx="50%%" cy="42%%" r="75%%"><stop offset="0" stop-color="#1c242b"/><stop offset="1" stop-color="#0b0f12"/></radialGradient>'
          '<linearGradient id="wm" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#5a98f0"/><stop offset=".55" stop-color="#5ccfe6"/><stop offset="1" stop-color="#ffffff"/></linearGradient>'
          '<filter id="glow"><feGaussianBlur stdDeviation="8"/></filter></defs><rect width="1024" height="1024" fill="url(#abg)"/>'
          '<g transform="translate(132 20)">%s</g>%s</svg>') % (defs, g, wordmark(300, 856, 0.56, 14))
    (ROOT / "assets/avatar.svg").write_text(av + chr(10), encoding="utf-8", newline=chr(10))
    defs2, g2 = scorp(600, "so", False)
    so = ('<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="640" viewBox="0 0 1280 640"><title>Antaryx</title><defs>%s'
          '<radialGradient id="abg" cx="35%%" cy="45%%" r="85%%"><stop offset="0" stop-color="#1c242b"/><stop offset="1" stop-color="#0b0f12"/></radialGradient>'
          '<linearGradient id="wm" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#5a98f0"/><stop offset=".55" stop-color="#5ccfe6"/><stop offset="1" stop-color="#ffffff"/></linearGradient>'
          '<filter id="glow"><feGaussianBlur stdDeviation="8"/></filter></defs><rect width="1280" height="640" fill="url(#abg)"/>'
          '<g transform="translate(40 20)">%s</g>%s'
          '<text x="690" y="400" font-family="%s" font-size="25" fill="#e6edf3" letter-spacing="1">/  SECURITY.  RESEARCH.  ADAPTATION.</text>'
          '<text x="690" y="446" font-family="%s" font-size="20" fill="#9aa7b4">hybrid security research node</text></svg>') % (defs2, g2, wordmark(690, 232, 0.72, 14), MONO, MONO)
    (ROOT / "assets/social-preview.svg").write_text(so + chr(10), encoding="utf-8", newline=chr(10))


if __name__ == "__main__":
    data = live()
    sizes = {}
    for th in (DARK, LIGHT):
        sizes[th["name"]] = build(th, data)
    art_assets()
    print("cards written:", len(sizes["dark"]) * 2, "| biggest:", max(sizes["dark"].items(), key=lambda kv: kv[1]))
    print("data:", {k: (v if not isinstance(v, list) else len(v)) for k, v in data.items()})
