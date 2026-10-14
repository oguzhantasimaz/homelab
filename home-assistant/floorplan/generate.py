#!/usr/bin/env python3
"""Generate the floor plan SVGs used by the "Plan" dashboard view.

Coordinates come from the hand sketch (canvas 1335 x 1402). Edit ROOMS / DOORS /
WINDOWS / LAMPS below, run `python3 generate.py`, and copy the output .svg files
to /config/www/floorplan/ on Home Assistant.
"""
W, H = 1335, 1402

# name, x, y, w, h  (None name = room without a light)
ROOMS = [
    (None,     52,   37, 231, 228),
    (None,     55,  277, 234, 227),
    (None,    297,   45, 158, 393),
    ("mutfak", 465,  37, 760, 393),
    (None,    350,  448,  96, 544),
    ("salon",  456,  442, 766, 463),
    (None,     42,  518, 301, 477),
    (None,    441,  913, 417,  75),
    ("yatak",   42,  999, 405, 326),
    (None,    450,  995, 406, 325),
    (None,    864,  908, 368, 414),
]
# (x1, y1, x2, y2): gaps cut in a wall + swing arc
DOORS = [
    (290,  70, 290, 130), (292, 335, 292, 395), (345,  45, 405,  45),
    (460, 295, 460, 365), (450, 495, 450, 565), (346, 710, 346, 780),
    (365, 997, 425, 997), (497, 993, 552, 993), (860, 920, 860, 985),
]
WINDOWS = [
    (1227, 130, 1227, 375), (1223, 535, 1223, 850), (1233, 1070, 1233, 1185),
    (143, 1323, 327, 1323), (598, 1320, 760, 1320), (1005, 1320, 1145, 1320),
]
# light name -> (x, y) of the lamp icon
LAMPS = {"mutfak": (855, 245), "salon": (642, 686), "yatak": (223, 1162)}
LABELS = {"mutfak": (855, 330), "salon": (642, 770), "yatak": (310, 1292)}
TV = (978, 873)
# rooms without a light: label only (dimmer pill)
EXTRA_LABELS = {"depo": (167, 122), "tuvalet": (172, 482), "banyo": (192, 830), "ofis": (1020, 1262), "misafir": (655, 1285)}
FLOOR = {"mutfak": "tile", "salon": "wood", "yatak": "wood"}

BG, ROOM, WALL, WINDOW, DOOR, TEXT = "#12151a", "#1b2027", "#5b6472", "#58b0ff", "#ef6a5b", "#8b95a3"
FURN, FURN_EDGE, FURN_SOFT = "#2c333d", "#3d4653", "#353d49"

DEFS = f"""<defs>
<pattern id="wood" width="60" height="1402" patternUnits="userSpaceOnUse"><rect width="60" height="1402" fill="#1f242b"/><line x1="0" y1="0" x2="0" y2="1402" stroke="#2a3038" stroke-width="2"/></pattern>
<pattern id="tile" width="48" height="48" patternUnits="userSpaceOnUse"><rect width="48" height="48" fill="#1c222a"/><path d="M48 0H0V48" fill="none" stroke="#262d37" stroke-width="2"/></pattern>
<pattern id="dots" width="32" height="32" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1.4" fill="#1d222a"/></pattern>
<filter id="shadow" x="-5%" y="-5%" width="110%" height="110%"><feDropShadow dx="0" dy="6" stdDeviation="9" flood-color="#000" flood-opacity=".55"/></filter>
<filter id="fshadow" x="-10%" y="-10%" width="120%" height="130%"><feDropShadow dx="0" dy="4" stdDeviation="4" flood-color="#000" flood-opacity=".45"/></filter>
<filter id="wglow" filterUnits="userSpaceOnUse" x="0" y="0" width="1335" height="1402"><feGaussianBlur stdDeviation="5" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<linearGradient id="glass" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="1335" y2="1402"><stop offset="0" stop-color="#9fd3ff"/><stop offset="1" stop-color="#3b8fe6"/></linearGradient>
<linearGradient id="vig" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".035"/><stop offset="1" stop-color="#000" stop-opacity=".18"/></linearGradient>
</defs>"""


def svg(body):
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">{body}</svg>\n'


def box(x, y, w, h, fill=FURN, rx=10, stroke=FURN_EDGE, sw=2.5, extra=""):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" {extra}/>'


def circle(cx, cy, r, fill=FURN_SOFT, stroke=FURN_EDGE, sw=2.5):
    return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'


def furniture():
    f = ['<g filter="url(#fshadow)">']
    # --- mutfak: counters, stove, sink, fridge, dining table
    f.append(box(482, 54, 560, 62, rx=8))
    f.append(box(482, 54, 62, 250, rx=8))
    f += [circle(640 + dx, 85 + dy, 11) for dx in (0, 46) for dy in (0, 0)]
    f += [circle(640 + dx, 85, 11) for dx in (92, 138)]
    f.append(box(780, 66, 110, 40, rx=14, fill="#232a33"))  # sink
    f.append(box(1110, 54, 98, 82, rx=8, fill="#38414d"))   # fridge
    f.append(box(1010, 240, 150, 120, rx=18))                # dining table
    f += [circle(1085 + dx, 232 if dy < 0 else 368, 17) for dx in (-45, 45) for dy in (-1, 1)]
    # --- salon: rug, sofa, coffee table, tv unit, armchair, plant
    f.append(box(790, 600, 380, 250, rx=26, fill="#242b35", stroke="#2f3744", extra='filter="none"'))
    f.append(box(820, 612, 320, 92, rx=24, fill="#3a4658"))     # sofa
    f.append(box(820, 612, 320, 30, rx=14, fill="#445168", sw=0))
    f.append(box(808, 622, 34, 72, rx=14, fill="#445168"))
    f.append(box(1120, 622, 34, 72, rx=14, fill="#445168"))
    f.append(box(890, 740, 180, 62, rx=16, fill="#323b47"))     # coffee table
    f.append(box(878, 880, 200, 20, rx=6, fill="#38414d"))      # tv unit
    f.append(box(488, 490, 92, 92, rx=24, fill="#3a4658"))      # armchair
    f.append(circle(1170, 500, 30, fill="#26402f", stroke="#2f5a3d"))
    f.append(circle(1170, 500, 14, fill="#2f6b44", stroke="none", sw=0))
    # --- yatak: bed, nightstands, wardrobe
    f.append(box(60, 1058, 150, 206, rx=14, fill="#3a4658"))
    f.append(box(60, 1058, 150, 52, rx=14, fill="#4a586e"))
    f.append(box(72, 1068, 58, 34, rx=12, fill="#e9eef5", stroke="none", sw=0, extra='opacity=".85"'))
    f.append(box(140, 1068, 58, 34, rx=12, fill="#e9eef5", stroke="none", sw=0, extra='opacity=".85"'))
    f.append(box(60, 1016, 50, 36, rx=8))
    f.append(box(60, 1270, 50, 36, rx=8))
    f.append(box(398, 1060, 38, 230, rx=8, fill="#38414d"))
    # --- depo: shelves and boxes
    f.append(box(66, 52, 206, 32, rx=6))
    f.append(box(66, 84, 30, 168, rx=6))
    f += [box(150, 168, 70, 52, rx=6, fill="#3a4658"), box(196, 214, 52, 40, rx=6, fill="#445168"), box(112, 210, 42, 42, rx=6, fill="#3a4658")]
    # --- alaturka tuvalet: squat pan, small sink
    f.append(box(112, 340, 76, 104, rx=16))
    f.append(f'<ellipse cx="150" cy="410" rx="15" ry="28" fill="#14181d" stroke="{FURN_EDGE}" stroke-width="2.5"/>')
    f += [box(122, 356, 24, 38, rx=6, fill="#3a4658"), box(154, 356, 24, 38, rx=6, fill="#3a4658")]
    f.append(box(70, 292, 62, 44, rx=12))
    f.append(circle(101, 314, 12, fill="#14181d"))
    # --- banyo: shower cabin, toilet, sink, washing machine
    f.append(box(62, 538, 134, 134, rx=10, fill="#1f3a4d", stroke="#2d5a78"))
    f.append(circle(80, 556, 10, fill="#58b0ff", stroke="none", sw=0))
    f.append(circle(150, 620, 11, fill="#14181d"))
    f.append(box(262, 540, 62, 26, rx=8))
    f.append(f'<ellipse cx="293" cy="596" rx="26" ry="34" fill="{FURN}" stroke="{FURN_EDGE}" stroke-width="2.5"/>')
    f.append(box(60, 724, 56, 80, rx=10))
    f.append(circle(88, 764, 18, fill="#14181d"))
    f.append(box(62, 880, 86, 86, rx=10))
    f.append(circle(105, 923, 28, fill="#14181d"))
    f.append(circle(105, 923, 18, fill="#27313c", stroke="#3d4653"))
    # --- ofis: desk, monitors, chair, shelf, plant
    f.append(box(1126, 1022, 92, 214, rx=8))
    f += [box(1138, 1052, 14, 64, rx=4, fill="#0f1318"), box(1138, 1140, 14, 64, rx=4, fill="#0f1318")]
    f.append(circle(1066, 1128, 32, fill="#3a4658"))
    f.append(box(878, 1004, 30, 250, rx=6, fill="#38414d"))
    f.append(circle(1190, 958, 26, fill="#26402f", stroke="#2f5a3d"))
    f.append(circle(1190, 958, 12, fill="#2f6b44", stroke="none", sw=0))
    # --- misafir odasi: bed + desk
    f.append(box(688, 1012, 148, 204, rx=14, fill="#3a4658"))
    f.append(box(688, 1012, 148, 52, rx=14, fill="#4a586e"))
    f.append(box(698, 1022, 60, 34, rx=12, fill="#e9eef5", stroke="none", sw=0, extra='opacity=".85"'))
    f.append(box(766, 1022, 60, 34, rx=12, fill="#e9eef5", stroke="none", sw=0, extra='opacity=".85"'))
    f.append(box(468, 1110, 72, 150, rx=8))
    f.append(circle(578, 1185, 28, fill="#3a4658"))
    f.append(box(474, 1130, 14, 54, rx=4, fill="#0f1318"))
    f.append('</g>')
    return "".join(f)


def swing(x1, y1, x2, y2):
    r = max(abs(x2 - x1), abs(y2 - y1))
    if x1 == x2:
        d = f"M{x1} {y1} h{r} A{r} {r} 0 0 1 {x1} {y1 + r}"
    else:
        d = f"M{x1} {y1} v{r} A{r} {r} 0 0 0 {x1 + r} {y1}"
    return f'<path d="{d}" fill="none" stroke="{DOOR}" stroke-width="2.5" stroke-dasharray="5 6" opacity=".55"/>'


def base():
    out = [DEFS, f'<rect width="{W}" height="{H}" rx="28" fill="{BG}"/><rect width="{W}" height="{H}" rx="28" fill="url(#dots)"/>']
    out.append('<g filter="url(#shadow)">')
    for name, x, y, w, h in ROOMS:
        out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="16" fill="{ROOM}" stroke="{WALL}" stroke-width="7"/>')
    out.append("</g>")
    for name, x, y, w, h in ROOMS:
        fill = f"url(#{FLOOR[name]})" if name in FLOOR else ROOM
        out.append(f'<rect x="{x + 3}" y="{y + 3}" width="{w - 6}" height="{h - 6}" rx="13" fill="{fill}"/>')
        out.append(f'<rect x="{x + 3}" y="{y + 3}" width="{w - 6}" height="{h - 6}" rx="13" fill="url(#vig)"/>')
    out.append(furniture())
    for x1, y1, x2, y2 in DOORS:
        out.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{ROOM}" stroke-width="13"/>')
        out.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{DOOR}" stroke-width="4" stroke-linecap="round"/>')
        out.append(swing(x1, y1, x2, y2))
    for x1, y1, x2, y2 in WINDOWS:
        out.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="url(#glass)" stroke-width="9" stroke-linecap="round" filter="url(#wglow)"/>')
    for labels, dim in ((LABELS, False), (EXTRA_LABELS, True)):
        for name, (x, y) in labels.items():
            t = {"tuvalet": "TUVALET", "misafir": "MİSAFİR", "ofis": "OFİS"}.get(name, name.upper())
            size = 20 if dim else 22
            wpx = len(t) * (size + 0) + 34
            out.append(f'<rect x="{x - wpx / 2}" y="{y - 24}" width="{wpx}" height="38" rx="19" fill="#0e1115" fill-opacity="{.4 if dim else .55}" stroke="#2d3540" stroke-width="2"/>')
            out.append(f'<text x="{x}" y="{y + 2}" text-anchor="middle" font-family="Inter,Segoe UI,Roboto,sans-serif" font-weight="600" font-size="{size}" letter-spacing="3" fill="{"#6f7987" if dim else TEXT}">{t}</text>')
    return svg("".join(out))


def glow(name):
    _, x, y, w, h = next(r for r in ROOMS if r[0] == name)
    cx, cy = LAMPS[name]
    r = max(w, h) * 0.8
    return svg(
        f'<defs><radialGradient id="g" gradientUnits="userSpaceOnUse" cx="{cx}" cy="{cy}" r="{r}">'
        f'<stop offset="0" stop-color="#ffe29a" stop-opacity=".62"/><stop offset=".35" stop-color="#ffc857" stop-opacity=".30"/>'
        f'<stop offset="1" stop-color="#ff9f1c" stop-opacity=".07"/></radialGradient></defs>'
        f'<rect x="{x + 3}" y="{y + 3}" width="{w - 6}" height="{h - 6}" rx="13" fill="url(#g)" style="mix-blend-mode:screen"/>'
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="16" fill="none" stroke="#ffd37a" stroke-opacity=".55" stroke-width="5"/>'
    )


files = {"plan.svg": base(), "off.svg": svg("")}
files.update({f"{n}-on.svg": glow(n) for n in LAMPS})
for fn, content in files.items():
    open(fn, "w", encoding="utf-8").write(content)
print("wrote", ", ".join(files))
