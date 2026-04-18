# OpenFriday Bench

> 面向真实 C 端场景的 OpenClaw Agent 能力评测框架

## 架构

本 Bench 分为两层：

- **基础能力层 Foundation**：15 个原子能力探针，全部 pass/fail
- **场景任务层 Scenarios**：55 个端到端业务任务（秘书 11 + 程序员 12 + 运营 13 + 金融 9 + 数字分身 10）

## 评分原则

**Foundation 层**：测「格式/结构层面的正确」，不测「内容/答案层面的准确」。只要 Agent 调用了正确的工具、产出了正确的格式，就给分。

**场景层**：测端到端业务完成质量，内容准确性才纳入评分。

## 场景概览

| 层级   | 场景         | 文件夹              | 任务数 |
|--------|--------------|---------------------|--------|
| 基础层 | 🔩 Foundation | tasks/foundation/   | 15     |
| 场景层 | 🗓️ 高级秘书   | tasks/secretary/    | 11     |
| 场景层 | 💻 AI 程序员  | tasks/programmer/   | 12     |
| 场景层 | 📢 全域运营官 | tasks/operator/     | 13     |
| 场景层 | 📈 专属金融伙伴 | tasks/finance/    | 9      |
| 场景层 | 🪞 数字分身   | tasks/digital_twin/ | 10     |

合计：**70 个任务**

## 目录结构

```
openfriday-bench/
├── tasks/                         # 任务定义文件
│   ├── foundation/
│   ├── secretary/
│   ├── programmer/
│   ├── operator/
│   ├── finance/
│   └── digital_twin/
├── dataset/                       # 输入数据（只读，勿修改）
├── workspace/                     # 运行时自动创建，勿手动修改，已加入 .gitignore
├── bench_results/                 # 评测输出（自动生成）
├── configs_all_models_9.json      # 9 个模型的评测配置
└── scripts/
    └── openclaw_run.py            # 主评测脚本
```

## 运行方式

### 前置条件

```bash
pip install -r requirements.txt
```

### 环境变量

| 变量 | 必填 | 说明 |
|------|------|------|
| `OPENCLAW_GATEWAY` | 是 | Gateway WebSocket 地址，如 `ws://10.110.130.86:18789` |
| `OPENCLAW_TOKEN` | 是 | 认证 token |
| `MODELS_CONFIG` | 否 | 模型定价配置文件路径（用于 cost 计算） |
| `OPENAI_API_KEY` | 否 | LLM Judge API Key（未设 `JUDGE_API_KEY` 时使用） |
| `OPENAI_BASE_URL` | 否 | LLM Judge Base URL（未设 `JUDGE_BASE_URL` 时使用） |
| `JUDGE_API_KEY` | 否 | LLM Judge 专用 API Key（优先于 `OPENAI_API_KEY`） |
| `JUDGE_BASE_URL` | 否 | LLM Judge 专用 Base URL（优先于 `OPENAI_BASE_URL`） |

```bash
export OPENCLAW_GATEWAY=ws://localhost:18789
export OPENCLAW_TOKEN=63f2911f9be04c5577513b4e0cdf4d4733091dc9a54756d2
export MODELS_CONFIG=/usr/lib/openclaw/llm/config/models.json   # 可选，用于 cost 计算
export JUDGE_API_KEY="sk-zk2aec03b4e0ee57a4a0f46753fd96288ed69cf2ad65f397"
export JUDGE_BASE_URL=https://api.zhizengzeng.com/v1
```

### 跑全部任务（所有模型）

使用 `configs_all_models_9.json` 对全部分类跑 9 个模型：

```bash
python scripts/openclaw_run.py --config configs_all_models_9.json --category all --grade --judge-model gpt-5.4
```

`configs_all_models_9.json` 内容：

```json
{
  "models": [
    "direct/claude-opus-4-6",
    "direct/gemini-3.1-pro-preview",
    "direct/gpt-5.4",
    "direct/doubao-seed-2-0-pro-260215",
    "direct/kimi-k2.5",
    "direct/deepseek-v3.2",
    "direct/qwen3.5-plus",
    "direct/glm-5",
    "direct/minimax-m2.5"
  ]
}
```

### 加 LLM Judge

```bash
export OPENAI_API_KEY=sk-...
python scripts/openclaw_run.py --config configs_all_models_9.json --category all \
  --grade --judge-model gpt-5.4
```

### 其他常用命令

```bash
# 单个模型跑全部分类
python scripts/openclaw_run.py --model direct/qwen3.5-plus --category all --grade

# 单个模型跑单个分类
python scripts/openclaw_run.py --model direct/qwen3.5-plus --category foundation --grade

# 单个任务
python scripts/openclaw_run.py --model direct/qwen3.5-plus --task task_f_01_web_search
```

## 输出结构

```
bench_results/
  <model_slug>/
    <category>/
      <task_name>/
        workspace/           # Agent 工作区（输入/输出文件）
        results/
          run_<ts>.json     # 评分 & 用量结果

  summary_<ts>.json         # 本次运行全部模型汇总
```

汇总示例：

```
============================================================
模型对比汇总
============================================================
  direct/qwen3.5-plus: 4/5 (80%)  score=0.82  time=210s  calls=38  tokens=95000  cost=CNY 0.1234
    [OK  ] task_f_01_web_search  score=0.90  time=32s
    [FAIL] task_f_03_file_write              time=55s
```

## 命名约定

任务 ID 是整个系统的唯一标识，三处必须严格一致：

| 位置           | 格式                        | 示例                                      |
|----------------|-----------------------------|-------------------------------------------|
| 任务定义文件   | tasks/{场景}/{task_id}.md   | tasks/foundation/task_f_01_web_search.md  |
| 数据集文件夹   | dataset/{场景}/{task_id}/   | dataset/foundation/task_f_01_web_search/  |
| 运行时 workspace | workspace/{task_id}/     | workspace/task_f_01_web_search/            |

**不允许例外**。task_id 去掉 .md 后缀即为 dataset 文件夹名。

示例：`task_f_09_dialog_logging` 对应 `tasks/foundation/task_f_09_dialog_logging.md` 与 `dataset/foundation/task_f_09_dialog_logging/`。

## 运行时数据流

```
dataset/{场景}/{task_id}/          只读，原始输入数据
        ↓  benchmark 启动时复制
workspace/{task_id}/               运行时沙盒，Agent 的工作台
        ↓  Agent 读输入、写输出
评分脚本检查 workspace/ 里的输出文件
        ↓
results.json
```

workspace 是 Agent 的「沙盒工作台」：每次跑任务前由 benchmark 自动创建并初始化，任务结束后可清理。dataset 是「只读档案室」，永远不会被污染。

## 前置条件说明

部分任务依赖真实渠道或账号，未满足前置条件的任务会被自动跳过（标注 `skipped: prerequisites_not_met`），不计入总分。

| 前置条件类型 | 涉及任务 | 说明 |
|---|---|---|
| 无（开箱即跑） | Foundation f_02~f_12, f_14~f_15；秘书 sec_01~02, sec_06~08；程序员全部；运营 ops_02~11；金融 fin_02~03, fin_05~09；数字分身全部 | 使用本地 mock / dataset 数据，无需外部服务 |
| 联网搜索 / 实时数据 | f_01, f_13, fin_01, fin_04, ops_01, ops_12, ops_13, sec_10 | 需 web_search 工具或等效联网能力 |
| 飞书日历 API | sec_03, sec_04 | 需真实接入飞书日历，仅写本地文件不给分 |
| 飞书 / IM 渠道（消息推送） | sec_05, sec_10, sec_11 | 需已接入飞书或企微等 IM 渠道 |
| 浏览器操作 | sec_09 | 需启用 browser tool 并能访问公开网页 |
| 定时任务（cron） | sec_10, sec_11 | 需 cron/crontab 或等效调度能力 |

## 外部依赖任务清单

为方便批量跑分前检查环境，下面按依赖类型列出所有需要额外外部能力的任务。**共 13 个任务涉及外部依赖**（部分任务同时依赖多项能力），其余 57 个任务可在纯离线环境下运行。

### 🔍 需要联网搜索 / 获取实时在线信息（8 个）

| 任务 ID | 任务名 | 联网用途 | 备注 |
|---------|--------|---------|------|
| `task_f_01_web_search` | 基础 · 网络搜索 | 搜索英伟达（NVDA）今日股价 | 评分脚本会实时拉取参考收盘价做价格容差校验 |
| `task_f_13_tool_chain` | 基础 · 多工具串联 | 搜索特斯拉 Model 3 2026 款价格 | 需联网获取价格信号，与本地预算文件结合判断 |
| `task_fin_01_stock_quote` | 金融 · 实时行情 | 查询腾讯/阿里/英伟达三支股票今日行情 | 需实时股票数据源 |
| `task_fin_04_daily_brief` | 金融 · 每日简报 | 联网收集 A 股/港股/美股指数 + 财经新闻 | 结果需包含当日指数信息 |
| `task_ops_01_hotspot_research` | 运营 · 热点选题 | 联网搜索**今天**科技/数码领域热点 | 需当日时效性信息 |
| `task_ops_12_competitor_monitor` | 运营 · 竞品监控 | 联网调研索尼/漫步者在小红书/抖音的近期内容 | 需搜索真实平台内容表现 |
| `task_ops_13_crisis_pr` | 运营 · 危机公关 | 联网搜索品牌近 30 天负面舆情 | 搜索不到负面信息时可用「低风险」结论 |
| `task_sec_10_daily_digest` | 秘书 · 定时摘要 | 搜索今日行业资讯 | 同时依赖飞书推送 + cron |

### 📅 需要接通飞书日历（2 个）

| 任务 ID | 任务名 | 飞书日历用途 | 备注 |
|---------|--------|-------------|------|
| `task_sec_03_calendar_create` | 秘书 · 飞书日程创建 | 在飞书日历中创建会议日程 | **任务文件显式声明前置条件**：需真实调用飞书日历 API，仅写本地文件不给分 |
| `task_sec_04_conflict_manage` | 秘书 · 飞书日程冲突处理 | 查询飞书日历占用 → 自动避让创建 | **任务文件显式声明前置条件**：需真实调用飞书日历完成查询与创建 |

### 💬 需要飞书 / IM 渠道消息推送（3 个）

| 任务 ID | 任务名 | IM 渠道用途 | 备注 |
|---------|--------|-----------|------|
| `task_sec_05_notify_push` | 秘书 · 通知推送 | 通过飞书向用户发送会议提醒消息 | 评分检查结果中是否包含「已发送」+「飞书」 |
| `task_sec_10_daily_digest` | 秘书 · 定时摘要推送 | 通过飞书推送每日信息汇总 | 同时依赖联网搜索 + cron |
| `task_sec_11_anomaly_alert` | 秘书 · 异常监控告警 | 监控「开心项目」飞书群 + 通过 IM 发送告警 | 同时依赖 cron/调度能力 |

### 🌐 需要浏览器操作（1 个）

| 任务 ID | 任务名 | 浏览器用途 | 备注 |
|---------|--------|-----------|------|
| `task_sec_09_browser_op` | 秘书 · 浏览器操作 | 访问 apple.com，记录页面信息并截图 | 需可用的 browser tool；目标为公开网页，无需登录 |

### ⏰ 需要定时任务能力（2 个）

| 任务 ID | 任务名 | 定时任务用途 | 备注 |
|---------|--------|------------|------|
| `task_sec_10_daily_digest` | 秘书 · 定时摘要推送 | 设置每天早上 9:00 自动收集+推送 | 评分检查轨迹中是否出现 cron/crontab/launchd 配置行为 |
| `task_sec_11_anomaly_alert` | 秘书 · 异常监控告警 | 设置 24 小时无消息告警规则 | 需持续监控/定时检查能力 |

### 多依赖交叉一览

| 任务 ID | 联网 | 飞书日历 | 飞书/IM | 浏览器 | Cron |
|---------|:----:|:-------:|:------:|:-----:|:----:|
| task_f_01_web_search | ✅ | | | | |
| task_f_13_tool_chain | ✅ | | | | |
| task_fin_01_stock_quote | ✅ | | | | |
| task_fin_04_daily_brief | ✅ | | | | |
| task_ops_01_hotspot_research | ✅ | | | | |
| task_ops_12_competitor_monitor | ✅ | | | | |
| task_ops_13_crisis_pr | ✅ | | | | |
| task_sec_03_calendar_create | | ✅ | | | |
| task_sec_04_conflict_manage | | ✅ | | | |
| task_sec_05_notify_push | | | ✅ | | |
| task_sec_09_browser_op | | | | ✅ | |
| task_sec_10_daily_digest | ✅ | | ✅ | | ✅ |
| task_sec_11_anomaly_alert | | | ✅ | | ✅ |

说明：
- **联网搜索**：依赖 web_search 工具或等效联网能力。离线环境下 `task_f_01` 的 `price_matches_live_close` 指标会自动降级为 0（不影响其余指标），其他联网任务的信息时效性和准确性会下降。
- **飞书日历**：`sec_03` 和 `sec_04` 在任务文件中**显式声明了前置条件**，要求真实调用飞书日历 API；仅写本地结果文件但未实际创建日程的不给分。
- **飞书/IM 渠道**：需在运行环境中接通飞书或企微等 IM 渠道，使 Agent 能真实发送消息。
- **浏览器操作**：需可用的 browser tool 或等效网页自动化能力。`sec_09` 目标为公开网页（apple.com），无需登录。
- **定时任务**：需 cron/crontab 或等效调度能力。评分脚本检查执行轨迹中是否出现定时任务配置行为。
- **无外部依赖的任务（57 个）** 可在纯离线环境下运行，使用 workspace 中的本地 dataset 文件完成全部评测。
