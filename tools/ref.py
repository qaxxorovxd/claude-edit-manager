"""Referenslar kutubxonasi.

  python tools/ref.py add SOURCE --name "Nom" [--tags a,b] [--note "nima yoqdi"] [--cookies chrome] [--transcribe]
  python tools/ref.py list [--tag TAG]
  python tools/ref.py show NAME
  python tools/ref.py reanalyze NAME
  python tools/ref.py index

SOURCE — URL (YouTube, Instagram, TikTok...) yoki lokal fayl yo'li.
Har bir referens: references/<slug>/ {video.mp4, meta.json, notes.md, analysis/}
"""
import argparse
import datetime as dt
import json
import shutil
import subprocess
import sys
from pathlib import Path

from analyze import analyze
from common import REFS, find_bin, fmt_time, slugify

NOTES_TEMPLATE = """# {name}

- Manba: {source}
- Qo'shilgan: {added}
- Teglar: {tags}

## Nima yoqdi (foydalanuvchi so'zi)
{note}

## Uslub tahlili
<!-- Claude kadrlarni ko'rib to'ldiradi -->
- Ritm / montaj tezligi:
- Kadrlar (plan, kamera harakati):
- O'tishlar (transitions):
- Matn / titrlar (shrift, joylashuv, animatsiya):
- Rang / grading:
- Ovoz / musiqa / SFX:
- Hook (birinchi 3 soniya):

## Qayta qo'llash uchun retsept
<!-- edit.json uchun aniq parametrlar: format, o'rtacha shot uzunligi, matn uslubi... -->
"""


def download(url, dest: Path, cookies=None) -> dict:
    cmd = [sys.executable, "-m", "yt_dlp", "--no-playlist",
           "-f", "bv*[height<=1080]+ba/b[height<=1080]/b", "--merge-output-format", "mp4",
           "--ffmpeg-location", str(Path(find_bin("ffmpeg")).parent),
           "--write-info-json", "-o", str(dest / "video.%(ext)s"), url]
    if cookies:
        cmd[3:3] = ["--cookies-from-browser", cookies]
    print("Yuklanmoqda:", url, flush=True)
    if subprocess.run(cmd).returncode != 0:
        sys.exit("XATO: yuklab bo'lmadi. Instagram/TikTok uchun --cookies chrome sinab ko'ring.")
    info_file = next(dest.glob("video.info.json"), None)
    meta = {}
    if info_file:
        j = json.loads(info_file.read_text(encoding="utf-8"))
        meta = {k: j.get(k) for k in ("title", "uploader", "webpage_url", "upload_date", "view_count")}
        info_file.unlink()
    return meta


def write_index():
    rows = []
    for m in sorted(REFS.glob("*/meta.json")):
        j = json.loads(m.read_text(encoding="utf-8"))
        a = j.get("analysis", {})
        rows.append(f"| [{j['name']}]({m.parent.name}/notes.md) | {', '.join(j.get('tags', []))} | "
                    f"{fmt_time(a.get('duration', 0))} | {a.get('aspect', '')} | {a.get('avg_shot_sec', '')}s | "
                    f"{a.get('cuts_per_min', '')} | {j.get('added', '')} |")
    text = ("# Referenslar\n\nAvtomatik yaratiladi: `python tools/ref.py index`\n\n"
            "| Nom | Teglar | Davomiylik | Format | O'rt. shot | Kesim/min | Qo'shilgan |\n"
            "|---|---|---|---|---|---|---|\n" + "\n".join(rows) + "\n")
    (REFS / "INDEX.md").write_text(text, encoding="utf-8")


def run_analysis(folder: Path, transcribe=False):
    video = next(folder.glob("video.*"))
    a = analyze(video, folder / "analysis")
    if transcribe and a.get("has_audio"):
        from transcribe import transcribe as tr
        tr(video, folder / "analysis" / "transcript.srt")
    return {k: v for k, v in a.items() if k not in ("frames_dir", "contact_sheet", "file")}


def cmd_add(a):
    slug = slugify(a.name)
    folder = REFS / slug
    if folder.exists() and not a.force:
        sys.exit(f"XATO: '{slug}' nomli referens bor. Boshqa nom bering yoki --force.")
    folder.mkdir(parents=True, exist_ok=True)
    src = a.source
    extra = {}
    if Path(src).exists():
        p = Path(src)
        shutil.copy2(p, folder / f"video{p.suffix.lower()}")
    else:
        extra = download(src, folder, a.cookies)
    tags = [t.strip() for t in (a.tags or "").split(",") if t.strip()]
    meta = {
        "name": a.name, "slug": slug, "source": src, "tags": tags, "note": a.note or "",
        "added": dt.date.today().isoformat(), **({"source_info": extra} if extra else {}),
    }
    meta["analysis"] = run_analysis(folder, a.transcribe)
    (folder / "meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    notes = folder / "notes.md"
    if not notes.exists():
        notes.write_text(NOTES_TEMPLATE.format(name=a.name, source=src, added=meta["added"],
                                               tags=", ".join(tags) or "-", note=a.note or "-"), encoding="utf-8")
    write_index()
    an = meta["analysis"]
    print(f"\nSaqlandi: references/{slug}/")
    print(f"  {an.get('aspect')} | {fmt_time(an['duration'])} | {an['shot_count']} shot | "
          f"o'rtacha {an['avg_shot_sec']}s | {an['cuts_per_min']} kesim/min")
    print(f"  Kadrlar: references/{slug}/analysis/frames/  Kontakt: references/{slug}/analysis/contact.jpg")


def find_ref(name) -> Path:
    folder = REFS / slugify(name)
    if folder.exists():
        return folder
    hits = [p for p in REFS.iterdir() if p.is_dir() and slugify(name) in p.name]
    if len(hits) == 1:
        return hits[0]
    sys.exit(f"XATO: referens topilmadi: {name}" + (f" (o'xshashlar: {[h.name for h in hits]})" if hits else ""))


def cmd_list(a):
    for m in sorted(REFS.glob("*/meta.json")):
        j = json.loads(m.read_text(encoding="utf-8"))
        if a.tag and a.tag not in j.get("tags", []):
            continue
        an = j.get("analysis", {})
        print(f"- {j['name']} [{m.parent.name}] {', '.join(j.get('tags', []))} | {an.get('aspect')} "
              f"{fmt_time(an.get('duration', 0))} | shot {an.get('avg_shot_sec')}s")


def cmd_show(a):
    f = find_ref(a.name)
    print((f / "meta.json").read_text(encoding="utf-8"))
    print((f / "notes.md").read_text(encoding="utf-8"))


def cmd_reanalyze(a):
    f = find_ref(a.name)
    meta = json.loads((f / "meta.json").read_text(encoding="utf-8"))
    meta["analysis"] = run_analysis(f, a.transcribe)
    (f / "meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    write_index()
    print("Qayta tahlil qilindi:", f.name)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("add")
    p.add_argument("source")
    p.add_argument("--name", required=True)
    p.add_argument("--tags")
    p.add_argument("--note")
    p.add_argument("--cookies", help="brauzer nomi: chrome, edge, firefox")
    p.add_argument("--transcribe", action="store_true")
    p.add_argument("--force", action="store_true")
    p.set_defaults(fn=cmd_add)
    p = sub.add_parser("list")
    p.add_argument("--tag")
    p.set_defaults(fn=cmd_list)
    p = sub.add_parser("show")
    p.add_argument("name")
    p.set_defaults(fn=cmd_show)
    p = sub.add_parser("reanalyze")
    p.add_argument("name")
    p.add_argument("--transcribe", action="store_true")
    p.set_defaults(fn=cmd_reanalyze)
    sub.add_parser("index").set_defaults(fn=lambda a: (write_index(), print("INDEX.md yangilandi")))
    a = ap.parse_args()
    REFS.mkdir(exist_ok=True)
    a.fn(a)


if __name__ == "__main__":
    main()
