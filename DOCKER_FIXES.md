# Docker 环境修复记录

本文档记录了在 Docker 环境中遇到的问题及其修复方案。

---

## 修复 1: Camoufox 0.4.11 Proxy 参数问题

### 问题描述

**错误信息**:
```
Error launching server: proxy: expected object, got null
Failed to launch browser.
RuntimeError: Server process terminated unexpectedly
```

**触发条件**:
- Docker 环境
- 无代理配置（headless 模式）
- Camoufox 0.4.11

### 问题根源

**Camoufox 0.4.11 的 bug**:
- 文件: `/usr/local/lib/python3.10/site-packages/camoufox/utils.py`
- 函数: `launch_options()`
- 问题: 该函数在返回配置字典时，无条件包含 `"proxy": proxy`
- 当 `proxy=None` 时，这个值会被序列化为 JSON 的 `null`
- Playwright 的 `launchServer()` 拒绝接受 `"proxy": null`，导致启动失败

**预期行为**:
- 有代理: `{"proxy": {"server": "http://..."}}`
- 无代理: `{}`（不包含 proxy 键）

**实际行为**:
- 无代理: `{"proxy": null}` ❌

### 解决方案

#### 文件 1: `patch_camoufox_proxy.py`（项目根目录）

创建自动修复脚本，在 Docker 构建时修改 Camoufox 源码：

```python
#!/usr/bin/env python3
# patch_camoufox_proxy.py
# 自动修复 Camoufox 0.4.11 的 proxy=None 问题

import sys
import os

CAMOUFOX_UTILS_PATH = "/usr/local/lib/python3.10/site-packages/camoufox/utils.py"

def patch_camoufox_utils():
    """修复 Camoufox utils.py 的 proxy 处理逻辑"""
    # 将 return {..., "proxy": proxy, ...}
    # 修改为:
    # result = {...}
    # if proxy is not None:
    #     result["proxy"] = proxy
    # return result

    # 详细实现见项目文件
```

**原理**:
- 查找 `launch_options()` 函数中的 return 语句
- 从字典中移除 `"proxy": proxy` 键值对
- 在 return 之前添加条件判断：只在 `proxy is not None` 时才添加该键
- 确保无代理时返回的字典中不包含 proxy 键

#### 文件 2: `docker/Dockerfile`（第 71-73 行）

在 Dockerfile 中添加自动执行修复脚本的步骤：

```dockerfile
# 下载 Camoufox 浏览器（从 GitHub 官方源）
RUN python -m camoufox fetch

# 修复 Camoufox 0.4.11 的 proxy=None 问题
COPY patch_camoufox_proxy.py /tmp/
RUN python /tmp/patch_camoufox_proxy.py && rm /tmp/patch_camoufox_proxy.py
```

**执行时机**:
- 在 `python -m camoufox fetch` 之后立即执行
- 在切换到非 root 用户之前执行（确保有修改权限）

#### 文件 3: `launch_camoufox.py`（第 629-632 行）

**重要**: 不要显式设置 `proxy=None`，让键在无代理时不存在：

```python
# 正确的代码（原始逻辑）
if camoufox_proxy_internal:  # 如果代理字符串存在且不为空
    launch_args_for_internal_camoufox["proxy"] = {"server": camoufox_proxy_internal}
# 如果 camoufox_proxy_internal 是 None 或空字符串，"proxy" 键就不会被添加。
```

**错误的代码**（不要这样写）:
```python
# ❌ 错误！Camoufox 0.4.11 不接受 proxy=None
if camoufox_proxy_internal:
    launch_args_for_internal_camoufox["proxy"] = {"server": camoufox_proxy_internal}
else:
    launch_args_for_internal_camoufox["proxy"] = None  # ❌ 这会导致错误
```

### 验证修复成功

**Docker 构建日志**应包含:
```
============================================================
Camoufox 0.4.11 Proxy 修复脚本
============================================================
正在检查文件: /usr/local/lib/python3.10/site-packages/camoufox/utils.py
找到需要修改的 return 语句
✅ 成功修复 Camoufox utils.py 的 proxy 问题！
============================================================
```

**容器启动日志**应包含:
```
✅ 成功从 Camoufox 内部进程捕获到 WebSocket 端点
Server launched: XXXms
Websocket endpoint: ws://localhost:9222/...
```

**不应出现**:
```
❌ Error launching server: proxy: expected object, got null
```

### 技术细节

**为什么不升级 Camoufox 版本？**
- 项目锁定了 Camoufox 0.4.11（见 `pyproject.toml`）
- 升级可能引入其他不兼容问题
- 通过源码修补是最安全的方案

**为什么不修改 launch_camoufox.py？**
- 尝试过设置 `proxy=None`，但 Camoufox 0.4.11 仍然报错
- 必须从源头（Camoufox 源码）解决问题
- 这样可以确保所有调用 `launch_server()` 的地方都能正常工作

**修复的稳定性**:
- ✅ 每次 Docker 构建都会自动执行修复
- ✅ 修复脚本有幂等性（重复执行安全）
- ✅ 不影响有代理配置的情况
- ✅ 向后兼容

---

## 修复 2: key.txt 文件权限问题

### 问题描述

**错误信息**:
```
PermissionError: [Errno 13] Permission denied: '/app/auth_profiles/key.txt'
File "/app/api_utils/auth_utils.py", line 21, in initialize_keys
    with open(KEY_FILE_PATH, "w") as f:
```

**触发条件**:
- Docker 环境
- FastAPI 启动时尝试初始化 API 密钥文件

### 问题根源

**Docker 文件权限问题**:

1. **文件复制阶段**（Dockerfile 第 66 行）:
   ```dockerfile
   COPY . .
   ```
   - 项目中已有 `auth_profiles/key.txt`
   - COPY 时文件所有者默认为 `root`
   - 此时容器仍以 root 用户运行

2. **权限设置阶段**（Dockerfile 第 89-90 行）:
   ```dockerfile
   chown -R appuser:appgroup /app
   ```
   - 递归修改 `/app` 目录所有者

3. **用户切换**（Dockerfile 第 95 行后）:
   ```dockerfile
   USER appuser
   ```
   - 切换到非特权用户 `appuser`

4. **运行时问题**:
   - 程序以 `appuser` 身份运行
   - 尝试以写模式（`"w"`）打开 `key.txt`
   - 如果 `chown` 执行时 `key.txt` 不存在，则无法修改其权限
   - 后续程序创建的文件可能权限不正确

### 问题细节

**COPY 和 chown 的时序问题**:

```dockerfile
# 第 66 行: 复制项目文件
COPY . .                    # key.txt 被复制，所有者: root

# 第 76-83 行: 创建目录
RUN mkdir -p /app/auth_profiles/active \
    /app/auth_profiles/saved

# 第 89-90 行: 修改所有者
chown -R appuser:appgroup /app   # ← 如果 key.txt 不存在，无法设置权限
```

**问题**:
- 如果源代码中没有 `key.txt`，`chown` 时该文件不存在
- 程序运行时创建的文件所有者可能是 `appuser`，但可能没有写权限
- 某些环境下文件系统配置可能导致权限异常

### 解决方案

#### 修改 `docker/Dockerfile`（第 88 行）

在 `chown` 之前预创建 `key.txt` 文件：

```dockerfile
# 创建目录和设置权限
RUN mkdir -p /app/logs \
    /app/auth_profiles/active \
    /app/auth_profiles/saved \
    /app/certs \
    /app/browser_utils/custom_scripts \
    /home/appuser/.cache/ms-playwright \
    /home/appuser/.mozilla \
    /var/cache/camoufox && \
    # 修正 camoufox 缓存逻辑
    if [ -d /root/.cache/camoufox ]; then cp -a /root/.cache/camoufox/* /var/cache/camoufox/; fi && \
    mkdir -p /app/.cache && \
    ln -s /var/cache/camoufox /app/.cache/camoufox && \
    touch /app/auth_profiles/key.txt && \    # ← 新增：确保 key.txt 存在
    chown -R appuser:appgroup /app && \
    chown -R appuser:appgroup /home/appuser
```

**原理**:
- `touch` 命令确保 `key.txt` 文件存在
- 如果文件已存在（从 COPY 复制来的），更新其时间戳
- 如果文件不存在，创建空文件
- 随后的 `chown` 会正确设置文件所有者为 `appuser:appgroup`
- 确保程序运行时有写权限

### 验证修复成功

**容器启动日志**应包含:
```
✅ 成功从 Camoufox 内部进程捕获到 WebSocket 端点
--- 步骤 5: 启动集成的 FastAPI 服务器 (监听端口: 2048) ---
===== AIStudioProxyServer 日志系统已在 lifespan 中初始化 =====
INFO:     Started server process [xxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:2048
```

**不应出现**:
```
❌ PermissionError: [Errno 13] Permission denied: '/app/auth_profiles/key.txt'
```

**手动验证**（可选）:
```bash
# 进入容器
docker exec -it ai-studio-proxy-container /bin/bash

# 检查文件权限
ls -la /app/auth_profiles/key.txt

# 预期输出:
# -rw-r--r-- 1 appuser appgroup 0 Oct 22 17:00 /app/auth_profiles/key.txt
#            ^^^^^^^^ ^^^^^^^^^
#            所有者    所属组
```

### 技术细节

**为什么使用 touch 而不是直接创建？**
- `touch` 是幂等操作（重复执行安全）
- 兼容文件已存在的情况
- 确保文件在 `chown` 执行时存在

**为什么不在 Python 代码中处理权限？**
- Python 代码运行时已切换到 `appuser`，无法修改权限
- 在 Dockerfile 构建阶段处理更可靠
- 避免运行时权限检查开销

**其他可能的解决方案（未采用）**:
1. ❌ 在 COPY 后立即 chown（需要额外的 RUN 层，增加镜像大小）
2. ❌ 修改程序以只读模式打开（违背程序设计意图）
3. ❌ 使用 VOLUME 挂载外部文件（增加部署复杂度）

---

## 完整修复流程

### 1. 确认文件存在

确保以下文件在项目中：
- ✅ `patch_camoufox_proxy.py`（项目根目录）
- ✅ `docker/Dockerfile`（已添加修复逻辑）
- ✅ `auth_profiles/key.txt`（可以是空文件）

### 2. 停止现有容器

```bash
cd docker
docker compose down
```

### 3. 清理 Docker 缓存（可选但推荐）

```bash
# 清理构建缓存
docker builder prune -f

# 清理悬空镜像
docker image prune -f
```

### 4. 重新构建镜像

```bash
# 使用 --no-cache 确保完全重新构建
docker compose build --no-cache

# 或者不使用 --no-cache（如果硬盘空间有限）
docker compose build
```

### 5. 启动容器

```bash
docker compose up -d
```

### 6. 验证修复

```bash
# 查看实时日志
docker compose logs -f

# 应该看到：
# ✅ 成功修复 Camoufox utils.py
# ✅ Server launched: XXXms
# ✅ Websocket endpoint: ws://localhost:9222/...
# ✅ Application startup complete.
# ✅ Uvicorn running on http://0.0.0.0:2048

# 按 Ctrl+C 退出日志查看

# 测试 API
curl http://localhost:2048/health
# 预期响应: {"status":"healthy"}
```

---

## 故障排除

### 问题 1: 修复脚本未执行

**症状**:
- 构建日志中看不到 "✅ 成功修复 Camoufox utils.py"

**原因**:
- Docker 使用了缓存，跳过了修复步骤

**解决**:
```bash
docker compose build --no-cache
```

### 问题 2: 仍然出现 proxy 错误

**症状**:
- 日志显示 "proxy: expected object, got null"

**排查**:
1. 检查 `launch_camoufox.py` 是否有 `else: proxy=None`（应该删除）
2. 进入容器手动验证修复：
   ```bash
   docker exec -it ai-studio-proxy-container /bin/bash
   grep -A 5 "if proxy is not None:" /usr/local/lib/python3.10/site-packages/camoufox/utils.py
   ```
3. 如果没有找到，说明修复脚本失败，重新构建镜像

### 问题 3: 仍然出现 key.txt 权限错误

**症状**:
- 日志显示 "PermissionError: /app/auth_profiles/key.txt"

**排查**:
```bash
# 进入容器
docker exec -it ai-studio-proxy-container /bin/bash

# 检查文件权限
ls -la /app/auth_profiles/key.txt

# 如果不存在或所有者不是 appuser，重新构建
```

**解决**:
```bash
docker compose down
docker compose build --no-cache
docker compose up -d
```

### 问题 4: 构建时提示找不到文件

**症状**:
- `COPY patch_camoufox_proxy.py /tmp/` 报错

**原因**:
- 文件不在项目根目录

**解决**:
```bash
# 确认文件位置
ls -la patch_camoufox_proxy.py

# 应该在项目根目录，与 pyproject.toml 同级
```

---

## 参考信息

### 相关 Issue

- **Camoufox PR #361**: "Fix launch server breaking when no proxy option is passed"
  - 官方修复了相同的问题，但未包含在 0.4.11 版本中
  - 我们的修复方案与官方思路一致

### 项目版本

- **Python**: 3.10
- **Camoufox**: 0.4.11（锁定版本，见 `pyproject.toml`）
- **Playwright**: 自动安装（通过 Poetry）
- **Docker Base Image**: `python:3.10-slim-bookworm`

### 修复文件位置

```
AIstudioProxyAPI/
├── patch_camoufox_proxy.py           # Camoufox 修复脚本
├── launch_camoufox.py                # 主启动器（无需修改）
├── auth_profiles/
│   └── key.txt                       # API 密钥文件
├── docker/
│   └── Dockerfile                    # 已添加两个修复
└── DOCKER_FIXES.md                   # 本文档
```

---

## 总结

这两个修复解决了 Docker 环境特有的问题：

1. **Camoufox Proxy 问题**: 通过自动化脚本修改源码，确保无代理环境正常工作
2. **Key.txt 权限问题**: 通过预创建文件并正确设置所有者，确保程序有写权限

两个修复都集成在 Dockerfile 中，每次构建自动执行，无需手动干预。

**关键要点**:
- ✅ 使用 `--no-cache` 确保修复生效
- ✅ 验证构建日志中的成功信息
- ✅ 测试容器启动和 API 访问
- ✅ 修复具有幂等性，安全可重复

---

**文档版本**: v1.0
**最后更新**: 2025-10-22
**适用版本**: Camoufox 0.4.11 + Docker 部署
