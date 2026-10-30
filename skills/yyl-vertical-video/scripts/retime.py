#!/usr/bin/env python3
"""Speed up a voice (or a lip-synced avatar video) and set every pause to one length.

  retime.py --in voice.wav  --out voice-fast.wav --speed 1.3 --gap 0.08              # before HeyGen (default path)
  retime.py --in avatar.mp4 --out avatar-fast.mp4 --speed 1.3 --gap 0.08 --map m.json # after HeyGen, no new render

Every silent run longer than the target is cut down so that, after the speed-up, it lasts --gap seconds
(half kept on each side, so word tails and onsets survive). The end keeps --tail seconds.
Video and audio are cut at the same points and sped up together, so lips stay in sync; each cut is a
jump in the picture, softened by --blend frames of cross-fade.
--map writes the kept source spans; --words/--captions remap project/words.json and captions.json through it.
"""
import argparse
import json
import subprocess
from pathlib import Path

import numpy as np

SR = 48000


def load(p):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(p), "-map", "0:a:0", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).copy()


def spans(a, speed, gap, tail, lead=0.0):
    env = np.convolve(np.abs(a), np.ones(480) / 480, "same")
    loud = env > max(env.max() * 0.02, 1e-3)
    idx = np.where(loud)[0]
    first, last = idx[0] / SR, idx[-1] / SR
    k = gap * speed                                # pause length in source time
    keep, cur = [], max(first - lead, 0.0)
    d = np.diff(loud.astype(np.int8))
    starts = np.where(d == -1)[0] + 1              # loud → silent
    ends = np.where(d == 1)[0] + 1                 # silent → loud
    for s in starts:
        e = ends[ends > s]
        if not len(e):
            break
        s0, e0 = s / SR, e[0] / SR
        if s0 < first or e0 > last or e0 - s0 <= k + 0.02:
            continue
        keep.append((cur, s0 + k / 2))
        cur = e0 - k / 2
    keep.append((cur, min(last + tail * speed, len(a) / SR)))
    return keep


def remap(t, keep, speed):
    acc = 0.0
    for s0, s1 in keep:
        if t < s0:
            return acc / speed                     # inside a removed pause → the cut point
        if t <= s1:
            return (acc + t - s0) / speed
        acc += s1 - s0
    return acc / speed


def picture(src, out, aud, keep, speed, fps, blend, total):
    """Output frame j shows the source at its mapped time; the first `blend` frames after a cut cross-fade from the
    footage that continued past the cut (frames from the removed pause) into the new span. Source frames are read
    once, in order, and cached only while a later output frame can still need them."""
    pr = json.loads(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                    "stream=width,height,r_frame_rate", "-of", "json", str(src)], capture_output=True, check=True).stdout)["streams"][0]
    w, h = pr["width"], pr["height"]
    n, d = map(int, pr["r_frame_rate"].split("/")); sfps = n / d
    starts, acc = [], 0.0
    for s0, s1 in keep:
        starts.append(acc / speed); acc += s1 - s0
    nf = int(round(total * fps))
    need = []                                      # per output frame: [(source frame, weight), …]
    for j in range(nf):
        t = j / fps
        i = max(k for k in range(len(keep)) if starts[k] <= t + 1e-9)
        u = t - starts[i]
        cur = int(round((keep[i][0] + u * speed) * sfps))
        k = int(round(u * fps))
        if i > 0 and blend and k < blend:
            wgt = (k + 1) / (blend + 1)
            prev = int(round((keep[i - 1][1] + u * speed) * sfps))
            need.append([(prev, 1 - wgt), (cur, wgt)])
        else:
            need.append([(cur, 1.0)])
    last_use = {}
    for j, fr in enumerate(need):
        for f, _ in fr:
            last_use[f] = j
    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(src), "-map", "0:v:0", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                           stdout=subprocess.PIPE)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}", "-r", str(fps),
                            "-i", "-", "-i", str(aud), "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "medium", "-crf", "12",
                            "-pix_fmt", "yuv420p", "-c:a", "pcm_s24le", "-shortest", str(out)], stdin=subprocess.PIPE)
    size, cache, nxt, lastf = w * h * 3, {}, 0, None
    for j, fr in enumerate(need):
        for f, _ in fr:
            while nxt <= f:
                buf = dec.stdout.read(size)
                if len(buf) < size:
                    break
                if nxt in last_use:
                    cache[nxt] = np.frombuffer(buf, np.uint8).reshape(h, w, 3)
                lastf = nxt; nxt += 1
        frames = [(cache.get(f, cache.get(min(f, lastf))), wt) for f, wt in fr]
        img = frames[0][0] if len(frames) == 1 else sum(x.astype(np.float32) * wt for x, wt in frames).round().astype(np.uint8)
        enc.stdin.write(np.ascontiguousarray(img).tobytes())
        for f, _ in fr:
            if last_use.get(f) == j and f != lastf:
                cache.pop(f, None)
    enc.stdin.close(); enc.wait(); dec.kill()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--speed", type=float, default=1.3)
    ap.add_argument("--gap", type=float, default=0.08)
    ap.add_argument("--tail", type=float, default=0.5)
    ap.add_argument("--fps", type=float, default=25)
    ap.add_argument("--blend", type=int, default=2, help="cross-fade frames at each picture cut")
    ap.add_argument("--map")
    ap.add_argument("--words", help="project/words.json to remap in place")
    ap.add_argument("--captions", help="project/captions.json to remap in place")
    a = ap.parse_args()
    src, out = Path(a.src), Path(a.out)
    keep = spans(load(src), a.speed, a.gap, a.tail)
    total = sum(e - s for s, e in keep) / a.speed
    video = src.suffix.lower() in (".mp4", ".mov", ".mkv")
    n = len(keep)
    asel = "".join(f"[0:a]atrim={s:.4f}:{e:.4f},asetpts=PTS-STARTPTS,afade=t=in:d=0.004,afade=t=out:st={e - s - 0.004:.4f}:d=0.004[a{i}];"
                   for i, (s, e) in enumerate(keep))
    fc = asel + "".join(f"[a{i}]" for i in range(n)) + f"concat=n={n}:v=0:a=1,atempo={a.speed}[ao]"
    if video:
        aud = out.with_suffix(".voice.wav")
        subprocess.run([str(c) for c in ["ffmpeg", "-v", "error", "-y", "-i", src, "-filter_complex", fc, "-map", "[ao]",
                                         "-c:a", "pcm_s24le", aud]], check=True)
        out = out.with_suffix(".mov")
        picture(src, out, aud, keep, a.speed, a.fps, a.blend, total)
        aud.unlink()
    else:
        cmd = ["ffmpeg", "-v", "error", "-y", "-i", src, "-filter_complex", fc, "-map", "[ao]", "-c:a", "pcm_s24le", out]
        subprocess.run([str(c) for c in cmd], check=True)
    print(f"{src.name}: {n} spans, {len(keep) - 1} pauses cut, {sum(e - s for s, e in keep):.2f}s kept → {total:.2f}s at {a.speed}× → {out}")
    if a.map:
        Path(a.map).write_text(json.dumps({"speed": a.speed, "gap": a.gap, "keep": keep, "duration": total}, indent=1))
    for p in (a.words, a.captions):
        if not p:
            continue
        d = json.loads(Path(p).read_text())

        def walk(o):
            if isinstance(o, dict):
                return {k: (round(remap(v, keep, a.speed), 3) if k in ("t0", "t1", "start", "end") and isinstance(v, (int, float)) else walk(v))
                        for k, v in o.items()}
            return [walk(x) for x in o] if isinstance(o, list) else o
        Path(p).write_text(json.dumps(walk(d), ensure_ascii=False, indent=1))
        print("remapped", p)


if __name__ == "__main__":
    main()
