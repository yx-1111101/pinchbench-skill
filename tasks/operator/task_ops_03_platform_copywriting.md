---
id: task_ops_03_platform_copywriting
name: "多平台风格文案（同一产品，输出三平台版本）"
category: operator
grading_type: llm_judge
timeout_seconds: 150
workspace_files: []
dataset_dir: dataset/operator/task_ops_03_platform_copywriting
---

## Prompt

工作区有一份产品发布公告 `press_release.txt`。

请输出三个平台的发布文案，分别保存：

1. **小红书版** `xhs_post.md`：
   - 字数 200-300 字，emoji 丰富，口语化，3-5个话题标签
   - 有明确的"使用场景"描述（帮读者代入）
   - 结尾引导互动

2. **微博版** `weibo_post.txt`：
   - 字数 140 字以内（微博限制）
   - 精炼有力，突出一个核心卖点
   - 可带 @和话题，但不超过 2 个

3. **公众号推文开头** `wechat_intro.md`：
   - 字数 150-250 字
   - 作为推文第一段，要能勾住读者读完全文
   - 可以用提问、故事、反常识开头

## Expected Behavior

The agent should complete the task as described in the prompt.

Evaluation criteria:
**自动**：
- `xhs_created`、`weibo_created`、`wechat_created`：三个文件存在
- `xhs_has_emoji`：小红书版含 emoji
- `xhs_has_hashtag`：小红书版含话题标签
- `weibo_length_ok`：微博版字数 ≤ 180 字

**LLM Judge**：三版平台风格区分度 · 是否准确传达产品信息 · 各版是否符合平台用户语境

## Grading Criteria

- [ ] `xhs_created`、`weibo_created`、`wechat_created`：三个文件存在
- [ ] xhs_has_emoji: 小红书版含 emoji
- [ ] xhs_has_hashtag: 小红书版含话题标签
- [ ] weibo_length_ok: 微博版字数 ≤ 180 字

## Automated Checks

```python
def grade(transcript, workspace_path):
    from pathlib import Path
    workspace_path = Path(workspace_path)
    import re
    files = {
        "xhs":   workspace_path / "xhs_post.md",
        "weibo": workspace_path / "weibo_post.txt",
        "wechat":workspace_path / "wechat_intro.md",
    }
    xhs_c   = files["xhs"].read_text(encoding="utf-8").strip()   if files["xhs"].exists()   else ""
    weibo_c = files["weibo"].read_text(encoding="utf-8").strip() if files["weibo"].exists() else ""
    has_emoji   = bool(re.search(r'[\U0001F300-\U0001FFFF\U00002600-\U000027BF]', xhs_c))
    has_hashtag = "#" in xhs_c
    weibo_len   = len(weibo_c.replace(" ","").replace("\n",""))
    return {
        "xhs_created":    1.0 if files["xhs"].exists() else 0.0,
        "weibo_created":  1.0 if files["weibo"].exists() else 0.0,
        "wechat_created": 1.0 if files["wechat"].exists() else 0.0,
        "xhs_has_emoji":  1.0 if has_emoji else 0.0,
        "xhs_has_hashtag":1.0 if has_hashtag else 0.0,
        "weibo_length_ok":1.0 if weibo_len <= 180 else 0.0,
    }
```

## LLM Judge Rubric

### Quality Assessment

Evaluate the agent's output against the task requirements.

Dimensions: 三版平台风格区分度 · 是否准确传达产品信息 · 各版是否符合平台用户语境三版平台风格区分度 · 是否准确传达产品信息 · 各版是否符合平台用户语境

**Score 1.0**: Fully meets all requirements with high quality
**Score 0.75**: Meets most requirements with minor gaps
**Score 0.5**: Partially meets requirements
**Score 0.25**: Significant gaps or quality issues
**Score 0.0**: Does not address the task
