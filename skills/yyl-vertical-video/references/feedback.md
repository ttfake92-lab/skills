# 用户反馈与落实位置

复盘只写本 Skill：默认值改 SKILL.md 的版式表，做法改 film/split.js 或 scripts/，坑写 SKILL.md「坑」，这里按日期记来源和证据。单片特例写任务的 TASK.md，不写这里。

## 2026-10-29 · 20261029-ai-edit-vertical（v1 → v2，用户定稿 v2）

| 反馈 | 定为 | 落实 | 证据 |
|---|---|---|---|
| 口播默认 1.3 倍速，气口 80 ms，整体节奏快一点 | 本 Skill 默认 | SKILL.md 流程 1、版式表「语速」；`scripts/retime.py`（配音阶段 `--speed 1 --gap 0.08`；已有数字人直接处理视频）；pipeline.md §1 | v2：86.6 s → 62.2 s，50 处停顿剪短，停顿中位 81 ms、最长 103 ms |
| 全片保持深色，白色背景段视觉太跳 | 本 Skill 默认 | SKILL.md 流程 6、版式表「背景」；beats.md 不再写 `theme`；reference-analysis.md「没照搬」 | v2 的 gate 质检段为深色 |
| 文字底板要有苹果液态玻璃质感 | 本 Skill 默认 | `film/split.js` `glass()`（背景模糊 + 饱和 + 提亮 + 1.07 倍透镜、烟灰色底、顶部高光、内缘柔光、高光描边、入场光带）、`env()` 弹性入场、`drawBg()` 两团漂移光晕；版式表「液态玻璃卡片」 | v2 抽帧 |
| 字体都用衬线 | 本 Skill 默认 | `serif()` 取代无衬线：宋体 Light/Regular/Bold/Black + Instrument Serif Italic；只有代码编辑器保留等宽；版式表「字体」 | v2 抽帧 |
| 上方重点花字适当拉高 | 本 Skill 默认 | `reveal()` 的 `sy`；分段标题 1.22 倍、CTA 关键词 1.16 倍；版式表「分段标题」 | v2 抽帧 |
| 数字人默认 Avatar V | 全项目数字人默认 | docs/macbook/HEYGEN.md（HeyGen 工具文档）、SKILL.md 流程 2 | job 638fa8f6…，70 credits |

自己发现并修掉的（没有用户反馈，属于实现缺陷）：人物卡背景没盖到画面底边、orbit 压标题、retime 叠化导致音画漂移。见 SKILL.md「坑」。
