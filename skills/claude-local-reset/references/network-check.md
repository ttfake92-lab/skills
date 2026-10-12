# 重置后的网络与路由检查

核查日期：2026-10-11。按用户提供的五项流程补充，检查与修复分开；本文件的命令不在制作 skill 时执行。结果用于诊断路由和隐私，不预测账号封禁。

## 运行方式与结果格式

自动部分使用 `scripts/claude_network_check.py`，Python 3.10+、标准库，无需安装新依赖。不带参数时只查询本地配置；`--online` 才用 curl 对 `https://ipinfo.io/json` 各进行一次 IPv4/IPv6 尝试。没有修复参数、不访问 Claude 账号、不自动保存检查报告。

脚本按当前系统选择检查面。macOS 检查用户主目录的已知启动文件（含 `.zlogin`、`.bash_login`）、系统启动文件（`/etc/zshrc`、`/etc/zprofile`、`/etc/profile`、`/etc/bashrc`）、`/etc/hosts` 与 `scutil --proxy`。Windows 检查 PowerShell 配置、Git Bash 启动文件、`%SystemRoot%\System32\drivers\etc\hosts`，以及当前用户 WinINet 的代理开关；不读取代理服务器字符串。两边都检查 `~/.curlrc` 与 `~/.wgetrc`、默认 Claude 全局设置（`settings.json` 与 `settings.local.json`）、npm 用户上下文和 Git 全局配置，并只读记录时区、`TZ` 覆盖和明确配置的隐私开关。Windows 的系统时区是 `tzutil` 的 Windows ID，IANA 名称只来自 Node。没有覆盖所有 shell（如 fish 的 `config.fish`）、项目配置、编辑器、托管策略或自定义 profile。项目内 npm/Claude 设置可能覆盖全局结果，有相关线索时按实际项目另行核实，不递归搜索所有项目。

检查表逐项记录观察结果；最终 HTML 使用“通过／未通过／待核实／未检测”，底层“已观察”不等于通过。浏览器项由实际浏览器测试补齐，不根据脚本的 JSON 占位条目写“通过”。新增 IPLeak、CN/HK 地区条件及 Net.Coffee 双项验收见 [browser-and-report.md](browser-and-report.md)，完成后必须生成并打开回执。稳定性需要不同时段、同样路由条件下的记录；单次检测只描述当前出口。

## ① 出口 IP

在实际使用的浏览器打开 [IPinfo](https://ipinfo.io/)，可用 [ping0.cc](https://ping0.cc/) 或 [Whoer](https://whoer.net/) 交叉核实。检测站会看到该次访问的公网出口，浏览器和终端结果要分别记录。

终端的简单查询用 HTTPS、明确 JSON 和超时：

```sh
curl -q -fsS --connect-timeout 5 --max-time 15 https://ipinfo.io/json
```

辅助脚本已对返回结果做字段筛选；不需要复制整份响应。观察 `ip`、`country`/`country_code`、`city`、`org`/ASN。供应商返回结构可能变化或缺少城市，记“未提供”，不要补猜。

- 将国家与用户预期的出口相对照。城市定位可能受数据库误差、移动网络或 Anycast 影响；城市改变是线索，不单独等同节点漂移。
- ASN/`org` 可提示运营商或云服务商归属，但公司名不能证明该地址的专属用途、住宅属性或 Anthropic 对其信誉的判断。
- [IPPure](https://ippure.com/) 和 [Net.Coffee Claude 检测页](https://ip.net.coffee/claude/) 的纯净度、风险、支持地区等显示只作第三方参考，不视为 Anthropic 官方风控分数。不输入账号、密钥或 cookie。
- mihomo 规则可能对 IPinfo、Claude、浏览器与 CLI 分流不同。IPinfo 的出口不一定就是 Claude 的出口；需要按实际代理客户端连接记录核对 Claude 目标域名是否走预期路线，勿输出带认证信息的完整日志。

脚本的 curl 查询保留当前进程的代理环境变量，不强制直连；`-q` 忽略 `.curlrc`，避免其中的输出文件或其他指令产生额外行为。因此该结果不能覆盖只在 `.curlrc` 配置的代理。`-4` / `-6` 是连接地址族要求，使用代理时可能约束的是代理连接；以返回 IP 的实际地址族为准。IPv6 请求失败只表示该次查询没有取得结果，不证明 IPv6 已关闭或无泄漏。

## ② WebRTC

在实际使用的浏览器与 profile 打开 [BrowserLeaks WebRTC](https://browserleaks.com/webrtc)，等待 JavaScript 检测完成，记录页面的 Remote IP 与 WebRTC Public IP。

若出现已知的国内真实公网 IP，或出现与预期隧道出口不一致的公网候选，列为需核实／需处理。局域网私有地址和 `.local` 候选不是国内公网出口的直接证据。关闭了 WebRTC、页面无法运行、脚本被拦截或结果为空时，写明具体状态，不直接判定“网络安全”。

TUN 可能覆盖更多流量，但是否覆盖 UDP、IPv6 和浏览器实际连接必须实测；不能只凭开关状态承诺无泄漏。

确认需要修复且用户要求该范围后：

- Chrome：先核实当前浏览器、代理和扩展可用性。[IPLeak](https://ipleak.net/) 已提醒旧 [Google WebRTC Network Limiter](https://chromewebstore.google.com/detail/webrtc-network-limiter/npeicpdbkakmehahjeeohfdhnlpdklia) 的时效性；不把旧教程当作当前安装保证，不默认安装。若当前可用工具明确支持，可按 [Chrome privacy API](https://developer.chrome.com/docs/extensions/reference/api/privacy) 核对限制非代理 UDP 的策略，保存原设置并复测；可能影响视频通话。旧选项 `Use my proxy server (if present)` 仅作为历史参考。
- Firefox：在 `about:config` 将 `media.peerconnection.enabled` 设为 `false` 可以禁用 RTCPeerConnection。记录原值，改后复测；依赖 WebRTC 的通话／数据连接可能不可用，恢复时还原原值（默认通常为 `true`）。不改相似的摄像头权限绕过设置。

脚本不安装扩展、不修改浏览器偏好。

## ③ DNS

在同一实际浏览器打开 [BrowserLeaks DNS](https://browserleaks.com/dns)，等待测试完成。记录解析器 IP、运营商及页面地理标签，并与期望 DNS 路径对照。

如果目标是让 Claude 相关解析经过选定网络，而结果仍显示本地 ISP 或未预期的国内解析器，先列为需核实：可能涉及分流、浏览器安全 DNS、系统局域网 DNS 或 VPN DNS 策略。解析器的国家标签本身不能证明泄漏；公共 DNS 的实际服务位置和地理数据库也可能不同。

使用 Clash/mihomo 时核对当前实际生效的 `dns.enable`、`tun.enable`、`tun.dns-hijack` 以及 DNS 出站规则。不同客户端 UI 和配置版本有差别，不直接覆盖现有配置。mihomo 文档明确：macOS/Windows 无法自动劫持发往局域网的 DNS 请求，因此“开 TUN 就一定接管所有 DNS”不成立。`dns.ipv6: false` 是 AAAA 解析行为设置，不等于关闭系统 IPv6。

没有实际浏览器结果时只报告未检测，不用系统 DNS 配置或终端解析替代该项。

## ④ 系统代理

macOS 使用下面的只读命令。Windows 不要运行 `scutil`；脚本改读 WinINet 的 `ProxyEnable`、自动配置地址是否存在，以及读得到的 `AutoDetect`。缺自动检测项时保持待核实。

### macOS

可使用用户给出的只读命令；增加 PAC 和自动发现项，避免遗漏：

```sh
scutil --proxy | rg 'HTTPEnable|HTTPSEnable|SOCKSEnable|ProxyAutoConfigEnable|ProxyAutoDiscoveryEnable'
```

没安装 `rg` 时可换成 `grep -E`。脚本直接解析 `scutil` 输出，只展示这些开关，不输出认证内容。

- 预期仅用 TUN 且已决定关闭系统代理时，仍为 `1` 的项可能是残留；需要对照客户端设置。
- 预期使用系统代理时，`1` 可能是正常配置；全部设为 `0` 反而可能让应用失去预期路由。
- `0` 不证明直连：环境代理、浏览器扩展、VPN、TUN 或应用自己的配置仍可能生效。字段未返回也不自动写成 `0`。

确认修复时先识别实际网络服务和相关客户端，保存开关原值，通过该客户端或系统设置调整对应服务。不能在检查阶段自动全关。

## ⑤ 终端代理与中转残留

使用脱敏脚本代替直接输出 `env`、shell 全行和 `cat ~/.claude/settings.json`，因为那些命令可能把 token 或代理密码一起打印出来。

重点看：

1. 当前进程中的 `HTTP_PROXY`/`HTTPS_PROXY`/`ALL_PROXY`/`NO_PROXY`（含小写形式）、`ANTHROPIC*` 与 `CLAUDE*` 名称。
2. `~/.zshrc`、`~/.zshenv`、`~/.zprofile`、`~/.zlogin`、`~/.bashrc`、`~/.bash_profile`、`~/.bash_login`、`~/.profile` 与系统级 `/etc/zshrc`、`/etc/zprofile`、`/etc/profile`、`/etc/bashrc` 的相关候选赋值；脚本只读文本，不 `source`、不执行命令替换，也不递归执行它们引用的文件。系统文件条目单独标注“系统启动文件候选”。
3. npm 的 `proxy`、`https-proxy`；Git 全局 `http.proxy`、URL 定向的 `http.<url>.proxy`，并检查可能遗留的 `https.proxy` 键。Git 文档支持的是 `http.proxy`；某个键存在不代表当前 HTTP 请求使用它。
4. 默认 `~/.claude/settings.json` 与 `~/.claude/settings.local.json` 的相关 `env` 字段；自定义 `CLAUDE_CONFIG_DIR`、项目 settings 和托管设置需要另行核对。
5. `/etc/hosts` 中的 anthropic/claude 域名映射：镜像站与中转工具的安装脚本常在这里添加 `api.anthropic.com`、`claude.ai` 等行。脚本只做静态文本匹配并隐藏映射地址；命中不代表当前生效（可能被代理接管或 DNS 缓存覆盖），清理该行需要管理员权限，动手前先备份原行。`~/.curlrc`、`~/.wgetrc` 的 `proxy` 行只影响 curl/wget 自身，不影响 Claude，但属于残留线索，确认无其他工具依赖后再处理。

`ANTHROPIC_BASE_URL` 可能改变 API 目标。发现自定义主机时报告“已配置自定义入口，确认是否仍需要”，不要未经判断就删。官方支持的 Bedrock、Vertex、Foundry 或组织网关也不是天然异常；不能声称服务器只凭客户端环境变量就一定知道用了中转。

若确认某条是用户已停用的镜像站、Claude Code Router 或中转配置，并且用户要求修复：

- 先备份具体启动文件／JSON／代理设置到本机私有位置，再只改对应赋值或 JSON 键；不要删除整份文件、其他密钥、模型、hooks 或企业配置。
- 同时处理已导出的旧环境与持久化来源。例如确认过期的 `ANTHROPIC_BASE_URL` 后，只在实际终端会话中 `unset ANTHROPIC_BASE_URL`，并移除其实际定义；不要批量 `unset ANTHROPIC*`。
- npm/Git 只删除已确认的对应层级与具体键，不把包管理器或 Git 的代理误当成 Claude 账号状态。保留变更前值用于恢复。
- 新开实际终端，并按需要重启相关 Claude 进程，再重新运行检查。修改某个代理环境变量并不改变已经运行的其他终端或 Desktop 的环境；脚本启动 shell 文件中出现某行也不证明当前值来自那里。

## 可选：IPv6

先核实 IPv6 实际出口和代理是否覆盖。支持 IPv6 的正常网络无需默认关闭。仅在确认其绕过预期隧道、无法通过现有代理修复，且用户选择关闭该服务的 IPv6 时操作。改动可能影响依赖 IPv6 的联网。

先识别实际服务名称并记录原模式、地址、前缀和路由器；服务不一定叫 `Wi-Fi` 或 `Ethernet`：

```sh
networksetup -listallnetworkservices
NETWORK_SERVICE="Wi-Fi"
networksetup -getinfo "$NETWORK_SERVICE"
```

经过实际服务选择与保存原设置后，才执行：

```sh
networksetup -setv6off "$NETWORK_SERVICE"
```

如需要管理员权限，密码仅在系统原生提示中输入，不发给执行者。恢复要按原模式：原来是自动时才使用下面的命令：

```sh
networksetup -setv6automatic "$NETWORK_SERVICE"
```

原来是 Link-local 或手动配置时，分别还原 `-setv6linklocal` 或已记录的手动地址／前缀／路由器配置。不能把 `automatic` 称为所有情况的原样恢复。修复后再运行出口与浏览器检查；失败或未测项继续保持未检测／待核实。

## 时区与隐私偏好

脚本通过固定只读命令查询 `/etc/localtime` 的时区链接和 Node 的 `Intl.DateTimeFormat().resolvedOptions().timeZone`，Node 不存在时这一项保留未检测；并记录当前 `TZ` 是否覆盖。[Node 官方文档](https://nodejs.org/api/cli.html#tz) 确认该变量可改变进程时区。固定 Node/npm 查询忽略 `NODE_OPTIONS`，避免加载用户额外启动脚本，原环境不被改动；这不代替实际 Claude 会话的进程时区。脚本不改系统日期、时区、定位或手机设置。只有用户明确指定预期时区时才比较；没有指定则作为上下文展示，不能因为是上海／台北／美西而直接推断封号。

`DISABLE_TELEMETRY`、`DISABLE_ERROR_REPORTING`、`CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` 只显示已配置的 `0/1` 值。未配置不等于不安全；实际默认与登录方式、版本和管理策略相关。[官方 Data usage](https://code.claude.com/docs/en/data-usage) 说明部分关闭开关会影响功能旗标与 Remote Control，改动属于用户隐私偏好，不能为质检自动设置。

## 资料依据与范围

- [IPinfo](https://ipinfo.io/)：地理与 ASN 信息来自查询服务；数据结构与套餐可能不同。
- [BrowserLeaks WebRTC](https://browserleaks.com/webrtc) 与 [DNS](https://browserleaks.com/dns)：两项需要实际浏览器运行其测试。网站抓取显示的 IP 属于抓取方，不是用户电脑。
- [Google 扩展说明](https://chromewebstore.google.com/detail/webrtc-network-limiter/npeicpdbkakmehahjeeohfdhnlpdklia) 与 [Chrome privacy API](https://developer.chrome.com/docs/extensions/reference/api/privacy)：支持限制非代理 UDP；扩展默认不自动启用这一限制，并可能影响实时通信。
- [Firefox 官方源码偏好定义](https://github.com/mozilla-firefox/firefox/blob/main/modules/libpref/init/StaticPrefList.yaml)：`media.peerconnection.enabled` 控制 RTCPeerConnection；版本更新后需核对当前行为。
- [mihomo TUN](https://wiki.metacubex.one/config/inbound/tun/) 与 [DNS](https://wiki.metacubex.one/config/dns/)：确认劫持条件、平台限制以及 IPv6 DNS 选项的含义。
- [Claude Code 环境变量](https://code.claude.com/docs/en/env-vars)：自定义 API 入口与官方支持的供应商路由存在合法用途。
- [npm 配置](https://docs.npmjs.com/cli/v11/using-npm/config/) 与 [Git 配置](https://git-scm.com/docs/git-config)：检查配置层级与代理键；脚本的 npm 查询关闭更新提示和该次日志写入。
- [curl 手册](https://curl.se/docs/manpage.html)：`-q` 第一参数禁用 curlrc，查询限定 HTTPS 和超时；不绕过证书检查。
- [Apple IPv6 设置](https://support.apple.com/en-euro/guide/mac-help/mh14129/27/mac/27) 及本机静态 `networksetup(8)` 手册：支持按实际网络服务选择和恢复 IPv6 模式。阅读手册未检查本机网络配置。

检查失败最多重试一次或换一个用户已列出的检测站，不反复轮换节点、不创建测试账号、不把第三方评分包装成官方结论。
