# 🦀 PinchBench

**Real-world benchmarks for AI coding agents**

[![Leaderboard](https://img.shields.io/badge/leaderboard-pinchbench.com-blue)](https://pinchbench.com)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

> **Note:** This repository contains the benchmark skill/tasks. It is NOT the source of official leaderboard results. To add models to the official results, modify [pinchbench/scripts/default-models.yml](https://github.com/pinchbench/scripts/blob/main/default-models.yml).

PinchBench measures how well LLM models perform as the brain of an [OpenClaw](https://github.com/openclaw/openclaw) agent. Instead of synthetic tests, we throw real tasks at agents: scheduling meetings, writing code, triaging email, researching topics, and managing files.

Results are collected on a public leaderboard at **[pinchbench.com](https://pinchbench.com)**.

![PinchBench](pinchbench.png)

## Why PinchBench?

Most LLM benchmarks test isolated capabilities. PinchBench tests what actually matters for coding agents:

- **Tool usage** — Can the model call the right tools with the right parameters?
- **Multi-step reasoning** — Can it chain together actions to complete complex tasks?
- **Real-world messiness** — Can it handle ambiguous instructions and incomplete information?
- **Practical outcomes** — Did it actually create the file, send the email, or schedule the meeting?

## Quick Start

```bash
# Clone the skill
git clone https://github.com/pinchbench/skill.git
cd skill

# Run benchmarks with your model of choice
./scripts/run.sh --model openrouter/anthropic/claude-sonnet-4

# Or run specific tasks
./scripts/run.sh --model openrouter/openai/gpt-4o --suite task_01_calendar,task_02_stock
```

> **Note:** Model IDs must include their provider prefix (e.g. `openrouter/`, `anthropic/`). [OpenRouter](https://openrouter.ai) is the default provider used for routing.

**Requirements:**

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) package manager
- A running OpenClaw instance

## Configuration

Copy `.env.example` to `.env` in the repo root and fill in your keys — the benchmark loads it automatically so you never need to `export` manually:

```bash
cp .env.example .env
# then edit .env with your OPENROUTER_API_KEY (and others as needed)
```

Shell exports always take precedence over `.env` values, so per-session overrides still work.

## What Gets Tested

PinchBench includes 23 tasks across real-world categories:

| Category         | Tasks                                   | What's tested                            |
| ---------------- | --------------------------------------- | ---------------------------------------- |
| **Productivity** | Calendar, daily summaries               | Event creation, time parsing, scheduling |
| **Research**     | Stock prices, conferences, markets      | Web search, data extraction, synthesis   |
| **Writing**      | Blog posts, emails, humanization        | Content generation, tone, formatting     |
| **Coding**       | Weather scripts, file structures        | Code generation, file operations         |
| **Analysis**     | Spreadsheets, PDFs, documents           | Data processing, summarization           |
| **Email**        | Triage, search                          | Inbox management, filtering              |
| **Memory**       | Context retrieval, knowledge management | Long-term memory, recall                 |
| **Skills**       | ClawHub, skill discovery                | OpenClaw ecosystem integration           |

Each task is graded automatically, by an LLM judge, or both — ensuring both objective and nuanced evaluation.

## Submitting Results

To get your results on the leaderboard:

```bash
# Register for an API token (one-time)
./scripts/run.sh --register

# Run benchmark — results auto-upload with your token
./scripts/run.sh --model openrouter/anthropic/claude-sonnet-4
```

Skip uploading with `--no-upload` if you just want local results.

### Official Results

To submit an official run (marked on the leaderboard):

```bash
# Using environment variable
export PINCHBENCH_OFFICIAL_KEY=your_official_key
./scripts/run.sh --model anthropic/claude-sonnet-4

# Using command line flag
./scripts/run.sh --model anthropic/claude-sonnet-4 --official-key your_official_key
```

## Command Reference

| Flag                     | Description                                                                   |
| ------------------------ | ----------------------------------------------------------------------------- |
| `--model MODEL`          | Model to test (e.g., `openrouter/anthropic/claude-sonnet-4`)                  |
| `--judge MODEL`          | Judge model for LLM grading (default: `openrouter/anthropic/claude-opus-4.5`) |
| `--judge-backend`        | `api` (default) or `openclaw` — how the judge is invoked                      |
| `--suite SUITE`          | `all`, `automated-only`, or comma-separated task IDs                          |
| `--runs N`               | Number of runs per task for averaging                                         |
| `--timeout-multiplier N` | Scale timeouts for slower models                                              |
| `--output-dir DIR`       | Where to save results (default: `results/`)                                   |
| `--execute-only`         | Run tasks and archive artifacts, skip grading                                 |
| `--grade-only`           | Re-grade previously archived artifacts without re-running tasks               |
| `--no-upload`            | Skip uploading to leaderboard                                                 |
| `--register`             | Request an API token for submissions                                          |
| `--upload FILE`          | Upload a previous results JSON                                                |
| `--official-key KEY`     | Mark submission as official (or use `PINCHBENCH_OFFICIAL_KEY` env var)        |

### Judge

The LLM judge calls the model API directly by default (`--judge-backend api`), bypassing OpenClaw. The default judge model is `openrouter/anthropic/claude-opus-4.5`.

```bash
# Default: direct API call, no extra flags needed
./scripts/run.sh --model openrouter/anthropic/claude-sonnet-4

# Override judge model (still direct API)
./scripts/run.sh --model openai/gpt-4o --judge openrouter/anthropic/claude-opus-4.5

# Direct API via Anthropic
./scripts/run.sh --model openai/gpt-4o --judge anthropic/claude-sonnet-4-5-20250514

# Direct API via OpenAI
./scripts/run.sh --model openai/gpt-4o --judge openai/gpt-4o

# Headless Claude CLI
./scripts/run.sh --model openai/gpt-4o --judge claude

# Run judge as an OpenClaw agent session instead
./scripts/run.sh --model openai/gpt-4o --judge-backend openclaw
```

Required env vars: `OPENROUTER_API_KEY`, `ANTHROPIC_API_KEY`, or `OPENAI_API_KEY` depending on the judge model prefix.

### Split execution and grading

Run tasks and grade in separate steps — useful when you want to re-grade with a different judge without re-running the model:

```bash
# Step 1: run tasks, archive artifacts, skip grading
./scripts/run.sh --model openrouter/anthropic/claude-sonnet-4 --execute-only

# Step 2: grade archived artifacts (fast, no model re-run)
./scripts/run.sh --model openrouter/anthropic/claude-sonnet-4 --grade-only --no-upload

# Grade only specific tasks
./scripts/run.sh --model openrouter/anthropic/claude-sonnet-4 --grade-only --suite task_03_blog --no-upload
```

## Contributing Tasks

We welcome new tasks! Check out [`tasks/TASK_TEMPLATE.md`](tasks/TASK_TEMPLATE.md) for the format. Good tasks are:

- **Real-world** — Something an actual user would ask an agent to do
- **Measurable** — Clear success criteria that can be graded
- **Reproducible** — Same task should produce consistent grading
- **Challenging** — Tests agent capabilities, not just LLM knowledge

### Transcript Archive

Session transcripts are automatically saved to `results/{run_id}_transcripts/` alongside the results JSON. Each task's full agent conversation is preserved as a JSONL file (e.g. `task_01_calendar.jsonl`) for post-run analysis.

## Links

- **Leaderboard:** [pinchbench.com](https://pinchbench.com)
- **OpenClaw:** [github.com/openclaw/openclaw](https://github.com/openclaw/openclaw)
- **Issues:** [github.com/pinchbench/skill/issues](https://github.com/pinchbench/skill/issues)

## Star History

<a href="https://www.star-history.com/?repos=pinchbench%2Fskill&type=date&logscale=&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/chart?repos=pinchbench/skill&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/chart?repos=pinchbench/skill&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/chart?repos=pinchbench/skill&type=date&legend=top-left" />
 </picture>
</a>

## License

MIT — see [LICENSE](LICENSE) for details.

---

_Claw-some AI agent testing_ 🦞
