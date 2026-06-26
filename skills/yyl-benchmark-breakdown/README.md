# yyl-benchmark-breakdown

> 给一个链接,把对方的内容拆到能复用的程度。

Claude Code 的对标账号拆解 skill。丢一个抖音 / 小红书 / B 站 / YouTube / 公众号链接,自动取数 → 转写口播 → 抽视觉帧 → 输出三件套:

1. **可复用爆款公式** —— 选题 + 结构 + 视觉钩子 + 剪辑节奏 公式,带「套到我」的改编示例
2. **画面 + 口播逐段拆解** —— 时间轴对齐,段段标注景别 / 切点 / 字幕 / 口播 + 两者协同方式
3. **人设与内容定位** —— 听觉记忆点 + 视觉符号 + 内容矩阵 + 差异化打法

所有拆解会自动存档到 `benchmarks/<平台>-<账号>/` 沉淀成对标库。

## 工作流

```
你丢链接
   ↓
平台 + 粒度识别(抖音/B站/小红书... · 单条/账号)
   ↓
取数(本地 Douyin_TikTok_Download_API → TikHub → Jina → 粘贴托底)
   ↓
短视频:下载 → ffmpeg 抽音轨 → whisper 转写口播
              ↓
         ffmpeg 场景检测 + 节奏采样 → 拼 contact sheet → 多模态读图
   ↓
五层拆解(选题 / 结构 / 表达-文字 / 表达-画面 / 转化)+ 各平台特化维度
   ↓
三件套报告(画面+口播对齐表)+ 存档 + 「最值得我抄的 N 个点」+ 下一步建议
```

## 快速开始

```bash
# 1) 克隆到你的 skills 目录
git clone <this-repo> ~/.claude/skills/yyl-benchmark-breakdown

# 2) 装依赖(必需 3 项)— 详见 INSTALL.md
docker pull evil0ctal/douyin_tiktok_download_api:latest
docker run -d --name douyin_tiktok_api -p 80:80 evil0ctal/douyin_tiktok_download_api
brew install ffmpeg openai-whisper          # macOS;Linux 看 INSTALL.md

# 3) 自检
bash ~/.claude/skills/yyl-benchmark-breakdown/scripts/check-deps.sh

# 4) 在 Claude Code 里说:「拆解这条:<链接>」
```

## 依赖

| 依赖 | 必需 | 用途 |
|---|---|---|
| [Douyin_TikTok_Download_API](https://github.com/Evil0ctal/Douyin_TikTok_Download_API) | ✅ | 抖音/TikTok/B站取数主力,本地自托管 |
| [ffmpeg](https://ffmpeg.org/) | ✅ | 抽音轨 |
| [openai-whisper](https://github.com/openai/whisper) | ✅ | 转写口播 |
| [TikHub](https://tikhub.io/) | 可选 | 小红书 / YouTube / 海外平台 |
| [Jina Reader](https://jina.ai/reader/) | 可选 | 公众号 / 普通网页 / 图文兜底 |

完整安装见 [INSTALL.md](INSTALL.md)。

## 文件结构

```
yyl-benchmark-breakdown/
├── SKILL.md                        # 主流程(Claude 读)
├── INSTALL.md                      # 依赖安装指南(人读)
├── README.md                       # 你正在看
├── scripts/
│   └── check-deps.sh               # 一键自检依赖
├── references/
│   ├── fetch-playbook.md           # 取数手册:四级回退 + 下载+转写+抽帧命令
│   ├── breakdown-framework.md      # 通用四层 + 各平台特化(脚本/结构层)
│   ├── visual-framework.md         # ★ 画面七维 + 视觉/口播时间轴对齐 + 视觉公式
│   └── output-template.md          # 三件套模板(含画面+口播对齐表)+ 存档约定
└── benchmarks/                     # 拆解存档(自动生成)
    └── <平台>-<账号>/
        └── <日期>-<标题>.md
```

## 设计原则

- **永不空手而归**:四级回退,真抓不到就引导粘贴,绝不只甩「失败」。
- **短视频必转写 + 必读图**:caption + 数据不够,口播 + 画面 contact sheet 两个证据都要,缺一拆不全。
- **要可复用,不要复述**:每个结论都回到「为什么这么做、我怎么套用」。
- **基于证据**:数据原句来自实际抓取;缺的指标如实标「未获取」,不编。
- **始终存档**:每次拆解都落地到 `benchmarks/`,为长期对标库铺地基。

## 路线图

第二阶段(规划中):
- **长期对标账号库** —— 基于 `benchmarks/` 跨账号/跨时间汇总规律
- **长视频转写优化** —— >15 分钟自动切片 + 并行;或接飞书妙记/通义听悟
- **小红书自动化** —— 接 MediaCrawler 自托管或截图视觉读,绕过 TikHub 付费墙

## License

MIT。
