#!/usr/bin/env bash
# Run the RAG evaluation suite locally without freezing the machine.
#
#   scripts/run_evaluation.sh --limit 10        # next 10 unfinished cases (a batch)
#   scripts/run_evaluation.sh                   # everything that is left
#   scripts/run_evaluation.sh --case orion-pro-price
#
# Safety measures:
#   - The LLM runs CPU-only in the `ollama-cpu` container, which has no GPU
#     devices, so generation can never stall the desktop's GPU.
#   - Ollama and the runner are pinned to CPU threads 4-15 (0-3 stay free for
#     the desktop), with CPU, memory and swap caps: an overload stops a
#     container instead of pushing the host into swap.
#   - Refuses to start unless enough memory is free.
#   - Pauses the API, worker, scheduler and frontend for the run and restores
#     them afterwards (also on Ctrl+C or errors).
#   - Resumes automatically: rerun the same command to continue.
#
# Tunables (environment variables):
#   EVAL_PROVIDER=ollama  ollama (CPU-only container), gemini or openrouter (remote APIs)
#   EVAL_MODEL=...        model (default: OLLAMA_MODEL / OPENROUTER_MODEL from .env)
#   OLLAMA_MEMORY         default 3584m for 4B models, 6500m otherwise
#   OLLAMA_CPUS=6  OLLAMA_CPUSET=4-15
#   EVAL_MEMORY=2048m    EVAL_CPUS=2    EVAL_THREADS=2
#   EVAL_PAUSE=5          seconds to rest between cases
#   EVAL_MIN_FREE_MB      required free memory (default: both caps + 512)
#   EVAL_OUTPUT=...       result file (default: evaluation_runs/local-<model>-cpu.json)
#   EVAL_FRESH=1          start over instead of resuming
#   KEEP_BACKEND=1        leave the API running (needs ~0.6 GB more memory)
set -euo pipefail

repo_root=$(cd "$(dirname "$0")/.." && pwd)
cd "$repo_root"

env_file=${ENV_FILE:-.env}
[ -f "$env_file" ] || { echo "Missing $env_file (copy .env.example)." >&2; exit 1; }

env_value() { grep -E "^$1=" "$env_file" | tail -1 | cut -d= -f2- || true; }

provider=${EVAL_PROVIDER:-ollama}
case "$provider" in
  ollama) model=${EVAL_MODEL:-$(env_value OLLAMA_MODEL)}; model=${model:-qwen3:8b}; runtime_suffix=-cpu ;;
  openrouter)
    model=${EVAL_MODEL:-$(env_value OPENROUTER_MODEL)}; model=${model:-google/gemma-4-31b-it:free}; runtime_suffix=
    [ -n "$(env_value OPENROUTER_API_KEY)" ] || { echo "Set OPENROUTER_API_KEY in $env_file first." >&2; exit 1; } ;;
  gemini)
    model=${EVAL_MODEL:-$(env_value GEMINI_MODEL)}; model=${model:-gemini-3.1-flash-lite}; runtime_suffix=
    [ -n "$(env_value GEMINI_API_KEY)" ] || { echo "Set GEMINI_API_KEY in $env_file first." >&2; exit 1; } ;;
  *) echo "EVAL_PROVIDER must be ollama, openrouter or gemini." >&2; exit 1 ;;
esac
# Weights + KV cache + headroom. qwen3:4b is ~2.6 GB of weights, qwen3:8b ~5.2 GB.
case "$model" in
  *:4b*|*-4b*) default_ollama_memory=3584m ;;
  *) default_ollama_memory=6500m ;;
esac
export OLLAMA_MEMORY=${OLLAMA_MEMORY:-$default_ollama_memory}
export EVAL_MEMORY=${EVAL_MEMORY:-2048m}

compose=(docker compose --env-file "$env_file"
  -f infrastructure/docker/docker-compose.yml
  -f infrastructure/docker/docker-compose.evaluation.yml)

to_mb() {  # 6500m / 7g -> MB
  local value=${1,,}
  case "$value" in
    *g) echo $(( ${value%g} * 1024 )) ;;
    *m) echo "${value%m}" ;;
    *) echo $(( value / 1024 / 1024 )) ;;
  esac
}

output=${EVAL_OUTPUT:-evaluation_runs/${provider}-${model//[^A-Za-z0-9._-]/-}${runtime_suffix}.json}
mkdir -p backend/evaluation_runs

pause_services=(worker scheduler frontend)
[ "${KEEP_BACKEND:-0}" = "1" ] || pause_services+=(backend)

running=()
for service in "${pause_services[@]}"; do
  if [ -n "$("${compose[@]}" ps --status running -q "$service" 2>/dev/null)" ]; then
    running+=("$service")
  fi
done

restore() {
  "${compose[@]}" stop ollama-cpu >/dev/null 2>&1 || true
  if [ ${#running[@]} -gt 0 ]; then
    echo "Restarting: ${running[*]}"
    "${compose[@]}" start "${running[@]}" >/dev/null || true
  fi
}
trap restore EXIT

if systemctl is-active --quiet ollama 2>/dev/null; then
  echo "Note: the host Ollama service is running. It is not used here; stop it to free memory:" >&2
  echo "      sudo systemctl stop ollama" >&2
fi

if [ ${#running[@]} -gt 0 ]; then
  echo "Pausing while the evaluation runs: ${running[*]}"
  "${compose[@]}" stop "${running[@]}" >/dev/null
fi

llm_mb=0
[ "$provider" = "ollama" ] && llm_mb=$(to_mb "$OLLAMA_MEMORY")
required_mb=${EVAL_MIN_FREE_MB:-$(( llm_mb + $(to_mb "$EVAL_MEMORY") + 512 ))}
available_mb=$(( $(awk '/MemAvailable/ {print $2}' /proc/meminfo) / 1024 ))
if [ "$available_mb" -lt "$required_mb" ]; then
  echo "Not starting: ${available_mb} MB of memory is free, ${required_mb} MB is needed." >&2
  echo "Close browsers/editors you don't need, or lower EVAL_MIN_FREE_MB at your own risk." >&2
  exit 1
fi
echo "Memory check: ${available_mb} MB free, ${required_mb} MB needed."

if [ "$provider" = "ollama" ]; then
  echo "Starting database, cache and CPU-only Ollama..."
  "${compose[@]}" up -d --wait postgres redis ollama-cpu >/dev/null
else
  echo "Starting database and cache (LLM: $provider API, no local model)..."
  "${compose[@]}" up -d --wait postgres redis >/dev/null
fi

# Remote free tiers limit requests per minute; ~7 s apart stays under ~8/min.
default_pause=5
[ "$provider" != "ollama" ] && default_pause=7

resume=(--resume)
[ "${EVAL_FRESH:-0}" = "1" ] && resume=()

echo "Results: backend/$output"
set +e
"${compose[@]}" run --rm --no-deps -T evaluation \
  python -m app.evaluation.runner \
  --output "$output" \
  --pause-seconds "${EVAL_PAUSE:-$default_pause}" \
  --provider "$provider" --model "$model" \
  "${resume[@]}" "$@" \
  2>&1 | grep --line-buffered -vE 'Warning: You are sending|Loading weights|Batches:|HTTP Request|FutureWarning|warnings.warn|get_sentence_embedding' \
  | tee -a "backend/${output%.json}.txt"
status=${PIPESTATUS[0]}
set -e

if [ "$status" -eq 137 ]; then
  echo "The run was stopped (a memory cap was hit, or it was stopped manually); the host was protected." >&2
  echo "Rerun the same command to resume, or raise OLLAMA_MEMORY / EVAL_MEMORY." >&2
fi
exit "$status"
