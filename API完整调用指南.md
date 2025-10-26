# AI Studio Proxy API 完整调用指南

本文档提供 AI Studio Proxy API 的完整调用说明，包括所有端点、参数、文件上传方式和代码示例。

## 目录

- [基础配置](#基础配置)
- [API 认证](#api-认证)
- [主要端点](#主要端点)
- [请求参数详解](#请求参数详解)
- [文件和图片上传](#文件和图片上传)
- [完整代码示例](#完整代码示例)
- [错误处理](#错误处理)

## 基础配置

### 服务器地址

默认服务器地址：`http://8.217.6.233:2048`

配置方式：
- 环境变量：`.env` 文件中设置 `PORT=2048` 或 `DEFAULT_FASTAPI_PORT=2048`
- 命令行参数：`--server-port 2048`
- GUI 启动器：图形界面直接配置

### Base URL

所有 API 请求的 Base URL：`http://8.217.6.233:2048/v1`

## API 认证

### 认证方式

支持两种标准的认证方式：

1. **Bearer Token 认证**（推荐）
```http
Authorization: Bearer your-api-key
```

2. **X-API-Key 头部认证**（向后兼容）
```http
X-API-Key: your-api-key
```

### 密钥管理

密钥配置文件：`auth_profiles/key.txt`

文件格式（每行一个密钥）：
```
your-api-key-1
your-api-key-2
# 注释行会被忽略

another-api-key
```

说明：
- 如果 `key.txt` 为空或不存在，则不需要认证
- 密钥最小长度：8 个字符
- 日志中密钥会被打码显示（如：`abcd****efgh`）

## 主要端点

### 1. 聊天完成接口

**端点**：`POST /v1/chat/completions`

这是核心的对话接口，与 OpenAI API 完全兼容。

**需要认证**：是（如果配置了 API 密钥）

### 2. 模型列表

**端点**：`GET /v1/models`

获取所有可用模型列表，包括 AI Studio 原生模型和注入的自定义模型。

**需要认证**：否

### 3. API 信息

**端点**：`GET /api/info`

返回 API 配置信息。

**需要认证**：否

### 4. 健康检查

**端点**：`GET /health`

返回服务器运行状态，包括 Playwright、浏览器、页面、Worker 和队列状态。

**需要认证**：否

### 5. 队列状态

**端点**：`GET /v1/queue`

返回当前请求队列的详细信息。

**需要认证**：否

### 6. 取消请求

**端点**：`POST /v1/cancel/{req_id}`

尝试取消队列中等待处理的请求。

**需要认证**：否

## 请求参数详解

### ChatCompletionRequest 完整参数

#### 必需参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| `messages` | Array | 对话消息数组，必须包含至少一条消息 |

#### 可选参数

| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `model` | String | 环境配置 | 模型 ID，如 `gemini-1.5-pro-latest` |
| `stream` | Boolean | `false` | 是否流式返回结果 |
| `temperature` | Float | `1.0` | 温度参数，范围 [0, 2] |
| `max_output_tokens` | Integer | `8192` | 最大输出 token 数 |
| `top_p` | Float | `0.95` | Top-p 采样参数，范围 [0, 1] |
| `stop` | String 或 Array | `null` | 停止序列，单个字符串或字符串数组 |
| `reasoning_effort` | String 或 Integer | `null` | 思考预算，可选值见下文 |
| `tools` | Array | `null` | 可用工具列表，支持 Google Search 等 |
| `tool_choice` | String 或 Object | `null` | 工具选择策略 |
| `seed` | Integer | `null` | 随机种子，用于可重复生成 |
| `response_format` | String 或 Object | `null` | 响应格式 |
| `attachments` | Array | `null` | 顶层附件数组，支持多种格式 |
| `mcp_endpoint` | String | `null` | MCP 服务端点（用于工具调用） |

### 参数详细说明

#### 1. messages 数组

每条消息对象包含：

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `role` | String | 是 | 角色：`system`, `user`, `assistant`, `tool` |
| `content` | String/Array/null | 否 | 消息内容，支持多种格式 |
| `name` | String | 否 | 发送者名称 |
| `tool_calls` | Array | 否 | 工具调用列表（assistant 角色） |
| `tool_call_id` | String | 否 | 工具调用 ID（tool 角色） |
| `attachments` | Array | 否 | 消息级附件 |
| `images` | Array | 否 | 图片附件（兼容字段） |
| `files` | Array | 否 | 文件附件（兼容字段） |
| `media` | Array | 否 | 媒体附件（兼容字段） |

#### 2. content 内容格式

content 支持三种格式：

**格式 1：纯文本字符串**
```json
{
  "role": "user",
  "content": "你好，请介绍一下自己"
}
```

**格式 2：内容项数组**（多模态消息）
```json
{
  "role": "user",
  "content": [
    {
      "type": "text",
      "text": "这张图片是什么？"
    },
    {
      "type": "image_url",
      "image_url": {
        "url": "data:image/jpeg;base64,...",
        "detail": "high"
      }
    }
  ]
}
```

**格式 3：字典对象**（兼容格式）
```json
{
  "role": "user",
  "content": {
    "text": "分析这个文件",
    "attachments": [...]
  }
}
```

#### 3. reasoning_effort 参数（pro:128-32768; flash:0-24576)

控制模型的思考深度（思考预算）。

**支持的值**：

| 值 | 类型 | Token 预算 | 说明 |
|----|------|------------|------|
| `"low"` | String | 1000 | 低思考预算 |
| `"medium"` | String | 8000 | 中等思考预算 |
| `"high"` | String | 24000 | 高思考预算 |
| `"none"` | String | 禁用 | 禁用思考预算功能 |
| 整数值 | Integer | 自定义 | 直接指定 token 数量 |

示例：
```json
{
  "reasoning_effort": "high"
}
```

或
```json
{
  "reasoning_effort": 16000
}
```

#### 4. tools 参数

定义可用的工具（函数）。

**Google Search 示例**：
```json
{
  "tools": [
    {
      "google_search_retrieval": {}
    }
  ]
}
```

**自定义函数示例**：
```json
{
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "get_weather",
        "description": "获取指定城市的天气信息",
        "parameters": {
          "type": "object",
          "properties": {
            "city": {
              "type": "string",
              "description": "城市名称"
            }
          },
          "required": ["city"]
        }
      }
    }
  ]
}
```

#### 5. tool_choice 参数

控制工具使用策略。

**支持的值**：

| 值 | 说明 |
|----|------|
| `"auto"` | 自动决定是否调用工具 |
| `"none"` | 不调用任何工具 |
| `"required"` | 必须调用工具 |
| `{"type": "function", "function": {"name": "函数名"}}` | 指定调用特定函数 |

#### 6. stop 参数

停止序列，当模型生成这些序列时停止。

**单个字符串**：
```json
{
  "stop": "\n\nUser:"
}
```

**字符串数组**：
```json
{
  "stop": ["\n\nUser:", "\n\nHuman:", "###"]
}
```

## 文件和图片上传

AI Studio Proxy API 支持多种文件和图片上传方式，兼容 OpenAI API 标准。

### 支持的文件类型

- **图片**：PNG, JPEG, JPG, GIF, WebP, SVG, BMP
- **视频**：MP4, WebM, OGG
- **音频**：MP3, WAV, OGG, WebM Audio
- **文档**：PDF, TXT, Markdown, HTML, JSON, ZIP

### 上传方式

#### 方式 1：data: URL（Base64 编码）

最通用的方式，适合任何客户端。

**图片示例**：
```json
{
  "role": "user",
  "content": [
    {
      "type": "text",
      "text": "这张图片是什么？"
    },
    {
      "type": "image_url",
      "image_url": {
        "url": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD...",
        "detail": "high"
      }
    }
  ]
}
```

**详细度参数**（`detail`）：
- `"auto"`：自动选择（默认）
- `"low"`：低分辨率，节省 token
- `"high"`：高分辨率，更精确的分析

**视频/音频示例**：
```json
{
  "role": "user",
  "content": [
    {
      "type": "input_video",
      "input_video": {
        "data": "data:video/mp4;base64,AAAAGGZ0eXBpc29tAAACAGlzb21...",
        "format": "mp4",
        "mime_type": "video/mp4"
      }
    }
  ]
}
```

**生成 Base64 编码**：

Python 示例：
```python
import base64

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# 使用
image_base64 = encode_image("path/to/image.jpg")
data_url = f"data:image/jpeg;base64,{image_base64}"
```

#### 方式 2：file:// URL（本地文件路径）

适合服务器端调用。

```json
{
  "role": "user",
  "content": [
    {
      "type": "image_url",
      "image_url": {
        "url": "file:///Users/username/Pictures/photo.jpg"
      }
    }
  ]
}
```

注意：
- URL 格式必须是 `file://` + 绝对路径
- 文件必须存在于服务器文件系统中
- 路径中的特殊字符需要 URL 编码

#### 方式 3：绝对路径

直接使用文件系统绝对路径。

**在 content 数组中**：
```json
{
  "role": "user",
  "content": [
    {
      "type": "image_url",
      "image_url": {
        "url": "/Users/username/Pictures/photo.jpg"
      }
    }
  ]
}
```

**在 attachments 字段中**：
```json
{
  "role": "user",
  "content": "分析这些文件",
  "attachments": [
    "/Users/username/Documents/report.pdf",
    "/Users/username/Pictures/chart.png"
  ]
}
```

#### 方式 4：消息级附件字段

兼容多种客户端的附件字段。

**attachments 字段**：
```json
{
  "role": "user",
  "content": "分析这张图片",
  "attachments": [
    {
      "url": "data:image/png;base64,...",
      "type": "image"
    }
  ]
}
```

**images 字段**（简化格式）：
```json
{
  "role": "user",
  "content": "这是什么？",
  "images": [
    "data:image/jpeg;base64,...",
    "/path/to/local/image.jpg"
  ]
}
```

**files 字段**：
```json
{
  "role": "user",
  "content": "处理这些文件",
  "files": [
    {
      "path": "/path/to/document.pdf"
    },
    {
      "url": "file:///path/to/data.json"
    }
  ]
}
```

#### 方式 5：请求级附件字段

在请求的顶层添加 attachments。

```json
{
  "messages": [...],
  "attachments": [
    "data:image/png;base64,...",
    "/path/to/file.pdf",
    {
      "url": "file:///path/to/video.mp4",
      "type": "video"
    }
  ]
}
```

### 支持的内容项类型

在 `content` 数组中支持的所有类型：

| 类型 | 字段 | 用途 |
|------|------|------|
| `text` | `text` | 纯文本内容 |
| `image_url` | `image_url` | 图片 URL（OpenAI 标准） |
| `input_image` | `input_image` | 图片输入（兼容格式） |
| `file_url` | `file_url` | 文件 URL |
| `media_url` | `media_url` | 媒体文件 URL |
| `input_audio` | `input_audio` | 音频输入 |
| `input_video` | `input_video` | 视频输入 |

### 文件处理流程

1. **识别附件**：从 content、attachments、images、files、media 等字段提取
2. **格式转换**：
   - `data:` URL → 解析 Base64 并保存到本地
   - `file://` URL → 解析并验证路径
   - 绝对路径 → 验证文件存在性
3. **上传到 AI Studio**：通过 Playwright 模拟文件上传
4. **清理临时文件**：请求完成后清理临时目录

### 附件配置

环境变量控制附件处理行为：

```env
# 仅收集最后一条用户消息的附件（默认 false）
ONLY_COLLECT_CURRENT_USER_ATTACHMENTS=false

# 上传文件临时目录
UPLOAD_FILES_DIR=upload_files
```

## 完整代码示例

### 示例 1：简单文本对话（非流式）

```python
import requests

url = "http://8.217.6.233:2048/v1/chat/completions"
headers = {
    "Authorization": "Bearer your-api-key",
    "Content-Type": "application/json"
}

data = {
    "model": "gemini-2.5-pro",
    "messages": [
        {
            "role": "system",
            "content": "你是一个有帮助的AI助手。"
        },
        {
            "role": "user",
            "content": "什么是量子计算？请简要说明。"
        }
    ],
    "stream": False,
    "temperature": 0.7,
    "max_output_tokens": 500
}

response = requests.post(url, headers=headers, json=data)

if response.status_code == 200:
    result = response.json()
    print("助手回复：")
    print(result['choices'][0]['message']['content'])
    print("\nToken 使用情况：")
    print(result['usage'])
else:
    print(f"错误 {response.status_code}: {response.text}")
```

### 示例 2：流式对话

```python
import requests
import json

url = "http://8.217.6.233:2048/v1/chat/completions"
headers = {
    "Authorization": "Bearer your-api-key",
    "Content-Type": "application/json"
}

data = {
    "model": "gemini-flash-latest",
    "messages": [
        {
            "role": "user",
            "content": "写一个关于春天的短诗。"
        }
    ],
    "stream": True,
    "temperature": 0.9
}

response = requests.post(url, headers=headers, json=data, stream=True)

if response.status_code == 200:
    print("流式输出：")
    for line in response.iter_lines():
        if line:
            decoded_line = line.decode('utf-8')
            if decoded_line.startswith('data: '):
                content = decoded_line[6:]  # 移除 'data: ' 前缀

                if content.strip() == '[DONE]':
                    print("\n\n流式输出完成。")
                    break

                try:
                    chunk = json.loads(content)
                    delta = chunk.get('choices', [{}])[0].get('delta', {})
                    text = delta.get('content', '')
                    if text:
                        print(text, end='', flush=True)
                except json.JSONDecodeError:
                    print(f"\n解析错误: {content}")
else:
    print(f"错误 {response.status_code}: {response.text}")
```

### 示例 3：上传图片（Base64 方式）

```python
import requests
import base64
import json

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# 读取并编码图片
image_path = "path/to/your/image.jpg"
base64_image = encode_image(image_path)

url = "http://8.217.6.233:2048/v1/chat/completions"
headers = {
    "Authorization": "Bearer your-api-key",
    "Content-Type": "application/json"
}

data = {
    "model": "gemini-2.5-pro",
    "messages": [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "请详细描述这张图片的内容。"
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}",
                        "detail": "high"
                    }
                }
            ]
        }
    ],
    "stream": False,
    "max_output_tokens": 1000
}

response = requests.post(url, headers=headers, json=data)

if response.status_code == 200:
    result = response.json()
    print(result['choices'][0]['message']['content'])
else:
    print(f"错误: {response.text}")
```

### 示例 4：上传多个文件（混合方式）

```python
import requests
import base64

url = "http://8.217.6.233:2048/v1/chat/completions"
headers = {
    "Authorization": "Bearer your-api-key",
    "Content-Type": "application/json"
}

# 方式1：使用 content 数组
data = {
    "model": "gemini-1.5-pro-latest",
    "messages": [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "分析这些图片的异同点。"
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "data:image/jpeg;base64,/9j/4AAQ...",
                        "detail": "high"
                    }
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "file:///Users/username/image2.png"
                    }
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "/Users/username/image3.jpg"
                    }
                }
            ]
        }
    ],
    "stream": False
}

# 方式2：使用 attachments 字段（更简洁）
data_alternative = {
    "model": "gemini-1.5-pro-latest",
    "messages": [
        {
            "role": "user",
            "content": "分析这些图片的异同点。",
            "attachments": [
                "data:image/jpeg;base64,/9j/4AAQ...",
                "file:///Users/username/image2.png",
                "/Users/username/image3.jpg"
            ]
        }
    ],
    "stream": False
}

response = requests.post(url, headers=headers, json=data)
# 或
# response = requests.post(url, headers=headers, json=data_alternative)

if response.status_code == 200:
    print(response.json()['choices'][0]['message']['content'])
else:
    print(f"错误: {response.text}")
```

### 示例 5：使用高级参数

```python
import requests

url = "http://8.217.6.233:2048/v1/chat/completions"
headers = {
    "Authorization": "Bearer your-api-key",
    "Content-Type": "application/json"
}

data = {
    "model": "gemini-2.0-flash-thinking-exp-01-21",
    "messages": [
        {
            "role": "system",
            "content": "你是一个逻辑推理专家。"
        },
        {
            "role": "user",
            "content": "解释量子纠缠的原理，并给出一个简单的类比。"
        }
    ],
    "stream": False,
    "temperature": 0.5,
    "max_output_tokens": 2000,
    "top_p": 0.9,
    "stop": ["\n\n---", "结束"],
    "reasoning_effort": "high",  # 启用深度思考
    "seed": 42  # 可重复生成
}

response = requests.post(url, headers=headers, json=data)

if response.status_code == 200:
    result = response.json()
    message = result['choices'][0]['message']

    print("回复内容：")
    print(message['content'])

    # 如果有推理内容
    if 'reasoning_content' in message:
        print("\n推理过程：")
        print(message['reasoning_content'])

    print("\nToken 统计：")
    print(f"输入: {result['usage']['prompt_tokens']}")
    print(f"输出: {result['usage']['completion_tokens']}")
    print(f"总计: {result['usage']['total_tokens']}")
else:
    print(f"错误: {response.text}")
```

### 示例 6：使用 Google Search 工具

```python
import requests

url = "http://8.217.6.233:2048/v1/chat/completions"
headers = {
    "Authorization": "Bearer your-api-key",
    "Content-Type": "application/json"
}

data = {
    "model": "gemini-1.5-pro-latest",
    "messages": [
        {
            "role": "user",
            "content": "2024年奥运会在哪里举办？"
        }
    ],
    "tools": [
        {
            "google_search_retrieval": {}
        }
    ],
    "stream": False
}

response = requests.post(url, headers=headers, json=data)

if response.status_code == 200:
    result = response.json()
    print(result['choices'][0]['message']['content'])
else:
    print(f"错误: {response.text}")
```

### 示例 7：处理视频文件

```python
import requests
import base64

def encode_video(video_path):
    with open(video_path, "rb") as video_file:
        return base64.b64encode(video_file.read()).decode('utf-8')

url = "http://8.217.6.233:2048/v1/chat/completions"
headers = {
    "Authorization": "Bearer your-api-key",
    "Content-Type": "application/json"
}

video_base64 = encode_video("path/to/video.mp4")

data = {
    "model": "gemini-1.5-pro-latest",
    "messages": [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "总结这个视频的主要内容。"
                },
                {
                    "type": "input_video",
                    "input_video": {
                        "data": f"data:video/mp4;base64,{video_base64}",
                        "format": "mp4",
                        "mime_type": "video/mp4"
                    }
                }
            ]
        }
    ],
    "stream": False,
    "max_output_tokens": 2000
}

response = requests.post(url, headers=headers, json=data)

if response.status_code == 200:
    print(response.json()['choices'][0]['message']['content'])
else:
    print(f"错误: {response.text}")
```

### 示例 8：OpenAI SDK 兼容使用

```python
from openai import OpenAI

# 初始化客户端，指向代理服务器
client = OpenAI(
    api_key="your-api-key",
    base_url="http://8.217.6.233:2048/v1"
)

# 非流式对话
response = client.chat.completions.create(
    model="gemini-1.5-pro-latest",
    messages=[
        {"role": "system", "content": "你是一个有帮助的AI助手。"},
        {"role": "user", "content": "解释一下什么是机器学习。"}
    ],
    temperature=0.7,
    max_tokens=500
)

print(response.choices[0].message.content)

# 流式对话
stream = client.chat.completions.create(
    model="gemini-1.5-flash-latest",
    messages=[
        {"role": "user", "content": "写一首关于秋天的诗。"}
    ],
    stream=True,
    temperature=0.9
)

for chunk in stream:
    if chunk.choices[0].delta.content is not None:
        print(chunk.choices[0].delta.content, end='', flush=True)
```

### 示例 9：使用 curl 命令

**非流式请求**：
```bash
curl -X POST http://8.217.6.233:2048/v1/chat/completions \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemini-1.5-pro-latest",
    "messages": [
      {
        "role": "user",
        "content": "你好，介绍一下自己"
      }
    ],
    "stream": false,
    "temperature": 0.7,
    "max_output_tokens": 500
  }'
```

**流式请求**：
```bash
curl -X POST http://8.217.6.233:2048/v1/chat/completions \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  --no-buffer \
  -d '{
    "model": "gemini-1.5-flash-latest",
    "messages": [
      {
        "role": "user",
        "content": "写一个Python函数计算斐波那契数列"
      }
    ],
    "stream": true,
    "temperature": 0.5
  }'
```

**上传图片（Base64）**：
```bash
# 先编码图片
IMAGE_BASE64=$(base64 -i path/to/image.jpg)

curl -X POST http://8.217.6.233:2048/v1/chat/completions \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"gemini-1.5-pro-latest\",
    \"messages\": [
      {
        \"role\": \"user\",
        \"content\": [
          {
            \"type\": \"text\",
            \"text\": \"描述这张图片\"
          },
          {
            \"type\": \"image_url\",
            \"image_url\": {
              \"url\": \"data:image/jpeg;base64,$IMAGE_BASE64\"
            }
          }
        ]
      }
    ],
    \"stream\": false
  }"
```

## 错误处理

### HTTP 状态码

| 状态码 | 说明 | 处理建议 |
|--------|------|----------|
| 200 | 成功 | 正常处理响应 |
| 400 | 错误的请求 | 检查请求参数格式 |
| 401 | 未授权 | 检查 API 密钥 |
| 422 | 无法处理的实体 | 检查模型是否可用 |
| 499 | 客户端断开连接 | 客户端取消了请求 |
| 500 | 服务器内部错误 | 查看服务器日志 |
| 502 | 上游错误 | Playwright 或 AI Studio 交互失败 |
| 503 | 服务不可用 | 服务器正在初始化或页面未就绪 |
| 504 | 请求超时 | 增加超时时间或简化请求 |

### 错误响应格式

```json
{
  "error": {
    "message": "错误描述",
    "type": "error_type",
    "code": "error_code"
  }
}
```

### 常见错误及解决方案

#### 1. 认证失败（401）

**错误信息**：
```json
{
  "detail": "Invalid API key"
}
```

**解决方案**：
- 检查 `Authorization` 头部是否正确
- 确认 API 密钥在 `auth_profiles/key.txt` 中存在
- 确认密钥至少 8 个字符

#### 2. 模型切换失败（422）

**错误信息**：
```json
{
  "detail": "[req_id] 未能切换到模型 'model-name'。请确保模型可用。"
}
```

**解决方案**：
- 调用 `GET /v1/models` 查看可用模型列表
- 使用列表中的模型 ID
- 检查模型是否在 `excluded_models.txt` 中被排除

#### 3. 服务不可用（503）

**错误信息**：
```json
{
  "detail": "[req_id] AI Studio 页面丢失或未就绪。"
}
```

**解决方案**：
- 调用 `GET /health` 检查服务状态
- 等待服务初始化完成
- 检查浏览器是否正常运行
- 重启服务

#### 4. 请求超时（504）

**错误信息**：
```json
{
  "detail": "[req_id] 请求处理超时。"
}
```

**解决方案**：
- 减少 `max_output_tokens` 参数
- 简化请求内容
- 检查网络连接
- 增加超时配置（`.env` 中的 `RESPONSE_COMPLETION_TIMEOUT`）

#### 5. 文件上传失败

**错误信息**：
```
文件不存在: /path/to/file.jpg
```

**解决方案**：
- 使用 Base64 编码的 data: URL
- 确保文件路径是绝对路径
- 检查文件权限
- 确认文件确实存在

### 错误处理示例代码

```python
import requests
import json

url = "http://8.217.6.233:2048/v1/chat/completions"
headers = {
    "Authorization": "Bearer your-api-key",
    "Content-Type": "application/json"
}

data = {
    "model": "gemini-1.5-pro-latest",
    "messages": [
        {"role": "user", "content": "Hello"}
    ]
}

try:
    response = requests.post(url, headers=headers, json=data, timeout=120)
    response.raise_for_status()  # 抛出 HTTP 错误

    result = response.json()
    print(result['choices'][0]['message']['content'])

except requests.exceptions.Timeout:
    print("请求超时，请稍后重试")

except requests.exceptions.HTTPError as e:
    status_code = e.response.status_code

    if status_code == 401:
        print("认证失败，请检查 API 密钥")
    elif status_code == 503:
        print("服务暂时不可用，请稍后重试")
    elif status_code == 504:
        print("请求处理超时")
    else:
        try:
            error_detail = e.response.json()
            print(f"API 错误: {error_detail}")
        except:
            print(f"HTTP 错误 {status_code}: {e.response.text}")

except requests.exceptions.ConnectionError:
    print("无法连接到服务器，请检查服务器是否运行")

except Exception as e:
    print(f"未知错误: {e}")
```

## 高级主题

### 三层响应获取机制

系统采用三层响应获取机制，确保高可用性：

1. **集成流式代理**（默认，端口 3120）
   - 最佳性能和稳定性
   - 支持基础参数
   - 推荐用于生产环境

2. **外部 Helper 服务**（可选）
   - 需要配置 `GUI_DEFAULT_HELPER_ENDPOINT`
   - 需要有效的认证文件
   - 作为流式代理的备用

3. **Playwright 页面交互**（最终后备）
   - 支持完整参数控制
   - 延迟较高
   - 适合调试和参数精确控制

配置示例：
```env
# 启用集成流式代理（推荐）
STREAM_PORT=3120

# 禁用流式代理，强制使用 Playwright
STREAM_PORT=0

# 配置外部 Helper
GUI_DEFAULT_HELPER_ENDPOINT=http://helper-service:port
```

### 批量请求处理

```python
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

url = "http://8.217.6.233:2048/v1/chat/completions"
headers = {
    "Authorization": "Bearer your-api-key",
    "Content-Type": "application/json"
}

def send_request(prompt):
    data = {
        "model": "gemini-1.5-flash-latest",
        "messages": [{"role": "user", "content": prompt}],
        "stream": False
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content']
    else:
        return f"Error: {response.status_code}"

# 批量提示
prompts = [
    "什么是人工智能？",
    "什么是机器学习？",
    "什么是深度学习？",
    "什么是神经网络？"
]

# 并发请求（注意：服务器有队列机制，会按顺序处理）
with ThreadPoolExecutor(max_workers=4) as executor:
    future_to_prompt = {executor.submit(send_request, prompt): prompt
                        for prompt in prompts}

    for future in as_completed(future_to_prompt):
        prompt = future_to_prompt[future]
        try:
            result = future.result()
            print(f"\n问题: {prompt}")
            print(f"回答: {result}\n")
        except Exception as e:
            print(f"请求失败: {prompt} - {e}")
```

### 对话历史管理

客户端负责维护完整的对话历史。

```python
import requests

class ChatSession:
    def __init__(self, api_key, base_url="http://8.217.6.233:2048/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.messages = []

    def add_system_message(self, content):
        self.messages.append({"role": "system", "content": content})

    def send_message(self, content, stream=False, **kwargs):
        self.messages.append({"role": "user", "content": content})

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "messages": self.messages,
            "stream": stream,
            **kwargs
        }

        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=data,
            stream=stream
        )

        if response.status_code == 200:
            if stream:
                return self._handle_stream(response)
            else:
                result = response.json()
                assistant_message = result['choices'][0]['message']['content']
                self.messages.append({"role": "assistant", "content": assistant_message})
                return assistant_message
        else:
            raise Exception(f"API Error: {response.status_code} - {response.text}")

    def _handle_stream(self, response):
        import json
        full_content = ""

        for line in response.iter_lines():
            if line:
                decoded = line.decode('utf-8')
                if decoded.startswith('data: '):
                    content = decoded[6:]
                    if content.strip() == '[DONE]':
                        break
                    try:
                        chunk = json.loads(content)
                        delta = chunk['choices'][0]['delta'].get('content', '')
                        full_content += delta
                        print(delta, end='', flush=True)
                    except:
                        pass

        print()  # 换行
        self.messages.append({"role": "assistant", "content": full_content})
        return full_content

    def clear_history(self, keep_system=True):
        if keep_system:
            self.messages = [msg for msg in self.messages if msg['role'] == 'system']
        else:
            self.messages = []

# 使用示例
session = ChatSession("your-api-key")
session.add_system_message("你是一个有帮助的AI助手。")

response1 = session.send_message("什么是量子计算？", model="gemini-1.5-pro-latest")
print(f"助手: {response1}\n")

response2 = session.send_message("它有什么实际应用？", model="gemini-1.5-pro-latest")
print(f"助手: {response2}\n")

# 查看完整对话历史
print("对话历史：")
for msg in session.messages:
    print(f"{msg['role']}: {msg['content'][:100]}...")
```

## 性能优化建议

1. **使用流式输出**：对于长文本生成，启用 `stream: true` 提供更好的用户体验
2. **合理设置 token 限制**：根据需求设置 `max_output_tokens`，避免不必要的长响应
3. **启用集成流式代理**：确保 `STREAM_PORT` 配置正确（默认 3120）
4. **使用适当的模型**：对于简单任务使用 `gemini-1.5-flash`，复杂任务使用 `gemini-1.5-pro`
5. **优化图片大小**：使用 `detail: "low"` 参数可以节省 token 和处理时间
6. **批量处理时控制并发**：虽然可以并发请求，但服务器队列会顺序处理

## 监控和调试

### 健康检查

```python
import requests

response = requests.get("http://8.217.6.233:2048/health")
health = response.json()

print(f"状态: {health['status']}")
print(f"Playwright 就绪: {health['playwright_ready']}")
print(f"浏览器连接: {health['browser_connected']}")
print(f"页面就绪: {health['page_ready']}")
print(f"Worker 运行: {health['worker_running']}")
print(f"队列长度: {health['queue_length']}")
```

### 获取模型列表

```python
import requests

response = requests.get("http://8.217.6.233:2048/v1/models")
models = response.json()

print("可用模型：")
for model in models['data']:
    print(f"- {model['id']}")
    if model.get('display_name'):
        print(f"  显示名称: {model['display_name']}")
    if model.get('injected'):
        print(f"  (注入模型)")
```

### 启用调试日志

在 `.env` 文件中：
```env
DEBUG_LOGS_ENABLED=true
TRACE_LOGS_ENABLED=true
SERVER_LOG_LEVEL=DEBUG
```

## 相关文档

- [安装指南](docs/installation-guide.md)
- [环境变量配置](docs/environment-configuration.md)
- [认证设置](docs/authentication-setup.md)
- [流式处理模式详解](docs/streaming-modes.md)
- [故障排除指南](docs/troubleshooting.md)
- [Web UI 使用指南](docs/webui-guide.md)

## 总结

AI Studio Proxy API 提供了完整的 OpenAI 兼容接口，支持：

1. 丰富的参数控制（temperature, max_tokens, top_p, stop, reasoning_effort 等）
2. 多种文件上传方式（data: URL, file://, 绝对路径, attachments 字段）
3. 流式和非流式响应
4. 工具调用（Google Search, 自定义函数）
5. 多模态输入（文本、图片、视频、音频、PDF 等）
6. 三层响应获取机制确保高可用性

通过本指南，你应该能够完全掌握 API 的使用方法。如有问题，请参考相关文档或查看服务器日志。
