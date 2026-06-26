# 取数手册:本地下载 API → TikHub → Jina → 粘贴

目标:**任意链接都能拿到可拆解的内容,且短视频必须有口播。** 优先零成本本地方案,免费额度类 API 作为兜底。**永不空手而归。**

---

## 0. 一次性 setup

跑根目录的 `bash scripts/check-deps.sh` 一键自检。缺什么按提示装,详细说明见 `INSTALL.md`。

**铁律:永远只从环境变量读 key(`TIKHUB_API_KEY` / `JINA_API_KEY`),绝不打印、绝不写进任何文件、绝不进命令历史。**

---

## 1. 平台 + 粒度识别(看 URL)

| 平台 | 域名 | 单条 | 账号主页 |
|---|---|---|---|
| 抖音 | `douyin.com`/`v.douyin.com` | `/video/`、`?modal_id=`、`/note/` | `/user/` |
| 快手 | `kuaishou.com` | `/short-video/` | `/profile/` |
| B站 | `bilibili.com`/`b23.tv` | `/video/BV...` | `space.bilibili.com` |
| TikTok | `tiktok.com` | `/@x/video/` | `/@x` |
| 小红书 | `xiaohongshu.com`/`xhslink.com` | `/explore/`、`/discovery/item/` | `/user/profile/` |
| YouTube | `youtube.com`/`youtu.be` | `/watch`、`/shorts/` | `/@` |
| 公众号 | `mp.weixin.qq.com` | `/s/` | 无 |

---

## 2. 取数路由(逐级回退)

### ① 本地下载 API(主力)—— 抖音 / TikTok / Bilibili
官方支持三平台(README 写明)。**响应快、字段全、零费用、能拿下载地址用于转写。**

```bash
# 通用解析(自动判平台)
curl -s "http://localhost:80/api/hybrid/video_data?url=<urlencoded>&minimal=false"
# 或具体端点:抖音单视频
curl -s "http://localhost:80/api/douyin/web/fetch_one_video?aweme_id=<id>"
# 账号作品流(找规律用)
curl -s "http://localhost:80/api/douyin/web/fetch_user_post_videos?sec_user_id=<sid>"
# 评论
curl -s "http://localhost:80/api/douyin/web/fetch_video_comments?aweme_id=<id>"
```

关键字段位置:
- `data.desc` — 标题/文案完整版
- `data.video.download_addr.url_list[0]` — 视频下载地址(**转写源**)
- `data.video.play_addr.url_list[0]` — 备用下载地址
- `data.music.play_url.url_list[0]` — ⚠️ **背景音乐,不是口播**
- `data.statistics.{digg/comment/share/collect/play}_count` — 数据
- `data.author.{nickname/signature/follower_count/aweme_count}` — 作者
- `data.cha_list[].cha_name`、`data.text_extra[].hashtag_name` — 话题标签

### ② TikHub(备用)—— 本地 API 不覆盖的平台:小红书 / YouTube / 快手 / 部分海外
```bash
# 小红书图文/视频笔记(⚠️ 小红书全系端点需付费额度,免费额度不接)
curl -s -G "https://api.tikhub.io/api/v1/xiaohongshu/web_v3/fetch_note_detail" \
  -H "Authorization: Bearer $TIKHUB_API_KEY" \
  --data-urlencode "note_id=<id>" --data-urlencode "xsec_token=<token>"
```
端点目录:https://api.tikhub.io/ ;`tikhub user info` 看额度。

### ③ Jina Reader(免费兜底)—— 公众号、网页、图文长文
```bash
curl -s "https://r.jina.ai/<完整url>"
```
对小红书图文:能拿到标题/标签/时间,**拿不到正文**(被客户端渲染挡)。

### ④ 引导粘贴(托底)
前三级都拿不到 → 让用户发文案/字幕/截图,**绝不只甩"失败"**。

---

## 3. 短视频:下载 + 转写口播 + 抽视觉帧(三步都做)

**铁律:抖音 / TikTok / B站 / YouTube 短视频拆解必须有口播 + 画面证据。** 只看 caption + 数据做不了脚本层;只看口播会漏掉视觉钩子、剪辑节奏、字幕样式等画面层证据。视觉拆解维度见 `visual-framework.md`。

```bash
mkdir -p /tmp/bm/frames

# a) 下视频(必须带 Referer 防盗链)
curl -L -A "Mozilla/5.0" -H "Referer: https://www.douyin.com/" \
  "<download_addr>" -o /tmp/bm/video.mp4

# b) 抽音轨(16kHz mono,whisper 最快)
ffmpeg -y -i /tmp/bm/video.mp4 -vn -ac 1 -ar 16000 -c:a pcm_s16le /tmp/bm/audio.wav -loglevel error

# c) 转写(中文用 medium 起步,精度要更高换 large-v3,但慢 3-4 倍)
whisper /tmp/bm/audio.wav --model medium --language Chinese \
  --output_dir /tmp/bm --output_format txt --task transcribe
# 输出: /tmp/bm/audio.txt

# d) 视觉:场景切点检测(每个切点抽一帧,拿剪辑节奏)
ffmpeg -i /tmp/bm/video.mp4 -vf "select='gt(scene,0.3)',showinfo" \
  -fps_mode vfr /tmp/bm/frames/cut_%03d.jpg 2>/tmp/bm/cuts.log

# e) 视觉:前 3 秒钩子细抽(每 1 秒一帧,共 3 帧,锁住前 3 秒钩子)
ffmpeg -i /tmp/bm/video.mp4 -t 3 -vf "fps=1" -fps_mode vfr /tmp/bm/frames/hook_%03d.jpg -loglevel error

# f) 视觉:整体节奏补抽(每 3 秒一帧,短视频<60s 可改 fps=1/2)
ffmpeg -i /tmp/bm/video.mp4 -vf "fps=1/3" -fps_mode vfr /tmp/bm/frames/t_%03d.jpg -loglevel error

# g) 视觉:拼 contact sheet(6x6=36 张/页,超过自动分多张 sheet_NNN.jpg)
ffmpeg -pattern_type glob -i "/tmp/bm/frames/*.jpg" \
  -filter_complex "scale=320:-1,tile=6x6:padding=4:color=white" \
  -fps_mode vfr /tmp/bm/sheet_%03d.jpg -loglevel error

# h) 算剪辑节奏(平均 X 秒一切)—— 用 awk 兼容 macOS BSD bc
TOTAL_CUTS=$(grep -c "pts_time" /tmp/bm/cuts.log)
DURATION=$(ffprobe -v error -show_entries format=duration -of csv=p=0 /tmp/bm/video.mp4)
AVG=$(awk -v d="$DURATION" -v c="$TOTAL_CUTS" 'BEGIN { printf "%.2f", d/c }')
echo "切点数: $TOTAL_CUTS / 时长: ${DURATION}s / 平均 ${AVG} 秒一切"
```

产出三样:
- `/tmp/bm/audio.txt` — 口播文字稿(脚本层证据)
- `/tmp/bm/sheet_*.jpg` — 视觉 contact sheet,可能多张(**用 Read 工具逐张读图,让模型多模态看**)
- `/tmp/bm/cuts.log` — 切点时间戳(对齐口播段落,看画面/口播协同方式)

模型选型(whisper):
- `medium` — 默认,中文够用,M-series Mac 跑 6 分钟视频 ~3-5 分钟
- `large-v3` — 重要对标 / 专业术语多 / 口音重时用,慢 3-4 倍
- `small` 及以下中文不行,**别用**

长视频(>5 分钟)抽帧 `fps=1/5` 减密度;>15 分钟建议先切片再转写,或考虑商业 API(飞书妙记/通义听悟,后续 skill 接)。多张 sheet 都要读,缺哪张视觉证据就缺。

---

## 4. 账号级 / 评论 / 进阶数据
- 账号作品流:本地 API `/api/douyin/web/fetch_user_post_videos`(参数 `sec_user_id`,从单视频响应里能拿到)
- 评论:`/api/douyin/web/fetch_video_comments`(参数 `aweme_id`)
- 抓最近 5–15 条标题+数据找规律,**够找规律就停**,别无限抓。挑 1–2 条代表作用上面的「下载+转写」流程深拆。

---

## 5. 抓到后必做

回显一句「**我抓到了什么**」:
- 平台 / 粒度 / 标题
- 拿到哪些字段(数据、标签、文案)
- **口播是否已转写**(没转写就明说,做不了脚本层)
- 缺什么、要不要补

再喂给 `breakdown-framework.md` 开始拆。
