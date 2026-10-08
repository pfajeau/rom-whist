#!/usr/bin/env bash
# Run the app and one AI service for each game. Ctrl+C stops them all.
set -Eeuo pipefail

cd -- "$(dirname -- "${BASH_SOURCE[0]}")"

# Prefer the project's environment without requiring manual activation.
if [[ -d venv/bin ]]; then
    export PATH="$PWD/venv/bin:$PATH"
fi
command -v python >/dev/null
command -v gunicorn >/dev/null

pids=()
cleanup() {
    trap - EXIT INT TERM
    if ((${#pids[@]})); then
        kill "${pids[@]}" 2>/dev/null || true
        wait "${pids[@]}" 2>/dev/null || true
    fi
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

echo 'Starting app on http://localhost:5000'
gunicorn -k gthread -w 1 --threads 100 -b :5000 'romwhist:create_app()' &
app_pid=$!
pids+=("$app_pid")

# AI clients connect immediately, so wait for the app to serve requests first.
ready=false
for ((attempt = 0; attempt < 60; attempt++)); do
    if ! kill -0 "$app_pid" 2>/dev/null; then
        echo 'App exited during startup.' >&2
        exit 1
    fi
    if python - <<'PY'
import urllib.error
import urllib.request

try:
    with urllib.request.urlopen('http://127.0.0.1:5000/home', timeout=1) as response:
        success = response.status == 200
except (OSError, urllib.error.URLError):
    success = False
raise SystemExit(0 if success else 1)
PY
    then
        ready=true
        break
    fi
    sleep 1
done
if [[ "$ready" != true ]]; then
    echo 'App did not become ready on port 5000.' >&2
    exit 1
fi

for game in ohell belote contree poker; do
    echo "Starting $game AI"
    python -u -m romwhist.ai.ai -g "$game" &
    pids+=("$!")
done

echo 'App and all four AI services started. Press Ctrl+C to stop.'
# Stop the remaining services if any one exits.
status=0
wait -n "${pids[@]}" || status=$?
echo 'A service exited; stopping all services.' >&2
exit "$status"
