# Friday Benchmark — OpenFriday 评测集成指南

基于 PinchBench 框架，集成了 OpenFriday 的 70 个真实 C 端场景评测任务。

## 架构

```
pinchbench-skill/
├── scripts/
│   ├── benchmark.py              # 通用评测入口（已支持 category / result_key / 两阶段模式）
│   ├── friday_benchmark.py       # Friday 兼容入口：仅保留递归任务发现 + dataset_dir 注入
│   ├── friday_adapter.py         # Friday 适配层：递归加载任务 + workspace 叠加 dataset_dir
│   ├── convert_friday_tasks.py   # 任务格式转换工具（新增）
│   ├── lib_agent.py              # PinchBench OpenClaw 执行引擎（已增强 transcript 等待）
│   ├── lib_grading.py            # PinchBench 评分引擎（未修改）
│   └── lib_tasks.py              # 通用任务加载（已支持 category 过滤，可被 Friday loader 复用）
├── tasks/
│   ├── task_00_sanity.md         # PinchBench 原始 27 个任务
│   ├── task_01_calendar.md
│   ├── ...
│   ├── foundation/               # OpenFriday 基础能力（15 个）
│   ├── secretary/                # OpenFriday 高级秘书（11 个）
│   ├── programmer/               # OpenFriday AI 程序员（12 个）
│   ├── operator/                 # OpenFriday 全域运营（13 个）
│   ├── finance/                  # OpenFriday 金融伙伴（9 个）
│   └── digital_twin/             # OpenFriday 数字分身（10 个）
├── dataset/                      # OpenFriday 任务输入数据（只读）
│   ├── foundation/
│   ├── secretary/
│   └── ...
└── assets/                       # PinchBench 原始任务数据
```

### 工作原理

```text
benchmark.py
  │
  ├── 负责通用链路：
  │   参数解析 / 执行 / 评分 / 两阶段模式 / 结果写入 / 上传
  │
  ├── 默认使用 TaskLoader
  │   扫描 tasks/task_*.md
  │
  └── 支持注入自定义 BenchmarkRunner / TaskLoader

friday_benchmark.py
  │
  ├── 替换成 FridayTaskLoader
  │   递归扫描 tasks/<scene>/task_*.md
  │
  ├── monkey-patch prepare_task_workspace
  │   额外把 frontmatter 中的 dataset_dir 整体拷入 workspace
  │
  └── 其余全部直接复用 benchmark.py
```

## 前置条件

| 条件 | 验证命令 |
|------|----------|
| Python >= 3.10 | `python3 --version` |
| `openclaw` CLI 在 PATH 中 | `openclaw --version` |
| 已有 main agent | `openclaw agents list` |
| models.json 已配置 | `cat ~/.openclaw/agents/main/agent/models.json` |

## 安装

```bash
# 1. 克隆仓库
git clone git@github.com:yx-1111101/pinchbench-skill.git
cd pinchbench-skill
git checkout friday-integration

# 2. 安装依赖（二选一）
# 方式 A：uv（推荐）
pip install uv
uv sync

# 方式 B：pip
pip install pyyaml>=6.0.1
```

## 运行评测

### 基本用法

```bash
# 跑全部 97 个任务（PinchBench 27 + OpenFriday 70）
uv run scripts/friday_benchmark.py \
  --model anthropic/claude-sonnet-4

# 跑原始 PinchBench 27 个任务（不变）
uv run scripts/benchmark.py \
  --model anthropic/claude-sonnet-4
```

### 两阶段运行

`scripts/benchmark.py` 和 `scripts/friday_benchmark.py` 现在都复用同一套两阶段执行/评分逻辑；对于 Friday 任务，兼容入口只额外处理递归任务发现和 `dataset_dir` workspace 注入。

```bash
# 第 1 步：只执行 Friday 任务，归档评分依赖文件
uv run scripts/friday_benchmark.py \
  --model anthropic/claude-sonnet-4 \
  --execute-only

# 第 2 步：基于默认结果目录下已归档的 artifacts 计算评分
uv run scripts/friday_benchmark.py \
  --model anthropic/claude-sonnet-4 \
  --grade-only
```

现在结果会按 `result_key` 分目录，避免不同类别/过滤条件互相覆盖：

- `summary.json` 写到 `results/<scope>/<model_slug>/<result_key>/summary.json`
- `transcripts/` 写到 `results/<scope>/<model_slug>/<result_key>/transcripts/`
- `artifacts/` 写到 `results/<scope>/<model_slug>/<result_key>/artifacts/`
- `result_key` 默认由参数自动推导：优先取 `--category`，否则基于 `--suite` 推导（默认 `all`）
- `--execute-only` 会先写一个带 `grading_pending: true` 的 `summary.json`
- `--grade-only` 默认会回到同一个 `result_key` 对应目录下，自动找到 `artifacts/` 并覆盖写回最终版 `summary.json`
- 只有在你想手动指定其他归档目录时，才需要额外传 `--artifacts-dir`

例如：

```bash
# foundation 会落到 results/formal/<model_slug>/foundation/
uv run scripts/friday_benchmark.py \
  --model anthropic/claude-sonnet-4 \
  --category foundation \
  --grade-only

# 已迁移的旧 PinchBench 27 任务如果放在 pinchbench/ 下，可这样重算
uv run scripts/benchmark.py \
  --model anthropic/claude-sonnet-4 \
  --category pinchbench \
  --grade-only
```

### 按场景分类跑

```bash
# 基础能力层（15 个任务）
uv run scripts/friday_benchmark.py \
  --model anthropic/claude-sonnet-4 \
  --category foundation

# 高级秘书（11 个任务）
uv run scripts/friday_benchmark.py \
  --model anthropic/claude-sonnet-4 \
  --category secretary

# AI 程序员（12 个任务）
uv run scripts/friday_benchmark.py \
  --model anthropic/claude-sonnet-4 \
  --category programmer

# 全域运营（13 个任务）
uv run scripts/friday_benchmark.py \
  --model anthropic/claude-sonnet-4 \
  --category operator

# 金融伙伴（9 个任务）
uv run scripts/friday_benchmark.py \
  --model anthropic/claude-sonnet-4 \
  --category finance

# 数字分身（10 个任务）
uv run scripts/friday_benchmark.py \
  --model anthropic/claude-sonnet-4 \
  --category digital_twin
```

### 跑单个任务

```bash
uv run scripts/friday_benchmark.py \
  --model anthropic/claude-sonnet-4 \
  --suite task_f_01_web_search
```

### 使用自定义 API 端点

```bash
uv run scripts/friday_benchmark.py \
  --model your-model-id \
  --base-url https://your-api.com/v1 \
  --api-key sk-xxx
```

### 启用 LLM Judge

hybrid 和 llm_judge 类型的任务需要 Judge 模型才能获得完整评分：

```bash
uv run scripts/friday_benchmark.py \
  --model anthropic/claude-sonnet-4 \
  --judge openai/gpt-4o
```

不传 `--judge` 时，hybrid 任务只跑 automated 部分。

默认不会自动上传排行榜；只有显式传入 `--auto-upload` 才会上传，因此通常不需要再写 `--no-upload`。

## 场景任务一览

| `--category` | 任务数 | 说明 | 评分类型 |
|--------------|--------|------|----------|
| `foundation` | 15 | Web 搜索、图片理解、PDF 解析、文件读写、工具链… | 全部 automated |
| `secretary` | 11 | 信息提取、消息优先级、日历管理、邮件搜索… | automated + hybrid |
| `programmer` | 12 | 脚本生成、Bug 修复、代码 Review、API 设计… | automated + hybrid |
| `operator` | 13 | 热点调研、内容改写、视频脚本、数据洞察… | 全部 hybrid |
| `finance` | 9 | 股票报价、研报摘要、账单分类、预算规划… | automated + hybrid |
| `digital_twin` | 10 | 人设构建、风格提取、代我回复、一致性检验… | 全部 hybrid |
| `pinchbench` | 27 | 原始 PinchBench 任务集 | mixed |
| 不传 | 97 | 以上全部 + PinchBench 原始 27 个 | 混合 |

## 评分机制

### 三种评分类型

- **automated**: 任务 markdown 中内嵌 Python `grade()` 函数，检查 workspace 输出文件
- **llm_judge**: 用 LLM（默认 claude-opus-4.5）对输出做质量评估
- **hybrid**: 两者加权组合，权重在任务 frontmatter 中配置（如 `automated: 0.7, llm_judge: 0.3`）

### 评分流程

```
OpenClaw 执行任务
  → 输出写入 workspace（agent 直接写文件）
  → grade() 函数检查 workspace 文件 → automated 分数
  → LLM Judge 评估输出质量 → llm_judge 分数（可选）
  → 加权合并 → 最终 0.0~1.0 分数
```

## 结果输出

```bash
# 结果 JSON 在 results/ 目录
ls results/

# 格式示例
{
  "model": "anthropic/claude-sonnet-4",
  "result_key": "foundation",
  "category": "foundation",
  "tasks": [
    {
      "task_id": "task_f_01_web_search",
      "status": "success",
      "grading": {
        "mean": 0.75,
        "runs": [{"score": 0.75, "breakdown": {"file_created": 1.0, ...}}]
      }
    }
  ]
}
```

对于两阶段模式，同一模型 + result_key 目录下会出现：

```bash
results/formal/<model_slug>/<result_key>/
├── summary.json
├── transcripts/
└── artifacts/
    ├── execution_manifest.json
    └── task_xx/
        └── run_1/
            ├── execution_result.json
            └── workspace/
```

说明：

- 默认单阶段模式也会写入同一个 `result_key` 目录，并保留 `artifacts/`
- `summary.json` 中的 `workspace` 字段仍保持原有风格，不会改成 artifact 路径
- 评分阶段实际读取的是 `artifacts/.../workspace/`
- viewer 会把不同 `result_key`（如 `pinchbench`、`foundation`）作为独立结果项展示

## 全部 CLI 参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--model` | 必填 | 模型 ID（如 `anthropic/claude-sonnet-4`） |
| `--category` | 无（跑全部） | 场景过滤：pinchbench / foundation / secretary / programmer / operator / finance / digital_twin |
| `--suite` | `all` | 任务过滤：`all` / `automated-only` / 逗号分隔的 task_id |
| `--base-url` | 无 | 自定义 API 端点（跳过 OpenRouter 验证） |
| `--api-key` | `$OPENAI_API_KEY` | 自定义端点的 API Key |
| `--judge` | 无 | LLM Judge 模型（如 `openai/gpt-4o`） |
| `--runs` | 1 | 每个任务执行次数（取平均） |
| `--timeout-multiplier` | 1.0 | 超时倍率 |
| `--output-dir` | `results` | 结果输出目录 |
| `--execute-only` | 关 | 只执行任务并归档评分依赖文件，不做最终评分 |
| `--grade-only` | 关 | 只基于已归档 artifacts 评分，不重新执行任务 |
| `--artifacts-dir` | 自动推导 | 自定义 artifacts 目录；默认在对应 `results/.../artifacts/` 下 |
| `--verbose` / `-v` | 关 | 详细日志 |
| `--auto-upload` | 关 | 评测完成后自动上传排行榜 |
| `--no-upload` | 兼容保留 | 旧参数；现在默认就不会上传 |
| `--no-fail-fast` | 关 | sanity check 失败后继续跑 |

## 常见问题

### `openclaw` 命令找不到

确认 openclaw 在 PATH 中，或设置环境变量：

```bash
export OPENCLAW_PATH=/path/to/openclaw
```

### 模型验证失败

不走 OpenRouter 时，加 `--base-url` 跳过验证：

```bash
uv run scripts/friday_benchmark.py \
  --model direct/your-model \
  --base-url http://localhost:20001/v1
```

### 只想跑自动评分

不传 `--judge` 即可。hybrid 任务只计算 automated 部分的分数。

### 任务超时

默认超时由任务定义（60-300 秒不等）。用 `--timeout-multiplier 2` 翻倍所有超时。

### 如何重跑转换

如果 OpenFriday 源任务有更新，重新运行转换脚本：

```bash
python3 scripts/convert_friday_tasks.py \
  --friday-root /path/to/openfriday-bench \
  --pinchbench-root /path/to/pinchbench-skill
```
