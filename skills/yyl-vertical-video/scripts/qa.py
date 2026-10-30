#!/usr/bin/env python3
"""Quality gate before delivery — every check must pass (exit 1 otherwise).

  qa.py --task <dir> [--video output/<stem>_vN.mp4] [--master media/build/audio/master.wav]

  face      render.mjs --mode qa: per frame the speaker's face box and every caption box (split and fullscreen layouts);
            a caption that overlaps the face by more than 2 % of the face area is a violation
  sync      every caption card starts within 0.12 s of the first character it shows (words.json, from the final voice's
            transcript) and ends no earlier than its last character; cards do not overlap
  loudness  master integrated -16 ± 1 LUFS, true peak ≤ -1.0 dBTP; voice-free stretches longer than 1 s are not silent
  video     (with --video) 1080×1920, fps = the film's, duration = voice ± 1 frame, video bitrate ≥ 12 Mbps, AAC 48 kHz,
            and no near-black single frames (talking-head-reel qa_frames.py flashes)
Writes logs/qa-<date>.json with every number it measured.
"""
import argparse
import datetime
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILLS = HERE.parent.parent
FILM = HERE.parent / "film/split.js"


def overlap(a, b):
    x0, y0 = max(a[0], b[0]), max(a[1], b[1])
    x1, y1 = min(a[0] + a[2], b[0] + b[2]), min(a[1] + a[3], b[1] + b[3])
    return max(0, x1 - x0) * max(0, y1 - y0)


def check_face(root, out):
    qa = root / "media/build/data/qa.jsonl"
    src = json.loads((root / "media/build/data/source.json").read_text())
    beats = json.loads((root / "project/film/beats.json").read_text())
    nf = int(round(beats["duration"] * src["fps"]))
    subprocess.run(["node", SKILLS / "lighttrail/tools/render.mjs", "--film", FILM, "--project", root / "project", "--media",
                    root / "media/build", "--mode", "qa", "--from", "0", "--to", str(nf - 1), "--size", "1080x1920", "--out", qa],
                   check=True, capture_output=True)
    bad = []
    for ln in qa.read_text().splitlines():
        r = json.loads(ln)
        face = r["face"]; fa = face[2] * face[3]
        for b in r["boxes"]:
            if b["tag"] == "caption" and overlap(face, [b["x"], b["y"], b["w"], b["h"]]) > 0.02 * fa:
                bad.append(r["f"])
    out["face"] = {"frames": nf, "violations": len(bad), "first": bad[:10]}
    return not bad


def check_sync(root, out):
    chars = json.loads((root / "project/words.json").read_text())["chars"]
    cards = json.loads((root / "project/captions.json").read_text())["cards"]
    late, early_end, over = [], [], []
    for i, c in enumerate(cards):
        if abs(c["t0"] - chars[c["i0"]]["t0"]) > 0.12:
            late.append(c["text"])
        if c["t1"] < chars[c["i1"]]["t1"] - 0.08:
            early_end.append(c["text"])
        if i and c["t0"] < cards[i - 1]["t1"] - 1e-3:
            over.append(c["text"])
    out["sync"] = {"cards": len(cards), "offStart": late, "endsEarly": early_end, "overlapping": over}
    return not (late or early_end or over)


def ebur(path):
    p = subprocess.run(["ffmpeg", "-v", "info", "-i", str(path), "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True)
    ls = p.stderr.splitlines()
    i = float([l for l in ls if l.strip().startswith("I:")][-1].split()[1])
    tp = float([l for l in ls if l.strip().startswith("Peak:")][-1].split()[1])
    return i, tp


def check_loud(root, master, out):
    i, tp = ebur(master)
    out["loudness"] = {"integrated": i, "truePeak": tp}
    return abs(i + 16) <= 1.0 and tp <= -1.0


def check_video(root, video, out):
    p = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,codec_name,width,height,r_frame_rate,"
                                   "bit_rate,sample_rate:format=duration,bit_rate", "-of", "json", str(video)],
                                  capture_output=True, text=True, check=True).stdout)
    v = next(s for s in p["streams"] if s["codec_type"] == "video")
    a = next((s for s in p["streams"] if s["codec_type"] == "audio"), None)
    n, d = map(int, v["r_frame_rate"].split("/"))
    beats = json.loads((root / "project/film/beats.json").read_text())
    res = {"size": f"{v['width']}x{v['height']}", "fps": n / d, "duration": float(p["format"]["duration"]),
           "videoMbps": round(int(v.get("bit_rate") or p["format"]["bit_rate"]) / 1e6, 2), "audio": a and f"{a['codec_name']} {a['sample_rate']}"}
    fl = subprocess.run([sys.executable, SKILLS / "talking-head-reel/scripts/qa_frames.py", "flashes", "--video", str(video)],
                        capture_output=True, text=True, cwd=SKILLS / "talking-head-reel/scripts")
    res["flashes"] = (fl.stdout + fl.stderr).strip().splitlines()[-3:]
    out["video"] = res
    ok = (res["size"] == "1080x1920" and abs(res["duration"] - beats["duration"]) <= 1.5 / res["fps"] + 0.05
          and res["videoMbps"] >= 12 and a is not None and a["codec_name"] == "aac" and fl.returncode == 0)
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True)
    ap.add_argument("--video")
    ap.add_argument("--master", default="media/build/audio/master.wav")
    ap.add_argument("--skip-face", action="store_true")
    a = ap.parse_args()
    root = Path(a.task).resolve()
    out, ok = {}, {}
    if not a.skip_face:
        ok["face"] = check_face(root, out)
    ok["sync"] = check_sync(root, out)
    ok["loudness"] = check_loud(root, root / a.master, out)
    if a.video:
        ok["video"] = check_video(root, root / a.video, out)
    out["pass"] = ok
    log = root / f"logs/qa-{datetime.date.today():%Y%m%d}.json"
    log.write_text(json.dumps(out, ensure_ascii=False, indent=1))
    print(json.dumps(out, ensure_ascii=False, indent=1))
    sys.exit(0 if all(ok.values()) else 1)


if __name__ == "__main__":
    main()
