---
name: college-application
description: 通过 Agent 对话帮助中国高考考生完成志愿填报决策：先做有科学依据的性格与职业兴趣测评，再研究适合的职业、专业和行业，最后结合省份、选科、分数/位次与官方招生数据生成可追溯来源的 HTML 报告。用户提到高考志愿、college application、选大学、选专业、性格测试、职业方向、行业前景、投档线、录取概率、冲稳保或志愿模拟时使用。
---

# College Application

把志愿填报视为“认识自己 → 理解职业/专业/行业 → 用招生数据约束选择 → 生成可审计报告”的决策过程。主交互在 Agent 对话中完成；HTML 只用于最终报告展示，不再作为主要填写入口。

## 不可省略的声明

启动后先告诉用户：本服务仅供高考志愿决策参考，所有性格分析、职业建议、行业判断和录取估算都基于公开来源与模型推断，不能替代各省教育考试院、高校招生章程、官方志愿填报系统或老师/家长意见；最终选择必须交叉验证。最终 HTML 报告顶部和底部也必须显示同样提示。

## 工作区文件

- `CANDIDATE.md`：考生画像、性格测评摘要、职业方向假设、高考信息。格式见 [CANDIDATE-FORMAT.md](./CANDIDATE-FORMAT.md)。
- `PERSONALITY-REPORT.md`：性格测试计分、解释、职业方向假设。格式见 [PERSONALITY-REPORT-FORMAT.md](./PERSONALITY-REPORT-FORMAT.md)。
- `SOURCES.md`：所有理论、行业、专业、招生数据的来源台账。格式见 [SOURCES-FORMAT.md](./SOURCES-FORMAT.md)。
- `plans/*.md`：职业/专业研究、志愿建议、最终方案。格式见 [PLAN-FORMAT.md](./PLAN-FORMAT.md)。
- `final-report.html`：最终可浏览报告，使用 [assets/final-report-template.html](./assets/final-report-template.html)。
- `history/events.jsonl`、`decision-records/*.md`、`audits/*.md`：如需长期跟踪或独立审计，沿用对应格式文件。

旧版 `assets/college-application-template.html` 与 `scripts/wait_for_request.py` / `complete_request.py` / `update_progress.py` / `fail_request.py` 属于网页任务队列工作台的 legacy 兼容资产。新版主流程不要要求用户打开网页填写，也不要把等待器作为必经步骤。

## 固定对话流程

### 1. 生成性格测试 HTML 表单

使用脚本从 [assets/personality-assessment-form.html](./assets/personality-assessment-form.html) 生成一份静态 HTML 表单，交给用户在浏览器里填写：

```bash
python3 <skill-dir>/scripts/create_assessment.py \
  --workspace <考生工作区绝对路径> \
  --open
```

`--open` 会自动用系统默认浏览器打开表单，避免用户自己去文件夹里找。脚本默认输出类似 `<workspace>/personality-assessment-YYYY-MM-DD.html` 的文件路径。把这个文件路径告诉用户，并说明：请用浏览器打开 HTML 表单，填完后点击“下载给 Agent 的 JSON”，再把下载的 JSON 文件发回、粘贴内容，或授权 Agent 读取该文件。不要要求用户在终端聊天里逐题填写。

Markdown 模板 [assets/personality-assessment-template.md](./assets/personality-assessment-template.md) 只作为 fallback：用户无法打开 HTML 时，可运行 `create_assessment.py --format md` 生成可填写 Markdown。

表格基于 RIASEC 职业兴趣与 Mini-IPIP 大五人格短量表，总计 32 题，1–5 分。

### 2. 生成性格与职业方向报告

解析用户发回的性格测试结果 JSON（或 fallback Markdown），按模板内规则计分。计分后先生成一份可读 HTML 报告，方便用户确认自己看得懂：

```bash
python3 <skill-dir>/scripts/render_personality_report.py \
  --input <personality-assessment-result.json> \
  --output <考生工作区绝对路径>/personality-report.html
```

报告应先给白话重点结论，再把完整得分表和局限放在后面展开。

- RIASEC：得到前三码，如 `I-A-S`。
- Big Five：计算开放性、尽责性、外向性、宜人性、神经质相对水平，反向题必须倒转。
- 输出 3–6 个职业方向假设，每个方向都写“支持证据 / 反证或风险 / 需要现实验证的问题”。

性格测试只能作为方向线索，不得把测试结果写成诊断或命运结论。

### 3. 职业、专业与行业深度研究

围绕职业方向假设生成 3–6 个专业簇。每个专业簇必须研究：

- 真实学习内容、核心课程、培养方案差异。
- 真实工作日常、职业出口、跨专业路径、继续深造路径。
- 行业需求、地域分布、学历门槛、资格门槛、AI/自动化影响。
- 适合与不适合该方向的证据。
- 可点击、可追溯来源。

优先来源：教育部专业目录、阳光高考、高校官网培养方案/招生章程/就业质量报告、国家统计局、人社部门、行业主管部门、权威行业协会。招聘网站和商业报告只能作辅助信号，必须说明样本偏差。

### 4. 生成高考信息 HTML 表单

使用脚本从 [assets/admission-info-form.html](./assets/admission-info-form.html) 生成一份静态 HTML 表单，交给用户在浏览器里填写：

```bash
python3 <skill-dir>/scripts/create_admission_info.py \
  --workspace <考生工作区绝对路径> \
  --open
```

`--open` 会自动用系统默认浏览器打开表单，避免用户自己去文件夹里找。脚本默认输出类似 `<workspace>/admission-info-YYYY-MM-DD.html` 的文件路径。把这个文件路径告诉用户，并说明：请用浏览器打开 HTML 表单，填完后点击“下载给 Agent 的 JSON”，再把下载的 JSON 文件发回、粘贴内容，或授权 Agent 读取该文件。不要要求用户在终端聊天里逐项填写。

Markdown 模板 [assets/admission-info-template.md](./assets/admission-info-template.md) 只作为 fallback：用户无法打开 HTML 时，可运行 `create_admission_info.py --format md` 生成可填写 Markdown。

高考信息文档必须覆盖：

| 项目 | 要求 |
|---|---|
| 招生省份 | 必填 |
| 填报年份 | 默认当前年份，可修改 |
| 意向填报地区 | 可多个；区分必须/优先/无所谓 |
| 考试模式 | 由省份按 [references/province-exam-mode.md](./references/province-exam-mode.md) 自动带出并复核 |
| 选科 | 按 3+3 或 3+1+2 校验；物理与历史互斥 |
| 高考成绩 / 全省位次 | 至少填一项；位次优先 |
| 批次/类别/特殊资格 | 如普通类、专项计划、中外合作等 |
| 学费、家庭等现实约束 | 可选但要主动提示；不主动收集健康/体检隐私信息，相关专业限制由用户自行查招生章程 |

信息不完整时先补信息，不要直接生成志愿建议。

### 5. 录取机会估算与志愿建议

按 [references/admission-estimation.md](./references/admission-estimation.md) 执行。优先比较位次；只有满足至少 3 个可比年份、当年计划已发布、口径一致、来源可核验时，才可输出区间式概率。否则只输出“冲刺 / 有机会 / 较稳 / 兜底”定性等级，并明确缺少哪些数据。

严禁把聚合站、自媒体、论坛或未注明年份的投档线作为关键依据。关键招生事实必须回到省教育考试院、教育部阳光高考或高校本科招生网复核。

### Agent 主动取数策略

如果用户只提供分数、没提供位次，Agent 应先尝试从省教育考试院官方一分一段表获取对应年份的位次参考；若当年数据未发布，可用最近年份估算“参考位次”，但必须标注不可替代真实位次。只有官方来源找不到、页面失效或用户所在省数据不可获得时，才要求用户上传/提供一分一段表、招生计划或投档线文件。

### 6. 生成最终 HTML 报告

最终报告优先使用脚本渲染：

```bash
python3 <skill-dir>/scripts/render_report.py \
  --workspace <考生工作区绝对路径> \
  --output <考生工作区绝对路径>/final-report.html
```

脚本读取工作区中的 `research.json`、`CANDIDATE.md`、`PERSONALITY-REPORT.md`、`SOURCES.md`，套用 [assets/final-report-template.html](./assets/final-report-template.html)。缺字段时显示“待补充 / 无法查证”，不得自动编造内容。

最终报告先展示重点结论：方向是否匹配、当前数据够不够、下一步要补什么。完整性格得分、专业行业细节、方法、不确定性和来源台账放到后面折叠展开，避免用户一打开就被专业术语淹没。

最终报告至少包含：

- 顶部“仅供参考 / 必须交叉验证 / 不构成录取承诺”声明。
- 性格测试结果：RIASEC、Big Five、解释与局限。
- 适合职业方向与专业簇：匹配证据、反证、现实探索建议。
- 职业/专业/行业深度分析：学习内容、工作日常、趋势、门槛、风险。
- 高考信息与录取分析：省份、模式、选科、分数/位次、数据口径、冲稳保建议。
- 来源台账：完整 URL、发布机构、年份/口径、最后核验日期、状态。
- 无法查证或数据不足的结论必须单独标出，不得混在确定结论里。

### 7. 可选独立审计

用户要求复核、报告用于重要决策、或 Agent 对关键来源不确定时，启动全新 subagent 按 [AUDIT-FORMAT.md](./AUDIT-FORMAT.md) 独立审计。审计不通过时，不得显示“可用于正式填报”。

## 来源与诚实边界

- 每个外部事实、行业判断、专业信息、招生规则、投档数据和概率输入都必须有 `source_ids`，并能追溯到 `SOURCES.md` 的完整 URL。
- 搜索结果摘要不是来源；Tavily/WebSearch 只能发现链接，不能直接支撑结论。
- 页面失效、来源冲突、年份不匹配、口径不一致时，要明确写“无法查证 / 存在冲突 / 仅作辅助线索”。
- 不输出“稳录”“保证录取”“100%”等承诺性措辞。
