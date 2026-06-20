#!/usr/bin/env python3
"""
cutout.py —— 人物抠图：真人照片 → 干净透明 PNG（封面里的主体）。
描边/投影/发光在 CSS 里做（见 template-thumbnail.html .person），
这里只负责把人从背景里干净地抠出来 + 裁到人物外接框。

⚠️ 喂真人照片。3D 渲染图 / logo / 插画分割会失败。

一次性安装:
    pip install "rembg[cpu]" onnxruntime pillow

用法:
    python3 src/cutout.py input/person.jpg input/person-cut.png
    python3 src/cutout.py input/person.jpg input/person-cut.png --hq   # 边缘更精细但慢很多

模型选择（实测）:
- 默认 u2net_human_seg：~170MB，几十秒，日常够用，是默认。
- --hq → birefnet-portrait：~970MB，边缘最细，但 CPU 上很慢/吃内存，仅在需要发丝级边缘时用。
- --matting：开 alpha matting，边缘更柔但极慢（大图慎用，会先降采样）。
"""
import sys
from pathlib import Path

MAX_SIDE = 1600  # 超过则先降采样，兼顾速度与清晰度


def cutout(src: str, dst: str, hq: bool = False, matting: bool = False):
    from rembg import remove, new_session
    from PIL import Image

    model = "birefnet-portrait" if hq else "u2net_human_seg"
    try:
        session = new_session(model)
    except Exception:
        session = new_session("u2net_human_seg")

    img = Image.open(src).convert("RGBA")
    if max(img.size) > MAX_SIDE:
        img.thumbnail((MAX_SIDE, MAX_SIDE))

    kw = {}
    if matting:
        kw = dict(alpha_matting=True,
                  alpha_matting_foreground_threshold=240,
                  alpha_matting_background_threshold=15,
                  alpha_matting_erode_size=3)
    out = remove(img, session=session, **kw)

    # ⚠️ 保持整幅尺寸（不裁外框）：pop-out 技法要让顶层人物和底层暗化原图精确对齐。
    if "--crop" in sys.argv:
        bbox = out.split()[-1].getbbox()
        if bbox:
            out = out.crop(bbox)

    # 边缘检查：若抠出来几乎是整张（mask 失败），警告
    alpha = out.split()[-1]
    lo, hi = alpha.getextrema()
    if lo == hi:
        print("⚠️  抠图可能失败（alpha 无层次）——这张大概率不是真人照片。")

    Path(dst).parent.mkdir(parents=True, exist_ok=True)
    out.save(dst)
    print(f"✅ 抠图完成: {dst}  {out.size}  (model={model}, matting={matting})")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = {a for a in sys.argv[1:] if a.startswith("--")}
    if len(args) < 2:
        print("用法: python3 src/cutout.py <input.jpg> <output.png> [--hq] [--matting]")
        sys.exit(1)
    cutout(args[0], args[1], hq="--hq" in flags, matting="--matting" in flags)
