"""Motion grafika dvigateli: videoni kadrma-kadr (PIL + numpy) kompozitsiya qilib ffmpeg'ga uzatadi.

Loyiha o'z build.py faylida elementlar ro'yxatini tuzadi va Renderer'ni ishga tushiradi:

    r = Renderer("source/x.mp4", out="export/final.mp4", extend=2.5)
    r.zoom = Zoom([(0, 1.0), (1.3, 1.1)])
    r.add(Captions(...), Pop(...), Burst(...), ...)
    r.main()     # CLI: --stills 1.2,5.0 | --range 5 9 | --preview

Har bir element: .render(canvas: Image RGBA, t: float).  SFX: r.sfx.pop(t) va h.k.
"""
import argparse
import math
import random
import re
import subprocess
import sys
import time
import wave
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from common import ffmpeg, probe

W, H = 1080, 1920
WINF = "C:/Windows/Fonts/"
_GDIR = Path(__file__).resolve().parent.parent / "assets" / "fonts" / "google"
GFONTS = {"mont": _GDIR / "Montserrat-VF.ttf", "inter": _GDIR / "Inter-VF.ttf", "grot": _GDIR / "SpaceGrotesk-VF.ttf"}
FONTS = {"black": "seguibl.ttf", "bold": "segoeuib.ttf", "semibold": "seguisb.ttf",
         "regular": "segoeui.ttf", "icons": "segmdl2.ttf", "emoji": "seguiemj.ttf", "num": "bahnschrift.ttf"}
RED = (255, 46, 59)
WHITE = (255, 255, 255)

# ---------------------------------------------------------------- easing


def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def prog(t, t0, dur):
    return clamp((t - t0) / dur) if dur > 0 else float(t >= t0)


def ease_out_cubic(p):
    return 1 - (1 - p) ** 3


def ease_in_cubic(p):
    return p ** 3


def ease_in_out(p):
    return 4 * p ** 3 if p < 0.5 else 1 - (-2 * p + 2) ** 3 / 2


def ease_out_back(p, s=1.9):
    return 1 + (s + 1) * (p - 1) ** 3 + s * (p - 1) ** 2


def uz(text):
    """o'/g' -> oʻ/gʻ, boshqa apostroflar -> ’"""
    return re.sub(r"([oOgG])'", "\\1ʻ", text).replace("'", "’")

# ---------------------------------------------------------------- chizish yordamchilari


@lru_cache(None)
def font(name, size):
    """name: FONTS kaliti ("black", "semibold"...) yoki Google shrifti "oila:Og'irlik" — masalan
    "mont:ExtraBold", "inter:SemiBold", "grot:Bold" (assets/fonts/google/ dagi o'zgaruvchan shriftlar)."""
    if ":" in name:
        fam, weight = name.split(":", 1)
        f = ImageFont.truetype(str(GFONTS[fam]), int(size))
        f.set_variation_by_name(weight)
        return f
    f = ImageFont.truetype(WINF + FONTS.get(name, name), int(size))
    if name == "num":  # Bahnschrift — o'zgaruvchan shrift, raqamlar uchun qalin variant
        try:
            f.set_variation_by_name("Bold")
        except Exception:
            pass
    return f


def from_alpha(alpha, rgb, opacity=1.0):
    im = Image.new("RGBA", alpha.size, tuple(rgb) + (255,))
    im.putalpha(alpha.point(lambda v: int(v * opacity)) if opacity != 1 else alpha)
    return im


def with_alpha(img, a):
    if a >= 0.999:
        return img
    img = img.copy()
    img.putalpha(img.getchannel("A").point(lambda v: int(v * a)))
    return img


def add_shadow(img, radius, offset=(0, 0), opacity=0.55, glow=None, glow_radius=None, glow_strength=2):
    """img atrofiga soya va (ixtiyoriy) rangli nur qo'shadi. img'da yetarli bo'sh chet bo'lishi kerak."""
    a = img.getchannel("A")
    out = Image.new("RGBA", img.size, (0, 0, 0, 0))
    if opacity:
        sh = from_alpha(a, (0, 0, 0), opacity).filter(ImageFilter.GaussianBlur(radius))
        out.alpha_composite(sh, (int(offset[0]), int(offset[1])))
    if glow:
        g = from_alpha(a, glow).filter(ImageFilter.GaussianBlur(glow_radius or radius * 2))
        for _ in range(glow_strength):
            out.alpha_composite(g)
    out.alpha_composite(img)
    return out


def ss_shape(w, h, fn, ss=3):
    """Supersampling bilan silliq shakl chizish: fn(draw, s) — s koordinata ko'paytiruvchisi."""
    big = Image.new("RGBA", (int(w * ss), int(h * ss)), (0, 0, 0, 0))
    fn(ImageDraw.Draw(big), ss)
    return big.resize((int(w), int(h)), Image.LANCZOS)


def rounded_mask(w, h, r):
    return ss_shape(w, h, lambda d, s: d.rounded_rectangle((0, 0, w * s - 1, h * s - 1), r * s, fill=(255,) * 4)).getchannel("A")


def paste(canvas, img, cx, cy, scale=1.0, alpha=1.0, rot=0.0):
    """img markazini (cx, cy) ga qo'yadi — masshtab, shaffoflik, burilish bilan, chetdan chiqsa kesadi."""
    if alpha <= 0.004 or scale <= 0.01:
        return
    if rot:
        img = img.rotate(rot, resample=Image.BICUBIC, expand=True)
    if abs(scale - 1) > 0.002:
        img = img.resize((max(1, round(img.width * scale)), max(1, round(img.height * scale))), Image.BICUBIC)
    img = with_alpha(img, alpha)
    x, y = round(cx - img.width / 2), round(cy - img.height / 2)
    x0, y0 = max(x, 0), max(y, 0)
    x1, y1 = min(x + img.width, canvas.width), min(y + img.height, canvas.height)
    if x0 < x1 and y0 < y1:
        canvas.alpha_composite(img.crop((x0 - x, y0 - y, x1 - x, y1 - y)), (x0, y0))


def glass(canvas, box, radius, tint=(255, 255, 255), tint_a=0.18, blur=22, alpha=1.0, border=True):
    """Frosted-glass panel: orqa fonni xiralashtirib, rang beradi."""
    x0, y0, x1, y1 = [int(round(v)) for v in box]
    w, h = x1 - x0, y1 - y0
    if w < 4 or h < 4 or alpha <= 0.01:
        return
    cx0, cy0, cx1, cy1 = max(x0, 0), max(y0, 0), min(x1, canvas.width), min(y1, canvas.height)
    if cx0 >= cx1 or cy0 >= cy1:
        return
    region = canvas.crop((x0, y0, x1, y1)).filter(ImageFilter.GaussianBlur(blur))
    region = Image.blend(region, Image.new("RGBA", region.size, tuple(tint) + (255,)), tint_a)
    mask = rounded_mask(w, h, radius)
    if border:
        edge = ss_shape(w, h, lambda d, s: d.rounded_rectangle((1, 1, w * s - 2, h * s - 2), radius * s,
                                                               outline=(255, 255, 255, 90), width=int(2 * s)))
        region.alpha_composite(edge)
    region.putalpha(mask.point(lambda v: int(v * alpha)))
    paste(canvas, region, x0 + w / 2, y0 + h / 2)

# ---------------------------------------------------------------- matn


@lru_cache(512)
def text_img(text, size, color=WHITE, fname="black", stroke=0, glow=None, shadow=0.6):
    """Matn rasmi; markazi = matn markazi, baseline barcha so'zlar uchun bir xil balandlikda."""
    f = font(fname, size)
    asc, desc = f.getmetrics()
    pad = int(size * 0.45)
    w = int(f.getlength(text)) + 2 * pad + 2 * stroke
    h = asc + desc + 2 * pad
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((w / 2, pad + asc), text, font=f, fill=tuple(color) + (255,), anchor="ms",
                            stroke_width=stroke, stroke_fill=(0, 0, 0, 150))
    out = add_shadow(im, radius=size * 0.07, offset=(0, size * 0.05), opacity=shadow)
    if glow:  # yumshoq nur — faqat orqada, harflar aniq qoladi
        g = from_alpha(im.getchannel("A"), glow, 0.55).filter(ImageFilter.GaussianBlur(size * 0.16))
        base = Image.new("RGBA", out.size, (0, 0, 0, 0))
        base.alpha_composite(g)
        base.alpha_composite(out)
        out = base
    return out


def text_width(text, size, fname="black"):
    return font(fname, size).getlength(text)

# ---------------------------------------------------------------- elementlar


class Captions:
    """So'zma-so'z chiqadigan subtitrlar.
    words: [(t0, t1, "matn", accent)] — accent: 0/1 yoki o'z rangi (R, G, B)
    chunks: [[indekslar], ...] yoki [{"w": [...], "size":, "y":, "end":}]
    pop=True: overshoot bilan sakrab chiqadi; False: yumshoq ko'tarilish (premium uslub).
    """

    def __init__(self, words, chunks, y=H * 0.62, size=92, max_w=W * 0.86, accent=RED, upper=True,
                 exit_pad=0.35, line_gap=1.08, exit_fade=0.07, fname="black", glow=True, pop=True,
                 accent_scale=1.12, shadow=0.6):
        self.words = [dict(t0=a, t1=b, text=uz(s).upper() if upper else uz(s), accent=acc) for a, b, s, acc in words]
        self.accent, self.fade = accent, exit_fade
        self.fname, self.glow, self.pop, self.ascale, self.shadow = fname, glow, pop, accent_scale, shadow
        self.items = []
        for i, ch in enumerate(chunks):
            ch = ch if isinstance(ch, dict) else {"w": ch}
            idx = ch["w"]
            nxt = chunks[i + 1] if i + 1 < len(chunks) else None
            nxt_t0 = self.words[(nxt if isinstance(nxt, list) else nxt["w"])[0]]["t0"] if nxt else 1e9
            # eski bo'lak yangisining birinchi so'zi chiqishidan oldin to'liq yo'qoladi — ustma-ust tushmaydi
            t_end = min(self.words[idx[-1]]["t1"] + exit_pad, nxt_t0 - 0.06 - exit_fade, ch.get("end", 1e9))
            self.items.append(self._layout(idx, ch.get("size", size), ch.get("y", y), max_w, t_end, line_gap))

    def _layout(self, idx, size, y, max_w, t_end, line_gap):
        def wsize(i):
            return size * (self.ascale if self.words[i]["accent"] else 1)
        while True:  # sig'masa kichraytirish
            if max(text_width(self.words[i]["text"], wsize(i), self.fname) for i in idx) <= max_w:
                break
            size *= 0.92
        space = size * (0.4 if self.pop else 0.3)
        lines, cur, cur_w = [], [], 0
        for i in idx:
            ww = text_width(self.words[i]["text"], wsize(i), self.fname)
            if cur and cur_w + space + ww > max_w:
                lines.append((cur, cur_w))
                cur, cur_w = [], 0
            cur_w += (space if cur else 0) + ww
            cur.append((i, ww))
        lines.append((cur, cur_w))
        lh = size * line_gap
        pos = {}
        for li, (ln, lw) in enumerate(lines):
            x = W / 2 - lw / 2
            cy = y + (li - (len(lines) - 1) / 2) * lh
            for i, ww in ln:
                pos[i] = (x + ww / 2, cy)
                x += ww + space
        return dict(idx=idx, pos=pos, size=size, t0=self.words[idx[0]]["t0"] - 0.06, t1=t_end)

    def render(self, c, t):
        for it in self.items:
            if not (it["t0"] <= t <= it["t1"] + self.fade):
                continue
            q = prog(t, it["t1"], self.fade)
            for i in it["idx"]:
                w = self.words[i]
                p = prog(t, w["t0"] - 0.05, 0.24)
                if p <= 0:
                    continue
                acc = w["accent"]
                col = tuple(acc) if isinstance(acc, (tuple, list)) else self.accent if acc else WHITE
                sz = int(it["size"] * (self.ascale if acc else 1))
                img = text_img(w["text"], sz, col, self.fname, shadow=min(1, self.shadow + 0.2) if acc else self.shadow,
                               glow=col if acc and self.glow else None)
                if self.pop:
                    sc = (0.45 + 0.55 * ease_out_back(p)) * (1 - 0.12 * q)
                else:
                    sc = (0.9 + 0.1 * ease_out_cubic(p)) * (1 - 0.05 * q)
                if acc and self.pop:  # urg'u so'z aytilayotganda yengil "nafas"
                    sc *= 1 + 0.05 * math.sin(math.pi * prog(t, w["t0"], max(0.2, w["t1"] - w["t0"] + 0.15)))
                x, y = it["pos"][i]
                dy = (1 - ease_out_cubic(p)) * it["size"] * 0.4 - q * 20
                paste(c, img, x, y + dy, sc, clamp(p * 3.5) * (1 - q))


@lru_cache(64)
def badge(glyph, size=185, fname="icons", bg=WHITE, fg=RED, glyph_scale=0.5, stroke=1):
    """Oq doira ichida ikonka (soya bilan)."""
    pad = int(size * 0.3)
    S = size + 2 * pad
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    disc = ss_shape(size, size, lambda d, s: d.ellipse((0, 0, size * s - 1, size * s - 1), fill=tuple(bg) + (255,)))
    im.alpha_composite(disc, (pad, pad))
    f = font(fname, size * glyph_scale)
    ImageDraw.Draw(im).text((S / 2, S / 2), glyph, font=f, fill=tuple(fg) + (255,), anchor="mm",
                            stroke_width=stroke, stroke_fill=tuple(fg) + (255,), embedded_color=fname == "emoji")
    return add_shadow(im, radius=size * 0.08, offset=(0, size * 0.06), opacity=0.45)


@lru_cache(64)
def emoji(ch, size=150, shadow=0.4):
    pad = int(size * 0.4)
    S = int(size * 1.4) + 2 * pad
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((S / 2, S / 2), ch, font=font("emoji", size), anchor="mm", embedded_color=True)
    return add_shadow(im, radius=size * 0.06, offset=(0, size * 0.05), opacity=shadow)


class Pop:
    """Rasm (ikonka) pop bo'lib kiradi, suzib turadi, kichrayib chiqadi."""

    def __init__(self, img, t0, t1, x, y, scale=1.0, rot_in=-25, bob=7, dur_in=0.38, dur_out=0.2):
        self.img, self.t0, self.t1, self.x, self.y = img, t0, t1, x, y
        self.scale, self.rot_in, self.bob, self.din, self.dout = scale, rot_in, bob, dur_in, dur_out

    def render(self, c, t):
        if not (self.t0 <= t <= self.t1 + self.dout):
            return
        p = prog(t, self.t0, self.din)
        q = prog(t, self.t1, self.dout)
        sc = self.scale * ease_out_back(p) * (1 - ease_in_cubic(q))
        rot = self.rot_in * (1 - ease_out_cubic(p)) + 3 * math.sin((t - self.t0) * 3.1)
        y = self.y + self.bob * math.sin((t - self.t0) * 2.6)
        paste(c, self.img, self.x, y, sc, clamp(p * 4), rot)


class Strike:
    """Element ustidan qizil X chizilishi (masalan 'shart emas')."""

    def __init__(self, t0, t1, x, y, size=150, color=RED, width=16):
        self.t0, self.t1, self.x, self.y, self.size, self.color, self.width = t0, t1, x, y, size, color, width

    def render(self, c, t):
        if not (self.t0 <= t <= self.t1 + 0.2):
            return
        s = self.size
        p1, p2 = ease_out_cubic(prog(t, self.t0, 0.16)), ease_out_cubic(prog(t, self.t0 + 0.12, 0.16))
        q = prog(t, self.t1, 0.2)

        def fn(d, k):
            m, e = s * 0.12 * k, s * 0.88 * k
            for (ax, ay, bx, by), p in (((m, m, e, e), p1), ((e, m, m, e), p2)):
                if p > 0:
                    d.line((ax, ay, ax + (bx - ax) * p, ay + (by - ay) * p), fill=tuple(self.color) + (255,),
                           width=int(self.width * k))
                    for px, py in ((ax, ay), (ax + (bx - ax) * p, ay + (by - ay) * p)):
                        r = self.width * k / 2
                        d.ellipse((px - r, py - r, px + r, py + r), fill=tuple(self.color) + (255,))
        img = ss_shape(s, s, fn)
        big = Image.new("RGBA", (s + 60, s + 60), (0, 0, 0, 0))
        big.alpha_composite(img, (30, 30))
        shake = 6 * math.sin(t * 90) * (1 - prog(t, self.t0 + 0.2, 0.25)) * (t > self.t0 + 0.12)
        paste(c, add_shadow(big, 6, (0, 4), 0.5), self.x + shake, self.y, 1, 1 - q)


@lru_cache(8)
def star_img(size, color=(255, 236, 160)):
    def fn(d, s):
        r, cx = size * s / 2, size * s / 2
        pts = []
        for k in range(8):
            ang = k * math.pi / 4 - math.pi / 2
            rr = r if k % 2 == 0 else r * 0.22
            pts.append((cx + rr * math.cos(ang), cx + rr * math.sin(ang)))
        d.polygon(pts, fill=tuple(color) + (255,))
    im = Image.new("RGBA", (size * 2, size * 2), (0, 0, 0, 0))
    im.alpha_composite(ss_shape(size, size, fn), (size // 2, size // 2))
    return add_shadow(im, 2, opacity=0, glow=(255, 220, 120), glow_radius=size * 0.25, glow_strength=1)


class Burst:
    """Uchqunlar portlashi + kengayuvchi halqa (masalan 'ideal' so'zida)."""

    def __init__(self, t0, x, y, n=12, radius=300, dur=0.8, seed=1):
        rnd = random.Random(seed)
        self.t0, self.x, self.y, self.dur, self.radius = t0, x, y, dur, radius
        self.parts = [(k * 2 * math.pi / n + rnd.uniform(-0.25, 0.25), rnd.uniform(0.55, 1.0),
                       rnd.choice((34, 46, 60)), rnd.uniform(-1, 1)) for k in range(n)]

    def render(self, c, t):
        p = prog(t, self.t0, self.dur)
        if p <= 0 or p >= 1:
            return
        e = ease_out_cubic(p)
        for ang, dist, size, spin in self.parts:
            d = self.radius * dist * e
            paste(c, star_img(size), self.x + d * math.cos(ang), self.y + d * math.sin(ang),
                  (1 - p) ** 0.6 * 1.1, 1 - p ** 2, spin * 200 * p)
        rr = 40 + self.radius * 0.9 * e
        ring = ss_shape(rr * 2 + 20, rr * 2 + 20, lambda dr, s: dr.ellipse(
            (10 * s, 10 * s, (rr * 2 + 10) * s, (rr * 2 + 10) * s), outline=(255, 255, 255, 255), width=int(6 * s * (1 - p) + s)), ss=2)
        paste(c, ring, self.x, self.y, 1, (1 - p) * 0.8)


class Leaves:
    """Barg zarralari: mode='fall' (yuqoridan tushadi) yoki 'wind' (o'ngdan chapga uchadi)."""

    def __init__(self, t0, t1, n=14, mode="fall", seed=3, chars=("🍂", "🍁"), sizes=(70, 95, 120)):
        rnd = random.Random(seed)
        self.t0, self.t1, self.mode = t0, t1, mode
        self.p = []
        span = max(0.01, (t1 - t0) - 1.2)
        for _ in range(n):
            self.p.append(dict(spawn=t0 + rnd.uniform(0, span), x=rnd.uniform(0.05, 0.95) * W,
                               y=rnd.uniform(0.15, 0.8) * H, life=rnd.uniform(1.2, 2.0),
                               sway=rnd.uniform(40, 110), f=rnd.uniform(1.5, 3), rot=rnd.uniform(-260, 260),
                               ch=rnd.choice(chars), size=rnd.choice(sizes), ph=rnd.uniform(0, 6)))

    def render(self, c, t):
        if not (self.t0 <= t <= self.t1 + 2):
            return
        for q in self.p:
            p = (t - q["spawn"]) / q["life"]
            if not (0 <= p <= 1):
                continue
            a = clamp(p * 6) * clamp((1 - p) * 4)
            if self.mode == "fall":
                x = q["x"] + q["sway"] * math.sin(q["ph"] + p * q["f"] * 3)
                y = -100 + p * (H * 0.85)
            else:
                x = W + 120 - p * (W + 300)
                y = q["y"] - p * 260 + q["sway"] * 0.5 * math.sin(q["ph"] + p * 8)
            paste(c, emoji(q["ch"], q["size"], 0.3), x, y, 1, a * 0.95, q["rot"] * p)


class Timer:
    """Frosted-glass doira ichida progress halqa va soniya sanog'i."""

    def __init__(self, t_in, t_start, t_end, t_out, x=W / 2, y=H * 0.21, seconds=5.0, size=260, on_done=None):
        self.t_in, self.ts, self.te, self.t_out = t_in, t_start, t_end, t_out
        self.x, self.y, self.secs, self.size = x, y, seconds, size

    def render(self, c, t):
        if not (self.t_in <= t <= self.t_out + 0.25):
            return
        pin = ease_out_back(prog(t, self.t_in, 0.45))
        q = ease_in_cubic(prog(t, self.t_out, 0.25))
        sc = pin * (1 - q)
        if sc <= 0.02:
            return
        done = t >= self.te
        pulse = 1 + 0.08 * math.sin(math.pi * prog(t, self.te, 0.35)) if done else 1
        s = int(self.size * sc * pulse)
        x0, y0 = self.x - s / 2, self.y - s / 2
        glass(c, (x0, y0, x0 + s, y0 + s), s / 2, tint=(15, 15, 18), tint_a=0.45, blur=16)
        frac = prog(t, self.ts, self.te - self.ts)

        def ring(d, k):
            m, wd = s * 0.09 * k, max(2, int(s * 0.055 * k))
            d.ellipse((m, m, s * k - m, s * k - m), outline=(255, 255, 255, 60), width=wd)
            if frac > 0:
                d.arc((m, m, s * k - m, s * k - m), -90, -90 + 360 * frac, fill=RED + (255,), width=wd)
        paste(c, ss_shape(s, s, ring), self.x, self.y)
        val = self.secs * frac
        num = f"{val:.1f}" if not done else f"{int(self.secs)}"
        paste(c, text_img(num, max(10, int(s * 0.3)), WHITE, "black", shadow=0.3), self.x, self.y - s * 0.04)
        paste(c, text_img("SEKUND", max(8, int(s * 0.085)), (220, 220, 225), "bold", shadow=0), self.x, self.y + s * 0.2)
        if done:
            paste(c, badge(chr(0xE73E), int(self.size * 0.36), fg=WHITE, bg=RED), self.x + s * 0.36, self.y - s * 0.36,
                  ease_out_back(prog(t, self.te, 0.35)) * (1 - q))


class Pill:
    """Frosted-glass 'sayt' plashkasi: chapdan sirpanib kiradi, ustidan yaltirash o'tadi."""

    def __init__(self, t0, t1, y, title, sub=None, icon=chr(0xE7BF), x=W / 2):
        self.t0, self.t1, self.y, self.x = t0, t1, y, x
        tf, sf = font("black", 64), font("semibold", 34)
        self.title, self.sub = title, sub
        self.ic = 104
        tw = max(tf.getlength(title), sf.getlength(sub) if sub else 0)
        self.w, self.h = int(self.ic + 60 + tw + 56), 150
        self.content = self._content(tf, sf)

    def _content(self, tf, sf):
        im = Image.new("RGBA", (self.w, self.h), (0, 0, 0, 0))
        disc = ss_shape(self.ic, self.ic, lambda d, s: d.ellipse((0, 0, self.ic * s - 1, self.ic * s - 1), fill=RED + (255,)))
        im.alpha_composite(disc, (24, (self.h - self.ic) // 2))
        d = ImageDraw.Draw(im)
        d.text((24 + self.ic / 2, self.h / 2), chr(0xE7BF), font=font("icons", 52), fill=WHITE + (255,), anchor="mm",
               stroke_width=1, stroke_fill=WHITE + (255,))
        tx = 24 + self.ic + 30
        if self.sub:
            d.text((tx, self.h / 2 + 6), self.title, font=tf, fill=(20, 20, 24, 255), anchor="ls")
            d.text((tx, self.h / 2 + 46), self.sub, font=sf, fill=(70, 70, 78, 255), anchor="ls")
        else:
            d.text((tx, self.h / 2), self.title, font=tf, fill=(20, 20, 24, 255), anchor="lm")
        return im

    def render(self, c, t):
        if not (self.t0 <= t <= self.t1 + 0.35):
            return
        p = ease_out_back(prog(t, self.t0, 0.55), 1.4)
        q = ease_in_cubic(prog(t, self.t1, 0.35))
        cx = -self.w / 2 + (self.x + self.w / 2) * p
        cy = self.y - q * 260
        a = clamp(prog(t, self.t0, 0.15)) * (1 - q)
        x0, y0 = cx - self.w / 2, cy - self.h / 2
        glass(c, (x0, y0, x0 + self.w, y0 + self.h), self.h / 2, tint=WHITE, tint_a=0.72, blur=24, alpha=a)
        content = self.content
        sp = prog(t, self.t0 + 0.7, 0.7)  # yaltirash
        if 0 < sp < 1:
            content = content.copy()
            band = Image.new("RGBA", (self.w, self.h), (0, 0, 0, 0))
            bx = -200 + sp * (self.w + 400)
            ImageDraw.Draw(band).polygon([(bx, 0), (bx + 90, 0), (bx + 30, self.h), (bx - 60, self.h)], fill=(255, 255, 255, 150))
            band = band.filter(ImageFilter.GaussianBlur(12))
            band.putalpha(Image.fromarray(np.minimum(np.array(band.getchannel("A")), np.array(rounded_mask(self.w, self.h, self.h / 2)))))
            content.alpha_composite(band)
        paste(c, content, cx, cy, 1, a)


class HighlightCaptions(Captions):
    """So'zlar aytilganda paydo bo'ladi, aytilayotgan so'z orqasida gradient plashka siljib boradi (premium karaoke).
    pills: {"default": (rang1, rang2), (R,G,B): (rang1, rang2)} — urg'u rangiga qarab plashka rangi."""

    def __init__(self, words, chunks, pills=None, slide=0.1, **kw):
        kw.setdefault("fname", "mont:ExtraBold")
        super().__init__(words, chunks, pop=False, glow=False, **kw)
        self.pills = pills or {"default": ((40, 123, 255), (0, 217, 255))}
        self.slide = slide

    @staticmethod
    @lru_cache(256)
    def _pill(w, h, c0, c1):
        x = np.linspace(0, 1, w)[None, :, None]
        arr = (np.array(c0) * (1 - x) + np.array(c1) * x).repeat(h, 0).astype(np.uint8)
        im = Image.fromarray(np.concatenate([arr, np.full((h, w, 1), 255, np.uint8)], 2), "RGBA")
        im.putalpha(rounded_mask(w, h, h * 0.32))
        out = Image.new("RGBA", (w + 60, h + 60), (0, 0, 0, 0))
        out.alpha_composite(im, (30, 30))
        return add_shadow(out, 12, (0, 6), 0.35)

    def _rect(self, it, i):
        w = self.words[i]
        sz = it["size"] * (self.ascale if w["accent"] else 1)
        x, y = it["pos"][i]
        return x, y - sz * 0.06, text_width(w["text"], sz, self.fname) + sz * 0.5, sz * 1.28

    def render(self, c, t):
        for it in self.items:
            if not (it["t0"] <= t <= it["t1"] + self.fade):
                continue
            q = prog(t, it["t1"], self.fade)
            idx = it["idx"]
            spoken = [i for i in idx if t >= self.words[i]["t0"] - 0.03]
            if spoken:  # plashka: oldingi so'zdan joriy so'zga siljiydi
                cur = spoken[-1]
                k = idx.index(cur)
                acc = self.words[cur]["accent"]
                key = tuple(acc) if isinstance(acc, (tuple, list)) else "default"
                c0, c1 = self.pills.get(key, self.pills["default"])
                x1, y1, w1, h1 = self._rect(it, cur)
                p = ease_out_cubic(prog(t, self.words[cur]["t0"] - 0.03, self.slide))
                if k > 0:
                    x0, y0, w0, h0 = self._rect(it, idx[k - 1])
                    if abs(y0 - y1) > 5:  # boshqa qatorga o'tsa — siljimasdan paydo bo'ladi
                        x0, y0, w0, h0 = x1, y1, w1 * 0.7, h1 * 0.7
                else:
                    x0, y0, w0, h0 = x1, y1, w1 * 0.6, h1 * 0.6

                def L(a, b):
                    return a + (b - a) * p
                pw, ph = int(L(w0, w1)), int(L(h0, h1))
                paste(c, self._pill(max(8, pw), max(8, ph), c0, c1), L(x0, x1), L(y0, y1), 1,
                      (1 - q) * clamp(prog(t, self.words[idx[0]]["t0"] - 0.05, 0.12)))
            for i in idx:
                w = self.words[i]
                pp = prog(t, w["t0"] - 0.05, 0.2)
                if pp <= 0:
                    continue
                acc = w["accent"]
                active = bool(spoken) and i == spoken[-1]
                if active or not acc:
                    col = WHITE
                else:
                    col = tuple(acc) if isinstance(acc, (tuple, list)) else self.accent
                sz = int(it["size"] * (self.ascale if acc else 1))
                img = text_img(w["text"], sz, col, self.fname, shadow=0.35 if active else self.shadow)
                x, y = it["pos"][i]
                sc = (0.92 + 0.08 * ease_out_cubic(pp)) * (1 - 0.04 * q) * (1.04 if active else 1)
                paste(c, img, x, y + (1 - ease_out_cubic(pp)) * it["size"] * 0.3, sc, clamp(pp * 3) * (1 - q))


class Whip:
    """Sahna kesimidagi o'tish: vertikal motion blur + zoom + yorug'lik chaqnashi (kesim atrofida dur*2 soniya)."""

    def __init__(self, t_cut, dur=0.14, zoom=0.18, blur=90, flash=(170, 230, 255), flash_a=0.35):
        self.t, self.dur, self.zoom, self.blur, self.flash, self.fa = t_cut, dur, zoom, blur, flash, flash_a

    def render(self, c, t):
        p = (t - (self.t - self.dur)) / (2 * self.dur)
        if not (0 < p < 1):
            return
        bump = math.sin(math.pi * p)
        s = 1 + self.zoom * bump
        small = c.convert("RGB").resize((W // 4, H // 4), Image.BILINEAR)
        if abs(s - 1) > 0.002:
            w, h = small.width / s, small.height / s
            small = small.resize(small.size, Image.BILINEAR,
                                 box=((small.width - w) / 2, (small.height - h) / 2, (small.width + w) / 2, (small.height + h) / 2))
        a = np.asarray(small, np.float32)
        k = max(1, int(self.blur * bump / 4))
        acc = np.zeros_like(a)
        n = 9
        for j in range(n):
            acc += np.roll(a, int((j - n // 2) * k / n * 2), axis=0)
        a = acc / n
        a = a + (np.array(self.flash, np.float32) - a) * (self.fa * bump ** 2)
        big = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).resize((W, H), Image.BILINEAR).convert("RGBA")
        c.paste(Image.blend(c, big, min(1, bump * 1.6)))


class Vignette:
    def __init__(self, strength=0.32, power=2.4):
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 * 0.7 + ((yy - H / 2) / (H / 2)) ** 2 * 0.55)
        a = (np.clip(r, 0, 1.4) ** power * strength * 255).clip(0, 255).astype(np.uint8)
        self.img = Image.new("RGBA", (W, H), (0, 0, 0, 255))
        self.img.putalpha(Image.fromarray(a))

    def render(self, c, t):
        c.alpha_composite(self.img)


class Grain:
    """Yengil film donadorligi (oldindan tayyorlangan 6 ta shovqin kadri aylanadi)."""

    def __init__(self, amount=7, seed=3, fps=30):
        rng = np.random.default_rng(seed)
        self.noise = [rng.normal(0, amount, (H // 2, W // 2)).astype(np.float32) for _ in range(6)]
        self.fps = fps

    def render(self, c, t):
        n = self.noise[int(t * self.fps) % len(self.noise)]
        n = np.repeat(np.repeat(n, 2, 0), 2, 1)[..., None]
        a = np.asarray(c, np.float32).copy()
        a[..., :3] += n
        c.paste(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA"))


class Zoom:
    """Kadr zoom'i: [(vaqt, masshtab)] — har bir nuqtada tez 'punch', orasida sekin drift."""

    def __init__(self, keys, ease=0.28, drift=0.01, center=(W / 2, H * 0.48)):
        self.keys, self.ease, self.drift, self.center = sorted(keys), ease, drift, center

    def to_screen(self, t, x, y):
        """Manba kadridagi (x, y) nuqta zoom'dan keyin ekranning qayeriga tushadi (Renderer.compose bilan bir xil)."""
        s = self(t)
        cx, cy = self.center
        w, h = W / s, H / s
        x0, y0 = clamp(cx - w / 2, 0, W - w), clamp(cy - h / 2, 0, H - h)
        return (x - x0) * s, (y - y0) * s

    def _seg(self, t, v0, s, tk, e):
        return v0 + (s - v0) * ease_out_cubic(prog(t, tk, e)) + self.drift * (t - tk)

    def __call__(self, t):
        """keys: (t, s) yoki (t, s, ease) — ease=0 bo'lsa keskin (sahna kesimida ko'rinmaydi)."""
        v0, s, tk, e = 1.0, 1.0, 0.0, self.ease
        for key in self.keys:
            k, sk = key[0], key[1]
            if t < k:
                break
            v0, s, tk, e = self._seg(k, v0, s, tk, e), sk, k, key[2] if len(key) > 2 else self.ease
        return self._seg(t, v0, s, tk, e)

# ---------------------------------------------------------------- SFX sintezi


class SFX:
    SR = 48000

    def __init__(self, total):
        self.buf = np.zeros(int((total + 2) * self.SR), np.float32)
        self.rng = np.random.default_rng(7)

    def _add(self, t, sig, gain):
        i = int(t * self.SR)
        if i < 0 or i >= len(self.buf):
            return
        sig = sig[: len(self.buf) - i]
        self.buf[i:i + len(sig)] += sig.astype(np.float32) * gain

    def _t(self, dur):
        return np.arange(int(dur * self.SR)) / self.SR

    def pop(self, t, gain=0.22, f0=380, f1=1100):
        x = self._t(0.12)
        f = f0 + (f1 - f0) * np.minimum(x / 0.05, 1)
        self._add(t, np.sin(2 * np.pi * np.cumsum(f) / self.SR) * np.exp(-x * 38), gain)

    def whoosh(self, t, dur=0.45, gain=0.16, up=True):
        x = self._t(dur)
        n = self.rng.standard_normal(len(x))
        env = np.sin(np.pi * (x / dur) ** (0.6 if up else 1.4)) ** 2
        out = np.zeros_like(n)
        for k, w in ((24, 1.0), (8, 0.6)):  # oddiy past chastota filtrlari aralashmasi
            out += np.convolve(n, np.ones(k) / k, mode="same") * w
        self._add(t - dur * 0.6, out * env / np.max(np.abs(out) + 1e-9), gain)

    def tick(self, t, gain=0.08, freq=3200):
        x = self._t(0.03)
        self._add(t, np.sin(2 * np.pi * freq * x) * np.exp(-x * 260), gain)

    def thump(self, t, gain=0.25):
        """yumshoq past zarba (muhim so'zlar uchun)"""
        x = self._t(0.5)
        self._add(t, np.sin(2 * np.pi * np.cumsum(48 + 60 * np.exp(-x / 0.04)) / self.SR) * np.exp(-x * 7), gain)

    def ding(self, t, gain=0.16):
        x = self._t(1.2)
        s = sum(a * np.sin(2 * np.pi * f * x) for f, a in ((1318.5, 1), (1975.5, 0.5), (2637, 0.25)))
        self._add(t, s * np.exp(-x * 4.5) / 1.75, gain)

    def sparkle(self, t, gain=0.08):
        for k, f in enumerate((2093, 2637, 3136, 4186)):
            x = self._t(0.35)
            self._add(t + k * 0.045, np.sin(2 * np.pi * f * x) * np.exp(-x * 14), gain)

    def type(self, t0, n, every, gain=0.06):
        for k in range(n):
            x = self._t(0.025)
            self._add(t0 + k * every, self.rng.standard_normal(len(x)) * np.exp(-x * 300), gain)

# ---------------------------------------------------------------- render


class Renderer:
    def __init__(self, src, out="export/final.mp4", fps=30, extend=0.0, size=(W, H), skip_white=None, crf=18,
                 vf=None, af=None, upscale=None):
        self.src, self.out, self.fps, self.extend, self.size = Path(src), Path(out), fps, extend, size
        # upscale=(2160, 3840): kompozitsiya 1080 da, chiqishda bir marta lanczos + yengil sharpen bilan 4K ga
        self.upscale = upscale
        self.vf, self.af = vf, af  # manba videosi uchun qo'shimcha ffmpeg filtrlari (rang / ovoz tozalash)
        self.bed = None  # fn(voice: np[n,2]) -> np[n,2]: musiqa qatlami (ovozga qarab ducking qilish mumkin)
        self.info = probe(self.src)
        self.total = self.info["duration"] + extend
        self.elements, self.post = [], []
        self.zoom = None
        self.skip_white = skip_white  # (t0, t1): shu oraliqdagi oq kadrlarni oldingi kadr bilan almashtirish
        self.sfx = SFX(self.total)
        self.crf = crf
        self.background = None  # fn(canvas, t) -> canvas: masalan end card fon effekti

    def add(self, *els):
        self.elements += els
        return self

    def compose(self, frame: Image.Image, t):
        if self.zoom:
            s = self.zoom(t)
            if abs(s - 1) > 0.001:
                cx, cy = self.zoom.center
                w, h = W / s, H / s
                x0 = clamp(cx - w / 2, 0, W - w)
                y0 = clamp(cy - h / 2, 0, H - h)
                frame = frame.resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + w, y0 + h))
        c = frame.convert("RGBA")
        if self.background:
            c = self.background(c, t)
        for e in self.elements:
            e.render(c, t)
        return c.convert("RGB")

    def _decoder(self, start=0.0):
        vf = f"fps={self.fps},scale={W}:{H}:flags=bicubic" + (f",{self.vf}" if self.vf else "") + ",format=rgb24"
        cmd = [ffmpeg(), "-v", "error", "-ss", f"{start:.3f}", "-i", self.src, "-vf", vf, "-f", "rawvideo", "-"]
        return subprocess.Popen([str(c) for c in cmd], stdout=subprocess.PIPE)

    def frames(self, t0, t1):
        # video tugagandan keyingi vaqt (extend) uchun oxirgi kadr kerak — biroz oldinroqdan dekodlaymiz
        ds = max(0.0, min(t0, self.info["duration"] - 0.6))
        dec = self._decoder(ds)
        n0, n1 = int(round(t0 * self.fps)), int(round(t1 * self.fps))
        last, fsz, alive = None, W * H * 3, True
        for n in range(int(round(ds * self.fps)), n1):
            t = n / self.fps
            buf = dec.stdout.read(fsz) if alive else b""
            if len(buf) == fsz:
                arr = np.frombuffer(buf, np.uint8).reshape(H, W, 3)
                if self.skip_white and self.skip_white[0] <= t <= self.skip_white[1] and arr.mean() > 225 and last is not None:
                    arr = last
                last = arr
            else:
                alive = False
            if n >= n0 and last is not None:
                yield t, Image.fromarray(last)
        dec.kill()

    def audio(self, path):
        """Manba ovozi (+af filtrlar) + musiqa (bed) + SFX -> wav."""
        r = subprocess.run([ffmpeg(), "-v", "error", "-i", str(self.src), "-vn"] + (["-af", self.af] if self.af else []) +
                           ["-ac", "2", "-ar", "48000", "-f", "f32le", "-"], capture_output=True)
        src = np.frombuffer(r.stdout, np.float32).reshape(-1, 2)
        n = int(self.total * SFX.SR)
        mix = np.zeros((n, 2), np.float32)
        m = min(n, len(src))
        mix[:m] = src[:m]
        if self.bed:
            mix += self.bed(mix.copy())[:n]
        mix += self.sfx.buf[:n, None]
        k = int(0.012 * SFX.SR)  # boshida/oxirida chertish bo'lmasin
        mix[:k] *= np.linspace(0, 1, k)[:, None]
        mix[-k:] *= np.linspace(1, 0, k)[:, None]
        peak = np.abs(mix).max()
        if peak > 0.98:
            mix *= 0.98 / peak
        mix = np.clip(mix, -1, 1)
        with wave.open(str(path), "wb") as w:
            w.setnchannels(2), w.setsampwidth(2), w.setframerate(SFX.SR)
            w.writeframes((mix * 32767).astype(np.int16).tobytes())

    def render(self, t0=0.0, t1=None, preview=False, out=None):
        t1 = t1 or self.total
        out = Path(out or self.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        wav = out.with_suffix(".mix.wav")
        self.audio(wav)
        enc = subprocess.Popen([str(c) for c in [
            ffmpeg(), "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", self.fps,
            "-i", "-", "-ss", f"{t0:.3f}", "-t", f"{t1 - t0:.3f}", "-i", wav,
            "-af", "loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000"] + self._vcodec(preview) + [
            "-c:a", "aac", "-b:a", "256k" if self.upscale else "192k", "-movflags", "+faststart", "-shortest", out]],
            stdin=subprocess.PIPE)
        st, total_n = time.time(), int((t1 - t0) * self.fps)
        for k, (t, fr) in enumerate(self.frames(t0, t1)):
            enc.stdin.write(self.compose(fr, t).tobytes())
            if k % 60 == 0:
                print(f"  {k}/{total_n} kadr  ({time.time() - st:.0f}s)", flush=True)
        enc.stdin.close()
        enc.wait()
        wav.unlink(missing_ok=True)
        print(f"Tayyor: {out}  ({time.time() - st:.0f}s)")

    def _vcodec(self, preview):
        if preview:
            return ["-c:v", "libx264", "-preset", "veryfast", "-crf", "26", "-pix_fmt", "yuv420p"]
        v = ["-c:v", "libx264", "-preset", "slow", "-crf", str(self.crf), "-pix_fmt", "yuv420p", "-profile:v", "high"]
        if self.upscale:
            w, h = self.upscale
            v = ["-vf", f"scale={w}:{h}:flags=lanczos+accurate_rnd+full_chroma_int,unsharp=5:5:0.5:5:5:0"] + v +                 ["-level", "5.1", "-preset", "medium"]
        return v

    def stills(self, times, outdir):
        outdir = Path(outdir)
        outdir.mkdir(parents=True, exist_ok=True)
        for t in times:
            fr = None
            for _, fr in self.frames(max(0, t - 0.4), t + 1 / self.fps):
                pass
            self.compose(fr, t).resize((540, 960), Image.LANCZOS).save(outdir / f"still_{t:06.2f}.jpg", quality=88)
        print("Stills:", outdir)

    def main(self):
        ap = argparse.ArgumentParser()
        ap.add_argument("--stills")
        ap.add_argument("--range", nargs=2, type=float)
        ap.add_argument("--preview", action="store_true")
        a = ap.parse_args()
        if a.stills:
            self.stills([float(x) for x in a.stills.split(",")], self.out.parent.parent / "work" / "stills")
        elif a.range:
            self.render(a.range[0], a.range[1], True, self.out.with_name(self.out.stem + f"_{a.range[0]:g}-{a.range[1]:g}.mp4"))
        else:
            self.render(preview=a.preview, out=self.out.with_name(self.out.stem + "_preview.mp4") if a.preview else None)


if __name__ == "__main__":
    sys.exit("Bu kutubxona. Loyiha build.py faylidan import qiling.")
