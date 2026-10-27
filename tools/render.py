"""edit.json (montaj rejasi) asosida videoni render qilish.

  python tools/render.py projects/NOM [--preview] [--edit edit.json]

--preview: tez, past sifatli (540p, ultrafast) — tekshirish uchun.
Barcha yo'llar loyiha papkasiga nisbatan. edit.json sxemasi: CLAUDE.md -> "edit.json formati".
"""
import argparse
import json
import shutil
import sys
from pathlib import Path

from common import ASSETS, ffmpeg, is_image, probe, run

FIT = {
    "crop": "scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}",
    "pad": "scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:black",
}
TEXT_POS = {"top": "h*0.12", "center": "(h-text_h)/2", "bottom": "h*0.72"}


def atempo(speed):
    parts = []
    while speed > 2:
        parts.append("atempo=2")
        speed /= 2
    while speed < 0.5:
        parts.append("atempo=0.5")
        speed /= 0.5
    parts.append(f"atempo={speed:.4f}")
    return ",".join(parts)


def prepare_font(proj: Path, font: str | None) -> str:
    """drawtext uchun shriftni work/ ga ko'chiradi (Windows'dagi 'C:' qochirish muammosidan qochish)."""
    cands = []
    if font:
        cands += [proj / font, ASSETS / "fonts" / font, Path("C:/Windows/Fonts") / font]
    cands += sorted((ASSETS / "fonts").glob("*.[ot]tf"))
    cands += [Path("C:/Windows/Fonts/arialbd.ttf"), Path("C:/Windows/Fonts/arial.ttf")]
    src = next((c for c in cands if c.is_file()), None)
    if not src:
        sys.exit("XATO: shrift topilmadi")
    dst = proj / "work" / "fonts" / src.name
    dst.parent.mkdir(parents=True, exist_ok=True)
    if not dst.exists():
        shutil.copy2(src, dst)
    return dst.relative_to(proj).as_posix()


def drawtext(t: dict, i: int, proj: Path, W: int, default_font: str) -> str:
    tf = proj / "work" / f"text_{i:03d}_{t.get('_k', 0)}.txt"
    tf.write_text(t["text"], encoding="utf-8")
    font = prepare_font(proj, t["font"]) if t.get("font") else default_font
    size = t.get("size", round(W / 14))
    y = TEXT_POS.get(t.get("pos", "bottom"), t.get("pos"))
    opts = [f"fontfile={font}", f"textfile={tf.relative_to(proj).as_posix()}", "expansion=none",
            f"fontsize={size}", f"fontcolor={t.get('color', 'white')}", f"x=(w-text_w)/2", f"y={y}",
            f"borderw={t.get('border', max(2, size // 12))}", "bordercolor=black", "line_spacing=8"]
    if t.get("box"):
        opts += ["box=1", f"boxcolor={t['box']}", f"boxborderw={size // 3}"]
    if "start" in t or "end" in t:
        opts.append(f"enable='between(t,{t.get('start', 0)},{t.get('end', 9999)})'")
    return "drawtext=" + ":".join(opts)


def build(proj: Path, edit: dict, preview: bool):
    fmt = edit.get("format", {})
    W, H, FPS = fmt.get("width", 1080), fmt.get("height", 1920), fmt.get("fps", 30)
    if preview:
        W, H = (W // 2) // 2 * 2, (H // 2) // 2 * 2
    fit = fmt.get("fit", "crop")
    (proj / "work").mkdir(exist_ok=True)
    default_font = prepare_font(proj, edit.get("font"))

    inputs, chains, labels = [], [], []
    total = 0.0
    for i, c in enumerate(edit["clips"]):
        src = proj / c["src"]
        if not src.exists():
            sys.exit(f"XATO: klip topilmadi: {src}")
        speed = float(c.get("speed", 1))
        if is_image(src):
            dur = float(c.get("duration", 3))
            vi = len(inputs)
            inputs += [["-loop", "1", "-framerate", str(FPS), "-t", f"{dur:.3f}", "-i", src]]
            has_audio = False
        else:
            info = probe(src)
            a_in = float(c.get("in", 0))
            a_out = float(c.get("out", info["duration"]))
            dur = (a_out - a_in) / speed
            vi = len(inputs)
            inputs += [["-ss", f"{a_in:.3f}", "-t", f"{a_out - a_in:.3f}", "-i", src]]
            has_audio = info["has_audio"] and not c.get("mute")

        v = f"[{vi}:v]setpts=(PTS-STARTPTS)/{speed}"
        cf = c.get("fit", fit)
        if cf == "blur":
            chains.append(f"{v},split[bg{i}][fg{i}]")
            chains.append(f"[bg{i}]{FIT['crop'].format(W=W, H=H)},boxblur=30:4[bgb{i}]")
            chains.append(f"[fg{i}]scale={W}:{H}:force_original_aspect_ratio=decrease[fgs{i}]")
            v = f"[bgb{i}][fgs{i}]overlay=(W-w)/2:(H-h)/2"
        else:
            v += "," + FIT[cf].format(W=W, H=H)
        if c.get("zoom"):  # sekin "Ken Burns" zoom: 1.0 -> zoom
            z = float(c["zoom"])
            v += (f",scale=w='trunc({W}*(1+({z}-1)*t/{dur:.3f})/2)*2':h=-2:eval=frame,"
                  f"crop={W}:{H}")
        v += f",fps={FPS},trim=duration={dur:.3f},setpts=PTS-STARTPTS,setsar=1,format=yuv420p"
        if c.get("filter"):  # ixtiyoriy ffmpeg video filtri (rang, eq, va h.k.)
            v += "," + c["filter"]
        if c.get("lut"):
            v += f",lut3d=file={Path(c['lut']).as_posix()}"
        for k, t in enumerate(c.get("texts", []) + ([{"text": c["text"]}] if c.get("text") else [])):
            t = {**edit.get("text_style", {}), **t, "_k": k}
            if preview and "size" in t:
                t["size"] = t["size"] // 2
            v += "," + drawtext(t, i, proj, W, default_font)
        if c.get("fade_in"):
            v += f",fade=t=in:st=0:d={c['fade_in']}"
        if c.get("fade_out"):
            v += f",fade=t=out:st={max(0, dur - c['fade_out']):.3f}:d={c['fade_out']}"
        chains.append(v + f"[v{i}]")

        if has_audio:
            a = f"[{vi}:a]asetpts=PTS-STARTPTS,{atempo(speed)}"
        else:
            ai = len(inputs)
            inputs += [["-f", "lavfi", "-t", f"{dur:.3f}", "-i", "anullsrc=r=48000:cl=stereo"]]
            a = f"[{ai}:a]asetpts=PTS-STARTPTS"
        a += f",aresample=48000,aformat=channel_layouts=stereo,volume={c.get('volume', 1)}"
        a += f",apad,atrim=0:{dur:.3f}"
        if c.get("fade_in"):
            a += f",afade=t=in:st=0:d={c['fade_in']}"
        if c.get("fade_out"):
            a += f",afade=t=out:st={max(0, dur - c['fade_out']):.3f}:d={c['fade_out']}"
        chains.append(a + f"[a{i}]")
        labels.append(f"[v{i}][a{i}]")
        total += dur

    n = len(edit["clips"])
    chains.append("".join(labels) + f"concat=n={n}:v=1:a=1[vc][ac]")
    vout, aout = "[vc]", "[ac]"

    if edit.get("subtitles"):
        style = edit.get("subtitle_style", "FontName=Arial,FontSize=16,Bold=1,Outline=2,Shadow=0,MarginV=60,Alignment=2")
        sub = Path(edit["subtitles"]).as_posix()
        f = f"subtitles={sub}" + ("" if sub.endswith(".ass") else f":force_style='{style}'")
        chains.append(f"{vout}{f}[vs]")
        vout = "[vs]"

    for k, ov in enumerate(edit.get("overlays", [])):  # logo/watermark
        oi = len(inputs)
        inputs += [["-i", proj / ov["src"]]]
        w = ov.get("width", round(W * 0.18))
        pos = {"tl": "40:40", "tr": "W-w-40:40", "bl": "40:H-h-40", "br": "W-w-40:H-h-40"}[ov.get("pos", "tr")]
        chains.append(f"[{oi}:v]scale={w}:-1,format=rgba,colorchannelmixer=aa={ov.get('opacity', 0.9)}[ov{k}]")
        chains.append(f"{vout}[ov{k}]overlay={pos}[vo{k}]")
        vout = f"[vo{k}]"

    m = edit.get("music")
    if m:
        mi = len(inputs)
        inputs += [["-stream_loop", "-1", "-ss", str(m.get("start", 0)), "-i", proj / m["src"]]]
        fo = m.get("fade_out", 1.5)
        chains.append(f"[{mi}:a]atrim=0:{total:.3f},asetpts=PTS-STARTPTS,aresample=48000,"
                      f"aformat=channel_layouts=stereo,volume={m.get('volume', 0.3)},"
                      f"afade=t=in:st=0:d={m.get('fade_in', 0.5)},afade=t=out:st={max(0, total - fo):.3f}:d={fo}[mus]")
        if m.get("duck", True):
            chains.append(f"{aout}asplit[av1][av2]")
            chains.append("[mus][av2]sidechaincompress=threshold=0.02:ratio=8:attack=20:release=400[musd]")
            chains.append("[av1][musd]amix=inputs=2:duration=first:normalize=0[am]")
        else:
            chains.append(f"{aout}[mus]amix=inputs=2:duration=first:normalize=0[am]")
        aout = "[am]"

    if edit.get("loudnorm", True):
        chains.append(f"{aout}loudnorm=I={edit.get('lufs', -14)}:TP=-1.5:LRA=11,aresample=48000[an]")
        aout = "[an]"

    out = proj / edit.get("output", "export/final.mp4")
    if preview:
        out = out.with_name(out.stem + "_preview.mp4")
    out.parent.mkdir(parents=True, exist_ok=True)
    graph = proj / "work" / "filter_graph.txt"
    graph.write_text(";\n".join(chains), encoding="utf-8")

    cmd = [ffmpeg(), "-hide_banner", "-y"]
    for inp in inputs:
        cmd += inp
    cmd += ["-/filter_complex", graph.relative_to(proj).as_posix(), "-map", vout, "-map", aout,
            "-c:v", "libx264", "-preset", "ultrafast" if preview else edit.get("preset", "medium"),
            "-crf", "28" if preview else str(edit.get("crf", 18)), "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "128k" if preview else "192k", "-movflags", "+faststart", out]
    print(f"Render: {n} klip, {total:.1f}s, {W}x{H}@{FPS} -> {out.relative_to(proj)}", flush=True)
    run(cmd, cwd=proj, quiet=True)
    return out, total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--edit", default="edit.json")
    ap.add_argument("--preview", action="store_true")
    a = ap.parse_args()
    proj = Path(a.project).resolve()
    edit = json.loads((proj / a.edit).read_text(encoding="utf-8"))
    out, total = build(proj, edit, a.preview)
    info = probe(out)
    print(f"Tayyor: {out} ({info['width']}x{info['height']}, {info['duration']:.1f}s, {info['size_mb']} MB)")


if __name__ == "__main__":
    main()
