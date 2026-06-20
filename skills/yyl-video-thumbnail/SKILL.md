---
name: yyl-video-thumbnail
description: 生成 B站 / YouTube / 抖音 的高点击「视频封面 / 缩略图」——pop-out 技法：抠图人物全亮叠在自己那张被压暗的原图上、文字压在中间，一套内容用 HTML/CSS 重排成 16:9 / 4:3 / 3:4 三种比例。当用户要视频封面、缩略图、thumbnail、B站封面、YouTube 封面、抖音/视频号竖封面、把人物放封面上、Codex/Agent/AI 视频封面时使用。注意：这是「视频封面」专用，走 YouTube 高设计感美学；要小红书图文/信息图/PPT 风请用 yuyile-social-card-skill。
---

# YYL 视频封面 Skill

做一件事：**给视频做高点击率的封面（缩略图）**。主战场 B站、YouTube、抖音/视频号。

核心技法是 **pop-out**：

```
底层：人物的原始照片，压暗 + 降饱和（保留房间/桌面等环境 → 真实感）
中层：大标题（关键词=黄色实色块），压在暗化原图上
顶层：把人物从原图里抠出来，全亮、原位精确叠回去
      → 人物“从自己的场景里跳出来”，盖住一点文字但关键词照样可读
```

一套内容用 CSS 重排成 **16:9 / 4:3 / 3:4**（重排，不是裁切）。

> 和 `yuyile-social-card-skill` 的分工：那个做小红书图文/信息图/杂志风，克制、编辑感。**这个做视频缩略图，强对比、大主体、高冲击。两套美学，不要混。**

## 何时用 / 不用

**用**：视频封面、缩略图、thumbnail、B站/YouTube/抖音封面、把"我"放封面上、AI/Codex/Agent/开源工具类视频封面。

**不用**：小红书图文/信息图/杂志风 → `yuyile-social-card-skill`；翻页 PPT → PPT skill；纯 AI 绘图。

## 一次性 setup

```bash
pip install "rembg[cpu]" onnxruntime
python3 -m playwright install chromium
```

## 工作流（Claude 做判断，代码做渲染）

1. **读输入**：用户口语需求 + 一张**真人照片**（要有环境感更好，环境会保留进封面）。
2. **想清楚（你判断，别写死规则，见 `references/brand-system.md`）**：
   - 标题砍到 8–16 字、断 2–3 行、哪个词做黄色块
   - 主题 → kicker 小标签
   - 人物在原图的左还是右 → `person_side`
3. **抠图**：`python3 src/cutout.py <照片> input/person-cut.png`
   - ⚠️ 输出**整幅**（不裁外框），这样顶层人物能和底层原图精确对齐。
4. **写 brief.json**：见 `examples/codex/brief.json`。`photo`=原图，`person_image`=抠图，**两者必须是同一张**。
5. **渲染**：`python3 src/render.py <brief.json> output/` → 3 张高清 PNG。
6. **视觉自检**：看输出图，对照 `references/brand-system.md` 的「合格/不合格」清单。关键词被人物挡到读不出、背景压太暗/太亮，就调 `focus` 或字号重渲。
7. 交付 + 简述取舍。

## 品牌铁律（写死）

- **pop-out 三层不能破**：暗化原图(留环境) → 文字 → 全亮抠图人物(原位对齐)。
- 人物全亮跳出、第一主体；标题第二，关键词用**黄色实色块**(招牌记忆点)。
- 人物可盖住部分文字，但**关键词必须仍可读**。
- 字体：拉丁用 Archivo Black，中文用 PingFang(系统最重)；要更狠就放 Heavy 中文字体到 `assets/fonts/` 接 `@font-face`。
- 背景压暗适度，**别压死**——环境要看得见才有真实感。
- 品牌签名：左下角**只放「@鱼亦乐」文字，无 logo**。
- 三比例各自重排，不是裁切。禁止绿色大字。
- **来源宽高比自动适配**：横图(≥1.2)做 3:4 时自动切「上方标题带 + 下方照片带」，竖图全铺。建议 16:9 用横图、3:4 优先用竖图拍。

## 三套模板（brief 里 `template` 字段切换，互不混用）

| 模板 | 风格 | 标题处理 | 适合 |
|---|---|---|---|
| `popout`（默认） | 深色海报风 | 大白字 + **黄色实色块**关键词，人物全亮跳出 | 大多数视频，强冲击 |
| `ui` | 深色命令面板风 | 标题做成"在 AI 工具里输入的查询"`✦ … ⌘↵` + 结果行 | 工具 / AI / 自动化类 |
| `paper` | 浅色胶片编辑风 | 褪色(近黑白)照片 + **胶片颗粒 + 半调网点**(中性不发黄)；关键词用 **iOS 文本选中**（黄底 + 蓝手柄）+ iOS 右键菜单紧贴选区上方 | 观点 / 故事 / 高级感选题 |

`popout`/`ui` 是深色 pop-out（暗化原图 + 全亮人物）；`paper` 是浅色（褪色照片 + 胶片颗粒/半调网点，人物褪色不跳出）。三套都带 @鱼亦乐 签名，但视觉语言不同，**不要在一张图里混用**。
- `ui`：用 `results` 字段给结果行（缺省用 `subtitle`）。
- `paper`：用 `menu` 字段给 iOS 右键菜单浮层（字符串列表，可省）；关键词 `[方括号]` 自动渲染成 iOS 选中高亮。

## brief.json 字段

| 字段 | 说明 |
|---|---|
| `template` | `popout`(默认) / `ui` / `paper` |
| `name` | 输出文件名前缀 |
| `kicker` | 左上小标签（如 `CODEX · SKILL`），可省 |
| `title` | 标题；`\n` 换行，`[方括号]` 包关键词=黄色实色块 |
| `subtitle` | 副标题，可省 |
| `photo` | **原图**路径（底层背景，保留环境） |
| `person_image` | **抠图**路径（顶层人物，须与 `photo` 同源、整幅） |
| `person_side` | `right`(默认) / `left` |
| `focus` | 取景焦点 object-position，可省（默认按竖图调好）；可传字符串统一或按比例 `{"16x9":"50% 30%",...}` |
| `brand_name` | 默认 `@鱼亦乐`（纯文字，无 logo） |
| `person_grade` | `mono`=黑白人物；省略=全彩 |
| `results` | （仅 `ui`）命令面板结果行，列表，每项 `{icon,label,sel}`；缺省用 `subtitle` |
| `menu` | （仅 `paper`）iOS 右键菜单浮层，字符串列表，可省 |
| `component` | （仅 `popout`）可选钩子组件（终端/GitHub），见 `references/components.md`；默认不放更干净 |
| `ratios` | 默认 `["16x9","4x3","3x4"]` |

## 文件

- `references/brand-system.md` —— ★核心：pop-out 美学规则、配色、标题、验收清单。**每次开工前读。**
- `references/components.md` —— 可选钩子组件规格。
- `assets/template-popout.html` —— 深色海报风模板（默认）。
- `assets/template-ui.html` —— 深色命令面板风模板。
- `assets/template-paper.html` —— 浅色纸质编辑风模板（iOS 选中高亮）。
- `src/cutout.py` —— rembg 抠图（整幅输出）。
- `src/render.py` —— 三层合成 + Playwright 精确截 3 张。
- `examples/codex/brief.json` —— 输入示例。
