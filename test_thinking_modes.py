#!/usr/bin/env python3
"""
思考模式测试脚本
测试三种核心场景：
1. 关闭思考模式
2. 开启思考并限制预算
3. 开启思考不限制预算
"""

import requests
import time
import sys
from typing import Optional

# API配置
API_BASE_URL = "http://localhost:12048"
CHAT_COMPLETION_ENDPOINT = f"{API_BASE_URL}/v1/chat/completions"


def test_request(scenario_name: str, reasoning_effort: Optional[any], description: str):
    """执行单个测试场景"""
    print("\n" + "=" * 80)
    print(f"场景: {scenario_name}")
    print("=" * 80)
    print(f"描述: {description}")
    print(f"reasoning_effort: {repr(reasoning_effort)}")
    print("=" * 80)

    payload = {
        "model": "gemini-flash-latest",
        "messages": [
            {
                "role": "user",
                "content": "请用一句话解释什么是量子纠缠。"
            }
        ],
        "temperature": 1.0,
        "max_output_tokens": 500,
        "stream": False,
    }

    # 只在不为 None 时才添加 reasoning_effort 参数
    if reasoning_effort is not None:
        payload["reasoning_effort"] = reasoning_effort

    print(f"\n发送请求...")

    try:
        start_time = time.time()

        response = requests.post(
            CHAT_COMPLETION_ENDPOINT,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=300
        )

        response.raise_for_status()
        end_time = time.time()
        total_time = end_time - start_time

        result = response.json()

        print(f"✅ 请求成功! 耗时: {total_time:.3f}秒")

        # 提取AI回复
        if "choices" in result and len(result["choices"]) > 0:
            ai_message = result["choices"][0]["message"]["content"]
            print(f"\nAI回复:")
            print("-" * 80)
            print(ai_message)
            print("-" * 80)

        # 输出使用信息
        if "usage" in result:
            usage = result["usage"]
            print(f"\nToken使用:")
            print(f"  输入: {usage.get('prompt_tokens', 'N/A')}")
            print(f"  输出: {usage.get('completion_tokens', 'N/A')}")
            print(f"  总计: {usage.get('total_tokens', 'N/A')}")

        return True

    except requests.exceptions.RequestException as e:
        print(f"❌ 请求失败: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"响应状态码: {e.response.status_code}")
            print(f"响应内容: {e.response.text}")
        return False
    except Exception as e:
        print(f"❌ 发生错误: {e}")
        return False


def main():
    """运行所有测试场景"""
    print("\n" + "=" * 80)
    print("思考模式重构 - 验收测试")
    print("=" * 80)
    print("测试三种核心场景，验证 reasoning_effort 参数处理逻辑")

    results = []

    # 场景1: 关闭思考模式
    print("\n\n" + "#" * 80)
    print("# 场景1: 关闭思考模式")
    print("#" * 80)

    results.append(("场景1a", test_request(
        "场景1a: 关闭思考（整数0）",
        0,
        "使用 reasoning_effort=0 明确关闭思考模式"
    )))

    time.sleep(2)  # 避免请求过快

    results.append(("场景1b", test_request(
        "场景1b: 关闭思考（字符串'0'）",
        "0",
        "使用 reasoning_effort='0' 明确关闭思考模式"
    )))

    # 场景2: 开启思考并限制预算
    print("\n\n" + "#" * 80)
    print("# 场景2: 开启思考并限制预算")
    print("#" * 80)

    time.sleep(2)

    results.append(("场景2a", test_request(
        "场景2a: 限制预算（预设值 medium）",
        "medium",
        "使用 reasoning_effort='medium' 开启思考并限制预算为 8000 tokens"
    )))

    time.sleep(2)

    results.append(("场景2b", test_request(
        "场景2b: 限制预算（具体数值 5000）",
        5000,
        "使用 reasoning_effort=5000 开启思考并限制预算为 5000 tokens"
    )))

    time.sleep(2)

    results.append(("场景2c", test_request(
        "场景2c: 限制预算（字符串数值 '3000'）",
        "3000",
        "使用 reasoning_effort='3000' 开启思考并限制预算为 3000 tokens"
    )))

    # 场景3: 开启思考不限制预算
    print("\n\n" + "#" * 80)
    print("# 场景3: 开启思考不限制预算")
    print("#" * 80)

    time.sleep(2)

    results.append(("场景3a", test_request(
        "场景3a: 不限制预算（字符串 'none'）",
        "none",
        "使用 reasoning_effort='none' 开启思考但不限制预算"
    )))

    time.sleep(2)

    results.append(("场景3b", test_request(
        "场景3b: 不限制预算（整数 -1）",
        -1,
        "使用 reasoning_effort=-1 开启思考但不限制预算"
    )))

    time.sleep(2)

    results.append(("场景3c", test_request(
        "场景3c: 不限制预算（字符串 '-1'）",
        "-1",
        "使用 reasoning_effort='-1' 开启思考但不限制预算"
    )))

    # 额外测试：默认配置
    print("\n\n" + "#" * 80)
    print("# 额外测试: 使用默认配置")
    print("#" * 80)

    time.sleep(2)

    results.append(("默认配置", test_request(
        "默认配置: 不指定 reasoning_effort",
        None,
        "不指定 reasoning_effort 参数，使用服务器默认配置"
    )))

    # 输出测试总结
    print("\n\n" + "=" * 80)
    print("测试总结")
    print("=" * 80)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {name}")

    print("\n" + "=" * 80)
    print(f"总计: {passed}/{total} 通过")
    print("=" * 80)

    if passed == total:
        print("\n🎉 所有测试通过！")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个测试失败")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
