"""
gui.py — 第6步：使用 PySide6 创建简单的图形界面。

包含：链接输入框、解析按钮、下载按钮、信息显示区、进度条。
"""

import os
import sys

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QProgressBar,
    QComboBox, QMessageBox, QGroupBox,
)
from PySide6.QtCore import QThread, Signal, Qt

from parser import extract_bv
from api import get_video_info
from downloader import download_file, get_stream_urls
from merger import merge_to_mp4, cleanup_temp_files, check_ffmpeg
import config


class DownloadWorker(QThread):
    """
    下载工作线程 — 在后台执行下载和合并，避免阻塞UI界面。

    通过信号(Signal)与主线程通信，更新进度和状态。
    """
    # 自定义信号
    log_signal = Signal(str)              # 日志信息
    progress_signal = Signal(int, str)    # 进度 (百分比, 描述)
    finished_signal = Signal(bool, str)   # 完成 (成功/失败, 消息)

    def __init__(self, bv: str, cid: int, video_title: str, part_title: str):
        super().__init__()
        self.bv = bv
        self.cid = cid
        self.video_title = video_title
        self.part_title = part_title

    def run(self):
        """在工作线程中执行下载和合并流程。"""
        try:
            # 清理文件名
            safe_title = self.video_title.replace("/", "_").replace("\\", "_") \
                .replace(":", "_").replace("*", "_").replace("?", "_") \
                .replace('"', "_").replace("<", "_").replace(">", "_").replace("|", "_")
            safe_part = self.part_title.replace("/", "_").replace("\\", "_") \
                .replace(":", "_").replace("*", "_").replace("?", "_") \
                .replace('"', "_").replace("<", "_").replace(">", "_").replace("|", "_")

            save_dir = config.DOWNLOAD_DIR
            os.makedirs(save_dir, exist_ok=True)

            # ---- 获取流地址 ----
            self.log_signal.emit("正在获取下载地址...")
            self.progress_signal.emit(5, "获取下载地址...")
            video_url, audio_url = get_stream_urls(self.bv, self.cid)

            # ---- 下载视频流 ----
            self.log_signal.emit("正在下载视频流...")
            self.progress_signal.emit(10, "下载视频流...")

            video_file = os.path.join(save_dir, f"{safe_title}_{safe_part}_video.m4s")
            self._download_with_progress(video_url, video_file, "视频流", 10, 50)

            # ---- 下载音频流 ----
            self.log_signal.emit("正在下载音频流...")
            self.progress_signal.emit(55, "下载音频流...")

            audio_file = os.path.join(save_dir, f"{safe_title}_{safe_part}_audio.m4s")
            self._download_with_progress(audio_url, audio_file, "音频流", 55, 90)

            # ---- 合并 ----
            self.log_signal.emit("正在合并音视频...")
            self.progress_signal.emit(92, "合并中...")

            output_file = os.path.join(save_dir, f"{safe_title}_{safe_part}.mp4")
            merge_to_mp4(video_file, audio_file, output_file)

            # 清理临时文件
            cleanup_temp_files(video_file, audio_file)

            self.progress_signal.emit(100, "完成！")
            self.log_signal.emit(f"下载完成: {output_file}")

            self.finished_signal.emit(True, f"下载成功！\n文件保存在:\n{output_file}")

        except Exception as e:
            self.log_signal.emit(f"错误: {e}")
            self.finished_signal.emit(False, f"下载失败: {e}")

    def _download_with_progress(self, url: str, filepath: str, label: str,
                                 start_pct: int, end_pct: int):
        """
        下载文件并报告进度。

        参数:
            url:        下载地址
            filepath:   保存路径
            label:      进度描述
            start_pct:  开始时的进度百分比
            end_pct:    结束时的进度百分比
        """
        import requests

        resp = requests.get(url, headers=config.get_headers(), stream=True, timeout=30)
        resp.raise_for_status()
        total_size = int(resp.headers.get("content-length", 0))

        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)

        downloaded = 0
        with open(filepath, "wb") as f:
            for chunk in resp.iter_content(chunk_size=config.CHUNK_SIZE):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        # 在当前阶段的范围内计算百分比
                        phase_pct = downloaded / total_size
                        overall_pct = start_pct + int(phase_pct * (end_pct - start_pct))
                        self.progress_signal.emit(
                            overall_pct,
                            f"{label} ({downloaded / (1024*1024):.1f} MB)"
                            if total_size > 1024 * 1024
                            else f"{label} ({downloaded / 1024:.1f} KB)"
                        )


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.video_info = None       # 保存当前解析的视频信息
        self.selected_page = None    # 当前选中的分P

        self.setWindowTitle("B站视频下载器")
        self.setMinimumSize(600, 500)

        # 创建中心部件和主布局
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(10)

        # ---- 输入区域 ----
        input_group = QGroupBox("视频链接")
        input_layout = QHBoxLayout(input_group)

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("输入B站视频链接或BV号...")
        self.url_input.returnPressed.connect(self.on_parse)  # 回车触发解析

        self.parse_btn = QPushButton("解析")
        self.parse_btn.clicked.connect(self.on_parse)

        input_layout.addWidget(self.url_input)
        input_layout.addWidget(self.parse_btn)
        layout.addWidget(input_group)

        # ---- 信息显示区域 ----
        info_group = QGroupBox("视频信息")
        info_layout = QVBoxLayout(info_group)

        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setMaximumHeight(150)
        self.info_text.setPlaceholderText("解析视频信息后将显示在这里...")

        info_layout.addWidget(self.info_text)
        layout.addWidget(info_group)

        # ---- 分P选择 ----
        page_group = QGroupBox("分P选择")
        page_layout = QHBoxLayout(page_group)

        page_layout.addWidget(QLabel("选择分P:"))
        self.page_combo = QComboBox()
        self.page_combo.setEnabled(False)
        page_layout.addWidget(self.page_combo)
        page_layout.addStretch()

        layout.addWidget(page_group)

        # ---- 进度条 ----
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("就绪")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        # ---- 下载按钮 ----
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.download_btn = QPushButton("下载")
        self.download_btn.setMinimumWidth(120)
        self.download_btn.setEnabled(False)  # 解析成功后才能下载
        self.download_btn.clicked.connect(self.on_download)

        btn_layout.addWidget(self.download_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # ---- 日志区域 ----
        log_group = QGroupBox("运行日志")
        log_layout = QVBoxLayout(log_group)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(120)
        self.log_text.setPlaceholderText("运行日志...")

        log_layout.addWidget(self.log_text)
        layout.addWidget(log_group)

        # 初始化状态
        self.worker = None

        # 检查 ffmpeg
        if not check_ffmpeg():
            self.log("警告: 未检测到 ffmpeg，下载后可能无法合并。")

    def log(self, msg: str):
        """向日志区域追加一条消息。"""
        self.log_text.append(msg)

    def on_parse(self):
        """点击"解析"按钮：提取BV号 → 获取视频信息。"""
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "提示", "请输入视频链接或BV号。")
            return

        # 第1步：提取BV号
        try:
            bv = extract_bv(url)
        except ValueError as e:
            QMessageBox.warning(self, "解析失败", str(e))
            return

        # 第2步：获取视频信息
        self.parse_btn.setEnabled(False)
        self.parse_btn.setText("解析中...")
        self.status_label.setText("正在获取视频信息...")
        self.log(f"正在获取 {bv} 的视频信息...")

        try:
            info = get_video_info(bv)
            self.video_info = info
            self._display_info(info)
            self.log("视频信息获取成功。")
            self.status_label.setText(f"解析成功: {info.get('title', '')}")

            # 启用下载按钮
            self.download_btn.setEnabled(True)

        except Exception as e:
            QMessageBox.warning(self, "获取失败", str(e))
            self.log(f"获取失败: {e}")
            self.status_label.setText("获取失败")
        finally:
            self.parse_btn.setEnabled(True)
            self.parse_btn.setText("解析")

    def _display_info(self, info: dict):
        """将视频信息显示在界面中。"""
        lines = []
        lines.append(f"标题: {info.get('title', 'N/A')}")
        lines.append(f"BV号: {info.get('bvid', 'N/A')}")
        lines.append(f"UP主: {info.get('owner', {}).get('name', 'N/A')}")

        desc = info.get("desc", "")
        if desc:
            desc_preview = desc[:80] + ("..." if len(desc) > 80 else "")
            lines.append(f"简介: {desc_preview}")

        pages = info.get("pages", [])
        lines.append(f"分P数量: {len(pages)}")

        self.info_text.setPlainText("\n".join(lines))

        # 更新分P下拉框
        self.page_combo.clear()
        for i, page in enumerate(pages):
            self.page_combo.addItem(f"P{i+1}: {page.get('part', 'N/A')}", page)
        self.page_combo.setEnabled(len(pages) > 1)

    def on_download(self):
        """点击"下载"按钮：启动后台线程下载。"""
        if self.video_info is None:
            return

        pages = self.video_info.get("pages", [])
        if not pages:
            QMessageBox.warning(self, "错误", "没有可下载的分P。")
            return

        # 获取选中的分P
        if self.page_combo.isEnabled() and self.page_combo.count() > 0:
            page_data = self.page_combo.currentData()
            if page_data:
                selected_page = page_data
            else:
                selected_page = pages[0]
        else:
            selected_page = pages[0]

        cid = selected_page["cid"]
        part_title = selected_page.get("part", "P1")
        video_title = self.video_info.get("title", "unknown")

        # 禁用按钮，防止重复点击
        self.download_btn.setEnabled(False)
        self.parse_btn.setEnabled(False)
        self.progress_bar.setValue(0)

        # 创建并启动工作线程
        self.worker = DownloadWorker(
            self.video_info["bvid"], cid, video_title, part_title
        )
        self.worker.log_signal.connect(self.log)
        self.worker.log_signal.connect(lambda msg: self.status_label.setText(msg))
        self.worker.progress_signal.connect(self._on_progress)
        self.worker.finished_signal.connect(self._on_finished)
        self.worker.start()

    def _on_progress(self, value: int, desc: str):
        """更新进度条。"""
        self.progress_bar.setValue(value)
        self.status_label.setText(desc)

    def _on_finished(self, success: bool, message: str):
        """下载完成后的处理。"""
        self.download_btn.setEnabled(True)
        self.parse_btn.setEnabled(True)

        if success:
            QMessageBox.information(self, "完成", message)
        else:
            QMessageBox.warning(self, "下载失败", message)

        self.status_label.setText("就绪" if success else "失败")


def run_gui():
    """启动GUI应用程序。"""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # 使用 Fusion 风格，跨平台外观一致

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    run_gui()
