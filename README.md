# 鱼亦乐的 AI Agent Skills / Yuyile's AI Agent Skills

[English](#english) | [中文](#中文)

---

## English

A collection of skills for AI coding agents. Skills are packaged instructions that extend agent capabilities — for content creators, video producers, and prompt engineers.

### Quickstart (30-second setup)

1. Run the skills installer:

```bash
npx skills@latest add ttfake92-lab/skills
```

2. Pick the skills you want, and which coding agents you want to install them on.

3. Bam — you're ready to go.

### Available Skills

#### Content Creation

- **[mx-shell-prompt](./skills/mx-shell-prompt/SKILL.md)** — Write structured, cinematic video generation prompts for AI video tools like Seedance 2.0, Kling, Sora, Runway, Pika. Transforms rough ideas into production-ready prompts with three pillars: who-where, what-feel, what-happens. Includes shot catalog, cinematic vocabulary, and composition templates.
- **[yyl-remotion-video](./skills/yyl-remotion-video/SKILL.md)** — Build 16:9 Remotion video projects from scripts, articles, notes, or outlines. Creates frame-driven React/TypeScript animations, estimates duration without synthesizing audio, renders still checks, and exports mp4 with built-in themes plus a dark 3D luxury gallery template.

### Skills Overview

This repository currently includes two content-creation skills. They cover two adjacent stages of an AI video workflow:

| Skill | What It Does | Best For |
|------|--------------|----------|
| `mx-shell-prompt` | Turns scripts, stories, voiceovers, or rough ideas into structured cinematic prompts. | Text-to-video tools, storyboard prompts, shot lists, camera language. |
| `yyl-remotion-video` | Turns scripts, articles, notes, or outlines into Remotion projects that can render mp4. | Frame-accurate explainers, product demos, command-line films, silent clips for post-production voiceover. |

### How To Choose

Use **mx-shell-prompt** when your next step is sending prompts to video generation tools such as Seedance 2.0, Kling, Jimeng, Sora, Runway, or Pika. It focuses on cinematic language: characters, props, scenes, sound, mood, shot sizes, composition, and camera movement.

Use **yyl-remotion-video** when your next step is building a real Remotion project and exporting an mp4. It focuses on React/TypeScript implementation, timeline timing, frame-based animation, still-frame checks, and theme-driven video templates.

### Example Workflow

1. Use `mx-shell-prompt` to break a script into cinematic blocks and shot ideas.
2. Use `yyl-remotion-video` when you want a deterministic 16:9 Remotion clip instead of model-generated footage.
3. Add voiceover, subtitles, sound design, and final edits in post-production.

### License

MIT

---

## 中文

AI Agent 技能集合 — 面向内容创作者、视频制作人和提示词工程师。

### 快速安装（30 秒搞定）

1. 运行安装命令：

```bash
npx skills@latest add ttfake92-lab/skills
```

2. 选择你要安装的 skill 和目标 Agent。

3. 搞定。

### 可用 Skills

#### 内容创作

- **[mx-shell-prompt](./skills/mx-shell-prompt/SKILL.md)** — 视频提示词写作。把粗略想法转化为结构化的电影级视频提示词，适用于 Seedance 2.0、Kling、Sora、Runway、Pika 等所有文生视频工具。核心理念：每个好提示词由三根支柱构成 —— 谁在哪、什么感觉、发生什么。内含景别速查表、电影词汇库和构图模板。
- **[yyl-remotion-video](./skills/yyl-remotion-video/SKILL.md)** — Remotion 视频制作。把口播稿、文章、资料摘要或明确大纲做成 16:9、逐帧可控、可直接导出 mp4 的视频项目。内置三套主题和深色 3D 高端画廊模板，不在流程内合成音频，适合后期统一配音。

### Skills 概览

这个仓库目前有 2 个内容创作类 skills，覆盖 AI 视频工作流里相邻但不同的两个阶段：

| Skill | 做什么 | 适合场景 |
|------|--------|----------|
| `mx-shell-prompt` | 把脚本、故事、口播稿或粗略想法转成结构化电影级视频提示词。 | 文生视频工具、分镜提示词、镜头语言、AI 视频生成。 |
| `yyl-remotion-video` | 把口播稿、文章、资料摘要或明确大纲做成可渲染 mp4 的 Remotion 项目。 | 逐帧可控讲解视频、产品 demo、命令行电影、后期统一配音的视频片段。 |

### 怎么选择

如果你的下一步是把提示词发给 Seedance 2.0、Kling、即梦、Sora、Runway、Pika 等视频生成工具，用 **mx-shell-prompt**。它关注的是电影语言：角色、道具、场景、声音、氛围、景别、构图和运镜。

如果你的下一步是生成一个真实的 Remotion 工程并导出 mp4，用 **yyl-remotion-video**。它关注的是 React / TypeScript 实现、时间轴、逐帧动画、检查帧和主题模板。

### 推荐工作流

1. 用 `mx-shell-prompt` 把脚本拆成电影化板块和镜头想法。
2. 如果你想要模型生成画面，就把提示词送进视频生成工具。
3. 如果你想要可控的 16:9 动态讲解片段，就用 `yyl-remotion-video` 做 Remotion 视频。
4. 最后在后期软件里加入口播、字幕、音效和剪辑。

### 许可

MIT
