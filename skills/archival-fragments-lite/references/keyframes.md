# 参考图：怎么设计、怎么写提示词

## 链式串联

**第 N 镜的尾帧和第 N+1 镜的首帧是同一张图。**

```
A01 ──W01──> A02 ──W02──> A03 ──W03──> A04 ...
```

34 个镜头只要 35 张图，而且每个接点是像素级严丝合缝的——因为那真的是同一个文件。

## ⚠ 不要理解成「全片一张图」

"共用"只发生在相邻两镜之间的那**一个接点**。

`A01 … A(n+1)` 每一张都是**不同的画面**，各有各的提示词。除了刻意复用（同一画面在片中出现两次），不允许两张内容相同。

看 `assets/example-01..08-*.jpg` 那八张连续图：空地图 → 芯片扫成三堆 → 三根图钉 → 空钉孔 → 天平 → 三级台阶 → 四级领奖台 → 结尾空台阶。这就是"每镜画面必须不同"的样子。

## 固定风格前缀

每张参考图的提示词 = **这段前缀** + 该张的画面描述。

```
Monochrome archival black-and-white print on cool ivory paper, matte halftone print
texture, flat even soft light, short soft pale grey shadows, nothing glossy. One accent
colour only: a muted brick crimson, not pure red, covering only a few percent of the
frame. Everything is a real physical object photographed on paper — never a chart,
never a diagram, never an infographic. No subtitles, no captions, no watermark.
```

**`never a chart, never a diagram, never an infographic` 这句不能删**——删了模型会滑向图表化，画面变成信息图，观众看不懂。

## 每张的画面描述怎么写

写成**一个静止的画面状态**，不是一段运动。运动由相邻两张的差值产生。

一句话交代三件事：**画面里有什么物件 → 它们什么状态 → 红色在哪**。

示例（对应 `assets/example-01`、`example-02`）：

```
A large old printed world map filling the entire frame, engraved coastlines and faint
graticule lines on ivory paper, pinned flat at its corners. There are no pins, no
markers and no highlights anywhere on it.
```

```
A large old printed world map, with the loose black memory chips now swept into three
big dense piles, and only a few stray chips left scattered across the rest of the map.
Three hands are just withdrawing from the piles.
```

注意第二张是第一张的**下一个状态**，不是另一个场景。

## 文字

- 要出的字**逐字写进提示词并加引号**，一张图最多一处精确文字
- 不要出的字明写成 `unreadable archival micro-text`
- 中文短句直接嵌汉字，主流图片模型都能逐字渲染

实测稳定命中的例子：`3.28万亿`、`长鑫科技`、`SAMSUNG`、`SK HYNIX`、`MICRON`、`LPDDR5 / DDR5 / LPDDR5X`、`7.7%`、`8.66`、`49.5`、`1412`、`2016`。

一张图上塞两处精确文字，必有一处崩。

## 复用

同一画面确实要在片中出现两次时，直接复制文件即可，不用重新生成。但要克制——一条 34 镜的片子复用超过 8 张，说明画面推进不够。

## 出完必须逐张审

三件事：

1. **文字**——有没有崩、有没有多出假字
2. **语义**——观众看不看得懂，会不会理解成别的东西
3. **接点**——这张能不能和前后接上

跑偏的单独重出。**图便宜、视频贵，审图这一步省不得**：一张跑偏的参考图会污染相邻两个镜头。

自检：

```
参考图张数 == 镜头数 + 1        ✓/✗
任意两张的画面描述不重复          ✓/✗
每张都有自己独立的提示词          ✓/✗
```
