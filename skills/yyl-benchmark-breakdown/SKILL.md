---
name: yyl-benchmark-breakdown
description: 拆解对标账号 / 竞品内容——丢一个链接进来,自动识别平台(抖音/小红书/B站/YouTube/公众号)和粒度(单条 or 整个账号),抓取内容后输出三件套:可复用爆款公式、画面+口播逐段拆解、人设与内容定位,并自动存档到 benchmarks/。短视频自动下载 + 转写口播 + 抽视觉帧(contact sheet 多模态读图),不只看 caption。当用户说「拆解这个账号/视频/笔记」「分析对标/竞品」「这条为什么火」「给链接拆内容」「teardown」「看看别人怎么做的」时使用。抓不到内容会引导粘贴文案/字幕,绝不直接报错。
---

# 对标账号拆解 Skill

做一件事:**给一个链接,把对方的内容拆到能复用的程度。**

产出固定三件套(见 `references/output-template.md`):
1. **可复用爆款公式** —— 提炼成能直接套用的选题套路 + 结构模板 + 视觉公式。
2. **画面 + 口播逐段拆解** —— 时间轴对齐,逐段标注画面/口播/钩子/节奏/转折/CTA + 两者协同方式。
3. **人设与内容定位** —— 人设标签、视觉符号、内容矩阵、差异化打法。

> 这是**分析型** skill,产出 markdown 报告,不产图。

## 工作流(Claude 做判断,流程做兜底)

0. **首次或换机器时,先自检依赖**:
   - 跑 `bash scripts/check-deps.sh`。任何「✗」按提示装,详见 `INSTALL.md`。
   - 必需:本地 Douyin_TikTok_Download_API(`localhost:80`)、ffmpeg、openai-whisper。
   - 可选:TikHub key(拆小红书/YouTube 备用)、Jina Reader(网页兜底,免费无需 key)。

1. **识别**:从 URL 判断平台 + 粒度(单条/账号)。规则见 `references/fetch-playbook.md`。
   - 拿不准粒度就先按单条处理,抓到页面再修正。

2. **取数(逐级回退,不要在第一级失败就停)**。细节、端点、命令见 `references/fetch-playbook.md`。
   - **① 本地下载 API(主力)**:`curl http://localhost:80/api/hybrid/video_data?url=...` —— **抖音 / TikTok / Bilibili** 三平台,免费、字段全、能拿下载地址。`docker ps | grep douyin` 确认在跑。
   - **② TikHub(备用)**:小红书、YouTube、快手、海外平台等本地 API 不覆盖时用。需要 `TIKHUB_API_KEY` 环境变量。
   - **③ Jina Reader**:公众号文章、普通网页、纯图文兜底,`curl https://r.jina.ai/<url>`。
   - **④ 引导粘贴**:还拿不到 → 让用户发文案/字幕/截图,**不报错**。
   - 取到素材先回显一句「我抓到了什么」(平台/字段/缺什么),再决定是否进入转写。

3. **短视频必做:下载 + 转写口播 + 抽视觉帧**(三样都缺不可)
   - 抖音 / B站 / TikTok / YouTube 单条 → 用 `download_addr` 下视频 → `ffmpeg` 抽音轨 → `whisper --model medium --language Chinese` 转写 → `ffmpeg` 场景检测 + 节奏采样 + 拼 contact sheet。
   - 抽完帧**用 Read 工具把 `/tmp/bm/sheet.jpg` 喂给自己看**——多模态读图是视觉拆解的核心证据。
   - 图文笔记 / 公众号文章 → 跳过下载/转写,但小红书图文要把图序当作"视觉脚本"看。
   - 命令模板见 `references/fetch-playbook.md` 第 3 节。

4. **拆解**:按通用四层 + 视觉七维 + 平台特化分析。
   - 脚本/结构/选题/转化 → `references/breakdown-framework.md`
   - 画面层(视觉钩子/景别/切点节奏/字幕/视觉符号/色调/场景调度)→ `references/visual-framework.md`
   - 单条 → 深拆这一条,**画面与口播必须时间轴对齐**(看协同/互补/错位/预告/强调)。
   - 账号 → 先抓 5–15 条样本,找**重复出现的规律**(选题、结构、视觉符号、发布、互动),再挑 1–2 条代表作深拆。

5. **输出 + 存档**:按 `references/output-template.md` 生成报告,**同时存一份**到
   `benchmarks/<平台>-<账号名>/<日期>-<标题slug>.md`(目录不存在就建)。
   存档是第二阶段「长期对标库」的地基,每次都存。

6. **收尾**:报告末尾给「**这条/这个账号最值得我抄的 3 个点**」+ 一句可执行的下一步建议。

## 铁律

- **永不空手而归**:逐级回退走完;真抓不到就引导粘贴,绝不只甩一句「抓取失败」。
- **短视频必转写 + 必读图**:caption + 数据不够,**口播 + 画面 contact sheet 两个证据都要**,缺一拆不全。
- **要可复用,不要复述**:别复述对方讲了什么/拍了什么,要提炼**为什么这么做、我怎么套用**。
- **基于证据**:数据、原句来自实际抓取;抓不到的指标标「未获取」,不要编。
- **第一性**:每个结论回到「它解决了观众什么问题 / 戳了什么情绪」,不堆术语。
- **始终存档**到 `benchmarks/`,文件名含平台、账号、日期。

## 文件

- `INSTALL.md` —— 依赖安装指南(给人看)+ 常见问题。
- `scripts/check-deps.sh` —— 一键自检 6 项依赖,缺什么给装的命令。
- `references/fetch-playbook.md` —— ★开工先读:平台/粒度识别表、四级取数回退、下载+转写+抽帧命令、粘贴引导话术。
- `references/breakdown-framework.md` —— 通用四层拆解 + 各平台特化(脚本/结构层) + 爆款公式提炼法。
- `references/visual-framework.md` —— ★短视频必读:画面七维拆解 + 视觉/口播时间轴对齐 + 视觉公式提炼法。
- `references/output-template.md` —— 三件套交付模板(已含画面+口播对齐表) + 存档命名约定。

## 第二阶段(暂未实现,已留地基)

- **长期对标账号库**:基于 `benchmarks/` 里沉淀的多份拆解,做跨账号/跨时间的规律汇总(谁的哪类选题稳定爆、行业共性、可追踪趋势)。
- **长视频转写优化**:>15 分钟视频自动切片 + 并行转写;或接商业 API(飞书妙记/通义听悟)。
- **小红书自动化**:接 MediaCrawler 自托管或截图视觉读,绕过 TikHub 的小红书付费墙。

等单链接拆解打磨稳了再做。
