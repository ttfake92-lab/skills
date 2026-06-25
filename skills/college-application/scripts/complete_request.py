#!/usr/bin/env python3
import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse


def now_iso():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def read_json(path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    temporary.replace(path)


def validate_research(research):
    sources = {source.get("id"): source for source in research.get("sources", [])}
    for source_id, source in sources.items():
        url = source.get("url", "")
        parsed = urlparse(url)
        if not source_id or parsed.scheme not in ("http", "https") or not parsed.netloc:
            raise ValueError(f"invalid source: {source_id}")
        if not source.get("publisher") or not source.get("verified_at"):
            raise ValueError(f"incomplete source metadata: {source_id}")

    referenced = set()
    for collection in ("major_clusters", "admission_records", "applications"):
        for item in research.get(collection, []):
            referenced.update(item.get("source_ids", []))
            # deep_dive 内挂的来源也要纳入校验
            deep = item.get("deep_dive") or {}
            referenced.update(deep.get("source_ids", []))
    missing = sorted(source_id for source_id in referenced if source_id not in sources)
    if missing:
        raise ValueError(f"missing source records: {', '.join(missing)}")


def merge_deep_dive(existing, result, cluster_id):
    """把 deep_dive 增量结果合并到已有 research.json：
    - 只更新目标簇的 deep_dive 字段，其他簇原样保留
    - 新增的 sources 追加到顶级 sources（按 id 去重）
    缺一个簇 / 缺 deep_dive 字段都视作错误。"""
    existing = existing if existing.get("major_clusters") else None
    if not existing:
        raise ValueError("major_deep_dive 必须基于已存在的 major_research 结果，"
                         "但 research.json 里没有 major_clusters")

    deep = (result.get("deep_dive_payload") or {}).get(cluster_id)
    if not deep:
        raise ValueError(f"deep_dive 结果中未找到 cluster_id={cluster_id} 的 deep_dive_payload")

    merged = dict(existing)
    found = False
    new_clusters = []
    for cluster in existing.get("major_clusters", []):
        if cluster.get("id") == cluster_id:
            cluster = dict(cluster)
            cluster["deep_dive"] = deep
            found = True
        new_clusters.append(cluster)
    if not found:
        raise ValueError(f"deep_dive 目标簇不存在：{cluster_id}")
    merged["major_clusters"] = new_clusters

    # 合并 sources（id 去重，新版本覆盖旧版本）
    by_id = {source["id"]: source for source in existing.get("sources", [])}
    for source in result.get("sources", []):
        by_id[source["id"]] = source
    merged["sources"] = list(by_id.values())
    merged["generated_at"] = now_iso()
    merged["status"] = "ready"
    return merged


def merge_recommendation(existing, result):
    """把 application_recommendation 增量结果合并到已有 research.json：
    - 用新 applications 整体替换 applications（同一批 candidate 输入对应一次完整推荐）
    - 新增 sources 追加去重；methodology 覆盖（其他字段保持原样）"""
    if not existing.get("major_clusters"):
        raise ValueError("application_recommendation 必须基于已存在的 major_research 结果")
    applications = result.get("applications") or []
    if not applications:
        raise ValueError("application_recommendation 结果必须包含至少一条 applications")
    for application in applications:
        if not application.get("source_ids"):
            raise ValueError(f"application {application.get('id')} 缺少 source_ids")
        if not application.get("risk_level"):
            raise ValueError(f"application {application.get('id')} 缺少 risk_level")

    merged = dict(existing)
    merged["applications"] = applications

    by_id = {source["id"]: source for source in existing.get("sources", [])}
    for source in result.get("sources", []):
        by_id[source["id"]] = source
    merged["sources"] = list(by_id.values())

    if result.get("methodology"):
        merged["methodology"] = result["methodology"]
    merged["generated_at"] = now_iso()
    merged["status"] = "ready"
    return merged


def append_event(workspace, event):
    path = workspace / "history" / "events.jsonl"
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(event, ensure_ascii=False) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--request-id", required=True)
    parser.add_argument("--result", required=True)
    args = parser.parse_args()

    workspace = Path(args.workspace).expanduser().resolve()
    request_path = (
        workspace / "requests" / "in-progress" / f"{args.request_id}.json"
    )
    if not request_path.exists():
        raise SystemExit(f"in-progress request not found: {args.request_id}")

    request = read_json(request_path, {})
    result = read_json(Path(args.result).expanduser().resolve(), {})

    if request["type"] == "major_deep_dive":
        # deep_dive 用增量 merge，不整体覆写
        cluster_id = (request.get("payload") or {}).get("cluster_id")
        if not cluster_id:
            raise ValueError("in-progress 的 major_deep_dive 任务缺少 payload.cluster_id")
        existing = read_json(workspace / "research.json", {})
        # 先单独校验 result 自带的 sources 完整性（用一个临时 wrapper）
        validate_research({
            "major_clusters": [{"source_ids": (result.get("deep_dive_payload", {})
                                               .get(cluster_id, {})
                                               .get("source_ids", []))}],
            "admission_records": [],
            "applications": [],
            "sources": result.get("sources", []),
        })
        if not (result.get("deep_dive_payload") or {}).get(cluster_id, {}).get("source_ids"):
            raise ValueError("deep_dive 结果必须挂至少一条 source_ids")
        merged = merge_deep_dive(existing, result, cluster_id)
        write_json(workspace / "research.json", merged)
    elif request["type"] == "application_recommendation":
        existing = read_json(workspace / "research.json", {})
        # 单独校验本次增量自带的 sources 完整性
        validate_research({
            "major_clusters": [],
            "admission_records": [],
            "applications": result.get("applications", []),
            "sources": result.get("sources", []),
        })
        merged = merge_recommendation(existing, result)
        write_json(workspace / "research.json", merged)
    else:
        validate_research(result)
        if result.get("status") == "ready":
            if request["type"] == "major_research" and not result.get("major_clusters"):
                raise ValueError("major research completed without major_clusters")
            if request["type"] == "audit" and not result.get("audit"):
                raise ValueError("audit completed without audit result")
        result["generated_at"] = result.get("generated_at") or now_iso()
        result["status"] = result.get("status") or "ready"
        write_json(workspace / "research.json", result)

    state = read_json(workspace / "state.json", {})
    state.setdefault("requests", {})[request.get("dedup_key", request["type"])] = "completed"
    state["version"] = int(state.get("version", 1) or 1) + 1
    state["updated_at"] = now_iso()
    write_json(workspace / "state.json", state)

    request["status"] = "completed"
    request["completed_at"] = now_iso()
    completed_path = (
        workspace / "requests" / "completed" / f"{args.request_id}.json"
    )
    write_json(request_path, request)
    os.replace(request_path, completed_path)

    append_event(
        workspace,
        {
            "id": f"evt_{int(datetime.now().timestamp() * 1000)}",
            "timestamp": now_iso(),
            "stage": "agent-work",
            "type": "request-completed",
            "summary": f"Agent 已完成任务 {args.request_id}: {request['type']}",
            "version": state.get("version"),
            "related_ids": [args.request_id],
        },
    )
    write_json(
        workspace / "agent-progress.json",
        {
            "request_id": request["id"],
            "status": "completed",
            "step": "completed",
            "message": "真实研究结果已校验并写回页面",
            "percent": 100,
            "heartbeat_at": now_iso(),
        },
    )
    print(json.dumps({"ok": True, "request": request}, ensure_ascii=False))


if __name__ == "__main__":
    main()
