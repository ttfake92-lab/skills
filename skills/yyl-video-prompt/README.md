# yyl-video-prompt

鱼亦乐的导演式 AI 视频提示词 Skill。把脚本、故事、口播稿、分镜表，或者一句想法，拆成能直接提交生成的分段视频提示词。

适用于 Seedance 2.0 / 2.5、即梦、dreamina、LibTV、TT AI 等视频生成工具。

版本 2.2.0（2026-10-01）

## 两个档位

Skill 会先按脚本风格自动选档：

| 档位 | 适合 | 写法 |
|---|---|---|
| 短视频 | 抖音、小红书节奏的剧情片段、街拍、角色小故事、竖屏短剧 | 一镜到底（以爆款《丹眉》为标杆）／多分镜（以赛博原子为标杆） |
| 电影精品 | 慢节奏剧情、对白、对手戏 | 八维表演公式 + AU 面部编码 + 情绪递进 |

## 安装

从 GitHub 安装（推荐），运行后在列表里选 `yyl-video-prompt`：

```bash
npx skills@latest add ttfake92-lab/skills
```

或者手动安装：把整个 `yyl-video-prompt` 文件夹放进 skills 目录：

- Claude Code，所有项目可用：`~/.claude/skills/yyl-video-prompt/`
- Claude Code，只在某个项目用：`<项目目录>/.claude/skills/yyl-video-prompt/`
- 其他支持 Agent Skills 标准的工具：放进它们各自的 skills 目录

在 Mac 上，用终端一条命令就能装到 Claude Code（压缩包放在「下载」文件夹时）：

```bash
unzip ~/Downloads/yyl-video-prompt-v2.2.0.zip -d ~/.claude/skills/
```

装好后新开一个会话就能用。

## 怎么用

直接把脚本贴给 AI，说「帮我写成视频提示词」。也可以说明平台或风格，例如「抖音短视频」「电影感的剧情戏」。

多段或方向不明确时，它会先发一条消息，列出分段和关键判断，等你确认后再写。

## 文件

| 文件 | 内容 |
|---|---|
| `SKILL.md` | 入口：选档位、工作流、通用规则 |
| `modes/` | 两个档位各自的写法 |
| `examples/` | 标杆示例：《丹眉》、赛博原子、《改名》、表演片段 |
| `REFERENCE.md` | 两档共用：分段、参考图绑定、声音、硬约束、实测教训 |
| `references/` | 各工具的素材引用写法、景别构图运镜速查、摄影词库 |
| `scripts/prompt_builder.py` | 提示词校验脚本，需要 Python 3，无第三方依赖：`python3 scripts/prompt_builder.py --validate 提示词.md` |

## 说明

- 示例里的「图片N」，要按你用的工具换成对应写法，见 `references/tool-adapters.md`。
- AU 面部编码还没有做过出片对照测试。
