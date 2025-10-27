#!/usr/bin/env python3
"""
思考模式归一化模块的独立测试脚本
不依赖其他项目模块，直接测试核心逻辑
"""

from dataclasses import dataclass
from typing import Optional, Any

# 模拟配置
ENABLE_THINKING_BUDGET = False
DEFAULT_THINKING_BUDGET = 8192


@dataclass
class ThinkingDirective:
    """标准化的思考指令"""
    thinking_enabled: bool
    budget_enabled: bool
    budget_value: Optional[int]
    original_value: Any


def normalize_reasoning_effort(reasoning_effort: Optional[Any]) -> ThinkingDirective:
    """归一化 reasoning_effort 参数"""

    # 场景1: 用户未指定，使用默认配置
    if reasoning_effort is None:
        return ThinkingDirective(
            thinking_enabled=ENABLE_THINKING_BUDGET,
            budget_enabled=ENABLE_THINKING_BUDGET,
            budget_value=DEFAULT_THINKING_BUDGET if ENABLE_THINKING_BUDGET else None,
            original_value=None
        )

    # 场景2: 关闭思考模式
    if reasoning_effort == 0 or (isinstance(reasoning_effort, str) and reasoning_effort.strip() == "0"):
        return ThinkingDirective(
            thinking_enabled=False,
            budget_enabled=False,
            budget_value=None,
            original_value=reasoning_effort
        )

    # 场景3: 开启思考但不限制预算
    if isinstance(reasoning_effort, str):
        reasoning_str = reasoning_effort.strip().lower()
        if reasoning_str in ["none", "-1"]:
            return ThinkingDirective(
                thinking_enabled=True,
                budget_enabled=False,
                budget_value=None,
                original_value=reasoning_effort
            )
    elif reasoning_effort == -1:
        return ThinkingDirective(
            thinking_enabled=True,
            budget_enabled=False,
            budget_value=None,
            original_value=reasoning_effort
        )

    # 场景4: 开启思考且限制预算
    budget_value = _parse_budget_value(reasoning_effort)

    if budget_value is not None and budget_value > 0:
        return ThinkingDirective(
            thinking_enabled=True,
            budget_enabled=True,
            budget_value=budget_value,
            original_value=reasoning_effort
        )

    # 无效值：使用默认配置
    return ThinkingDirective(
        thinking_enabled=ENABLE_THINKING_BUDGET,
        budget_enabled=ENABLE_THINKING_BUDGET,
        budget_value=DEFAULT_THINKING_BUDGET if ENABLE_THINKING_BUDGET else None,
        original_value=reasoning_effort
    )


def _parse_budget_value(reasoning_effort: Any) -> Optional[int]:
    """解析预算值"""
    if isinstance(reasoning_effort, int) and reasoning_effort > 0:
        return reasoning_effort

    if isinstance(reasoning_effort, str):
        effort_str = reasoning_effort.strip().lower()
        effort_map = {
            "low": 1000,
            "medium": 8000,
            "high": 24000,
        }

        if effort_str in effort_map:
            return effort_map[effort_str]

        try:
            value = int(effort_str)
            if value > 0:
                return value
        except (ValueError, TypeError):
            pass

    return None


def format_directive_log(directive: ThinkingDirective) -> str:
    """格式化思考指令为日志字符串"""
    if not directive.thinking_enabled:
        return f"关闭思考模式 (原始值: {directive.original_value})"
    elif directive.budget_enabled and directive.budget_value is not None:
        return f"开启思考并限制预算: {directive.budget_value} tokens (原始值: {directive.original_value})"
    else:
        return f"开启思考，不限制预算 (原始值: {directive.original_value})"


def test_all_scenarios():
    """测试所有场景"""
    print("=" * 60)
    print("思考模式归一化 - 单元测试")
    print("=" * 60)

    test_cases = [
        # (输入值, 期望thinking_enabled, 期望budget_enabled, 期望budget_value, 描述)
        (None, False, False, None, "None值（默认配置关闭）"),
        (0, False, False, None, "整数0"),
        ("0", False, False, None, "字符串'0'"),
        (" 0 ", False, False, None, "字符串' 0 '（带空格）"),
        ("none", True, False, None, "字符串'none'"),
        ("None", True, False, None, "字符串'None'（大写）"),
        (" NONE ", True, False, None, "字符串' NONE '（带空格大写）"),
        ("-1", True, False, None, "字符串'-1'"),
        (-1, True, False, None, "整数-1"),
        ("low", True, True, 1000, "预设值'low'"),
        ("medium", True, True, 8000, "预设值'medium'"),
        ("high", True, True, 24000, "预设值'high'"),
        ("LOW", True, True, 1000, "预设值'LOW'（大写）"),
        (" medium ", True, True, 8000, "预设值' medium '（带空格）"),
        (1000, True, True, 1000, "整数1000"),
        (5000, True, True, 5000, "整数5000"),
        ("2000", True, True, 2000, "字符串'2000'"),
        (" 3000 ", True, True, 3000, "字符串' 3000 '（带空格）"),
    ]

    passed = 0
    failed = 0

    for value, exp_thinking, exp_budget, exp_value, description in test_cases:
        directive = normalize_reasoning_effort(value)

        # 检查结果
        success = (
            directive.thinking_enabled == exp_thinking and
            directive.budget_enabled == exp_budget and
            directive.budget_value == exp_value
        )

        status = "✅ PASS" if success else "❌ FAIL"

        print(f"\n{status} - {description}")
        print(f"  输入: {repr(value)}")
        print(f"  结果: {format_directive_log(directive)}")
        print(f"  期望: thinking={exp_thinking}, budget={exp_budget}, value={exp_value}")
        print(f"  实际: thinking={directive.thinking_enabled}, budget={directive.budget_enabled}, value={directive.budget_value}")

        if success:
            passed += 1
        else:
            failed += 1

    # 总结
    print("\n" + "=" * 60)
    print(f"测试总结: {passed}/{passed+failed} 通过")
    print("=" * 60)

    if failed == 0:
        print("\n🎉 所有测试通过！")
        return True
    else:
        print(f"\n⚠️  {failed} 个测试失败")
        return False


if __name__ == "__main__":
    success = test_all_scenarios()
    exit(0 if success else 1)
