#!/usr/bin/env python3
"""Read-only macOS or Windows routing audit; browser leakage tests remain separate."""

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import ipaddress
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import stat
import subprocess
import sys
from urllib.parse import urlsplit


MAX_BYTES = 1024 * 1024
SHELL_FILES = (".zshrc", ".zshenv", ".zprofile", ".bashrc", ".bash_profile", ".profile", ".zlogin", ".bash_login")
WIN_SHELL_FILES = (
    "Documents/PowerShell/Microsoft.PowerShell_profile.ps1",
    "Documents/WindowsPowerShell/Microsoft.PowerShell_profile.ps1",
    ".bashrc", ".bash_profile", ".profile",
)
SYSTEM_SHELL_FILES = ("/etc/zshrc", "/etc/zprofile", "/etc/profile", "/etc/bashrc")
TOOL_CONFIG_FILES = (".curlrc", ".wgetrc")
HOSTS_FILE = "/etc/hosts"
PS_ENV_ASSIGNMENT = re.compile(r"^\s*\$env:([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$")
PROXY_FLAGS = (
    "HTTPEnable", "HTTPSEnable", "SOCKSEnable",
    "ProxyAutoConfigEnable", "ProxyAutoDiscoveryEnable",
)
IP_ENDPOINT = "https://ipinfo.io/json"
ASSIGNMENT = re.compile(r"(?<![\w$])([A-Za-z_][A-Za-z0-9_]*)\s*=\s*")
TOOL_ASSIGNMENT = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+?)\s*$")
PRIVACY_FLAGS = {"DISABLE_TELEMETRY", "DISABLE_ERROR_REPORTING", "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC"}


@dataclass
class CommandResult:
    returncode: int | None
    stdout: str = ""
    error: str | None = None


def run_command(argv, *, cwd, environment, timeout):
    """Do not echo command output or exceptions, which may contain credentials."""
    try:
        result = subprocess.run(
            argv, cwd=cwd, env=dict(environment), stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
            encoding="utf-8", errors="replace", timeout=timeout, check=False,
        )
        if len(result.stdout.encode("utf-8")) > MAX_BYTES:
            return CommandResult(result.returncode, error="output_too_large")
        return CommandResult(result.returncode, result.stdout)
    except subprocess.TimeoutExpired:
        return CommandResult(None, error="timeout")
    except OSError:
        return CommandResult(None, error="unavailable")


def relevant_name(name):
    if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,127}", name):
        return False
    lower = name.lower()
    return "proxy" in lower or lower.startswith(("anthropic", "claude")) or name.upper() in PRIVACY_FLAGS


def url_target(value):
    """Expose only scheme, hostname and port; omit auth, path and query."""
    if not isinstance(value, str) or not value or len(value) > MAX_BYTES:
        return None
    if any(char in value for char in ("$", "`", "\n", "\r", "\\")):
        return None
    try:
        parsed = urlsplit(value if "://" in value else "//" + value)
        scheme = parsed.scheme.lower() or "unspecified"
        if scheme not in {"http", "https", "socks", "socks4", "socks4a", "socks5", "socks5h", "unspecified"}:
            return None
        host = parsed.hostname
        port = parsed.port
        if not host or not re.fullmatch(r"[A-Za-z0-9._:-]+", host):
            return None
        host = host.lower()
        display = "[" + host + "]" if ":" in host else host
        return {
            "scheme": scheme, "host": host,
            "port": port, "display": f"{scheme}://{display}" + (f":{port}" if port is not None else ""),
        }
    except (ValueError, TypeError):
        return None


def describe_value(name, value, *, candidate=False, origin="启动文件候选；不代表当前已生效"):
    result = {"name": name, "status": "已观察", "value": "已隐藏"}
    if candidate:
        result["origin"] = origin
    lower = name.lower()
    if name.upper() in PRIVACY_FLAGS:
        result.update(kind="privacy_preference", configured=value is not None, value=str(value) if str(value) in {"0", "1"} else "已隐藏；未解析为 0/1")
        return result
    if re.search(r"key|token|auth|secret|password|credential|cookie", lower):
        result["kind"] = "credential_or_sensitive"
        result["configured"] = bool(value)
        return result
    is_base = bool(re.search(r"anthropic.*base.*url", lower))
    is_proxy = lower in {"http_proxy", "https_proxy", "all_proxy", "proxy", "https-proxy", "http.proxy", "https.proxy"}
    if is_base or is_proxy:
        result["kind"] = "api_base_url" if is_base else "proxy"
        if value is None or (isinstance(value, str) and value.strip().lower() in {"", "null", "undefined", "none"}):
            result.update(configured=False, value="未配置")
            return result
        result["configured"] = True
        target = url_target(value)
        if target:
            result["target"] = target["display"]
            if is_base:
                result["route"] = "official_api_host" if target["host"] == "api.anthropic.com" else "custom_host"
                result["status"] = "待核实" if result["route"] == "custom_host" else "已观察"
                result["next_step"] = "确认该入口是否仍需要；自定义入口不自动等于异常"
        else:
            result.update(status="待核实", value="已隐藏；不能安全解析或含变量／命令表达式")
        return result
    result.update(kind="related_setting", configured=bool(value))
    return result


def read_home_file(home, relative):
    """Fixed files only. Skip symlinks, oversized files and non-regular files."""
    path = home / relative
    try:
        for current in (home, *[home.joinpath(*Path(relative).parts[:i]) for i in range(1, len(Path(relative).parts) + 1)]):
            if stat.S_ISLNK(current.lstat().st_mode):
                return "symlink_skipped", None
        return read_regular_file(path)
    except FileNotFoundError:
        return "absent", None
    except (OSError, UnicodeError):
        return "unreadable", None


def read_regular_file(path):
    """Open one fixed file; never follow a final symlink; cap the size read."""
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0))
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode):
            return "not_regular", None
        if info.st_size > MAX_BYTES:
            return "too_large", None
        with os.fdopen(descriptor, "rb", closefd=False) as source:
            data = source.read(MAX_BYTES + 1)
    finally:
        os.close(descriptor)
    if len(data) > MAX_BYTES:
        return "too_large", None
    return "read", data.decode("utf-8")


def read_system_file(path):
    """Fixed system files only. Ancestors are OS-managed; only the file itself is checked."""
    try:
        if stat.S_ISLNK(os.lstat(path).st_mode):
            return "symlink_skipped", None
        return read_regular_file(path)
    except FileNotFoundError:
        return "absent", None
    except (OSError, UnicodeError):
        return "unreadable", None


def shell_candidates(content, origin="启动文件候选；不代表当前已生效"):
    entries = []
    for number, line in enumerate(content.splitlines(), 1):
        if line.lstrip().startswith("#"):
            continue
        powershell = PS_ENV_ASSIGNMENT.match(line)
        if powershell and relevant_name(powershell[1]):
            raw = powershell[2].strip()
            if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in {'"', "'"}:
                raw = raw[1:-1]
            entry = describe_value(powershell[1], raw, candidate=True, origin=origin)
            entry["line"] = number
            entries.append(entry)
            continue
        # Tokenize text only: no sourcing, expansion, or command substitution.
        try:
            tokens = shlex.split(line, comments=True, posix=True)
        except ValueError:
            tokens = []
        seen = set()
        for token in tokens:
            match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)=(.*)$", token, re.DOTALL)
            if match and relevant_name(match[1]):
                entry = describe_value(match[1], match[2], candidate=True, origin=origin)
                entry["line"] = number
                entries.append(entry)
                seen.add(match[1])
        # Unparseable expressions still count as candidates; never print the line.
        for match in ASSIGNMENT.finditer(line.split("#", 1)[0]):
            name = match[1]
            if relevant_name(name) and name not in seen:
                entry = describe_value(name, "${unresolved}", candidate=True, origin=origin)
                entry["line"] = number
                entry["status"] = "待核实"
                entries.append(entry)
                seen.add(name)
    return entries


def scan_shell_files(home, names=SHELL_FILES):
    files = []
    for relative in names:
        state, content = read_home_file(home, relative)
        files.append({
            "file": "~/" + relative, "read_state": state,
            "status": "已观察" if state in {"read", "absent"} else "未检测",
            "entries": shell_candidates(content) if state == "read" else [],
        })
    return files


def scan_system_shell_files(files=SYSTEM_SHELL_FILES):
    results = []
    for path in files:
        state, content = read_system_file(path)
        results.append({
            "file": path, "read_state": state,
            "status": "已观察" if state in {"read", "absent"} else "未检测",
            "entries": shell_candidates(content, origin="系统启动文件候选；不代表当前已生效") if state == "read" else [],
        })
    return results


def hosts_domain(token):
    """Return the host only when a token is a domain bearing an anthropic/claude label."""
    host = token.strip().lower().split("/")[0]
    if not host or ":" in host or "@" in host or "." not in host:
        return None
    labels = host.split(".")
    if not ({"anthropic", "claude"} & set(labels)):
        return None
    if not all(re.fullmatch(r"[a-z0-9-]{1,63}", label) for label in labels):
        return None
    return host


def scan_hosts_file(path=HOSTS_FILE):
    state, content = read_system_file(path)
    result = {"file": path, "read_state": state, "matches": []}
    if state == "read":
        for number, line in enumerate(content.splitlines(), 1):
            if line.lstrip().startswith("#"):
                continue
            for token in line.split():
                domain = hosts_domain(token)
                if domain:
                    # Only the domain is reported; the mapped address stays hidden.
                    result["matches"].append({"line": number, "domain": domain})
        result["status"] = "待核实" if result["matches"] else "已观察"
        result["note"] = "仅静态文本匹配；映射不一定生效，也不包含代理客户端的分流规则或 DNS 覆盖"
    else:
        result["status"] = "未检测"
    return result


def tool_config_candidates(content):
    entries = []
    for number, line in enumerate(content.splitlines(), 1):
        if line.lstrip().startswith("#"):
            continue
        match = TOOL_ASSIGNMENT.match(line)
        if not match or not relevant_name(match[1]):
            continue
        entry = describe_value(match[1], match[2].strip("\"'"), candidate=True, origin="工具配置文件候选；不代表当前已生效")
        entry["line"] = number
        entries.append(entry)
    return entries


def scan_curl_wget(home):
    results = []
    for relative in TOOL_CONFIG_FILES:
        state, content = read_home_file(home, relative)
        entries = tool_config_candidates(content) if state == "read" else []
        results.append({
            "file": "~/" + relative, "read_state": state,
            "status": "待核实" if any(entry.get("configured") for entry in entries)
            else ("已观察" if state in {"read", "absent"} else "未检测"),
            "entries": entries,
        })
    return results


def scan_settings(home, relative=".claude/settings.json"):
    state, content = read_home_file(home, relative)
    result = {"file": "~/" + relative, "read_state": state, "entries": []}
    result["status"] = "已观察" if state in {"read", "absent"} else "未检测"
    if state != "read":
        return result
    try:
        def unique_object(pairs):
            item = {}
            for key, value in pairs:
                if key in item:
                    raise ValueError("duplicate_key")
                item[key] = value
            return item
        settings = json.loads(content, object_pairs_hook=unique_object)
        if not isinstance(settings, dict) or not isinstance(settings.get("env", {}), dict):
            raise ValueError("unexpected_shape")
        result["entries"] = [describe_value(key, value) for key, value in sorted(settings.get("env", {}).items()) if relevant_name(key)]
    except (ValueError, TypeError, RecursionError):
        result.update(read_state="invalid_json_or_shape", status="未检测")
    return result


def query(tool, arguments, *, home, environment, runner, finder, timeout=8):
    executable = finder(tool)
    if not executable:
        return CommandResult(None, error="command_missing")
    query_environment = {key: value for key, value in environment.items() if tool not in {"node", "npm"} or key != "NODE_OPTIONS"}
    return runner([executable, *arguments], cwd=home, environment=query_environment, timeout=timeout)


def query_error(result):
    return {"status": "未检测", "reason": result.error or "command_failed", "returncode": result.returncode}


def interpret_proxy_flags(flags, expected_mode):
    enabled = [key for key, values in flags.items() if values and 1 in values]
    if all(value is None for value in flags.values()):
        return {"status": "未检测", "flags": flags, "reason": "no_recognized_flags"}
    if enabled and expected_mode in {"tun", "direct"}:
        note = "代理开关与预期模式可能不一致；核对客户端后再决定是否属于残留"
        status = "待核实"
    elif enabled and expected_mode == "system-proxy":
        note, status = "已开启；与使用系统代理的预期一致，但尚未验证实际出口", "已观察"
    elif enabled:
        note, status = "已开启；需先明确预期模式，不自动判为残留", "待核实"
    elif expected_mode == "system-proxy":
        note, status = "未观察到开启的系统代理；与预期可能不一致，需核对实际服务及客户端", "待核实"
    else:
        note, status = "已返回的开关没有启用；缺失字段未知，也不能证明直连或无泄漏", "已观察"
    return {"status": status, "flags": flags, "enabled": enabled, "interpretation": note}


def system_proxy(context, expected_mode):
    response = query("scutil", ["--proxy"], **context)
    if response.error or response.returncode != 0:
        return query_error(response)
    flags = {}
    for name in PROXY_FLAGS:
        values = sorted({int(value) for value in re.findall(r"\b" + name + r"\s*:\s*([01])\b", response.stdout)})
        flags[name] = values if values else None
    return interpret_proxy_flags(flags, expected_mode)


def windows_proxy_flags(snapshot):
    """Map a WinINet snapshot to the same switches. Never copy server strings."""
    if not isinstance(snapshot, dict):
        return None
    enable = snapshot.get("ProxyEnable")
    if enable not in {0, 1}:
        return None
    flags = {
        "HTTPEnable": [enable],
        "HTTPSEnable": [enable],
        "SOCKSEnable": [enable],
        "ProxyAutoConfigEnable": [1 if snapshot.get("AutoConfigURL") else 0],
    }
    detect = snapshot.get("AutoDetect")
    if detect in {0, 1}:
        flags["ProxyAutoDiscoveryEnable"] = [detect]
    return flags


def read_wininet_proxy():
    """Read only on/off switches. ProxyServer can contain credentials and is ignored."""
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Internet Settings") as key:
            def read_value(name):
                try:
                    return winreg.QueryValueEx(key, name)[0]
                except FileNotFoundError:
                    return None
            enable = read_value("ProxyEnable")
            detect = read_value("AutoDetect")
            pac = read_value("AutoConfigURL")
    except (OSError, ImportError, ValueError):
        return None
    return {
        "ProxyEnable": enable if enable in {0, 1} else None,
        "AutoConfigURL": bool(pac),
        "AutoDetect": detect if detect in {0, 1} else None,
    }


def npm_proxy(context):
    entries = []
    for key in ("proxy", "https-proxy"):
        response = query("npm", ["config", "get", key, "--offline", "--logs-max=0", "--update-notifier=false"], **context)
        if response.error or response.returncode != 0:
            entries.append({"name": key, **query_error(response)})
        else:
            entries.append(describe_value(key, response.stdout.strip()))
    return {"entries": entries, "status": "未检测" if any(item["status"] == "未检测" for item in entries) else "已观察"}


def git_proxy(context):
    response = query("git", ["config", "--global", "--null", "--get-regexp", r"^(http|https)(\..*)?\.proxy$"], **context)
    if response.error or response.returncode not in {0, 1}:
        return query_error(response)
    # Git exit 1 with an empty response means no matching configuration keys.
    if response.returncode == 1:
        if response.stdout:
            return {"status": "未检测", "reason": "unexpected_git_response"}
        return {"status": "已观察", "entries": []}
    entries = []
    for record in response.stdout.split("\0"):
        if not record:
            continue
        name, separator, value = record.partition("\n")
        if not separator:
            return {"status": "未检测", "reason": "unexpected_git_response"}
        scoped = re.fullmatch(r"(http|https)\.(.+)\.proxy", name)
        if name in {"http.proxy", "https.proxy"}:
            entry = describe_value(name, value)
        elif scoped:
            entry = describe_value(scoped[1] + ".proxy", value)
            entry["scope"] = "URL 定向配置"
            target = url_target(scoped[2])
            entry["scope_target"] = target["display"] if target else "已隐藏；不能安全解析"
        else:
            return {"status": "未检测", "reason": "unexpected_git_key"}
        entries.append(entry)
    return {"status": "已观察", "entries": entries}


def short_metadata(value):
    if not isinstance(value, str) or len(value) > 180 or any(ord(char) < 32 for char in value):
        return None
    return value or None


def normalize_ipinfo(data):
    if not isinstance(data, dict) or not isinstance(data.get("ip"), str):
        raise ValueError("invalid_response")
    address = ipaddress.ip_address(data.get("ip", ""))
    if not address.is_global:
        raise ValueError("not_public_ip")
    geo = data.get("geo", {})
    as_data = data.get("as", {})
    geo = geo if isinstance(geo, dict) else {}
    as_data = as_data if isinstance(as_data, dict) else {}
    return {
        "ip": str(address), "reported_ip_family": address.version,
        "country": short_metadata(data.get("country") or geo.get("country_code") or geo.get("country")),
        "city": short_metadata(data.get("city") or geo.get("city")),
        "org": short_metadata(data.get("org") or as_data.get("name") or data.get("as_name")),
        "asn": short_metadata(as_data.get("asn") or data.get("asn")),
    }


def exit_ip(context, online):
    if not online:
        return {"status": "未检测", "reason": "online_not_requested", "attempts": []}
    attempts = []
    for family in (4, 6):
        response = query(
            "curl", ["-q", f"-{family}", "-fsS", "--proto", "=https", "--connect-timeout", "5", "--max-time", "15", "--max-filesize", str(MAX_BYTES), IP_ENDPOINT],
            timeout=18, **context,
        )
        item = {"requested_connection_family": family, "endpoint": IP_ENDPOINT}
        if response.error or response.returncode != 0:
            item.update(query_error(response))
        else:
            try:
                data = normalize_ipinfo(json.loads(response.stdout))
                item.update(status="已观察", observation=data)
            except (ValueError, TypeError, RecursionError):
                item.update(status="未检测", reason="invalid_or_nonpublic_response")
        attempts.append(item)
    return {
        "status": "已观察" if any(item["status"] == "已观察" for item in attempts) else "未检测",
        "attempts": attempts,
        "limitations": "仅该次终端查询出口；不证明浏览器／Claude 路由、长期稳定或 IPv6 无泄漏。代理连接地址族可能不同于返回 IP。",
    }


def default_hosts_path(platform):
    if platform == "win32":
        root = os.environ.get("SystemRoot") or os.environ.get("WINDIR") or r"C:\Windows"
        return str(Path(root) / "System32" / "drivers" / "etc" / "hosts")
    return HOSTS_FILE


def timezone_context(context, platform="darwin"):
    def zone(value):
        value = value.strip() if isinstance(value, str) else ""
        if value and len(value) < 100 and re.fullmatch(r"[A-Za-z0-9_+/-]+", value):
            return value
        return None
    system = {"status": "未检测"}
    if platform == "win32":
        response = query("tzutil", ["/g"], **context)
        if not response.error and response.returncode == 0:
            name = response.stdout.strip()
            if name and len(name) < 80 and re.fullmatch(r"[A-Za-z0-9_ ()+-]+", name):
                system = {"status": "已观察", "windows_id": name, "note": "这是 Windows 时区 ID，不是 IANA 名称"}
    else:
        response = query("readlink", ["/etc/localtime"], **context)
        if not response.error and response.returncode == 0:
            _, marker, tail = response.stdout.strip().partition("zoneinfo/")
            if marker and zone(tail):
                system = {"status": "已观察", "value": zone(tail)}
    node_context = {**context, "environment": {key: value for key, value in context["environment"].items() if key != "NODE_OPTIONS"}}
    response = query("node", ["-e", "console.log(Intl.DateTimeFormat().resolvedOptions().timeZone)"], **node_context)
    node = {"status": "未检测"}
    if not response.error and response.returncode == 0 and zone(response.stdout):
        node = {"status": "已观察", "value": zone(response.stdout)}
    value = context["environment"].get("TZ")
    return {
        "system": system, "node_process": node,
        "tz_override_present": bool(value), "tz_override": zone(value),
        "note": "只读上下文，不更改系统；Node 查询未加载 NODE_OPTIONS，不代替实际 Claude 会话的进程时区。",
    }


def collect_report(home, environment, *, online=False, expected_mode="unknown", runner=run_command, finder=shutil.which, system_files=None, hosts_path=None, platform=None, windows_proxy=None, shell_files=None):
    platform = platform or sys.platform
    if platform not in {"darwin", "win32"}:
        raise ValueError("此检查脚本只支持 macOS 与 Windows")
    if shell_files is None:
        shell_files = WIN_SHELL_FILES if platform == "win32" else SHELL_FILES
    if system_files is None:
        system_files = () if platform == "win32" else SYSTEM_SHELL_FILES
    if hosts_path is None:
        hosts_path = default_hosts_path(platform)
    home = Path(home).absolute()
    context = {"home": home, "environment": environment, "runner": runner, "finder": finder}
    if platform == "win32":
        flags = windows_proxy_flags(read_wininet_proxy() if windows_proxy is None else windows_proxy)
        proxy_report = interpret_proxy_flags(flags, expected_mode) if flags else {"status": "未检测", "reason": "unavailable", "flags": {}}
    else:
        proxy_report = system_proxy(context, expected_mode)
    env_entries = [describe_value(key, value) for key, value in sorted(environment.items()) if relevant_name(key)]
    report = {
        "schema_version": 2, "mode": "read-only", "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "expected_mode": expected_mode,
        "exit_ip": exit_ip(context, online),
        "browser_tests": {
            "ipleak": {"status": "未检测", "url": "https://ipleak.net/", "next_step": "在已确认的本地浏览器读取出口地区与公网 IP"},
            "webrtc": {"status": "未检测", "url": "https://browserleaks.com/webrtc", "next_step": "在实际使用的浏览器及 profile 运行页面测试"},
            "dns": {"status": "未检测", "url": "https://browserleaks.com/dns", "next_step": "在同一实际浏览器等待 DNS 测试完成"},
            "netcoffee": {"status": "未检测", "url": "https://ip.net.coffee/claude/", "next_step": "分别等待 DNS 与 WebRTC UDP 检测完成"},
        },
        "system_proxy": proxy_report,
        "timezone": timezone_context(context, platform),
        "environment": {"status": "已观察", "entries": env_entries},
        "shell_files": scan_shell_files(home, shell_files),
        "system_shell_files": scan_system_shell_files(system_files),
        "profile_scan": {"platform": platform, "user_files": len(shell_files), "system_files": len(system_files)},
        "hosts_file": scan_hosts_file(hosts_path),
        "curl_wget": scan_curl_wget(home),
        "npm_proxy": npm_proxy(context),
        "git_proxy": git_proxy(context),
        "claude_settings": scan_settings(home, ".claude/settings.json"),
        "claude_settings_local": scan_settings(home, ".claude/settings.local.json"),
        "limitations": [
            "只读检查；不修改代理、IPv6、浏览器或账号，不输出完整配置、token、代理密码或命令错误原文。",
            "仅当前进程环境与该平台的固定已知文件（系统 hosts、启动文件、~/.curlrc）；项目内配置、编辑器、托管策略、shell 引用的其他文件未覆盖。",
            "第三方 IP 标签／评分不能预测账号封禁；缺失或失败结果不算通过。",
        ],
    }
    if environment.get("CLAUDE_CONFIG_DIR"):
        for key in ("claude_settings", "claude_settings_local"):
            report[key]["custom_config_dir_present"] = True
            report[key]["scope_note"] = "存在自定义配置目录；本次仅检查默认文件，实际生效配置待核实"
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description="只读脱敏检查 Claude 路由相关配置；不会修复或执行浏览器测试。")
    parser.add_argument("--online", action="store_true", help="对固定 IPinfo HTTPS 地址各尝试一次 IPv4/IPv6 请求")
    parser.add_argument("--expected-mode", choices=("unknown", "tun", "system-proxy", "direct"), default="unknown", help="只用于判读，不切换路由")
    arguments = parser.parse_args(argv)
    if sys.platform not in {"darwin", "win32"}:
        print("此检查脚本只支持 macOS 与 Windows；其他平台需另行核实。", file=sys.stderr)
        return 2
    report = collect_report(Path.home(), dict(os.environ), online=arguments.online, expected_mode=arguments.expected_mode)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0  # Collection completed; individual states, not exit 0, determine coverage.


if __name__ == "__main__":
    raise SystemExit(main())
