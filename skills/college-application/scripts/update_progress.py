#!/usr/bin/env python3
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def now_iso():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--request-id", required=True)
    parser.add_argument(
        "--status",
        required=True,
        choices=("working", "waiting-user", "completed", "failed"),
    )
    parser.add_argument("--step", required=True)
    parser.add_argument("--message", required=True)
    parser.add_argument("--percent", type=int, required=True)
    args = parser.parse_args()

    progress = {
        "request_id": args.request_id,
        "status": args.status,
        "step": args.step,
        "message": args.message,
        "percent": max(0, min(100, args.percent)),
        "heartbeat_at": now_iso(),
    }
    workspace = Path(args.workspace).expanduser().resolve()
    path = workspace / "agent-progress.json"
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(progress, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    temporary.replace(path)
    print(json.dumps(progress, ensure_ascii=False))


if __name__ == "__main__":
    main()
