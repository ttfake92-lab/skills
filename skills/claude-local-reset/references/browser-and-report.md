# 本地浏览器检测与 HTML 交付

## 自动完成的一次流程

1. 先确定本次是检查、预览、重置还是回滚，记录实际完成情况。建立新私有批次目录；本地读取用随附脚本，生成脱敏 `network.json`。用户要求完整网络质检时使用 `--online`。
2. 从当前任务的浏览器信息确认用户实际使用 Claude 的本地浏览器与 profile。优先复用该 profile 中的标签页或新建同 profile 的标签，不为检测另开无扩展、无原代理的新 profile。信息不足时先完成本地检查；浏览器项保持未检测，并请求必要的浏览器信息。
3. AI 使用可用的本地浏览器工具打开下面四个检测页。读取工具文档后按其 API 操作；等待实际测试完成，读取页面可见的 IP、国家码/旗帜、DNS 与 WebRTC 状态。单页最多等待 60 秒，可重试一次；仍无结果就记录未检测。不要运行 torrent 磁力测试、不授予摄像头或麦克风权限。
4. 记录本次观察到的结构化结果，生成 `browser.json` 和 `run.json`。不存原始 HTML、全屏截图、账号信息或控制台敏感数据。报告工具按固定字段判定，生成回执、指南和脱敏 JSON，并在工具允许时自动打开回执。
5. 质检未通过时，先指出对应项目和下一步。修复须在用户授权的具体范围内，改完只复测受影响的项目。每次回执新建批次，不覆盖旧结论。

浏览器工具不存在或该浏览器无法控制时，HTML 仍要交付，待测项提供跳转入口。不能要求用户逐项复制可由 AI 读取的结果。浏览器信息不明确时也不能擅自把默认新窗口当作已确认 profile。

## 必测网站与标准

| 网站 | 读取字段 | 质检标准 |
| --- | --- | --- |
| [IPLeak](https://ipleak.net/) | 测试 IP 对应的国家码、公网 IP，必要时 DNS 标签 | 结果不出现 CN/HK；已知预期出口国家时核对一致。与出口无关的页脚旗帜不算测试结果 |
| [BrowserLeaks DNS](https://browserleaks.com/dns) | 实际完成的解析器国家码、解析器 IP | 不出现 CN/HK 标签；该项表示符合用户地区条件，不能单独证明 DNS 完全没有泄漏 |
| [Net.Coffee Claude](https://ip.net.coffee/claude/) | DNS 泄露、WebRTC UDP 泄露两个独立测试的状态与完成情况 | 两项都实际完成且明确未报告泄漏；一项通过不代替另一项 |
| [BrowserLeaks WebRTC](https://browserleaks.com/webrtc) | Remote IP、Public IP 与测试是否可用 | 对比预期出口和已知真实公网 IP；确认不匹配的公网候选才判泄漏，私有地址/mDNS 不当作国内公网 IP |

`country_codes` 使用 ISO 两字码；把旗帜转换为国家码，不凭 IP 段猜国家。缺少国家标签、只有“Loading/检测中”、仅显示主页面或已禁用 WebRTC 时，不判通过。多站结果矛盾则保留各站结果并待核实，不能挑一个绿色结果覆盖其他失败。

这些是用户标准和检测站的报告；IP 数据库可能有误，公共 DNS 也可能跨地区服务。出现 CN/HK 在本次质检中仍记未通过，但下一步是核对实际路径，不直接认定账号封禁原因或自动更换节点。

## 浏览器结果输入

生成器不控制浏览器，也不发请求。以下 JSON 是 AI 根据当次本地可见结果填写的记录；**不能照抄示例当作实测**。不要自填 `passed`，程序依据字段计算。时间使用带时区的 ISO 格式，单项结果与当次网络记录时间相距不得超过一小时；过期记录不自动通过。

```json
{
  "schema_version": 1,
  "context": {
    "type": "local-browser",
    "browser": "Chrome",
    "profile_confirmed": true
  },
  "sites": {
    "ipleak": {
      "checked_at_utc": "2026-10-11T02:00:00+00:00",
      "completed": true,
      "country_codes": ["JP"],
      "public_ips": ["203.0.113.10"]
    },
    "browserleaks_dns": {
      "checked_at_utc": "2026-10-11T02:01:00+00:00",
      "completed": true,
      "country_codes": ["JP"],
      "resolver_ips": ["203.0.113.20"]
    },
    "netcoffee": {
      "checked_at_utc": "2026-10-11T02:02:00+00:00",
      "dns": {"completed": true, "state": "clear"},
      "webrtc": {"completed": false, "state": "unknown"}
    },
    "browserleaks_webrtc": {
      "checked_at_utc": "2026-10-11T02:03:00+00:00",
      "completed": true,
      "state": "clear",
      "public_ips": ["203.0.113.10"]
    }
  }
}
```

`state` 取 `clear`、`leak`、`unknown`、`disabled`。`clear` 只用于明确完成的测试且 AI 已根据可见内容核实；`leak` 是站点明确报告或已确认的出口不匹配；空白或禁用不写 `clear`。网页反馈对应字段不确定时使用 `unknown`，不靠颜色猜测。`completed` 只用布尔值。

示例 IP 是文档地址，仅用于演示。实际采集需要有效公网地址；生成器排除私有、回环等地址作为公网证据，展示时会遮住完整 IP。WebRTC 私有候选可用于诊断但不写进 `public_ips`。

## 操作摘要输入

```json
{
  "action": "reset",
  "status": "completed",
  "backup_path": "/Users/example/ClaudeLocalResetBackups/example-batch"
}
```

`action` 取 `check`、`preview`、`reset`、`restore`；`status` 取 `completed`、`partial`、`failed`、`not_run`。只检查时用 `check`，没有执行重置不能写重置成功；操作进行到一半时用 `partial`。摘要不包含 ID、邮箱、授权链接、凭据或原始 manifest。

## 页面生成和自动打开

先把输入以 `0600` 保存到当前项目新建的 `0700` 批次目录，再执行入口里的生成命令。三个输入参数均可省略，缺项会显示未检测；`--output-dir` 的父目录需已存在，生成器以 `0700` 新建交付目录，不覆盖前次结果。`--open` 在允许的 macOS 环境使用默认浏览器打开本地 HTML；生成失败与打开失败分开报告，打开失败时文件仍保留。若当前浏览器/工具的安全策略明确禁止本地文件访问，停止自动打开，给出文件链接让用户查看；不能用本地服务、其他浏览器或 shell 绕过该限制。

交付目录包含 `report.html`、`guide.html`、`report.json`。回执首屏放清晰可见的“Claude 防封号指南”入口；指南与回执用固定相对链接互相跳转，移动或分享文件时保留整个目录。CLI 输出 `html`、`guide`、`json` 的绝对路径及 `open_status`，打开失败不影响已生成文件。

回执保持简洁：指南入口、结果总览、最多三条优先步骤、三个主要网站的结果和按钮、可扫描的质检清单、折叠的补充入口和注意事项。补充入口保留 IPinfo、ping0、Whoer、IPPure、BrowserLeaks WebRTC，未测网站显示未检测。退出码 `0` 只表示生成成功；四种质检状态要看清单。

指南采用 [assets/guide-template.html](../assets/guide-template.html)：先按首次使用/曾被限制分流，再给共同手动步骤、可复制的质检提示词、标准表和复测提示词。首次用户不默认重置；曾被限制用户先识别用量/故障/封禁并走原账号申诉。打开指南本身不触发审计、登录或清理，阅读与完成手动步骤不能把原回执的未检测改成通过。用户只要指南时可以无输入生成缺项回执，不能顺带扫描本机。

- 时区只记录真实值；用户指定预期时区时才比较，不默认要求台北，不因 IP 国家推断用户应该改时区。
- 无中转候选仅表示已覆盖文件内未发现，项目、编辑器与管理策略仍可能不同。凭据存在不算失败，合法网关也不自动失败。
- 保存备份；后续自行在已确认 profile 中登录官方客户端。不要整份复制旧 profile 回去；需要 MCP 时按原回滚说明只选配置。
- 账号会话、用量、隐私及申诉入口放在补充说明中，由用户按需要自行访问。本 skill 没有验证账号能登录或服务器关联已解除。
- HTML 不含外部脚本、字体、iframe 或自动探测请求；按钮由用户点击才访问检测站。页面没有可以手动把红色改成绿色的勾选框。

制作时只运行演示：

```sh
python3 "$SKILL_DIR/scripts/claude_check_report.py" --demo --output-dir "/absolute/new-preview-directory" --open
```

演示模式不读取账号、网络、环境变量或真实配置，不运行检测命令；页面顶部明确显示“演示 · 模拟数据”。
