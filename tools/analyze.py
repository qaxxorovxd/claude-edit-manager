"""Videoni tahlil qilish: metadata, kesimlar (scene cuts), kadrlar va kontakt varaq.

  python tools/analyze.py VIDEO [--out DIR] [--threshold 0.3] [--max-frames 40]

Natija DIR ichida: frames/NNN_mm-ss.jpg, contact.jpg, analysis.json
"""
import argparse
import json
import re
import statistics
from pathlib import Path

from common import ffmpeg, fmt_time, probe, run


def detect_cuts(video, threshold):
    r = run([ffmpeg(), "-hide_banner", "-i", video, "-an", "-vf",
             f"select='gt(scene,{threshold})',showinfo", "-f", "null", "-"], quiet=True)
    return [round(float(t), 2) for t in re.findall(r"pts_time:([\d.]+)", r.stderr)]


def analyze(video, out: Path, threshold=0.3, max_frames=40) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    frames = out / "frames"
    frames.mkdir(exist_ok=True)
    for f in frames.glob("*.jpg"):
        f.unlink()

    info = probe(video)
    dur = info["duration"] or 1
    cuts = detect_cuts(video, threshold)
    bounds = [0.0] + cuts + [dur]
    shots = [round(b - a, 2) for a, b in zip(bounds, bounds[1:]) if b - a > 0.05]

    # Har bir shot o'rtasidan bitta kadr (ko'p bo'lsa — teng taqsimlab)
    mids = [(a + b) / 2 for a, b in zip(bounds, bounds[1:]) if b - a > 0.05]
    if len(mids) > max_frames:
        step = len(mids) / max_frames
        mids = [mids[int(i * step)] for i in range(max_frames)]
    for i, t in enumerate(mids, 1):
        name = f"{i:03d}_{fmt_time(t).replace(':', '-')}.jpg"
        run([ffmpeg(), "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", video, "-frames:v", "1",
             "-vf", "scale=480:-2", "-q:v", "4", frames / name], quiet=True)

    # Kontakt varaq: butun videodan 16 ta teng oraliqdagi kadr
    run([ffmpeg(), "-v", "error", "-y", "-i", video, "-vf",
         f"fps=16/{dur:.3f},scale=320:-2,tile=4x4:padding=4:margin=4", "-frames:v", "1",
         "-q:v", "4", out / "contact.jpg"], quiet=True)

    result = {
        **info,
        "cuts": cuts,
        "shot_count": len(shots),
        "avg_shot_sec": round(statistics.mean(shots), 2) if shots else dur,
        "median_shot_sec": round(statistics.median(shots), 2) if shots else dur,
        "cuts_per_min": round(len(cuts) / dur * 60, 1),
        "frames_dir": str(frames),
        "contact_sheet": str(out / "contact.jpg"),
    }
    (out / "analysis.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--out")
    ap.add_argument("--threshold", type=float, default=0.3)
    ap.add_argument("--max-frames", type=int, default=40)
    a = ap.parse_args()
    v = Path(a.video).resolve()
    out = Path(a.out) if a.out else v.parent / f"{v.stem}_analysis"
    r = analyze(v, out, a.threshold, a.max_frames)
    print(json.dumps({k: r[k] for k in r if k != "cuts"}, indent=2, ensure_ascii=False))
    print(f"Kesimlar: {len(r['cuts'])} ta. Kadrlar: {r['frames_dir']}")


if __name__ == "__main__":
    main()
