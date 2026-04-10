# 任务管理系统 PRD（API 设计用）

## 产品概述
一个团队协作的任务管理工具，用户可以创建项目、在项目下管理任务、为任务分配成员。

## 核心实体
- **User**：id, username, email, created_at
- **Project**：id, name, description, owner_id, created_at
- **Task**：id, project_id, title, description, assignee_id, status(todo/in_progress/done), priority(low/medium/high), due_date, created_at

## 功能需求

### 任务相关（核心）
1. 创建任务（POST）：指定项目、标题、描述、负责人、优先级、截止日期
2. 获取任务详情（GET）：按 task_id
3. 更新任务（PATCH）：可更新标题、状态、负责人、优先级
4. 删除任务（DELETE）：只有项目 owner 可删除
5. 列表查询（GET）：按项目ID过滤，支持 status / assignee_id / priority 筛选，分页（page + page_size）

### 用户相关
6. 用户登录（POST）：返回 Bearer Token
7. 获取当前用户信息（GET）：需鉴权

## 非功能需求
- 所有接口（除登录）均需 Bearer Token 鉴权
- 所有错误需返回统一 JSON 格式：`{"error": "message", "code": 400}`
- 支持 JSON 请求体，Content-Type: application/json
