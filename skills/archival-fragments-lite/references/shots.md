# 镜头：首尾帧运动句怎么写

## 一句话原则

**画面内容由两张参考图决定，提示词只写运动。**

提示词写长了没有收益，反而会和参考图打架。这是首尾帧相对文生视频最大的优势——控制权交给图，文字只负责说清"怎么走"。

## 固定三段

```
<风格行> <运动句> <禁止行>
```

**风格行**（每镜相同，直接复制）：

```
Monochrome archival black-and-white print on cool ivory paper, matte halftone texture,
flat even light. One muted brick crimson accent only. Everything is a real physical
object, never a chart or diagram.
```

**运动句**（每镜唯一，一句话）：

```
The camera slides across the map away from the pins and the chip piles, settling on
eastern China where there is nothing at all but one small empty pin hole.
```

**禁止行**（每镜相同）：

```
One continuous transformation, no cuts, no camera shake. No subtitles, no captions,
no watermark.
```

三段加起来通常 300–400 字符。

## 运动句只回答两件事

**镜头怎么动**、**画面里什么东西在变**。

已验证有效的动词：

| 类型 | 写法 |
|---|---|
| 推近 | `The camera pushes in on X until it fills the frame` |
| 拉开 | `The camera pulls steadily back, revealing that Y continues beyond` |
| 横移 | `The camera slides across Z, settling on W` |
| 物件进入 | `X slides in from the left and settles onto Y` |
| 物件退出 | `The slips slide away toward the frame edges, uncovering Z` |
| 堆积 | `X pours down in enormous quantity and piles up until it covers Y` |
| 生长 | `Coin after coin stacks up until the pile towers high` |
| 展开 | `The folded drawing opens, one panel lifting and falling flat` |

**不要写时长、快慢、节奏**——由生成时长参数和后期变速决定。
**不要重复描述参考图里已有的东西**——模型看得到图。

## 挂图的顺序

绝大多数工具里，第一张是**首帧**、第二张是**尾帧**。挂反了运动就倒着走。

第 N 镜挂 `A(n)` + `A(n+1)`，第 N+1 镜挂 `A(n+1)` + `A(n+2)`——中间那张两边都用到，这就是接点无缝的原因。

## 时长与变速

多数视频工具最短生成 5 秒，而这个风格每镜通常只用 1–3 秒。

**统一生成 5 秒，剪辑时整条变速到目标时长。不要裁切**——尾帧必须落在下一镜的首帧上，裁了接点就断。

```bash
# 5.17 秒的素材压到 1.85 秒
ffmpeg -i shot.mp4 -filter:v "setpts=0.358*PTS,fps=30" -an out.mp4
```

同一条素材改时长是几秒钟的事，所以**节奏在剪辑台上定，不在提示词里定**。

## 已知瑕疵

两张参考图上的文字不同时（比如 `8.66` → `49.5`），中间过渡帧会出现残留字符或假数字。

翻牌板、滚动屏这类"本来就该翻动"的载体可以吃掉这个问题；其余情况把文字变化放到镜头外。
