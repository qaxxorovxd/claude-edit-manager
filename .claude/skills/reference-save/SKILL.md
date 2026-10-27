---
name: reference-save
description: Foydalanuvchi yoqqan video referensni (link yoki fayl) nom berib saqlash, tahlil qilish va uslubini yozib qo'yish. "Shu yoqdi", "referens qilib saqla", "save reference", link yuborilganda yoki saqlangan referensni qidirish/ko'rsatish so'ralganda ishlat.
---

# Referensni saqlash

1. **Nom**: foydalanuvchi nom bermagan bo'lsa, qisqa tavsifiy nom taklif qil (masalan "Tez kesimli kofe reklamasi") va tasdiqlat. Teglar: format (reels, youtube), janr (reklama, vlog, podkast), uslub (tez-montaj, kinematik, matnli).
   Referens ma'lum bir mijoz uchun bo'lsa, teglarga mijoz slug'ini qo'sh (masalan `brend-nomi`) va
   `clients/<m>/profile.md` "Didi va afzalliklari" ga havola yoz.
2. **Saqla** (ildiz papkadan):
   ```
   python tools/ref.py add "<URL yoki fayl>" --name "<Nom>" --tags reels,reklama --note "<foydalanuvchi nima yoqdi>"
   ```
   - Nutq muhim bo'lsa `--transcribe` qo'sh.
   - Instagram/TikTok yuklanmasa: `--cookies chrome` (yoki edge).
   - `inbox/` dagi fayl bo'lsa yo'lini ber.
3. **Ko'r**: `references/<slug>/analysis/contact.jpg` ni, so'ng `frames/` dan 6-12 tasini Read bilan och. `meta.json` dagi `avg_shot_sec`, `cuts_per_min`, `cuts` ga qara.
4. **Uslub tahlili**: `references/<slug>/notes.md` dagi bo'limlarni aniq, raqamlar bilan to'ldir (ritm, kadrlar, o'tishlar, matn uslubi, rang, ovoz, hook). "Qayta qo'llash uchun retsept" bo'limiga edit.json'ga to'g'ridan-to'g'ri o'tkaziladigan parametrlar yoz: format, fit, shot uzunligi oralig'i, text_style, filter (rang), musiqa hajmi.
5. Foydalanuvchiga qisqa xulosa: nom, papka, 3-4 ta asosiy uslub belgisi.

Uslub qayta ishlatishga arziydigan bo'lsa, `styles/<nom>.md` yarat (styles/INDEX.md ga qo'sh).

Qidirish: `python tools/ref.py list [--tag X]`, `python tools/ref.py show "<nom>"`, yoki `references/INDEX.md`.
