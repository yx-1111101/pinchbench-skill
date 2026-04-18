#!/usr/bin/env bash
#
# OpenFriday 70 任务（6 个场景，不含 tasks/ 根目录下 27 个 PinchBench）：
#   先按模型顺序跑完 execute-only，再统一 grade-only。
#
# 用法：
#   ./scripts/run_openfriday_70_execute_then_grade.sh
#   OPENROUTER_ENV=/path/to.env ./scripts/run_openfriday_70_execute_then_grade.sh
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${SKILL_ROOT}"

# OpenRouter 密钥等（与 OpenClaw 一致）
OPENROUTER_ENV="${OPENROUTER_ENV:-${HOME}/.config/openclaw/openrouter.env}"
if [[ -f "${OPENROUTER_ENV}" ]]; then
  set -a
  # shellcheck source=/dev/null
  source "${OPENROUTER_ENV}"
  set +a
else
  echo "警告: 未找到 ${OPENROUTER_ENV}，若缺少 OPENROUTER_API_KEY 可能导致失败。" >&2
fi

if command -v uv >/dev/null 2>&1; then
  UV=(uv run)
elif [[ -x "${HOME}/.local/bin/uv" ]]; then
  UV=("${HOME}/.local/bin/uv" run)
else
  echo "错误: 未找到 uv，请先安装: curl -LsSf https://astral.sh/uv/install.sh | sh" >&2
  exit 1
fi

BENCH=(scripts/friday_benchmark.py)
JUDGE_MODEL="${JUDGE_MODEL:-openrouter/anthropic/claude-opus-4.6}"

# 70 = 15+11+12+13+9+10（与 FRIDAY_README 中 OpenFriday 场景一致）
CATEGORIES=(
  foundation
  secretary
  programmer
  operator
  finance
  digital_twin
)

MODELS=(
  "openrouter/bytedance-seed/seed-2.0-lite"
  "openrouter/x-ai/grok-4.20"
  "openrouter/qwen/qwen3.6-plus"
  "openrouter/openai/gpt-5.4"
  "openrouter/google/gemini-3-flash-preview"
)

run_bench() {
  "${UV[@]}" "${BENCH[@]}" "$@"
}

echo "== 阶段 1: 按模型依次执行（每模型 ${#CATEGORIES[@]} 个场景 ≈ 70 任务），仅归档、不评分 =="
for model in "${MODELS[@]}"; do
  echo ""
  echo ">>> 模型: ${model}"
  for cat in "${CATEGORIES[@]}"; do
    echo "    --category ${cat} --execute-only"
    run_bench --model "${model}" --category "${cat}" --execute-only
  done
done

echo ""
echo "== 阶段 2: 全部模型执行完毕后，按模型与场景评分（LLM Judge: ${JUDGE_MODEL}）=="
for model in "${MODELS[@]}"; do
  echo ""
  echo ">>> 模型: ${model}"
  for cat in "${CATEGORIES[@]}"; do
    echo "    --category ${cat} --grade-only --judge ${JUDGE_MODEL}"
    run_bench --model "${model}" --category "${cat}" --grade-only --judge "${JUDGE_MODEL}"
  done
done

echo ""
echo "完成。结果目录: ${SKILL_ROOT}/results/<scope>/<model_slug>/<category>/"
