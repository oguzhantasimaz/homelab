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
# light name -> (x, y) of the lamp icon; also used for the room label
LAMPS = {"mutfak": (855, 245), "salon": (642, 686), "yatak": (223, 1162)}
TV = (978, 873)

BG, ROOM, WALL, WINDOW, DOOR, TEXT = "#14171c", "#1d2128", "#444b55", "#4aa3ff", "#e5534b", "#7d8794"


def svg(body):
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">{body}</svg>\n'


def swing(x1, y1, x2, y2):
    """Quarter-circle door swing hinged at (x1, y1)."""
    r = max(abs(x2 - x1), abs(y2 - y1))
    if x1 == x2:  # vertical wall, door swings right
        return f'<path d="M{x1} {y1} h{r} A{r} {r} 0 0 1 {x1} {y1 + r}" fill="none" stroke="{DOOR}" stroke-width="3" stroke-dasharray="6 5" opacity=".7"/>'
    return f'<path d="M{x1} {y1} v{r} A{r} {r} 0 0 0 {x1 + r} {y1}" fill="none" stroke="{DOOR}" stroke-width="3" stroke-dasharray="6 5" opacity=".7"/>'


def base():
    out = [f'<rect width="{W}" height="{H}" rx="28" fill="{BG}"/>']
    for _, x, y, w, h in ROOMS:
        out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="16" fill="{ROOM}" stroke="{WALL}" stroke-width="6"/>')
    for x1, y1, x2, y2 in DOORS:
        out.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{ROOM}" stroke-width="12" stroke-linecap="butt"/>')
        out.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{DOOR}" stroke-width="4"/>')
        out.append(swing(x1, y1, x2, y2))
    for x1, y1, x2, y2 in WINDOWS:
        out.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{WINDOW}" stroke-width="8" stroke-linecap="round"/>')
    for name, (x, y) in LAMPS.items():
        out.append(f'<text x="{x}" y="{y + 78}" text-anchor="middle" font-family="sans-serif" font-size="30" letter-spacing="4" fill="{TEXT}">{name.upper()}</text>')
    tx, ty = TV
    out.append(f'<rect x="{tx - 90}" y="{ty + 18}" width="180" height="10" rx="5" fill="{WALL}"/>')
    return svg("".join(out))


def glow(name):
    _, x, y, w, h = next(r for r in ROOMS if r[0] == name)
    cx, cy = LAMPS[name]
    return svg(
        f'<defs><radialGradient id="g" gradientUnits="userSpaceOnUse" cx="{cx}" cy="{cy}" r="{max(w, h) * 0.75}">'
        f'<stop offset="0" stop-color="#ffd166" stop-opacity=".55"/><stop offset="1" stop-color="#ffd166" stop-opacity=".12"/>'
        f'</radialGradient></defs><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="16" fill="url(#g)"/>'
    )


files = {"plan.svg": base(), "off.svg": svg("")}
files.update({f"{n}-on.svg": glow(n) for n in LAMPS})
for fn, content in files.items():
    open(fn, "w", encoding="utf-8").write(content)
print("wrote", ", ".join(files))
