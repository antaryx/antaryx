"""The Antaryx scorpion, v2: a naturalistic side-profile scorpion, drawn procedurally (standard library only). Original artwork.

Anatomy shown: carapace with two median eyes and a ridge, seven overlapping mesosomal plates, a five-segment tail (metasoma) arching over the back
into a telson with a curved aculeus (the stinger), two pedipalps with a chela (palm, fixed finger, movable finger), and four pairs of jointed
walking legs with tarsal claws (the far-side legs sit behind, darker). Antares, the red star of the constellation, glows on the carapace.

    group(style, size, pad, pal, animate, uid)  ->  (defs, svg-fragment)  fitted into a size x size box
      style "neon": lit, shaded armour with a cool rim light; style "flat": one solid colour (the small panel icon)
"""
import math

DESIGN_W, DESIGN_H = 860, 640     # design space; the artwork is fitted into the box at the end


# ------------------------------------------------------------------ geometry helpers
def catmull(pts, n=18):
    P = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(n):
            t = k / n; t2 = t * t; t3 = t2 * t
            out.append(tuple(0.5 * (2 * p1[j] + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2 + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in (0, 1)))
    out.append(tuple(pts[-1]))
    return out


def cum(poly):
    c = [0.0]
    for a, b in zip(poly, poly[1:]):
        c.append(c[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    return c


def at(poly, c, s):
    s = max(0.0, min(s, c[-1]))
    lo, hi = 0, len(c) - 1
    while hi - lo > 1:
        m = (lo + hi) // 2
        if c[m] <= s: lo = m
        else: hi = m
    seg = (c[hi] - c[lo]) or 1
    t = (s - c[lo]) / seg
    return (poly[lo][0] + (poly[hi][0] - poly[lo][0]) * t, poly[lo][1] + (poly[hi][1] - poly[lo][1]) * t)


def part(poly, c, s0, s1, step=7):
    out, s = [], s0
    while s < s1:
        out.append(at(poly, c, s)); s += step
    out.append(at(poly, c, s1))
    return out


def tube(poly, wf, cap=False):
    """a band along a polyline; wf(t) is its width at parameter t in 0..1 (organic: pass a function with bulges); cap=True rounds both ends"""
    L, R, N = [], [], []
    n = len(poly)
    for i, (x, y) in enumerate(poly):
        a = poly[max(i - 1, 0)]; b = poly[min(i + 1, n - 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]; d = math.hypot(dx, dy) or 1
        nx, ny = -dy / d, dx / d
        w = wf(i / max(n - 1, 1)) / 2
        L.append((x + nx * w, y + ny * w)); R.append((x - nx * w, y - ny * w)); N.append((nx, ny, dx / d, dy / d, w))
    if not cap:
        return L + R[::-1]
    nx, ny, dx, dy, w = N[-1]
    end = [(poly[-1][0] + (nx * math.cos(th) + dx * math.sin(th)) * w, poly[-1][1] + (ny * math.cos(th) + dy * math.sin(th)) * w) for th in [k * math.pi / 8 for k in range(1, 8)]]
    nx, ny, dx, dy, w = N[0]
    start = [(poly[0][0] + (-nx * math.cos(th) - dx * math.sin(th)) * w, poly[0][1] + (-ny * math.cos(th) - dy * math.sin(th)) * w) for th in [k * math.pi / 8 for k in range(1, 8)]]
    return L + end + R[::-1] + start


def smooth_path(pts):
    """a closed path through pts with rounded corners (quadratic curves through the midpoints)"""
    n = len(pts)
    mids = [((pts[i][0] + pts[(i + 1) % n][0]) / 2, (pts[i][1] + pts[(i + 1) % n][1]) / 2) for i in range(n)]
    d = "M%.1f %.1f" % mids[-1]
    for i in range(n):
        d += " Q%.1f %.1f %.1f %.1f" % (pts[i][0], pts[i][1], mids[i][0], mids[i][1])
    return d + " Z"


def poly_path(pts):
    return "M" + " L".join("%.1f %.1f" % p for p in pts) + " Z"


def rot(p, deg, o=(0, 0)):
    a = math.radians(deg); c, s = math.cos(a), math.sin(a)
    x, y = p[0] - o[0], p[1] - o[1]
    return (o[0] + x * c - y * s, o[1] + x * s + y * c)


def bez(p0, p1, p2, n=14):
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0], (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]) for t in [i / (n - 1) for i in range(n)]]


# ------------------------------------------------------------------ the animal
def build():
    """returns dict of part lists, each a list of (name, path-d) in drawing order groups; coordinates in design space (facing left)"""
    A = {"legs_far": [], "legs": [], "claw_far": [], "claw": [], "plates": [], "carapace": [], "tail": [], "telson": [], "sting": [], "keels": [], "detail": [], "joints": []}

    # -- legs: hip, knee, ankle, foot; (dx, dy) shifts the far side behind and above
    def leg(hip, knee, ankle, foot, shift=(0, 0), width=(17, 5)):
        pts = [(hip[0] + shift[0], hip[1] + shift[1]), (knee[0] + shift[0], knee[1] + shift[1]), (ankle[0] + shift[0], ankle[1] + shift[1]), (foot[0] + shift[0], foot[1] + shift[1])]
        sp = catmull(pts, 8)
        poly = tube(sp, lambda t: width[0] + (width[1] - width[0]) * t + 5 * math.sin(math.pi * min(t * 2.0, 1.0)))
        return smooth_path(poly), None, pts
    LEGS = [((345, 522), (288, 508), (258, 568), (232, 616)), ((392, 528), (350, 534), (334, 588), (314, 620)),
            ((442, 530), (464, 542), (480, 592), (496, 620)), ((490, 526), (530, 530), (558, 584), (586, 616))]
    for i, (h, k, a, f) in enumerate(LEGS):
        p, c, pts = leg(h, k, a, f, (28, -18), (15, 4))
        A["legs_far"].append((p, None))
        p, c, pts = leg(h, k, a, f)
        A["legs"].append((p, None))
        A["joints"] += [pts[1], pts[2]]

    # -- pedipalps: a two-part arm and a chela (palm + fixed finger + movable finger)
    def pedipalp(base, elbow, wrist, ang, shift=(0, 0), s=1.0):
        pts = [(base[0] + shift[0], base[1] + shift[1]), (elbow[0] + shift[0], elbow[1] + shift[1]), (wrist[0] + shift[0], wrist[1] + shift[1])]
        arm = tube(catmull(pts, 10), lambda t: (38 - 10 * t) * s + 9 * math.sin(math.pi * t), True)
        wx, wy = pts[2]
        def L(p): return rot((wx + p[0] * s, wy + p[1] * s), ang, (wx, wy))
        palm = [L((22 + 58 * math.cos(a) * 0.95, 40 * math.sin(a))) for a in [i * math.pi / 10 for i in range(20)]]
        fixed = tube([L(p) for p in bez((50, -20), (128, -66), (196, -16), 18)], lambda t: (40 - 36 * t) * s + 6 * math.sin(math.pi * t))
        movable = tube([L(p) for p in bez((50, 20), (136, 50), (190, 2), 18)], lambda t: (34 - 31 * t) * s + 5 * math.sin(math.pi * t))
        return smooth_path(arm), smooth_path(palm), smooth_path(fixed), smooth_path(movable), L((90, 0)), pts[1]
    A["claw_far"] = list(pedipalp((330, 470), (262, 426), (206, 366), -50, (56, -50), 0.92)[:4])
    near = pedipalp((322, 480), (246, 452), (172, 396), -34)
    A["claw"] = list(near[:4]); A["joints"] += [near[5], near[4]]

    # -- carapace (prosoma): a low shield with a raised eye mound
    car = [(296, 478), (306, 438), (344, 414), (396, 402), (448, 406), (484, 424), (494, 470), (490, 514), (462, 530), (386, 534), (322, 528), (300, 508)]
    A["carapace"] = [smooth_path(car)]
    A["detail"] += [("ridge", "M330 440 Q400 418 470 436"), ("ridge", "M338 500 Q400 520 478 506")]
    A["eyes"] = [(350, 424, 8), (372, 416, 7)]

    # -- mesosoma: seven overlapping plates, narrowing and rising towards the tail
    for i in range(7):
        x0 = 480 + i * 29; x1 = x0 + 36
        top = 410 - i * 5.5; bot = 528 - i * 9
        A["plates"].append(smooth_path([(x0, top + 6), ((x0 + x1) / 2, top - 5), (x1, top + 4), (x1 + 4, (top + bot) / 2), (x1, bot - 2), ((x0 + x1) / 2, bot + 6), (x0, bot - 4), (x0 - 3, (top + bot) / 2)]))
        A["keels"].append("M%.1f %.1f Q%.1f %.1f %.1f %.1f" % (x0 + 4, top + 10, (x0 + x1) / 2, top + 2, x1 - 2, top + 9))

    # -- tail (metasoma): five segments arching over the back, then the telson
    spine = catmull([(676, 420), (730, 404), (782, 358), (808, 292), (800, 222), (766, 160), (716, 118), (660, 104), (606, 118)], 14)
    c = cum(spine); total = c[-1]
    n = 5; gap = 3; s0, s1 = 0.0, total * 0.97
    seg = (s1 - s0) / n
    widths = [(62, 54), (54, 48), (48, 43), (43, 38), (38, 33)]
    for i in range(n):
        a, b = s0 + i * seg + gap / 2, s0 + (i + 1) * seg - gap / 2
        w0, w1 = widths[i]
        sp = part(spine, c, a, b, 6)
        A["tail"].append(smooth_path(tube(sp, lambda t, w0=w0, w1=w1: w0 + (w1 - w0) * t + 7 * math.sin(math.pi * t), True)))
        A["keels"].append("M" + " L".join("%.1f %.1f" % (x + (-0.0) * 1, y - 8) for (x, y) in sp[::2]))
        A["joints"].append(at(spine, c, s0 + (i + 1) * seg))
    E = at(spine, c, s1); E2 = at(spine, c, s1 - 16)
    t = (E[0] - E2[0], E[1] - E2[1]); d = math.hypot(*t) or 1; t = (t[0] / d, t[1] / d)
    bc = (E[0] + t[0] * 26, E[1] + t[1] * 26)
    A["telson"] = [smooth_path([(bc[0] + (30 * math.cos(a)) * t[0] - (22 * math.sin(a)) * -t[1], bc[1] + (30 * math.cos(a)) * t[1] - (22 * math.sin(a)) * t[0]) for a in [i * math.pi / 10 for i in range(20)]])]
    nrm = (-t[1], t[0])
    tip = (bc[0] + t[0] * 62 - nrm[0] * 30, bc[1] + t[1] * 62 - nrm[1] * 30)      # the aculeus hooks down and forward
    ctrl = (bc[0] + t[0] * 46, bc[1] + t[1] * 46 + 8)
    A["sting"] = [smooth_path(tube(bez((bc[0] + t[0] * 18, bc[1] + t[1] * 18), ctrl, (tip[0], tip[1] + 34), 14), lambda u: 26 * (1 - u) ** 0.9 + 1.5))]
    A["tip"] = (tip[0], tip[1] + 34)
    A["antares"] = (404, 458)
    return A


def bbox(A):
    xs, ys = [], []
    def grab(d):
        import re
        nums = re.findall(r"-?\d+\.?\d*", d)
        for i in range(0, len(nums) - 1, 2):
            xs.append(float(nums[i])); ys.append(float(nums[i + 1]))
    for key in ("legs_far", "legs"):
        for p, c in A[key]: grab(p)
    for key in ("claw_far", "claw", "plates", "carapace", "tail", "telson", "sting"):
        for d in A[key]: grab(d)
    return min(xs), min(ys), max(xs), max(ys)


def group(style="neon", size=512, pad=26, pal=None, animate=False, uid="sc"):
    P = {"hi": "#7fd8ee", "rim": "#5ccfe6", "rim2": "#3a78d6", "top": "#41566e", "mid": "#1b2632", "bot": "#080c10", "far": "#0e151c", "star": "#eef6ff", "red": "#ff6b81", "flat": "#e6edf3", "dark": "#05080b"}
    if pal:
        # callers pass the card palette (edge1/edge2/plate/star/red/flat); map what we use
        if "edge1" in pal: P["rim2"] = pal["edge1"]
        if "edge2" in pal: P["rim"] = pal["edge2"]; P["hi"] = pal["edge2"]
        if "plate" in pal: P["mid"] = pal["plate"]; P["top"] = pal["plate_hi"] if "plate_hi" in pal else P["top"]
        if "star" in pal: P["star"] = pal["star"]
        if "red" in pal: P["red"] = pal["red"]
        if "flat" in pal: P["flat"] = pal["flat"]
    A = build()
    x0, y0, x1, y1 = bbox(A)
    k = (size - 2 * pad) / max(x1 - x0, y1 - y0)
    ox = (size - k * (x1 - x0)) / 2 - k * x0; oy = (size - k * (y1 - y0)) / 2 - k * y0
    flat = style == "flat"
    o = []
    fill = "url(#%s-fill)" % uid if not flat else P["flat"]
    edge = "url(#%s-edge)" % uid if not flat else "none"
    sw = 1.6 if not flat else 0
    farfill = "url(#%s-far)" % uid if not flat else P["flat"]
    farop = "" if not flat else ' opacity=".55"'
    def shape(d, f, st=edge, w=sw, extra=""):
        return '<path d="%s" fill="%s" stroke="%s" stroke-width="%s" stroke-linejoin="round"%s/>' % (d, f, st, w, extra)
    # far side first (the flat icon is a clean silhouette: no far side)
    if not flat:
        for p, c in A["legs_far"]:
            o.append(shape(p, farfill, "url(#%s-edge2)" % uid, 1.2, farop))
        for d in A["claw_far"]:
            o.append(shape(d, farfill, "url(#%s-edge2)" % uid, 1.2, farop))
    # tail behind the body? the tail rises from the last plate: draw it before the plates so the plates overlap its root
    for i, d in enumerate(A["tail"]):
        cls = ' class="%s-seg" style="animation-delay:%.2fs"' % (uid, i * 0.25) if animate and not flat else ""
        o.append(shape(d, fill, extra=cls))
    for d in A["telson"]:
        o.append(shape(d, "url(#%s-red)" % uid if not flat else P["flat"], "url(#%s-edge)" % uid if not flat else "none"))
    for d in A["sting"]:
        o.append(shape(d, "url(#%s-red)" % uid if not flat else P["flat"], "none"))
    # near legs, then body plates (right to left so each plate overlaps the next), then carapace, then the near pedipalp on top
    for p, c in A["legs"]:
        o.append(shape(p, fill))
    for d in reversed(A["plates"]):
        o.append(shape(d, fill))
    for d in A["claw"]:
        o.append(shape(d, fill))
    for d in A["carapace"]:
        o.append(shape(d, fill))
    if not flat:
        for d in A["keels"]:
            o.append('<path d="%s" fill="none" stroke="%s" stroke-opacity=".45" stroke-width="1.6" stroke-linecap="round"/>' % (d, P["hi"]))
        for kind, d in A["detail"]:
            o.append('<path d="%s" fill="none" stroke="%s" stroke-opacity=".35" stroke-width="1.4" stroke-linecap="round"/>' % (d, P["hi"]))
        for (ex, ey, r) in A["eyes"]:
            o.append('<circle cx="%.1f" cy="%.1f" r="%d" fill="#05080b" stroke="%s" stroke-width="1.2"/><circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s"/>' % (ex, ey, r, P["rim"], ex - r * .3, ey - r * .3, r * .32, P["star"]))
        for (jx, jy) in A["joints"]:
            o.append('<circle cx="%.1f" cy="%.1f" r="3.4" fill="%s" fill-opacity=".9"/>' % (jx, jy, P["star"]))
    ax, ay = A["antares"]
    if flat:
        o.append('<circle cx="%.1f" cy="%.1f" r="30" fill="%s"/>' % (ax, ay, P["red"]))
        o.append('<circle cx="%.1f" cy="%.1f" r="30" fill="none" stroke="%s" stroke-width="10"/>' % (ax, ay, "#0b0f12"))
    else:
        o.append('<circle cx="%.1f" cy="%.1f" r="62" fill="url(#%s-ag)"/><circle cx="%.1f" cy="%.1f" r="20" fill="%s"/><circle cx="%.1f" cy="%.1f" r="7" fill="#ffd9df"/>' % (ax, ay, uid, ax, ay, P["red"], ax, ay))
    body = '<g transform="translate(%.2f %.2f) scale(%.4f)">%s</g>' % (ox, oy, k, "".join(o))
    defs = ('<linearGradient id="%s-fill" x1="0" y1="0" x2="0.15" y2="1"><stop offset="0" stop-color="%s"/><stop offset=".42" stop-color="%s"/><stop offset="1" stop-color="%s"/></linearGradient>'
            '<linearGradient id="%s-far" gradientUnits="userSpaceOnUse" x1="0" y1="80" x2="0" y2="620"><stop offset="0" stop-color="#151e28"/><stop offset="1" stop-color="#06090d"/></linearGradient>'
            '<linearGradient id="%s-edge" gradientUnits="userSpaceOnUse" x1="0" y1="80" x2="0" y2="620"><stop offset="0" stop-color="%s"/><stop offset=".55" stop-color="%s"/><stop offset="1" stop-color="%s" stop-opacity=".5"/></linearGradient>'
            '<linearGradient id="%s-edge2" gradientUnits="userSpaceOnUse" x1="0" y1="80" x2="0" y2="620"><stop offset="0" stop-color="%s" stop-opacity=".5"/><stop offset="1" stop-color="%s" stop-opacity=".2"/></linearGradient>'
            '<linearGradient id="%s-red" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#ff9aa9"/><stop offset=".5" stop-color="%s"/><stop offset="1" stop-color="#b3243f"/></linearGradient>'
            '<radialGradient id="%s-ag"><stop offset="0" stop-color="%s" stop-opacity=".85"/><stop offset="1" stop-color="%s" stop-opacity="0"/></radialGradient>') % (
        uid, P["top"], P["mid"], P["bot"], uid, uid, P["hi"], P["rim"], P["rim2"], uid, P["rim"], P["rim2"], uid, P["red"], uid, P["red"], P["red"])
    return defs, body


if __name__ == "__main__":
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else "."
    for style in ("neon", "flat"):
        d, g = group(style, 640, 30, None, False, "t" + style)
        bg = '<rect width="640" height="640" rx="40" fill="#0b0f12"/>' if style == "neon" else '<rect width="640" height="640" rx="40" fill="#1c242b"/>'
        open("%s/s2-%s.svg" % (out, style), "w", encoding="utf-8", newline=chr(10)).write('<svg xmlns="http://www.w3.org/2000/svg" width="640" height="640" viewBox="0 0 640 640"><defs>%s</defs>%s%s</svg>' % (d, bg, g))
    print("ok")
