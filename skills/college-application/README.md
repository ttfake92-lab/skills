# College Application

高考志愿决策辅助 Skill。

它把填报流程拆成 4 个阶段：

1. 性格与职业兴趣测评
2. 职业 / 专业 / 行业研究
3. 高考信息收集
4. 最终 HTML 报告生成

这个 Skill 的主交互在 Agent 对话里完成，HTML 页面主要用于填写输入和生成报告。

## 这是什么

一个基于 Agent 的高考志愿决策辅助工具，目标不是替学生做决定，而是：

- 先了解人的兴趣倾向
- 再研究职业、专业和行业
- 最后结合省份、选科、分数 / 位次和官方招生数据生成参考报告

## 设计目标

- 不需要用户会写 Markdown
- 不依赖网页任务队列、心跳、后台轮询
- 所有用户输入都通过浏览器 HTML 表单
- 所有页面离线可用，不上传数据
- 最终报告重点结论优先，详细内容折叠展示

## 安装与依赖

### 系统要求

- Python 3.9+
- macOS / Windows / Linux 均可
- 一个能打开本地 HTML 文件的浏览器

### Python 依赖

当前脚本主要使用 Python 标准库：

- `argparse`
- `json`
- `pathlib`
- `datetime`
- `html`
- `subprocess`
- `sys`

**当前不需要安装第三方 pip 包。**

如果你希望直接运行：

```bash
python3 scripts/create_assessment.py --help
python3 scripts/create_admission_info.py --help
python3 scripts/render_personality_report.py --help
python3 scripts/render_report.py --help
```

### 可选依赖

如果后续你要扩展联网研究能力，某些工具链可能需要额外配置，例如：

- Chrome / Chromium（用于真实浏览器取数）
- Tavily API Key（用于更稳定的官方 URL 发现）

但**基础填写、报告生成、本地演示流程本身不依赖这些**。

## 快速开始

### 1. 生成性格测试表单

```bash
python3 scripts/create_assessment.py \
  --workspace <workspace> \
  --open
```

生成文件示例：

```text
<personality-assessment-YYYY-MM-DD.html>
```

用户在浏览器填写后，点击“下载给 Agent 的 JSON”。

### 2. 生成性格报告

```bash
python3 scripts/render_personality_report.py \
  --input <workspace>/personality-assessment-result.json \
  --output <workspace>/personality-report.html
```

### 3. 生成高考信息表单

```bash
python3 scripts/create_admission_info.py \
  --workspace <workspace> \
  --open
```

生成文件示例：

```text
<admission-info-YYYY-MM-DD.html>
```

用户在浏览器填写后，点击“下载给 Agent 的 JSON”。

### 4. 生成最终报告

```bash
python3 scripts/render_report.py \
  --workspace <workspace> \
  --output <workspace>/final-report.html
```

## 输出文件结构

一个典型的 workspace 里会有：

- `personality-assessment-YYYY-MM-DD.html`
- `personality-assessment-result.json`
- `personality-report.html`
- `admission-info-YYYY-MM-DD.html`
- `admission-info-result.json`
- `research.json`
- `CANDIDATE.md`
- `PERSONALITY-REPORT.md`
- `SOURCES.md`
- `plans/*.md`
- `final-report.html`

## 数据边界

这个工具**不是**招生数据库产品。

### 能做的

- 生成性格 / 职业兴趣方向假设
- 研究职业、专业、行业
- 结合省份、选科、位次做方向性判断
- 在有官方数据时做更精确分析
- 生成带来源链接的参考报告

### 不能做的

- 不能替代省教育考试院政策
- 不能替代高校招生章程
- 不能替代官方志愿填报系统
- 不能保证录取
- 不能在没有数据时给出伪精确概率

## 来源要求

所有外部事实、行业判断、招生规则、投档数据和概率输入都要求：

- 完整 URL
- 发布机构
- 年份 / 口径
- 核验日期
- 状态

如果来源不可查证，报告里必须如实说明，不能混在确定结论里。

## 隐私说明

当前流程强调：

- HTML 页面离线可用
- 数据默认不会上传网络
- 健康 / 体检等敏感信息不主动收集
- 用户应避免填写不必要的隐私数据

如果后续接入联网工具或云端服务，必须单独说明数据去向。

## 适合谁用

- 想做一个轻量高考志愿辅助工具的人
- 想把 Agent 对话和 HTML 报告结合的人
- 想开源一套可继续扩展的 Skill 模板的人

## 扩展方向

- 更完整的省份 / 选科标准化输入组件
- 更丰富的可视化报告模板
- 多轮对话式志愿模拟（冲稳保动态调整）
- 与各省官方数据源的深度对接

## License

MIT
