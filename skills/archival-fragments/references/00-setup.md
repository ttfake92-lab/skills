# 阶段 0：环境准备与检查

在一个**空文件夹**里也能走完。三样东西：ffmpeg、LibTV CLI、Fish Audio 凭据。

**做完这一阶段之前，不要开始写文案，也不要生成任何东西。**

## 1. ffmpeg

用来量音频时长、变速、拼片、混音。

```bash
ffmpeg -version | head -1 && ffprobe -version | head -1
```

没有就装：

```bash
brew install ffmpeg                    # macOS
sudo apt-get install -y ffmpeg         # Debian / Ubuntu
```

## 2. LibTV CLI

用来调 MiniMax H3 出视频、Seedream 出图。

```bash
export PATH="$HOME/.libtv:$PATH"
libtv --version
```

没有就去 LibLib 官网下 CLI 安装包（装完在 `~/.libtv/libtv`）。装好后**必须登录**：

```bash
libtv login web        # 浏览器登录
# 或
libtv login phone      # 手机号登录
```

**登录验证**——这一步不能跳：

```bash
libtv account info
```

返回里要能看到 `user` 和 `activeAccount`。报未登录或返回空，回去重新 `libtv login`。

再确认账号能用到这两个模型：

```bash
libtv model search --type video | grep -o 'MiniMax-Hailuo-H3'
libtv model search --type image | grep -o 'doubao-seedream-5-0-pro'
```

两条都要有输出。没有说明账号权限不够，换账号或开通会员。

## 3. Fish Audio 凭据

用来合成旁白。**镜长由配音时长决定，所以这个不通，整条流程走不下去。**

在工作目录建 `.env`：

```bash
cat > .env <<'ENV'
FISH_API_KEY=你的key
FISH_VOICE_ID=你要用的音色id
ENV
```

- API key 在 Fish Audio 官网「API Keys」页面创建
- voice id 是音色的 reference id，在音色页面地址栏或分享链接里

**凭据验证**——真的合成一句，不要只看变量填没填：

```bash
set -a && source .env && set +a
curl -s -X POST https://api.fish.audio/v1/tts \
  -H "Authorization: Bearer $FISH_API_KEY" \
  -H "Content-Type: application/json" \
  -H "model: s2-pro" \
  -d "{\"text\":\"测试\",\"reference_id\":\"$FISH_VOICE_ID\",\"format\":\"wav\"}" \
  -o /tmp/tts-check.wav
ffprobe -v error -show_entries format=duration -of csv=p=0 /tmp/tts-check.wav
```

能打印出一个秒数（约 0.5–1.5）就是通的。如果文件 0 字节或 ffprobe 报错，把 wav 当文本打开看错误信息——通常是 key 无效或 voice id 不存在。

**`.env` 不要提交到 git，也不要写进任何交付文档。**

## 4. 检查清单

全部跑一遍，把结果报给用户：

| 检查项 | 命令 | 通过标准 |
|---|---|---|
| ffmpeg | `ffmpeg -version \| head -1` | 有版本号 |
| ffprobe | `ffprobe -version \| head -1` | 有版本号 |
| libtv 可执行 | `libtv --version` | 有版本号 |
| libtv 已登录 | `libtv account info` | 返回含 `activeAccount` |
| 视频模型可用 | `libtv model search --type video \| grep MiniMax-Hailuo-H3` | 有输出 |
| 图片模型可用 | `libtv model search --type image \| grep doubao-seedream-5-0-pro` | 有输出 |
| Fish Audio 可用 | 上面那段 curl + ffprobe | 打印出秒数 |

## 5. 建工作目录

```bash
mkdir -p keyframes clips narration build out
```

## 6. 绑定 LibTV 画布

```bash
libtv workspace create "<项目名>"
libtv workspace use <上一步返回的 workspaceId>
libtv project create "<画布名>"
libtv project use <上一步返回的 uuid>
```

## 7. 告诉用户可以开始了

七项全绿之后，明确告诉用户：

> 环境已就绪（ffmpeg / LibTV 已登录 / Fish Audio 可用）。
> 现在把你的想法或者写好的文案发给我——一句话的选题也行，我来写文案并拆分镜。

**有任何一项没过，就停在这里，把没过的那项和修复办法告诉用户，不要往下走。**
