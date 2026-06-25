#!/usr/bin/env python3
import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path


def now_iso():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    temporary.replace(path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--request-id", required=True)
    parser.add_argument("--reason", required=True)
    args = parser.parse_args()

    workspace = Path(args.workspace).expanduser().resolve()
    request_path = (
        workspace / "requests" / "in-progress" / f"{args.request_id}.json"
    )
    if not request_path.exists():
        raise SystemExit(f"in-progress request not found: {args.request_id}")
    request = read_json(request_path)
    request.update(status="failed", failed_at=now_iso(), reason=args.reason)
    write_json(request_path, request)
    os.replace(
        request_path,
        workspace / "requests" / "failed" / f"{args.request_id}.json",
    )

    state_path = workspace / "state.json"
    state = read_json(state_path)
    state.setdefault("requests", {})[request.get("dedup_key", request["type"])] = "failed"
    # 与 complete_request.py 同步：跨"任务失败"事件也要让 version +1。
    state["version"] = int(state.get("version", 1) or 1) + 1
    state["updated_at"] = now_iso()
    write_json(state_path, state)
    write_json(
        workspace / "agent-progress.json",
        {
            "request_id": request["id"],
            "status": "failed",
            "step": "failed",
            "message": args.reason,
            "percent": 100,
            "heartbeat_at": now_iso(),
        },
    )
    print(json.dumps({"ok": True, "request": request}, ensure_ascii=False))


if __name__ == "__main__":
    main()
