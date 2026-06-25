#!/usr/bin/env python3
import argparse
import json
import mimetypes
import traceback
from datetime import datetime, timezone
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse


SKILL_DIR = Path(__file__).resolve().parent.parent
APP_TEMPLATE = SKILL_DIR / "assets" / "college-application-template.html"

# 一个 in-progress 任务的进度心跳超过这个秒数，视为 Agent 已掉线，可被重新排队。
INPROGRESS_RECLAIM_SECONDS = 180

# 单个任务最多可被重新排队的次数（自动 reclaim + 手动重试合计）。超过后不再放回 pending。
MAX_RECLAIM = 2


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


def initialize_workspace(workspace):
    workspace.mkdir(parents=True, exist_ok=True)
    (workspace / "history").mkdir(exist_ok=True)
    (workspace / "plans" / "submissions").mkdir(parents=True, exist_ok=True)
    (workspace / "audits").mkdir(exist_ok=True)
    for status in ("pending", "in-progress", "completed", "failed"):
        (workspace / "requests" / status).mkdir(parents=True, exist_ok=True)

    state_path = workspace / "state.json"
    if not state_path.exists():
        write_json(
            state_path,
            {
                "version": 1,
                "stage": "self",
                "profile": {},
                "candidate": {},
                "major_preferences": {},
                "application_order": [],
                "requests": {},
                "submissions": [],
                "audit": None,
                "updated_at": now_iso(),
            },
        )

    research_path = workspace / "research.json"
    if not research_path.exists():
        write_json(
            research_path,
            {
                "status": "not_started",
                "generated_at": None,
                "major_clusters": [],
                "industry_sources": [],
                "admission_records": [],
                "applications": [],
                "sources": [],
                "methodology": None,
                "audit": None,
            },
        )


def append_event(workspace, event):
    event = {
        "id": event.get("id") or f"evt_{int(datetime.now().timestamp() * 1000)}",
        "timestamp": event.get("timestamp") or now_iso(),
        "stage": event.get("stage", "unknown"),
        "type": event.get("type", "updated"),
        "summary": event.get("summary", ""),
        "version": event.get("version"),
        "related_ids": event.get("related_ids", []),
    }
    with (workspace / "history" / "events.jsonl").open("a", encoding="utf-8") as file:
        file.write(json.dumps(event, ensure_ascii=False) + "\n")
    return event


def list_requests(workspace):
    requests = []
    for status in ("pending", "in-progress", "completed", "failed"):
        for path in (workspace / "requests" / status).glob("*.json"):
            request = read_json(path, {})
            request["status"] = status
            requests.append(request)
    return sorted(requests, key=lambda item: item.get("created_at", ""), reverse=True)


def listener_status(workspace):
    """Agent 监听器（wait_for_request.py）写入的在线心跳。"""
    listener = read_json(
        workspace / "agent-listener.json",
        {"status": "offline", "heartbeat_at": None},
    )
    listener["heartbeat_age_seconds"] = age_seconds(listener.get("heartbeat_at"))
    return listener


def move_request(workspace, request, from_status, to_status):
    source = workspace / "requests" / from_status / f"{request['id']}.json"
    destination = workspace / "requests" / to_status / f"{request['id']}.json"
    write_json(source, request)
    source.replace(destination)


def fail_request(workspace, request, from_status, reason):
    """把任务直接标记为 failed，更新进度，让页面看到明确的失败状态。"""
    request["status"] = "failed"
    request["failed_at"] = now_iso()
    request["reason"] = reason
    move_request(workspace, request, from_status, "failed")
    write_json(
        workspace / "agent-progress.json",
        {
            "request_id": request["id"],
            "status": "failed",
            "step": "failed",
            "message": reason,
            "percent": 100,
            "heartbeat_at": now_iso(),
        },
    )
    return request


def requeue_request(workspace, request, from_status, note, percent=10):
    """把一个任务移回 pending，并刷新进度，让监听中的 Agent 能重新领取。
    若超过 MAX_RECLAIM 次重试，则直接标记为失败，避免页面陷入“反复领取又卡死”循环。"""
    reclaim_count = int(request.get("reclaim_count", 0)) + 1
    request["reclaim_count"] = reclaim_count
    if reclaim_count > MAX_RECLAIM:
        return fail_request(
            workspace,
            request,
            from_status,
            f"任务已重试 {reclaim_count - 1} 次仍未完成，已停止自动重排。"
            "请回到 Claude Code 检查 Agent 会话，或在网页上手动重新排队。",
        )

    request["status"] = "pending"
    request["resumed_at"] = now_iso()
    state = read_json(workspace / "state.json", {})
    request["state_version"] = state.get("version")
    request["state_snapshot"] = state
    move_request(workspace, request, from_status, "pending")
    write_json(
        workspace / "agent-progress.json",
        {
            "request_id": request["id"],
            "status": "queued",
            "step": "等待 Agent",
            "message": f"{note}（第 {reclaim_count}/{MAX_RECLAIM} 次重试）",
            "percent": percent,
            "heartbeat_at": now_iso(),
        },
    )
    return request


def candidate_complete(candidate):
    """application_recommendation 入队前的最低必填校验。"""
    if not candidate:
        return False, "缺少 candidate 数据"
    must = ["province", "year", "exam_mode", "subjects"]
    missing = [field for field in must if not candidate.get(field)]
    if missing:
        return False, f"考生信息不全：{', '.join(missing)}"
    # subjects 必须是非空列表或字符串
    subjects = candidate.get("subjects")
    if isinstance(subjects, list) and len(subjects) == 0:
        return False, "请选择选科"
    score = (candidate.get("score") or "").strip() if isinstance(candidate.get("score"), str) else candidate.get("score")
    rank = (candidate.get("rank") or "").strip() if isinstance(candidate.get("rank"), str) else candidate.get("rank")
    if not score and not rank:
        return False, "高考成绩与全省位次至少填一项"
    return True, None


def enqueue_request(workspace, request_type, payload=None):
    """为某类型任务排队。
    去重 key = (type, dedup_key)：默认 dedup_key 与 type 相同；major_deep_dive 用 cluster_id 区分，
    允许多个簇各自排独立任务。已有同 key 任务时尽量复用并恢复，避免重复与卡死。"""
    payload = payload or {}
    state = read_json(workspace / "state.json", {})
    progress = read_json(workspace / "agent-progress.json", {})

    if request_type == "major_deep_dive":
        cluster_id = payload.get("cluster_id")
        if not cluster_id:
            raise ValueError("major_deep_dive 缺少 cluster_id")
        dedup_key = f"major_deep_dive:{cluster_id}"
    elif request_type == "application_recommendation":
        # 入队前做完整性校验，前端避免无效请求落到队列里。
        candidate = (state or {}).get("candidate", {})
        ok, error = candidate_complete(candidate)
        if not ok:
            raise ValueError(error)
        # 至少要有一个用户保留 / 深入的专业簇，否则没有可推荐范围。
        kept = [
            cid for cid, choice in (state.get("major_preferences") or {}).items()
            if choice in ("keep", "deep")
        ]
        if not kept:
            raise ValueError("没有任何保留或深入研究的专业簇，无法生成填报建议")
        dedup_key = "application_recommendation"
        # 把 candidate 与 kept clusters 写进 payload，wait_for_request 输出时 Agent 能直接读。
        payload = {**payload, "candidate": candidate, "kept_cluster_ids": kept}
    else:
        dedup_key = request_type

    for request in list_requests(workspace):
        if request.get("dedup_key", request.get("type")) != dedup_key:
            continue
        status = request.get("status")

        if status == "pending":
            # 已在队列里，无需重复创建。
            return request, False

        if status == "in-progress":
            same_request = progress.get("request_id") == request.get("id")
            waiting_user = same_request and progress.get("status") == "waiting-user"
            heartbeat_age = age_seconds(progress.get("heartbeat_at"))
            stale = (
                same_request
                and heartbeat_age is not None
                and heartbeat_age > INPROGRESS_RECLAIM_SECONDS
            )
            if waiting_user:
                request = requeue_request(
                    workspace,
                    request,
                    "in-progress",
                    "用户已补充信息，任务已重新排队",
                    percent=progress.get("percent", 10),
                )
                return request, False
            if stale:
                request = requeue_request(
                    workspace,
                    request,
                    "in-progress",
                    "上一个 Agent 已掉线，任务已重新排队等待领取",
                )
                return request, False
            # 仍在正常处理中，不重复入队。
            return request, False

        if status == "failed":
            # 失败任务不无脑重排——历史失败是历史，要等用户明确『重试』再动。
            # force=true 是用户的显式重试意图（来自页面的『重新排队』按钮，或 Agent 显式重做）。
            if not payload.get("force"):
                return request, False
            request["reclaim_count"] = 0
            request = requeue_request(
                workspace,
                request,
                "failed",
                "任务已重新排队，等待 Agent 重新处理",
            )
            return request, False

        if status == "completed":
            # 已完成任务默认不重做——避免误触和资源浪费。
            # 用户/前端如果确实想重新跑（比如 profile 变了），显式传 force=true。
            if not payload.get("force"):
                return request, False
            # 显式重做：当作新任务处理（不复用旧 ID），跳出循环让下面 create new request。
            break

    request_id = f"req_{int(datetime.now().timestamp() * 1000)}"
    request = {
        "id": request_id,
        "type": request_type,
        "dedup_key": dedup_key,
        "payload": payload,
        "status": "pending",
        "created_at": now_iso(),
        "state_version": state.get("version"),
        "state_snapshot": state,
    }
    write_json(workspace / "requests" / "pending" / f"{request_id}.json", request)
    listener = listener_status(workspace)
    online = (
        listener.get("status") == "listening"
        and (listener.get("heartbeat_age_seconds") or 1e9) < 10
    )
    write_json(
        workspace / "agent-progress.json",
        {
            "request_id": request_id,
            "status": "queued",
            "step": "等待 Agent",
            "message": (
                "网页数据已传回，Agent 在线，正在等待领取"
                if online
                else "网页数据已传回，但当前没有在线的 Agent。请回到 Claude Code 让该 Skill 继续运行等待器。"
            ),
            "percent": 0,
            "heartbeat_at": now_iso(),
        },
    )
    state.setdefault("requests", {})[dedup_key] = "pending"
    state["updated_at"] = now_iso()
    write_json(workspace / "state.json", state)
    append_event(
        workspace,
        {
            "stage": "agent-work",
            "type": "request-enqueued",
            "summary": f"已创建 Agent 任务 {request_id}: {dedup_key}",
            "version": state.get("version"),
            "related_ids": [request_id],
        },
    )
    return request, True


# 这些字段只属于 Agent，页面 PUT /api/state 不允许覆盖，避免回写被旧快照冲掉。
AGENT_OWNED_KEYS = ("version", "submissions", "audit")
# 比较内容是否变化时忽略的字段。
META_KEYS = ("version", "updated_at")


def merge_state(existing, incoming):
    """合并页面提交的 state：Agent 字段以磁盘为准，version 由服务端独占管理。"""
    state = {**existing, **incoming}
    for key in AGENT_OWNED_KEYS:
        if key in existing:
            state[key] = existing[key]

    existing_requests = existing.get("requests", {})
    incoming_requests = incoming.get("requests", {})
    merged_requests = {**existing_requests, **incoming_requests}
    for key, value in existing_requests.items():
        # 已完成的任务不允许被页面降级回 pending。
        if value in ("completed", "in-progress") and incoming_requests.get(key) == "pending":
            merged_requests[key] = value
    state["requests"] = merged_requests

    # 服务端独占 version：内容有实质变化才 +1，且永不倒退。
    def content(value):
        return {k: v for k, v in value.items() if k not in META_KEYS}

    base_version = int(existing.get("version", 1) or 1)
    if content(state) != content(existing):
        state["version"] = base_version + 1
    else:
        state["version"] = base_version
    state["updated_at"] = now_iso()
    return state


class Handler(BaseHTTPRequestHandler):
    workspace = None

    def log_message(self, format, *args):
        return

    def send_json(self, value, status=200):
        body = json.dumps(value, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_file(self, path):
        if not path.exists() or not path.is_file():
            self.send_error(404)
            return
        body = path.read_bytes()
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def body_json(self):
        length = int(self.headers.get("Content-Length", "0"))
        return json.loads(self.rfile.read(length) or b"{}")

    # 统一异常处理：任何处理错误都回 JSON，而不是断开连接让页面静默卡住。
    def do_GET(self):
        try:
            self.route_get(urlparse(self.path).path)
        except Exception as error:  # noqa: BLE001
            self.fail(error)

    def do_PUT(self):
        try:
            self.route_put(urlparse(self.path).path)
        except Exception as error:  # noqa: BLE001
            self.fail(error)

    def do_POST(self):
        try:
            self.route_post(urlparse(self.path).path)
        except Exception as error:  # noqa: BLE001
            self.fail(error)

    def fail(self, error):
        try:
            self.send_json(
                {"error": str(error) or error.__class__.__name__,
                 "trace": traceback.format_exc().splitlines()[-1]},
                500,
            )
        except Exception:  # noqa: BLE001
            pass

    def route_get(self, path):
        if path in ("/", "/index.html"):
            self.send_file(APP_TEMPLATE)
        elif path == "/api/health":
            self.send_json({"ok": True, "workspace": str(self.workspace)})
        elif path == "/api/state":
            self.send_json(read_json(self.workspace / "state.json", {}))
        elif path == "/api/research":
            self.send_json(read_json(self.workspace / "research.json", {}))
        elif path == "/api/history":
            events_path = self.workspace / "history" / "events.jsonl"
            events = []
            if events_path.exists():
                events = [
                    json.loads(line)
                    for line in events_path.read_text(encoding="utf-8").splitlines()
                    if line.strip()
                ]
            self.send_json(events)
        elif path == "/api/requests":
            self.send_json(list_requests(self.workspace))
        elif path == "/api/agent-listener":
            self.send_json(listener_status(self.workspace))
        elif path == "/api/agent-progress":
            self.send_json(
                read_json(
                    self.workspace / "agent-progress.json",
                    {
                        "status": "idle",
                        "step": "idle",
                        "message": "当前没有 Agent 在处理任务",
                        "percent": 0,
                        "heartbeat_at": None,
                    },
                )
            )
        else:
            self.send_error(404)

    def route_put(self, path):
        if path == "/api/state":
            incoming = self.body_json()
            existing = read_json(self.workspace / "state.json", {})
            state = merge_state(existing, incoming)
            write_json(self.workspace / "state.json", state)
            self.send_json(state)
            return
        if path == "/api/research":
            research = self.body_json()
            research["generated_at"] = research.get("generated_at") or now_iso()
            write_json(self.workspace / "research.json", research)
            self.send_json(research)
            return
        self.send_error(404)

    def route_post(self, path):
        payload = self.body_json()
        if path == "/api/events":
            self.send_json(append_event(self.workspace, payload), 201)
            return
        if path == "/api/requests":
            request_type = payload.get("type")
            allowed = (
                "major_research",
                "major_deep_dive",
                "application_recommendation",
                "audit",
            )
            if request_type not in allowed:
                self.send_json({"error": "unsupported request type"}, 400)
                return
            # 把任务参数（cluster_id 等）原样透传给 enqueue_request
            extra = {k: v for k, v in payload.items() if k != "type"}
            try:
                request, created = enqueue_request(self.workspace, request_type, extra)
            except ValueError as error:
                self.send_json({"error": str(error)}, 400)
                return
            self.send_json(request, 201 if created else 200)
            return
        if path == "/api/submissions":
            state = read_json(self.workspace / "state.json", {})
            research = read_json(self.workspace / "research.json", {})
            if not research.get("applications"):
                self.send_json(
                    {"error": "no verified applications available for submission"}, 400
                )
                return
            submission_id = f"sim_{int(datetime.now().timestamp() * 1000)}"
            snapshot = {
                "id": submission_id,
                "timestamp": now_iso(),
                "state": state,
                "research": research,
            }
            write_json(
                self.workspace / "plans" / "submissions" / f"{submission_id}.json",
                snapshot,
            )
            state.setdefault("submissions", []).append(
                {"id": submission_id, "timestamp": snapshot["timestamp"]}
            )
            state["audit"] = {
                "submission_id": submission_id,
                "status": "waiting_fresh_subagent",
            }
            state["version"] = int(state.get("version", 1)) + 1
            write_json(self.workspace / "state.json", state)
            append_event(
                self.workspace,
                {
                    "stage": "simulation",
                    "type": "simulation-submitted",
                    "summary": f"生成只读模拟提交 {submission_id}",
                    "version": state["version"],
                    "related_ids": [submission_id],
                },
            )
            enqueue_request(self.workspace, "audit")
            self.send_json(snapshot, 201)
            return
        self.send_error(404)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    workspace = Path(args.workspace).expanduser().resolve()
    initialize_workspace(workspace)
    Handler.workspace = workspace
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"http://{args.host}:{args.port}")
    print(f"workspace={workspace}")
    server.serve_forever()


if __name__ == "__main__":
    main()
