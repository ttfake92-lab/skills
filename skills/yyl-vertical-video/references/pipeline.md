# 命令

在仓库根目录执行。`T=tasks/<slug>`，`M=<素材盘>/tasks/<slug>`（`ln -s $M $T/media`）。

## 1. 配音（Breeze）

```bash
# project/tts_lines.json: [{"id":"s01","text":"…","gap":0.2}, …]  一句一段，gap 是这句之后的停顿
python3 scripts/breeze_audio.py tts --text "…" --speed 1.3 --out $T/assets/audio/tts/s01.wav --format wav   # 每句一次，默认 1.3 倍；加 --dry-run 先看 credits
# 旧后端（用户点名时）：python3 scripts/fish_audio.py tts … 参数同上
python3 $T/project/stitch_voice.py $T     # 裁首尾静音、按句拼接 → assets/audio/voice-final.wav
python3 skills/yyl-vertical-video/scripts/retime.py --in $T/assets/audio/voice-final.wav --out $T/assets/audio/voice-fast.wav --speed 1 --gap 0.08   # 所有气口 80 ms
```

已经按 1 倍生成好的数字人，直接处理视频（不重新生成；在 `align.py` 之后跑，字级时间同步换算）：

```bash
python3 skills/yyl-vertical-video/scripts/retime.py --in $M/heygen-avatar-v1.mp4 --out $M/heygen-avatar-v1-fast.mov --speed 1.3 --gap 0.08 \
  --map $T/project/retime-map.json --words $T/project/words.json --captions $T/project/captions.json
ffmpeg -i $M/heygen-avatar-v1-fast.mov -map 0:a -c:a pcm_s24le $T/assets/audio/voice-fast.wav     # split.json: source / voice / duration 改成新文件
```

转写核对：补 1 s 静音的 mp3 交 ElevenLabs Scribe（字级时间）；拿不准的句子用 Groq `whisper-large-v3` 交叉听。

## 2. 数字人（HeyGen MCP · Avatar V）

按 `docs/macbook/HEYGEN.md`：会员 credits、外部音频 `audioUrl`、只提交一次。当前会话没有 `mcp__heygen__*` 时：

```bash
claude -p "$(cat heygen_prompt.md)" --permission-mode bypassPermissions --output-format text > $T/logs/heygen-agent.out
```

提示词里写清：音频路径、`.env.local` 的 `HEYGEN_AVATAR_ID`、Avatar V、横版 1080p、cloudflared 临时隧道只公开这一个文件、下载到 `$M/heygen-avatar-v1.mp4`、互相关测音频偏移、写 `logs/heygen-v1.md`。

## 3. 字幕对齐

```bash
python3 skills/yyl-vertical-video/scripts/align.py --task $T     # captions.src.txt + transcripts/voice.scribe.json → words.json, captions.json
```

## 4. 素材

```bash
python3 scripts/tikhub.py search --platform douyin --query "…" --sort popular --limit 20 --json-out $T/assets/social/x.json
python3 scripts/tikhub.py download --search-file $T/assets/social/x.json --index 3 --out $T/assets/social/a.mp4
dreamina text2video --model_version=seedance2.0_vip --video_resolution=720p --duration=5 --ratio=16:9 --prompt="…" --poll=0
dreamina query_result --submit_id=<id>
python3 scripts/epidemic_mcp.py call SearchRecordings '{"query":{"term":"minimal tech beat"},"filter":{"vocals":false},"first":10}' out.json
python3 scripts/epidemic_mcp.py call EditRecording '{"id":"<recording>","input":{"targetDurationMs":87800,"downloadAudioFormat":"WAV"}}'
python3 scripts/epidemic_mcp.py call PollEditRecordingJob '{"id":"<job>"}'
python3 scripts/epidemic_mcp.py call DownloadRecordingEdit '{"input":{"jobId":"<job>","editId":"<edit>"}}'
```

## 5. 媒体准备

```bash
python3 skills/yyl-vertical-video/scripts/prep.py --task $T            # cam faces mask broll images
python3 skills/yyl-vertical-video/scripts/prep.py --task $T broll      # 只重做 B-roll
```

87 s / 30 fps：抽帧约 20 s，Vision 人脸约 40 s，人像蒙版约 4 分钟。

## 6. 看样帧

```bash
node skills/lighttrail/tools/render.mjs --film skills/yyl-vertical-video/film/split.js --project $T/project \
  --media $T/media/build --mode stills --stills 45,255,405 --size 1080x1920 --samples 1 --out-dir /tmp/stills
```

## 7. 成片与质检

```bash
python3 skills/yyl-vertical-video/scripts/make.py --task $T --version v1 --music assets/audio/music/x.wav [--nocap]
python3 skills/yyl-vertical-video/scripts/qa.py --task $T --video output/<stem>_v1.mp4
```

`make.py`：音效触发点 → 混音（`mix.py`）→ FFV1 母版（samples 3，87 s 约 15–25 分钟）→ x264 两遍 20 Mbps → SRT。只改了声音时加 `--skip-render`。
