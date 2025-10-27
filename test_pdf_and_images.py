#!/usr/bin/env python3
"""
测试脚本3: PDF+图片调用
展示如何上传PDF和图片文件
"""

import requests
import json
import base64
import os
import time

# API配置
API_BASE_URL = "http://localhost:12048"
CHAT_COMPLETION_ENDPOINT = f"{API_BASE_URL}/v1/chat/completions"

# ========== 文件路径配置 ==========
# 请修改为你的实际文件路径
PDF_PATHS = [
    "/path/to/your/document1.pdf",
    "/path/to/your/document2.pdf",
    # 可以添加更多PDF路径
]

IMAGE_PATHS = [
    "/path/to/your/image1.jpg",
    "/path/to/your/image2.png",
    # 可以添加更多图片路径
]

def encode_file_to_base64(file_path):
    """将文件编码为base64"""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")

    with open(file_path, 'rb') as file:
        return base64.b64encode(file.read()).decode('utf-8')

# 构建消息内容
message_content = [
    {
        "type": "text",
        "text": "请分析这些文档和图片的内容，并给出总结。"
    }
]

# 添加PDF文件
for pdf_path in PDF_PATHS:
    if os.path.exists(pdf_path):
        base64_pdf = encode_file_to_base64(pdf_path)

        message_content.append({
            "type": "image_url",  # PDF也使用image_url格式
            "image_url": {
                "url": f"data:application/pdf;base64,{base64_pdf}"
            }
        })
        print(f"✅ 已加载PDF: {pdf_path}")
    else:
        print(f"⚠️  PDF不存在，跳过: {pdf_path}")

# 添加图片文件
for image_path in IMAGE_PATHS:
    if os.path.exists(image_path):
        # 获取MIME类型
        ext = os.path.splitext(image_path)[1].lower()
        mime_map = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
        }
        mime_type = mime_map.get(ext, 'image/jpeg')

        # 编码图片
        base64_image = encode_file_to_base64(image_path)

        message_content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:{mime_type};base64,{base64_image}"
            }
        })
        print(f"✅ 已加载图片: {image_path}")
    else:
        print(f"⚠️  图片不存在，跳过: {image_path}")

# 请求配置
payload = {
    # ========== 必需参数 ==========
    "model": "gemini-2.5-flash",  # 支持PDF和图片的模型
    "messages": [
        {
            "role": "user",
            "content": message_content
        }
    ],

    # ========== 生成参数 ==========
    "temperature": 1.0,              # 温度 (0.0-2.0)
    "max_output_tokens": 8192,      # 最大输出token数（注意：是max_output_tokens，不是max_tokens）
    "top_p": 0.95,                  # Top-P采样 (0.0-1.0)
    "stop": [],                     # 停止序列

    # ========== 流式输出 ==========
    "stream": False,                 # 是否使用流式输出

    # ========== 高级参数 ==========
    # "reasoning_effort": "medium",  # 思考预算: "low" (1000), "medium" (8000), "high" (24000), 或直接数字
    # "reasoning_effort": 1000,      # 或直接指定token数量
    # "reasoning_effort": "none",    # 禁用思考预算（必须是字符串"none"）

    # ========== 工具配置 ==========
    # "tools": [                     # 启用Google搜索（动态控制，优先级高于环境变量）
    #     {
    #         "google_search_retrieval": {}
    #     }
    # ],
    # 注意：URL Context 不能通过 tools 控制，只能通过环境变量 ENABLE_URL_CONTEXT 控制

    # ========== 其他可选参数 ==========
    # "seed": 123,                   # 随机种子
    # "response_format": {"type": "text"},  # 响应格式
    # "tool_choice": "auto",         # 工具选择策略

    # ========== 多模态参数 ==========
    # 注意：PDF通常需要较大的max_output_tokens来容纳完整内容分析
    # 建议对于PDF设置较高的 max_output_tokens 值（如 65536）
}

print("=" * 80)
print("测试脚本3: PDF+图片调用")
print("=" * 80)
print(f"\n模型: {payload['model']}")
print(f"消息内容块数量: {len(message_content)}")
print(f"  - 文本块: 1")
print(f"  - PDF块: {len([c for c in message_content if 'application/pdf' in str(c)])}")
print(f"  - 图片块: {len([c for c in message_content if c.get('type') == 'image_url' and 'application/pdf' not in str(c)])}")
print("\n" + "=" * 80)
print("发送请求...\n")

try:
    # 记录开始时间
    start_time = time.time()
    first_token_time = None

    # 检查是否是流式请求
    is_stream = payload.get("stream", False)

    if is_stream:
        # 流式请求处理
        response = requests.post(
            CHAT_COMPLETION_ENDPOINT,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=300,
            stream=True
        )

        # 检查响应状态
        response.raise_for_status()

        print("✅ 开始接收流式响应...\n")

        full_content = ""
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    data_str = line_str[6:]
                    if data_str.strip() == '[DONE]':
                        break

                    try:
                        chunk_data = json.loads(data_str)
                        if "choices" in chunk_data and len(chunk_data["choices"]) > 0:
                            delta = chunk_data["choices"][0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                # 记录首token时间
                                if first_token_time is None:
                                    first_token_time = time.time()
                                full_content += content
                                print(content, end='', flush=True)
                    except json.JSONDecodeError:
                        pass

        print("\n")
        end_time = time.time()

        # 输出时间统计
        total_time = end_time - start_time
        print("\n" + "=" * 80)
        print("⏱️  时间统计:")
        print("=" * 80)
        if first_token_time:
            time_to_first_token = first_token_time - start_time
            print(f"首Token时间: {time_to_first_token:.3f}秒")
        print(f"总耗时: {total_time:.3f}秒")

    else:
        # 非流式请求处理
        response = requests.post(
            CHAT_COMPLETION_ENDPOINT,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=300
        )

        # 检查响应状态
        response.raise_for_status()

        # 记录结束时间
        end_time = time.time()
        total_time = end_time - start_time

        # 解析响应
        result = response.json()

        print("✅ 请求成功!")
        print("\n响应摘要:")
        print("=" * 80)
        print(f"模型: {result.get('model', 'N/A')}")
        print(f"使用Token: {result.get('usage', {})}")

        # 提取AI回复
        if "choices" in result and len(result["choices"]) > 0:
            ai_message = result["choices"][0]["message"]["content"]
            print("\n" + "=" * 80)
            print("AI回复:")
            print("=" * 80)
            print(ai_message)

        # 输出时间统计
        print("\n" + "=" * 80)
        print("⏱️  时间统计:")
        print("=" * 80)
        print(f"总耗时: {total_time:.3f}秒")

    print("\n" + "=" * 80)
    print("✅ 测试完成!")
    print("=" * 80)

except FileNotFoundError as e:
    print(f"❌ 文件错误: {e}")
except requests.exceptions.RequestException as e:
    print(f"❌ 请求失败: {e}")
    if hasattr(e, 'response') and e.response is not None:
        print(f"响应状态码: {e.response.status_code}")
        print(f"响应内容: {e.response.text}")
except Exception as e:
    print(f"❌ 发生错误: {e}")


# ========== 使用说明 ==========
"""
使用方法：
1. 修改上面的 PDF_PATHS 和 IMAGE_PATHS 为你的实际文件路径
2. 运行脚本: python test_pdf_and_images.py

支持的文件格式：
- PDF: .pdf
- 图片: .jpg, .jpeg, .png, .gif, .webp

参数说明：
- model: 模型ID，推荐使用支持多模态的模型
- temperature: 控制输出的随机性，0.0最确定，2.0最随机
- max_tokens: 最大输出token数，PDF内容较多时建议设置较大值
- top_p: Top-P采样参数，控制多样性
- stop: 停止序列，遇到这些文本时停止生成
- stream: 是否使用流式输出
- reasoning_effort: 思考预算（仅支持的模型有效）
- tools: 工具配置，如启用Google搜索

注意事项：
1. 文件大小限制：请确保文件不要太大，建议单个PDF < 10MB
2. Token限制：PDF内容会占用较多tokens，需要合理设置max_tokens
3. 超时设置：处理PDF可能需要较长时间，已设置300秒超时
"""
