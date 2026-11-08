# gen_board.py - regenerate board.svg from board_data.json.
# Source: Duke (original work, 2026-11-04; layout reworked 2026-11-08).
# Dependency-free; run by hand or by the board workflow on every
# data change.
# 2026-11-08 rework: the old layout let the CURRENT STEP value run
# into the WEBSITE column and let row blurbs crowd the right-hand
# status text. Every string now passes through fit(), which trims
# it to its own slot's pixel budget before it is drawn, and the
# step name / step detail sit on separate lines. Palette updated
# to the DirectDesk colors: navy #102331, teal #0197A6, bright
# green #00FF00, light #E8E8E8.
import json, os
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__))
NAVY = "#102331"; TEAL = "#0197A6"; GREEN = "#00FF00"
BG = "#E8E8E8"; INK = "#1C2B33"; MUTED = "#5A6B73"; WHITE = "#FFFFFF"
TINT = "#BFE6EA"; TRACK = "#C9D6DA"; HAIR = "#D8E2E6"

# Conservative Arial advance widths, as fractions of the font size.
# Estimated wide on purpose: a string that fits this estimate fits
# the real font with room to spare.
_WIDE = {"%": 0.889, "@": 0.975, "W": 0.944, "M": 0.833, "m": 0.833,
         "w": 0.722, "&": 0.667, "Q": 0.777, "G": 0.777, "O": 0.777}
_NARROW = {" ": 0.278, ".": 0.278, ",": 0.278, ":": 0.278, ";": 0.278,
           "/": 0.278, "!": 0.278, "'": 0.191, "-": 0.333, "(": 0.333,
           ")": 0.333, "i": 0.278, "l": 0.278, "j": 0.278, "I": 0.278,
           "t": 0.333, "f": 0.333, "r": 0.333, "$": 0.556, "+": 0.584,
           "?": 0.556, "#": 0.556, "·": 0.278, "…": 0.778}

def est_width(text, size, bold):
    total = 0.0
    for ch in text:
        if ch in _WIDE:
            total += _WIDE[ch]
        elif ch in _NARROW:
            total += _NARROW[ch]
        elif ch.isupper():
            total += 0.68
        elif ch.isdigit():
            total += 0.556
        else:
            total += 0.52
    w = total * size
    return w * 1.09 if bold else w * 1.05

def fit(text, size, bold, budget):
    if est_width(text, size, bold) <= budget:
        return text
    t = text
    while t and est_width(t + "…", size, bold) > budget:
        t = t[:-1]
    return t.rstrip() + "…"

def bar(x, y, w, pct, color):
    fill = int(w * max(0, min(100, pct)) / 100.0)
    return ('<rect x="%d" y="%d" width="%d" height="10" rx="5" fill="%s"/>'
            '<rect x="%d" y="%d" width="%d" height="10" rx="5" fill="%s"/>'
            % (x, y, w, TRACK, x, y, fill, color))

def text(x, y, size, fill, txt, bold=False, anchor=None, budget=None):
    if budget is not None:
        txt = fit(txt, size, bold, budget)
    attrs = ' font-weight="bold"' if bold else ""
    if anchor:
        attrs += ' text-anchor="%s"' % anchor
    return ('<text x="%d" y="%d" font-family="Arial, sans-serif" '
            'font-size="%d"%s fill="%s">%s</text>'
            % (x, y, size, attrs, fill, escape(txt)))

def main():
    d = json.load(open(os.path.join(HERE, "board_data.json")))
    W = 880; pad = 28; rows = []
    # Header band: name, tagline, goal pill.
    rows.append('<rect width="%d" height="96" fill="%s"/>' % (W, NAVY))
    rows.append(text(pad, 42, 30, WHITE, d["org"], bold=True, budget=520))
    rows.append(text(pad, 72, 15, TINT, d["tagline"], budget=520))
    goal = "Goal: %s" % d["goal"]
    pill_w = max(252, int(est_width(goal, 15, True)) + 40)
    rows.append('<rect x="%d" y="26" width="%d" height="44" rx="8" fill="%s"/>' % (W - pad - pill_w, pill_w, GREEN))
    rows.append(text(W - pad - pill_w // 2, 54, 15, NAVY, goal, bold=True, anchor="middle", budget=pill_w - 16))
    # Stats band: three columns, each string in its own slot.
    y = 96
    rows.append('<rect y="%d" width="%d" height="92" fill="%s"/>' % (y, W, BG))
    rows.append(text(pad, y + 26, 13, MUTED, "INDEPENDENCE", budget=240))
    rows.append(text(pad, y + 60, 26, TEAL, "%d%%" % d["independence_pct"], bold=True, budget=90))
    rows.append(bar(pad + 92, y + 50, 150, d["independence_pct"], TEAL))
    rows.append(text(320, y + 26, 13, MUTED, "CURRENT STEP", budget=296))
    rows.append(text(320, y + 54, 19, NAVY, d["step"], bold=True, budget=296))
    rows.append(text(320, y + 78, 13, TEAL, d["step_name"], bold=True, budget=296))
    rows.append(text(640, y + 26, 13, MUTED, "WEBSITE", budget=212))
    rows.append(text(640, y + 54, 20, TEAL, d["website"], bold=True, budget=212))
    y += 92
    # One row per line of work: name + status share a line, the
    # blurb gets its own line underneath, the bar sits right.
    for ln in d["lines"]:
        status = ln["status"]
        sw = min(est_width(status, 14, True), 360)
        rows.append('<rect y="%d" width="%d" height="86" fill="%s"/>' % (y, W, WHITE))
        rows.append('<rect y="%d" width="%d" height="1" fill="%s"/>' % (y, W, HAIR))
        rows.append(text(pad, y + 34, 19, NAVY, ln["name"], bold=True,
                         budget=W - pad - sw - 20 - pad))
        rows.append(text(W - pad, y + 34, 14, TEAL, status, bold=True,
                         anchor="end", budget=360))
        blurb_budget = (662 - 16 - pad) if ln.get("pct") is not None else (W - pad - pad)
        rows.append(text(pad, y + 62, 13, MUTED, ln["blurb"], budget=blurb_budget))
        if ln.get("pct") is not None:
            rows.append(bar(W - pad - 190, y + 52, 190, ln["pct"], GREEN))
        y += 86
    # Crew band: every person's name in their own color (the
    # Persona_Windows PERSONAS table) on navy, role underneath.
    crew = d.get("crew") or []
    if crew:
        rows.append('<rect y="%d" width="%d" height="76" fill="%s"/>' % (y, W, NAVY))
        rows.append(text(pad, y + 20, 11, TINT, "THE CREW", bold=True, budget=200))
        n = len(crew)
        for i, p in enumerate(crew):
            cx = pad + int((W - 2 * pad) * (i + 0.5) / n)
            rows.append(text(cx, y + 48, 16, p["color"], p["name"],
                             bold=True, anchor="middle", budget=124))
            rows.append(text(cx, y + 68, 11, "#E8E8E8", p["role"],
                             anchor="middle", budget=124))
        y += 76
    rows.append('<rect y="%d" width="%d" height="30" fill="%s"/>' % (y, W, NAVY))
    rows.append(text(pad, y + 19, 11, TINT,
                     "Public board - basic information only. It rebuilds itself from board_data.json.",
                     budget=W - 2 * pad))
    y += 30
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">'
           '<rect width="%d" height="%d" fill="%s"/>%s</svg>'
           % (W, y, W, y, W, y, WHITE, "".join(rows)))
    with open(os.path.join(HERE, "board.svg"), "w", encoding="utf-8") as fh:
        fh.write(svg + "\n")
    print("board.svg written, height", y)

if __name__ == "__main__":
    main()
