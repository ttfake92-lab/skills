# 鱼亦乐的 AI Agent Skills / Yuyile's AI Agent Skills

[English](#english) | [中文](#中文)

---

## English

A collection of skills for AI coding agents. Skills are packaged instructions that extend agent capabilities — for content creators, video producers, prompt engineers, and students making life decisions.

### Agent Install (one command)

Ask your coding agent to install the skills for you — give it this command:

```bash
npx skills@latest add ttfake92-lab/skills
```

It will read this repository's skill manifest, show the available skills, and let the agent install the selected skills into supported agent environments.

### Quickstart (30-second setup)

1. Run the skills installer. This command reads this repository's skill manifest and lets you install all listed skills:

```bash
npx skills@latest add ttfake92-lab/skills
```

2. Pick the skills you want, and which coding agents you want to install them on.

3. Bam — you're ready to go.

### Available Skills

#### Content Creation

- **[yyl-video-prompt](./skills/yyl-video-prompt/SKILL.md)** — Director-style AI video prompts. Picks a mode from the script's style, then splits any script, story, voiceover, or one-line idea into ready-to-submit segment prompts. Short-video mode has two styles, one-take and multi-shot, benchmarked on a viral short and a multi-shot narrative example; cinematic-drama mode handles slow, performance-driven scenes with an eight-dimension acting formula and FACS action units. Every segment covers reference-image binding, time-coded action, camera language, sound design, and hard constraints. Works with Seedance 2.0/2.5, Jimeng/Dreamina, LibTV, and more. Replaces `AI-video-prompt` and `mx-shell-prompt`.
- **[yyl-remotion-video](./skills/yyl-remotion-video/SKILL.md)** — Build 16:9 Remotion video projects from scripts, articles, notes, or outlines. Creates frame-driven React/TypeScript animations, estimates duration without synthesizing audio, renders still checks, and exports mp4 with built-in themes plus a dark 3D luxury gallery template.
- **[yyl-video-thumbnail](./skills/yyl-video-thumbnail/SKILL.md)** — Generate high-CTR video thumbnails for Bilibili, YouTube, and Douyin/TikTok. Uses pop-out technique: darkened original photo as base, yellow-highlighted title text, and cutout subject overlaid at full brightness. Ships with three templates (popout poster, UI command panel, film-edit style) and auto-generates 16:9 / 4:3 / 3:4 ratios.
- **[yyl-benchmark-breakdown](./skills/yyl-benchmark-breakdown/SKILL.md)** — Teardown competitor content from any link. Auto-detects platform (Douyin/XHS/Bilibili/YouTube/WeChat) and scope (single post or entire account), fetches content via 4-level fallback, transcribes audio, extracts visual frames, then outputs a 3-piece report: reusable formula, frame-by-frame breakdown with visual+audio alignment, and persona/positioning analysis. Auto-archives to benchmarks/ for long-term reference library.
- **[archival-fragments](./skills/archival-fragments/SKILL.md)** — End-to-end short-film pipeline in the Archival Fragments visual style (ivory paper, monochrome print, one muted crimson accent). Takes an idea or script, installs and verifies dependencies (ffmpeg / LibTV CLI / Fish Audio), writes the script, breaks it into story, visuals and rhythm, designs a chained keyframe sequence, drives MiniMax H3 first-last-frame generation shot by shot, synthesizes narration, and assembles with ffmpeg. Validated on a 67.3s / 34-shot film.
- **[archival-fragments-lite](./skills/archival-fragments-lite/SKILL.md)** — The Archival Fragments visual style plus the reference-image-to-first-last-frame method, with no tool lock-in. Build a chain of N+1 distinct reference images, then generate each shot from two adjacent images so consecutive shots share a frame and cut seamlessly. Works with any image model and any video tool that supports first-and-last-frame input. Start here unless you already run the exact toolchain the full version expects.

#### Education & Decision

- **[college-application](./skills/college-application/SKILL.md)** — China gaokao (college entrance exam) application assistant. Guides students through a structured decision process: scientifically-grounded personality & career interest assessment (RIASEC + Big Five), career/major/industry research, and admission data analysis — then generates a traceable HTML report with sources, cross-validation suggestions, and disclaimer. Supports provinces, subject combos, scores/rank, and official admission data.

#### System Tools

- **[yyl-disk-cleaner-cat](./skills/yyl-disk-cleaner-cat/SKILL.md)** — macOS disk cleanup with a pixel-art cat. Scans developer caches, system caches, large files, performance metrics, and network diagnostics. Presents an interactive pixel-art web page where you confirm deletions — a blue-white cat physically walks through a hand-drawn apartment, sweeping dust piles in real-time as files are permanently removed. Includes persistent memory across sessions.
- **[macos-migration](./skills/macos-migration/SKILL.md)** — Two-phase macOS migration assistant. On the old Mac it scans Homebrew packages, App Store / manual apps, npm/uv/pip/go tools, dotfiles, editor extensions, fonts, and launch agents into a JSON manifest; on the new Mac it reads the manifest and restores everything (batch Homebrew install, config files, Library data from Time Machine), then reports what needs manual handling. Requires a full Time Machine backup up front and asks before collecting secrets like SSH keys.

### New Skill

- `yyl-video-prompt` has been added. It merges `AI-video-prompt` and `mx-shell-prompt` into one skill with two modes, short-video and cinematic drama. The two older skills have been removed — if you installed them before, switch to `yyl-video-prompt`.
- `archival-fragments` and `archival-fragments-lite` have been added — the Archival Fragments visual style, as a full end-to-end film pipeline and as a tool-agnostic style-and-method pack. Now discoverable via `npx skills@latest add ttfake92-lab/skills`.

### Skills Overview

This repository includes nine skills — six for content creation, one for education/decision support, and two for system tools:

| Skill | What It Does | Best For |
|------|--------------|----------|
| `yyl-video-prompt` | Turns scripts or ideas into segment-by-segment video prompts, choosing short-video or cinematic-drama mode from the script's style. | Seedance 2.0/2.5, Jimeng, multi-image reference, one-take and multi-shot shorts, performance-driven drama scenes. |
| `yyl-remotion-video` | Turns scripts, articles, notes, or outlines into Remotion projects that can render mp4. | Frame-accurate explainers, product demos, command-line films, silent clips for post-production voiceover. |
| `yyl-video-thumbnail` | Generates high-CTR video thumbnails with pop-out technique — darkened base, yellow keyword text, full-brightness cutout subject. | Bilibili, YouTube, Douyin/TikTok covers, AI tool demos, command-line film posters. |
| `college-application` | Guides gaokao students through personality assessment, career/major/industry research, and admission data analysis; outputs a sourced HTML report. | China gaokao applicants, parents, education consultants, anyone building decision-support agents. |
| `yyl-benchmark-breakdown` | Teardown competitor content from any link: auto-detect platform, fetch via 4-level fallback, transcribe audio, extract visual frames, output reusable formula + frame-by-frame breakdown + persona analysis. | Content creators doing competitive research, viral video analysis, benchmark building. |
| `yyl-disk-cleaner-cat` | Scans macOS disk, presents interactive pixel-art cleanup page with real-time cat animation. | Freeing disk space, clearing developer caches, system optimization, network diagnostics. |
| `macos-migration` | Two-phase macOS migration: scans the old Mac into a JSON manifest, then restores apps, packages, and configs on the new Mac, with a manual-handling diff report. | Getting a new Mac, reinstalling macOS, restoring from Time Machine, moving a full dev setup. |
| `archival-fragments` | Idea or script to finished film: verifies deps, breaks the script into story/visuals/rhythm, chains keyframes, generates shot by shot on MiniMax H3, narrates and assembles. | Explainer shorts, news commentary, paper-collage editorial style, first-last-frame workflows. |
| `archival-fragments-lite` | Same style and method, no tool lock-in: chain N+1 distinct reference images, generate each shot from two adjacent ones. | Anyone with an image model and a video tool that supports first-and-last-frame. Start here. |

### How To Choose

Use **yyl-video-prompt** when your next step is generating footage with an AI video model. It first decides between short-video mode (one-take or multi-shot, short-platform pacing) and cinematic-drama mode (slow, performance-driven scenes), then writes each segment with reference-image roles, time-coded action, camera language, sound design, and hard constraints. It merges and replaces the former `AI-video-prompt` and `mx-shell-prompt`.

Use **yyl-remotion-video** when your next step is building a real Remotion project and exporting an mp4. It focuses on React/TypeScript implementation, timeline timing, frame-based animation, still-frame checks, and theme-driven video templates.

Use **yyl-video-thumbnail** when your video is done and you need a click-worthy cover image. It focuses on the pop-out visual technique, three ratio outputs per brief, and three distinct aesthetic templates — poster, command-panel, and film-edit.

Use **college-application** when a student needs structured help choosing majors and universities for China's gaokao system. It focuses on evidence-based personality assessment, career/major/industry research grounded in official sources, and admission data analysis — all wrapped in a traceable HTML report with explicit disclaimers.

Use **yyl-benchmark-breakdown** when you want to learn from a competitor's content. Drop a link and get a teardown: why it works, what formula you can steal, frame-by-frame visual+audio breakdown, and their persona/positioning strategy. Auto-archives everything for your long-term benchmark library.

Use **yyl-disk-cleaner-cat** when you need to free up macOS disk space, clear developer caches, or optimize system performance. It focuses on safe deletion with user confirmation, persistent preference learning, and a unique pixel-art interactive experience.

Use **archival-fragments-lite** when you want the look and the method but bring your own tools. It fixes only two things — the visual style and the reference-image-to-first-last-frame workflow — so it runs on any image model and any video tool with first-and-last-frame support. This is the one to reach for first.

Use **archival-fragments** when you want a finished short film, not just prompts. It handles the whole chain — dependency checks, script writing, story/visual/rhythm breakdown, chained keyframes, shot-by-shot generation on MiniMax H3, narration, and ffmpeg assembly. Its hard constraints exist to prevent the two failure modes that actually happen: every shot looking identical, and abstract graphics the audience cannot decode.

Use **macos-migration** when you're setting up a new Mac or reinstalling macOS. It scans your old system into a JSON manifest, then on the new machine batch-installs Homebrew packages and restores configs and Library data from Time Machine, never overwriting existing files and reporting everything that needs manual handling.

### Example Workflow

1. Use `yyl-benchmark-breakdown` to analyze a competitor's viral video — extract the formula, hooks, and visual rhythm.
2. Use `yyl-video-prompt` to turn your script into segment prompts — short-video or cinematic-drama mode, with reference-image binding and hard constraints.
3. Use `yyl-remotion-video` when you want a deterministic 16:9 Remotion clip instead of model-generated footage.
4. Use `yyl-video-thumbnail` to generate a high-CTR cover image once the video is ready.
5. Add voiceover, subtitles, sound design, and final edits in post-production.

### License

MIT

---

## 中文

AI Agent 技能集合 — 面向内容创作者、视频制作人、提示词工程师，以及需要决策辅助的学生和家长。

### 给 Agent 的一条命令

跟你的 Agent 说「用这个方式帮我安装 skill」，把下面这条命令给它：

```bash
npx skills@latest add ttfake92-lab/skills
```

它会读取这个仓库里的 skill 清单，展示可安装的 skills，并把你选中的 skills 安装到支持的 Agent 环境里。

### 快速安装（30 秒搞定）

1. 运行安装命令。这个命令会读取仓库里的 skill 清单，并允许你安装清单中的所有 skill：

```bash
npx skills@latest add ttfake92-lab/skills
```

2. 选择你要安装的 skill 和目标 Agent。

3. 搞定。

### 可用 Skills

#### 内容创作

- **[yyl-video-prompt](./skills/yyl-video-prompt/SKILL.md)** — 导演式 AI 视频提示词。先按脚本风格选档位，再把脚本、故事、口播稿或一句想法拆成能直接提交生成的分段提示词。短视频档分一镜到底和多分镜两种写法，以一条爆款短视频和一个多分镜叙事案例为标杆；电影精品档面向慢节奏的表演戏，用八维表演公式和 AU 面部编码。每段都写参考图绑定、秒级动作、镜头语言、声音设计和硬约束。适用 Seedance 2.0/2.5、即梦、LibTV 等。合并并取代了原来的 `AI-video-prompt` 和 `mx-shell-prompt`。
- **[yyl-remotion-video](./skills/yyl-remotion-video/SKILL.md)** — Remotion 视频制作。把口播稿、文章、资料摘要或明确大纲做成 16:9、逐帧可控、可直接导出 mp4 的视频项目。内置三套主题和深色 3D 高端画廊模板，不在流程内合成音频，适合后期统一配音。
- **[yyl-video-thumbnail](./skills/yyl-video-thumbnail/SKILL.md)** — 视频封面生成。用 pop-out 技法做 B站/YouTube/抖音高点击率封面：底层压暗原图保留环境、中层黄色关键词标题、顶层全亮抠图人物原位叠回。支持 popout 深色海报、ui 命令面板、paper 胶片编辑三套模板，自动输出 16:9/4:3/3:4 三种比例。
- **[yyl-benchmark-breakdown](./skills/yyl-benchmark-breakdown/SKILL.md)** — 对标账号拆解。丢一个链接，自动识别平台（抖音/小红书/B站/YouTube/公众号）和粒度（单条或整个账号），通过四级回退取数、转写口播、抽视觉帧，输出三件套：可复用爆款公式、画面+口播逐段拆解（时间轴对齐）、人设与内容定位。自动存档到 benchmarks/ 沉淀成对标库。
- **[archival-fragments](./skills/archival-fragments/SKILL.md)** — 档案剪贴风格短片全流程。给一个想法或一份文案，从空文件夹开始：装依赖并逐项验证（ffmpeg / LibTV CLI / Fish Audio，含真实发一次 TTS 测试）、写文案、拆故事拆画面拆节奏、设计串联关键帧链、用 MiniMax H3 首尾帧逐镜生成、Fish Audio 配音、ffmpeg 变速拼片成片。三条硬约束：每镜画面必须不同、逐镜表须先给用户过目、具象符号优先于抽象图形。已用一条 67.3 秒 / 34 镜成片验证。
- **[archival-fragments-lite](./skills/archival-fragments-lite/SKILL.md)** — 档案剪贴风格 + 「参考图 → 首尾帧」方法，不绑定任何工具。先出一串各不相同的参考图，再用相邻两张作为首尾帧生成镜头，相邻两镜共用同一张图所以接点严丝合缝。任何图片模型 + 任何支持首尾帧的视频工具都能用。**除非你已经在用完整版要求的那套工具链，否则从这个开始。**

#### 教育与决策

- **[college-application](./skills/college-application/SKILL.md)** — 高考志愿决策辅助。通过 Agent 对话引导考生完成「认识自己 → 理解职业/专业/行业 → 用招生数据约束选择 → 生成可审计报告」的完整决策流程。包含有科学依据的性格与职业兴趣测评（RIASEC + Big Five）、职业/专业/行业深度研究、省份/选科/分数/位次与官方招生数据整合，最终生成带完整来源链接和免责声明的 HTML 报告。

#### 系统工具

- **[yyl-disk-cleaner-cat](./skills/yyl-disk-cleaner-cat/SKILL.md)** — macOS 磁盘清理小猫。扫描开发者缓存、系统缓存、大文件、性能指标和网络状态，打开一个像素风网页让你勾选确认——确认后一只蓝白小猫在手绘公寓里一间间走、实时打扫灰尘堆。带持续记忆：偏好、永不清理列表、历史清理记录跨会话保留。
- **[macos-migration](./skills/macos-migration/SKILL.md)** — macOS 系统迁移助手，两阶段设计。旧系统上把 Homebrew 软件、App Store/手动安装的应用、npm/uv/pip/go 工具、dotfiles、编辑器扩展、字体、自启动服务扫描成一份 JSON 清单；新系统上读清单逐步还原（Homebrew 批量安装、配置文件、从 Time Machine 恢复 Library 数据），最后输出需手动处理的差异报告。前置要求先做一次 Time Machine 全量备份，采集私钥等敏感数据前先征求确认。

### 新增说明

- 已新增 `yyl-video-prompt`：把 `AI-video-prompt` 和 `mx-shell-prompt` 合并成一个 Skill，分短视频和电影精品两个档位。两个旧 Skill 已从仓库下架，之前装过的话换成 `yyl-video-prompt` 即可。
- 已新增 `archival-fragments`（档案剪贴风格短片全流程）和 `archival-fragments-lite`（同样的风格与方法，但不绑定工具，推荐大多数人用这个），并加入仓库 skill 清单。现在使用 `npx skills@latest add ttfake92-lab/skills` 时，可以和已有 skill 一起被发现与安装。

### Skills 概览

这个仓库目前有 9 个 skills：6 个内容创作类 + 1 个教育决策类 + 2 个系统工具类。

| Skill | 做什么 | 适合场景 |
|------|--------|----------|
| `yyl-video-prompt` | 把脚本或想法拆成逐段可提交的视频提示词，按脚本风格自动选短视频档或电影精品档。 | Seedance 2.0/2.5、即梦、多图参考、一镜到底和多分镜短视频、靠表演推进的剧情戏。 |
| `yyl-remotion-video` | 把口播稿、文章、资料摘要或明确大纲做成可渲染 mp4 的 Remotion 项目。 | 逐帧可控讲解视频、产品 demo、命令行电影、后期统一配音的视频片段。 |
| `yyl-video-thumbnail` | 用 pop-out 技法生成视频封面：压暗原图 + 黄色关键词 + 全亮抠图人物。 | B站/YouTube/抖音封面、AI 工具 demo 封面、命令行电影海报。 |
| `college-application` | 引导高考考生完成性格测评、职业/专业/行业研究和招生数据分析，生成带来源的 HTML 报告。 | 高考考生、家长、教育咨询师、需要构建决策辅助 Agent 的开发者。 |
| `yyl-benchmark-breakdown` | 丢一个链接，自动拆解对标内容：四级回退取数、转写口播、抽视觉帧，输出可复用爆款公式、画面+口播逐段拆解、人设定位。 | 内容创作者做竞品分析、爆款视频拆解、建立对标库。 |
| `yyl-disk-cleaner-cat` | 扫描 macOS 磁盘，打开像素风交互页确认删除，小猫实时打扫。 | 释放磁盘空间、清理开发者缓存、系统优化、网络诊断。 |
| `macos-migration` | 两阶段 macOS 迁移：旧系统扫描成 JSON 清单，新系统还原软件、包和配置，并输出需手动处理的差异报告。 | 换新 Mac、重装系统、从 Time Machine 恢复、迁移整套开发环境。 |
| `archival-fragments` | 从想法或文案到成片：验环境、拆故事拆画面拆节奏、串联关键帧、H3 逐镜生成、配音、变速拼片。 | 解说短片、新闻评论、纸质拼贴编辑风格、首尾帧工作流。 |
| `archival-fragments-lite` | 同样的风格和方法，但不绑定工具：串联 N+1 张各不相同的参考图，用相邻两张生成一镜。 | 有图片模型 + 支持首尾帧的视频工具就能用。**推荐从这个开始。** |

### 怎么选择

如果你的下一步是用 AI 视频模型生成画面，用 **yyl-video-prompt**。它先判断走短视频档（一镜到底或多分镜，短视频平台的节奏）还是电影精品档（慢节奏、靠表演推进），再逐段写好参考图绑定、秒级动作、镜头语言、声音设计和硬约束。它合并并取代了原来的 `AI-video-prompt` 和 `mx-shell-prompt`。

如果你的下一步是生成一个真实的 Remotion 工程并导出 mp4，用 **yyl-remotion-video**。它关注的是 React / TypeScript 实现、时间轴、逐帧动画、检查帧和主题模板。

如果你的视频已经做好，需要一张高点击率封面，用 **yyl-video-thumbnail**。它关注的是 pop-out 视觉技法、三种比例自动输出、三套美学模板（海报风/命令面板/胶片编辑）。

如果你需要帮高考生做志愿决策，用 **college-application**。它关注的是科学依据的性格测评、基于官方来源的职业/专业/行业研究、招生数据分析，以及带完整来源链接和免责声明的可审计 HTML 报告。

如果你想拆解对标账号或竞品内容，用 **yyl-benchmark-breakdown**。丢一个链接进去，它会自动取数、转写口播、抽视觉帧，输出可复用的爆款公式、画面+口播逐段拆解和人设定位，并自动存档到对标库。

如果你的下一步是释放 macOS 磁盘空间、清理缓存或优化系统性能，用 **yyl-disk-cleaner-cat**。它关注的是安全删除（用户确认）、持续偏好学习和像素风交互体验。

如果你想要这套画风和做法、但工具用自己手上的，用 **archival-fragments-lite**。它只固定风格和「参考图 → 首尾帧」的方法，任何图片模型 + 任何支持首尾帧的视频工具都能跑。**大多数人应该从这个开始。**

如果你要的是一条做完的片子而不只是提示词，用 **archival-fragments**。它管的是全链路：验环境、写文案、拆故事拆画面拆节奏、串联关键帧、用 MiniMax H3 逐镜生成、配音、ffmpeg 拼片。它的三条硬约束是为了防两个真实发生过的翻车：整片镜头长得一模一样，以及观众看不懂的抽象图形。

如果你在装新 Mac 或重装系统，用 **macos-migration**。它先把旧系统扫描成一份 JSON 清单，再在新机器上批量安装 Homebrew 软件、从 Time Machine 恢复配置和 Library 数据，全程不覆盖已有文件，并把所有需手动处理的项目列成差异报告。

### 推荐工作流

1. 用 `yyl-benchmark-breakdown` 拆解竞品爆款视频 —— 提取公式、钩子、视觉节奏。
2. 用 `yyl-video-prompt` 把脚本拆成逐段视频提示词——按风格走短视频档或电影精品档，带参考图绑定和硬约束。
3. 如果你想要可控的 16:9 动态讲解片段，就用 `yyl-remotion-video` 做 Remotion 视频。
4. 视频做好后，用 `yyl-video-thumbnail` 生成高点击率封面。
5. 最后在后期软件里加入口播、字幕、音效和剪辑。

### 许可

MIT
