#!/usr/bin/env python3
"""Verifies site/index.html (built by retro/build.py) against the hard numbers from the approved
mock, adapted to the repo's paths and to the artist's later GIF audit.

Run:  python3 retro/verify.py   (from the repo root, or anywhere -- paths are resolved relative
to this file)

Prints: number of different GIF files used, number of animated <img>, number of marquees,
every background= file with its frame count, any GIF with a frame under 80ms, any asset not
used, any asset missing from SOURCES.md, whether the only style= in the file is the one
permitted background/image-rendering declaration on <body>, and the total size of the page's
images in MB. Exits non-zero if a hard number fails.
"""
import re
import sys
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).parent
SITE = ROOT.parent / "site"
html = (SITE / "index.html").read_text()
assets = SITE / "retro" / "assets"

ALLOWED_ANIMATED_BG = {"third-eye-tile-128.gif"}

# The artist's GIF audit (2026-10-12, later narrowed to drop "dividers-badges" entirely): only
# these library topics, plus a fixed list of GIFs drawn for this page and a few one-off choices of
# hers (including the site's own logo/star mark), may appear on the page.
APPROVED_PREFIXES = {"tesla-electric", "pyramids-egypt", "crystals-geometry", "esoteric-homepages"}
APPROVED_UNPREFIXED = {
    "bullet-arrow-cyan.gif", "bullet-arrow-ice.gif", "bullet-eye.gif", "bullet-pyramid.gif", "bullet-spark.gif",
    "bullet-star.gif", "bullet-torus.gif", "buy-button-blue.gif", "buy-button-silver.gif", "buy-button-white.gif",
    "counter.gif", "divider-arcane-a.gif", "divider-arcane-b.gif", "divider-hieroglyph-a.gif",
    "divider-lightning-a.gif", "divider-lightning-b.gif", "pinecone-icon.gif", "pyramid-solid-ice.gif",
    "pyramid-solid-silver.gif", "pyramid-wire-cyan.gif", "pyramid-wire-gold.gif", "rosette-cyan.gif",
    "rosette-gold.gif", "spiral-maze.gif", "star-5point-ice.gif", "star-8point-cyan.gif", "tesla-coil-large.gif",
    "tesla-coil-small.gif", "tesla-lab-arcs-1899.gif", "reich-portrait.gif", "torus-cyan.gif",
    "torus-electric.gif", "torus-gold.gif", "torus-silver.gif", "torus-white.gif", "triangle-prism.gif",
    "webring-badge.gif", "pyramid-grid-bg.gif", "third-eye-tile-128.gif", "spacer.gif",
    "logo-white.gif", "star-mark-white.gif",
}

problems = []

img_srcs = re.findall(r'<img[^>]+src\s*=\s*"([^"]+)"', html, re.I)
bg_srcs = re.findall(r'\sbackground\s*=\s*"([^"]+)"', html, re.I)
local_gifs = set()
for src in img_srcs + bg_srcs:
    if src.startswith("retro/assets/"):
        local_gifs.add(src[len("retro/assets/"):])
style_url = re.search(r'url\(\s*retro/assets/([^)\s]+)\s*\)', html, re.I)
if style_url:
    local_gifs.add(style_url.group(1))

print("approved-GIF audit:")
not_approved = sorted(
    name for name in local_gifs
    if name not in APPROVED_UNPREFIXED and name.split("--", 1)[0] not in APPROVED_PREFIXES
)
if not_approved:
    for name in not_approved[:20]:
        print(f"  NOT APPROVED: {name}")
    problems.append(f"{len(not_approved)} GIF(s) on the page are outside the artist's approved set")
else:
    print("  (every GIF on the page is from an approved topic or the approved drawn/one-off list)")
if any(name.startswith("dividers-badges--") for name in local_gifs):
    problems.append("a dividers-badges GIF is on the page; the artist dropped that topic entirely")
print(f"different GIF files used (local retro/assets/): {len(local_gifs)}")

animated_img_count = 0
frame_cache = {}


def frames_of(path):
    if path not in frame_cache:
        try:
            with Image.open(path) as im:
                frame_cache[path] = getattr(im, "n_frames", 1)
        except Exception:
            frame_cache[path] = 1
    return frame_cache[path]


for src in img_srcs:
    path = (SITE / src).resolve()
    if not path.exists():
        problems.append(f"missing image referenced by <img>: {src}")
        continue
    if path.suffix.lower() == ".gif" and frames_of(path) > 1:
        animated_img_count += 1
print(f"animated <img> elements: {animated_img_count}")

marquees = re.findall(r"<marquee\b([^>]*)>", html, re.I)
print(f"marquees: {len(marquees)}")
for i, attrs in enumerate(marquees):
    direction = re.search(r'direction\s*=\s*"([^"]+)"', attrs, re.I)
    behavior = re.search(r'behavior\s*=\s*"([^"]+)"', attrs, re.I)
    amount = re.search(r'scrollamount\s*=\s*"([^"]+)"', attrs, re.I)
    print(f"  marquee {i}: direction={direction.group(1) if direction else '(default=left)'} "
          f"behavior={behavior.group(1) if behavior else '(default=scroll)'} "
          f"scrollamount={amount.group(1) if amount else '(default)'}")

print("backgrounds:")
for src in sorted(set(bg_srcs)):
    path = (SITE / src).resolve()
    name = Path(src).name
    if not path.exists():
        problems.append(f"missing background image: {src}")
        continue
    n = frames_of(path)
    print(f"  {src}  {n} frame(s)")
    if n > 1 and name not in ALLOWED_ANIMATED_BG:
        problems.append(f"background {src} is animated ({n} frames) but is not one of the allowed animated backgrounds")

style_attrs = re.findall(r'\sstyle\s*=\s*"([^"]*)"', html, re.I)
body_tag_match = re.search(r"<body\b[^>]*>", html, re.I)
body_tag = body_tag_match.group(0) if body_tag_match else ""
if len(style_attrs) != 1:
    problems.append(f"expected exactly one style= attribute in the whole file (the body background), found {len(style_attrs)}")
elif "style=" not in body_tag.lower():
    problems.append("the one style= attribute found is not on <body>")
else:
    allowed_props = {"background", "image-rendering"}
    declared = style_attrs[0]
    props = {decl.split(":", 1)[0].strip().lower() for decl in declared.split(";") if decl.strip()}
    stray = props - allowed_props
    if stray:
        problems.append(f"the body style= declares properties beyond background/image-rendering: {stray}")
    else:
        print(f"body style= OK (only {sorted(props)})")
if "retro/assets/pyramid-grid-bg.gif" not in html:
    problems.append("pyramid-grid-bg.gif is not referenced anywhere in the page (expected in the body style=)")

print("frames under 80ms:")
under80 = []
for name in sorted(local_gifs):
    path = assets / name
    if not path.exists():
        continue
    try:
        with Image.open(path) as im:
            n = getattr(im, "n_frames", 1)
            if n > 1:
                for i in range(n):
                    im.seek(i)
                    d = im.info.get("duration", 100) or 100
                    if d < 80:
                        under80.append((name, i, d))
    except Exception as e:
        problems.append(f"could not open {name}: {e}")
if under80:
    for name, i, d in under80[:20]:
        print(f"  {name} frame {i}: {d}ms")
    problems.append(f"{len(under80)} frame(s) under 80ms")
else:
    print("  (none)")

all_assets = {p.name for p in assets.glob("*.gif")}
unused = sorted(all_assets - local_gifs)
print(f"assets not used on the page: {len(unused)}")
if unused:
    for name in unused[:20]:
        print(f"  UNUSED: {name}")
    problems.append(f"{len(unused)} asset(s) in retro/assets/ not referenced on the page")

sources_text = (ROOT / "SOURCES.md").read_text()
missing_sources = sorted(name for name in all_assets
                          if f"retro/assets/{name} " not in sources_text and f"retro/assets/{name}|" not in sources_text)
print(f"assets missing from SOURCES.md: {len(missing_sources)}")
if missing_sources:
    for name in missing_sources[:20]:
        print(f"  NO SOURCE: {name}")
    problems.append(f"{len(missing_sources)} asset(s) missing a SOURCES.md line")

total_bytes = sum((assets / name).stat().st_size for name in all_assets if (assets / name).exists())
for src in set(img_srcs):
    if not src.startswith("retro/assets/"):
        path = (SITE / src).resolve()
        if path.exists():
            total_bytes += path.stat().st_size
print(f"total size of page images: {total_bytes / 1024 / 1024:.2f} MB")

print()
print("hard numbers:")
# Lower than the original mock's thresholds (230 / 420 / 4): the artist's later removal of the
# whole "dividers-badges" topic (50 GIFs) shrank the approved set, and these numbers are a
# regression guard against that smaller set, not an arbitrary target.
checks = [
    (len(local_gifs) >= 200, f"different GIF files used: {len(local_gifs)} (need >= 200)"),
    (animated_img_count >= 380, f"animated <img>: {animated_img_count} (need >= 380)"),
    (len(marquees) >= 4, f"marquees: {len(marquees)} (need >= 4)"),
]
for ok, label in checks:
    print(f"  [{'OK' if ok else 'FAIL'}] {label}")
    if not ok:
        problems.append(label)

if problems:
    print()
    print("PROBLEMS:")
    for p in problems:
        print("  -", p)
    sys.exit(1)

print()
print("OK")
