"""Public repo qo'riqchisi: commit qilinayotgan fayllarda mijoz izi bo'lmasin.

  python tools/check_public.py            # staged fayllarni tekshiradi (pre-commit hook shuni chaqiradi)
  python tools/check_public.py --all      # git kuzatayotgan barcha fayllarni tekshiradi

Taqiqlangan so'zlar avtomatik olinadi: clients/*/profile.md dagi name, slug, contact va telefon raqamlari.
Hook o'rnatish: python tools/check_public.py --install
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PRIVATE_DIRS = ("clients/", "projects/", "references/", "inbox/")
MEDIA = re.compile(r"\.(mp4|mov|mkv|webm|mp3|wav|ogg|opus|m4a|png|jpe?g|webp|ttf|otf)$", re.I)


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, encoding="utf-8").stdout


def banned_terms():
    terms = set()
    for prof in (ROOT / "clients").glob("*/profile.md"):
        text = prof.read_text(encoding="utf-8")
        m = re.match(r"^---\n(.*?)\n---", text, re.S)
        fm = dict(l.split(":", 1) for l in m.group(1).splitlines() if ":" in l) if m else {}
        for k in ("name", "slug", "contact"):
            v = fm.get(k, "").strip()
            for part in re.split(r"[,;]| — ", v):
                part = part.strip()
                if len(part) >= 4 and part != "-":
                    terms.add(part)
        terms.add(prof.parent.name)
        terms.update(re.findall(r"\+998[\d\s()\-]{9,}", text))
    # nomlarning bo'shliqsiz/defissiz variantlari ham ("Brend Nomi" -> "brendnomi")
    for t in list(terms):
        terms.add(re.sub(r"[\s\-_]", "", t))
    return {t for t in terms if len(t) >= 4}


def main():
    if "--install" in sys.argv:
        hook = ROOT / ".git" / "hooks" / "pre-commit"
        hook.write_text("#!/bin/sh\nexec python tools/check_public.py\n", encoding="utf-8")
        print("O'rnatildi:", hook)
        return 0
    files = git("ls-files").split() if "--all" in sys.argv else git("diff", "--cached", "--name-only", "--diff-filter=ACM").split()
    terms = banned_terms()
    pat = re.compile("|".join(re.escape(t) for t in sorted(terms, key=len, reverse=True)), re.I) if terms else None
    bad = []
    for f in files:
        if f.startswith(PRIVATE_DIRS) and not f.endswith(".keep"):
            bad.append(f"{f}: maxfiy papka")
            continue
        if MEDIA.search(f):
            bad.append(f"{f}: media fayl")
            continue
        p = ROOT / f
        if not p.is_file() or pat is None:
            continue
        try:
            text = (git("show", f":{f}") if "--all" not in sys.argv else p.read_text(encoding="utf-8"))
        except UnicodeDecodeError:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            m = pat.search(line)
            if m:
                bad.append(f"{f}:{i}: mijoz izi '{m.group(0)}'")
    if bad:
        print("PUBLIC REPO QO'RIQCHISI: commit to'xtatildi — mijoz ma'lumoti topildi:")
        print("\n".join("  " + b for b in bad))
        return 1
    print(f"Toza: {len(files)} fayl, {len(terms)} ta taqiqlangan so'z bo'yicha tekshirildi.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
