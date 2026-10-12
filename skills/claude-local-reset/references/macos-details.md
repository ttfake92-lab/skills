# macOS 补充操作

仅在当前系统是 macOS，或用户要求相应范围时阅读并操作。Windows 的对应说明在 [windows-details.md](windows-details.md)。所有示例里的占位路径必须换成实际路径，不照抄尖括号。制作 skill 的阶段不执行这里的步骤。路径白名单以脚本为准。

## Claude Code：文件身份与真正注销是两件事

`--code-identity` 会轮换已存在的 64 位小写十六进制 `userID` / `machineID`，移除 `anonymousId` 与 `oauthAccount` 本地元数据。它将 `.claude/backups/` 下的 `.claude.json.backup.*`、主目录的 `~/.claude.json.backup` 旧身份快照、`statsig`、`telemetry` 和可能存在的 `.credentials.json` 归档，避免这些文件留在当前默认目录——旧快照里同样带着旧身份字段，留着它等于白轮换；不会改 `settings.json`、skills、plugins、项目记录或 MCP 字段。

这些身份键不是硬件序列号。格式不匹配时脚本在写盘前停止；不要通过放宽匹配、正则替换 JSON 或改动所有 UUID 来绕过检查。

**脚本不调用 macOS 钥匙串。** 若旧 CLI 登录来自钥匙串，重置文件之后仍可能取得该凭据。需使用当前版本官方 `/logout` 注销旧登录，再使用 `/login` 登录所选账号。注销会移除／撤销凭据，不能靠恢复文件保证原凭据恢复有效。用户密码只在官方登录页或系统原生提示中输入。

如果原生注销无法工作，需要单独的钥匙串排障：只检查对应服务名称及归属，不读取密码内容。默认配置常见服务名称是 `Claude Code-credentials`，自定义配置可能有不同的服务名称。不要根据搜索词 `Claude` / `Anthropic` 批量删除所有结果，不执行 `security dump-keychain`，也不使用输出秘密的 `-w` / `-g`。

只有用户明确选择删除某个已核实的 CLI 登录凭据时，才通过钥匙串访问删除那个条目。这不是可自动回滚的文件操作；结果报告应写“该凭据已移除，需要重新登录”。不用额外安装工具。

`CLAUDE_CONFIG_DIR`、第三方账号切换工具、Cowork VM 和远程开发机可能有独立状态。脚本遇到自定义环境变量会停止其 Code 身份选项；不要假定默认 `~/.claude` 的处理覆盖这些环境，也不要主动递归清理项目目录。

## Desktop 归档范围补充

Desktop 重置除应用资料目录、Caches、HTTPStorages、WebKit 外，还归档 `~/Library/Logs/Claude`（桌面与 MCP 运行日志）和 `~/Library/Preferences/com.anthropic.claudefordesktop.plist`（仅当实际存在）。这些同样是使用痕迹；归档后应用下次启动会重新生成默认值，回滚批次可整体还原。

偏好 plist 由 macOS 偏好服务（cfprefsd）管理：归档后该服务可能从内存缓存重建同名文件，属于正常现象，不代表归档失败；复检以文件系统与回执记录为准，不要为了“删干净”而反复执行重置。清理 plist 前先确认没有其他工具依赖其中的自定义键。

## Desktop 钥匙串

社区直接实现显示 `Claude Safe Storage` / `Claude Key` 用于解密 Desktop 登录资料，见 [Swivel](https://github.com/jspanji/Swivel)。不同版本仍须核实。它不是已经证实的“封禁标签”。

本 skill 默认保留这些加密密钥，旧 token 存储随完整 Desktop profile 归档。这样支持恢复原 profile。若将来专门排查钥匙串损坏，需提前说明删除加密密钥可能使旧 profile 无法解密，用户接受失去该回滚能力后再进行；不能声称“彻底清理了所有设备信息”。

也不要删除整个登录钥匙串、浏览器的 Safe Storage 密钥或公司管理配置。

## 浏览器：只清 Claude 的站点状态

如果 Desktop 登录通过默认浏览器继续带入旧账号，先退出该网站账号；必要时在浏览器设置中移除 **`claude.ai` 的站点数据**。页面实际使用其他 Claude 域名时逐一核实再处理。可能需要重新完成登录。

不要删除全部浏览器用户目录、全部 cookies、密码或 Google/Apple 的身份提供方会话。独立浏览器 profile 或无痕窗口可以隔离部分站点存储，但不能改变网络地址、硬件身份或服务器历史；不能把它叫作“全新物理设备”。

浏览器操作需要用户要求该范围。操作后只确认站点数据已清除，不为测试反复创建账号或登录新号。

## 恢复局部配置

Desktop 重置后如需 MCP，在用户要求恢复时，从本批次的 `original/Library/Application Support/Claude/claude_desktop_config.json` 读取并核对，复制该配置到新 profile 即可。配置可能含服务环境变量和秘密，内容不要打印、上传或附在交付消息中。不要复制 `config.json`、Cookies、Local Storage、IndexedDB、旧身份文件或整份资料目录到新环境。

完整回滚会恢复旧 profile 与旧本地身份。跨账号移植 Desktop Code/Cowork 本地会话没有验证；有需要先备份并单独研究，不承诺“历史全部保留在新账号里”。
