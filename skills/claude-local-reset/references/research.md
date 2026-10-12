# 社区检索与证据边界

核查日期：2026-10-12。研究对象覆盖 macOS 与 Windows 的 Claude Desktop 和 Claude Code 本地残留。没有读取制作本 skill 的电脑上的 Claude 账号文件，也没有执行清理。

## 结论

社区有这类操作教程，也有本地安装身份文件的直接观察。现有材料不足以确认“每个被封账号都会导致永久硬件标记”，更不足以保证换本地 ID 后新账号不被封。官方隐私政策说明会接收设备、网络和标识符等技术信息，但没有公布设备封禁判定算法。

| 来源 | 能支持什么 | 不能据此推出什么 |
| --- | --- | --- |
| [NodeSeek：被封三十多个 Claude 号的防封策略分享](https://www.nodeseek.com/post-968032-1) | 作者分享在两台 Mac 清理后继续使用的个人经验，并链接自己的 skill。 | 没有控制网络、账号等变量，不能证明设备标记是封号原因，或清理产生了因果效果。 |
| [作者公开的 claude-cleanup skill](https://github.com/suyuan2022/suyuan-skill/blob/main/claude-cleanup/SKILL.md) 与 [其脚本](https://raw.githubusercontent.com/suyuan2022/suyuan-skill/main/claude-cleanup/scripts/claude_cleanup.py) | 可直接审阅所选路径、ID 轮换、钥匙串与备份行为。 | 描述操作的代码不等于 Anthropic 服务器实现；其本地身份方案也不承诺改变平台关联判断。 |
| [Claude Code issue #75419](https://github.com/anthropics/claude-code/issues/75419) | 报告者直接观察到配置中的 `userID`、`machineID` 和 `.claude/backups`。 | 是用户报告，且环境为 Windows；不能视为 macOS 所有版本的官方字段契约。 |
| [Claude Code issue #92318](https://github.com/anthropics/claude-code/issues/92318) | 报告者观察到 `ant-did`、`ant-device-registry.json` 与设备记录，并列出文件时间证据。 | 文件仍保持旧身份时服务器也生成了新设备记录；本地文件与服务器记录并非简单一对一，且该报告不是封号实验。 |
| [Swivel：macOS Desktop profile 工具](https://github.com/jspanji/Swivel) | 作者的实现说明了应用资料目录和钥匙串加密密钥在 profile 恢复中的关系。 | 不能据此推断 `Claude Safe Storage` 是封号标记，或删除密钥会解除限制。 |
| [RengoCode/claude-cleaner](https://github.com/RengoCode/claude-cleaner) 与 [其 shell 实现](https://raw.githubusercontent.com/RengoCode/claude-cleaner/main/claude-reset.sh) | 展示另一种社区清理实现，可对照候选路径。 | “Anti-Ban”“hardware ID”等效果宣称没有受控验证。不能将脚本成功输出当作服务器清理成功。 |

以上是研究资料，不是运行授权。没有复制、下载运行或直接调用第三方清理程序；本 skill 的辅助脚本独立编写。

## 官方资料用于确认基础事实

- [Anthropic 隐私政策](https://www.anthropic.com/legal/privacy)：列举 IP、时区、设备/浏览器信息及各类标识符等技术信息。支持“关联信号可能不限于本地文件”这一推断，不公开具体封禁权重，也不证明读取硬件序列号。
- [Claude Code settings](https://code.claude.com/docs/en/settings)：`~/.claude.json` 保存登录、MCP 和项目状态，`CLAUDE_CONFIG_DIR` 可以改变配置目录。不能把整个 JSON 当作可随便丢弃的追踪文件。
- [Claude Code authentication](https://code.claude.com/docs/en/authentication)（2026-10-11 文档）：macOS 使用钥匙串，写入失败时回退到 `.credentials.json`；Windows 的凭据文件是 `%USERPROFILE%\.claude\.credentials.json`；官方 `/login`、`/logout` 管理凭据。
- [Claude Desktop 3P 数据位置](https://claude.com/docs/third-party/claude-desktop/data-storage)：3P 使用单独的 `Claude-3p` 目录；Windows 上新位置在 `%LOCALAPPDATA%\Claude-3p`。本 skill 默认不归档 3P。
- 消费版 Desktop 的配置路径：MCP 指南确认 macOS 为 `~/Library/Application Support/Claude/claude_desktop_config.json`。Windows 标准安装的公开配置位置是 `%APPDATA%\Claude`；MSIX 安装会把同一目录虚拟化到 `%LOCALAPPDATA%\Packages\Claude_*\LocalCache\Roaming\Claude`。后者来自 2026 年的安装报告，发布者哈希不写死，目录不存在就跳过。
- [Claude Code advanced setup](https://code.claude.com/docs/en/setup)：删除 `~/.claude` 与 `.claude.json` 会删除设置、MCP 和会话历史；Desktop 和编辑器扩展也写入共享目录。因此本 skill 不整体清空 `~/.claude`。
- [MCP 官方本地服务连接指南](https://modelcontextprotocol.io/docs/2026-07-28/develop/connect-local-servers)：确认 macOS 的 Desktop MCP 配置路径为 `~/Library/Application Support/Claude/claude_desktop_config.json`。
- [Anthropic 申诉说明](https://support.claude.com/en/articles/8241253-safeguards-warnings-and-appeals)：解释误封申诉入口；不提供“清本地设备标记即可解封”的方法。

## 本 skill 采用的判断

1. **本地资料目录整体归档**：Desktop 的内部字段随版本变化。完整移走旧 profile 能隔离其中的旧登录存储和身份文件，同时保留原件，不需要猜测签名设备注册表的结构。代价是本地扩展、设置、Code/Cowork 会话暂时退出当前 profile，后续需要按需恢复。
2. **不制造设备注册表 JSON**：社区 shell 会重写 `ant-device-registry.json`；这可能与版本所需结构不符。本 skill 将旧文件随 profile 归档，后续由官方应用管理新状态。
3. **CLI 操作单独选择**：Desktop 清理并不等于清理 Claude Code。仅当用户要求时，对实际存在且格式符合已知社区观察的身份键进行轮换；保留项目/MCP 配置与 skills。
4. **保留加密密钥**：应用 profile 中的加密登录资料被归档后，当前 profile 无法通过这些旧文件使用旧 token。钥匙串加密密钥暂不删除，以保留解密回滚条件；这不等于证明钥匙串里没有其他身份信号。
5. **不修改系统时区或硬件身份**：来源没有证明这能清除封禁。用户真实所在地、账号、网络或服务端历史也不会因为移走几个文件而改变。

## 实际覆盖范围

Desktop 白名单由 `scripts/claude_local_reset.py` 按系统选择：macOS 是应用资料、缓存、HTTPStorages、WebKit、日志和偏好 plist；Windows 是 `AppData/Roaming/Claude`，外加已经存在的 MSIX 虚拟化资料目录。安装目录、Claude-3p、浏览器 profile、钥匙串、Windows 凭据管理器、企业策略和远程记录没有被覆盖。没有这些路径不代表从未安装 Claude，也不代表没有任何关联信息。执行前若发现第三方多 profile 工具或自定义目录，应先核实实际存储位置。

可验证的是：指定文件被归档、原件仍在、已知 CLI 字段按所选方式变化、其他 CLI 内容保留。不可验证的是：服务器已遗忘这台电脑、账号会不会被封、未来版本一定会重新生成同一格式的 ID。
