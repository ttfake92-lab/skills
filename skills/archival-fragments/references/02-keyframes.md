# 阶段 2：设计关键帧链

## 为什么是首尾帧

文生视频要靠提示词描述运动，提示词越写越长、越来越不可控，而且镜与镜之间必然跳变。

首尾帧（`frames2video`）把控制权交给两张图：运动方向、变化的元素、起止状态全部由图决定，提示词只留一句话。而且**首帧 ≠ 尾帧从结构上保证画面在动**，不会生成静止镜。

## 链式串联

**第 N 镜的尾帧和第 N+1 镜的首帧是同一个文件。**

```
A01 ──W01──> A02 ──W02──> A03 ──W03──> A04 ...
```

34 个镜头只要 35 张图，每个接点像素级严丝合缝。

## ⚠ 最容易犯的致命错误

**"共用"只发生在相邻两镜之间的那一个接点。整片不是共用一张图。**

已经真实发生过的翻车：Agent 拿一张结构图当所有镜头的输入，结果几十个镜头画面一模一样，整条片子等于一张静态图配了段旁白。

**硬规矩**：

1. `A01 … A(n+1)` 每一张都是**不同的画面**，各有各的提示词
2. 除了 `reuse` 明确标注的复用，不允许两张关键帧内容相同
3. `assets/style-reference.png` 是**给人看的风格参考板**，永远不要作为任何一次生成的图片输入
4. 生成关键帧用的是**文生图**（只有提示词），不挂任何参考图

看 `assets/example-01..08-*.jpg` 这八张连续帧——空地图 → 芯片扫成三堆 → 三根图钉 → 空钉孔 → 天平 → 三级台阶 → 四级领奖台 → 结尾空台阶。这就是"每镜画面必须不同"的样子。

**自检**：

```bash
python3 -c "
import json
d=json.load(open('keyframes.json'))
ks=d['keyframes']
descs=[k.get('desc','') for k in ks]
print('关键帧张数:', len(ks))
print('描述有重复:', len(descs)!=len(set(descs)), [x for x in descs if descs.count(x)>1])
print('缺提示词:', [k['id'] for k in ks if 'prompt' not in k and 'reuse' not in k])
"
```

`关键帧张数` 必须等于镜头数 + 1；`描述有重复` 必须是 `False`；`缺提示词` 必须是空。

## keyframes.json 结构

```json
{
  "image_model": "Seedream 5.0 Pro",
  "ratio": "4:3",
  "style_prefix": "Monochrome archival black-and-white print on cool ivory paper, matte halftone print texture, flat even soft light, short soft pale grey shadows, nothing glossy. One accent colour only: a muted brick crimson, not pure red, covering only a few percent of the frame. Everything is a real physical object photographed on paper — never a chart, never a diagram, never an infographic. No subtitles, no captions, no watermark.",
  "keyframes": [
    {"id": "A09", "desc": "世界地图，没有任何图钉",
     "prompt": "A large old printed world map filling the entire frame, engraved coastlines and faint graticule lines on ivory paper, pinned flat at its corners. There are no pins, no markers and no highlights anywhere on it."},
    {"id": "A10", "desc": "地图上散着一大堆芯片",
     "prompt": "A large old printed world map filling the frame, with a great scattered heap of small black memory chips lying loose all over its surface, hundreds of them, unsorted."}
  ]
}
```

`style_prefix` 每张都拼在最前面。**里面那句 `never a chart, never a diagram, never an infographic` 不能删**——删了模型会滑向图表化。

## 每张关键帧的提示词怎么写

写成**一个静止的画面状态**，不是一段运动。运动由相邻两张的差值产生。

一句话交代清楚三件事：**画面里有什么物件 → 它们什么状态 → 红色在哪**。

参考 `examples/keyframes.json` 里那 35 张的原文。**不要直接照抄**——那是为"某公司市值第一"这个题材设计的符号，换题材要重新找。照抄出来就是另一种"全片一个样"。

## 文字

- 要出的字**逐字写进提示词并加引号**，一张图最多一处精确文字
- 不要出的字明写成 `unreadable archival micro-text`
- 中文短句直接嵌汉字，Seedream 能逐字渲染

实测稳定命中的例子：`3.28万亿`、`长鑫科技`、`SAMSUNG`、`SK HYNIX`、`MICRON`、`LPDDR5 / DDR5 / LPDDR5X`、`7.7%`、`8.66`、`49.5`、`1412`、`2016`。

## 复用

确实需要同一张画面在片中出现两次时，用 `reuse`：

```json
{"id": "A27", "reuse": "A03", "desc": "贴纸占据中心，四周账册"}
```

复用的帧除了拷文件，**还必须在画布上建同名图片节点**，否则下一步 `--left` 解析不到：

```bash
cp keyframes/A03.png keyframes/A27.png
libtv upload A27 -t image --resource keyframes/A27.png
```

复用要克制。一条 34 镜的片子复用超过 8 张，说明画面推进不够。
