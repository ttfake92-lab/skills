# research.json 数据协议

不得写入示例、占位或推测数据。没有完成真实检索时保留空数组，并将 `status` 标为 `not_started`、`researching` 或 `blocked`。

```json
{
  "status": "ready",
  "generated_at": "2026-06-24T12:00:00+08:00",
  "personality_profile": {
    "assessment_file": "personality-assessment-2026-06-24.md",
    "report_file": "PERSONALITY-REPORT.md",
    "riasec": {
      "scores": {"R": 0, "I": 0, "A": 0, "S": 0, "E": 0, "C": 0},
      "top_code": "I-A-S",
      "interpretation": "只作为职业兴趣线索，不是结论"
    },
    "big_five": {
      "openness": {"score": 0, "level": "low | medium | high"},
      "conscientiousness": {"score": 0, "level": "low | medium | high"},
      "extraversion": {"score": 0, "level": "low | medium | high"},
      "agreeableness": {"score": 0, "level": "low | medium | high"},
      "neuroticism": {"score": 0, "level": "low | medium | high"}
    },
    "limitations": ["测试结果仅用于生成假设，需结合用户经历和现实探索验证"],
    "source_ids": ["SRC-001", "SRC-002"]
  },
  "career_directions": [
    {
      "id": "career-direction-id",
      "name": "职业方向名称",
      "match_evidence": ["来自 RIASEC / Big Five / 用户经历的证据"],
      "counter_evidence": ["不匹配或尚待验证之处"],
      "work_realities": ["真实工作内容"],
      "related_major_families": ["对应专业门类或专业簇"],
      "industry_questions": ["后续需要研究的问题"],
      "source_ids": ["SRC-003"]
    }
  ],
  "major_clusters": [
    {
      "id": "major-cluster-id",
      "name": "专业簇名称",
      "career_direction_ids": ["career-direction-id"],
      "match_reasons": ["引用用户回答、测评结果和研究来源的匹配理由"],
      "counter_evidence": ["不匹配或尚待验证之处"],
      "courses": ["真实课程"],
      "work_realities": ["真实工作内容"],
      "career_paths": ["职业出口"],
      "industry_outlook": "有来源支持的行业判断",
      "risks": ["学历门槛、地域、周期、AI 等"],
      "source_ids": ["SRC-001"],
      "deep_dive": {
        "representative_universities": ["第一梯队院校"],
        "training_plan_highlights": ["头部院校培养方案的关键差异"],
        "employment_signals": ["就业质量报告、薪资带宽、岗位需求"],
        "notes": "补充判断（如该专业适合谁/不适合谁）",
        "source_ids": ["SRC-020", "SRC-021"]
      }
    }
  ],
  "industry_sources": [],
  "admission_records": [
    {
      "application_id": "院校专业组唯一 ID",
      "province": "招生省份",
      "year": 2025,
      "university": "院校",
      "group_or_major": "专业组或专业",
      "minimum_score": 0,
      "minimum_rank": 0,
      "plan_count": 0,
      "source_ids": ["SRC-010"]
    }
  ],
  "applications": [
    {
      "id": "application-id",
      "university": "院校",
      "group_or_major": "专业组或专业",
      "major_cluster_id": "major-cluster-id",
      "campus": "校区",
      "city": "校区所在城市",
      "tuition": "学费",
      "restrictions": ["限制"],
      "risk_level": "冲刺 | 有机会 | 较稳 | 兜底",
      "chance_range": "45%–65%（可选，仅在有足够 3 年以上可比数据时才给）",
      "city_match": "hard_satisfied | soft_satisfied | violates_preference",
      "method_summary": "可复算方法摘要",
      "rationale": "为什么推荐这条：匹配的职业方向、专业簇、城市契合度、风险层、调剂提示等",
      "source_ids": ["SRC-010", "SRC-011"]
    }
  ],
  "sources": [
    {
      "id": "SRC-001",
      "claim": "该来源支持的声明",
      "publisher": "发布机构",
      "url": "https://完整链接",
      "published_or_data_year": "2025",
      "scope": "适用范围",
      "level": "官方原始",
      "verified_at": "2026-06-24",
      "status": "verified"
    }
  ],
  "methodology": {
    "description": "录取机会估算方法",
    "comparable_years": [2023, 2024, 2025],
    "limitations": ["不确定性"]
  },
  "audit": null
}
```

每项理论、行业、专业或录取结论必须能通过 `source_ids` 追溯到 `sources` 中可访问的完整链接。无法查证的内容不得写成确定结论，必须标记为限制或待核验。

## personality_profile 规则

- 只能来自用户填写的性格测试表和公开计分规则。
- RIASEC 与 Big Five 都只能作为方向线索，不得作为诊断或最终专业结论。
- 理论来源、量表来源和职业映射来源必须进入 `sources`。

## career_directions 规则

- 每个职业方向都必须有 `match_evidence` 和 `counter_evidence`。
- 职业方向只是专业/行业研究的输入，不直接等同于最终志愿。
- 后续专业簇必须通过官方专业目录、培养方案和行业来源进一步核验。

## major_deep_dive 增量结果格式

deep_dive 任务**不要**返回完整 `research.json`。只返回增量结果：

```json
{
  "deep_dive_payload": {
    "cluster-ai-core": {
      "representative_universities": ["..."],
      "training_plan_highlights": ["..."],
      "employment_signals": ["..."],
      "notes": "...",
      "source_ids": ["SRC-020", "SRC-021"]
    }
  },
  "sources": [
    {"id": "SRC-020", "...": "..."}
  ]
}
```

`complete_request.py` 是旧版网页任务队列的兼容脚本。若继续使用旧流程，它会把这块挂到对应簇的 `deep_dive` 字段，并把新 sources 追加到顶级 `sources`（按 id 去重）。新版对话流程可直接维护同样的数据结构。

## application_recommendation 增量结果格式

录取建议任务**不要**返回完整 `research.json`。只返回新的 `applications` 列表 + 用到的新 sources：

```json
{
  "applications": [
    { "id": "...", "university": "...", "risk_level": "冲刺", "city_match": "soft_satisfied", "...": "..." }
  ],
  "sources": [
    {"id": "SRC-030", "...": "..."}
  ],
  "methodology": {
    "description": "录取机会估算方法或定性等级判断依据",
    "comparable_years": [2023, 2024, 2025],
    "limitations": ["未取得近 3 年完整投档数据，仅给定性等级"]
  }
}
```

旧版 `complete_request.py` 会用新 `applications` 整体替换原 `applications`，并把 sources 追加去重、写入 `methodology`。新版对话流程生成最终报告时也应遵守同样边界：同一批 candidate 输入对应一次完整推荐，数据不足时只输出定性等级。
