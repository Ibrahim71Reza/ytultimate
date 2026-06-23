#!/usr/bin/env bash
# YT Ultimate CLI feature audit
#
# This script validates the claims made in the README as far as possible without
# needing a real video URL. Network/live download checks are optional and only run
# when you provide environment variables.
#
# Basic:
#   bash scripts/audit_features.sh
#
# With live metadata / dry-run checks using a video you are allowed to access:
#   YTDOWN_TEST_URL="https://www.youtube.com/watch?v=..." bash scripts/audit_features.sh
#
# With an actual test download of that permitted URL:
#   YTDOWN_TEST_URL="https://www.youtube.com/watch?v=..." YTDOWN_LIVE_DOWNLOAD=1 bash scripts/audit_features.sh
#
# Optional browser-cookie check:
#   YTDOWN_TEST_URL="..." YTDOWN_COOKIES_BROWSER=chrome bash scripts/audit_features.sh

set -u
set -o pipefail

ROOT_DIR="${1:-$(pwd)}"
ROOT_DIR="$(cd "$ROOT_DIR" 2>/dev/null && pwd || printf '%s' "$ROOT_DIR")"

if [[ ! -f "$ROOT_DIR/pyproject.toml" || ! -d "$ROOT_DIR/ytu" ]]; then
  echo "ERROR: Run this from the YT Ultimate project root, or pass the project path:" >&2
  echo "  bash scripts/audit_features.sh /path/to/ytultimate" >&2
  exit 2
fi

STAMP="$(date +%Y%m%d-%H%M%S)"
REPORT_ROOT="${YTDOWN_AUDIT_REPORT_DIR:-$ROOT_DIR/audit-reports/$STAMP}"
LOG_DIR="$REPORT_ROOT/logs"
REPORT_MD="$REPORT_ROOT/test-report.md"
REPORT_JSON="$REPORT_ROOT/test-report.json"
RESULTS_JSONL="$REPORT_ROOT/results.jsonl"
VENV_DIR="${YTDOWN_AUDIT_VENV:-$REPORT_ROOT/.venv}"
CMD_TIMEOUT="${YTDOWN_CMD_TIMEOUT:-120}"
INSTALL_TIMEOUT="${YTDOWN_INSTALL_TIMEOUT:-300}"
USE_CURRENT_ENV="${YTDOWN_USE_CURRENT_ENV:-0}"
SKIP_INSTALL="${YTDOWN_SKIP_INSTALL:-0}"
TEST_URL="${YTDOWN_TEST_URL:-}"
LIVE_DOWNLOAD="${YTDOWN_LIVE_DOWNLOAD:-0}"
TEST_AUDIO="${YTDOWN_TEST_AUDIO:-0}"
TEST_QUEUE_RUN="${YTDOWN_TEST_QUEUE_RUN:-0}"
COOKIES_BROWSER="${YTDOWN_COOKIES_BROWSER:-}"

mkdir -p "$LOG_DIR"
: > "$RESULTS_JSONL"

PASS=0
FAIL=0
SKIP=0
WARN=0
STEP_NO=0
START_EPOCH="$(date +%s)"

json_escape_python='import json,sys; print(json.dumps(sys.stdin.read())[1:-1])'

json_escape() {
  python3 -c "$json_escape_python" <<< "${1:-}"
}

append_result() {
  local status="$1"; shift
  local name="$1"; shift
  local detail="${1:-}"; shift || true
  local log_file="${1:-}"
  local safe_name safe_detail safe_log
  safe_name="$(json_escape "$name")"
  safe_detail="$(json_escape "$detail")"
  safe_log="$(json_escape "$log_file")"
  printf '{"step":%s,"status":"%s","name":"%s","detail":"%s","log":"%s"}\n' \
    "$STEP_NO" "$status" "$safe_name" "$safe_detail" "$safe_log" >> "$RESULTS_JSONL"
}

status_line() {
  local status="$1"; shift
  local name="$1"; shift
  local detail="${1:-}"
  case "$status" in
    PASS) printf '✅ PASS  %s%s\n' "$name" "${detail:+ — $detail}" ;;
    FAIL) printf '❌ FAIL  %s%s\n' "$name" "${detail:+ — $detail}" ;;
    SKIP) printf '⏭️  SKIP  %s%s\n' "$name" "${detail:+ — $detail}" ;;
    WARN) printf '⚠️  WARN  %s%s\n' "$name" "${detail:+ — $detail}" ;;
  esac
}

record() {
  local status="$1"; shift
  local name="$1"; shift
  local detail="${1:-}"; shift || true
  local log_file="${1:-}"
  STEP_NO=$((STEP_NO + 1))
  case "$status" in
    PASS) PASS=$((PASS + 1)) ;;
    FAIL) FAIL=$((FAIL + 1)) ;;
    SKIP) SKIP=$((SKIP + 1)) ;;
    WARN) WARN=$((WARN + 1)) ;;
  esac
  status_line "$status" "$name" "$detail" | tee -a "$REPORT_ROOT/console-summary.txt"
  append_result "$status" "$name" "$detail" "$log_file"
}

run_cmd() {
  local name="$1"; shift
  local log_name
  log_name="$(printf '%03d-%s.log' "$((STEP_NO + 1))" "$(echo "$name" | tr ' /:' '---' | tr -cd '[:alnum:]_.-')")"
  local log_path="$LOG_DIR/$log_name"
  {
    echo "# $name"
    echo "# cwd: $(pwd)"
    echo "# command: $*"
    echo
  } > "$log_path"

  if command -v timeout >/dev/null 2>&1; then
    timeout "$CMD_TIMEOUT" "$@" >> "$log_path" 2>&1
  else
    "$@" >> "$log_path" 2>&1
  fi
  local code=$?

  if [[ $code -eq 0 ]]; then
    record PASS "$name" "exit 0" "$log_path"
    return 0
  elif [[ $code -eq 124 ]]; then
    record FAIL "$name" "timed out after ${CMD_TIMEOUT}s" "$log_path"
    return 124
  else
    record FAIL "$name" "exit $code" "$log_path"
    return "$code"
  fi
}

run_cmd_allow_fail() {
  local name="$1"; shift
  local log_name
  log_name="$(printf '%03d-%s.log' "$((STEP_NO + 1))" "$(echo "$name" | tr ' /:' '---' | tr -cd '[:alnum:]_.-')")"
  local log_path="$LOG_DIR/$log_name"
  {
    echo "# $name"
    echo "# cwd: $(pwd)"
    echo "# command: $*"
    echo
  } > "$log_path"
  if command -v timeout >/dev/null 2>&1; then
    timeout "$CMD_TIMEOUT" "$@" >> "$log_path" 2>&1
  else
    "$@" >> "$log_path" 2>&1
  fi
  local code=$?
  record WARN "$name" "non-blocking exit $code" "$log_path"
  return 0
}

skip_step() {
  local name="$1"; shift
  local detail="${1:-}"
  STEP_NO=$((STEP_NO + 1))
  SKIP=$((SKIP + 1))
  status_line SKIP "$name" "$detail" | tee -a "$REPORT_ROOT/console-summary.txt"
  append_result SKIP "$name" "$detail" ""
}

warn_step() {
  local name="$1"; shift
  local detail="${1:-}"
  STEP_NO=$((STEP_NO + 1))
  WARN=$((WARN + 1))
  status_line WARN "$name" "$detail" | tee -a "$REPORT_ROOT/console-summary.txt"
  append_result WARN "$name" "$detail" ""
}

section() {
  echo
  echo "## $1" | tee -a "$REPORT_ROOT/console-summary.txt"
}

cd "$ROOT_DIR" || exit 2

cat > "$REPORT_MD" <<EOF
# YT Ultimate CLI Audit Report

Generated: $(date -Iseconds)
Project root: \`$ROOT_DIR\`
Report dir: \`$REPORT_ROOT\`

## Environment requested

| Variable | Value |
|---|---|
| YTDOWN_TEST_URL | ${TEST_URL:+provided}${TEST_URL:-not provided} |
| YTDOWN_LIVE_DOWNLOAD | $LIVE_DOWNLOAD |
| YTDOWN_TEST_AUDIO | $TEST_AUDIO |
| YTDOWN_TEST_QUEUE_RUN | $TEST_QUEUE_RUN |
| YTDOWN_COOKIES_BROWSER | ${COOKIES_BROWSER:-not provided} |
| YTDOWN_USE_CURRENT_ENV | $USE_CURRENT_ENV |
| YTDOWN_SKIP_INSTALL | $SKIP_INSTALL |

EOF

echo "YT Ultimate CLI audit starting..."
echo "Report will be saved to: $REPORT_ROOT"

section "Static project checks"

[[ -f pyproject.toml ]] && record PASS "Project has pyproject.toml" "found" || record FAIL "Project has pyproject.toml" "missing"
[[ -f README.md ]] && record PASS "Project has README.md" "found" || record FAIL "Project has README.md" "missing"
[[ -d ytu ]] && record PASS "Project has ytu package" "found" || record FAIL "Project has ytu package" "missing"
[[ -d tests ]] && record PASS "Project has tests directory" "found" || warn_step "Project has tests directory" "missing"
[[ -d .git ]] && record PASS "Local Git repository initialized" "found .git" || warn_step "Local Git repository initialized" "missing .git"

run_cmd "Validate pyproject entry points and dependencies" python3 - <<'PY'
from pathlib import Path
import sys
try:
    import tomllib
except Exception as exc:
    raise SystemExit(f"tomllib unavailable: {exc}")

pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
project = pyproject["project"]
scripts = project.get("scripts", {})
expected_scripts = {"ytdown", "yt-down", "ytultimate", "ytu"}
missing_scripts = expected_scripts - set(scripts)
assert not missing_scripts, f"missing script aliases: {missing_scripts}"
for name in expected_scripts:
    assert scripts[name] == "ytu.cli:app", f"{name} points to {scripts[name]!r}"

deps = "\n".join(project.get("dependencies", []))
for dep in ["yt-dlp", "typer", "rich", "platformdirs"]:
    assert dep in deps, f"missing dependency {dep}"
assert project.get("requires-python"), "requires-python missing"
print("Project:", project["name"], project["version"])
print("Scripts:", ", ".join(sorted(scripts)))
print("Dependencies OK")
PY

run_cmd "Validate source feature wiring" python3 - <<'PY'
from pathlib import Path
cli = Path("ytu/cli.py").read_text(encoding="utf-8")
core = Path("ytu/core.py").read_text(encoding="utf-8")
config = Path("ytu/config.py").read_text(encoding="utf-8")
formats = Path("ytu/formats.py").read_text(encoding="utf-8")

checks = {
    "download command": '@app.command("download")' in cli,
    "audio command": '@app.command("audio")' in cli,
    "wizard command": '@app.command("wizard")' in cli,
    "formats command": '@app.command("formats")' in cli,
    "plan command": '@app.command("plan")' in cli,
    "info command": '@app.command("info")' in cli,
    "init-config command": '@app.command("init-config")' in cli,
    "doctor command": '@app.command("doctor")' in cli,
    "selfcheck command": '@app.command("selfcheck")' in cli,
    "update-engine command": '@app.command("update-engine")' in cli,
    "queue subcommands": all(x in cli for x in ['@queue_app.command("add")', '@queue_app.command("list")', '@queue_app.command("run")', '@queue_app.command("clear")']),
    "yt_dlp import/use": "yt_dlp" in core,
    "ffmpeg check": 'shutil.which("ffmpeg")' in core or 'shutil.which("ffmpeg")' in cli,
    "SponsorBlock categories": "SPONSORBLOCK_CATEGORIES" in core,
    "presets": "PRESETS" in config and all(p in config for p in ["mobile", "lecture", "archive", "1080p", "720p"]),
    "fallback policies": all(p in formats for p in ["lower", "exact", "higher", "nearest", "any"]),
    "compat selector": "ext=mp4" in formats and "ext=m4a" in formats,
}
failed = [name for name, ok in checks.items() if not ok]
assert not failed, "missing feature wiring: " + ", ".join(failed)
for name in sorted(checks):
    print(f"OK: {name}")
PY

section "Install and command availability"

if [[ "$SKIP_INSTALL" == "1" ]]; then
  skip_step "Create isolated virtualenv and install project" "YTDOWN_SKIP_INSTALL=1"
elif [[ "$USE_CURRENT_ENV" == "1" ]]; then
  skip_step "Create isolated virtualenv and install project" "using current Python environment"
else
  run_cmd "Create isolated virtualenv" python3 -m venv "$VENV_DIR"
  # shellcheck disable=SC1091
  source "$VENV_DIR/bin/activate"
  if command -v timeout >/dev/null 2>&1; then
    run_cmd "Install project into isolated virtualenv" timeout "$INSTALL_TIMEOUT" python -m pip install --upgrade pip pytest >/dev/null
    run_cmd "Editable install project" timeout "$INSTALL_TIMEOUT" python -m pip install -e .
  else
    run_cmd "Install project into isolated virtualenv" python -m pip install --upgrade pip pytest
    run_cmd "Editable install project" python -m pip install -e .
  fi
fi

# Activate venv after install unless told otherwise.
if [[ "$SKIP_INSTALL" != "1" && "$USE_CURRENT_ENV" != "1" && -f "$VENV_DIR/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source "$VENV_DIR/bin/activate"
fi

run_cmd "Python import package" python - <<'PY'
import ytu
print("ytu version:", ytu.__version__)
import yt_dlp
print("yt-dlp version:", yt_dlp.version.__version__)
PY

for cmd in ytdown yt-down ytultimate ytu; do
  if command -v "$cmd" >/dev/null 2>&1; then
    record PASS "Command alias available: $cmd" "$(command -v "$cmd")"
    run_cmd "$cmd --version" "$cmd" --version
  else
    record FAIL "Command alias available: $cmd" "not found in PATH"
  fi
done

section "CLI help surface"

run_cmd "Top-level help" ytdown --help
for subcmd in download audio wizard formats plan info init-config doctor selfcheck update-engine queue; do
  run_cmd "Help: ytdown $subcmd" ytdown "$subcmd" --help
done
for subcmd in add list run clear; do
  run_cmd "Help: ytdown queue $subcmd" ytdown queue "$subcmd" --help
done

run_cmd "Help contains claimed download options" python - <<'PY'
import subprocess
help_text = subprocess.check_output(["ytdown", "download", "--help"], text=True)
required = [
    "--quality", "--exact-quality", "--fallback", "--format-id", "--compat", "--container",
    "--file", "--playlist", "--playlist-items", "--archive", "--rate-limit", "--retries",
    "--fragment-retries", "--fragments", "--cookies-from-browser", "--ffmpeg-location",
    "--sponsorblock-remove", "--sponsorblock-mark", "--format-sort", "--format-sort-force",
    "--write-info-json", "--write-description", "--thumbnail", "--embed-thumbnail",
    "--subs", "--auto-subs", "--embed-subs", "--sub-langs", "--dry-run", "--print-filename",
    "--overwrite", "--sleep", "--max-sleep", "--socket-timeout", "--preset",
]
missing = [x for x in required if x not in help_text]
assert not missing, "missing options: " + ", ".join(missing)
print("All claimed download options are visible in help.")
PY

section "Offline behavior tests"

run_cmd "Compile Python package" python -m compileall ytu
if [[ -d tests ]]; then
  run_cmd "Run included unit tests" python -m pytest -q
else
  skip_step "Run included unit tests" "tests directory missing"
fi

TMP_CONFIG="$REPORT_ROOT/config/config.json"
run_cmd "init-config creates config file" ytdown init-config --path "$TMP_CONFIG" --force
run_cmd "Validate generated config JSON" python - <<PY
import json
from pathlib import Path
path = Path(r"$TMP_CONFIG")
assert path.exists(), "config file not created"
data = json.loads(path.read_text(encoding="utf-8"))
for key in ["output_dir", "quality", "fallback", "container", "output_template", "retries", "fragment_retries", "playlist", "compat"]:
    assert key in data, f"missing config key {key}"
print("Config keys:", len(data))
PY

QUEUE_FILE="$REPORT_ROOT/queue/queue.jsonl"
run_cmd "Queue clear" ytdown queue clear --queue "$QUEUE_FILE"
run_cmd "Queue add URLs" ytdown queue add "https://example.com/video-a" "https://example.com/video-b" --quality 720p --fallback nearest --compat --queue "$QUEUE_FILE"
run_cmd "Queue list" ytdown queue list --queue "$QUEUE_FILE"
run_cmd "Validate queue JSONL" python - <<PY
import json
from pathlib import Path
path = Path(r"$QUEUE_FILE")
rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
assert len(rows) == 2, f"expected 2 queue rows, got {len(rows)}"
for row in rows:
    assert row["quality"] == "720p"
    assert row["fallback"] == "nearest"
    assert row["compat"] is True
    assert row["status"] == "queued"
print("Queue rows validated:", len(rows))
PY
run_cmd "Queue clear after validation" ytdown queue clear --queue "$QUEUE_FILE"

run_cmd "Internal feature assertions" python - <<'PY'
from pathlib import Path
from tempfile import TemporaryDirectory
from ytu.config import DEFAULT_CONFIG, PRESETS, apply_preset
from ytu.core import build_ydl_opts, normalize_urls, parse_cookies_from_browser
from ytu.formats import build_video_format, parse_quality, smart_default_quality

assert parse_quality("720p") == 720
assert parse_quality("1080") == 1080
assert parse_quality("best") is None
assert "height<=720" in build_video_format("720p", fallback="lower")
assert "height=720" in build_video_format("720p", fallback="exact")
assert "height>=720" in build_video_format("720p", fallback="higher")
nearest = build_video_format("720p", fallback="nearest")
assert "height=720" in nearest and "height<=720" in nearest and "height>=720" in nearest
compat = build_video_format("720p", fallback="lower", compat=True)
assert "ext=mp4" in compat and "ext=m4a" in compat
assert build_video_format("720p", format_id="137+140") == "137+140"
assert smart_default_quality([2160, 1080, 720]) == "1080p"
assert parse_cookies_from_browser("chrome:Profile 1") == ("chrome", "Profile 1")
assert apply_preset(DEFAULT_CONFIG, "mobile")["quality"] == "720p"
assert apply_preset(DEFAULT_CONFIG, "archive")["archive"] is True

with TemporaryDirectory() as td:
    url_file = Path(td) / "urls.txt"
    url_file.write_text("# comment\nhttps://a.example/video\nhttps://a.example/video\nhttps://b.example/video\n", encoding="utf-8")
    urls = normalize_urls(["https://c.example/video"], url_file)
    assert urls == ["https://c.example/video", "https://a.example/video", "https://b.example/video"]

    opts = build_ydl_opts(
        output_dir=Path(td) / "out",
        output_template="%(title)s.%(ext)s",
        quality="720p",
        exact_quality=False,
        format_id=None,
        compat=True,
        container="mp4",
        playlist=False,
        playlist_items="1:5,8",
        subtitles=True,
        auto_subtitles=True,
        embed_subtitles=True,
        sub_langs="en.*,bn",
        thumbnail=True,
        embed_thumbnail=True,
        metadata=True,
        safe_names=True,
        archive=True,
        archive_path=None,
        rate_limit="2M",
        retries=7,
        fragment_retries=8,
        concurrent_fragments=4,
        cookies_from_browser="chrome",
        ffmpeg_location="/usr/bin",
        sponsorblock_remove="sponsor,intro",
        sponsorblock_mark="outro",
        dry_run=True,
        fallback="nearest",
        format_sort="res:720,ext:mp4:m4a",
        format_sort_force=True,
        write_info_json=True,
        write_description=True,
        keep_video=True,
        no_overwrites=True,
        sleep_interval=1.0,
        max_sleep_interval=2.0,
        socket_timeout=30,
        print_filename=True,
    )
    assert opts["noplaylist"] is True
    assert opts["playlist_items"] == "1:5,8"
    assert opts["writesubtitles"] is True
    assert opts["writeautomaticsub"] is True
    assert opts["embedsubtitles"] is True
    assert opts["writethumbnail"] is True
    assert opts["writeinfojson"] is True
    assert opts["writedescription"] is True
    assert opts["restrictfilenames"] is True
    assert opts["download_archive"].endswith(".download-archive.txt")
    assert opts["ratelimit"] == "2M"
    assert opts["cookiesfrombrowser"] == ("chrome",)
    assert opts["sponsorblock_remove"] == ["sponsor", "intro"]
    assert opts["sponsorblock_mark"] == ["outro"]
    assert opts["simulate"] is True and opts["skip_download"] is True
    assert opts["format_sort"] == ["res:720", "ext:mp4:m4a"]
    assert opts["format_sort_force"] is True
    assert opts["overwrites"] is False

print("Internal features validated.")
PY

section "External dependency checks"

run_cmd "doctor command" ytdown doctor
run_cmd "selfcheck command" ytdown selfcheck

for bin in python3 git ffmpeg ffprobe; do
  if command -v "$bin" >/dev/null 2>&1; then
    record PASS "External binary available: $bin" "$(command -v "$bin")"
  else
    if [[ "$bin" == "ffmpeg" || "$bin" == "ffprobe" ]]; then
      record FAIL "External binary available: $bin" "missing; install with sudo apt install ffmpeg"
    else
      record FAIL "External binary available: $bin" "missing"
    fi
  fi
done

section "Optional live URL tests"

if [[ -z "$TEST_URL" ]]; then
  skip_step "Live info/plan/formats/dry-run tests" "Set YTDOWN_TEST_URL to a video URL you are allowed to access."
else
  run_cmd "Live info" ytdown info "$TEST_URL"
  run_cmd "Live plan" ytdown plan "$TEST_URL"
  run_cmd "Live formats" ytdown formats "$TEST_URL"
  run_cmd "Live dry-run 720p nearest" ytdown download "$TEST_URL" --quality 720p --fallback nearest --compat --container mp4 --dry-run --output-dir "$REPORT_ROOT/live-dry-run"
  run_cmd "Live dry-run metadata/subtitle flags" ytdown download "$TEST_URL" --quality 720p --fallback nearest --subs --auto-subs --embed-subs --sub-langs "en.*" --thumbnail --write-info-json --write-description --dry-run --output-dir "$REPORT_ROOT/live-dry-run-metadata"

  if [[ -n "$COOKIES_BROWSER" ]]; then
    run_cmd_allow_fail "Live dry-run with cookies-from-browser" ytdown download "$TEST_URL" --cookies-from-browser "$COOKIES_BROWSER" --dry-run --output-dir "$REPORT_ROOT/live-dry-run-cookies"
  else
    skip_step "Browser-cookie live test" "Set YTDOWN_COOKIES_BROWSER=chrome or firefox to test this path."
  fi

  if [[ "$LIVE_DOWNLOAD" == "1" ]]; then
    LIVE_OUT="$REPORT_ROOT/live-download"
    run_cmd "Actual video download test" ytdown download "$TEST_URL" --quality 360p --fallback nearest --compat --container mp4 --archive --output-dir "$LIVE_OUT"
    run_cmd "Validate actual video output exists" python - <<PY
from pathlib import Path
root = Path(r"$LIVE_OUT")
files = [p for p in root.rglob("*") if p.is_file() and not p.name.startswith(".")]
assert files, f"no output files found under {root}"
for f in files[:20]:
    print(f.relative_to(root), f.stat().st_size)
PY
  else
    skip_step "Actual video download test" "Set YTDOWN_LIVE_DOWNLOAD=1 to download the permitted test URL."
  fi

  if [[ "$TEST_AUDIO" == "1" ]]; then
    AUDIO_OUT="$REPORT_ROOT/live-audio"
    run_cmd "Actual audio extraction test" ytdown audio "$TEST_URL" --audio-format m4a --audio-quality 0 --output-dir "$AUDIO_OUT"
    run_cmd "Validate actual audio output exists" python - <<PY
from pathlib import Path
root = Path(r"$AUDIO_OUT")
files = [p for p in root.rglob("*") if p.is_file() and not p.name.startswith(".")]
assert files, f"no audio output files found under {root}"
for f in files[:20]:
    print(f.relative_to(root), f.stat().st_size)
PY
  else
    skip_step "Actual audio extraction test" "Set YTDOWN_TEST_AUDIO=1 together with YTDOWN_TEST_URL to run this."
  fi

  if [[ "$TEST_QUEUE_RUN" == "1" ]]; then
    LIVE_QUEUE="$REPORT_ROOT/live-queue/queue.jsonl"
    run_cmd "Live queue clear" ytdown queue clear --queue "$LIVE_QUEUE"
    run_cmd "Live queue add" ytdown queue add "$TEST_URL" --quality 360p --fallback nearest --compat --queue "$LIVE_QUEUE"
    run_cmd "Live queue run" ytdown queue run --queue "$LIVE_QUEUE" --output-dir "$REPORT_ROOT/live-queue-downloads"
    run_cmd "Validate live queue status" python - <<PY
import json
from pathlib import Path
rows = [json.loads(line) for line in Path(r"$LIVE_QUEUE").read_text(encoding="utf-8").splitlines() if line.strip()]
assert rows and rows[0]["status"] == "done", rows
print(rows)
PY
  else
    skip_step "Live queue run" "Set YTDOWN_TEST_QUEUE_RUN=1 to download the permitted test URL through queue."
  fi
fi

section "Report finalization"

END_EPOCH="$(date +%s)"
DURATION=$((END_EPOCH - START_EPOCH))

python - <<PY
from pathlib import Path
import json
report_root = Path(r"$REPORT_ROOT")
results = []
for line in Path(r"$RESULTS_JSONL").read_text(encoding="utf-8").splitlines():
    if line.strip():
        results.append(json.loads(line))
summary = {
    "project_root": r"$ROOT_DIR",
    "report_root": r"$REPORT_ROOT",
    "duration_seconds": $DURATION,
    "pass": $PASS,
    "fail": $FAIL,
    "warn": $WARN,
    "skip": $SKIP,
    "live_url_provided": bool(r"$TEST_URL"),
    "live_download_enabled": r"$LIVE_DOWNLOAD" == "1",
    "results": results,
}
Path(r"$REPORT_JSON").write_text(json.dumps(summary, indent=2), encoding="utf-8")
PY

cat >> "$REPORT_MD" <<EOF
## Summary

| Status | Count |
|---|---:|
| PASS | $PASS |
| FAIL | $FAIL |
| WARN | $WARN |
| SKIP | $SKIP |

Duration: ${DURATION}s

## Results

EOF

python - <<PY >> "$REPORT_MD"
from pathlib import Path
import json, os
report_root = Path(r"$REPORT_ROOT")
for line in Path(r"$RESULTS_JSONL").read_text(encoding="utf-8").splitlines():
    if not line.strip():
        continue
    item = json.loads(line)
    icon = {"PASS":"✅", "FAIL":"❌", "WARN":"⚠️", "SKIP":"⏭️"}.get(item["status"], "•")
    log = item.get("log") or ""
    if log:
        try:
            rel = Path(log).relative_to(report_root)
        except Exception:
            rel = Path(log)
        log_text = f" — log: `{rel}`"
    else:
        log_text = ""
    detail = f" — {item.get('detail','')}" if item.get('detail') else ""
    print(f"- {icon} **{item['status']}**: {item['name']}{detail}{log_text}")
PY

cat >> "$REPORT_MD" <<EOF

## How to reproduce with live checks

Metadata and dry-run only:

\`\`\`bash
YTDOWN_TEST_URL="PASTE_A_PERMITTED_VIDEO_URL_HERE" bash scripts/audit_features.sh
\`\`\`

Actual video download:

\`\`\`bash
YTDOWN_TEST_URL="PASTE_A_PERMITTED_VIDEO_URL_HERE" YTDOWN_LIVE_DOWNLOAD=1 bash scripts/audit_features.sh
\`\`\`

Actual audio extraction:

\`\`\`bash
YTDOWN_TEST_URL="PASTE_A_PERMITTED_VIDEO_URL_HERE" YTDOWN_TEST_AUDIO=1 bash scripts/audit_features.sh
\`\`\`

EOF

echo
printf 'Audit complete. Report files:\n'
printf '  Markdown: %s\n' "$REPORT_MD"
printf '  JSON:     %s\n' "$REPORT_JSON"
printf '  Logs:     %s\n' "$LOG_DIR"
printf '\nSummary: PASS=%s FAIL=%s WARN=%s SKIP=%s\n' "$PASS" "$FAIL" "$WARN" "$SKIP"

if [[ "$FAIL" -gt 0 ]]; then
  exit 1
fi
exit 0
