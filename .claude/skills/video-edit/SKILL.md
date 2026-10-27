---
name: video-edit
description: Videoni montaj qilish — xom videolardan reels/shorts/youtube video yig'ish, kesish, motion grafika, subtitr, musiqa, rang, referens yoki mijoz uslubida montaj, tuzatishlar. "Montaj qil", "videoni tayyorla", "kesib ber", "subtitr qo'sh", "shu referensdek qil", "tuzat" deganda ishlat. Mijoz yoki loyiha noaniq bo'lsa, avval studio-start.
---

# Video montaj ish oqimi

## 0. Kontekst (har doim, kod yozishdan oldin)
- Mijoz va loyiha aniq bo'lsin (aks holda `studio-start`).
- O'qi: `clients/<m>/profile.md` (did, qilinmasin, brend) → `styles/<uslub>.md` → `projects/<loyiha>/project.md`.
- Mijoz brief yoki prompt yuborsa → `clients/<m>/briefs/<sana>-<mavzu>.md` ga saqla, project.md "Brief" bo'limiga havola qo'y.

## 1. Loyiha
```
python tools/new_project.py "<Nom>" --client <m> --format 9:16 --style <uslub> [--ref "<referens>"] [--from-inbox]
python tools/studio.py set <loyiha> status=jarayonda next="Material tahlili"
```
Fayllar `inbox/` da bo'lmasa, yo'lini so'rab `projects/<slug>/source/` ga nusxala.

## 2. Materialni o'rganish
- Har bir manba: `python tools/analyze.py projects/<slug>/source/<fayl> --out projects/<slug>/work/an_<fayl>`.
  Keyin `contact.jpg` va kerakli `frames/` ni Read bilan ko'r. Yuz, qo'l va mahsulot kadrning qayerida ekanini belgila.
- Nutq: mijoz matn bergan bo'lsa, so'z vaqtlarini o'sha matn bilan moslashtir. Bermagan bo'lsa, `large-v3`
  va neytral lotin prompt ishlat, noaniq joylarni mijozdan so'ra.
  Tasdiqlangan matnni project.md "Matn / ssenariy" ga yoz.
- Material tavsifini (kadrlar, vaqtlar) project.md "Material" ga yoz.

## 3. Montaj
- **Motion grafikali video** (asosiy yo'l): uslubning namuna `build.py` faylini nusxala
  (`styles/<uslub>.md` → "Namuna"), so'ng WORDS/CHUNKS, grafika vaqtlari, logo va ranglarni moslashtir.
  Kutubxona: `tools/motion.py`, musiqa: `tools/music.py`.
- **Oddiy kesish yoki yig'ish**: `edit.json` + `tools/render.py`.
- Qoidalar: birinchi 1–3 soniyada hook. Profildagi subtitr joyiga amal qil (odatda 0.72–0.78H, odam ustiga tushmasin).
  Faqat aytilgan narsani ko'rsat.
- Videoga xos qarorlarni project.md "Ushbu video uslubi" va "Montaj qarorlari" ga yoz.

## 4. Tekshiruv
```
python projects/<slug>/build.py --stills 1.0,5.2,...     # har bir sahna va grafikadan kadr olib ko'r
python projects/<slug>/build.py                          # final (~2 daqiqa)
```
Tekshiriladi: matn sig'adimi, ustma-ust tushmayaptimi, yuz yoki mahsulot yopilmaganmi, end card to'g'rimi.
Natijani probe qil (o'lcham, davomiylik, ovoz) va LUFS ni o'lcha.

## 5. Topshirish va tuzatish
- Foydalanuvchiga: fayl (`SendUserFile`), davomiylik, nima qilingani, cheklovlar.
- `python tools/studio.py set <loyiha> status=tekshiruvda next="Mijoz fikrini kutish"`.
- Fikr kelsa: `studio.py log <loyiha> "<fikr>"`. U **doimiy did** bo'lsa (masalan "subtitr har doim pastroq"),
  `studio.py client-log <m> "..."` qil va profile.md "Didi va afzalliklari" ga qo'sh.
  Tuzat → qayta render → status yangila.
- Mijoz rozi bo'lsa → `status=tayyor` yoki `topshirildi`.

## Maxsus holatlar
- Imkoniyat bo'lmasa (shrift o'rnatilmagan, musiqa yo'q), eng yaxshi muqobilni ishlat, project.md ga yoz va foydalanuvchiga ayt.
- Shriftlar `assets/fonts/` yoki `clients/<m>/assets/` da bo'ladi. Yuklab olish uchun ruxsat so'ra.
