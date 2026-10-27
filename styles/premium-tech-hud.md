# Uslub: premium-tech-hud

`premium-tech-commercial` ning kuchaytirilgan varianti: high-end tech reklama. Mahsulotga bog'langan HUD callout'lar,
3D kinetik tipografiya, so'z plashkali (karaoke) subtitrlar, whip o'tishlar, kino ko'rinishi (vinyetka va donadorlik)
va mahsulot "suzib" turadigan end card.

- **Qachon:** mahsulot obzori, mijoz "premium", "high-end", "oddiy edit emas" desa.
- **Shablon:** namuna loyiha: `styles/SAMPLES.local.md` (lokal, git'ga chiqmaydi).

## Parametrlar
| Element | Qiymat |
|---|---|
| Shriftlar | Montserrat ExtraBold/Black (`mont:ExtraBold`), Inter SemiBold (`inter:SemiBold`), Space Grotesk Bold (`grot:Bold`) — `assets/fonts/google/` |
| Palitra | Blue `#287BFF`, Cyan `#00D9FF`, Orange `#FF8A24` (CTA va brend so'zlari), White, Navy `#101828` |
| Subtitr | `HighlightCaptions` — Montserrat ExtraBold 64px KATTA HARFLAR, so'z aytilganda chiqadi, aytilayotgan so'z orqasida ko'k→cyan plashka siljiydi (orange so'zlarda orange→amber) |
| Joylashuvi | 0.735–0.785H (odam ustiga tushmasin) |
| Hook | `letter_line` + `extrude`: harfma-harf 3D matn, orqasida cyan nur, shockwave halqasi, yengil punch-in 1.04→1.08 |
| Kinetik so'zlar | asosiy foydani katta 3D tipografiya bilan berish (masalan "QULAY"), shu vaqtda subtitr o'chiriladi |
| Callout'lar | `brackets()` HUD burchaklari, skan nuri, `tag()` shisha yorliqlar. Koordinatalar manba kadriga nisbatan, `zoom.to_screen()` bilan ekranga o'tkaziladi |
| Infografika | karta va plitkalar (chiziqli ikonkalar), segmentli gauge (Space Grotesk raqam), so'zga sinxron yonadigan kartalar |
| O'tishlar | `Whip(t_cut, dur=0.11, zoom=0.12, blur=60, flash_a=0.28)` — qisqa va yengil |
| Post | **Grain va Vignette ishlatilmaydi** — ular kadrni xira qiladi. Toza, keskin kadr |
| Rang | `eq=contrast=1.06:saturation=1.05:gamma=0.99,colorbalance=bs=0.02,unsharp=5:5:0.25` |
| Zoom | punch'lar ≤1.06 (hook ≤1.08), drift 0.002 — kattalashtirish 1080p manbani yumshatadi |
| Chiqish | **4K**: `Renderer(upscale=(2160, 3840), crf=16)` — 1080 da kompozitsiya, bir marta lanczos + unsharp bilan 4K ga. Qayta siqilgan "social" nusxa qilinmaydi |
| End card | navy fon, perspektivali HUD to'r (harakatlanadi), mahsulot freeze-frame kartasi (aksi va yaltirash bilan), logo, CTA, gradient tugma + bosilish halqasi |
| Musiqa | `track(bpm=112)` + `duck_bed(-14, -10)` |
| SFX | thump (hook, kinetik so'z, end card), whoosh (kesimlar), tick (ko'tariluvchi ohang bilan sanash), sparkle (skan, yaltirash) |

## Ish tartibi
1. Kadrlarni koordinata to'ri bilan chiqarib (`work/coords.jpg`), mahsulot, nasadka, qo'l va yuz bbox'larini o'lchash.
2. Har bir grafikani aynan aytilgan so'z vaqtiga bog'lash. Aytilmagan xususiyat qo'shilmaydi.
3. `--stills` bilan har bir sahnani ko'rish: yorliqlar telefon ekranida o'qiladimi (yorliq shrifti ≥ 38px).
