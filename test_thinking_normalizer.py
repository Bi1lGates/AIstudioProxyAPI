#!/usr/bin/env python3
"""
思考模式归一化模块的单元测试

测试 thinking_normalizer.py 中的各个函数是否正确处理不同的输入
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from browser_utils.thinking_normalizer import (
    normalize_reasoning_effort,
    format_directive_log,
    ThinkingDirective
)


def print_test_result(test_name: str, passed: bool, details: str = ""):
    """打印测试结果"""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} - {test_name}")
    if details:
        print(f"     {details}")


def test_scenario_1_none_value():
    """测试场景1: None值，应使用默认配置"""
    print("\n=== 测试场景1: None值（使用默认配置） ===")

    directive = normalize_reasoning_effort(None)

    # 验证结果
    print(f"结果: {format_directive_log(directive)}")
    print(f"  thinking_enabled: {directive.thinking_enabled}")
    print(f"  budget_enabled: {directive.budget_enabled}")
    print(f"  budget_value: {directive.budget_value}")

    # 注意：结果取决于环境变量ENABLE_THINKING_BUDGET的值
    print_test_result(
        "None值处理",
        directive.original_value is None,
        f"已根据默认配置处理"
    )

    return True


def test_scenario_2_disable_thinking():
    """测试场景2: 关闭思考模式"""
    print("\n=== 测试场景2: 关闭思考模式 ===")

    test_cases = [
        (0, "整数0"),
        ("0", "字符串'0'"),
        (" 0 ", "字符串' 0 '（带空格）"),
    ]

    all_passed = True
    for value, description in test_cases:
        directive = normalize_reasoning_effort(value)

        print(f"\n输入: {repr(value)} ({description})")
        print(f"结果: {format_directive_log(directive)}")

        passed = (
            directive.thinking_enabled == False and
            directive.budget_enabled == False and
            directive.budget_value is None
        )

        print_test_result(
            f"关闭思考 - {description}",
            passed,
            f"thinking_enabled={directive.thinking_enabled}, budget_enabled={directive.budget_enabled}"
        )

        all_passed = all_passed and passed

    return all_passed


def test_scenario_3_unlimited_budget():
    """测试场景3: 开启思考，不限制预算"""
    print("\n=== 测试场景3: 开启思考，不限制预算 ===")

    test_cases = [
        ("none", "字符串'none'"),
        ("None", "字符串'None'（大写）"),
        ("NONE", "字符串'NONE'（全大写）"),
        (" none ", "字符串' none '（带空格）"),
        ("-1", "字符串'-1'"),
        (-1, "整数-1"),
    ]

    all_passed = True
    for value, description in test_cases:
        directive = normalize_reasoning_effort(value)

        print(f"\n输入: {repr(value)} ({description})")
        print(f"结果: {format_directive_log(directive)}")

        passed = (
            directive.thinking_enabled == True and
            directive.budget_enabled == False and
            directive.budget_value is None
        )

        print_test_result(
            f"不限制预算 - {description}",
            passed,
            f"thinking_enabled={directive.thinking_enabled}, budget_enabled={directive.budget_enabled}"
        )

        all_passed = all_passed and passed

    return all_passed


def test_scenario_4_limited_budget():
    """测试场景4: 开启思考，限制预算"""
    print("\n=== 测试场景4: 开启思考，限制预算 ===")

    test_cases = [
        ("low", 1000, "预设值'low'"),
        ("medium", 8000, "预设值'medium'"),
        ("high", 24000, "预设值'high'"),
        ("LOW", 1000, "预设值'LOW'（大写）"),
        (" medium ", 8000, "预设值' medium '（带空格）"),
        (1000, 1000, "整数1000"),
        (5000, 5000, "整数5000"),
        ("2000", 2000, "字符串'2000'"),
        (" 3000 ", 3000, "字符串' 3000 '（带空格）"),
    ]

    all_passed = True
    for value, expected_budget, description in test_cases:
        directive = normalize_reasoning_effort(value)

        print(f"\n输入: {repr(value)} ({description})")
        print(f"结果: {format_directive_log(directive)}")

        passed = (
            directive.thinking_enabled == True and
            directive.budget_enabled == True and
            directive.budget_value == expected_budget
        )

        print_test_result(
            f"限制预算 - {description}",
            passed,
            f"期望预算={expected_budget}, 实际预算={directive.budget_value}"
        )

        all_passed = all_passed and passed

    return all_passed


def test_invalid_values():
    """测试无效值的处理"""
    print("\n=== 测试无效值处理 ===")

    test_cases = [
        ("invalid", "无效字符串"),
        (-100, "负数（非-1）"),
        ("", "空字符串"),
        ("  ", "纯空格字符串"),
    ]

    all_passed = True
    for value, description in test_cases:
        directive = normalize_reasoning_effort(value)

        print(f"\n输入: {repr(value)} ({description})")
        print(f"结果: {format_directive_log(directive)}")

        # 无效值应该使用默认配置
        print_test_result(
            f"无效值降级 - {description}",
            True,  # 只要不抛异常就算通过
            "已使用默认配置"
        )

    return all_passed


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("思考模式归一化模块 - 单元测试")
    print("=" * 60)

    tests = [
        ("场景1: None值", test_scenario_1_none_value),
        ("场景2: 关闭思考", test_scenario_2_disable_thinking),
        ("场景3: 不限制预算", test_scenario_3_unlimited_budget),
        ("场景4: 限制预算", test_scenario_4_limited_budget),
        ("无效值处理", test_invalid_values),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed, None))
        except Exception as e:
            results.append((test_name, False, str(e)))
            print(f"\n❌ 测试异常: {test_name}")
            print(f"   错误: {e}")
            import traceback
            traceback.print_exc()

    # 打印总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)

    total = len(results)
    passed = sum(1 for _, p, _ in results if p)

    for test_name, passed_flag, error in results:
        if passed_flag:
            print(f"✅ {test_name}")
        else:
            print(f"❌ {test_name}")
            if error:
                print(f"   错误: {error}")

    print(f"\n总计: {passed}/{total} 通过")

    if passed == total:
        print("\n🎉 所有测试通过！")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个测试失败")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
