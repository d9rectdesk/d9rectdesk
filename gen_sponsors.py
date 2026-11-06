# gen_sponsors.py - regenerate sponsors.svg, the backer grid,
# from GitHub Sponsors data. Source: Duke (original work,
# 2026-11-04), following the sponsors-svg pattern: a scheduled
# workflow renders sponsor avatars grouped by tier into one
# committed SVG that the profile README embeds.
#
# Data road: the GraphQL sponsorshipsAsMaintainer connection.
# It answers only to a token belonging to the sponsored account
# itself, so the workflow passes SPONSORS_TOKEN (a personal
# access token stored as a repository secret). The workflow's
# built-in GITHUB_TOKEN cannot read it - that is a GitHub limit,
# not a bug here.
#
# Honesty rules: only PUBLIC sponsorships are rendered; nobody
# is ever invented. With no token, or before the first sponsor,
# the grid is the correct zero state. If a token is present but
# the fetch fails, the script exits nonzero and leaves the
# existing grid untouched rather than clobbering it with an
# empty one.
import base64, json, os, sys, urllib.request, urllib.error
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "sponsors.svg")
LOGIN = "directdesk-cmd"
NAVY = "#102331"; TEAL = "#0097A7"; GREEN = "#76FF03"
BG = "#F4F7F8"; INK = "#1C2B33"; MUTED = "#5A6B73"; WHITE = "#FFFFFF"
TIERS = [(1000, "Corporate - $1,000/month"), (250, "Silver Org - $250/month"),
         (25, "Supporter - $25/month"), (5, "Individual - $5/month"),
         (1, "Backers"), (0, "One-time supporters")]

def tier_of(price, one_time):
    if one_time:
        return "One-time supporters"
    for floor, name in TIERS:
        if price >= floor:
            return name
    return "Backers"

def fetch_sponsors(token):
    query = """
    query($login: String!, $after: String) {
      user(login: $login) {
        sponsorshipsAsMaintainer(first: 100, includePrivate: false, after: $after) {
          pageInfo { hasNextPage endCursor }
          nodes {
            privacyLevel
            isOneTimePayment
            tier { monthlyPriceInDollars }
            sponsorEntity {
              ... on User { login avatarUrl }
              ... on Organization { login avatarUrl }
            }
          }
        }
      }
    }"""
    best = {}
    after = None
    while True:
        body = json.dumps({"query": query,
                           "variables": {"login": LOGIN, "after": after}}).encode()
        req = urllib.request.Request("https://api.github.com/graphql",
                                     data=body, method="POST")
        req.add_header("Authorization", "bearer " + token)
        req.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(req) as fh:
            data = json.load(fh)
        conn = data["data"]["user"]["sponsorshipsAsMaintainer"]
        for node in conn["nodes"]:
            if node.get("privacyLevel") != "PUBLIC":
                continue
            ent = node.get("sponsorEntity") or {}
            login = ent.get("login")
            if not login:
                continue
            price = (node.get("tier") or {}).get("monthlyPriceInDollars") or 0
            one = bool(node.get("isOneTimePayment"))
            key = login.lower()
            cur = best.get(key)
            if cur is None or (price, not one) > (cur[1], not cur[2]):
                best[key] = (login, price, one, ent.get("avatarUrl") or "")
        if conn["pageInfo"]["hasNextPage"]:
            after = conn["pageInfo"]["endCursor"]
        else:
            return list(best.values())

def avatar_tile(x, y, size, login, avatar_url):
    parts = ['<a href="https://github.com/%s"><title>%s</title>'
             % (escape(login), escape(login))]
    img = None
    if avatar_url:
        try:
            req = urllib.request.Request(avatar_url + "&s=96")
            req.add_header("User-Agent", "duke-sponsors-grid")
            with urllib.request.urlopen(req, timeout=15) as fh:
                img = base64.b64encode(fh.read()).decode()
        except Exception:
            img = None
    cid = "c" + "".join(ch if ch.isalnum() else "_" for ch in login)
    parts.append('<clipPath id="%s"><circle cx="%d" cy="%d" r="%d"/></clipPath>'
                 % (cid, x + size // 2, y + size // 2, size // 2))
    if img:
        parts.append('<image x="%d" y="%d" width="%d" height="%d" '
                     'clip-path="url(#%s)" href="data:image/png;base64,%s"/>'
                     % (x, y, size, size, cid, img))
    else:
        parts.append('<circle cx="%d" cy="%d" r="%d" fill="%s"/>'
                     '<text x="%d" y="%d" font-family="Arial, sans-serif" '
                     'font-size="%d" font-weight="bold" fill="%s" '
                     'text-anchor="middle">%s</text>'
                     % (x + size // 2, y + size // 2, size // 2, TEAL,
                        x + size // 2, y + size // 2 + size // 5,
                        size // 2, WHITE, escape(login[:1].upper())))
    parts.append("</a>")
    return "".join(parts)

def render(groups, total):
    W = 880; pad = 28
    rows = ['<rect width="%d" height="72" fill="%s"/>' % (W, NAVY)]
    rows.append('<text x="%d" y="46" font-family="Arial, sans-serif" '
                'font-size="26" font-weight="bold" fill="%s">DirectDesk Backers</text>'
                % (pad, WHITE))
    rows.append('<rect y="66" width="%d" height="6" fill="%s"/>' % (W, GREEN))
    if total:
        rows.append('<text x="%d" y="46" font-family="Arial, sans-serif" '
                    'font-size="16" fill="#9FD8DE" text-anchor="end">%d sponsor%s</text>'
                    % (W - pad, total, "" if total == 1 else "s"))
    y = 72
    if not total:
        rows.append('<rect y="%d" width="%d" height="128" fill="%s"/>' % (y, W, BG))
        rows.append('<text x="%d" y="%d" font-family="Arial, sans-serif" '
                    'font-size="19" font-weight="bold" fill="%s" '
                    'text-anchor="middle">Sponsorship is open</text>'
                    % (W // 2, y + 56, TEAL))
        rows.append('<rect x="%d" y="%d" width="120" height="4" fill="%s"/>'
                    % (W // 2 - 60, y + 66, GREEN))
        rows.append('<text x="%d" y="%d" font-family="Arial, sans-serif" '
                    'font-size="14" fill="%s" text-anchor="middle">Be the first to back '
                    'DirectDesk - this grid fills in on its own as backers arrive.</text>'
                    % (W // 2, y + 84, MUTED))
        y += 128
    size = 56; gap = 14; per = (W - 2 * pad + gap) // (size + gap)
    for name, members in groups:
        if not members:
            continue
        rows.append('<rect y="%d" width="%d" height="34" fill="%s"/>' % (y, W, BG))
        rows.append('<text x="%d" y="%d" font-family="Arial, sans-serif" '
                    'font-size="14" font-weight="bold" fill="%s">%s</text>'
                    % (pad, y + 22, TEAL, escape(name)))
        y += 34
        lines = (len(members) + per - 1) // per
        rows.append('<rect y="%d" width="%d" height="%d" fill="%s"/>'
                    % (y, W, lines * (size + gap) + 8, WHITE))
        for i, (login, avatar) in enumerate(members):
            tx = pad + (i % per) * (size + gap)
            ty = y + 8 + (i // per) * (size + gap)
            rows.append(avatar_tile(tx, ty, size, login, avatar))
        y += lines * (size + gap) + 8
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
           'viewBox="0 0 %d %d"><!-- backers: %d -->\n%s\n</svg>\n'
           % (W, y, W, y, total, "\n".join(rows)))
    return svg

def main():
    token = os.environ.get("SPONSORS_TOKEN", "").strip()
    if not token:
        if os.path.exists(OUT):
            with open(OUT, encoding="utf-8") as fh:
                if "<!-- backers: 0 -->" not in fh.read():
                    print("SPONSORS_TOKEN not set and a populated grid "
                          "exists - leaving it untouched.")
                    return 0
        with open(OUT, "w", encoding="utf-8") as fh:
            fh.write(render([], 0))
        print("SPONSORS_TOKEN not set - wrote the zero-state grid.")
        return 0
    try:
        sponsors = fetch_sponsors(token)
    except Exception as exc:
        print("Sponsor fetch failed (%s) - existing grid untouched." % exc)
        return 1
    groups = {}
    for login, price, one, avatar in sponsors:
        groups.setdefault(tier_of(price, one), []).append((login, avatar))
    ordered = [(name, sorted(groups.get(name, []), key=lambda m: m[0].lower()))
               for _floor, name in TIERS]
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(render(ordered, len(sponsors)))
    print("Wrote sponsors.svg with %d public sponsor(s)." % len(sponsors))
    return 0

if __name__ == "__main__":
    sys.exit(main())
