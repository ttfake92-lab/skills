# 安装指南

这个 skill 依赖几个外部服务和工具。**必需的不装拆解跑不起来,可选的没有也能用主流程。**

> **快速自检**:克隆下来先跑 `bash scripts/check-deps.sh`,看缺什么。

---

## 依赖一览

| 依赖 | 必需? | 用途 | 大小/费用 |
|---|---|---|---|
| Douyin_TikTok_Download_API(本地) | **必需** | 主力取数:抖音 / TikTok / Bilibili 元数据 + 下载地址 | Docker 镜像 ~500MB,免费 |
| ffmpeg | **必需** | 从视频抽音轨 | ~100MB,免费 |
| openai-whisper | **必需** | 把音轨转写成文字(脚本拆解的核心) | 命令行 ~50MB + 首跑下载 medium 模型 ~1.5GB,免费 |
| TikHub | **可选** | 小红书 / YouTube / 海外平台备用 API | 注册免费,部分端点付费,小红书全系付费 |
| Jina Reader | **可选** | 公众号 / 普通网页 / 图文兜底 | 免费,20 次/分钟匿名;注册免费 key 200 次/分钟 |

---

## 1. Douyin_TikTok_Download_API(必需)

抖音/TikTok/Bilibili 拆解的**主力取数源**。本地自托管,免费,Apache-2.0。

**官方仓库**:https://github.com/Evil0ctal/Douyin_TikTok_Download_API

### 推荐方式:Docker(最简单)

先装 Docker Desktop:https://www.docker.com/products/docker-desktop/

```bash
docker pull evil0ctal/douyin_tiktok_download_api:latest
docker run -d --name douyin_tiktok_api -p 80:80 evil0ctal/douyin_tiktok_download_api
docker ps                                       # 看到容器在跑
open http://localhost:80/docs                   # 看 API 文档
```

**端口冲突就改**:如 80 被占,`-p 8080:80`,然后用环境变量告诉 skill:
```bash
export DOUYIN_API_BASE=http://localhost:8080
```

### Cookie 风控(部署完务必看)
抖音有反爬,**官方说部署后要在 config.yaml 里替换浏览器 Cookie**,否则部分接口会失效。
- 抖音 Cookie 怎么拿、放在哪:看官方 README → "[部署前的准备工作](https://github.com/Evil0ctal/Douyin_TikTok_Download_API#%EF%B8%8F%E9%83%A8%E7%BD%B2%E5%89%8D%E7%9A%84%E5%87%86%E5%A4%87%E5%B7%A5%E4%BD%9C%E8%AF%B7%E4%BB%94%E7%BB%86%E9%98%85%E8%AF%BB)"
- 改完配置 → `docker restart douyin_tiktok_api`

### 不想自托管?
官方有演示站 `https://api.douyin.wtf`,**Cookie 不保证有效,只能 demo**。生产请自托管。

---

## 2. ffmpeg + whisper(必需,转写)

短视频拆解必须有口播。没这俩你只能看 caption 和数据,做不了脚本层拆解。

### macOS(brew,最简)
```bash
brew install ffmpeg openai-whisper
```

### Linux
```bash
# Debian/Ubuntu
sudo apt install ffmpeg && pip install -U openai-whisper
# Fedora
sudo dnf install ffmpeg && pip install -U openai-whisper
```

### Windows
- ffmpeg:https://www.gyan.dev/ffmpeg/builds/ 下载 + 加 PATH
- whisper:`pip install -U openai-whisper`

### 模型
首次 `whisper` 运行会自动从 OpenAI 下 medium 模型(~1.5GB)到 `~/.cache/whisper/`。中文用 `medium` 够了,要更准上 `large-v3`(慢 3-4 倍)。

### Apple Silicon 加速
你机器是 M1/2/3/4 的话,openai-whisper 默认走 CPU FP32。要 GPU 加速可以装 `mlx-whisper`(MLX 后端)或 `whisper.cpp`(Metal 后端),但 skill 默认命令是 openai-whisper,替换时改 SKILL.md 里的 whisper 命令即可。

---

## 3. TikHub(可选)

只在拆**小红书 / YouTube / 海外平台**时需要。

### 注册
https://user.tikhub.io/ → 注册 → Dashboard 拿 API Key

### 装 CLI(可选,curl 也能调)
```bash
pip install "tikhub[cli]"
echo 'export TIKHUB_API_KEY=<你的key>' >> ~/.zshrc   # bash 的话改 ~/.bashrc
source ~/.zshrc
tikhub user info                                     # 看额度
```

### 关于额度(实测,2026-06)
- 注册送少量免费额度,每日签到再领,**不过期**。
- 抖音 / B站 / YouTube 等多数端点接受免费额度。
- ⚠️ **小红书全系端点拒收免费额度,必须充值**。
- 充值最低 $5,够个人创作者拆几百条。

### 安全提示
- key **只走环境变量**,绝不写进代码 / commit / 命令历史。
- 实测 TikHub 402 响应会把 Authorization 头回显在 body 里 → 如果你在共享屏幕/录屏调用接口,务必先撤掉 key 重申一把。

---

## 4. Jina Reader(可选,纯免费)

公众号、普通网页、图文兜底。**无 key 也能直接用,curl 一下就行。**

```bash
curl -s "https://r.jina.ai/<完整URL>"
```

要更高速率(200 次/分钟)免费注册 https://jina.ai/reader/ 拿 key:
```bash
echo 'export JINA_API_KEY=<你的key>' >> ~/.zshrc && source ~/.zshrc
```

---

## 自检

装完全跑一遍:
```bash
bash scripts/check-deps.sh
```

输出 `━━━ 必需依赖全部就绪,可以开拆 ━━━` 就 OK。可选项缺没事。

---

## 常见问题

**Q: 本地 API 装好了,跑 hybrid 端点报 cookie 失效?**
A: 看本文 §1 的「Cookie 风控」,去更新 config.yaml 里的 Douyin Cookie。

**Q: whisper 太慢?**
A: 短视频(<3 min)用 `medium` 够。M 系 Mac 长视频换 `mlx-whisper` 或 `whisper.cpp`。Linux + NVIDIA 显卡用 `--device cuda`。

**Q: 不想装 Docker 部署本地 API?**
A: 项目也支持 pip 模式(`pip install douyin-tiktok-scraper` 作为库),或 Linux 一键部署脚本,具体看[官方 README](https://github.com/Evil0ctal/Douyin_TikTok_Download_API)。

**Q: 完全不想装本地 API,能拆抖音吗?**
A: 可以,但要付费走 TikHub 的抖音端点(或用演示站 `api.douyin.wtf`,不保证可用)。把 skill 里 `localhost:80` 全部换成相应 base 即可。
