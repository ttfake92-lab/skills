#!/usr/bin/env python3
"""Media for the split-reel render (everything under <task>/media/build/, safe to delete and rebuild).

  prep.py --task <dir> [cam] [faces] [mask] [broll] [images]        (no step = all)

  cam     every A-roll frame at the output fps → build/frames/cam/f_NNNNNN.jpg (lighttrail frame_vf colour path)
  faces   Vision face box per cam frame (normalised, top-left origin), misses filled, 5-frame smoothing
  mask    Vision person segmentation per cam frame → build/frames/mask/f_NNNNNN.png (white + alpha, half size):
          largest region only, temporal blend 0.65/0.35 against edge flicker, eroded 1 px, feathered 1.5 px.
          The person card's pop-out and the fullscreen depth title both read it.
  broll   project/split.json "broll": {key: {path, t0, dur, fit: cover|contain, w, h}} → build/frames/<key>/ JPEG sequences
  images  project/split.json "images": {key: path} → build/img/<key>.<ext>
Always rewrites build/data/media.json and build/data/source.json — the film reads both.

The A-roll is project/split.json "source" (a HeyGen digital human, landscape or portrait). Its own audio is never used:
the voice is the final TTS file (Breeze by default), the avatar was lip-synced to it.
"""
import argparse
import json
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILLS = HERE.parent.parent
sys.path.insert(0, str(SKILLS / "lighttrail/tools"))
from frame_vf import frame_vf  # noqa: E402

SWIFT = {"vision_faces": SKILLS / "talking-head-reel/scripts/vision_faces.swift",
         "person_mask": SKILLS / "talking-head-reel/scripts/person_mask.swift"}


def run(cmd, **kw):
    return subprocess.run([str(c) for c in cmd], check=True, **kw)


def probe(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                        "stream=width,height,r_frame_rate:format=duration", "-of", "json", str(path)],
                       capture_output=True, text=True, check=True)
    d = json.loads(r.stdout)
    s = d["streams"][0]
    n, m = map(int, s["r_frame_rate"].split("/"))
    return {"width": s["width"], "height": s["height"], "fps": n / m, "duration": float(d["format"]["duration"])}


def tool(b, name):
    exe = b / "bin" / name
    if not exe.exists() or exe.stat().st_mtime < SWIFT[name].stat().st_mtime:
        exe.parent.mkdir(parents=True, exist_ok=True)
        run(["swiftc", "-O", "-suppress-warnings", SWIFT[name], "-o", exe])
    return exe


class Task:
    def __init__(self, path):
        self.root = Path(path).resolve()
        self.cfg = json.loads((self.root / "project/split.json").read_text(encoding="utf-8"))
        self.b = self.root / "media/build"
        self.fps = self.cfg.get("fps", 30)

    def save(self, rel, obj):
        p = self.b / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(obj, ensure_ascii=False))


def cam(t):
    src = t.cfg["source"]
    out = t.b / "frames/cam"
    shutil.rmtree(out, ignore_errors=True); out.mkdir(parents=True)
    vf, label, notes = frame_vf(src)
    for m in notes:
        print("cam:", m)
    dur = t.cfg.get("duration") or probe(src)["duration"]
    run(["ffmpeg", "-v", "error", "-y", "-i", src, "-t", f"{dur:.3f}", "-vf", f"fps={t.fps},{vf}", "-q:v", "2",
         "-start_number", "0", out / "f_%06d.jpg"])
    print(f"cam: {len(list(out.glob('f_*.jpg')))} frames ({label})")


def faces(t):
    exe = tool(t.b, "vision_faces")
    raw = t.b / "data/faces.raw.json"
    raw.parent.mkdir(parents=True, exist_ok=True)
    run([exe, t.b / "frames/cam", raw])
    d = json.loads(raw.read_text())
    ks = sorted(int(k) for k in d)
    box = {k: max(d[str(k)], key=lambda q: q[2] * q[3]) for k in ks if d[str(k)]}
    miss = [k for k in ks if k not in box]
    for k in miss:
        if box:
            box[k] = box[min(box, key=lambda j: abs(j - k))]
    sm = {k: [round(sum(box[j][i] for j in range(k - 2, k + 3) if j in box) / len([j for j in range(k - 2, k + 3) if j in box]), 4)
              for i in range(4)] for k in ks}
    t.save("data/faces.json", {"note": "normalised [x,y,w,h], top-left origin", "missing": miss, "faces": sm})
    print(f"faces: {len(ks)} frames, {len(miss)} filled")


def mask(t):
    from PIL import Image, ImageFilter
    import numpy as np
    from scipy import ndimage
    exe = tool(t.b, "person_mask")
    frames = sorted((t.b / "frames/cam").glob("f_*.jpg"))
    W, H = Image.open(frames[0]).size
    w2, h2 = W // 2, H // 2
    tmp_s, tmp_m, out = t.b / "mask-src", t.b / "mask-raw", t.b / "frames/mask"
    for d in (tmp_s, tmp_m, out):
        shutil.rmtree(d, ignore_errors=True); d.mkdir(parents=True)

    def to_png(f):
        Image.open(f).save(tmp_s / f"{f.stem}.png")
    with ThreadPoolExecutor(8) as ex:
        list(ex.map(to_png, frames))
    run([exe, tmp_s, tmp_m])
    prev = None
    for f in frames:
        m = np.asarray(Image.open(tmp_m / f"{f.stem}.png").convert("L").resize((w2, h2), Image.BILINEAR), dtype=np.float32)
        lab, n = ndimage.label(m > 96)
        if n > 1:
            sizes = ndimage.sum(np.ones_like(m), lab, range(1, n + 1))
            m = m * ndimage.binary_dilation(lab == 1 + int(np.argmax(sizes)), iterations=3)
        if prev is not None:
            m = 0.65 * m + 0.35 * prev
        prev = m
        a = Image.fromarray(m.clip(0, 255).astype("uint8")).filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(1.5))
        rgba = Image.new("RGBA", (w2, h2), (255, 255, 255, 0)); rgba.putalpha(a)
        rgba.save(out / f"{f.stem}.png")
    shutil.rmtree(tmp_s); shutil.rmtree(tmp_m)
    print(f"mask: {len(frames)} masks at {w2}×{h2}")


def broll(t):
    for k, s in t.cfg.get("broll", {}).items():
        out = t.b / "frames" / k
        shutil.rmtree(out, ignore_errors=True); out.mkdir(parents=True)
        w, h = s.get("w", 1080), s.get("h", 1920)
        fit = (f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h}" if s.get("fit", "cover") == "cover"
               else f"scale={w}:{h}:force_original_aspect_ratio=decrease")
        if s.get("crop"):
            fit = f"crop={s['crop']}," + fit
        vf, _, _ = frame_vf(s["path"])
        vf = vf.replace("scale=", f"fps={t.fps},{fit},scale=", 1)
        run(["ffmpeg", "-v", "error", "-y", "-ss", str(s.get("t0", 0)), "-i", s["path"], "-t", str(s["dur"]), "-an",
             "-vf", vf, "-q:v", "3", "-start_number", "0", out / "f_%06d.jpg"])
        print(f"broll {k}: {len(list(out.glob('f_*.jpg')))} frames")


def images(t):
    d = t.b / "img"
    d.mkdir(parents=True, exist_ok=True)
    for k, p in t.cfg.get("images", {}).items():
        shutil.copy(p, d / f"{k}{Path(p).suffix.lower()}")


def index(t):
    seq = {d.name: len(list(d.glob("f_*.jpg"))) or len(list(d.glob("f_*.png")))
           for d in (t.b / "frames").iterdir() if d.is_dir()} if (t.b / "frames").exists() else {}
    img = {p.stem: f"img/{p.name}" for p in (t.b / "img").glob("*")} if (t.b / "img").exists() else {}
    t.save("data/media.json", {"seq": seq, "images": img})
    first = t.b / "frames/cam/f_000000.jpg"
    if first.exists():
        from PIL import Image
        w, h = Image.open(first).size
        t.save("data/source.json", {"width": w, "height": h, "fps": t.fps, "frames": seq.get("cam", 0)})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True)
    ap.add_argument("steps", nargs="*")
    a = ap.parse_args()
    t = Task(a.task)
    steps = a.steps or ["cam", "faces", "mask", "broll", "images"]
    for s in steps:
        {"cam": cam, "faces": faces, "mask": mask, "broll": broll, "images": images}[s](t)
    index(t)


if __name__ == "__main__":
    main()
