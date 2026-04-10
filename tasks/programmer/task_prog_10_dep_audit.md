---
id: task_prog_10_dep_audit
name: "依赖安全扫描 + 升级建议"
category: programmer
grading_type: automated
timeout_seconds: 120
workspace_files: []
dataset_dir: dataset/programmer/task_prog_10_dep_audit
---

## Prompt

工作区有一份 `requirements.txt`。

请：
1. 识别所有存在已知安全漏洞的依赖
2. 给出建议升级的版本
3. 将审计报告保存到 `audit_report.md`

## Expected Behavior

The agent should complete the task as described in the prompt.

Evaluation criteria:
（Golden answers 基于 dataset 中预埋的3个问题包）

- `file_created`：audit_report.md 存在
- `flask_vuln_found`：识别出旧版 Flask 的漏洞（「Flask」+「CVE」或「漏洞」或「升级」）
- `requests_vuln_found`：识别出旧版 requests 的问题（「requests」+「升级」或「CVE」）
- `pillow_vuln_found`：识别出旧版 Pillow 的漏洞（「Pillow」+「CVE」或「漏洞」）
- `has_upgrade_versions`：包含具体升级版本号（含 `>=` 或 `==` 后跟版本号）
- `has_severity`：包含严重程度描述（「高危」/「中危」/「Critical」/「High」/「Medium」）

## Grading Criteria

- [ ] （Golden answers 基于 dataset 中预埋的3个问题包）
- [ ] file_created: audit_report.md 存在
- [ ] flask_vuln_found: 识别出旧版 Flask 的漏洞（「Flask」+「CVE」或「漏洞」或「升级」）
- [ ] requests_vuln_found: 识别出旧版 requests 的问题（「requests」+「升级」或「CVE」）
- [ ] pillow_vuln_found: 识别出旧版 Pillow 的漏洞（「Pillow」+「CVE」或「漏洞」）
- [ ] has_upgrade_versions: 包含具体升级版本号（含 `>=` 或 `==` 后跟版本号）
- [ ] has_severity: 包含严重程度描述（「高危」/「中危」/「Critical」/「High」/「Medium」）

## Automated Checks

```python
def grade(transcript, workspace_path):
    from pathlib import Path
    workspace_path = Path(workspace_path)
    f = workspace_path / "audit_report.md"
    if not f.exists():
        return {k: 0.0 for k in ["file_created","flask_vuln_found","requests_vuln_found",
                                   "pillow_vuln_found","has_upgrade_versions","has_severity"]}
    import re
    c = f.read_text(encoding="utf-8")
    cl = c.lower()
    flask_ok    = "flask" in cl and any(w in cl for w in ["cve","漏洞","升级","vulnerability"])
    req_ok      = "requests" in cl and any(w in cl for w in ["cve","升级","vulnerability","ssrf"])
    pillow_ok   = "pillow" in cl and any(w in cl for w in ["cve","漏洞","升级","vulnerability"])
    ver_ok      = bool(re.search(r'[>=!]{1,2}\s*\d+\.\d+', c))
    sev_ok      = any(w in cl for w in ["高危","中危","低危","critical","high","medium","severity"])
    return {
        "file_created":        1.0,
        "flask_vuln_found":    1.0 if flask_ok else 0.0,
        "requests_vuln_found": 1.0 if req_ok else 0.0,
        "pillow_vuln_found":   1.0 if pillow_ok else 0.0,
        "has_upgrade_versions":1.0 if ver_ok else 0.0,
        "has_severity":        1.0 if sev_ok else 0.0,
    }
```
