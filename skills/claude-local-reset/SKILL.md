---
name: claude-local-reset
description: 在 macOS 与 Windows 上备份重置 Claude Desktop 本地状态，检查网络出口、DNS/WebRTC、代理与中转配置，自动交付 HTML 质检回执和可跳转的 Claude 防封号指南。使用时先停下来确认任务范围：清除 Claude 本地使用痕迹，或只做网络检查；指南分别引导首次使用与曾被限制用户完成手动准备（时区、出口、TUN、登录前自检、账号与支付、日常使用、出发前清单）、调用 skill 质检。可单独检查环境；不承诺解除服务器关联或防止封号。Linux 与未核实的安装方式不要套用。
---

# Claude 本地状态重置

目标是让下次启动使用重新生成的本地状态，并保留回滚材料。所谓“设备标记”需要拆开：本地安装 ID、账号登录凭据、浏览器站点数据，以及 Anthropic 已保存的服务器记录。这个 skill 只能处理列出的本地文件，不能证明服务器不再关联该设备。

首次解释依据或用户询问“防封号”时，阅读 [references/research.md](references/research.md)。社区教程报告了本地身份文件，但没有提供足以证明“删除后解除设备封禁”的对照证据。不要把“发现 ID 文件”解释成“这台电脑已被拉黑”。

## 确定当前任务

用户没有写明要哪条路径时，先停下来问，再执行。问的时候列出两条主路径和默认行为：

1. **清除 Claude 的本地使用痕迹**：走 Desktop 重置（可选扩展 Claude Code 本地身份、浏览器与钥匙串），执行前先预览路径和影响，已有授权时不再重复确认。
2. **只做网络与路由检查**：只读检查出口、DNS/WebRTC、代理与中转，生成回执，不改任何文件。

用户回答前不执行任何清理，也不默认选择重置；等待期间可以先做只读预览。初次问询时同时说明：网络检查可以单独做，不必先清理本地状态；只要指南或解释时直接交付，不运行检查。用户在消息中已写明意图（如“只检查”“重置”“只要指南”）或复现了指南里的提示词时，直接按对应路径执行，不重复追问。

- 用户只要求制作或更新 skill、研究、教程或解释：只交付资料，不检查真机账号与网络，不运行任何清理；测试仅使用模拟文件与命令结果。
- 用户要求审计：只运行预览，报告存在的候选路径与操作范围；不要输出 ID、邮箱、cookie、token 或 JSON 原文。
- 用户明确要求执行重置：先展示具体路径和影响，已有授权涵盖这些操作时继续，不增加重复确认。若发现需求之外的钥匙串、浏览器或 Claude Code 操作，先完成已授权范围，再说明剩余部分。
- 用户首次使用 Claude 或只想减少配置问题：走指南的首次使用路径，默认只读网络质检；没有旧状态需要处理时不运行重置。
- 用户曾被封号、停用或限制：先说明原账号官方申诉与服务/用量提示的区别；按要求做只读排查。不能把清理本地 ID、创建新账号或网络通过写成账号已恢复。
- 用户只要打开指南：不运行审计或检查，直接生成包含指南的缺项回执；用户后续明确要求质检时再实际执行。
- Linux 及其他平台：不要套用本脚本。macOS 与 Windows 使用同一入口，路径由脚本按当前系统选择；细节见 [references/macos-details.md](references/macos-details.md) 与 [references/windows-details.md](references/windows-details.md)。

默认只处理 Claude Desktop。仅仅发现安装了 Claude Code，并不授权重置它。

重置成功后继续执行下方“网络与路由检查”，最后生成并打开 HTML 回执；即使部分失败也交付真实的完成状态。用户也可单独请求网络检查，不必先清理本地身份。网络检查不代表授权修改代理、浏览器或 IPv6；范围不明确时先完成只读检查，再列出未测项目。

## 检查与预览

使用本 skill 实际所在目录的绝对路径，下面的 `SKILL_DIR` 应由执行者替换。脚本需要 Python 3.10+，仅使用标准库。没有可用 Python 时报告缺少运行条件，不擅自安装依赖。

```sh
SKILL_DIR="/absolute/path/to/claude-local-reset"
python3 "$SKILL_DIR/scripts/claude_local_reset.py"
```

Windows 上若没有 `python3`，改用 `py -3`，并把路径换成该技能目录。两套命令都不安装 Python。

不带 `--apply` 时只读：不创建备份目录、不退出应用、不改钥匙串，也不访问网络。脚本预览固定的 Desktop 目录；不存在的路径跳过。不要把未发现的路径描述成已清理。

默认操作是将旧 Desktop 应用资料完整归档，而不是猜测未知 JSON 字段并写入伪造的设备注册表。归档包含旧的 `ant-did`、登录存储、桌面端 MCP 配置、扩展和本地 Code/Cowork 会话（仅当当前版本实际存在）。macOS 另含桌面日志与偏好 plist；Windows 另含标准资料目录，以及已经存在的 MSIX 虚拟化资料目录。安装程序、Claude-3p 资料和其他应用的包目录不在白名单里。偏好 plist 由 macOS 偏好服务管理，归档后该服务可能从缓存重建同名文件；复检以文件系统为准，回滚批次可恢复原件。重置后这些本地内容暂时不显示，原件仍在备份里。具体路径以脚本白名单为准。

## 执行 Desktop 重置

先让用户正常退出 Claude Desktop、Claude Code、Cowork 任务及编辑器内的 Claude 会话。Windows 还要从系统托盘退出，只关窗口不够。不要强杀正在写入文件的进程。由独立终端执行，不能让正在运行的 Claude 执行者清理自己的状态。

```sh
python3 "$SKILL_DIR/scripts/claude_local_reset.py" --apply
```

脚本复检相关进程，然后把现存白名单目录以同一文件系统的重命名方式移到 `~/ClaudeLocalResetBackups/<timestamp>/original/`，逐项记录结果并核验移动对象。不存在永久删除。失败即停止并报告备份位置与部分完成状态。

其范围不包含：`/Applications/Claude.app`、系统硬件 UUID/MAC 地址、时区、网络设置、企业管理策略、浏览器或钥匙串。普通 Desktop 重置也不改 `~/.claude` 和 `~/.claude.json`。

完成后先做网络与路由检查，再让用户自行重新打开官方 Claude Desktop 并登录。新 ID 是否生成、登录是否成功，属于之后的另一次验证；不能根据脚本成功推断“防封成功”。

## 可选：Claude Code 本地身份

仅当用户明确要求同时处理 Claude Code，先阅读当前平台的 reference，然后追加该选项：

```sh
python3 "$SKILL_DIR/scripts/claude_local_reset.py" --code-identity
python3 "$SKILL_DIR/scripts/claude_local_reset.py" --code-identity --apply
```

该选项同时执行 Desktop 重置；它不是单独重置 CLI 的命令。它备份 `~/.claude.json` 原件，仅轮换已存在且符合已知格式的 `userID` / `machineID`，移除 `anonymousId` 与 `oauthAccount` 本地缓存，并归档已存在的配置滚动备份、主目录下的 `~/.claude.json.backup` 旧身份快照、`statsig`、`telemetry` 及文件凭据回退。其余 JSON 字段、skills、hooks、插件、设置和 CLI 历史保留。

这是版本相关的社区方法。若字段格式变化、JSON 损坏、存在自定义 `CLAUDE_CONFIG_DIR` 或当前身份字段缺失，先停止核实，不为“成功”补造缺失字段。不改变遥测开关。

macOS 钥匙串中的旧 CLI 凭据不会被这个选项清除。Windows 的 CLI 凭据文件会随该选项归档，但这仍不是官方注销。使用官方 `/logout` 另行处理；详细说明见平台 reference。不要声称 CLI 已彻底退出旧账号。

## 可选：浏览器与钥匙串

这些不由脚本自动操作。macOS 阅读 [references/macos-details.md](references/macos-details.md)，Windows 阅读 [references/windows-details.md](references/windows-details.md)。仅处理明确选定的 Claude 站点数据或应用凭据，不清空整个浏览器、钥匙串或 Windows 凭据管理器。特别不要把 macOS 的 `Claude Safe Storage` 加密密钥直接当作黑名单标记删除，这会影响归档资料的解密回滚。

## 网络与路由检查

执行这一阶段时阅读 [references/network-check.md](references/network-check.md)，形成出口 IP、实际浏览器 WebRTC/DNS、系统代理、终端与中转、时区、可选 IPv6 的结果。默认检查，不修复。对照社区手册时阅读 [references/guide-audit.md](references/guide-audit.md)，不要把社区经验当作封号机制。

先用随附的只读脱敏脚本检查系统代理、导出的环境变量、该平台的 shell 启动文件、系统 hosts 里的 anthropic/claude 域名映射、`~/.curlrc`/`~/.wgetrc`、npm/Git 代理及 Claude Code 全局设置（含 `settings.local.json`）。macOS 用 `scutil` 与 shell 启动文件；Windows 只读 WinINet 开关，并检查 PowerShell 配置与 Git Bash 启动文件。它不执行 shell 文件、不打印 token 或代理密码、不修改配置；hosts 命中只代表静态文本存在映射，不证明当前生效。Windows 时区记录的是 Windows 时区 ID，不是 IANA 名称。

```sh
python3 "$SKILL_DIR/scripts/claude_network_check.py"
```

用户要求出口 IP/联网检查时，可一次性对固定 IP 查询服务发起 HTTPS 请求。当前查到的 IP 是检测站看到的**终端请求出口**，不能推断为浏览器或 Claude Desktop 的出口：

```sh
python3 "$SKILL_DIR/scripts/claude_network_check.py" --online
```

如已明确使用 TUN、系统代理或直连，可追加 `--expected-mode tun`、`--expected-mode system-proxy` 或 `--expected-mode direct`。这是判读依据，不会切换路由模式。

浏览器检测由 AI 主动执行，具体记录格式和判定见 [references/browser-and-report.md](references/browser-and-report.md)。使用用户实际登录 Claude 的本地浏览器及 profile，依次打开 IPLeak、BrowserLeaks DNS、Net.Coffee Claude 和 BrowserLeaks WebRTC，等待测试完成、读取结果并交叉核实。网络检查的授权涵盖这些只读页面访问；不要自动更换节点、修改浏览器或登录账号。

用户指定的附加质检必须保留：IPLeak 和 BrowserLeaks DNS 的测试结果不出现 CN/中国或 HK/香港标签，出口与已知预期国家对应；Net.Coffee 的 DNS 与 WebRTC UDP 两项都需实际完成且未报告泄漏。将地区规则标为用户标准；第三方报泄漏或出现禁用地区时质检“未通过”，不自动断言 Anthropic 的风控原因。

网页搜索工具、远端浏览器、终端查询和检测页初始 HTML 不能代替本地浏览器测试。未完成、空白、禁用 WebRTC、无法确定 profile 的项目标为“未检测／待核实”，提供检测入口，不写“全部通过”。

系统代理值为 `1` 只说明已开启；是否属于残留需要对照预期路由模式。IP 城市变动、机房归属、国内 DNS 或“纯净度分数”是排查线索，不能单独判定封号原因。不要因为 IP 变动而自动更换节点。

任何修复只针对已确认的问题和用户选定范围：备份后结构化改动具体配置，保留其他设置；不整文件删除、不自动安装扩展、不默认关闭 IPv6。详见 reference 的修复与恢复说明。底层“已观察”不等于质检“通过”，不能将 IP 稳定性从单次检测判成通过。

## 自动交付 HTML 回执

这一步是 skill 的完成条件，不只回复一段文字。阅读 [references/browser-and-report.md](references/browser-and-report.md)，把本次脱敏网络 JSON、浏览器实测结果和操作摘要交给生成器：

```sh
python3 "$SKILL_DIR/scripts/claude_check_report.py" \
  --network-json "$RUN_DIR/network.json" \
  --browser-json "$RUN_DIR/browser.json" \
  --run-json "$RUN_DIR/run.json" \
  --output-dir "$RUN_DIR/delivery" --open
```

`RUN_DIR` 使用当前项目下新建的私有批次目录；先建立目录约定，以 `0700` 建目录，`0600` 保存输入。每次新建，不覆盖前次交付。用户没有指定项目时才使用 `~/ClaudeCheckReports/<timestamp-random>/`。实际预期出口已知时追加 `--expected-country JP` 等 ISO 国家码；明确约定时区时追加 `--expected-timezone Asia/Taipei`，不为通过质检自动改时区。

没有取得的输入可以省略，仍生成缺项回执；重置部分失败时必须在 `run.json` 标明 `partial` 或 `failed`，不得写 `completed`。生成器不运行环境检查，不发网络请求，只依据输入判断；它输出 `report.html`、`guide.html` 与脱敏 `report.json`，然后 `--open` 用当前系统的默认浏览器打开回执（macOS 用 `open`，Windows 用 `start`）。若有允许的本地文件预览工具，也可直接打开同一文件。打不开时给出可点击路径并说明，不声称已经打开。Windows 上目录权限不能当成 Unix 的 `0700` 隔离。当前工具明确拒绝本地文件访问时，保留回执交付链接，不换浏览器、启动本地服务、使用 shell 或其他通道绕过该安全策略。

页面保持简洁：首屏可见的“Claude 防封号指南”入口 → 本次结论和状态计数 → 最多三条优先下一步 → 三个主要检测网站的结果与跳转 → 质检清单 → 折叠的补充资料。每项区分“通过／未通过／待核实／未检测”，展示依据与下一步；不要放原始配置、token、账号邮箱或完整 IP，不嵌入外部网站、字体、跟踪器，不在打开报告时重新检测。

独立指南内容在 [assets/guide-template.html](assets/guide-template.html)，由生成器输出到同一批次的 `guide.html`，通过固定相对链接往返 `report.html`；交付时保留两个页面所在目录，不能只复制其中一页。指南包含首次使用与曾被限制的两条路径（含“降智/限额/故障/封禁”区分表与退款路径）、与 AI 配合的手动准备、环境准备（时区、出口、代理客户端与 TUN、登录前 5 项自检、设备纪律）、账号与支付（邮箱手机号、订阅节奏、付款渠道）、AI/用户分工、具体质检标准、可复制的“只检查”和“修复后复测”提示词、日常注意事项（官方客户端、内容红线、遥测开关）、出发前清单与“少信的说法”。手动准备不能改变回执状态，实际复测后生成新回执才更新结果。

指南的“防封号”指减少配置问题与识别异常，不保证免封。执行前按 [官方地区要求](https://www.anthropic.com/supported-countries)核对实际所在地等条件，不能用出口旗帜替代使用资格；账号受限走原账号官方申诉。指南区分“官方”与“社区经验”两类标注：官方事实对照当前官方资料更新并记录资料核对日期；社区经验步骤（时区改台北、出口 ASN 选择、TUN 设置、订阅节奏、App Store 内购优先等）逐项标注来源属性，不写成官方规则、封号阈值或效果保证，不加入推广或返利链接与具体商家档位；更新社区步骤时对照 [references/guide-audit.md](references/guide-audit.md) 的采用与边界记录。

注意事项包括：检测是在什么浏览器/profile 里完成、未测项目先补齐、同一 profile 里自行登录官方客户端、保存备份及回滚入口。网络报告不验证账号可用性，也不保证不会封号。不要代用户输入密码、提交申诉、付款或终止其他会话。

制作或更新 skill 时用 `--demo` 生成明确标注模拟数据的双页预览，在当前工具允许时打开，不能借此运行真实环境检查。Python 不可用时，由文件工具按两个模板生成回执与指南，缺项继续标未检测，不擅自安装依赖。

## 回滚

先退出所有相关 Claude 会话。用实际备份批次替换路径，先预览再执行：

```sh
python3 "$SKILL_DIR/scripts/claude_local_reset.py" --restore "/absolute/path/to/ClaudeLocalResetBackups/<timestamp>"
python3 "$SKILL_DIR/scripts/claude_local_reset.py" --restore "/absolute/path/to/ClaudeLocalResetBackups/<timestamp>" --apply
```

脚本把当前新状态保存在该批次的 `current-before-restore/`，再移回原件；不会直接覆盖或丢弃当前数据。回滚会把旧本地身份和登录资料一起带回，不要同时宣称还维持了新身份。一次批次只能执行一次完整回滚；部分失败时按清单定位原件，不反复盲跑。

需要重新使用 MCP 时，优先人工核对后仅恢复旧的 `claude_desktop_config.json`。不要为了恢复几个设置，把旧 profile、cookies、`ant-did`、设备注册表或完整 `.claude.json` 直接复制回新环境。桌面本地会话与扩展的跨账号迁移没有在本 skill 中验证。

## 交付与验证

用简短结果说明：实际处理了哪些路径、哪些没有处理、备份位置、是否部分完成，以及后续是否需要用户自行登录。备份可能含登录凭据和对话，保存在本机私有目录，不上传、不打包进 skill，也不自动删除。

制作或修改此 skill 时只运行模拟夹具测试：

```sh
python3 "$SKILL_DIR/scripts/test_claude_local_reset.py"
python3 "$SKILL_DIR/scripts/test_claude_network_check.py"
python3 "$SKILL_DIR/scripts/test_claude_check_report.py"
```

单元测试不代表真实 Claude 登录或服务器设备关联已经验证。误封申诉入口见 [Anthropic 官方说明](https://support.claude.com/en/articles/8241253-safeguards-warnings-and-appeals)；清理本地状态不能撤销账号封禁。
