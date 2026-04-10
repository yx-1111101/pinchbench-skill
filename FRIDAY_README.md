# Friday Benchmark — OpenFriday 评测集成指南

基于 PinchBench 框架，集成了 OpenFriday 的 70 个真实 C 端场景评测任务。

## 架构

```
pinchbench-skill/
├── scripts/
│   ├── benchmark.py              # PinchBench 原始入口（未修改）
│   ├── friday_benchmark.py       # Friday 评测入口（新增）
│   ├── friday_adapter.py         # 适配层：扩展任务加载 + workspace 处理（新增）
│   ├── convert_friday_tasks.py   # 任务格式转换工具（新增）
│   ├── lib_agent.py              # PinchBench OpenClaw 执行引擎（未修改）
│   ├── lib_grading.py            # PinchBench 评分引擎（未修改）
│   └── lib_tasks.py              # PinchBench 任务加载（未修改）
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

```
friday_benchmark.py
  │
  ├── 使用 FridayTaskLoader（递归扫描子目录）
  │
  ├── monkey-patch prepare_task_workspace
  │   添加 dataset_dir 批量拷贝支持
  │
  └── 复用 PinchBench 全部基础设施：
      ├── openclaw CLI 调用 (openclaw agent --message ...)
      ├── 评分引擎 (automated / llm_judge / hybrid)
      ├── 日志 (benchmark.log + stdout)
      ├── 结果 JSON (results/ 目录)
      └── 排行榜上传
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
  --model anthropic/claude-sonnet-4 \
  --no-upload

# 跑原始 PinchBench 27 个任务（不变）
uv run scripts/benchmark.py \
  --model anthropic/claude-sonnet-4
```

### 按场景分类跑

```bash
# 基础能力层（15 个任务）
uv run scripts/friday_benchmark.py \
  --model anthropic/claude-sonnet-4 \
  --category foundation \
  --no-upload

# 高级秘书（11 个任务）
uv run scripts/friday_benchmark.py \
  --model anthropic/claude-sonnet-4 \
  --category secretary \
  --no-upload

# AI 程序员（12 个任务）
uv run scripts/friday_benchmark.py \
  --model anthropic/claude-sonnet-4 \
  --category programmer \
  --no-upload

# 全域运营（13 个任务）
uv run scripts/friday_benchmark.py \
  --model anthropic/claude-sonnet-4 \
  --category operator \
  --no-upload

# 金融伙伴（9 个任务）
uv run scripts/friday_benchmark.py \
  --model anthropic/claude-sonnet-4 \
  --category finance \
  --no-upload

# 数字分身（10 个任务）
uv run scripts/friday_benchmark.py \
  --model anthropic/claude-sonnet-4 \
  --category digital_twin \
  --no-upload
```

### 跑单个任务

```bash
uv run scripts/friday_benchmark.py \
  --model anthropic/claude-sonnet-4 \
  --suite task_f_01_web_search \
  --no-upload
```

### 使用自定义 API 端点

```bash
uv run scripts/friday_benchmark.py \
  --model your-model-id \
  --base-url https://your-api.com/v1 \
  --api-key sk-xxx \
  --no-upload
```

### 启用 LLM Judge

hybrid 和 llm_judge 类型的任务需要 Judge 模型才能获得完整评分：

```bash
uv run scripts/friday_benchmark.py \
  --model anthropic/claude-sonnet-4 \
  --judge openai/gpt-4o \
  --no-upload
```

不传 `--judge` 时，hybrid 任务只跑 automated 部分。

## 场景任务一览

| `--category` | 任务数 | 说明 | 评分类型 |
|--------------|--------|------|----------|
| `foundation` | 15 | Web 搜索、图片理解、PDF 解析、文件读写、工具链… | 全部 automated |
| `secretary` | 11 | 信息提取、消息优先级、日历管理、邮件搜索… | automated + hybrid |
| `programmer` | 12 | 脚本生成、Bug 修复、代码 Review、API 设计… | automated + hybrid |
| `operator` | 13 | 热点调研、内容改写、视频脚本、数据洞察… | 全部 hybrid |
| `finance` | 9 | 股票报价、研报摘要、账单分类、预算规划… | automated + hybrid |
| `digital_twin` | 10 | 人设构建、风格提取、代我回复、一致性检验… | 全部 hybrid |
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

## 全部 CLI 参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--model` | 必填 | 模型 ID（如 `anthropic/claude-sonnet-4`） |
| `--category` | 无（跑全部） | 场景过滤：foundation / secretary / programmer / operator / finance / digital_twin |
| `--suite` | `all` | 任务过滤：`all` / `automated-only` / 逗号分隔的 task_id |
| `--base-url` | 无 | 自定义 API 端点（跳过 OpenRouter 验证） |
| `--api-key` | `$OPENAI_API_KEY` | 自定义端点的 API Key |
| `--judge` | 无 | LLM Judge 模型（如 `openai/gpt-4o`） |
| `--runs` | 1 | 每个任务执行次数（取平均） |
| `--timeout-multiplier` | 1.0 | 超时倍率 |
| `--output-dir` | `results` | 结果输出目录 |
| `--verbose` / `-v` | 关 | 详细日志 |
| `--no-upload` | 关 | 跳过上传排行榜 |
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
  --base-url http://localhost:20001/v1 \
  --no-upload
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
