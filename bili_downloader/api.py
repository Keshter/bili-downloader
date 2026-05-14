"""
api.py — 第2步：调用B站公开API获取视频基本信息。

公开API不需要登录即可访问：
  - 视频信息: https://api.bilibili.com/x/web-interface/view?bvid={bv}
  - 注意：此API只能获取公开视频信息，会员/付费内容会返回错误。
"""

import requests
import config


def get_video_info(bv: str):
    """
    根据BV号获取视频基本信息（标题、UP主、简介、分P信息等）。

    参数:
        bv: BV号字符串

    返回:
        dict: API返回的 data 字段，包含:
            - bvid: BV号
            - title: 视频标题
            - owner.name: UP主名称
            - desc: 视频简介
            - pages: 分P列表，每个元素包含 cid, part, duration 等

    异常:
        requests.RequestException: 网络请求失败
        ValueError: API返回错误（如视频不存在、视频为付费内容等）
    """
    # 构造请求参数
    params = {"bvid": bv}

    try:
        resp = requests.get(config.API_URL, params=params, headers=config.get_headers(), timeout=10)
        resp.raise_for_status()  # 如果HTTP状态码不是200，抛出异常
    except requests.RequestException as e:
        raise requests.RequestException(f"网络请求失败: {e}")

    # 解析JSON响应
    data = resp.json()

    # B站API返回格式: {"code": 0, "message": "0", "data": {...}}
    if data.get("code") != 0:
        msg = data.get("message", "未知错误")
        raise ValueError(f"API返回错误 (code={data.get('code')}): {msg}")

    return data["data"]


def print_video_info(info: dict):
    """
    将视频信息格式化输出到控制台（方便查看）。

    参数:
        info: get_video_info() 返回的数据字典
    """
    print("\n" + "=" * 50)
    print(f"视频标题: {info.get('title', 'N/A')}")
    print(f"BV号:     {info.get('bvid', 'N/A')}")
    print(f"AV号:     av{info.get('aid', 'N/A')}")

    # UP主信息
    owner = info.get("owner", {})
    print(f"UP主:     {owner.get('name', 'N/A')}")

    # 视频简介（截取前100个字符）
    desc = info.get("desc", "")
    if desc:
        desc_preview = desc[:100] + ("..." if len(desc) > 100 else "")
        print(f"简介:     {desc_preview}")

    # 播放/弹幕等统计
    stat = info.get("stat", {})
    print(f"播放量:   {stat.get('view', 'N/A')}")
    print(f"弹幕数:   {stat.get('danmaku', 'N/A')}")

    # 分P信息
    pages = info.get("pages", [])
    print(f"分P数量:  {len(pages)}")
    for i, page in enumerate(pages, start=1):
        print(f"  P{i}: {page.get('part', 'N/A')} "
              f"(cid={page.get('cid')}, "
              f"时长={page.get('duration', 'N/A')}秒)")
    print("=" * 50)


if __name__ == "__main__":
    # 简单交互测试：输入BV号查看视频信息
    print("视频信息查询 - 交互测试")
    while True:
        bv = input("\n请输入BV号 (输入q退出): ").strip()
        if bv.lower() == "q":
            break
        if not bv:
            continue
        try:
            info = get_video_info(bv)
            print_video_info(info)
        except Exception as e:
            print(f"获取失败: {e}")
