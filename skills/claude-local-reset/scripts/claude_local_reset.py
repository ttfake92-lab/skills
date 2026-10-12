#!/usr/bin/env python3
"""Preview or archive allowlisted Claude state on macOS or Windows; never contact a service."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import stat
import subprocess
import sys
import tempfile
from typing import Any

MAC_DESKTOP_PATHS = (
    "Library/Application Support/Claude",
    "Library/Caches/com.anthropic.claudefordesktop",
    "Library/HTTPStorages/com.anthropic.claudefordesktop",
    "Library/WebKit/com.anthropic.claudefordesktop",
    "Library/Logs/Claude",
    "Library/Preferences/com.anthropic.claudefordesktop.plist",
)
# Kept for callers that index the macOS whitelist. Windows targets are resolved separately.
DESKTOP_PATHS = MAC_DESKTOP_PATHS
WIN_DESKTOP_PATHS = ("AppData/Roaming/Claude",)
MSIX_DATA_RE = re.compile(r"AppData/Local/Packages/Claude_[A-Za-z0-9]+/LocalCache/Roaming/Claude")
MSIX_FAMILY_RE = re.compile(r"Claude_[A-Za-z0-9]+")
CODE_PATHS = (".claude/statsig", ".claude/telemetry", ".claude/.credentials.json", ".claude.json.backup")
CODE_BACKUP_PREFIX = ".claude/backups/.claude.json.backup."
BACKUP_ROOT = "ClaudeLocalResetBackups"
IDENTITY_KEYS = ("userID", "machineID")


def allowed(relative: str) -> bool:
    path = Path(relative)
    if path.is_absolute() or path.as_posix() != relative or ".." in path.parts:
        return False
    if relative in (*MAC_DESKTOP_PATHS, *WIN_DESKTOP_PATHS, *CODE_PATHS, ".claude.json"):
        return True
    if MSIX_DATA_RE.fullmatch(relative):
        return True
    return (
        relative.startswith(CODE_BACKUP_PREFIX)
        and len(path.parts) == 3
        and len(relative) > len(CODE_BACKUP_PREFIX)
    )


def desktop_candidates(home: Path, platform: str) -> list[str]:
    """Return this platform's Desktop whitelist. Installers and 3P profiles are not included."""
    if platform == "darwin":
        return list(MAC_DESKTOP_PATHS)
    if platform != "win32":
        raise ValueError("此辅助脚本只支持 macOS 与 Windows")
    paths = list(WIN_DESKTOP_PATHS)
    packages = home / "AppData" / "Local" / "Packages"
    if packages.is_dir() and not packages.is_symlink():
        for child in sorted(packages.iterdir()):
            if not MSIX_FAMILY_RE.fullmatch(child.name) or child.is_symlink():
                continue
            data = child / "LocalCache" / "Roaming" / "Claude"
            try:
                relative = data.relative_to(home).as_posix()
            except ValueError:
                continue
            if data.is_dir() and not data.is_symlink() and allowed(relative):
                paths.append(relative)
    return paths


def safe_path(home: Path, path: Path) -> Path:
    try:
        relative = path.relative_to(home)
    except ValueError as error:
        raise ValueError("路径不在指定用户目录内") from error
    if not relative.parts or ".." in relative.parts:
        raise ValueError("拒绝用户目录自身或上级路径")
    current = home
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"路径或父目录为符号链接，需单独核实：{path}")
    return path


def fingerprint(path: Path) -> dict[str, Any]:
    info = path.lstat()
    if not (stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode)):
        raise ValueError(f"不是普通文件或目录：{path}")
    result = {
        "device": info.st_dev,
        "inode": info.st_ino,
        "size": info.st_size,
        "mtime_ns": info.st_mtime_ns,
        "kind": "directory" if stat.S_ISDIR(info.st_mode) else "file",
    }
    if path.name == ".claude.json":
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise ValueError("身份配置不是单一普通文件，需单独核实")
        result["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def require_unchanged(path: Path, expected: dict[str, Any], copied: bool = False) -> None:
    actual = fingerprint(path)
    keys = ("sha256", "kind") if copied else tuple(expected)
    if any(actual.get(key) != expected.get(key) for key in keys):
        raise ValueError(f"状态已变化或原件校验不符，停止：{path}")


def no_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("JSON 存在重复键，拒绝改写")
        result[key] = value
    return result


def reject_constant(value: str) -> None:
    raise ValueError("JSON 存在非标准数值，拒绝改写")


def read_json(path: Path) -> dict[str, Any]:
    data = json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=no_duplicate_keys,
        parse_constant=reject_constant,
    )
    if not isinstance(data, dict):
        raise ValueError("JSON 顶层必须是对象")
    return data


def atomic_json(path: Path, data: dict[str, Any]) -> None:
    descriptor, name = tempfile.mkstemp(prefix=".claude-reset-", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2, allow_nan=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def identity_changes(data: dict[str, Any]) -> list[str]:
    present = [key for key in IDENTITY_KEYS if key in data]
    if not present:
        raise ValueError("未发现已知身份键；先核实当前版本，不生成缺失字段")
    for key in present:
        if not isinstance(data[key], str) or not re.fullmatch(r"[0-9a-f]{64}", data[key]):
            raise ValueError(f"{key} 格式与已知版本不同，先核实当前版本")
    return present + [key for key in ("anonymousId", "oauthAccount") if key in data]


def build_plan(home: Path, code_identity: bool = False) -> list[dict[str, Any]]:
    if code_identity and os.environ.get("CLAUDE_CONFIG_DIR"):
        raise ValueError("发现 CLAUDE_CONFIG_DIR；此选项仅覆盖默认目录，需单独核实")
    candidates = desktop_candidates(home, sys.platform)
    fields: list[str] = []
    if code_identity:
        identity = safe_path(home, home / ".claude.json")
        if not identity.is_file():
            raise ValueError("未找到默认 .claude.json；不执行 Code 身份重置")
        fields = identity_changes(read_json(identity))
        candidates.extend(CODE_PATHS)
        backups = safe_path(home, home / ".claude/backups")
        if backups.exists():
            if not backups.is_dir():
                raise ValueError("Code backups 不是目录")
            for child in sorted(backups.iterdir()):
                if child.name.startswith(".claude.json.backup."):
                    if child.is_dir():
                        raise ValueError("发现非文件的 Code 配置备份，需核实")
                    candidates.append(child.relative_to(home).as_posix())
        candidates.append(".claude.json")
    entries = []
    for relative in candidates:
        if not allowed(relative):
            raise ValueError("目标超出白名单")
        path = safe_path(home, home / relative)
        if path.exists():
            entry = {
                "path": relative,
                "operation": "edit" if relative == ".claude.json" else "move",
                "before": fingerprint(path),
            }
            if entry["operation"] == "edit":
                entry["fields"] = fields
            entries.append(entry)
    safe_path(home, home / BACKUP_ROOT)
    return entries


def pids_from_ps(stdout: str, own_pid: str) -> list[str]:
    found = []
    for line in stdout.splitlines():
        parts = line.strip().split(maxsplit=1)
        if len(parts) != 2 or parts[0] == own_pid:
            continue
        command = parts[1]
        if (
            "/Claude.app/" in command
            or "/share/claude/versions/" in command
            or "@anthropic-ai/claude-code/" in command
            or "/.claude-code-router/" in command
            or re.match(r"(?:\S*/)?claude(?:-code(?:-router)?)?(?:\s|$)", command)
            or re.search(r"(?i)(?:^|\\)claude(?:-code(?:-router)?)?\.exe(?:\s|$)", command)
        ):
            found.append(parts[0])
    return found


def pids_from_tasklist(stdout: str, own_pid: str) -> list[str]:
    """Image names only. A node-hosted router will not appear here."""
    found = []
    for line in stdout.splitlines():
        if not line.startswith('"'):
            continue
        try:
            row = next(csv.reader([line]))
        except csv.Error:
            continue
        if len(row) < 2 or not row[1].isdigit() or row[1] == own_pid:
            continue
        if re.fullmatch(r"(?i)claude(?:-code(?:-router)?)?\.exe", row[0]):
            found.append(row[1])
    return found


def require_stopped() -> None:
    own_pid = str(os.getpid())
    if sys.platform == "darwin":
        result = subprocess.run(
            ["/bin/ps", "-axo", "pid=,args="], capture_output=True, text=True, check=True
        )
        found = pids_from_ps(result.stdout, own_pid)
    elif sys.platform == "win32":
        result = subprocess.run(
            ["tasklist", "/FO", "CSV", "/NH"], capture_output=True, text=True, check=True
        )
        found = pids_from_tasklist(result.stdout, own_pid)
    else:
        raise ValueError("此辅助脚本只支持 macOS 与 Windows")
    if found:
        raise ValueError(
            "仍有 Claude 相关进程（PID " + ", ".join(found)
            + "）；请正常退出后重试。脚本不会终止进程。"
        )


def preview(entries: list[dict[str, Any]], platform: str) -> None:
    print("仅列白名单内的现存目标；不输出标识符或凭据：")
    for entry in entries:
        label = "备份并改身份字段" if entry["operation"] == "edit" else "完整归档"
        print(f"- {label}：~/{entry['path']}")
        if entry.get("fields"):
            print("  仅涉及键名：" + ", ".join(entry["fields"]))
    outside = "钥匙串和浏览器不在范围内。" if platform == "darwin" else "安装目录、凭据管理器和浏览器不在范围内。"
    print(f"目标共 {len(entries)} 项。{outside}")


def apply_plan(home: Path, entries: list[dict[str, Any]]) -> Path | None:
    if not entries:
        return None
    require_stopped()
    for entry in entries:
        if not allowed(entry["path"]):
            raise ValueError("目标超出白名单")
        require_unchanged(safe_path(home, home / entry["path"]), entry["before"])
    root = safe_path(home, home / BACKUP_ROOT)
    root.mkdir(mode=0o700, exist_ok=True)
    os.chmod(root, 0o700)
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    batch = root / f"{stamp}-{secrets.token_hex(4)}"
    batch.mkdir(mode=0o700)
    manifest = {"version": 1, "home": str(home), "status": "prepared", "entries": entries}
    atomic_json(batch / "manifest.json", manifest)
    print(f"备份批次：{batch}")
    try:
        for entry in entries:
            source = safe_path(home, home / entry["path"])
            require_unchanged(source, entry["before"])
            saved = safe_path(home, batch / "original" / entry["path"])
            saved.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            if entry["operation"] == "move":
                os.rename(source, saved)
                entry["saved"] = True
                require_unchanged(saved, entry["before"])
            else:
                data = read_json(source)
                fields = identity_changes(data)
                shutil.copyfile(source, saved)
                os.chmod(saved, 0o600)
                require_unchanged(saved, entry["before"], copied=True)
                entry["saved"] = True
                atomic_json(batch / "manifest.json", manifest)
                require_unchanged(source, entry["before"])
                for key in IDENTITY_KEYS:
                    if key in fields:
                        data[key] = secrets.token_hex(32)
                for key in ("anonymousId", "oauthAccount"):
                    data.pop(key, None)
                atomic_json(source, data)
            entry["done"] = True
            atomic_json(batch / "manifest.json", manifest)
        manifest["status"] = "complete"
        atomic_json(batch / "manifest.json", manifest)
    except Exception:
        manifest["status"] = "partial"
        atomic_json(batch / "manifest.json", manifest)
        print(f"部分完成，已停止。请保留原件与清单：{batch}", file=sys.stderr)
        raise
    return batch


def load_restore(home: Path, batch: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    safe_path(home, batch)
    if batch.parent != home / BACKUP_ROOT:
        raise ValueError("仅支持该用户 ClaudeLocalResetBackups 下的直属备份批次")
    manifest = read_json(safe_path(home, batch / "manifest.json"))
    if manifest.get("version") != 1 or manifest.get("home") != str(home):
        raise ValueError("备份版本或所属用户目录不匹配")
    if manifest.get("status") not in {"complete", "partial", "prepared"}:
        raise ValueError("该批次已回滚或回滚中断；不要覆盖，按清单人工检查")
    entries = manifest.get("entries")
    if not isinstance(entries, list):
        raise ValueError("备份清单结构异常")
    selected = []
    seen: set[str] = set()
    for entry in entries:
        relative = entry["path"]
        expected_op = "edit" if relative == ".claude.json" else "move"
        if not allowed(relative) or relative in seen or entry["operation"] != expected_op:
            raise ValueError("清单存在非白名单、重复或异常操作")
        seen.add(relative)
        original = safe_path(home, batch / "original" / relative)
        safe_path(home, home / relative)
        current_saved = safe_path(home, batch / "current-before-restore" / relative)
        if current_saved.exists():
            raise ValueError("已有回滚前新状态归档；停止，避免覆盖")
        if original.exists():
            require_unchanged(original, entry["before"], copied=expected_op == "edit")
            selected.append(entry)
        elif entry.get("saved") or entry.get("done"):
            raise ValueError(f"清单中的原件缺失：{relative}")
    return manifest, selected


def restore_batch(home: Path, batch: Path, apply: bool = False) -> int:
    manifest, entries = load_restore(home, batch)
    for entry in entries:
        print(f"- 恢复原件：~/{entry['path']}；当前新状态将另存")
    if not apply or not entries:
        return len(entries)
    require_stopped()
    manifest["status"] = "restore_started"
    atomic_json(batch / "manifest.json", manifest)
    try:
        for entry in entries:
            destination = safe_path(home, home / entry["path"])
            original = safe_path(home, batch / "original" / entry["path"])
            require_unchanged(original, entry["before"], copied=entry["operation"] == "edit")
            if destination.exists():
                current_saved = safe_path(home, batch / "current-before-restore" / entry["path"])
                current_saved.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
                os.rename(destination, current_saved)
                entry["current_saved"] = True
                atomic_json(batch / "manifest.json", manifest)
            destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            os.rename(original, destination)
            entry["restored"] = True
            atomic_json(batch / "manifest.json", manifest)
        manifest["status"] = "restored"
        atomic_json(batch / "manifest.json", manifest)
    except Exception:
        manifest["status"] = "restore_partial"
        atomic_json(batch / "manifest.json", manifest)
        print(f"回滚部分完成；当前数据与原件均保留在清单所指位置：{batch}", file=sys.stderr)
        raise
    return len(entries)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="预览、归档或回滚 macOS / Windows 上的 Claude 本地状态")
    parser.add_argument("--apply", action="store_true", help="实际执行；默认仅预览")
    parser.add_argument("--code-identity", action="store_true", help="额外重置默认 Claude Code 文件身份")
    parser.add_argument("--restore", type=Path, help="预览或回滚指定备份批次")
    args = parser.parse_args(argv)
    if sys.platform not in {"darwin", "win32"}:
        parser.error("此辅助脚本只支持 macOS 与 Windows")
    if args.restore and args.code_identity:
        parser.error("回滚范围由备份清单决定，不能追加 --code-identity")
    home = Path.home().resolve()
    try:
        if args.restore:
            count = restore_batch(home, args.restore.absolute(), args.apply)
            print(f"{'已回滚' if args.apply else '只读回滚预览'}：{count} 项。")
        else:
            entries = build_plan(home, args.code_identity)
            preview(entries, sys.platform)
            if args.apply:
                batch = apply_plan(home, entries)
                print(f"本地文件操作完成；{'备份：' + str(batch) if batch else '没有现存目标，未写盘'}。")
                if args.code_identity and sys.platform == "darwin":
                    print("CLI 钥匙串凭据未处理；仍需官方注销／登录步骤。")
                elif args.code_identity:
                    print("Windows 的 CLI 凭据文件已随身份选项归档；仍需官方 /logout 撤销服务端登录。")
            else:
                print("只读预览结束，没有修改本地状态。")
        return 0
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        print(f"已停止：{error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
