#!/usr/bin/env python3
"""Render a static college-application HTML report from workspace files.

The script intentionally has no third-party dependencies. It reads:
- research.json for structured personality/career/admission/source data
- CANDIDATE.md, PERSONALITY-REPORT.md, SOURCES.md as fallback narrative context
- assets/final-report-template.html as the visual template

Missing fields are rendered as honest placeholders instead of invented data.
"""

import argparse
import html
import json
from datetime import datetime, timezone
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parent.parent
DEFAULT_TEMPLATE = SKILL_DIR / "assets" / "final-report-template.html"


def now_iso_date():
    return datetime.now(timezone.utc).astimezone().date().isoformat()


def read_json(path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def read_text(path, default=""):
    if not path.exists():
        return default
    return path.read_text(encoding="utf-8")


def esc(value):
    if value is None or value == "":
        return "待补充"
    return html.escape(str(value), quote=True)


def join_values(values):
    if not values:
        return "待补充"
    if isinstance(values, str):
        return values
    return "、".join(str(value) for value in values if value is not None) or "待补充"


def first_present(*values, default="待补充"):
    for value in values:
        if value not in (None, "", [], {}):
            return value
    return default


def render_bullets(values, empty="待补充"):
    if not values:
        return f"<p class=\"muted\">{esc(empty)}</p>"
    return "<ul>" + "".join(f"<li>{esc(value)}</li>" for value in values) + "</ul>"


def render_career_direction_cards(directions):
    if not directions:
        return "<p class=\"muted\">待补充：尚未生成职业方向假设。</p>"
    cards = []
    for direction in directions:
        cards.append(
            "<section>"
            f"<h3>{esc(direction.get('name'))}</h3>"
            f"<p><span class=\"tag\">支持证据</span></p>{render_bullets(direction.get('match_evidence'))}"
            f"<p><span class=\"tag\">反证/风险</span></p>{render_bullets(direction.get('counter_evidence'))}"
            f"<p class=\"muted\">关联专业：{esc(join_values(direction.get('related_major_families')))}</p>"
            "</section>"
        )
    return "".join(cards)


def render_industry_sections(clusters):
    if not clusters:
        return "<p class=\"muted\">待补充：尚未完成专业与行业深度研究。</p>"
    sections = []
    for cluster in clusters:
        sections.append(
            "<section>"
            f"<h3>{esc(cluster.get('name'))}</h3>"
            f"<p><strong>匹配理由：</strong>{esc(join_values(cluster.get('match_reasons')))}</p>"
            f"<p><strong>课程与学习内容：</strong>{esc(join_values(cluster.get('courses')))}</p>"
            f"<p><strong>真实工作：</strong>{esc(join_values(cluster.get('work_realities')))}</p>"
            f"<p><strong>职业出口：</strong>{esc(join_values(cluster.get('career_paths')))}</p>"
            f"<p><strong>行业判断：</strong>{esc(cluster.get('industry_outlook'))}</p>"
            f"<p><strong>主要风险：</strong>{esc(join_values(cluster.get('risks')))}</p>"
            f"<p class=\"muted\">来源：{esc(join_values(cluster.get('source_ids')))}</p>"
            "</section>"
        )
    return "".join(sections)


def render_application_rows(applications):
    if not applications:
        return (
            "<tr><td colspan=\"6\" class=\"muted\">"
            "待补充：尚未生成志愿建议；若缺少近 3 年可比投档数据，只能输出定性等级。"
            "</td></tr>"
        )
    rows = []
    for app in applications:
        rows.append(
            "<tr>"
            f"<td class=\"risk\">{esc(app.get('risk_level'))}</td>"
            f"<td>{esc(app.get('university'))}<br><span class=\"muted\">{esc(app.get('group_or_major'))}</span></td>"
            f"<td>{esc(app.get('rationale'))}</td>"
            f"<td>{esc(first_present(app.get('chance_range'), app.get('risk_level')))}</td>"
            f"<td>{esc(join_values(app.get('restrictions')))}</td>"
            f"<td>{esc(join_values(app.get('source_ids')))}</td>"
            "</tr>"
        )
    return "".join(rows)


def render_sources(sources):
    if not sources:
        return "<li class=\"muted\">待补充：没有可追溯来源时，不应把报告用于正式填报。</li>"
    items = []
    for source in sources:
        url = source.get("url") or ""
        link = f"<a href=\"{esc(url)}\" target=\"_blank\" rel=\"noreferrer\">{esc(url)}</a>" if url.startswith(("http://", "https://")) else esc(url or "无 URL")
        items.append(
            "<li>"
            f"<strong>{esc(source.get('id'))}</strong> — {esc(source.get('claim'))}<br>"
            f"发布机构：{esc(source.get('publisher'))}；年份/口径：{esc(source.get('published_or_data_year'))}；"
            f"状态：{esc(source.get('status'))}；最后核验：{esc(source.get('verified_at'))}<br>"
            f"{link}"
            "</li>"
        )
    return "".join(items)




def render_key_takeaways(research):
    candidate = research.get("candidate") or {}
    profile = research.get("personality_profile") or {}
    riasec = (profile.get("riasec") or {}).get("top_code") or "待补充"
    directions = research.get("career_directions") or []
    first_dirs = "、".join(direction.get("name", "") for direction in directions[:3] if direction.get("name")) or "待补充"
    rank = candidate.get("rank")
    score = candidate.get("score")
    items = [
        f"当前兴趣画像更适合先研究复合方向：{first_dirs}。",
        f"RIASEC 前三码为 {riasec}，只能作为方向线索，不是专业结论。",
    ]
    if rank:
        items.append(f"已提供位次：{rank}，后续可优先按位次做跨年比较。")
    elif score:
        items.append(f"目前只提供分数 {score}，缺少全省位次；Agent 应先尝试查找官方一分一段表估算参考位次，拿不到再请用户提供。")
    else:
        items.append("尚未提供分数或位次，不能进入录取分析。")
    items.append("没有官方投档线和招生计划时，不输出具体录取概率。")
    return render_bullets(items)


def render_next_data_steps(research):
    candidate = research.get("candidate") or {}
    province = candidate.get("province") or "招生省份"
    year = candidate.get("application_year") or "填报年份"
    steps = [
        f"Agent 先尝试检索 {province} {year} 官方一分一段表；如果只找到往年数据，只能估算参考位次，并标注误差。",
        f"Agent 先尝试检索 {province} {year} 本科批招生计划和目标院校招生章程。",
        "Agent 先尝试检索目标专业组近 3–5 年官方投档线；找不到完整官方数据时，只给定性等级。",
        "只有官方来源不足或访问失败时，再请用户上传/提供文件或链接。",
    ]
    return render_bullets(steps)


def render_personality_score_tables(profile):
    riasec = profile.get("riasec") or {}
    big_five = profile.get("big_five") or {}
    scores = riasec.get("scores") or {}
    riasec_rows = "".join(f"<tr><td>{esc(key)}</td><td>{esc(value)}</td></tr>" for key, value in scores.items())
    big_rows = "".join(
        f"<tr><td>{esc(key)}</td><td>{esc((value or {}).get('score'))}</td><td>{esc((value or {}).get('level'))}</td></tr>"
        for key, value in big_five.items()
        if isinstance(value, dict)
    )
    return (
        "<h4>RIASEC</h4><table><thead><tr><th>类型</th><th>得分</th></tr></thead><tbody>"
        + (riasec_rows or "<tr><td>待补充</td><td>待补充</td></tr>")
        + "</tbody></table>"
        + "<h4>Big Five</h4><table><thead><tr><th>维度</th><th>得分</th><th>水平</th></tr></thead><tbody>"
        + (big_rows or "<tr><td>待补充</td><td>待补充</td><td>待补充</td></tr>")
        + "</tbody></table>"
    )


def render_unverified_items(research):
    items = []
    methodology = research.get("methodology") or {}
    for limitation in methodology.get("limitations") or []:
        items.append(f"<li>{esc(limitation)}</li>")
    for source in research.get("sources") or []:
        if source.get("status") in {"unverified", "待核验", "无法核验", "conflict", "冲突", "失效"}:
            items.append(f"<li>{esc(source.get('id'))}: {esc(source.get('claim'))}（{esc(source.get('status'))}）</li>")
    if not items:
        return "<p class=\"muted\">暂无标记项。仍建议逐条打开来源链接交叉验证。</p>"
    return "<ul>" + "".join(items) + "</ul>"


def build_context(workspace, research):
    candidate = read_text(workspace / "CANDIDATE.md")
    personality_report = read_text(workspace / "PERSONALITY-REPORT.md")
    sources_md = read_text(workspace / "SOURCES.md")

    profile = research.get("personality_profile") or {}
    riasec = profile.get("riasec") or {}
    big_five = profile.get("big_five") or {}
    methodology = research.get("methodology") or {}

    candidate_info = research.get("candidate") or {}
    context = {
        "report_title": first_present(research.get("title"), "高考志愿决策辅助报告"),
        "generated_at": first_present(research.get("generated_at"), datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")),
        "verified_at": first_present(research.get("verified_at"), now_iso_date()),
        "province": first_present(candidate_info.get("province"), research.get("province")),
        "application_year": first_present(candidate_info.get("application_year"), candidate_info.get("year")),
        "exam_mode": first_present(candidate_info.get("exam_mode")),
        "subjects": join_values(candidate_info.get("subjects")),
        "score_rank": first_present(candidate_info.get("score_rank"), candidate_info.get("score"), candidate_info.get("rank")),
        "executive_summary": first_present(research.get("executive_summary"), "先看重点结论：方向是否匹配、当前数据够不够、下一步要补什么。完整专业分析和来源放在后面展开。"),
        "key_takeaways": render_key_takeaways(research),
        "next_data_steps": render_next_data_steps(research),
        "region_preferences": join_values(candidate_info.get("preferred_regions") or candidate_info.get("preferred_cities")),
        "riasec_json": json.dumps({k: int(v) for k, v in ((riasec.get("scores") or {}).items())} if riasec.get("scores") else {}, ensure_ascii=False),
        "bigfive_json": json.dumps({k: int(v.get("score", 0)) for k, v in big_five.items() if isinstance(v, dict)} if big_five else {}, ensure_ascii=False),
        "riasec_code": first_present(riasec.get("top_code")),
        "openness": first_present((big_five.get("openness") or {}).get("level")),
        "conscientiousness": first_present((big_five.get("conscientiousness") or {}).get("level")),
        "extraversion": first_present((big_five.get("extraversion") or {}).get("level")),
        "personality_summary": first_present(riasec.get("interpretation"), personality_report[:700] if personality_report else None),
        "personality_limitations": join_values(profile.get("limitations")),
        "career_direction_cards": render_career_direction_cards(research.get("career_directions") or []),
        "industry_analysis_sections": render_industry_sections(research.get("major_clusters") or []),
        "personality_score_tables": render_personality_score_tables(profile),
        "personality_career_direction_cards": render_career_direction_cards(research.get("career_directions") or []),
        "methodology": first_present(methodology.get("description")),
        "data_limitations": join_values(methodology.get("limitations")),
        "application_rows": render_application_rows(research.get("applications") or []),
        "unverified_items": render_unverified_items(research),
        "source_items": render_sources(research.get("sources") or []),
    }

    if context["personality_summary"] == "待补充" and candidate:
        context["personality_summary"] = "已找到 CANDIDATE.md，但 research.json 尚未结构化写入性格摘要。请以 Markdown 原文为准，并补充结构化字段。"
    if not research.get("sources") and sources_md:
        context["source_items"] = "<li class=\"muted\">已找到 SOURCES.md，但 research.json 尚未结构化写入 sources。请检查 Markdown 来源台账。</li>"
    return {key: esc(value) if isinstance(value, str) and key not in {
        "career_direction_cards", "industry_analysis_sections", "application_rows", "unverified_items", "source_items", "key_takeaways", "next_data_steps", "personality_score_tables", "personality_career_direction_cards", "riasec_json", "bigfive_json"
    } else value for key, value in context.items()}


def render_template(template, context):
    output = template
    for key, value in context.items():
        output = output.replace("{{" + key + "}}", str(value))
    return output


def main():
    parser = argparse.ArgumentParser(description="Render final college-application HTML report")
    parser.add_argument("--workspace", required=True, help="Candidate workspace directory")
    parser.add_argument("--template", default=str(DEFAULT_TEMPLATE), help="HTML template path")
    parser.add_argument("--output", help="Output HTML path; defaults to <workspace>/final-report.html")
    args = parser.parse_args()

    workspace = Path(args.workspace).expanduser().resolve()
    template_path = Path(args.template).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve() if args.output else workspace / "final-report.html"

    if not workspace.exists():
        raise SystemExit(f"workspace does not exist: {workspace}")
    if not template_path.exists():
        raise SystemExit(f"template does not exist: {template_path}")

    research = read_json(workspace / "research.json", {})
    template = template_path.read_text(encoding="utf-8")
    context = build_context(workspace, research)
    output = render_template(template, context)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(output, encoding="utf-8")
    print(output_path)


if __name__ == "__main__":
    main()
