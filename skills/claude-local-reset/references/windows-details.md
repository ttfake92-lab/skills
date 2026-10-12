# Windows 补充操作

仅在当前系统是 Windows，或用户要求相应范围时阅读。制作 skill 的阶段不执行这里的步骤。路径白名单以 `scripts/claude_local_reset.py` 为准，本文件解释哪些位置故意不进白名单。

资料核对：2026-10-12。

## Desktop 资料在两个位置之一

标准安装的应用资料在 `%APPDATA%\Claude`，也就是用户目录下的 `AppData/Roaming/Claude`。配置文件名仍是 `claude_desktop_config.json`。日志通常在这个目录的 `logs` 里，随整个目录一起归档。

微软商店或 MSIX 安装会把同一份资料虚拟化到：

```text
%LOCALAPPDATA%\Packages\Claude_<发布者哈希>\LocalCache\Roaming\Claude
```

脚本只在这个目录已经存在时归档它，并且只移动 `LocalCache\Roaming\Claude`。发布者哈希不写死。同级的安装文件、`LocalCache\Local` 和其他应用的包目录保持不动。

不归档：

- `%LOCALAPPDATA%\AnthropicClaude`：这是安装程序和程序文件，不是使用痕迹。
- `%LOCALAPPDATA%\Claude-3p` 与 `%APPDATA%\Claude-3p`：这是单独的 3P 模式，macOS 上对应的 `Claude-3p` 同样不在默认白名单。
- `C:\Program Files\ClaudeCode` 与企业托管策略。发现托管策略时停止，不要改。

两个资料目录都存在时，预览会同时列出。不要只清 `%APPDATA%\Claude` 就认为 MSIX 里的旧身份也没了。

## 退出与文件锁

关闭窗口不够。从系统托盘退出 Claude，并退出 Claude Code。Windows 上文件被占用时重命名会失败，脚本停止并保留已完成的归档，不会强行结束进程。进程复检只看映像名 `Claude.exe`、`claude.exe`、`claude-code.exe`、`claude-code-router.exe`。由 `node.exe` 启动、命令行里才看得到的路由程序不会出现在这个名单里，所以执行前仍要确认那些窗口已经关掉。

## Claude Code

`%USERPROFILE%\.claude` 与 `%USERPROFILE%\.claude.json` 和 macOS 使用同一套相对路径。官方说明 Windows 的登录凭据放在 `%USERPROFILE%\.claude\.credentials.json`，不是 macOS 钥匙串。`--code-identity` 会归档这个文件里已存在的副本，并轮换符合已知格式的 `userID` / `machineID`。

归档文件不等于官方注销。仍要在 Claude Code 里执行 `/logout`，再 `/login`。不要按名字批量清理 Windows 凭据管理器，也不要删除整个用户配置目录。`CLAUDE_CONFIG_DIR` 存在时，身份选项停止。

## 网络检查怎么读

系统代理来自当前用户的 WinINet 开关：`ProxyEnable`、是否存在自动配置地址、以及读得到的 `AutoDetect`。脚本不记录 `ProxyServer`，因为其中可能有账号和密码。没有读到自动检测开关时，质检保持待核实，不会补一个 0 来显示通过。

hosts 文件是 `%SystemRoot%\System32\drivers\etc\hosts`。PowerShell 配置与 Git Bash 的 `.bashrc` 一类文件只作文本扫描，不执行。`tzutil /g` 得到的是 Windows 时区 ID；和 IANA 名称对照时用 Node 的结果，不要把 `Taipei Standard Time` 直接写成 `Asia/Taipei` 的通过项。

备份目录仍在用户主目录的 `ClaudeLocalResetBackups`。Windows 的目录权限不是 Unix 的 `0700`；隔离靠当前用户的配置文件权限，不要把 chmod 的结果说成只有本人可读。
