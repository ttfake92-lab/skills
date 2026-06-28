# 鱼亦乐的 AI Agent Skills / Yuyile's AI Agent Skills

[English](#english) | [中文](#中文)

---

## English

A collection of skills for AI coding agents. Skills are packaged instructions that extend agent capabilities — for content creators, video producers, prompt engineers, and students making life decisions.

### Quickstart (30-second setup)

1. Run the skills installer. This command reads this repository's skill manifest and lets you install all listed skills:

```bash
npx skills@latest add ttfake92-lab/skills
```

2. Pick the skills you want, and which coding agents you want to install them on.

3. Bam — you're ready to go.

### Available Skills

#### Content Creation

- **[AI-video-prompt](./skills/AI-video-prompt/SKILL.md)** — Write image-reference video prompts with reference binding, time-coded action, sound design, camera movement, and hard constraints. Best for multi-image reference workflows such as 多图参考, 首尾帧, 全能参考, and script-to-video prompt generation.
- **[mx-shell-prompt](./skills/mx-shell-prompt/SKILL.md)** — Write structured, cinematic video generation prompts for AI video tools like Seedance 2.0, Kling, Sora, Runway, Pika. Transforms rough ideas into production-ready prompts with three pillars: who-where, what-feel, what-happens. Includes shot catalog, cinematic vocabulary, and composition templates.
- **[yyl-remotion-video](./skills/yyl-remotion-video/SKILL.md)** — Build 16:9 Remotion video projects from scripts, articles, notes, or outlines. Creates frame-driven React/TypeScript animations, estimates duration without synthesizing audio, renders still checks, and exports mp4 with built-in themes plus a dark 3D luxury gallery template.
- **[yyl-video-thumbnail](./skills/yyl-video-thumbnail/SKILL.md)** — Generate high-CTR video thumbnails for Bilibili, YouTube, and Douyin/TikTok. Uses pop-out technique: darkened original photo as base, yellow-highlighted title text, and cutout subject overlaid at full brightness. Ships with three templates (popout poster, UI command panel, film-edit style) and auto-generates 16:9 / 4:3 / 3:4 ratios.
- **[yyl-benchmark-breakdown](./skills/yyl-benchmark-breakdown/SKILL.md)** — Teardown competitor content from any link. Auto-detects platform (Douyin/XHS/Bilibili/YouTube/WeChat) and scope (single post or entire account), fetches content via 4-level fallback, transcribes audio, extracts visual frames, then outputs a 3-piece report: reusable formula, frame-by-frame breakdown with visual+audio alignment, and persona/positioning analysis. Auto-archives to benchmarks/ for long-term reference library.

#### Education & Decision

- **[college-application](./skills/college-application/SKILL.md)** — China gaokao (college entrance exam) application assistant. Guides students through a structured decision process: scientifically-grounded personality & career interest assessment (RIASEC + Big Five), career/major/industry research, and admission data analysis — then generates a traceable HTML report with sources, cross-validation suggestions, and disclaimer. Supports provinces, subject combos, scores/rank, and official admission data.

#### System Tools

- **[yyl-disk-cleaner-cat](./skills/yyl-disk-cleaner-cat/SKILL.md)** — macOS disk cleanup with a pixel-art cat. Scans developer caches, system caches, large files, performance metrics, and network diagnostics. Presents an interactive pixel-art web page where you confirm deletions — a blue-white cat physically walks through a hand-drawn apartment, sweeping dust piles in real-time as files are permanently removed. Includes persistent memory across sessions.

### New Skill

- `yyl-disk-cleaner-cat` has been added — a macOS disk cleanup tool with a pixel-art cat animation. Now discoverable via `npx skills@latest add ttfake92-lab/skills`.

### Skills Overview

This repository includes seven skills — five for content creation, one for education/decision support, and one for system tools:

| Skill | What It Does | Best For |
|------|--------------|----------|
| `AI-video-prompt` | Turns scripts or story beats into image-reference prompts with second-by-second action, sound, and hard constraints. | Seedance 2.0, multi-image reference prompts, first/end frame continuity, production control prompts. |
| `mx-shell-prompt` | Turns scripts, stories, voiceovers, or rough ideas into structured cinematic prompts. | Text-to-video tools, storyboard prompts, shot lists, camera language. |
| `yyl-remotion-video` | Turns scripts, articles, notes, or outlines into Remotion projects that can render mp4. | Frame-accurate explainers, product demos, command-line films, silent clips for post-production voiceover. |
| `yyl-video-thumbnail` | Generates high-CTR video thumbnails with pop-out technique — darkened base, yellow keyword text, full-brightness cutout subject. | Bilibili, YouTube, Douyin/TikTok covers, AI tool demos, command-line film posters. |
| `college-application` | Guides gaokao students through personality assessment, career/major/industry research, and admission data analysis; outputs a sourced HTML report. | China gaokao applicants, parents, education consultants, anyone building decision-support agents. |
| `yyl-benchmark-breakdown` | Teardown competitor content from any link: auto-detect platform, fetch via 4-level fallback, transcribe audio, extract visual frames, output reusable formula + frame-by-frame breakdown + persona analysis. | Content creators doing competitive research, viral video analysis, benchmark building. |
| `yyl-disk-cleaner-cat` | Scans macOS disk, presents interactive pixel-art cleanup page with real-time cat animation. | Freeing disk space, clearing developer caches, system optimization, network diagnostics. |

### How To Choose

Use **AI-video-prompt** when your next step is generating footage in image-reference workflows such as Seedance-style multi-image generation. It focuses on locking image roles, character continuity, time-coded motion, sound design, spatial logic, and hard failure-prevention constraints.

Use **mx-shell-prompt** when your next step is sending prompts to video generation tools such as Seedance 2.0, Kling, Jimeng, Sora, Runway, or Pika. It focuses on cinematic language: characters, props, scenes, sound, mood, shot sizes, composition, and camera movement.

Use **yyl-remotion-video** when your next step is building a real Remotion project and exporting an mp4. It focuses on React/TypeScript implementation, timeline timing, frame-based animation, still-frame checks, and theme-driven video templates.

Use **yyl-video-thumbnail** when your video is done and you need a click-worthy cover image. It focuses on the pop-out visual technique, three ratio outputs per brief, and three distinct aesthetic templates — poster, command-panel, and film-edit.

Use **college-application** when a student needs structured help choosing majors and universities for China's gaokao system. It focuses on evidence-based personality assessment, career/major/industry research grounded in official sources, and admission data analysis — all wrapped in a traceable HTML report with explicit disclaimers.

Use **yyl-benchmark-breakdown** when you want to learn from a competitor's content. Drop a link and get a teardown: why it works, what formula you can steal, frame-by-frame visual+audio breakdown, and their persona/positioning strategy. Auto-archives everything for your long-term benchmark library.

Use **yyl-disk-cleaner-cat** when you need to free up macOS disk space, clear developer caches, or optimize system performance. It focuses on safe deletion with user confirmation, persistent preference learning, and a unique pixel-art interactive experience.

### Example Workflow

1. Use `yyl-benchmark-breakdown` to analyze a competitor's viral video — extract the formula, hooks, and visual rhythm.
2. Use `mx-shell-prompt` to break your script into cinematic blocks and shot ideas.
3. Use `AI-video-prompt` when the output needs image-reference prompts with precise constraints.
4. Use `yyl-remotion-video` when you want a deterministic 16:9 Remotion clip instead of model-generated footage.
5. Use `yyl-video-thumbnail` to generate a high-CTR cover image once the video is ready.
6. Add voiceover, subtitles, sound design, and final edits in post-production.

### License

MIT

---

## 中文

AI Agent 技能集合 — 面向内容创作者、视频制作人、提示词工程师，以及需要决策辅助的学生和家长。

### 快速安装（30 秒搞定）

1. 运行安装命令。这个命令会读取仓库里的 skill 清单，并允许你安装清单中的所有 skill：

```bash
npx skills@latest add ttfake92-lab/skills
```

2. 选择你要安装的 skill 和目标 Agent。

3. 搞定。

### 可用 Skills

#### 内容创作

- **[AI-video-prompt](./skills/AI-video-prompt/SKILL.md)** — 图片参考型视频提示词生成。把脚本或故事节拍转成带图片参考绑定、秒级动作、声音设计、运镜和硬约束的完整提示词，适合多图参考、首尾帧、全能参考和脚本转视频提示词。
- **[mx-shell-prompt](./skills/mx-shell-prompt/SKILL.md)** — 视频提示词写作。把粗略想法转化为结构化的电影级视频提示词，适用于 Seedance 2.0、Kling、Sora、Runway、Pika 等所有文生视频工具。核心理念：每个好提示词由三根支柱构成 —— 谁在哪、什么感觉、发生什么。内含景别速查表、电影词汇库和构图模板。
- **[yyl-remotion-video](./skills/yyl-remotion-video/SKILL.md)** — Remotion 视频制作。把口播稿、文章、资料摘要或明确大纲做成 16:9、逐帧可控、可直接导出 mp4 的视频项目。内置三套主题和深色 3D 高端画廊模板，不在流程内合成音频，适合后期统一配音。
- **[yyl-video-thumbnail](./skills/yyl-video-thumbnail/SKILL.md)** — 视频封面生成。用 pop-out 技法做 B站/YouTube/抖音高点击率封面：底层压暗原图保留环境、中层黄色关键词标题、顶层全亮抠图人物原位叠回。支持 popout 深色海报、ui 命令面板、paper 胶片编辑三套模板，自动输出 16:9/4:3/3:4 三种比例。
- **[yyl-benchmark-breakdown](./skills/yyl-benchmark-breakdown/SKILL.md)** — 对标账号拆解。丢一个链接，自动识别平台（抖音/小红书/B站/YouTube/公众号）和粒度（单条或整个账号），通过四级回退取数、转写口播、抽视觉帧，输出三件套：可复用爆款公式、画面+口播逐段拆解（时间轴对齐）、人设与内容定位。自动存档到 benchmarks/ 沉淀成对标库。

#### 教育与决策

- **[college-application](./skills/college-application/SKILL.md)** — 高考志愿决策辅助。通过 Agent 对话引导考生完成「认识自己 → 理解职业/专业/行业 → 用招生数据约束选择 → 生成可审计报告」的完整决策流程。包含有科学依据的性格与职业兴趣测评（RIASEC + Big Five）、职业/专业/行业深度研究、省份/选科/分数/位次与官方招生数据整合，最终生成带完整来源链接和免责声明的 HTML 报告。

#### 系统工具

- **[yyl-disk-cleaner-cat](./skills/yyl-disk-cleaner-cat/SKILL.md)** — macOS 磁盘清理小猫。扫描开发者缓存、系统缓存、大文件、性能指标和网络状态，打开一个像素风网页让你勾选确认——确认后一只蓝白小猫在手绘公寓里一间间走、实时打扫灰尘堆。带持续记忆：偏好、永不清理列表、历史清理记录跨会话保留。

### 新增说明

- 已新增 `yyl-disk-cleaner-cat`（macOS 磁盘清理小猫），并加入仓库 skill 清单。现在使用 `npx skills@latest add ttfake92-lab/skills` 时，可以和已有 skill 一起被发现与安装。

### Skills 概览

这个仓库目前有 7 个 skills：5 个内容创作类 + 1 个教育决策类 + 1 个系统工具类。

| Skill | 做什么 | 适合场景 |
|------|--------|----------|
| `AI-video-prompt` | 把脚本或故事节拍转成图片参考型提示词，包含图片参考、秒级动作、声音和硬约束。 | Seedance 2.0、多图参考、首尾帧连续、强控制视频生成提示词。 |
| `mx-shell-prompt` | 把脚本、故事、口播稿或粗略想法转成结构化电影级视频提示词。 | 文生视频工具、分镜提示词、镜头语言、AI 视频生成。 |
| `yyl-remotion-video` | 把口播稿、文章、资料摘要或明确大纲做成可渲染 mp4 的 Remotion 项目。 | 逐帧可控讲解视频、产品 demo、命令行电影、后期统一配音的视频片段。 |
| `yyl-video-thumbnail` | 用 pop-out 技法生成视频封面：压暗原图 + 黄色关键词 + 全亮抠图人物。 | B站/YouTube/抖音封面、AI 工具 demo 封面、命令行电影海报。 |
| `college-application` | 引导高考考生完成性格测评、职业/专业/行业研究和招生数据分析，生成带来源的 HTML 报告。 | 高考考生、家长、教育咨询师、需要构建决策辅助 Agent 的开发者。 |
| `yyl-benchmark-breakdown` | 丢一个链接，自动拆解对标内容：四级回退取数、转写口播、抽视觉帧，输出可复用爆款公式、画面+口播逐段拆解、人设定位。 | 内容创作者做竞品分析、爆款视频拆解、建立对标库。 |
| `yyl-disk-cleaner-cat` | 扫描 macOS 磁盘，打开像素风交互页确认删除，小猫实时打扫。 | 释放磁盘空间、清理开发者缓存、系统优化、网络诊断。 |

### 怎么选择

如果你的下一步是 Seedance 这类依赖图片参考的视频生成工作流，用 **AI-video-prompt**。它关注的是图片角色绑定、人物连续性、秒级动作、声音设计、空间逻辑和防跑偏硬约束。

如果你的下一步是把提示词发给 Seedance 2.0、Kling、即梦、Sora、Runway、Pika 等视频生成工具，用 **mx-shell-prompt**。它关注的是电影语言：角色、道具、场景、声音、氛围、景别、构图和运镜。

如果你的下一步是生成一个真实的 Remotion 工程并导出 mp4，用 **yyl-remotion-video**。它关注的是 React / TypeScript 实现、时间轴、逐帧动画、检查帧和主题模板。

如果你的视频已经做好，需要一张高点击率封面，用 **yyl-video-thumbnail**。它关注的是 pop-out 视觉技法、三种比例自动输出、三套美学模板（海报风/命令面板/胶片编辑）。

如果你需要帮高考生做志愿决策，用 **college-application**。它关注的是科学依据的性格测评、基于官方来源的职业/专业/行业研究、招生数据分析，以及带完整来源链接和免责声明的可审计 HTML 报告。

如果你想拆解对标账号或竞品内容，用 **yyl-benchmark-breakdown**。丢一个链接进去，它会自动取数、转写口播、抽视觉帧，输出可复用的爆款公式、画面+口播逐段拆解和人设定位，并自动存档到对标库。

如果你的下一步是释放 macOS 磁盘空间、清理缓存或优化系统性能，用 **yyl-disk-cleaner-cat**。它关注的是安全删除（用户确认）、持续偏好学习和像素风交互体验。

### 推荐工作流

1. 用 `yyl-benchmark-breakdown` 拆解竞品爆款视频 —— 提取公式、钩子、视觉节奏。
2. 用 `mx-shell-prompt` 把你的脚本拆成电影化板块和镜头想法。
3. 如果要用 Seedance 等图片参考型视频工具生成画面，用 `AI-video-prompt` 写成带图片参考和硬约束的生产型提示词。
4. 如果你想要可控的 16:9 动态讲解片段，就用 `yyl-remotion-video` 做 Remotion 视频。
5. 视频做好后，用 `yyl-video-thumbnail` 生成高点击率封面。
6. 最后在后期软件里加入口播、字幕、音效和剪辑。

### 许可

MIT
