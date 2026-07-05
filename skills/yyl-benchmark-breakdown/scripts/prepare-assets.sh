#!/usr/bin/env bash
# Prepare evidence assets for yyl-benchmark-breakdown.
# Output: metadata.json, video/audio/transcript, contact sheets, and manifest.txt.

set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  bash scripts/prepare-assets.sh "<url>" [output_dir]

Environment:
  DOUYIN_API_BASE       Default: http://localhost:80
  XHS_API_BASE          Default: http://127.0.0.1:5556
  XHS_CONTAINER_NAME    Default: xhs-downloader-api
  XHS_DOWNLOAD_DIR      Default: inferred from Docker mount, then $HOME/.xhs-downloader/Volume/Download
  BENCHMARK_WORKDIR     Default: /tmp/yyl-benchmark
  WHISPER_MODEL         Default: medium
  WHISPER_LANGUAGE      Default: Chinese
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" || $# -lt 1 ]]; then
  usage
  exit 0
fi

URL="$1"
RUN_ID="$(date +%Y%m%d-%H%M%S)"
WORK_ROOT="${BENCHMARK_WORKDIR:-/tmp/yyl-benchmark}"
RUN_DIR="${2:-$WORK_ROOT/$RUN_ID}"
DOUYIN_API_BASE="${DOUYIN_API_BASE:-http://localhost:80}"
XHS_API_BASE="${XHS_API_BASE:-http://127.0.0.1:5556}"
XHS_CONTAINER_NAME="${XHS_CONTAINER_NAME:-xhs-downloader-api}"
WHISPER_MODEL="${WHISPER_MODEL:-medium}"
WHISPER_LANGUAGE="${WHISPER_LANGUAGE:-Chinese}"

infer_xhs_download_dir() {
  if [[ -n "${XHS_DOWNLOAD_DIR:-}" ]]; then
    printf '%s\n' "$XHS_DOWNLOAD_DIR"
    return 0
  fi

  if command -v docker >/dev/null 2>&1; then
    local volume_dir
    volume_dir="$(docker inspect -f '{{range .Mounts}}{{if eq .Destination "/app/Volume"}}{{.Source}}{{end}}{{end}}' "$XHS_CONTAINER_NAME" 2>/dev/null || true)"
    if [[ -n "$volume_dir" ]]; then
      printf '%s\n' "$volume_dir/Download"
      return 0
    fi
  fi

  printf '%s\n' "$HOME/.xhs-downloader/Volume/Download"
}

XHS_DOWNLOAD_DIR="$(infer_xhs_download_dir)"

mkdir -p "$RUN_DIR/frames" "$RUN_DIR/xhs_images"
MANIFEST="$RUN_DIR/manifest.txt"
METADATA="$RUN_DIR/metadata.json"

log() { printf '%s\n' "$*" | tee -a "$MANIFEST" >&2; }
need() {
  if ! command -v "$1" >/dev/null 2>&1; then
    log "missing dependency: $1"
    exit 1
  fi
}

need curl
need ffmpeg
need ffprobe
need python3

detect_platform() {
  case "$URL" in
    *xiaohongshu.com*|*xhslink.com*) echo "xhs" ;;
    *douyin.com*|*v.douyin.com*) echo "douyin" ;;
    *tiktok.com*) echo "tiktok" ;;
    *bilibili.com*|*b23.tv*) echo "bilibili" ;;
    *youtube.com*|*youtu.be*) echo "youtube" ;;
    *mp.weixin.qq.com*) echo "weixin" ;;
    *) echo "unknown" ;;
  esac
}

json_payload() {
  local download="${1:-true}"
  python3 - "$URL" "$download" <<'PY'
import json, sys
download = sys.argv[2].lower() == "true"
print(json.dumps({"url": sys.argv[1], "download": download, "skip": False}, ensure_ascii=False))
PY
}

xhs_settings_file() {
  local volume_dir
  volume_dir="$(dirname "$XHS_DOWNLOAD_DIR" 2>/dev/null || true)"
  if [[ -n "$volume_dir" && -f "$volume_dir/settings.json" ]]; then
    printf '%s\n' "$volume_dir/settings.json"
    return 0
  fi

  if command -v docker >/dev/null 2>&1; then
    local mounted_volume
    mounted_volume="$(docker inspect -f '{{range .Mounts}}{{if eq .Destination "/app/Volume"}}{{.Source}}{{end}}{{end}}' "$XHS_CONTAINER_NAME" 2>/dev/null || true)"
    if [[ -n "$mounted_volume" && -f "$mounted_volume/settings.json" ]]; then
      printf '%s\n' "$mounted_volume/settings.json"
      return 0
    fi
  fi

  return 1
}

xhs_cookie_configured() {
  local settings
  settings="$(xhs_settings_file || true)"
  [[ -n "$settings" ]] || return 1
  python3 - "$settings" <<'PY'
import json, sys
try:
    cookie = json.load(open(sys.argv[1], encoding="utf-8")).get("cookie") or ""
except Exception:
    raise SystemExit(1)
raise SystemExit(0 if cookie.strip() else 1)
PY
}

warn_xhs_cookie_if_needed() {
  if ! xhs_cookie_configured; then
    log "warning: XHS API returned no data and XHS-Downloader cookie is empty"
    log "warning: official docs say cookie is optional, but configure/update Volume/settings.json cookie when XHS functions are abnormal"
  fi
}

extract_video_url() {
  python3 - "$METADATA" <<'PY'
import json, sys
from collections.abc import Mapping, Sequence

with open(sys.argv[1], "r", encoding="utf-8") as f:
    root = json.load(f)

def walk(node):
    if isinstance(node, Mapping):
        if "download_addr" in node:
            yield node["download_addr"]
        for key in ("play_addr", "video", "video_url", "url", "urls"):
            if key in node:
                yield node[key]
        for value in node.values():
            yield from walk(value)
    elif isinstance(node, Sequence) and not isinstance(node, (str, bytes, bytearray)):
        for value in node:
            yield from walk(value)

def urls_from(node):
    if isinstance(node, str) and node.startswith(("http://", "https://")):
        yield node
    elif isinstance(node, Mapping):
        for key in ("url_list", "urls"):
            value = node.get(key)
            if isinstance(value, list):
                for item in value:
                    yield from urls_from(item)
        for key in ("url", "href", "download_url", "master_url"):
            yield from urls_from(node.get(key))
    elif isinstance(node, Sequence) and not isinstance(node, (str, bytes, bytearray)):
        for item in node:
            yield from urls_from(item)

seen = set()
for candidate in walk(root):
    for url in urls_from(candidate):
        if url not in seen:
            seen.add(url)
            print(url)
            raise SystemExit(0)
raise SystemExit(1)
PY
}

download_video_from_url() {
  local video_url="$1"
  local referer="$2"
  curl -L -A "Mozilla/5.0" -H "Referer: $referer" "$video_url" -o "$RUN_DIR/video.mp4"
}

prepare_video_assets() {
  [[ -f "$RUN_DIR/video.mp4" ]] || return 0

  log "video: $RUN_DIR/video.mp4"
  ffmpeg -y -i "$RUN_DIR/video.mp4" -vn -ac 1 -ar 16000 -c:a pcm_s16le "$RUN_DIR/audio.wav" -loglevel error || true

  if [[ -s "$RUN_DIR/audio.txt" ]]; then
    log "transcript: $RUN_DIR/audio.txt"
  elif [[ -s "$RUN_DIR/audio.wav" ]]; then
    if command -v whisper >/dev/null 2>&1; then
      whisper "$RUN_DIR/audio.wav" --model "$WHISPER_MODEL" --language "$WHISPER_LANGUAGE" \
        --output_dir "$RUN_DIR" --output_format txt --task transcribe
    else
      log "warning: whisper not found; transcript skipped"
    fi
  fi

  ffmpeg -i "$RUN_DIR/video.mp4" -vf "select='gt(scene,0.3)',showinfo" \
    -fps_mode vfr "$RUN_DIR/frames/cut_%03d.jpg" 2>"$RUN_DIR/cuts.log" || true
  ffmpeg -i "$RUN_DIR/video.mp4" -t 3 -vf "fps=1" \
    -fps_mode vfr "$RUN_DIR/frames/hook_%03d.jpg" -loglevel error || true
  ffmpeg -i "$RUN_DIR/video.mp4" -vf "fps=1/3" \
    -fps_mode vfr "$RUN_DIR/frames/t_%03d.jpg" -loglevel error || true

  if find "$RUN_DIR/frames" -type f -name '*.jpg' | grep -q .; then
    ffmpeg -pattern_type glob -i "$RUN_DIR/frames/*.jpg" \
      -filter_complex "scale=320:-1,tile=6x6:padding=4:color=white" \
      -fps_mode vfr "$RUN_DIR/sheet_%03d.jpg" -loglevel error || true
  fi

  local duration cuts avg
  duration="$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$RUN_DIR/video.mp4" 2>/dev/null || echo 0)"
  cuts="$(grep -c "pts_time" "$RUN_DIR/cuts.log" 2>/dev/null || echo 0)"
  avg="$(awk -v d="$duration" -v c="$cuts" 'BEGIN { if (c > 0) printf "%.2f", d/c; else printf "未检测到切点" }')"
  printf 'duration=%s\ncuts=%s\navg_cut=%s\n' "$duration" "$cuts" "$avg" > "$RUN_DIR/video_stats.txt"
}

prepare_image_sheet() {
  if ! find "$RUN_DIR/xhs_images" -type f | grep -q .; then
    return 0
  fi

  ffmpeg -pattern_type glob -i "$RUN_DIR/xhs_images/*" \
    -filter_complex "scale=360:-1,tile=4x4:padding=8:color=white" \
    -fps_mode vfr "$RUN_DIR/xhs_sheet_%03d.jpg" -loglevel error || true
}

download_xhs_assets_from_json() {
  local json_file="$1"
  local url_list="$RUN_DIR/xhs_download_urls.tsv"
  python3 - "$json_file" "$url_list" <<'PY'
import json, sys
from pathlib import Path

src = Path(sys.argv[1])
dst = Path(sys.argv[2])
payload = json.load(src.open(encoding="utf-8"))
data = payload.get("data") or {}
urls = data.get("下载地址") or []
kind = data.get("作品类型") or ""
rows = []
if "视频" in kind and urls:
    rows.append(("video", urls[0]))
else:
    for url in urls:
        rows.append(("image", url))
dst.write_text("\n".join(f"{kind}\t{url}" for kind, url in rows) + ("\n" if rows else ""), encoding="utf-8")
PY

  local i=0 kind url ext
  while IFS=$'\t' read -r kind url; do
    [[ -n "$url" ]] || continue
    case "$kind" in
      video)
        [[ -f "$RUN_DIR/video.mp4" ]] || curl -L -A "Mozilla/5.0" -H "Referer: https://www.xiaohongshu.com/" "$url" -o "$RUN_DIR/video.mp4"
        ;;
      image)
        i=$((i + 1))
        ext="${url%%\?*}"
        ext="${ext##*.}"
        case "$ext" in
          jpg|jpeg|png|webp|heic|avif) ;;
          *) ext="jpg" ;;
        esac
        curl -L -A "Mozilla/5.0" -H "Referer: https://www.xiaohongshu.com/" "$url" -o "$RUN_DIR/xhs_images/$(printf '%03d' "$i").$ext"
        ;;
    esac
  done < "$url_list"
}

srt_to_text() {
  local srt="$1"
  local out="$2"
  python3 - "$srt" "$out" <<'PY'
import re, sys
from pathlib import Path

src = Path(sys.argv[1])
dst = Path(sys.argv[2])
lines = []
for raw in src.read_text(encoding="utf-8", errors="ignore").splitlines():
    line = raw.strip()
    if not line:
        continue
    if line.isdigit():
        continue
    if re.match(r"\d{2}:\d{2}:\d{2}[,.]\d{3}\s+-->\s+\d{2}:\d{2}:\d{2}[,.]\d{3}", line):
        continue
    lines.append(line)

dst.write_text("\n".join(lines).strip() + ("\n" if lines else ""), encoding="utf-8")
PY
}

copy_new_xhs_files() {
  local marker="$1"
  if [[ ! -d "$XHS_DOWNLOAD_DIR" ]]; then
    log "warning: XHS_DOWNLOAD_DIR not found: $XHS_DOWNLOAD_DIR"
    log "set XHS_DOWNLOAD_DIR to the mounted XHS-Downloader Volume/Download directory to collect downloaded files"
    return 0
  fi

  local newest_video=""
  newest_video="$(find "$XHS_DOWNLOAD_DIR" -type f -newer "$marker" -iname '*.mp4' -print 2>/dev/null | sort | tail -1 || true)"
  if [[ -n "$newest_video" ]]; then
    cp "$newest_video" "$RUN_DIR/video.mp4"
  fi

  local i=0 ext base
  while IFS= read -r file; do
    i=$((i + 1))
    base="$(basename "$file")"
    ext="${base##*.}"
    cp "$file" "$RUN_DIR/xhs_images/$(printf '%03d' "$i").$ext"
  done < <(find "$XHS_DOWNLOAD_DIR" -type f -newer "$marker" \( \
      -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.png' -o -iname '*.webp' -o -iname '*.heic' \
    \) -print 2>/dev/null | sort)
}

json_has_data() {
  python3 - "$1" <<'PY'
import json, sys
try:
    with open(sys.argv[1], "r", encoding="utf-8") as f:
        payload = json.load(f)
except Exception:
    raise SystemExit(1)
data = payload.get("data")
raise SystemExit(0 if data else 1)
PY
}

prepare_xhs_web_fallback() {
  local replace_metadata="${1:-true}"
  local page="$RUN_DIR/xhs_page.html"
  local web_meta="$RUN_DIR/xhs_web_meta.json"
  curl -sS -L -A "Mozilla/5.0" "$URL" -o "$page"

  python3 - "$page" "$web_meta" "$URL" <<'PY'
import json, re, sys
from pathlib import Path
from urllib.parse import urlparse

page = Path(sys.argv[1])
out = Path(sys.argv[2])
source_url = sys.argv[3]
s = page.read_text(encoding="utf-8", errors="ignore")
normalized = s.replace("\\u002F", "/")

def first(pattern, text=normalized, flags=0):
    m = re.search(pattern, text, flags)
    return m.group(1) if m else ""

def json_string(key, text):
    value = first(rf'"{re.escape(key)}":"((?:\\.|[^"\\])*)"', text)
    if not value:
        return ""
    try:
        return json.loads(f'"{value}"')
    except Exception:
        return value

def json_number(key, text):
    return first(rf'"{re.escape(key)}":([0-9]+)', text)

path = urlparse(source_url).path
note_id = ""
for pattern in (
    r"/explore/([0-9a-f]+)",
    r"/discovery/item/([0-9a-f]+)",
    r"/user/profile/[a-z0-9]+/([0-9a-f]+)",
):
    note_id = first(pattern, path) or note_id
note_id = note_id or first(r'"firstNoteId":"([^"]+)"') or first(r'"noteId":"([^"]+)"')

note_marker = f'"noteDetailMap":{{"{note_id}"' if note_id else '"noteDetailMap":{'
note_pos = normalized.find(note_marker)
if note_pos < 0 and note_id:
    note_pos = normalized.find(f'"noteId":"{note_id}"')
segment = normalized[max(0, note_pos - 2000): note_pos + 50000] if note_pos >= 0 else normalized

video_urls = []
for pattern in (r'"master_url":"([^"]+)"', r'"masterUrl":"([^"]+)"'):
    video_urls.extend(re.findall(pattern, normalized))

subtitle_url = ""
subtitle_lang = ""
media_v2_raw = json_string("mediaV2", segment)
if media_v2_raw:
    try:
        media_v2 = json.loads(media_v2_raw)
        subtitles = (((media_v2.get("video") or {}).get("subtitles")) or {})
        for lang in ("source", "zh-CN", "en-US"):
            items = subtitles.get(lang) or []
            if items and items[0].get("url"):
                subtitle_url = items[0]["url"].replace("\\u002F", "/")
                subtitle_lang = items[0].get("language") or lang
                break
    except Exception:
        pass
if not subtitle_url:
    subtitle_url = first(r'https://sns-subtitle[^"\\]+', normalized)

meta = {
    "platform": "xhs",
    "type": first(r'"type":"([^"]+)"', segment),
    "noteId": note_id,
    "title": json_string("title", segment),
    "desc": json_string("desc", segment),
    "author": json_string("nickname", segment),
    "time": json_number("time", segment),
    "lastUpdateTime": json_number("lastUpdateTime", segment),
    "likedCount": first(r'"likedCount":"([^"]+)"', segment),
    "collectedCount": first(r'"collectedCount":"([^"]+)"', segment),
    "commentCount": first(r'"commentCount":"([^"]+)"', segment),
    "shareCount": first(r'"shareCount":"([^"]+)"', segment),
    "videoUrl": video_urls[0] if video_urls else "",
    "subtitleUrl": subtitle_url,
    "subtitleLanguage": subtitle_lang,
    "fallback": "xhs_web_html",
}

out.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(meta, ensure_ascii=False))
PY

  local video_url subtitle_url
  video_url="$(python3 - "$web_meta" <<'PY'
import json, sys
print(json.load(open(sys.argv[1], encoding="utf-8")).get("videoUrl", ""))
PY
)"
  subtitle_url="$(python3 - "$web_meta" <<'PY'
import json, sys
print(json.load(open(sys.argv[1], encoding="utf-8")).get("subtitleUrl", ""))
PY
)"

  if [[ -n "$video_url" && ! -f "$RUN_DIR/video.mp4" ]]; then
    curl -L -A "Mozilla/5.0" -H "Referer: https://www.xiaohongshu.com/" "$video_url" -o "$RUN_DIR/video.mp4"
  fi
  if [[ -n "$subtitle_url" ]]; then
    curl -L -A "Mozilla/5.0" -H "Referer: https://www.xiaohongshu.com/" "$subtitle_url" -o "$RUN_DIR/subtitle.srt" || true
    if [[ -s "$RUN_DIR/subtitle.srt" ]]; then
      srt_to_text "$RUN_DIR/subtitle.srt" "$RUN_DIR/audio.txt"
    fi
  fi
  if [[ "$replace_metadata" == "true" ]]; then
    cp "$web_meta" "$METADATA"
  fi
}

prepare_xhs_detail_retry() {
  local detail="$RUN_DIR/xhs_detail_retry.json"
  curl -sS -X POST "$XHS_API_BASE/xhs/detail" \
    -H "Content-Type: application/json" \
    -d "$(json_payload false)" \
    -o "$detail"

  if ! json_has_data "$detail"; then
    return 1
  fi

  cp "$detail" "$METADATA"
  download_xhs_assets_from_json "$detail"
}

PLATFORM="$(detect_platform)"
: > "$MANIFEST"
printf '%s\n' "$URL" > "$RUN_DIR/source.url"
log "run_dir: $RUN_DIR"
log "platform: $PLATFORM"

case "$PLATFORM" in
  xhs)
    marker="$RUN_DIR/download.marker"
    : > "$marker"
    curl -sS -X POST "$XHS_API_BASE/xhs/detail" \
      -H "Content-Type: application/json" \
      -d "$(json_payload false)" \
      -o "$METADATA"
    if json_has_data "$METADATA"; then
      download_xhs_assets_from_json "$METADATA"
      prepare_xhs_web_fallback false
    else
      warn_xhs_cookie_if_needed
      log "warning: XHS API detail-only returned no data; retrying download=true mode"
      curl -sS -X POST "$XHS_API_BASE/xhs/detail" \
        -H "Content-Type: application/json" \
        -d "$(json_payload true)" \
        -o "$METADATA"
      copy_new_xhs_files "$marker"
      if ! json_has_data "$METADATA"; then
        log "warning: XHS API download=true returned no data; trying web HTML fallback for metadata/subtitles"
        prepare_xhs_web_fallback
      elif json_has_data "$METADATA"; then
        if [[ ! -f "$RUN_DIR/video.mp4" ]] && ! find "$RUN_DIR/xhs_images" -type f | grep -q .; then
          download_xhs_assets_from_json "$METADATA"
        fi
        prepare_xhs_web_fallback false
      fi
    fi
    ;;
  douyin|tiktok|bilibili)
    encoded_url="$(python3 - "$URL" <<'PY'
from urllib.parse import quote
import sys
print(quote(sys.argv[1], safe=""))
PY
)"
    curl -sS "$DOUYIN_API_BASE/api/hybrid/video_data?url=$encoded_url&minimal=false" -o "$METADATA"
    if video_url="$(extract_video_url)"; then
      case "$PLATFORM" in
        douyin) referer="https://www.douyin.com/" ;;
        tiktok) referer="https://www.tiktok.com/" ;;
        bilibili) referer="https://www.bilibili.com/" ;;
      esac
      download_video_from_url "$video_url" "$referer"
    else
      log "warning: no video url found in metadata"
    fi
    ;;
  *)
    log "warning: platform not automated by this script; use TikHub/Jina/browser fallback from fetch-playbook"
    printf '{"url": %s, "platform": %s, "message": "manual fallback required"}\n' \
      "$(python3 -c 'import json,sys; print(json.dumps(sys.argv[1]))' "$URL")" \
      "$(python3 -c 'import json,sys; print(json.dumps(sys.argv[1]))' "$PLATFORM")" > "$METADATA"
    ;;
esac

prepare_video_assets
prepare_image_sheet

{
  echo ""
  echo "outputs:"
  find "$RUN_DIR" -maxdepth 2 -type f | sort
} >> "$MANIFEST"

log "done: $RUN_DIR"
