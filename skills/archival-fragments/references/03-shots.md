# 档案剪贴视频提示词写法

**2026-08-17 全面重写。** 旧版是文生视频的六拍长提示词写法，已废弃。现行工作流是首尾帧，提示词的角色从「描述一切」降级为「说清两张图之间怎么走」。

## 一句话原则

**画面内容由关键帧决定，提示词只写运动。** 提示词写长了没有收益，反而会和关键帧打架。

## 固定三段

```
<风格行> <运动句> <禁止行>
```

**风格行**（每镜相同，直接复制）：

```
Monochrome archival black-and-white print on cool ivory paper, matte halftone texture, flat even light. One muted brick crimson accent only. Everything is a real physical object, never a chart or diagram.
```

**运动句**（每镜唯一，一句话，说清主语和方向）：

```
The camera slides across the map away from the pins and the chip piles, settling on eastern China where there is nothing at all but one small empty pin hole.
```

**禁止行**（每镜相同）：

```
One continuous transformation, no cuts, no camera shake. No subtitles, no captions, no watermark.
```

三段加起来通常 300–400 字符，远低于 2000 上限。

## 运动句怎么写

只需要回答两件事：**镜头怎么动**、**画面里什么东西在变**。

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

**不要写时长、快慢、节奏**——由 `duration` 参数和后期变速决定。
**不要重复描述关键帧里已有的东西**——模型看得到图。

## 关键帧的图片提示词另有写法

那部分见 [02-keyframes.md](./02-keyframes.md)。图片提示词要写全画面内容，且必须带这一句排除图表化：

```
Everything is a real physical object photographed on paper — never a chart, never a diagram, never an infographic.
```

## 文字命中率（实测）

关键帧上的文字实测非常稳，35 张关键帧里文字几乎全中：`3.28万亿`、`长鑫科技`、`工商银行`、`SAMSUNG`、`SK HYNIX`、`MICRON`、`LPDDR5 / DDR5 / LPDDR5X`、`7.7%`、`8.66`、`49.5`、`1412`、`2016`。

规则不变：

- 要出的字逐字写进提示词并加引号，一张图最多一处精确文字
- 不要出的字明写成 `unreadable archival micro-text`
- 中文短句直接嵌汉字，H3 与 Seedream 都能逐字渲染

**已知瑕疵**：首尾帧在两张图文字不同时（如 `8.66` → `49.5`），中间态会出现残留字符或假数字。翻牌板这类「本来就该翻动」的载体可以吃掉这个问题，其余情况把变化过程放到镜头外。


## shots.json 结构

```json
{
  "model": "Minimax H3",
  "mode": "frames2video",
  "resolution": "2K",
  "count": 1,
  "seconds": 5,
  "style_line": "Monochrome archival black-and-white print on cool ivory paper, matte halftone texture, flat even light. One muted brick crimson accent only. Everything is a real physical object, never a chart or diagram.",
  "tail": "One continuous transformation, no cuts, no camera shake. No subtitles, no captions, no watermark.",
  "plan": [["N01", ["W01","W02"], [0.62,0.38]], ["N02", ["W03","W04"], null]],
  "shots": [
    {"id": "W09", "from": "A09", "to": "A10",
     "motion": "Hundreds of small black memory chips rain down and scatter loose all across the surface of the map."}
  ]
}
```

完整提示词 = `style_line` + 空格 + 该镜 `motion` + 空格 + `tail`。
`plan` 是镜长分配表：`[旁白句id, [镜id...], 权重]`，权重 `null` 表示平均分。

**自检**：每镜的 `to` 必须等于下一镜的 `from`。

```bash
python3 -c "
import json
d=json.load(open('shots.json'))['shots']
bad=[(d[i]['id'],d[i]['to'],d[i+1]['from']) for i in range(len(d)-1) if d[i]['to']!=d[i+1]['from']]
print('链断裂:', bad or '无')
"
```
