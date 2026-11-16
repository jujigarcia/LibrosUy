"""Rasterizes the LibrosUy icon (same design as frontend/public/favicon.svg) to PNG/ICO.

Uso (requiere Pillow): python frontend/scripts/make_icons.py frontend/public
"""
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(sys.argv[1])
VIOLET = (126, 34, 206, 255)
WHITE = (255, 255, 255, 255)
YELLOW = (254, 240, 138, 255)
SS = 8  # supersampling factor for smooth edges


def arc(cx, cy, r, a0, a1, steps=12):
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / steps)),
             cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / steps))) for i in range(steps + 1)]


# Book pages in the 24-unit lucide coordinate system (same paths as the SVG)
LEFT = [(2, 3), (8, 3)] + arc(8, 7, 4, -90, 0) + [(12, 21)] + arc(9, 21, 3, 0, -90)[1:] + [(2, 18), (2, 3)]
RIGHT = [(22, 3), (16, 3)] + arc(16, 7, 4, -90, -180) + [(12, 21)] + arc(15, 21, 3, 180, 270)[1:] + [(22, 18), (22, 3)]


def polyline(draw, pts, width, color):
    draw.line(pts, fill=color, width=width, joint="curve")
    r = width / 2
    for x, y in (pts[0], pts[-1]):
        draw.ellipse([x - r, y - r, x + r, y + r], fill=color)


PINK = (251, 207, 232)
LILAC = (216, 180, 254)
INK = (55, 65, 81, 255)


def gradient(S):
    """Diagonal pink -> lilac gradient, like the home page background."""
    img = Image.new("RGBA", (S, S))
    px = img.load()
    for y in range(S):
        for x in range(S):
            t = (x + y) / (2 * (S - 1))
            px[x, y] = tuple(round(PINK[i] + (LILAC[i] - PINK[i]) * t) for i in range(3)) + (255,)
    return img


def render(size, rounded):
    S = size * SS
    k = S / 64  # 64-unit icon space
    bg = gradient(S)
    if rounded:
        mask = Image.new("L", (S, S), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, S - 1, S - 1], radius=14 * k, fill=255)
        img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        img.paste(bg, (0, 0), mask)
    else:
        img = bg  # full bleed: iOS/Android apply their own mask

    # Book on its own layer, centered, then rotated 30deg (clockwise) like the SVG
    layer = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)

    def book(p):  # translate(12.2 12.2) scale(1.65)
        return [((12.2 + x * 1.65) * k, (12.2 + y * 1.65) * k) for x, y in p]

    w = max(1, round(2 * 1.65 * k))
    polyline(d, book(LEFT), w, INK)
    polyline(d, book(RIGHT), w, INK)
    layer = layer.rotate(-30, resample=Image.BICUBIC, center=(S / 2, S / 2))
    img = Image.alpha_composite(img, layer)
    return img.resize((size, size), Image.LANCZOS)


for name, size, rounded in [("favicon-32.png", 32, True), ("apple-touch-icon.png", 180, False),
                            ("icon-192.png", 192, False), ("icon-512.png", 512, False)]:
    render(size, rounded).save(OUT / name, optimize=True)
    print("ok", name)

# Multi-size .ico for old browsers / Windows shortcuts
render(64, True).save(OUT / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])
print("ok favicon.ico")
