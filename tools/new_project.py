"""Yangi montaj loyihasi yaratish (mijozga bog'langan).

  python tools/new_project.py "Loyiha nomi" --client MIJOZ [--format 9:16|16:9|1:1|4:5] [--style USLUB]
                              [--ref REFERENS] [--from-inbox] [--deadline 2026-11-02]

Papka nomi: projects/<mijoz>-<loyiha>/. Barcha ma'lumot project.md da (frontmatter + bo'limlar).
--from-inbox: inbox/ dagi barcha fayllarni loyiha source/ papkasiga ko'chiradi.
"""
import argparse
import datetime as dt
import json
import shutil
import sys

from common import PROJECTS, ROOT, slugify
from studio import CLIENTS, find_client, write_index

FORMATS = {"9:16": (1080, 1920), "16:9": (1920, 1080), "1:1": (1080, 1080), "4:5": (1080, 1350)}

PROJECT = """---
client: {client}
status: yangi
style: {style}
format: {fmt}
reference: {ref}
created: {date}
updated: {date}
deadline: {deadline}
next: Material va talablarni yig'ish
---
# {name}

## Brief (mijoz so'zi)
<!-- mijoz yuborgan topshiriq / prompt — o'zgartirmasdan yoki aniq qisqartma -->

## Material
<!-- source/ dagi fayllar: nomi, davomiyligi, nima tasvirlangan -->

## Matn / ssenariy
<!-- tasdiqlangan subtitr matni; noaniq joylar belgilansin -->

## Ushbu video uslubi
<!-- shu videoga xos qarorlar: ranglar, shrift, subtitr joyi, grafikalar, musiqa. Asos: styles/<uslub>.md -->

## Montaj qarorlari
<!-- render qilish: python projects/<slug>/build.py | tools/render.py -->

## Mijoz fikrlari / tuzatishlar

## Holat / keyingi qadam
<!-- yangi sessiya shu yerdan davom etadi: nima qilindi, nima qoldi -->
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("name")
    ap.add_argument("--client", required=True, help="clients/ dagi mijoz (nomi yoki slug)")
    ap.add_argument("--format", default="9:16", choices=FORMATS)
    ap.add_argument("--style", default="-")
    ap.add_argument("--ref")
    ap.add_argument("--deadline", default="-")
    ap.add_argument("--from-inbox", action="store_true")
    a = ap.parse_args()
    c = find_client(a.client)["slug"]
    slug = slugify(a.name)
    if not slug.startswith(c):
        slug = f"{c}-{slug}"
    proj = PROJECTS / slug
    if proj.exists():
        sys.exit(f"XATO: loyiha bor: projects/{slug}")
    for d in ("source", "work", "export"):
        (proj / d).mkdir(parents=True)
    if a.from_inbox:
        for f in (ROOT / "inbox").iterdir():
            if f.is_file() and f.name != ".keep":
                shutil.move(str(f), proj / "source" / f.name)
    w, h = FORMATS[a.format]
    edit = {
        "output": "export/final.mp4",
        "format": {"width": w, "height": h, "fps": 30, "fit": "crop"},
        "text_style": {"pos": "bottom", "color": "white"},
        "clips": [],
        "loudnorm": True,
    }
    if a.ref:
        edit["reference"] = slugify(a.ref)
    (proj / "edit.json").write_text(json.dumps(edit, indent=2, ensure_ascii=False), encoding="utf-8")
    (proj / "project.md").write_text(PROJECT.format(name=a.name, client=c, style=a.style, fmt=a.format,
                                                    ref=slugify(a.ref) if a.ref else "-", deadline=a.deadline,
                                                    date=dt.date.today().isoformat()), encoding="utf-8")
    write_index()
    print(f"Yaratildi: projects/{slug}/  (mijoz: clients/{c}/profile.md)")
    print("  source:", [f.name for f in (proj / "source").iterdir()])


if __name__ == "__main__":
    main()
