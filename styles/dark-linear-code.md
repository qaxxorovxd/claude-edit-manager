# Uslub: dark-linear-code

Texnik tushuntirish videolari (explainer) uchun qorong'i, chiziqli, kodli uslub. Butun video **bitta uzluksiz arxitektura
diagrammasi** bo'lib, gapga qarab rivojlanadi: tugunlar paydo bo'ladi, so'rov paketlari oqadi, holatlar o'zgaradi.
Kesimlar yo'q, kamera va diagramma silliq o'zgaradi. Kalit so'zlar: dark, linear, coding, motion, tech SFX va musiqa.

- **Qachon:** dasturlash va IT tushunchalari (load balancer, cache, API, DB, queue...), faqat ovoz berilganda.
- **Shablon:** namuna loyiha: `styles/SAMPLES.local.md` (lokal, git'ga chiqmaydi).

## Parametrlar
| Element | Qiymat |
|---|---|
| Fon | `#06080C`, 60px qadamli nuqtali to'r, sekin pastga suriladigan skan nuri. Grain va vinyetka yo'q |
| Chiziqlar | 2px `#2C3644`, bezier bog'lanishlar. Neon nur: qatlamni ¼ o'lchamda blur qilib orqasiga qo'shish (`line_glow`) |
| Ranglar | so'rov cyan `#4CE0FF`, sog'lom green `#3DFF9A`, yuk/ogohlantirish amber `#FFB547`, xato red `#FF4D5E`, matn white, ikkinchi darajali `#788698` |
| Shriftlar | sarlavha Space Grotesk Bold (`grot:Bold`); kod, yorliq, HUD — Consolas (`consola.ttf`/`consolab.ttf`); subtitr Inter Bold |
| Glif | Consolas'da ✓ ✗ yo'q, ularning o'rniga matn ishlatiladi (`OK`, `FAIL`, `DOWN`). `→` va `↑` bor |
| Subtitr | `HighlightCaptions` 58px, 0.86H, qorong'i rangli plashkalar (cyan/green/amber/red ohangli), shadow 0 |
| Bo'limlar | yuqori chapda `// 01 · MUAMMO` mono yorliq va uzun chiziq. Bo'lim almashganda whoosh |
| Sarlavha | terminal uslubida harfma-harf yoziladi, blok kursor miltillaydi, ustida `> what_is --topic` |
| Kod kartasi | `file.py` oynasi, harflar tegishli gap davomida yoziladi, kalit so'zlar binafsha |
| Haqqoniylik | yuk %, holatlar va paketlar simulyatsiyadan hisoblanadi (o'ylab topilgan raqam yo'q) |
| SFX | yozuv tick'lari, bo'lim whoosh'i, qulashda thump + pasayuvchi tick'lar, health-check tick, tiklanishda ding |
| Musiqa | `track(bpm=100, chords=dark minor (A2 F2 D2 E2))`, `duck_bed(-15, -9)` |
| Chiqish | 9:16, 4K `upscale=(2160, 3840)`, crf 16 |
