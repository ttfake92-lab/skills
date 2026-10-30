#!/usr/bin/env python3
"""Voice + sound effects + ducked music → one master WAV at -16 LUFS / -1.5 dBTP.

  mix.py --task <dir> --cues media/build/data/cues.json [--music assets/audio/music/x.wav] [--out media/build/audio/master.wav]
         [--sfx-bus -7] [--music-under -26] [--music-free -20]

cues.json comes from `render.mjs --mode cues` (film.cues(): [{t, id, gain}]). Each id is looked up in the shared library
skills/talking-head-reel/assets/sfx-library.json and placed so its anchor (peak of a whoosh, onset of a hit) lands on t + at.
Music is levelled to --music-free LUFS where nobody talks and pulled down to --music-under under the voice by a
voice-envelope sidechain (attack 60 ms, release 450 ms) — the reference reels keep the bed audible but never on top.
Writes a stems folder next to the master (voice / sfx / music) for the editable project.
"""
import argparse
import json
import subprocess
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
THR = HERE.parent.parent / "talking-head-reel"   # owner of the shared SFX library (paths in it are relative to that skill)
SR = 48000


def load(path, ch=2):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-ac", str(ch), "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, ch).copy()


def save(path, a):
    path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", str(a.shape[1]), "-i", "-",
                    "-c:a", "pcm_s24le", str(path)], input=a.astype(np.float32).tobytes(), check=True)


def lufs(a):
    """Integrated loudness via ffmpeg ebur128 (stereo float)."""
    p = subprocess.run(["ffmpeg", "-v", "info", "-f", "f32le", "-ar", str(SR), "-ac", str(a.shape[1]), "-i", "-",
                        "-af", "ebur128=peak=true", "-f", "null", "-"], input=a.astype(np.float32).tobytes(), capture_output=True)
    lines = p.stderr.decode().splitlines()
    i = [l for l in lines if l.strip().startswith("I:")][-1]
    tp = [l for l in lines if l.strip().startswith("Peak:")][-1]
    return float(i.split()[1]), float(tp.split()[1])


def db(x):
    return 10 ** (x / 20)


def follower(env, att, rel):
    out = np.empty_like(env); y = 0.0
    a, r = np.exp(-1 / (att * SR / 100)), np.exp(-1 / (rel * SR / 100))
    for i, v in enumerate(env):           # env is at 100 Hz
        y = a * y + (1 - a) * v if v > y else r * y + (1 - r) * v
        out[i] = y
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True)
    ap.add_argument("--cues", default="media/build/data/cues.json")
    ap.add_argument("--music")
    ap.add_argument("--music-align", choices=["start", "end"], default="end", help="when the music is longer than the film")
    ap.add_argument("--out", default="media/build/audio/master.wav")
    ap.add_argument("--sfx-bus", type=float, default=-7.0, help="dB on the whole effects bus")
    ap.add_argument("--music-under", type=float, default=-27.0, help="music LUFS (short-term target) under the voice")
    ap.add_argument("--music-free", type=float, default=-20.0, help="music LUFS where nobody talks")
    a = ap.parse_args()
    root = Path(a.task)
    cfg = json.loads((root / "project/split.json").read_text())
    voice = load(cfg["voice"])
    n = int(round(cfg["duration"] * SR))
    voice = np.pad(voice, ((0, max(0, n - len(voice))), (0, 0)))[:n]
    vl, _ = lufs(voice)
    voice *= db(-16.5 - vl)

    lib = json.loads((THR / "assets/sfx-library.json").read_text())["sounds"]
    cues = json.loads((root / a.cues).read_text())
    sfx = np.zeros((n, 2), np.float32)
    cache, missing = {}, set()
    for q in cues:
        s = lib.get(q["id"])
        if not s:
            missing.add(q["id"]); continue
        if q["id"] not in cache:
            cache[q["id"]] = load(THR / s["file"])
        clip = cache[q["id"]] * q.get("gain", 1)
        start = int(round((q["t"] + s.get("at", 0) - s.get("anchor", 0)) * SR))
        if start < 0:
            clip, start = clip[-start:], 0
        end = min(n, start + len(clip))
        if end > start:
            sfx[start:end] += clip[:end - start]
    sfx *= db(a.sfx_bus)

    music = np.zeros((n, 2), np.float32)
    if a.music:
        m = load(root / a.music)
        if a.music_align == "end" and len(m) > n:
            # a length-edited track ends on its own cadence: keep that ending on the last frame, trim the intro instead
            m = m[len(m) - n:].copy(); fi = int(0.4 * SR); m[:fi] *= np.linspace(0, 1, fi)[:, None]
        m = np.pad(m, ((0, max(0, n - len(m))), (0, 0)))[:n]
        ml, _ = lufs(m)
        m *= db(a.music_free - ml)
        hop = SR // 100
        k = n // hop
        env = np.sqrt((voice[:k * hop, 0].reshape(k, hop) ** 2).mean(1))
        talk = (env > db(-45)).astype(np.float32)
        g = follower(talk, 0.06, 0.45)
        duck = db((a.music_under - a.music_free) * g)
        duck = np.repeat(duck, hop)
        duck = np.pad(duck, (0, n - len(duck)), mode="edge")
        fade = np.ones(n, np.float32); f = int((0.15 if a.music_align == 'end' else 0.6) * SR); fade[-f:] = np.linspace(1, 0, f)
        music = m * (duck * fade)[:, None]

    mix = voice + sfx + music
    il, _ = lufs(mix)
    mix *= db(-16.0 - il)
    peak = np.abs(mix).max()
    lim = db(-1.5)
    if peak > lim:                      # soft knee above -3 dBFS keeps transients of hits from clipping
        knee = db(-3.0)
        x = np.abs(mix); over = x > knee
        mix[over] = np.sign(mix[over]) * (knee + (lim - knee) * np.tanh((x[over] - knee) / (lim - knee)))
    out = root / a.out
    save(out, mix)
    stems = out.parent / "stems"
    for name, s in (("voice", voice), ("sfx", sfx), ("music", music)):
        save(stems / f"{name}.wav", s * db(-16.0 - il))
    fl, ftp = lufs(mix)
    print(f"master -> {out}  {fl:.1f} LUFS / {ftp:.1f} dBFS peak; {len(cues)} cues"
          + (f"; missing sfx ids: {sorted(missing)}" if missing else ""))


if __name__ == "__main__":
    main()
