# 项目修改记录 - 2025-10-22

## 概述

本次修改主要解决了 Docker 环境下的两个关键问题，确保项目能在容器环境中正常运行。

---

## 修改清单

### 1. 修复 Camoufox 0.4.11 Proxy 参数问题

#### 问题描述
Docker 环境中，无代理配置时 Camoufox 启动失败：
```
Error launching server: proxy: expected object, got null
```

#### 解决方案

##### 新增文件：`patch_camoufox_proxy.py`
- **位置**：项目根目录
- **作用**：自动修复 Camoufox 源码中的 proxy 参数处理逻辑
- **原理**：
  - 修改 `/usr/local/lib/python3.10/site-packages/camoufox/utils.py`
  - 将 `return {..., "proxy": proxy, ...}` 改为条件判断
  - 只在 `proxy is not None` 时才包含该键
- **执行时机**：Docker 构建时自动执行

##### 修改文件：`docker/Dockerfile`
- **修改位置**：第 71-73 行（在 `RUN python -m camoufox fetch` 之后）
- **添加内容**：
  ```dockerfile
  # 修复 Camoufox 0.4.11 的 proxy=None 问题
  COPY patch_camoufox_proxy.py /tmp/
  RUN python /tmp/patch_camoufox_proxy.py && rm /tmp/patch_camoufox_proxy.py
  ```

##### 修改文件：`launch_camoufox.py`
- **修改位置**：第 629-634 行
- **修改内容**：撤销了错误的 `else: proxy=None` 分支
- **修改前**（错误）：
  ```python
  if camoufox_proxy_internal:
      launch_args_for_internal_camoufox["proxy"] = {"server": camoufox_proxy_internal}
  else:
      launch_args_for_internal_camoufox["proxy"] = None  # ❌ 会导致错误
  ```
- **修改后**（正确）：
  ```python
  if camoufox_proxy_internal:
      launch_args_for_internal_camoufox["proxy"] = {"server": camoufox_proxy_internal}
  # 如果 camoufox_proxy_internal 是 None 或空字符串，"proxy" 键就不会被添加。
  ```

---

### 2. 修复 key.txt 文件权限问题

#### 问题描述
FastAPI 启动时无法写入 API 密钥文件：
```
PermissionError: [Errno 13] Permission denied: '/app/auth_profiles/key.txt'
```

#### 解决方案

##### 修改文件：`docker/Dockerfile`
- **修改位置**：第 88 行
- **添加内容**：在 `chown` 之前添加 `touch /app/auth_profiles/key.txt`
- **修改后**：
  ```dockerfile
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
      touch /app/auth_profiles/key.txt && \    # ← 新增
      chown -R appuser:appgroup /app && \
      chown -R appuser:appgroup /home/appuser
  ```
- **作用**：确保 `key.txt` 在 `chown` 执行时存在，从而正确设置文件所有者为 `appuser`

---

### 3. 新增文档

#### 文件：`DOCKER_FIXES.md`
- **位置**：项目根目录
- **内容**：
  - 详细记录了两个 Docker 环境修复的问题分析、解决方案和验证方法
  - 包含完整修复流程、故障排除指南和技术细节
  - 总计 600+ 行完整文档

#### 文件：`CAMOUFOX_FIX_GUIDE.txt`
- **位置**：项目根目录
- **内容**：
  - 简洁的操作指南，适合快速参考
  - 包含步骤清单、常见问题和验证方法

---

## 文件修改汇总

### 新增文件（3个）
```
AIstudioProxyAPI/
├── patch_camoufox_proxy.py      # Camoufox 修复脚本
├── DOCKER_FIXES.md              # 详细修复文档
└── CAMOUFOX_FIX_GUIDE.txt       # 快速操作指南
```

### 修改文件（2个）
```
AIstudioProxyAPI/
├── launch_camoufox.py           # 撤销错误修改（第 629-634 行）
└── docker/
    └── Dockerfile               # 添加两处修复逻辑（第 71-73, 88 行）
```

---

## 修改前后对比

### Dockerfile 变化

#### 修改前
```dockerfile
# 第 69 行
RUN python -m camoufox fetch

# 第 75-89 行
RUN mkdir -p /app/logs \
    /app/auth_profiles/active \
    /app/auth_profiles/saved \
    ... && \
    chown -R appuser:appgroup /app && \
    chown -R appuser:appgroup /home/appuser
```

#### 修改后
```dockerfile
# 第 69-73 行
RUN python -m camoufox fetch

# 修复 Camoufox 0.4.11 的 proxy=None 问题
COPY patch_camoufox_proxy.py /tmp/
RUN python /tmp/patch_camoufox_proxy.py && rm /tmp/patch_camoufox_proxy.py

# 第 75-90 行
RUN mkdir -p /app/logs \
    /app/auth_profiles/active \
    /app/auth_profiles/saved \
    ... && \
    touch /app/auth_profiles/key.txt && \    # ← 新增
    chown -R appuser:appgroup /app && \
    chown -R appuser:appgroup /home/appuser
```

---

## 验证结果

### 构建日志
```
✅ 成功修复 Camoufox utils.py 的 proxy 问题！
```

### 启动日志
```
✅ 成功从 Camoufox 内部进程捕获到 WebSocket 端点
Server launched: 707ms
Websocket endpoint: ws://localhost:9222/...
✅ Application startup complete.
✅ Uvicorn running on http://0.0.0.0:2048
```

### 错误消失
- ❌ ~~`proxy: expected object, got null`~~（已解决）
- ❌ ~~`PermissionError: /app/auth_profiles/key.txt`~~（已解决）

---

## 技术要点

### 为什么不升级 Camoufox？
- 项目锁定了 0.4.11 版本（`pyproject.toml`）
- 升级可能引入其他兼容性问题
- 通过源码补丁是最安全的方案

### 为什么不能设置 proxy=None？
- Camoufox 0.4.11 会将 `proxy=None` 传递给 Playwright
- Playwright 将其序列化为 JSON 的 `null`
- Playwright 的 `launchServer()` 拒绝接受 `"proxy": null`
- 必须让 proxy 键完全不存在（不传递该参数）

### 修复的幂等性
- ✅ `patch_camoufox_proxy.py` 可重复执行，会检查是否已修复
- ✅ `touch` 命令是幂等操作，文件存在时只更新时间戳
- ✅ 每次 Docker 构建都会自动执行修复，无需手动干预

---

## 部署说明

### 重新构建 Docker 镜像

```bash
# 1. 停止容器
cd docker
docker compose down

# 2. 清理缓存（可选但推荐）
docker builder prune -f

# 3. 重新构建（必须使用 --no-cache）
docker compose build --no-cache

# 4. 启动容器
docker compose up -d

# 5. 查看日志验证
docker compose logs -f
```

### 验证清单

- [ ] 构建日志中看到 "✅ 成功修复 Camoufox utils.py"
- [ ] 启动日志中看到 "Server launched: XXXms"
- [ ] 启动日志中看到 "Application startup complete"
- [ ] 没有 "proxy: expected object, got null" 错误
- [ ] 没有 "PermissionError" 错误
- [ ] `curl http://localhost:2048/health` 返回 `{"status":"healthy"}`

---

## 代理配置（补充）

### 香港服务器无法访问 AI Studio 的解决方案

由于 Google AI Studio 不支持香港地区访问，需要配置代理。

#### 方法：环境变量配置（推荐）

编辑 `docker/.env` 文件：

```env
# 统一代理配置
UNIFIED_PROXY_CONFIG=http://代理IP:端口

# 如果代理需要认证
# UNIFIED_PROXY_CONFIG=http://username:password@代理IP:端口

# 如果使用 SOCKS5
# UNIFIED_PROXY_CONFIG=socks5://代理IP:端口
```

重启容器：
```bash
docker compose down
docker compose up -d
```

#### 验证代理生效

查看日志：
```bash
docker compose logs -f | grep -i proxy
```

应该看到：
```
代理配置: http://代理IP:端口
传递给 launch_server 的参数: {..., 'proxy': {'server': 'http://代理IP:端口'}, ...}
```

#### 是否需要重新获取 cookies？

**不需要！**
- Auth JSON 文件中的 cookies 是用户身份凭证，与网络环境无关
- 只要 cookies 没过期（通常 1-2 年），可以在任何地区使用
- 代理只影响网络连接，不影响身份认证

---

## 相关参考

### 官方 Issue
- **Camoufox PR #361**: "Fix launch server breaking when no proxy option is passed"
  - 官方修复了相同的问题，但未包含在 0.4.11 中
  - 我们的修复方案与官方思路一致

### 项目版本信息
- **Python**: 3.10
- **Camoufox**: 0.4.11（锁定）
- **Playwright**: 自动安装
- **Docker Base**: python:3.10-slim-bookworm

### 文档链接
- 详细修复文档：`DOCKER_FIXES.md`
- 快速操作指南：`CAMOUFOX_FIX_GUIDE.txt`
- 项目架构说明：`CLAUDE.md`

---

## 后续建议

### 监控关注点
1. **Camoufox 版本更新**
   - 关注 0.4.12+ 版本是否包含官方修复
   - 如果官方修复发布，可考虑升级并移除补丁

2. **Auth 文件有效期**
   - Cookies 通常 1-2 年有效
   - 定期检查是否需要重新认证

3. **代理稳定性**
   - 监控代理连接质量
   - 准备备用代理方案

### 维护建议
1. **文档同步**
   - 如果修改 Dockerfile，同步更新 `DOCKER_FIXES.md`
   - 记录新的问题和解决方案

2. **版本控制**
   - 将修复纳入版本控制
   - 标记关键修复的 commit

3. **测试流程**
   - 每次构建后验证两个修复是否生效
   - 测试有代理和无代理两种场景

---

## 总结

本次修改成功解决了 Docker 环境下的两个关键问题：

1. **Camoufox Proxy 问题**
   - 通过自动化脚本修改源码
   - 确保无代理环境正常工作
   - 不影响有代理配置的场景

2. **Key.txt 权限问题**
   - 通过预创建文件并正确设置所有者
   - 确保程序有写权限
   - 避免运行时权限错误

两个修复都集成在 Dockerfile 中，每次构建自动执行，无需手动干预，确保了项目在 Docker 环境中的稳定运行。

---

**修改日期**: 2025-10-22
**修改人员**: Claude Code + 用户
**测试状态**: ✅ 通过（Docker 环境）
**部署状态**: ✅ 已部署（香港服务器）
