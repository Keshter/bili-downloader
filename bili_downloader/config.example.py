"""
配置文件模板 — 复制为 config.py 后填写你的Cookie。

使用方法：
  1. 复制本文件 → 重命名为 config.py
  2. 在 COOKIE 中填入你的B站Cookie（获取方法见下方注释）
  3. 运行 python main.py
"""

# B站登录Cookie（从浏览器中复制）
# 不填只能下载低画质(480P)；填入后可下载登录用户能看到的最高画质(如1080P/4K)
# 获取方法：浏览器登录B站后，F12 → Application → Cookies → 复制完整Cookie字符串
COOKIE = ""

# 请求头：模拟浏览器访问，避免被服务器拒绝
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.bilibili.com/",
}


def get_headers() -> dict:
    """
    获取带Cookie的请求头（如果用户配置了Cookie则自动添加）。
    """
    headers = HEADERS.copy()
    if COOKIE:
        headers["Cookie"] = COOKIE
    return headers


# B站公开API地址
API_URL = "https://api.bilibili.com/x/web-interface/view"

# 视频流信息API（获取下载地址）
PLAYER_API = "https://api.bilibili.com/x/player/playurl"

# 下载保存目录（默认下载到当前目录下的 downloads 文件夹）
DOWNLOAD_DIR = "./downloads"

# 每个分块下载的大小（字节），用于显示进度
CHUNK_SIZE = 1024 * 1024  # 1MB
