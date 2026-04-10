---
id: task_ops_02_content_rewrite
name: "内容二次加工（长文 → 短视频文案 → 朋友圈文案）"
category: operator
grading_type: llm_judge
timeout_seconds: 150
workspace_files: []
dataset_dir: dataset/operator/task_ops_02_content_rewrite
---

## Prompt

工作区有一篇深度行业长文 `long_article.txt`，请将其改写为两个版本：

1. **短视频口播文案** `video_script.txt`：
   - 时长：60-90秒口播，约 200-300 字
   - 开头 10 字必须能抓住注意力
   - 结尾要有行动号召（点赞/关注/评论）
   - 语气口语化，可以用"你知道吗""说真的"等连接词

2. **朋友圈文案** `moments_post.txt`：
   - 字数：150 字以内
   - 有个人视角和情绪（不是纯转述）
   - 可以用 emoji，结尾可以提问引导评论
   - 3-5 个话题标签

## Expected Behavior

The agent should complete the task as described in the prompt.

Evaluation criteria:
**自动**：
- `video_created`：video_script.txt 存在
- `moments_created`：moments_post.txt 存在
- `video_length_ok`：视频文案字数在 150-400 字之间
- `moments_length_ok`：朋友圈文案字数在 50-200 字之间
- `moments_has_hashtag`：朋友圈文案包含 # 话题标签
- `moments_has_emoji`：朋友圈文案包含 emoji

**LLM Judge**：改写是否忠于原文核心观点 · 钩子是否有吸引力 · 朋友圈是否有个人温度 · 两版风格区分度

## Grading Criteria

- [ ] video_created: video_script.txt 存在
- [ ] moments_created: moments_post.txt 存在
- [ ] video_length_ok: 视频文案字数在 150-400 字之间
- [ ] moments_length_ok: 朋友圈文案字数在 50-200 字之间
- [ ] moments_has_hashtag: 朋友圈文案包含 # 话题标签
- [ ] moments_has_emoji: 朋友圈文案包含 emoji

## Automated Checks

```python
def grade(transcript, workspace_path):
    from pathlib import Path
    workspace_path = Path(workspace_path)
    import re
    vf = workspace_path / "video_script.txt"
    mf = workspace_path / "moments_post.txt"
    v_exists = vf.exists()
    m_exists = mf.exists()
    v_content = vf.read_text(encoding="utf-8").strip() if v_exists else ""
    m_content = mf.read_text(encoding="utf-8").strip() if m_exists else ""
    v_len = len(v_content.replace(" ","").replace("\n",""))
    m_len = len(m_content.replace(" ","").replace("\n",""))
    has_hashtag = "#" in m_content
    has_emoji = bool(re.search(r'[\U0001F300-\U0001FFFF\U00002600-\U000027BF]', m_content))
    return {
        "video_created":      1.0 if v_exists else 0.0,
        "moments_created":    1.0 if m_exists else 0.0,
        "video_length_ok":    1.0 if 150 <= v_len <= 400 else 0.0,
        "moments_length_ok":  1.0 if 50 <= m_len <= 200 else 0.0,
        "moments_has_hashtag":1.0 if has_hashtag else 0.0,
        "moments_has_emoji":  1.0 if has_emoji else 0.0,
    }
```

## LLM Judge Rubric

### Quality Assessment

Evaluate the agent's output against the task requirements.

Dimensions (from task spec): LLM Judge**：改写是否忠于原文核心观点 · 钩子是否有吸引力 · 朋友圈是否有个人温度 · 两版风格区分度

**Score 1.0**: Fully meets all requirements with high quality
**Score 0.75**: Meets most requirements with minor gaps
**Score 0.5**: Partially meets requirements
**Score 0.25**: Significant gaps or quality issues
**Score 0.0**: Does not address the task
