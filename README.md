# Skills

Claude Code & AI Agent Skills — 安装即用。

## 快速安装

### 全局安装（所有项目通用）

```bash
SKILL_BASE_URL=https://github.com/ttfake92-lab/skills/tree/main npx skill skills/<skill-name> && mv .codebuddy/skills/<skill-name> ~/.codebuddy/skills/ && rm -rf .codebuddy
```

### 仅当前项目

```bash
SKILL_BASE_URL=https://github.com/ttfake92-lab/skills/tree/main npx skill skills/<skill-name>
```

### 省略环境变量

在 `~/.zshrc` 或 `~/.bashrc` 中添加：

```bash
export SKILL_BASE_URL=https://github.com/ttfake92-lab/skills/tree/main
```

之后直接 `npx skill skills/<skill-name>` 即可。

## 可用 Skills

| Skill | 用途 |
|-------|------|
| [mx-shell-prompt](skills/mx-shell-prompt) | 视频提示词写作 — 把想法变成电影级 AI 视频提示词 |

## 支持的 Agent

本仓库的 Skills 遵循 [Agent Skills](https://agentskills.io/) 标准格式，支持所有兼容 `.codebuddy/skills/` 的 AI 编程助手：Claude Code、Cursor、Windsurf、CodeBuddy 等。

## 许可

MIT
