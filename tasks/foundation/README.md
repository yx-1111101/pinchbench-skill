# 🔩 Foundation 基础能力层

定位：原子能力探针，pass/fail，验证模型是否具备该能力（不评估答案正确性/事实命中，仅评估能力链路与产物是否达标）

建议先跑通基础层，再进入场景层。

## 📥 感知输入类

| # | 文件 | 测试能力 |
|---|---|---|
| f_01 | task_f_01_web_search.md | 联网搜索 → 能返回真实结果 |
| f_02 | task_f_02_image_understand.md | 图片识别 → 能描述图片内容 |
| f_03 | task_f_03_video_understand.md | 视频理解 → 能生成字幕或摘要 🔬 |
| f_04 | task_f_04_speech_to_text.md | 语音转文字 → 能准确转录音频 🔬 |
| f_05 | task_f_05_pdf_parse.md | PDF解析 → 能提取正文内容 |
| f_06 | task_f_06_table_read.md | 表格处理 → 能读懂CSV/Excel数据 |

## 📤 生成输出类

| # | 文件 | 测试能力 |
|---|---|---|
| f_07 | task_f_07_structured_output.md | 结构化输出 → 严格按JSON格式 |
| f_08 | task_f_08_markdown_output.md | Markdown输出 → 标题/表格/列表格式正确 |
| f_09 | task_f_09_realtime_voice.md | 实时语音对话 → 能维持多轮交互 🔬 |

## 🧠 记忆与状态类

| # | 文件 | 测试能力 |
|---|---|---|
| f_10 | task_f_10_file_rw.md | 文件读写 → 能在 workspace 创建/读取/修改 |
| f_11 | task_f_11_cross_session.md | 跨会话记忆 → 信息持久化，下次可取到 |
| f_12 | task_f_12_long_context.md | 长文本理解 → 超长上下文不丢关键信息 |

## ⚙️ 推理与协调类

| # | 文件 | 测试能力 |
|---|---|---|
| f_13 | task_f_13_tool_chain.md | 工具调用链 → 多步工具串联不断链 |
| f_14 | task_f_14_task_planning.md | 任务规划 → 模糊指令拆解为可执行步骤 |
| f_15 | task_f_15_doc_summary.md | 文本摘要 → 三段式要点总结 |

🔬 = 实验性，OpenClaw 中能力尚不稳定，占位备用
