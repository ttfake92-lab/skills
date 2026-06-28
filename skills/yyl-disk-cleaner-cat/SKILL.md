---
name: yyl-disk-cleaner-cat
description: 像素小猫帮你清理 macOS 磁盘、优化空间与性能。扫描开发者缓存 / 系统缓存 / 大文件下载，给出性能与网络优化建议，然后打开一个「像素风网页」让你勾选确认——确认后一只 3D 像素小猫在房间里实时打扫，灰尘堆随真实删除进度缩小。带持续记忆：每次清理了什么、你的偏好都记在 ~/.disk-cleanup-cat/，下次更懂你。当用户说「清理磁盘 / 清理空间 / 磁盘满了 / C盘满了 / 优化电脑 / 优化性能 / 电脑变慢了 / 清缓存 / disk cleanup / free up space」时使用。仅限 macOS。
---

# 磁盘清理小猫 🐱

一句话：**扫描 → 打开像素网页让你确认 → 小猫实时打扫 → 把这次清理写进记忆。**

三层结构：
- **大脑（你，Claude）**：读记忆、按偏好讲解、收尾总结、更新偏好。
- **引擎 + 桥梁（`src/server.py`）**：扫描磁盘、起本地服务、执行永久删除、把进度实时推给网页、写记忆。
- **界面（`web/` 像素页）**：展示可清理项（学到的安全类别已预勾选）+ 永久删除确认 + 会打扫的像素小猫。

> 为什么要本地服务而不是单个 HTML：静态网页无法把「用户点了确认」告诉后端，也收不到真实删除进度。`server.py` 是让「确认 → 真删 → 小猫同步打扫」成立的桥梁。

## 运行流程（你要做的）

设 `$SKILL_DIR` = 本 SKILL.md 所在文件夹。

### 1. 先读记忆，回忆偏好
```bash
cat ~/.disk-cleanup-cat/MEMORY.md 2>/dev/null || echo "（首次使用，还没有记忆）"
```
读到偏好后，用一句话跟用户打招呼，比如「上次释放了 X，缓存类你一向直接清，这次我先帮你预勾好」。

### 2. 启动小猫（会扫描 → 自动开浏览器）
**在后台运行**，这样你能继续对话、并在结束后读取结果：
```bash
python3 "$SKILL_DIR/src/server.py"
```
- 启动后会先扫描磁盘（约 10–20 秒，终端打印进度），**扫完自动用浏览器打开像素页**。
- 告诉用户：「小猫正在巡视磁盘，扫完会自动弹出一个像素页面，你在上面勾选要清理的东西、点『开始打扫』就行。」
- 终端会实时打印每一项的释放情况；用户点页面右下角「关掉小猫」即退出服务。

### 3. 用户在网页上确认 + 打扫
这一步在网页里完成，你不用操作。页面会：
- 列出可清理项（缓存类已预勾选，大文件永远默认不勾、需用户亲自勾）；
- 醒目提示「永久删除，不进废纸篓」；
- 确认后小猫走到对应灰尘堆实时打扫，删完显示成果。

### 4. 收尾总结
服务结束后（或用户说扫完了），读最新记忆并总结：
```bash
tail -n 3 ~/.disk-cleanup-cat/history.jsonl 2>/dev/null; echo "---"; cat ~/.disk-cleanup-cat/MEMORY.md
```
用结论先行的方式汇报：这次释放了多少、清了哪些类别、磁盘现在多空。

### 5.（可选）把对话里学到的偏好写进记忆
如果用户在对话里表达了偏好（例如「微信缓存别动」「Downloads 里的素材永远别碰」），写进 `preferences.json` 的 `never_touch` 或 `notes`，让下次更聪明：
```bash
python3 - <<'PY'
import json,sys; sys.path.insert(0,"$SKILL_DIR/src"); import engine
p=engine.load_prefs()
p.setdefault("never_touch",[]).append("/Users/你/某个永不清理的路径")   # 按需修改
p["notes"]=(p.get("notes","")+"\n用户说：微信缓存不要动").strip()
engine.save_prefs(p); engine.render_memory_md()
print("偏好已更新")
PY
```

## 安全红线（务必遵守）

- **永久删除，删什么必须用户在网页上确认**——这是设计约定，不要替用户跳过确认。
- 引擎只删两类：(1) 已知缓存白名单目录 (2) 用户亲手勾选的大文件。删除前过 `_is_safe_to_delete()`：绝不碰 `/`、家目录根、`~/Library`、`~/Documents` 等关键路径，绝不超出家目录，命中 `never_touch` 即跳过。
- **性能 / 网络是「真实测量 + 安全一键」板块**：
  - 测量只读（内存 swap、Top 进程、DNS 实测延迟、ping 延迟/丢包），不改任何东西。
  - **唯一的一键操作 = 禁用/还原「用户级」后台自启**（`~/Library/LaunchAgents/*.plist`）。禁用 = `launchctl unload` + 把 plist **挪到** `~/.disk-cleanup-cat/disabled-agents/`（不删除、随时一键还原）。每次都要用户在网页上点 + 确认。
  - 系统级 daemon、改 DNS、刷新缓存等需 `sudo` 的，**只给可复制命令**，由用户手动执行。
  - **Theater 坚决不做**：清内存/RAM 加速、一键加速、提升带宽——在 macOS 上无效甚至有害。
- 不要自己写 `rm` 或 `launchctl` 去操作——一切删除/禁用走 `server.py`（`/api/clean`、`/api/action`），它有白名单守卫和可还原设计。

## 清理板块一览

| 板块 | 内容 | 默认勾选 |
|---|---|---|
| 开发者缓存 | npm/yarn/pnpm、pip、Homebrew、Xcode DerivedData/DeviceSupport、模拟器、Go、Gradle、Docker | ✅（Docker、Archives 除外） |
| 系统与应用缓存 | `~/Library/Caches` 各应用、应用日志、废纸篓、`.DS_Store` | ✅ |
| 大文件与下载 | 超大文件、久未动的下载 | ⬜ 永远手动 |
| 性能优化 | 内存 swap 压力、CPU/内存 Top 进程、登录项、后台自启 | 测量只读；自启可**一键禁用/还原**（用户级、可还原） |
| 网络优化 | DNS 实测延迟+推荐、ping 延迟/丢包、Wi-Fi | 测量只读；改 DNS/刷新缓存给 `sudo` 命令 |

细节见 `references/categories.md`。

## 记忆与交接

全部存在 `~/.disk-cleanup-cat/`（独立于本 skill 文件夹，重装不丢）：
- `MEMORY.md` —— 给人/Claude 读的概览与交接（自动生成，可手动补「备注」）。
- `preferences.json` —— 代码用：自动勾选偏好、`never_touch`、`notes`、学习统计。
- `history.jsonl` —— 每次清理一行：时间、释放、类别、清了哪些项。

学习逻辑：某类别被批准 ≥2 次后，下次自动勾选；大文件永远保持手动。

## 自测 / 调试

```bash
python3 "$SKILL_DIR/src/engine.py"             # 只扫描打印 JSON，不删任何东西
CAT_NO_OPEN=1 CAT_PORT=8799 python3 "$SKILL_DIR/src/server.py"   # 起服务但不自动开浏览器
```
离线打开 `web/index.html`（无后端）会自动用演示数据渲染，可纯看小猫动画。
