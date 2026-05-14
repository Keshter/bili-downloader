"""
merger.py — 第4步：调用 ffmpeg 将视频流和音频流合并为 mp4 文件。

使用无损合并模式 (copy codec)，不做重新编码，速度很快。
需要系统已安装 ffmpeg 并添加到 PATH 环境变量中。

ffmpeg 下载地址: https://ffmpeg.org/download.html
"""

import os
import subprocess
import sys


def check_ffmpeg() -> bool:
    """
    检查系统是否安装了 ffmpeg。

    返回:
        bool: True 表示 ffmpeg 可用
    """
    try:
        # 在 Windows 上设置 CREATE_NO_WINDOW 避免弹出控制台窗口
        creationflags = 0
        if sys.platform == "win32":
            creationflags = subprocess.CREATE_NO_WINDOW  # type: ignore

        subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            creationflags=creationflags,
            timeout=5,
        )
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def merge_to_mp4(video_file: str, audio_file: str, output_file: str):
    """
    使用 ffmpeg 将视频文件和音频文件合并为一个 mp4 文件。

    参数:
        video_file:  视频流文件路径（.m4s 格式）
        audio_file:  音频流文件路径（.m4s 格式）
        output_file: 输出的 mp4 文件路径

    异常:
        FileNotFoundError: 输入文件不存在
        RuntimeError:      ffmpeg 执行失败

    返回:
        str: 合并后的输出文件路径
    """
    # 检查输入文件是否存在
    if not os.path.exists(video_file):
        raise FileNotFoundError(f"视频文件不存在: {video_file}")
    if not os.path.exists(audio_file):
        raise FileNotFoundError(f"音频文件不存在: {audio_file}")

    # 检查 ffmpeg 是否可用
    if not check_ffmpeg():
        raise RuntimeError(
            "未检测到 ffmpeg！请先安装 ffmpeg 并将其添加到系统 PATH 中。\n"
            "下载地址: https://ffmpeg.org/download.html\n"
            "安装后请重启终端，然后运行 'ffmpeg -version' 验证。"
        )

    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)

    # 构建 ffmpeg 命令
    # -i: 输入文件
    # -c:v copy: 视频流直接复制（不重新编码）
    # -c:a copy: 音频流直接复制（不重新编码）
    # -y: 覆盖已存在的输出文件
    cmd = [
        "ffmpeg",
        "-i", video_file,
        "-i", audio_file,
        "-c:v", "copy",
        "-c:a", "copy",
        "-y",             # 覆盖已有文件
        output_file,
    ]

    print(f"\n正在合并音视频...")
    print(f"  视频: {os.path.basename(video_file)}")
    print(f"  音频: {os.path.basename(audio_file)}")

    # 在 Windows 上隐藏 ffmpeg 的控制台窗口
    creationflags = 0
    if sys.platform == "win32":
        creationflags = subprocess.CREATE_NO_WINDOW  # type: ignore

    try:
        # 运行 ffmpeg，将输出重定向到管道
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            creationflags=creationflags,
            timeout=300,  # 5分钟超时
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError("合并超时（超过5分钟），请检查文件是否正常。")
    except FileNotFoundError:
        raise RuntimeError("未找到 ffmpeg，请确认已正确安装。")

    # 检查执行结果
    if result.returncode != 0:
        # ffmpeg 的错误信息在 stderr 中
        error_msg = result.stderr.strip().split("\n")[-1] if result.stderr else "未知错误"
        raise RuntimeError(f"ffmpeg 合并失败: {error_msg}")

    # 验证输出文件是否生成
    if not os.path.exists(output_file):
        raise RuntimeError(f"合并后未找到输出文件: {output_file}")

    output_size = os.path.getsize(output_file)
    size_mb = output_size / (1024 * 1024)
    print(f"合并完成！")
    print(f"  输出文件: {output_file}")
    print(f"  文件大小: {size_mb:.1f} MB")

    return output_file


def cleanup_temp_files(*files: str):
    """
    删除临时文件（视频流和音频流文件）。

    参数:
        files: 要删除的文件路径列表
    """
    for f in files:
        if os.path.exists(f):
            try:
                os.remove(f)
                print(f"  已删除临时文件: {os.path.basename(f)}")
            except OSError as e:
                print(f"  删除失败 {os.path.basename(f)}: {e}")


if __name__ == "__main__":
    # 简单测试
    print("ffmpeg 检查...")
    if check_ffmpeg():
        print("ffmpeg 可用！")
    else:
        print("ffmpeg 不可用，请先安装。")
