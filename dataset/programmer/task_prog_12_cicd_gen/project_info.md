# 项目信息 - CI/CD 配置用

## 技术栈
- 语言：Python 3.11
- Web 框架：Flask
- 测试：pytest（测试文件在 tests/ 目录下）
- 容器化：Docker（Dockerfile 已存在于项目根目录）
- 代码仓库：GitHub

## 部署需求
- 目标分支：main
- 触发条件：向 main 分支 push，或创建 PR
- CI 步骤：
  1. 检出代码
  2. 设置 Python 3.11 环境
  3. 安装依赖（`pip install -r requirements.txt`）
  4. 运行测试（`pytest tests/ -v`）
  5. 构建 Docker 镜像（`docker build -t myapp:latest .`）
- 环境变量：
  - `DATABASE_URL`：从 GitHub Secrets 注入（secret 名称：DATABASE_URL）
  - `FLASK_ENV`：固定为 `production`

## 注意
- 测试失败时不应继续构建 Docker 镜像
- Python 版本必须严格为 3.11
