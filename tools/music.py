"""Sintez qilingan tech-commercial instrumental (vokalsiz) + ovozga qarab ducking.

    from music import track, duck_bed
    m = track(30.0, bpm=110, end_at=26.6)          # np[n, 2]
    r.bed = duck_bed(m, level_db=-17)              # motion.Renderer uchun

  python tools/music.py 30 out.wav [--bpm 110] [--end 26.6]  — alohida tinglab ko'rish uchun
"""
import argparse
import wave

import numpy as np

SR = 48000


def hz(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


def fft_filter(x, lo=None, hi=None, order=2):
    """Butun signalni chastota sohasida filtrlash (lo — highpass, hi — lowpass), yumshoq qiyalik."""
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    g = np.ones_like(f)
    if hi:
        g /= np.sqrt(1 + (f / hi) ** (2 * order))
    if lo:
        g /= np.sqrt(1 + (lo / np.maximum(f, 1e-3)) ** (2 * order))
    return np.fft.irfft(X * g, len(x))


def saw(freq, t, harmonics=14):
    out = np.zeros_like(t)
    for k in range(1, harmonics + 1):
        if freq * k > SR / 2.2:
            break
        out += np.sin(2 * np.pi * freq * k * t) / k
    return out


def put(buf, i, sig):
    if i >= len(buf):
        return
    sig = sig[: len(buf) - i]
    buf[i:i + len(sig)] += sig


def track(duration, bpm=110, end_at=None, seed=1,
          chords=((57, (0, 3, 7, 10)), (53, (0, 4, 7, 11)), (48, (0, 4, 7, 11)), (55, (0, 4, 7, 9)))):
    """end_at: shu vaqtda riser -> impact, keyin barabanlar to'xtab, akkord so'nadi."""
    rng = np.random.default_rng(seed)
    n = int(duration * SR)
    beat = 60 / bpm
    bar = 4 * beat
    t_all = np.arange(n) / SR
    stop = end_at if end_at else duration
    L, R = np.zeros(n), np.zeros(n)

    # --- barabanlar
    kick = np.zeros(n)
    tk = np.arange(int(0.4 * SR)) / SR
    k_sig = np.sin(2 * np.pi * np.cumsum(45 + 110 * np.exp(-tk / 0.035)) / SR) * np.exp(-tk / 0.22)
    k_sig += 0.3 * np.exp(-tk / 0.004) * rng.standard_normal(len(tk))
    clap = np.zeros(n)
    tc = np.arange(int(0.3 * SR)) / SR
    c_sig = np.zeros(len(tc))
    for d in (0, 0.011, 0.022):
        c_sig += np.roll(rng.standard_normal(len(tc)) * np.exp(-tc / (0.012 if d < 0.02 else 0.1)), int(d * SR))
    c_sig = fft_filter(c_sig, lo=900, hi=5000)
    hat = np.zeros(n)
    th = np.arange(int(0.08 * SR)) / SR
    h_sig = fft_filter(rng.standard_normal(len(th)), lo=7000) * np.exp(-th / 0.018)
    nb = int(stop / beat)
    for b in range(nb):
        tb = b * beat
        put(kick, int(tb * SR), k_sig)
        if b % 4 in (1, 3):
            put(clap, int(tb * SR), c_sig)
        put(hat, int((tb + beat / 2) * SR), h_sig)
        put(hat, int((tb + beat / 4) * SR), h_sig * 0.35)
        put(hat, int((tb + 3 * beat / 4) * SR), h_sig * 0.35)
    # sidechain "nafas" (kick bilan pompalanish)
    phase = (t_all % beat)
    side = 1 - 0.55 * np.exp(-phase / 0.11)
    side[t_all >= stop] = 1

    # --- akkordlar: pad, bas, arpejio
    pad_l, pad_r, bass, arp_l, arp_r = (np.zeros(n) for _ in range(5))
    nbar = int(np.ceil(duration / bar))
    for bi in range(nbar):
        root, iv = chords[bi % len(chords)]
        s, e = int(bi * bar * SR), min(n, int((bi + 1) * bar * SR))
        if s >= n:
            break
        tt = np.arange(e - s) / SR
        env = np.minimum(1, tt / 0.08) * np.minimum(1, (e - s) / SR - tt + 0.02) ** 0.3
        for j, i in enumerate(iv):
            f = hz(root + i + 12 * (j == 0))
            pad_l[s:e] += saw(f * 0.997, tt + j * 0.01, 10) * env
            pad_r[s:e] += saw(f * 1.003, tt + j * 0.013, 10) * env
        # bas: 8-taliklar
        for k in range(8):
            ts = bi * bar + k * beat / 2
            if ts >= stop:
                break
            tb = np.arange(int(beat / 2 * SR * 0.95)) / SR
            fb = hz(root - 12 if root >= 52 else root)
            sig = np.tanh(2.2 * (np.sin(2 * np.pi * fb * tb) + 0.3 * np.sin(4 * np.pi * fb * tb))) * np.exp(-tb / 0.16)
            put(bass, int(ts * SR), sig)
        # arpejio: 16-taliklar
        notes = [root + 12 + i for i in iv] + [root + 24]
        for k in range(16):
            ts = bi * bar + k * beat / 4
            if ts >= stop:
                break
            ta = np.arange(int(0.25 * SR)) / SR
            f = hz(notes[(k * 3) % len(notes)])
            sig = (np.sin(2 * np.pi * f * ta) + 0.25 * np.sin(6 * np.pi * f * ta)) * np.exp(-ta / 0.07)
            target = arp_l if k % 2 == 0 else arp_r
            put(target, int(ts * SR), sig * (0.8 if k % 4 == 0 else 0.5))
    pad_l, pad_r = fft_filter(pad_l, lo=180, hi=2200), fft_filter(pad_r, lo=180, hi=2200)
    bass = fft_filter(bass, hi=900)
    arp_l, arp_r = fft_filter(arp_l, lo=400, hi=6000), fft_filter(arp_r, lo=400, hi=6000)

    # --- boshlanish zarbasi, riser, yakuniy impact
    fx = np.zeros(n)
    crash_t = np.arange(int(2.0 * SR)) / SR
    crash = fft_filter(rng.standard_normal(len(crash_t)), lo=4000) * np.exp(-crash_t / 0.6)
    boom_t = np.arange(int(1.4 * SR)) / SR
    boom = np.sin(2 * np.pi * np.cumsum(38 + 70 * np.exp(-boom_t / 0.08)) / SR) * np.exp(-boom_t / 0.5)
    boom = np.pad(boom, (0, len(crash) - len(boom)))
    put(fx, 0, crash * 0.35 + boom * 0.8)
    if end_at:
        rl = 1.3
        rt = np.arange(int(rl * SR)) / SR
        riser = fft_filter(rng.standard_normal(len(rt)), lo=1500, hi=9000) * (rt / rl) ** 2.2
        riser += 0.3 * np.sin(2 * np.pi * np.cumsum(200 + 900 * (rt / rl) ** 2) / SR) * (rt / rl) ** 2
        put(fx, int((end_at - rl) * SR), riser * 0.5)
        put(fx, int(end_at * SR), crash * 0.5 + boom * 1.0)
        # oxirgi akkord: impactdan keyin pad so'nadi
        tail = t_all >= end_at
        fade = np.clip(1 - (t_all - end_at) / max(0.1, duration - end_at), 0, 1)
        for arr in (pad_l, pad_r):
            arr[tail] *= fade[tail] * 1.3
        for arr in (bass, arp_l, arp_r):
            arr[t_all >= end_at + 0.05] = 0

    drums = kick * 0.9 + clap * 0.35
    L = drums + hat * 0.15 + (bass * 0.55 + pad_l * 0.16 + arp_l * 0.12) * side + fx * 0.7
    R = drums + hat * 0.12 + (bass * 0.55 + pad_r * 0.16 + arp_r * 0.12) * side + fx * 0.7
    out = np.stack([L, R], 1)
    fi = int(0.02 * SR)
    out[:fi] *= np.linspace(0, 1, fi)[:, None]
    fo = int(min(1.0, duration * 0.1) * SR)
    out[-fo:] *= np.linspace(1, 0, fo)[:, None] ** 2
    out = np.tanh(out / np.abs(out).max() * 1.4) / np.tanh(1.4)  # yumshoq limiter
    return (out * 0.9).astype(np.float32)


def rms_env(x, win=0.02):
    """Mono RMS konvert (namunama-namuna, chiziqli interpolyatsiya)."""
    m = x.mean(1) if x.ndim == 2 else x
    w = int(win * SR)
    k = len(m) // w
    r = np.sqrt((m[: k * w].reshape(k, w) ** 2).mean(1) + 1e-12)
    return np.interp(np.arange(len(m)), np.arange(k) * w + w / 2, r)


def duck_bed(music, level_db=-17, duck_db=-9, attack=0.04, release=0.35):
    """motion.Renderer.bed uchun funksiya: ovoz bor joyda musiqa duck_db ga pasayadi.
    level_db — ovozsiz joydagi musiqa darajasi (ovoz RMS'iga nisbatan)."""
    def bed(voice):
        n = len(voice)
        m = np.zeros((n, 2), np.float32)
        m[: min(n, len(music))] = music[:n]
        env = rms_env(voice)
        speech = env > np.percentile(env, 60) * 0.35
        vr = np.sqrt((voice.mean(1)[speech] ** 2).mean()) if speech.any() else 0.05
        mr = np.sqrt((m.mean(1) ** 2).mean()) + 1e-9
        base = vr / mr * 10 ** (level_db / 20)
        # ovoz -> silliq gain (tez pasayish, sekin qaytish)
        tgt = np.where(speech, 10 ** (duck_db / 20), 1.0)
        g = np.empty_like(tgt)
        a_up, a_dn = np.exp(-1 / (release * SR)), np.exp(-1 / (attack * SR))
        cur = 1.0
        step = 64  # tezlik uchun blokma-blok
        for i in range(0, n, step):
            v = tgt[i]
            a = a_dn ** step if v < cur else a_up ** step
            cur = v + (cur - v) * a
            g[i:i + step] = cur
        return m * (base * g)[:, None]
    return bed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("duration", type=float)
    ap.add_argument("out")
    ap.add_argument("--bpm", type=float, default=110)
    ap.add_argument("--end", type=float)
    a = ap.parse_args()
    x = track(a.duration, a.bpm, a.end)
    with wave.open(a.out, "wb") as w:
        w.setnchannels(2), w.setsampwidth(2), w.setframerate(SR)
        w.writeframes((x * 32767).astype(np.int16).tobytes())
    print("Saqlandi:", a.out)


if __name__ == "__main__":
    main()
