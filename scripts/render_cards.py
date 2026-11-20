#!/usr/bin/env python3
"""Draws every card of the Antaryx profile README as an animated SVG (no third-party widget services, nothing runs in a viewer's browser
except CSS/SMIL animation inside <img>). Standard library only.

    python3 scripts/render_cards.py            # writes ./cards/*.svg

Live data comes from the public GitHub API (plumbline: version, commit count, weekly commit activity, check counts from its README). If the API
is unreachable the cards fall back to the last known values below, so the script never produces a broken card.
Design: violet to silver on near-black with one red star (Antares), the Scorpius constellation of the avatar and banner.
Every base style shows the FINAL picture; animations only start from "hidden" (fill-mode: backwards), so a renderer that ignores animation
still draws a complete card.
"""
import html
import json
import os
import pathlib
import re
import time
import urllib.request

OUT = pathlib.Path(__file__).resolve().parent.parent / "cards"
OUT.mkdir(parents=True, exist_ok=True)

BG0, BG1, PANEL, EDGE = "#07050d", "#150f2b", "#100b21", "#2c2252"
VIOLET, LILAC, SILVER, TEXT, DIM, RED = "#7a64d8", "#b9a8ff", "#d9d4f2", "#e7e3f7", "#8a84a8", "#ff3b5c"
MONO = "ui-monospace, 'SF Mono', SFMono-Regular, Menlo, Consolas, 'DejaVu Sans Mono', monospace"
OWNER = "antaryx"

# ------------------------------------------------------------------ live data (public API, no token)
FALLBACK = {"version": "v2.0.1", "commits": 115, "stars": 0, "checks": 112, "modules": 11, "weeks": []}


def hdrs():
    h = {"User-Agent": "antaryx-profile-cards", "Accept": "application/vnd.github+json"}
    if os.environ.get("GITHUB_TOKEN"):
        h["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]
    return h


def api(path):
    req = urllib.request.Request("https://api.github.com" + path, headers=hdrs())
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.status, json.load(r), r.headers


def live():
    d = dict(FALLBACK)
    try:
        d["version"] = api("/repos/%s/plumbline/releases/latest" % OWNER)[1]["tag_name"]
        d["stars"] = api("/repos/%s/plumbline" % OWNER)[1]["stargazers_count"]
        _, _, h = api("/repos/%s/plumbline/commits?per_page=1" % OWNER)
        m = re.search(r'page=(\d+)>; rel="last"', h.get("Link", ""))
        if m:
            d["commits"] = int(m.group(1))
        raw = urllib.request.urlopen(urllib.request.Request("https://raw.githubusercontent.com/%s/plumbline/main/README.md" % OWNER,
                                                            headers={"User-Agent": "antaryx-profile-cards"}), timeout=20).read().decode("utf-8", "ignore")
        m = re.search(r"\*\*(\d+) checks .{1,6} (\d+) modules", raw)
        if m:
            d["checks"], d["modules"] = int(m.group(1)), int(m.group(2))
        for _ in range(5):   # the statistics endpoint answers 202 (and no data) while GitHub computes them
            st, w, _ = api("/repos/%s/plumbline/stats/commit_activity" % OWNER)
            if st == 200 and isinstance(w, list) and w:
                d["weeks"] = [x["total"] for x in w]
                break
            time.sleep(4)
    except Exception as e:  # noqa: BLE001
        print("live data unavailable, using the last known values:", e)
    return d


# ------------------------------------------------------------------ building blocks
def esc(s):
    return html.escape(str(s), quote=True)


STYLE = """
  <style>
    text { font-family: %s; }
    @keyframes tw { 0%%,100%% { opacity: .35 } 50%% { opacity: 1 } }
    @keyframes fade { from { opacity: 0 } }
    @keyframes rise { from { opacity: 0; transform: translateY(10px) } }
    @keyframes draw { from { stroke-dasharray: var(--l); stroke-dashoffset: var(--l) } to { stroke-dashoffset: 0 } }
    @keyframes ripple { from { transform: scale(.4); opacity: .9 } to { transform: scale(2.6); opacity: 0 } }
    @keyframes blink { 0%%,49%% { opacity: 1 } 50%%,100%% { opacity: 0 } }
    @keyframes scan { from { transform: translateY(-80px) } to { transform: translateY(520px) } }
    @keyframes type { from { clip-path: inset(0 100%% 0 0) } to { clip-path: inset(0 0 0 0) } }
    .tw { animation: tw 3.2s ease-in-out infinite }
    .cur { animation: blink 1s steps(1) infinite }
    .ripple { transform-box: fill-box; transform-origin: center; animation: ripple 3.4s ease-out infinite }
    .scan { animation: scan 9s linear infinite }
    @media (prefers-reduced-motion: reduce) { * { animation: none !important } }
  </style>""" % MONO


def svg(w, h, body, title, extra_defs=""):
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" role="img" aria-label="%s">\n<title>%s</title>\n'
            '<defs>%s\n  <linearGradient id="vio" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="%s"/><stop offset="1" stop-color="%s"/></linearGradient>\n'
            '  <linearGradient id="wm" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#6d56c9"/><stop offset=".55" stop-color="%s"/><stop offset="1" stop-color="#ffffff"/></linearGradient>\n'
            '  <radialGradient id="sg"><stop offset="0" stop-color="#d8ccff" stop-opacity=".9"/><stop offset="1" stop-color="%s" stop-opacity="0"/></radialGradient>\n'
            '  <radialGradient id="ag"><stop offset="0" stop-color="%s" stop-opacity=".95"/><stop offset="1" stop-color="%s" stop-opacity="0"/></radialGradient>\n'
            '  <radialGradient id="bg" cx="50%%" cy="40%%" r="80%%"><stop offset="0" stop-color="%s"/><stop offset="1" stop-color="%s"/></radialGradient>\n'
            '  <linearGradient id="scan" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="%s" stop-opacity="0"/><stop offset=".5" stop-color="%s" stop-opacity=".10"/><stop offset="1" stop-color="%s" stop-opacity="0"/></linearGradient>\n'
            '  <filter id="glow" x="-20%%" y="-40%%" width="140%%" height="180%%"><feGaussianBlur stdDeviation="7"/></filter>%s</defs>%s\n%s\n</svg>\n') % (
        w, h, w, h, esc(title), esc(title), STYLE, VIOLET, LILAC, "#8f7fe0", VIOLET, RED, RED, BG1, BG0, LILAC, LILAC, LILAC, extra_defs, "", body)


def panel(w, h, rx=22):
    return ('<rect x="1" y="1" width="%d" height="%d" rx="%d" fill="url(#bg)" stroke="%s" stroke-width="2"/>'
            '<rect class="scan" x="2" y="0" width="%d" height="80" fill="url(#scan)"/>') % (w - 2, h - 2, rx, EDGE, w - 4)


def clip(w, h, rx=22, cid="c"):
    return '<clipPath id="%s"><rect x="1" y="1" width="%d" height="%d" rx="%d"/></clipPath>' % (cid, w - 2, h - 2, rx)


# --- the Scorpius constellation of the avatar and banner (positions traced from antaryx_banner.png)
PTS = [(913, 177, "s"), (951, 258, "d"), (944, 368, "s"), (811, 331, "s"), (730, 372, "r"), (667, 443, "s"), (569, 611, "d"), (561, 720, "s"),
       (549, 840, "s"), (445, 880, "s"), (314, 874, "d"), (237, 785, "d"), (271, 746, "s"), (321, 677, "d")]
LINES = [(0, 1), (1, 2), (1, 3), (3, 4), (4, 5), (5, 6), (6, 7), (7, 8), (8, 9), (9, 10), (10, 11), (11, 12), (12, 13)]


def constellation(x, y, size, star=1.0, draw=True):
    x0 = min(p[0] for p in PTS); x1 = max(p[0] for p in PTS); y0 = min(p[1] for p in PTS); y1 = max(p[1] for p in PTS)
    k = size / max(x1 - x0, y1 - y0)
    ox, oy = x + (size - k * (x1 - x0)) / 2 - k * x0, y + (size - k * (y1 - y0)) / 2 - k * y0
    f = lambda px, py: (round(ox + k * px, 1), round(oy + k * py, 1))
    o = ['<g stroke="url(#vio)" stroke-width="%.1f" stroke-linecap="round" fill="none">' % (2.4 * star)]
    for i, (a, b) in enumerate(LINES):
        (ax, ay), (bx, by) = f(*PTS[a][:2]), f(*PTS[b][:2])
        ln = int(((ax - bx) ** 2 + (ay - by) ** 2) ** .5) + 2
        anim = ' style="--l:%d;animation:draw .5s ease-out %.2fs backwards"' % (ln, 0.4 + i * 0.18) if draw else ""
        o.append('<line x1="%s" y1="%s" x2="%s" y2="%s"%s/>' % (ax, ay, bx, by, anim))
    o.append("</g>")
    for i, (px, py, kind) in enumerate(PTS):
        cx, cy = f(px, py)
        dl = "animation-delay:%.1fs" % ((i * 0.37) % 3.2)
        if kind == "r":
            o.append('<circle class="ripple" cx="%s" cy="%s" r="%.1f" fill="none" stroke="%s" stroke-width="2"/>' % (cx, cy, 14 * star, RED))
            o.append('<circle class="ripple" style="animation-delay:1.7s" cx="%s" cy="%s" r="%.1f" fill="none" stroke="%s" stroke-width="1.5"/>' % (cx, cy, 14 * star, RED))
            o.append('<circle cx="%s" cy="%s" r="%.1f" fill="url(#ag)"/><circle class="tw" style="%s" cx="%s" cy="%s" r="%.1f" fill="%s"/>'
                     '<circle cx="%s" cy="%s" r="%.1f" fill="#ffd9df"/>' % (cx, cy, 36 * star, dl, cx, cy, 8.5 * star, RED, cx, cy, 3.2 * star))
        elif kind == "d":
            r = 8.5 * star
            o.append('<circle class="tw" style="%s" cx="%s" cy="%s" r="%.1f" fill="url(#sg)"/><path d="M%s %.1f L%.1f %s L%s %.1f L%.1f %s Z" fill="#fff"/>' % (
                dl, cx, cy, 24 * star, cx, cy - r, cx + r, cy, cx, cy + r, cx - r, cy))
        else:
            o.append('<circle class="tw" style="%s" cx="%s" cy="%s" r="%.1f" fill="url(#sg)"/><circle cx="%s" cy="%s" r="%.1f" fill="#f3eeff"/>' % (
                dl, cx, cy, 15 * star, cx, cy, 4.2 * star))
    return "".join(o)


# --- the wordmark is drawn, not typed: the same pointed A (no crossbar) as the banner, identical on every platform
LETTERS = {"A": "M0 100 L40 0 L80 100", "N": "M0 100 V0 L80 100 V0", "T": "M0 0 H80 M40 0 V100", "R": "M0 100 V0 H52 Q80 0 80 25 Q80 50 52 50 H0 M46 50 L80 100",
           "Y": "M0 0 L40 50 L80 0 M40 50 V100", "X": "M0 0 L80 100 M80 0 L0 100"}


def wordmark(x, y, scale, width=13):
    g = []
    for i, ch in enumerate("ANTARYX"):
        g.append('<path d="%s" transform="translate(%.1f 0)"/>' % (LETTERS[ch], i * 108))
    inner = "".join(g)
    return ('<g transform="translate(%s %s) scale(%.3f)" fill="none" stroke-linejoin="miter" stroke-linecap="butt">'
            '<g stroke="#8f7fe0" stroke-width="%d" opacity=".55" filter="url(#glow)">%s</g>'
            '<g stroke="url(#wm)" stroke-width="%d">%s</g></g>') % (x, y, scale, width + 6, inner, width, inner)


def digits_rain(x0, x1, y0, y1, seed=7):
    import random
    r = random.Random(seed)
    o = []
    for cx in range(x0, x1, 26):
        col = "".join('<tspan x="%d" dy="%d">%s</tspan>' % (cx, 0 if i == 0 else 22, r.choice("0123456789")) for i in range(int((y1 - y0) / 22)))
        o.append('<text class="tw" style="animation-delay:%.1fs;animation-duration:%.1fs" x="%d" y="%d" fill="%s" fill-opacity=".11" font-size="16">%s</text>' % (
            r.random() * 4, 4 + r.random() * 4, cx, y0, LILAC, col))
    return "".join(o)


def typed(x, y, text, size, fill, delay, dur, extra=""):
    steps = max(len(text), 1)
    return ('<text x="%s" y="%s" font-size="%s" fill="%s" xml:space="preserve" style="animation:type %ss steps(%d) %ss backwards" %s>%s</text>') % (
        x, y, size, fill, dur, steps, delay, extra, esc(text))


# ------------------------------------------------------------------ cards
def hero():
    w, h = 1200, 440
    b = clip(w, h, 26, "hc") and ""
    body = '<g clip-path="url(#hc)">' + panel(w, h, 26) + digits_rain(540, 1180, 40, 420) + digits_rain(20, 130, 40, 420, 3)
    body += '<g style="animation:fade 1.2s ease-out backwards">' + constellation(90, 44, 350, 1.35) + "</g>"
    body += '<g style="animation:rise .9s ease-out .6s backwards">' + wordmark(548, 124, 0.8) + "</g>"
    body += '<line x1="550" y1="246" x2="1130" y2="246" stroke="%s" stroke-opacity=".5" stroke-width="1.5"/>' % LILAC
    body += typed(550, 292, "/  SECURITY.  RESEARCH.  ADAPTATION.", 26, "#cfc8ee", 1.4, 2.6, 'textLength="566" lengthAdjust="spacing"')
    body += '<rect class="cur" x="1126" y="270" width="14" height="26" fill="%s"/>' % RED
    body += '<g style="animation:fade 1s ease-out 2.6s backwards"><text x="550" y="340" font-size="17" fill="%s">hybrid security research node</text>' % DIM
    body += '<text x="550" y="368" font-size="17" fill="%s">blue team  <tspan fill="%s">+</tspan>  red team  <tspan fill="%s">//</tspan>  authorized scope only</text></g>' % (DIM, RED, VIOLET)
    # HUD corners
    for (cx, cy, sx, sy) in ((22, 22, 1, 1), (w - 22, 22, -1, 1), (22, h - 22, 1, -1), (w - 22, h - 22, -1, -1)):
        body += '<path d="M%d %d h%d M%d %d v%d" stroke="%s" stroke-width="2" stroke-opacity=".7" fill="none"/>' % (cx, cy, 26 * sx, cx, cy, 26 * sy, LILAC)
    body += "</g>"
    return svg(w, h, body, "ANTARYX - security. research. adaptation.", clip(w, h, 26, "hc"))


def term(w, h, title, lines, cid, total_delay=0.4):
    """lines: (kind, text) kind: p prompt, o output, d dim, r red, k ok"""
    body = '<g clip-path="url(#%s)">' % cid + panel(w, h)
    body += '<rect x="1" y="1" width="%d" height="44" fill="%s"/><line x1="1" y1="45" x2="%d" y2="45" stroke="%s" stroke-width="2"/>' % (w - 2, PANEL, w - 1, EDGE)
    for i, c in enumerate(("#ff5f67", "#f5c451", "#5fd38d")):
        body += '<circle cx="%d" cy="23" r="7" fill="%s" opacity=".85"/>' % (30 + i * 24, c)
    body += '<text x="%d" y="29" font-size="15" fill="%s" text-anchor="middle">%s</text>' % (w // 2, DIM, esc(title))
    y, t = 86, total_delay
    for kind, text in lines:
        if kind == "p":
            body += '<text x="34" y="%d" font-size="20" fill="%s" style="animation:fade .01s steps(1) %.2fs backwards"><tspan fill="%s">&gt;_</tspan> %s</text>' % (y, TEXT, t, RED, esc(text))
            t += 0.9
        else:
            col = {"o": SILVER, "d": DIM, "r": RED, "k": "#7ee7b0"}[kind]
            body += '<text x="34" y="%d" font-size="19" fill="%s" style="animation:fade .4s ease-out %.2fs backwards">%s</text>' % (y, col, t, esc(text))
            t += 0.5
        y += 34
    return body, t, y


def whoami():
    w, h = 1200, 402
    lines = [("p", "whoami && id"), ("o", "antaryx   uid=1337(antaryx) gid=1337(operators) groups=defense,offense,research"),
             ("p", "cat /etc/mission"), ("o", "operating in the void between defensive architecture and offensive exploitation."),
             ("p", "echo $RULES_OF_ENGAGEMENT"), ("k", "authorized targets only  //  HTB  THM  CTF  own lab  //  scope before scan"),
             ("p", "plumbline scan --offline"), ("o", "%d checks  %d modules  0 network calls  evidence first" % (D["checks"], D["modules"]))]
    body, t, y = term(w, h, "antaryx@void: ~", lines, "wc")
    body += '<text x="34" y="%d" font-size="20" fill="%s"><tspan fill="%s">&gt;_</tspan></text><rect class="cur" x="74" y="%d" width="11" height="22" fill="%s"/></g>' % (y, TEXT, RED, y - 18, RED)
    return svg(w, h, body, "whoami: a hybrid security research node", clip(w, h, 22, "wc"))


def vectors(kind):
    w, h = 598, 330
    blue = kind == "blue"
    head = "DEFENSE_VECTORS  //  BLUE TEAM" if blue else "OFFENSE_VECTORS  //  RED TEAM"
    accent = LILAC if blue else RED
    items = [("Anomaly detection", "parsing the void for unauthorized telemetry"), ("Forensic architecture", "reconstructing fragmented footprints, auditing access logs"),
             ("System hardening", "impenetrable Linux / WSL and containerised infrastructure")] if blue else [
        ("Vulnerability research", "logic flaws, misconfigurations, system weaknesses"), ("Payload engineering", "silent, adaptive execution chains"),
        ("Stealth operations", "behavioural mutation, footprint reduction")]
    body = '<g clip-path="url(#vc%s)">' % kind + panel(w, h)
    body += '<text x="30" y="52" font-size="19" fill="%s" letter-spacing="1.5">[ %s ]</text>' % (accent, head)
    body += '<line x1="30" y1="68" x2="%d" y2="68" stroke="%s" stroke-opacity=".5"/>' % (w - 30, accent)
    for i, (a, b) in enumerate(items):
        y = 112 + i * 62
        body += ('<g style="animation:rise .6s ease-out %.2fs backwards"><path d="M34 %d l9 7 l-9 7" stroke="%s" stroke-width="3" fill="none" stroke-linecap="round"/>'
                 '<text x="58" y="%d" font-size="20" fill="%s">%s</text><text x="58" y="%d" font-size="14.5" fill="%s">%s</text></g>') % (
            0.3 + i * 0.25, y - 14, accent, y, TEXT, esc(a), y + 22, DIM, esc(b))
    foot = "defence is the ground truth: measure it" if blue else "scope-gated  //  authorized targets only"
    body += '<text x="30" y="%d" font-size="14" fill="%s">%s</text></g>' % (h - 24, accent if not blue else DIM, esc(foot))
    return svg(w, h, body, head, clip(w, h, 22, "vc" + kind))


def repo_card(name, tagline, chips, stats, cid):
    w, h = 598, 260
    body = '<g clip-path="url(#%s)">' % cid + panel(w, h)
    body += '<path d="M30 40 h10 v-10 M30 40 v-12 h10" stroke="%s" fill="none" stroke-width="0"/>' % LILAC
    body += '<text x="30" y="54" font-size="26" fill="%s" font-weight="bold">%s</text>' % (TEXT, esc(name))
    body += '<circle cx="%d" cy="46" r="5" fill="%s"/>' % (w - 38, RED)
    # wrap the tagline over two lines
    words, lines, cur = tagline.split(), [], ""
    for wd in words:
        if len(cur) + len(wd) + 1 > 52:
            lines.append(cur); cur = wd
        else:
            cur = (cur + " " + wd).strip()
    lines.append(cur)
    for i, ln in enumerate(lines[:3]):
        body += '<text x="30" y="%d" font-size="16" fill="%s">%s</text>' % (92 + i * 24, SILVER, esc(ln))
    x = 30
    for c in chips:
        cw = 14 + len(c) * 8.6
        body += '<rect x="%.1f" y="172" width="%.1f" height="28" rx="14" fill="none" stroke="%s" stroke-opacity=".8"/><text x="%.1f" y="191" font-size="14" fill="%s" text-anchor="middle">%s</text>' % (
            x, cw, LILAC, x + cw / 2, LILAC, esc(c))
        x += cw + 10
    body += '<line x1="30" y1="214" x2="%d" y2="214" stroke="%s" stroke-opacity=".5"/>' % (w - 30, EDGE)
    sx = 30
    for label, val in stats:
        body += '<text x="%d" y="242" font-size="17" fill="%s" font-weight="bold">%s <tspan font-size="13" fill="%s" font-weight="normal">%s</tspan></text>' % (sx, TEXT, esc(val), DIM, esc(label))
        sx += 24 + len(val + label) * 9.6
    body += "</g>"
    return svg(w, h, body, name, clip(w, h, 22, cid))


def activity():
    w, h = 1200, 230
    weeks = D["weeks"] or [0] * 52
    mx = max(max(weeks), 1)
    body = '<g clip-path="url(#ac)">' + panel(w, h)
    body += '<text x="34" y="46" font-size="18" fill="%s" letter-spacing="1.5">[ SIGNAL // plumbline commit activity, last %d weeks ]</text>' % (LILAC, len(weeks))
    body += '<text x="%d" y="46" font-size="15" fill="%s" text-anchor="end">%d commits in total  //  %s</text>' % (w - 34, DIM, D["commits"], esc(D["version"]))
    x0, x1, yb, ht = 40, w - 40, 196, 110
    step = (x1 - x0) / max(len(weeks) - 1, 1)
    pts = [(x0 + i * step, yb - ht * v / mx) for i, v in enumerate(weeks)]
    area = "M%.1f %d " % (pts[0][0], yb) + " ".join("L%.1f %.1f" % p for p in pts) + " L%.1f %d Z" % (pts[-1][0], yb)
    line = "M" + " L".join("%.1f %.1f" % p for p in pts)
    body += '<defs><linearGradient id="ar" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="%s" stop-opacity=".55"/><stop offset="1" stop-color="%s" stop-opacity="0"/></linearGradient></defs>' % (VIOLET, VIOLET)
    body += '<path d="%s" fill="url(#ar)" style="animation:fade 1.4s ease-out .3s backwards"/>' % area
    body += '<path d="%s" fill="none" stroke="url(#vio)" stroke-width="2.4" stroke-linejoin="round" style="--l:3200;animation:draw 2.2s ease-out .2s backwards"/>' % line
    if any(weeks):
        i = max(range(len(weeks)), key=lambda k: weeks[k]); px, py = pts[i]
        body += '<circle class="ripple" cx="%.1f" cy="%.1f" r="9" fill="none" stroke="%s" stroke-width="2"/><circle cx="%.1f" cy="%.1f" r="5" fill="%s"/>' % (px, py, RED, px, py, RED)
        body += '<text x="%.1f" y="%.1f" font-size="13" fill="%s" text-anchor="middle">peak %d</text>' % (px, max(py - 16, 70), RED, weeks[i])
    body += "</g>"
    return svg(w, h, body, "plumbline commit activity", clip(w, h, 22, "ac"))


def rules():
    w, h = 1200, 96
    items = ["AUTHORIZED TARGETS ONLY", "SCOPE BEFORE SCAN", "EVIDENCE OVER OPINION", "REPORT, NEVER WEAPONISE"]
    body = '<g clip-path="url(#rc)">' + panel(w, h, 18)
    cw = (w - 40) / len(items)
    for i, t in enumerate(items):
        cx = 20 + cw * i + cw / 2
        body += '<g style="animation:fade .6s ease-out %.2fs backwards"><path d="M%.1f 34 l7 7 l-7 7 l-7 -7 Z" fill="%s"/><text x="%.1f" y="66" font-size="15" fill="%s" text-anchor="middle" letter-spacing="1.2">%s</text></g>' % (
            0.2 + i * 0.2, cx, RED if i == 0 else LILAC, cx, SILVER, t)
    body += "</g>"
    return svg(w, h, body, "rules of engagement", clip(w, h, 18, "rc"))


def button(name, label, sub, cid):
    w, h = 286, 64
    body = '<g clip-path="url(#%s)">' % cid + panel(w, h, 16)
    body += '<text x="22" y="29" font-size="17" fill="%s" font-weight="bold" letter-spacing="1">%s</text><text x="22" y="49" font-size="13" fill="%s">%s</text>' % (TEXT, esc(label), DIM, esc(sub))
    body += '<path d="M%d 22 l9 10 l-9 10" stroke="%s" stroke-width="3" fill="none" stroke-linecap="round"/></g>' % (w - 34, RED)
    return svg(w, h, body, label + " " + sub, clip(w, h, 16, cid))


def footer():
    w, h = 1200, 210
    lines = [("p", "exit"), ("k", "[ IDENTITY: VERIFIED ]"), ("d", "[ PGP FINGERPRINT: UNAVAILABLE ]"), ("d", "Connection to 127.0.0.1 closed.")]
    body, t, y = term(w, h, "antaryx@void: ~", lines, "fc")
    body += '<rect class="cur" x="34" y="%d" width="11" height="20" fill="%s"/></g>' % (y - 18, RED)
    return svg(w, h, body, "connection closed", clip(w, h, 22, "fc"))


def stack():
    w, h = 1200, 92
    items = ["Python", "Go", "Docker", "Bash", "Django", "Linux / WSLg", "Git"]
    body = '<g clip-path="url(#sk)">' + panel(w, h, 18)
    body += '<text x="30" y="30" font-size="14" fill="%s" letter-spacing="1.5">CORE_STACK</text>' % DIM
    x = 30
    for i, t in enumerate(items):
        cw = 42 + len(t) * 10.6
        body += ('<g style="animation:fade .5s ease-out %.2fs backwards"><rect x="%.1f" y="42" width="%.1f" height="34" rx="17" fill="none" stroke="%s" stroke-opacity=".85"/>'
                 '<circle cx="%.1f" cy="59" r="3.5" fill="%s"/><text x="%.1f" y="64" font-size="16" fill="%s">%s</text></g>') % (
            0.2 + i * 0.15, x, cw, LILAC, x + 19, RED if t == "Go" else VIOLET, x + 32, TEXT, esc(t))
        x += cw + 12
    body += "</g>"
    return svg(w, h, body, "core stack: " + ", ".join(items), clip(w, h, 18, "sk"))


def divider():
    w, h = 1200, 70
    body = '<line x1="40" y1="35" x2="560" y2="35" stroke="url(#vio)" stroke-opacity=".6"/><line x1="640" y1="35" x2="1160" y2="35" stroke="url(#vio)" stroke-opacity=".6"/>'
    body += constellation(568, 2, 64, 0.45, draw=False)
    return svg(w, h, body, "divider")


D = live()
cards = {
    "hero": hero(), "whoami": whoami(), "blue": vectors("blue"), "red": vectors("red"),
    "plumbline": repo_card("plumbline", "A deterministic, offline, evidence-first host security auditor for Linux. Hang a line. See what's true.",
                           ["Go", "Linux", "CIS", "SARIF", "Apache-2.0"], [("checks", str(D["checks"])), ("modules", str(D["modules"])), ("network calls", "0"), ("release", D["version"])], "pc"),
    "plumbline-action": repo_card("plumbline-action", "Runs plumbline on a GitHub Actions runner and sends the findings to the Security tab as SARIF.",
                                  ["GitHub Actions", "SARIF", "DevSecOps"], [("pinned release", D["version"]), ("checksum", "verified")], "pa"),
    "activity": activity(), "stack": stack(), "rules": rules(), "divider": divider(), "footer": footer(),
    "btn-htb": button("htb", "HACKTHEBOX", "/users/3514431", "b1"), "btn-thm": button("thm", "TRYHACKME", "/p/antaryx", "b2"), "btn-mail": button("mail", "SECURE COMM", "antaryx@proton.me", "b3"),
}
for name, text in cards.items():
    (OUT / (name + ".svg")).write_text(text, encoding="utf-8", newline="\n")
print("cards:", {n: len(t) for n, t in cards.items()})
print("data:", {k: v for k, v in D.items() if k != "weeks"}, "weeks:", len(D["weeks"]))
