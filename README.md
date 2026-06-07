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
- **[yyl-remotion-video](./skills/yyl-remotion-video/SKILL.md)** — Build 16:9 Remotion video projects from scripts, articles, notes, or outlines. Creates frame-driven React/TypeScript animations, estimates duration without synthesizing audio, renders still checks, and exports mp4 with built-in themes for command-line films, product demos, and research explainers.

### Why This Skill Exists

#### The Problem: AI Video Prompts Are Too Vague

Most people write video prompts like "a cool cyberpunk scene with a robot". The result? Generic, boring outputs that look like everyone else's.

AI video tools are only as good as the prompts you feed them. Without structure, you get:
- Flat, lifeless scenes with no cinematic language
- Inconsistent characters across shots
- No sense of composition, lighting, or camera movement

#### The Fix: Structured Cinematic Prompts

`mx-shell-prompt` enforces a three-pillar framework:

1. **Who & Where** — Character descriptions with physical precision, not vague traits
2. **What Feel** — Specific cameras, lenses, color grading — not just "cinematic"
3. **What Happens** — Shot-by-shot breakdowns with composition, camera movement, and action

Each prompt includes a complete shot catalog, cinematic vocabulary reference, and composition templates so you never stare at a blank page.

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
- **[yyl-remotion-video](./skills/yyl-remotion-video/SKILL.md)** — Remotion 视频制作。把口播稿、文章、资料摘要或明确大纲做成 16:9、逐帧可控、可直接导出 mp4 的视频项目。内置 command-film、studio-white、research-desk 三套主题，不在流程内合成音频，适合后期统一配音。

### 为什么做这个 Skill

#### 问题：AI 视频提示词太模糊

大多数人写视频提示词就像「一个酷的赛博朋克机器人场景」。结果？千篇一律、毫无生气的画面。

AI 视频工具的能力上限就是你给它的提示词。没有结构，你会得到：
- 没有电影语言的扁平场景
- 镜头之间角色不一致
- 没有构图、灯光、运镜的概念

#### 解法：结构化电影提示词

`mx-shell-prompt` 强制使用三支柱框架：

1. **谁在哪** — 角色描述要精确到物理层面，不是模糊的性格标签
2. **什么感觉** — 指定具体摄影机、镜头、色彩方案 —— 不是只写「电影质感」
3. **发生什么** — 逐镜头拆解，包含景别、构图、运镜和动作

每个提示词都包含完整的景别速查表、电影词汇库和构图模板，让你永远不用对着空白页发呆。

### 许可

MIT
