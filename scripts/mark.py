"""The Antaryx marks (standard library only), built from the wordmark's lambda (an A without a bar):

    sigil   a hexagon the red sting breaks out of, the lambda inside it, Antares (the red star) at its heart. Big places: avatar, hero, social preview.
    lambda  the lambda alone, one leg curling into the sting, Antares in the arch. Small places: panel icon, divider.

group(style, size, pad, pal, animate, uid, kind) -> (defs, body): the same interface the old scorpion module had.
pal keys: edge1 (blue), edge2 (cyan), red, flat (text colour: the end of the ink gradient and the whole flat icon)
"""
import math

BBOX = {"mark": (76, 66, 440, 522)}


def hook(p0, p1, p2, w0, n=28, w1=1.5):
    """a tapered curved horn along a quadratic bezier: w0 wide at the start, a sharp point at the end"""
    pts = [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0], (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]) for t in [i / n for i in range(n + 1)]]
    left, right = [], []
    for i, (x, y) in enumerate(pts):
        a = pts[max(i - 1, 0)]
        b = pts[min(i + 1, n)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        d = math.hypot(dx, dy) or 1
        w = (w0 * (1 - i / n) ** 0.85 + w1) / 2
        left.append((x - dy / d * w, y + dx / d * w))
        right.append((x + dy / d * w, y - dx / d * w))
    return "M" + " L".join("%.1f %.1f" % p for p in left + right[::-1]) + " Z"


def _star(cx, cy, r, flat, uid, red):
    if flat:
        return '<circle cx="%s" cy="%s" r="%s" fill="%s"/>' % (cx, cy, r * 1.25, red)
    return ('<circle cx="%s" cy="%s" r="%s" fill="url(#%s-ag)"/><circle cx="%s" cy="%s" r="%s" fill="%s"/><circle cx="%s" cy="%s" r="%s" fill="#ffd9df"/>'
            % (cx, cy, r * 3.6, uid, cx, cy, r, red, cx, cy, r * 0.38))


def group(style="neon", size=512, pad=26, pal=None, animate=False, uid="mk", kind="mark"):
    c = {"edge1": "#5a98f0", "edge2": "#5ccfe6", "red": "#ff6b81", "flat": "#e6edf3"}
    if pal:
        c.update({k: v for k, v in pal.items() if k in c})
    flat = style == "flat"
    ink = c["flat"] if flat else "url(#%s-ink)" % uid
    redf = c["red"] if flat else "url(#%s-red)" % uid
    seg = ' class="%s-seg"' % uid if animate and not flat else ""
    o = []

    def stroke(d, w):
        if not flat:
            o.append('<path d="%s" fill="none" stroke="%s" stroke-width="%s" stroke-linejoin="miter" stroke-miterlimit="10" opacity=".4" filter="url(#%s-gl)"/>' % (d, c["edge2"], w, uid))
        o.append('<path d="%s" fill="none" stroke="%s" stroke-width="%s" stroke-linejoin="miter" stroke-miterlimit="10"/>' % (d, ink, w))

    # one mark: a hexagon with a notch; the lambda inside has its right leg break out through the notch and curl into the red sting; Antares in the arch
    cx, cy, R = 256, 266, 190
    V = [(cx + R * math.cos(math.radians(-90 + 60 * k)), cy + R * math.sin(math.radians(-90 + 60 * k))) for k in range(6)]
    def along(a, b, t):
        return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
    p_in, p_out = along(V[2], V[3], 0.50), along(V[2], V[3], 0.12)
    hexd = "M%.1f %.1f " % p_in + " ".join("L%.1f %.1f" % p for p in (V[3], V[4], V[5], V[0], V[1], V[2], p_out))
    stroke(hexd, 24 if flat else 16)
    stroke("M158 392 L256 168 L368 410", 36 if flat else 32)
    o.append('<path d="%s" fill="%s"%s/>' % (hook((368, 410), (412, 506), (310, 514), 34), redf, seg))
    o.append(_star(256, 322, 17, flat, uid, c["red"]))
    x0, y0, x1_, y1_ = BBOX['mark']
    k = (size - 2 * pad) / max(x1_ - x0, y1_ - y0)
    ox = (size - k * (x1_ - x0)) / 2 - k * x0
    oy = (size - k * (y1_ - y0)) / 2 - k * y0
    body = '<g transform="translate(%.2f %.2f) scale(%.4f)">%s</g>' % (ox, oy, k, "".join(o))
    defs = ('<linearGradient id="%s-ink" gradientUnits="userSpaceOnUse" x1="90" y1="0" x2="430" y2="0"><stop offset="0" stop-color="%s"/><stop offset=".55" stop-color="%s"/><stop offset="1" stop-color="%s"/></linearGradient>'
            '<linearGradient id="%s-red" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#ff9aa9"/><stop offset=".5" stop-color="%s"/><stop offset="1" stop-color="#d2415c"/></linearGradient>'
            '<radialGradient id="%s-ag"><stop offset="0" stop-color="%s" stop-opacity=".8"/><stop offset="1" stop-color="%s" stop-opacity="0"/></radialGradient>'
            '<filter id="%s-gl" x="-30%%" y="-30%%" width="160%%" height="160%%"><feGaussianBlur stdDeviation="7"/></filter>') % (
        uid, c["edge1"], c["edge2"], c["flat"], uid, c["red"], uid, c["red"], c["red"], uid)
    return defs, body
