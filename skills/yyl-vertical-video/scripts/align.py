#!/usr/bin/env python3
"""Script → per-character times → caption cards.

  align.py --task <dir> [--scribe project/transcripts/voice.scribe.json] [--pad 1.0]

Reads project/captions.src.txt (one spoken phrase per line, `|` splits it into caption cards — the reference films show
2–8 characters at a time) and Scribe's character timestamps of the final voice (padded 1 s in front; --pad subtracts it).
Writes project/words.json ({chars:[{c,t0,t1}]}, script characters only, punctuation dropped) and project/captions.json
({cards:[{text,t0,t1,i0,i1}]}); i0/i1 index into words.chars so beats can anchor to「at:词」.
Characters ASR got wrong (同音字、英文拼写) keep the script text and borrow the matched neighbour's time.
"""
import argparse, difflib, json, re
from pathlib import Path

PUNCT = re.compile(r"[\s，。、？！：；“”‘’「」,.?!:;\"'()（）…—-]")


def norm(s):
    return PUNCT.sub("", s).lower()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True)
    ap.add_argument("--scribe", default="project/transcripts/voice.scribe.json")
    ap.add_argument("--pad", type=float, default=1.0)
    ap.add_argument("--gap", type=float, default=0.3, help="close gaps between cards shorter than this")
    a = ap.parse_args()
    root = Path(a.task)
    sc = json.loads((root / a.scribe).read_text())
    asr = []
    for w in sc["words"]:
        if w.get("type") != "word":
            continue
        chars = w.get("characters") or [{"text": w["text"], "start": w["start"], "end": w["end"]}]
        for ch in chars:
            for c in norm(ch["text"]):
                asr.append((c, ch["start"] - a.pad, ch["end"] - a.pad))
    lines = [l.strip() for l in (root / "project/captions.src.txt").read_text().splitlines() if l.strip()]
    cards_txt = [p for l in lines for p in l.split("|")]
    script = "".join(norm(p) for p in cards_txt)
    sm = difflib.SequenceMatcher(None, script, "".join(c for c, _, _ in asr), autojunk=False)
    times = [None] * len(script)
    for b in sm.get_matching_blocks():
        for k in range(b.size):
            times[b.a + k] = asr[b.b + k][1:]
    # fill misses by interpolation between matched neighbours
    known = [i for i, t in enumerate(times) if t]
    for i in range(len(times)):
        if times[i] is None:
            lo = max([k for k in known if k < i], default=None)
            hi = min([k for k in known if k > i], default=None)
            if lo is None: times[i] = times[hi]
            elif hi is None: times[i] = times[lo]
            else:
                f = (i - lo) / (hi - lo)
                t = times[lo][1] + f * (times[hi][0] - times[lo][1])
                times[i] = (t, t + 0.05)
    miss = len(script) - len(known)
    for i, t in enumerate(times):   # Scribe gives interjections (哦) zero length: let them run until the next character
        if t[1] - t[0] < 0.06:
            nxt = times[i + 1][0] if i + 1 < len(times) else t[0] + 0.3
            times[i] = (t[0], max(t[0] + 0.06, min(nxt, t[0] + 0.35)))
    chars = [{"c": c, "t0": round(t[0], 3), "t1": round(t[1], 3)} for c, t in zip(script, times)]
    cards, i = [], 0
    for p in cards_txt:
        n = len(norm(p))
        cards.append({"text": p.replace("“", "「").replace("”", "」"), "i0": i, "i1": i + n - 1, "t0": chars[i]["t0"], "t1": chars[i + n - 1]["t1"]})
        i += n
    for c, d in zip(cards, cards[1:]):
        if d["t0"] - c["t1"] < a.gap:
            c["t1"] = d["t0"]
    (root / "project/words.json").write_text(json.dumps({"text": script, "chars": chars}, ensure_ascii=False, indent=0))
    (root / "project/captions.json").write_text(json.dumps({"cards": cards}, ensure_ascii=False, indent=1))
    print(f"{len(script)} chars, {miss} not matched by ASR (interpolated), {len(cards)} caption cards")


if __name__ == "__main__":
    main()
