#!/usr/bin/env python3
"""Generate the floor plan SVGs used by the "Plan" dashboard view.

Coordinates come from the hand sketch (canvas 1267 x 1362). Edit ROOMS / DOORS /
WINDOWS / LAMPS below, run `python3 generate.py`, and copy the output .svg files
to /config/www/floorplan/ on Home Assistant.
"""
W, H = 1267, 1362

# name, x, y, w, h. Rooms share walls; the hallway (HALL) is one connected L-shaped polygon.
ROOMS = [
    ("depo",     42,   37, 301, 233),
    ("tuvalet",  42,  270, 301, 235),
    ("banyo",    42,  505, 301, 490),
    ("mutfak",  455,   37, 770, 398),
    ("salon",   455,  435, 770, 470),
    ("yatak",    42,  995, 413, 330),
    ("misafir", 455,  995, 409, 330),
    ("ofis",    864,  905, 361, 420),
]
HALL = [(343, 37), (455, 37), (455, 905), (864, 905), (864, 995), (343, 995)]
# (x1, y1, x2, y2): gaps cut in a wall + swing arc
DOORS = [
    (372,  37, 432,  37),                                  # front door (top of the hallway)
    (343,  90, 343, 150), (343, 350, 343, 410), (343, 690, 343, 760),   # depo, tuvalet, banyo
    (455, 270, 455, 340), (455, 520, 455, 590),            # mutfak, salon
    (385, 995, 445, 995), (497, 995, 552, 995),            # yatak, misafir
    (864, 920, 864, 985),                                  # ofis
]
WINDOWS = [
    (1225, 130, 1225, 375), (1225, 535, 1225, 850), (1225, 1070, 1225, 1185),
    (143, 1325, 327, 1325), (598, 1325, 760, 1325), (1005, 1325, 1145, 1325),
]
# light name -> (x, y) of the lamp icon
LAMPS = {"mutfak": (855, 245), "salon": (642, 686), "yatak": (335, 1162)}
LABELS = {"mutfak": (855, 330), "salon": (642, 770), "yatak": (250, 1294)}
TV = (978, 873)
# rooms without a light: label only (dimmer pill)
EXTRA_LABELS = {"depo": (192, 125), "tuvalet": (192, 482), "banyo": (192, 830), "ofis": (1020, 1262), "misafir": (655, 1040)}
FLOOR = {"mutfak": "tile", "salon": "wood", "yatak": "wood", "misafir": "wood", "ofis": "wood", "tuvalet": "tile", "banyo": "tile"}

BG, ROOM, WALL, WINDOW, DOOR, TEXT = "#12151a", "#1b2027", "#5b6472", "#58b0ff", "#ef6a5b", "#8b95a3"
FURN, FURN_EDGE, FURN_SOFT = "#2c333d", "#3d4653", "#353d49"

DEFS = f"""<defs>
<pattern id="wood" width="60" height="1362" patternUnits="userSpaceOnUse"><rect width="60" height="1362" fill="#1f242b"/><line x1="0" y1="0" x2="0" y2="1402" stroke="#2a3038" stroke-width="2"/></pattern>
<pattern id="tile" width="48" height="48" patternUnits="userSpaceOnUse"><rect width="48" height="48" fill="#1c222a"/><path d="M48 0H0V48" fill="none" stroke="#262d37" stroke-width="2"/></pattern>
<pattern id="hall" width="90" height="90" patternUnits="userSpaceOnUse"><rect width="90" height="90" fill="#1e232a"/><path d="M90 0H0V90" fill="none" stroke="#272d36" stroke-width="2"/></pattern>
<pattern id="dots" width="32" height="32" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1.4" fill="#1d222a"/></pattern>
<filter id="shadow" x="-5%" y="-5%" width="110%" height="110%"><feDropShadow dx="0" dy="6" stdDeviation="9" flood-color="#000" flood-opacity=".55"/></filter>
<filter id="fshadow" x="-10%" y="-10%" width="120%" height="130%"><feDropShadow dx="0" dy="4" stdDeviation="4" flood-color="#000" flood-opacity=".45"/></filter>
<filter id="wglow" filterUnits="userSpaceOnUse" x="0" y="0" width="1267" height="1362"><feGaussianBlur stdDeviation="5" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<linearGradient id="glass" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="1267" y2="1362"><stop offset="0" stop-color="#9fd3ff"/><stop offset="1" stop-color="#3b8fe6"/></linearGradient>
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
    # --- salon: rug, sofa along the top wall, tall sofa by the window, coffee table, tv unit, 2 bookshelves, armchair, plant
    f.append(box(790, 572, 330, 270, rx=26, fill="#242b35", stroke="#2f3744", extra='filter="none"'))
    f.append(box(800, 462, 300, 92, rx=24, fill="#3a4658"))     # sofa (top wall, faces the TV)
    f.append(box(800, 462, 300, 30, rx=14, fill="#445168", sw=0))
    f.append(box(788, 472, 34, 72, rx=14, fill="#445168"))
    f.append(box(1078, 472, 34, 72, rx=14, fill="#445168"))
    f.append(box(1146, 590, 66, 230, rx=24, fill="#3a4658"))    # tall sofa by the window
    f.append(box(1182, 590, 30, 230, rx=14, fill="#445168", sw=0))
    f.append(box(880, 690, 170, 62, rx=16, fill="#323b47"))     # coffee table
    f.append(box(878, 880, 200, 20, rx=6, fill="#38414d"))      # tv unit
    f.append(box(470, 736, 32, 80, rx=5, fill="#38414d"))       # bookshelf 1 (against the left wall)
    f.append(box(470, 822, 32, 80, rx=5, fill="#38414d"))       # bookshelf 2
    f += [f'<line x1="474" y1="{y}" x2="498" y2="{y}" stroke="#4b5563" stroke-width="2"/>' for y in (756, 776, 796, 842, 862, 882)]
    f.append(box(488, 630, 80, 80, rx=24, fill="#3a4658"))      # armchair
    f.append(circle(1170, 500, 30, fill="#26402f", stroke="#2f5a3d"))
    f.append(circle(1170, 500, 14, fill="#2f6b44", stroke="none", sw=0))
    # --- yatak: horizontal bed (headboard on the left wall), nightstands, wardrobe
    f.append(box(60, 1090, 206, 144, rx=14, fill="#3a4658"))
    f.append(box(60, 1090, 46, 144, rx=14, fill="#4a586e"))
    f.append(box(76, 1100, 34, 56, rx=12, fill="#e9eef5", stroke="none", sw=0, extra='opacity=".85"'))
    f.append(box(76, 1168, 34, 56, rx=12, fill="#e9eef5", stroke="none", sw=0, extra='opacity=".85"'))
    f.append(box(60, 1044, 46, 36, rx=8))
    f.append(box(60, 1244, 46, 36, rx=8))
    f.append(box(398, 1060, 38, 230, rx=8, fill="#38414d"))
    # --- depo: shelves and boxes
    f.append(box(58, 52, 270, 32, rx=6))
    f.append(box(58, 84, 30, 170, rx=6))
    f += [box(190, 172, 74, 52, rx=6, fill="#3a4658"), box(244, 218, 52, 40, rx=6, fill="#445168"), box(146, 214, 42, 42, rx=6, fill="#3a4658")]
    # --- alaturka tuvalet: squat pan, small sink
    f.append(box(154, 340, 76, 104, rx=16))
    f.append(f'<ellipse cx="192" cy="410" rx="15" ry="28" fill="#14181d" stroke="{FURN_EDGE}" stroke-width="2.5"/>')
    f += [box(164, 356, 24, 38, rx=6, fill="#3a4658"), box(196, 356, 24, 38, rx=6, fill="#3a4658")]
    f.append(box(62, 286, 62, 44, rx=12))
    f.append(circle(93, 308, 12, fill="#14181d"))
    # --- banyo: shower cabin, toilet, sink, washing machine
    f.append(box(62, 538, 134, 134, rx=10, fill="#1f3a4d", stroke="#2d5a78"))
    f.append(circle(80, 556, 10, fill="#58b0ff", stroke="none", sw=0))
    f.append(circle(150, 620, 11, fill="#14181d"))
    f.append(box(262, 540, 64, 54, rx=10))                      # sink (top right)
    f.append(circle(294, 568, 16, fill="#14181d"))
    f.append(box(58, 730, 30, 54, rx=8))                        # toilet tank (middle of left wall)
    f.append(f'<ellipse cx="116" cy="757" rx="34" ry="28" fill="{FURN}" stroke="{FURN_EDGE}" stroke-width="2.5"/>')
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
    f.append(box(740, 1094, 100, 212, rx=14, fill="#3a4658"))   # single bed, head in the bottom-right corner
    f.append(box(740, 1258, 100, 48, rx=14, fill="#4a586e"))
    f.append(box(756, 1266, 68, 32, rx=12, fill="#e9eef5", stroke="none", sw=0, extra='opacity=".85"'))
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
    pts = " ".join(f"{x},{y}" for x, y in HALL)
    out.append('<g filter="url(#shadow)" stroke-linejoin="round">')
    for name, x, y, w, h in ROOMS:
        out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{ROOM}" stroke="{WALL}" stroke-width="7"/>')
    out.append(f'<polygon points="{pts}" fill="{ROOM}" stroke="{WALL}" stroke-width="7"/>')
    out.append("</g>")
    for name, x, y, w, h in ROOMS:
        fill = f"url(#{FLOOR[name]})" if name in FLOOR else ROOM
        out.append(f'<rect x="{x + 3}" y="{y + 3}" width="{w - 6}" height="{h - 6}" fill="{fill}"/>')
        out.append(f'<rect x="{x + 3}" y="{y + 3}" width="{w - 6}" height="{h - 6}" fill="url(#vig)"/>')
    out.append(f'<polygon points="{pts}" fill="url(#hall)" stroke="none"/>')
    out.append(f'<polygon points="{pts}" fill="url(#vig)" stroke="none"/>')
    out.append(f'<polygon points="{pts}" fill="none" stroke="{WALL}" stroke-width="7" stroke-linejoin="round"/>')
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
        f'<rect x="{x + 3}" y="{y + 3}" width="{w - 6}" height="{h - 6}" rx="2" fill="url(#g)" style="mix-blend-mode:screen"/>'
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="2" fill="none" stroke="#ffd37a" stroke-opacity=".55" stroke-width="5"/>'
    )


files = {"plan.svg": base(), "off.svg": svg("")}
files.update({f"{n}-on.svg": glow(n) for n in LAMPS})
for fn, content in files.items():
    open(fn, "w", encoding="utf-8").write(content)
print("wrote", ", ".join(files))
