---
id: task_prog_01_script_gen
name: "自然语言 → Python 脚本生成（HTTP 请求 + 解析 + 错误处理）"
category: programmer
grading_type: automated
timeout_seconds: 360
workspace_files: []
dataset_dir: dataset/programmer/task_prog_01_script_gen
---

## Prompt

请在工作区创建一个 Python 脚本 `weather.py`，要求：

- 调用公开接口 `https://wttr.in/San_Francisco?format=j1`（或等价的 wttr.in 格式接口）
- 解析返回结果，提取并打印一段**可读的天气摘要**
- 有基本的异常处理（网络失败 / JSON 解析失败时给出友好提示）

## Expected Behavior

The agent should complete the task as described in the prompt.

Evaluation criteria:
- `file_created`：`weather.py` 是否存在  
- `valid_python`：是否为合法 Python 语法 
- `has_http_request`：是否包含 HTTP 请求代码（`requests`/`urllib` 等）  
- `references_location`：是否包含 San Francisco 相关字样  
- `has_error_handling`：是否包含 try/except 等异常处理  
- `has_output`：是否有 `print(...)` 等输出  
- `executable_structure`：是否有函数或 `if __name__ == "__main__"` 结构（简单脚本可给部分分）

## Grading Criteria

- [ ] file_created: `weather.py` 是否存在
- [ ] valid_python: 是否为合法 Python 语法
- [ ] has_http_request: 是否包含 HTTP 请求代码（`requests`/`urllib` 等）
- [ ] references_location: 是否包含 San Francisco 相关字样
- [ ] has_error_handling: 是否包含 try/except 等异常处理
- [ ] has_output: 是否有 `print(...)` 等输出
- [ ] executable_structure: 是否有函数或 `if __name__ == "__main__"` 结构（简单脚本可给部分分）

## Automated Checks

```python
def grade(transcript, workspace_path):
    from pathlib import Path
    workspace_path = Path(workspace_path)
    import ast
    import re

    f = workspace_path / "weather.py"
    if not f.exists():
        return {k: 0.0 for k in [
            "file_created",
            "valid_python",
            "has_http_request",
            "references_location",
            "has_error_handling",
            "has_output",
            "executable_structure",
        ]}

    content = f.read_text(encoding="utf-8", errors="ignore")

    scores = {"file_created": 1.0}

    try:
        ast.parse(content)
        scores["valid_python"] = 1.0
    except SyntaxError:
        scores["valid_python"] = 0.0
        scores["has_http_request"] = 0.0
        scores["references_location"] = 0.0
        scores["has_error_handling"] = 0.0
        scores["has_output"] = 0.0
        scores["executable_structure"] = 0.0
        return scores

    http_patterns = [
        r"import\s+requests",
        r"from\s+requests\s+import",
        r"requests\.get",
        r"import\s+urllib",
        r"from\s+urllib",
        r"urllib\.request",
        r"urlopen",
        r"https?://wttr\.in",
    ]
    scores["has_http_request"] = 1.0 if any(re.search(p, content, re.IGNORECASE) for p in http_patterns) else 0.0

    sf_patterns = [r"San\s*Francisco", r"San_Francisco", r"san\s*francisco"]
    scores["references_location"] = 1.0 if any(re.search(p, content, re.IGNORECASE) for p in sf_patterns) else 0.0

    err_patterns = [r"try\s*:", r"except\s+", r"Exception"]
    scores["has_error_handling"] = 1.0 if any(re.search(p, content) for p in err_patterns) else 0.0

    out_patterns = [r"print\s*\(", r"sys\.stdout"]
    scores["has_output"] = 1.0 if any(re.search(p, content) for p in out_patterns) else 0.0

    struct_patterns = [r"def\s+\w+\s*\(", r'if\s+__name__\s*==\s*[\'"]__main__[\'"]']
    if any(re.search(p, content) for p in struct_patterns):
        scores["executable_structure"] = 1.0
    else:
        scores["executable_structure"] = 0.5

    return scores
```
