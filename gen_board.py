# gen_board.py - regenerate board.svg from board_data.json.
# Source: Duke (original work, 2026-11-04). Dependency-free;
# run by hand or by the board workflow on every data change.
import json, os
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__))
NAVY = "#102331"; TEAL = "#0097A7"; GREEN = "#76FF03"
BG = "#F4F7F8"; INK = "#1C2B33"; MUTED = "#5A6B73"; WHITE = "#FFFFFF"

def bar(x, y, w, pct, color):
    fill = int(w * max(0, min(100, pct)) / 100.0)
    return ('<rect x="%d" y="%d" width="%d" height="10" rx="5" fill="#D8E2E6"/>'
            '<rect x="%d" y="%d" width="%d" height="10" rx="5" fill="%s"/>'
            % (x, y, w, x, y, fill, color))

def main():
    d = json.load(open(os.path.join(HERE, "board_data.json")))
    W = 880; pad = 28; rows = []
    rows.append('<rect width="%d" height="96" fill="%s"/>' % (W, NAVY))
    rows.append('<text x="%d" y="42" font-family="Arial, sans-serif" font-size="30" font-weight="bold" fill="%s">%s</text>' % (pad, WHITE, escape(d["org"])))
    rows.append('<text x="%d" y="72" font-family="Arial, sans-serif" font-size="15" fill="#9FD8DE">%s</text>' % (pad, escape(d["tagline"])))
    rows.append('<rect x="%d" y="26" width="252" height="44" rx="8" fill="%s"/>' % (W - pad - 252, GREEN))
    rows.append('<text x="%d" y="54" font-family="Arial, sans-serif" font-size="15" font-weight="bold" fill="%s" text-anchor="middle">Mission: %s</text>' % (W - pad - 126, NAVY, escape(d["mission"])))
    y = 96
    rows.append('<rect y="%d" width="%d" height="86" fill="%s"/>' % (y, W, BG))
    rows.append('<text x="%d" y="%d" font-family="Arial, sans-serif" font-size="13" fill="%s">INDEPENDENCE</text>' % (pad, y + 26, MUTED))
    rows.append('<text x="%d" y="%d" font-family="Arial, sans-serif" font-size="26" font-weight="bold" fill="%s">%d%%</text>' % (pad, y + 58, NAVY, d["independence_pct"]))
    rows.append(bar(pad + 110, y + 46, 190, d["independence_pct"], TEAL))
    rows.append('<text x="360" y="%d" font-family="Arial, sans-serif" font-size="13" fill="%s">CURRENT STEP</text>' % (y + 26, MUTED))
    rows.append('<text x="360" y="%d" font-family="Arial, sans-serif" font-size="20" font-weight="bold" fill="%s">%s - %s</text>' % (y + 58, NAVY, escape(d["step"]), escape(d["step_name"])))
    rows.append('<text x="640" y="%d" font-family="Arial, sans-serif" font-size="13" fill="%s">WEBSITE</text>' % (y + 26, MUTED))
    rows.append('<text x="640" y="%d" font-family="Arial, sans-serif" font-size="20" font-weight="bold" fill="%s">%s</text>' % (y + 58, TEAL, escape(d["website"])))
    y += 86
    for ln in d["lines"]:
        rows.append('<rect y="%d" width="%d" height="86" fill="%s"/>' % (y, W, WHITE))
        rows.append('<rect y="%d" width="%d" height="1" fill="#D8E2E6"/>' % (y, W))
        rows.append('<text x="%d" y="%d" font-family="Arial, sans-serif" font-size="19" font-weight="bold" fill="%s">%s</text>' % (pad, y + 32, NAVY, escape(ln["name"])))
        rows.append('<text x="%d" y="%d" font-family="Arial, sans-serif" font-size="13" fill="%s">%s</text>' % (pad, y + 56, MUTED, escape(ln["blurb"])))
        rows.append('<text x="%d" y="%d" font-family="Arial, sans-serif" font-size="14" font-weight="bold" fill="%s" text-anchor="end">%s</text>' % (W - pad, y + 34, TEAL, escape(ln["status"])))
        if ln.get("pct") is not None:
            rows.append(bar(W - pad - 190, y + 48, 190, ln["pct"], GREEN))
        y += 86
    rows.append('<rect y="%d" width="%d" height="30" fill="%s"/>' % (y, W, NAVY))
    rows.append('<text x="%d" y="%d" font-family="Arial, sans-serif" font-size="11" fill="#9FD8DE">Public board - basic information only. This panel regenerates automatically from board_data.json.</text>' % (pad, y + 19))
    y += 30
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">'
           '<rect width="%d" height="%d" fill="%s"/>%s</svg>'
           % (W, y, W, y, W, y, WHITE, "".join(rows)))
    with open(os.path.join(HERE, "board.svg"), "w", encoding="utf-8") as fh:
        fh.write(svg + "\n")
    print("board.svg written, height", y)

if __name__ == "__main__":
    main()
