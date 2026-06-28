#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
engine.py — 扫描 / 删除 / 记忆 的核心逻辑（macOS，纯标准库）

设计要点：
- 删除一律「永久删除」，但只删两类路径：(1) 已知的缓存白名单目录 (2) 用户在页面上亲自勾选的大文件。
- 任何删除前都过 _is_safe_to_delete() 守卫，绝不碰系统根、用户家目录根、never_touch 列表。
- 记忆存在 ~/.disk-cleanup-cat/：preferences.json(代码用) + history.jsonl(日志) + MEMORY.md(给人/Claude看)。
"""

import os
import re
import json
import time
import shutil
import subprocess
import concurrent.futures as cf
from pathlib import Path
from datetime import datetime, timedelta

HOME = Path.home()
MEM_DIR = HOME / ".disk-cleanup-cat"
PREFS_PATH = MEM_DIR / "preferences.json"
HISTORY_PATH = MEM_DIR / "history.jsonl"
MEMORY_MD = MEM_DIR / "MEMORY.md"

# ----------------------------------------------------------------------------
# 基础工具
# ----------------------------------------------------------------------------

def human_size(n):
    n = float(n or 0)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(n) < 1024.0:
            return f"{n:.1f}{unit}" if unit != "B" else f"{int(n)}{unit}"
        n /= 1024.0
    return f"{n:.1f}PB"


def _run(cmd, timeout=20):
    """跑命令，永不抛异常。返回 (rc, stdout, stderr)。"""
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, p.stdout, p.stderr
    except Exception as e:  # noqa
        return 1, "", str(e)


def _safe_future(fut, default=None):
    """取并发结果，出错/超时返回默认值（空列表），不让单个探测拖垮整次扫描。"""
    try:
        return fut.result(timeout=20)
    except Exception:  # noqa
        return default if default is not None else []


def dir_size(path):
    """目录/文件字节数。优先用 du -sk（快），失败回退到 Python 遍历。"""
    p = Path(path)
    if not p.exists():
        return 0
    rc, out, _ = _run(["du", "-skx", str(p)], timeout=40)
    if rc == 0 and out:
        try:
            return int(out.split()[0]) * 1024
        except Exception:  # noqa
            pass
    total = 0
    try:
        if p.is_file():
            return p.stat().st_size
        for root, _dirs, files in os.walk(p, onerror=lambda e: None):
            for f in files:
                try:
                    total += (Path(root) / f).stat(follow_symlinks=False).st_size
                except OSError:
                    pass
    except Exception:  # noqa
        pass
    return total


def subdirs_with_size(path, limit=40):
    """列出某目录下一级子项及大小，按大小降序。"""
    p = Path(path)
    items = []
    if not p.exists():
        return items
    try:
        for child in p.iterdir():
            try:
                if child.name.startswith("."):
                    # 仍统计，但保留点目录（缓存里也有点目录）
                    pass
                sz = dir_size(child)
                if sz > 0:
                    items.append((child, sz))
            except OSError:
                pass
    except OSError:
        return items
    items.sort(key=lambda x: x[1], reverse=True)
    return items[:limit]


# ----------------------------------------------------------------------------
# 安全守卫
# ----------------------------------------------------------------------------

# 绝不允许删除的路径（即便误入白名单）
_FORBIDDEN = {
    Path("/"), HOME, Path("/System"), Path("/Library"), Path("/Applications"),
    Path("/usr"), Path("/bin"), Path("/etc"), Path("/var"),
    HOME / "Documents", HOME / "Desktop", HOME / "Pictures", HOME / "Music",
    HOME / "Movies", HOME / "Library", HOME / "Downloads",
}


def _is_safe_to_delete(path, never_touch):
    p = Path(path).expanduser()
    try:
        p_res = p.resolve()
    except Exception:  # noqa
        return False, "无法解析路径"
    if not p.exists():
        return False, "路径不存在"
    if p_res in _FORBIDDEN or p in _FORBIDDEN:
        return False, "受保护的系统/家目录关键路径"
    # 必须在 HOME 之内（大文件删除也只允许家目录内）
    try:
        p_res.relative_to(HOME.resolve())
    except ValueError:
        return False, "超出家目录范围"
    # 路径深度太浅（如 ~/Library）不允许整删
    if len(p_res.relative_to(HOME.resolve()).parts) < 2:
        return False, "路径层级过浅，拒绝整目录删除"
    for nt in (never_touch or []):
        try:
            ntp = Path(nt).expanduser().resolve()
            if p_res == ntp or str(p_res).startswith(str(ntp) + os.sep):
                return False, "命中 never_touch 偏好"
        except Exception:  # noqa
            pass
    return True, "ok"


def _which(name):
    return shutil.which(name) is not None


# ----------------------------------------------------------------------------
# 各板块扫描
# ----------------------------------------------------------------------------

# 已知开发者缓存目录（路径 -> 标签）。会被 system_caches 排除以免重复计算。
def _dev_cache_targets():
    t = []
    def add(key, label, paths, cmd=None, auto=True):
        existing = [Path(p).expanduser() for p in paths if Path(p).expanduser().exists()]
        if existing:
            t.append({"key": key, "label": label, "paths": existing, "clean_cmd": cmd, "auto": auto})
    add("npm", "npm 缓存", ["~/.npm/_cacache"])
    add("yarn", "Yarn 缓存", ["~/Library/Caches/Yarn", "~/.cache/yarn"])
    add("pnpm", "pnpm store", ["~/Library/pnpm/store", "~/.pnpm-store", "~/.local/share/pnpm/store"])
    add("pip", "pip 缓存", ["~/Library/Caches/pip"])
    add("homebrew", "Homebrew 缓存", ["~/Library/Caches/Homebrew"],
        cmd=["brew", "cleanup", "-s"] if _which("brew") else None)
    add("xcode_dd", "Xcode DerivedData", ["~/Library/Developer/Xcode/DerivedData"])
    add("xcode_dev_support", "Xcode iOS DeviceSupport", ["~/Library/Developer/Xcode/iOS DeviceSupport"])
    add("xcode_archives", "Xcode Archives", ["~/Library/Developer/Xcode/Archives"], auto=False)
    add("coresim", "模拟器缓存", ["~/Library/Developer/CoreSimulator/Caches"])
    add("gobuild", "Go build 缓存", ["~/Library/Caches/go-build"])
    add("gradle", "Gradle 缓存", ["~/.gradle/caches"])
    return t


def scan_dev_caches():
    items = []
    for t in _dev_cache_targets():
        size = sum(dir_size(p) for p in t["paths"])
        if size < 1024 * 1024:   # < 1MB 不值得列
            continue
        items.append({
            "id": f"dev:{t['key']}",
            "category": "dev_caches",
            "label": t["label"],
            "detail": "  ".join(str(p).replace(str(HOME), "~") for p in t["paths"]),
            "size": size,
            "paths": [str(p) for p in t["paths"]],
            "clean_cmd": t["clean_cmd"],
            "auto_default": t["auto"],
            "deletable": True,
        })
    # Docker（只有装了才列；清理用 prune，默认不自动勾）
    if _which("docker"):
        rc, out, _ = _run(["docker", "system", "df", "--format", "{{.Size}} {{.Type}}"], timeout=10)
        if rc == 0 and out.strip():
            items.append({
                "id": "dev:docker",
                "category": "dev_caches",
                "label": "Docker 悬空镜像/缓存",
                "detail": "docker system prune（删除未使用的镜像、容器、网络、构建缓存）",
                "size": _parse_docker_reclaimable(),
                "paths": [],
                "clean_cmd": ["docker", "system", "prune", "-f"],
                "auto_default": False,
                "deletable": True,
            })
    items.sort(key=lambda x: x["size"], reverse=True)
    return items


def _parse_docker_reclaimable():
    rc, out, _ = _run(["docker", "system", "df"], timeout=10)
    total = 0
    if rc != 0:
        return 0
    for line in out.splitlines():
        m = re.search(r"\(([\d.]+)\s*(\wB)\b", line)  # RECLAIMABLE 列形如 "1.2GB (80%)"
        if m:
            try:
                val = float(m.group(1))
                unit = m.group(2).upper()
                mult = {"B": 1, "KB": 1024, "MB": 1024**2, "GB": 1024**3, "TB": 1024**4}.get(unit, 1)
                total += int(val * mult)
            except Exception:  # noqa
                pass
    return total


def scan_system_caches():
    items = []
    dev_paths = set()
    for t in _dev_cache_targets():
        for p in t["paths"]:
            dev_paths.add(str(p.resolve()))

    # ~/Library/Caches 下、未被开发者板块覆盖的应用缓存（按子目录逐个列）
    caches_root = HOME / "Library" / "Caches"
    for child, sz in subdirs_with_size(caches_root, limit=25):
        if str(child.resolve()) in dev_paths:
            continue
        if sz < 20 * 1024 * 1024:   # 只列 >20MB 的，避免噪音
            continue
        items.append({
            "id": f"sys:cache:{child.name}",
            "category": "system_caches",
            "label": f"应用缓存 · {child.name}",
            "detail": str(child).replace(str(HOME), "~"),
            "size": sz,
            "paths": [str(child)],
            "clean_cmd": None,
            "auto_default": True,
            "deletable": True,
        })

    # 应用日志
    logs = HOME / "Library" / "Logs"
    sz = dir_size(logs)
    if sz > 20 * 1024 * 1024:
        items.append({
            "id": "sys:logs", "category": "system_caches", "label": "应用日志",
            "detail": "~/Library/Logs（删内容，保留目录）", "size": sz,
            "paths": [str(logs)], "clean_cmd": None, "auto_default": True,
            "deletable": True, "contents_only": True,
        })

    # 废纸篓
    trash = HOME / ".Trash"
    sz = dir_size(trash)
    if sz > 1024 * 1024:
        items.append({
            "id": "sys:trash", "category": "system_caches", "label": "废纸篓",
            "detail": "~/.Trash（清空）", "size": sz,
            "paths": [str(trash)], "clean_cmd": None, "auto_default": True,
            "deletable": True, "contents_only": True,
        })

    items.sort(key=lambda x: x["size"], reverse=True)
    return items


def scan_large_files():
    """大文件 + 久未动的下载。这些是用户文件，永不自动勾选。"""
    items = []
    seen = set()

    def consider(path, min_size, tag, old_days=None):
        try:
            st = path.stat()
        except OSError:
            return
        if st.st_size < min_size:
            return
        rp = str(path.resolve())
        if rp in seen:
            return
        old = ""
        if old_days is not None:
            age = (time.time() - st.st_mtime) / 86400
            if age < old_days:
                return
            old = f"，{int(age)} 天未动"
        seen.add(rp)
        items.append({
            "id": f"big:{abs(hash(rp))}",
            "category": "large_files",
            "label": path.name,
            "detail": str(path).replace(str(HOME), "~") + old,
            "size": st.st_size,
            "paths": [str(path)],
            "clean_cmd": None,
            "auto_default": False,
            "deletable": True,
        })

    # Downloads：>100MB 或 90 天没动
    dl = HOME / "Downloads"
    if dl.exists():
        for f in _find_files(dl, min_size=100 * 1024 * 1024, max_depth=2, limit=60):
            consider(f, 100 * 1024 * 1024, "dl")
        for f in _find_files(dl, min_size=20 * 1024 * 1024, max_depth=2, limit=60, older_days=90):
            consider(f, 20 * 1024 * 1024, "dl_old", old_days=90)

    # 其它常见目录里的超大文件（>500MB）
    for d in ("Desktop", "Movies", "Documents"):
        root = HOME / d
        if root.exists():
            for f in _find_files(root, min_size=500 * 1024 * 1024, max_depth=3, limit=40):
                consider(f, 500 * 1024 * 1024, "big")

    items.sort(key=lambda x: x["size"], reverse=True)
    return items[:50]


def _find_files(root, min_size, max_depth=3, limit=80, older_days=None):
    """用 find 快速找大文件，失败回退 os.walk。返回 Path 列表。"""
    cmd = ["find", str(root), "-maxdepth", str(max_depth), "-type", "f",
           "-size", f"+{min_size // 1024}k"]
    if older_days is not None:
        cmd += ["-mtime", f"+{older_days}"]
    rc, out, _ = _run(cmd, timeout=25)
    results = []
    if rc == 0 and out:
        for line in out.splitlines():
            p = Path(line)
            if p.exists():
                results.append(p)
            if len(results) >= limit:
                break
    return results


# ----------------------------------------------------------------------------
# 建议板块：真实测量 + 安全一键
#   只对「用户级、可还原」的操作开放一键（禁用自启=挪开不删，随时还原）。
#   涉及 sudo / 系统级的只给命令；清内存、一键加速这类无效操作坚决不做。
# ----------------------------------------------------------------------------

DISABLED_AGENTS_DIR = MEM_DIR / "disabled-agents"


def _sysctl(key):
    rc, out, _ = _run(["sysctl", "-n", key], timeout=5)
    return out.strip() if rc == 0 else ""


def _mem_stats():
    """真实内存：物理内存 + swap 占用 + 诚实判断（看 swap，不看『空闲%』）。"""
    try:
        total = int(_sysctl("hw.memsize"))
    except Exception:  # noqa
        total = 0
    swap_used = 0
    m = re.search(r"used\s*=\s*([\d.]+)([MG])", _sysctl("vm.swapusage"))
    if m:
        swap_used = int(float(m.group(1)) * (1024**3 if m.group(2) == "G" else 1024**2))
    rc, out, _ = _run(["vm_stat"], timeout=5)
    page, free = 16384, 0
    if rc == 0 and out:
        pm = re.search(r"page size of (\d+)", out)
        if pm:
            page = int(pm.group(1))
        for label in ("Pages free", "Pages speculative"):
            mm = re.search(label + r":\s*(\d+)", out)
            if mm:
                free += int(mm.group(1))
    used = max(0, total - free * page)
    if swap_used > 3 * 1024**3:
        lvl, verdict = "bad", "内存吃紧（swap 占用偏高，已在压硬盘，会卡）"
    elif swap_used > 1024**3:
        lvl, verdict = "warn", "内存略紧（开始用 swap）"
    else:
        lvl, verdict = "ok", "内存充足（macOS 用空闲内存做缓存，属正常）"
    return {"title": "内存压力", "level": lvl,
            "body": f"已用 {human_size(used)} / 共 {human_size(total)} · swap 占用 {human_size(swap_used)}",
            "hint": verdict + "。注：『清内存释放 X GB』在 macOS 上无效，本工具不做。"}


def _top_procs():
    """CPU / 内存占用最高的进程（真实诊断，只报告，关进程由用户自己来）。"""
    rows = []
    rc, out, _ = _run(["ps", "-Aro", "pcpu=,comm="], timeout=6)
    if rc == 0 and out:
        for line in out.strip().splitlines()[:4]:
            parts = line.strip().split(None, 1)
            if len(parts) == 2 and float(parts[0] or 0) > 1.0:
                rows.append({"label": parts[1].rsplit("/", 1)[-1][:34], "sub": f"CPU {parts[0]}%"})
    seen = {r["label"] for r in rows}
    rc, out, _ = _run(["ps", "-Amo", "rss=,comm="], timeout=6)
    if rc == 0 and out:
        for line in out.strip().splitlines()[:4]:
            parts = line.strip().split(None, 1)
            if len(parts) == 2:
                name = parts[1].rsplit("/", 1)[-1][:34]
                rss = int(parts[0] or 0) * 1024
                if name not in seen and rss > 300 * 1024 * 1024:
                    rows.append({"label": name, "sub": f"内存 {human_size(rss)}"})
                    seen.add(name)
    if not rows:
        return None
    return {"title": "资源占用大户", "level": "info",
            "body": "下面这些最吃 CPU / 内存，确认不用就自己关掉，能立刻变快：", "rows": rows}


def scan_performance():
    s = [_mem_stats()]
    tp = _top_procs()
    if tp:
        s.append(tp)
    # 登录项（只读 + 指路，避免误删，删除请去系统设置）
    rc, out, _ = _run(["osascript", "-e",
                       'tell application "System Events" to get the name of every login item'], timeout=10)
    if rc == 0 and out.strip():
        names = [x.strip() for x in out.strip().split(",") if x.strip()]
        if names:
            s.append({"title": f"开机登录项（{len(names)} 个）", "level": "info",
                      "body": "、".join(names),
                      "hint": "在 系统设置 › 通用 › 登录项 里关掉不需要的，能加快开机。"})
    # 用户级后台自启 —— 安全一键禁用（挪开不删，可还原）
    la = HOME / "Library" / "LaunchAgents"
    rows = []
    if la.exists():
        for p in sorted(la.glob("*.plist")):
            rows.append({"label": p.stem, "sub": "用户级常驻",
                         "action": {"type": "disable_agent", "target": str(p)}})
    if rows:
        s.append({"title": f"后台自启（{len(rows)} 个 · 可一键禁用）", "level": "warn",
                  "body": "这些在后台常驻、吃内存与电。确认无用的可禁用——只是挪开、随时还原，不删除：",
                  "rows": rows})
    # 已禁用的，给一键还原
    drows = []
    if DISABLED_AGENTS_DIR.exists():
        for p in sorted(DISABLED_AGENTS_DIR.glob("*.plist")):
            drows.append({"label": p.stem, "sub": "已禁用",
                          "action": {"type": "enable_agent", "target": str(p)}})
    if drows:
        s.append({"title": f"已禁用的自启（{len(drows)} 个）", "level": "ok",
                  "body": "之前禁用的，需要时可一键还原：", "rows": drows})
    return s


def _resolve_dns():
    rc, out, _ = _run(["scutil", "--dns"], timeout=6)
    servers = re.findall(r"nameserver\[\d+\]\s*:\s*([\d.]+)", out) if rc == 0 else []
    return list(dict.fromkeys(servers))


def _dig_ms(server):
    rc, out, _ = _run(["dig", "+time=1", "+tries=1", f"@{server}", "www.apple.com"], timeout=4)
    if rc == 0:
        m = re.search(r"Query time:\s*(\d+)\s*msec", out)
        if m:
            return int(m.group(1))
    return None


def _gateway():
    rc, out, _ = _run(["route", "-n", "get", "default"], timeout=5)
    m = re.search(r"gateway:\s*([\d.]+)", out) if rc == 0 else None
    return m.group(1) if m else None


def _ping(host):
    if not host:
        return (None, None)
    rc, out, _ = _run(["ping", "-c", "3", "-t", "3", host], timeout=8)
    avg = loss = None
    m = re.search(r"=\s*[\d.]+/([\d.]+)/", out)
    if m:
        avg = float(m.group(1))
    lm = re.search(r"([\d.]+)%\s*packet loss", out)
    if lm:
        loss = float(lm.group(1))
    return (avg, loss)


def _wifi_service():
    rc, out, _ = _run(["networksetup", "-listallnetworkservices"], timeout=6)
    if rc == 0:
        for line in out.splitlines():
            if "Wi-Fi" in line or "AirPort" in line:
                return line.strip()
    return "Wi-Fi"


def scan_network():
    s = []
    current = _resolve_dns()
    cur = current[0] if current else None
    candidates = {"223.5.5.5": "阿里", "119.29.29.29": "腾讯", "1.1.1.1": "Cloudflare", "8.8.8.8": "Google"}
    probe = {}
    targets = list(candidates) + ([cur] if cur and cur not in candidates else [])
    try:
        with cf.ThreadPoolExecutor(max_workers=6) as ex:
            futs = {ex.submit(_dig_ms, ip): ip for ip in targets}
            for f in cf.as_completed(futs, timeout=8):
                probe[futs[f]] = f.result()
    except Exception:  # noqa
        pass
    cur_ms = probe.get(cur)
    ranked = sorted([(ip, probe[ip]) for ip in candidates if probe.get(ip) is not None], key=lambda x: x[1])
    item = {"title": "DNS 实测延迟", "level": "info",
            "body": f"当前 {cur or '—'}：{cur_ms}ms" if cur_ms is not None else f"当前 {cur or '—'}：超时",
            "rows": [{"label": f"{ip} {candidates[ip]}", "sub": f"{ms}ms"} for ip, ms in ranked],
            "hint": "数字越小越快。"}
    if ranked:
        best_ip, best_ms = ranked[0]
        if cur_ms is None or best_ms + 5 < cur_ms:
            item["level"] = "warn"
            item["hint"] = f"实测最快是 {best_ip}（{best_ms}ms）。切换需管理员，命令如右："
            item["command"] = f'networksetup -setdnsservers "{_wifi_service()}" {best_ip} 1.1.1.1'
    s.append(item)
    # 延迟 / 丢包（并发 ping 路由器 + 外网）
    gw = _gateway()
    gw_avg = gw_loss = ext_avg = ext_loss = None
    try:
        with cf.ThreadPoolExecutor(max_workers=2) as ex:
            fg, fe = ex.submit(_ping, gw), ex.submit(_ping, "223.5.5.5")
            gw_avg, gw_loss = fg.result(timeout=10)
            ext_avg, ext_loss = fe.result(timeout=10)
    except Exception:  # noqa
        pass
    parts = []
    if ext_avg is not None:
        parts.append(f"外网延迟 {ext_avg:.0f}ms")
    if ext_loss is not None:
        parts.append(f"丢包 {ext_loss:.0f}%")
    if gw_avg is not None:
        parts.append(f"到路由器 {gw_avg:.0f}ms")
    if parts:
        lvl = "ok"
        if (ext_loss or 0) > 5 or (ext_avg or 0) > 120:
            lvl = "warn"
        if (ext_loss or 0) > 20:
            lvl = "bad"
        s.append({"title": "网络延迟 / 丢包", "level": lvl, "body": " · ".join(parts),
                  "hint": "丢包高或延迟大：靠近路由器、换 5GHz、或重启路由器。"})
    # Wi-Fi
    rc, out, _ = _run(["networksetup", "-getairportnetwork", "en0"], timeout=6)
    if rc == 0 and "Current Wi-Fi Network" in out:
        s.append({"title": "当前 Wi-Fi", "level": "info", "body": out.split(":", 1)[-1].strip(),
                  "hint": "信号弱时靠近路由器或用 5GHz 频段。"})
    # 维护命令（需 sudo，手动执行）
    s.append({"title": "刷新 DNS 缓存", "level": "action",
              "body": "网页打不开 / 解析错乱时常能解决",
              "command": "sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder",
              "hint": "需输入开机密码，终端手动执行。"})
    return s


def execute_action(action_type, target):
    """安全一键：只对用户级、可还原的操作放开（禁用/还原自启）。"""
    ensure_mem_dir()
    DISABLED_AGENTS_DIR.mkdir(parents=True, exist_ok=True)
    la = (HOME / "Library" / "LaunchAgents").resolve()
    try:
        tp = Path(target).resolve()
    except Exception:  # noqa
        return {"ok": False, "message": "路径无效"}
    if action_type == "disable_agent":
        if tp.parent != la or tp.suffix != ".plist" or not tp.exists():
            return {"ok": False, "message": "只允许禁用 ~/Library/LaunchAgents 下的用户级自启"}
        _run(["launchctl", "unload", "-w", str(tp)], timeout=10)
        try:
            shutil.move(str(tp), str(DISABLED_AGENTS_DIR / tp.name))
        except Exception as e:  # noqa
            return {"ok": False, "message": f"挪动失败：{e}"}
        return {"ok": True, "message": f"已禁用 {tp.stem}（挪到 disabled-agents，可还原）"}
    if action_type == "enable_agent":
        if tp.parent != DISABLED_AGENTS_DIR.resolve() or not tp.exists():
            return {"ok": False, "message": "只允许还原本工具禁用过的项"}
        dest = HOME / "Library" / "LaunchAgents" / tp.name
        try:
            shutil.move(str(tp), str(dest))
        except Exception as e:  # noqa
            return {"ok": False, "message": f"还原失败：{e}"}
        _run(["launchctl", "load", "-w", str(dest)], timeout=10)
        return {"ok": True, "message": f"已还原 {tp.stem}"}
    return {"ok": False, "message": "未知操作"}


# ----------------------------------------------------------------------------
# 完整扫描
# ----------------------------------------------------------------------------

def full_scan(prefs):
    auto_map = prefs.get("auto_check", {})

    def apply_auto(items):
        for it in items:
            cat = it["category"]
            # 类别级偏好覆盖单项默认；大文件永远不自动勾
            if cat == "large_files":
                it["checked"] = False
            elif cat in auto_map:
                it["checked"] = bool(auto_map[cat]) and it.get("auto_default", True)
            else:
                it["checked"] = it.get("auto_default", False)
        return items

    # 性能/网络测量（含 ping/dig）和磁盘扫描并发跑，避免拖慢总时长
    with cf.ThreadPoolExecutor(max_workers=2) as ex:
        f_perf = ex.submit(scan_performance)
        f_net = ex.submit(scan_network)
        dev = apply_auto(scan_dev_caches())
        sysc = apply_auto(scan_system_caches())
        big = apply_auto(scan_large_files())
        perf_items = _safe_future(f_perf)
        net_items = _safe_future(f_net)

    cleanable = {
        "dev_caches": {"label": "开发者缓存", "items": dev},
        "system_caches": {"label": "系统与应用缓存", "items": sysc},
        "large_files": {"label": "大文件与下载", "items": big},
    }
    advisories = {
        "performance": {"label": "性能优化建议", "items": perf_items},
        "network": {"label": "网络优化建议", "items": net_items},
    }
    total_reclaimable = sum(it["size"] for c in cleanable.values() for it in c["items"])
    pre_checked = sum(it["size"] for c in cleanable.values() for it in c["items"] if it.get("checked"))

    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "disk": _disk_info(),
        "cleanable": cleanable,
        "advisories": advisories,
        "total_reclaimable": total_reclaimable,
        "total_reclaimable_h": human_size(total_reclaimable),
        "pre_checked": pre_checked,
        "pre_checked_h": human_size(pre_checked),
        "memory_summary": load_memory_summary(),
    }


def _disk_info():
    rc, out, _ = _run(["df", "-k", "/"], timeout=8)
    if rc == 0:
        lines = out.strip().splitlines()
        if len(lines) >= 2:
            parts = lines[1].split()
            try:
                total = int(parts[1]) * 1024
                avail = int(parts[3]) * 1024
                used = total - avail
                return {"total": total, "used": used, "avail": avail,
                        "total_h": human_size(total), "used_h": human_size(used),
                        "avail_h": human_size(avail),
                        "used_pct": round(used / total * 100) if total else 0}
            except Exception:  # noqa
                pass
    return {}


# ----------------------------------------------------------------------------
# 执行删除（带进度回调）
# ----------------------------------------------------------------------------

def clean_items(selected_items, prefs, progress_cb):
    """
    selected_items: full_scan 里被勾选的 item dict 列表。
    progress_cb(event): event 是 dict，前端 SSE 会收到。
    返回 summary dict。
    """
    never_touch = prefs.get("never_touch", [])
    total = len(selected_items)
    freed_total = 0
    done = []
    errors = []

    progress_cb({"type": "start", "total": total})

    for idx, it in enumerate(selected_items):
        label = it.get("label", it.get("id"))
        cat = it.get("category")
        progress_cb({"type": "item_start", "index": idx, "total": total,
                     "id": it["id"], "label": label, "category": cat})
        freed = 0
        err = None
        try:
            if it.get("clean_cmd"):
                # 用工具自带命令清理（brew/docker），按命令前后目录差估算释放
                before = sum(dir_size(p) for p in it.get("paths", []))
                rc, out, serr = _run(it["clean_cmd"], timeout=180)
                after = sum(dir_size(p) for p in it.get("paths", []))
                freed = max(before - after, 0) if it.get("paths") else it.get("size", 0)
                if rc != 0 and not it.get("paths"):
                    err = (serr or out or "命令执行失败").strip()[:200]
            else:
                for p in it.get("paths", []):
                    ok, reason = _is_safe_to_delete(p, never_touch)
                    if not ok:
                        err = f"跳过（{reason}）：{p}"
                        continue
                    sz = dir_size(p)
                    if it.get("contents_only"):
                        freed += _delete_contents(Path(p))
                    else:
                        freed += _delete_path(Path(p))
        except Exception as e:  # noqa
            err = str(e)[:200]

        freed_total += freed
        rec = {"id": it["id"], "label": label, "category": cat,
               "freed": freed, "freed_h": human_size(freed), "error": err}
        if err:
            errors.append(rec)
        else:
            done.append(rec)
        progress_cb({"type": "item_done", "index": idx, "total": total,
                     "id": it["id"], "label": label, "category": cat,
                     "freed": freed, "freed_h": human_size(freed),
                     "freed_total": freed_total, "freed_total_h": human_size(freed_total),
                     "error": err})
        time.sleep(0.05)  # 让小猫动画看得见每一步

    summary = {
        "type": "finished",
        "freed_total": freed_total,
        "freed_total_h": human_size(freed_total),
        "count_done": len(done),
        "count_error": len(errors),
        "done": done,
        "errors": errors,
        "finished_at": datetime.now().isoformat(timespec="seconds"),
    }
    progress_cb(summary)
    record_history(selected_items, summary)
    update_prefs_after_run(selected_items, prefs)
    return summary


def _delete_path(p):
    """永久删除文件或目录，返回释放字节。"""
    sz = dir_size(p)
    try:
        if p.is_dir() and not p.is_symlink():
            shutil.rmtree(p, ignore_errors=True)
        else:
            p.unlink(missing_ok=True)
    except Exception:  # noqa
        rc, _, _ = _run(["rm", "-rf", str(p)], timeout=120)
    return sz if not p.exists() else 0


def _delete_contents(p):
    """只删目录内容，保留目录本身（日志/废纸篓）。"""
    freed = 0
    if not p.exists():
        return 0
    for child in list(p.iterdir()):
        freed += _delete_path(child)
    return freed


# ----------------------------------------------------------------------------
# 记忆：preferences / history / MEMORY.md
# ----------------------------------------------------------------------------

DEFAULT_PREFS = {
    "delete_mode": "permanent",
    "auto_check": {            # 类别级：是否自动勾选
        "dev_caches": True,
        "system_caches": True,
        "large_files": False,
    },
    "never_touch": [],
    "category_stats": {},      # 学习用：每类别 approved / declined 次数
    "notes": "",
}


def ensure_mem_dir():
    MEM_DIR.mkdir(parents=True, exist_ok=True)


def load_prefs():
    ensure_mem_dir()
    if PREFS_PATH.exists():
        try:
            data = json.loads(PREFS_PATH.read_text("utf-8"))
            merged = dict(DEFAULT_PREFS)
            merged.update(data)
            for k, v in DEFAULT_PREFS["auto_check"].items():
                merged.setdefault("auto_check", {}).setdefault(k, v)
            return merged
        except Exception:  # noqa
            pass
    save_prefs(DEFAULT_PREFS)
    return dict(DEFAULT_PREFS)


def save_prefs(prefs):
    ensure_mem_dir()
    PREFS_PATH.write_text(json.dumps(prefs, ensure_ascii=False, indent=2), "utf-8")


def record_history(selected_items, summary):
    ensure_mem_dir()
    entry = {
        "ts": summary["finished_at"],
        "freed": summary["freed_total"],
        "freed_h": summary["freed_total_h"],
        "count_done": summary["count_done"],
        "count_error": summary["count_error"],
        "categories": sorted({it["category"] for it in selected_items}),
        "items": [{"id": it["id"], "label": it.get("label"), "category": it["category"]}
                  for it in selected_items],
    }
    with HISTORY_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    render_memory_md()


def update_prefs_after_run(selected_items, prefs):
    """根据用户实际勾了什么，强化/弱化类别自动勾选偏好。"""
    chosen_cats = {it["category"] for it in selected_items}
    stats = prefs.setdefault("category_stats", {})
    for cat in ("dev_caches", "system_caches", "large_files"):
        st = stats.setdefault(cat, {"approved": 0, "declined": 0})
        if cat in chosen_cats:
            st["approved"] += 1
        # 连续被批准 2 次以上 → 下次自动勾（large_files 永远保持手动）
        if cat != "large_files" and st["approved"] >= 2:
            prefs["auto_check"][cat] = True
    save_prefs(prefs)


def load_memory_summary():
    """给页面顶部展示的简短记忆：上次清理时间 + 累计释放。"""
    if not HISTORY_PATH.exists():
        return {"runs": 0, "last": None, "total_freed_h": "0B"}
    runs = 0
    total = 0
    last = None
    try:
        for line in HISTORY_PATH.read_text("utf-8").splitlines():
            if not line.strip():
                continue
            e = json.loads(line)
            runs += 1
            total += e.get("freed", 0)
            last = e.get("ts")
    except Exception:  # noqa
        pass
    return {"runs": runs, "last": last, "total_freed_h": human_size(total)}


def render_memory_md():
    """生成给人/Claude 读的 MEMORY.md。"""
    ensure_mem_dir()
    summ = load_memory_summary()
    prefs = load_prefs()
    lines = [
        "# 磁盘清理小猫 · 记忆与交接",
        "",
        "> 本文件由 skill 自动维护，也欢迎 Claude / 你手动补充「备注」段。",
        "",
        "## 概览",
        f"- 累计清理次数：**{summ['runs']}**",
        f"- 累计释放空间：**{summ['total_freed_h']}**",
        f"- 上次清理：{summ['last'] or '（无）'}",
        "",
        "## 当前偏好（自动学习）",
        f"- 删除方式：`{prefs.get('delete_mode')}`（永久删除，删什么需页面确认）",
        "- 自动勾选：",
    ]
    for k, v in prefs.get("auto_check", {}).items():
        lines.append(f"  - {k}: {'✅ 自动勾选' if v else '⬜ 默认不勾'}")
    nt = prefs.get("never_touch", [])
    lines.append("- never_touch（永不清理）：" + ("、".join(nt) if nt else "（空）"))
    if prefs.get("notes"):
        lines += ["", "## 备注", prefs["notes"]]
    lines += ["", "## 最近清理记录"]
    if HISTORY_PATH.exists():
        rows = [l for l in HISTORY_PATH.read_text("utf-8").splitlines() if l.strip()]
        for line in rows[-10:][::-1]:
            try:
                e = json.loads(line)
                lines.append(f"- {e['ts']} · 释放 {e['freed_h']} · "
                             f"{e['count_done']} 项 · 类别：{'/'.join(e.get('categories', []))}")
            except Exception:  # noqa
                pass
    else:
        lines.append("- （暂无）")
    MEMORY_MD.write_text("\n".join(lines) + "\n", "utf-8")


if __name__ == "__main__":
    # 命令行自测：只扫描，打印 JSON
    p = load_prefs()
    import pprint
    pprint.pprint(full_scan(p))
