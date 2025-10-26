#!/usr/bin/env python3
# patch_camoufox_proxy.py
# 自动修复 Camoufox 0.4.11 的 proxy=None 问题
# 修改 utils.py 中的 launch_options 函数，使其在 proxy 为 None 时不传递该键

import sys
import os

CAMOUFOX_UTILS_PATH = "/usr/local/lib/python3.10/site-packages/camoufox/utils.py"

def patch_camoufox_utils():
    """修复 Camoufox utils.py 的 proxy 处理逻辑"""
    try:
        print(f"正在检查文件: {CAMOUFOX_UTILS_PATH}")

        if not os.path.exists(CAMOUFOX_UTILS_PATH):
            print(f"❌ 文件未找到: {CAMOUFOX_UTILS_PATH}")
            print("   请确保 Camoufox 已正确安装。")
            return False

        with open(CAMOUFOX_UTILS_PATH, 'r', encoding='utf-8') as f:
            content = f.read()

        # 检查是否已经打过补丁
        if 'if proxy is not None:' in content and 'result["proxy"] = proxy' in content:
            print("✅ Camoufox utils.py 已经打过补丁，跳过修改。")
            return True

        # 查找 return 语句的位置
        # 寻找包含 "proxy": proxy 的 return 字典
        lines = content.split('\n')
        modified = False
        new_lines = []
        i = 0

        while i < len(lines):
            line = lines[i]

            # 查找包含 return { ... "proxy": proxy, ... } 的模式
            if 'return' in line and '{' in line:
                # 找到 return 语句的开始
                return_start = i
                brace_count = line.count('{') - line.count('}')
                return_end = i

                # 找到完整的 return 字典
                while brace_count > 0 and return_end < len(lines) - 1:
                    return_end += 1
                    brace_count += lines[return_end].count('{') - lines[return_end].count('}')

                # 检查这个 return 字典是否包含 "proxy": proxy
                return_block = '\n'.join(lines[return_start:return_end+1])

                if '"proxy": proxy' in return_block or '"proxy":proxy' in return_block:
                    print("找到需要修改的 return 语句")

                    # 提取缩进
                    indent = ' ' * (len(line) - len(line.lstrip()))

                    # 构建新的代码
                    new_lines.append(f'{indent}result = {{')

                    # 复制字典内容，但跳过 proxy 行
                    for j in range(return_start, return_end + 1):
                        dict_line = lines[j]
                        if j == return_start:
                            # 跳过 return { 行
                            continue
                        elif '"proxy": proxy' in dict_line or '"proxy":proxy' in dict_line:
                            # 跳过 proxy 行，但保留逗号（如果有的话，移到上一行）
                            continue
                        else:
                            # 移除最后的 }
                            if j == return_end:
                                dict_line = dict_line.replace('}', '').rstrip()
                                if dict_line.strip():
                                    new_lines.append(dict_line)
                            else:
                                new_lines.append(dict_line)

                    # 添加结束的 }
                    new_lines.append(f'{indent}}}')

                    # 添加条件判断
                    new_lines.append(f'{indent}# 只在 proxy 不为 None 时才添加')
                    new_lines.append(f'{indent}if proxy is not None:')
                    new_lines.append(f'{indent}    result["proxy"] = proxy')
                    new_lines.append(f'{indent}return result')

                    modified = True
                    i = return_end + 1
                    continue

            new_lines.append(line)
            i += 1

        if not modified:
            print("⚠️  未找到需要修改的代码模式。")
            print("   尝试使用简单替换方法...")

            # 备选方案：简单的字符串替换
            if '"proxy": proxy,' in content:
                content = content.replace(
                    '"proxy": proxy,',
                    ''
                )
                # 在 return 之前添加条件判断
                if 'return {' in content and 'launch_options if launch_options' in content:
                    # 找到包含这两个模式的位置
                    import re
                    pattern = r'(\s+)(\*\*\(\.\.\.launch_options if launch_options is not None else \{\}\)\s*\})'
                    replacement = r'\1\2\n\1if proxy is not None:\n\1    result["proxy"] = proxy\n\1return result'
                    content = re.sub(pattern, replacement, content)

                    # 替换 return { 为 result = {
                    content = re.sub(
                        r'return\s*\{(\s*"executable_path")',
                        r'result = {\1',
                        content
                    )

                    with open(CAMOUFOX_UTILS_PATH, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print("✅ 成功修复 Camoufox utils.py (使用备选方案)")
                    return True

            return False

        # 写回文件
        new_content = '\n'.join(new_lines)
        with open(CAMOUFOX_UTILS_PATH, 'w', encoding='utf-8') as f:
            f.write(new_content)

        print("✅ 成功修复 Camoufox utils.py 的 proxy 问题！")
        return True

    except Exception as e:
        print(f"❌ 修复失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Camoufox 0.4.11 Proxy 修复脚本")
    print("=" * 60)
    success = patch_camoufox_utils()
    print("=" * 60)
    sys.exit(0 if success else 1)
