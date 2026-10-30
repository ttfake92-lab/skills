#!/usr/bin/env python3
"""One command from prepared media to the delivery file.

  make.py --task <dir> --version v1 [--music assets/audio/music/x.wav] [--samples 3] [--mbps 20] [--skip-render]

  1 cues     render.mjs --mode cues → media/build/data/cues.json (every sound the film asks for)
  2 mix      mix.py → media/build/audio/master.wav (+ stems/)
  3 master   render.mjs --mode frames → media/build/master-<v>.mkv (FFV1, lossless RGB) — and a caption-free picture layer
             master-<v>-nocap.mkv for the editable project (--q-captions 0)
  4 encode   x264 two-pass, High profile, 1080×1920, BT.709 tagged, --mbps video (default 20 Mbps: short-video platforms
             re-encode, so the upload must not already be starved), AAC 320 kb/s 48 kHz → output/<stem>_<v>.mp4
  5 srt      project/captions.json → output/<stem>_<v>.srt
Run qa.py on the result before telling anyone it is done.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILLS = HERE.parent.parent
FILM = HERE.parent / "film/split.js"
RENDER = SKILLS / "lighttrail/tools/render.mjs"


def run(cmd, **kw):
    print("$", " ".join(str(c) for c in cmd)[:200], flush=True)
    return subprocess.run([str(c) for c in cmd], check=True, **kw)


def srt_time(t):
    ms = int(round(t * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True)
    ap.add_argument("--version", required=True)
    ap.add_argument("--music")
    ap.add_argument("--samples", type=int, default=3)
    ap.add_argument("--mbps", type=float, default=20)
    ap.add_argument("--skip-render", action="store_true", help="reuse the existing master (audio-only change)")
    ap.add_argument("--nocap", action="store_true", help="also render the caption-free picture layer")
    a = ap.parse_args()
    root = Path(a.task).resolve()
    cfg = json.loads((root / "project/split.json").read_text())
    beats = json.loads((root / "project/film/beats.json").read_text())
    fps = cfg.get("fps", 30)
    nf = int(round(beats["duration"] * fps))
    b = root / "media/build"
    common = ["--film", FILM, "--project", root / "project", "--media", b, "--size", "1080x1920", "--fps", fps]
    run(["node", RENDER, *common, "--mode", "cues", "--out", b / "data/cues.json"])
    mix = [sys.executable, HERE / "mix.py", "--task", root]
    if a.music:
        mix += ["--music", a.music]
    run(mix)
    master = b / f"master-{a.version}.mkv"
    if not a.skip_render:
        run(["node", RENDER, *common, "--mode", "frames", "--from", "0", "--to", nf - 1, "--samples", a.samples, "--out", master])
        if a.nocap:
            run(["node", RENDER, *common, "--mode", "frames", "--from", "0", "--to", nf - 1, "--samples", a.samples,
                 "--q-captions", "0", "--out", b / f"master-{a.version}-nocap.mkv"])
    out = root / "output" / f"{cfg['output']['stem']}_{a.version}.mp4"
    out.parent.mkdir(parents=True, exist_ok=True)
    br = f"{a.mbps:g}M"
    vf = "scale=out_color_matrix=bt709:out_range=tv:flags=bicubic+accurate_rnd+full_chroma_int,format=yuv420p"
    x264 = ["-c:v", "libx264", "-preset", "slow", "-profile:v", "high", "-b:v", br, "-maxrate", f"{a.mbps * 1.5:g}M",
            "-bufsize", f"{a.mbps * 2:g}M", "-g", str(fps * 2), "-colorspace", "bt709", "-color_primaries", "bt709",
            "-color_trc", "bt709", "-color_range", "tv"]
    log = b / f"x264-{a.version}"
    run(["ffmpeg", "-v", "error", "-y", "-i", master, "-vf", vf, *x264, "-pass", "1", "-passlogfile", log, "-an", "-f", "null", "/dev/null"])
    run(["ffmpeg", "-v", "error", "-y", "-i", master, "-i", b / "audio/master.wav", "-map", "0:v", "-map", "1:a", "-vf", vf, *x264,
         "-pass", "2", "-passlogfile", log, "-c:a", "aac", "-b:a", "320k", "-ar", "48000", "-shortest", "-movflags", "+faststart", out])
    cards = json.loads((root / "project/captions.json").read_text())["cards"]
    srt = out.with_suffix(".srt")
    srt.write_text("".join(f"{i}\n{srt_time(c['t0'])} --> {srt_time(c['t1'])}\n{c['text']}\n\n" for i, c in enumerate(cards, 1)), encoding="utf-8")
    print(f"done -> {out}\n        {srt}")


if __name__ == "__main__":
    main()
