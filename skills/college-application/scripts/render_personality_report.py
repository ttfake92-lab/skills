#!/usr/bin/env python3
"""Render a readable HTML report from personality assessment JSON/results.

This renderer is intentionally independent from the final admission report. It
lets users see an immediate, friendly report after the first form, before moving
on to gaokao admission information.
"""

import argparse
import html
import json
from datetime import datetime, timezone
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parent.parent
DEFAULT_TEMPLATE = SKILL_DIR / "assets" / "personality-report-template.html"


def esc(value):
    if value is None or value == "":
        return "待补充"
    return html.escape(str(value), quote=True)


def level(score):
    if score <= 9:
        return "低"
    if score <= 15:
        return "中"
    return "高"


def reverse(score):
    return 6 - score


def score_assessment(answers):
    riasec_map = {
        "R": ["A01", "A02"],
        "I": ["A03", "A04"],
        "A": ["A05", "A06"],
        "S": ["A07", "A08"],
        "E": ["A09", "A10"],
        "C": ["A11", "A12"],
    }
    riasec = {key: sum(int(answers[item]) for item in items) for key, items in riasec_map.items()}
    ranked = sorted(riasec.items(), key=lambda item: (-item[1], item[0]))
    code = "-".join(key for key, _ in ranked[:3])

    big_five = {
        "外向性": int(answers["B01"]) + reverse(int(answers["B02"])) + reverse(int(answers["B03"])) + int(answers["B04"]),
        "宜人性": int(answers["B05"]) + reverse(int(answers["B06"])) + int(answers["B07"]) + reverse(int(answers["B08"])),
        "尽责性": int(answers["B09"]) + int(answers["B10"]) + int(answers["B11"]) + reverse(int(answers["B12"])),
        "神经质": int(answers["B13"]) + reverse(int(answers["B14"])) + int(answers["B15"]) + reverse(int(answers["B16"])),
        "开放性": int(answers["B17"]) + reverse(int(answers["B18"])) + reverse(int(answers["B19"])) + reverse(int(answers["B20"])),
    }
    return riasec, code, big_five


def career_directions(riasec, big_five):
    ranked = [key for key, _ in sorted(riasec.items(), key=lambda item: (-item[1], item[0]))]
    directions = []
    if "I" in ranked[:4] and "C" in ranked[:4]:
        directions.append(("数据 / 计算机 / 信息系统", "适合分析、整理、建模和系统化解决问题。"))
    if "R" in ranked[:4] and "I" in ranked[:4]:
        directions.append(("工程技术 / 智能制造", "适合把原理、工具、设备和真实问题结合起来。"))
    if "A" in ranked[:4] and "I" in ranked[:4]:
        directions.append(("创意技术 / 数字媒体 / 产品体验", "适合把表达、设计、研究和技术交付结合起来。"))
    if "C" in ranked[:4] and ("R" in ranked[:4] or "I" in ranked[:4]):
        directions.append(("质量 / 合规 / 实验室与技术治理", "适合标准、记录、验证、测试和流程改进。"))
    if not directions:
        directions.append(("待进一步探索", "当前结果不够集中，需要结合真实经历继续判断。"))
    return directions[:4]


def render_direction_cards(directions):
    return "".join(
        f"<section><h3>{esc(name)}</h3><p>{esc(desc)}</p></section>"
        for name, desc in directions
    )


def render_score_tables(riasec, big_five):
    riasec_rows = "".join(f"<tr><td>{esc(key)}</td><td>{score}</td></tr>" for key, score in riasec.items())
    big_rows = "".join(f"<tr><td>{esc(key)}</td><td>{score}</td><td>{esc(level(score))}</td></tr>" for key, score in big_five.items())
    return (
        "<h3>RIASEC</h3><table><thead><tr><th>类型</th><th>得分</th></tr></thead><tbody>"
        + riasec_rows
        + "</tbody></table>"
        + "<h3>Big Five</h3><table><thead><tr><th>维度</th><th>得分</th><th>水平</th></tr></thead><tbody>"
        + big_rows
        + "</tbody></table>"
    )


def render_template(template, context):
    output = template
    for key, value in context.items():
        output = output.replace("{{" + key + "}}", str(value))
    return output


def main():
    parser = argparse.ArgumentParser(description="Render personality assessment HTML report")
    parser.add_argument("--input", required=True, help="personality-assessment-result.json path")
    parser.add_argument("--output", required=True, help="Output HTML path")
    parser.add_argument("--template", default=str(DEFAULT_TEMPLATE), help="HTML template path")
    args = parser.parse_args()

    payload = json.loads(Path(args.input).expanduser().read_text(encoding="utf-8"))
    answers = payload.get("answers") or {}
    missing = [key for key in [f"A{i:02d}" for i in range(1, 13)] + [f"B{i:02d}" for i in range(1, 21)] if key not in answers]
    if missing:
        raise SystemExit(f"missing answers: {', '.join(missing)}")

    riasec, code, big_five = score_assessment(answers)
    directions = career_directions(riasec, big_five)
    generated_at = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")

    plain_summary = "你的结果更像是若干方向的组合，而不是单一标签。先把它当成职业探索线索，再用课程、项目和行业信息验证。"
    if len({score for score in riasec.values() if score == max(riasec.values())}) > 1:
        plain_summary = "你的兴趣不是单一路线，几个维度都比较强。更适合先看交叉方向，而不是马上锁定一个热门专业。"

    context = {
        "report_title": "性格与职业兴趣测评报告",
        "generated_at": esc(generated_at),
        "plain_summary": esc(plain_summary),
        "riasec_code": esc(code),
        "openness": esc(level(big_five["开放性"])),
        "conscientiousness": esc(level(big_five["尽责性"])),
        "extraversion": esc(level(big_five["外向性"])),
        "personality_summary": esc("RIASEC 前三码用于判断兴趣方向；Big Five 用于判断更可能适应的工作方式。它们都不是诊断。"),
        "career_direction_cards": render_direction_cards(directions),
        "interpretation": esc("先看高分方向共同指向什么，再看反证。高分不是‘必须选’，低分也不是‘不能选’；真正重要的是未来课程、项目和工作日常是否能长期承受。"),
        "score_tables": render_score_tables(riasec, big_five),
        "riasec_json": json.dumps(riasec, ensure_ascii=False),
        "bigfive_json": json.dumps(big_five, ensure_ascii=False),
        "limitations": "<ul><li>短量表只能做初筛，不适合作心理诊断。</li><li>如果多个 RIASEC 维度并列高，说明需要进一步用真实经历验证。</li><li>职业方向还必须结合行业研究、高考信息和招生数据。</li></ul>",
    }

    template = Path(args.template).expanduser().read_text(encoding="utf-8")
    output = render_template(template, context)
    output_path = Path(args.output).expanduser()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(output, encoding="utf-8")
    print(output_path)


if __name__ == "__main__":
    main()
