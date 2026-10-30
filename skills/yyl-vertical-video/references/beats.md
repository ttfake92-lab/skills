# 节拍表 `project/film/beats.json`

所有时间可以写秒数，或锚点字符串：

- `"at:词"` 这个词第一个字开始发音的时刻；`"at:词#2"` 第二次出现；`"at:词+0.2"` / `"at:词-0.1"` 偏移。
- `"end:词"` 这个词最后一个字结束的时刻。
- 词按 `words.json` 匹配：去标点、英文小写（`B-roll` 写成 `broll`）。任何字段里的锚点字符串都会被解析。

## 顶层

```json
{
 "duration": 86.566,
 "layout": [{"t": 0, "mode": "split"}, {"t": "at:我只需要", "mode": "full"}, ...],
 "titles": [{"from": 0.05, "to": "at:我只需要", "a": "这条视频", "b": "是AI剪的"}],
 "cta":    [{"from": "at:需要的话", "to": "at:你还有哪些", "at": "at:ai剪辑", "a": "评论区留言", "b": "「AI剪辑」", "c": "领取工作流"}],
 "scenes": [ {"kind": "...", "t0": ..., "t1": ..., ...} ]
}
```

- `layout`：`split` 分屏 / `full` 人物全屏。切换从锚点前 0.12 s 开始，0.34 s 变形完成，自动配 `swish-soft`。全屏时动效区和标题淡出。
- `theme`：渲染器仍支持 `light`，但本风格全片深色，不写这一项（浅色段视觉太跳，用户 2026-10-29 否决）。
- `titles`：分段标题，`a` 上行粗黑体，`b` 下行斜体衬线 + 红下划线。
- `cta`：全屏时代替字幕的大字号召，`b` 在 `at` 时刻砸下（红色斜体衬线）。
- `scenes`：动效区部件，同一时刻只放一个；`t1` 后 0.26 s 模糊退场。`"sfx": [[id, gain, dt], …]` 覆盖默认音效（`[]` 静音）。

## 部件目录（film/split.js `C.*`）

| kind | 用途 | 关键字段 |
|---|---|---|
| `nle` | 剪辑时间线：预览窗轮播缩略图，四条轨道的片段逐个落位，红色播放头 | — |
| `chips` | 清单玻璃卡：图标 + 文字，逐项模糊入场，最新一项变红；`sound` 图标那项带实时波形 | `items[{icon,text,at,hot}]` |
| `rec` | REC 按钮被划掉 + 「不用录」印章 | `strike` |
| `doc` | 文档打字机，`send` 时缩小飞进红色 AI 节点 | `lines[]`, `send` |
| `pipe` | 三步流程：顶部节点 + 进度线，大卡片内容依次换成 文稿 / 实时配音波形 / 数字人画面 | `steps[{icon,label,tool,show:doc|wave|avatar,at}]` |
| `logic` | 红色「叙事逻辑」节点，曲线连到 4 行台词，`match` 时每行弹出对应素材缩略图 | `rows[{text,img}]`, `match` |
| `phones` | 2×2 手机框播放社媒视频，绿色在线点，「社交媒体素材」标签 | `seqs[4]` |
| `window` | macOS 窗口播放录屏，鼠标移动，「我的录屏」标签 | `seq`, `label` |
| `search` | 搜索框打字 → 空结果格 → 抖动 +「未找到合适素材」 | `query`, `fail` |
| `aigen` | AI 生成卡：扫光 + 进度百分比，`reveal` 时从模糊去色变成清晰的 AI 视频 | `seq`, `reveal`, `badge` |
| `code` | 代码编辑器打字（JSON 语法着色，`at:` 锚点标红） | `lines[]` |
| `sync` | 上排口播词、下排动效块，虚线连起来 | `pairs[{word,fx,icon}]` |
| `sfxlane` | 动效块 + 音效波形块，每块出现时真的播放该音效 | `fx[{fx,label,id,gain,decay,at}]` |
| `music` | 曲库列表，`pick` 时选中一首、均衡器跳动 | `tracks[{title,meta}]`, `chosen`, `pick` |
| `gate` | 质检（深色）：缩略图条被扫描、三条检查项打绿勾、响度条指针到 −16 LUFS | `scan`, `checks[{icon,text,at}]`, `meter` |
| `orbit` | 缩略图环绕人物剪影（白色光盘 + 红色发光），`feed` 时飞入，`lock` 锁环闭合，`stamp` 红色印章 | `feed`, `lock`, `stamp`, `stampText` |
| `files` | 文件卡依次滑入，`group` 时收进群聊卡片，红色角标 | `files[{name,icon,at}]`, `group` |
| `comments` | 评论气泡逐条弹出（示意话题，不写用户名和数字） | `items[{text,at}]` |

图标（`icon`）：cut cc film spark sound doc wave user check face sync vol search music lock chat code rec cam。

## 写法

- 先按句子把段落切好，再给每段挑一个部件；部件里每个子元素都锚到说出它的字。
- 每 1.5–3 s 动效区要有一次变化（新一项、新连线、换内容）；连续 4 s 以上没变化就补一个子动作。
- 判断句、自嘲、号召用 `full`；全片人物全屏 15–20%。
- 社媒视频进 `split.json` 的 `broll`（竖版 360×640，录屏 / AI 视频 960×540），缩略图进 `images`（`t0`…`t11`，`nle` / `logic` / `gate` / `orbit` 会用）。
- 改完跑 `render.mjs --mode stills` 抽帧；每个部件看入场中间帧、满状态帧、退场帧。
