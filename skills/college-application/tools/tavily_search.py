#!/usr/bin/env python3
"""Tavily 搜索的极薄封装。

用途：发现"哪个 URL 是当前问题的权威来源"。**只负责发现 URL，不负责把网页内容当作可信结论**。
真正的取数与核验由 Chrome MCP（open_browser_use）做——它能跟跳转、跑 JS、过反爬，比任何搜索 API
拿到的 snippet 都更可信。

Tavily 在中文官方站（教育部、阳光高考、省考试院）上的覆盖比 Brave / DuckDuckGo 好，
但 snippet 不能直接作为 SOURCES.md 的引用，必须用 Chrome 二次访问原 URL 再写入。

使用：
  python3 tools/tavily_search.py "教育部 普通高等学校本科专业目录 人工智能" \
      --max-results 5 --include moe.gov.cn,gaokao.chsi.com.cn

环境变量：
  TAVILY_API_KEY  必填。建议放在 ~/.claude/settings.json 的 env 段。
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request


TAVILY_ENDPOINT = "https://api.tavily.com/search"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", help="搜索词，可中可英")
    parser.add_argument("--max-results", type=int, default=5)
    parser.add_argument(
        "--include",
        default="",
        help="逗号分隔的域名白名单，建议加 moe.gov.cn,gaokao.chsi.com.cn 等官方域",
    )
    parser.add_argument(
        "--exclude",
        default="",
        help="逗号分隔的域名黑名单，建议屏蔽聚合站 / 自媒体",
    )
    parser.add_argument(
        "--depth",
        choices=("basic", "advanced"),
        default="basic",
        help="advanced 更慢更贵但更准；学情研究默认 basic 已够",
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="返回原始 Tavily 响应（含 answer / images 等）",
    )
    args = parser.parse_args()

    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        print(
            "ERROR: 未找到 TAVILY_API_KEY。\n"
            "在 ~/.claude/settings.json 的 env 段加：\n"
            '  "TAVILY_API_KEY": "tvly-..."',
            file=sys.stderr,
        )
        sys.exit(2)

    payload = {
        "api_key": api_key,
        "query": args.query,
        "max_results": max(1, min(20, args.max_results)),
        "search_depth": args.depth,
    }
    if args.include:
        payload["include_domains"] = [d.strip() for d in args.include.split(",") if d.strip()]
    if args.exclude:
        payload["exclude_domains"] = [d.strip() for d in args.exclude.split(",") if d.strip()]

    request = urllib.request.Request(
        TAVILY_ENDPOINT,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        print(f"ERROR: Tavily HTTP {error.code}: {body}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as error:
        print(f"ERROR: Tavily 网络错误: {error.reason}", file=sys.stderr)
        sys.exit(1)

    if args.raw:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return

    # 精简结构，方便 Agent 在终端里读。只输出 url + title + 一句话摘要。
    # 强调：snippet 仅用于判断"是否值得用 Chrome 进一步访问"，不能直接作为引用。
    simplified = [
        {
            "url": item.get("url"),
            "title": item.get("title"),
            "snippet": (item.get("content") or "")[:240],
        }
        for item in data.get("results", [])
    ]
    print(json.dumps(simplified, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
