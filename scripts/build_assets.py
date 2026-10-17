#!/usr/bin/env python3
"""Generate the CRT-terminal style SVG cards used by README.md.

Reads profile.config.json (content) and stats.json (numbers) and writes
SVG files into assets/. Standard library only.

    python scripts/build_assets.py
"""
import html
import json
import pathlib
import random
import textwrap

ROOT = pathlib.Path(__file__).resolve().parent.parent
CFG = json.loads((ROOT / "profile.config.json").read_text(encoding="utf-8"))
try:
    STATS = json.loads((ROOT / "stats.json").read_text(encoding="utf-8"))
except (FileNotFoundError, ValueError):
    STATS = {}
OUT = ROOT / "assets"
OUT.mkdir(exist_ok=True)

START, END = "<!--START_PROJECTS-->", "<!--END_PROJECTS-->"


def get_projects():
    """Auto-detected repos from stats.json, else the manual list in the config."""
    projs = STATS.get("projects") or CFG["projects"]
    return projs[: int(CFG.get("projects_count", 6))]


def update_readme(projs):
    """Rewrite the project links between the markers in README.md."""
    readme = ROOT / "README.md"
    if not readme.exists():
        return
    text = readme.read_text(encoding="utf-8")
    if START not in text or END not in text:
        return
    lines = []
    for p in projs:
        url = p.get("url") or f"https://github.com/{CFG['username']}/{p.get('repo', p['title'])}"
        desc = " ".join(str(p.get("desc", "")).split())
        lines.append(f"- [**{p['title']}**]({url}) - {desc}")
    head = text.split(START)[0]
    tail = text.split(END, 1)[1]
    readme.write_text(head + START + "\n" + "\n".join(lines) + "\n" + END + tail, encoding="utf-8")

BG = "#0d1117"
BAR = "#111a22"
GREEN = "#39ff7a"
DIM = "#1f6f43"
TEXT = "#c9d1d9"
MUTED = "#6e7f8d"
FONT = "'JetBrains Mono','Fira Code','SFMono-Regular',Consolas,'Courier New',monospace"
W = 1200


def esc(s):
    return html.escape(str(s), quote=True)


def num(key, default=0):
    try:
        return int(STATS.get(key, default) or 0)
    except (TypeError, ValueError):
        return default


def svg(w, h, body, title, extra_css="", extra_defs=""):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{esc(title)}">
<title>{esc(title)}</title>
<defs>
<pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse"><rect width="4" height="1" fill="#000" opacity=".30"/></pattern>
<filter id="glow" x="-20%" y="-30%" width="140%" height="160%"><feGaussianBlur stdDeviation="2.4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<linearGradient id="fade" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{GREEN}" stop-opacity="0"/><stop offset=".5" stop-color="{GREEN}"/><stop offset="1" stop-color="{GREEN}" stop-opacity="0"/></linearGradient>
<clipPath id="clip"><rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="12"/></clipPath>
{extra_defs}
</defs>
<style>
text{{font-family:{FONT}}}
.g{{fill:{GREEN}}} .t{{fill:{TEXT}}} .m{{fill:{MUTED}}} .b{{font-weight:700}}
@keyframes blink{{0%,49%{{opacity:1}}50%,100%{{opacity:0}}}}
.cur{{animation:blink 1s steps(1) infinite}}
@keyframes pulse{{0%,100%{{opacity:.55}}50%{{opacity:1}}}}
.pulse{{animation:pulse 2.4s ease-in-out infinite}}
{extra_css}
</style>
{body}
</svg>
"""


def window(w, h, title):
    return f"""<rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="12" fill="{BG}" stroke="{DIM}" stroke-width="2"/>
<path d="M1 13a12 12 0 0 1 12-12h{w - 26}a12 12 0 0 1 12 12v30H1z" fill="{BAR}"/>
<circle cx="26" cy="22" r="6" fill="#ff5f56"/><circle cx="48" cy="22" r="6" fill="#ffbd2e"/><circle cx="70" cy="22" r="6" fill="{GREEN}"/>
<text x="{w // 2}" y="27" text-anchor="middle" class="m" font-size="13">{esc(title)}</text>"""


def scanlines(w, h):
    return f'<rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="12" fill="url(#scan)" pointer-events="none"/>'


def rain(w, h, cols, seed, opacity, fall_to):
    """Falling matrix characters. Returns (markup, css)."""
    rnd = random.Random(seed)
    chars = "01<>/{}[];=+*#$%&"
    parts = []
    step = w / cols
    for i in range(cols):
        x = round(i * step + rnd.uniform(0, step * 0.6), 1)
        dur = round(rnd.uniform(6, 12), 1)
        delay = round(-rnd.uniform(0, dur), 1)
        length = rnd.randint(7, 13)
        glyphs = []
        for j in range(length):
            op = round(opacity * (j + 1) / length, 3)
            glyphs.append(
                f'<text x="0" y="{j * 16}" font-size="14" fill="{GREEN}" opacity="{op}">{esc(rnd.choice(chars))}</text>'
            )
        parts.append(
            f'<g transform="translate({x} 0)"><g style="animation:rf {dur}s linear {delay}s infinite">{"".join(glyphs)}</g></g>'
        )
    css = f"@keyframes rf{{from{{transform:translateY(-230px)}}to{{transform:translateY({fall_to}px)}}}}"
    return f'<g clip-path="url(#clip)">{"".join(parts)}</g>', css


def write(name, content):
    (OUT / name).write_text(content, encoding="utf-8")
    print("wrote assets/" + name)


# --------------------------------------------------------------------------- header
def build_header():
    h = 320
    name = CFG["name"]
    roles = CFG["roles"]
    phrases = CFG["typing"]
    n = len(phrases)
    slot = 100 / n
    css_parts, text_parts = [], []
    for i, p in enumerate(phrases):
        a = round(i * slot, 2)
        b = round((i + 1) * slot - 3, 2)
        css_parts.append(
            f"@keyframes ph{i}{{0%,{max(a - 0.01, 0)}%{{opacity:0}}{a}%,{b}%{{opacity:1}}{round(b + 1.5, 2)}%,100%{{opacity:0}}}}"
            f".ph{i}{{animation:ph{i} {n * 4}s linear infinite;opacity:0}}"
        )
        text_parts.append(
            f'<text x="62" y="272" font-size="21" class="ph{i}"><tspan class="g">&gt;</tspan><tspan class="t"> {esc(p)}</tspan><tspan class="g cur">_</tspan></text>'
        )
    rain_markup, rain_css = rain(W, h, 46, 7, 0.28, h + 30)
    role_x = 62
    role_svg = []
    for i, r in enumerate(roles):
        txt = esc(r)
        role_svg.append(f'<tspan class="g">{txt}</tspan>')
        if i < len(roles) - 1:
            role_svg.append('<tspan class="m">  |  </tspan>')
    body = (
        window(W, h, f"{CFG['username']} - ~/profile")
        + rain_markup
        + f'<text x="62" y="96" font-size="17" class="m">$ ./hello_world <tspan class="g">--name</tspan></text>'
        + f'<text x="60" y="170" font-size="54" class="g b" filter="url(#glow)">{esc(name)}</text>'
        + f'<text x="62" y="214" font-size="23">{"".join(role_svg)}</text>'
        + f'<rect x="62" y="232" width="340" height="2" fill="url(#fade)"/>'
        + "".join(text_parts)
        + scanlines(W, h)
    )
    write("header.svg", svg(W, h, body, f"{name} - {' | '.join(roles)}", "\n".join(css_parts) + rain_css))


# --------------------------------------------------------------------------- divider
def build_divider():
    body = (
        f'<rect x="40" y="9" width="{W - 80}" height="2" fill="url(#fade)"/>'
        f'<rect x="{W // 2 - 5}" y="5" width="10" height="10" fill="{GREEN}" transform="rotate(45 {W // 2} 10)" class="pulse" filter="url(#glow)"/>'
    )
    write("divider.svg", svg(W, 20, body, "divider"))


# --------------------------------------------------------------------------- section banners
def build_section(slug, title):
    h = 64
    body = (
        f'<text x="40" y="26" font-size="14" class="m">$ cd ~/{esc(slug)}</text>'
        f'<text x="40" y="52" font-size="26" class="g b" filter="url(#glow)">&gt; {esc(title)}<tspan class="cur">_</tspan></text>'
        f'<rect x="40" y="58" width="{W - 80}" height="1.5" fill="url(#fade)" opacity=".6"/>'
    )
    write(f"section-{slug}.svg", svg(W, h, body, title))


# --------------------------------------------------------------------------- terminal
def build_terminal():
    lh = 28
    y = 84
    lines = []
    for block in CFG["terminal"]:
        lines.append(f'<text x="40" y="{y}" font-size="16"><tspan class="g">lokeswar@data</tspan><tspan class="m">:</tspan><tspan style="fill:#58a6ff">~</tspan><tspan class="m">$ </tspan><tspan class="t">{esc(block["cmd"])}</tspan></text>')
        y += lh
        for out in block["out"]:
            lines.append(f'<text x="40" y="{y}" font-size="16" class="g" xml:space="preserve" style="white-space:pre">{esc(out)}</text>')
            y += lh
        y += 10
    lines.append(f'<text x="40" y="{y}" font-size="16"><tspan class="g">lokeswar@data</tspan><tspan class="m">:</tspan><tspan style="fill:#58a6ff">~</tspan><tspan class="m">$ </tspan><tspan class="g cur">&#9608;</tspan></text>')
    h = y + 36
    body = window(W, h, "whoami - zsh") + "".join(lines) + scanlines(W, h)
    write("terminal.svg", svg(W, h, body, "whoami: " + CFG["name"]))


# --------------------------------------------------------------------------- interests
def build_interests():
    h = 250
    items = CFG["interests"]
    cw = (W - 80 - 24 * (len(items) - 1)) // len(items)
    cards = []
    for i, it in enumerate(items):
        x = 40 + i * (cw + 24)
        lines = "".join(
            f'<text x="{x + 28}" y="{150 + k * 26}" font-size="16" class="t">{esc(l)}</text>'
            for k, l in enumerate(it["lines"])
        )
        cards.append(
            f'<rect x="{x}" y="50" width="{cw}" height="180" rx="10" fill="{BAR}" stroke="{DIM}" stroke-width="1.5"/>'
            f'<rect x="{x + 28}" y="72" width="52" height="40" rx="6" fill="none" stroke="{GREEN}" stroke-width="2"/>'
            f'<text x="{x + 54}" y="99" text-anchor="middle" font-size="20" class="g b" filter="url(#glow)">{esc(it["badge"])}</text>'
            f'<text x="{x + 94}" y="99" font-size="19" class="g b">{esc(it["title"])}</text>'
            + lines
        )
    body = f'<text x="40" y="30" font-size="14" class="m">$ ls ~/focus-areas</text>' + "".join(cards) + scanlines(W, h)
    write("interests.svg", svg(W, h, body, "Focus areas: AI, Cloud Computing, Data Engineering"))


# --------------------------------------------------------------------------- stack (neofetch)
def build_stack():
    rows = CFG["stack"]
    lh = 32
    h = 110 + lh * len(rows) + 60
    y = 100
    out = []
    out.append(f'<text x="42" y="150" font-size="96" class="g b pulse" filter="url(#glow)">{{ }}</text>')
    out.append(f'<text x="48" y="205" font-size="15" class="m">data . ai . cloud</text>')
    out.append(f'<text x="360" y="{y}" font-size="18"><tspan class="g b">lokeswar</tspan><tspan class="m">@</tspan><tspan class="g b">stack</tspan></text>')
    out.append(f'<rect x="360" y="{y + 10}" width="760" height="1.5" fill="{DIM}"/>')
    y += 42
    for r in rows:
        items = "  .  ".join(r["items"])
        out.append(
            f'<text x="360" y="{y}" font-size="17" class="g b">{esc(r["label"])}</text>'
            f'<text x="500" y="{y}" font-size="17" class="t">{esc(items)}</text>'
        )
        y += lh
    cols = ["#ff5f56", "#ffbd2e", GREEN, "#58a6ff", "#bc8cff", "#39c5cf", "#c9d1d9", "#6e7f8d"]
    sw = "".join(f'<rect x="{360 + i * 34}" y="{y + 6}" width="30" height="16" fill="{c}"/>' for i, c in enumerate(cols))
    body = window(W, h, "neofetch --stack") + "".join(out) + sw + scanlines(W, h)
    write("stack.svg", svg(W, h, body, "Tech stack"))


# --------------------------------------------------------------------------- stats
def fmt(n):
    return f"{int(n):,}"


def build_stats():
    h = 380
    metrics = [
        ("commits", "total commits"),
        ("prs", "pull requests"),
        ("issues", "issues"),
        ("stars", "stars earned"),
        ("repos", "repositories"),
        ("followers", "followers"),
        ("current_streak", "current streak (days)"),
        ("longest_streak", "longest streak (days)"),
    ]
    out = []
    for i, (k, label) in enumerate(metrics):
        col, row = i % 4, i // 4
        x = 40 + col * 190
        y = 90 + row * 130
        out.append(
            f'<rect x="{x}" y="{y}" width="176" height="108" rx="8" fill="{BAR}" stroke="{DIM}" stroke-width="1.2"/>'
            f'<text x="{x + 88}" y="{y + 56}" text-anchor="middle" font-size="36" class="g b" filter="url(#glow)">{fmt(num(k))}</text>'
            f'<text x="{x + 88}" y="{y + 88}" text-anchor="middle" font-size="12" class="m">{esc(label)}</text>'
        )
    # languages
    lx = 830
    out.append(f'<text x="{lx}" y="96" font-size="17" class="g b">top languages</text>')
    out.append(f'<rect x="{lx}" y="106" width="330" height="1.5" fill="{DIM}"/>')
    langs = STATS.get("top_languages") or []
    if not langs:
        out.append(f'<text x="{lx}" y="146" font-size="14" class="m">no data yet - run the</text>')
        out.append(f'<text x="{lx}" y="168" font-size="14" class="m">"Update stats" workflow</text>')
    for i, lg in enumerate(langs[:6]):
        y = 140 + i * 38
        pct = max(0.0, min(100.0, float(lg.get("pct", 0))))
        out.append(
            f'<text x="{lx}" y="{y}" font-size="14" class="t">{esc(lg["name"])}</text>'
            f'<text x="{lx + 330}" y="{y}" text-anchor="end" font-size="14" class="g">{pct:.1f}%</text>'
            f'<rect x="{lx}" y="{y + 8}" width="330" height="8" rx="4" fill="#16212b"/>'
            f'<rect x="{lx}" y="{y + 8}" width="{330 * pct / 100:.1f}" height="8" rx="4" fill="{GREEN}"/>'
        )
    upd = STATS.get("updated") or "pending first run"
    out.append(f'<text x="40" y="{h - 18}" font-size="12" class="m">contributions in the last year: {fmt(num("contributions_year"))}   |   updated: {esc(upd)}</text>')
    body = window(W, h, "github --stats --all") + "".join(out) + scanlines(W, h)
    write("stats.svg", svg(W, h, body, "GitHub stats"))


# --------------------------------------------------------------------------- achievements
TIERS = [
    ("locked", "#3a4651"),
    ("bronze", "#cd7f32"),
    ("silver", "#c0c8d0"),
    ("gold", "#ffd23f"),
    ("platinum", "#39ff7a"),
    ("diamond", "#58e6ff"),
]


def tier_for(value, thresholds):
    t = 0
    for i, th in enumerate(thresholds, start=1):
        if value >= th:
            t = i
    return t


def build_achievements():
    h = 290
    defs = [
        ("Commits", num("commits"), [10, 100, 500, 1000, 5000]),
        ("Pull Requests", num("prs"), [1, 10, 50, 100, 500]),
        ("Stars", num("stars"), [1, 10, 50, 100, 500]),
        ("Repositories", num("repos"), [3, 10, 25, 50, 100]),
        ("Streak", num("longest_streak"), [3, 7, 30, 100, 365]),
        ("Followers", num("followers"), [1, 10, 50, 100, 500]),
    ]
    cw = (W - 80 - 16 * 5) // 6
    out = [f'<text x="40" y="30" font-size="14" class="m">$ ./achievements --tiers</text>']
    for i, (label, val, ths) in enumerate(defs):
        x = 40 + i * (cw + 16)
        t = tier_for(val, ths)
        name, color = TIERS[t]
        nxt = ths[t] if t < len(ths) else None
        prog = 1.0 if nxt is None else min(1.0, val / nxt)
        cx = x + cw / 2
        out.append(
            f'<rect x="{x}" y="46" width="{cw}" height="224" rx="10" fill="{BAR}" stroke="{color}" stroke-width="1.5" opacity="{1 if t else .7}"/>'
            f'<g transform="translate({cx} 112)" filter="url(#glow)">'
            f'<path d="M-18,-22 H18 V-8 C18,8 9,15 0,15 C-9,15 -18,8 -18,-8 Z" fill="{color}"/>'
            f'<path d="M-18,-16 H-28 V-8 C-28,2 -23,5 -18,5" fill="none" stroke="{color}" stroke-width="3"/>'
            f'<path d="M18,-16 H28 V-8 C28,2 23,5 18,5" fill="none" stroke="{color}" stroke-width="3"/>'
            f'<rect x="-3.5" y="15" width="7" height="12" fill="{color}"/><rect x="-14" y="27" width="28" height="6" rx="2" fill="{color}"/></g>'
            f'<text x="{cx}" y="174" text-anchor="middle" font-size="15" class="t b">{esc(label)}</text>'
            f'<text x="{cx}" y="198" text-anchor="middle" font-size="14" fill="{color}">{name}</text>'
            f'<text x="{cx}" y="222" text-anchor="middle" font-size="12" class="m">{fmt(val)}' + (f' / {fmt(nxt)}' if nxt else ' (max)') + '</text>'
            f'<rect x="{x + 20}" y="238" width="{cw - 40}" height="6" rx="3" fill="#16212b"/>'
            f'<rect x="{x + 20}" y="238" width="{(cw - 40) * prog:.1f}" height="6" rx="3" fill="{color}"/>'
        )
    body = "".join(out) + scanlines(W, h)
    write("achievements.svg", svg(W, h, body, "Achievements"))


# --------------------------------------------------------------------------- projects
def build_projects():
    projs = get_projects()
    cw, ch = (W - 80 - 24) // 2, 170
    rows = (len(projs) + 1) // 2
    h = 50 + rows * (ch + 20)
    out = [f'<text x="40" y="30" font-size="14" class="m">$ ls ~/projects --top</text>']
    for i, p in enumerate(projs):
        col, row = i % 2, i // 2
        title = p["title"] if len(p["title"]) <= 28 else p["title"][:27] + "..."
        x = 40 + col * (cw + 24)
        y = 46 + row * (ch + 20)
        desc = textwrap.wrap(p["desc"], 58)[:3]
        d = "".join(f'<text x="{x + 28}" y="{y + 84 + k * 22}" font-size="14" class="t">{esc(l)}</text>' for k, l in enumerate(desc))
        tx = x + 28
        tags = []
        for tg in p["tags"][:4]:
            tw = 12 + len(tg) * 8.2
            tags.append(
                f'<rect x="{tx}" y="{y + ch - 40}" width="{tw:.0f}" height="24" rx="12" fill="none" stroke="{DIM}"/>'
                f'<text x="{tx + tw / 2:.0f}" y="{y + ch - 23}" text-anchor="middle" font-size="12" class="g">{esc(tg)}</text>'
            )
            tx += tw + 10
        out.append(
            f'<rect x="{x}" y="{y}" width="{cw}" height="{ch}" rx="10" fill="{BAR}" stroke="{DIM}" stroke-width="1.5"/>'
            f'<text x="{x + 28}" y="{y + 44}" font-size="20" class="g b" filter="url(#glow)">./{esc(title)}</text>'
            f'<text x="{x + cw - 28}" y="{y + 44}" text-anchor="end" font-size="13" class="m">#{i + 1:02d}</text>'
            f'<rect x="{x + 28}" y="{y + 54}" width="{cw - 56}" height="1" fill="{DIM}"/>'
            + d + "".join(tags)
        )
    body = "".join(out) + scanlines(W, h)
    write("projects.svg", svg(W, h, body, "Featured projects"))


# --------------------------------------------------------------------------- footer
def build_footer():
    h = 200
    f = CFG["footer"]
    rain_markup, rain_css = rain(W, h, 40, 21, 0.25, h + 30)
    body = (
        window(W, h, "contact --open")
        + rain_markup
        + f'<text x="{W // 2}" y="112" text-anchor="middle" font-size="40" class="g b" filter="url(#glow)">{esc(f["headline"])}</text>'
        + f'<text x="{W // 2}" y="148" text-anchor="middle" font-size="18" class="t">{esc(f["sub"])}</text>'
        + f'<text x="{W // 2}" y="178" text-anchor="middle" font-size="15" class="m">&gt; get in touch<tspan class="g cur">_</tspan></text>'
        + scanlines(W, h)
    )
    write("footer.svg", svg(W, h, body, f["headline"], rain_css))


def main():
    build_header()
    build_divider()
    for slug, title in [
        ("about", "About"),
        ("focus", "What I do"),
        ("projects", "Featured work"),
        ("stack", "Tech stack"),
        ("stats", "GitHub activity"),
        ("feed", "Latest activity"),
        ("contact", "Let's talk"),
    ]:
        build_section(slug, title)
    build_terminal()
    build_interests()
    build_stack()
    build_stats()
    build_achievements()
    build_projects()
    build_footer()
    update_readme(get_projects())


if __name__ == "__main__":
    main()
