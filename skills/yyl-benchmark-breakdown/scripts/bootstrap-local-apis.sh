#!/usr/bin/env bash
# Start the required local download APIs for yyl-benchmark-breakdown.

set -euo pipefail

DOUYIN_API_BASE="${DOUYIN_API_BASE:-http://localhost:80}"
DOUYIN_CONTAINER_NAME="${DOUYIN_CONTAINER_NAME:-douyin_tiktok_api}"
DOUYIN_IMAGE="${DOUYIN_IMAGE:-evil0ctal/douyin_tiktok_download_api:latest}"
DOUYIN_PORT="${DOUYIN_PORT:-80}"

XHS_API_BASE="${XHS_API_BASE:-http://127.0.0.1:5556}"
XHS_CONTAINER_NAME="${XHS_CONTAINER_NAME:-xhs-downloader-api}"
XHS_IMAGE="${XHS_IMAGE:-joeanamier/xhs-downloader}"
XHS_PORT="${XHS_PORT:-5556}"
XHS_VOLUME_DIR="${XHS_VOLUME_DIR:-$HOME/.xhs-downloader/Volume}"

ok() { printf '✓ %s\n' "$*"; }
warn() { printf '! %s\n' "$*"; }
die() { printf '✗ %s\n' "$*" >&2; exit 1; }

require_docker() {
  if ! command -v docker >/dev/null 2>&1; then
    cat >&2 <<'EOF'
✗ Docker 未安装。

先安装 Docker Desktop:
  macOS:   brew install --cask docker
  Windows: https://www.docker.com/products/docker-desktop/
  Linux:   https://docs.docker.com/engine/install/

安装后打开 Docker Desktop,等它启动完成,再运行:
  bash scripts/bootstrap-local-apis.sh
EOF
    exit 1
  fi

  if ! docker info >/dev/null 2>&1; then
    cat >&2 <<'EOF'
✗ Docker 已安装,但 Docker daemon 没启动。

下一步:
  1. 打开 Docker Desktop
  2. 等状态变成 Running
  3. 重新运行 bash scripts/bootstrap-local-apis.sh
EOF
    exit 1
  fi
}

api_ok() {
  curl -sSf -m 3 "$1/docs" >/dev/null 2>&1
}

container_exists() {
  docker ps -a --format '{{.Names}}' | grep -q "^$1$"
}

container_running() {
  docker ps --format '{{.Names}}' | grep -q "^$1$"
}

start_or_run_douyin() {
  if api_ok "$DOUYIN_API_BASE"; then
    ok "Douyin_TikTok_Download_API 已可用:$DOUYIN_API_BASE"
    return 0
  fi

  if container_exists "$DOUYIN_CONTAINER_NAME"; then
    if container_running "$DOUYIN_CONTAINER_NAME"; then
      warn "容器 $DOUYIN_CONTAINER_NAME 正在运行,但 API 不可达:$DOUYIN_API_BASE"
    else
      docker start "$DOUYIN_CONTAINER_NAME" >/dev/null
      ok "已启动容器:$DOUYIN_CONTAINER_NAME"
    fi
  else
    docker pull "$DOUYIN_IMAGE"
    docker run -d --name "$DOUYIN_CONTAINER_NAME" -p "$DOUYIN_PORT:80" "$DOUYIN_IMAGE" >/dev/null
    ok "已创建并启动容器:$DOUYIN_CONTAINER_NAME"
  fi

  if api_ok "$DOUYIN_API_BASE"; then
    ok "Douyin_TikTok_Download_API 已可用:$DOUYIN_API_BASE"
  else
    warn "Douyin API 仍不可达。若改过端口,设置 DOUYIN_API_BASE;若端口冲突,重建容器并改 DOUYIN_PORT。"
  fi
}

start_or_run_xhs() {
  if api_ok "$XHS_API_BASE"; then
    ok "XHS-Downloader API 已可用:$XHS_API_BASE"
    return 0
  fi

  mkdir -p "$XHS_VOLUME_DIR"

  if container_exists "$XHS_CONTAINER_NAME"; then
    if container_running "$XHS_CONTAINER_NAME"; then
      warn "容器 $XHS_CONTAINER_NAME 正在运行,但 API 不可达:$XHS_API_BASE"
    else
      docker start "$XHS_CONTAINER_NAME" >/dev/null
      ok "已启动容器:$XHS_CONTAINER_NAME"
    fi
  else
    docker pull "$XHS_IMAGE"
    docker run -d --name "$XHS_CONTAINER_NAME" -p "$XHS_PORT:5556" \
      -v "$XHS_VOLUME_DIR:/app/Volume" \
      "$XHS_IMAGE" python main.py api >/dev/null
    ok "已创建并启动容器:$XHS_CONTAINER_NAME"
  fi

  if api_ok "$XHS_API_BASE"; then
    ok "XHS-Downloader API 已可用:$XHS_API_BASE"
  else
    warn "XHS API 仍不可达。若改过端口,设置 XHS_API_BASE;查看日志: docker logs $XHS_CONTAINER_NAME"
  fi
}

require_docker
start_or_run_douyin
start_or_run_xhs

printf '\n完成后运行自检:\n  bash scripts/check-deps.sh\n'
