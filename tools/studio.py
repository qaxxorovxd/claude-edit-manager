"""Studiya boshqaruvi: mijozlar, loyihalar, ish taxtasi.

  python tools/studio.py status                         ish taxtasi: mijozlar + faol loyihalar
  python tools/studio.py client-new "Nom" [--type brend|shaxs] [--contact "..."]
  python tools/studio.py client-show NOM                profil + uning loyihalari
  python tools/studio.py find SO'Z                      mijoz/loyiha/uslubni nom bo'yicha qidirish
  python tools/studio.py set LOYIHA status=tuzatish next="Musiqani almashtirish" [deadline=2026-11-02]
  python tools/studio.py log LOYIHA "Mijoz: subtitr kattaroq bo'lsin"    -> project.md fikrlar bo'limiga
  python tools/studio.py client-log MIJOZ "Qizil rang yoqmaydi"          -> profile.md did/fikrlar bo'limiga
  python tools/studio.py index                          clients/INDEX.md, WORKBOARD.md ni yangilash

Holatlar: yangi -> jarayonda -> tekshiruvda (mijozga yuborildi) -> tuzatish -> tayyor -> topshirildi | to'xtatilgan
"""
import argparse
import datetime as dt
import re
import sys

from common import PROJECTS, ROOT, slugify

CLIENTS = ROOT / "clients"
STYLES = ROOT / "styles"
STATUSES = ["yangi", "jarayonda", "tekshiruvda", "tuzatish", "tayyor", "topshirildi", "to'xtatilgan"]
ACTIVE = {"yangi", "jarayonda", "tekshiruvda", "tuzatish"}

PROFILE = """---
name: {name}
slug: {slug}
type: {type}
contact: {contact}
since: {date}
updated: {date}
default_style: -
---
# {name}

## Kim / nima bilan shug'ullanadi
-

## Brend
- Logo: -
- Ranglar: -
- Shriftlar: -
- Sayt / telefon / ijtimoiy tarmoq: -
- Majburiy elementlar (CTA, watermark, end card): -

## Didi va afzalliklari (doimiy)
<!-- mijoz bir marta aytgan va keyingi videolarda ham amal qiladigan narsalar -->
-

## Qilinmasin
-

## Odatiy topshiriq formati
- Platforma / format: -
- Davomiylik: -
- Til / subtitr: -

## Fikrlar jurnali
<!-- sana — mijoz so'zi — qaysi loyiha -->
"""


def read_fm(path):
    """md fayl boshidagi '---' bloki -> dict, qolgan matn."""
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n?", text, re.S)
    if not m:
        return {}, text
    fm = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip()
    return fm, text[m.end():]


def write_fm(path, fm, body):
    head = "\n".join(f"{k}: {v}" for k, v in fm.items())
    path.write_text(f"---\n{head}\n---\n{body}", encoding="utf-8")


def today():
    return dt.date.today().isoformat()


def clients():
    out = []
    for p in sorted(CLIENTS.glob("*/profile.md")):
        fm, _ = read_fm(p)
        fm.setdefault("slug", p.parent.name)
        out.append(fm)
    return out


def projects():
    out = []
    for p in sorted(PROJECTS.glob("*/project.md")):
        fm, _ = read_fm(p)
        fm["slug"] = p.parent.name
        fm["title"] = next((l[2:].strip() for l in _.splitlines() if l.startswith("# ")), p.parent.name)
        out.append(fm)
    return out


def find_client(name):
    s = slugify(name)
    hits = [c for c in clients() if s == c["slug"] or s in c["slug"] or s in slugify(c.get("name", ""))]
    if len(hits) != 1:
        sys.exit(f"Mijoz topilmadi yoki bir nechta: {name} -> {[h['slug'] for h in hits]}")
    return hits[0]


def find_project(name):
    s = slugify(name)
    hits = [p for p in projects() if s == p["slug"]] or [p for p in projects() if s in p["slug"]]
    if len(hits) != 1:
        sys.exit(f"Loyiha topilmadi yoki bir nechta: {name} -> {[h['slug'] for h in hits]}")
    return PROJECTS / hits[0]["slug"] / "project.md"


def write_index():
    cl, pr = clients(), projects()
    rows = []
    for c in cl:
        mine = [p for p in pr if p.get("client") == c["slug"]]
        act = [p for p in mine if p.get("status") in ACTIVE]
        rows.append(f"| [{c.get('name', c['slug'])}]({c['slug']}/profile.md) | {c.get('type', '-')} | "
                    f"{c.get('default_style', '-')} | {len(mine)} | {len(act)} | {c.get('updated', '-')} |")
    (CLIENTS / "INDEX.md").write_text(
        "# Mijozlar\n\nAvtomatik: `python tools/studio.py index`\n\n"
        "| Mijoz | Turi | Asosiy uslub | Loyihalar | Faol | Yangilangan |\n|---|---|---|---|---|---|\n"
        + "\n".join(rows) + "\n", encoding="utf-8")

    def prow(p):
        return (f"| [{p['title']}](projects/{p['slug']}/project.md) | {p.get('client', '-')} | **{p.get('status', '-')}** | "
                f"{p.get('style', '-')} | {p.get('deadline', '-')} | {p.get('next', '-')} | {p.get('updated', '-')} |")
    head = "| Loyiha | Mijoz | Holat | Uslub | Muddat | Keyingi qadam | Yangilangan |\n|---|---|---|---|---|---|---|\n"
    order = {s: i for i, s in enumerate(STATUSES)}
    act = sorted([p for p in pr if p.get("status") in ACTIVE], key=lambda p: (order.get(p.get("status"), 9), p.get("deadline", "")))
    done = [p for p in pr if p.get("status") not in ACTIVE]
    nobind = [p["slug"] for p in pr if not p.get("client") or p.get("client") == "-"]
    text = ("# Ish taxtasi\n\nAvtomatik: `python tools/studio.py index`. Bu fayl qo'lda tahrirlanmaydi — "
            "ma'lumot `projects/*/project.md` frontmatter'idan olinadi.\n\n"
            f"## Faol ({len(act)})\n\n" + head + "\n".join(prow(p) for p in act) + "\n\n"
            f"## Tugagan / arxiv ({len(done)})\n\n" + head + "\n".join(prow(p) for p in done) + "\n")
    if nobind:
        text += "\n> Mijozga bog'lanmagan loyihalar: " + ", ".join(nobind) + "\n"
    (ROOT / "WORKBOARD.md").write_text(text, encoding="utf-8")


def cmd_status(a):
    write_index()
    cl, pr = clients(), projects()
    print(f"MIJOZLAR ({len(cl)}):")
    for c in cl:
        mine = [p for p in pr if p.get("client") == c["slug"]]
        print(f"  - {c.get('name')} [{c['slug']}] — {len(mine)} loyiha, uslub: {c.get('default_style', '-')}")
    act = [p for p in pr if p.get("status") in ACTIVE]
    print(f"\nFAOL LOYIHALAR ({len(act)}):")
    for p in act:
        print(f"  - {p['title']} [{p['slug']}] | {p.get('client')} | {p.get('status')} | keyingi: {p.get('next', '-')}")
    rest = [p for p in pr if p.get("status") not in ACTIVE]
    if rest:
        print(f"\nSO'NGGI TUGAGANLAR:")
        for p in sorted(rest, key=lambda p: p.get("updated", ""), reverse=True)[:5]:
            print(f"  - {p['title']} [{p['slug']}] | {p.get('client')} | {p.get('status')} | {p.get('updated')}")
    print("\nUSLUBLAR:", ", ".join(s.stem for s in sorted(STYLES.glob("*.md")) if s.stem != "INDEX") or "-")


def cmd_client_new(a):
    slug = slugify(a.name)
    d = CLIENTS / slug
    if d.exists():
        sys.exit(f"Mijoz allaqachon bor: clients/{slug}")
    for sub in ("briefs", "assets"):
        (d / sub).mkdir(parents=True)
    (d / "profile.md").write_text(PROFILE.format(name=a.name, slug=slug, type=a.type, contact=a.contact or "-",
                                                 date=today()), encoding="utf-8")
    write_index()
    print(f"Yaratildi: clients/{slug}/profile.md (briefs/, assets/)")


def cmd_client_show(a):
    c = find_client(a.name)
    print((CLIENTS / c["slug"] / "profile.md").read_text(encoding="utf-8"))
    print("\n## Loyihalari")
    for p in projects():
        if p.get("client") == c["slug"]:
            print(f"- {p['title']} [{p['slug']}] | {p.get('status')} | uslub: {p.get('style')} | {p.get('updated')}")
    br = sorted((CLIENTS / c["slug"] / "briefs").glob("*"))
    if br:
        print("\n## Brief'lar\n" + "\n".join(f"- {b.relative_to(ROOT).as_posix()}" for b in br))


def cmd_find(a):
    s = slugify(a.query)
    for c in clients():
        if s in c["slug"] or s in slugify(c.get("name", "")):
            print(f"mijoz:   {c.get('name')} -> clients/{c['slug']}/profile.md")
    for p in projects():
        if s in p["slug"] or s in slugify(p["title"]):
            print(f"loyiha:  {p['title']} [{p.get('status')}] -> projects/{p['slug']}/project.md")
    for st in STYLES.glob("*.md"):
        if s in st.stem:
            print(f"uslub:   styles/{st.name}")


def cmd_set(a):
    path = find_project(a.project)
    fm, body = read_fm(path)
    for kv in a.pairs:
        k, v = kv.split("=", 1)
        if k == "status" and v not in STATUSES:
            sys.exit(f"Noto'g'ri holat: {v}. Mumkin: {STATUSES}")
        fm[k] = v
    fm["updated"] = today()
    write_fm(path, fm, body)
    write_index()
    print(f"{path.parent.name}: " + ", ".join(a.pairs))


def _append(path, section, line):
    fm, body = read_fm(path)
    entry = f"- {today()} — {line}"
    if section in body:
        i = body.index(section) + len(section)
        nxt = body.find("\n## ", i)
        nxt = len(body) if nxt == -1 else nxt
        body = body[:nxt].rstrip("\n") + "\n" + entry + "\n" + body[nxt:]
    else:
        body = body.rstrip("\n") + f"\n\n{section}\n{entry}\n"
    fm["updated"] = today()
    write_fm(path, fm, body)


def cmd_log(a):
    path = find_project(a.project)
    _append(path, "## Mijoz fikrlari / tuzatishlar", a.text)
    write_index()
    print("Yozildi:", path.relative_to(ROOT).as_posix())


def cmd_client_log(a):
    c = find_client(a.client)
    path = CLIENTS / c["slug"] / "profile.md"
    _append(path, "## Fikrlar jurnali", a.text)
    write_index()
    print("Yozildi:", path.relative_to(ROOT).as_posix())


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status").set_defaults(fn=cmd_status)
    p = sub.add_parser("client-new")
    p.add_argument("name")
    p.add_argument("--type", default="brend")
    p.add_argument("--contact")
    p.set_defaults(fn=cmd_client_new)
    p = sub.add_parser("client-show")
    p.add_argument("name")
    p.set_defaults(fn=cmd_client_show)
    p = sub.add_parser("find")
    p.add_argument("query")
    p.set_defaults(fn=cmd_find)
    p = sub.add_parser("set")
    p.add_argument("project")
    p.add_argument("pairs", nargs="+")
    p.set_defaults(fn=cmd_set)
    p = sub.add_parser("log")
    p.add_argument("project")
    p.add_argument("text")
    p.set_defaults(fn=cmd_log)
    p = sub.add_parser("client-log")
    p.add_argument("client")
    p.add_argument("text")
    p.set_defaults(fn=cmd_client_log)
    sub.add_parser("index").set_defaults(fn=lambda a: (write_index(), print("INDEX.md va WORKBOARD.md yangilandi")))
    a = ap.parse_args()
    CLIENTS.mkdir(exist_ok=True)
    STYLES.mkdir(exist_ok=True)
    a.fn(a)


if __name__ == "__main__":
    main()
