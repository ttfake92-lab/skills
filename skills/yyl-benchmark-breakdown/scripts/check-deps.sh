#!/usr/bin/env bash
# yyl-benchmark-breakdown 依赖自检
# 跑这个看缺什么、对应装什么。所有检测都是只读,不会动你系统。

set -u
GREEN="\033[32m"; RED="\033[31m"; YELLOW="\033[33m"; DIM="\033[2m"; NC="\033[0m"

ok()    { echo -e "${GREEN}✓${NC} $1"; }
miss()  { echo -e "${RED}✗${NC} $1"; }
warn()  { echo -e "${YELLOW}!${NC} $1"; }
hint()  { echo -e "  ${DIM}→ $1${NC}"; }

echo "=== yyl-benchmark-breakdown 依赖自检 ==="
echo ""

ESSENTIAL_MISS=0
OPTIONAL_MISS=0

# ─── 必需:Docker(用于本地下载 API)───────────────────────────────
echo "▎Docker(本地下载 API 运行环境)"
DOCKER_READY=0
if command -v docker >/dev/null 2>&1; then
  ok "docker CLI 已安装"
  if docker info >/dev/null 2>&1; then
    ok "Docker daemon 已启动"
    DOCKER_READY=1
  else
    miss "Docker daemon 未启动"
    hint "打开 Docker Desktop,等状态变成 Running,再重跑自检"
    ESSENTIAL_MISS=$((ESSENTIAL_MISS+1))
  fi
else
  miss "Docker 未安装"
  hint "macOS:  brew install --cask docker"
  hint "Windows: https://www.docker.com/products/docker-desktop/"
  hint "Linux:   https://docs.docker.com/engine/install/"
  ESSENTIAL_MISS=$((ESSENTIAL_MISS+1))
fi
echo ""

# ─── 必需:本地 Douyin_TikTok_Download_API ──────────────────────────
echo "▎本地下载 API(主力:抖音 / TikTok / Bilibili)"
if curl -sSf -m 3 "${DOUYIN_API_BASE:-http://localhost:80}/docs" >/dev/null 2>&1; then
  ok "本地 API 可达:${DOUYIN_API_BASE:-http://localhost:80}"
else
  miss "本地 API 不可达(${DOUYIN_API_BASE:-http://localhost:80})"
  if [[ $DOCKER_READY -eq 1 ]]; then
    hint "运行: bash scripts/bootstrap-local-apis.sh"
  else
    hint "先安装并启动 Docker,再运行: bash scripts/bootstrap-local-apis.sh"
  fi
  hint "详见 INSTALL.md 或 https://github.com/Evil0ctal/Douyin_TikTok_Download_API"
  ESSENTIAL_MISS=$((ESSENTIAL_MISS+1))
fi
echo ""

# ─── 必需:本地 XHS-Downloader API ───────────────────────────────
echo "▎XHS-Downloader API(主力:小红书)"
XHS_BASE="${XHS_API_BASE:-http://127.0.0.1:5556}"
XHS_CONTAINER="${XHS_CONTAINER_NAME:-xhs-downloader-api}"
if [[ -z "${XHS_DOWNLOAD_DIR:-}" ]] && command -v docker >/dev/null 2>&1; then
  XHS_VOLUME_DIR="$(docker inspect -f '{{range .Mounts}}{{if eq .Destination "/app/Volume"}}{{.Source}}{{end}}{{end}}' "$XHS_CONTAINER" 2>/dev/null || true)"
  if [[ -n "$XHS_VOLUME_DIR" ]]; then
    XHS_DOWNLOAD_DIR="$XHS_VOLUME_DIR/Download"
  else
    XHS_DOWNLOAD_DIR="$HOME/.xhs-downloader/Volume/Download"
  fi
else
  XHS_DOWNLOAD_DIR="${XHS_DOWNLOAD_DIR:-$HOME/.xhs-downloader/Volume/Download}"
fi
if curl -sSf -m 3 "$XHS_BASE/docs" >/dev/null 2>&1; then
  ok "XHS API 可达:$XHS_BASE"
  if docker ps --filter name="$XHS_CONTAINER" --format '{{.Names}}' 2>/dev/null | grep -q "^${XHS_CONTAINER}$"; then
    ok "容器运行中:$XHS_CONTAINER"
  else
    warn "API 可达,但没在 docker ps 里看到 $XHS_CONTAINER(可能不是 Docker 启动,可忽略)"
  fi
  if [[ -d "$XHS_DOWNLOAD_DIR" ]]; then
    ok "XHS 下载目录可读:$XHS_DOWNLOAD_DIR"
  else
    warn "XHS 下载目录未找到:$XHS_DOWNLOAD_DIR"
    hint "如使用自定义挂载,设置: export XHS_DOWNLOAD_DIR=/path/to/Volume/Download"
  fi
else
  miss "XHS API 不可达($XHS_BASE)"
  if [[ $DOCKER_READY -eq 1 ]]; then
    hint "运行: bash scripts/bootstrap-local-apis.sh"
  else
    hint "先安装并启动 Docker,再运行: bash scripts/bootstrap-local-apis.sh"
  fi
  hint "如端口不同,设置: export XHS_API_BASE=http://127.0.0.1:<port>"
  ESSENTIAL_MISS=$((ESSENTIAL_MISS+1))
fi
echo ""

# ─── 必需:ffmpeg + whisper(短视频转写)──────────────────────────
echo "▎转写工具链(短视频拆解必需)"
if command -v ffmpeg >/dev/null 2>&1; then
  ok "ffmpeg: $(ffmpeg -version 2>&1 | head -1 | awk '{print $1, $3}')"
else
  miss "ffmpeg"
  hint "macOS:  brew install ffmpeg"
  hint "Linux:  apt install ffmpeg / dnf install ffmpeg"
  ESSENTIAL_MISS=$((ESSENTIAL_MISS+1))
fi

if command -v whisper >/dev/null 2>&1; then
  ok "whisper(OpenAI 官方,Python)已就绪"
elif command -v whisper-cli >/dev/null 2>&1 || command -v whisper-cpp >/dev/null 2>&1; then
  ok "whisper.cpp 已就绪(skill 默认用官方 whisper,你需要在命令里替换)"
else
  miss "whisper(语音转写)"
  hint "推荐:brew install openai-whisper   # macOS"
  hint "或:  pip install -U openai-whisper"
  hint "首次跑会自动下载 medium 模型(~1.5GB)"
  ESSENTIAL_MISS=$((ESSENTIAL_MISS+1))
fi
echo ""

# ─── 可选:TikHub(YouTube / 海外平台 / 小红书备用)─────────────────
echo "▎TikHub(可选,YouTube/海外平台/小红书备用)"
if command -v tikhub >/dev/null 2>&1; then
  ok "tikhub CLI 已装"
  if [[ -n "${TIKHUB_API_KEY:-}" ]]; then
    ok "TIKHUB_API_KEY 环境变量已设(不打印 key 本身)"
  else
    warn "TIKHUB_API_KEY 未设 → YouTube/海外平台会回退到 Jina 或粘贴"
    hint "申请: https://user.tikhub.io/  申请后:"
    hint "  echo 'export TIKHUB_API_KEY=<你的key>' >> ~/.zshrc && source ~/.zshrc"
    OPTIONAL_MISS=$((OPTIONAL_MISS+1))
  fi
else
  warn "tikhub CLI 未装(可选)"
  hint "如需 TikHub 备用:pip install 'tikhub[cli]'"
  OPTIONAL_MISS=$((OPTIONAL_MISS+1))
fi
echo ""

# ─── 可选:Jina Reader(网页/公众号/图文兜底,免费)─────────────────
echo "▎Jina Reader(可选,免费无 key 也能用)"
if curl -sSf -m 5 "https://r.jina.ai/https://example.com" >/dev/null 2>&1; then
  ok "r.jina.ai 可达"
  if [[ -n "${JINA_API_KEY:-}" ]]; then
    ok "JINA_API_KEY 已设(速率更高)"
  else
    warn "JINA_API_KEY 未设(可选,20 次/分钟匿名够用)"
    hint "如需提速到 200/分钟,免费注册 https://jina.ai/reader/ 拿 key"
  fi
else
  warn "r.jina.ai 不可达,检查网络"
fi
echo ""

# ─── 汇总 ───────────────────────────────────────────────────────
if [[ $ESSENTIAL_MISS -eq 0 ]]; then
  echo -e "${GREEN}━━━ 必需依赖全部就绪,可以开拆 ━━━${NC}"
  [[ $OPTIONAL_MISS -gt 0 ]] && echo -e "${YELLOW}可选项 $OPTIONAL_MISS 个未装(不影响主流程)${NC}"
  exit 0
else
  echo -e "${RED}━━━ 必需依赖缺 $ESSENTIAL_MISS 项,按上面 → 提示先装 ━━━${NC}"
  echo "本地 API 可用前不要开始拆解。先运行:"
  echo "  bash scripts/bootstrap-local-apis.sh"
  echo "详细安装见 INSTALL.md"
  exit 1
fi
