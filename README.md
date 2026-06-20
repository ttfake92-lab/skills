# 鱼亦乐的 AI Agent Skills / Yuyile's AI Agent Skills

[English](#english) | [中文](#中文)

---

## English

A collection of skills for AI coding agents. Skills are packaged instructions that extend agent capabilities — for content creators, video producers, and prompt engineers.

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

### New Skill

- `yyl-video-thumbnail` has been added to the repository manifest, so `npx skills@latest add ttfake92-lab/skills` can discover it together with the existing skills.

### Skills Overview

This repository currently includes four content-creation skills. They cover adjacent stages of an AI video workflow:

| Skill | What It Does | Best For |
|------|--------------|----------|
| `AI-video-prompt` | Turns scripts or story beats into image-reference prompts with second-by-second action, sound, and hard constraints. | Seedance 2.0, multi-image reference prompts, first/end frame continuity, production control prompts. |
| `mx-shell-prompt` | Turns scripts, stories, voiceovers, or rough ideas into structured cinematic prompts. | Text-to-video tools, storyboard prompts, shot lists, camera language. |
| `yyl-remotion-video` | Turns scripts, articles, notes, or outlines into Remotion projects that can render mp4. | Frame-accurate explainers, product demos, command-line films, silent clips for post-production voiceover. |
| `yyl-video-thumbnail` | Generates high-CTR video thumbnails with pop-out technique — darkened base, yellow keyword text, full-brightness cutout subject. | Bilibili, YouTube, Douyin/TikTok covers, AI tool demos, command-line film posters. |

### How To Choose

Use **AI-video-prompt** when your next step is generating footage in image-reference workflows such as Seedance-style multi-image generation. It focuses on locking image roles, character continuity, time-coded motion, sound design, spatial logic, and hard failure-prevention constraints.

Use **mx-shell-prompt** when your next step is sending prompts to video generation tools such as Seedance 2.0, Kling, Jimeng, Sora, Runway, or Pika. It focuses on cinematic language: characters, props, scenes, sound, mood, shot sizes, composition, and camera movement.

Use **yyl-remotion-video** when your next step is building a real Remotion project and exporting an mp4. It focuses on React/TypeScript implementation, timeline timing, frame-based animation, still-frame checks, and theme-driven video templates.

Use **yyl-video-thumbnail** when your video is done and you need a click-worthy cover image. It focuses on the pop-out visual technique, three ratio outputs per brief, and three distinct aesthetic templates — poster, command-panel, and film-edit.

### Example Workflow

1. Use `mx-shell-prompt` to break a script into cinematic blocks and shot ideas.
2. Use `AI-video-prompt` when the output needs image-reference prompts with precise constraints.
3. Use `yyl-remotion-video` when you want a deterministic 16:9 Remotion clip instead of model-generated footage.
4. Use `yyl-video-thumbnail` to generate a high-CTR cover image once the video is ready.
5. Add voiceover, subtitles, sound design, and final edits in post-production.

### License

MIT

---

## 中文

AI Agent 技能集合 — 面向内容创作者、视频制作人和提示词工程师。

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

### 新增说明

- 已新增 `yyl-video-thumbnail`，并加入仓库 skill 清单。现在使用 `npx skills@latest add ttfake92-lab/skills` 时，可以和已有 skill 一起被发现与安装。

### Skills 概览

这个仓库目前有 4 个内容创作类 skills，覆盖 AI 视频工作流里相邻但不同的阶段：

| Skill | 做什么 | 适合场景 |
|------|--------|----------|
| `AI-video-prompt` | 把脚本或故事节拍转成图片参考型提示词，包含图片参考、秒级动作、声音和硬约束。 | Seedance 2.0、多图参考、首尾帧连续、强控制视频生成提示词。 |
| `mx-shell-prompt` | 把脚本、故事、口播稿或粗略想法转成结构化电影级视频提示词。 | 文生视频工具、分镜提示词、镜头语言、AI 视频生成。 |
| `yyl-remotion-video` | 把口播稿、文章、资料摘要或明确大纲做成可渲染 mp4 的 Remotion 项目。 | 逐帧可控讲解视频、产品 demo、命令行电影、后期统一配音的视频片段。 |
| `yyl-video-thumbnail` | 用 pop-out 技法生成视频封面：压暗原图 + 黄色关键词 + 全亮抠图人物。 | B站/YouTube/抖音封面、AI 工具 demo 封面、命令行电影海报。 |

### 怎么选择

如果你的下一步是 Seedance 这类依赖图片参考的视频生成工作流，用 **AI-video-prompt**。它关注的是图片角色绑定、人物连续性、秒级动作、声音设计、空间逻辑和防跑偏硬约束。

如果你的下一步是把提示词发给 Seedance 2.0、Kling、即梦、Sora、Runway、Pika 等视频生成工具，用 **mx-shell-prompt**。它关注的是电影语言：角色、道具、场景、声音、氛围、景别、构图和运镜。

如果你的下一步是生成一个真实的 Remotion 工程并导出 mp4，用 **yyl-remotion-video**。它关注的是 React / TypeScript 实现、时间轴、逐帧动画、检查帧和主题模板。

如果你的视频已经做好，需要一张高点击率封面，用 **yyl-video-thumbnail**。它关注的是 pop-out 视觉技法、三种比例自动输出、三套美学模板（海报风/命令面板/胶片编辑）。

### 推荐工作流

1. 用 `mx-shell-prompt` 把脚本拆成电影化板块和镜头想法。
2. 如果要用 Seedance 等图片参考型视频工具生成画面，用 `AI-video-prompt` 写成带图片参考和硬约束的生产型提示词。
3. 如果你想要可控的 16:9 动态讲解片段，就用 `yyl-remotion-video` 做 Remotion 视频。
4. 视频做好后，用 `yyl-video-thumbnail` 生成高点击率封面。
5. 最后在后期软件里加入口播、字幕、音效和剪辑。

### 许可

MIT
