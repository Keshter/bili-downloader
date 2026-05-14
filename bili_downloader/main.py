"""
main.py — 程序入口（命令行版本）。

运行方法:
  python main.py           完整流程（下载+合并）
  python main.py step1     第1步：BV号提取
  python main.py step2     第2步：视频信息获取
  python main.py step3     第3步：视频下载
  python main.py step4     第4步：完整流程(下载+合并)
"""

import os
import sys
from parser import extract_bv
from api import get_video_info, print_video_info
from downloader import download_video_and_audio
from merger import merge_to_mp4, cleanup_temp_files, check_ffmpeg
import config


def step1_extract_bv():
    """第1步：接收用户输入，提取并验证BV号。"""
    print("=" * 50)
    print("B站视频下载器 — 第1步：BV号提取")
    print("=" * 50)
    print("输入 'q' 退出程序\n")

    while True:
        user_input = input("请输入B站视频链接或BV号: ").strip()

        if user_input.lower() == "q":
            print("程序退出。")
            sys.exit(0)

        if not user_input:
            print("输入为空，请重新输入。\n")
            continue

        try:
            bv = extract_bv(user_input)
            print(f"成功提取BV号: {bv}")
            print(f"  (下一步将根据此BV号获取视频信息)\n")
        except ValueError as e:
            print(f"提取失败: {e}\n")


def step2_video_info():
    """第2步：提取BV号后，调用API获取视频信息并显示。"""
    print("=" * 50)
    print("B站视频下载器 — 第2步：视频信息获取")
    print("=" * 50)
    print("输入 'q' 退出程序\n")

    while True:
        user_input = input("请输入B站视频链接或BV号: ").strip()

        if user_input.lower() == "q":
            print("程序退出。")
            sys.exit(0)

        if not user_input:
            print("输入为空，请重新输入。\n")
            continue

        try:
            bv = extract_bv(user_input)
            print(f"提取到BV号: {bv}")
        except ValueError as e:
            print(f"提取失败: {e}\n")
            continue

        try:
            print("正在获取视频信息...")
            info = get_video_info(bv)
            print_video_info(info)
        except Exception as e:
            print(f"获取视频信息失败: {e}\n")


def step3_download():
    """第3步：提取BV → 获取信息 → 下载（不含合并）。"""
    print("=" * 50)
    print("B站视频下载器 — 第3步：视频下载")
    print("=" * 50)
    print("输入 'q' 退出程序\n")

    while True:
        user_input = input("请输入B站视频链接或BV号: ").strip()

        if user_input.lower() == "q":
            print("程序退出。")
            sys.exit(0)

        if not user_input:
            print("输入为空，请重新输入。\n")
            continue

        try:
            bv = extract_bv(user_input)
            print(f"BV号: {bv}")
        except ValueError as e:
            print(f"提取失败: {e}\n")
            continue

        try:
            print("正在获取视频信息...")
            info = get_video_info(bv)
            print_video_info(info)
        except Exception as e:
            print(f"获取视频信息失败: {e}\n")
            continue

        pages = info.get("pages", [])
        if len(pages) == 0:
            print("该视频没有分P信息，无法下载。\n")
            continue

        if len(pages) == 1:
            selected_page = pages[0]
            print(f"单P视频，自动选择: {selected_page.get('part', 'P1')}")
        else:
            print(f"\n该视频有 {len(pages)} 个分P，请输入要下载的分P序号：")
            for i, page in enumerate(pages, start=1):
                print(f"  {i}. {page.get('part', 'N/A')} (cid={page.get('cid')})")
            try:
                choice = input(f"\n请选择 (1-{len(pages)}): ").strip()
                idx = int(choice) - 1
                if idx < 0 or idx >= len(pages):
                    print(f"序号超出范围 (1-{len(pages)})。\n")
                    continue
                selected_page = pages[idx]
            except (ValueError, IndexError):
                print("输入无效。\n")
                continue

        cid = selected_page["cid"]
        part_title = selected_page.get("part", "P1")
        video_title = info.get("title", bv)

        if len(pages) > 1:
            download_title = f"{video_title}_{part_title}"
        else:
            download_title = video_title

        try:
            download_video_and_audio(bv, cid, download_title)
            print()
        except Exception as e:
            print(f"下载失败: {e}\n")


def step4_full_flow():
    """
    完整流程：提取BV → 获取信息 → 下载 → ffmpeg合并 → 清理临时文件。
    """
    print("=" * 50)
    print("B站视频下载器 — 命令行完整版")
    print("=" * 50)

    # 启动时检查 ffmpeg
    if not check_ffmpeg():
        print("\n警告：未检测到 ffmpeg！")
        print("  下载完成后无法合并音视频。")
        print("  请访问 https://ffmpeg.org/download.html 下载安装。\n")

    print("输入 'q' 退出程序\n")

    while True:
        user_input = input("请输入B站视频链接或BV号: ").strip()

        if user_input.lower() == "q":
            print("程序退出。")
            sys.exit(0)

        if not user_input:
            print("输入为空，请重新输入。\n")
            continue

        # ---- 第1步：提取BV号 ----
        try:
            bv = extract_bv(user_input)
            print(f"\nBV号: {bv}")
        except ValueError as e:
            print(f"提取失败: {e}\n")
            continue

        # ---- 第2步：获取视频信息 ----
        try:
            print("正在获取视频信息...")
            info = get_video_info(bv)
            print_video_info(info)
        except Exception as e:
            print(f"获取视频信息失败: {e}\n")
            continue

        # ---- 分P选择 ----
        pages = info.get("pages", [])
        if len(pages) == 0:
            print("该视频没有分P信息，无法下载。\n")
            continue

        if len(pages) == 1:
            selected_page = pages[0]
            print(f"单P视频，自动选择: {selected_page.get('part', 'P1')}")
        else:
            print(f"\n该视频有 {len(pages)} 个分P：")
            for i, page in enumerate(pages, start=1):
                print(f"  {i}. {page.get('part', 'N/A')} (cid={page.get('cid')})")
            try:
                choice = input(f"\n请选择要下载的分P (1-{len(pages)}): ").strip()
                idx = int(choice) - 1
                if idx < 0 or idx >= len(pages):
                    print(f"序号超出范围 (1-{len(pages)})。\n")
                    continue
                selected_page = pages[idx]
            except (ValueError, IndexError):
                print("输入无效。\n")
                continue

        cid = selected_page["cid"]
        part_title = selected_page.get("part", "P1")
        video_title = info.get("title", bv)

        # 清理文件名中的非法字符
        safe_title = video_title.replace("/", "_").replace("\\", "_").replace(":", "_") \
                                .replace("*", "_").replace("?", "_").replace('"', "_") \
                                .replace("<", "_").replace(">", "_").replace("|", "_")

        if len(pages) > 1:
            safe_part = part_title.replace("/", "_").replace("\\", "_").replace(":", "_") \
                                  .replace("*", "_").replace("?", "_").replace('"', "_") \
                                  .replace("<", "_").replace(">", "_").replace("|", "_")
            safe_filename = f"{safe_title}_{safe_part}"
        else:
            safe_filename = safe_title

        # ---- 第3步：下载 ----
        try:
            video_file, audio_file = download_video_and_audio(bv, cid, safe_filename)
        except Exception as e:
            print(f"下载失败: {e}\n")
            continue

        # ---- 第4步：合并 ----
        output_file = os.path.join(config.DOWNLOAD_DIR, f"{safe_filename}.mp4")
        try:
            merge_to_mp4(video_file, audio_file, output_file)
            print(f"\n全部完成！最终文件: {output_file}\n")

            # 合并成功后删除临时 .m4s 文件
            cleanup_temp_files(video_file, audio_file)
        except Exception as e:
            print(f"合并失败: {e}")
            print("视频流和音频流文件已保留，你可以手动用 ffmpeg 合并：")
            print(f"  ffmpeg -i \"{video_file}\" -i \"{audio_file}\" -c copy \"{output_file}\"")
            print()

        print("-" * 50)


def run_gui():
    """启动GUI图形界面版本。"""
    from gui import run_gui as launch_gui
    launch_gui()


def print_usage():
    """打印使用说明。"""
    print("用法:")
    print("  python main.py           完整流程（默认CLI）")
    print("  python main.py gui       GUI图形界面模式")
    print("  python main.py step1     第1步：BV号提取")
    print("  python main.py step2     第2步：视频信息获取")
    print("  python main.py step3     第3步：视频下载")
    print("  python main.py step4     第4步：完整流程(下载+合并)")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        if mode == "gui":
            run_gui()
        elif mode == "step1":
            step1_extract_bv()
        elif mode == "step2":
            step2_video_info()
        elif mode == "step3":
            step3_download()
        elif mode == "step4":
            step4_full_flow()
        else:
            print(f"未知模式: {mode}\n")
            print_usage()
    else:
        # 默认运行命令行完整版
        step4_full_flow()
