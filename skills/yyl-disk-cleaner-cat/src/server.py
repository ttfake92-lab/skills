#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
server.py — 本地桥梁服务

流程：
  1. 启动时读偏好 + 扫描（终端打印进度）
  2. 起一个本地 http 服务，自动用浏览器打开像素风页面
  3. 页面拿 /api/scan 渲染清理项（已学到的安全类别预勾选）
  4. 用户在页面勾选 + 点「开始打扫」→ POST /api/clean
  5. 服务真正执行永久删除，每删一项通过 /api/events(SSE) 推进度，小猫同步打扫
  6. 删完写 history + 刷新偏好 + 渲染 MEMORY.md，页面显示成果

只用标准库，零额外安装。Ctrl-C 退出。
"""

import os
import sys
import json
import time
import queue
import threading
import webbrowser
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import engine  # noqa: E402

WEB_DIR = Path(__file__).resolve().parent.parent / "web"

STATE = {
    "scan": None,
    "prefs": None,
    "event_q": queue.Queue(),
    "cleaning": False,
    "finished": False,
    "summary": None,
}


def log(msg):
    print(f"  {msg}", flush=True)


def do_scan():
    STATE["prefs"] = engine.load_prefs()
    log("🐱 小猫开始巡视磁盘…")
    t0 = time.time()
    STATE["scan"] = engine.full_scan(STATE["prefs"])
    s = STATE["scan"]
    log(f"扫描完成（{time.time()-t0:.1f}s）：可释放约 "
        f"{s['total_reclaimable_h']}，已为你预勾选 {s['pre_checked_h']}")


def push(event):
    STATE["event_q"].put(event)


def run_clean(selected_ids):
    # 从扫描结果里取出被选中的 item dict
    by_id = {}
    for cat in STATE["scan"]["cleanable"].values():
        for it in cat["items"]:
            by_id[it["id"]] = it
    selected = [by_id[i] for i in selected_ids if i in by_id]
    STATE["cleaning"] = True
    log(f"🧹 开始打扫，共 {len(selected)} 项…")

    def cb(ev):
        push(ev)
        if ev.get("type") == "item_done":
            log(f"  · {ev['label']} → 释放 {ev['freed_h']}"
                + (f"（{ev['error']}）" if ev.get("error") else ""))

    summary = engine.clean_items(selected, STATE["prefs"], cb)
    STATE["summary"] = summary
    STATE["finished"] = True
    STATE["cleaning"] = False
    log(f"✅ 打扫完成：共释放 {summary['freed_total_h']}，"
        f"成功 {summary['count_done']} 项，失败 {summary['count_error']} 项")
    log("记忆已更新 → ~/.disk-cleanup-cat/MEMORY.md")


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):  # 静音默认日志
        pass

    def _send(self, code, body, ctype="application/json; charset=utf-8"):
        if isinstance(body, (dict, list)):
            body = json.dumps(body, ensure_ascii=False).encode("utf-8")
        elif isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _serve_file(self, rel):
        path = (WEB_DIR / rel).resolve()
        if not str(path).startswith(str(WEB_DIR.resolve())) or not path.exists():
            self._send(404, {"error": "not found"})
            return
        ctype = {
            ".html": "text/html; charset=utf-8",
            ".css": "text/css; charset=utf-8",
            ".js": "application/javascript; charset=utf-8",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".svg": "image/svg+xml",
        }.get(path.suffix, "application/octet-stream")
        self._send(200, path.read_bytes(), ctype)

    def do_GET(self):
        route = self.path.split("?")[0]
        if route in ("/", "/index.html"):
            self._serve_file("index.html")
        elif route.startswith("/web/"):
            self._serve_file(route[len("/web/"):])
        elif route in ("/style.css", "/app.js", "/room.png",
                       "/room1-2.png", "/room2-3.png", "/room2-4.png"):
            self._serve_file(route.lstrip("/"))
        elif route == "/api/scan":
            self._send(200, STATE["scan"] or {"error": "scanning"})
        elif route == "/api/events":
            self._serve_sse()
        elif route == "/api/status":
            self._send(200, {"cleaning": STATE["cleaning"], "finished": STATE["finished"],
                             "summary": STATE["summary"]})
        else:
            self._send(404, {"error": "not found"})

    def _serve_sse(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.end_headers()
        # 若已完成，先补发 summary
        if STATE["finished"] and STATE["summary"]:
            self._sse_write(STATE["summary"])
        last_ping = time.time()
        while True:
            try:
                ev = STATE["event_q"].get(timeout=1.0)
                self._sse_write(ev)
                if ev.get("type") == "finished":
                    break
            except queue.Empty:
                if time.time() - last_ping > 10:
                    try:
                        self.wfile.write(b": ping\n\n")
                        self.wfile.flush()
                        last_ping = time.time()
                    except Exception:  # noqa
                        break
            except Exception:  # noqa
                break

    def _sse_write(self, obj):
        try:
            self.wfile.write(b"data: " + json.dumps(obj, ensure_ascii=False).encode("utf-8") + b"\n\n")
            self.wfile.flush()
        except Exception:  # noqa
            pass

    def do_POST(self):
        route = self.path.split("?")[0]
        length = int(self.headers.get("Content-Length", 0) or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            data = json.loads(raw or b"{}")
        except Exception:  # noqa
            data = {}

        if route == "/api/clean":
            if STATE["cleaning"]:
                self._send(409, {"error": "正在清理中"})
                return
            ids = data.get("ids", [])
            STATE["finished"] = False
            STATE["summary"] = None
            STATE["event_q"] = queue.Queue()
            threading.Thread(target=run_clean, args=(ids,), daemon=True).start()
            self._send(200, {"ok": True, "count": len(ids)})
        elif route == "/api/action":
            # 性能板块的安全一键（禁用/还原用户级自启）
            res = engine.execute_action(data.get("type", ""), data.get("target", ""))
            log(("✅ " if res.get("ok") else "⚠️ ") + res.get("message", ""))
            self._send(200, res)
        elif route == "/api/prefs":
            # 页面可写回偏好（如 never_touch、notes、delete_mode）
            prefs = STATE["prefs"] or engine.load_prefs()
            for k in ("never_touch", "notes", "auto_check"):
                if k in data:
                    prefs[k] = data[k]
            engine.save_prefs(prefs)
            engine.render_memory_md()
            STATE["prefs"] = prefs
            self._send(200, {"ok": True})
        elif route == "/api/shutdown":
            self._send(200, {"ok": True})
            threading.Thread(target=lambda: (time.sleep(0.3), os._exit(0)), daemon=True).start()
        else:
            self._send(404, {"error": "not found"})


def main():
    do_scan()
    port = int(os.environ.get("CAT_PORT", "8765"))
    server = None
    for p in range(port, port + 10):
        try:
            server = ThreadingHTTPServer(("127.0.0.1", p), Handler)
            port = p
            break
        except OSError:
            continue
    if server is None:
        log("无法绑定端口，退出。")
        sys.exit(1)
    url = f"http://127.0.0.1:{port}/"
    log(f"🌐 像素清理页已就绪：{url}")
    if os.environ.get("CAT_NO_OPEN") != "1":
        threading.Thread(target=lambda: (time.sleep(0.6), webbrowser.open(url)), daemon=True).start()
    log("（页面里点「开始打扫」后回到这里可看实时日志；Ctrl-C 退出服务）")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log("已退出。")


if __name__ == "__main__":
    main()
