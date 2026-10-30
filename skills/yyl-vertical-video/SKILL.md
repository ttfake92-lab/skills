---
name: yyl-vertical-video
description: 竖屏分屏口播 REEL — 把一份口播脚本做成 1080×1920 的「上方动效 + 下方人物卡」知识 / 观点短视频：Breeze 配音 → 音频驱动 HeyGen 数字人（Avatar V）→ 逐句配素材（TikHub 社媒、自己的录屏、即梦 Seedance AI 视频）→ 代码动效（拉高衬线标题模糊入场、液态玻璃卡片、清单、流程、手机墙、代码、质检表…）每段锚到口播的字 → 按动效出场配音效 → Epidemic 配乐自动避让人声 → 质检门槛（字幕挡脸、字幕对齐、响度、黑帧）。招牌细节：下方圆角人物卡里的人物抠像放大约 16%、底边对齐，头和手冲出卡片上沿，背景被卡片裁在下面，形成立体感。用户说「竖屏口播 / 上面动效下面人 / 人物出框 / 参考这种分屏 reels / 用数字人做一条口播 / 脚本发给你做成片」时使用。不用于：横版口播（talking-head-reel）、实拍长口播删减（talking-head-edit）、无出镜讲解（knowledge-explainer）、vlog。
---

# 竖屏分屏口播 REEL

一份脚本 → 一条竖屏短视频。画面分两层信息：**上方是「正在说的那件事」的动效**，**下方是人**。判断、玩笑、号召切人物全屏；事实、步骤、例子留在分屏。

版式和节奏来自两条参考片的逐帧测量，见 [reference-analysis.md](references/reference-analysis.md)。部件、节拍表格式见 [beats.md](references/beats.md)；每步命令见 [pipeline.md](references/pipeline.md)；用户确认过的修改与落实位置见 [feedback.md](references/feedback.md)，复盘只追加到这里和本 Skill。

## 三份文件

| 文件 | 管什么 |
|---|---|
| `project/split.json` | A-roll（数字人）路径、定稿配音、fps、时长、B-roll 序列、缩略图 |
| `project/captions.src.txt` | 口播稿，一行一句，`|` 切字幕块（2–8 字一块） |
| `project/film/beats.json` | 版式切换、主题明暗、分段标题、动效场景、CTA，全部用 `at:词` 锚到口播 |

渲染模块 `film/split.js` 跑在项目内 `skills/lighttrail` 引擎上（headless Chrome 逐帧）。素材和母版放素材盘，任务夹里 `media` 软链过去。

## 流程

1. **脚本 → 配音**：默认语速 **1.3 倍**、气口统一 **80 ms**（用户 2026-10-29 指定）。按句（到句号 / 问号）分段交 **Breeze**（`scripts/breeze_audio.py`，默认后端，2026-10-30 起；Fish 仅在用户点名时用），`--speed 1.3` 每段单独生成，先 `--dry-run` 报 credits，拼接后跑 `retime.py --speed 1 --gap 0.08` 把所有停顿（句内、句间）统一到 80 ms，再交 HeyGen。已经按 1 倍做好的数字人不用重新生成：`retime.py` 直接处理数字人视频（1.3 倍 + 80 ms，画面和声音同点剪、同步加速，剪点 2 帧叠化），字级时间同步换算。用 ElevenLabs Scribe + Groq 转写核对；同音误读三次重生成仍一样就是声线口音，记进「重点听」，不改稿。
2. **数字人**：HeyGen MCP（会员 credits），**Avatar V**，外部音频走只含这一个文件的短效 `audioUrl`（cloudflared 临时隧道），只提交一次。本会话没注册 `mcp__heygen__*` 时，用 `claude -p` 新起一个进程去生成（新进程会加载 `.mcp.json` 的 HeyGen）。规则以 `docs/macbook/HEYGEN.md` 为准。数字人没到时可以先用旧数字人片段做占位，把包装全部做完，到位后只重跑 `prep.py` 和渲染。
3. **对齐字幕**：`align.py` 把稿子逐字对到 Scribe 字级时间，生成 `words.json`（锚点用）和 `captions.json`。
4. **找素材**（先写进 beats 再检索）：
   - 社媒：`scripts/tikhub.py search/download`（抖音热门），竖版优先，只取画面不取界面和作者信息；
   - 录屏：用户自己的录屏（课程录屏在仓库根目录 `YYYYMMDD-课程节名/`）；
   - 找不到的情境：即梦 `dreamina text2video`，Seedance 2.0（会员积分；`_vip` 通道排队快得多），提示词里写主色（本风格是暗色 + 红色霓虹边光）。
5. **准备媒体**：`prep.py`（逐帧 JPEG、Vision 人脸框、Vision 人像蒙版、B-roll 序列、缩略图）。
6. **写节拍表**：全片深色，不切浅色主题（浅色段落视觉太跳）；每 1.5–3 s 换一个动效状态；列表项、流程节点、勾选都锚到说出它的那个字；分段标题跟着段落换；人物全屏占 15–20%。`render.mjs --mode stills` 抽帧看。
7. **声音**：配乐按片长剪，比片长多出的部分从开头裁掉，让曲子的自然结尾落在最后一帧（`mix.py --music-align end`，默认）。`render.mjs --mode cues` 导出每个出场的音效 → `mix.py`。音效库是共用的 `skills/talking-head-reel/assets/sfx-library.json`（2026-10-29 补了 16 个 Mixkit 免费音效：UI、打字、扫描、锁定、印章、AI 闪光）。配乐用 Epidemic MCP：`SearchRecordings` 选曲 → `EditRecording` 剪到片长 → `DownloadRecordingEdit`；人声下 −27 LUFS、空档 −20 LUFS 自动避让。
8. **成片**：`make.py --version vN`：FFV1 无损母版 → x264 两遍 20 Mbps（可调）+ AAC 320k → `output/<stem>_vN.mp4` + `.srt`。
9. **质检门槛**：`qa.py --video …` 必须全部通过（见下）。不能连续试听时如实写「听感未验收」并列重点听位置。

## 版式默认值（1080×1920）

| 项 | 默认 |
|---|---|
| 背景 | 近黑 `#09090B` + 54 px 细网格（4% 白）+ 两团缓慢漂移的暗红 / 冷蓝光晕（给玻璃折射用）+ 径向暗角；全片深色，不用浅色主题 |
| 字体 | 全部衬线：中文与正文拉丁字母用宋体（Songti SC Light / Regular / Bold / Black），标题里的拉丁字母用 Instrument Serif Italic；只有代码编辑器里的代码用等宽 |
| 分段标题 | 两行居中，纵向拉高 1.22 倍：上行宋体 Black 62 px（y 172），下行宋体 Black 78 px + 斜切 0.2（拉丁 Instrument Serif Italic 92 px，y 282），下行下方红线 5 px 扫出；逐字模糊入场，段落结束模糊退场。CTA 关键词拉高 1.16 倍 |
| 动效区 | y 330–1190，一次只放一个部件 |
| 液态玻璃卡片 | 背后画面模糊 20 px、饱和 180%、提亮 1.3、放大 1.07 倍（透镜感）→ 58–72% 烟灰色底保证文字可读 → 左上高光 → 内缘 14 px 柔光（玻璃厚度）→ 高光描边（左上 60%、右下 32%）→ 入场时一道光带扫过；入场弹性放大并轻微横向压扁回弹（0.55 s） |
| 人物卡 | x 72–1008，顶边 y 1410，圆角 34，底边出画；背景模糊 1.6 px、压暗 20% |
| 人物出框 | 抠像 ×1.16，以卡片底边中点为锚；发顶在卡片顶边上方约 80–110 px；投影 34 px |
| 全屏人物 | 卡片 0.34 s 变形到全屏；进入时 0.35 s 轻推 + 4 s 内慢推 4.5% |
| 字幕 | 白色宋体 Black 62 px，无底板，柔和投影，一块 2–8 字；分屏 y 1262（头顶上方），全屏 y 1300；弹入 0.14 s |
| 主色 | 深红 `rgb(226,28,52)`：当前项、节点、印章、CTA 关键词；绿色只表示「通过 / 在线」 |
| 音效 | 每个可见出场一个，效果总线 −7 dB；换版式 `swish-soft`，标题 `ui-pop-deep`，列表 `ui-blip`，选中 `ui-select` |
| 响度 | −16 LUFS，峰值 ≤ −1 dBTP |
| 语速 | 1.3 倍，所有气口 80 ms |
| 成片 | 1080×1920，帧率跟数字人（HeyGen Avatar V 出 25 fps，`split.json` 的 `fps` 照填，不插帧），H.264 High 20 Mbps 两遍，AAC 320 kb/s |

## 验收门槛（缺一项不算完成）

- `qa.py` 的 `face`：任何一帧字幕 / CTA 与人脸框重叠不超过脸面积的 2%。
- `sync`：每张字幕卡的开始与它第一个字的发音差 ≤ 0.12 s，不提前结束、不互相重叠。
- `loudness`：−16 ± 1 LUFS，峰值 ≤ −1 dBTP。
- `video`：1080×1920、时长对上配音、视频码率 ≥ 12 Mbps、AAC，`qa_frames.py flashes` 无单帧黑闪。
- 抽帧看每个部件的进场、换版式中间帧、人物出框（发顶、手、肩膀边缘没有锯齿和残影）。
- 素材：社媒画面不带作者头像和昵称；AI 生成的镜头在画面里标明「AI 生成」。

## 坑

- 渲染器每帧取多个子帧时间；视频序列的帧号必须按整帧号算（`seqIdx`），否则子帧会取到没预取的帧，画面变黑。
- beats 里任何 `"at:…"` / `"end:…"` 字符串都会被解析成秒，字段名不限。
- 横版数字人放到全屏竖屏要放大约 1.8 倍，脸框很大：CTA 大字要放在下巴以下（y ≥ 1330）。
- Scribe 给语气词（「哦」）零时长，`align.py` 会把它延到下一个字。
- 人物卡的缩放同时保证房间背景越过画面底边（源片偏矮时会自动放大），否则卡片底部露黑边。
- 语速变快后部件的子动作挤在一起：重跑 stills 看每个部件，尤其环绕、飞入类会不会压到标题（2026-10-29 orbit 缩略图压住「是喂出来的」，已把环绕压扁、下移，最高点 y≈316）。
- `retime.py` 处理视频不能用 ffmpeg 串 50 个 `xfade`：每个 xfade 会把后面的画面提前一个叠化时长，累积成几秒的音画不同步，串长了还会直接截断。现在逐帧映射：每帧按时间表取源帧，剪点处与「剪掉的停顿里继续的画面」叠化 2 帧，画面与声音同长。
- Avatar V 实际约 48 credits/分钟（86.6 s 扣 70），不是 20；`VOICE_PROVIDER_TIMEOUT` 是 HeyGen 侧失败、不扣费，重提一次要用户点头；外部音频隧道用 `cloudflared --protocol http2`（QUIC 隧道曾在下载中途断开）。
- 配乐按片长剪出来常比片长多 2–4 s：`mix.py` 默认 `--music-align end`，裁开头、保留曲子自己的结尾。
- HeyGen API Key 曾经失效（401），会员 MCP 是默认通道；不要因为 MCP 不在当前会话就改走 API 钱包。

## 文件

```text
skills/yyl-vertical-video/
  SKILL.md
  references/  reference-analysis.md（两条参考片逐帧拆解）· beats.md（节拍表与部件目录）· pipeline.md（命令）· feedback.md（用户反馈与落实位置）
  film/split.js           渲染模块（版式、人物出框、标题、字幕、18 个部件、音效触发点、QA 框）
  scripts/  retime.py（1.3 倍 + 80 ms 气口）· align.py · prep.py · mix.py · make.py · qa.py
```

依赖：`skills/lighttrail`（引擎、render.mjs、frame_vf.py、字体）、`skills/talking-head-reel`（vision_faces / person_mask 的 Swift 源码、共用音效库、qa_frames.py）、Node ≥ 22、Google Chrome、ffmpeg、python3 + numpy + scipy + Pillow、Xcode 命令行工具。
