# 思考开关与预算逻辑改造计划

## 目标概述
- 仅基于 OpenAI 请求中的 `reasoning_effort` 字段驱动思考/预算的控制逻辑。
- 明确三种用户意图：关闭思考、开启且限定预算、开启且不限制预算，并在网页端稳定实现对应操作。
- 提升容错能力：应对不同模型下开关缺失或禁用的场景，提供降级策略与清晰日志。

## 需求拆解
1. **API 请求侧**
   - 继续使用单一的 `reasoning_effort` 字段作为入口，兼容字符串/数字/`None` 等取值。
   - 建立参数归一化模块：根据 `reasoning_effort` 与默认配置推导出标准化指令（`thinking_enabled`、`budget_enabled`、`budget_value`、是否受限等）。
   - 在 `api_utils/request_processor.py` 中调用归一化模块，确保传入 `PageController.adjust_parameters` 的 `request_params` 已包含整理后的思考指令（可作为临时字段，如 `_thinking_directive`）。

2. **配置与选择器**
   - 在 `config/selectors.py` 中新增主思考开关选择器（示例：`ENABLE_THINKING_TOGGLE_SELECTOR = '[data-test-toggle="enable-thinking"] button'`），保留现有 `manual-budget` 相关选择器。
   - 如需额外 DOM 元素判断（例如提示气泡、禁用状态），提前定义，避免硬编码。

3. **页面控制逻辑**
   - `browser_utils/page_controller.py` 需引入新的主开关选择器，并新增 `_control_thinking_mode_toggle` 方法，保证：
     - 可以读取当前 `aria-checked` 状态；
     - 根据期望状态执行点击/等待 UI 刷新；
   - 重构 `_handle_thinking_budget`，按照标准化指令分支：
     1. **开启 + 受限预算（如具体数字或 `low|medium|high`）**  
        - 确保主开关开启，若关闭则先点开。  
        - 确保预算开关开启（可见 `manual-budget` toggle）。  
        - 等待输入框出现后填入预算值，并进行二次读取验证。
     2. **开启 + 不限制预算（`reasoning_effort = "none"` / `"-1"` / `-1`）**  
        - 确保主开关开启。  
        - 若预算开关当前开启，则点击关闭（网页即代表无限制）。  
     3. **关闭思考（`reasoning_effort = 0` 或 `"0"`）**  
        - 尝试关闭主开关，若成功则直接返回。  
        - 如果主开关在当前模型上被锁定为开启：  
          - 启用预算开关；  
          - 在输入框填入 `0`，交由页面自动调整到最小值，并记录该降级路径。
   - 更新日志信息：清晰记录每次状态变化、失败原因、降级策略触发点。
   - 当开关状态发生变化时，清理 `page_params_cache` 中与思考相关的缓存，避免下次错误跳过。

4. **异常与兼容性处理**
   - 对于主开关或预算开关不存在的模型，编写保护逻辑：记录说明性日志，跳过设置步骤，避免抛出致命异常。

5. **测试与示例**
   - 在 `test_text_only.py` 等脚本中新增/更新示例：  
     - 关闭思考 (`reasoning_effort = "0"` 或 `"0"` 字符串)；  
     - 开启 + 限定预算 (`reasoning_effort = "medium"`、`"high"`、`8000` 等)；  
     - 开启 + 不限制预算 (`reasoning_effort = "none"`、`"-1"`、`-1`)。
   - 确认数字与字符串形式均被正确解析，并在日志中打印解析结果。

6. **文档与维护**
   - 在根级 README 中补充 `reasoning_effort` 的取值说明：  
     - `0` → 关闭思考；  
     - 正数或 `low|medium|high` → 开启思考并限制预算；  
     - `none` / `-1` → 开启思考但不限制预算。  
   - 若存在外部集成（如 GUI Launcher），同步更新提示与默认选项。

## 实施顺序建议
1. 补齐选择器与数据模型（Pydantic）。  
2. 编写参数归一化模块并在请求流中串联。  
3. 重构 `PageController` 的相关方法，先实现主开关逻辑，再集成预算开关与输入框处理。  
4. 调整测试脚本与 README，验证三种核心场景。  
5. 最终回归测试：手动或半自动发起不同组合请求，观察日志与页面行为，确认无回归。

## 验收标准
- 三类意图都能稳定实现，重复调用不会因开关状态异常而失败。
- 不同类型的 `reasoning_effort` 取值均能获得预期行为，并记录清晰日志。
- 发生页面异常时能自动截图且不中断其他参数设置流程。
- 代码结构清晰，后续扩展（如新增思考模式选项）无需大规模重写。
