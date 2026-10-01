#!/usr/bin/env python3
"""Build or validate AI video prompts using the yyl-video-prompt methodology."""

import argparse
import json
import re
import sys

DIMENSIONS = [
    "时间段",
    "人物目的",
    "情绪变化",
    "台词触发词",
    "面部动作与 AU",
    "目光与身体",
    "声音、呼吸与停顿",
    "结束状态与静止反应",
]

EMOTION_LABELS = [
    "悲伤", "伤心", "难过", "痛苦",
    "愤怒", "生气", "恼火", "气愤", "大怒",
    "高兴", "开心", "快乐", "喜悦", "兴奋",
    "害怕", "恐惧", "惊恐", "惊慌",
    "羞愧", "羞耻", "尴尬",
    "惊讶", "吃惊", "震惊",
    "厌恶", "讨厌", "反感",
]

SCENE_TYPES = {
    "日常动作": ["走路", "坐下", "站起来", "拿东西", "看窗外", "进门", "出门", "倒水", "吃饭", "喝咖啡", "放下手机", "打开"],
    "情绪递进": ["哭", "笑", "发怒", "崩溃", "颤抖", "愣住", "眼眶红", "破音", "开心", "喜悦", "悲伤", "愤怒", "害怕", "恐惧", "厌恶", "羞愧", "惊讶", "情绪波动"],
    "对手戏": ["对话", "争吵", "对峙", "两人", "对方", "A说", "B说", "男人", "女人", "男主", "女主"],
    "内心戏": ["静止", "无台词", "沉默", "发呆", "独自", "一个人", "没有台词", "特写脸"],
}

# Cinematic-drama segments use fixed block names. 参考绑定 is only required when the
# segment uses reference media; 道具 is optional.
CINEMATIC_SECTIONS = [
    "全文地图",
    "人物一致性",
    "场景与空间",
    "风格与画质",
    "分镜时间轴",
    "声音设计",
    "硬约束",
    "核心要求",
]

# Short-video style B (多分镜, the mx-shell-prompt layout). Style A (一镜到底, the
# AI-video-prompt layout) is one dense paragraph whose 【】 labels vary, so it is
# checked by content instead of block names.
MULTI_SHOT_SECTIONS = ["基础设定", "场景", "声音", "氛围与画质", "画面内容"]
SHOT_HEADER = re.compile(r"^分镜[一二三四五六七八九十0-9]+(?:（[^）]*）)?[：:]", re.M)
SHOT_FIELDS = ["景别", "构图", "运镜"]

# Generation tools have no memory across segments, so each one must stand alone.
CARRY_OVER_PHRASES = ["同上", "沿用上一段", "延续上一段", "与上一段相同", "同段1", "参考上一段", "沿用段"]

PHONE_LOOK_HINTS = ["手机拍", "手机随手", "手机横着", "手机竖着", "手持手机", "前置自拍"]
CINEMA_BUZZWORDS = ["电影感", "大片", "4K", "IMAX", "精修", "高清"]

SEGMENT_HEADER = re.compile(r"^#*\s*(?:段|片段|板块)\s*[0-9一二三四五六七八九十]+\s*[：:]", re.M)
REF_USE = re.compile(r"(?:@?图片|参考图|@图像)\s*(\d+)")
REF_DEF = re.compile(r"^\s*(?:@?图片|参考图|@图像)\s*(\d+)\s*[：:]", re.M)


def classify_scene(text: str) -> str:
    """Classify a scene fragment into one of the scene types."""
    scores = {name: 0 for name in SCENE_TYPES}
    for scene_type, keywords in SCENE_TYPES.items():
        for kw in keywords:
            if kw in text:
                scores[scene_type] += 1
    best = max(scores, key=scores.get)
    if scores[best] == 0:
        return "待判断"
    return best


def split_segments(text: str) -> list:
    """Split a document into segments by '## 段N' headers; no header means one segment."""
    starts = [m.start() for m in SEGMENT_HEADER.finditer(text)]
    if not starts:
        return [("段1", text)]
    segments = []
    for i, start in enumerate(starts):
        end = starts[i + 1] if i + 1 < len(starts) else len(text)
        body = text[start:end]
        title = body.splitlines()[0].lstrip("#").strip()
        segments.append((title, body))
    return segments


def duration_cap(params: str) -> int:
    """Single-generation length limit implied by the 模型参数 line."""
    if re.search(r"2\.0", params):
        return 15
    return 30


def detect_mode(body: str) -> str:
    """Read the 档位 line; fall back to the mode whose signature is present."""
    declared = re.search(r"档位[：:]\s*(短视频|电影精品)", body)
    if declared:
        return declared.group(1)
    if "全文地图" in body or "核心要求" in body:
        return "电影精品"
    if "基础设定" in body or "画面内容" in body or "一镜到底" in body or SHOT_HEADER.search(body):
        return "短视频"
    return ""


def is_multi_shot(body: str) -> bool:
    return "画面内容" in body or bool(SHOT_HEADER.search(body))


def check_segment(body: str) -> tuple:
    issues = []
    suggestions = []

    mode = detect_mode(body)
    if not mode:
        issues.append("没写『档位：短视频 / 电影精品』，也看不出用的是哪一档的结构")
        return mode, issues, suggestions

    uses_refs = bool(REF_DEF.search(body)) or bool(re.search(r"生成模式[：:]\s*(?!纯文生)", body))

    if mode == "电影精品":
        for section in CINEMATIC_SECTIONS + (["参考绑定"] if uses_refs else []):
            if section not in body:
                issues.append(f"缺少『{section}』块")
    elif is_multi_shot(body):
        for section in MULTI_SHOT_SECTIONS:
            if section not in body:
                issues.append(f"多分镜写法缺少『{section}』块")
        shots = SHOT_HEADER.findall(body)
        for field in SHOT_FIELDS:
            if body.count(field) < len(shots):
                issues.append(f"有 {len(shots)} 个分镜，但『{field}』只写了 {body.count(field)} 处，每个分镜都要写")
        if shots and not any("秒" in s for s in shots):
            suggestions.append("分镜没标秒数，例如「分镜一（0.0–3.0秒）」")
        if "约束" not in body:
            suggestions.append("多分镜写法末尾可加【约束——必须严格遵守】")
    else:
        if "约束" not in body:
            issues.append("一镜到底写法缺少约束（【约束--必须严格遵守】）")
        if not any(w in body for w in ("音效", "声音", "环境声", "背景音乐")):
            issues.append("一镜到底写法没写声音")
        if not re.search(r"\d+\.?\d*\s*[-~—–到]\s*\d+\.?\d*\s*[秒s]", body):
            issues.append("一镜到底写法没有秒级时间码")

    if mode == "短视频":
        if uses_refs and "锁定" not in body:
            suggestions.append("用了参考图，但没写每张图锁定什么")
        if re.search(r"AU\d+", body):
            suggestions.append("短视频档不用 AU 编码，改成一句人话的表情变化")

    params = re.search(r"模型参数[：:](.*)", body)
    if params:
        seconds = re.findall(r"(\d+)\s*(?:s|秒)", params.group(1))
        if seconds:
            length, cap = int(seconds[-1]), duration_cap(params.group(1))
            if length > cap:
                issues.append(f"单段 {length} 秒超过该模型上限 {cap} 秒，需要拆段")
    else:
        suggestions.append("没有『模型参数』行，提交时会缺参数")

    for phrase in CARRY_OVER_PHRASES:
        if phrase in body:
            issues.append(f"出现『{phrase}』：生成工具没有跨段记忆，每段要自包含")
            break

    defined = set(REF_DEF.findall(body))
    used = set(REF_USE.findall(body))
    missing = sorted(used - defined, key=int)
    if missing:
        suggestions.append(f"正文引用了 图片{'/'.join(missing)}，但参考素材列表里没定义")

    if any(h in body for h in PHONE_LOOK_HINTS):
        hits = [w for w in CINEMA_BUZZWORDS if w in body]
        if hits:
            suggestions.append(f"手机实拍基调里出现了 {'、'.join(hits)}，这类词会把画面推向商业大片感")

    return mode, issues, suggestions


def validate_prompt(text: str) -> dict:
    """Check every segment against the skill's structure, then run document-wide checks."""
    issues = []
    suggestions = []
    segments = []

    for title, body in split_segments(text):
        mode, seg_issues, seg_suggestions = check_segment(body)
        segments.append({"segment": title, "mode": mode, "issues": seg_issues, "suggestions": seg_suggestions})
        issues += [f"[{title}] {i}" for i in seg_issues]
        suggestions += [f"[{title}] {s}" for s in seg_suggestions]

    # Emotion labels used as actor directives, e.g. "很悲伤地说", "表现得很愤怒"
    for label in EMOTION_LABELS:
        performance_patterns = [
            rf"(?:很|非常|特别|十分|有点|有些){label}",
            rf"{label}(?:地|着)?(?:说|笑|哭|喊|叫)",
            rf"表现(?:得)?(?:很|非常|特别|十分)?{label}",
            rf"(?:显得|看起来)(?:很|非常|特别|十分)?{label}",
        ]
        for pattern in performance_patterns:
            if re.search(pattern, text):
                issues.append(f"发现孤立情绪标签：'{label}'，建议改写成可见动作")
                break

    # Time codes (support hyphen, tilde, em-dash, en-dash, and 到)
    time_codes = re.findall(r"\d+\.?\d*\s*[-~—–到]\s*\d+\.?\d*\s*[秒s]", text)
    if not time_codes:
        issues.append("未发现明确时间码")

    au_matches = re.findall(r"AU\d+", text)
    if not au_matches and any(s["mode"] == "电影精品" for s in segments):
        suggestions.append("关键表情处可补充 AU 编码做辅助校准（必须配人话描述）")

    jump_patterns = [
        r"情绪直接(?:变成|跳到)",
        r"直接(?:变成|跳到)(?:悲伤|愤怒|开心|恐惧|厌恶|羞愧|惊讶)",
        r"突然(?:变成|跳到)(?:悲伤|愤怒|开心|恐惧|厌恶|羞愧|惊讶)",
    ]
    for pattern in jump_patterns:
        if re.search(pattern, text):
            issues.append("可能存在情绪跳跃，建议增加保护层失效的过渡")
            break

    dim_count = sum(1 for dim in DIMENSIONS if dim in text)
    if dim_count == len(DIMENSIONS):
        suggestions.append("提示词覆盖很全，确认是否每个镜头都需要八维细写；日常镜头可以轻量处理")

    return {
        "segment_count": len(segments),
        "segments": segments,
        "issues": issues,
        "suggestions": suggestions,
        "au_count": len(au_matches),
        "time_code_count": len(time_codes),
        "pass": len(issues) == 0,
    }


def analyze_scene(text: str) -> dict:
    """Analyze a single scene fragment and suggest detail level."""
    scene_type = classify_scene(text)
    needs_8dim = scene_type in ("情绪递进", "对手戏", "内心戏")
    return {
        "scene_type": scene_type,
        "needs_8_dimensions": needs_8dim,
        "suggested_level": "八维公式细写" if needs_8dim else "轻量表演描述",
        "reason": "包含明显情绪转折或反应链" if needs_8dim else "偏向日常动作或过渡",
    }


def build_prompt(data: dict) -> str:
    """Build a structured performance segment from an 8-dimension JSON object."""
    lines = []
    lines.append("【表演控制】")
    for dim in DIMENSIONS:
        value = data.get(dim, "")
        if value:
            lines.append(f"{dim}：{value}")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="yyl-video-prompt helper")
    parser.add_argument("--validate", help="Validate a prompt file (one or more '## 段N' segments)")
    parser.add_argument("--analyze-scene", help="Analyze a scene fragment file")
    parser.add_argument("--build", help="Build an 8-dimension performance segment from JSON")
    args = parser.parse_args()

    if args.validate:
        text = open(args.validate, encoding="utf-8").read()
        result = validate_prompt(text)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(0 if result["pass"] else 1)

    if args.analyze_scene:
        text = open(args.analyze_scene, encoding="utf-8").read()
        result = analyze_scene(text)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(0)

    if args.build:
        data = json.loads(open(args.build, encoding="utf-8").read())
        print(build_prompt(data))
        sys.exit(0)

    parser.print_help()


if __name__ == "__main__":
    main()
