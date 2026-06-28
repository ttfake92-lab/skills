# 清理板块细则

记录每个板块扫描什么、清理什么、安全性。改扫描/清理逻辑前先更新本文件（先改文档、再改实践）。

## 1. 开发者缓存 dev_caches（默认勾选，安全）

| key | 标签 | 路径 / 命令 | 说明 |
|---|---|---|---|
| npm | npm 缓存 | `~/.npm/_cacache` | 直接删，npm 会重建 |
| yarn | Yarn 缓存 | `~/Library/Caches/Yarn`、`~/.cache/yarn` | 同上 |
| pnpm | pnpm store | `~/Library/pnpm/store` 等 | 全局内容寻址 store，删后重装依赖会重新下载 |
| pip | pip 缓存 | `~/Library/Caches/pip` | 直接删 |
| homebrew | Homebrew 缓存 | `brew cleanup -s` + `~/Library/Caches/Homebrew` | 优先用 brew 命令清旧版本下载 |
| xcode_dd | Xcode DerivedData | `~/Library/Developer/Xcode/DerivedData` | 编译中间产物，删后下次构建变慢一次 |
| xcode_dev_support | iOS DeviceSupport | `~/Library/Developer/Xcode/iOS DeviceSupport` | 旧 iOS 调试符号，常占数 GB |
| xcode_archives | Xcode Archives | `~/Library/Developer/Xcode/Archives` | **默认不勾**：含历史打包，可能要留存 |
| coresim | 模拟器缓存 | `~/Library/Developer/CoreSimulator/Caches` | 直接删 |
| gobuild | Go build 缓存 | `~/Library/Caches/go-build` | 直接删 |
| gradle | Gradle 缓存 | `~/.gradle/caches` | 直接删 |
| docker | Docker 悬空镜像/缓存 | `docker system prune -f` | **默认不勾**：会删未使用镜像/容器/构建缓存，先看 `docker system df` |

## 2. 系统与应用缓存 system_caches（默认勾选，安全）

- **应用缓存**：`~/Library/Caches` 下各子目录，逐个列出（>20MB 才显示），排除已在开发者板块出现的目录避免重复计算。
- **应用日志**：`~/Library/Logs`，只删内容、保留目录（`contents_only`）。
- **废纸篓**：`~/.Trash`，清空（`contents_only`）。
- 注意：某些 App 的「缓存」里可能混有可重下的资源（如聊天软件的图片缓存），删后 App 会重新下载，不丢账号数据。需要保留的让用户加进 `never_touch`。

## 3. 大文件与下载 large_files（永远默认不勾，需手动）

- `~/Downloads`：>100MB 或 90 天未动的文件（各取最多 60 个）。
- `~/Desktop`、`~/Movies`、`~/Documents`：>500MB 的文件。
- 这些是**用户文件**，永久删除不可逆，因此永远不自动勾选，必须用户在网页上亲手勾。

## 4. 性能优化 performance（真实测量 + 安全一键）

测量（只读）：
- **内存压力** `_mem_stats()`：`hw.memsize` + `vm.swapusage` + `vm_stat`。判断看 **swap 占用**（>3G→bad，>1G→warn），不看「空闲%」（macOS 用空闲内存做缓存，空闲低≠慢）。明确标注「清内存」无效不做。
- **资源大户** `_top_procs()`：`ps -Aro pcpu=,comm=`（CPU Top）+ `ps -Amo rss=,comm=`（内存 Top，>300MB）。只报告，关进程由用户来。
- 开机登录项：`osascript` 读 login items（只读 + 指路系统设置，不一键删，避免误删）。

安全一键（`execute_action`）：
- **后台自启**：`~/Library/LaunchAgents/*.plist` 每个一行，带 `action: disable_agent`。
- 禁用 = `launchctl unload -w` + `shutil.move` 到 `~/.disk-cleanup-cat/disabled-agents/`（**挪开不删，可还原**）。
- 还原 = `enable_agent`：移回 + `launchctl load -w`。
- 守卫：disable 只接受 `~/Library/LaunchAgents` 下的 `.plist`；enable 只接受 `disabled-agents/` 下的。**不碰系统级 daemon**（那些超出用户权限、需 sudo）。

## 5. 网络优化 network（真实测量 + 命令）

测量（只读，探测并发执行，~几秒）：
- **DNS 实测延迟** `_dig_ms()`：`dig +time=1 +tries=1 @server www.apple.com` 取 `Query time`。对比当前 DNS 与公共 DNS（阿里 223.5.5.5 / 腾讯 119.29.29.29 / Cloudflare 1.1.1.1 / Google 8.8.8.8），排名。只有当最快公共 DNS 比当前快 >5ms 才推荐切换，并给 `networksetup -setdnsservers` 命令（需管理员，用户手动跑）。
- **延迟/丢包** `_ping()`：`ping -c 3` 路由器（`route -n get default`）+ 外网，取 avg 延迟与丢包率。
- 当前 Wi-Fi：`networksetup -getairportnetwork en0`。
- 维护命令（需 sudo，手动）：刷新 DNS 缓存。

**不做的（theater）**：清内存/RAM 加速、一键加速、提升带宽——改不了物理链路/ISP 套餐，或在 macOS 上无效。

## 安全守卫 `_is_safe_to_delete()`

拒绝删除的情形：路径不存在 / 命中 `_FORBIDDEN`（`/`、各系统目录、家目录及其一级关键子目录）/ 超出 `$HOME` / 路径层级 <2 / 命中 `never_touch`。任何新增删除目标都必须能通过此守卫。
