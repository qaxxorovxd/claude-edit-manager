# AI video montaj studiyasi (Claude Code uchun)

[Claude Code](https://claude.com/claude-code) bilan ishlaydigan ko'p mijozli video montaj ish joyi. Reels va Shorts uchun
kinetik tipografiya, motion grafika, so'z plashkali subtitrlar, HUD callout'lar, sintez musiqa va 4K chiqish bor.
Barcha montaj Python (Pillow + numpy) va ffmpeg bilan kadrma-kadr bajariladi. Tashqi montaj dasturi kerak emas.

Claude bilan o'zbek tilida ishlashga mo'ljallangan, lekin vositalarning o'zi tilga bog'liq emas.

## Imkoniyatlar
- **Studiya tizimi:** mijoz profillari (brend, did, nima qilinmasin), loyihalar holati (`WORKBOARD.md`), fikrlar jurnali.
  Hammasi md fayllarda saqlanadi, shuning uchun Claude'ning konteksti to'lsa ham ma'lumot yo'qolmaydi.
- **Motion grafika** (`tools/motion.py`, `tools/fx.py`): 3D harfma-harf matn, karaoke subtitr, frosted-glass kartalar,
  HUD qavslar, gauge, karusel (perspektiva bilan), uchqunlar, whip o'tishlar, punch-in zoom, end card'lar.
- **Ovoz:** faster-whisper (large-v3) bilan transkripsiya, ffmpeg bilan ovozni tozalash, sintez instrumental va
  ovoz ostida avtomatik ducking (`tools/music.py`), SFX sintezi.
- **Referenslar:** yoqqan videoni URL yoki fayldan saqlash, kesim ritmini tahlil qilish, kontakt varaq (`tools/ref.py`).
- **4K chiqish:** kompozitsiya 1080p da qilinadi, video bir marta lanczos bilan 2160×3840 ga kattalashtirilib siqiladi.

## O'rnatish (Windows)
```bash
winget install Gyan.FFmpeg
pip install -r requirements.txt
```
Shriftlar (Google Fonts, OFL):
```bash
mkdir -p assets/fonts/google && cd assets/fonts/google
curl -L -o Montserrat-VF.ttf  "https://github.com/google/fonts/raw/main/ofl/montserrat/Montserrat%5Bwght%5D.ttf"
curl -L -o Inter-VF.ttf       "https://github.com/google/fonts/raw/main/ofl/inter/Inter%5Bopsz,wght%5D.ttf"
curl -L -o SpaceGrotesk-VF.ttf "https://github.com/google/fonts/raw/main/ofl/spacegrotesk/SpaceGrotesk%5Bwght%5D.ttf"
```
Tekshirish: `python tools/check_env.py`

## Ishlatish
Papkada Claude Code'ni oching va "ishni boshlaymiz" deng. `studio-start` skill'i yangi yoki eski mijozni so'raydi,
loyiha ochadi yoki davom ettiradi. Video yoki audio yuborib "reels yasa" deyish ham kifoya.

## Tuzilma
```
CLAUDE.md          Claude uchun qoidalar (sessiya boshlanishi, xotira intizomi, tiniqlik qoidalari)
.claude/skills/    studio-start, video-edit, reference-save
tools/             motion.py, fx.py, music.py, studio.py, new_project.py, analyze.py, transcribe.py, ref.py, render.py
styles/            qayta ishlatiladigan montaj uslublari (parametrlar jadvali)
clients/  projects/  references/  inbox/  assets/     ← lokal ma'lumotlar, git'ga chiqmaydi (.gitignore)
```

## Maxfiylik
Mijoz ma'lumotlari, footage, audio, logolar va tayyor videolar `.gitignore` orqali repodan butunlay chiqarib tashlangan.
Repoda faqat vositalar va qoidalar bor.
