"""
downloader.py — 第3/5步：获取视频/音频流地址并下载，显示进度条。

B站使用DASH格式，视频和音频是分开的.m4s文件，需要分别下载后合并。
"""

import os
import requests
import config
from tqdm import tqdm


def get_stream_urls(bv: str, cid: int):
    """
    获取视频和音频流的下载地址。

    参数:
        bv:  BV号
        cid: 视频分P的cid

    返回:
        tuple: (video_url, audio_url)
            video_url: 最高画质视频流地址
            audio_url: 最高音质音频流地址

    异常:
        requests.RequestException: 网络请求失败
        ValueError: 无法获取流地址（可能需要登录或视频受限）
    """
    params = {
        "bvid": bv,
        "cid": cid,
        "qn": 80,         # 请求最高画质
        "fnval": 4048,    # DASH格式（4048 = 支持多种编码）
        "fnver": 0,
        "fourk": 1,
    }

    try:
        resp = requests.get(config.PLAYER_API, params=params, headers=config.get_headers(), timeout=10)
        resp.raise_for_status()
    except requests.RequestException as e:
        raise requests.RequestException(f"获取视频流信息失败: {e}")

    data = resp.json()
    if data.get("code") != 0:
        msg = data.get("message", "未知错误")
        raise ValueError(f"API返回错误 (code={data.get('code')}): {msg}")

    dash = data["data"].get("dash")
    if not dash:
        raise ValueError("该视频不支持DASH格式下载，可能为受限内容。")

    videos = dash.get("video", [])
    audios = dash.get("audio", [])

    if not videos:
        raise ValueError("未找到可下载的视频流。")
    if not audios:
        raise ValueError("未找到可下载的音频流。")

    # 按带宽(bandwidth)排序，选择最高画质/音质
    best_video = max(videos, key=lambda v: v.get("bandwidth", 0))
    best_audio = max(audios, key=lambda a: a.get("bandwidth", 0))

    # base_url 和 baseUrl 两种键名都可能出现
    video_url = best_video.get("base_url") or best_video.get("baseUrl")
    audio_url = best_audio.get("base_url") or best_audio.get("baseUrl")

    if not video_url or not audio_url:
        raise ValueError("无法提取视频/音频流地址。")

    # 打印流信息
    video_codec = best_video.get("codecs", "未知")
    video_size = f"{best_video.get('width', '?')}x{best_video.get('height', '?')}"
    audio_codec = best_audio.get("codecs", "未知")

    print(f"视频流: {video_size}, 编码={video_codec}")
    print(f"音频流: 编码={audio_codec}")

    return video_url, audio_url


def download_file(url: str, filepath: str, desc: str = "下载中"):
    """
    下载文件并显示进度条。

    参数:
        url:      下载地址
        filepath: 保存到本地的文件路径
        desc:     进度条前面的描述文字

    异常:
        requests.RequestException: 下载失败
    """
    # 如果上级目录不存在，先创建
    os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)

    # 发送GET请求，stream=True 表示流式下载（边下边存，不占内存）
    try:
        resp = requests.get(
            url,
            headers=config.get_headers(),
            stream=True,
            timeout=30,
        )
        resp.raise_for_status()
    except requests.RequestException as e:
        raise requests.RequestException(f"下载失败: {e}")

    # 获取文件总大小（如果服务器提供了 Content-Length 头）
    total_size = int(resp.headers.get("content-length", 0))

    # 使用 tqdm 显示下载进度条
    with open(filepath, "wb") as f:
        with tqdm(
            total=total_size,
            unit="B",          # 单位：字节
            unit_scale=True,   # 自动转换为 KB/MB/GB
            unit_divisor=1024,
            desc=desc,
            ncols=80,          # 进度条宽度
        ) as pbar:
            for chunk in resp.iter_content(chunk_size=config.CHUNK_SIZE):
                if chunk:
                    f.write(chunk)
                    pbar.update(len(chunk))

    # 下载完成后显示文件大小
    if total_size > 0:
        size_mb = total_size / (1024 * 1024)
        print(f"  已保存: {filepath} ({size_mb:.1f} MB)")
    else:
        actual_size = os.path.getsize(filepath)
        size_mb = actual_size / (1024 * 1024)
        print(f"  已保存: {filepath} ({size_mb:.1f} MB)")


def download_video_and_audio(bv: str, cid: int, title: str, save_dir: str = None):
    """
    下载视频的视频流和音频流。

    参数:
        bv:       BV号
        cid:      视频分P的cid
        title:    视频标题（用于生成文件名）
        save_dir: 保存目录，默认使用 config.DOWNLOAD_DIR

    返回:
        tuple: (video_filepath, audio_filepath)
    """
    if save_dir is None:
        save_dir = config.DOWNLOAD_DIR

    # 清理文件名中的非法字符（Windows不允许这些字符出现在文件名中）
    safe_title = title.replace("/", "_").replace("\\", "_").replace(":", "_") \
                      .replace("*", "_").replace("?", "_").replace('"', "_") \
                      .replace("<", "_").replace(">", "_").replace("|", "_")

    print(f"\n正在获取 {safe_title} 的下载地址...")
    video_url, audio_url = get_stream_urls(bv, cid)

    # 生成文件路径
    video_file = os.path.join(save_dir, f"{safe_title}_video.m4s")
    audio_file = os.path.join(save_dir, f"{safe_title}_audio.m4s")

    # 下载视频流
    print(f"\n[1/2] 下载视频流...")
    download_file(video_url, video_file, desc="视频流")

    # 下载音频流
    print(f"\n[2/2] 下载音频流...")
    download_file(audio_url, audio_file, desc="音频流")

    print(f"\n下载完成！")
    print(f"  视频文件: {video_file}")
    print(f"  音频文件: {audio_file}")
    print(f"  (下一步需要用 ffmpeg 合并两个文件为 mp4)")

    return video_file, audio_file


if __name__ == "__main__":
    # 简单交互测试：用已知的公开视频测试下载
    print("下载器 - 交互测试\n")
    bv = input("请输入BV号: ").strip()
    cid_str = input("请输入cid: ").strip()
    if bv and cid_str:
        try:
            cid = int(cid_str)
            download_video_and_audio(bv, cid, f"test_{bv}")
        except Exception as e:
            print(f"下载失败: {e}")
