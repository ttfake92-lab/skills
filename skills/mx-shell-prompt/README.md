# MX Shell Prompt — 视频提示词写作

把粗略想法转化为结构化的电影级视频提示词，适用于 Seedance 2.0、Kling、Sora、Runway、Pika 等所有文生视频工具。

## 安装

```bash
SKILL_BASE_URL=https://github.com/ttfake92-lab/skills/tree/main npx skill skills/mx-shell-prompt
```

或设置别名后使用：

```bash
export SKILL_BASE_URL=https://github.com/ttfake92-lab/skills/tree/main
npx skill skills/mx-shell-prompt
```

## 使用方式

安装后在 Claude Code 中直接对话即可。触发方式：

- 描述一个视频想法
- 说「帮我写一个视频提示词」
- 提到 Seedance、Kling、Sora 等关键词
- 说「分镜」「视频生成」等

## 核心理念

每个好提示词由三根支柱构成：

1. **谁在哪** — 基础设定（角色 + 场景）
2. **什么感觉** — 氛围与画质（风格 + 摄影机 + 色彩）
3. **发生什么** — 画面内容（景别 + 构图 + 运镜 + 动作）

## 包含内容

| 文件 | 用途 |
|------|------|
| `SKILL.md` | Skill 定义与工作流程 |
| `references/template.md` | 提示词结构模板 |
| `references/cinematic-vocabulary.md` | 摄影机、镜头、色彩、灯光速查 |
| `references/shot-catalog.md` | 景别、构图、运镜速查表 |
| `references/example-cyber-atom.md` | 完整示例：赛博原子风格 |

## 许可

MIT
