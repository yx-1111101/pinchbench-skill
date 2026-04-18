---
id: task_ops_05_video_script
name: "视频脚本创作（口播向，带镜头指示）"
category: operator
grading_type: llm_judge
timeout_seconds: 150
workspace_files:
  - video_brief.txt
dataset_dir: dataset/operator/task_ops_05_video_script
---

## Prompt

工作区有一份视频选题 Brief `video_brief.txt`。

请根据 Brief 创作一份完整的视频脚本，保存到 `video_script.md`，要求：

- 视频时长：3-5分钟（口播字数约 600-1000 字）
- 格式：分段落，每段注明【旁白/口播】或简单的画面提示
- 开头 30 秒必须有强钩子，让观众不划走
- 给出 3-5 个具体可操作的建议（不是废话）
- 结尾引导互动（提问或行动号召）
- 语气符合 Brief 要求：干货向，直接，轻微毒舌但不说教

## Expected Behavior

The agent should complete the task as described in the prompt.

Evaluation criteria:
**自动**：
- `file_created`：video_script.md 存在
- `file_not_empty`：内容超过 400 字
- `has_hook`：前 200 字包含疑问句或感叹句（钩子）
- `has_tips`：包含数字编号的建议（"第一""1.""①"等）
- `has_cta`：结尾 100 字包含互动引导词（"评论""点赞""关注""告诉我"）

**LLM Judge**：钩子吸引力 · 建议是否具体可操作 · 风格是否符合 Brief · 整体节奏感

## Grading Criteria

- [ ] file_created: video_script.md 存在
- [ ] file_not_empty: 内容超过 400 字
- [ ] has_hook: 前 200 字包含疑问句或感叹句（钩子）
- [ ] has_tips: 包含数字编号的建议（"第一""1.""①"等）
- [ ] has_cta: 结尾 100 字包含互动引导词（"评论""点赞""关注""告诉我"）

## Automated Checks

```python
def grade(transcript, workspace_path):
    from pathlib import Path
    workspace_path = Path(workspace_path)
    import re
    f = workspace_path / "video_script.md"
    if not f.exists():
        return {k: 0.0 for k in ["file_created","file_not_empty","has_hook","has_tips","has_cta"]}
    content = f.read_text(encoding="utf-8").strip()
    opening = content[:200]
    ending  = content[-100:] if len(content) > 100 else content
    has_hook = bool(re.search(r'[？?！!]', opening))
    has_tips = bool(re.search(r'(?:第[一二三四五]|[1-5][\.、]|[①②③④⑤])', content))
    has_cta  = any(w in ending for w in ["评论","点赞","关注","告诉我","留言","分享","收藏"])
    return {
        "file_created":   1.0,
        "file_not_empty": 1.0 if len(content) > 400 else 0.0,
        "has_hook":       1.0 if has_hook else 0.0,
        "has_tips":       1.0 if has_tips else 0.0,
        "has_cta":        1.0 if has_cta else 0.0,
    }
```

## LLM Judge Rubric

### Quality Assessment

Evaluate the agent's output against the task requirements.

Dimensions: 钩子吸引力 · 建议是否具体可操作 · 风格是否符合 Brief · 整体节奏感钩子吸引力 · 建议是否具体可操作 · 风格是否符合 Brief · 整体节奏感

**Score 1.0**: Fully meets all requirements with high quality
**Score 0.75**: Meets most requirements with minor gaps
**Score 0.5**: Partially meets requirements
**Score 0.25**: Significant gaps or quality issues
**Score 0.0**: Does not address the task
