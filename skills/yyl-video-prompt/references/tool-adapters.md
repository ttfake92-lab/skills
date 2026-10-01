# 工具适配：素材引用写法、生成模式、单段上限

提示词正文结构不变，落到具体工具时只改三处：**素材引用写法、生成模式、参数行**。
以下内容来自鱼亦乐的项目实测记录，工具更新后以工具自身的帮助文档为准。

## 素材引用写法

| 工具 | 提示词里怎么引用素材 | 注意 |
|---|---|---|
| 即梦网页端 | `@图片1` / `@视频1` / `@音频1` | 上传顺序即编号 |
| dreamina CLI | 「参考图1 / 参考图2」或「第一张参考图」 | 编号 = `--image` 传入顺序；第一张定身份，第二张定接续状态 |
| LibTV | **`{{Node "节点名"}}`** | 引号要成对；节点必须**已经连线**到生成节点。纯文本「图片1」「参考视频1」无效（2026-08-31 连烧六次的教训） |
| TT AI 平台 | `@图像1` / `@视频1` / `@音频1` | 参考视频必须是公网 URL；本地图片和音频会自动转 base64 |
| 不确定的工具 | `图片1` / `图片2`，并在提示词前列清每张图的用途 | — |
| Sora / Runway / Pika | 不用编号引用 | 这类工具更吃英文连贯散文：把各块内容改写成英文电影化段落，去掉【】标签 |

## 生成模式对照

| 生成模式 | dreamina CLI | LibTV（Seedance 2.5 modeType） | TT AI（seedance-2.5-guanfang） |
|---|---|---|---|
| 纯文生 | `text2video` | `text2video` | 不传素材 |
| 首帧图生 | `image2video` | `singleImage2video` / `image2video`（以模型 schema 为准） | `images` 传 1 张 |
| 首尾帧 | `frames2video` | `frames2video` | `mode=shouweizhen`，`images` 传 2 张 |
| 多图参考 | `multimodal2video`（多个 `--image`） | `mixed2video` | `mode=cankaosheng`，`image_url` 传 3–30 张 |
| 多图故事 | `multiframe2video`（2–20 张，不能设模型和分辨率） | — | — |
| 全能参考（图＋视频＋音频） | `multimodal2video`（`--image` / `--video` / `--audio`） | `mixed2video` | `_quan_neng_mode=quan_neng` |
| 音频驱动 | `multimodal2video --audio`（2–15 秒） | `audio2video` | `audio_url` |
| 视频编辑（保留运镜，改内容） | — | `videoEdit2video` | `_quan_neng_mode=edit` |

## 单段时长与参数

| 工具 / 模型 | 单段时长 | 分辨率 | 画幅要点 |
|---|---|---|---|
| Seedance 2.0（dreamina 等） | ≤ 15 秒 | 普通通道 720p；VIP 通道 1080p | — |
| Seedance 2.5（dreamina） | 4–30 秒（`multimodal2video`、`image2video` 已实测） | 480p / 720p | `multimodal2video` 不传 `--ratio` 时固定 16:9，**竖片必须显式写 `--ratio=9:16`**；`image2video` / `frames2video` 的比例由输入图决定 |
| Seedance 2.5（LibTV） | 4–30 秒 | 480p / 720p / 1080p | `videoEdit2video` 的时长和比例跟随输入视频，输入短于 4 秒会被打回（报错文案说的是别的原因，别被骗） |
| seedance-2.5-guanfang（TT AI） | 4–30 秒 | 480p / 720p / 1080p | 首尾帧、编辑、延长任务只能用 `adaptive` |

## 声音开关

- **dreamina**：没有硬开关。「无背景音乐」只能写在提示词里，模型未必完全遵守。
- **LibTV**：`enableSound=on/off` 是硬开关。要完全无声就直接关掉。
- **TT AI**：按所选模型的参数说明。

## 什么时候不用本 Skill 的高密度写法

**合成 / 编辑类任务**：例如把 A 视频的内容放进 B 里的手机屏幕、`videoEdit2video` 只改背景。这类任务只写三样东西：

1. 第一句用素材引用说清操作：「把 {{Node "B-屏幕内容"}} 的内容完整地做到 {{Node "A-手机实拍"}} 里面的手机屏幕里」
2. 只写画面里最重要的信息：「能看到有 56 万赞，屏幕上还在不停地跳」
3. 「其他的都不要变」一句带过

不写图标形状、颜色、位置，也不写否定清单。描述过度会把本该在画面内部的元素提升到整个画面上。
