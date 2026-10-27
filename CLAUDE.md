# Video montaj studiyasi

Bu papka — ko'p mijozli video montaj studiyasi. Foydalanuvchi (montajchi) bilan **o'zbek tilida** gaplash.
U bir nechta mijoz (brend yoki shaxs) bilan ishlaydi. Har bir mijozning ko'p loyihasi bo'ladi, bir vaqtda 2–3 ta video so'ralishi mumkin.

## ⚡ Sessiya boshlanishi (har doim)

Foydalanuvchi "ishni boshlaymiz", "salom", "yangi video" desa, video yuborsa yoki qaysi ish ekani noaniq bo'lsa,
**`studio-start` skill'ini ishga tushir**. Qisqasi:
1. `python tools/studio.py status` — mijozlar, faol loyihalar, uslublar.
2. So'ra (AskUserQuestion): **eski mijozmi yoki yangi?** → qaysi mijoz → **yangi loyihami yoki davom etamizmi?**
   Fayl nomi, matn yoki brend videoda ko'rinib tursa, javobni taxmin qilib, tasdiqlatib ol.
3. Ishlashdan oldin o'qi: `clients/<mijoz>/profile.md` → `styles/<uslub>.md` → `projects/<loyiha>/project.md`.

## 🧠 Xotira intizomi (kontekst to'lishi mumkin)

Suhbat tarixiga ishonma, **fayllarga yoz**. Yangi sessiya faqat md fayllardan ishni to'liq davom ettira olishi kerak.
- Mijoz aytgan **doimiy** did yoki afzallik → darhol `clients/<m>/profile.md` ("Didi va afzalliklari" / "Qilinmasin").
  Jurnalga yozish: `python tools/studio.py client-log <m> "..."`.
- Videoga xos tuzatish yoki fikr → `python tools/studio.py log <loyiha> "..."` va kerakli bo'limni yangila.
- Tasdiqlangan subtitr matni → project.md "Matn / ssenariy" bo'limiga.
- Har bir muhim bosqichdan keyin (render, yuborish, tuzatish) holatni yangila:
  `python tools/studio.py set <loyiha> status=... next="..."`.
- Mijoz yuborgan uzun brief yoki prompt → `clients/<m>/briefs/<sana>-<mavzu>.md`.
- Yangi, qayta ishlatsa bo'ladigan uslub paydo bo'lsa → `styles/<nom>.md` va `styles/INDEX.md`.
- Bir xil mijozga ikki marta bir xil savol berma. Avval profilda javob bormi, tekshir.

## 🔀 Bir nechta ish bir vaqtda

- Har bir loyiha mustaqil: `source/`, `build.py`, `project.md`. Loyihalar o'rtasida fayl aralashmasin.
- Bir xabarda 2–3 ta video kelsa: har biri uchun alohida loyiha och. Ularni **ketma-ket** bajar va har biridan keyin
  project.md ni yangila. Hammasining holatini `WORKBOARD.md` da ko'rsat.
- Uzun render (~2 daqiqa) paytida keyingi loyihaning tahlil yoki transkripsiyasini tayyorlash mumkin.
- Foydalanuvchi parallel ishlashni xohlasa, har bir loyiha uchun alohida Claude sessiyasi ochish mumkin.
  Har bir sessiya o'z loyihasining project.md faylidan boshlaydi.

## Tuzilma

```
WORKBOARD.md             ish taxtasi — barcha loyihalar holati (avtomatik)
clients/INDEX.md         mijozlar ro'yxati (avtomatik)
clients/<mijoz>/         profile.md (kim, brend, did, qilinmasin, fikrlar jurnali), briefs/, assets/ (logo, shrift)
projects/<mijoz>-<nom>/  project.md (frontmatter: client/status/style/next + brief, matn, uslub, qarorlar, fikrlar),
                         source/ (xom, tegilmaydi), work/, export/, build.py yoki edit.json
styles/                  qayta ishlatiladigan montaj uslublari (parametrlar + namuna loyiha)
references/<slug>/       saqlangan referens videolar va tahlili. references/INDEX.md
inbox/                   foydalanuvchi xom videolarni shu yerga tashlaydi
assets/                  umumiy resurslar: music/ sfx/ fonts/ logos/ luts/ overlays/
tools/                   python skriptlar
```

Loyiha holatlari: `yangi → jarayonda → tekshiruvda (mijozga yuborildi) → tuzatish → tayyor → topshirildi | to'xtatilgan`.

## Vositalar

Hamma skriptlar ildiz papkadan ishga tushiriladi: `python tools/<skript>.py ...`

| Skript | Vazifa |
|---|---|
| `studio.py status / client-new / client-show / find / set / log / client-log / index` | mijozlar, loyiha holati, ish taxtasi, fikrlar jurnali |
| `new_project.py "Nom" --client M [--format 9:16] [--style S] [--ref R] [--from-inbox]` | yangi loyiha (mijozga bog'langan, project.md bilan) |
| `ref.py add SOURCE --name "Nom" --tags a,b --note "..."` | URL yoki fayldan referens saqlash + avtomatik tahlil |
| `ref.py list / show NAME / reanalyze NAME / index` | referenslar bilan ishlash |
| `analyze.py VIDEO [--out DIR]` | metadata, kesimlar, shot uzunligi, kadrlar, kontakt varaq |
| `transcribe.py VIDEO --out X.srt [--lang uz] [--max-words 3]` | nutq → SRT (faster-whisper) |
| `render.py projects/NOM [--preview]` | oddiy montaj: edit.json → video |
| `motion.py` | kadrma-kadr motion grafika kutubxonasi: subtitr, ikonkalar, taymer, glass panel, uchqun, barglar, zoom, SFX, `vf`/`af` filtrlar, `bed` musiqa. Loyihada `build.py` yoziladi (`--stills`, `--range`, `--preview`) |
| `fx.py` | umumiy motion-dizayn: 3D matn (`extrude`), harfma-harf (`letter_line`), halqa, nur, HUD qavslar, shisha yorliq (`tag`), uchqun, perspektiva, chiziqli ikonkalar, `TechBackground` (videosiz reels uchun fon) |
| `music.py` | sintez qilingan instrumental (`track`) + ovozga qarab ducking (`duck_bed` → `Renderer.bed`) |
| `check_env.py` | ffmpeg / yt-dlp / whisper tekshiruvi |

ffmpeg/ffprobe PATH'da bo'lmasa ham skriptlar o'zi topadi (winget Gyan.FFmpeg). To'g'ridan-to'g'ri ffmpeg kerak bo'lsa:
`python -c "import sys;sys.path.insert(0,'tools');from common import ffmpeg;print(ffmpeg())"`.

**Videoni "ko'rish"**: `analyze.py` chiqargan `contact.jpg` va `frames/*.jpg` ni Read bilan och. Grafikani tekshirish uchun `build.py --stills`.
**O'zbek nutqi**: `large-v3` modeli va neytral lotin prompt ishlatiladi. Mijoz matnini prompt qilib berma, Whisper uni ko'chirib qo'yadi.
Noaniq so'zlarni mijozdan so'ra.

## edit.json formati (oddiy montaj uchun)

Barcha yo'llar loyiha papkasiga nisbatan.

```json
{
  "output": "export/final.mp4",
  "format": {"width": 1080, "height": 1920, "fps": 30, "fit": "crop"},
  "font": "Montserrat-Bold.ttf",
  "text_style": {"pos": "bottom", "color": "white", "size": 80},
  "clips": [
    {"src": "source/a.mp4", "in": 1.2, "out": 3.5, "text": "Hook matni", "fade_in": 0.2},
    {"src": "source/b.mp4", "in": 0, "out": 2, "fit": "blur", "speed": 1.5, "zoom": 1.1, "mute": true},
    {"src": "source/foto.jpg", "duration": 2.5, "zoom": 1.15,
     "texts": [{"text": "Ikki\nqator", "pos": "center", "start": 0.5, "box": "black@0.5"}]},
    {"src": "source/c.mp4", "in": 4, "out": 7, "filter": "eq=contrast=1.1:saturation=1.2", "lut": "../../assets/luts/x.cube", "fade_out": 0.4}
  ],
  "subtitles": "work/subs.srt",
  "subtitle_style": "FontName=Arial,FontSize=16,Bold=1,Outline=2,MarginV=60,Alignment=2",
  "overlays": [{"src": "../../assets/logos/logo.png", "pos": "tr", "width": 180, "opacity": 0.9}],
  "music": {"src": "../../assets/music/track.mp3", "start": 12, "volume": 0.3, "duck": true, "fade_in": 0.5, "fade_out": 1.5},
  "loudnorm": true, "lufs": -14, "crf": 18
}
```

- `fit`: `crop` (to'ldirib kesish), `pad` (qora chiziqlar), `blur` (xira fon — gorizontal videoni vertikalga).
- `pos`: `top` / `center` / `bottom` yoki ffmpeg ifodasi (`h*0.4`). Matn `\n` bilan qatorlarga bo'linadi.
- `duck`: gap paytida musiqani avtomatik pasaytirish. `.ass` subtitr berilsa uslub o'zidan olinadi.
- Platforma LUFS: Reels/TikTok/YouTube ≈ -14.

## Ish qoidalari

1. **Sessiya boshlanishi** → `studio-start`. **Referens** → `reference-save`. **Montaj** → `video-edit`.
2. Har doim avval `--stills` yoki `--preview` bilan tekshir, keyin final render. Fayl tekshirilmaguncha "tayyor" dema.
3. Xom fayllarni (`source/`, `references/*/video.*`) hech qachon o'zgartirma yoki o'chirma, faqat yangi fayl yarat.
4. Mijoz profilidagi "Qilinmasin" ro'yxatiga har doim amal qil. Narx, xususiyat yoki kontaktni o'ylab topma.
5. Yangi loyihani o'xshash eski loyihaning `build.py` faylidan boshla (namunalar: `styles/SAMPLES.local.md`).
6. **Tiniqlik muqaddas:** grain/noise, vinyetka va tiniqlikni buzadigan post-effektlar ishlatilmaydi (faqat mijoz o'zi so'rasa).
   Final video **bir marta** siqiladi, tayyor faylni qayta siqib "yengil nusxa" qilinmaydi. Zoom ≤1.06.
   Yuborishdan oldin yuz va matnni to'liq o'lchamli crop qilib tiniqlikni tekshir. Mijoz profilida 4K bo'lsa: `upscale=(2160, 3840)`.
7. **GitHub — faqat vositalar.** Repoda mijoz nomi, kontakti, matni, footage yoki natija bo'lmaydi. Kuzatiladigan fayllarda
   (tools, skills, styles, CLAUDE.md) mijozni misol qilib ham yozma — ular `clients/`, `projects/`, `*.local.md` da turadi.
   Commit'dan oldin `python tools/check_public.py --all`. Pre-commit hook mijoz izini topsa, commit'ni to'xtatadi.
