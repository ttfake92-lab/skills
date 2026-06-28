---
name: macos-migration
description: >
  macOS 系统迁移助手 — 两阶段：先在旧系统采集清单（JSON），再在新系统还原。
  Use when user mentions: 系统迁移、换电脑、新装系统、Time Machine 恢复、
  数据迁移、重装系统、migration、setup new mac、restore from backup、备份系统。
  自动检测当前是旧系统（采集模式）还是新系统（还原模式）。
  前置：先做一次 Time Machine 全量备份；唯一软件依赖是 Homebrew。
---

# macOS 系统迁移助手

两阶段设计：**旧系统采集 → 新系统还原**。中间通过一个 JSON 清单文件衔接。

## 前置要求（务必先做）

**在旧系统上先做一次 Time Machine 全量备份。** 这是整个迁移的安全网——新系统上
任何一步出问题，都能从这份全量备份里捞回来。还原阶段也直接从 Time Machine 挂载点
读取数据。

> 没有 Time Machine 全量备份，就不要开始迁移。

## 运行模式检测

判断「采集还是还原」只看一个信号：**清单文件在不在**。

```bash
ls ~/migration-manifest.json 2>/dev/null
```

| 条件 | 模式 |
|------|------|
| 无清单文件 | 采集模式（在旧系统上，生成清单） |
| 有清单文件 | 还原模式（在新系统上，读清单还原） |

Time Machine 只是还原阶段的**数据来源**，不参与模式判断。
用户也可以直接指定：「采集」「备份」「还原」「迁移」。

---

## 第零步：Homebrew 检查（两种模式都必须）

```bash
which brew && brew --version || echo "NOT_INSTALLED"
```

- 已安装 → 继续
- 未安装 → **引导用户在终端手动执行**安装命令。这一步需要输入管理员密码（sudo），
  无法静默完成：

  ```bash
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  ```

  装完后按提示把 brew 加入 PATH（Apple Silicon：`eval "$(/opt/homebrew/bin/brew shellenv)"`），
  再继续。

---

## 模式 A：旧系统采集

在旧系统上运行，扫描所有软件、配置、开发环境，生成 `~/migration-manifest.json`。

### A1. Homebrew 软件包

```bash
brew list --formula
brew list --cask
brew tap
```

### A2. 系统 Applications

```bash
ls /Applications/
ls ~/Applications/ 2>/dev/null
```

与 Homebrew cask 列表对比，标记哪些是 Homebrew 装的、哪些是手动/App Store 装的。

### A3. Mac App Store 应用

```bash
mas list 2>/dev/null || echo "mas not installed"
```

如果 `mas` 未安装，提示用户是否要安装（`brew install mas`）。

### A4. npm 全局包

```bash
npm ls -g --depth=0 2>/dev/null
```

### A5. uv 工具

```bash
uv tool list 2>/dev/null
```

### A6. pip/pipx 包

```bash
pip list 2>/dev/null
pipx list 2>/dev/null
```

### A7. Go 全局工具

```bash
ls ~/go/bin/ 2>/dev/null
```

### A8. 配置文件扫描

扫描 home 目录下的 dotfiles 和配置目录：

```bash
ls -la ~/
```

重点采集：
- Shell：`.zshrc`, `.zshenv`, `.zprofile`, `.bashrc`, `.bash_profile`
- Git：`.gitconfig`, `.gitignore_global`
- SSH：`.ssh/`
- 编辑器：`.claude/`, `.codex/`, `.config/`, `.cursor/`, `.zed/`
- 容器：`.docker/`, `.kube/`
- 包管理器：`.npm/`, `.nvm/`, `.bun/`, `.cargo/`, `.rustup/`
- 其他应用配置：`.SwitchHosts/`, `.ollama/`, `.syncthing/` 等

**敏感数据先问后采**：`.ssh/`（私钥）、dotfiles 里可能含 token、`.aws/`、`.kube/`、
钥匙串等都是密钥级信息。采集这些之前**先问用户是否纳入**：

- 用户同意 → 正常采集，并**明确提醒**：「清单和备份里含私钥/凭据，传输、存放、
  通过网盘或聊天工具发送时注意不要外泄。」
- 用户拒绝 → 跳过这些项，在清单里记入 `"skipped_sensitive": [...]`，让用户日后
  自行手动迁移（差异报告里也会再列一次）。

### A9. LaunchAgents（自启动服务）

```bash
ls ~/Library/LaunchAgents/
```

### A10. 用户项目目录

列出 home 目录下非 dotfile 的顶层目录：

```bash
ls -d ~/*/ 2>/dev/null
```

排除系统目录（Library, Applications, Public 等），记录用户自建的项目/数据目录。

### A11. Shell 环境

```bash
# 当前 shell 版本
zsh --version
# Homebrew 路径 / 版本管理器（nvm、fnm 等）配置
grep -iE 'brew|nvm|fnm' ~/.zshrc
```

### A12. 其他易漏项

迁移时最容易漏、丢了又很烦的几类：

```bash
# 编辑器扩展
code --list-extensions 2>/dev/null
cursor --list-extensions 2>/dev/null

# 自购/自装字体
ls ~/Library/Fonts/ 2>/dev/null

# 定时任务
crontab -l 2>/dev/null

# 手动装到非 Homebrew 路径的命令行工具
ls /usr/local/bin/ 2>/dev/null
ls /opt/ 2>/dev/null
```

> 系统偏好（`defaults`）量大且与机型强相关，不自动采集；如用户在意，在还原差异
> 报告里提醒手动核对（键盘、触控板、Dock、快捷键等）。

### A13. 生成清单文件

将以上所有信息写入 `~/migration-manifest.json`：

```json
{
  "version": 1,
  "captured_at": "2026-06-28T16:00:00+08:00",
  "source_macos": "15.5",
  "source_hostname": "old-macbook",

  "homebrew": {
    "taps": ["user/repo", "..."],
    "formulas": ["git", "node@22", "..."],
    "casks": ["1password", "docker-desktop", "..."]
  },

  "applications": {
    "homebrew_casks": ["claude", "firefox", "..."],
    "app_store": [{"id": 123456, "name": "App Name"}],
    "manual": ["Final Cut Pro.app", "..."]
  },

  "package_managers": {
    "npm_global": ["@anthropic-ai/claude-code", "..."],
    "uv_tools": ["nano-pdf", "..."],
    "pip_packages": ["package1", "..."],
    "go_binaries": ["tool1", "..."]
  },

  "configs": {
    "dotfiles": [".zshrc", ".gitconfig", ".ssh", "..."],
    "config_dirs": [".claude", ".codex", ".config", ".docker", "..."],
    "app_support_keys": ["Syncthing", "obs-studio", "..."]
  },

  "editor_extensions": {
    "vscode": ["ms-python.python", "..."],
    "cursor": ["..."]
  },

  "fonts": ["MyFont.otf", "..."],
  "crontab": "<crontab -l 原文，无则空>",
  "manual_bins": ["/usr/local/bin/foo", "/opt/bar", "..."],

  "launch_agents": ["com.github.syncthing.plist", "..."],

  "user_dirs": ["Projects", "Sites", "..."],

  "shell": {
    "shell": "zsh",
    "brew_in_path": true,
    "nvm_installed": true,
    "custom_env_vars": {}
  },

  "skipped_sensitive": []
}
```

### A14. 采集完成

输出清单摘要，提示用户：

```
✅ 采集完成！清单已保存到 ~/migration-manifest.json

采集内容：
- Homebrew: X taps, Y formulas, Z casks
- 应用: X 个 Homebrew, Y 个 App Store, Z 个手动安装
- npm 全局包: X 个
- 配置文件: X 个 dotfiles, Y 个配置目录
- 编辑器扩展: X 个 / 字体: Y 个 / 定时任务: 有/无
- 自启动服务: X 个
- 用户目录: X 个
- 跳过的敏感项: X 个（用户选择不采集）

⚠️ 若采集了 .ssh / dotfiles 中的凭据，清单与备份含私钥，传输存放注意不要外泄。

下一步：确认已有 Time Machine 全量备份，将 migration-manifest.json 复制到新系统，
再次运行此 skill。
```

---

## 模式 B：新系统还原

在新系统上运行，读取 `migration-manifest.json` 并逐步还原。

### B0. 获取清单

```bash
ls ~/migration-manifest.json
```

如果不存在：

```
找不到 migration-manifest.json。

请将旧系统上采集的清单文件复制到新系统的 home 目录：
  scp old-mac:~/migration-manifest.json ~/migration-manifest.json

或者手动指定路径。
```

### B1. Homebrew 软件安装

> 前提：第零步已确认 Homebrew 装好（需用户手动输密码安装）。装好之后这一步才能跑。

读取清单中的 `homebrew` 字段。

```bash
# 添加 taps（逐个）
brew tap <user>/<repo>

# 信任第三方 taps
brew trust <user>/<repo>

# 安装 formulas（批量，失败不回滚整批）
brew install <formula1> <formula2> ...

# 安装 casks（逐个，避免回滚）
for cask in <cask1> <cask2> ...; do
  brew install --cask "$cask" 2>&1 | tail -3
done
```

没装上的（需 sudo、网络失败等）先记下，最后在 B7 差异报告统一列给用户。

### B2. 其他包管理器

读取清单中的 `package_managers` 字段。

```bash
# npm
npm install -g <pkg1> <pkg2> ...

# uv
uv tool install <pkg1> <pkg2> ...

# pip（如果需要）
pip install <pkg1> <pkg2> ...

# go binaries
go install <pkg1>@latest <pkg2>@latest ...
```

### B3. 配置文件恢复

读取清单中的 `configs` 字段。

有两种数据来源，优先级：

1. **Time Machine 直接复制**（如果有挂载）
2. **用户手动提供**（如果清单是从别的方式获取的）

```bash
TM="<Time Machine 用户目录路径>"
LOCAL="/Users/<username>"

# dotfiles
rsync -av --ignore-existing "$TM/.zshrc" "$LOCAL/"
rsync -av --ignore-existing "$TM/.gitconfig" "$LOCAL/"
rsync -av --ignore-existing "$TM/.ssh/" "$LOCAL/.ssh/"

# 配置目录
for dir in .claude .codex .config .docker .SwitchHosts ...; do
  rsync -av --ignore-existing "$TM/$dir/" "$LOCAL/$dir/"
done
```

> 恢复 `.ssh/` 后确认权限：`chmod 700 ~/.ssh && chmod 600 ~/.ssh/id_*`。
> 如无 Time Machine，提示用户提供配置文件的来源路径。

### B4. Library 关键子目录

从 Time Machine 恢复（如果有）：

| 子目录 | 命令 | 说明 |
|--------|------|------|
| Preferences | `cp -rn` | 应用偏好设置 |
| Keychains | `cp -rn` | 钥匙串 |
| Containers | `cp -rn` | 沙盒应用数据 |
| Group Containers | `cp -rn` | 共享容器 |
| Mail | `cp -rn` | 邮件数据 |
| Safari | `cp -rn` | 书签/历史 |

> rsync 在 Time Machine APFS 快照上会报 `io_read_flush` 错误，Library 用 `cp -rn`。

### B5. LaunchAgents（自启动服务）

读取清单中的 `launch_agents` 字段。

逐个检查并创建对应的 plist 文件，然后 `launchctl load`。

### B6. 其他易漏项还原

对应采集阶段的 A12：

```bash
# 编辑器扩展（逐个装）
for ext in <清单 editor_extensions.vscode>; do code --install-extension "$ext"; done

# 字体
rsync -av --ignore-existing "$TM/Library/Fonts/" "$LOCAL/Library/Fonts/"

# 定时任务：先看新机器有没有现成的，再决定是否合并写入，避免覆盖
crontab -l 2>/dev/null
```

> `/usr/local/bin`、`/opt` 里的手动安装工具无法自动还原，列入 B7 差异报告提醒用户。

### B7. 未安装项目处理

对比清单和实际安装结果，输出差异：

```
## 还原差异报告

### ❌ 安装失败（需手动处理）
- docker-desktop: 需要 sudo → 手动执行 `brew install --cask docker-desktop`
- tailscale-app: 需要 sudo → 手动执行 `brew install --cask tailscale-app`
- android-platform-tools: 网络问题 → 稍后重试

### ⚠️ 清单中有但无 Homebrew cask
- Final Cut Pro: App Store 应用
- DaVinci Resolve Studio: 手动下载 → blackmagicdesign.com

### ℹ️ App Store 应用（需手动安装或用 mas）
- GarageBand
- Infuse

### 🔧 需手动核对（非软件）
- 系统偏好 defaults：键盘 / 触控板 / Dock / 快捷键
- /usr/local/bin、/opt 手动工具：<manual_bins 列表>
- 拒绝采集的敏感项：<skipped_sensitive 列表>
```

---

## 踩坑记录

### 1. `brew bundle` 一个失败全部回滚

**问题**：`brew bundle --file=Brewfile` 中任何一个 cask 下载失败，整批已安装的包全部回滚。

**解决**：不用 `brew bundle`。taps 逐个添加，formulas 批量安装，casks 逐个安装。

### 2. 第三方 taps 未信任

**问题**：Homebrew 6+ 要求显式信任第三方 taps，否则报 `Refusing to load cask from untrusted tap`。

**解决**：`brew trust <user>/<repo>`

### 3. rsync 在 Time Machine APFS 快照上报错

**问题**：`rsync -av --ignore-existing` 复制 Library 子目录时报 `io_read_flush` 错误。

**解决**：Library 子目录改用 `cp -rn`。

### 4. `cp -rn` 的 "Operation not permitted"

**问题**：macOS SIP/TCC 保护的文件无法直接复制（系统 Preferences、Mail 数据库等）。

**影响**：不影响使用。系统或应用在首次启动时自动重建。

### 5. `cp -rn` 的 "Not a directory" 错误

**问题**：Containers 中系统容器使用符号链接指向标准目录。

**影响**：不影响使用。用户应用的容器数据已正确复制。

### 6. 需要 sudo 的 casks

**问题**：`docker-desktop`、`tailscale-app`、`adobe-creative-cloud` 安装时需要 sudo。

**解决**：记录在差异报告中，让用户手动执行。

### 7. node 版本冲突

**问题**：`brew install node@22` 后 `brew link` 失败。

**解决**：`brew link --overwrite node@22`

### 8. Homebrew 检测不到非 Homebrew 安装的软件

**问题**：旧系统上通过 DMG/PKG/App Store 安装的软件，Homebrew 无法感知。

**解决**：采集阶段扫描 `/Applications/` 并与 `brew list --cask` 对比，标记出手动安装的应用，还原时单独处理。

## 原则

1. **先有 Time Machine 全量备份再开始**：这是出错时唯一的兜底，也是还原的数据来源
2. **Homebrew 由用户手动安装**：需要输密码（sudo），引导用户在终端执行，装好再继续
3. **两阶段分离**：采集和还原是独立的步骤，通过 JSON 文件衔接
4. **敏感数据先问后采**：私钥/凭据采不采由用户决定；采了就提醒外泄风险
5. **绝不覆盖已有文件**：所有 rsync/cp 都带 `--ignore-existing` 或 `-n`
6. **先小后大**：按目录大小排序复制，方便快速验证
7. **先做计划再动手**：还原前输出清单摘要，让用户确认
8. **记录差异**：还原后输出差异报告，列出需要手动处理的项目
9. **逐个安装 casks**：避免 `brew bundle` 的回滚问题
10. **验证每一步**：安装后 `brew list` 确认，复制后 `du -sh` 验证大小
11. **跳过缓存**：Library/Application Support 中的缓存数据不恢复
