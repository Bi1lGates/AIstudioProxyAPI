# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

AI Studio Proxy API 是一个基于 Python 的代理服务器，将 Google AI Studio 的网页界面转换为 OpenAI 兼容的 API。通过 Camoufox（反指纹检测的 Firefox）和 Playwright 自动化，提供稳定的 API 访问。

## 系统架构

### 核心设计原则
- **模块化分离**: 按功能领域划分模块，避免循环依赖
- **单一职责**: 每个模块专注于特定的功能领域
- **配置统一**: 使用 `.env` 文件和 `config/` 模块统一管理配置
- **异步优先**: 全面采用异步编程模式，提升性能

### 模块结构
```
api_utils/              # FastAPI 应用核心模块
├── app.py             # FastAPI 应用入口和生命周期管理
├── routers/           # API 路由定义（按职责拆分）
├── request_processor.py # 请求处理核心逻辑
├── queue_worker.py    # 异步队列工作器
├── auth_utils.py      # API 密钥认证管理
└── dependencies.py    # FastAPI 依赖注入

browser_utils/         # 浏览器自动化模块
├── page_controller.py # 页面控制器和生命周期管理
├── model_management.py # AI Studio 模型管理
├── script_manager.py  # 脚本注入管理 (v3.0)
├── operations.py      # 浏览器操作封装
└── initialization.py  # 浏览器初始化逻辑

config/                # 配置管理模块
├── settings.py        # 主要设置和环境变量
├── constants.py       # 系统常量定义
├── timeouts.py        # 超时配置管理
└── selectors.py       # CSS 选择器定义

models/                # 数据模型定义
├── chat.py           # 聊天相关数据模型
├── exceptions.py     # 自定义异常类
└── logging.py        # 日志相关模型

stream/                # 流式代理服务模块
├── main.py           # 流式代理服务入口
├── proxy_server.py   # 代理服务器实现
└── interceptors.py   # 请求拦截器

logging_utils/         # 日志管理模块
└── setup.py          # 日志系统配置
```

## 开发环境

### 依赖管理
- **工具**: Poetry（现代化 Python 依赖管理）
- **Python**: >=3.9, <4.0（推荐 3.10+ 以获得最佳性能）
- **类型检查**: Pyright（可选，用于开发时类型检查）

### 常用命令

```bash
# 安装依赖
poetry install
poetry install --with dev  # 包含开发依赖

# 虚拟环境
poetry env activate
poetry run python script.py

# 依赖管理
poetry add package_name
poetry add --group dev package_name
poetry update

# 类型检查
pyright
pyright api_utils/app.py

# 代码格式化
poetry run black .
poetry run isort .
```

## 配置管理

### .env 文件配置
项目使用 `.env` 文件进行统一配置管理，避免硬编码参数。

```bash
# 复制配置模板
cp .env.example .env

# 编辑配置
nano .env
```

**配置优先级**（从高到低）：
1. 命令行参数（最高优先级）
2. `.env` 文件配置（推荐）
3. 系统环境变量
4. 默认值（代码中定义）

**重要配置项**：
- `PORT` / `DEFAULT_FASTAPI_PORT`: FastAPI 服务端口（默认 2048）
- `STREAM_PORT`: 流式代理服务端口（默认 3120，设置为 0 禁用）
- `UNIFIED_PROXY_CONFIG`: 统一代理配置
- `ENABLE_SCRIPT_INJECTION`: 是否启用油猴脚本注入功能
- `DEBUG_LOGS_ENABLED`: 是否启用调试日志

## 运行和调试

### 启动服务

```bash
# 图形界面启动（推荐新手）
python gui_launcher.py

# 命令行启动（日常使用）
python launch_camoufox.py --headless

# 调试模式（首次设置或故障排除）
python launch_camoufox.py --debug
```

### 首次认证设置
首次运行需要通过调试模式获取认证文件：

```bash
# 启动调试模式
python launch_camoufox.py --debug

# 在浏览器中完成 Google 登录
# 按终端提示确认操作
# 认证文件保存在 auth_profiles/saved/
# 将文件移动到 auth_profiles/active/ 目录
```

### 认证文件管理
- **位置**: `auth_profiles/active/*.json`
- **作用**: 无头模式依赖此文件维持登录状态
- **更新**: 认证文件会过期，需定期通过 `--debug` 模式重新获取

## 三层响应获取机制

项目采用三层响应获取机制，确保高可用性：

1. **集成流式代理 (Stream Proxy)** - 默认启用，端口 3120
   - 最佳性能和稳定性
   - 直接处理 AI Studio 请求
   - 支持基础参数传递

2. **外部 Helper 服务** - 可选配置
   - 作为流式代理的备用方案
   - 需要有效认证文件提取 SAPISID Cookie

3. **Playwright 页面交互** - 最终后备方案
   - 通过浏览器自动化获取响应
   - 支持完整参数控制（temperature, max_output_tokens, top_p, stop, reasoning_effort）
   - 适用于调试模式和参数精确控制

## 脚本注入功能 v3.0

**革命性改进**：使用 Playwright 原生网络拦截，100% 可靠性

### 工作机制
1. **脚本解析**: 从油猴脚本解析 `MODELS_TO_INJECT` 数组
2. **网络拦截**: Playwright 拦截 `/api/models` 请求
3. **数据合并**: 将注入模型与原始模型合并
4. **响应修改**: 返回包含注入模型的完整列表

### 配置
```env
ENABLE_SCRIPT_INJECTION=true
USERSCRIPT_PATH=browser_utils/more_modles.js
```

**优势**：
- 100% 可靠（Playwright 原生拦截）
- 零维护（脚本更新自动生效）
- 完全同步（前后端使用相同数据源）

## API 端点

### 主要端点
- `POST /v1/chat/completions` - 聊天完成接口（需要认证）
- `GET /v1/models` - 获取模型列表
- `GET /health` - 健康检查
- `GET /api/info` - API 配置信息
- `GET /v1/queue` - 队列状态
- `POST /v1/cancel/{req_id}` - 取消请求

### API 认证
支持两种认证方式：
- `Authorization: Bearer your-api-key` (推荐)
- `X-API-Key: your-api-key` (向后兼容)

认证密钥管理：
- 文件位置：`auth_profiles/key.txt`
- 格式：每行一个密钥
- 如果文件为空，则不需要认证

## 开发规范

### 新增端点规范
- 在 `api_utils/routers/` 下创建对应模块
- 在 `api_utils/routers/__init__.py` 中重导出端点
- 遵循错误统一：使用 `api_utils.error_utils` 构造 HTTPException
- 环境变量读取统一使用 `config.get_environment_variable`

### 错误处理规范
- 499: 客户端断开/取消
- 502: 上游/Playwright 失败
- 503: 服务不可用
- 504: 处理超时

### 命名规范
- 文件名: `snake_case`
- 类名: `PascalCase`
- 函数名: `snake_case`
- 常量: `UPPER_CASE`

### 类型注解
使用 Pyright 进行类型检查，配置文件：`pyrightconfig.json`

```python
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

def process_request(data: Dict[str, Any]) -> Optional[str]:
    """处理请求数据"""
    return data.get("message")
```

### 文档字符串
每个函数/类都应包含清晰的文档字符串：

```python
def process_chat_request(request: ChatRequest) -> ChatResponse:
    """
    处理聊天请求

    Args:
        request: 聊天请求对象

    Returns:
        ChatResponse: 聊天响应对象

    Raises:
        ValidationError: 当请求数据无效时
        ProcessingError: 当处理失败时
    """
    pass
```

## Docker 部署

```bash
# 进入 Docker 目录
cd docker

# 准备配置文件
cp .env.docker .env
nano .env

# 启动服务
docker compose up -d

# 查看日志
docker compose logs -f

# 版本更新
bash update.sh
```

**注意事项**：
- 首次运行需要在主机上获取认证文件
- 然后挂载到容器的 `auth_profiles/active/` 目录
- 支持 x86_64 和 ARM64 架构

## 故障排除

### 认证文件过期
症状：无头模式启动失败，重定向到登录页
解决：
1. 删除 `auth_profiles/active/` 下的旧文件
2. 重新执行 `python launch_camoufox.py --debug`
3. 完成登录后将新文件移动到 `active` 目录

### 端口冲突
使用 GUI 启动器的端口检查功能，或修改 `.env` 中的端口配置

### 代理配置问题
代理配置优先级：
1. `--internal-camoufox-proxy` 命令行参数
2. `UNIFIED_PROXY_CONFIG` 环境变量
3. `HTTP_PROXY` / `HTTPS_PROXY` 环境变量

## 重要提示

### 客户端管理历史
客户端负责维护完整的聊天记录并发送给代理。代理服务器本身不支持在 AI Studio 界面中对历史消息进行编辑或分叉操作。

### 性能考虑
- 推荐使用集成流式代理以获得最佳性能
- Playwright 模式延迟较高，仅用于调试和完整参数控制
- 大量模型注入可能影响页面加载性能

### 安全性
- `.env` 文件已被 `.gitignore` 忽略
- API 密钥在日志中会被打码显示
- 认证文件包含敏感信息，不应提交到版本控制

## 参考文档

项目包含完整的文档目录 `docs/`：
- `installation-guide.md` - 安装指南
- `environment-configuration.md` - 环境变量配置
- `authentication-setup.md` - 认证设置
- `daily-usage.md` - 日常运行指南
- `api-usage.md` - API 使用指南
- `architecture-guide.md` - 架构指南
- `development-guide.md` - 开发者指南
- `streaming-modes.md` - 流式处理模式详解
- `script_injection_guide.md` - 脚本注入指南
- `troubleshooting.md` - 故障排除指南

## 贡献指南

1. Fork 项目
2. 创建功能分支: `git checkout -b feature/amazing-feature`
3. 提交更改: `git commit -m 'feat: 添加惊人的功能'`
4. 推送分支: `git push origin feature/amazing-feature`
5. 创建 Pull Request

提交前检查清单：
- 代码遵循项目规范
- 添加了必要的测试
- 类型检查通过（`pyright`）
- 代码格式化完成（`black`, `isort`）
- 文档已更新
