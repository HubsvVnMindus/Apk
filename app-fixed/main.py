# -*- coding: utf-8 -*-
"""NOVA DARK Android shell for the existing TST-TOOL logic."""
import builtins
import io
import os
import queue
import re
import sys
import threading
import traceback

from kivy.app import App
from kivy.clock import Clock
from kivy.core.clipboard import Clipboard
from kivy.lang import Builder
from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout

ANSI_RE = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
input_queue  = queue.Queue()
output_queue = queue.Queue()
_original_input = builtins.input

KV = r"""
<NovaRoot>:
    orientation: "vertical"
    padding: dp(12)
    spacing: dp(8)
    canvas.before:
        Color:
            rgba: 0.025, 0.035, 0.075, 1
        Rectangle:
            pos: self.pos
            size: self.size

    # ── header ──────────────────────────────────────────────
    BoxLayout:
        size_hint_y: None
        height: dp(54)
        orientation: "vertical"
        Label:
            text: "[b]♛ TST-TOOL  /  NOVA DARK[/b]"
            markup: True
            color: 0.66, 0.55, 1, 1
            font_size: "20sp"
            halign: "left"
            text_size: self.size
        Label:
            text: "AI COMMAND SYSTEM  •  ANDROID"
            color: 0.48, 0.58, 0.72, 1
            font_size: "10sp"
            halign: "left"
            text_size: self.size

    # ── accent line ─────────────────────────────────────────
    BoxLayout:
        size_hint_y: None
        height: dp(2)
        canvas:
            Color:
                rgba: 0.48, 0.36, 1, 1
            Rectangle:
                pos: self.pos
                size: self.size

    # ── terminal output ─────────────────────────────────────
    TextInput:
        id: terminal
        text: root.log_text
        readonly: True
        multiline: True
        font_size: "12sp"
        foreground_color: 0.84, 0.88, 0.96, 1
        background_color: 0.04, 0.055, 0.11, 1
        padding: dp(10)
        size_hint_y: 1

    # ── input bar ───────────────────────────────────────────
    BoxLayout:
        size_hint_y: None
        height: dp(48)
        spacing: dp(8)
        TextInput:
            id: command
            hint_text: "Nhập lựa chọn / dữ liệu..."
            multiline: False
            size_hint_x: 1
            background_color: 0.08, 0.10, 0.18, 1
            foreground_color: 1, 1, 1, 1
            hint_text_color: 0.5, 0.56, 0.68, 1
            on_text_validate: root.submit()
        Button:
            text: "GỬI"
            size_hint_x: None
            width: dp(80)
            background_normal: ""
            background_color: 0.36, 0.25, 0.85, 1
            on_release: root.submit()

    # ── action buttons ───────────────────────────────────────
    BoxLayout:
        size_hint_y: None
        height: dp(42)
        spacing: dp(6)
        Button:
            text: "SAO CHÉP"
            background_normal: ""
            background_color: 0.08, 0.38, 0.32, 1
            on_release: root.copy_log()
        Button:
            text: "LƯU FILE"
            background_normal: ""
            background_color: 0.10, 0.28, 0.48, 1
            on_release: root.save_log()
        Button:
            text: "XÓA LOG"
            background_normal: ""
            background_color: 0.12, 0.16, 0.25, 1
            on_release: root.clear_log()
        Button:
            text: "DỪNG"
            background_normal: ""
            background_color: 0.52, 0.14, 0.22, 1
            on_release: root.send_stop()
"""


# ── QueueWriter ──────────────────────────────────────────────────────────────

class QueueWriter:
    """Chuyển stdout/stderr vào output_queue. Khởi tạo SAU khi Kivy init xong."""
    def write(self, value):
        if value:
            output_queue.put(str(value))
        return len(value or "")
    def flush(self):    pass
    def isatty(self):   return True
    def readable(self): return False
    def writable(self): return True
    def seekable(self): return False
    def fileno(self):   raise io.UnsupportedOperation("fileno")


# ── gui_input (thay builtins.input) ─────────────────────────────────────────

def gui_input(prompt=""):
    if prompt:
        output_queue.put(str(prompt))
    return input_queue.get()


# ── NovaRoot ─────────────────────────────────────────────────────────────────

class NovaRoot(BoxLayout):
    log_text = StringProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Clock.schedule_interval(self.drain_output, 0.12)

    # drain output_queue → terminal
    def drain_output(self, _dt):
        chunks = []
        while True:
            try:
                chunks.append(output_queue.get_nowait())
            except queue.Empty:
                break
        if chunks:
            cleaned = ANSI_RE.sub("", "".join(chunks))
            cleaned = cleaned.replace("\r", "")
            self.log_text = (self.log_text + cleaned)[-60000:]
            try:
                lines = self.ids.terminal.text.splitlines()
                if lines:
                    self.ids.terminal.cursor = (0, len(lines) - 1)
            except Exception:
                pass

    # gửi lệnh
    def submit(self):
        value = self.ids.command.text.strip()
        self.ids.command.text = ""
        input_queue.put(value)
        output_queue.put("\n› " + value + "\n")

    # sao chép toàn bộ log vào clipboard
    def copy_log(self):
        try:
            Clipboard.copy(self.log_text)
            output_queue.put("\n[APP] ✓ Đã sao chép log vào clipboard.\n")
        except Exception as e:
            output_queue.put(f"\n[APP] Lỗi sao chép: {e}\n")

    # lưu log ra file (nằm trong app storage, luôn có quyền ghi)
    def save_log(self):
        try:
            app  = App.get_running_app()
            path = os.path.join(app.user_data_dir, "nova_log.txt")
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.log_text)
            output_queue.put(f"\n[APP] ✓ Đã lưu log:\n      {path}\n")
        except Exception as e:
            output_queue.put(f"\n[APP] Lỗi lưu file: {e}\n")

    def clear_log(self):
        self.log_text = ""

    def send_stop(self):
        input_queue.put("q")
        output_queue.put("\n[APP] Đã gửi lệnh dừng.\n")


# ── TSTNovaApp ───────────────────────────────────────────────────────────────

class TSTNovaApp(App):

    def build(self):
        self.title = "TST-TOOL NOVA"
        try:
            Builder.load_string(KV)
            root = NovaRoot()
            Clock.schedule_once(lambda _dt: self._activate_io_and_start(), 0.5)
            return root
        except Exception:
            # Build fail → hiện lỗi ngay, vẫn có nút SAO CHÉP
            err_text = traceback.format_exc()
            return self._error_screen(err_text)

    def on_start(self):
        """Xin quyền file ngay khi app start (Android 6+)."""
        self._request_android_permissions()

    def _activate_io_and_start(self):
        """
        Chuyển hướng I/O chỉ SAU khi Kivy window + UI đã sẵn sàng.
        Không được làm ở module-level: Kivy logger dùng stderr trong lúc init,
        nếu bị replace bởi QueueWriter sẽ crash trước khi render được gì.
        """
        builtins.input = gui_input
        sys.stdout     = QueueWriter()
        sys.stderr     = QueueWriter()
        self._start_core()

    def _start_core(self):
        def worker():
            try:
                os.makedirs(self.user_data_dir, exist_ok=True)
                os.chdir(self.user_data_dir)
                core_dir = os.path.dirname(os.path.abspath(__file__))
                if core_dir not in sys.path:
                    sys.path.insert(0, core_dir)
                import tst_tool_core
                output_queue.put("\n[NOVA] Đang khởi động TST-TOOL...\n")
                tst_tool_core.main_vth()
                output_queue.put("\n[NOVA] TST-TOOL đã kết thúc.\n")
            except Exception:
                err = "[LỖI KHỞI ĐỘNG]\n" + traceback.format_exc() + "\n"
                output_queue.put(err)
                # Ghi crash log ra file để debug sau
                try:
                    crash_path = os.path.join(self.user_data_dir, "crash.log")
                    import datetime
                    with open(crash_path, "a", encoding="utf-8") as f:
                        f.write(f"\n=== {datetime.datetime.now()} ===\n{err}")
                    output_queue.put(f"[APP] Crash log: {crash_path}\n")
                    output_queue.put("[APP] Dùng nút SAO CHÉP hoặc LƯU FILE để lấy log.\n")
                except Exception:
                    pass
        threading.Thread(target=worker, daemon=True, name="tst-core").start()

    # Màn hình lỗi khẩn cấp khi build() fail
    @staticmethod
    def _error_screen(err_text):
        from kivy.uix.floatlayout import FloatLayout
        from kivy.uix.label import Label
        from kivy.uix.button import Button
        layout = FloatLayout()
        lbl = Label(
            text="[BUILD ERROR]\n\n" + err_text,
            color=(1, 0.4, 0.4, 1),
            halign="left", valign="top",
            text_size=(None, None),
            size_hint=(1, 0.85),
            pos_hint={"top": 1},
        )
        btn = Button(
            text="SAO CHÉP LỖI",
            size_hint=(1, None),
            height=50,
            pos_hint={"bottom": 1},
            background_color=(0.08, 0.38, 0.32, 1),
            background_normal="",
        )
        btn.bind(on_release=lambda _: Clipboard.copy(err_text))
        layout.add_widget(lbl)
        layout.add_widget(btn)
        return layout

    # Runtime permission request (Android 6+ / API 23+)
    @staticmethod
    def _request_android_permissions():
        try:
            from android.permissions import request_permissions, Permission  # type: ignore
            request_permissions([
                Permission.READ_EXTERNAL_STORAGE,
                Permission.WRITE_EXTERNAL_STORAGE,
            ])
        except ImportError:
            pass   # không chạy trên Android → bỏ qua
        except Exception:
            pass

        # MANAGE_EXTERNAL_STORAGE (Android 11+ / API 30+) — cần nếu đọc/ghi ngoài app folder
        try:
            from android.permissions import check_permission  # type: ignore
            from jnius import autoclass                       # type: ignore
            if not check_permission("android.permission.MANAGE_EXTERNAL_STORAGE"):
                Intent   = autoclass("android.content.Intent")
                Settings = autoclass("android.provider.Settings")
                Uri      = autoclass("android.net.Uri")
                activity = autoclass("org.kivy.android.PythonActivity").mActivity
                intent   = Intent(
                    Settings.ACTION_MANAGE_APP_ALL_FILES_ACCESS_PERMISSION
                )
                intent.setData(Uri.parse("package:vn.tsttool"))
                activity.startActivity(intent)
        except Exception:
            pass   # thiết bị < API 30 hoặc không cần — bỏ qua


if __name__ == "__main__":
    TSTNovaApp().run()
