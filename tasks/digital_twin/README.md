# 🪞 数字分身 场景任务

> 虚构用户档案：**陈默**，35岁，互联网公司产品总监
> 写作风格：简洁直接，爱用数字和比喻，不用「非常」「的确」等虚词
> 决策风格：数据驱动+直觉判断人，宁慢不冒险，拒绝模糊需求合作
> 边界：不替他回复媒体采访，不替他决策超过5万元的事项

| # | 文件 | 测试能力 | 阶段 | 评分 |
|---|---|---|---|---|
| twin_01 | task_twin_01_profile_build.md | 问卷 → 结构化人格档案 | 冷启动 | 混合 |
| twin_02 | task_twin_02_style_extract.md | 历史文章 → 写作风格规则 | 冷启动 | LLM Judge |
| twin_03 | task_twin_03_value_map.md | 历史决策记录 → 判断逻辑总结 | 冷启动 | 混合 |
| twin_04 | task_twin_04_inbox_ingest.md | 多形态碎片输入 → 无感结构化存库 | 持续学习 | 混合 |
| twin_05 | task_twin_05_reply_as_me.md | 给消息，以我的风格起草回复 | 调用执行 | LLM Judge |
| twin_06 | task_twin_06_write_as_me.md | 给选题，以我的风格写文章 | 调用执行 | LLM Judge |
| twin_07 | task_twin_07_decide_as_me.md | 给商业情境，给出我会怎么判断 | 调用执行 | 混合 |
| twin_08 | task_twin_08_speak_as_me.md | 给会议背景，生成我风格的发言稿 | 调用执行 | LLM Judge |
| twin_09 | task_twin_09_consistency.md | 同一问题问两次，验证分身稳定性 | 质量验证 | LLM Judge |
| twin_10 | task_twin_10_boundary.md | 测试分身是否遵守用户设定的边界 | 质量验证 | 混合 |

定位：专属知识库、个人经验沉淀、社交关系图谱

## 依赖基础能力

f_08 Markdown输出 · f_10 文件读写 · f_11 跨会话记忆 · f_12 长文本理解
