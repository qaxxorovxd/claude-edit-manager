# Uslub: kinetik-qizil-urgu

Energiyali kinetik tipografiya. So'zlar aytilishi bilan pop bo'lib chiqadi, urg'u so'zlar qizil va yengil nurli.
Animatsiyali emoji/badge ikonkalar va punch-zoom'lar bor. Asos: kinetik tipografiya referensi (lokal `references/`).

- **Qachon:** ko'cha yoki uy sharoitidagi jonli mahsulot namoyishi, tez va "vau" effektli reels, yoshlar auditoriyasi.
- **Shablon:** namuna loyiha: `styles/SAMPLES.local.md` (lokal, git'ga chiqmaydi). Uning `build.py` fayli nusxalanadi.

## Parametrlar
| Element | Qiymat |
|---|---|
| Subtitr shrifti | Segoe UI Black, KATTA HARFLAR, 92px (hook 118px) |
| Animatsiya | `Captions(pop=True)` — overshoot (ease_out_back), so'zma-so'z, urg'u so'zda "nafas" |
| Ranglar | oq matn + qizil urg'u `#FF2E3B`, glow 0.55 opacity, kuchli qora soya |
| Joylashuvi | 0.72–0.78H (odam ustiga tushmasin). Hook: kattaroq, markazroqda |
| Bo'laklar | 2–3 so'z. Eski bo'lak yangisidan oldin 0.07s da yo'qoladi |
| Ikonkalar | `badge()` (oq doira + qizil MDL2 glif), `emoji()` (faslar va h.k.), `Pop`, `Burst` (uchqun), `Leaves`, `Strike` (qizil X) |
| Maxsus | `Timer` (frosted doira, 0→N soniya), `Pill` (frosted sayt plashkasi), end card (qidiruv satrida yozilish + tugma bosilishi) |
| Zoom | har gap boshida punch (1.0↔1.08–1.16), ease 0.28s, drift 0.008/s |
| SFX | har ikonkada pop, o'tishlarda whoosh, taymerda tick + ding, "ideal" so'zida sparkle, oxirida typing |
| Musiqa | yo'q (yoki trek berilsa `duck_bed`) |
| Ovoz | -14 LUFS |

## Ehtiyot bo'ling
- Glow kuchli bo'lsa, och fonda harflar o'qilmay qoladi. Glow 0.55 dan oshmasin, soya ≥0.8 bo'lsin.
- Tez nutqda bo'laklar ustma-ust tushishi mumkin, `--stills` bilan tekshirish kerak.
