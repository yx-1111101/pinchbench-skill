# 🗓️ 高级秘书 场景任务

定位：7×24 全栈 AI 秘书，接管日程、消息、文档、主动情报

## 依赖基础能力

f_01 联网搜索 · f_05 PDF解析 · f_06 表格处理 · f_07 结构化输出 · f_08 Markdown输出 · f_10 文件读写

## 前置条件说明

| 任务 | 前置条件 |
|---|---|
| sec_01 ~ sec_02 · sec_06 ~ sec_08 | 无，开箱即跑 |
| sec_03 · sec_04 | ✅ **飞书日历**（推荐；亦兼容已接入的其它日历源） |
| sec_05 | ✅ 任意已接入 IM 渠道（飞书/企微） |
| sec_07（真实版） | ✅ 真实邮箱接入 |
| sec_09 | ✅ OpenClaw browser 已启用 + 飞书 web 已登录 |
| sec_10 · sec_11 | ✅ 任意已接入 IM 渠道 + cron 已启用 |

## 任务列表

| # | 文件 | 测试能力 | 前置 | 评分 |
|---|---|---|---|---|
| sec_01 | task_sec_01_info_extract.md | 内容关键信息提取 | 无 | 自动 |
| sec_02 | task_sec_02_msg_priority.md | 消息优先级分类 | 无 | 混合 |
| sec_03 | task_sec_03_calendar_create.md | 飞书日程创建 | ✅ 飞书日历 | 自动 |
| sec_04 | task_sec_04_conflict_manage.md | 飞书日程冲突处理（自动避让创建） | ✅ 飞书日历 | 自动 |
| sec_05 | task_sec_05_notify_push.md | 通知主动推送 | ✅ IM | 自动 |
| sec_06 | task_sec_06_doc_generation.md | 结构化文档生成 | 无 | 混合 |
| sec_07 | task_sec_07_email_search.md | 邮件检索 | ✅ 邮箱 | 混合 |
| sec_08 | task_sec_08_office_pipeline.md | 办公软件应用 | 无 | 混合 |
| sec_09 | task_sec_09_browser_op.md | 浏览器操作 | ✅ browser | 自动 |
| sec_10 | task_sec_10_daily_digest.md | 主动情报·定时摘要 | ✅ IM+cron | 自动 |
| sec_11 | task_sec_11_anomaly_alert.md | 主动情报·异常监控 | ✅ IM+cron | 自动 |

