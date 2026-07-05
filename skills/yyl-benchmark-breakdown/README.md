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
准备证据包(scripts/prepare-assets.sh:下载 → 转写 → 抽帧/拼图)
   ↓
取数兜底(平台本地 API:Douyin/XHS → TikHub → Jina → 粘贴托底)
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

# 2) 自检前置清单
bash ~/.claude/skills/yyl-benchmark-breakdown/scripts/check-deps.sh

# 3) 如果本地下载 API 缺失且 Docker 已启动,一键拉起
bash ~/.claude/skills/yyl-benchmark-breakdown/scripts/bootstrap-local-apis.sh

# 4) 再自检;通过后就可以拆
bash ~/.claude/skills/yyl-benchmark-breakdown/scripts/check-deps.sh

# 5) 在 Claude Code 里说:「拆解这条:<链接>」
```

如果 Docker / ffmpeg / whisper 缺失,按 [INSTALL.md](INSTALL.md) 先补齐。TikHub 是可选项;需要拆 YouTube、快手、海外平台或想要备用 API 时再配置。

## 一键准备证据包

```bash
bash scripts/prepare-assets.sh "<链接>"
```

这个脚本会完成机械流程:识别平台 → 调本地 API → 下载视频/图片 → 视频转写 → 抽帧/拼 contact sheet → 生成 `manifest.txt`。Claude 再基于证据包做判断和拆解。

## 依赖

| 依赖 | 必需 | 用途 |
|---|---|---|
| [Docker](https://www.docker.com/products/docker-desktop/) | ✅ | 运行本地下载 API |
| [Douyin_TikTok_Download_API](https://github.com/Evil0ctal/Douyin_TikTok_Download_API) | ✅ | 抖音/TikTok/B站取数主力,本地自托管 |
| [XHS-Downloader](https://github.com/JoeanAmier/XHS-Downloader) | ✅ | 小红书图文/视频笔记取数和文件下载,本地自托管 |
| [ffmpeg](https://ffmpeg.org/) | ✅ | 抽音轨 |
| [openai-whisper](https://github.com/openai/whisper) | ✅ | 转写口播 |
| [TikHub](https://tikhub.io/) | 可选 | YouTube / 海外平台 / 小红书备用 |
| [Jina Reader](https://jina.ai/reader/) | 可选 | 公众号 / 普通网页 / 图文兜底 |

完整安装见 [INSTALL.md](INSTALL.md)。

## 文件结构

```
yyl-benchmark-breakdown/
├── SKILL.md                        # 主流程(Claude 读)
├── INSTALL.md                      # 依赖安装指南(人读)
├── README.md                       # 你正在看
├── scripts/
│   ├── bootstrap-local-apis.sh      # 拉起本地 Douyin/XHS 下载 API
│   ├── check-deps.sh               # 一键自检依赖
│   └── prepare-assets.sh           # 下载/转写/抽帧/拼图证据包工作流
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
- **小红书账号级自动化** —— 接 MediaCrawler 自托管,做主页采样、评论和搜索

## License

MIT。作者:鱼亦乐(@yuyile)。
