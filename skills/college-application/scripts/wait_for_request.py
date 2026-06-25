#!/usr/bin/env python3
import argparse
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path


def now_iso():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def parse_iso(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def age_seconds(value):
    parsed = parse_iso(value)
    if parsed is None:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - parsed.astimezone(timezone.utc)).total_seconds()


def read_json(path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return default


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    temporary.replace(path)


def beat_listener(workspace, status="listening", message="Agent 正在监听网页任务"):
    """写入在线心跳，让页面诚实地显示 Agent 在不在线。"""
    write_json(
        workspace / "agent-listener.json",
        {
            "status": status,
            "message": message,
            "pid": os.getpid(),
            "heartbeat_at": now_iso(),
        },
    )


# 同一个任务最多可被重新领取的次数，超过后判定为反复掉线，直接标记失败。
MAX_RECLAIM = 2


def reclaim_stale(workspace, reclaim_after):
    """把心跳已过期的 in-progress 任务移回 pending；超过重试上限则直接标记失败。"""
    in_progress = workspace / "requests" / "in-progress"
    pending = workspace / "requests" / "pending"
    failed = workspace / "requests" / "failed"
    progress = read_json(workspace / "agent-progress.json", {})
    for source in sorted(in_progress.glob("*.json")):
        request = read_json(source, {})
        # 只回收心跳确实过期的任务；正在被本进程处理的不动。
        if progress.get("request_id") == request.get("id"):
            age = age_seconds(progress.get("heartbeat_at"))
        else:
            age = age_seconds(request.get("claimed_at"))
        if age is None or age <= reclaim_after:
            continue

        reclaim_count = int(request.get("reclaim_count", 0)) + 1
        request["reclaim_count"] = reclaim_count
        request["reclaimed_at"] = now_iso()

        if reclaim_count > MAX_RECLAIM:
            # 反复掉线，停止自动重试，让用户在网页看到明确失败状态。
            request["status"] = "failed"
            request["failed_at"] = now_iso()
            request["reason"] = (
                f"Agent 反复掉线（{reclaim_count} 次未在心跳窗口内汇报进度），"
                "已停止自动重试。请回到 Claude Code 检查会话或点击网页上的“重新排队”。"
            )
            destination = failed / source.name
            write_json(source, request)
            try:
                os.replace(source, destination)
            except FileNotFoundError:
                continue
            write_json(
                workspace / "agent-progress.json",
                {
                    "request_id": request["id"],
                    "status": "failed",
                    "step": "failed",
                    "message": request["reason"],
                    "percent": 100,
                    "heartbeat_at": now_iso(),
                },
            )
            continue

        request["status"] = "pending"
        destination = pending / source.name
        write_json(source, request)
        try:
            os.replace(source, destination)
        except FileNotFoundError:
            continue
        write_json(
            workspace / "agent-progress.json",
            {
                "request_id": request["id"],
                "status": "queued",
                "step": "等待 Agent",
                "message": (
                    f"检测到上一个 Agent 已掉线，任务已重新排队"
                    f"（第 {reclaim_count}/{MAX_RECLAIM} 次重试）"
                ),
                "percent": 10,
                "heartbeat_at": now_iso(),
            },
        )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--timeout", type=int, default=3600)
    parser.add_argument("--poll", type=float, default=1.0)
    parser.add_argument(
        "--reclaim-after",
        type=float,
        default=180,
        help="in-progress 任务心跳超过该秒数则自动重新排队",
    )
    parser.add_argument(
        "--loop",
        action="store_true",
        default=False,
        help="实验性：领取任务后继续监听不退出。默认 False，因为 Claude Code 的 Bash 工具是阻塞调用，"
             "进程不退出 Agent 就读不到 stdout 上的任务 JSON。除非你知道自己在做什么，否则不要开。",
    )
    args = parser.parse_args()

    workspace = Path(args.workspace).expanduser().resolve()
    pending = workspace / "requests" / "pending"
    in_progress = workspace / "requests" / "in-progress"
    deadline = time.monotonic() + args.timeout
    loop_mode = args.loop
    tasks_claimed = 0

    # 启动时先回收掉死任务，再开始监听。
    reclaim_stale(workspace, args.reclaim_after)
    beat_listener(workspace, message="Agent 常驻监听已启动" if loop_mode else "Agent 正在监听网页任务")

    while time.monotonic() < deadline:
        for source in sorted(pending.glob("*.json")):
            destination = in_progress / source.name
            try:
                os.replace(source, destination)
            except FileNotFoundError:
                continue
            request = json.loads(destination.read_text(encoding="utf-8"))
            request["status"] = "in-progress"
            request["claimed_at"] = now_iso()
            write_json(destination, request)
            # 只写 claimed，不伪造 working/5%。
            # 真正的 working 状态由领到任务的 Agent 调 update_progress.py 自己刷。
            # 这样心跳窗口能区分"Agent 没收到"和"Agent 在干活"。
            write_json(
                workspace / "agent-progress.json",
                {
                    "request_id": request["id"],
                    "status": "claimed",
                    "step": "claimed",
                    "message": "等待器已领取任务并交给 Agent，等待 Agent 开始处理",
                    "percent": 0,
                    "heartbeat_at": now_iso(),
                },
            )
            tasks_claimed += 1
            beat_listener(
                workspace,
                status="busy",
                message=f"Agent 正在处理任务 {request['id']}（已领 {tasks_claimed} 个）",
            )
            # 输出任务，flush 确保实时可读
            print(json.dumps(request, ensure_ascii=False), flush=True)

            if not loop_mode:
                return

            # 常驻模式：继续监听下一个任务
            beat_listener(workspace, message=f"Agent 处理完任务，继续监听（已领 {tasks_claimed} 个）")

        beat_listener(workspace)
        time.sleep(args.poll)

    # 超时退出
    beat_listener(workspace, status="offline", message=f"监听器已超时退出，共领取 {tasks_claimed} 个任务")
    raise SystemExit(f"timeout: claimed {tasks_claimed} tasks")


if __name__ == "__main__":
    main()
