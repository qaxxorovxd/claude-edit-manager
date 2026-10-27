# Uslub: minimal-auto

Minimalist, avtomobil kayfiyatidagi uslub. Kino kabi ochilish, kam va aniq grafika: bitta holat chipi, ingichka
qavslar, kichik shisha yorliqlar, sovuq aksent rang, sekin zoom'lar, past va chuqur musiqa.
Avto aksessuarlar, salon ichidagi namoyish va mashina bilan bog'liq mahsulotlar uchun.

- **Shablon:** namuna loyiha: `styles/SAMPLES.local.md` (lokal, git'ga chiqmaydi).

## Parametrlar
| Element | Qiymat |
|---|---|
| Palitra | oq matn, sovuq aksent `#7FD8FF` (ambient yorug'lik), holat: yashil `#34D399`, qizil `#FF5C5C`; brend CTA so'zi orange |
| Shisha chip | `fx.tag(tint=(10,12,16), tint_a≈0.6)`, h≈96, Inter SemiBold 42 / Medium 40, ixtiyoriy pulsatsiyalanuvchi rangli nuqta |
| Ochilish | 0–2.4s letterbox (har biri 10% balandlik) + keng harfli `C A R P L A Y` (Montserrat SemiBold 92, harf orasi asta yaqinlashadi), ingichka chiziq, kichik subtitle |
| Hikoya | bitta chip holati o'zgaradi (muammo qizil ● → yechim yashil ●) — matn emas, holat |
| Callout | ingichka oq qavslar (3px), kuzatiladigan obyektga halqa — markaz va radius manba kadridan vaqt bo'yicha o'lchanadi (keyframe) |
| Qadamlar | chap tepada 01 / 02 / ✓, har biri shisha fonda (yorug' osmonda ham o'qiladi) |
| Subtitr | `Captions(fname="inter:SemiBold", upper=False, pop=False, glow=False, shadow=0.85)`, 58px, 0.715H, aksent so'zlar sovuq ko'k |
| Zoom | sekin (ease 0.6–2.5s), ≤1.05, drift 0.0015 |
| Rang | `eq=contrast=1.07:saturation=0.96:gamma=0.98,colorbalance=bs=0.04:bm=0.02,unsharp=5:5:0.25` |
| Musiqa | `track(bpm=92, chords=past minor)`, `duck_bed(-17, -11)` — fonda zo'rg'a sezilsin |
| SFX | juda kam: chip'larda tick, yechimda ding, ochilish va yakunda whoosh + thump |
| End card | 235 alfa qorong'ilashish, logo, ingichka chiziq, bir qatorli tavsif, sayt chipi, telefon |
| Chiqish | 4K `upscale=(2160, 3840)`, crf 16, grain/vinyetka yo'q |

## Ehtiyot bo'ling
- Footage'ga yopishtirilgan watermark yoki telefon raqami bo'lsa, ular qayerdaligini o'lchang va subtitr hamda chip'larni ulardan uzoqroq qo'ying.
- Qo'lda olingan kadrda obyekt qimirlaydi. Halqa yoki qavslar uchun 0.4s qadam bilan keyframe oling.
