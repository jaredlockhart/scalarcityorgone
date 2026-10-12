#!/usr/bin/env python3
"""Draws the hand-made GIFs for the 90s page (site/index.html, built by retro/build.py). Pillow
only, small + chunky on purpose,
hard edges, few colours, 2-12 frames.

Per the heroes brief, hand-drawn GIFs here are ABSTRACT ONLY: toruses, wireframe pyramids and
solids, sacred geometry, dividers, bullets, the counter, lightning bars, a couple of simple
product-shape icons (triangle/star/pinecone silhouettes -- objects, not figures). No people, gods,
animals or other figures are drawn here; those come from vetted found GIFs instead, or not at all.

Much of the 3D engine and several shapes are adapted from mock 7's make_gifs.py (sanctioned by the
brief: "mock 7 is a parts bin you may read and copy from" / "mock7's [abstract ones] are fine to
reuse"). The derpy hand-drawn figures (egyptian_emblem, winged_scarab_small, egyptian_god, Thoth,
Anubis) are NOT carried over.

Rules this file must respect:
  - no GIF anywhere may use a frame shorter than 80ms.
  - BLACK AND BLUE palette: navy/midnight/electric/cyan/ice/white/silver, with gold only as a
    sparing warm accent (pyramids, Egypt).
"""
import math
import random
from pathlib import Path
from PIL import Image, ImageDraw

OUT = Path(__file__).parent.parent / "site" / "retro" / "assets"
OUT.mkdir(parents=True, exist_ok=True)

random.seed(8181)

# ---------------------------------------------------------------- black & blue palette --
BLACK = (0, 0, 0)
NAVY = (0, 0, 0x33)
MIDNIGHT = (0, 0, 0x66)
DEEPBLUE = (0, 0x10, 0x40)
DARKBLUE2 = (0x0A, 0x0A, 0x2A)
ELECTRIC = (0, 0x66, 0xFF)
CYAN = (0, 0xCC, 0xFF)
SKYBLUE = (0x33, 0x99, 0xFF)
ICE = (0xCC, 0xE6, 0xFF)
PALECYAN = (0x99, 0xCC, 0xFF)
SILVER = (0xC0, 0xC0, 0xC0)
WHITE = (255, 255, 255)
STEEL = (0x66, 0x88, 0xBB)
GOLD = (255, 204, 0)

MIN_DURATION = 90


def save(frames, path, duration=150):
    if isinstance(duration, list):
        dur = [max(MIN_DURATION, d) for d in duration]
    else:
        dur = max(MIN_DURATION, duration)
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=dur, loop=0, disposal=2)


def shade(color, delta):
    return tuple(max(0, min(255, c + delta)) for c in color)


# ---------------------------------------------------------------- 3D engine (from mock 7) --
def rot_point(p, ax, ay):
    x, y, z = p
    cy, sy = math.cos(ay), math.sin(ay)
    x, z = x * cy + z * sy, -x * sy + z * cy
    cx, sx = math.cos(ax), math.sin(ax)
    y, z = y * cx - z * sx, y * sx + z * cx
    return (x, y, z)


def project(p, size, scale, dist=3.4):
    x, y, z = p
    f = dist / (dist - z)
    return (size / 2 + x * f * scale, size / 2 + y * f * scale)


def spin_frames(points, edges, size, scale, color, n=12, tilt=0.5, tri_tone=None, bg=BLACK, width=2):
    tilted = [rot_point(p, tilt, 0) for p in points]
    frames = []
    for i in range(n):
        ang = 2 * math.pi * i / n
        img = Image.new("RGB", (size, size), bg)
        d = ImageDraw.Draw(img)
        proj = []
        for p in tilted:
            rp = rot_point(p, 0, ang)
            proj.append((project(rp, size, scale), rp[2]))
        order = sorted(range(len(edges)), key=lambda k: (proj[edges[k][0]][1] + proj[edges[k][1]][1]))
        if tri_tone:
            zs = [(proj[a][1] + proj[b][1]) / 2 for (a, b) in edges]
            zmin, zmax = min(zs), max(zs)
            span = (zmax - zmin) or 1.0
        for k in order:
            a, b = edges[k]
            (xa, ya), za = proj[a]
            (xb, yb), zb = proj[b]
            c = color
            if tri_tone:
                t = ((za + zb) / 2 - zmin) / span
                c = tri_tone[0] if t > 0.66 else (tri_tone[1] if t > 0.33 else tri_tone[2])
            d.line([(xa, ya), (xb, yb)], fill=c, width=width)
        frames.append(img)
    return frames


def torus_points(nu=16, nv=9, R=1.0, r=0.46):
    pts, idx, k = [], {}, 0
    for i in range(nu):
        u = 2 * math.pi * i / nu
        for j in range(nv):
            v = 2 * math.pi * j / nv
            x = (R + r * math.cos(v)) * math.cos(u)
            y = r * math.sin(v)
            z = (R + r * math.cos(v)) * math.sin(u)
            pts.append((x, y, z))
            idx[(i, j)] = k
            k += 1
    edges = []
    for i in range(nu):
        for j in range(nv):
            edges.append((idx[(i, j)], idx[((i + 1) % nu, j)]))
            edges.append((idx[(i, j)], idx[(i, (j + 1) % nv)]))
    return pts, edges


def pyramid_points(s=1.0, h=1.25):
    apex = (0, -h, 0)
    base = [(s, h * 0.35, s), (s, h * 0.35, -s), (-s, h * 0.35, -s), (-s, h * 0.35, s)]
    pts = [apex] + base
    edges = [(0, 1), (0, 2), (0, 3), (0, 4), (1, 2), (2, 3), (3, 4), (4, 1)]
    return pts, edges


def hex_grid_points(ring_counts=(1, 6, 12), radii=(0, 1.0, 1.9)):
    pts = [(0.0, 0.0)]
    for count, radius in zip(ring_counts[1:], radii[1:]):
        for i in range(count):
            a = 2 * math.pi * i / count
            pts.append((radius * math.cos(a), radius * math.sin(a)))
    return pts


# ----------------------------------------------------------------- toruses & pyramids --
def torus(name, size, tri_tone, nu=16, nv=9):
    pts, edges = torus_points(nu=nu, nv=nv)
    frames = spin_frames(pts, edges, size, scale=size * 0.30, color=tri_tone[0], n=16, tilt=1.05,
                          tri_tone=tri_tone, width=2)
    save(frames, OUT / name, duration=110)


def pyramid_wire(name, size, tri_tone):
    pts, edges = pyramid_points()
    frames = spin_frames(pts, edges, size, scale=size * 0.30, color=tri_tone[0], n=14, tilt=0.35,
                          tri_tone=tri_tone, width=2)
    save(frames, OUT / name, duration=110)


def pyramid_solid(name, size, colors):
    pts, _ = pyramid_points()
    faces = [(0, 1, 2), (0, 2, 3), (0, 3, 4), (0, 4, 1)]
    tilted = [rot_point(p, 0.35, 0) for p in pts]
    frames = []
    n = 14
    for i in range(n):
        ang = 2 * math.pi * i / n
        img = Image.new("RGB", (size, size), BLACK)
        d = ImageDraw.Draw(img)
        proj = [(project(rot_point(p, 0, ang), size, size * 0.32), rot_point(p, 0, ang)[2]) for p in tilted]
        order = sorted(range(len(faces)), key=lambda k: sum(proj[v][1] for v in faces[k]))
        for k in order:
            face = faces[k]
            sh = colors[0] if k % 2 == 0 else colors[1]
            poly = [proj[v][0] for v in face]
            d.polygon(poly, outline=BLACK, fill=sh)
        frames.append(img)
    save(frames, OUT / name, duration=110)


def rosette(name, ring_color=(ICE, CYAN), accent=ELECTRIC):
    size = 72
    n = 12
    frames = []
    for i in range(n):
        ang0 = 2 * math.pi * i / n
        img = Image.new("RGB", (size, size), BLACK)
        d = ImageDraw.Draw(img)
        cx = cy = size // 2
        R = size * 0.32
        for j in range(12):
            a = ang0 + 2 * math.pi * j / 12
            px = cx + R * math.cos(a)
            py = cy + R * math.sin(a)
            c = ring_color[0] if j % 2 == 0 else ring_color[1]
            d.ellipse([px - 7, py - 7, px + 7, py + 7], outline=c, width=2)
        d.ellipse([cx - 6, cy - 6, cx + 6, cy + 6], outline=accent, width=2)
        frames.append(img)
    save(frames, OUT / name, duration=110)


# ---------------------------------------------------------- sacred geometry --
def flower_of_life(name="flower-of-life.gif"):
    size = 96
    cx = cy = size / 2
    r = size * 0.155
    centers = hex_grid_points()
    ring_color = [ICE] + [CYAN] * 6 + [ELECTRIC] * 12
    frames = []
    for shown in range(1, len(centers) + 1):
        img = Image.new("RGB", (size, size), BLACK)
        d = ImageDraw.Draw(img)
        for idx, (x, y) in enumerate(centers[:shown]):
            px, py = cx + x * r * 2, cy + y * r * 2
            d.ellipse([px - r, py - r, px + r, py + r], outline=ring_color[idx], width=2)
        frames.append(img)
    for _ in range(4):
        frames.append(frames[-1])
    save(frames, OUT / name, duration=170)


def seed_of_life(name="seed-of-life.gif"):
    size = 96
    cx = cy = size / 2
    r = size * 0.21
    centers = hex_grid_points(ring_counts=(1, 6), radii=(0, 1.0))
    colors = [CYAN, WHITE, ELECTRIC]
    frames = []
    for c in colors:
        img = Image.new("RGB", (size, size), BLACK)
        d = ImageDraw.Draw(img)
        for (x, y) in centers:
            px, py = cx + x * r * 1.8, cy + y * r * 1.8
            d.ellipse([px - r, py - r, px + r, py + r], outline=c, width=2)
        frames.append(img)
    save(frames, OUT / name, duration=230)


def metatron_cube(name="metatron-cube.gif"):
    size = 96
    cx = cy = size / 2
    R = size * 0.30
    pts2d = [(0.0, 0.0)]
    for i in range(6):
        a = 2 * math.pi * i / 6
        pts2d.append((R * math.cos(a), R * math.sin(a)))
    for i in range(6):
        a = 2 * math.pi * i / 6 + math.pi / 6
        pts2d.append((R * 1.9 * math.cos(a), R * 1.9 * math.sin(a)))
    n = 10
    frames = []
    for f in range(n):
        ang = 2 * math.pi * f / n
        img = Image.new("RGB", (size, size), BLACK)
        d = ImageDraw.Draw(img)
        proj = []
        for (x, y) in pts2d:
            ca, sa = math.cos(ang), math.sin(ang)
            rx, ry = x * ca - y * sa, x * sa + y * ca
            proj.append((cx + rx, cy + ry))
        for i in range(len(proj)):
            for j in range(i + 1, len(proj)):
                c = CYAN if (i + j) % 2 == 0 else ELECTRIC
                d.line([proj[i], proj[j]], fill=c)
        for (px, py) in proj:
            d.ellipse([px - 5, py - 5, px + 5, py + 5], outline=ICE, width=2)
        frames.append(img)
    save(frames, OUT / name, duration=140)


def vesica_piscis(name="vesica-piscis.gif"):
    size = 96
    r = size * 0.30
    cy = size / 2
    colors = [CYAN, WHITE, ELECTRIC]
    frames = []
    for c in colors:
        img = Image.new("RGB", (size, size), BLACK)
        d = ImageDraw.Draw(img)
        d.ellipse([size / 2 - r * 1.6, cy - r, size / 2 - r * 1.6 + 2 * r, cy + r], outline=c, width=2)
        d.ellipse([size / 2 + r * 0.4, cy - r, size / 2 + r * 0.4 + 2 * r, cy + r], outline=c, width=2)
        frames.append(img)
    save(frames, OUT / name, duration=270)


def pentagram(name="pentagram.gif"):
    size = 96
    cx = cy = size / 2
    R = size * 0.42
    n = 12
    frames = []
    for f in range(n):
        ang = 2 * math.pi * f / n
        img = Image.new("RGB", (size, size), BLACK)
        d = ImageDraw.Draw(img)
        pts = []
        for i in range(5):
            a = ang - math.pi / 2 + 2 * math.pi * i / 5
            pts.append((cx + R * math.cos(a), cy + R * math.sin(a)))
        order = [0, 2, 4, 1, 3, 0]
        d.line([pts[i] for i in order], fill=CYAN, width=2)
        frames.append(img)
    save(frames, OUT / name, duration=120)


def spiral_maze(name="spiral-maze.gif"):
    """A simple square spiral maze, drawing itself inward -- for the Silver Labyrinth pyramid."""
    size = 96
    frames = []
    steps_total = 9
    for shown in range(2, steps_total + 1):
        img = Image.new("RGB", (size, size), BLACK)
        d = ImageDraw.Draw(img)
        cx, cy = size / 2, size / 2
        x, y = cx, cy
        step = 4
        length = 6
        direction = 0  # 0=right,1=down,2=left,3=up
        pts = [(x, y)]
        for i in range(shown):
            if direction == 0:
                x += length
            elif direction == 1:
                y += length
            elif direction == 2:
                x -= length
            else:
                y -= length
            pts.append((x, y))
            direction = (direction + 1) % 4
            if i % 2 == 1:
                length += step
        c = SILVER if shown % 2 == 0 else ICE
        d.line(pts, fill=c, width=2)
        d.ellipse([cx - 3, cy - 3, cx + 3, cy + 3], fill=CYAN)
        frames.append(img)
    for _ in range(3):
        frames.append(frames[-1])
    save(frames, OUT / name, duration=180)


def star_points_icon(name, points, color, size=48, fill=None):
    """A simple N-pointed rotating star outline -- an object/shape, not a figure."""
    frames = []
    n = 10
    for f in range(n):
        ang = 2 * math.pi * f / n * 0.3
        img = Image.new("RGB", (size, size), BLACK)
        d = ImageDraw.Draw(img)
        cx = cy = size / 2
        R = size * 0.42
        r = size * 0.18
        pts = []
        for i in range(points * 2):
            rad = R if i % 2 == 0 else r
            a = ang + math.pi * i / points - math.pi / 2
            pts.append((cx + rad * math.cos(a), cy + rad * math.sin(a)))
        if fill:
            d.polygon(pts, outline=color, fill=fill)
        else:
            d.polygon(pts, outline=color)
        frames.append(img)
    save(frames, OUT / name, duration=130)


def pinecone_icon(name="pinecone-icon.gif"):
    """A simple layered pinecone silhouette (an object, not a figure), bronze/silver scales."""
    w, h = 40, 56
    frames = []
    colors = [SILVER, STEEL, ICE]
    for ci in range(3):
        img = Image.new("RGB", (w, h), BLACK)
        d = ImageDraw.Draw(img)
        base_c = colors[ci]
        d.polygon([(w / 2, 2), (w - 6, h - 10), (6, h - 10)], outline=base_c)
        rows = 6
        for row in range(rows):
            y = 10 + row * 7
            width_here = 4 + row * 2.6
            offset = 6 if row % 2 == 0 else 0
            for sx in range(-int(width_here), int(width_here) + 1, 8):
                px = w / 2 + sx + offset * (1 if sx > 0 else -1) * 0
                d.polygon([(px, y), (px - 4, y + 7), (px + 4, y + 7)], outline=shade(base_c, -30))
        frames.append(img)
    save(frames, OUT / name, duration=200)


def triangle_prism_icon(name="triangle-prism.gif"):
    """A holographic-looking triangle, colour-cycling -- for the triangle sticker."""
    w, h = 48, 44
    cycle = [CYAN, ICE, ELECTRIC, WHITE, SKYBLUE]
    frames = []
    for c in cycle:
        img = Image.new("RGB", (w, h), BLACK)
        d = ImageDraw.Draw(img)
        d.polygon([(w / 2, 2), (w - 4, h - 4), (4, h - 4)], outline=c, width=2)
        d.polygon([(w / 2, 14), (w - 12, h - 10), (12, h - 10)], outline=shade(c, -40))
        frames.append(img)
    save(frames, OUT / name, duration=160)


# ------------------------------------------------------------------ dividers --
def arcane_divider(name="divider-arcane.gif"):
    w, h = 400, 14
    glyphs = ["tri", "circ", "eye", "x"]
    colors = [ICE, CYAN, ELECTRIC, WHITE]
    frames = []
    for shift in range(4):
        img = Image.new("RGB", (w, h), BLACK)
        d = ImageDraw.Draw(img)
        x = 4
        i = shift
        while x < w - 10:
            g = glyphs[i % len(glyphs)]
            c = colors[i % len(colors)]
            cy = h // 2
            if g == "tri":
                d.polygon([(x, cy + 5), (x + 5, cy - 5), (x + 10, cy + 5)], outline=c)
            elif g == "circ":
                d.ellipse([x, cy - 5, x + 10, cy + 5], outline=c)
            elif g == "eye":
                d.line([x, cy, x + 10, cy], fill=c)
                d.point((x + 5, cy), fill=c)
            else:
                d.line([x, cy - 5, x + 10, cy + 5], fill=c)
                d.line([x, cy + 5, x + 10, cy - 5], fill=c)
            x += 18
            i += 1
        frames.append(img)
    save(frames, OUT / name, duration=220)


def lightning_divider(name="divider-lightning.gif", w=400):
    h = 18
    frames = []
    for f in range(4):
        img = Image.new("RGB", (w, h), BLACK)
        d = ImageDraw.Draw(img)
        y = h // 2
        x = 0
        pts = [(0, y)]
        while x < w:
            x += random.randint(14, 26)
            y = h // 2 + random.choice([-6, -2, 2, 6])
            pts.append((min(x, w), y))
        pts.append((w, h // 2))
        c = WHITE if f % 2 == 0 else CYAN
        d.line(pts, fill=c, width=2)
        d.line(pts, fill=ELECTRIC, width=1)
        frames.append(img)
    save(frames, OUT / name, duration=130)


def hieroglyph_strip_divider(name="divider-hieroglyph.gif"):
    w, h = 400, 20
    glyphs = ["ankh", "eye", "bird", "wave", "sun"]
    frames = []
    for shift in range(3):
        img = Image.new("RGB", (w, h), BLACK)
        d = ImageDraw.Draw(img)
        x = 4
        i = shift
        while x < w - 16:
            g = glyphs[i % len(glyphs)]
            c = SILVER if i % 2 == 0 else CYAN
            cy = h // 2
            if g == "ankh":
                d.ellipse([x + 4, cy - 8, x + 11, cy - 1], outline=c, width=1)
                d.line([x + 7, cy - 1, x + 7, cy + 8], fill=c, width=1)
                d.line([x + 2, cy + 2, x + 12, cy + 2], fill=c, width=1)
            elif g == "eye":
                d.line([x + 1, cy, x + 14, cy], fill=c, width=1)
                d.polygon([(x + 7, cy - 5), (x + 11, cy), (x + 7, cy + 5)], outline=c)
            elif g == "bird":
                d.line([x + 1, cy + 3, x + 7, cy - 4], fill=c, width=1)
                d.line([x + 7, cy - 4, x + 14, cy + 3], fill=c, width=1)
                d.line([x + 7, cy - 4, x + 7, cy + 6], fill=c, width=1)
            elif g == "wave":
                d.arc([x, cy - 4, x + 8, cy + 4], 0, 180, fill=c)
                d.arc([x + 6, cy - 4, x + 14, cy + 4], 0, 180, fill=c)
            else:
                d.ellipse([x + 3, cy - 6, x + 12, cy + 3], outline=c)
                for a in range(0, 360, 45):
                    rx = x + 7 + 7 * math.cos(math.radians(a))
                    ry = cy - 1 + 7 * math.sin(math.radians(a))
                    d.point((rx, ry), fill=c)
            x += 20
            i += 1
        frames.append(img)
    save(frames, OUT / name, duration=220)


# ------------------------------------------------------------------ bullets --
def bullet_variant(name, kind, color):
    size = 14
    frames = []
    n = 6
    for i in range(n):
        img = Image.new("RGB", (size, size), BLACK)
        d = ImageDraw.Draw(img)
        cx = cy = size // 2
        if kind == "torus":
            w = 10 - abs((i % n) - n // 2) * 2
            d.ellipse([cx - w // 2, cy - 4, cx + w // 2, cy + 4], outline=color)
        elif kind == "pyramid":
            off = (i % n) - n // 2
            d.polygon([(cx + off, 1), (1, size - 2), (size - 2, size - 2)], outline=color)
        elif kind == "eye":
            closed = 1.0 if i == n - 1 else 0.0
            if closed:
                d.line([2, cy, size - 2, cy], fill=color)
            else:
                d.arc([1, 2, size - 2, size - 2], 200, 340, fill=color)
                d.arc([1, 2, size - 2, size - 2], 20, 160, fill=color)
                d.point((cx, cy), fill=WHITE)
        elif kind == "spark":
            l = 3 + (i % 3)
            d.line([(cx - l, cy), (cx + l, cy)], fill=color)
            d.line([(cx, cy - l), (cx, cy + l)], fill=color)
        frames.append(img)
    save(frames, OUT / name, duration=160)


def bullet_star(name="bullet-star.gif"):
    size = 14
    colors = [WHITE, CYAN, ICE, ELECTRIC]
    frames = []
    for c in colors:
        img = Image.new("RGB", (size, size), BLACK)
        d = ImageDraw.Draw(img)
        cx = cy = size // 2
        d.line([(cx, 0), (cx, size - 1)], fill=c)
        d.line([(0, cy), (size - 1, cy)], fill=c)
        d.line([(2, 2), (size - 3, size - 3)], fill=c)
        d.line([(2, size - 3), (size - 3, 2)], fill=c)
        d.point((cx, cy), fill=WHITE)
        frames.append(img)
    save(frames, OUT / name, duration=150)


def bullet_arrow(name="bullet-arrow.gif", color=CYAN):
    size = 16
    frames = []
    for off in (-2, 0, 2, 0):
        img = Image.new("RGB", (size, size), BLACK)
        d = ImageDraw.Draw(img)
        cy = size // 2
        d.line([(1, cy), (size - 5 + off, cy)], fill=color, width=2)
        d.polygon([(size - 6 + off, cy - 4), (size - 1 + off, cy), (size - 6 + off, cy + 4)], fill=color)
        frames.append(img)
    save(frames, OUT / name, duration=150)


# ---------------------------------------------------------- unchanged furniture --
def counter(name="counter.gif", digits="006419"):
    dw, dh = 10, 16
    pad = 2
    w = dw * len(digits) + pad * (len(digits) + 1)
    h = dh + pad * 2
    SEG = {
        "0": "abcdef", "1": "bc", "2": "abged", "3": "abgcd",
        "4": "fgbc", "5": "afgcd", "6": "afgedc", "7": "abc",
        "8": "abcdefg", "9": "abcfgd",
    }

    def draw_digit(d, ch, ox, oy, color):
        segs = SEG[ch]
        x0, y0 = ox, oy
        x1, y1 = ox + dw, oy + dh
        ym = oy + dh // 2
        if "a" in segs:
            d.line([(x0, y0), (x1, y0)], fill=color)
        if "g" in segs:
            d.line([(x0, ym), (x1, ym)], fill=color)
        if "d" in segs:
            d.line([(x0, y1), (x1, y1)], fill=color)
        if "f" in segs:
            d.line([(x0, y0), (x0, ym)], fill=color)
        if "e" in segs:
            d.line([(x0, ym), (x0, y1)], fill=color)
        if "b" in segs:
            d.line([(x1, y0), (x1, ym)], fill=color)
        if "c" in segs:
            d.line([(x1, ym), (x1, y1)], fill=color)

    frames = []
    for on in (True, False):
        img = Image.new("RGB", (w, h), (6, 6, 14))
        d = ImageDraw.Draw(img)
        color = CYAN if on else shade(CYAN, -140)
        x = pad
        for ch in digits:
            draw_digit(d, ch, x, pad, color)
            x += dw + pad
        frames.append(img)
    save(frames, OUT / name, duration=600)


def webring_badge(name="webring-badge.gif"):
    size = 32
    frames = []
    steps = 8
    for i in range(steps):
        img = Image.new("RGB", (size, size), NAVY)
        d = ImageDraw.Draw(img)
        cx = cy = size // 2
        d.ellipse([3, 3, size - 4, size - 4], outline=CYAN)
        ang = (i / steps) * 2 * math.pi
        px = cx + int((size // 2 - 4) * math.cos(ang))
        py = cy + int((size // 2 - 4) * math.sin(ang) * 0.5)
        d.ellipse([px - 2, py - 2, px + 2, py + 2], fill=WHITE)
        d.point((cx, cy), fill=WHITE)
        frames.append(img)
    save(frames, OUT / name, duration=110)


def tesla_coil(name, size):
    w, h = size
    frames = []
    cx = w // 2
    top_y = int(h * 0.18)
    base_y = h - 6
    for fi in range(5):
        img = Image.new("RGB", (w, h), BLACK)
        d = ImageDraw.Draw(img)
        d.rectangle([cx - w * 0.28, base_y - 8, cx + w * 0.28, base_y], outline=SILVER, fill=DARKBLUE2)
        coil_w = w * 0.16
        rings = 10
        for i in range(rings):
            y = base_y - 10 - i * ((base_y - 10 - top_y) / rings)
            d.ellipse([cx - coil_w, y - 3, cx + coil_w, y + 3], outline=SKYBLUE)
        d.line([(cx, top_y), (cx, base_y - 10)], fill=STEEL, width=2)
        d.ellipse([cx - w * 0.30, top_y - h * 0.10, cx + w * 0.30, top_y + h * 0.10], outline=SILVER, width=3)
        n_arcs = 3 + (fi % 3)
        for a in range(n_arcs):
            ang = random.uniform(0, 2 * math.pi)
            length = random.uniform(h * 0.18, h * 0.34)
            x0 = cx + math.cos(ang) * w * 0.26
            y0 = top_y
            pts = [(x0, y0)]
            steps = 4
            for s in range(1, steps + 1):
                nx = x0 + math.cos(ang) * length * (s / steps) + random.uniform(-6, 6)
                ny = y0 - length * (s / steps) * 0.4 + random.uniform(-4, 4)
                pts.append((nx, ny))
            c = WHITE if a % 2 == 0 else CYAN
            d.line(pts, fill=c, width=1)
        frames.append(img)
    save(frames, OUT / name, duration=110)


def danger_sign(name="danger-sign.gif"):
    w, h = 96, 72
    frames = []
    for fi in range(4):
        img = Image.new("RGB", (w, h), BLACK)
        d = ImageDraw.Draw(img)
        d.rectangle([2, 2, w - 3, h - 3], outline=WHITE, width=3)
        d.rectangle([6, 6, w - 7, h - 7], outline=ELECTRIC, width=1)
        d.polygon([(w / 2 - 4, 10), (w / 2 + 6, 10), (w / 2 - 2, 26), (w / 2 + 4, 26), (w / 2 - 8, 44),
                   (w / 2 - 2, 28), (w / 2 - 8, 28)], fill=CYAN if fi % 2 == 0 else WHITE)
        d.text((8, 46), "DANGER", fill=WHITE)
        d.text((4, 58), "HIGH VOLTAGE", fill=ICE)
        if fi % 2 == 1:
            for _ in range(5):
                sx, sy = random.randint(4, w - 4), random.randint(4, 44)
                d.point((sx, sy), fill=WHITE)
        frames.append(img)
    save(frames, OUT / name, duration=160)


def spacer_gif():
    img = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
    img.save(OUT / "spacer.gif", transparency=0)


# ---------------------------------------------------------- buy buttons (per the artist's ask) --
from PIL import ImageFont

_BUTTON_FONT = ImageFont.load_default(size=16)


def buy_button(name, label, face, shadow, text_color, w=200, h=44):
    """A chunky bevelled 90s button, also a link: a 3-frame shine sweeps down the face so every
    frame is pixel-distinct (identical frames get silently merged by the GIF encoder). face/
    shadow/text_color are RGB tuples; label is plain text (no logo)."""
    shine_ys = [6, h // 2, h - 8]
    frames = []
    for fi in range(3):
        img = Image.new("RGB", (w, h), face)
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, w - 1, h - 1], outline=BLACK)
        d.line([(1, 1), (w - 2, 1)], fill=WHITE, width=2)
        d.line([(1, 1), (1, h - 2)], fill=WHITE, width=2)
        d.line([(1, h - 2), (w - 2, h - 2)], fill=shadow, width=2)
        d.line([(w - 2, 1), (w - 2, h - 2)], fill=shadow, width=2)
        bbox = d.textbbox((0, 0), label, font=_BUTTON_FONT)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        d.text(((w - tw) / 2, (h - th) / 2 - bbox[1]), label, fill=text_color, font=_BUTTON_FONT)
        d.line([(5, shine_ys[fi]), (w - 5, shine_ys[fi])], fill=WHITE, width=1)
        frames.append(img)
    save(frames, OUT / name, duration=160)


def main():
    spacer_gif()

    # toruses: cyan/ice/electric tri-tone, four distinct colourways so cloudbuster/accessory
    # heroes each get their own (brief: "do not reuse a GIF in two heroes")
    torus("torus-cyan.gif", 64, (CYAN, ICE, DEEPBLUE))
    torus("torus-electric.gif", 64, (ELECTRIC, SKYBLUE, NAVY))
    torus("torus-silver.gif", 60, (SILVER, ICE, DARKBLUE2))
    torus("torus-white.gif", 56, (WHITE, PALECYAN, MIDNIGHT))
    torus("torus-gold.gif", 58, (GOLD, SILVER, DARKBLUE2))

    pyramid_wire("pyramid-wire-cyan.gif", 64, (CYAN, ELECTRIC, DEEPBLUE))
    pyramid_wire("pyramid-wire-gold.gif", 60, (GOLD, STEEL, DARKBLUE2))
    pyramid_solid("pyramid-solid-silver.gif", 56, (SILVER, STEEL))
    pyramid_solid("pyramid-solid-ice.gif", 52, (ICE, PALECYAN))

    rosette("rosette-cyan.gif", (ICE, CYAN), ELECTRIC)
    rosette("rosette-gold.gif", (GOLD, STEEL), SILVER)

    flower_of_life()
    seed_of_life()
    metatron_cube()
    vesica_piscis()
    pentagram()
    spiral_maze()

    star_points_icon("star-8point-cyan.gif", 8, CYAN)
    star_points_icon("star-5point-ice.gif", 5, ICE, fill=None)
    pinecone_icon()
    triangle_prism_icon()

    arcane_divider("divider-arcane-a.gif")
    arcane_divider("divider-arcane-b.gif")
    lightning_divider("divider-lightning-a.gif")
    lightning_divider("divider-lightning-b.gif", w=300)
    hieroglyph_strip_divider("divider-hieroglyph-a.gif")

    bullet_variant("bullet-torus.gif", "torus", CYAN)
    bullet_variant("bullet-pyramid.gif", "pyramid", GOLD)
    bullet_variant("bullet-eye.gif", "eye", ICE)
    bullet_variant("bullet-spark.gif", "spark", ELECTRIC)
    bullet_star()
    bullet_arrow("bullet-arrow-cyan.gif", CYAN)
    bullet_arrow("bullet-arrow-ice.gif", ICE)

    counter()
    webring_badge()
    tesla_coil("tesla-coil-large.gif", (90, 130))
    tesla_coil("tesla-coil-small.gif", (48, 70))
    danger_sign()

    # three buy-button variants (drawn for this mock, per the artist's "beef up the buy link" ask)
    buy_button("buy-button-blue.gif", "BUY NOW", ELECTRIC, NAVY, WHITE)
    buy_button("buy-button-white.gif", "VIEW ON ETSY", WHITE, SILVER, NAVY)
    buy_button("buy-button-silver.gif", "CLICK TO ADOPT THIS ONE", SILVER, STEEL, NAVY, w=220)

    print("make_gifs.py: done")


if __name__ == "__main__":
    main()
