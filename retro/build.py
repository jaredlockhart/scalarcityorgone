#!/usr/bin/env python3
"""Builds site/index.html: the 90s-styled look of the Scalar Orgone site. Ported from the
artist-approved mock "PRODUCT HEROES": masthead, 17 product heroes (each its own shrine: its own
table, its own text, its own materials list, its own matched GIFs, its own layout), about, footer.
No sidebar, no topic drawers, no button wall. Plain HTML 4, no CSS/JS except the one permitted
body style= for the full-window background and the one small <style> block for phones.

Self-contained: every asset it reads lives under this repo (retro/products.json next to this
script, and the GIFs/photos under site/retro/). It writes site/index.html with every path relative
to site/, and it also writes the small hooks (ids / data-* attributes) that site/retro/retro.js
uses at runtime to keep the page's prices, availability and new listings in sync with
site/data/products.json without ever re-running this script.

Deterministic (seeded). Run:  python3 retro/build.py   (from the repo root, or anywhere -- paths
are resolved relative to this file)
"""
import json
import random
import zlib
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).parent
SITE = ROOT.parent / "site"
ASSETS = SITE / "retro" / "assets"
OUT = SITE / "index.html"

random.seed(88)

# ================================================================= palette ==
BLUES = ["#FFFFFF", "#CCE6FF", "#99CCFF", "#00CCFF", "#3399FF", "#0066FF", "#6633CC"]
NAVY = "#000033"
MIDNIGHT = "#000066"
DEEPBLUE = "#001040"
DARKBLUE2 = "#0A0A2A"
ELECTRIC = "#0066FF"
CYAN = "#00CCFF"
SKYBLUE = "#3399FF"
ICE = "#CCE6FF"
PALECYAN = "#99CCFF"
SILVER = "#C0C0C0"
WHITE = "#FFFFFF"
STEEL = "#6688BB"
GOLD = "#FFFFFF"  # prices in white: the page is black and blue only
BLACK = "#000000"

FONTS = ["Times New Roman", "Comic Sans MS, Arial", "Arial", "Courier New", "Impact, Arial"]

# ================================================================ scan assets =
INFO = {}
for p in sorted(ASSETS.glob("*.gif")):
    with Image.open(p) as im:
        INFO[p.name] = {"frames": getattr(im, "n_frames", 1), "w": im.width, "h": im.height}
ALL = sorted(INFO)
USED = set()


def img(name, w=None, h=None, align=None, hspace=None, vspace=None, alt=None, border=0, lazy=True):
    USED.add(name)
    info = INFO[name]
    width = w or info["w"]
    height = h if h is not None else (info["h"] if w is None else round(info["h"] * width / info["w"]))
    bits = [f'src="retro/assets/{name}"', f'width="{width}"', f'height="{height}"', f'border="{border}"']
    if align:
        bits.append(f'align="{align}"')
    if hspace is not None:
        bits.append(f'hspace="{hspace}"')
    if vspace is not None:
        bits.append(f'vspace="{vspace}"')
    if lazy:
        bits.append('loading="lazy"')
    bits.append(f'alt="{alt or name.replace(".gif", "")}"')
    return f'<img {" ".join(bits)}> '


def thumb(name, maxdim=50, lazy=True, **kw):
    info = INFO[name]
    scale = min(1.0, maxdim / max(info["w"], info["h"]))
    w = max(1, round(info["w"] * scale))
    return img(name, w=w, lazy=lazy, **kw)


def bg(name, allow_animated=False):
    if not allow_animated:
        assert INFO[name]["frames"] == 1, f"{name} must be single-frame to use as a background"
    USED.add(name)
    return f"retro/assets/{name}"


def font(text, face="Courier New", color=ICE, size=2, b=False, i=False):
    t = text
    if b:
        t = f"<b>{t}</b>"
    if i:
        t = f"<i>{t}</i>"
    return f'<font face="{face}" color="{color}" size="{size}">{t}</font>'


def rainbow(text, face="Times New Roman", size=7, b=True):
    """Letter-by-letter rainbow text. Letters within a word stay glued together (no space, so
    they don't visually separate); a real breakable space sits between words -- a run of huge
    per-letter <font> tags with NO break opportunity anywhere (e.g. &nbsp; for spaces) blows the
    whole page out sideways, since the browser has nowhere to wrap a long headline."""
    words = text.split(" ")
    out_words = []
    ci = 0
    for word in words:
        letters = []
        for ch in word:
            letters.append(f'<font face="{face}" size="{size}" color="{BLUES[ci % len(BLUES)]}">{ch}</font>')
            ci += 1
        out_words.append("".join(letters))
    t = " ".join(out_words)
    if b:
        t = f"<b>{t}</b>"
    return t


def rainbow_lines(lines, face="Times New Roman", size=7, b=True, gap_w=28):
    """Like rainbow(), but the words are split across explicit <br>-separated lines (for the
    masthead headline). The letter colour cycle continues across the whole run so the result
    matches what one rainbow() call over all the words would have produced. Between the two
    words on each line sits a transparent spacer (so there's a clear gap) plus a normal breakable
    space, so the line can still wrap on a narrow phone."""
    ci = 0
    out_lines = []
    for line in lines:
        out_words = []
        for word in line.split(" "):
            letters = []
            for ch in word:
                letters.append(f'<font face="{face}" size="{size}" color="{BLUES[ci % len(BLUES)]}">{ch}</font>')
                ci += 1
            out_words.append("".join(letters))
        gap = img("spacer.gif", w=gap_w, h=1, lazy=False) + " "
        out_lines.append(gap.join(out_words))
    t = "<br>".join(out_lines)
    if b:
        t = f"<b>{t}</b>"
    return t


# ---------------------------------------------------------------- theme pools --
THEMES = {}
for name in ALL:
    if "--" in name:
        theme, _ = name.split("--", 1)
        THEMES.setdefault(theme, []).append(name)
for theme in THEMES:
    random.shuffle(THEMES[theme])
CURSOR = {t: 0 for t in THEMES}


def take(theme, n):
    lst = THEMES[theme]
    out = []
    for _ in range(n):
        out.append(lst[CURSOR[theme] % len(lst)])
        CURSOR[theme] += 1
    return out


EXPLICIT_USED = set()


def explicit(name):
    assert name not in EXPLICIT_USED, f"explicit asset reused across heroes: {name}"
    EXPLICIT_USED.add(name)
    return name


# ---------------------------------------------------------------- dividers --
# The artist dropped the whole "dividers-badges" library topic (2026-10-12): no GIF whose name
# starts with "dividers-badges--" may appear anywhere on the page. Section-level dividers and the
# per-listing dividers above/below each hero now draw from the hand-drawn divider set plus a
# couple of tesla-electric divider/lightning bars, so the gaps between sections and between
# listings stay dressed without it.
SECTION_DIVIDERS = ["divider-arcane-a.gif", "divider-lightning-a.gif",
                     "tesla-electric--electric-divider-wide.gif", "divider-hieroglyph-a.gif",
                     "tesla-electric--lightning-divider-bar.gif"]


def divider(w=None):
    name = SECTION_DIVIDERS[divider.i % len(SECTION_DIVIDERS)]
    divider.i += 1
    return f'<center>{img(name, w=w or min(400, INFO[name]["w"]))}</center>'


divider.i = 0


def own_divider():
    """Each hero gets its own divider bar above and below, from a small drawn + lightning-bar
    pool (no dividers-badges)."""
    pool = ["divider-arcane-a.gif", "divider-arcane-b.gif", "divider-lightning-a.gif",
            "divider-lightning-b.gif", "divider-hieroglyph-a.gif",
            "tesla-electric--electric-divider-bar.gif", "tesla-electric--electric-line-divider.gif"]
    name = pool[own_divider.i % len(pool)]
    own_divider.i += 1
    return f'<center>{img(name, w=min(360, INFO[name]["w"]))}</center>'


own_divider.i = 0

BULLETS = ["bullet-torus.gif", "bullet-pyramid.gif", "bullet-eye.gif", "bullet-spark.gif", "bullet-star.gif"]
ARROWS = ["bullet-arrow-cyan.gif", "bullet-arrow-ice.gif"]


def bullet(i):
    return img(BULLETS[i % len(BULLETS)], align="absmiddle")


def arrow(i):
    return img(ARROWS[i % len(ARROWS)], align="absmiddle")


# ============================================================== product data =
# Id, display name, category, price, Etsy url and the live photo path recorded at build time
# (compared at runtime by retro.js against data/products.json's current "image", so it can swap
# the photo if it changed on Etsy). Kept as its own small JSON file so it's easy to refresh.
PRODUCTS = {p["id"]: p for p in json.loads((ROOT / "products.json").read_text())["products"]}


def price_str(pid):
    amt = PRODUCTS[pid]["price"]["amount"]
    return f"CA${amt:,.2f}"


def by_category(cat):
    return [pid for pid, p in PRODUCTS.items() if p["category"] == cat]


# full Etsy titles + materials ("WHAT'S INSIDE" table), from the artist's product notes
FACTS = {
    "4558993952": {
        "title": "8-Sided Cheops Orgone Pyramid - desert sky",
        "materials": ["black zinc flakes", "diatomaceous earth", "selenite", "cannabis", "gold", "rose quartz",
                      "quartz", "monoatomic ormus", "black iron magnetite", "shungite", "copper", "resin"],
    },
    "4558990496": {
        "title": "8-Sided Cheops Orgone Pyramid with large quartz cluster , copper spheres and mica halo",
        "materials": ["mica", "cannabis", "gold", "quartz", "monoatomic ormus", "black iron magnetite", "shungite",
                      "copper", "resin", "selenite", "pyrite"],
    },
    "4558966455": {
        "title": "8-Sided Cheops orgone pyramid with quartz/pyrite sphere",
        "materials": ["mica", "selenite", "cannabis", "gold", "rose quartz", "quartz", "monoatomic ormus",
                      "black iron magnetite", "shungite", "copper", "elite shungite"],
    },
    "4558964255": {
        "title": "8-Sided Cheops Orgone Pyramid with Quartz/pyrite Cluster & iridescent waves",
        "materials": ["diatomaceous earth", "zinc", "pyrite", "graphene", "mica", "monoatomic ormus",
                      "black iron magnetite", "shungite", "copper", "resin", "citrine", "chalcedony",
                      "aura cluster"],
    },
    "1759891754": {
        "title": "8-Sided Cheops Orgone Pyramid -silver labyrinth on iridescent pyramid with copper wrapped orgone core",
        "materials": ["black zinc flakes", "diatomaceous earth", "selenite", "cannabis", "gold", "rose quartz",
                      "quartz", "monoatomic ormus", "black iron magnetite", "shungite", "copper", "resin"],
    },
    "1786644260": {
        "title": "8-Sided Cheops Orgone Pyramid - pastel sky",
        "materials": ["black zinc flakes", "diatomaceous earth", "selenite", "cannabis", "gold", "rose quartz",
                      "quartz", "monoatomic ormus", "black iron magnetite", "shungite", "copper", "resin"],
    },
    "1528324112": {
        "title": "Quartz Rutile Cloudbuster Orgonite – Tensor Rings, EMF Protection",
        "materials": ["graphene honey", "gans", "shungite", "zinc", "quartz", "monoatomic ormus",
                      "black iron magnetite", "copper", "tensor ring"],
    },
    "4482087245": {
        "title": "Earthpipe Cloudbuster with Shungite, Iron, Copper, Quartz, & 1/2 Lost Cubit Tensor Ring -25x10cm",
        "materials": ["graphene honey", "gans", "shungite", "zinc", "quartz", "monoatomic ormus",
                      "black iron magnetite", "copper", "tensor ring"],
    },
    "1749902666": {
        "title": "Smokey quartz earthpipe Cloudbuster with wooden base and 1/4 empowerment cubit tensor",
        "materials": ["graphene honey", "gans", "shungite", "zinc", "quartz", "monoatomic ormus",
                      "black iron magnetite", "copper", "tensor ring"],
    },
    "4470900991": {
        "title": "Stainless steel Earthpipe Cloudbuster with quartz tips , Silver plated copper base,"
                  "crushed quartz and Stu cubit dragon scale tensor ring",
        "materials": ["gans", "shungite", "zinc", "quartz", "monoatomic ormus", "black iron magnetite",
                      "copper", "tensor ring", "Smokey quartz"],
    },
    "1787602558": {
        "title": "Orgone Cellphone Sticker - holographic triangle",
        "materials": ["resin", "zinc", "quartz", "shungite", "ormus", "magnetite", "copper"],
    },
    "1728100038": {
        "title": "Orgone mix coaster/water charger with holographic torus -12cm",
        "materials": ["resin", "zinc", "quartz", "shungite", "ormus", "magnetite", "copper", "iridescent glitter"],
    },
    "1801801867": {
        "title": "Orgone Cellphone Sticker - holographic 8 pointed star",
        "materials": ["resin", "zinc", "quartz", "shungite", "ormus", "magnetite", "copper"],
    },
    "1701108597": {
        "title": "Orgone Cellphone Sticker - pinecone",
        "materials": ["resin", "zinc", "quartz", "shungite", "ormus", "magnetite", "copper"],
    },
    "1701109811": {
        "title": "Orgone Cellphone Sticker - Crystal",
        "materials": ["resin", "zinc", "quartz", "shungite", "ormus", "magnetite", "copper"],
    },
    "1425287636": {
        "title": "Orgone Cellphone Sticker - Star",
        "materials": ["resin", "zinc", "quartz", "shungite", "ormus", "magnetite", "copper"],
    },
    "1796765960": {
        "title": "charging/cleansing/rolling tray",
        "materials": ["quartz", "copper", "monoatomic ormus", "mica", "resin", "shungite", "magnetite", "vinyl"],
    },
}

# Two sentences of flavour per product. The ingredients are NOT repeated here: the WHAT'S INSIDE table is
# refreshed from Etsy by site/retro/retro.js, and prose that listed them would go stale.
BLURBS = {
    "4558993952": [
        "Behold the 8-Sided Cheops Pyramid in its Desert Sky colourway: eight faces rising to a point, "
        "finished in warm dune tones under a dusk-blue dome.",
        "A little landscape in miniature, pyramid-shaped, desert-coloured, ready for the shelf.",
    ],
    "4558990496": [
        "The 8-Sided Cheops Pyramid with Large Quartz Cluster tops its eight faces with a genuine quartz "
        "cluster, ringed by a halo of shimmering mica and copper spheres.",
        "Easily the spikiest pyramid in the collection, and proud of it.",
    ],
    "4558966455": [
        "This 8-Sided Cheops Pyramid wears a polished quartz-and-pyrite sphere at its peak, catching the "
        "light like a tiny planet balanced on a mountain.",
        "Part geometry lesson, part gemstone, entirely a pyramid.",
    ],
    "4558964255": [
        "Waves of iridescent colour ripple across this 8-Sided Cheops Pyramid, crowned with a "
        "quartz/pyrite cluster and an aura cluster for good measure.",
        "The waviest pyramid in the house, by design.",
    ],
    "1759891754": [
        "Trace the path across this 8-Sided Cheops Pyramid — Silver Labyrinth, where a hand-finished "
        "silver maze winds over an iridescent surface around a copper-wrapped core.",
        "Every turn of the labyrinth leads back to the apex.",
    ],
    "1786644260": [
        "Softer than its Desert Sky sibling, this 8-Sided Cheops Pyramid — Pastel Sky drifts in powder "
        "blues and clouded pinks across all eight faces.",
        "A pyramid for cloud-watchers.",
    ],
    "1528324112": [
        "The Quartz Rutile Cloudbuster Orgonite stands tall, tensor rings stacked along its length and a "
        "rutile quartz point at the tip.",
        "A tower built for the sky, not the shelf.",
    ],
    "4482087245": [
        "At 25 by 10 centimetres, the Earthpipe Cloudbuster with Shungite, Iron, Copper, Quartz & ½ Lost "
        "Cubit Tensor Ring is the broad-shouldered one of the family.",
        "Built like a chimney, aimed at the weather.",
    ],
    "1749902666": [
        "This Smokey Quartz Earthpipe Cloudbuster rests on a proper wooden base, a quarter empowerment "
        "cubit tensor ring coiled near its crown.",
        "The quiet one of the cloudbuster shelf, until you look closely.",
    ],
    "4470900991": [
        "The flagship: a Stainless Steel Earthpipe Cloudbuster with quartz tips, a silver-plated copper "
        "base, crushed quartz and a full Stu cubit dragon-scale tensor ring.",
        "The most cloudbuster any cloudbuster in this shop has ever cloudbusted.",
    ],
    "1787602558": [
        "A small Orgone Cellphone Sticker shaped like a holographic triangle, catching rainbow light off "
        "every angle no matter which way you tilt your phone.",
        "The tiniest pyramid shape in the whole shop.",
    ],
    "1728100038": [
        "Set your glass on the Orgone mix coaster/water charger, a 12cm disc ringed by a holographic "
        "torus and a scatter of iridescent glitter.",
        "A ring-shaped little universe to rest a mug on.",
    ],
    "1801801867": [
        "Eight points, one hologram: the Orgone Cellphone Sticker — holographic 8 pointed star throws "
        "colour in every direction it's held up to.",
        "The star of the sticker drawer.",
    ],
    "1701108597": [
        "The Orgone Cellphone Sticker - pinecone is exactly that: a tidy little pinecone silhouette, "
        "scale by scale.",
        "Small, woodland, and stuck to a phone near you.",
    ],
    "1701109811": [
        "A faceted little gem rendered flat: the Orgone Cellphone Sticker - Crystal, cut like a jewel and"
        " finished glossy.",
        "Proof that good things come in sticker-sized packages.",
    ],
    "1425287636": [
        "Plain and proud, the Orgone Cellphone Sticker - Star is exactly what it says: a single star.",
        "No frills, no hologram, just a star doing its best star impression. The classic of the lineup.",
    ],
    "1796765960": [
        "Part tray, part centrepiece: the charging/cleansing/rolling tray catches a little sparkle of its"
        " own in the light.",
        "Big enough for a full rolling session or a small gathering of crystals.",
    ],
}

# per-hero: pool pulls, explicit (exact, unique page-wide) names, a drawn "signature" shape,
# layout, and table dressing (border/bg/width/align) -- varied deliberately between heroes. The
# artist dropped "dividers-badges" (2026-10-12); every pool that used to pull from it now pulls
# from another approved topic instead (no need to match the old counts one for one).
HERO_CFG = {
    "4558993952": dict(pools=[("pyramids-egypt", 6), ("esoteric-homepages", 3), ("crystals-geometry", 2)],
                        explicit=[],
                        signature="pyramid-wire-cyan.gif", layout="center", border=4, bgcolor=NAVY, width="90%"),
    "4558990496": dict(pools=[("pyramids-egypt", 3), ("crystals-geometry", 6), ("esoteric-homepages", 2)],
                        explicit=[], signature="pyramid-solid-silver.gif", layout="side-left", border=3,
                        bgcolor=MIDNIGHT, width="80%"),
    "4558966455": dict(pools=[("pyramids-egypt", 3), ("crystals-geometry", 6), ("esoteric-homepages", 1)],
                        explicit=[], signature="rosette-gold.gif", layout="side-right", border=6,
                        bgcolor=DEEPBLUE, width="75%"),
    "4558964255": dict(pools=[("pyramids-egypt", 3), ("crystals-geometry", 6), ("esoteric-homepages", 2)],
                        explicit=[], signature="pyramid-wire-gold.gif", layout="float-right", border=2,
                        bgcolor=DARKBLUE2, width="70%"),
    "1759891754": dict(pools=[("pyramids-egypt", 3), ("crystals-geometry", 4), ("esoteric-homepages", 3)],
                        explicit=["spiral-maze.gif"], signature="pyramid-solid-ice.gif", layout="side-left",
                        border=5, bgcolor=NAVY, width="82%"),
    "1786644260": dict(pools=[("pyramids-egypt", 3), ("tesla-electric", 3), ("crystals-geometry", 2),
                               ("esoteric-homepages", 2)],
                        explicit=[], signature="rosette-cyan.gif", layout="offside-right", border=3,
                        bgcolor=MIDNIGHT, width="62%"),
    "1528324112": dict(pools=[("tesla-electric", 10), ("esoteric-homepages", 2)], explicit=[],
                        signature="torus-cyan.gif", layout="side-right", border=5, bgcolor=DEEPBLUE, width="78%"),
    "4482087245": dict(pools=[("tesla-electric", 10), ("esoteric-homepages", 2)], explicit=[],
                        signature="torus-electric.gif", layout="float-left", border=7, bgcolor=NAVY, width="72%"),
    "1749902666": dict(pools=[("tesla-electric", 9), ("crystals-geometry", 3)], explicit=[],
                        signature="torus-silver.gif", layout="side-left", border=2, bgcolor=DARKBLUE2, width="76%"),
    "4470900991": dict(pools=[("tesla-electric", 13), ("esoteric-homepages", 2)], explicit=[],
                        signature="torus-white.gif", layout="center", border=8, bgcolor=MIDNIGHT, width="94%"),
    "1787602558": dict(pools=[("esoteric-homepages", 4), ("crystals-geometry", 3), ("pyramids-egypt", 2)],
                        explicit=["triangle-prism.gif"], signature=None, layout="side-right", border=3,
                        bgcolor=NAVY, width="60%"),
    "1728100038": dict(pools=[("tesla-electric", 5), ("crystals-geometry", 2), ("esoteric-homepages", 1)],
                        explicit=[], signature="torus-gold.gif", layout="side-left", border=4, bgcolor=DEEPBLUE,
                        width="62%"),
    "1801801867": dict(pools=[("tesla-electric", 4), ("crystals-geometry", 2), ("esoteric-homepages", 2)],
                        explicit=["star-8point-cyan.gif"], signature=None, layout="offside-left", border=6,
                        bgcolor=DARKBLUE2, width="58%"),
    "1701108597": dict(pools=[("crystals-geometry", 5), ("tesla-electric", 2), ("pyramids-egypt", 1)],
                        explicit=["pinecone-icon.gif"], signature=None, layout="side-right", border=2,
                        bgcolor=NAVY, width="58%"),
    "1701109811": dict(pools=[("crystals-geometry", 7), ("tesla-electric", 2)], explicit=[], signature=None,
                        layout="side-left", border=5, bgcolor=MIDNIGHT, width="60%"),
    "1425287636": dict(pools=[("tesla-electric", 4), ("esoteric-homepages", 3), ("crystals-geometry", 1)],
                        explicit=["star-5point-ice.gif"], signature=None, layout="float-right", border=3,
                        bgcolor=DEEPBLUE, width="58%"),
    "1796765960": dict(pools=[("crystals-geometry", 4), ("esoteric-homepages", 3), ("pyramids-egypt", 1)],
                        explicit=[], signature=None, layout="center", border=4, bgcolor=NAVY, width="85%"),
}


def hero_photo(pid):
    """The big hero photo: full listing width, proportions kept by the browser (no height=),
    linked to the product's Etsy listing. data-image records the live photo path at build time, so
    retro.js can tell when Etsy's photo has changed and swap it in."""
    product = PRODUCTS[pid]
    return (f'<a href="{product["url"]}"><img class="hero-photo" data-image="{product.get("image") or ""}" '
            f'src="retro/products/{pid}.jpg" width="100%" border="3" loading="lazy" alt="{product["name"]}"></a>')


# --------------------------------------------------- buy-link box (beefed up per the artist) --
# No dividers-badges: the in-box accents are the drawn arrows, tesla-electric lightning bits and
# the drawn sparkle/star bullets.
ACCENTS = ["bullet-arrow-cyan.gif", "bullet-arrow-ice.gif", "tesla-electric--bolt-pixel-white.gif",
           "tesla-electric--bolt-pixel-yellow.gif", "tesla-electric--lightning-bolt-animation.gif",
           "bullet-spark.gif", "bullet-star.gif", "tesla-electric--spark-line-animation.gif"]
BOLTS = ["tesla-electric--lightning-ball-electric.gif", "tesla-electric--hazard-lightning-yellow.gif",
         "tesla-electric--bolt-small-pixel.gif", "tesla-electric--bolt-tiny-white.gif",
         "tesla-electric--lightning-bolt-animation.gif"]
SPARKLES = ["bullet-spark.gif", "bullet-star.gif"]
BUY_BUTTONS = ["buy-button-blue.gif", "buy-button-white.gif", "buy-button-silver.gif"]


def _cycle(pool, start, k):
    return [pool[(start + j) % len(pool)] for j in range(k)]


def buy_box(pid, idx):
    """Her ask: 'beef up' the buy link -- its own border=3 electric-blue/cyan framed table,
    full listing width, with inward-pointing arrows either side, bolts, sparkles, a bouncing
    marquee and a drawn button, all still linking to the exact Etsy URL. Arrangement rotates
    through 4 patterns and arrow/bolt picks rotate by product index so listings don't match."""
    url = PRODUCTS[pid]["url"]
    pattern = idx % 4
    top_arrows = _cycle(ACCENTS, idx, 3)
    left_arrows = _cycle(ACCENTS, idx + 3, 2)
    right_arrows = _cycle(ACCENTS, idx + 5, 2)
    bolts = _cycle(BOLTS, idx, 2)
    sparkles = _cycle(SPARKLES, idx, 2)
    marquee_set = _cycle(BOLTS, idx + 2, 2) + _cycle(ACCENTS, idx + 1, 3)
    btn_name = BUY_BUTTONS[idx % len(BUY_BUTTONS)]

    link = font("&raquo;&raquo; BUY / VIEW ON ETSY &laquo;&laquo;", face="Comic Sans MS, Arial",
                color=WHITE, size=6, b=True)
    link_a = f'<a href="{url}">{link}</a>'
    button = f'<a href="{url}">{img(btn_name, w=INFO[btn_name]["w"], border=0)}</a>'

    top_row = ("".join(img(n, w=min(34, INFO[n]["w"]), align="absmiddle") for n in top_arrows))
    left_cell = (img(bolts[0], w=min(38, INFO[bolts[0]]["w"]), align="absmiddle")
                 + "".join(img(n, w=min(30, INFO[n]["w"]), align="absmiddle") for n in left_arrows))
    right_cell = ("".join(img(n, w=min(30, INFO[n]["w"]), align="absmiddle") for n in right_arrows)
                  + img(bolts[1], w=min(38, INFO[bolts[1]]["w"]), align="absmiddle"))
    sparkle_bits = "".join(img(n, align="absmiddle") for n in sparkles)
    marquee = (f'<marquee behavior="alternate" scrollamount="4" bgcolor="{NAVY}">'
               + "".join(img(n, w=min(32, INFO[n]["w"]), align="absmiddle") for n in marquee_set)
               + "</marquee>")

    middle = (f'<tr><td align="center" width="64" bgcolor="{NAVY}">{left_cell}</td>'
              f'<td align="center" bgcolor="{MIDNIGHT}">{link_a}<br>{sparkle_bits}<br>{button}</td>'
              f'<td align="center" width="64" bgcolor="{NAVY}">{right_cell}</td></tr>')
    top = f'<tr><td colspan="3" align="center" bgcolor="{NAVY}">{top_row}</td></tr>'
    bottom = f'<tr><td colspan="3" bgcolor="{NAVY}">{marquee}</td></tr>'

    if pattern == 0:
        rows = [top, middle, bottom]
    elif pattern == 1:
        rows = [bottom, top, middle]
    elif pattern == 2:
        rows = [top, bottom, middle]
    else:
        rows = [middle, top, bottom]

    return (f'<table border="3" cellpadding="4" cellspacing="0" bgcolor="{CYAN}" width="100%">'
            + "".join(rows) + "</table>")


# ================================================================= hero builder =
def gather_gifs(cfg):
    names = []
    for theme, n in cfg["pools"]:
        names.extend(take(theme, n))
    for n in cfg["explicit"]:
        names.append(explicit(n))
    if cfg["signature"]:
        names.append(cfg["signature"])
        USED.add(cfg["signature"])
    rnd = random.Random(zlib.crc32('|'.join(names).encode()))  # stable across runs, unlike hash()
    rnd.shuffle(names)
    return names


def materials_block(pid):
    mats = FACTS[pid]["materials"]
    rows = []
    for i, m in enumerate(mats):
        rows.append(f'<tr><td bgcolor="{DEEPBLUE}" width="18">{bullet(i)}</td>'
                     f'<td bgcolor="{DEEPBLUE}">{font(m, face="Courier New", color=ICE, size=2)}</td></tr>')
    # class="materials": retro.js finds this table and rebuilds its rows from Etsy's materials
    return (f'<table class="materials" border="1" cellpadding="3" cellspacing="1" bgcolor="{STEEL}" width="230">'
            f'<tr><td colspan="2" bgcolor="{MIDNIGHT}" align="center">'
            f"{font('WHAT&#39;S INSIDE', face='Impact, Arial', color=WHITE, size=2, b=True)}</td></tr>"
            + "".join(rows) + "</table>")


def buy_link(pid, size=4):
    url = PRODUCTS[pid]["url"]
    label = font("&raquo;&raquo; BUY / VIEW ON ETSY &laquo;&laquo;", face="Comic Sans MS, Arial", color=WHITE,
                  size=size, b=True)
    return f'{arrow(0)}<a href="{url}">{label}</a>{arrow(1)}'


def title_block(pid, size=5):
    return rainbow(PRODUCTS[pid]["name"].upper(), face="Times New Roman", size=size)


def blurb_block(pid, color=ICE, size=2):
    return "<br><br>".join(font(s, face="Times New Roman", color=color, size=size) for s in BLURBS[pid])


def gif_cluster(names, maxdim=58, align=None, lazy=True):
    return "".join(thumb(n, maxdim=maxdim, hspace=4, vspace=4, align=align, lazy=lazy) for n in names)


HERO_WIDTH = 440


def hero(pid, idx):
    """One product, one tall slim table (440px wide for every listing): a small GIF strip, the
    headline, the price, the (beefed-up) buy box, the full-width photo, another GIF strip, the
    text, the materials table unchanged, then the rest of the product's GIFs. border/bgcolor still
    come from HERO_CFG so listings keep differing from each other even though the shape is now
    identical. The price sits in a [data-price] span and the photo carries data-image/class
    hooks, so retro.js can find and update them without touching anything else."""
    cfg = HERO_CFG[pid]
    gifs = gather_gifs(cfg)
    n = len(gifs)
    bgcolor = cfg["bgcolor"]
    border = cfg["border"]

    top_n = 4 if n >= 13 else 3
    mid_n = 4 if n - top_n >= 9 else 3
    top_strip = gifs[:top_n]
    mid_strip = gifs[top_n:top_n + mid_n]
    rest = gifs[top_n + mid_n:]

    photo = hero_photo(pid)
    mats = materials_block(pid)  # kept exactly as it is, per the artist
    text = blurb_block(pid)
    price = font(f'<span class="price" data-price>{price_str(pid)}</span>', face="Impact, Arial", color=GOLD,
                 size=7, b=True)

    rows = [
        f'<tr><td align="center" bgcolor="{bgcolor}">{gif_cluster(top_strip, maxdim=40)}</td></tr>',
        f'<tr><td align="center" bgcolor="{bgcolor}">{title_block(pid, size=4)}</td></tr>',
        f'<tr><td align="center" bgcolor="{bgcolor}">{price}</td></tr>',
        f'<tr><td align="center" bgcolor="{bgcolor}">{buy_box(pid, idx)}</td></tr>',
        f'<tr><td bgcolor="{bgcolor}">{photo}</td></tr>',
        f'<tr><td align="center" bgcolor="{bgcolor}">{gif_cluster(mid_strip, maxdim=40)}</td></tr>',
        f'<tr><td bgcolor="{bgcolor}">{text}</td></tr>',
        f'<tr><td align="center" bgcolor="{bgcolor}">{mats}</td></tr>',
        f'<tr><td align="center" bgcolor="{bgcolor}">{gif_cluster(rest, maxdim=40)}</td></tr>',
    ]
    return (f'<table class="hero" border="{border}" cellpadding="6" cellspacing="2" bgcolor="{STEEL}" '
            f'width="{HERO_WIDTH}" align="center">' + "".join(rows) + "</table>")


def hero_column(pids, start_idx, category):
    """All listings in one centred vertical column, one per row, with an own_divider() above and
    below each (as before) and a transparent ~24px gap between listings so the animated page
    background shows through. Each listing and the gap that precedes it (if any) share one
    <div class="listing" data-id=... data-category=...> container, so retro.js can hide a listing
    that's gone from products.json -- divider, table, gap and all -- as a single unit, leaving a
    normal single gap behind."""
    parts = []
    for i, pid in enumerate(pids):
        spacer = f'<center>{img("spacer.gif", w=1, h=24)}</center>' if i > 0 else ""
        block = f'<center>{own_divider()}{hero(pid, start_idx + i)}{own_divider()}</center>'
        parts.append(f'<div class="listing" id="listing-{pid}" data-id="{pid}" data-category="{category}">'
                     f'{spacer}{block}</div>')
    return "".join(parts)


# =================================================================== BODY ====
BODY = []


def add(html):
    BODY.append(html)


def eye_row(n=5, maxdim=26, lazy=True):
    names = take("pyramids-egypt", n)
    return "".join(thumb(nm, maxdim=maxdim, align="absmiddle", hspace=4, lazy=lazy) for nm in names)


# ---- masthead ---------------------------------------------------------------
def build_masthead():
    """Everything here is above the fold, so none of its images are lazy-loaded. The three Etsy
    facts (rating, reviews, sales, years) sit in [data-stat] spans that retro.js refreshes."""
    s = ['<center>']
    s.append(f'<table border="0" cellpadding="6" cellspacing="6"><tr valign="middle">')
    coils_left = take("tesla-electric", 4)
    coils_right = take("tesla-electric", 4)
    s.append(f'<td class="coil-cell" align="center" bgcolor="{DEEPBLUE}">'
              f'{img("tesla-coil-large.gif", w=70, lazy=False)}<br>'
              + gif_cluster(coils_left, maxdim=40, lazy=False) + '</td>')
    s.append(f'<td align="center" bgcolor="{NAVY}">')
    s.append(img("logo-white.gif", w=320, lazy=False))
    s.append('<br>')
    s.append(f'<center class="hl">{rainbow_lines(["WELCOME TO", "SCALAR ORGONE"], size=7)}</center>')
    s.append('<br>')
    s.append(font("*** TOOLS FOR JOYFUL LIVING ***", face="Courier New", color=CYAN, size=4, b=True))
    s.append(f'<br>{font("handmade in Toronto", face="Times New Roman", color=PALECYAN, size=3, i=True)}')
    intro_sentence = ("Pyramids, cloudbusters and small pieces, each one made by hand from authentic "
                       "stones, crystals, metals and powders.")
    s.append(f'<p>{font(intro_sentence, face="Times New Roman", color=WHITE, size=3)}</p>')
    s.append(eye_row(5, 24, lazy=False))
    s.append("</td>")
    s.append(f'<td class="coil-cell" align="center" bgcolor="{DEEPBLUE}">'
              f'{img("tesla-coil-small.gif", w=48, lazy=False)}<br>'
              + gif_cluster(coils_right, maxdim=40, lazy=False) + '</td>')
    s.append("</tr></table>")

    # Etsy facts table -- rating/reviews/sales/years each carry a [data-stat] hook
    s.append(f'<table border="3" cellpadding="6" bgcolor="{NAVY}" cellspacing="0"><tr>')
    egypt_icons = take("pyramids-egypt", 3)
    cells = [
        (egypt_icons[0], '<span data-stat="rating">5.0</span>',
         'STARS FROM <span data-stat="reviews">69</span> REVIEWS'),
        (egypt_icons[1], '<span data-stat="sales">195</span>', "SALES"),
        (egypt_icons[2], '<span data-stat="years">5</span>', "YEARS ON ETSY"),
    ]
    for gname, big, label in cells:
        s.append(f'<td align="center" bgcolor="{MIDNIGHT}">{thumb(gname, maxdim=34, lazy=False)}<br>'
                  f'{font(big, color=WHITE, size=5, b=True)}<br>{font(label, color=CYAN, size=1)}</td>')
    s.append("</tr></table><br>")

    # navigation
    s.append(f'<table border="2" cellpadding="6" bgcolor="{NAVY}"><tr><td align="center">')
    s.append(font("[ <a href=\"#pyramids\">PYRAMIDS</a> ] [ <a href=\"#cloudbusters\">CLOUDBUSTERS</a> ] "
                  "[ <a href=\"#accessories\">ACCESSORIES</a> ] [ <a href=\"#about\">ABOUT</a> ] "
                  "[ <a href=\"https://www.etsy.com/shop/ScalarOrgone\">OUR ETSY SHOP</a> ]",
                  face="Courier New", color=CYAN, size=2, b=True))
    s.append("</td></tr></table>")

    s.append(f'<marquee behavior="scroll" direction="left" scrollamount="5" bgcolor="{NAVY}">')
    s.append(font("*** WELCOME, WELCOME *** 5.0 STARS FROM 69 REVIEWS *** 195 SALES *** 5 YEARS ON ETSY *** "
                  "HANDMADE IN TORONTO *** PYRAMIDS * CLOUDBUSTERS * ACCESSORIES *** ", color=ICE, size=3, b=True))
    s.append("</marquee>")
    s.append(f'<marquee behavior="alternate" direction="right" scrollamount="6" bgcolor="{MIDNIGHT}">')
    s.append(gif_cluster(take("pyramids-egypt", 10), maxdim=40, lazy=False))
    s.append("</marquee>")
    s.append("</center>")
    return "".join(s)


# ---- section banners ---------------------------------------------------------
def section_banner(anchor, title, motto, theme, n, w=40):
    s = [f'<a name="{anchor}"></a><center>']
    icons = take(theme, 3)
    s.append(f'<table border="3" cellpadding="8" bgcolor="{NAVY}" width="70%"><tr><td align="center">')
    s.append("".join(thumb(x, maxdim=w, align="absmiddle") for x in icons))
    s.append(font(title, face="Impact, Arial", color=WHITE, size=6, b=True))
    s.append("".join(thumb(x, maxdim=w, align="absmiddle") for x in icons[:1]))
    s.append(f'<br>{font(motto, face="Times New Roman", color=PALECYAN, size=2, i=True)}</td></tr></table>')
    s.append("</center>")
    return "".join(s)


# ---- about --------------------------------------------------------------------
def build_about():
    s = ['<a name="about"></a><center>']
    s.append(f'<table border="4" cellpadding="10" bgcolor="{NAVY}" width="640"><tr><td align="center">')
    s.append(img("star-mark-white.gif", w=50))
    s.append(font("ABOUT SCALAR ORGONE", face="Impact, Arial", color=WHITE, size=5, b=True))
    s.append(img("star-mark-white.gif", w=50))
    s.append("<br><br>")
    s.append(img("reich-portrait.gif", w=90, align="left", hspace=10))
    s.append(font("Every ScalarOrgone piece is made by hand in Toronto using only high-quality, authentic "
                   "stones, crystals, metals and powders.", face="Times New Roman", color=ICE, size=3))
    s.append(img("tesla-lab-arcs-1899.gif", w=130, align="right", hspace=10))
    s.append('<br clear="all"><br>')
    s.append(img("tesla-coil-large.gif", w=60, align="absmiddle"))
    s.append(font(' Questions about a piece? Email <a href="mailto:scalarorgone@gmail.com">'
                   'scalarorgone@gmail.com</a>', color=CYAN, size=3))
    s.append(img("tesla-coil-small.gif", w=40, align="absmiddle"))
    s.append("<br><br>")
    s.append(f'<marquee behavior="alternate" direction="down" scrollamount="4" height="70" bgcolor="{BLACK}">')
    s.append(font("CRACKLE &middot; HUM &middot; ARC &middot; THE COIL SINGS ITS ONE NOTE &middot; ",
                   color=WHITE, size=3, b=True))
    s.append("</marquee>")
    s.append(gif_cluster(take("tesla-electric", 10), maxdim=48))
    s.append("</td></tr></table>")
    s.append("</center>")
    return "".join(s)


# ---- footer -------------------------------------------------------------------
def build_footer():
    s = ['<center>']
    s.append(f'<table border="2" cellpadding="8" bgcolor="{NAVY}" width="640"><tr><td align="center">')
    s.append(img("esoteric-homepages--dragon-blue-wings.gif", w=46, align="absmiddle"))
    s.append(font("THIS PAGE IS ALWAYS UNDER ARCANE CONSTRUCTION", face="Comic Sans MS, Arial", color=WHITE,
                   size=2, b=True))
    s.append(img("esoteric-homepages--goddess-purple-animated.gif", w=46, align="absmiddle"))
    s.append("<br>")
    s.append(gif_cluster(take("esoteric-homepages", 6), maxdim=36))
    s.append("<br><br>")

    s.append(img("counter.gif", border=2))
    s.append(f'<br>{font("YOU ARE SEEKER NO. 006419 TO VISIT THIS SHRINE", color=ICE, size=1)}<br><br>')

    s.append(img("esoteric-homepages--seal-ritual-circle.gif", w=80, align="absmiddle"))
    s.append(f' {font("SIGN MY GUESTBOOK, TRAVELLER!", color=CYAN, size=2, b=True)}<br><br>')

    s.append(f'<table border="2" cellpadding="4" bgcolor="{MIDNIGHT}"><tr><td align="center">')
    s.append(img("webring-badge.gif", border=1))
    s.append(f'<br>{font("ORDER OF THE SOLDERED PYRAMID WEBRING", color=WHITE, size=1, b=True)}'
              f'<br>{font("[ prev site | random | next site ]", color=CYAN, size=1)}</td></tr></table><br>')

    s.append(font("Best viewed with Netscape Navigator at 800x600, by candlelight, ideally during a "
                   "thunderstorm.", face="Times New Roman", color=ICE, size=2, b=True))
    s.append("<br><br>")

    s.append(f'<marquee behavior="scroll" direction="up" scrollamount="3" height="50" width="400" '
              f'bgcolor="{DEEPBLUE}">')
    s.append(font("SIGN THE GUESTBOOK -- JOIN THE WEBRING -- VISIT THE ETSY SHOP -- COME BACK SOON -- ",
                   color=PALECYAN, size=1))
    s.append("</marquee><br>")

    s.append(font("The term 'Etsy' is a trademark of Etsy, Inc. This application uses the Etsy API but is "
                   "not endorsed or certified by Etsy, Inc.", color=STEEL, size=1))
    s.append("<p>")
    s.append(font('<a href="https://www.etsy.com/shop/ScalarOrgone">Visit the Etsy Shop</a> &middot; '
                  '<a href="https://www.etsy.com/shop/ScalarOrgone#reviews">Read our Reviews</a> &middot; '
                  '<a href="terms.html">Terms &amp; Privacy</a> &middot; '
                  '<a href="mailto:scalarorgone@gmail.com">Email Us</a>', color=STEEL, size=1))
    s.append("</p>")
    s.append(font("Last updated: sometime in 1998 (probably)", color="#444477", size=1))
    s.append("<br><br>")
    s.append(img("logo-white.gif", w=160))
    s.append("</td></tr></table></center>")
    return "".join(s)


MOBILE_CSS = """
img { max-width: 100%; height: auto }
table { max-width: 100% }
@media (max-width: 760px) {
  body { margin: 0; overflow-x: hidden; background-attachment: scroll !important; background-size: 100% auto !important;
         background-repeat: repeat-y !important; background-position: center top !important }
  * { box-sizing: border-box }
  .side-eye, .coil-cell { display: none }
  .hl font { font-size: 22px }
  img { max-width: 100vw }
  marquee { width: min(340px, 92vw) !important }
  .hero, table[width="640"] { width: 100vw !important; max-width: 440px }
}
""".strip()


def build_look_toggle_90s():
    """Her ask: a small toggle, top right of the content, above the masthead -- "90s" shown as the
    current look (bold, not a link, with one small animated GIF beside it) and "MODERN" linking to
    the modern-styled page. A bordered navy table in the page's own style, nothing fancier."""
    s = [f'<table align="right" border="1" cellpadding="4" cellspacing="0" bgcolor="{NAVY}"><tr><td>']
    s.append(font("LOOK:", face="Courier New", color=CYAN, size=1, b=True))
    s.append(" ")
    s.append(font("CRISPY", face="Courier New", color=WHITE, size=1, b=True))
    s.append(" ")
    s.append(img("esoteric-homepages--burst-new-yellow.gif", align="absmiddle", lazy=False))
    s.append(" | ")
    s.append(f'<a href="modern.html">{font("MODERN", face="Courier New", color=CYAN, size=1, b=True)}</a>')
    s.append('</td></tr></table><br clear="all">')
    return "".join(s)


# ---- default GIF pools for products retro.js adds at runtime (new on Etsy, no static listing) --
# File names only, from retro/assets/ -- retro.js can't call take()/gather_gifs(), so it gets a
# small deterministic pool per category instead, embedded below as data (not code).
NEW_PRODUCT_GIF_POOLS = {
    "Pyramids": ["pyramids-egypt--pyramid-gold-sphinx.gif", "pyramids-egypt--pyramids-blue-palette.gif",
                 "pyramid-wire-cyan.gif", "pyramids-egypt--ankh-gold-precious.gif",
                 "pyramids-egypt--eye-of-horus-mystical.gif", "rosette-gold.gif",
                 "pyramids-egypt--tutankhamun-mask-gleaming.gif", "divider-hieroglyph-a.gif"],
    "Cloudbusters": ["tesla-electric--tesla-coil-golden.gif", "torus-cyan.gif",
                      "tesla-electric--lightning-strike-tall.gif", "tesla-electric--plasma-blue-final.gif",
                      "torus-electric.gif", "tesla-electric--electric-divider-bar.gif",
                      "tesla-electric--spark-gold-burst.gif", "tesla-coil-small.gif"],
    "Accessories": ["crystals-geometry--diamond-blue-cluster.gif", "crystals-geometry--jewel-gold-star-2.gif",
                     "crystals-geometry--gem-pink-diamond.gif", "star-8point-cyan.gif",
                     "crystals-geometry--crystal-ball-shimmering.gif", "bullet-spark.gif",
                     "crystals-geometry--rotating-crystal-color.gif", "triangle-prism.gif"],
}


def main():
    add('<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">')
    add("<html><head>")
    add("<title>Scalar Orgone — Tools for joyful living</title>")
    add('<meta http-equiv="Content-Type" content="text/html; charset=utf-8">')
    add('<meta name="viewport" content="width=device-width, initial-scale=1">')
    add('<meta name="description" content="Handmade orgone pyramids, cloudbusters and small pieces, made by '
        'hand in Toronto from authentic stones, crystals, metals and powders.">')
    add('<meta property="og:title" content="Scalar Orgone — Tools for joyful living">')
    add('<meta property="og:description" content="Handmade orgone pyramids, cloudbusters and small pieces, '
        'made by hand in Toronto.">')
    add('<link rel="icon" href="assets/star-mark.svg" type="image/svg+xml">')
    add('<link rel="apple-touch-icon" href="assets/apple-touch-icon.png">')
    add(f"<style>{MOBILE_CSS}</style>")
    add("</head>")
    USED.add("pyramid-grid-bg.gif")
    add(f'<body bgcolor="#000000" text="#CCE6FF" link="#00CCFF" vlink="#6688BB" alink="#FFFFFF" '
        f'style="background: #000000 url(retro/assets/pyramid-grid-bg.gif) center center / cover no-repeat fixed; '
        f'image-rendering: pixelated">')

    add('<table border="0" cellpadding="0" cellspacing="0" width="100%"><tr>')
    add(f'<td width="128" valign="top" class="side-eye" '
        f'background="{bg("third-eye-tile-128.gif", allow_animated=True)}">'
        f'{img("spacer.gif", w=128, h=1, lazy=False)}</td>')
    add('<td valign="top" align="center">')

    add(build_look_toggle_90s())
    add(build_masthead())
    add(divider())

    pyramids, cloudbusters, accessories = (by_category("Pyramids"), by_category("Cloudbusters"),
                                            by_category("Accessories"))

    add(section_banner("pyramids", "&raquo; THE PYRAMIDS &laquo;",
                        "eight faces each, hand finished, Toronto made", "pyramids-egypt", 3))
    add('<div class="listings" id="section-pyramids" data-category="Pyramids">')
    add(hero_column(pyramids, start_idx=0, category="Pyramids"))
    add('</div>')

    add(divider())
    add(section_banner("cloudbusters", "&raquo; THE CLOUDBUSTERS &laquo;",
                        "tensor rings, copper and quartz, aimed at the sky", "tesla-electric", 3))
    add('<div class="listings" id="section-cloudbusters" data-category="Cloudbusters">')
    add(hero_column(cloudbusters, start_idx=len(pyramids), category="Cloudbusters"))
    add('</div>')

    add(divider())
    add(section_banner("accessories", "&raquo; THE ACCESSORIES &laquo;",
                        "small pieces for pockets, phones and tables", "crystals-geometry", 3))
    add('<div class="listings" id="section-accessories" data-category="Accessories">')
    add(hero_column(accessories, start_idx=len(pyramids) + len(cloudbusters), category="Accessories"))
    add('</div>')

    add(divider())
    add(build_about())
    add(divider())
    add(build_footer())

    add("</td>")
    add(f'<td width="128" valign="top" class="side-eye" '
        f'background="{bg("third-eye-tile-128.gif", allow_animated=True)}">'
        f'{img("spacer.gif", w=128, h=1, lazy=False)}</td>')
    add("</tr></table>")

    # Data (not code) for retro.js: the default GIF pool it draws from when it builds a listing
    # for a product that's new on Etsy and has no static listing of its own.
    add('<script type="application/json" id="retro-gif-pools">'
        + json.dumps(NEW_PRODUCT_GIF_POOLS) + '</script>')
    add('<script src="retro/retro.js" defer></script>')
    add("</body></html>")

    html = "\n".join(BODY)
    OUT.write_text(html)

    unused = sorted(set(ALL) - USED)
    print(f"wrote {OUT}: {len(html)} bytes")
    print(f"assets referenced: {len(USED)} / {len(ALL)}; unused: {len(unused)}")

    # prune assets that ended up unused, and their SOURCES.md lines, so "every asset used" holds
    if unused:
        for name in unused:
            (ASSETS / name).unlink()
        src_path = ROOT / "SOURCES.md"
        lines = src_path.read_text().splitlines(keepends=True)
        kept = [ln for ln in lines if not any(f"retro/assets/{name} |" in ln for name in unused)]
        src_path.write_text("".join(kept))
        print(f"pruned {len(unused)} unused asset(s) and their SOURCES.md lines")


if __name__ == "__main__":
    main()
