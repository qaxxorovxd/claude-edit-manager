"""Umumiy motion-dizayn yordamchilari (motion.py ustiga): 3D matn, harfma-harf animatsiya, nur, halqa,
HUD qavslar, shisha yorliqlar, chiziqli ikonkalar, gradientlar, perspektiva, animatsiyali fon.

Loyihalarning build.py fayllari shu yerdan import qiladi.
"""
import math
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from motion import (H, W, WHITE, add_shadow, clamp, ease_out_cubic, font, from_alpha, glass, paste, prog,
                    ss_shape, text_img)

BLUE, CYAN, ORANGE, NAVY, AMBER = (40, 123, 255), (0, 217, 255), (255, 138, 36), (16, 24, 40), (255, 178, 64)
F_XB, F_BLK, F_B, F_UI, F_UIM, F_NUM = "mont:ExtraBold", "mont:Black", "mont:Bold", "inter:SemiBold", "inter:Medium", "grot:Bold"

_cache = {}


def padded(im, p):
    out = Image.new("RGBA", (im.width + 2 * p, im.height + 2 * p), (0, 0, 0, 0))
    out.alpha_composite(im, (p, p))
    return out


def fade(im, a):
    if a >= 0.999:
        return im
    im = im.copy()
    im.putalpha(im.getchannel("A").point(lambda v: int(v * a)))
    return im


def gradient(w, h, c0=BLUE, c1=CYAN, diag=True):
    x = np.linspace(0, 1, w)[None, :, None]
    y = np.linspace(0, 1, h)[:, None, None]
    k = np.clip(x * 0.6 + y * 0.4, 0, 1) if diag else np.broadcast_to(x, (h, w, 1))
    arr = (np.array(c0) * (1 - k) + np.array(c1) * k).astype(np.uint8)
    return Image.fromarray(np.concatenate([arr, np.full((h, w, 1), 255, np.uint8)], 2), "RGBA")


def grad_fill(alpha, c0, c1, vertical=True):
    w, h = alpha.size
    k = np.linspace(0, 1, h)[:, None, None] if vertical else np.linspace(0, 1, w)[None, :, None]
    arr = np.broadcast_to(np.array(c0) * (1 - k) + np.array(c1) * k, (h, w, 3)).astype(np.uint8)
    im = Image.fromarray(np.ascontiguousarray(arr)).convert("RGBA")
    im.putalpha(alpha)
    return im


def rounded(im, r):
    from motion import rounded_mask
    im = im.convert("RGBA")
    im.putalpha(rounded_mask(im.width, im.height, r))
    return im


def extrude(text, size, face=WHITE, face2=None, side=(14, 52, 140), depth=9, fname=F_BLK, shadow=0.5):
    """Hajmli (3D) matn: orqa qatlamlar diagonal siljigan, old yuzasi bir rang yoki vertikal gradient."""
    key = ("ex", text, size, face, face2, side, depth, fname, shadow)
    if key in _cache:
        return _cache[key]
    f = font(fname, size)
    asc, desc = f.getmetrics()
    pad = int(size * 0.35) + depth
    w, h = int(f.getlength(text)) + 2 * pad, asc + desc + 2 * pad
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).text((pad, pad + asc), text, font=f, fill=255, anchor="ls")
    im = Image.new("RGBA", (w + depth, h + depth), (0, 0, 0, 0))
    for k in range(depth, 0, -1):
        shade = tuple(int(c * (0.55 + 0.45 * (1 - k / depth))) for c in side)
        im.alpha_composite(from_alpha(mask, shade), (k, k))
    im.alpha_composite(grad_fill(mask, face, face2) if face2 else from_alpha(mask, face), (0, 0))
    out = add_shadow(padded(im, 40), size * 0.08, (0, size * 0.07), shadow) if shadow else padded(im, 40)
    _cache[key] = out
    return out


def letter_line(c, t, t0, text, size, cx, cy, stagger=0.028, dur=0.32, rise=60, spread=0.0, a=1.0, **kw):
    """Harfma-harf ko'tarilib chiqadigan 3D matn. spread — harflar orasiga qo'shimcha masofa (px, markazdan)."""
    f = font(kw.get("fname", F_BLK), size)
    widths = [f.getlength(ch) for ch in text]
    total = sum(widths)
    x = cx - total / 2
    n = len(text)
    for i, ch in enumerate(text):
        cw = widths[i]
        p = prog(t, t0 + i * stagger, dur)
        if p > 0 and ch != " ":
            img = extrude(ch, size, **kw)
            sc = 1.25 - 0.25 * ease_out_cubic(p)
            off = (i - (n - 1) / 2) * spread
            paste(c, img, x + cw / 2 + kw.get("depth", 9) / 2 + off, cy + (1 - ease_out_cubic(p)) * rise, sc,
                  clamp(p * 2.5) * a, (i - (n - 1) / 2) * spread * 0.04)
        x += cw


def ring(c, x, y, r, width, col, a):
    if a <= 0.01 or r <= 1:
        return
    im = ss_shape(2 * r + 20, 2 * r + 20, lambda d, s: d.ellipse(
        (10 * s, 10 * s, (2 * r + 10) * s, (2 * r + 10) * s), outline=tuple(col) + (255,), width=max(1, int(width * s))), ss=2)
    paste(c, im, x, y, 1, a)


def soft_glow(c, x, y, rx, ry, col, a):
    if a <= 0.01:
        return
    key = ("glow", int(rx), int(ry), tuple(col))
    if key not in _cache:
        rx, ry = int(rx), int(ry)
        yy, xx = np.mgrid[0:2 * ry, 0:2 * rx].astype(np.float32)
        g = np.exp(-(((xx - rx) / (rx * 0.5)) ** 2 + ((yy - ry) / (ry * 0.5)) ** 2))
        im = Image.new("RGBA", (2 * rx, 2 * ry), tuple(col) + (0,))
        im.putalpha(Image.fromarray((g * 255).astype(np.uint8)))
        _cache[key] = im
    paste(c, _cache[key], x, y, 1, a)


def brackets(c, box, p, col=CYAN, arm=64, wd=6, a=1.0):
    if p <= 0 or a <= 0.01:
        return
    x0, y0, x1, y1 = box
    L = arm * ease_out_cubic(p)
    ov = Image.new("RGBA", (int(x1 - x0) + 40, int(y1 - y0) + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    ox, oy = x0 - 20, y0 - 20
    colr = tuple(col) + (int(255 * a),)
    for (cx, cy, sx, sy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
        px, py = cx - ox, cy - oy
        d.line((px, py, px + sx * L, py), fill=colr, width=wd)
        d.line((px, py, px, py + sy * L), fill=colr, width=wd)
    c.alpha_composite(ov.filter(ImageFilter.GaussianBlur(8)), (int(ox), int(oy)))
    c.alpha_composite(ov, (int(ox), int(oy)))


def tag(c, x, y, parts, a=1.0, scale=1.0, h=86, anchor="center", tint=NAVY, tint_a=0.62):
    """Shishasimon yorliq: parts = [(matn, rang, shrift, o'lcham), ...]."""
    if a <= 0.01:
        return
    gap = 14
    widths = [font(fn, sz).getlength(s) for s, _, fn, sz in parts]
    w = int(sum(widths) + gap * (len(parts) - 1) + 56)
    w, hh = w * scale, h * scale
    x0 = x - w / 2 if anchor == "center" else x
    glass(c, (x0, y - hh / 2, x0 + w, y + hh / 2), hh / 2, tint=tint, tint_a=tint_a, blur=18, alpha=a)
    tx = x0 + 28 * scale
    for (s, col, fn, sz), wd in zip(parts, widths):
        paste(c, text_img(s, sz, col, fn, shadow=0.25), tx + wd * scale / 2, y, scale, a)
        tx += (wd + gap) * scale


def stars_burst(c, t, t0, x, y, n=14, radius=320, dur=0.75, seed=1, cols=(WHITE, CYAN, AMBER)):
    """Uchqun va konfetti portlashi."""
    p = prog(t, t0, dur)
    if not (0 < p < 1):
        return
    rnd = random.Random(seed)
    e = ease_out_cubic(p)
    for k in range(n):
        ang = k * 2 * math.pi / n + rnd.uniform(-0.3, 0.3)
        dist = radius * rnd.uniform(0.55, 1.0) * e
        size = rnd.choice((18, 26, 34))
        col = rnd.choice(cols)
        key = ("star", size, col)
        if key not in _cache:
            def fn(d, s, size=size, col=col):
                r, cc = size * s / 2, size * s / 2
                pts = [(cc + (r if j % 2 == 0 else r * 0.25) * math.cos(j * math.pi / 4 - math.pi / 2),
                        cc + (r if j % 2 == 0 else r * 0.25) * math.sin(j * math.pi / 4 - math.pi / 2)) for j in range(8)]
                d.polygon(pts, fill=tuple(col) + (255,))
            _cache[key] = add_shadow(padded(ss_shape(size, size, fn), size), 2, opacity=0, glow=col, glow_radius=size * 0.3,
                                     glow_strength=1)
        paste(c, _cache[key], x + dist * math.cos(ang), y + dist * math.sin(ang) + p * p * 60, 1.2 * (1 - p) ** 0.5,
              1 - p ** 2, p * 300 * (1 if k % 2 else -1))


def perspective(img, k):
    """Kartani Y o'qi atrofida burish (k>0: o'ng cheti uzoqlashadi). k ~ -0.3..0.3"""
    w, h = img.size
    dy = abs(k) * h * 0.5
    if k >= 0:
        dst = [(0, 0), (w, dy), (w, h - dy), (0, h)]
    else:
        dst = [(0, dy), (w, 0), (w, h), (0, h - dy)]
    src = [(0, 0), (w, 0), (w, h), (0, h)]
    A, B = [], []
    for (x, y), (u, v) in zip(dst, src):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y])
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y])
        B += [u, v]
    coeffs = np.linalg.solve(np.array(A, float), np.array(B, float))
    return img.transform((w, h), Image.PERSPECTIVE, tuple(coeffs), Image.BICUBIC)

# ---------------------------------------------------------------- chiziqli ikonkalar


def _stroke(d, pts, w, col, closed=False):
    if closed:
        pts = list(pts) + [pts[0]]
    d.line(pts, fill=col, width=int(w), joint="curve")
    r = w / 2
    for x, y in (pts[0], pts[-1]):
        d.ellipse((x - r, y - r, x + r, y + r), fill=col)


def icon(kind, size=128, col=WHITE + (255,), sw=0.06):
    """SVG uslubidagi chiziqli ikonka: box, bell, check, star, globe, play, cursor, flame, gift, user."""
    key = ("icon", kind, size, col, sw)
    if key in _cache:
        return _cache[key]

    def fn(d, s):
        S = size * s
        w = S * sw

        def P(*xy):
            return [(x * S, y * S) for x, y in zip(xy[::2], xy[1::2])]
        if kind == "box":  # izometrik quti
            _stroke(d, P(0.5, 0.12, 0.88, 0.32, 0.5, 0.52, 0.12, 0.32), w, col, closed=True)
            _stroke(d, P(0.12, 0.32, 0.12, 0.72, 0.5, 0.92, 0.88, 0.72, 0.88, 0.32), w, col)
            _stroke(d, P(0.5, 0.52, 0.5, 0.92), w, col)
        elif kind == "bell":
            _stroke(d, P(0.22, 0.7, 0.28, 0.6, 0.28, 0.42), w, col)
            d.arc((0.28 * S, 0.18 * S, 0.72 * S, 0.66 * S), 180, 360, fill=col, width=int(w))
            _stroke(d, P(0.72, 0.42, 0.72, 0.6, 0.78, 0.7, 0.22, 0.7), w, col)
            d.arc((0.4 * S, 0.66 * S, 0.6 * S, 0.86 * S), 0, 180, fill=col, width=int(w))
            _stroke(d, P(0.5, 0.12, 0.5, 0.18), w, col)
        elif kind == "check":
            _stroke(d, P(0.18, 0.52, 0.42, 0.74, 0.84, 0.28), w * 1.3, col)
        elif kind == "globe":
            d.ellipse((0.12 * S, 0.12 * S, 0.88 * S, 0.88 * S), outline=col, width=int(w))
            d.ellipse((0.33 * S, 0.12 * S, 0.67 * S, 0.88 * S), outline=col, width=int(w))
            _stroke(d, P(0.14, 0.5, 0.86, 0.5), w, col)
        elif kind == "play":
            _stroke(d, P(0.32, 0.2, 0.8, 0.5, 0.32, 0.8), w, col, closed=True)
        elif kind == "star":
            pts = [(0.5 + (0.4 if j % 2 == 0 else 0.17) * math.cos(j * math.pi / 5 - math.pi / 2),
                    0.52 + (0.4 if j % 2 == 0 else 0.17) * math.sin(j * math.pi / 5 - math.pi / 2)) for j in range(10)]
            _stroke(d, [(x * S, y * S) for x, y in pts], w, col, closed=True)
        elif kind == "flame":
            pts = [(0.5, 0.1), (0.66, 0.34), (0.76, 0.56), (0.72, 0.76), (0.58, 0.9), (0.42, 0.9), (0.28, 0.76),
                   (0.26, 0.56), (0.36, 0.42), (0.42, 0.56), (0.48, 0.38)]
            _stroke(d, [(x * S, y * S) for x, y in pts], w, col, closed=True)
        elif kind == "gift":
            d.rounded_rectangle((0.16 * S, 0.42 * S, 0.84 * S, 0.88 * S), 0.04 * S, outline=col, width=int(w))
            d.rounded_rectangle((0.1 * S, 0.28 * S, 0.9 * S, 0.42 * S), 0.04 * S, outline=col, width=int(w))
            _stroke(d, P(0.5, 0.28, 0.5, 0.88), w, col)
            d.arc((0.3 * S, 0.1 * S, 0.5 * S, 0.3 * S), 90, 360, fill=col, width=int(w))
            d.arc((0.5 * S, 0.1 * S, 0.7 * S, 0.3 * S), 180, 90, fill=col, width=int(w))
        elif kind == "user":
            d.ellipse((0.34 * S, 0.12 * S, 0.66 * S, 0.44 * S), outline=col, width=int(w))
            d.arc((0.16 * S, 0.52 * S, 0.84 * S, 1.2 * S), 180, 360, fill=col, width=int(w))
    out = ss_shape(size, size, fn, ss=4)
    _cache[key] = out
    return out


def disc_icon(kind, size=120, c0=BLUE, c1=CYAN, icon_scale=0.56):
    """Gradient doira ichida oq ikonka (soya bilan)."""
    key = ("disc", kind, size, c0, c1, icon_scale)
    if key in _cache:
        return _cache[key]
    g = gradient(size, size, c0, c1)
    g.putalpha(ss_shape(size, size, lambda d, s: d.ellipse((0, 0, size * s - 1, size * s - 1), fill=(255,) * 4)).getchannel("A"))
    ic = icon(kind, int(size * icon_scale))
    g.alpha_composite(ic, ((size - ic.width) // 2, (size - ic.height) // 2))
    out = add_shadow(padded(g, 24), 10, (0, 6), 0.4)
    _cache[key] = out
    return out

# ---------------------------------------------------------------- fon


class TechBackground:
    """Navy fon: harakatlanuvchi ko'k/cyan nurlar, perspektivali HUD to'r, ko'tariluvchi zarrachalar (parallaks)."""

    def __init__(self, seed=5, grid=True, particles=48):
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        base = np.array(NAVY, np.float32)[None, None] * (1.05 - 0.35 * (yy / H))[..., None]
        self.base = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)).convert("RGBA")
        self.grid = grid
        rnd = random.Random(seed)
        self.parts = [(rnd.uniform(0, W), rnd.uniform(0, H), rnd.choice((2, 3, 4, 6)), rnd.uniform(20, 90), rnd.uniform(0, 6))
                      for _ in range(particles)]
        self.blobs = [(BLUE, 760, 0.25, 0.28, 0.11, 0.0), (CYAN, 620, 0.78, 0.62, 0.09, 2.1), ((90, 60, 255), 560, 0.4, 0.86, 0.13, 4.0)]

    def render(self, c, t):
        c.paste(self.base)
        for col, r, fx, fy, sp, ph in self.blobs:
            x = W * fx + math.sin(t * sp * 6 + ph) * 160
            y = H * fy + math.cos(t * sp * 5 + ph) * 140
            soft_glow(c, x, y, r, r, col, 0.42)
        if self.grid:
            ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            d = ImageDraw.Draw(ov)
            vx, vy = W / 2, H * 0.62
            for k in range(-9, 10):
                d.line((vx, vy, vx + k * 240, H), fill=CYAN + (22,), width=2)
            off = (t * 0.35) % 1
            for k in range(10):
                z = (k + off) / 10
                y = vy + (H - vy) * z ** 2.2
                d.line((0, y, W, y), fill=CYAN + (int(6 + 34 * z),), width=2)
            c.alpha_composite(ov)
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(ov)
        for x, y, s, sp, ph in self.parts:
            yy = (y - t * sp) % H
            xx = x + math.sin(t * 0.8 + ph) * 12
            a = int(70 + 90 * (s / 6))
            d.ellipse((xx - s / 2, yy - s / 2, xx + s / 2, yy + s / 2), fill=(170, 230, 255, a))
        c.alpha_composite(ov)
