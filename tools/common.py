"""Umumiy yordamchilar: ffmpeg topish, probe, slug, buyruq ishga tushirish."""
import json
import os
import re
import shutil
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REFS = ROOT / "references"
PROJECTS = ROOT / "projects"
ASSETS = ROOT / "assets"

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass


@lru_cache(None)
def find_bin(name: str) -> str:
    p = shutil.which(name)
    if p:
        return p
    # winget o'rnatgan, lekin PATH hali yangilanmagan holat
    base = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Packages"
    for c in base.glob(f"Gyan.FFmpeg*/*/bin/{name}.exe"):
        return str(c)
    sys.exit(f"XATO: {name} topilmadi. O'rnatish: winget install Gyan.FFmpeg")


def ffmpeg() -> str:
    return find_bin("ffmpeg")


def ffprobe() -> str:
    return find_bin("ffprobe")


def run(cmd, cwd=None, quiet=False):
    cmd = [str(c) for c in cmd]
    if not quiet:
        print("$", " ".join(cmd[:3]), "...", flush=True)
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        sys.stderr.write(r.stderr[-4000:])
        sys.exit(f"XATO: buyruq muvaffaqiyatsiz tugadi ({r.returncode})")
    return r


def probe(path) -> dict:
    r = run([ffprobe(), "-v", "error", "-print_format", "json", "-show_format", "-show_streams", path], quiet=True)
    data = json.loads(r.stdout)
    v = next((s for s in data["streams"] if s["codec_type"] == "video"), None)
    a = next((s for s in data["streams"] if s["codec_type"] == "audio"), None)
    info = {
        "file": str(path),
        "duration": float(data["format"].get("duration", 0) or 0),
        "size_mb": round(int(data["format"].get("size", 0)) / 1e6, 2),
        "has_audio": a is not None,
    }
    if v:
        w, h = int(v["width"]), int(v["height"])
        rot = 0
        for sd in v.get("side_data_list", []):
            rot = int(sd.get("rotation", 0) or 0)
        if abs(rot) == 90:
            w, h = h, w
        num, den = (v.get("avg_frame_rate") or "0/1").split("/")
        info.update({
            "width": w, "height": h,
            "fps": round(int(num) / int(den), 3) if int(den) else 0,
            "vcodec": v.get("codec_name"),
            "aspect": aspect_label(w, h),
        })
    if a:
        info.update({"acodec": a.get("codec_name"), "sample_rate": int(a.get("sample_rate", 0))})
    return info


def aspect_label(w: int, h: int) -> str:
    r = w / h if h else 0
    for label, val in (("9:16", 9 / 16), ("4:5", 4 / 5), ("1:1", 1), ("16:9", 16 / 9), ("4:3", 4 / 3), ("21:9", 21 / 9)):
        if abs(r - val) < 0.03:
            return label
    return f"{w}x{h}"


def slugify(name: str) -> str:
    s = name.strip().lower()
    s = re.sub(r"[’'`ʻʼ]", "", s)  # o'zbekcha apostroflar: o'rik -> orik
    s = re.sub(r"[^\w]+", "-", s, flags=re.UNICODE).strip("-_")
    return s or "nomsiz"


def is_image(path) -> bool:
    return Path(path).suffix.lower() in {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def fmt_time(t: float) -> str:
    m, s = divmod(t, 60)
    return f"{int(m):02d}:{s:05.2f}"
