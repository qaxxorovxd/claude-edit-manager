# Uslub: premium-tech-commercial

Toza va premium texnika reklamasi. Ibora bo'yicha chiqadigan, yumshoq ko'tariladigan subtitrlar. Navy rangdagi
frosted-glass kartalar, bir xil qalinlikdagi chiziqli ikonkalar, minimal HUD yorliqlar, sintez qilingan
elektron musiqa va brendli end card.

- **Qachon:** do'kon ichida mahsulot obzori, texnik xususiyatlarni tushuntirish, brend imidji muhim bo'lganda.
- **Shablon:** namuna loyiha: `styles/SAMPLES.local.md` (lokal, git'ga chiqmaydi).

## Parametrlar
| Element | Qiymat |
|---|---|
| Palitra | Blue `#287BFF`, Cyan `#00D9FF` (asosiy), Orange `#FF8A24` (faqat CTA/brend), White, Navy `#101828` |
| Subtitr | Segoe UI Black 74px, KATTA HARFLAR, `Captions(pop=False, glow=False, shadow=0.75, accent_scale=1.08)` |
| Joylashuvi | yaqin plan 0.78H, o'rta 0.74H, keng 0.73H. Mahsulot tepadan ko'ringan kadrda 0.845H |
| Grafikalar (build.py ichida) | `Card` (navy glass + sarlavha + chiziq + plitkalar), `tile()` (ko'k gradient + oq chiziqli ikonka), `icon()` (ball/flat/bullet/fork/dumbbell/house/briefcase/compress/cable/globe/bolt), `speed_dot` (1–N indikator), `HudLabel` (yorliq + mahsulotga chiziq), `Chip`, `LogoPill`, `EndCard` (navy panel pastdan ko'tariladi) |
| Grafika joyi | ekran tepasi 0.14–0.17H (keng plandagi bo'sh tokchalar), yuzdan yuqorida |
| Zoom | sahna kesimida keskin `(t, 1.0, 0)`, muhim iboralarda 1.04–1.09 punch, drift 0.006/s |
| Rang | `eq=contrast=1.05:saturation=1.05:gamma=0.99,unsharp=5:5:0.3` |
| Ovoz | `highpass=80, afftdn nr=8, EQ (-1.5dB@250, +1.5dB@3.2k), deesser, acompressor 2.5:1` |
| Musiqa | `music.track(bpm=110, end_at=END+0.3)` + `duck_bed(level_db=-15, duck_db=-10)` |
| SFX | kam: kartalarda whoosh, plitkalarda tick (ko'tariluvchi ohang), muhim so'zda thump, end card'da impact |
| Natija | -14 LUFS, true peak ≤ -1.5 dB |

## Shriftlar
Montserrat / Inter / Space Grotesk tavsiya etiladi (`assets/fonts/google/`, README'ga qarang). Ular bo'lmasa,
Segoe UI Black / Semibold va Bahnschrift ishlatiladi.
