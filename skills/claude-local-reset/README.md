# Claude 本地状态重置（claude-local-reset）

在 macOS 和 Windows 上备份并重置 Claude Desktop 的本地状态，可选处理 Claude Code 的本地身份，再做只读网络检查，交出 HTML 质检回执和防封号指南。

它只处理列出的本地文件，可以回滚。不能证明 Anthropic 不再关联这台设备，也不承诺解封。Linux 不要套用。

## 安装

只装这一个：

```bash
npx skills add ttfake92-lab/skills --skill claude-local-reset
```

从整包清单里勾选：

```bash
npx skills add ttfake92-lab/skills
```

直接指向这个目录：

```bash
npx skills add https://github.com/ttfake92-lab/skills/tree/main/skills/claude-local-reset
```

## 边界

- 默认只归档 Claude Desktop 白名单目录。Claude Code、浏览器和钥匙串都要单独授权。
- Windows 不归档安装目录、`Claude-3p` 和整个 `Packages`。微软商店安装只移动已经存在的数据目录。
- 不永久删除。备份留在本机 `~/ClaudeLocalResetBackups/`，不要上传。
- 清理本地文件不能撤销账号封禁。

运行说明见 [SKILL.md](./SKILL.md)。

## Install

```bash
npx skills add ttfake92-lab/skills --skill claude-local-reset
```

Backs up allowlisted Claude Desktop state on macOS and Windows, optionally rotates Claude Code local identity, then writes an HTML network-check receipt and a risk-reduction guide. It does not unban an account. Do not use it on Linux.
