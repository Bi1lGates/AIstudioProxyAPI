# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目简介

AI Studio Proxy API 是一个基于 Python 的代理服务器,将 Google AI Studio 网页界面转换为 OpenAI 兼容的 API。通过 Camoufox (反指纹检测的 Firefox) 和 Playwright 自动化提供稳定的 API 访问。

核心特性:
- OpenAI 兼容的 `/v1/chat/completions` 端点
- 三层流式响应机制: 流式代理 → Helper 服务 → Playwright 页面交互
- 脚本注入功能 v3.0: 使用 Playwright 原生网络拦截,支持油猴脚本动态挂载
- 现代化开发工具链: Poetry 依赖管理 + Pyright 类型检查

## 技术栈

- Python >= 3.9, < 4.0 (推荐 3.10+, Docker 使用 3.10)
- Poetry: 现代化依赖管理工具
- FastAPI: Web 框架
- Playwright: 浏览器自动化
- Camoufox: 反指纹检测浏览器
- Docker: 容器化部署 (支持 x86_64 和 ARM64)

## 项目架构

采用模块化架构,按功能领域划分:

```
api_utils/              # FastAPI 应用核心模块
├── app.py             # FastAPI 应用入口和生命周期
├── routers/           # API 路由 (按职责拆分)
├── request_processor.py # 请求处理核心逻辑
├── queue_worker.py    # 异步队列工作器
└── auth_utils.py      # API 密钥认证管理

browser_utils/          # 浏览器自动化模块
├── page_controller.py # 页面控制器和生命周期
├── model_management.py # AI Studio 模型管理
├── script_manager.py  # 脚本注入管理 (v3.0)
└── operations.py      # 浏览器操作封装

config/                 # 配置管理模块
├── settings.py        # 环境变量和主要设置
├── constants.py       # 系统常量定义
├── timeouts.py        # 超时配置
└── selectors.py       # CSS 选择器定义

models/                 # 数据模型定义
├── chat.py           # 聊天相关数据模型
├── exceptions.py     # 自定义异常类
└── logging.py        # 日志相关模型

stream/                 # 流式代理服务模块
└── main.py           # 流式代理服务入口

logging_utils/          # 日志管理模块
└── setup.py          # 日志系统配置

docker/                 # Docker 部署文件
├── Dockerfile        # 多阶段构建配置
├── docker-compose.yml # Docker Compose 配置
└── .env.docker       # Docker 环境配置模板
```

核心文件说明:
- server.py: 主服务器入口,导入并启动 FastAPI 应用
- launch_camoufox.py: 命令行启动脚本,负责启动浏览器和服务
- gui_launcher.py: 图形界面启动器
- llm.py: LLM 相关逻辑

## 配置管理

项目使用 .env 文件进行统一配置管理:

1. 复制配置模板:
   ```bash
   cp .env.example .env
   ```

2. 编辑配置文件:
   ```bash
   nano .env
   ```

3. 主要配置项:
   - PORT, DEFAULT_FASTAPI_PORT: FastAPI 服务端口 (默认 2048)
   - STREAM_PORT: 流式代理服务端口 (默认 3120)
   - HTTP_PROXY, HTTPS_PROXY, UNIFIED_PROXY_CONFIG: 代理设置
   - SERVER_LOG_LEVEL: 日志级别 (DEBUG/INFO/WARNING/ERROR)
   - DEBUG_LOGS_ENABLED, TRACE_LOGS_ENABLED: 详细日志开关
   - AUTO_CONFIRM_LOGIN: 自动确认登录
   - ENABLE_SCRIPT_INJECTION: 启用脚本注入功能
   - USERSCRIPT_PATH: 油猴脚本路径

配置优先级: 命令行参数 > 环境变量 > .env 文件 > 默认值

## 开发环境设置

### 依赖安装

使用 Poetry 管理依赖:

```bash
# 安装 Poetry
curl -sSL https://install.python-poetry.org | python3 -

# 安装项目依赖
poetry install

# 激活虚拟环境
poetry shell

# 或直接运行命令
poetry run python server.py
```

### 开发依赖

```bash
# 安装开发依赖 (包含类型检查、测试工具)
poetry install --with dev

# 类型检查 (需要 npm install -g pyright)
pyright

# 查看依赖树
poetry show --tree

# 更新依赖
poetry update
```

## 常用命令

### 本地开发

```bash
# 图形界面启动 (推荐新手)
python gui_launcher.py

# 命令行启动 (日常使用)
python launch_camoufox.py --headless

# 调试模式 (首次设置或故障排除)
python launch_camoufox.py --debug

# 直接运行服务器 (不推荐,仅测试用)
python server.py
```

### Docker 部署

所有 Docker 文件位于 docker/ 目录:

```bash
# 进入 docker 目录
cd docker

# 准备配置文件
cp .env.docker .env
nano .env

# 使用 Docker Compose
docker compose build          # 构建镜像
docker compose up -d          # 启动服务
docker compose logs -f        # 查看日志
docker compose ps             # 查看状态
docker compose down           # 停止服务
docker compose restart        # 重启服务

# 进入容器
docker compose exec ai-studio-proxy /bin/bash

# 版本更新
bash update.sh
```

### 测试

```bash
# 文本对话测试
python test_text_only.py

# 文本和图片测试
python test_text_and_images.py

# PDF 和图片测试
python test_pdf_and_images.py
```

### 其他工具

```bash
# 更新 Browserforge 数据
python update_browserforge_data.py

# 获取 Camoufox 数据
python fetch_camoufox_data.py

# 修补 Camoufox 代理
python patch_camoufox_proxy.py
```

## 重要注意事项

### 认证文件管理

- 首次运行需要在调试模式下获取认证文件
- 认证文件存储在 auth_profiles/active/ 目录
- Docker 部署需要预先在主机上获取认证文件并挂载到容器

### 三层响应获取机制

响应获取优先级:
1. 集成流式代理服务 (Stream Proxy) - 默认启用,端口 3120,最佳性能
2. 外部 Helper 服务 - 可选配置,需要有效认证文件
3. Playwright 页面交互 - 最终后备方案,支持所有参数

### 脚本注入功能 (v3.0)

- 使用 Playwright 原生网络拦截,100% 可靠性
- 直接从油猴脚本解析模型数据,无需配置文件
- 默认脚本路径: browser_utils/more_modles.js
- 通过 ENABLE_SCRIPT_INJECTION=true 启用

### 客户端管理历史

代理服务器不支持在 AI Studio 界面中编辑历史消息。客户端负责维护完整的聊天记录并发送给代理。

### 模块化设计

- 遵循单一职责原则,避免循环依赖
- 配置统一在 config/ 模块管理
- 异步优先,全面采用 async/await
- 通过 dependencies.py 管理组件依赖关系

## 重要文件路径

- 配置: .env, .env.example, config/
- 认证: auth_profiles/active/, auth_profiles/saved/
- API 密钥: auth_profiles/key.txt
- 日志: logs/
- 错误快照: errors_py/, screenshots/
- 证书: certs/
- 文档: docs/
- Docker: docker/

## 调试技巧

1. 启用详细日志:
   ```env
   SERVER_LOG_LEVEL=DEBUG
   DEBUG_LOGS_ENABLED=true
   TRACE_LOGS_ENABLED=true
   ```

2. 使用调试模式启动:
   ```bash
   python launch_camoufox.py --debug
   ```

3. 查看实时日志:
   - 本地: 终端输出或 logs/ 目录
   - Docker: `docker compose logs -f`

4. 检查页面错误:
   - 错误截图保存在 errors_py/
   - 操作截图保存在 screenshots/

## 相关文档

详细文档位于 docs/ 目录:
- installation-guide.md: 安装指南
- environment-configuration.md: 环境变量配置指南
- authentication-setup.md: 认证设置指南
- daily-usage.md: 日常运行指南
- api-usage.md: API 使用指南
- webui-guide.md: Web UI 使用指南
- script_injection_guide.md: 脚本注入指南 (v3.0)
- streaming-modes.md: 流式处理模式详解
- architecture-guide.md: 项目架构指南
- development-guide.md: 开发者指南
- troubleshooting.md: 故障排除指南

Docker 相关文档:
- docker/README.md: Docker 快速指南
- docker/README-Docker.md: Docker 详细部署指南
- docker/SCRIPT_INJECTION_DOCKER.md: Docker 环境脚本注入配置
