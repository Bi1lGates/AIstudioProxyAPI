#!/usr/bin/env python3
"""
AI Studio Proxy API 测试脚本
包含所有参数示例和图片上传功能
"""

import requests
import json
import base64
from typing import Optional, List

# =========================
# 配置区域 - 请根据实际情况修改
# =========================

# API 服务器地址
API_BASE_URL = "http://8.217.6.233:2048/v1"
# API_BASE_URL = "http://127.0.0.1:2048/v1"  # 本地测试用这个

# API 密钥（如果服务器需要认证）
API_KEY = "test1"  # 替换为你的实际密钥

# 图片路径（请修改为实际路径）
IMAGE_PATH = "/Users/liuyuan/Desktop/壁纸/wallhaven-761ogy.jpg"  # 修改这里！
# IMAGE_PATH = "/Users/username/Pictures/test.jpg"  # macOS 示例
# IMAGE_PATH = "C:/Users/username/Pictures/test.jpg"  # Windows 示例

# =========================
# 工具函数
# =========================

def encode_image(image_path: str) -> str:
    """
    将图片编码为 Base64 字符串

    Args:
        image_path: 图片文件路径

    Returns:
        Base64 编码的字符串
    """
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except FileNotFoundError:
        print(f"错误：找不到图片文件 {image_path}")
        return None
    except Exception as e:
        print(f"编码图片时出错：{e}")
        return None


def get_mime_type(image_path: str) -> str:
    """
    根据文件扩展名获取 MIME 类型

    Args:
        image_path: 图片文件路径

    Returns:
        MIME 类型字符串
    """
    ext = image_path.lower().split('.')[-1]
    mime_types = {
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'gif': 'image/gif',
        'webp': 'image/webp',
        'bmp': 'image/bmp',
    }
    return mime_types.get(ext, 'image/jpeg')


# =========================
# 测试函数
# =========================

def test_non_streaming(include_image: bool = False):
    """
    测试非流式 API 调用

    Args:
        include_image: 是否包含图片
    """
    print("\n" + "="*60)
    print("测试 1: 非流式 API 调用（包含所有参数）")
    print("="*60)

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    # 构建消息内容
    if include_image:
        # 编码图片
        image_base64 = encode_image(IMAGE_PATH)
        if not image_base64:
            print("跳过图片测试（图片文件不存在）")
            include_image = False

    if include_image:
        # 包含图片的消息
        messages = [
            {
                "role": "system",
                "content": "你是一个有帮助的AI助手，擅长分析图片和回答问题。"
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "请详细描述这张图片的内容，包括主要元素、颜色、氛围等。"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{get_mime_type(IMAGE_PATH)};base64,{image_base64}",
                            "detail": "high"  # 可选: "auto", "low", "high"
                        }
                    }
                ]
            }
        ]
    else:
        # 纯文本消息
        messages = [
            {
                "role": "system",
                "content": "你是一个有帮助的AI助手。请简洁明了地回答问题。"
            },
            {
                "role": "user",
                "content": "解释一下量子计算的基本原理，用简单的语言。"
            }
        ]

    # 完整的请求参数
    data = {
        "model": "gemini-flash-latest",
        "messages": messages,
        "stream": False,

        # 温度参数 (0-2)
        "temperature": 0.7,

        # 最大输出 token 数
        "max_output_tokens": 2000,

        # Top-p 采样参数 (0-1)
        "top_p": 0.9,

        # 停止序列（可选）
        "stop": ["\n\n---", "结束"],

        # 思考预算（可选）
        # 可以是字符串: "low", "medium", "high", "none"
        # 或整数: 1000, 8000, 24000 等
        "reasoning_effort": "0",

        # 随机种子（用于可重复生成，可选）
        # "seed": 42,

        # 响应格式（可选）
        # "response_format": {"type": "json_object"}
    }

    print(f"\n请求配置:")
    print(f"  - 模型: {data['model']}")
    print(f"  - 温度: {data['temperature']}")
    print(f"  - 最大token: {data['max_output_tokens']}")
    print(f"  - Top-p: {data['top_p']}")
    print(f"  - 思考预算: {data['reasoning_effort']}")
    print(f"  - 包含图片: {'是' if include_image else '否'}")

    try:
        print(f"\n发送请求到: {API_BASE_URL}/chat/completions")
        response = requests.post(
            f"{API_BASE_URL}/chat/completions",
            headers=headers,
            json=data,
            timeout=120  # 超时时间 120 秒
        )

        response.raise_for_status()
        result = response.json()

        print(f"\n✅ 请求成功!")
        print(f"\n助手回复:")
        print("-" * 60)
        print(result['choices'][0]['message']['content'])
        print("-" * 60)

        # 显示 token 使用情况
        if 'usage' in result:
            usage = result['usage']
            print(f"\nToken 使用情况:")
            print(f"  - 输入: {usage.get('prompt_tokens', 'N/A')}")
            print(f"  - 输出: {usage.get('completion_tokens', 'N/A')}")
            print(f"  - 总计: {usage.get('total_tokens', 'N/A')}")

        # 显示其他元数据
        print(f"\n响应元数据:")
        print(f"  - 请求ID: {result.get('id', 'N/A')}")
        print(f"  - 模型: {result.get('model', 'N/A')}")
        print(f"  - 结束原因: {result['choices'][0].get('finish_reason', 'N/A')}")

    except requests.exceptions.Timeout:
        print("\n❌ 错误：请求超时")
    except requests.exceptions.HTTPError as e:
        print(f"\n❌ HTTP 错误: {e.response.status_code}")
        try:
            error_detail = e.response.json()
            print(f"错误详情: {json.dumps(error_detail, indent=2, ensure_ascii=False)}")
        except:
            print(f"错误详情: {e.response.text}")
    except requests.exceptions.ConnectionError:
        print(f"\n❌ 错误：无法连接到服务器 {API_BASE_URL}")
        print("请检查:")
        print("  1. 服务器是否正在运行")
        print("  2. API_BASE_URL 配置是否正确")
        print("  3. 网络连接是否正常")
    except Exception as e:
        print(f"\n❌ 未知错误: {e}")


def test_streaming():
    """
    测试流式 API 调用
    """
    print("\n" + "="*60)
    print("测试 2: 流式 API 调用")
    print("="*60)

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "gemini-flash-latest",
        "messages": [
            {
                "role": "system",
                "content": "你是一个创意写作助手。"
            },
            {
                "role": "user",
                "content": "写一首关于秋天的短诗，4行即可。"
            }
        ],
        "stream": True,
        "temperature": 0.9,
        "max_output_tokens": 500,
    }

    print(f"\n请求配置:")
    print(f"  - 模型: {data['model']}")
    print(f"  - 温度: {data['temperature']}")
    print(f"  - 流式模式: 是")

    try:
        print(f"\n发送流式请求到: {API_BASE_URL}/chat/completions")
        response = requests.post(
            f"{API_BASE_URL}/chat/completions",
            headers=headers,
            json=data,
            stream=True,
            timeout=120
        )

        response.raise_for_status()

        print(f"\n✅ 流式响应开始:")
        print("-" * 60)

        for line in response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')

                if decoded_line.startswith('data: '):
                    content = decoded_line[6:]  # 移除 'data: ' 前缀

                    if content.strip() == '[DONE]':
                        print()
                        print("-" * 60)
                        print("✅ 流式输出完成")
                        break

                    try:
                        chunk = json.loads(content)
                        delta = chunk.get('choices', [{}])[0].get('delta', {})
                        text = delta.get('content', '')

                        if text:
                            print(text, end='', flush=True)

                    except json.JSONDecodeError as e:
                        print(f"\n⚠️ 解析 JSON 时出错: {content}")

    except requests.exceptions.Timeout:
        print("\n❌ 错误：请求超时")
    except requests.exceptions.HTTPError as e:
        print(f"\n❌ HTTP 错误: {e.response.status_code}")
        print(f"错误详情: {e.response.text}")
    except requests.exceptions.ConnectionError:
        print(f"\n❌ 错误：无法连接到服务器")
    except Exception as e:
        print(f"\n❌ 未知错误: {e}")


def test_with_google_search():
    """
    测试使用 Google Search 工具
    """
    print("\n" + "="*60)
    print("测试 3: 使用 Google Search 工具")
    print("="*60)

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "gemini-flash-latest",
        "messages": [
            {
                "role": "user",
                "content": "2024年巴黎奥运会的金牌榜前三名是哪些国家？"
            }
        ],
        "tools": [
            {
                "google_search_retrieval": {}
            }
        ],
        "stream": False,
        "temperature": 0.5,
        "max_output_tokens": 1000,
    }

    print(f"\n请求配置:")
    print(f"  - 模型: {data['model']}")
    print(f"  - 工具: Google Search")

    try:
        print(f"\n发送请求到: {API_BASE_URL}/chat/completions")
        response = requests.post(
            f"{API_BASE_URL}/chat/completions",
            headers=headers,
            json=data,
            timeout=120
        )

        response.raise_for_status()
        result = response.json()

        print(f"\n✅ 请求成功!")
        print(f"\n助手回复:")
        print("-" * 60)
        print(result['choices'][0]['message']['content'])
        print("-" * 60)

    except Exception as e:
        print(f"\n❌ 错误: {e}")


def test_health():
    """
    测试服务器健康状态
    """
    print("\n" + "="*60)
    print("测试 0: 服务器健康检查")
    print("="*60)

    try:
        # 健康检查不需要认证
        response = requests.get(f"{API_BASE_URL.replace('/v1', '')}/health", timeout=10)
        response.raise_for_status()

        health = response.json()
        print(f"\n✅ 服务器状态: {health.get('status', 'unknown')}")
        print(f"\n详细信息:")
        print(f"  - Playwright 就绪: {health.get('playwright_ready', False)}")
        print(f"  - 浏览器连接: {health.get('browser_connected', False)}")
        print(f"  - 页面就绪: {health.get('page_ready', False)}")
        print(f"  - Worker 运行: {health.get('worker_running', False)}")
        print(f"  - 队列长度: {health.get('queue_length', 0)}")

        return True

    except Exception as e:
        print(f"\n❌ 无法连接到服务器: {e}")
        print(f"\n请检查:")
        print(f"  - 服务器地址: {API_BASE_URL}")
        print(f"  - 服务器是否正在运行")
        return False


# =========================
# 主函数
# =========================

def main():
    """
    主测试函数
    """
    print("\n" + "="*60)
    print("AI Studio Proxy API 测试脚本")
    print("="*60)
    print(f"\nAPI 服务器: {API_BASE_URL}")
    print(f"API 密钥: {API_KEY[:8]}****{API_KEY[-4:] if len(API_KEY) > 12 else '****'}")

    # # 测试 0: 健康检查
    # if not test_health():
    #     print("\n⚠️ 服务器健康检查失败，终止测试")
    #     return

    # 测试 1: 非流式调用（纯文本）
    test_non_streaming(include_image=False)

    # 测试 1b: 非流式调用（包含图片）
    import os
    if os.path.exists(IMAGE_PATH):
        test_non_streaming(include_image=True)
    else:
        print(f"\n⚠️ 跳过图片测试（图片路径不存在: {IMAGE_PATH}）")
        print("请修改脚本中的 IMAGE_PATH 变量为实际图片路径")

    # 测试 2: 流式调用
    test_streaming()

    # 测试 3: Google Search
    test_with_google_search()

    print("\n" + "="*60)
    print("所有测试完成！")
    print("="*60)


if __name__ == "__main__":
    # 检查配置
    if API_KEY == "your-api-key-here":
        print("\n⚠️ 警告：请先修改脚本中的 API_KEY 变量")
        print("如果服务器不需要认证，可以忽略此警告\n")

    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断测试")
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
