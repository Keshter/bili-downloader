"""
parser.py — 第1步：从各种B站链接中提取BV号。

支持以下输入格式：
  - 完整链接：https://www.bilibili.com/video/BV1xx411c7mD
  - 短链接：  https://b23.tv/xxxxx
  - 直接输入：BV1xx411c7mD
"""

import re


def extract_bv(user_input: str) -> str:
    """
    从用户输入的字符串中提取BV号。

    参数:
        user_input: 用户输入的链接或BV号

    返回:
        提取到的BV号字符串（如 "BV1xx411c7mD"）

    异常:
        ValueError: 当无法从输入中识别出有效的BV号时抛出
    """
    # 去除首尾空白字符
    user_input = user_input.strip()

    # 1. 优先检查是否直接就是BV号（以"BV"开头，后面是字母或数字，共12位）
    match = re.match(r"(BV[a-zA-Z0-9]{10})", user_input)
    if match:
        return match.group(1)

    # 2. 从标准链接中提取：bilibili.com/video/BV...
    match = re.search(r"bilibili\.com/video/(BV[a-zA-Z0-9]{10})", user_input)
    if match:
        return match.group(1)

    # 3. 如果都没匹配到，抛出错误
    raise ValueError(
        f"无法从输入中识别BV号，请检查链接格式。\n"
        f"你的输入: {user_input}\n"
        f"支持格式:\n"
        f"  - BV1xx411c7mD（直接输入BV号）\n"
        f"  - https://www.bilibili.com/video/BV1xx411c7mD/（完整链接）"
    )


def is_valid_bv(bv: str) -> bool:
    """
    检查一个字符串是否为合法的BV号格式。

    参数:
        bv: 待检查的字符串

    返回:
        是否为合法BV号
    """
    return bool(re.fullmatch(r"BV[a-zA-Z0-9]{10}", bv))


# 如果直接运行此文件，进入简单的交互测试模式
if __name__ == "__main__":
    print("=" * 50)
    print("BV号提取器 - 交互测试")
    print("=" * 50)
    print("支持输入: BV号 / 完整B站视频链接")
    print("输入 'q' 退出\n")

    while True:
        user_input = input("请输入: ").strip()
        if user_input.lower() == "q":
            print("退出。")
            break
        if not user_input:
            continue
        try:
            bv = extract_bv(user_input)
            print(f"  → 提取到的BV号: {bv}")
            print(f"  → 格式验证: {'通过' if is_valid_bv(bv) else '不通过'}")
        except ValueError as e:
            print(f"  ✗ 错误: {e}")
        print()
