# 阶段 5：生成与合成

前提：阶段 0 检查全绿、阶段 1 逐镜表已被用户确认、`keyframes.json` 与 `shots.json` 已写好并通过自检。

## 硬约束

| 项 | 值 |
|---|---|
| **并发** | **1**。同时发第二个任务必被拒（错误码 2000166），必须一条跑完再发下一条 |
| **最短时长** | **5 秒**。2 秒镜做不出来，靠后期变速 |
| `count` | 首尾帧模式取 **1**。结果被两张图钉死，多抽没价值，而 `count=2` 会让单镜从 5 分钟涨到 15 分钟 |
| 分辨率 | 定稿 **2K**（4:3 出 1920×1440）。768P 放大后纸的纤维颗粒会糊，这个风格靠它撑质感 |
| 图片比例 | Qwen image 3.0、Seedream 5.0 Lite **不支持 21:9**；Seedream 5.0 Pro、Lib Image、nebula-ultra 支持 |
| 提示词 | ≤ 2000 字符 |

**耗时**：关键帧约 45 秒/张；首尾帧视频 **5–9.5 分钟/镜**，波动大。排期按 **9 分钟/镜**。34 镜 ≈ 4.5 小时。

**成本要点**：H3 最短只能生成 5 秒，而每镜实际只用 1–3 秒，剩下靠变速压掉。也就是说**你为 170 秒付费、只用上 67 秒**（素材/成片比约 2.5×）。这是本工作流目前最大的一笔浪费。

## 1. 出关键帧

串行，一张一条命令。已存在的跳过（可断点续跑）。

```bash
export PATH="$HOME/.libtv:$PATH"
python3 -c "
import json
d=json.load(open('keyframes.json'))
for k in d['keyframes']:
    if 'reuse' in k: continue
    print(k['id'] + '\t' + d['style_prefix'] + ' ' + k['prompt'])
" > /tmp/kf.tsv

while IFS=$'\t' read -r id prompt; do
  [ -f "keyframes/$id.png" ] && continue
  libtv node create "$id" -t image --prompt "$prompt" \
    --set "model=Seedream 5.0 Pro" --set count=1 --set ratio=4:3 --run \
    > /tmp/out.txt 2>&1
  url=$(grep -oE 'https://[^"]+\.(png|jpg|jpeg|webp)' /tmp/out.txt | tail -1)
  if [ -z "$url" ]; then echo "$id FAILED"; tail -3 /tmp/out.txt; continue; fi
  curl -sSL -o "keyframes/$id.png" "$url" && echo "$id ok"
done < /tmp/kf.tsv
```

复用的帧另外处理（拷文件 + 上传成同名节点）：

```bash
cp keyframes/A03.png keyframes/A27.png
libtv upload A27 -t image --resource keyframes/A27.png
```

### 出完必须逐张审

```bash
ffmpeg -v error -pattern_type glob -i 'keyframes/A*.png' \
  -vf "scale=400:-2,tile=6x3:padding=6:color=white" -q:v 3 keyframes/sheet_%d.jpg
```

三件事：**文字**有没有崩或多字、**语义**观众看不看得懂、**接点**能不能和前后接上。

跑偏的单独重出（先删画布节点再重建）：

```bash
rm keyframes/A19.png && libtv node delete A19
# 然后重跑上面的循环，它只会补这一张
```

**一张图 45 秒，一个镜头 9 分钟。审图这一步省不得。**

## 2. 先跑 2–4 个代表性镜头

挑最难、最能代表方向的（通常是符号第一次出现那几镜和结尾镜）。

```bash
libtv node create W13 -t video \
  --prompt "<style_line> <该镜 motion> <tail>" \
  --set "model=Minimax H3" --set modeType=frames2video --set count=1 \
  --set resolution=2K --set duration=5 \
  --left A13 --left A14 --run
```

`--left` 的顺序就是**首帧、尾帧**。`frames2video` 模式下 `ratio` 自动跟随输入图，不要传。

**把样片给用户看，确认方向再跑全量。**

## 3. 跑全量

```bash
python3 -c "
import json
d=json.load(open('shots.json'))
for s in d['shots']:
    print(s['id'] + '\t' + s['from'] + '\t' + s['to'] + '\t' + d['style_line'] + ' ' + s['motion'] + ' ' + d['tail'])
" > /tmp/shots.tsv

while IFS=$'\t' read -r id from to prompt; do
  [ -f "clips/$id.mp4" ] && continue
  run() {
    libtv node create "$id" -t video --prompt "$prompt" \
      --set "model=Minimax H3" --set modeType=frames2video --set count=1 \
      --set resolution=2K --set duration=5 \
      --left "$from" --left "$to" --run > /tmp/out.txt 2>&1
  }
  run
  if grep -q "已存在显示名" /tmp/out.txt; then
    libtv node delete "$id" >/dev/null 2>&1; run
  fi
  url=$(grep -oE 'https://[^"]+\.mp4' /tmp/out.txt | head -1)
  if [ -z "$url" ]; then echo "$id FAILED"; tail -3 /tmp/out.txt; continue; fi
  curl -sSL -o "clips/$id.mp4" "$url" && echo "$id ok $from->$to"
done < /tmp/shots.tsv
```

**每跑完一镜立刻下载到本地**，中断后按文件是否存在跳过即可续跑。4.5 小时的运行大概率被打断。

### 两个必然踩到的坑

**节点重名**：上一轮中断留下空节点，重跑会报「已存在显示名」。必须先 `libtv node delete <ID>` 再重建——上面的循环已处理。

**服务端偶发失败**：返回 `当前模型资源紧张，积分将会在2小时内返还，请重新生成`，任务 status=3。重跑即可，积分会退。

跑完清点：`ls clips/*.mp4 | wc -l` 应等于镜头数。

## 4. 变速拼片

素材都是 5.17 秒，每镜整条变速到目标时长。**不要裁切**——尾帧必须落在下一镜的首帧上，裁了接点就断。

```bash
python3 - <<'PY'
import json, subprocess, pathlib

def dur(p):
    r = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
                        "-of","csv=p=0",str(p)], capture_output=True, text=True)
    return float(r.stdout.strip())

sh = json.load(open("shots.json"))
na = json.load(open("narration.json"))
gap, black = na.get("gap_seconds",0.18), na.get("black_seconds",0.5)
W,H,FPS = 1920,1440,30
pathlib.Path("build").mkdir(exist_ok=True); pathlib.Path("out").mkdir(exist_ok=True)

v,a,cuts,t = [],[],[],0.0
for line_id, ids, weights in sh["plan"]:
    if line_id == "BLACK":
        subprocess.run(["ffmpeg","-v","error","-f","lavfi","-i",
            f"color=c=black:s={W}x{H}:r={FPS}:d={black}","-pix_fmt","yuv420p","-y","build/black.mp4"],check=True)
        subprocess.run(["ffmpeg","-v","error","-f","lavfi","-i",
            f"anullsrc=r=44100:cl=mono:d={black}","-y","build/black.wav"],check=True)
        v.append("build/black.mp4"); a.append("build/black.wav")
        cuts.append((line_id,t,black)); t += black; continue
    span = dur(f"narration/{line_id}.wav") + gap
    weights = weights or [1/len(ids)]*len(ids)
    for sid, w in zip(ids, weights):
        target = span*w
        subprocess.run(["ffmpeg","-v","error","-i",f"clips/{sid}.mp4","-filter:v",
            f"setpts={target/dur(f'clips/{sid}.mp4')}*PTS,fps={FPS},scale={W}:{H}",
            "-an","-pix_fmt","yuv420p","-y",f"build/{sid}.mp4"],check=True)
        v.append(f"build/{sid}.mp4"); cuts.append((sid,t,target)); t += target
    subprocess.run(["ffmpeg","-v","error","-i",f"narration/{line_id}.wav","-af",
        f"apad=pad_dur={gap},aresample=44100","-ac","1","-y",f"build/{line_id}_pad.wav"],check=True)
    a.append(f"build/{line_id}_pad.wav")

for name, parts in (("v",v),("a",a)):
    open(f"build/{name}list.txt","w").write("".join(
        f"file '{pathlib.Path(p).resolve()}'\n" for p in parts))
subprocess.run(["ffmpeg","-v","error","-f","concat","-safe","0","-i","build/vlist.txt",
                "-c","copy","-y","build/video.mp4"],check=True)
subprocess.run(["ffmpeg","-v","error","-f","concat","-safe","0","-i","build/alist.txt",
                "-c","copy","-y","build/audio.wav"],check=True)
subprocess.run(["ffmpeg","-v","error","-i","build/video.mp4","-i","build/audio.wav",
                "-c:v","libx264","-crf","18","-preset","slow","-c:a","aac","-b:a","192k",
                "-shortest","-y","out/film.mp4"],check=True)
json.dump([{"id":c,"start":round(s,3),"dur":round(d,3)} for c,s,d in cuts],
          open("out/cutlist.json","w"), ensure_ascii=False, indent=2)
print(f"成片 out/film.mp4  {dur('out/film.mp4'):.2f}s  ({len(cuts)} 段)")
PY
```

## 5. 验收成片

```bash
ffprobe -v error -select_streams v:0 -show_entries stream=width,height,r_frame_rate -of csv=p=0 out/film.mp4
ffmpeg -v error -i out/film.mp4 -vf "fps=1,scale=300:-2" -q:v 3 out/f_%02d.jpg
ffmpeg -v error -i "out/f_%02d.jpg" -vf "tile=10x7:padding=3:color=red" -q:v 3 out/sheet.jpg
```

看那张 `sheet.jpg`，逐格确认：**没有连续几格长得一样**。如果有，说明关键帧设计出了问题，回阶段 2。

## 6. 还没做的

配音之外的音频层留给用户：单层弦乐 pad，加上逐个物件的 foley（图钉按下、硬币落盘、印章压下、纸片堆落）。**不要用氛围垫**——参考片的 68 个瞬态点每一个都对应画面里一个具体动作，那是质感的真正来源。
