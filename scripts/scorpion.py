"""The Antaryx scorpion: a segmented scorpion drawn on the skeleton of the Scorpius constellation of the GitHub avatar (claws at the top right,
body along the diagonal with Antares as its heart, tail curling at the bottom left into a stinger).

    group(style, palette, ids)  ->  SVG fragment inside a 0..512 box (normalised), styles: "neon" (outlined plates, glowing) or "flat" (one colour)
"""
import math

# ---- skeleton, in the coordinates of antaryx_banner.png (the constellation); every other shape is built from these
TAIL = [(569, 611), (561, 720), (549, 840), (445, 880), (314, 874), (237, 785), (271, 746), (321, 677)]
BODY0, BODY1 = (580, 590), (690, 405)      # the abdomen runs from here to the head
HEAD = (715, 385)
ANTARES = (730, 372)
CLAW_A = {"base": (770, 360), "elbow": (885, 300), "tip1": (968, 222), "tip2": (990, 296)}   # the big pedipalp (the constellation's claw)
CLAW_B = {"base": (700, 340), "elbow": (655, 270), "tip1": (606, 196), "tip2": (648, 180)}   # the second pedipalp, towards the upper left


def catmull(pts, n=22):
    P = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(n):
            t = k / n; t2 = t * t; t3 = t2 * t
            out.append(tuple(0.5 * (2 * p1[j] + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2 + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in (0, 1)))
    out.append(tuple(pts[-1]))
    return out


def arclen(poly):
    c = [0.0]
    for a, b in zip(poly, poly[1:]):
        c.append(c[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    return c


def sub(poly, cum, s0, s1, step=8):
    """the part of a polyline between arc-length s0 and s1, resampled every `step` units"""
    out = []
    s = s0
    while s < s1 + 1e-6:
        out.append(at(poly, cum, min(s, s1)))
        s += step
    if out[-1] != at(poly, cum, s1):
        out.append(at(poly, cum, s1))
    return out


def at(poly, cum, s):
    s = max(0.0, min(s, cum[-1]))
    lo, hi = 0, len(cum) - 1
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if cum[mid] <= s: lo = mid
        else: hi = mid
    seg = (cum[hi] - cum[lo]) or 1
    t = (s - cum[lo]) / seg
    return (poly[lo][0] + (poly[hi][0] - poly[lo][0]) * t, poly[lo][1] + (poly[hi][1] - poly[lo][1]) * t)


def tube(poly, w0, w1, cap=True):
    """a tapered band along a polyline (width w0 at the start, w1 at the end) as a closed polygon, with round ends"""
    L, R = [], []
    n = len(poly)
    for i, (x, y) in enumerate(poly):
        a = poly[max(i - 1, 0)]; b = poly[min(i + 1, n - 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]; d = math.hypot(dx, dy) or 1
        nx, ny = -dy / d, dx / d
        w = (w0 + (w1 - w0) * i / max(n - 1, 1)) / 2
        L.append((x + nx * w, y + ny * w)); R.append((x - nx * w, y - ny * w))
    pts = L + R[::-1]
    return pts


def path(pts, close=True):
    return "M" + " L".join("%.1f %.1f" % p for p in pts) + (" Z" if close else "")


def rot(v, deg):
    a = math.radians(deg); c, s = math.cos(a), math.sin(a)
    return (v[0] * c - v[1] * s, v[0] * s + v[1] * c)


def curve(p0, p1, p2, n=14):
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0], (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]) for t in [i / (n - 1) for i in range(n)]]


def shapes():
    """returns dict of lists of polygons / polylines in banner coordinates"""
    S = {"tail": [], "sting": [], "body": [], "head": [], "claws": [], "legs": [], "joints": []}
    # tail: six plates along the spiral, narrowing towards the stinger
    bx0, by0 = BODY1[0] - BODY0[0], BODY1[1] - BODY0[1]; bl0 = math.hypot(bx0, by0)
    root = (BODY0[0] + bx0 / bl0 * 14, BODY0[1] + by0 / bl0 * 14)      # just inside the last abdomen plate: the tail grows out of it
    sp = catmull([root] + TAIL[1:])      # TAIL[0] is only the anchor point on the constellation; the spline leaves the abdomen's own axis instead (no kink)
    cum = arclen(sp); total = cum[-1]
    n = 6; gap = 4; end = total * 0.94; start = total * 0.0
    seg = (end - start) / n
    for i in range(n):
        a, b = start + i * seg + gap / 2, start + (i + 1) * seg - gap / 2
        w0 = 66 - i * 6.5; w1 = 66 - (i + 1) * 6.5
        S["tail"].append(tube(sub(sp, cum, a, b, 6), w0, w1))
        S["joints"].append(at(sp, cum, start + (i + 1) * seg))
    # the stinger: a bulb and a hooked barb that carries on the curl
    E = at(sp, cum, end); E2 = at(sp, cum, end - 14)
    t = (E[0] - E2[0], E[1] - E2[1]); d = math.hypot(*t) or 1; t = (t[0] / d, t[1] / d)
    bulb_c = (E[0] + t[0] * 20, E[1] + t[1] * 20)
    bulb = [(bulb_c[0] + 26 * math.cos(a) * t[0] - 19 * math.sin(a) * -t[1], bulb_c[1] + 26 * math.cos(a) * t[1] - 19 * math.sin(a) * t[0]) for a in [i * math.pi / 8 for i in range(16)]]
    S["sting"].append(bulb)
    k1 = (bulb_c[0] + t[0] * 34, bulb_c[1] + t[1] * 34)
    nrm = rot(t, 90)
    barb = curve((bulb_c[0] + t[0] * 14, bulb_c[1] + t[1] * 14), (k1[0] + nrm[0] * 26, k1[1] + nrm[1] * 26), (k1[0] + t[0] * 4 + nrm[0] * 64, k1[1] + t[1] * 4 + nrm[1] * 64), 12)
    S["sting"].append(tube(barb, 20, 2))
    # abdomen: five plates from the tail root to the head
    bx, by = BODY1[0] - BODY0[0], BODY1[1] - BODY0[1]; bl = math.hypot(bx, by); ux, uy = bx / bl, by / bl
    for i in range(5):
        a = i / 5 * bl + 3; b = (i + 1) / 5 * bl - 3
        wa, wb = 94 - i * 4, 94 - (i + 1) * 4 + 2
        S["body"].append(tube([(BODY0[0] + ux * a, BODY0[1] + uy * a), (BODY0[0] + ux * b, BODY0[1] + uy * b)], wa, wb))
        S["joints"].append((BODY0[0] + ux * (i + 1) / 5 * bl, BODY0[1] + uy * (i + 1) / 5 * bl))
    # the head shield
    ang = math.atan2(uy, ux); cx, cy = HEAD
    loc = [(-34, -54), (32, -64), (70, -26), (74, 26), (32, 64), (-34, 54), (-52, 0)]
    S["head"].append([(cx + x * math.cos(ang) - y * math.sin(ang), cy + x * math.sin(ang) + y * math.cos(ang)) for x, y in loc])
    # two pedipalps: an arm in two parts and two blades each
    for C in (CLAW_A, CLAW_B):
        S["claws"].append(("arm", tube(curve(C["base"], ((C["base"][0] + C["elbow"][0]) / 2 + 12, (C["base"][1] + C["elbow"][1]) / 2 - 12), C["elbow"], 10), 40, 34)))
        dxa, dya = C["elbow"][0] - C["base"][0], C["elbow"][1] - C["base"][1]; da = math.hypot(dxa, dya); ua = (dxa / da, dya / da); na = (-ua[1], ua[0])
        for tip, side in ((C["tip1"], -1), (C["tip2"], 1)):
            ctrl = ((C["elbow"][0] + tip[0]) / 2 + na[0] * side * 34, (C["elbow"][1] + tip[1]) / 2 + na[1] * side * 34)
            S["claws"].append(("blade", tube(curve(C["elbow"], ctrl, tip, 12), 34, 3)))
        S["joints"].append(C["elbow"])
    # eight legs, four a side: coxa, femur and tibia with a small foot; the front pair reaches forward, the rear pair back
    for k, f in enumerate((0.93, 0.74, 0.55, 0.36)):
        px, py = BODY0[0] + ux * bl * f, BODY0[1] + uy * bl * f
        fwd = (38, 12, -14, -38)[k]
        for side in (-1, 1):
            nx, ny = -uy * side, ux * side
            pts = [(px + nx * 36, py + ny * 36),
                   (px + nx * 62 + ux * fwd * 0.5, py + ny * 62 + uy * fwd * 0.5),
                   (px + nx * 100 + ux * fwd * 1.1, py + ny * 100 + uy * fwd * 1.1),
                   (px + nx * 128 + ux * (fwd * 1.1 - 16 * (1 if fwd > 0 else -1)), py + ny * 128 + uy * (fwd * 1.1 - 16 * (1 if fwd > 0 else -1)))]
            S["legs"].append(catmull(pts, 6))
    return S


def extent(S):
    xs, ys = [], []
    for key in ("tail", "sting", "body", "head", "legs"):
        for poly in S[key]:
            for x, y in poly: xs.append(x); ys.append(y)
    for _, poly in S["claws"]:
        for x, y in poly: xs.append(x); ys.append(y)
    return min(xs), min(ys), max(xs), max(ys)


def group(style="neon", size=512, pad=26, pal=None, animate=False, uid="sc"):
    """the scorpion as an SVG fragment fitted into a size x size box. style 'neon': dark plates with a glowing outline; 'flat': one solid colour.
    animate: a pulse travels down the tail plates (CSS, class names carry uid)"""
    P = {"edge1": "#6aa8ff", "edge2": "#5ccfe6", "fill": "#10161c", "plate": "#17202a", "leg": "#5ccfe6", "star": "#e6edf3", "red": "#ff6b81", "flat": "#e6edf3"}
    if pal: P.update(pal)
    S = shapes()
    x0, y0, x1, y1 = extent(S)
    k = (size - 2 * pad) / max(x1 - x0, y1 - y0)
    ox = (size - k * (x1 - x0)) / 2 - k * x0; oy = (size - k * (y1 - y0)) / 2 - k * y0
    F = lambda poly: [(ox + k * x, oy + k * y) for x, y in poly]
    o = []
    flat = style == "flat"
    if flat:
        fill, stroke, sw = P["flat"], "none", 0
    else:
        fill, stroke, sw = P["plate"], "url(#%s-edge)" % uid, 3.2
    # legs first (behind), then claws, tail, body, head
    for leg in S["legs"]:
        poly = tube(F(leg), 22 if flat else 11, 10 if flat else 4)
        o.append('<path d="%s" fill="%s" stroke="%s" stroke-width="%s" stroke-linejoin="round"/>' % (path(poly), fill, stroke, 2.4 if not flat else 0))
    for kind, poly in S["claws"]:
        o.append('<path d="%s" fill="%s" stroke="%s" stroke-width="%s" stroke-linejoin="round"/>' % (path(F(poly)), fill, stroke, sw))
    for i, poly in enumerate(S["tail"]):
        cls = ' class="%s-seg" style="animation-delay:%.2fs"' % (uid, i * 0.22) if animate and not flat else ""
        o.append('<path d="%s" fill="%s" stroke="%s" stroke-width="%s" stroke-linejoin="round"%s/>' % (path(F(poly)), fill, stroke, sw, cls))
    for poly in S["sting"]:
        o.append('<path d="%s" fill="%s" stroke="%s" stroke-width="%s" stroke-linejoin="round"/>' % (path(F(poly)), P["red"] if not flat else fill, stroke if not flat else "none", sw))
    for poly in S["body"]:
        o.append('<path d="%s" fill="%s" stroke="%s" stroke-width="%s" stroke-linejoin="round"/>' % (path(F(poly)), fill, stroke, sw))
    for poly in S["head"]:
        o.append('<path d="%s" fill="%s" stroke="%s" stroke-width="%s" stroke-linejoin="round"/>' % (path(F(poly)), fill, stroke, sw))
    ax, ay = F([ANTARES])[0]
    if flat:
        o.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s"/>' % (ax, ay, 30 * k * 1.1, P["red"]))
    else:
        for (jx, jy) in F(S["joints"]):
            o.append('<circle cx="%.1f" cy="%.1f" r="3.2" fill="%s"/>' % (jx, jy, P["star"]))
        o.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="url(#%s-ag)"/><circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s"/><circle cx="%.1f" cy="%.1f" r="%.1f" fill="#ffd9df"/>' % (
            ax, ay, 56 * k * 1.6, uid, ax, ay, 15, P["red"], ax, ay, 5.5))
    defs = ('<linearGradient id="%s-edge" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="%s"/><stop offset="1" stop-color="%s"/></linearGradient>'
            '<radialGradient id="%s-ag"><stop offset="0" stop-color="%s" stop-opacity=".9"/><stop offset="1" stop-color="%s" stop-opacity="0"/></radialGradient>') % (
        uid, P["edge1"], P["edge2"], uid, P["red"], P["red"])
    return defs, "".join(o)


if __name__ == "__main__":
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else "."
    for style in ("neon", "flat"):
        d, g = group(style, 512)
        bg = '<rect width="512" height="512" rx="96" fill="#0b0f12"/>' if style == "neon" else '<rect width="512" height="512" rx="96" fill="#1c242b"/>'
        open("%s/scorpion-%s.svg" % (out, style), "w", encoding="utf-8", newline="\n").write(
            '<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512"><defs>%s</defs>%s%s</svg>' % (d, bg, g))
    print("ok")
