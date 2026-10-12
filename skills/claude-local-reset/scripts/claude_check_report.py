#!/usr/bin/env python3
"""Turn recorded checks into an offline HTML receipt; never run an audit."""

import argparse
from datetime import datetime, timezone
from html import escape
import ipaddress
import json
import os
from pathlib import Path
import re
from string import Template
import subprocess
import sys


STATES = {"pass": "通过", "fail": "未通过", "review": "待核实", "not_tested": "未检测"}
SITES = {
    "ipleak": ("IPLeak", "https://ipleak.net/"),
    "browserleaks_dns": ("BrowserLeaks DNS", "https://browserleaks.com/dns"),
    "netcoffee": ("Net.Coffee Claude", "https://ip.net.coffee/claude/"),
    "browserleaks_webrtc": ("BrowserLeaks WebRTC", "https://browserleaks.com/webrtc"),
    "ipinfo": ("IPinfo", "https://ipinfo.io/"),
    "ping0": ("ping0", "https://ping0.cc/"),
    "whoer": ("Whoer", "https://whoer.net/"),
    "ippure": ("IPPure", "https://ippure.com/"),
}
EXCLUDED = {"CN", "HK"}
TEMPLATE = Path(__file__).resolve().parent.parent / "assets/report-template.html"
GUIDE_TEMPLATE = TEMPLATE.with_name("guide-template.html")


def mapping(value):
    return value if isinstance(value, dict) else {}


def items(value):
    return value if isinstance(value, list) else []


def timestamp(value):
    if not isinstance(value, str):
        return None
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return result if result.tzinfo is not None else None
    except ValueError:
        return None


def countries(value):
    values = items(value)
    if not values or any(not isinstance(item, str) or not re.fullmatch(r"[A-Z]{2}", item.upper()) or item.upper() in {"ZZ", "XX", "EU", "UN"} for item in values):
        return []
    return sorted(set(item.upper() for item in values))


def flag(code):
    return "".join(chr(127397 + ord(char)) for char in code) + " " + code


def public_ips(values, *, demo=False):
    result = []
    for value in items(values):
        if not isinstance(value, str):
            continue
        try:
            address = ipaddress.ip_address(value)
            if address.is_global or (demo and value.startswith("203.0.113.")):
                result.append(str(address))
        except ValueError:
            pass
    return list(dict.fromkeys(result))


def masked_ip(value):
    address = ipaddress.ip_address(value)
    if address.version == 4:
        return ".".join(str(address).split(".")[:3]) + ".*"
    return ":".join(address.exploded.split(":")[:3]) + ":…"


def check(identifier, title, state, evidence, next_step, *, critical=False, site=None):
    return {
        "id": identifier, "title": title, "state": state, "status": STATES[state],
        "evidence": evidence, "next_step": next_step, "critical": critical,
        "site": site,
    }


def evaluate(network=None, browser=None, operation=None, *, expected_country=None, expected_timezone=None, now=None, demo=False):
    network, browser, operation = mapping(network), mapping(browser), mapping(operation)
    now = now or datetime.now(timezone.utc)
    anchor = timestamp(network.get("checked_at_utc")) or now
    local_fresh = timestamp(network.get("checked_at_utc")) is not None and abs((anchor - now).total_seconds()) <= 3600
    context = mapping(browser.get("context"))
    context_ok = context.get("type") == "local-browser" and context.get("profile_confirmed") is True
    observations = mapping(browser.get("sites"))
    results = []

    def fresh_site(site):
        value = mapping(observations.get(site))
        measured = timestamp(value.get("checked_at_utc"))
        valid = context_ok and measured is not None and abs((measured - anchor).total_seconds()) <= 3600 and abs((measured - now).total_seconds()) <= 3600
        return value, valid

    action, outcome = operation.get("action", "check"), operation.get("status", "not_run")
    action_label = {"check": "仅检查", "preview": "仅预览", "reset": "本地重置", "restore": "本地回滚"}.get(action, "未说明操作")
    if action in {"reset", "restore"}:
        state = "pass" if outcome == "completed" else "fail" if outcome in {"partial", "failed"} else "not_tested"
        evidence = "操作完成；保留备份" if state == "pass" else "操作仅部分完成或失败" if state == "fail" else "没有有效的执行结果"
        results.append(check("operation", action_label, state, evidence, "先核对原批次清单和备份，不盲目重复执行" if state != "pass" else "保存备份；需要回滚时先退出相关 Claude 会话", critical=True))
    elif outcome in {"partial", "failed"}:
        results.append(check("operation", "检查流程完成情况", "fail", "流程部分完成或失败；已有绿色结果不能代替流程完成", "保留已取得结果，先处理失败阶段再补齐检测", critical=True))

    attempts = items(mapping(network.get("exit_ip")).get("attempts")) if local_fresh else []
    observed = []
    for attempt in attempts:
        attempt = mapping(attempt)
        data = mapping(attempt.get("observation"))
        addresses = public_ips([data.get("ip")], demo=demo)
        codes = countries([data.get("country")])
        if attempt.get("status") == "已观察" and addresses and codes:
            observed.append((attempt.get("requested_connection_family"), addresses[0], codes[0]))
    if not observed:
        results.append(check("terminal_ip", "终端出口地区", "not_tested", "未取得当次可核验的终端出口", "如需检查 CLI 出口，在实际终端运行一次 --online", site="ipinfo"))
    else:
        codes = {row[2] for row in observed}
        state = "fail" if codes & EXCLUDED or (expected_country and codes != {expected_country}) else "pass"
        evidence = "；".join(f"{flag(code)} · {masked_ip(address)}" for _, address, code in observed)
        results.append(check("terminal_ip", "终端出口地区", state, evidence + "（只代表该次终端查询）", "核对终端与代理目标域名路由，再复测" if state == "fail" else "浏览器出口须另测；长期稳定性不能用单次结果判断", critical=True, site="ipinfo"))

    for site, title, ip_key in (("ipleak", "IPLeak 地区标签", "public_ips"), ("browserleaks_dns", "BrowserLeaks DNS 地区", "resolver_ips")):
        value, fresh = fresh_site(site)
        codes = countries(value.get("country_codes"))
        addresses = public_ips(value.get(ip_key), demo=demo)
        if not fresh:
            state, evidence = "not_tested", "缺少当次本地浏览器结果，或 profile／时间未核实"
        elif codes and (set(codes) & EXCLUDED or (expected_country and set(codes) != {expected_country})):
            state, evidence = "fail", "出现未符合用户标准的地区标签：" + "、".join(flag(code) for code in codes)
        elif value.get("completed") is not True or not codes or not addresses:
            state, evidence = "not_tested", "测试未完成，或缺少可核验的国家／公网地址"
        else:
            state, evidence = "pass", "、".join(flag(code) for code in codes) + "；未出现 CN/HK，符合本次地区标准"
        results.append(check(site, title, state, evidence, "在同一 profile 完成检测；核对标签与实际出口/DNS 路径" if state != "pass" else "保留当次结果；地区标签通过不等于证明完全无泄漏", critical=True, site=site))

    def leak_result(site, identifier, title, component=None, critical=True):
        value, fresh = fresh_site(site)
        item = mapping(value.get(component)) if component else value
        reported = item.get("state")
        if not fresh:
            state, evidence = "not_tested", "缺少当次已确认 profile 的实测结果"
        elif reported == "leak":
            state, evidence = "fail", "该次检测报告泄漏或已确认公网出口不匹配"
        elif item.get("completed") is not True or reported in {None, "unknown", "disabled"}:
            state, evidence = "not_tested", "尚未完成／结果不明／WebRTC 不可用，不能当作通过"
        elif reported == "clear":
            state, evidence = "pass", "实际测试完成，未报告该项泄漏"
            if site == "browserleaks_webrtc":
                tcp = public_ips(mapping(observations.get("ipleak")).get("public_ips"), demo=demo)
                udp = public_ips(value.get("public_ips"), demo=demo)
                if tcp and udp and not set(udp).issubset(tcp):
                    state, evidence = "review", "公网候选与 IPLeak 出口不同；需核对分流或 UDP 路径，不能仅凭 clear 通过"
        else:
            state, evidence = "review", "无法识别检测状态，需核对原页面"
        results.append(check(identifier, title, state, evidence, "检查 DNS、UDP、IPv6 或浏览器设置后复测" if state == "fail" else "在原 profile 完成该项测试" if state != "pass" else "结果只适用于该次浏览器测试", critical=critical, site=site))

    leak_result("netcoffee", "netcoffee_dns", "Net.Coffee · DNS 泄漏", "dns")
    leak_result("netcoffee", "netcoffee_webrtc", "Net.Coffee · WebRTC UDP", "webrtc")
    leak_result("browserleaks_webrtc", "browserleaks_webrtc", "BrowserLeaks · WebRTC", critical=False)

    proxy = mapping(network.get("system_proxy")) if local_fresh else {}
    flags = mapping(proxy.get("flags"))
    valid_flags = {key: value for key, value in flags.items() if key in {"HTTPEnable", "HTTPSEnable", "SOCKSEnable", "ProxyAutoConfigEnable", "ProxyAutoDiscoveryEnable"} and isinstance(value, list) and value and all(type(flag_value) is int and flag_value in {0, 1} for flag_value in value)}
    enabled = [key for key, value in valid_flags.items() if 1 in value]
    mode = network.get("expected_mode", "unknown")
    if not valid_flags:
        state, evidence = "not_tested", "未获得有效系统代理开关"
    elif mode == "system-proxy" and enabled:
        state, evidence = "pass", "系统代理已开启，与指定模式一致；实际出口见浏览器测试"
    elif mode in {"tun", "direct"} and not enabled and len(valid_flags) == 5:
        state, evidence = "pass", "五个代理/PAC/自动发现开关均关闭，与指定模式一致"
    else:
        state, evidence = "review", "已观察到开启的代理，或字段/预期模式未补齐；不能自动当作残留"
    results.append(check("system_proxy", "系统代理与预期模式", state, evidence, "对照客户端与实际网络服务核对；不要默认全关", critical=True))

    sources = [mapping(network.get("environment")), mapping(network.get("claude_settings")), mapping(network.get("claude_settings_local")), *[mapping(value) for value in items(network.get("shell_files"))], *[mapping(value) for value in items(network.get("system_shell_files"))], *[mapping(value) for value in items(network.get("curl_wget"))], mapping(network.get("hosts_file"))] if local_fresh else []
    entries = [mapping(entry) for source in sources for entry in items(source.get("entries"))]
    route_entries = [entry for entry in entries if entry.get("kind") in {"proxy", "api_base_url"} and entry.get("configured") is True]
    hosts_matches = [mapping(item) for item in items(mapping(network.get("hosts_file")).get("matches"))] if local_fresh else []
    custom = any(entry.get("route") == "custom_host" or entry.get("status") == "待核实" or entry.get("kind") == "proxy" for entry in route_entries) or bool(hosts_matches)
    profile = mapping(network.get("profile_scan"))
    expected_user = profile.get("user_files") if type(profile.get("user_files")) is int else 8
    expected_system = profile.get("system_files") if type(profile.get("system_files")) is int else 4
    shell_count = len(list(items(network.get("shell_files"))))
    system_count = len(list(items(network.get("system_shell_files"))))
    curl_count = len(list(items(network.get("curl_wget"))))
    hosts_name = hosts_label(mapping(network.get("hosts_file")).get("file"))
    covered = shell_count == expected_user and system_count == expected_system and curl_count == 2 and mapping(network.get("hosts_file")).get("status") == "已观察" and all(source.get("status") == "已观察" for source in sources) and not any(mapping(network.get(key)).get("custom_config_dir_present") for key in ("claude_settings", "claude_settings_local"))
    if not sources:
        state, evidence = "not_tested", "缺少当次本地配置检查"
    elif custom or not covered:
        state, evidence = "review", "存在代理/自定义入口候选或未覆盖配置；需确认用途，尚未自动删除"
        if hosts_matches:
            evidence += "；" + hosts_name + " 中发现 anthropic/claude 域名映射（行 " + "、".join(str(item.get("line")) for item in hosts_matches[:5]) + "），需核对是否为镜像/中转残留"
    else:
        state, evidence = "pass", f"当前环境、{shell_count} 个用户启动文件、{system_count} 个系统启动文件、settings 与 settings.local、curl/wget 配置及 {hosts_name} 中未发现待核实路由候选"
    results.append(check("terminal_routes", "终端与中转配置", state, evidence, "确认废弃来源后，只修改对应键并新开实际终端；项目/管理策略另核对" if state != "pass" else "此结论只覆盖已扫描文件，仍保留其他配置", critical=True))

    npm, git = mapping(network.get("npm_proxy")), mapping(network.get("git_proxy"))
    package_entries = [mapping(entry) for source in (npm, git) for entry in items(source.get("entries"))]
    if not local_fresh or npm.get("status") != "已观察" or git.get("status") != "已观察":
        state, evidence = "not_tested", "npm/Git 查询缺失或失败，不能当作无残留"
    elif any(entry.get("configured") is True for entry in package_entries):
        state, evidence = "review", "存在代理配置；是否仍需要须按该工具用途核对"
    else:
        state, evidence = "pass", "已查询的 npm 用户上下文与 Git 全局未发现已配置代理"
    results.append(check("package_proxies", "npm / Git 代理", state, evidence, "保留合法配置；只删除已确认废弃的具体键"))

    ipv6 = [row for row in observed if ipaddress.ip_address(row[1]).version == 6]
    if ipv6:
        codes = {row[2] for row in ipv6}
        state = "fail" if codes & EXCLUDED or (expected_country and codes != {expected_country}) else "pass"
        evidence = "取得 IPv6 出口并核对地区；不等于浏览器 IPv6 无泄漏"
    else:
        state, evidence = "not_tested", "未取得 IPv6 出口；查询失败不证明 IPv6 已关闭"
    results.append(check("ipv6", "IPv6 出口观察", state, evidence, "先核实代理覆盖；确认绕行后才按原设置修复，勿默认关闭 IPv6"))
    results.append(check("stability", "出口长期稳定性", "not_tested", "本次是一个检测时点，没有长期对照", "保留本次回执；换网络或重启后在同一条件下复测"))

    zone = mapping(network.get("timezone")) if local_fresh else {}
    system_zone = mapping(zone.get("system")).get("value")
    node_zone = mapping(zone.get("node_process")).get("value")
    zone_pattern = r"[A-Za-z0-9_+/-]{1,99}"
    system_zone = system_zone if isinstance(system_zone, str) and re.fullmatch(zone_pattern, system_zone) else None
    node_zone = node_zone if isinstance(node_zone, str) and re.fullmatch(zone_pattern, node_zone) else None
    if expected_timezone:
        state = "not_tested" if not system_zone else "review" if not node_zone else "pass" if system_zone == node_zone == expected_timezone else "fail"
        results.append(check("timezone", "约定时区核对", state, f"系统：{system_zone or '未检测'}；Node：{node_zone or '未检测'}", "按真实使用环境核对 TZ/系统设置，不为过检自动改时区"))

    browser_name = context.get("browser") if context.get("browser") in {"Chrome", "Chromium", "Safari", "Firefox", "Edge"} else "本地浏览器"
    environment_label = browser_name + " · 已确认常用 profile" if context_ok else "实际浏览器/profile 尚未确认"
    privacy = sorted({entry.get("name") + "=" + entry.get("value") for entry in entries if entry.get("kind") == "privacy_preference" and entry.get("name") in {"DISABLE_TELEMETRY", "DISABLE_ERROR_REPORTING", "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC"} and entry.get("value") in {"0", "1"}})
    counts = {state: sum(row["state"] == state for row in results) for state in STATES}
    blockers = [row for row in results if row["critical"] and row["state"] != "pass"]
    if any(row["state"] == "fail" for row in results):
        heading, tone = "先处理未通过项，再继续", "fail"
    elif blockers:
        heading, tone = "先补齐关键检查，再继续", "review"
    else:
        heading, tone = "本次关键质检已通过", "pass"
    if demo:
        heading = "演示：先处理未通过项，再继续"
    priority = {"fail": 0, "not_tested": 1, "review": 2, "pass": 3}
    pending = sorted((row for row in results if row["state"] != "pass"), key=lambda row: (not row["critical"], priority[row["state"]]))
    next_steps = []
    for row in pending:
        step = {"title": row["title"], "text": row["next_step"], "url": SITES[row["site"]][1] if row["site"] else None}
        if step["text"] not in {item["text"] for item in next_steps}:
            next_steps.append(step)
        if len(next_steps) == 3:
            break
    if not blockers and not any(row["state"] == "fail" for row in results):
        next_steps.insert(0, {"title": "自行登录并验证", "text": "在已确认的同一 profile 中打开官方 Claude，核对登录与账号提示；保留备份。", "url": "https://claude.ai/"})
        next_steps = next_steps[:3]
    backup = shorten_backup(operation.get("backup_path"))
    return {
        "schema_version": 1, "demo": demo, "generated_at_utc": now.isoformat(),
        "action_label": action_label, "operation_status": outcome if outcome in {"completed", "partial", "failed", "not_run"} else "not_run",
        "browser_context": environment_label, "expected_country": expected_country,
        "expected_timezone": expected_timezone, "heading": heading, "tone": tone,
        "counts": counts, "checks": results, "next_steps": next_steps,
        "timezone_context": f"系统：{system_zone or '未检测'}；Node：{node_zone or '未检测'}（仅记录，不改设置）",
        "privacy_context": "；".join(privacy) if privacy else "未观察到可展示的显式开关；默认与生效层级未核验，不作为防封判据",
        "backup_display": backup,
    }


def render_html(report):
    def badge(state):
        return f'<span class="badge {state}">{STATES[state]}</span>'
    rows = []
    for row in report["checks"]:
        detail = '<span class="next-inline">下一步：' + escape(row["next_step"]) + '</span>' if row["state"] != "pass" else ''
        rows.append(f'<li class="check-row" data-check="{escape(row["id"])}"><div class="check-title"><strong>{escape(row["title"])}</strong>{badge(row["state"])}</div><p>{escape(row["evidence"])}{detail}</p></li>')
    cards = []
    for site in ("ipleak", "browserleaks_dns", "netcoffee"):
        associated = [row for row in report["checks"] if row["site"] == site]
        state = next((state for state in ("fail", "not_tested", "review", "pass") if any(row["state"] == state for row in associated)), "not_tested")
        labels = " · ".join(("DNS" if row["id"] == "netcoffee_dns" else "UDP" if row["id"] == "netcoffee_webrtc" else "地区") + "：" + row["status"] for row in associated)
        evidence = "；".join(row["evidence"] for row in associated)
        name, url = SITES[site]
        cards.append(f'<article class="site-card"><div class="site-top"><h3>{escape(name)}</h3>{badge(state)}</div><p class="site-result">{escape(labels)}</p><p class="site-evidence">{escape(evidence)}</p><a class="site-link" href="{url}" target="_blank" rel="noopener noreferrer">打开原检测页 <span aria-hidden="true">↗</span></a></article>')
    links = []
    for site in ("ipinfo", "browserleaks_webrtc", "ping0", "whoer", "ippure"):
        name, url = SITES[site]
        associated = next((row for row in report["checks"] if row["site"] == site), None)
        status = associated["status"] if associated else "未检测"
        links.append(f'<a href="{url}" target="_blank" rel="noopener noreferrer"><span>{escape(name)} ↗</span><small>{escape(status)}</small></a>')
    actions = []
    for step in report["next_steps"]:
        link = f'<a href="{escape(step["url"], quote=True)}" target="_blank" rel="noopener noreferrer">前往检测 ↗</a>' if step["url"] else ''
        actions.append(f'<li><strong>{escape(step["title"])}</strong><p>{escape(step["text"])} {link}</p></li>')
    totals = "".join(f'<span class="count {state}"><b>{report["counts"][state]}</b> {STATES[state]}</span>' for state in STATES)
    backup = '<p><strong>备份位置：</strong><code>' + escape(report["backup_display"]) + '</code>。回滚会带回旧身份与登录资料；先退出相关会话。</p>' if report["backup_display"] else '<p>本页未记录可核验的备份位置；仅检查不代表已重置。操作过文件时，请保留原批次清单。</p>'
    demo_banner = '<div class="demo-banner" role="note">演示 · 模拟数据。本页展示样式与判定逻辑，没有检查或改动这台电脑。</div>' if report["demo"] else ''
    return Template(TEMPLATE.read_text(encoding="utf-8")).substitute(
        heading=escape(report["heading"]), tone=report["tone"], demo_banner=demo_banner,
        counts=totals, next_steps="".join(actions), site_cards="".join(cards), check_rows="".join(rows),
        more_links="".join(links), browser_context=escape(report["browser_context"]),
        action_label=escape(report["action_label"]), generated_at=escape(report["generated_at_utc"][:19].replace("T", " ") + " UTC"),
        policy=escape("不出现 CN / HK" + ("；预期地区 " + report["expected_country"] if report["expected_country"] else "；预期出口国家尚未指定")),
        timezone_context=escape(report["timezone_context"]), privacy_context=escape(report["privacy_context"]), backup=backup,
    )


def render_guide(report):
    demo_banner = '<div class="demo-banner" role="note">演示 · 模拟数据。关联回执没有检查或改动这台电脑；本页是手动操作说明。</div>' if report["demo"] else ''
    return Template(GUIDE_TEMPLATE.read_text(encoding="utf-8")).substitute(
        demo_banner=demo_banner,
        generated_at=escape(report["generated_at_utc"][:19].replace("T", " ") + " UTC"),
    )


def write_report(output_dir, report):
    output_dir = Path(output_dir).absolute()
    for parent in output_dir.parents:
        if parent.is_symlink():
            raise ValueError("输出路径不能经过符号链接")
    if not output_dir.parent.is_dir():
        raise ValueError("输出目录的父目录必须已存在")
    html = render_html(report)
    guide = render_guide(report)
    output_dir.mkdir(mode=0o700)  # Existing deliveries are never overwritten.
    for name, data in (("report.html", html), ("guide.html", guide), ("report.json", json.dumps(report, ensure_ascii=False, indent=2))):
        descriptor = os.open(output_dir / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as file:
            file.write(data)
    return output_dir / "report.html"


def hosts_label(path):
    if path == "/etc/hosts":
        return "/etc/hosts"
    if isinstance(path, str) and path.replace("\\", "/").lower().endswith("/system32/drivers/etc/hosts"):
        return "Windows hosts"
    return "hosts 文件"


def shorten_backup(backup):
    if not isinstance(backup, str) or len(backup) >= 600 or any(char in backup for char in "\r\n\x00"):
        return None
    normalized = backup.replace("\\", "/")
    shortened = re.sub(r"^(?:/Users|[A-Za-z]:/Users)/[^/]+/", "~/", normalized)
    if not shortened.startswith("~/") or shortened == normalized:
        return None
    return shortened


def open_report(path, *, runner=subprocess.run, platform=None):
    plat = platform or sys.platform
    target = str(Path(path).absolute())
    if plat == "darwin":
        argv = ["/usr/bin/open", target]
    elif plat == "win32":
        argv = ["cmd", "/c", "start", "", target]
    else:
        return "unsupported_platform"
    try:
        result = runner(argv, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5, check=False)
        return "opened" if result.returncode == 0 else "failed"
    except (OSError, subprocess.TimeoutExpired):
        return "failed"


def read_input(path):
    if path is None:
        return {}
    path = Path(path)
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 4 * 1024 * 1024:
        raise ValueError("输入需为不超过 4 MiB 的普通 JSON 文件")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError("invalid_shape")
        return value
    except (ValueError, UnicodeError, RecursionError):
        raise ValueError("输入 JSON 无效；不会输出原文") from None


def demo_inputs(now):
    measured = now.isoformat()
    network = {
        "checked_at_utc": measured, "expected_mode": "tun",
        "exit_ip": {"attempts": [{"status": "已观察", "requested_connection_family": 4, "observation": {"ip": "203.0.113.10", "country": "JP"}}]},
        "system_proxy": {"flags": {key: [0] for key in ("HTTPEnable", "HTTPSEnable", "SOCKSEnable", "ProxyAutoConfigEnable", "ProxyAutoDiscoveryEnable")}},
        "environment": {"status": "已观察", "entries": [{"name": "DISABLE_TELEMETRY", "kind": "privacy_preference", "value": "1"}]},
        "shell_files": [{"status": "已观察", "entries": []} for _ in range(8)],
        "system_shell_files": [{"status": "已观察", "entries": []} for _ in range(4)],
        "hosts_file": {"status": "已观察", "matches": []},
        "curl_wget": [{"status": "已观察", "entries": []} for _ in range(2)],
        "claude_settings": {"status": "已观察", "entries": [{"kind": "api_base_url", "configured": True, "route": "custom_host"}]},
        "claude_settings_local": {"status": "已观察", "entries": []},
        "npm_proxy": {"status": "已观察", "entries": []}, "git_proxy": {"status": "已观察", "entries": []},
        "timezone": {"system": {"value": "Asia/Taipei"}, "node_process": {"value": "Asia/Taipei"}},
    }
    browser = {
        "context": {"type": "local-browser", "browser": "Chrome", "profile_confirmed": True},
        "sites": {
            "ipleak": {"checked_at_utc": measured, "completed": True, "country_codes": ["JP"], "public_ips": ["203.0.113.10"]},
            "browserleaks_dns": {"checked_at_utc": measured, "completed": True, "country_codes": ["JP"], "resolver_ips": ["203.0.113.20"]},
            "netcoffee": {"checked_at_utc": measured, "dns": {"completed": True, "state": "leak"}, "webrtc": {"completed": False, "state": "unknown"}},
            "browserleaks_webrtc": {"checked_at_utc": measured, "completed": True, "state": "clear"},
        },
    }
    return network, browser, {"action": "check", "status": "completed"}


def main(argv=None):
    parser = argparse.ArgumentParser(description="依据已记录的质检生成离线 HTML；不运行环境检查。")
    parser.add_argument("--network-json", type=Path)
    parser.add_argument("--browser-json", type=Path)
    parser.add_argument("--run-json", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--expected-country", type=str.upper)
    parser.add_argument("--expected-timezone")
    parser.add_argument("--demo", action="store_true", help="仅生成明确标注模拟数据的预览，不读取真实配置")
    parser.add_argument("--open", action="store_true", help="生成后用本机默认浏览器打开本地 HTML；仅 macOS 与 Windows")
    arguments = parser.parse_args(argv)
    if arguments.demo and any((arguments.network_json, arguments.browser_json, arguments.run_json)):
        parser.error("演示不能混用真实输入")
    if arguments.expected_country and (not re.fullmatch(r"[A-Z]{2}", arguments.expected_country) or arguments.expected_country in {"XX", "ZZ", "EU", "UN"}):
        parser.error("预期地区需为 ISO 两字国家码")
    if arguments.expected_timezone and not re.fullmatch(r"[A-Za-z0-9_+/-]{1,99}", arguments.expected_timezone):
        parser.error("预期时区格式无效")
    try:
        now = datetime.now(timezone.utc)
        values = demo_inputs(now) if arguments.demo else tuple(read_input(path) for path in (arguments.network_json, arguments.browser_json, arguments.run_json))
        report = evaluate(*values, expected_country=arguments.expected_country or ("JP" if arguments.demo else None), expected_timezone=arguments.expected_timezone, now=now, demo=arguments.demo)
        path = write_report(arguments.output_dir, report)
    except (OSError, ValueError, TypeError):
        print("未生成回执：输入或输出路径无效，或交付目录已存在。原有文件未覆盖。", file=sys.stderr)
        return 2
    opening = open_report(path) if arguments.open else "not_requested"
    print(json.dumps({"html": str(path), "guide": str(path.with_name("guide.html")), "json": str(path.with_suffix(".json")), "open_status": opening, "demo": report["demo"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
