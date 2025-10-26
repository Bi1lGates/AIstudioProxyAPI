# 服务器运维与API调用完整指南

本文档是AI Studio Proxy API的综合性运维与调用指南，涵盖API参数详解、服务器启动维护、日志管理等所有运维操作。

## 目录

- [API调用参数完整列表](#api调用参数完整列表)
- [Thinking Budget详细配置](#thinking-budget详细配置)
- [服务器启动与运维](#服务器启动与运维)
- [日志查看与问题排查](#日志查看与问题排查)
- [完整的API调用示例](#完整的api调用示例)

---

## API调用参数完整列表

### 基本信息

- **API端点**: `POST /v1/chat/completions`
- **Content-Type**: `application/json`
- **认证方式**: Bearer Token 或 X-API-Key Header

### 所有支持的参数

#### 1. messages (必需)

**类型**: `Array<Message>`

**说明**: 对话消息列表，包含用户和助手之间的对话历史。

**Message对象结构**:
```json
{
  "role": "user|assistant|system",
  "content": "文本内容" 或 [多模态内容数组]
}
```

**多模态内容支持**:
- 文本: `{"type": "text", "text": "内容"}`
- 图片: `{"type": "image_url", "image_url": {"url": "图片URL或data:URI"}}`
- 音频: `{"type": "input_audio", "input_audio": {"url": "音频URL", "format": "wav|mp3"}}`
- 视频: `{"type": "input_video", "input_video": {"url": "视频URL"}}`

**示例**:
```json
{
  "messages": [
    {"role": "user", "content": "你好"},
    {"role": "assistant", "content": "你好！有什么可以帮助你的吗？"}
  ]
}
```

#### 2. model (可选)

**类型**: `String`

**默认值**: `AI-Studio_Proxy_API` (可通过环境变量`MODEL_NAME`配置)

**说明**: 指定使用的AI模型。可通过 `GET /v1/models` 端点查看所有可用模型。

**常用模型**:
- `gemini-2.0-flash-exp`
- `gemini-2.5-pro-latest`
- `gemini-2.5-flash-latest`
- `gemini-exp-1206`

**示例**:
```json
{
  "model": "gemini-2.5-pro-latest"
}
```

#### 3. stream (可选)

**类型**: `Boolean`

**默认值**: `false`

**说明**: 是否启用流式响应。启用后，响应将以Server-Sent Events (SSE)方式逐步返回。

**注意**: 流式响应需要Stream Proxy服务运行（端口3120，可通过`STREAM_PORT`环境变量配置）

**示例**:
```json
{
  "stream": true
}
```

#### 4. temperature (可选)

**类型**: `Float`

**默认值**: `1.0` (可通过环境变量`DEFAULT_TEMPERATURE`配置)

**取值范围**: `0.0 - 2.0`

**说明**: 控制输出的随机性。值越低，输出越确定；值越高，输出越随机多样。
- 0.0: 完全确定性输出
- 1.0: 平衡的随机性（推荐）
- 2.0: 最大随机性

**示例**:
```json
{
  "temperature": 0.7
}
```

#### 5. max_output_tokens (可选)

**类型**: `Integer`

**默认值**: `65536` (可通过环境变量`DEFAULT_MAX_OUTPUT_TOKENS`配置)

**取值范围**: `1 - 模型最大支持值`

**说明**: 限制AI生成的最大token数量。不同模型支持的最大值不同，系统会自动根据模型限制进行调整。

**注意**: 设置过小可能导致回答被截断

**示例**:
```json
{
  "max_output_tokens": 8192
}
```

#### 6. top_p (可选)

**类型**: `Float`

**默认值**: `0.95` (可通过环境变量`DEFAULT_TOP_P`配置)

**取值范围**: `0.0 - 1.0`

**说明**: 核采样参数。控制模型从累积概率达到top_p的最小token集合中采样。
- 0.1: 只考虑概率最高的10%的tokens
- 0.95: 考虑累积概率达到95%的tokens（推荐）
- 1.0: 考虑所有tokens

**示例**:
```json
{
  "top_p": 0.9
}
```

#### 7. stop (可选)

**类型**: `String` 或 `Array<String>`

**默认值**: `["用户:"]` (可通过环境变量`DEFAULT_STOP_SEQUENCES`配置)

**说明**: 停止序列。当AI生成这些序列时，会立即停止生成。支持单个字符串或字符串数组。

**示例**:
```json
{
  "stop": ["用户:", "助手:", "\n\n"]
}
```

或单个字符串：
```json
{
  "stop": "END"
}
```

#### 8. reasoning_effort (可选) - Thinking Budget控制

**类型**: `String` 或 `Integer`

**默认值**: `null` (行为由环境变量`ENABLE_THINKING_BUDGET`控制)

**说明**: 控制AI的思考token预算限制。**重要**：AI的思考功能默认是**开启的**，此参数用于限制思考时使用的token数量。

**核心概念**:
- 不设置此参数（或设为`"none"`）= **不限制**思考预算 → 模型自由思考，自行决定深度（**默认最智能状态**）
- 设置具体数值 = **限制**思考预算 → 模型思考受限于指定token数
- 设置为 `0` = **关闭**思考功能 → 模型不进行思考，直接输出

**支持的值**:

| 值 | Token预算 | AI Studio界面 | 说明 |
|---|---|---|---|
| `"none"` 或 `null` | 不限制 | "Set thinking budget"开关**关闭** | 模型自由思考，不受token限制（**推荐默认**） |
| `"low"` | 1000 | 开关打开，显示1000 | 限制思考为1000 tokens |
| `"medium"` | 8000 | 开关打开，显示8000 | 限制思考为8000 tokens |
| `"high"` | 24000 | 开关打开，显示24000 | 限制思考为24000 tokens |
| 整数值（如5000） | 自定义 | 开关打开，显示该值 | 限制思考为指定token数 |
| `0` | 0 | 开关打开，值为0 | **完全关闭思考功能** |

**环境变量配置**:
- `ENABLE_THINKING_BUDGET=true/false`: 是否默认启用思考预算限制（默认false=不限制）
- `DEFAULT_THINKING_BUDGET=8192`: 当启用限制时的默认token数

**使用场景**:
- **不设置**或`"none"`: 让模型自由发挥，适合所有需要高质量输出的场景（**推荐**）
- `"low"` (1000): 轻度限制思考，适合快速响应场景
- `"medium"` (8000): 中度限制思考，平衡质量和速度
- `"high"` (24000): 高度限制但仍给予充足思考空间
- 自定义整数: 精确控制思考预算上限
- `0`: 需要最快响应，不需要深度推理的场景

**示例**:

不限制思考（推荐默认）：
```json
{
  "reasoning_effort": "none"
}
```
或直接不提供此参数

限制思考预算：
```json
{
  "reasoning_effort": "high"
}
```

自定义限制：
```json
{
  "reasoning_effort": 12000
}
```

完全关闭思考：
```json
{
  "reasoning_effort": 0
}
```

**详细说明请参见**: [Thinking Budget详细配置](#thinking-budget详细配置)

#### 9. tools (可选)

**类型**: `Array<Object>`

**默认值**: `null`

**说明**: 定义AI可以调用的工具/函数。支持Function Calling和Google Search工具。

**Google Search工具**:
```json
{
  "tools": [
    {"google_search_retrieval": {}}
  ]
}
```

或使用OpenAI格式：
```json
{
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "googleSearch",
        "description": "Search Google"
      }
    }
  ]
}
```

**环境变量配置**:
- `ENABLE_GOOGLE_SEARCH=true/false`: 当tools参数未提供时的默认行为

#### 10. tool_choice (可选)

**类型**: `String` 或 `Object`

**默认值**: `null`

**说明**: 控制工具调用的行为。

**可选值**:
- `"auto"`: AI自动决定是否调用工具
- `"none"`: 禁止调用任何工具
- `{"type": "function", "function": {"name": "工具名"}}`: 强制调用指定工具

#### 11. seed (可选)

**类型**: `Integer`

**默认值**: `null`

**说明**: 随机种子。使用相同的seed和参数可以获得更一致的输出结果。

**示例**:
```json
{
  "seed": 42
}
```

#### 12. response_format (可选)

**类型**: `String` 或 `Object`

**默认值**: `null`

**说明**: 指定响应格式。

**支持的格式**:
- `{"type": "json_object"}`: 要求返回JSON格式
- `{"type": "text"}`: 返回纯文本（默认）

#### 13. attachments (可选)

**类型**: `Array<Any>`

**默认值**: `null`

**说明**: 附件列表。用于兼容某些第三方客户端的顶层附件字段。

#### 14. mcp_endpoint (可选)

**类型**: `String`

**默认值**: `null`

**说明**: MCP（Model Context Protocol）端点URL。用于工具调用时回退到MCP服务。

---

## Thinking Budget详细配置

### 什么是Thinking Budget？

**重要理解**：AI模型的**思考功能默认是开启的**，模型会自行决定是否需要思考以及思考的深度。

Thinking Budget（思考预算）不是用来"开启"思考，而是用来**限制**思考时使用的token数量。这是一个**限制器**而非开关。

### 三种状态说明

| 状态 | AI Studio界面 | 模型行为 | 适用场景 |
|------|--------------|---------|---------|
| **不设置预算**（默认） | "Set thinking budget"开关关闭 | 模型**自由思考**，自行决定思考深度和token使用 | **推荐**：所有需要高质量输出的场景 |
| **设置具体预算** | 开关打开，显示数值 | 模型思考**受限**于指定token数 | 需要控制响应时间或成本 |
| **设置预算为0** | 开关打开，值为0 | **完全关闭**思考功能 | 只需要最快响应的简单任务 |

### 工作原理

AI模型具有内置的思考能力，在生成回答前会进行内部推理。这个推理过程可以帮助模型：
- 更好地理解复杂问题
- 进行多步骤推理
- 检查和验证答案
- 考虑多个可能的解决方案

**默认情况下**（不设置thinking budget），模型会根据问题的复杂度自主决定是否需要思考以及思考多深，这通常能获得最佳效果。

**设置thinking budget**会对模型的思考施加token限制，可能降低输出质量，但能缩短响应时间。

### 配置方式

#### 方式1: 通过API参数控制（优先级最高）

在每次API调用时通过`reasoning_effort`参数控制：

**不限制思考（推荐默认）**:
```bash
curl -X POST http://localhost:2048/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{
    "model": "gemini-2.5-pro-latest",
    "messages": [{"role": "user", "content": "解释量子纠缠"}]
  }'
```
或明确设置：
```json
{
  "reasoning_effort": "none"
}
```

**限制思考预算为1000 tokens**:
```json
{
  "reasoning_effort": "low"
}
```

**限制思考预算为8000 tokens**:
```json
{
  "reasoning_effort": "medium"
}
```

**限制思考预算为24000 tokens**:
```json
{
  "reasoning_effort": "high"
}
```

**自定义思考预算限制**:
```json
{
  "reasoning_effort": 15000
}
```

**完全关闭思考功能**:
```json
{
  "reasoning_effort": 0
}
```

#### 方式2: 通过环境变量配置（全局默认）

在`.env`文件中配置：

```env
# 是否默认启用思考预算限制
# false = 不限制，让模型自由思考（推荐）
# true = 启用限制，使用DEFAULT_THINKING_BUDGET的值
ENABLE_THINKING_BUDGET=false

# 当启用限制时的默认token数
DEFAULT_THINKING_BUDGET=8192
```

**注意**:
- 如果API请求中提供了`reasoning_effort`参数，则环境变量设置会被覆盖
- 如果API请求中未提供`reasoning_effort`参数：
  - `ENABLE_THINKING_BUDGET=false`（默认）→ 不限制思考
  - `ENABLE_THINKING_BUDGET=true` → 限制思考为`DEFAULT_THINKING_BUDGET`指定的token数

### 预设值详解

| 预设值 | Token预算 | 模型行为 | 适用场景 | 响应速度 |
|--------|-----------|---------|----------|----------|
| `"none"` 或不设置 | 不限制 | 自由思考，自主决定深度 | **所有场景（推荐默认）** | 取决于问题复杂度 |
| `"low"` | 1000 | 思考受限于1000 tokens | 需要快速响应的简单任务 | 快 |
| `"medium"` | 8000 | 思考受限于8000 tokens | 平衡质量和速度 | 中等 |
| `"high"` | 24000 | 思考受限于24000 tokens | 复杂任务但需要控制时间 | 较慢 |
| 自定义整数 | 自定义 | 思考受限于指定token数 | 精确控制需求 | 可变 |
| `0` | 0 | 完全不思考，直接输出 | 只需最快响应的极简任务 | 最快 |

### 实际应用示例

#### 场景1: 默认使用（不限制思考，推荐）

```bash
curl -X POST http://localhost:2048/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{
    "model": "gemini-2.5-pro-latest",
    "messages": [
      {"role": "user", "content": "解释机器学习中的过拟合问题，并提供解决方案"}
    ]
  }'
```
不设置`reasoning_effort`参数，让模型根据问题复杂度自主决定是否思考以及思考深度。

#### 场景2: 快速翻译（限制思考为1000 tokens）

```bash
curl -X POST http://localhost:2048/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{
    "model": "gemini-2.5-flash-latest",
    "messages": [
      {"role": "user", "content": "将以下英文翻译成中文: Hello, how are you?"}
    ],
    "reasoning_effort": "low"
  }'
```
简单翻译任务不需要深度思考，限制为1000 tokens以加快响应。

#### 场景3: 代码审查（限制为8000 tokens平衡质量和速度）

```bash
curl -X POST http://localhost:2048/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{
    "model": "gemini-2.5-pro-latest",
    "messages": [
      {
        "role": "user",
        "content": "请审查这段Python代码的安全性和性能问题：\n```python\ndef process_data(data):\n    result = []\n    for item in data:\n        result.append(item * 2)\n    return result\n```"
      }
    ],
    "reasoning_effort": "medium"
  }'
```
需要一定的分析深度但又要控制响应时间。

#### 场景4: 复杂推理（限制为24000 tokens）

```bash
curl -X POST http://localhost:2048/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{
    "model": "gemini-2.5-pro-latest",
    "messages": [
      {
        "role": "user",
        "content": "证明：对于任意正整数n，1^2 + 2^2 + 3^2 + ... + n^2 = n(n+1)(2n+1)/6"
      }
    ],
    "reasoning_effort": "high",
    "temperature": 0.3
  }'
```
复杂数学证明需要较深思考，但仍限制在24000 tokens以控制时间。

#### 场景5: 完全关闭思考（最快响应）

```bash
curl -X POST http://localhost:2048/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{
    "model": "gemini-2.5-flash-latest",
    "messages": [
      {"role": "user", "content": "今天是星期几？"}
    ],
    "reasoning_effort": 0
  }'
```
极简单的问题，完全不需要思考，追求最快响应。

### 性能与成本考虑

**响应时间影响**:
- **不设置**（默认）: 根据问题复杂度，模型自主决定
- `0`: 最快，无思考延迟
- `low` (1000): 增加少量延迟（~0.5-1秒）
- `medium` (8000): 增加1-3秒
- `high` (24000): 增加3-8秒
- 自定义高值: 可能增加10秒以上

**质量权衡**:
- **不设置预算**（推荐）：模型自主优化，通常获得最佳质量
- **设置预算限制**：可能降低输出质量，但能控制响应时间
- **设置为0**：完全不思考，质量可能明显下降

**使用建议**:
- **默认策略**：不设置`reasoning_effort`，让模型自由发挥
- **响应时间敏感**：使用`low`或`medium`限制
- **极简任务**：使用`0`完全关闭思考
- **不要盲目设置高值**：过高的限制不一定带来更好的效果

### 最佳实践

1. **默认策略（推荐）**:
   ```json
   {
     // 不设置reasoning_effort参数
     // 让模型根据问题复杂度自主决定
   }
   ```

2. **根据任务类型选择**:
   - 复杂分析、代码审查、创意写作 → **不设置**（让模型自由思考）
   - 简单翻译、格式转换 → `low` (1000)
   - 需要极快响应的简单问答 → `0`（关闭思考）

3. **与temperature配合使用**:
   - 不限制thinking + 低temperature → 高质量确定性输出
   - 限制thinking + 高temperature → 快速创意性输出
   - 关闭thinking (0) + 任意temperature → 最快响应

4. **流式输出考虑**:
   - 思考阶段不会产生流式输出
   - 不限制thinking时，首字节响应时间取决于问题复杂度
   - 关闭thinking (0)可以获得最快的首字节响应

5. **调试建议**:
   - 开发阶段：先不设置限制，观察效果
   - 如果响应太慢：逐步添加限制（从`high` → `medium` → `low`）
   - A/B测试：对比不同设置的效果和响应时间

### 故障排查

**问题1: 想要不限制思考，但模型表现不如预期**

可能原因：
- 环境变量 `ENABLE_THINKING_BUDGET=true` 导致默认启用了限制

解决方案：
```bash
# 方案1: 在API调用中明确指定不限制
{
  "reasoning_effort": "none"
}

# 方案2: 修改环境变量（全局生效）
# 在.env文件中设置
ENABLE_THINKING_BUDGET=false
```

**问题2: 响应时间过长**

可能原因：
- 没有设置thinking预算限制，模型自主决定了深度思考
- 或设置的预算值过高

解决方案：
```bash
# 方案1: 添加预算限制
{
  "reasoning_effort": "medium"  # 限制为8000 tokens
}

# 方案2: 进一步降低限制
{
  "reasoning_effort": "low"  # 限制为1000 tokens
}

# 方案3: 完全关闭思考（最快）
{
  "reasoning_effort": 0
}
```

**问题3: 想要关闭思考，但设置"none"没有效果**

原因：
- `"none"` 不是关闭思考，而是**不限制思考预算**

正确方案：
```bash
# 关闭思考必须设置为 0
{
  "reasoning_effort": 0
}
```

---

## 服务器启动与运维

### 启动方式对比

| 启动方式 | 适用场景 | 优点 | 缺点 |
|---------|---------|------|------|
| GUI启动器 | 新手、首次配置 | 图形化界面，易于配置 | 需要图形环境 |
| 命令行启动 | 日常使用、自动化 | 简单快捷，适合脚本 | 需要熟悉参数 |
| Docker部署 | 生产环境、多环境 | 环境隔离，易于部署 | 需要Docker知识 |

### 方式1: GUI图形界面启动（推荐新手）

**启动命令**:
```bash
python gui_launcher.py
```

**特点**:
- 提供友好的图形界面
- 实时显示服务状态
- 支持端口检测和配置
- 适合首次配置和调试

**适用场景**:
- 首次使用，需要配置各项参数
- 不熟悉命令行操作
- 需要实时查看服务状态

### 方式2: 命令行启动（推荐日常使用）

#### 基础启动（推荐）

使用`.env`配置文件，启动命令极简：

**无头模式（生产环境推荐）**:
```bash
python launch_camoufox.py --headless
```

**调试模式（首次设置或故障排除）**:
```bash
python launch_camoufox.py --debug
```

**虚拟显示模式（Linux服务器）**:
```bash
python launch_camoufox.py --virtual-display
```

#### 高级启动参数

虽然推荐使用`.env`配置，但命令行参数可以临时覆盖：

```bash
python launch_camoufox.py \
  --headless \
  --server-port 2048 \
  --stream-port 3120 \
  --internal-camoufox-proxy "http://127.0.0.1:7890"
```

**常用参数说明**:
- `--headless`: 无头模式（不显示浏览器窗口）
- `--debug`: 调试模式（显示浏览器窗口）
- `--virtual-display`: 虚拟显示模式（Linux服务器）
- `--server-port PORT`: FastAPI服务端口（默认2048）
- `--stream-port PORT`: 流式代理端口（默认3120，设为0禁用）
- `--internal-camoufox-proxy URL`: Camoufox浏览器代理地址

### 方式3: Docker部署（生产环境推荐）

#### 首次部署

**1. 准备配置文件**:
```bash
cd docker
cp .env.docker .env
nano .env  # 编辑配置
```

**2. 准备认证文件**:
```bash
# 在主机上先生成认证文件
cd ..
python launch_camoufox.py --debug
# 完成登录后，将生成的JSON文件移动到auth_profiles/active/目录
```

**3. 启动容器**:
```bash
cd docker
docker compose up -d
```

#### 日常运维命令

**查看日志**:
```bash
docker compose logs -f
```

**停止服务**:
```bash
docker compose stop
```

**重启服务**:
```bash
docker compose restart
```

**更新服务**:
```bash
bash update.sh
```

**完全删除并重建**:
```bash
docker compose down
docker compose up -d --build
```

### 环境变量配置详解

#### 核心配置项

**服务端口配置**:
```env
# FastAPI服务端口
PORT=2048
DEFAULT_FASTAPI_PORT=2048

# Camoufox调试端口（仅内部启动模式需要）
DEFAULT_CAMOUFOX_PORT=9222

# 流式代理端口（设为0禁用）
STREAM_PORT=3120
```

**代理配置**:
```env
# 统一代理配置（优先级最高）
UNIFIED_PROXY_CONFIG=http://127.0.0.1:7890

# 或使用HTTP/HTTPS分别配置
HTTP_PROXY=http://127.0.0.1:7890
HTTPS_PROXY=http://127.0.0.1:7890

# 代理绕过列表
NO_PROXY=localhost;127.0.0.1;*.local
```

**日志配置**:
```env
# 日志级别: DEBUG, INFO, WARNING, ERROR, CRITICAL
SERVER_LOG_LEVEL=INFO

# 启用调试日志（输出详细的操作信息）
DEBUG_LOGS_ENABLED=false

# 启用跟踪日志（输出最详细的调试信息）
TRACE_LOGS_ENABLED=false
```

**认证配置**:
```env
# 自动保存认证信息
AUTO_SAVE_AUTH=false

# 认证保存超时时间（秒）
AUTH_SAVE_TIMEOUT=30

# 自动确认登录
AUTO_CONFIRM_LOGIN=true
```

#### API默认参数配置

```env
# 默认温度值（0.0-2.0）
DEFAULT_TEMPERATURE=1.0

# 默认最大输出token数
DEFAULT_MAX_OUTPUT_TOKENS=65536

# 默认Top-P值（0.0-1.0）
DEFAULT_TOP_P=0.95

# 默认停止序列（JSON数组格式）
DEFAULT_STOP_SEQUENCES=["用户:"]

# 是否默认启用URL Context功能
ENABLE_URL_CONTEXT=false

# 是否默认启用思考预算功能
ENABLE_THINKING_BUDGET=false

# 默认思考预算token数
DEFAULT_THINKING_BUDGET=8192

# 是否默认启用Google Search功能
ENABLE_GOOGLE_SEARCH=false
```

#### 超时配置（毫秒）

```env
# 响应完成总超时时间
RESPONSE_COMPLETION_TIMEOUT=300000

# 初始等待时间
INITIAL_WAIT_MS_BEFORE_POLLING=500

# 轮询间隔
POLLING_INTERVAL=300
POLLING_INTERVAL_STREAM=180

# 静默超时（长时间无输出视为完成）
SILENCE_TIMEOUT_MS=60000

# 清理聊天相关超时
CLEAR_CHAT_VERIFY_TIMEOUT_MS=4000

# 点击操作超时
CLICK_TIMEOUT_MS=3000

# 元素等待超时
WAIT_FOR_ELEMENT_TIMEOUT_MS=10000
```

### 服务管理

#### 检查服务状态

**检查端口是否被占用**:
```bash
# macOS/Linux
lsof -i :2048
lsof -i :3120

# 或使用
netstat -an | grep 2048
```

**检查服务健康状态**:
```bash
curl http://localhost:2048/health
```

**查看API信息**:
```bash
curl http://localhost:2048/api/info
```

**查看可用模型**:
```bash
curl http://localhost:2048/v1/models
```

#### 停止服务

**正常模式启动的服务**:
```bash
# 使用Ctrl+C停止
# 或在另一个终端中
pkill -f "launch_camoufox.py"
```

**后台运行的服务**:
```bash
# 查找进程ID
ps aux | grep launch_camoufox

# 优雅停止
kill PID

# 强制停止
kill -9 PID
```

**Docker服务**:
```bash
docker compose stop
```

#### 重启服务

**命令行模式**:
```bash
# 停止后重新启动
python launch_camoufox.py --headless
```

**Docker模式**:
```bash
docker compose restart
```

#### 资源监控

**查看进程资源使用**:
```bash
# 实时监控
top -p $(pgrep -f launch_camoufox)

# 或使用htop（需要安装）
htop -p $(pgrep -f launch_camoufox)
```

**Docker资源监控**:
```bash
docker stats ai-studio-proxy-container
```

---

## 日志查看与问题排查

### 日志文件位置

#### 标准部署

所有日志文件存储在项目根目录的`logs/`目录下：

```
logs/
├── launch_app.log          # 启动器主日志
├── server.log              # FastAPI服务器日志
├── stream_proxy.log        # 流式代理服务日志
└── browser_automation.log  # 浏览器自动化日志
```

#### Docker部署

Docker部署默认不持久化日志，但可以通过挂载实现：

```yaml
# docker-compose.yml
volumes:
  - ../logs:/app/logs
```

**注意**: 如果出现权限报错，需要修改日志目录权限：
```bash
sudo chmod -R 777 ../logs
```

### 日志查看命令

#### 实时查看日志

**标准部署 - 查看所有日志**:
```bash
tail -f logs/*.log
```

**标准部署 - 查看特定日志**:
```bash
# 查看服务器日志
tail -f logs/server.log

# 查看启动器日志
tail -f logs/launch_app.log

# 查看流式代理日志
tail -f logs/stream_proxy.log
```

**Docker部署 - 实时查看**:
```bash
# 查看所有容器日志
docker compose logs -f

# 只查看最近100行
docker compose logs --tail=100 -f

# 查看特定时间后的日志
docker compose logs --since "2025-10-22T10:00:00" -f
```

#### 搜索日志内容

**搜索错误信息**:
```bash
# 标准部署
grep -i "error" logs/*.log
grep -i "exception" logs/*.log
grep -i "failed" logs/*.log

# Docker部署
docker compose logs | grep -i "error"
```

**搜索特定请求ID**:
```bash
# 标准部署
grep "req_id_12345" logs/server.log

# Docker部署
docker compose logs | grep "req_id_12345"
```

**搜索特定时间段**:
```bash
# 搜索特定日期的日志
grep "2025-10-22" logs/server.log

# 结合时间筛选
grep "2025-10-22 14:" logs/server.log
```

### 日志级别控制

#### 配置日志级别

在`.env`文件中配置：

```env
# 基础日志级别
SERVER_LOG_LEVEL=INFO

# 启用调试日志
DEBUG_LOGS_ENABLED=false

# 启用跟踪日志（最详细）
TRACE_LOGS_ENABLED=false
```

**日志级别说明**:
- `DEBUG`: 调试信息（包括所有操作细节）
- `INFO`: 一般信息（推荐生产环境）
- `WARNING`: 警告信息
- `ERROR`: 错误信息
- `CRITICAL`: 严重错误

#### 临时启用调试日志

**方法1: 修改.env文件**:
```env
SERVER_LOG_LEVEL=DEBUG
DEBUG_LOGS_ENABLED=true
```

**方法2: 环境变量覆盖**:
```bash
SERVER_LOG_LEVEL=DEBUG DEBUG_LOGS_ENABLED=true python launch_camoufox.py --headless
```

**Docker环境**:
```bash
# 修改docker/.env文件
SERVER_LOG_LEVEL=DEBUG
DEBUG_LOGS_ENABLED=true

# 重启容器
docker compose restart
```

### 常见问题排查

#### 问题1: 服务启动失败

**症状**: 启动后立即退出或报错

**排查步骤**:

1. **查看启动日志**:
```bash
cat logs/launch_app.log
```

2. **检查端口占用**:
```bash
lsof -i :2048
lsof -i :3120
```

3. **检查认证文件**:
```bash
ls -la auth_profiles/active/
```

4. **检查代理配置**:
```bash
echo $HTTP_PROXY
echo $HTTPS_PROXY
cat .env | grep PROXY
```

**常见原因**:
- 端口被占用 → 修改端口或停止占用端口的进程
- 认证文件缺失 → 运行`--debug`模式重新生成
- 代理配置错误 → 检查代理地址是否正确

#### 问题2: API请求失败或超时

**症状**: curl请求无响应或返回错误

**排查步骤**:

1. **检查服务状态**:
```bash
curl http://localhost:2048/health
```

2. **查看实时日志**:
```bash
tail -f logs/server.log
```

3. **测试简单请求**:
```bash
curl -X POST http://localhost:2048/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{
    "model": "gemini-2.5-flash-latest",
    "messages": [{"role": "user", "content": "测试"}]
  }'
```

4. **检查队列状态**:
```bash
curl http://localhost:2048/v1/queue
```

**常见原因**:
- Stream Proxy未启动 → 检查STREAM_PORT配置
- 认证文件过期 → 重新生成认证文件
- 网络代理问题 → 检查UNIFIED_PROXY_CONFIG
- 请求排队超时 → 查看队列状态，等待前面的请求完成

#### 问题3: 认证文件过期

**症状**: 日志显示重定向到登录页面

**排查步骤**:

1. **查看浏览器自动化日志**:
```bash
grep "login" logs/browser_automation.log
grep "redirect" logs/server.log
```

2. **删除旧认证文件**:
```bash
rm auth_profiles/active/*.json
```

3. **重新生成认证文件**:
```bash
python launch_camoufox.py --debug
# 在浏览器中完成登录
# 等待提示后确认保存
```

4. **移动认证文件**:
```bash
mv auth_profiles/saved/新文件名.json auth_profiles/active/
```

#### 问题4: 响应内容为空或不完整

**症状**: API返回空内容或内容被截断

**排查步骤**:

1. **检查超时设置**:
```bash
cat .env | grep TIMEOUT
```

2. **查看完成检测日志**:
```bash
grep "response completion" logs/server.log
grep "timeout" logs/server.log
```

3. **增加超时时间**:
```env
# .env文件
RESPONSE_COMPLETION_TIMEOUT=600000  # 增加到10分钟
SILENCE_TIMEOUT_MS=120000          # 增加静默超时
```

4. **检查max_output_tokens设置**:
```json
{
  "max_output_tokens": 65536  # 确保足够大
}
```

#### 问题5: Stream流式输出异常

**症状**: 流式输出卡住或格式错误

**排查步骤**:

1. **检查Stream Proxy状态**:
```bash
lsof -i :3120
curl http://localhost:3120/health
```

2. **查看Stream Proxy日志**:
```bash
tail -f logs/stream_proxy.log
```

3. **重启Stream Proxy**:
```bash
# 如果是独立启动的
pkill -f "stream.*proxy"

# 重新启动整个服务
python launch_camoufox.py --headless
```

4. **测试非流式请求**:
```bash
curl -X POST http://localhost:2048/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "stream": false,
    "messages": [{"role": "user", "content": "测试"}]
  }'
```

### 日志分析技巧

#### 追踪完整请求链路

每个请求都有唯一的`req_id`，通过它可以追踪完整处理链路：

```bash
# 提取请求ID（假设是req_abc123）
REQ_ID="req_abc123"

# 查看该请求的所有日志
grep "$REQ_ID" logs/*.log

# 按时间顺序排序
grep "$REQ_ID" logs/*.log | sort
```

#### 统计错误频率

```bash
# 统计各类错误的数量
grep -i "error" logs/server.log | wc -l
grep -i "timeout" logs/server.log | wc -l
grep -i "exception" logs/server.log | wc -l

# 统计最常见的错误
grep -i "error" logs/server.log | sort | uniq -c | sort -rn | head -10
```

#### 性能分析

```bash
# 查找响应时间较长的请求
grep "响应时间" logs/server.log | awk '{print $NF}' | sort -n | tail -20

# 统计平均响应时间
grep "响应时间" logs/server.log | awk '{sum+=$NF; count++} END {print sum/count}'
```

---

## 完整的API调用示例

### 基础调用示例

#### 示例1: 最简单的调用

```bash
curl -X POST http://localhost:2048/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{
    "messages": [
      {"role": "user", "content": "你好，请介绍一下你自己"}
    ]
  }'
```

#### 示例2: 指定模型和参数

```bash
curl -X POST http://localhost:2048/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{
    "model": "gemini-2.5-pro-latest",
    "messages": [
      {"role": "user", "content": "解释什么是机器学习"}
    ],
    "temperature": 0.7,
    "max_output_tokens": 2048,
    "top_p": 0.9
  }'
```

#### 示例3: 多轮对话

```bash
curl -X POST http://localhost:2048/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{
    "model": "gemini-2.5-flash-latest",
    "messages": [
      {"role": "user", "content": "什么是Python？"},
      {"role": "assistant", "content": "Python是一种高级编程语言..."},
      {"role": "user", "content": "它有什么优点？"}
    ],
    "temperature": 0.8
  }'
```

### 流式输出示例

#### 示例4: 基础流式输出

```bash
curl -X POST http://localhost:2048/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{
    "model": "gemini-2.5-flash-latest",
    "messages": [
      {"role": "user", "content": "写一篇关于人工智能的短文"}
    ],
    "stream": true
  }'
```

#### 示例5: Python流式处理

```python
import requests
import json

url = "http://localhost:2048/v1/chat/completions"
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer your-api-key"
}

data = {
    "model": "gemini-2.5-flash-latest",
    "messages": [
        {"role": "user", "content": "讲一个有趣的故事"}
    ],
    "stream": True
}

with requests.post(url, headers=headers, json=data, stream=True) as response:
    for line in response.iter_lines():
        if line:
            line = line.decode('utf-8')
            if line.startswith('data: '):
                if line.strip() == 'data: [DONE]':
                    break
                json_data = json.loads(line[6:])
                if 'choices' in json_data:
                    delta = json_data['choices'][0].get('delta', {})
                    content = delta.get('content', '')
                    if content:
                        print(content, end='', flush=True)
```

### Thinking Budget示例

#### 示例6: 不限制思考（推荐默认）

```bash
curl -X POST http://localhost:2048/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{
    "model": "gemini-2.5-pro-latest",
    "messages": [
      {"role": "user", "content": "解释深度学习中的反向传播算法"}
    ]
  }'
```
不设置`reasoning_effort`，让模型自由思考，获得最佳效果。

#### 示例7: 限制思考为1000 tokens（快速响应）

```bash
curl -X POST http://localhost:2048/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{
    "model": "gemini-2.5-flash-latest",
    "messages": [
      {"role": "user", "content": "将'Hello World'翻译成法语"}
    ],
    "reasoning_effort": "low"
  }'
```
简单翻译任务，限制思考以加快响应。

#### 示例8: 限制思考为8000 tokens（平衡质量和速度）

```bash
curl -X POST http://localhost:2048/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{
    "model": "gemini-2.5-pro-latest",
    "messages": [
      {
        "role": "user",
        "content": "用Python写一个快速排序算法，要求包含详细注释"
      }
    ],
    "reasoning_effort": "medium",
    "temperature": 0.5
  }'
```
需要一定的代码质量，但又要控制响应时间。

#### 示例9: 限制思考为24000 tokens（复杂推理）

```bash
curl -X POST http://localhost:2048/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{
    "model": "gemini-2.5-pro-latest",
    "messages": [
      {
        "role": "user",
        "content": "有3个盒子，每个盒子里有2个球。如果我从第一个盒子拿出1个球，然后把这个球放到第二个盒子，接着从第二个盒子拿出2个球放到第三个盒子，请问现在每个盒子里各有几个球？请详细说明推理过程。"
      }
    ],
    "reasoning_effort": "high",
    "temperature": 0.3
  }'
```
复杂推理任务，但仍限制在24000 tokens以控制响应时间。

#### 示例10: 自定义思考预算限制

```bash
curl -X POST http://localhost:2048/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{
    "model": "gemini-2.5-pro-latest",
    "messages": [
      {
        "role": "user",
        "content": "设计一个电商系统的数据库架构，包括用户、商品、订单、支付等模块，要求支持分库分表，并考虑高并发场景"
      }
    ],
    "reasoning_effort": 15000,
    "temperature": 0.6,
    "max_output_tokens": 8192
  }'
```
自定义限制为15000 tokens，在质量和时间间找到平衡点。

#### 示例11: 完全关闭思考（最快响应）

```bash
curl -X POST http://localhost:2048/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{
    "model": "gemini-2.5-flash-latest",
    "messages": [
      {"role": "user", "content": "今天天气怎么样？"}
    ],
    "reasoning_effort": 0
  }'
```
极简单问题，完全关闭思考功能以获得最快响应。

### 多模态输入示例

#### 示例12: 图片输入

```bash
curl -X POST http://localhost:2048/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{
    "model": "gemini-2.5-flash-latest",
    "messages": [
      {
        "role": "user",
        "content": [
          {"type": "text", "text": "这张图片里有什么？"},
          {
            "type": "image_url",
            "image_url": {
              "url": "https://example.com/image.jpg"
            }
          }
        ]
      }
    ]
  }'
```

#### 示例13: Base64编码的图片

```bash
curl -X POST http://localhost:2048/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{
    "model": "gemini-2.5-flash-latest",
    "messages": [
      {
        "role": "user",
        "content": [
          {"type": "text", "text": "分析这张图片"},
          {
            "type": "image_url",
            "image_url": {
              "url": "data:image/jpeg;base64,/9j/4AAQSkZJRg..."
            }
          }
        ]
      }
    ],
    "reasoning_effort": "medium"
  }'
```

### 工具调用示例

#### 示例14: 启用Google Search

```bash
curl -X POST http://localhost:2048/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{
    "model": "gemini-2.5-pro-latest",
    "messages": [
      {"role": "user", "content": "最新的AI技术发展是什么？"}
    ],
    "tools": [
      {"google_search_retrieval": {}}
    ]
  }'
```
不限制思考，让模型自由决定如何使用Google Search。

### 高级组合示例

#### 示例15: 完整参数配置

```bash
curl -X POST http://localhost:2048/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{
    "model": "gemini-2.5-pro-latest",
    "messages": [
      {
        "role": "system",
        "content": "你是一个专业的Python编程助手"
      },
      {
        "role": "user",
        "content": "帮我优化这段代码：\ndef fib(n):\n    if n <= 1:\n        return n\n    return fib(n-1) + fib(n-2)"
      }
    ],
    "temperature": 0.5,
    "max_output_tokens": 4096,
    "top_p": 0.9,
    "stop": ["```\n\n", "用户:"],
    "reasoning_effort": "high",
    "stream": false,
    "seed": 42
  }'
```

#### 示例16: 流式 + 限制思考预算 + 多模态

```python
import requests
import json

url = "http://localhost:2048/v1/chat/completions"
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer your-api-key"
}

data = {
    "model": "gemini-2.5-pro-latest",
    "messages": [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "分析这个图表中的数据趋势，并提供详细的统计分析和预测"
                },
                {
                    "type": "image_url",
                    "image_url": {"url": "https://example.com/chart.png"}
                }
            ]
        }
    ],
    "reasoning_effort": "high",  # 限制思考为24000 tokens
    "temperature": 0.4,
    "max_output_tokens": 8192,
    "stream": True
}

print("正在分析图表...")
with requests.post(url, headers=headers, json=data, stream=True) as response:
    for line in response.iter_lines():
        if line:
            line = line.decode('utf-8')
            if line.startswith('data: '):
                if line.strip() == 'data: [DONE]':
                    print("\n分析完成！")
                    break
                try:
                    json_data = json.loads(line[6:])
                    if 'choices' in json_data:
                        delta = json_data['choices'][0].get('delta', {})
                        content = delta.get('content', '')
                        if content:
                            print(content, end='', flush=True)
                except json.JSONDecodeError:
                    pass
```

### OpenAI SDK兼容示例

#### 示例17: 使用OpenAI Python SDK

```python
from openai import OpenAI

# 初始化客户端
client = OpenAI(
    api_key="your-api-key",
    base_url="http://localhost:2048/v1"
)

# 基础调用（不限制思考）
response = client.chat.completions.create(
    model="gemini-2.5-flash-latest",
    messages=[
        {"role": "user", "content": "你好，请介绍一下你自己"}
    ]
)
print(response.choices[0].message.content)

# 流式调用 + 限制思考预算
stream = client.chat.completions.create(
    model="gemini-2.5-pro-latest",
    messages=[
        {"role": "user", "content": "写一篇关于人工智能的文章"}
    ],
    stream=True,
    temperature=0.7,
    extra_body={
        "reasoning_effort": "medium"  # 限制为8000 tokens
    }
)

for chunk in stream:
    if chunk.choices[0].delta.content is not None:
        print(chunk.choices[0].delta.content, end='', flush=True)
```

### Node.js示例

#### 示例18: 使用Node.js调用

```javascript
const OpenAI = require('openai');

const openai = new OpenAI({
  apiKey: 'your-api-key',
  baseURL: 'http://localhost:2048/v1'
});

async function main() {
  // 非流式调用
  const completion = await openai.chat.completions.create({
    model: 'gemini-2.5-flash-latest',
    messages: [
      { role: 'user', content: '用JavaScript写一个Promise示例' }
    ],
    temperature: 0.6,
    reasoning_effort: 'medium'  // 自定义参数
  });

  console.log(completion.choices[0].message.content);

  // 流式调用
  const stream = await openai.chat.completions.create({
    model: 'gemini-2.5-pro-latest',
    messages: [
      { role: 'user', content: '解释什么是闭包' }
    ],
    stream: true,
    reasoning_effort: 'high'
  });

  for await (const chunk of stream) {
    process.stdout.write(chunk.choices[0]?.delta?.content || '');
  }
}

main();
```

---

## 附录

### API端点快速参考

| 端点 | 方法 | 说明 | 需要认证 |
|------|------|------|---------|
| `/health` | GET | 健康检查 | 否 |
| `/api/info` | GET | API配置信息 | 否 |
| `/v1/models` | GET | 获取模型列表 | 否 |
| `/v1/chat/completions` | POST | 聊天完成 | 是 |
| `/v1/queue` | GET | 查看队列状态 | 否 |
| `/v1/cancel/{req_id}` | POST | 取消请求 | 否 |

### 环境变量快速参考

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `PORT` | 2048 | FastAPI服务端口 |
| `STREAM_PORT` | 3120 | 流式代理端口 |
| `UNIFIED_PROXY_CONFIG` | - | 统一代理配置 |
| `SERVER_LOG_LEVEL` | INFO | 日志级别 |
| `DEFAULT_TEMPERATURE` | 1.0 | 默认温度 |
| `DEFAULT_MAX_OUTPUT_TOKENS` | 65536 | 默认最大输出tokens |
| `ENABLE_THINKING_BUDGET` | false | 是否默认启用思考预算限制（false=不限制） |
| `DEFAULT_THINKING_BUDGET` | 8192 | 启用限制时的默认token数 |

### 故障排查速查表

| 症状 | 可能原因 | 解决方案 |
|------|---------|---------|
| 服务启动失败 | 端口被占用 | 检查并释放端口，或修改配置 |
| API请求超时 | 响应超时设置太短 | 增加RESPONSE_COMPLETION_TIMEOUT |
| 认证失败 | API密钥错误 | 检查key.txt文件 |
| 响应为空 | 认证文件过期 | 重新生成认证文件 |
| 流式输出异常 | Stream Proxy未运行 | 检查STREAM_PORT配置 |
| 设置"none"无法关闭思考 | "none"表示不限制而非关闭 | 使用reasoning_effort=0完全关闭思考 |

### 性能优化建议

1. **选择合适的模型**:
   - 简单任务: gemini-2.5-flash-latest
   - 复杂任务: gemini-2.5-pro-latest

2. **合理设置thinking budget**:
   - 默认不设置，让模型自由思考（推荐）
   - 需要控制响应时间时添加限制（low/medium/high）
   - 极简任务设为0完全关闭思考

3. **使用流式输出**:
   - 提升用户体验
   - 更快的首字节响应时间

4. **优化超时设置**:
   - 根据实际需求调整RESPONSE_COMPLETION_TIMEOUT
   - 避免设置过短导致超时

5. **日志级别控制**:
   - 生产环境使用INFO级别
   - 仅在调试时启用DEBUG

### 相关文档

- [安装指南](docs/installation-guide.md)
- [环境变量配置](docs/environment-configuration.md)
- [认证设置](docs/authentication-setup.md)
- [API使用指南](docs/api-usage.md)
- [日常运行指南](docs/daily-usage.md)
- [故障排除](docs/troubleshooting.md)
- [架构指南](docs/architecture-guide.md)

---

本文档最后更新: 2025-10-22
