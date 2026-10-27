---
name: studio-start
description: Sessiya yoki yangi ishning boshlanishi — mijozni aniqlash (yangi yoki eski), loyihani tanlash yoki ochish, kerakli profil va uslubni yuklash. "Ishni boshlaymiz", "salom", "yangi video", "davom etamiz", video yoki fayl yuborilgan, mijoz yoki loyiha noaniq bo'lgan har qanday holatda ishlat. Yangi mijozni qabul qilish (intake) ham shu yerda.
---

# Studiya: ishni boshlash

## 1. Holatni ko'r
```
python tools/studio.py status
```
Natijani foydalanuvchiga qisqa ko'rsat: faol loyihalar va ularning keyingi qadami.

## 2. Mijozni aniqla
- Xabarda belgi bo'lsa (brend nomi, logo, telefon, fayl nomi, mavzu), mijozni taxmin qil:
  `python tools/studio.py find <so'z>`. Keyin bitta savol bilan tasdiqlat.
- Belgi bo'lmasa, AskUserQuestion ber: **"Bu qaysi mijoz uchun?"** Variantlarga mavjud mijozlarni
  (eng faollari birinchi) va **"Yangi mijoz"** ni qo'y.
- Bir xabarda 2–3 ta video kelsa, har biri qaysi mijozga tegishli ekanini birdaniga so'ra (bitta AskUserQuestion, bir nechta savol).

## 3a. Eski mijoz
1. O'qi: `clients/<m>/profile.md` (did, qilinmasin, brend) va `default_style` uchun `styles/<uslub>.md`.
2. So'ra: **yangi loyihami yoki mavjudini davom ettiramizmi?** Faol loyihalarni variant qilib ber.
3. Davom etilsa: `projects/<loyiha>/project.md` ni o'qi, ayniqsa "Holat / keyingi qadam" va "Mijoz fikrlari".
4. Yangi loyiha bo'lsa: `python tools/new_project.py "<nom>" --client <m> --style <uslub> [--from-inbox]`,
   so'ng `video-edit` skill.
5. Profilda javobi bor savolni qayta berma (masalan logo, sayt, subtitr joyi).

## 3b. Yangi mijoz (intake)
1. `python tools/studio.py client-new "<Nom>" --type brend|shaxs [--contact "..."]`
2. Bir martalik qisqa intake. Bitta AskUserQuestion'da ko'pi bilan 4 ta savol bo'lsin, qolganini matn bilan so'ra:
   - Nima bilan shug'ullanadi, auditoriyasi kim?
   - Brend: logo (fayl), ranglar, shriftlar, sayt, telefon yoki ijtimoiy tarmoq, majburiy CTA.
   - Qaysi uslub yoqadi? Mavjud `styles/` dan tanlash, referens video yoki "o'zing tanla".
   - Platforma va format (Reels 9:16, YouTube 16:9…), davomiylik, subtitr tili.
   - Qilinmasin: yoqmaydigan narsalar.
3. Javoblarni **darhol** `clients/<m>/profile.md` ga yoz. Logo va assetlarni `clients/<m>/assets/` ga ko'chir.
   Mijoz bilmagan joylarni "-" qilib qoldir. Ish davomida bilib olganingni qo'shib bor.
4. Keyin yangi loyiha och (3a.4).

## 4. Doim
- Har bir muhim qaror yoki fikrni o'sha zahoti md ga yoz (CLAUDE.md → "Xotira intizomi").
- Ish oxirida: `python tools/studio.py set <loyiha> status=<holat> next="<keyingi qadam>"`.
