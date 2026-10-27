"""Nutqni matnga o'girish (faster-whisper) -> SRT.

  python tools/transcribe.py VIDEO [--out subs.srt] [--lang uz] [--model small] [--max-words 4]

--max-words: bitta subtitr qatoridagi so'zlar soni (Reels/Shorts uslubi uchun 2-4).
"""
import argparse
from pathlib import Path

from common import ffmpeg, run


def ts(t):
    h, r = divmod(t, 3600)
    m, s = divmod(r, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int((s % 1) * 1000):03d}"


def transcribe(video, out: Path, lang=None, model="small", max_words=0):
    from faster_whisper import WhisperModel

    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    wav = out.with_suffix(".wav")
    run([ffmpeg(), "-v", "error", "-y", "-i", video, "-vn", "-ac", "1", "-ar", "16000", wav], quiet=True)
    print(f"Whisper '{model}' modeli yuklanmoqda (birinchi marta internetdan yuklaydi)...", flush=True)
    wm = WhisperModel(model, device="auto", compute_type="int8")
    segs, info = wm.transcribe(str(wav), language=lang, word_timestamps=bool(max_words), vad_filter=True)
    items = []
    for s in segs:
        if max_words and s.words:
            ws = list(s.words)
            for i in range(0, len(ws), max_words):
                chunk = ws[i:i + max_words]
                items.append((chunk[0].start, chunk[-1].end, "".join(w.word for w in chunk).strip()))
        else:
            items.append((s.start, s.end, s.text.strip()))
    out.write_text("\n".join(f"{i}\n{ts(a)} --> {ts(b)}\n{t}\n" for i, (a, b, t) in enumerate(items, 1)),
                   encoding="utf-8")
    wav.unlink(missing_ok=True)
    print(f"Til: {info.language} ({info.language_probability:.0%}). {len(items)} qator -> {out}")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--out")
    ap.add_argument("--lang")
    ap.add_argument("--model", default="small")
    ap.add_argument("--max-words", type=int, default=0)
    a = ap.parse_args()
    v = Path(a.video)
    transcribe(v, a.out or v.with_suffix(".srt"), a.lang, a.model, a.max_words)


if __name__ == "__main__":
    main()
