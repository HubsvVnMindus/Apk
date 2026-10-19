# -*- coding: utf-8 -*-
from __future__ import annotations
import subprocess
import sys
import importlib
import os
import threading
import logging
import json
import time
import random
import math
import re
import hashlib
import hmac
import base64
import socket
import ipaddress
import platform
import uuid
import secrets
from collections import defaultdict, deque, Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Tuple, Optional, List
from urllib.parse import urlparse, parse_qs

# ================== KIỂM TRA VÀ CÀI ĐẶT THƯ VIỆN ==================

REQUIRED_PACKAGES = [
    "pytz",
    "requests",
    "websocket-client",
    "rich",
    "cryptography",
]

def check_and_install_packages():
    missing_packages = []
    
    print("=" * 60)
    print("🔍 ĐANG KIỂM TRA THƯ VIỆN...")
    print("=" * 60)
    
    for package in REQUIRED_PACKAGES:
        try:
            import_name = package
            if package == "websocket-client":
                import_name = "websocket"
            elif package == "cryptography":
                import_name = "cryptography"
            
            importlib.import_module(import_name)
            print(f"✅ {package} - Đã cài đặt")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} - CHƯA CÀI ĐẶT")
    
    if not missing_packages:
        print("\n✅ TẤT CẢ THƯ VIỆN ĐÃ SẴN SÀNG!")
        print("=" * 60)
        return True
    
    print("\n" + "=" * 60)
    print(f"⚠️  PHÁT HIỆN {len(missing_packages)} THƯ VIỆN THIẾU:")
    for pkg in missing_packages:
        print(f"   - {pkg}")
    print("=" * 60)
    print("\n🔄 ĐANG TIẾN HÀNH CÀI ĐẶT TỰ ĐỘNG...")
    print("-" * 60)
    
    for package in missing_packages:
        try:
            print(f"📦 Đang cài đặt {package}...")
            subprocess.check_call([
                sys.executable, 
                "-m", 
                "pip", 
                "install", 
                package,
                "--quiet"
            ])
            print(f"✅ Đã cài đặt {package} thành công!")
        except Exception as e:
            print(f"❌ Lỗi khi cài đặt {package}: {e}")
            print(f"💡 Vui lòng cài đặt thủ công: pip install {package}")
            return False
    
    print("\n" + "=" * 60)
    print("✅ TẤT CẢ THƯ VIỆN ĐÃ ĐƯỢC CÀI ĐẶT XONG!")
    print("=" * 60)
    return True

if not check_and_install_packages():
    print("\n" + "=" * 60)
    print("❌ KHÔNG THỂ CÀI ĐẶT ĐẦY ĐỦ THƯ VIỆN")
    print("💡 VUI LÒNG CÀI ĐẶT THỦ CÔNG:")
    print("   pip install pytz requests websocket-client rich cryptography")
    print("=" * 60)
    sys.exit(1)

# ================== IMPORT THƯ VIỆN ==================

import pytz
import requests
import websocket
from rich.console import Console, Group
from rich.table import Table
from rich.panel import Panel
from rich.live import Live
from rich.align import Align
from rich.prompt import Prompt, Confirm, IntPrompt, FloatPrompt
from rich.rule import Rule
from rich.text import Text
from rich import box
from rich.columns import Columns
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# ================== CẤU HÌNH ==================

console = Console(force_terminal=True, color_system="auto")
tz = pytz.timezone("Asia/Ho_Chi_Minh")

def force_clear():
    """Xóa sạch hoàn toàn màn hình (hoạt động tốt trên Windows + Linux + macOS)"""
    try:
        # 1. System clear (Windows: cls, Linux/mac: clear)
        if os.name == "nt":
            os.system("cls")
        else:
            os.system("clear")
    except Exception:
        pass

    try:
        # 2. Rich clear (gọi trực tiếp method gốc để tránh đệ quy)
        Console.clear(console)
    except Exception:
        pass

    try:
        # 3. ANSI escape mạnh (xóa buffer + về đầu)
        print("\033[2J\033[3J\033[H", end="", flush=True)
    except Exception:
        pass

# Ghi đè console.clear() để mọi chỗ gọi đều xóa sạch
console.clear = force_clear

# ================== GIAO DIỆN TST-TOOL ==================

TST_COLORS = {
    # NOVA DARK // cinematic terminal — deep space + electric accents
    "gold": "#FFD166",       # amber highlight
    "gold_dark": "#C9920A",  # warm amber dim
    "platinum": "#E2E8F0",   # near-white text on dark
    "diamond": "#38BDF8",    # electric sky
    "ruby": "#FF4D6D",       # hot coral-red
    "emerald": "#06D6A0",    # neon mint-green
    "sapphire": "#818CF8",   # periwinkle-indigo
    "amethyst": "#A78BFA",   # soft violet
    "onyx": "#1E293B",       # deep panel bg
    "rose": "#FB7185",       # soft pink
    "neon_blue": "#22D3EE",  # cyan electric
    "neon_pink": "#F472B6",  # vivid rose
    "neon_green": "#4ADE80", # lime signal
    "neon_orange": "#FB923C",# warm signal
    "crimson": "#EF4444",    # error red
    "turquoise": "#2DD4BF",  # teal accent
    "lavender": "#C4B5FD",   # muted violet
    "sky": "#7DD3FC",        # soft sky blue
    "mint": "#6EE7B7",       # pastel mint
    "text": "#F1F5F9",       # primary text (light on dark)
    "muted": "#94A3B8",      # secondary text
    "surface": "#0F172A",    # deep background
    "white": "#F8FAFC",      # near-white
    "bg_panel": "#1E293B",   # panel dark
    "bg_deep": "#0F172A",    # deepest bg
    "accent_line": "#334155",# subtle dividers
}

ICONS = {
    "crown":"♛", "diamond":"◈", "star":"★", "fire":"⬡", "lightning":"⚡",
    "target":"⊕", "shield":"⬡", "sword":"⟫", "brain":"◉", "robot":"▶",
    "rocket":"▲", "trophy":"◆", "medal":"◎", "gem":"◈", "sparkle":"✦",
    "settings":"◈", "user":"◉", "key":"⌘", "lock":"■", "unlock":"□",
    "check":"✓", "cross":"✕", "warning":"▲", "info":"◆", "money":"◈",
    "chart":"▦", "clock":"◷", "link":"→", "wifi":"≋", "globe":"⊕",
    "plus":"＋", "minus":"−", "arrow":"▶", "heart":"♥", "bell":"◆",
    "gift":"◈", "magic":"✦", "phone":"◉", "pulse":"◉", "scan":"⊡",
    "ai":"▣", "race":"▶▶", "escape":"⊠", "lotto":"★",
}

# LOGO TST-TOOL — block chữ kiểu cũ (vàng / xanh xen kẽ)
LOGO = r"""
████████╗███████╗████████╗      ████████╗ ██████╗  ██████╗ ██╗     
╚══██╔══╝██╔════╝╚══██╔══╝      ╚══██╔══╝██╔═══██╗██╔═══██╗██║     
   ██║   ███████╗   ██║   █████╗   ██║   ██║   ██║██║   ██║██║     
   ██║   ╚════██║   ██║   ╚════╝   ██║   ██║   ██║██║   ██║██║     
   ██║   ███████║   ██║            ██║   ╚██████╔╝╚██████╔╝███████╗
   ╚═╝   ╚══════╝   ╚═╝            ╚═╝    ╚═════╝  ╚═════╝ ╚══════╝
"""

LOGO_TAGLINE = "TST-TOOL  ·  AI COMMAND SYSTEM  ·  V3"

def _vn_now_str() -> str:
    """Giờ Việt Nam realtime."""
    try:
        return datetime.now(tz).strftime("%H:%M:%S  %d/%m/%Y")
    except Exception:
        return datetime.now().strftime("%H:%M:%S  %d/%m/%Y")


def _key_countdown_str() -> str:
    """Đếm ngược hạn key từng giây (hoặc Vĩnh viễn)."""
    global _key_expires_at, _key_expiry_info
    if _key_expires_at is None:
        info = (_key_expiry_info or "").strip()
        if info and info not in ("—",):
            return info
        return "Vĩnh viễn"
    try:
        exp = _key_expires_at
        if getattr(exp, "tzinfo", None) is None:
            exp = exp.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        secs = int((exp - now).total_seconds())
        if secs <= 0:
            return "Đã hết hạn"
        d, rem = divmod(secs, 86400)
        h, rem = divmod(rem, 3600)
        m, s = divmod(rem, 60)
        if d > 0:
            return f"{d}n {h:02d}:{m:02d}:{s:02d}"
        if h > 0:
            return f"{h:02d}:{m:02d}:{s:02d}"
        return f"{m:02d}:{s:02d}"
    except Exception:
        return (_key_expiry_info or "—")


def is_key_expired() -> bool:
    """True nếu key có hạn và đã quá hạn."""
    global _key_expires_at
    if _key_expires_at is None:
        return False
    try:
        exp = _key_expires_at
        if getattr(exp, "tzinfo", None) is None:
            exp = exp.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) >= exp
    except Exception:
        return False


def stop_tool_key_expired(reason: str = "") -> None:
    """Dừng toàn bộ tool khi key hết hạn."""
    global stop_flag, cdtd_stop_flag, _key_expiry_info, ui_state
    stop_flag = True
    try:
        cdtd_stop_flag = True
    except Exception:
        pass
    _key_expiry_info = "Đã hết hạn"
    msg = "🔑 KEY ĐÃ HẾT HẠN — tự dừng tool."
    if reason:
        msg += f" ({reason})"
    try:
        safe_console_print(f"[bold red]{msg}[/]")
    except Exception:
        try:
            console.print(f"[bold red]{msg}[/]")
        except Exception:
            pass
    try:
        ui_state = "STOPPED"
    except Exception:
        pass
    # đóng WS nếu có
    try:
        wsobj = _ws.get("ws") if isinstance(_ws, dict) else None
        if wsobj:
            wsobj.close()
    except Exception:
        pass


def check_key_expiry_and_stop(context: str = "") -> bool:
    """
    Kiểm tra hạn key. Nếu hết hạn → dừng tool, return True.
    Gọi định kỳ trong live loop / trước khi cược.
    """
    if is_key_expired():
        stop_tool_key_expired(context or "hết hạn")
        return True
    return False


def build_live_brand(game_code: str = "LIVE"):
    """Logo TST-TOOL + giờ VN + hạn key trên bảng trực tiếp."""
    t = Text()
    t.append("TST", style=f"bold {TST_COLORS['gold']}")
    t.append("-", style="bold white")
    t.append("TOOL", style=f"bold {TST_COLORS['sapphire']}")
    t.append(f"  ·  {game_code}  ·  ", style=TST_COLORS["muted"])
    t.append(_vn_now_str(), style=f"bold {TST_COLORS['sky']}")
    t.append("  ·  HẠN ", style=TST_COLORS["muted"])
    t.append(_key_countdown_str(), style=f"bold {TST_COLORS['gold']}")
    t.append(f"  ·  {str(_key_type or 'free').upper()}", style=TST_COLORS["platinum"])
    return Align.center(t)




def print_tst_logo():
    """In logo block chữ — căn đều, không lệch hàng."""
    lines = [ln.rstrip() for ln in LOGO.splitlines() if ln.strip()]
    # pad cùng width rồi center
    width = max(len(ln) for ln in lines) if lines else 0
    for i, line in enumerate(lines):
        col = TST_COLORS["gold"] if i % 2 == 0 else TST_COLORS["sapphire"]
        console.print(Align.center(Text(line.ljust(width), style=f"bold {col}")))
    console.print(Align.center(Text(LOGO_TAGLINE, style=TST_COLORS["muted"])))



def _ui_title(icon, title, subtitle=""):
    """NOVA DARK: cinematic section header — icon + gradient wordmark."""
    console.print()
    # brand strip
    brand = Text()
    brand.append("  ♛ ", style=f"bold {TST_COLORS['gold']}")
    brand.append("TST-TOOL", style=f"bold {TST_COLORS['platinum']}")
    brand.append("  ·  ", style=TST_COLORS["accent_line"])
    brand.append("NOVA", style=f"bold {TST_COLORS['sapphire']}")
    brand.append("  ♛ ", style=f"bold {TST_COLORS['gold']}")
    console.print(Align.center(brand))
    console.print(Align.center(Text(
        "▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰",
        style=TST_COLORS["sapphire"]
    )))
    title_text = Text()
    title_text.append(f" {icon}  ", style=f"bold {TST_COLORS['neon_orange']}")
    title_text.append(title.upper(), style=f"bold {TST_COLORS['gold']}")
    console.print(Align.center(title_text))
    if subtitle:
        console.print(Align.center(Text(f"  {subtitle}  ", style=TST_COLORS["muted"])))
    console.print()


def _ui_section(title, body, accent=None):
    """NOVA DARK: sleek card with left accent bar."""
    accent = accent or TST_COLORS["sapphire"]
    head = Text()
    head.append("▌ ", style=f"bold {accent}")
    head.append(title.upper(), style=f"bold {TST_COLORS['gold']}")
    console.print(head)
    console.print(Panel(body, border_style=accent, box=box.HEAVY_HEAD, padding=(0, 2)))


def _ui_prompt(label="COMMAND"):
    return Prompt.ask(
        f"\n[bold {TST_COLORS['gold']}] ♛  {label.upper()}[/bold {TST_COLORS['gold']}]"
        f"[{TST_COLORS['accent_line']}] ─────────────────── [/{TST_COLORS['accent_line']}]"
        f"[bold {TST_COLORS['emerald']}]▶[/bold {TST_COLORS['emerald']}]",
        default="q"
    ).strip()


def _ui_chip(number, title, detail, accent):
    t = Text()
    t.append(f"  {number}  ", style=f"bold {TST_COLORS['bg_deep']} on {accent}")
    t.append(f"  {title.upper()}  ", style=f"bold {TST_COLORS['gold']}")
    t.append(detail, style=TST_COLORS["muted"])
    return t


def _ui_status_bar(pairs: list):
    """Render a compact dark status strip from [(label, value, color)] list."""
    t = Text()
    for i, (label, value, color) in enumerate(pairs):
        if i > 0:
            t.append("  │  ", style=TST_COLORS["accent_line"])
        t.append(f"{label} ", style=TST_COLORS["muted"])
        t.append(value, style=f"bold {color}")
    return Panel(
        Align.center(t),
        border_style=TST_COLORS["accent_line"],
        box=box.SIMPLE,
        padding=(0, 1),
    )


def _ui_divider(label=""):
    """Sleek horizontal divider with optional centered label."""
    if label:
        console.print(Rule(f"[bold {TST_COLORS['muted']}] {label} [/]", style=TST_COLORS["accent_line"]))
    else:
        console.print(Rule(style=TST_COLORS["accent_line"]))

# ================== BIẾN TOÀN CỤC ==================
_ws_status = "⏳ Đang kết nối..."
_is_authenticated = False
_user_key = None
_key_type = "free"
_key_expiry_info = ""  # "Còn X ngày..." hoặc "Vĩnh viễn"
_key_expires_at = None  # datetime hoặc None
_heartbeat_running = False
_heartbeat_thread = None
_in_menu = False
_ip_info = {}
AI_PERFORMANCE = defaultdict(lambda: {"wins": 0, "losses": 0, "total": 0})

def load_ai_performance() -> None:
    """Load thống kê AI dài hạn từ file."""
    global AI_PERFORMANCE
    try:
        if os.path.exists("ai_performance.json"):
            with open("ai_performance.json", "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                for k, v in data.items():
                    if isinstance(v, dict):
                        AI_PERFORMANCE[k]["wins"] = int(v.get("wins", 0) or 0)
                        AI_PERFORMANCE[k]["losses"] = int(v.get("losses", 0) or 0)
                        AI_PERFORMANCE[k]["total"] = int(v.get("total", 0) or 0)
    except Exception:
        pass

try:
    load_ai_performance()
except Exception:
    pass


def get_ai_winrate_rows(prefix: str = "", limit: int = 8) -> list:
    """Trả list (name, wins, losses, total, rate) sắp theo total giảm dần."""
    rows = []
    for name, st in AI_PERFORMANCE.items():
        if prefix and not str(name).startswith(prefix) and prefix not in str(name):
            # nếu prefix=CDTD_ thì chỉ lấy CDTD
            if prefix.endswith("_") and not str(name).startswith(prefix):
                continue
            if not prefix.endswith("_") and prefix.upper() not in str(name).upper():
                continue
        total = int(st.get("total", 0) or 0)
        if total <= 0:
            continue
        w = int(st.get("wins", 0) or 0)
        l = int(st.get("losses", 0) or 0)
        rate = (w / total * 100.0) if total else 0.0
        rows.append((str(name), w, l, total, rate))
    rows.sort(key=lambda x: (x[3], x[4]), reverse=True)
    return rows[:limit]


def format_ai_stats_text(current_algo: str = "", prefix: str = ""):
    """Text thống kê AI cho panel live."""
    t = Text()
    t.append("THỐNG KÊ AI" + chr(10), style=f"bold {TST_COLORS['gold']}")
    cur = str(current_algo or "").strip()
    if cur:
        key = cur if not prefix else (prefix + cur if not cur.startswith(prefix) else cur)
        st = AI_PERFORMANCE.get(key) or AI_PERFORMANCE.get(cur) or {}
        total = int(st.get("total", 0) or 0)
        w = int(st.get("wins", 0) or 0)
        l = int(st.get("losses", 0) or 0)
        rate = (w / total * 100.0) if total else 0.0
        t.append(("ĐANG DÙNG  %s" % cur) + chr(10), style=f"bold {TST_COLORS['sapphire']}")
        if total:
            col = TST_COLORS["emerald"] if rate >= 50 else TST_COLORS["ruby"]
            t.append(("  %dW/%dL  (%.0f%%)  n=%d" % (w, l, rate, total)) + chr(10), style=f"bold {col}")
        else:
            t.append("  chưa có dữ liệu" + chr(10), style=TST_COLORS["muted"])
    rows = get_ai_winrate_rows(prefix=prefix, limit=6)
    if rows:
        t.append("TOP" + chr(10), style=f"bold {TST_COLORS['muted']}")
        for name, w, l, total, rate in rows:
            short = name.replace("CDTD_", "").replace("choose_", "")[:18]
            col = TST_COLORS["emerald"] if rate >= 50 else TST_COLORS["neon_orange"] if rate >= 40 else TST_COLORS["ruby"]
            t.append(("  %-18s %5.1f%%  (%d/%d)" % (short, rate, w, total)) + chr(10), style=col)
    else:
        t.append("Chưa đủ ván để xếp hạng" + chr(10), style=TST_COLORS["muted"])
    return t


_secure_mode = False
_secure_tool = None
stop_flag = False
USER_ID = None
SECRET_KEY = None

# ================== SUPABASE CONFIG ==================

SUPABASE_URL = "https://ebviepssggyyrdeedpnz.supabase.co"
SUPABASE_KEY = "sb_publishable_B3VF2kG0260fFrOtWBJi1g_ylklAm1_"
ADMIN_SECRET_CODE = "9826665"

# ================== TELEGRAM CONFIG ==================

TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
TELEGRAM_CHAT_ID = ""
TELEGRAM_ENABLED = False

# ================== HỆ THỐNG BẢO MẬT (legacy) ==================

class AntiDetectionSystem:
    def __init__(self):
        self.is_stealth_mode = False
        self.detection_risk = 0
        self.last_check = time.time()
        self.request_history = []
        self.stealth_session_id = hashlib.md5(str(time.time()).encode()).hexdigest()[:8]
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0',
        ]
        self.accept_languages = ['vi-VN,vi;q=0.9,en;q=0.8', 'en-US,en;q=0.9', 'vi;q=0.9,en;q=0.8']
        self.last_request_time = 0
        self.min_delay = 0.3
        self.max_delay = 1.5
    
    def enable_stealth_mode(self):
        self.is_stealth_mode = True
        safe_console_print("[bold green]🛡️ Đã bật chế độ tàng hình![/bold green]")
        self.stealth_session_id = hashlib.md5(str(time.time() + random.random()).encode()).hexdigest()[:8]
    
    def get_random_delay(self) -> float:
        return random.uniform(self.min_delay, self.max_delay)
    
    def wait_before_request(self):
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        if elapsed < self.min_delay:
            wait_time = self.get_random_delay() - elapsed
            if wait_time > 0:
                time.sleep(wait_time)
        self.last_request_time = time.time()
    
    def get_random_headers(self) -> dict:
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': random.choice(self.accept_languages),
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
        }
    
    def make_stealth_request(self, url: str, method: str = 'GET', **kwargs) -> Optional[requests.Response]:
        self.wait_before_request()
        headers = self.get_random_headers()
        if 'headers' in kwargs:
            headers.update(kwargs['headers'])
        kwargs['headers'] = headers
        if 'timeout' not in kwargs:
            kwargs['timeout'] = random.uniform(8, 15)
        
        try:
            response = requests.request(method, url, **kwargs)
            self.request_history.append({
                'url': url,
                'time': time.time(),
                'status': response.status_code
            })
            self.check_detection_risk()
            return response
        except Exception as e:
            safe_console_print(f"[yellow]⚠️ Request error: {e}[/yellow]")
            return None
    
    def check_detection_risk(self):
        recent_requests = [r for r in self.request_history 
                          if time.time() - r['time'] < 60]
        
        if len(recent_requests) > 30:
            self.detection_risk += 10
        elif len(recent_requests) > 20:
            self.detection_risk += 5
        elif len(recent_requests) > 10:
            self.detection_risk += 2
        
        if self.detection_risk > 70:
            safe_console_print(f"[red]⚠️ Phát hiện rủi ro cao ({self.detection_risk}%)[/red]")
            self.detection_risk = 0
    
    def get_status(self) -> dict:
        return {
            'stealth_mode': self.is_stealth_mode,
            'detection_risk': self.detection_risk,
            'request_count': len(self.request_history),
            'session_id': self.stealth_session_id,
        }
    
    def display_status(self):
        status = self.get_status()
        safe_console_print("\n" + "="*50)
        safe_console_print("🛡️ ANTI-DETECTION STATUS")
        safe_console_print("="*50)
        safe_console_print(f"🔒 Stealth Mode: {'✅ BẬT' if status['stealth_mode'] else '❌ TẮT'}")
        safe_console_print(f"⚠️ Detection Risk: {status['detection_risk']}%")
        safe_console_print(f"📊 Total Requests: {status['request_count']}")
        safe_console_print(f"🔑 Session ID: {status['session_id']}")
        safe_console_print("="*50)

class SecureTSTTool:
    def __init__(self):
        self.anti_detection = AntiDetectionSystem()
        self.is_stealth = False
    
    def start_stealth_mode(self):
        safe_console_print("\n[bold]🛡️ KHỞI ĐỘNG CHẾ ĐỘ CHỐNG SOI[/bold]")
        safe_console_print("="*50)
        self.anti_detection.enable_stealth_mode()
        self.is_stealth = True
        self.anti_detection.display_status()
        safe_console_print("\n[green]✅ Đã sẵn sàng chống soi![/green]")
        time.sleep(2)
    
    def make_secure_request(self, url: str, **kwargs) -> Optional[requests.Response]:
        if self.is_stealth:
            return self.anti_detection.make_stealth_request(url, **kwargs)
        else:
            method = kwargs.pop('method', 'GET')
            return requests.request(method, url, **kwargs)
    
    def secure_post(self, url: str, **kwargs) -> Optional[requests.Response]:
        if self.is_stealth:
            return self.anti_detection.make_stealth_request(url, method='POST', **kwargs)
        else:
            return requests.post(url, **kwargs)
    
    def get_status(self) -> dict:
        if self.is_stealth:
            return self.anti_detection.get_status()
        return {'stealth_mode': False}
    
    def display_status(self):
        if self.is_stealth:
            self.anti_detection.display_status()

# ================== SCAN IP ==================

def get_public_ip() -> Optional[str]:
    try:
        response = requests.get('https://api.ipify.org', timeout=5)
        if response.status_code == 200:
            return response.text.strip()
    except:
        pass
    
    try:
        response = requests.get('https://ip-api.com/json', timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get('query')
    except:
        pass
    return None

def get_local_ip() -> Optional[str]:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return None

def get_device_fingerprint() -> str:
    """
    Mã thiết bị CỐ ĐỊNH — chỉ từ phần cứng/OS.
    Không ghi file .txt / .json (dễ sửa → đổi mã).
    Không dùng time/random — cùng máy luôn ra cùng mã.
    Ghim thật sự: lưu fingerprint lên Supabase lúc tạo user.
    """
    parts = []
    # MAC (uuid.getnode) — ổn định trên cùng máy
    try:
        node = uuid.getnode()
        mac = ":".join(f"{(node >> ele) & 0xFF:02x}" for ele in range(40, -1, -8))
        parts.append(f"mac:{mac}")
    except Exception:
        pass
    try:
        parts.append(f"host:{socket.gethostname()}")
    except Exception:
        pass
    try:
        parts.append(f"sys:{platform.system()}")
        parts.append(f"rel:{platform.release()}")
        parts.append(f"mach:{platform.machine()}")
        parts.append(f"proc:{platform.processor() or 'x'}")
    except Exception:
        pass
    try:
        # home path — ổn định theo user OS, không phải JSON app
        parts.append(f"home:{Path.home()}")
    except Exception:
        pass

    raw = "|".join(parts) if parts else "tst-tool-fixed-device"
    # SHA256 đầy đủ rồi lấy 24 ký tự — cố định
    return hashlib.sha256(raw.encode("utf-8", errors="ignore")).hexdigest()[:24]

def scan_ip_ban_list() -> bool:
    try:
        ip = get_public_ip()
        if not ip:
            return False
        
        blacklist_file = "ip_blacklist.txt"
        if not os.path.exists(blacklist_file):
            with open(blacklist_file, 'w', encoding='utf-8') as f:
                f.write("# Blacklisted IPs\n")
            return False
        
        with open(blacklist_file, 'r', encoding='utf-8') as f:
            blacklist = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        
        if ip in blacklist:
            safe_console_print(f"[red]❌ IP {ip} đã bị cấm![/red]")
            return True
        return False
    except:
        return False

def check_ip_whitelist() -> bool:
    try:
        ip = get_public_ip()
        if not ip:
            return False
        
        whitelist_file = "ip_whitelist.txt"
        if not os.path.exists(whitelist_file):
            return True
        
        with open(whitelist_file, 'r', encoding='utf-8') as f:
            whitelist = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        
        if not whitelist:
            return True
        
        if ip in whitelist:
            return True
        
        for entry in whitelist:
            if '/' in entry:
                try:
                    network = ipaddress.ip_network(entry, strict=False)
                    if ipaddress.ip_address(ip) in network:
                        return True
                except:
                    pass
        
        safe_console_print(f"[red]❌ IP {ip} không có trong whitelist![/red]")
        return False
    except:
        return True

class IPScanner:
    def __init__(self):
        self.public_ip = None
        self.local_ip = None
        self.device_fingerprint = None
        self.location_info = None
        self._scanned = False
    
    def scan(self) -> bool:
        try:
            self.public_ip = get_public_ip()
            self.local_ip = get_local_ip()
            self.device_fingerprint = get_device_fingerprint()
            
            if self.public_ip:
                try:
                    response = requests.get(f'http://ip-api.com/json/{self.public_ip}', timeout=5)
                    if response.status_code == 200:
                        self.location_info = response.json()
                except:
                    pass
            
            self._scanned = True
            
            if scan_ip_ban_list():
                return False
            
            if not check_ip_whitelist():
                return False
            
            self.log_scan_info()
            return True
        except Exception as e:
            safe_console_print(f"[yellow]⚠️ Lỗi scan IP: {e}[/yellow]")
            return False
    
    def log_scan_info(self):
        log_data = {
            "timestamp": datetime.now(tz).isoformat(),
            "public_ip": self.public_ip,
            "local_ip": self.local_ip,
            "fingerprint": self.device_fingerprint,
            "location": self.location_info,
        }
        
        try:
            with open("ip_scan_log.json", "a", encoding="utf-8") as f:
                f.write(json.dumps(log_data, ensure_ascii=False) + "\n")
        except:
            pass
        
        safe_console_print("[dim]📡 SCAN IP:[/dim]")
        if self.public_ip:
            safe_console_print(f"  🌐 Public IP: [bold]{self.public_ip}[/bold]")
        if self.local_ip:
            safe_console_print(f"  🏠 Local IP: [bold]{self.local_ip}[/bold]")
        if self.location_info:
            city = self.location_info.get('city', 'N/A')
            country = self.location_info.get('country', 'N/A')
            safe_console_print(f"  📍 Location: [bold]{city}, {country}[/bold]")
        safe_console_print(f"  🔑 Fingerprint: [dim]{self.device_fingerprint}[/dim]")
        safe_console_print("")
    
    def get_status(self) -> dict:
        return {
            "scanned": self._scanned,
            "public_ip": self.public_ip,
            "local_ip": self.local_ip,
            "fingerprint": self.device_fingerprint,
            "location": self.location_info,
        }
    
    def is_ip_safe(self) -> bool:
        if not self._scanned:
            self.scan()
        if scan_ip_ban_list():
            return False
        if not check_ip_whitelist():
            return False
        return True

def enhanced_auth_check():
    global _ip_info
    ip_scanner = IPScanner()
    if not ip_scanner.scan():
        safe_console_print("[red]❌ Scan IP thất bại! Tool sẽ không chạy.[/red]")
        return False
    if not ip_scanner.is_ip_safe():
        safe_console_print("[red]❌ IP không an toàn! Tool sẽ không chạy.[/red]")
        return False
    _ip_info = ip_scanner.get_status()
    return True

# ================== CHỐNG DEBUG ==================

def detect_debugger() -> bool:
    try:
        if sys.gettrace() is not None:
            return True
        if 'PYCHARM_HOSTED' in os.environ:
            return True
        return False
    except:
        return False

def anti_crack_check() -> bool:
    if detect_debugger():
        console.print("[red]❌ Phát hiện debugger! Tool sẽ không chạy.[/red]")
        return False
    return True

# ================== HÀM XÁC THỰC KEY ==================

def verify_key_with_device(key: str) -> dict:
    if detect_debugger():
        return {"valid": False, "error": "Phát hiện debugger! Không thể xác thực."}

    key = (key or "").strip()
    url = f"{SUPABASE_URL}/rest/v1/keys?key_code=eq.{key}"

    headers = supabase_headers()

    try:
        response = requests.get(url, headers=headers, timeout=15)

        if response.status_code != 200:
            # Fallback: key FREE local nếu Supabase lỗi
            local_ok, local_uid, local_item = validate_local_free_key(key)
            if local_ok and local_item:
                exp = local_item.get("expires")
                expires_at = datetime.fromtimestamp(float(exp), tz=timezone.utc).isoformat() if exp else "forever"
                return {
                    "valid": True,
                    "data": {
                        "key": key,
                        "key_type": "free",
                        "max_ai": 10,
                        "expires_at": expires_at,
                        "note": f"Local FREE key (user {local_uid})",
                        "used_count": 0,
                        "max_uses": None,
                        "source": "local",
                    }
                }
            return {"valid": False, "error": f"HTTP {response.status_code}"}

        data = response.json()

        if not data:
            # Không có trên Supabase → thử key FREE local
            local_ok, local_uid, local_item = validate_local_free_key(key)
            if local_ok and local_item:
                exp = local_item.get("expires")
                expires_at = datetime.fromtimestamp(float(exp), tz=timezone.utc).isoformat() if exp else "forever"
                return {
                    "valid": True,
                    "data": {
                        "key": key,
                        "key_type": "free",
                        "max_ai": 10,
                        "expires_at": expires_at,
                        "note": f"Local FREE key (user {local_uid})",
                        "used_count": 0,
                        "max_uses": None,
                        "source": "local",
                    }
                }
            return {"valid": False, "error": "Key không tồn tại"}

        keyData = data[0]

        if keyData.get('status') != 'active':
            return {"valid": False, "error": "Key đã bị vô hiệu hóa"}

        if keyData.get('expires_at'):
            try:
                expiry = datetime.fromisoformat(keyData['expires_at'].replace('Z', '+00:00'))
                if datetime.now().astimezone() > expiry:
                    return {"valid": False, "error": "Key đã hết hạn"}
            except Exception:
                pass

        used_count = keyData.get('used_count', 0)
        max_uses = keyData.get('max_uses')
        if max_uses and used_count >= max_uses:
            return {"valid": False, "error": "Key đã đạt giới hạn sử dụng"}

        new_count = used_count + 1
        update_url = f"{SUPABASE_URL}/rest/v1/keys?key_code=eq.{key}"
        update_data = {"used_count": new_count}

        try:
            requests.patch(update_url, json=update_data, headers=headers, timeout=10)
        except Exception:
            pass

        return {
            "valid": True,
            "data": {
                "key": key,
                "key_type": keyData.get('key_type', 'free'),
                "max_ai": keyData.get('max_ai', 10),
                "expires_at": keyData.get('expires_at', 'forever'),
                "note": keyData.get('note', ''),
                "used_count": new_count,
                "max_uses": keyData.get('max_uses'),
                "source": "supabase",
            }
        }

    except Exception as e:
        local_ok, local_uid, local_item = validate_local_free_key(key)
        if local_ok and local_item:
            exp = local_item.get("expires")
            expires_at = datetime.fromtimestamp(float(exp), tz=timezone.utc).isoformat() if exp else "forever"
            return {
                "valid": True,
                "data": {
                    "key": key,
                    "key_type": "free",
                    "max_ai": 10,
                    "expires_at": expires_at,
                    "note": f"Local FREE key (user {local_uid})",
                    "used_count": 0,
                    "max_uses": None,
                    "source": "local",
                }
            }
        return {"valid": False, "error": f"Lỗi: {str(e)}"}


def supabase_headers(prefer: Optional[str] = None) -> dict:
    """Headers chuẩn cho Supabase REST API."""
    h = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "User-Agent": "TST-TOOL-Secure/3.0",
    }
    if prefer:
        h["Prefer"] = prefer
    return h


def create_key_on_supabase(
    key_code: str,
    key_type: str = "free",
    max_ai: int = 10,
    duration_hours: int = 13,
    note: str = "",
    user_id: str = "",
    max_uses: Optional[int] = None,
) -> tuple:
    """
    Tạo key mới trên Supabase (bảng keys).
    Trả về (success: bool, message_or_data).
    """
    url = f"{SUPABASE_URL}/rest/v1/keys"
    expires_at = (datetime.now(timezone.utc) + timedelta(hours=duration_hours)).isoformat()

    payload = {
        "key_code": key_code,
        "key_type": key_type,
        "status": "active",
        "max_ai": max_ai,
        "expires_at": expires_at,
        "used_count": 0,
        "note": note or f"Đổi xu - user {user_id}" if user_id else "KEY FREE 13H (đổi xu)",
    }
    if max_uses is not None:
        payload["max_uses"] = max_uses

    try:
        response = requests.post(
            url,
            headers=supabase_headers(prefer="return=representation"),
            json=payload,
            timeout=15,
        )

        if response.status_code in (200, 201):
            data = response.json()
            row = data[0] if isinstance(data, list) and data else data
            return True, {
                "key_code": key_code,
                "key_type": key_type,
                "expires_at": expires_at,
                "max_ai": max_ai,
                "supabase": row,
            }

        # Conflict: key đã tồn tại
        if response.status_code == 409:
            return False, "Key đã tồn tại trên Supabase"

        err_text = response.text[:300] if response.text else f"HTTP {response.status_code}"
        return False, f"Supabase lỗi {response.status_code}: {err_text}"

    except Exception as e:
        return False, f"Lỗi kết nối Supabase: {str(e)}"


# ================== SUPABASE USERS (NGUỒN CHÍNH — KHÔNG LƯU LOCAL) ==================
# Toàn bộ user/xu/IP lưu trên Supabase. Không dùng user_data.enc.
# SQL tạo bảng (SQL Editor):
#   create table if not exists public.users (
#     user_id text primary key,
#     ip text,
#     coins double precision default 0,
#     total_mined double precision default 0,
#     keys_count int default 0,
#     keys jsonb default '[]'::jsonb,
#     daily_claim_date text default '',
#     coin_day text default '',
#     mining boolean default false,
#     mining_start double precision default 0,
#     note text default '',
#     fingerprint text default '',
#     status text default 'active',
#     created_at timestamptz default now(),
#     updated_at timestamptz default now(),
#     last_seen_at timestamptz default now()
#   );
#   create index if not exists users_ip_idx on public.users (ip);
#
# Nếu bảng cũ đã tạo, chạy thêm:
#   alter table public.users add column if not exists keys jsonb default '[]'::jsonb;
#   alter table public.users add column if not exists daily_claim_date text default '';
#   alter table public.users add column if not exists coin_day text default '';
#   alter table public.users add column if not exists mining boolean default false;
#   alter table public.users add column if not exists mining_start double precision default 0;
#   alter table public.users add column if not exists ban_until timestamptz;
#   alter table public.users add column if not exists ban_reason text default '';
#   create index if not exists users_fingerprint_idx on public.users (fingerprint);
#   alter table public.users add column if not exists banned_until timestamptz;
#   alter table public.users add column if not exists ban_reason text default '';
#   create index if not exists users_fingerprint_idx on public.users (fingerprint);

# Cache RAM (không ghi file local)
_USER_CACHE: Dict[str, dict] = {}
_USER_CACHE_TS: float = 0.0
_USER_CACHE_TTL = 15.0  # giây
DEVICE_BAN_DAYS = 2
DEVICE_BAN_HOURS = 48  # 2 ngày — đổi IP trên cùng mã thiết bị


def supabase_get_user(user_id: str) -> Optional[dict]:
    """Lấy 1 user từ Supabase theo user_id."""
    try:
        url = f"{SUPABASE_URL}/rest/v1/users?user_id=eq.{user_id}&select=*&limit=1"
        r = requests.get(url, headers=supabase_headers(), timeout=12)
        if r.status_code == 200:
            rows = r.json() if isinstance(r.json(), list) else []
            return rows[0] if rows else None
        return None
    except Exception:
        return None


def supabase_find_user_by_ip(ip: str) -> Optional[dict]:
    """Tìm user trên Supabase theo IP (mỗi IP ideally 1 user)."""
    if not ip or ip == "unknown":
        return None
    try:
        url = f"{SUPABASE_URL}/rest/v1/users?ip=eq.{ip}&select=*&limit=1"
        r = requests.get(url, headers=supabase_headers(), timeout=12)
        if r.status_code == 200:
            rows = r.json() if isinstance(r.json(), list) else []
            return rows[0] if rows else None
        return None
    except Exception:
        return None


def supabase_find_user_by_fingerprint(fp: str) -> Optional[dict]:
    """Tìm user theo mã thiết bị (fingerprint)."""
    if not fp:
        return None
    try:
        # encode an toàn cho query
        from urllib.parse import quote
        q = quote(str(fp), safe="")
        url = f"{SUPABASE_URL}/rest/v1/users?fingerprint=eq.{q}&select=*&limit=1"
        r = requests.get(url, headers=supabase_headers(), timeout=12)
        if r.status_code == 200:
            rows = r.json() if isinstance(r.json(), list) else []
            return rows[0] if rows else None
        return None
    except Exception:
        return None


def supabase_ban_user(user_id: str, hours: int = DEVICE_BAN_HOURS, reason: str = "") -> tuple:
    """Ban user trên Supabase trong `hours` giờ."""
    uid = str(user_id).strip()
    if not uid:
        return False, "user_id trống"
    until = datetime.now(timezone.utc) + timedelta(hours=hours)
    payload = {
        "status": "banned",
        "ban_until": until.isoformat(),
        "ban_reason": reason or "Đổi IP / gian lận thiết bị",
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        url = f"{SUPABASE_URL}/rest/v1/users?user_id=eq.{uid}"
        r = requests.patch(
            url,
            headers=supabase_headers(prefer="return=representation"),
            json=payload,
            timeout=15,
        )
        if r.status_code in (200, 204):
            return True, until.isoformat()
        return False, f"Ban fail {r.status_code}: {r.text[:200]}"
    except Exception as e:
        return False, str(e)


def supabase_clear_ban_if_expired(user_id: str, row: Optional[dict] = None) -> bool:
    """Hết hạn ban → status active. True nếu đã clear hoặc không còn ban."""
    uid = str(user_id)
    row = row or supabase_get_user(uid)
    if not row:
        return True
    if str(row.get("status") or "") != "banned":
        return True
    ban_until = row.get("ban_until") or ""
    if not ban_until:
        return False
    try:
        dt = parse_datetime_safe(str(ban_until))
        if dt is None:
            return False
        if datetime.now(timezone.utc) >= dt:
            url = f"{SUPABASE_URL}/rest/v1/users?user_id=eq.{uid}"
            requests.patch(
                url,
                headers=supabase_headers(prefer="return=minimal"),
                json={
                    "status": "active",
                    "ban_until": None,
                    "ban_reason": "",
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                },
                timeout=12,
            )
            return True
        return False
    except Exception:
        return False


def show_ban_screen(user_id: str = "", reason: str = "", ban_until: str = "") -> None:  # noqa: E501
    """Màn hình ban — hiện mỗi lần mở tool."""
    console.print()
    ban_info = Text()
    ban_info.append("✕  SECURITY LOCK\n\n", style=f"bold {TST_COLORS['ruby']}")
    ban_info.append("◈ USER       ", style=TST_COLORS["muted"])
    ban_info.append(f"{user_id or '?'}\n", style=f"bold {TST_COLORS['platinum']}")
    ban_info.append("◈ LÝ DO      ", style=TST_COLORS["muted"])
    ban_info.append(f"{reason or 'Đổi IP trên cùng thiết bị'}\n", style=f"bold {TST_COLORS['neon_orange']}")
    ban_info.append("◈ HẾT HẠN   ", style=TST_COLORS["muted"])
    ban_info.append(f"{str(ban_until)[:19] or 'sau 2 ngày'}\n\n", style=f"bold {TST_COLORS['gold']}")
    ban_info.append("Tool bị khóa. Liên hệ admin để gỡ ban.\n", style=TST_COLORS["platinum"])
    ban_info.append("Chạy lại tool vẫn sẽ hiện thông báo này đến hết hạn.", style=TST_COLORS["muted"])
    console.print(Panel(
        Align.center(ban_info),
        border_style=TST_COLORS["ruby"],
        box=box.HEAVY_HEAD,
        title=f"[bold {TST_COLORS['ruby']}]  ✕  ACCESS DENIED  [/]",
        padding=(1, 2),
    ))


def supabase_unban_user(user_id: str) -> tuple:
    """Admin gỡ ban user trên Supabase."""
    uid = str(user_id).strip()
    if not uid:
        return False, "user_id trống"
    try:
        url = f"{SUPABASE_URL}/rest/v1/users?user_id=eq.{uid}"
        r = requests.patch(
            url,
            headers=supabase_headers(prefer="return=representation"),
            json={
                "status": "active",
                "ban_until": None,
                "ban_reason": "",
                "updated_at": datetime.now(timezone.utc).isoformat(),
            },
            timeout=15,
        )
        if r.status_code in (200, 204):
            return True, f"Đã gỡ ban user {uid}"
        return False, f"Unban fail {r.status_code}: {r.text[:200]}"
    except Exception as e:
        return False, str(e)


def check_device_ip_integrity() -> tuple:
    """
    ĐÃ TẮT kiểm tra 'cùng máy' (fingerprint).
    Chỉ còn rule: mỗi IP 1 user trên Supabase (xem create_user / check_ip).
    Vẫn chặn nếu user đang bị ban (status=banned) theo user_id gắn IP hiện tại.
    """
    ip = _current_client_ip()
    try:
        has_user, uid, row, _msg = check_ip_user_on_supabase(ip)
    except Exception:
        return True, "skip", None
    if not has_user or not uid or not row:
        return True, "OK", None
    if str(row.get("status") or "") == "banned":
        if not supabase_clear_ban_if_expired(uid, row):
            show_ban_screen(uid, str(row.get("ban_reason") or ""), str(row.get("ban_until") or ""))
            return False, "BỊ BAN RỒI GIAN LẬN KHÔNG ĐƯỢC NỮA ĐÂU", uid
    return True, "OK", uid


def _row_to_user_data(row: dict) -> dict:
    """Map 1 row Supabase → dict user nội bộ."""
    if not row:
        return {}
    keys = row.get("keys") or []
    if isinstance(keys, str):
        try:
            keys = json.loads(keys)
        except Exception:
            keys = []
    if not isinstance(keys, list):
        keys = []
    return {
        "coins": float(row.get("coins", 0) or 0),
        "mining": bool(row.get("mining", False)),
        "mining_start": float(row.get("mining_start", 0) or 0),
        "keys": keys,
        "total_mined": float(row.get("total_mined", 0) or 0),
        "daily_claim_date": str(row.get("daily_claim_date") or ""),
        "coin_day": str(row.get("coin_day") or ""),
        "created_at": str(row.get("created_at") or ""),
        "ip": str(row.get("ip") or "unknown"),
        "note": str(row.get("note") or ""),
        "fingerprint": str(row.get("fingerprint") or ""),
        "status": str(row.get("status") or "active"),
        "ban_until": str(row.get("ban_until") or ""),
        "ban_reason": str(row.get("ban_reason") or ""),
        "checksum": "",
    }


def supabase_upsert_user(
    user_id: str,
    ip: str = "",
    coins: float = 0,
    total_mined: float = 0,
    keys_count: int = 0,
    note: str = "",
    fingerprint: str = "",
    status: str = "active",
    keys: Optional[list] = None,
    daily_claim_date: str = "",
    coin_day: str = "",
    mining: bool = False,
    mining_start: float = 0,
) -> tuple:
    """
    Lưu / cập nhật user lên Supabase (bảng users) — nguồn chính, không local.
    Trả về (ok: bool, message_or_row).
    """
    uid = str(user_id).strip()
    if not uid:
        return False, "user_id trống"

    now_iso = datetime.now(timezone.utc).isoformat()
    keys_list = keys if isinstance(keys, list) else []
    payload = {
        "user_id": uid,
        "ip": ip or "unknown",
        "coins": float(coins or 0),
        "total_mined": float(total_mined or 0),
        "keys_count": int(keys_count if keys_count is not None else len(keys_list)),
        "keys": keys_list,
        "daily_claim_date": daily_claim_date or "",
        "coin_day": coin_day or "",
        "mining": bool(mining),
        "mining_start": float(mining_start or 0),
        "note": note or "",
        "fingerprint": fingerprint or "",
        "status": status or "active",
        "updated_at": now_iso,
        "last_seen_at": now_iso,
    }

    url = f"{SUPABASE_URL}/rest/v1/users"
    headers = supabase_headers(prefer="resolution=merge-duplicates,return=representation")
    headers["Prefer"] = "resolution=merge-duplicates,return=representation"
    # PostgREST upsert
    try:
        # Thử PATCH nếu đã tồn tại
        existing = supabase_get_user(uid)
        if existing:
            patch_url = f"{SUPABASE_URL}/rest/v1/users?user_id=eq.{uid}"
            # không ghi đè created_at
            patch_body = {k: v for k, v in payload.items() if k != "user_id"}
            r = requests.patch(
                patch_url,
                headers=supabase_headers(prefer="return=representation"),
                json=patch_body,
                timeout=15,
            )
            if r.status_code in (200, 204):
                row = r.json()[0] if r.text and r.status_code == 200 and isinstance(r.json(), list) and r.json() else payload
                return True, row
            # fallback POST
        else:
            payload["created_at"] = now_iso

        r = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=15,
        )
        if r.status_code in (200, 201):
            data = r.json()
            row = data[0] if isinstance(data, list) and data else data
            return True, row
        if r.status_code == 409:
            # conflict → patch
            patch_url = f"{SUPABASE_URL}/rest/v1/users?user_id=eq.{uid}"
            r2 = requests.patch(
                patch_url,
                headers=supabase_headers(prefer="return=representation"),
                json={k: v for k, v in payload.items() if k != "user_id"},
                timeout=15,
            )
            if r2.status_code in (200, 204):
                return True, payload
            return False, f"Conflict + patch fail: {r2.status_code} {r2.text[:200]}"

        return False, f"Supabase users lỗi {r.status_code}: {r.text[:300]}"
    except Exception as e:
        return False, f"Lỗi kết nối Supabase users: {e}"


def supabase_list_users(limit: int = 50) -> list:
    """Danh sách user trên Supabase."""
    try:
        url = f"{SUPABASE_URL}/rest/v1/users?select=*&order=updated_at.desc&limit={limit}"
        r = requests.get(url, headers=supabase_headers(), timeout=15)
        if r.status_code == 200:
            return r.json() if isinstance(r.json(), list) else []
        url2 = f"{SUPABASE_URL}/rest/v1/users?select=*&limit={limit}"
        r2 = requests.get(url2, headers=supabase_headers(), timeout=15)
        if r2.status_code == 200:
            return r2.json() if isinstance(r2.json(), list) else []
        return []
    except Exception as e:
        safe_console_print(f"[red]Lỗi list users: {e}[/red]")
        return []


def sync_user_to_supabase(user_id: str, user_data: Optional[dict] = None) -> tuple:
    """Ghi user lên Supabase (nguồn chính)."""
    uid = str(user_id)
    if user_data is None:
        data = load_user_data_secure()
        user_data = data.get(uid) or {}
    ip = str(user_data.get("ip") or get_public_ip() or _ip_info.get("public_ip") or "unknown")
    keys = user_data.get("keys") or []
    if not isinstance(keys, list):
        keys = []
    fp = str(user_data.get("fingerprint") or "")
    if not fp:
        try:
            fp = get_device_fingerprint()
        except Exception:
            pass
    ok, result = supabase_upsert_user(
        user_id=uid,
        ip=ip,
        coins=float(user_data.get("coins", 0) or 0),
        total_mined=float(user_data.get("total_mined", 0) or 0),
        keys_count=len(keys),
        keys=keys,
        daily_claim_date=str(user_data.get("daily_claim_date") or ""),
        coin_day=str(user_data.get("coin_day") or ""),
        mining=bool(user_data.get("mining", False)),
        mining_start=float(user_data.get("mining_start", 0) or 0),
        note=str(user_data.get("note") or ""),
        fingerprint=fp,
        status=str(user_data.get("status") or "active"),
    )
    if ok:
        global _USER_CACHE, _USER_CACHE_TS
        _USER_CACHE[uid] = dict(user_data)
        _USER_CACHE_TS = time.time()
    return ok, result


def parse_datetime_safe(date_str):
    if not date_str or date_str == 'forever':
        return None
    try:
        if 'Z' in date_str or '+' in date_str:
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt.astimezone(timezone.utc)
        else:
            dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            return dt.replace(tzinfo=timezone.utc)
    except ValueError:
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%f")
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            return None

# ================== HEARTBEAT ==================

def heartbeat_worker():
    global _is_authenticated, _user_key, _heartbeat_running
    
    while _heartbeat_running:
        time.sleep(30)
        
        if _user_key and _is_authenticated:
            result = verify_key_with_device(_user_key)
            if not result.get("valid"):
                _is_authenticated = False
                safe_console_print("[bold red]🔒 KEY ĐÃ BỊ KHÓA HOẶC HẾT HẠN![/bold red]")
                safe_console_print("[bold red]Tool sẽ tự động thoát sau 5 giây...[/bold red]")
                time.sleep(5)
                os._exit(0)

def start_heartbeat():
    global _heartbeat_thread, _heartbeat_running
    _heartbeat_running = True
    _heartbeat_thread = threading.Thread(target=heartbeat_worker, daemon=True)
    _heartbeat_thread.start()

def stop_heartbeat():
    global _heartbeat_running
    _heartbeat_running = False

# ================== MÀN HÌNH XÁC THỰC ==================

def show_auth_choice_menu():
    while True:
        console.clear()
        print_tst_logo()
        console.print()

        tiers = Table.grid(expand=True, padding=(0, 1))
        tiers.add_column(ratio=1)
        tiers.add_column(ratio=1)

        free_body = Text()
        free_body.append("★ FREE\n", style=f"bold {TST_COLORS['gold']}")
        free_body.append("10 AI engines\nVTH + CDTD\nLotto 5 AI", style=TST_COLORS["muted"])

        vip_body = Text()
        vip_body.append("♛ VIP\n", style=f"bold {TST_COLORS['neon_pink']}")
        vip_body.append("42 AI engines\nAll modules\nPriority access", style=TST_COLORS["platinum"])

        tiers.add_row(
            Panel(Align.center(free_body), border_style=TST_COLORS["gold"], box=box.HEAVY_HEAD, padding=(1, 2)),
            Panel(Align.center(vip_body), border_style=TST_COLORS["neon_pink"], box=box.HEAVY_HEAD, padding=(1, 2)),
        )
        console.print(Panel(
            tiers,
            title=f"[bold {TST_COLORS['sapphire']}]  ♛  ACCESS GATE  —  TST-TOOL  [/]",
            border_style=TST_COLORS["sapphire"],
            box=box.HEAVY_HEAD,
            padding=(0, 1),
        ))
        # Chỉ nhập KEY — đã bỏ ADMIN và tạo user
        return show_auth_screen()



def coin_exchange_before_auth() -> None:
    """Menu nhận xu / đổi key FREE (không tạo user)."""
    while True:
        console.clear()
        console.print(Panel(
            Align.center("🎁 NHẬN XU / ĐỔI KEY FREE 🎁"),
            border_style=TST_COLORS["gold"],
            box=box.ROUNDED
        ))
        console.print()
        console.print("[1] 🎁 Nhận xu / Đổi KEY FREE 13 GIỜ")
        console.print("[q] 🔙 Quay lại")
        console.print()

        sub = Prompt.ask(
            f"[bold {TST_COLORS['gold']}]>> Chọn[/bold {TST_COLORS['gold']}]",
            choices=["1", "q"],
            default="1"
        )
        if sub == "q":
            return

        ip_now = _current_client_ip()
        bound = find_user_by_ip(ip_now)
        if bound:
            console.print(f"[dim]IP {ip_now} đã gắn user [bold]{bound}[/bold] — nên dùng đúng ID này.[/dim]")

        user_id_text = Prompt.ask(
            "[bold cyan]Nhập ID tài khoản để dùng xu[/bold cyan]",
            default=str(bound) if bound else ""
        )
        if not user_id_text.isdigit():
            console.print("[red]❌ ID tài khoản không hợp lệ![/red]")
            time.sleep(1.5)
            continue
        user_id = int(user_id_text)

        data = load_user_data_secure()
        if str(user_id) not in data:
            console.print(f"[red]❌ User {user_id} chưa tồn tại. Liên hệ hỗ trợ @tst-tool88.[/red]")
            time.sleep(2)
            continue

        ok_access, access_msg = verify_user_id_access(user_id)
        if not ok_access:
            console.print(Panel(
                Text(access_msg, style="bold red"),
                title="[bold red]CHỐNG NHẬP BỪA ID[/bold red]",
                border_style=TST_COLORS["ruby"],
                box=box.ROUNDED,
            ))
            time.sleep(2.5)
            continue

        success, msg = claim_daily_coins_secure(user_id)
        console.print(f"[green]✅ {msg}[/green]" if success else f"[yellow]ℹ️ {msg}[/yellow]")
        balance = get_user_balance_secure(user_id)
        console.print(f"\n[bold green]💰 Số dư: {balance.get('coins', 0):.2f} xu[/bold green]")
        console.print("[dim]🔑 5 xu = KEY FREE 13 GIỜ[/dim]\n")

        if balance.get("coins", 0) >= FREE_KEY_PRICE:
            confirm = Prompt.ask(
                "[bold cyan]Đổi 5 xu lấy KEY FREE 13 GIỜ? (y/n)[/bold cyan]",
                choices=["y", "n"],
                default="y"
            )
            if confirm == "y":
                with console.status("[bold yellow]⏳ Đang tạo key trên Supabase...[/bold yellow]", spinner="dots"):
                    ok, result = exchange_free_key_13h_secure(user_id)
                if ok:
                    console.print(Panel(
                        Text.assemble(
                            ("✅ ĐỔI KEY THÀNH CÔNG!\n\n", "bold green"),
                            ("KEY: ", "bold white"), (f"{result}\n", f"bold {TST_COLORS['gold']}"),
                            ("Loại: FREE\n", "bold cyan"),
                            ("Thời hạn: 13 GIỜ\n", "bold green"),
                            ("💡 Dùng key này ở menu NHẬP KEY để đăng nhập.", "dim"),
                        ),
                        border_style=TST_COLORS["emerald"],
                        box=box.ROUNDED
                    ))
                else:
                    console.print(f"[red]❌ {result}[/red]")
        else:
            console.print("[yellow]⚠️ Chưa đủ 5 xu để đổi key.[/yellow]")
        input("\n[dim]Nhấn Enter để quay lại...[/dim]")



def show_auth_screen():
    global _key_type, _secure_mode
    
    if not anti_crack_check():
        return False, None, "free"
    
    if not enhanced_auth_check():
        console.print("[red]❌ Xác thực IP thất bại![/red]")
        time.sleep(2)
        return False, None, "free"
    
    console.clear()
    gold_color = TST_COLORS["gold"]
    print_tst_logo()
    console.print()
    console.print(Rule(f"[bold {TST_COLORS['gold']}]  ♛  XÁC THỰC KEY  [/]", style=TST_COLORS["sapphire"]))
    console.print()
    
    # Access tier display
    access_grid = Table.grid(expand=True, padding=(0, 2))
    access_grid.add_column(ratio=1); access_grid.add_column(ratio=1)

    free_info = Text()
    free_info.append("★ FREE KEY\n", style=f"bold {TST_COLORS['gold']}")
    free_info.append("· 10 AI engines\n", style=TST_COLORS["muted"])
    free_info.append("· VTH + CDTD\n", style=TST_COLORS["muted"])
    free_info.append("· Lotto 5 AI", style=TST_COLORS["muted"])

    vip_info = Text()
    vip_info.append("♛ VIP KEY\n", style=f"bold {TST_COLORS['neon_pink']}")
    vip_info.append("· 42 AI engines\n", style=TST_COLORS["platinum"])
    vip_info.append("· All modules unlocked\n", style=TST_COLORS["platinum"])
    vip_info.append("· Priority + Lotto full", style=TST_COLORS["platinum"])

    access_grid.add_row(
        Panel(free_info,  border_style=TST_COLORS["gold"],     box=box.SIMPLE, padding=(0,1)),
        Panel(vip_info,   border_style=TST_COLORS["neon_pink"],box=box.SIMPLE, padding=(0,1)),
    )

    sec_body = Text()
    sec_body.append("◈ Anti-Crack   ", style=f"bold {TST_COLORS['emerald']}")
    sec_body.append("ACTIVE  ", style=TST_COLORS["muted"])
    sec_body.append("⬡ IP Guard   ", style=f"bold {TST_COLORS['turquoise']}")
    sec_body.append("ACTIVE  ", style=TST_COLORS["muted"])
    sec_body.append("⬡ Anti-Detection   ", style=f"bold {TST_COLORS['sapphire']}")
    sec_body.append("ACTIVE", style=TST_COLORS["muted"])

    console.print(Panel(
        Group(access_grid, Rule(style=TST_COLORS["accent_line"]), Align.center(sec_body)),
        title=f"[bold {TST_COLORS['sapphire']}]  ◉  ACCESS OVERVIEW  [/]",
        border_style=TST_COLORS["sapphire"],
        box=box.HEAVY_HEAD,
        padding=(0, 1),
    ))
    console.print()

    console.print(Panel(
        Text.assemble(("◈  ", f"bold {TST_COLORS['gold']}"), ("Nhập Key xác thực để tiếp tục", TST_COLORS["platinum"])),
        border_style=TST_COLORS["gold"],
        box=box.SIMPLE,
        padding=(0, 1),
    ))
    console.print()

    console.print(Panel(
        Text.assemble(
            ("◈ KEY FORMAT  ", f"bold {TST_COLORS['muted']}"),
            ("TST-TOOL_XXXXX", f"bold {TST_COLORS['gold']}"),
            ("  hoặc  ", TST_COLORS["muted"]),
            ("FREE_XXXXX", f"bold {TST_COLORS['sapphire']}"),
        ),
        border_style=TST_COLORS["accent_line"],
        box=box.SIMPLE,
        padding=(0, 1),
    ))
    key = Prompt.ask(
        f"[bold {TST_COLORS['gold']}] ♛  NHẬP KEY[/bold {TST_COLORS['gold']}]"
        f"[{TST_COLORS['accent_line']}] ──────────── [/{TST_COLORS['accent_line']}]"
        f"[bold {TST_COLORS['emerald']}]▶[/bold {TST_COLORS['emerald']}]",
        default=""
    )
    
    if not key:
        console.print("[red]❌ Key không được để trống![/red]")
        time.sleep(1.5)
        return False, None, "free"
    
    # Đã bỏ xoay IP / chống soi
    global _secure_mode, _secure_tool
    _secure_mode = False
    _secure_tool = None

    with console.status(f"[bold yellow]⏳ Đang xác thực...[/bold yellow]", spinner="dots") as status:
        time.sleep(0.5)
        result = verify_key_with_device(key)
    
    if result.get("valid"):
        console.print()
        data = result.get("data", {})
        key_type = data.get("key_type", "free")
        max_ai = data.get("max_ai", 10)
        
        global _key_type, _key_expiry_info, _key_expires_at
        expiry_info = "Vĩnh viễn"
        expires_at = data.get('expires_at')
        _key_expires_at = None
        if expires_at and str(expires_at).lower() not in ('forever', 'none', ''):
            try:
                expiry_dt = parse_datetime_safe(expires_at)
                if expiry_dt:
                    if expiry_dt.tzinfo is None:
                        expiry_dt = expiry_dt.replace(tzinfo=timezone.utc)
                    _key_expires_at = expiry_dt
                    now_utc = datetime.now(timezone.utc)
                    time_left = expiry_dt - now_utc
                    if time_left.total_seconds() <= 0:
                        expiry_info = "Đã hết hạn"
                    else:
                        days = time_left.days
                        hours = time_left.seconds // 3600
                        minutes = (time_left.seconds % 3600) // 60
                        # ngày hết hạn local
                        local_exp = expiry_dt.astimezone()
                        date_s = local_exp.strftime("%d/%m/%Y %H:%M")
                        if days > 0:
                            expiry_info = f"Còn {days} ngày {hours} giờ (đến {date_s})"
                        elif hours > 0:
                            expiry_info = f"Còn {hours} giờ {minutes} phút (đến {date_s})"
                        else:
                            expiry_info = f"Còn {minutes} phút (đến {date_s})"
            except Exception:
                expiry_info = str(expires_at)
        _key_expiry_info = expiry_info
        _key_type = key_type
        
        key_icon = "👑" if key_type == "vip" else "🔑"
        key_color = "bold gold" if key_type == "vip" else "bold white"
        
        # Auth success — premium dark card
        auth_grid = Table.grid(expand=True, padding=(0, 2))
        auth_grid.add_column(ratio=1); auth_grid.add_column(ratio=1)

        left_info = Text()
        left_info.append("◈ KEY\n", style=f"bold {TST_COLORS['muted']}")
        left_info.append(f"{key}\n\n", style=f"bold {TST_COLORS['gold']}")
        left_info.append("◈ LOẠI\n", style=f"bold {TST_COLORS['muted']}")
        left_info.append(f"{key_icon} {key_type.upper()}\n\n", style=key_color)
        left_info.append("◈ ENGINE AI\n", style=f"bold {TST_COLORS['muted']}")
        left_info.append(f"{max_ai} / 42 AI", style=f"bold {TST_COLORS['neon_blue']}")

        right_info = Text()
        right_info.append("◈ TRẠNG THÁI\n", style=f"bold {TST_COLORS['muted']}")
        right_info.append("● ACTIVE\n\n", style=f"bold {TST_COLORS['emerald']}")
        right_info.append("◈ THỜI HẠN KEY\n", style=f"bold {TST_COLORS['muted']}")
        right_info.append(f"{expiry_info}\n\n", style=f"bold {TST_COLORS['gold']}")

        auth_grid.add_row(
            Panel(left_info,  border_style=TST_COLORS["accent_line"], box=box.SIMPLE, padding=(0,1)),
            Panel(right_info, border_style=TST_COLORS["accent_line"], box=box.SIMPLE, padding=(0,1)),
        )

        sec_strip = Text()
        sec_strip.append("◈ Anti-Crack  ACTIVE  ", style=f"bold {TST_COLORS['emerald']}")
        sec_strip.append(f"· IP: {_ip_info.get('public_ip', 'N/A')}  ", style=TST_COLORS["muted"])
        sec_strip.append(f"· Used: {data.get('used_count',0)}/{data.get('max_uses','∞')}", style=TST_COLORS["muted"])

        console.print(Panel(
            Group(auth_grid, Rule(style=TST_COLORS["accent_line"]), Align.center(sec_strip)),
            title=f"[bold {TST_COLORS['emerald']}]  ✓  XÁC THỰC THÀNH CÔNG  [/]",
            border_style=TST_COLORS["emerald"],
            box=box.HEAVY_HEAD,
            padding=(0, 1),
        ))
        
        console.print()
        console.print("[dim]Nhấn Enter để tiếp tục...[/dim]")
        input()
        
        return True, key, key_type
    else:
        console.print()
        console.print(Panel(
            Text.assemble(
                ("✕  XÁC THỰC THẤT BẠI\n\n", f"bold {TST_COLORS['ruby']}"),
                ("◈ Lỗi   ", f"bold {TST_COLORS['muted']}"),
                (f"{result.get('error', 'Không xác định')}\n\n", f"bold {TST_COLORS['ruby']}"),
                ("Vui lòng kiểm tra lại Key và thử lại.", TST_COLORS["muted"]),
            ),
            title=f"[bold {TST_COLORS['ruby']}]  ✕  THẤT BẠI  [/]",
            border_style=TST_COLORS["ruby"],
            box=box.HEAVY_HEAD,
            padding=(1, 2),
        ))
        console.print()
        console.print("[dim]Nhấn Enter để thử lại...[/dim]")
        input()
        return False, None, "free"

def require_valid_auth() -> bool:
    global _is_authenticated
    return _is_authenticated

def safe_console_print(*args, **kwargs):
    try:
        console.print(*args, **kwargs)
    except:
        pass

def safe_console_status(message, spinner="dots"):
    return console.status(message, spinner=spinner)

# ================== TELEGRAM ==================

def send_telegram_message(message: str) -> bool:
    if not TELEGRAM_ENABLED or not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML", "disable_web_page_preview": True}
        
        if _secure_tool and _secure_tool.is_stealth:
            response = _secure_tool.make_secure_request(url, method='POST', json=payload, timeout=10)
            return response.status_code == 200 if response else False
        else:
            response = requests.post(url, json=payload, timeout=10)
            return response.status_code == 200
    except:
        return False

def setup_telegram():
    global TELEGRAM_CHAT_ID, TELEGRAM_ENABLED
    console.clear()
    header = Panel(Align.center(Text.assemble((f"{ICONS['bell']} ", f"bold {TST_COLORS['gold']}"), ("CẤU HÌNH THÔNG BÁO TELEGRAM", f"bold {TST_COLORS['neon_blue']}"))), border_style=TST_COLORS["gold"], box=box.ROUNDED)
    console.print(header)
    console.print()
    console.print(Panel(Text.assemble(("🤖 BOT TELEGRAM CHÍNH THỨC\n\n", f"bold {TST_COLORS['neon_blue']}"), ("Bot: @tst-tool88_bot\n", f"bold {TST_COLORS['gold']}"), ("Link: https://t.me/tst-tool88_bot\n\n", f"bold {TST_COLORS['sapphire']}"), ("Bot sẽ gửi thông báo RIÊNG cho bạn sau mỗi ván.\n", "white")), border_style=TST_COLORS["sapphire"], box=box.ROUNDED))
    console.print()
    console.print(f"[bold {TST_COLORS['gold']}]Bạn có muốn nhận thông báo qua Telegram?[/]")
    if Prompt.ask(f"[bold {TST_COLORS['gold']}]>> Chọn (y/n)[/]", choices=['y', 'n'], default='n') == 'n':
        TELEGRAM_ENABLED = False
        console.print(f"[yellow]⚠️ Thông báo Telegram đã tắt[/]")
        time.sleep(1)
        return
    TELEGRAM_ENABLED = True
    console.print()
    console.print("[bold]📖 CÁCH LẤY CHAT ID:[/]")
    console.print("1. Chat /start với bot @tst-tool88_bot")
    console.print("2. Vào @userinfobot để lấy ID của bạn")
    console.print("3. Copy dãy số và dán vào đây\n")
    saved_chat_id = ""
    if os.path.exists('telegram_config.json'):
        try:
            with open('telegram_config.json', 'r', encoding='utf-8') as f:
                saved_chat_id = json.load(f).get('chat_id', '')
        except:
            pass
    if saved_chat_id:
        console.print(f"[bold {TST_COLORS['emerald']}]📂 Đã tìm thấy Chat ID: {saved_chat_id}[/]")
        if Prompt.ask(f"[bold {TST_COLORS['gold']}]Sử dụng? (y/n)[/]", choices=['y', 'n'], default='y') == 'y':
            TELEGRAM_CHAT_ID = saved_chat_id
        else:
            TELEGRAM_CHAT_ID = Prompt.ask(f"[bold {TST_COLORS['gold']}]📱 Nhập Chat ID mới[/]", default="")
    else:
        TELEGRAM_CHAT_ID = Prompt.ask(f"[bold {TST_COLORS['gold']}]📱 Nhập Chat ID của bạn[/]", default="")
    TELEGRAM_CHAT_ID = ''.join(c for c in TELEGRAM_CHAT_ID if c.isdigit())
    if not TELEGRAM_CHAT_ID:
        console.print(f"[red]❌ Chat ID không hợp lệ![/]")
        TELEGRAM_ENABLED = False
        time.sleep(2)
        return
    console.print(f"\n[bold yellow]🔍 Đang kiểm tra kết nối...[/]")
    test_msg = f"✅ <b>KẾT NỐI THÀNH CÔNG!</b>\n\n🔔 <b>TST-TOOL PREMIUM - Thông báo đã kích hoạt</b>\n🕐 <b>{datetime.now(tz).strftime('%H:%M:%S %d/%m/%Y')}</b>"
    if send_telegram_message(test_msg):
        console.print(f"[green]✅ Kết nối thành công! Kiểm tra Telegram nhé![/]")
        try:
            with open('telegram_config.json', 'w', encoding='utf-8') as f:
                json.dump({'chat_id': TELEGRAM_CHAT_ID}, f, indent=2)
        except:
            pass
    else:
        console.print(f"[red]❌ Không thể gửi tin nhắn![/]")
        console.print(f"[yellow]  Hãy chắc chắn bạn đã chat /start với bot![/]")
        if Prompt.ask(f"[bold {TST_COLORS['gold']}]Nhập lại? (y/n)[/]", choices=['y', 'n'], default='y') == 'y':
            setup_telegram()
            return
        else:
            TELEGRAM_ENABLED = False
    time.sleep(2)
    # ================== HỆ THỐNG MÃ HÓA JSON ==================

ENCRYPTION_KEY = b'tst-tool_v3_secret_key_2024_encryption_secure_'
SALT = b'tst-tool_salt_2024_secure_'

def generate_encryption_key():
    """Tạo key mã hóa từ password"""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=SALT,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(ENCRYPTION_KEY))
    return key

FERNET_KEY = generate_encryption_key()
cipher = Fernet(FERNET_KEY)

def encrypt_data(data: dict) -> str:
    """Mã hóa dữ liệu dict thành string"""
    try:
        json_str = json.dumps(data, ensure_ascii=False)
        encrypted = cipher.encrypt(json_str.encode('utf-8'))
        return base64.urlsafe_b64encode(encrypted).decode('utf-8')
    except Exception as e:
        print(f"Lỗi mã hóa: {e}")
        return None

def decrypt_data(encrypted_data: str) -> dict:
    """Giải mã dữ liệu từ string thành dict"""
    try:
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode('utf-8'))
        decrypted = cipher.decrypt(encrypted_bytes)
        return json.loads(decrypted.decode('utf-8'))
    except Exception as e:
        print(f"Lỗi giải mã: {e}")
        return None

def save_encrypted_json(filepath: str, data: dict):
    """Lưu dữ liệu đã mã hóa vào file"""
    try:
        encrypted = encrypt_data(data)
        if encrypted:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(encrypted)
            return True
    except Exception as e:
        print(f"Lỗi lưu file mã hóa: {e}")
    return False

def load_encrypted_json(filepath: str) -> dict:
    """Load dữ liệu đã mã hóa từ file"""
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                encrypted = f.read()
            return decrypt_data(encrypted)
    except Exception as e:
        print(f"Lỗi load file mã hóa: {e}")
    return {}

# ================== HỆ THỐNG CHỐNG BYPASS XU ==================

SECURITY_SALT = b'tst-tool_security_salt_2024_very_secure_'
CHECKSUM_KEY = b'tst-tool_checksum_key_2024_secret_'

def generate_checksum(data: dict, user_id: str) -> str:
    """Tạo checksum cho dữ liệu user"""
    try:
        check_data = f"{user_id}:{data.get('coins', 0)}:{data.get('total_mined', 0)}:{len(data.get('keys', []))}:{data.get('mining', False)}"
        h = hmac.new(CHECKSUM_KEY, check_data.encode(), hashlib.sha256)
        return h.hexdigest()
    except Exception as e:
        print(f"Lỗi tạo checksum: {e}")
        return None

def verify_checksum(data: dict, user_id: str) -> bool:
    """Kiểm tra checksum. Nguồn Supabase (cloud) không bắt buộc checksum local."""
    try:
        if not isinstance(data, dict):
            return False
        # Cloud-first: không có checksum hoặc rỗng → tin Supabase
        stored = data.get("checksum")
        if not stored:
            return True
        current_checksum = generate_checksum(data, user_id)
        if current_checksum is None:
            return False
        return hmac.compare_digest(current_checksum, stored)
    except Exception as e:
        print(f"Lỗi verify checksum: {e}")
        return False

def add_checksum_to_data(data: dict, user_id: str) -> dict:
    """Thêm checksum vào dữ liệu"""
    checksum = generate_checksum(data, user_id)
    if checksum:
        data['checksum'] = checksum
    return data

def detect_data_anomaly(data: dict, user_id: str) -> tuple:
    """Phát hiện dữ liệu bất thường"""
    warnings = []
    is_anomaly = False
    
    if data.get('coins', 0) < 0:
        warnings.append("Số xu âm")
        is_anomaly = True
    
    if data.get('coins', 0) > 1000000000:
        warnings.append("Số xu quá lớn (> 1 tỷ)")
        is_anomaly = True
    
    if data.get('total_mined', 0) > data.get('coins', 0) + 1000:
        warnings.append("Tổng đào lớn hơn số dư đáng kể")
        is_anomaly = True
    
    if data.get('mining', False):
        start_time = data.get('mining_start', 0)
        if start_time > time.time():
            warnings.append("Thời gian đào trong tương lai")
            is_anomaly = True
    
    keys = data.get('keys', [])
    if len(keys) > 100:
        warnings.append(f"Số key quá nhiều ({len(keys)})")
        is_anomaly = True
    
    return is_anomaly, warnings

def fix_corrupted_data(data: dict, user_id: str) -> dict:
    """Sửa dữ liệu bị hỏng hoặc bị hack"""
    fixed = False
    
    if data.get('coins', 0) < 0:
        data['coins'] = 0
        fixed = True
    
    if data.get('coins', 0) > 10000000:
        data['coins'] = 10000000
        fixed = True
    
    if data.get('total_mined', 0) < 0:
        data['total_mined'] = data.get('coins', 0)
        fixed = True
    
    if data.get('mining_start', 0) > time.time():
        data['mining_start'] = time.time()
        fixed = True
    
    if 'keys' in data:
        seen = set()
        unique_keys = []
        for key in data['keys']:
            key_tuple = (key.get('type', ''), key.get('purchased', 0))
            if key_tuple not in seen:
                seen.add(key_tuple)
                unique_keys.append(key)
        if len(unique_keys) != len(data['keys']):
            data['keys'] = unique_keys
            fixed = True
    
    if fixed:
        safe_console_print(f"[yellow]⚠️ Đã phát hiện và sửa dữ liệu bất thường cho user {user_id}[/yellow]")
    
    return data

# ================== FILE LƯU TRỮ ==================

USER_DATA_FILE = "user_data.enc"
KEY_SHOP_FILE = "key_shop.enc"

MINING_RATE = 0.01
MINING_INTERVAL = 1

KEY_PRICES = {
    "24h": 5,
    "7d": 30,
    "30d": 100,
    "90d": 250,
}

# ================== XU HẰNG NGÀY / ĐỔI KEY FREE ==================
DAILY_COIN_REWARD = 5
FREE_KEY_PRICE = 5
FREE_KEY_DURATION = 13 * 3600
# Xu nhận trong ngày nếu không dùng (đổi key) → qua ngày hôm sau bị reset về 0


def _today_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def apply_daily_coin_expiry(user_data: dict, user_id: str = "") -> tuple:
    """
    Nếu xu còn từ ngày trước mà chưa dùng hết → reset về 0 khi sang ngày mới.
    Trả về (user_data, did_reset: bool, message).
    """
    if not isinstance(user_data, dict):
        return user_data, False, ""

    today = _today_str()
    # Ngày gắn với số xu hiện có: ưu tiên coin_day, fallback daily_claim_date
    coin_day = str(user_data.get("coin_day") or user_data.get("daily_claim_date") or "").strip()
    coins = float(user_data.get("coins", 0) or 0)

    # Chưa có mốc ngày → gán hôm nay nếu đang có xu (tránh reset ngay user cũ)
    if not coin_day:
        if coins > 0:
            user_data["coin_day"] = today
        return user_data, False, ""

    # Cùng ngày → giữ nguyên
    if coin_day >= today:
        return user_data, False, ""

    # Đã qua ngày → xu chưa dùng bị hủy
    if coins > 0:
        user_data["coins"] = 0
        user_data["coin_day"] = today
        msg = f"Xu ngày {coin_day} hết hạn (không dùng) → reset 0. Hôm nay nhận lại {DAILY_COIN_REWARD} xu."
        if user_id:
            safe_console_print(f"[yellow]⚠️ User {user_id}: {msg}[/yellow]")
        return user_data, True, msg

    user_data["coin_day"] = today
    return user_data, False, ""

# ================== HÀM QUẢN LÝ USER DATA (SUPABASE ONLY) ==================

def load_user_data_secure():
    """
    Load toàn bộ user từ Supabase (không đọc file local).
    Cache RAM ngắn để giảm request.
    """
    global _USER_CACHE, _USER_CACHE_TS
    now = time.time()
    if _USER_CACHE and (now - _USER_CACHE_TS) < _USER_CACHE_TTL:
        return {k: dict(v) for k, v in _USER_CACHE.items()}

    rows = supabase_list_users(limit=500)
    data: Dict[str, dict] = {}
    for row in rows or []:
        uid = str(row.get("user_id") or "").strip()
        if not uid:
            continue
        ud = _row_to_user_data(row)
        is_anomaly, _ = detect_data_anomaly(ud, uid)
        if is_anomaly:
            ud = fix_corrupted_data(ud, uid)
        data[uid] = ud

    _USER_CACHE = {k: dict(v) for k, v in data.items()}
    _USER_CACHE_TS = now
    return {k: dict(v) for k, v in data.items()}


def save_user_data_secure(data):
    """
    Lưu user lên Supabase (không ghi user_data.enc).
    Upsert từng user trong dict.
    """
    global _USER_CACHE, _USER_CACHE_TS
    if not isinstance(data, dict):
        return False
    ok_all = True
    try:
        for user_id, user_data in data.items():
            uid = str(user_id)
            if not isinstance(user_data, dict):
                continue
            is_anomaly, warnings = detect_data_anomaly(user_data, uid)
            if is_anomaly:
                safe_console_print(f"[red]🚨 Dữ liệu bất thường user {uid}[/red]")
                for w in warnings:
                    safe_console_print(f"[red]  - {w}[/red]")
                user_data = fix_corrupted_data(user_data, uid)
            data[uid] = user_data
            sb_ok, sb_msg = sync_user_to_supabase(uid, user_data)
            if not sb_ok:
                ok_all = False
                safe_console_print(f"[red]❌ Lưu Supabase user {uid}: {sb_msg}[/red]")
        _USER_CACHE = {k: dict(v) for k, v in data.items()}
        _USER_CACHE_TS = time.time()
        return ok_all
    except Exception as e:
        safe_console_print(f"[red]❌ Lỗi lưu Supabase users: {e}[/red]")
        return False

def load_key_shop():
    """Load bảng giá key"""
    data = load_encrypted_json(KEY_SHOP_FILE)
    if data is None or not data:
        save_key_shop(KEY_PRICES)
        return KEY_PRICES
    return data

def save_key_shop(prices):
    """Lưu bảng giá key"""
    return save_encrypted_json(KEY_SHOP_FILE, prices)

def migrate_old_data():
    """Chuyển đổi dữ liệu từ file JSON cũ sang file mã hóa"""
    old_user_file = "user_data.json"
    old_key_file = "key_shop.json"
    
    if os.path.exists(old_user_file):
        try:
            with open(old_user_file, 'r', encoding='utf-8') as f:
                old_data = json.load(f)
            if old_data:
                for user_id, user_data in old_data.items():
                    old_data[user_id] = add_checksum_to_data(user_data, user_id)
                save_encrypted_json(USER_DATA_FILE, old_data)
                print(f"[green]✅ Đã chuyển đổi {old_user_file} sang mã hóa[/green]")
                os.rename(old_user_file, f"{old_user_file}.backup")
        except Exception as e:
            print(f"[yellow]⚠️ Lỗi chuyển đổi {old_user_file}: {e}[/yellow]")
    
    if os.path.exists(old_key_file):
        try:
            with open(old_key_file, 'r', encoding='utf-8') as f:
                old_data = json.load(f)
            if old_data:
                save_encrypted_json(KEY_SHOP_FILE, old_data)
                print(f"[green]✅ Đã chuyển đổi {old_key_file} sang mã hóa[/green]")
                os.rename(old_key_file, f"{old_key_file}.backup")
        except Exception as e:
            print(f"[yellow]⚠️ Lỗi chuyển đổi {old_key_file}: {e}[/yellow]")

# ================== HÀM XỬ LÝ USER ==================

def find_user_by_ip(ip: str) -> Optional[str]:
    """
    Tìm user_id gắn với IP — ưu tiên Supabase (nguồn chính), fallback cache.
    Mỗi IP chỉ 1 user vĩnh viễn.
    """
    if not ip or ip == "unknown":
        return None
    # 1) Supabase
    try:
        row = supabase_find_user_by_ip(ip)
        if row and row.get("user_id"):
            return str(row["user_id"])
    except Exception:
        pass
    # 2) Cache / list đã load
    data = load_user_data_secure()
    for uid, udata in data.items():
        if str(udata.get("ip", "")) == str(ip):
            return str(uid)
    return None


def check_ip_user_on_supabase(ip: str = "") -> tuple:
    """
    Kiểm tra IP hiện tại trên Supabase.
    Trả về (has_user: bool, user_id_or_None, row_or_None, message).
    """
    ip = ip or _current_client_ip()
    if not ip or ip == "unknown":
        return False, None, None, "Không lấy được IP công khai. Kiểm tra mạng."
    try:
        row = supabase_find_user_by_ip(ip)
    except Exception as e:
        return False, None, None, f"Không kết nối Supabase: {e}"
    if row and row.get("user_id"):
        uid = str(row["user_id"])
        return True, uid, row, f"IP {ip} đã gắn user {uid} trên Supabase (vĩnh viễn)."
    return False, None, None, f"IP {ip} chưa có user trên Supabase — cần tạo user."


def _current_client_ip() -> str:
    return get_public_ip() or _ip_info.get("public_ip") or "unknown"


def revoke_user_keys_abuse(user_id: str, reason: str = "IP mismatch / nhập bừa ID") -> int:
    """
    Thu hồi ngay toàn bộ key local của user + cố gắng vô hiệu hóa trên Supabase.
    Dùng khi phát hiện cố truy cập ID không thuộc IP hiện tại.
    Trả về số key đã thu hồi local.
    """
    data = load_user_data_secure()
    uid = str(user_id)
    if uid not in data:
        return 0

    user_data = data[uid]
    keys = list(user_data.get("keys", []) or [])
    if not keys:
        return 0

    revoked = 0
    for item in keys:
        key_code = str(item.get("key", "") or "").strip()
        if key_code:
            try:
                supabase_deactivate_key(key_code)
            except Exception:
                pass
            revoked += 1

    user_data["keys"] = []
    user_data["note"] = (user_data.get("note") or "") + f" | REVOKED:{reason}@{datetime.now(tz).isoformat()}"
    user_data["coins"] = 0  # chặn luôn lợi dụng xu sau khi bị bắt
    data[uid] = add_checksum_to_data(user_data, uid)
    save_user_data_secure(data)

    safe_console_print(
        f"[bold red]🚨 ĐÃ THU HỒI {revoked} KEY của user {uid} — lý do: {reason}[/bold red]"
    )
    return revoked


def verify_user_id_access(user_id, *, allow_missing: bool = False) -> tuple:
    """
    Chống nhập bừa ID — kiểm tra Supabase:
    - User phải tồn tại trên Supabase (trừ allow_missing).
    - IP hiện tại phải khớp IP gắn user trên Supabase.
    - IP hiện tại chỉ được 1 user (vĩnh viễn).
    - Sai IP + còn key → thu hồi key ngay.
    """
    uid = str(user_id).strip()
    if not uid.isdigit():
        return False, "ID tài khoản không hợp lệ! Chỉ nhập số."

    ip = _current_client_ip()

    # Nguồn chính: Supabase
    sb_row = supabase_get_user(uid)
    if not sb_row:
        if allow_missing:
            return True, "OK"
        return False, (
            f"User {uid} không tồn tại trên Supabase.\n"
            f"   IP {ip}: hãy tạo user (mỗi IP chỉ 1 user vĩnh viễn)."
        )

    stored_ip = str(sb_row.get("ip") or "")
    keys = sb_row.get("keys") or []
    if isinstance(keys, str):
        try:
            keys = json.loads(keys)
        except Exception:
            keys = []
    if not isinstance(keys, list):
        keys = []
    active_keys = [k for k in keys if float(k.get("expires", 0) or 0) > time.time()]

    if stored_ip and stored_ip != "unknown" and ip != "unknown" and stored_ip != ip:
        if active_keys or keys:
            revoke_user_keys_abuse(uid, reason=f"IP mismatch (stored={stored_ip}, now={ip})")
            return False, (
                f"❌ ID {uid} không thuộc IP của bạn!\n"
                f"   IP gắn user (Supabase): {stored_ip} | IP hiện tại: {ip}\n"
                f"   🚨 Key đã bị THU HỒI NGAY."
            )
        return False, (
            f"❌ ID {uid} không thuộc IP của bạn!\n"
            f"   IP gắn user (Supabase): {stored_ip} | IP hiện tại: {ip}"
        )

    # IP này đã gắn user khác trên Supabase?
    owner = find_user_by_ip(ip)
    if owner and owner != uid:
        return False, (
            f"❌ IP {ip} đang gắn user {owner} trên Supabase.\n"
            f"   Không dùng được ID {uid}. Mỗi IP chỉ 1 user."
        )

    return True, "OK"


def display_user_info(user_id: str, user_data: dict) -> None:
    """Hiển thị thông tin user đã lưu."""
    keys = user_data.get("keys", []) or []
    valid = [k for k in keys if float(k.get("expires", 0) or 0) > time.time()]
    console.print(Panel(
        Text.assemble(
            ("👤 THÔNG TIN USER\n\n", f"bold {TST_COLORS['gold']}"),
            ("ID: ", "bold white"), (f"{user_id}\n", f"bold {TST_COLORS['neon_blue']}"),
            ("IP: ", "bold white"), (f"{user_data.get('ip', 'N/A')}\n", "dim"),
            ("Xu: ", "bold white"), (f"{user_data.get('coins', 0):.2f}\n", f"bold {TST_COLORS['emerald']}"),
            ("Keys còn hạn: ", "bold white"), (f"{len(valid)}\n", f"bold {TST_COLORS['neon_pink']}"),
            ("Tạo lúc: ", "bold white"), (f"{user_data.get('created_at', 'N/A')}\n", "dim"),
            ("Ghi chú: ", "bold white"), (f"{user_data.get('note', '')}\n", "dim"),
        ),
        border_style=TST_COLORS["gold"],
        box=box.ROUNDED
    ))
    if valid:
        for k in valid[-5:]:
            console.print(f"  🔑 {k.get('key', '?')} | {k.get('type', '')} | hết hạn: {datetime.fromtimestamp(float(k.get('expires', 0))).strftime('%d/%m %H:%M')}")


def create_user_secure(user_id: int) -> tuple:
    """
    Tạo user mới — CHỈ lưu Supabase (không local).
    ĐÃ CÓ USER (theo IP hoặc mã thiết bị) → KHÔNG được tạo mới.
    Mỗi IP / mỗi thiết bị chỉ 1 user vĩnh viễn.
    """
    uid = str(user_id).strip()
    if not uid.isdigit():
        return False, "ID tài khoản không hợp lệ! Chỉ nhập số."

    ip = _current_client_ip()
    if not ip or ip == "unknown":
        return False, "Không lấy được IP công khai. Không thể tạo user."

    # --- 1) IP đã có user trên Supabase → KHÔNG tạo thêm (vĩnh viễn) ---
    # (Đã bỏ rule 'cùng máy' / fingerprint)
    has_user, bound_uid, bound_row, ip_msg = check_ip_user_on_supabase(ip)
    if has_user and bound_uid:
        try:
            display_user_info(bound_uid, _row_to_user_data(bound_row or {}))
        except Exception:
            pass
        return False, (
            f"❌ Đã có user {bound_uid} trên IP {ip}.\n"
            f"   Không được tạo user mới. Mỗi IP chỉ 1 user vĩnh viễn."
        )

    # --- 2) user_id đã tồn tại trên Supabase → không tạo trùng ---
    sb_by_uid = supabase_get_user(uid)
    if sb_by_uid:
        stored_ip = str(sb_by_uid.get("ip") or "")
        display_user_info(uid, _row_to_user_data(sb_by_uid))
        return False, (
            f"❌ User {uid} đã tồn tại trên Supabase"
            + (f" (IP: {stored_ip})" if stored_ip else "")
            + ".\n   Không được tạo lại / chiếm ID này."
        )

    # --- 3) Tạo mới chỉ trên Supabase (theo IP, không ghim máy) ---
    user_payload = {
        "coins": 0,
        "mining": False,
        "mining_start": 0,
        "keys": [],
        "total_mined": 0,
        "daily_claim_date": "",
        "coin_day": "",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "ip": ip,
        "note": "created_via_tst-tool",
        "fingerprint": "",
        "status": "active",
        "checksum": "",
    }

    sb_ok, sb_result = supabase_upsert_user(
        user_id=uid,
        ip=ip,
        coins=0,
        total_mined=0,
        keys_count=0,
        keys=[],
        daily_claim_date="",
        coin_day="",
        mining=False,
        mining_start=0,
        note="created_via_tst-tool",
        fingerprint="",
        status="active",
    )
    if not sb_ok:
        return False, f"Không lưu được lên Supabase: {sb_result}"

    # Cập nhật cache RAM
    global _USER_CACHE, _USER_CACHE_TS
    _USER_CACHE[uid] = dict(user_payload)
    _USER_CACHE_TS = time.time()

    display_user_info(uid, user_payload)
    return True, f"✅ Tạo user {uid} thành công · IP {ip} · đã lưu Supabase (vĩnh viễn 1 IP = 1 user)."


def ensure_user_for_current_ip(*, force_prompt: bool = True) -> Optional[str]:
    """
    Kiểm tra IP trên Supabase:
    - Đã có user → trả về user_id
    - Chưa có → bắt buộc tạo (prompt) rồi trả về user_id mới
    """
    ip = _current_client_ip()
    has_user, uid, row, msg = check_ip_user_on_supabase(ip)
    if has_user and uid:
        safe_console_print(f"[dim]☁️ Supabase: {msg}[/dim]")
        return uid

    safe_console_print(f"[yellow]⚠️ {msg}[/yellow]")
    if not force_prompt:
        return None
    created = prompt_create_user()
    return str(created) if created else None


def prompt_create_user() -> Optional[int]:
    """Form tạo user — đã có user (IP/thiết bị) thì KHÔNG cho tạo mới."""
    console.print()
    ip = _current_client_ip()

    # 1) IP đã có user
    has_user, existing, row, msg = check_ip_user_on_supabase(ip)
    if has_user and existing:
        console.print(Panel(
            Text.assemble(
                ("⛔ KHÔNG ĐƯỢC TẠO USER MỚI\n\n", f"bold {TST_COLORS['ruby']}"),
                (f"{msg}\n", "yellow"),
                ("Mỗi IP chỉ 1 user — vĩnh viễn.\n", "white"),
            ),
            border_style=TST_COLORS["ruby"],
            box=box.ROUNDED,
        ))
        display_user_info(existing, _row_to_user_data(row or {}))
        input("\n[dim]Nhấn Enter để tiếp tục...[/dim]")
        return int(existing) if str(existing).isdigit() else None

    console.print(Panel(
        Align.center(Text.assemble(
            ("👤 TẠO USER MỚI (SUPABASE)\n\n", f"bold {TST_COLORS['gold']}"),
            ("Chỉ tạo khi IP hiện tại CHƯA có user.\n", "white"),
            ("Mỗi IP chỉ 1 user — vĩnh viễn.\n", f"bold {TST_COLORS['ruby']}"),
            (f"IP hiện tại: {ip}\n", "dim"),
            ("Nhập ID tài khoản (số) để đăng ký.", "dim"),
        )),
        border_style=TST_COLORS["gold"],
        box=box.ROUNDED
    ))
    console.print()
    user_id_text = Prompt.ask(
        "[bold cyan]Nhập ID tài khoản muốn tạo[/bold cyan]",
        default=""
    )
    if not user_id_text:
        console.print("[yellow]⚠️ Đã hủy tạo user.[/yellow]")
        time.sleep(1)
        return None
    if not user_id_text.isdigit():
        console.print("[red]❌ ID tài khoản không hợp lệ! Chỉ nhập số.[/red]")
        time.sleep(1.5)
        return None
    user_id = int(user_id_text)
    success, msg = create_user_secure(user_id)
    if success:
        console.print(f"[green]{msg}[/green]")
        time.sleep(1.5)
        return user_id
    console.print(f"[yellow]⚠️ {msg}[/yellow]")
    time.sleep(1.8)
    return None


def get_user_balance_secure(user_id: int) -> dict:
    """Lấy số dư xu từ Supabase (+ reset xu qua ngày). Không tạo user local."""
    global _USER_CACHE_TS
    user_id = str(user_id)
    data = load_user_data_secure()
    if user_id not in data:
        # Thử fetch đúng 1 user
        row = supabase_get_user(user_id)
        if row:
            data[user_id] = _row_to_user_data(row)
            _USER_CACHE[user_id] = dict(data[user_id])
        else:
            return {
                "coins": 0,
                "mining": False,
                "mining_start": 0,
                "keys": [],
                "total_mined": 0,
                "daily_claim_date": "",
                "coin_day": "",
                "ip": "",
                "note": "",
                "checksum": "",
            }

    user_data, did_reset, _ = apply_daily_coin_expiry(data[user_id], user_id)
    if did_reset:
        data[user_id] = user_data
        save_user_data_secure({user_id: user_data})  # chỉ ghi 1 user lên cloud
    else:
        data[user_id] = user_data
    return data[user_id]

def update_user_coins_secure(user_id: int, amount: float) -> float:
    """Cập nhật số xu của user (có kiểm tra bảo mật)"""
    data = load_user_data_secure()
    user_id = str(user_id)
    if user_id not in data:
        data[user_id] = {
            "coins": 0,
            "mining": False,
            "mining_start": 0,
            "keys": [],
            "total_mined": 0,
            "daily_claim_date": "",
            "checksum": ""
        }
    
    if not verify_checksum(data[user_id], user_id):
        safe_console_print(f"[red]🚨 PHÁT HIỆN GIẢ MẠO DỮ LIỆU! User: {user_id}[/red]")
        data[user_id] = {
            "coins": 0,
            "mining": False,
            "mining_start": 0,
            "keys": [],
            "total_mined": 0,
            "daily_claim_date": "",
            "checksum": ""
        }
    
    new_coins = data[user_id]["coins"] + amount
    if new_coins < 0:
        safe_console_print(f"[red]🚨 CỐ GẮNG GIẢM XU BẤT THƯỜNG! User: {user_id}[/red]")
        new_coins = 0
    if new_coins > 10000000:
        safe_console_print(f"[red]🚨 CỐ GẮNG TĂNG XU QUÁ MỨC! User: {user_id}[/red]")
        new_coins = 10000000
    
    data[user_id]["coins"] = new_coins
    data[user_id] = add_checksum_to_data(data[user_id], user_id)
    save_user_data_secure(data)
    return data[user_id]["coins"]

def claim_daily_coins_secure(user_id: int) -> tuple:
    """
    Nhận đúng 5 xu mỗi ngày (1 lần/ngày).
    Xu không dùng hết → qua ngày hôm sau bị reset về 0.
    """
    ok_access, access_msg = verify_user_id_access(user_id)
    if not ok_access:
        return False, access_msg

    data = load_user_data_secure()
    user_id = str(user_id)

    if user_id not in data:
        return False, f"User {user_id} không tồn tại. Hãy tạo user trước."

    user_data = data[user_id]
    if not verify_checksum(user_data, user_id):
        safe_console_print(f"[red]🚨 PHÁT HIỆN GIẢ MẠO DỮ LIỆU! User: {user_id}[/red]")
        return False, "Dữ liệu bị giả mạo!"

    # Reset xu cũ nếu đã qua ngày
    user_data, did_reset, reset_msg = apply_daily_coin_expiry(user_data, user_id)

    today = _today_str()
    if user_data.get("daily_claim_date") == today:
        data[user_id] = add_checksum_to_data(user_data, user_id)
        save_user_data_secure(data)
        return False, "Hôm nay bạn đã nhận 5 xu rồi! (Xu không dùng sẽ mất vào ngày mai)"

    # Mỗi ngày chỉ có đúng 5 xu nhận (không cộng dồn ngày trước — đã reset)
    user_data["coins"] = float(DAILY_COIN_REWARD)
    user_data["daily_claim_date"] = today
    user_data["coin_day"] = today
    user_data = add_checksum_to_data(user_data, user_id)
    data[user_id] = user_data
    save_user_data_secure(data)
    try:
        sync_user_to_supabase(user_id, user_data)
    except Exception:
        pass

    extra = f"\n⚠️ {reset_msg}" if did_reset else ""
    return True, f"Nhận thành công {DAILY_COIN_REWARD} xu hôm nay! Dùng trong ngày, không dùng sẽ reset 0 vào ngày mai.{extra}"


def exchange_free_key_13h_secure(user_id: int) -> tuple:
    """Đổi đúng 5 xu lấy 1 KEY FREE 13 GIỜ — tạo key trên Supabase + lưu local. Chống nhập bừa ID."""
    ok_access, access_msg = verify_user_id_access(user_id)
    if not ok_access:
        return False, access_msg

    data = load_user_data_secure()
    user_id = str(user_id)

    if user_id not in data:
        return False, f"User {user_id} không tồn tại. Hãy tạo user trước."

    user_data = data[user_id]
    if not verify_checksum(user_data, user_id):
        return False, "Dữ liệu bị giả mạo!"

    # Xu qua ngày chưa dùng → đã hết hạn
    user_data, did_reset, reset_msg = apply_daily_coin_expiry(user_data, user_id)
    if did_reset:
        data[user_id] = add_checksum_to_data(user_data, user_id)
        save_user_data_secure(data)
        try:
            sync_user_to_supabase(user_id, user_data)
        except Exception:
            pass
        return False, reset_msg or "Xu ngày trước đã hết hạn. Hãy nhận 5 xu hôm nay rồi đổi key."

    if user_data.get("coins", 0) < FREE_KEY_PRICE:
        return False, f"Không đủ xu! Cần {FREE_KEY_PRICE} xu, bạn có {user_data.get('coins', 0):.2f} xu."

    now = time.time()
    key = "FREE_" + secrets.token_hex(5).upper()

    # 1) Tạo key trên Supabase trước (để xác thực online)
    sb_ok, sb_result = create_key_on_supabase(
        key_code=key,
        key_type="free",
        max_ai=10,
        duration_hours=13,
        note=f"Đổi {FREE_KEY_PRICE} xu - user {user_id}",
        user_id=user_id,
        max_uses=None,
    )

    if not sb_ok:
        # Retry 1 lần với key khác nếu conflict
        if "đã tồn tại" in str(sb_result).lower() or "409" in str(sb_result):
            key = "FREE_" + secrets.token_hex(5).upper()
            sb_ok, sb_result = create_key_on_supabase(
                key_code=key,
                key_type="free",
                max_ai=10,
                duration_hours=13,
                note=f"Đổi {FREE_KEY_PRICE} xu - user {user_id}",
                user_id=user_id,
            )
        if not sb_ok:
            return False, f"Không tạo được key trên Supabase: {sb_result}"

    # 2) Trừ xu + lưu local sau khi Supabase OK
    user_data["coins"] -= FREE_KEY_PRICE
    expires_iso = None
    if isinstance(sb_result, dict):
        expires_iso = sb_result.get("expires_at")
    user_data.setdefault("keys", []).append({
        "key": key,
        "type": "free_13h",
        "key_type": "free",
        "duration": "13h",
        "purchased": now,
        "expires": now + FREE_KEY_DURATION,
        "expires_at": expires_iso,
        "supabase": True,
        "id": secrets.token_hex(8),
    })

    data[user_id] = add_checksum_to_data(user_data, user_id)
    save_user_data_secure(data)
    try:
        sync_user_to_supabase(user_id, data[user_id])
    except Exception:
        pass
    return True, key


def validate_local_free_key(key: str) -> tuple:
    """Kiểm tra key FREE 13 giờ đã đổi bằng xu. IP phải khớp user sở hữu key."""
    key = key.strip().upper()
    data = load_user_data_secure()
    now = time.time()
    ip = _current_client_ip()

    for user_id, user_data in data.items():
        if not verify_checksum(user_data, user_id):
            continue
        for item in user_data.get("keys", []):
            if item.get("key", "").upper() == key and item.get("type") == "free_13h":
                if now < float(item.get("expires", 0)):
                    stored_ip = str(user_data.get("ip", "") or "")
                    # Key dùng từ IP khác IP tạo user → thu hồi ngay
                    if stored_ip and stored_ip != "unknown" and ip != "unknown" and stored_ip != ip:
                        revoke_user_keys_abuse(
                            user_id,
                            reason=f"Key dùng sai IP (owner={stored_ip}, now={ip})",
                        )
                        return False, None, None
                    return True, user_id, item
    return False, None, None



def daily_coin_exchange_menu():
    """Menu nhận xu hằng ngày, đổi xu lấy key FREE 13 giờ, và tạo user."""
    global USER_ID

    if USER_ID is None:
        safe_console_print("[red]❌ Vui lòng chọn tài khoản trước![/red]")
        time.sleep(2)
        return

    # Bắt buộc: IP phải có user trên Supabase (chưa có → tạo)
    bound = ensure_user_for_current_ip(force_prompt=True)
    if not bound:
        safe_console_print("[red]❌ IP này chưa có user trên Supabase. Hãy tạo user trước.[/red]")
        time.sleep(2)
        return
    # User TST-TOOL xu phải khớp IP-bound user (không dùng ID game bừa)
    if str(USER_ID) != str(bound):
        # Vẫn cho nhận xu theo ID game nếu IP đã tạo đúng user = USER_ID;
        # nếu IP gắn user khác → chặn
        has, uid_ip, _, msg = check_ip_user_on_supabase()
        if has and uid_ip and str(uid_ip) != str(USER_ID):
            safe_console_print(
                f"[red]❌ IP đã gắn user Supabase {uid_ip}, "
                f"không dùng account game {USER_ID} cho hệ xu.[/red]"
            )
            time.sleep(2.5)
            return

    while True:
        console.clear()
        balance = get_user_balance_secure(USER_ID)
        today = datetime.now().strftime("%Y-%m-%d")
        claimed = balance.get("daily_claim_date") == today

        console.print(Panel(
            Text.assemble(
                ("💰 HỆ THỐNG XU & ĐỔI KEY\n\n", f"bold {TST_COLORS['gold']}"),
                ("Số dư: ", "bold white"),
                (f"{balance.get('coins', 0):.2f} xu\n", f"bold {TST_COLORS['emerald']}"),
                ("🎁 Xu hằng ngày: ", "bold white"),
                (f"{DAILY_COIN_REWARD} xu/ngày (không dùng → reset 0 ngày mai)\n", f"bold {TST_COLORS['neon_blue']}"),
                ("🔑 Đổi key: ", "bold white"),
                ("5 xu → KEY FREE 13 GIỜ", f"bold {TST_COLORS['neon_pink']}"),
            ),
            border_style=TST_COLORS["gold"],
            box=box.ROUNDED
        ))
        console.print()
        console.print(f"[1] 🎁 Nhận {DAILY_COIN_REWARD} xu hôm nay "
                      f"{'[ĐÃ NHẬN]' if claimed else ''}")
        console.print("[2] 🔑 Đổi 5 xu lấy KEY FREE 13 GIỜ")
        console.print("[q] 🔙 Quay lại")
        console.print()

        choice = Prompt.ask(
            f"[bold {TST_COLORS['gold']}]>> Chọn[/bold {TST_COLORS['gold']}]",
            choices=['1', '2', 'q'],
            default='q'
        )

        if choice == '1':
            success, msg = claim_daily_coins_secure(USER_ID)
            safe_console_print(f"[green]✅ {msg}[/green]" if success else f"[yellow]⚠️ {msg}[/yellow]")
            time.sleep(2)

        elif choice == '2':
            confirm = Prompt.ask(
                "[bold yellow]Đổi 5 xu lấy KEY FREE 13 GIỜ? (y/n)[/bold yellow]",
                choices=['y', 'n'],
                default='n'
            )
            if confirm == 'y':
                with console.status("[bold yellow]⏳ Đang tạo key trên Supabase...[/bold yellow]", spinner="dots"):
                    success, msg = exchange_free_key_13h_secure(USER_ID)
                if success:
                    console.print(Panel(
                        Text.assemble(
                            ("✅ ĐỔI KEY THÀNH CÔNG!\n\n", "bold green"),
                            ("KEY: ", "bold white"), (f"{msg}\n", f"bold {TST_COLORS['gold']}"),
                            ("Loại: FREE | Hạn: 13 GIỜ\n", "bold cyan"),
                            ("🌐 Supabase: Đã tạo & kích hoạt\n", "bold green"),
                            ("💡 Nhập key này ở menu Xác thực để dùng tool.", "dim"),
                        ),
                        border_style=TST_COLORS["emerald"],
                        box=box.ROUNDED
                    ))
                else:
                    safe_console_print(f"[red]❌ {msg}[/red]")
                time.sleep(2)

        elif choice == 'q':
            break


def start_mining_secure(user_id: int) -> bool:
    """Bắt đầu đào xu (có kiểm tra bảo mật)"""
    data = load_user_data_secure()
    user_id = str(user_id)
    if user_id not in data:
        data[user_id] = {
            "coins": 0,
            "mining": False,
            "mining_start": 0,
            "keys": [],
            "total_mined": 0,
            "daily_claim_date": "",
            "checksum": ""
        }
    
    if not verify_checksum(data[user_id], user_id):
        safe_console_print(f"[red]🚨 PHÁT HIỆN GIẢ MẠO DỮ LIỆU! User: {user_id}[/red]")
        return False
    
    if data[user_id]["mining"]:
        return False
    
    data[user_id]["mining"] = True
    data[user_id]["mining_start"] = time.time()
    data[user_id] = add_checksum_to_data(data[user_id], user_id)
    save_user_data_secure(data)
    return True

def stop_mining_secure(user_id: int) -> tuple:
    """Dừng đào xu và tính số xu đã đào (có kiểm tra bảo mật)"""
    data = load_user_data_secure()
    user_id = str(user_id)
    if user_id not in data:
        return False, 0
    
    if not verify_checksum(data[user_id], user_id):
        safe_console_print(f"[red]🚨 PHÁT HIỆN GIẢ MẠO DỮ LIỆU! User: {user_id}[/red]")
        return False, 0
    
    if not data[user_id]["mining"]:
        return False, 0
    
    elapsed = time.time() - data[user_id]["mining_start"]
    coins_earned = elapsed * MINING_RATE
    
    max_daily = 864
    if coins_earned > max_daily:
        safe_console_print(f"[yellow]⚠️ Giới hạn đào tối đa 1 ngày ({max_daily} xu)[/yellow]")
        coins_earned = max_daily
    
    data[user_id]["mining"] = False
    data[user_id]["coins"] += coins_earned
    data[user_id]["total_mined"] += coins_earned
    data[user_id]["mining_start"] = 0
    data[user_id] = add_checksum_to_data(data[user_id], user_id)
    save_user_data_secure(data)
    return True, coins_earned

def buy_key_secure(user_id: int, key_type: str) -> tuple:
    """Mua key bằng xu (có kiểm tra bảo mật)"""
    prices = load_key_shop()
    
    if key_type not in prices:
        return False, "Loại key không hợp lệ!"
    
    price = prices[key_type]
    user_data = get_user_balance_secure(user_id)
    
    if not verify_checksum(user_data, str(user_id)):
        safe_console_print(f"[red]🚨 PHÁT HIỆN GIẢ MẠO DỮ LIỆU! User: {user_id}[/red]")
        return False, "Dữ liệu bị giả mạo!"
    
    if user_data["coins"] < price:
        return False, f"Không đủ xu! Cần {price} xu, bạn có {user_data['coins']:.1f} xu"
    
    user_data["coins"] -= price
    
    key_info = {
        "type": key_type,
        "purchased": time.time(),
        "expires": time.time() + get_key_duration(key_type),
        "id": secrets.token_hex(8)
    }
    user_data["keys"].append(key_info)
    user_data = add_checksum_to_data(user_data, str(user_id))
    
    data = load_user_data_secure()
    data[str(user_id)] = user_data
    save_user_data_secure(data)
    
    return True, f"Mua key {key_type} thành công! Giá: {price} xu"

def get_key_duration(key_type: str) -> float:
    """Lấy thời gian key theo giây"""
    durations = {
        "24h": 24 * 3600,
        "7d": 7 * 24 * 3600,
        "30d": 30 * 24 * 3600,
        "90d": 90 * 24 * 3600,
    }
    return durations.get(key_type, 0)

def get_user_stats_secure(user_id: int) -> dict:
    """Lấy thống kê user (có kiểm tra bảo mật)"""
    data = load_user_data_secure()
    user_id = str(user_id)
    if user_id not in data:
        return {
            "coins": 0,
            "mining": False,
            "total_mined": 0,
            "keys": 0,
            "valid_keys": 0
        }
    
    user_data = data[user_id]
    
    if not verify_checksum(user_data, user_id):
        safe_console_print(f"[red]🚨 PHÁT HIỆN GIẢ MẠO DỮ LIỆU! User: {user_id}[/red]")
        return {
            "coins": 0,
            "mining": False,
            "total_mined": 0,
            "keys": 0,
            "valid_keys": 0
        }
    
    valid_keys = check_user_keys_secure(user_id)
    mining_status = get_mining_status_secure(user_id)
    
    return {
        "coins": user_data.get("coins", 0),
        "mining": mining_status["mining"],
        "total_mined": user_data.get("total_mined", 0),
        "keys": len(user_data.get("keys", [])),
        "valid_keys": len(valid_keys),
        "mining_earned": mining_status.get("earned", 0) if mining_status["mining"] else 0,
        "mining_elapsed": mining_status.get("elapsed", 0) if mining_status["mining"] else 0
    }

def check_user_keys_secure(user_id: int) -> list:
    """Kiểm tra key của user (có bảo mật)"""
    data = load_user_data_secure()
    user_id = str(user_id)
    if user_id not in data:
        return []
    
    user_data = data[user_id]
    
    if not verify_checksum(user_data, user_id):
        safe_console_print(f"[red]🚨 PHÁT HIỆN GIẢ MẠO DỮ LIỆU! User: {user_id}[/red]")
        return []
    
    valid_keys = []
    current_time = time.time()
    
    for key in user_data.get("keys", []):
        if key.get("expires", 0) > current_time:
            valid_keys.append(key)
    
    user_data["keys"] = valid_keys
    user_data = add_checksum_to_data(user_data, user_id)
    data[user_id] = user_data
    save_user_data_secure(data)
    
    return valid_keys

def get_mining_status_secure(user_id: int) -> dict:
    """Lấy trạng thái đào (có bảo mật)"""
    data = load_user_data_secure()
    user_id = str(user_id)
    if user_id not in data:
        return {"mining": False, "elapsed": 0, "earned": 0}
    
    user_data = data[user_id]
    
    if not verify_checksum(user_data, user_id):
        safe_console_print(f"[red]🚨 PHÁT HIỆN GIẢ MẠO DỮ LIỆU! User: {user_id}[/red]")
        return {"mining": False, "elapsed": 0, "earned": 0}
    
    if not user_data.get("mining", False):
        return {"mining": False, "elapsed": 0, "earned": 0}
    
    elapsed = time.time() - user_data.get("mining_start", time.time())
    earned = elapsed * MINING_RATE
    
    max_session = 864
    if earned > max_session:
        earned = max_session
    
    return {
        "mining": True,
        "elapsed": elapsed,
        "earned": earned,
        "start_time": user_data.get("mining_start", 0)
    }

# ================== MINING THREAD ==================

def mining_worker_secure():
    """Thread chạy ngầm để đào xu - Có bảo mật"""
    global stop_flag
    last_update = {}
    
    while not stop_flag:
        time.sleep(MINING_INTERVAL)
        
        try:
            data = load_user_data_secure()
            updated = False
            
            for user_id, user_data in data.items():
                if not verify_checksum(user_data, user_id):
                    safe_console_print(f"[red]🚨 PHÁT HIỆN GIẢ MẠO DỮ LIỆU! User: {user_id}[/red]")
                    continue
                
                if user_data.get("mining", False):
                    start_time = user_data.get("mining_start", 0)
                    if start_time > time.time():
                        user_data["mining_start"] = time.time()
                        safe_console_print(f"[yellow]⚠️ Sửa thời gian đào bất thường user {user_id}[/yellow]")
                    
                    elapsed = time.time() - start_time
                    
                    if int(elapsed) % 10 == 0:
                        daily_limit = 864
                        total_mined_today = user_data.get("total_mined", 0)
                        
                        if total_mined_today < daily_limit:
                            user_data["coins"] = user_data.get("coins", 0) + 0.1
                            user_data["total_mined"] = total_mined_today + 0.1
                            user_data["mining_start"] = time.time()
                            user_data = add_checksum_to_data(user_data, user_id)
                            data[user_id] = user_data
                            updated = True
                            
                            if user_id not in last_update or time.time() - last_update.get(user_id, 0) > 60:
                                safe_console_print(f"[dim]⛏️ User {user_id} đã đào thêm 0.1 xu (10s)[/dim]")
                                last_update[user_id] = time.time()
                        else:
                            if user_id not in last_update or time.time() - last_update.get(user_id, 0) > 300:
                                safe_console_print(f"[yellow]⛏️ User {user_id} đã đạt giới hạn {daily_limit} xu/ngày[/yellow]")
                                last_update[user_id] = time.time()
            
            if updated:
                save_user_data_secure(data)
                
        except Exception as e:
            safe_console_print(f"[red]❌ Lỗi mining: {e}[/red]")
            time.sleep(5)

def start_mining_thread_secure():
    """Khởi chạy thread đào có bảo mật"""
    thread = threading.Thread(target=mining_worker_secure, daemon=True)
    thread.start()
    return thread

# ================== KIỂM TRA VÀ SỬA CHỮA DỮ LIỆU ==================

def verify_and_repair_all_data():
    """Kiểm tra và sửa chữa toàn bộ dữ liệu user"""
    safe_console_print("\n[bold]🔍 ĐANG KIỂM TRA DỮ LIỆU NGƯỜI DÙNG...[/bold]")
    
    data = load_user_data_secure()
    if not data:
        safe_console_print("[yellow]⚠️ Không có dữ liệu user[/yellow]")
        return
    
    repaired_count = 0
    anomaly_count = 0
    
    for user_id, user_data in data.items():
        if not verify_checksum(user_data, user_id):
            safe_console_print(f"[red]❌ Dữ liệu user {user_id} bị giả mạo! Đang sửa...[/red]")
            data[user_id] = {
                "coins": 0,
                "mining": False,
                "mining_start": 0,
                "keys": [],
                "total_mined": 0,
                "checksum": ""
            }
            data[user_id] = add_checksum_to_data(data[user_id], user_id)
            repaired_count += 1
            anomaly_count += 1
            continue
        
        is_anomaly, warnings = detect_data_anomaly(user_data, user_id)
        if is_anomaly:
            safe_console_print(f"[yellow]⚠️ User {user_id} có dữ liệu bất thường:[/yellow]")
            for warning in warnings:
                safe_console_print(f"[yellow]  - {warning}[/yellow]")
            data[user_id] = fix_corrupted_data(user_data, user_id)
            data[user_id] = add_checksum_to_data(data[user_id], user_id)
            repaired_count += 1
            anomaly_count += 1
    
    if repaired_count > 0:
        safe_console_print(f"[yellow]⚠️ Đã sửa {repaired_count} dữ liệu bị lỗi[/yellow]")
        save_user_data_secure(data)
    else:
        safe_console_print("[green]✅ Tất cả dữ liệu đều an toàn![/green]")
    
    safe_console_print(f"[dim]📊 Tổng số user: {len(data)}[/dim]")
    return anomaly_count

# ================== MENU ĐÀO XU ==================

def show_mining_menu():
    console.clear()
    console.print(Align.center(Text("TST-TOOL  /  NOVA  •  ENGINE XU", style=f"bold {TST_COLORS['sapphire']}")))
    console.print(Rule(style=TST_COLORS["sky"]))
    rate = MINING_RATE
    stats = Table.grid(expand=True,padding=(0,3))
    stats.add_column(); stats.add_column(); stats.add_column(); stats.add_column()
    stats.add_row(
        Text("TỐC ĐỘ",style=TST_COLORS["muted"]), Text(f"{rate:.4f} /s",style=f"bold {TST_COLORS['emerald']}"),
        Text("1 HOUR",style=TST_COLORS["muted"]), Text(f"{rate*3600:.1f} xu",style=f"bold {TST_COLORS['gold']}")
    )
    stats.add_row(
        Text("1 DAY",style=TST_COLORS["muted"]), Text(f"{rate*86400:.1f} xu",style=f"bold {TST_COLORS['gold']}"),
        Text("KEY",style=TST_COLORS["muted"]), Text("5 xu → FREE 13H",style=f"bold {TST_COLORS['neon_pink']}")
    )
    console.print(Panel(stats,border_style=TST_COLORS["emerald"],box=box.MINIMAL,padding=(1,2)))
    menu = ["1  BẮT ĐẦU ĐÀO","2  DỪNG ĐÀO","3  SỐ DƯ","4  MUA KEY","5  KEY CỦA TÔI","6  THỐNG KÊ","7  BẢO MẬT DỮ LIỆU","8  HÀNG NGÀY / KEY FREE","q  QUAY LẠI"]
    for item in menu: console.print(f"  {item}")
    console.print()
    return _ui_prompt("MINING").lower()


def mining_menu():
    """Menu đào xu chính"""
    global USER_ID
    
    if USER_ID is None:
        safe_console_print("[red]❌ Vui lòng chọn tài khoản trước![/red]")
        time.sleep(2)
        return
    
    while True:
        choice = show_mining_menu()
        
        if choice == '1':
            if start_mining_secure(USER_ID):
                safe_console_print(f"[green]✅ ĐÃ BẮT ĐẦU ĐÀO XU![/green]")
                safe_console_print(f"[dim]⛏️ Tốc độ: 10 giây = 0.1 xu[/dim]")
                safe_console_print("[dim]💡 Dùng lệnh /stopmining để dừng[/dim]")
                time.sleep(2)
            else:
                safe_console_print("[yellow]⚠️ Bạn đang đào rồi![/yellow]")
                time.sleep(2)
        
        elif choice == '2':
            success, earned = stop_mining_secure(USER_ID)
            if success:
                safe_console_print(f"[green]✅ ĐÃ DỪNG ĐÀO![/green]")
                safe_console_print(f"[gold]💰 Đã đào được: {earned:.2f} xu[/gold]")
                time.sleep(2)
            else:
                safe_console_print("[yellow]⚠️ Bạn chưa đào![/yellow]")
                time.sleep(2)
        
        elif choice == '3':
            stats = get_user_stats_secure(USER_ID)
            panel = Panel(Text.assemble(
                ("💰 SỐ DƯ CỦA BẠN\n\n", f"bold {TST_COLORS['gold']}"),
                (f"Số dư: ", "bold white"),
                (f"{stats['coins']:.2f} xu\n", f"bold {TST_COLORS['emerald']}"),
                (f"Tổng đã đào: ", "bold white"),
                (f"{stats['total_mined']:.2f} xu\n", f"bold {TST_COLORS['gold']}"),
                (f"Trạng thái: ", "bold white"),
                (f"{'⛏️ Đang đào' if stats['mining'] else '⏹️ Đã dừng'}\n", f"bold {TST_COLORS['neon_orange'] if stats['mining'] else 'dim'}"),
                (f"Key: ", "bold white"),
                (f"{stats['valid_keys']} key còn hiệu lực", f"bold {TST_COLORS['neon_pink']}"),
                ("\n🔒 ", "bold green"),
                ("Dữ liệu đã được bảo vệ", "bold green")
            ), border_style=TST_COLORS["gold"], box=box.ROUNDED)
            console.print(panel)
            input("[dim]Nhấn Enter để tiếp tục...[/dim]")
        
        elif choice == '4':
            show_key_shop_secure()
        
        elif choice == '5':
            show_my_keys_secure()

        elif choice == '8':
            daily_coin_exchange_menu()
        
        elif choice == '6':
            show_mining_stats_secure()
        
        elif choice == '7':
            show_data_security_status()
        
        elif choice == 'q':
            break

# ================== HIỂN THỊ KEY VÀ THỐNG KÊ ==================

def show_key_shop_secure():
    console.clear(); _ui_title("◇","KEY STORE","Key plans · pricing · mining equivalent")
    prices=load_key_shop(); stats=get_user_stats_secure(USER_ID)
    wallet=Table(show_header=False,box=None,padding=(0,1)); wallet.add_column(width=18); wallet.add_column()
    wallet.add_row("SỐ DƯ",f"{stats['coins']:.2f} xu"); _ui_section("WALLET",wallet,TST_COLORS["emerald"])
    table=Table(show_header=True,box=box.ROUNDED,expand=True,border_style=TST_COLORS["sky"],padding=(0,1))
    table.add_column("#",width=5,justify="center"); table.add_column("PLAN"); table.add_column("DURATION"); table.add_column("PRICE",justify="right"); table.add_column("MINING EQUIVALENT")
    names={"24h":"KEY 1 NGÀY","7d":"KEY 7 NGÀY","30d":"KEY 30 NGÀY","90d":"KEY 90 NGÀY","free_13h":"KEY FREE 13 GIỜ"}
    dur={"24h":"24 giờ","7d":"7 ngày","30d":"30 ngày","90d":"90 ngày"}; mine={"24h":"50 giây","7d":"300 giây (5 phút)","30d":"1000 giây (16.7 phút)","90d":"2500 giây (41.7 phút)"}
    key_list=list(prices.items())
    for i,(kt,price) in enumerate(key_list,1): table.add_row(str(i),names.get(kt,kt),dur.get(kt,"13 giờ" if kt=="free_13h" else ""),f"{price} xu",mine.get(kt,"—"))
    console.print(table); console.print(); choice=_ui_prompt("BUY / Q").lower()
    if choice.isdigit():
        idx=int(choice)-1
        if 0<=idx<len(key_list):
            kt,price=key_list[idx]; name=names.get(kt,kt)
            _ui_section("CONFIRM PURCHASE",Text(f"{name}\nGiá: {price} xu\n\nXác nhận giao dịch?",style=TST_COLORS["platinum"]),TST_COLORS["gold"])
            if Prompt.ask(f"[bold {TST_COLORS['sapphire']}]  CONFIRM  ›[/]",choices=["y","n"],default="n")=="y":
                success,msg=buy_key_secure(USER_ID,kt); color=TST_COLORS["emerald"] if success else TST_COLORS["ruby"]
                _ui_section("TRANSACTION",Text(("✓ " if success else "✕ ")+msg,style=f"bold {color}"),color); time.sleep(2)
    console.clear()

def show_my_keys_secure():
    """Hiển thị key của user (có bảo mật)"""
    console.clear()
    header = Panel(Align.center(Text.assemble(
        (f"🔑 ", f"bold {TST_COLORS['gold']}"),
        ("KEY CỦA TÔI", f"bold {TST_COLORS['neon_blue']}"),
        (f" 🔑", f"bold {TST_COLORS['gold']}")
    )), border_style=TST_COLORS["gold"], box=box.ROUNDED)
    console.print(header)
    console.print()
    
    keys = check_user_keys_secure(USER_ID)
    stats = get_user_stats_secure(USER_ID)
    
    console.print(f"[bold]💰 Số dư: {stats['coins']:.2f} xu[/bold]")
    console.print(f"[bold]🔑 Số key: {len(keys)} key còn hiệu lực[/bold]\n")
    
    if not keys:
        console.print("[dim]Bạn chưa có key nào hoặc key đã hết hạn[/dim]")
        input("\n[dim]Nhấn Enter để tiếp tục...[/dim]")
        return
    
    table = Table(box=box.ROUNDED, border_style=TST_COLORS["gold"])
    table.add_column("Loại Key", style=TST_COLORS["neon_blue"])
    table.add_column("Mua lúc", style="dim")
    table.add_column("Hết hạn", style=TST_COLORS["ruby"])
    table.add_column("Còn lại", style=TST_COLORS["emerald"])
    table.add_column("ID", style="dim")
    
    key_names = {
        "24h": "KEY 1 NGÀY",
        "7d": "KEY 7 NGÀY",
        "30d": "KEY 30 NGÀY",
        "90d": "KEY 90 NGÀY",
        "free_13h": "KEY FREE 13 GIỜ"
    }
    
    for key in keys:
        key_type = key.get("type", "unknown")
        purchased = datetime.fromtimestamp(key.get("purchased", 0)).strftime("%d/%m %H:%M")
        expires = datetime.fromtimestamp(key.get("expires", 0)).strftime("%d/%m %H:%M")
        remaining = key.get("expires", 0) - time.time()
        key_id = key.get("id", "N/A")[:8]
        
        if remaining > 0:
            days = int(remaining // 86400)
            hours = int((remaining % 86400) // 3600)
            minutes = int((remaining % 3600) // 60)
            remaining_text = f"{days}d {hours}h {minutes}m"
        else:
            remaining_text = "Đã hết hạn"
        
        table.add_row(
            key_names.get(key_type, key_type),
            purchased,
            expires,
            remaining_text,
            key_id
        )
    
    console.print(table)
    input("\n[dim]Nhấn Enter để tiếp tục...[/dim]")

def show_mining_stats_secure():
    console.clear(); _ui_title("◌","MINING DASHBOARD","Live wallet & mining telemetry")
    stats=get_user_stats_secure(USER_ID); state=get_mining_status_secure(USER_ID)
    m=Table(show_header=False,box=None,padding=(0,1)); m.add_column(width=20,style=TST_COLORS["muted"]); m.add_column(style=f"bold {TST_COLORS['platinum']}")
    if stats["mining"]:
        m.add_row("STATUS","● MINING"); m.add_row("ELAPSED",f"{state['elapsed']:.0f} giây"); m.add_row("EARNED",f"{state['earned']:.2f} xu")
        m.add_row("TỐC ĐỘ / PHÚT",f"{MINING_RATE*60:.2f} xu"); m.add_row("TỐC ĐỘ / GIỜ",f"{MINING_RATE*3600:.1f} xu"); m.add_row("TỐC ĐỘ / NGÀY",f"{MINING_RATE*86400:.1f} xu")
        _ui_section("ĐANG ĐÀO",m,TST_COLORS["emerald"])
    else:
        m.add_row("TRẠNG THÁI","○ CHỜ"); m.add_row("SỐ DƯ",f"{stats['coins']:.2f} xu"); m.add_row("TỔNG ĐÀO",f"{stats['total_mined']:.2f} xu"); m.add_row("KEY HỢP LỆ",f"{stats['valid_keys']} key")
        _ui_section("MINING SUMMARY",m,TST_COLORS["sky"])
    console.print(Align.center(Text("🔒 Protected data  •  Press Enter to return",style=TST_COLORS["muted"]))); input()

def show_data_security_status():
    """Hiển thị trạng thái bảo mật dữ liệu"""
    console.clear()
    header = Panel(Align.center(Text.assemble(
        (f"🔒 ", f"bold {TST_COLORS['gold']}"),
        ("BẢO MẬT DỮ LIỆU", f"bold {TST_COLORS['neon_blue']}"),
        (f" 🔒", f"bold {TST_COLORS['gold']}")
    )), border_style=TST_COLORS["gold"], box=box.ROUNDED)
    console.print(header)
    console.print()
    
    data = load_user_data_secure()
    
    total_users = len(data)
    total_coins = sum(u.get('coins', 0) for u in data.values())
    total_mined = sum(u.get('total_mined', 0) for u in data.values())
    total_keys = sum(len(u.get('keys', [])) for u in data.values())
    mining_users = sum(1 for u in data.values() if u.get('mining', False))
    
    corrupted = 0
    for user_id, user_data in data.items():
        if not verify_checksum(user_data, user_id):
            corrupted += 1
    
    panel = Panel(Text.assemble(
        ("📊 THỐNG KÊ DỮ LIỆU\n\n", f"bold {TST_COLORS['gold']}"),
        (f"👤 Tổng user: ", "bold white"),
        (f"{total_users}\n", f"bold {TST_COLORS['emerald']}"),
        (f"💰 Tổng xu: ", "bold white"),
        (f"{total_coins:.2f} xu\n", f"bold {TST_COLORS['gold']}"),
        (f"⛏️ Tổng đã đào: ", "bold white"),
        (f"{total_mined:.2f} xu\n", f"bold {TST_COLORS['gold']}"),
        (f"🔑 Tổng key: ", "bold white"),
        (f"{total_keys} key\n", f"bold {TST_COLORS['neon_pink']}"),
        (f"⛏️ Đang đào: ", "bold white"),
        (f"{mining_users} user\n", f"bold {TST_COLORS['neon_orange']}"),
        (f"🔒 Dữ liệu bị giả mạo: ", "bold white"),
        (f"{'✅ 0' if corrupted == 0 else f'❌ {corrupted}'}\n", f"bold {TST_COLORS['emerald'] if corrupted == 0 else TST_COLORS['ruby']}"),
        (f"🛡️ Trạng thái: ", "bold white"),
        (f"{'✅ AN TOÀN' if corrupted == 0 else '⚠️ CẦN SỬA CHỮA'}", f"bold {TST_COLORS['emerald'] if corrupted == 0 else TST_COLORS['neon_orange']}")
    ), border_style=TST_COLORS["gold"], box=box.ROUNDED)
    console.print(panel)
    console.print()
    
    console.print("[bold]📌 CHỌN CHỨC NĂNG:[/bold]")
    console.print("[1] 🔍 Kiểm tra và sửa chữa dữ liệu")
    console.print("[2] 📊 Xem chi tiết user")
    console.print("[q] 🔙 Quay lại")
    console.print()
    
    choice = Prompt.ask(f"[bold {TST_COLORS['gold']}]>> Chọn[/bold {TST_COLORS['gold']}]", choices=['1','2','q'], default='q')
    
    if choice == '1':
        verify_and_repair_all_data()
        input("\n[dim]Nhấn Enter để tiếp tục...[/dim]")
    elif choice == '2':
        show_user_details()
    return choice

def show_user_details():
    """Hiển thị chi tiết từng user"""
    data = load_user_data_secure()
    
    if not data:
        console.print("[yellow]⚠️ Không có dữ liệu user[/yellow]")
        time.sleep(2)
        return
    
    table = Table(box=box.ROUNDED, border_style=TST_COLORS["gold"])
    table.add_column("User ID", style=TST_COLORS["neon_blue"])
    table.add_column("Xu", justify="right", style=TST_COLORS["emerald"])
    table.add_column("Đã đào", justify="right", style=TST_COLORS["gold"])
    table.add_column("Key", justify="right", style=TST_COLORS["neon_pink"])
    table.add_column("Trạng thái", style="dim")
    table.add_column("Bảo mật", style="dim")
    
    for user_id, user_data in data.items():
        coins = user_data.get('coins', 0)
        total_mined = user_data.get('total_mined', 0)
        keys = len(user_data.get('keys', []))
        mining = user_data.get('mining', False)
        is_valid = verify_checksum(user_data, user_id)
        
        status = "⛏️ Đang đào" if mining else "⏹️ Dừng"
        security = "✅" if is_valid else "❌"
        
        table.add_row(
            user_id[:8] + "...",
            f"{coins:.2f}",
            f"{total_mined:.2f}",
            str(keys),
            status,
            security
        )
    
    console.print(table)
    input("\n[dim]Nhấn Enter để tiếp tục...[/dim]")
# ================== CÁC HÀM AI CHO VUA THOÁT HIỂM ==================

ROOM_NAMES = {1: "📦 Nhà kho", 2: "🪑 Phòng họp", 3: "👔 Phòng giám đốc", 4: "💬 Phòng trò chuyện", 5: "🎥 Phòng giám sát", 6: "🏢 Văn phòng", 7: "💰 Phòng tài vụ", 8: "👥 Phòng nhân sự"}
ROOM_ORDER = [1, 2, 3, 4, 5, 6, 7, 8]

issue_id: Optional[int] = None
issue_start_ts: Optional[float] = None
issue_end_ts: Optional[float] = None
count_down: Optional[int] = None
killed_room: Optional[int] = None
last_finished_issue: Optional[int] = None
last_finished_label: str = ""
round_index: int = 0

room_state: Dict[int, Dict[str, Any]] = {r: {"players": 0, "bet": 0} for r in ROOM_ORDER}
room_stats: Dict[int, Dict[str, Any]] = {r: {"kills": 0, "survives": 0, "last_kill_round": None, "last_players": 0, "last_bet": 0} for r in ROOM_ORDER}

predicted_room: Optional[int] = None
predicted_rooms: List[int] = []
num_rooms: int = 1  # số phòng cược mỗi ván (1–4)
last_killed_room: Optional[int] = None
last_finished_issue: Optional[int] = None
last_finished_label: str = ""
last_killed_room_delayed: Optional[int] = None
prediction_locked: bool = False

current_build: Optional[float] = None
current_usdt: Optional[float] = None
current_world: Optional[float] = None
last_balance_ts: Optional[float] = None
last_balance_val: Optional[float] = None
starting_balance: Optional[float] = None
cumulative_profit: Optional[float] = None

win_streak: int = 0
lose_streak: int = 0
max_win_streak: int = 0
max_lose_streak: int = 0

base_bet: float = 1.0
multiplier: float = 2.0
current_bet: Optional[float] = None
run_mode: str = "AUTO"
bet_rounds_before_skip: int = 0
_rounds_placed_since_skip: int = 0
skip_next_round_flag: bool = False

bet_history: deque = deque(maxlen=200)
bet_sent_for_issue: set = set()
bet_room_sent: set = set()  # (issue, room) đã gửi cược
skipped_for_issue: set = set()  # kỳ đã bỏ theo setting / danger

pause_after_losses: int = 0
random_skip_pct: float = 0.0  # % kỳ bỏ ngẫu nhiên (0–40)
_skip_rounds_remaining: int = 0
profit_target: Optional[float] = None
stop_when_profit_reached: bool = False
stop_loss_target: Optional[float] = None
stop_when_loss_reached: bool = False

ui_state: str = "IDLE"
round_warning: str = ""  # cảnh báo nguy hiểm / bỏ ván
analysis_duration: float = 45.0
analysis_start_ts: Optional[float] = None

last_msg_ts: float = time.time()
last_balance_fetch_ts: float = 0.0
BALANCE_POLL_INTERVAL: float = 4.0
_ws: Dict[str, Any] = {"ws": None}

_sequential_bet_index = 0
killer_history = deque(maxlen=20)
game_kill_log = deque(maxlen=10)

# ================== AI LIST ==================

# KEY FREE: tối đa 10 AI (Vua Thoát Hiểm / CDTD)
FREE_AI_LIST = [
    "RANDOM", "MIN_PLAYER_BET", "PROBABILITY", "FOLLOW_KILLER",
    "SEQUENTIAL", "KILLER_PERSONALITY", "SMART_SAFE",
    "FOLLOW_KILLER_DELAYED", "HIDE_SEEK_MASTER", "BALANCE",
]

# KEY FREE Lotto: tối đa 5 AI
LOTTO_FREE_AI_LIST = [
    "RANDOM", "HOT_TRACK", "COLD_TRACK", "BALANCE", "SMART",
]

VIP_AI_LIST = [
    "MOST_PLAYERS", "LEAST_PLAYERS", "RICHEST", "POOREST",
    "ALTERNATE", "AVOID_RESULT", "COLD", "HOT", "MEDIAN", "PATTERN",
    "VIP_RANDOM", "KILLER_WAVE", "PSYCHO_ANALYSIS", "MARKOV_CHAIN",
    "DEEP_LEARNING", "REINFORCEMENT", "BAYESIAN", "K_MEANS",
    "NEURAL", "FUZZY", "GENETIC", "ANT_COLONY", "PARTICLE_SWARM",
    "KNN", "DECISION_TREE", "RANDOM_FOREST", "GRADIENT_BOOST",
    "LSTM", "TRANSFORMER", "ENSEMBLE", "CYCLE_ANALYSIS", "TREND_ANALYSIS",
    "SAFE_RISK",
]

SELECTION_MODES = {
    "RANDOM": "1. PHẬT ĐỘ (Random)",
    "MIN_PLAYER_BET": "2. AN TOÀN (Min Players & Bet)",
    "PROBABILITY": "3. XÁC SUẤT (Probability)",
    "FOLLOW_KILLER": "4. THEO SÁT THỦ (Follow Killer)",
    "SEQUENTIAL": "5. TUẦN TỰ (1→2→3→...→8)",
    "KILLER_PERSONALITY": "6. TÍNH CÁCH SÁT THỦ (AI Enhanced)",
    "SMART_SAFE": "7. THÔNG MINH (AI Smart Enhanced)",
    "FOLLOW_KILLER_DELAYED": "8. THEO VẾT SÁT THỦ (Delay 1 ván)",
    "HIDE_SEEK_MASTER": "9. THÁNH TRỐN TÌM (Master AI)",
    "BALANCE": "10. CÂN BẰNG (Balance)",
    "MOST_PLAYERS": "11. ĐÔNG NHẤT (Most Players)",
    "LEAST_PLAYERS": "12. ÍT NHẤT (Least Players)",
    "RICHEST": "13. GIÀU NHẤT (Richest)",
    "POOREST": "14. NGHÈO NHẤT (Poorest)",
    "ALTERNATE": "15. XEN KẼ (Alternate)",
    "AVOID_RESULT": "16. TRÁNH KẾT QUẢ (Avoid Result)",
    "COLD": "17. PHÒNG LẠNH (Cold Room)",
    "HOT": "18. PHÒNG NÓNG (Hot Room)",
    "MEDIAN": "19. TRUNG VỊ (Median)",
    "PATTERN": "20. MẪU LẶP (Pattern)",
    "VIP_RANDOM": "21. VIP RANDOM (Random 22 logic)",
    "KILLER_WAVE": "22. BẮT SÓNG SÁT THỦ",
    "PSYCHO_ANALYSIS": "23. PHÂN TÍCH TÂM LÝ",
    "MARKOV_CHAIN": "24. CHUỖI MARKOV",
    "DEEP_LEARNING": "25. HỌC SÂU (Enhanced)",
    "REINFORCEMENT": "26. HỌC TĂNG CƯỜNG",
    "BAYESIAN": "27. XÁC SUẤT BAYES",
    "K_MEANS": "28. PHÂN CỤM K-MEANS",
    "NEURAL": "29. MẠNG NƠ-RON",
    "FUZZY": "30. LOGIC MỜ",
    "GENETIC": "31. THUẬT TOÁN DI TRUYỀN",
    "ANT_COLONY": "32. KIẾN BÒ",
    "PARTICLE_SWARM": "33. BẦY ĐÀN",
    "KNN": "34. K-NEAREST NEIGHBORS",
    "DECISION_TREE": "35. CÂY QUYẾT ĐỊNH",
    "RANDOM_FOREST": "36. RỪNG NGẪU NHIÊN",
    "GRADIENT_BOOST": "37. TĂNG CƯỜNG GRADIENT",
    "LSTM": "38. LSTM",
    "TRANSFORMER": "39. TRANSFORMER",
    "ENSEMBLE": "40. TỔNG HỢP (Enhanced)",
    "CYCLE_ANALYSIS": "41. PHÂN TÍCH CHU KỲ (Mới)",
    "TREND_ANALYSIS": "42. PHÂN TÍCH XU HƯỚNG (Mới)",
    "SAFE_RISK": "43. RỦI RO AN TOÀN (VIP)",
}

settings = {"algo": "RANDOM"}
STRATEGY_CONFIG_FILE = "strategy_tst.json"

def get_available_ai_list(key_type: str = "free") -> List[str]:
    """FREE = 10 AI, VIP = toàn bộ."""
    if key_type == "vip":
        return FREE_AI_LIST + VIP_AI_LIST
    return list(FREE_AI_LIST)  # đúng 10 AI


def get_available_lotto_ai_list(key_type: str = "free") -> List[str]:
    """Lotto: FREE = 5 AI, VIP = full (CDTD algorithms nếu có)."""
    if key_type == "vip":
        try:
            return list(CDTD_ALGORITHMS.keys())
        except NameError:
            return list(LOTTO_FREE_AI_LIST)
    return list(LOTTO_FREE_AI_LIST)


def is_ai_available(ai_key: str, key_type: str = "free") -> bool:
    available = get_available_ai_list(key_type)
    return ai_key in available

# ================== HÀM HỖ TRỢ ==================

def _parse_number(x: Any) -> Optional[float]:
    if x is None:
        return None
    if isinstance(x, (int, float)):
        return float(x)
    s = str(x)
    _num_re = re.compile(r"-?\d+[\d,]*\.?\d*")
    m = _num_re.search(s)
    if not m:
        return None
    token = m.group(0).replace(",", "")
    try:
        return float(token)
    except Exception:
        return None

def human_ts() -> str:
    return datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")

def balance_headers_for(uid: Optional[int] = None, secret: Optional[str] = None) -> Dict[str, str]:
    h = {"accept": "*/*", "accept-language": "vi,en;q=0.9", "cache-control": "no-cache", "country-code": "vn", "origin": "https://xworld.info", "pragma": "no-cache", "referer": "https://xworld.info/", "user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36", "user-login": "login_v2", "xb-language": "vi-VN"}
    if uid is not None:
        h["user-id"] = str(uid)
    if secret:
        h["user-secret-key"] = str(secret)
    return h

def fetch_balances_3games(retries=3, timeout=8, params=None, uid=None, secret=None):
    global current_build, current_usdt, current_world, last_balance_ts, starting_balance, last_balance_val, cumulative_profit
    uid = uid or USER_ID
    secret = secret or SECRET_KEY
    WALLET_API_URL = "https://wallet.3games.io/api/wallet/user_asset"
    payload = {"user_id": int(uid) if uid is not None else None, "source": "home"}
    attempt = 0
    while attempt <= retries:
        attempt += 1
        try:
            HTTP = requests.Session()
            r = HTTP.post(WALLET_API_URL, json=payload, headers=balance_headers_for(uid, secret), timeout=timeout)
            r.raise_for_status()
            j = r.json()
            data = j.get("data", {}) if isinstance(j, dict) else {}
            ua = data.get("user_asset", {}) if isinstance(data, dict) else {}
            build = _parse_number(ua.get("BUILD"))
            world = _parse_number(ua.get("WORLD"))
            usdt = _parse_number(ua.get("USDT"))
            if build is not None:
                if starting_balance is None:
                    starting_balance = build
                # Giống CDTD: P&L chỉ thay đổi theo số dư wallet sau khi có kết quả.
                current_build = build
                last_balance_val = current_build
                if starting_balance is not None:
                    cumulative_profit = current_build - starting_balance
            if usdt is not None:
                current_usdt = usdt
            if world is not None:
                current_world = world
            last_balance_ts = time.time()
            return current_build, current_world, current_usdt
        except Exception as e:
            time.sleep(min(1.5 * attempt, 4))
    return current_build, current_world, current_usdt

def api_headers() -> Dict[str, str]:
    return {"content-type": "application/json", "user-agent": "Mozilla/5.0", "user-id": str(USER_ID) if USER_ID else "", "user-secret-key": SECRET_KEY if SECRET_KEY else ""}

BET_API_URL = "https://api.escapemaster.net/escape_game/bet"

# Random delay trước mỗi lệnh cược (giây) — giảm pattern máy móc
BET_DELAY_MIN = 1.2
BET_DELAY_MAX = 4.0


def human_bet_delay(label: str = "") -> float:
    """Chờ ngẫu nhiên trước khi gửi cược."""
    lo = float(BET_DELAY_MIN)
    hi = float(BET_DELAY_MAX)
    if hi < lo:
        lo, hi = hi, lo
    delay = random.uniform(lo, hi)
    try:
        msg = f"⏳ Chờ {delay:.1f}s trước khi cược"
        if label:
            msg += f" ({label})"
        safe_console_print(f"[dim]{msg}...[/]")
    except Exception:
        pass
    time.sleep(delay)
    return delay


def place_bet_http(issue: int, room_id: int, amount: float) -> dict:
    try:
        payload = {
            "asset_type": "BUILD",
            "user_id": USER_ID,
            "room_id": int(room_id),
            "bet_amount": float(amount),
        }
        response = requests.post(
            BET_API_URL,
            headers=api_headers(),
            json=payload,
            timeout=8,
        )
        try:
            return response.json()
        except Exception:
            return {"raw": response.text, "http_status": response.status_code}
    except Exception as e:
        return {"error": str(e)}

def record_bet(issue: int, room_id: int, amount: float, resp: dict, algo_used: Optional[str] = None) -> dict:
    now = datetime.now(tz).strftime("%H:%M:%S")
    rec = {"issue": issue, "room": room_id, "amount": float(amount), "time": now, "resp": resp, "result": "Đang", "algo": algo_used, "delta": 0.0, "win_streak": win_streak, "lose_streak": lose_streak}
    bet_history.append(rec)
    return rec

def refresh_balance_after_bet(amount: float) -> None:
    """Refresh nhẹ sau khi cược nhưng không trừ tạm P&L."""
    try:
        time.sleep(0.6)
        fetch_balances_3games(retries=1, timeout=5)
    except Exception:
        pass

def place_bet_async(issue: int, room_id: int, amount: float, algo_used: Optional[str] = None):
    # Chặn trùng: cùng kỳ + cùng phòng chỉ gửi 1 lần
    try:
        key = (int(issue), int(room_id))
    except Exception:
        key = (issue, room_id)
    if key in bet_room_sent:
        return
    bet_room_sent.add(key)
    try:
        bet_sent_for_issue.add(int(issue))
    except Exception:
        bet_sent_for_issue.add(issue)

    def worker():
        global prediction_locked, ui_state
        safe_console_print(f"[cyan]Đang đặt {amount} BUILD -> PHÒNG_{room_id} (v{issue}) — Thuật toán: {algo_used}[/]")
        human_bet_delay(f"P{room_id} · kỳ {issue}")
        res = place_bet_http(issue, room_id, amount)
        ok = isinstance(res, dict) and (
            res.get("msg") == "ok"
            or res.get("code") == 0
            or res.get("status") in ("ok", 1)
            or str(res.get("msg", "")).lower() in ("success", "thanh cong", "thành công")
        )
        rec = record_bet(issue, room_id, amount, res, algo_used=algo_used)
        if ok:
            bet_sent_for_issue.add(issue)
            rec["result"] = "Đang"
            threading.Thread(
                target=refresh_balance_after_bet,
                args=(float(amount),),
                daemon=True,
            ).start()
            safe_console_print(f"[green]✅ Đặt thành công {amount} BUILD vào PHÒNG_{room_id} (v{issue}).[/]")
        else:
            rec["result"] = "Lỗi"
            # Không unlock cả kỳ (tránh cược lại nhiều lần). Cho phép retry đúng 1 phòng này.
            try:
                bet_room_sent.discard((int(issue), int(room_id)))
            except Exception:
                bet_room_sent.discard((issue, room_id))
            safe_console_print(f"[red]❌ Đặt lỗi v{issue} P{room_id}: {res}[/]")
    threading.Thread(target=worker, daemon=True).start()

def lock_prediction_if_needed(force: bool = False):
    global prediction_locked, predicted_room, predicted_rooms, ui_state, current_bet, _rounds_placed_since_skip, skip_next_round_flag, _skip_rounds_remaining, stop_flag, num_rooms, round_warning
    
    if stop_flag:
        return
    if check_key_expiry_and_stop("VTH trước cược"):
        return
    if issue_id is None:
        return

    # Đã xử lý kỳ này (cược hoặc bỏ theo setting) → không đụng lại
    try:
        iid = int(issue_id)
    except Exception:
        iid = issue_id
    try:
        if iid in {int(x) for x in bet_sent_for_issue} or iid in {int(x) for x in skipped_for_issue}:
            prediction_locked = True
            return
    except Exception:
        if issue_id in bet_sent_for_issue or issue_id in skipped_for_issue:
            prediction_locked = True
            return

    # Nghỉ theo setting — TRƯỚC khi chọn phòng / cược
    if _skip_rounds_remaining > 0:
        safe_console_print(f"[yellow]⏸️ Đang nghỉ {_skip_rounds_remaining} ván theo cấu hình sau khi thua.[/]")
        _skip_rounds_remaining -= 1
        try:
            skipped_for_issue.add(iid)
        except Exception:
            skipped_for_issue.add(issue_id)
        prediction_locked = True
        predicted_rooms = []
        predicted_room = None
        round_warning = "Nghỉ theo cấu hình (sau khi thua)"
        ui_state = "SKIP"
        return
    if skip_next_round_flag:
        safe_console_print("[yellow]⏸️ Tạm bỏ 1 ván (cấu hình bỏ qua định kỳ).[/]")
        skip_next_round_flag = False
        try:
            skipped_for_issue.add(iid)
        except Exception:
            skipped_for_issue.add(issue_id)
        prediction_locked = True
        predicted_rooms = []
        predicted_room = None
        round_warning = "Bỏ ván theo cấu hình (định kỳ)"
        ui_state = "SKIP"
        return

    # Bỏ ngẫu nhiên % kỳ (giảm pattern bot)
    try:
        pct = float(random_skip_pct or 0)
    except Exception:
        pct = 0.0
    if pct > 0 and random.random() * 100.0 < min(40.0, max(0.0, pct)):
        safe_console_print(f"[yellow]🎲 Bỏ ngẫu nhiên ván này ({pct:.0f}% setting).[/]")
        try:
            skipped_for_issue.add(iid)
        except Exception:
            skipped_for_issue.add(issue_id)
        prediction_locked = True
        predicted_rooms = []
        predicted_room = None
        round_warning = f"Bỏ ngẫu nhiên ({pct:.0f}%)"
        ui_state = "SKIP"
        return

    if prediction_locked and not force:
        # Nếu đã khóa nhưng chưa có lệnh pending kỳ này → mở khóa để thử lại
        has_pending = False
        try:
            for b in bet_history:
                if str(b.get("issue")) == str(issue_id) and str(b.get("result", "")).lower() in (
                    "đang", "dang", "pending", "chờ", "cho", "wait", ""
                ):
                    has_pending = True
                    break
        except Exception:
            pass
        if has_pending:
            return
        # không pending + chưa sent → cho đặt lại
        prediction_locked = False
    
    mode = settings.get("algo", "ENSEMBLE")
    n_pick = max(1, min(4, int(num_rooms or 1)))
    chosen_list, algo_used = choose_rooms_multi(mode, n_pick)
    if not chosen_list:
        # Fallback: không bỏ ván — chọn ngẫu nhiên theo num_rooms
        chosen_list = random.sample(list(ROOM_ORDER), k=min(n_pick, len(ROOM_ORDER)))
        algo_used = mode
    round_warning = ""
    predicted_rooms = list(chosen_list)
    predicted_room = chosen_list[0] if chosen_list else None
    prediction_locked = True
    ui_state = "PREDICTED"

    if run_mode != "AUTO":
        safe_console_print("[cyan]Mode MANUAL — đã khóa dự đoán, không tự cược.[/]")
        return
    if run_mode == "AUTO":
        bld = current_build
        if bld is None:
            bld, _, _ = fetch_balances_3games(retries=1, timeout=3)
            if bld is None:
                safe_console_print("[yellow]⚠️ Không lấy được số dư, sẽ thử lại kỳ sau...[/]")
                prediction_locked = False
                ui_state = "ANALYZING"
                return
        if current_bet is None:
            current_bet = base_bet
        amt = float(current_bet)
        if amt <= 0:
            current_bet = base_bet
            amt = float(base_bet)
        # đủ vốn cho tất cả phòng
        total_need = amt * max(1, len(chosen_list))
        if total_need > float(bld or 0):
            safe_console_print(
                f"[red]🔥 Vốn không đủ multi (cần {total_need:,.2f}, có {float(bld or 0):,.2f}).[/red]"
            )
            current_bet = base_bet
            amt = float(current_bet)
            total_need = amt * max(1, len(chosen_list))
            # giảm số phòng nếu vẫn thiếu
            while len(chosen_list) > 1 and amt * len(chosen_list) > float(bld or 0):
                chosen_list = chosen_list[:-1]
            predicted_rooms = list(chosen_list)
            predicted_room = chosen_list[0] if chosen_list else None
            if amt > float(bld or 0) or not chosen_list:
                safe_console_print(
                    f"[yellow]⚠️ Vốn < cược. Bỏ ván này, không dừng tool.[/yellow]"
                )
                prediction_locked = False
                ui_state = "ANALYZING"
                return
        # Đánh dấu kỳ đã xử lý NGAY (tránh race gọi lock nhiều lần → cược trùng)
        try:
            bet_sent_for_issue.add(int(issue_id))
        except Exception:
            bet_sent_for_issue.add(issue_id)
        prediction_locked = True
        ui_state = "BETTING"
        # Chỉ đúng số phòng theo setting
        rooms_to_bet = list(chosen_list)[: max(1, min(4, int(num_rooms or 1)))]
        predicted_rooms = list(rooms_to_bet)
        predicted_room = rooms_to_bet[0] if rooms_to_bet else None
        for room in rooms_to_bet:
            place_bet_async(issue_id, room, amt, algo_used=algo_used)
        _rounds_placed_since_skip += 1
        if bet_rounds_before_skip > 0 and _rounds_placed_since_skip >= bet_rounds_before_skip:
            skip_next_round_flag = True
            _rounds_placed_since_skip = 0



def _vth_kill_gap(room: int) -> float:
    """Số ván từ lần kill gần nhất (cao = an toàn hơn)."""
    if not game_kill_log:
        return 8.0
    log = list(game_kill_log)
    for i in range(len(log) - 1, -1, -1):
        if log[i] == room:
            return float(len(log) - 1 - i)
    return float(min(12, len(log) + 2))


def _vth_transition_safe(room: int) -> float:
    """P(không bị kill ngay sau last) — điểm an toàn Markov."""
    if len(game_kill_log) < 2:
        return 0.5
    last = game_kill_log[-1]
    trans = defaultdict(int)
    total = 0
    for a, b in zip(game_kill_log, list(game_kill_log)[1:]):
        if a == last:
            trans[b] += 1
            total += 1
    if total == 0:
        return 0.5
    # xác suất room bị kill tiếp
    p_kill = (trans.get(room, 0) + 0.35) / (total + 0.35 * len(ROOM_ORDER))
    return 1.0 - p_kill


def _vth_unified_scores(noise: float = 0.04) -> Dict[int, float]:
    """
    Điểm an toàn hợp nhất (cao = nên cược):
    survival + gap + markov + anti-crowd + anti-money + risk% (nếu có).
    """
    max_p = max((room_state[r].get("players", 0) or 0) for r in ROOM_ORDER) or 1
    max_b = max((room_state[r].get("bet", 0) or 0) for r in ROOM_ORDER) or 1.0
    risk_by = {}
    try:
        for row in compute_vth_room_risk() or []:
            rid = int(row.get("id") or row.get("room") or 0)
            if rid:
                risk_by[rid] = float(row.get("risk_pct", 50) or 50) / 100.0
    except Exception:
        pass

    scores = {}
    for r in ROOM_ORDER:
        kills = int(room_stats[r].get("kills", 0) or 0)
        survives = int(room_stats[r].get("survives", 0) or 0)
        survival = (survives + 1.2) / (kills + survives + 2.4)
        gap = min(1.0, _vth_kill_gap(r) / 8.0)
        markov_safe = _vth_transition_safe(r)
        crowd = 1.0 - (float(room_state[r].get("players", 0) or 0) / max_p)
        money = 1.0 - (float(room_state[r].get("bet", 0) or 0) / max_b)
        risk_safe = 1.0 - risk_by.get(r, 0.5)

        scores[r] = (
            0.24 * survival
            + 0.18 * gap
            + 0.18 * markov_safe
            + 0.14 * crowd
            + 0.12 * money
            + 0.14 * risk_safe
        )
        if noise:
            scores[r] += random.uniform(-noise, noise)
    return scores


def _vth_pick_max(scores: Dict[int, float]) -> int:
    if not scores:
        return random.choice(ROOM_ORDER)
    best = max(scores.values())
    tops = [r for r, v in scores.items() if abs(v - best) < 1e-9]
    return random.choice(tops)



# Ngưỡng giảm thua: bỏ ván quá rủi ro / ưu tiên phòng risk thấp
VTH_SKIP_IF_SAFEST_ABOVE = 78.0   # an toàn nhất vẫn >78% → bỏ ván
VTH_DROP_ROOM_ABOVE = 70.0        # loại phòng risk cao khỏi multi
CDTD_SKIP_IF_SAFEST_ABOVE = 72.0
CDTD_DROP_NV_ABOVE = 68.0


def _vth_risk_map() -> Dict[int, float]:
    try:
        return {int(r["id"]): float(r.get("risk_pct", 50) or 50) for r in (compute_vth_room_risk() or [])}
    except Exception:
        return {}


def _vth_conservative_pick(candidates: List[int], n: int = 1) -> List[int]:
    """Ưu tiên risk thấp — luôn trả đủ n phòng (không bỏ ván)."""
    n = max(1, min(4, int(n or 1)))
    rm = _vth_risk_map()
    pool = list(candidates) if candidates else list(ROOM_ORDER)
    pool = sorted(set(pool), key=lambda r: (rm.get(r, 55.0), r))
    out = list(pool)
    if len(out) < n:
        for r in sorted(ROOM_ORDER, key=lambda x: (rm.get(x, 55.0), x)):
            if r not in out:
                out.append(r)
            if len(out) >= n:
                break
    if not out:
        out = list(ROOM_ORDER)[:n]
    return out[:n]


def _cdtd_conservative_pick(candidates: List[int], n: int = 1, data_top10=None, data_top100=None) -> List[int]:
    """Ưu tiên risk thấp — luôn trả đủ n NV (không bỏ ván)."""
    n = max(1, min(5, int(n or 1)))
    try:
        rows = compute_cdtd_nv_risk(data_top10, data_top100) or []
        rm = {int(r["id"]): float(r.get("risk_pct", 50) or 50) for r in rows}
    except Exception:
        rm = {i: 50.0 for i in range(1, 7)}
    pool = [c for c in candidates if 1 <= int(c) <= 6] if candidates else list(range(1, 7))
    pool = sorted(set(int(x) for x in pool), key=lambda i: (rm.get(i, 55.0), i))
    out = list(pool)
    if len(out) < n:
        for i in sorted(range(1, 7), key=lambda x: (rm.get(x, 55.0), x)):
            if i not in out:
                out.append(i)
            if len(out) >= n:
                break
    if not out:
        out = list(range(1, 7))[:n]
    return out[:n]



def _vth_round_danger_check() -> tuple:
    """
    Phân tích độ ổn định kỳ hiện tại.
    Returns: (is_danger: bool, message: str)
    """
    try:
        rows = compute_vth_room_risk() or []
    except Exception:
        rows = []
    if not rows:
        return True, "Chưa đủ dữ liệu — phân tích không ổn"
    risks = [float(r.get("risk_pct", 50) or 50) for r in rows]
    safest = min(risks)
    avg = sum(risks) / max(1, len(risks))
    high_n = sum(1 for x in risks if x >= 70)
    # mẫu kill quá ít → kém tin cậy
    samples = sum(int(r.get("samples", 0) or 0) for r in rows)
    if samples < 8 and len(list(game_kill_log or [])) < 5:
        return True, f"Dữ liệu mỏng (mẫu {samples}) — chưa ổn để cược"
    if safest >= VTH_SKIP_IF_SAFEST_ABOVE:
        return True, f"Nguy hiểm: phòng an toàn nhất vẫn {safest:.0f}% risk"
    if avg >= 66.0:
        return True, f"Nguy hiểm: risk trung bình {avg:.0f}% quá cao"
    if high_n >= 6:
        return True, f"Nguy hiểm: {high_n}/8 phòng risk CAO"
    # chênh lệch quá nhỏ + avg cao → không có chỗ trú
    if (max(risks) - min(risks)) < 8 and avg >= 58:
        return True, "Nguy hiểm: mọi phòng risk gần nhau, không có lựa chọn ổn"
    return False, ""


def _cdtd_round_danger_check(data_top10=None, data_top100=None) -> tuple:
    """Returns (is_danger, message) cho CDTD."""
    try:
        rows = compute_cdtd_nv_risk(data_top10, data_top100) or []
    except Exception:
        rows = []
    if not rows:
        return True, "Chưa đủ dữ liệu đua — phân tích không ổn"
    risks = [float(r.get("risk_pct", 50) or 50) for r in rows]
    safest = min(risks)
    avg = sum(risks) / max(1, len(risks))
    high_n = sum(1 for x in risks if x >= 68)
    if safest >= CDTD_SKIP_IF_SAFEST_ABOVE:
        return True, f"Nguy hiểm: NV an toàn nhất vẫn {safest:.0f}% risk"
    if avg >= 64.0:
        return True, f"Nguy hiểm: risk trung bình {avg:.0f}% quá cao"
    if high_n >= 5:
        return True, f"Nguy hiểm: {high_n}/6 NV risk cao"
    if (max(risks) - min(risks)) < 6 and avg >= 55:
        return True, "Nguy hiểm: form mơ hồ, không có NV nổi trội an toàn"
    return False, ""


def choose_safe_risk() -> int:
    """VIP: tối ưu giảm thua — risk thấp là trọng số chính."""
    scores = _vth_unified_scores(noise=0.015)
    try:
        for row in compute_vth_room_risk() or []:
            rid = int(row.get("id") or 0)
            if rid in scores:
                rp = float(row.get("risk_pct", 50) or 50) / 100.0
                scores[rid] += 0.55 * (1.0 - rp)
                if rp > 0.70:
                    scores[rid] -= 0.45
    except Exception:
        pass
    # conservative: chỉ xét top risk thấp
    picks = _vth_conservative_pick(list(scores.keys()), 1)
    if picks:
        return picks[0]
    return _vth_pick_max(scores)

def choose_random() -> int:
    return random.choice(ROOM_ORDER)

def choose_min_player_bet() -> int:
    if not any(rs.get('players', 0) > 0 or rs.get('bet', 0) > 0 for rs in room_state.values()):
        return choose_random()
    player_ranks = sorted(ROOM_ORDER, key=lambda r: room_state[r]['players'])
    bet_ranks = sorted(ROOM_ORDER, key=lambda r: room_state[r]['bet'])
    scores = defaultdict(int)
    for i, r in enumerate(player_ranks):
        scores[r] += i
    for i, r in enumerate(bet_ranks):
        scores[r] += i
    return min(scores, key=scores.get)

def choose_probability() -> int:
    scores = {}
    for r in ROOM_ORDER:
        kills = room_stats[r].get('kills', 0)
        survives = room_stats[r].get('survives', 0)
        survival_rate = (survives + 1) / (kills + survives + 2)
        scores[r] = survival_rate
    return max(scores, key=scores.get)

def choose_follow_killer() -> int:
    if last_killed_room is not None and last_killed_room in ROOM_ORDER:
        return last_killed_room
    return random.choice(ROOM_ORDER)

def choose_sequential() -> int:
    global _sequential_bet_index
    room_to_bet = ROOM_ORDER[_sequential_bet_index]
    _sequential_bet_index = (_sequential_bet_index + 1) % len(ROOM_ORDER)
    return room_to_bet

def choose_killer_personality_enhanced() -> int:
    if len(killer_history) < 3:
        return choose_random()
    
    recent_killers = killer_history[-15:] if len(killer_history) > 15 else killer_history
    avg_players = sum(h['players'] for h in recent_killers) / len(recent_killers)
    avg_bet = sum(h['bet'] for h in recent_killers) / len(recent_killers)
    player_var = sum((h['players'] - avg_players) ** 2 for h in recent_killers) / len(recent_killers)
    bet_var = sum((h['bet'] - avg_bet) ** 2 for h in recent_killers) / len(recent_killers)
    stability_factor = 1.5 if player_var < 2 and bet_var < 100 else 0.8
    
    avoidance_scores = {}
    for r in ROOM_ORDER:
        current_players = room_state[r]['players']
        current_bet = room_state[r]['bet']
        player_dist = abs(current_players - avg_players) / (avg_players + 1)
        bet_dist = abs(current_bet - avg_bet) / (avg_bet + 1)
        base_score = (player_dist + bet_dist) * stability_factor
        kills = room_stats[r].get('kills', 0)
        survives = room_stats[r].get('survives', 0)
        survival_rate = (survives + 1) / (kills + survives + 2)
        base_score += survival_rate * 0.3
        avoidance_scores[r] = base_score
    
    return max(avoidance_scores, key=avoidance_scores.get)

def choose_smart_safe_enhanced() -> int:
    """Smart Safe v2 — unified score + lệch pattern sát thủ."""
    scores = _vth_unified_scores(noise=0.05)
    if killer_history:
        avg_p = sum(h.get("players", 0) for h in killer_history) / len(killer_history)
        avg_b = sum(h.get("bet", 0) for h in killer_history) / len(killer_history)
        for r in ROOM_ORDER:
            # càng khác profile sát thủ càng an toàn
            pd = abs((room_state[r].get("players", 0) or 0) - avg_p) / (avg_p + 1)
            bd = abs((room_state[r].get("bet", 0) or 0) - avg_b) / (avg_b + 1)
            scores[r] += 0.12 * (pd + bd)
    return _vth_pick_max(scores)

def choose_follow_killer_delayed() -> int:
    global last_killed_room_delayed
    if last_killed_room_delayed is not None and last_killed_room_delayed in ROOM_ORDER:
        return last_killed_room_delayed
    return random.choice(ROOM_ORDER)

def choose_hide_seek_master() -> int:
    danger_scores = {}
    max_players = max(rs['players'] for rs in room_state.values()) or 1
    max_bet = max(rs['bet'] for rs in room_state.values()) or 1
    avg_players_killed = 0
    avg_bet_killed = 0
    if killer_history:
        avg_players_killed = sum(h['players'] for h in killer_history) / len(killer_history)
        avg_bet_killed = sum(h['bet'] for h in killer_history) / len(killer_history)
    for r in ROOM_ORDER:
        kills = room_stats[r].get('kills', 0)
        survives = room_stats[r].get('survives', 0)
        hist_danger = (kills + 1) / (kills + survives + 2)
        crowd_danger = room_state[r]['players'] / max_players
        money_danger = room_state[r]['bet'] / max_bet
        personality_danger = 0
        if killer_history:
            player_sim = 1 - (abs(room_state[r]['players'] - avg_players_killed) / (avg_players_killed + max_players + 1))
            bet_sim = 1 - (abs(room_state[r]['bet'] - avg_bet_killed) / (avg_bet_killed + max_bet + 1))
            personality_danger = (player_sim + bet_sim) / 2
        recency_penalty = 0.0  # không chặn phòng vừa kill
        total_danger = (0.3 * hist_danger) + (0.2 * crowd_danger) + (0.2 * money_danger) + (0.3 * personality_danger) + recency_penalty
        danger_scores[r] = total_danger
    return min(danger_scores, key=danger_scores.get)

def choose_balance() -> int:
    scores = {}
    total_players = sum(rs['players'] for rs in room_state.values())
    total_bet = sum(rs['bet'] for rs in room_state.values())
    avg_players = total_players / len(ROOM_ORDER) if total_players > 0 else 0
    avg_bet = total_bet / len(ROOM_ORDER) if total_bet > 0 else 0
    for r in ROOM_ORDER:
        players = room_state[r]['players']
        bet = room_state[r]['bet']
        score = abs(players - avg_players) / (avg_players + 1) + abs(bet - avg_bet) / (avg_bet + 1)
        scores[r] = score
    return min(scores, key=scores.get)

def choose_most_players() -> int:
    return max(ROOM_ORDER, key=lambda r: room_state[r]['players'])

def choose_least_players() -> int:
    return min(ROOM_ORDER, key=lambda r: room_state[r]['players'])

def choose_richest() -> int:
    return max(ROOM_ORDER, key=lambda r: room_state[r]['bet'])

def choose_poorest() -> int:
    return min(ROOM_ORDER, key=lambda r: room_state[r]['bet'])

def choose_alternate() -> int:
    if len(bet_history) < 2:
        return random.choice(ROOM_ORDER)
    last_rooms = [b.get('room') for b in list(bet_history)[-3:] if b.get('room')]
    candidates = [r for r in ROOM_ORDER if r not in last_rooms]
    if candidates:
        return random.choice(candidates)
    return random.choice(ROOM_ORDER)

def choose_avoid_result() -> int:
    if last_killed_room is None:
        return random.choice(ROOM_ORDER)
    candidates = [r for r in ROOM_ORDER if r != last_killed_room]
    if not candidates:
        return random.choice(ROOM_ORDER)
    return random.choice(candidates)

def choose_cold() -> int:
    player_ranks = sorted(ROOM_ORDER, key=lambda r: room_state[r]['players'])
    bet_ranks = sorted(ROOM_ORDER, key=lambda r: room_state[r]['bet'])
    scores = defaultdict(int)
    for i, r in enumerate(reversed(player_ranks)):
        scores[r] += i
    for i, r in enumerate(reversed(bet_ranks)):
        scores[r] += i
    return min(scores, key=scores.get)

def choose_hot() -> int:
    player_ranks = sorted(ROOM_ORDER, key=lambda r: room_state[r]['players'])
    bet_ranks = sorted(ROOM_ORDER, key=lambda r: room_state[r]['bet'])
    scores = defaultdict(int)
    for i, r in enumerate(player_ranks):
        scores[r] += i
    for i, r in enumerate(bet_ranks):
        scores[r] += i
    return max(scores, key=scores.get)

def choose_median() -> int:
    if not any(rs['players'] > 0 for rs in room_state.values()):
        return random.choice(ROOM_ORDER)
    players_list = sorted(ROOM_ORDER, key=lambda r: room_state[r]['players'])
    bet_list = sorted(ROOM_ORDER, key=lambda r: room_state[r]['bet'])
    median_players = players_list[len(players_list) // 2]
    median_bet = bet_list[len(bet_list) // 2]
    if median_players == median_bet:
        return median_players
    scores = {}
    for r in ROOM_ORDER:
        dist_players = abs(room_state[r]['players'] - room_state[median_players]['players'])
        dist_bet = abs(room_state[r]['bet'] - room_state[median_bet]['bet'])
        scores[r] = dist_players + dist_bet
    return min(scores, key=scores.get)

def choose_pattern() -> int:
    if len(game_kill_log) < 3:
        return random.choice(ROOM_ORDER)
    last_3 = list(game_kill_log)[-3:]
    if len(last_3) == 3 and last_3[0] == last_3[2]:
        return last_3[1]
    return random.choice(ROOM_ORDER)

def choose_cycle_analysis() -> int:
    if len(game_kill_log) < 6:
        return choose_random()
    
    history = list(game_kill_log)
    best_cycle = None
    best_score = -1
    
    for cycle_len in range(2, 11):
        if len(history) >= cycle_len * 2:
            matches = 0
            total = len(history) - cycle_len
            for i in range(total):
                if history[i] == history[i + cycle_len]:
                    matches += 1
            score = matches / max(1, total)
            if score > best_score:
                best_score = score
                best_cycle = cycle_len
    
    if best_cycle and best_score > 0.6:
        last_cycle_start = len(history) - best_cycle
        if last_cycle_start >= 0:
            predicted = history[last_cycle_start]
            if predicted in ROOM_ORDER:
                if predicted == last_killed_room:
                    alternatives = [r for r in ROOM_ORDER if r != predicted]
                    if alternatives:
                        return random.choice(alternatives)
                return predicted
    
    return choose_smart_safe_enhanced()

def choose_trend_analysis() -> int:
    if len(killer_history) < 5:
        return choose_random()
    
    player_trends = []
    bet_trends = []
    for h in killer_history[-10:]:
        player_trends.append(h['players'])
        bet_trends.append(h['bet'])
    
    if len(player_trends) >= 3:
        player_slope = (player_trends[-1] - player_trends[0]) / max(1, len(player_trends))
        bet_slope = (bet_trends[-1] - bet_trends[0]) / max(1, len(bet_trends))
        next_players = player_trends[-1] + player_slope * 1.5
        next_bet = bet_trends[-1] + bet_slope * 1.5
        
        scores = {}
        for r in ROOM_ORDER:
            if r == last_killed_room:
                scores[r] = -999999
                continue
            players = room_state[r]['players']
            bet = room_state[r]['bet']
            player_dist = abs(players - next_players) / (next_players + 1)
            bet_dist = abs(bet - next_bet) / (next_bet + 1)
            scores[r] = player_dist + bet_dist
        
        return max(scores, key=scores.get)
    
    return choose_random()

def choose_vip_random() -> int:
    logic_list = [
        choose_random, choose_min_player_bet, choose_probability,
        choose_follow_killer, choose_sequential, choose_killer_personality_enhanced,
        choose_smart_safe_enhanced, choose_follow_killer_delayed, choose_hide_seek_master,
        choose_balance, choose_most_players, choose_least_players,
        choose_richest, choose_poorest, choose_alternate,
        choose_avoid_result, choose_cold, choose_hot, choose_median, choose_pattern,
        choose_cycle_analysis, choose_trend_analysis
    ]
    sys_random = random.SystemRandom()
    chosen_func = sys_random.choice(logic_list)
    return chosen_func()

def choose_killer_wave() -> int:
    if len(game_kill_log) < 4:
        return choose_random()
    last_4 = list(game_kill_log)[-4:]
    for i in range(1, 4):
        if len(last_4) >= i*2 and last_4[-i:] == last_4[-i*2:-i]:
            predicted = last_4[-i-1] if len(last_4) > i else last_4[-1]
            return predicted
    return choose_smart_safe_enhanced()

def choose_psycho_analysis() -> int:
    max_players_room = max(ROOM_ORDER, key=lambda r: room_state[r]['players'])
    max_bet_room = max(ROOM_ORDER, key=lambda r: room_state[r]['bet'])
    crowd_favorite = max_players_room if room_state[max_players_room]['players'] > room_state[max_bet_room]['players'] else max_bet_room
    candidates = [r for r in ROOM_ORDER if r != crowd_favorite]
    if candidates:
        return min(candidates, key=lambda r: room_state[r]['players'] + room_state[r]['bet'] * 0.01)
    return choose_random()

def choose_markov_chain() -> int:
    """Markov v2: dự đoán phòng kill kế → cược phòng KHÁC (an toàn)."""
    if len(game_kill_log) < 3:
        return _vth_pick_max(_vth_unified_scores())
    # bậc 1
    t1 = defaultdict(lambda: defaultdict(float))
    for a, b in zip(game_kill_log, list(game_kill_log)[1:]):
        t1[a][b] += 1.0
    last = game_kill_log[-1]
    # bậc 2 nếu đủ dữ liệu
    pred_kill_scores = {r: 0.15 for r in ROOM_ORDER}
    if len(game_kill_log) >= 3:
        t2 = defaultdict(lambda: defaultdict(float))
        log = list(game_kill_log)
        for i in range(len(log) - 2):
            t2[(log[i], log[i + 1])][log[i + 2]] += 1.0
        key = (log[-2], log[-1])
        if t2[key]:
            for r, c in t2[key].items():
                pred_kill_scores[r] += c
    if t1[last]:
        for r, c in t1[last].items():
            pred_kill_scores[r] += c * 0.85
    # chọn phòng ít khả năng bị kill nhất
    return min(pred_kill_scores, key=pred_kill_scores.get)

def choose_deep_learning_enhanced() -> int:
    if len(killer_history) < 5:
        return choose_random()
    
    weights = {}
    for r in ROOM_ORDER:
        kills = room_stats[r].get('kills', 0)
        survives = room_stats[r].get('survives', 0)
        survival_rate = (survives + 1) / (kills + survives + 2)
        
        recent_boost = 0
        if r in game_kill_log:
            recent_count = list(game_kill_log).count(r)
            recent_boost = -0.3 * min(1, recent_count / 3)
        
        trend_boost = 0
        if len(game_kill_log) >= 5:
            last_5 = list(game_kill_log)[-5:]
            if r in last_5:
                recent_appear = last_5.count(r)
                trend_boost = -0.2 * recent_appear
            else:
                trend_boost = 0.1
        
        max_players = max(rs['players'] for rs in room_state.values()) or 1
        max_bet = max(rs['bet'] for rs in room_state.values()) or 1
        crowd_boost = 1 - (room_state[r]['players'] / max_players)
        money_boost = 1 - (room_state[r]['bet'] / max_bet)
        
        killer_pattern_boost = 0
        if len(game_kill_log) >= 3:
            last_3 = list(game_kill_log)[-3:]
            if len(last_3) == 3 and last_3[0] == last_3[2] and last_3[0] == r:
                killer_pattern_boost = -0.4
        
        weights[r] = (0.25 * survival_rate + 0.20 * recent_boost + 0.15 * trend_boost + 0.15 * crowd_boost + 0.10 * money_boost + 0.15 * killer_pattern_boost)
        weights[r] += random.uniform(-0.08, 0.08)
    
    return max(weights, key=weights.get)

def choose_reinforcement() -> int:
    if len(bet_history) < 3:
        return choose_random()
    action_scores = {r: 0 for r in ROOM_ORDER}
    for b in list(bet_history)[-10:]:
        room = b.get('room')
        result = b.get('result')
        if room in ROOM_ORDER and result:
            if result == "Thắng":
                action_scores[room] += 1
            else:
                action_scores[room] -= 0.5
    max_score = max(action_scores.values())
    if max_score <= 0:
        return choose_random()
    best_rooms = [r for r, s in action_scores.items() if s == max_score]
    return random.choice(best_rooms)

def choose_bayesian() -> int:
    """Bayes v2: posterior P(kill) kết hợp form realtime → chọn min."""
    if len(game_kill_log) < 2:
        return _vth_pick_max(_vth_unified_scores())
    room_counts = Counter(game_kill_log)
    total_kills = len(game_kill_log)
    posterior = {}
    for r in ROOM_ORDER:
        prior = 1.0 / len(ROOM_ORDER)
        like = (room_counts.get(r, 0) + 0.8) / (total_kills + 0.8 * len(ROOM_ORDER))
        # evidence: đông / nhiều tiền → sát thủ hay chọn
        max_p = max(room_state[x].get("players", 0) or 0 for x in ROOM_ORDER) or 1
        max_b = max(room_state[x].get("bet", 0) or 0 for x in ROOM_ORDER) or 1
        crowd = (room_state[r].get("players", 0) or 0) / max_p
        money = (room_state[r].get("bet", 0) or 0) / max_b
        evidence = 0.55 + 0.25 * crowd + 0.20 * money
        posterior[r] = prior * like * evidence
    s = sum(posterior.values()) or 1
    for r in posterior:
        posterior[r] /= s
    return min(posterior, key=posterior.get)

def choose_k_means() -> int:
    if len(game_kill_log) < 6:
        return choose_random()
    from collections import defaultdict
    room_features = defaultdict(lambda: [0, 0])
    for i, room in enumerate(list(game_kill_log)[-10:]):
        room_features[room][0] += 1
        room_features[room][1] = i
    cluster_1 = set()
    cluster_2 = set()
    for room, features in room_features.items():
        if features[0] < 2:
            cluster_1.add(room)
        else:
            cluster_2.add(room)
    if cluster_1:
        return random.choice(list(cluster_1))
    return choose_random()

def choose_neural() -> int:
    if len(killer_history) < 3:
        return choose_random()
    scores = {}
    for r in ROOM_ORDER:
        players = room_state[r]['players']
        bet = room_state[r]['bet']
        kills = room_stats[r].get('kills', 0)
        survives = room_stats[r].get('survives', 0)
        layer1 = (0.3 * survives) - (0.5 * kills) + (0.2 * players) - (0.3 * bet)
        layer2 = (0.4 * layer1) + (0.2 * (survives - kills))
        layer3 = (0.5 * layer2) + (0.3 * (1 - players/max(1, max(rs['players'] for rs in room_state.values()))))
        output = 1 / (1 + math.exp(-layer3))
        scores[r] = output
    return max(scores, key=scores.get)

def choose_fuzzy() -> int:
    if len(killer_history) < 2:
        return choose_random()
    scores = {}
    for r in ROOM_ORDER:
        players = room_state[r]['players']
        bet = room_state[r]['bet']
        players_young = max(0, 1 - players/2) if players < 2 else 0
        players_mid = max(0, 1 - abs(players-3)/2) if 1 < players < 5 else 0
        players_old = max(0, (players-4)/2) if players > 4 else 0
        bet_low = max(0, 1 - bet/100) if bet < 100 else 0
        bet_mid = max(0, 1 - abs(bet-300)/200) if 100 < bet < 500 else 0
        bet_high = max(0, (bet-400)/200) if bet > 400 else 0
        rule1 = min(players_young, bet_low)
        rule2 = min(players_old, bet_high)
        rule3 = min(players_mid, bet_mid)
        safety_score = (rule1 * 1.0 + rule2 * 0.0 + rule3 * 0.5) / (rule1 + rule2 + rule3 + 0.01)
        scores[r] = safety_score
    return max(scores, key=scores.get)

def choose_genetic() -> int:
    if len(killer_history) < 5:
        return choose_random()
    population = list(game_kill_log)[-10:]
    if not population:
        return choose_random()
    fitness = {}
    for r in ROOM_ORDER:
        kills = room_stats[r].get('kills', 0)
        survives = room_stats[r].get('survives', 0)
        fitness[r] = (survives + 1) / (kills + survives + 2)
    return max(fitness, key=fitness.get)

def choose_ant_colony() -> int:
    if len(game_kill_log) < 3:
        return choose_random()
    pheromone = {}
    for r in ROOM_ORDER:
        count = list(game_kill_log).count(r)
        pheromone[r] = count / len(game_kill_log) if game_kill_log else 0
    return min(pheromone, key=pheromone.get)

def choose_particle_swarm() -> int:
    if len(killer_history) < 3:
        return choose_random()
    scores = {}
    for r in ROOM_ORDER:
        kills = room_stats[r].get('kills', 0)
        survives = room_stats[r].get('survives', 0)
        survival_rate = (survives + 1) / (kills + survives + 2)
        recent_trend = 0.3 if r in list(game_kill_log)[-3:] else 0
        scores[r] = survival_rate + recent_trend
    return max(scores, key=scores.get)

def choose_knn() -> int:
    if len(game_kill_log) < 3:
        return choose_random()
    k = min(3, len(game_kill_log))
    nearest = list(game_kill_log)[-k:]
    counts = Counter(nearest)
    min_count = min(counts.values())
    candidates = [r for r, c in counts.items() if c == min_count]
    if candidates:
        return random.choice(candidates)
    return choose_random()

def choose_decision_tree() -> int:
    if len(killer_history) < 5:
        return choose_random()
    return choose_probability() if killer_history else choose_random()

def choose_random_forest() -> int:
    if len(killer_history) < 3:
        return choose_random()
    predictions = []
    for _ in range(5):
        if random.random() > 0.5:
            predictions.append(choose_probability())
        else:
            predictions.append(choose_min_player_bet())
    counts = Counter(predictions)
    return max(counts, key=counts.get)

def choose_gradient_boost() -> int:
    if len(killer_history) < 3:
        return choose_random()
    scores = {}
    for r in ROOM_ORDER:
        base_score = 0.5
        kills = room_stats[r].get('kills', 0)
        survives = room_stats[r].get('survives', 0)
        survival_rate = (survives + 1) / (kills + survives + 2)
        base_score += 0.3 * survival_rate
        base_score -= 0.1 * (room_state[r]['players'] / max(1, max(rs['players'] for rs in room_state.values())))
        base_score -= 0.1 * (room_state[r]['bet'] / max(1, max(rs['bet'] for rs in room_state.values())))
        scores[r] = base_score
    return max(scores, key=scores.get)

def choose_lstm() -> int:
    if len(game_kill_log) < 4:
        return choose_random()
    last_5 = list(game_kill_log)[-5:]
    if len(last_5) == 5 and last_5[0] == last_5[3] and last_5[1] == last_5[4]:
        return last_5[2]
    return choose_markov_chain()

def choose_transformer() -> int:
    if len(game_kill_log) < 4:
        return choose_random()
    attention_scores = {}
    for r in ROOM_ORDER:
        kills = room_stats[r].get('kills', 0)
        survives = room_stats[r].get('survives', 0)
        recency = 1 - (list(game_kill_log).count(r) / max(1, len(game_kill_log)))
        attention_scores[r] = (0.4 * recency) + (0.3 * (survives / max(1, kills + survives))) + (0.3 * (1 - room_state[r]['players'] / max(1, max(rs['players'] for rs in room_state.values()))))
    return max(attention_scores, key=attention_scores.get)

def choose_ensemble_enhanced() -> int:
    """Ensemble v3: multi-AI + unified score + adaptive performance + anti-kill."""
    base = _vth_unified_scores(noise=0.02)
    votes = defaultdict(float)
    for r, sc in base.items():
        votes[r] += sc * 1.15

    ai_weights = {
        "choose_safe_risk": 1.45,
        "choose_smart_safe_enhanced": 1.15,
        "choose_probability": 0.9,
        "choose_markov_chain": 1.05,
        "choose_bayesian": 1.0,
        "choose_killer_personality_enhanced": 0.7,
        "choose_deep_learning_enhanced": 0.7,
        "choose_hide_seek_master": 0.5,
        "choose_neural": 0.65,
        "choose_cycle_analysis": 0.6,
        "choose_trend_analysis": 0.55,
        "choose_transformer": 0.55,
    }
    for ai_name, weight in ai_weights.items():
        try:
            func = globals().get(ai_name)
            if not func:
                continue
            room = func()
            w = float(weight)
            perf = AI_PERFORMANCE.get(ai_name, {}) or AI_PERFORMANCE.get(ai_name.replace("choose_", "").upper(), {})
            total_p = int(perf.get("total", 0) or 0)
            if total_p >= 4:
                wr = float(perf.get("wins", 0)) / total_p
                w *= 0.5 + 1.0 * wr
            votes[room] += w
        except Exception:
            continue

    if not votes:
        picks = _vth_conservative_pick(list(ROOM_ORDER), 1)
        return picks[0] if picks else random.choice(ROOM_ORDER)
    top = _vth_pick_max(dict(votes))
    picks = _vth_conservative_pick([top] + sorted(votes.keys(), key=lambda r: votes[r], reverse=True), 1)
    return picks[0] if picks else top

ENHANCED_LOGIC_MAP = {
    "RANDOM": choose_random,
    "MIN_PLAYER_BET": choose_min_player_bet,
    "PROBABILITY": choose_probability,
    "FOLLOW_KILLER": choose_follow_killer,
    "SEQUENTIAL": choose_sequential,
    "KILLER_PERSONALITY": choose_killer_personality_enhanced,
    "SMART_SAFE": choose_smart_safe_enhanced,
    "FOLLOW_KILLER_DELAYED": choose_follow_killer_delayed,
    "HIDE_SEEK_MASTER": choose_hide_seek_master,
    "BALANCE": choose_balance,
    "MOST_PLAYERS": choose_most_players,
    "LEAST_PLAYERS": choose_least_players,
    "RICHEST": choose_richest,
    "POOREST": choose_poorest,
    "ALTERNATE": choose_alternate,
    "AVOID_RESULT": choose_avoid_result,
    "COLD": choose_cold,
    "HOT": choose_hot,
    "MEDIAN": choose_median,
    "PATTERN": choose_pattern,
    "VIP_RANDOM": choose_vip_random,
    "KILLER_WAVE": choose_killer_wave,
    "PSYCHO_ANALYSIS": choose_psycho_analysis,
    "MARKOV_CHAIN": choose_markov_chain,
    "DEEP_LEARNING": choose_deep_learning_enhanced,
    "REINFORCEMENT": choose_reinforcement,
    "BAYESIAN": choose_bayesian,
    "K_MEANS": choose_k_means,
    "NEURAL": choose_neural,
    "FUZZY": choose_fuzzy,
    "GENETIC": choose_genetic,
    "ANT_COLONY": choose_ant_colony,
    "PARTICLE_SWARM": choose_particle_swarm,
    "KNN": choose_knn,
    "DECISION_TREE": choose_decision_tree,
    "RANDOM_FOREST": choose_random_forest,
    "GRADIENT_BOOST": choose_gradient_boost,
    "LSTM": choose_lstm,
    "TRANSFORMER": choose_transformer,
    "ENSEMBLE": choose_ensemble_enhanced,
    "SAFE_RISK": choose_safe_risk,
    "CYCLE_ANALYSIS": choose_cycle_analysis,
    "TREND_ANALYSIS": choose_trend_analysis,
}



def choose_rooms_multi(mode: str, n: int = 1) -> Tuple[List[int], str]:
    """Chọn n phòng — AI + lọc risk thấp (giảm thua)."""
    global _key_type
    n = max(1, min(4, int(n or 1)))
    mode = (mode or "ENSEMBLE").upper()
    if not is_ai_available(mode, _key_type):
        mode = "RANDOM"
    try:
        scores = _vth_unified_scores(noise=0.02)
    except Exception:
        scores = {r: random.random() for r in ROOM_ORDER}
    # tăng trọng risk thấp
    try:
        for row in compute_vth_room_risk() or []:
            rid = int(row.get("id") or 0)
            if rid in scores:
                scores[rid] += 0.40 * (1.0 - float(row.get("risk_pct", 50) or 50) / 100.0)
    except Exception:
        pass
    try:
        if mode != "SAFE_RISK":
            primary, _ = choose_room_tn(mode)
            if primary in scores:
                scores[primary] += 0.25
    except Exception:
        pass
    ranked = sorted(scores.keys(), key=lambda r: scores[r], reverse=True)
    # lọc conservative
    filtered = _vth_conservative_pick(ranked, n)
    if not filtered:
        return [], mode
    return filtered, mode


def choose_room_tn(mode: str) -> Tuple[int, str]:
    global _key_type
    mode = mode.upper()
    if not is_ai_available(mode, _key_type):
        safe_console_print(f"[yellow]⚠️ AI {mode} không khả dụng với key {_key_type}. Chuyển sang RANDOM.[/yellow]")
        mode = "RANDOM"
    func = ENHANCED_LOGIC_MAP.get(mode, choose_random)
    chosen_room = func()
    return chosen_room, mode

def update_ai_performance(algo_name: str, is_win: bool):
    if is_win:
        AI_PERFORMANCE[algo_name]["wins"] += 1
    else:
        AI_PERFORMANCE[algo_name]["losses"] += 1
    AI_PERFORMANCE[algo_name]["total"] += 1
    try:
        with open('ai_performance.json', 'w', encoding='utf-8') as f:
            json.dump(dict(AI_PERFORMANCE), f, indent=2)
    except:
        pass

def get_best_ai() -> str:
    best_ai = "RANDOM"
    best_rate = 0
    for ai_name, stats in AI_PERFORMANCE.items():
        if stats["total"] >= 5:
            rate = stats["wins"] / stats["total"]
            if rate > best_rate:
                best_rate = rate
                best_ai = ai_name
    return best_ai

def calculate_smart_bet(base_bet: float, multiplier: float, lose_streak: int, current_balance: float, max_bet_percent: float = 0.2) -> float:
    bet = base_bet * (multiplier ** lose_streak)
    max_allowed = current_balance * max_bet_percent
    if bet > max_allowed:
        safe_console_print(f"[yellow]⚠️ Cược {bet:.2f} vượt quá {max_bet_percent*100}% số dư. Reset về {base_bet:.2f}.[/yellow]")
        bet = base_bet
    if lose_streak > 5:
        bet = min(bet, current_balance * 0.05)
    return round(bet, 2)
    # ================== WEBSOCKET ==================

def safe_send_enter_game(ws):
    if not ws:
        return
    try:
        uid = USER_ID
        secret = SECRET_KEY
        # thử nhiều dạng payload (API đôi khi cần string)
        payloads = [
            {
                "msg_type": "handle_enter_game",
                "asset_type": "BUILD",
                "user_id": uid,
                "user_secret_key": secret,
            },
            {
                "msg_type": "handle_enter_game",
                "asset_type": "BUILD",
                "user_id": str(uid) if uid is not None else "",
                "user_secret_key": str(secret) if secret is not None else "",
            },
            {
                "msg_type": "handle_enter_game",
                "assetType": "BUILD",
                "userId": uid,
                "userSecretKey": secret,
            },
        ]
        for payload in payloads:
            try:
                ws.send(json.dumps(payload, ensure_ascii=False))
            except Exception:
                continue
    except Exception:
        pass

def _extract_issue_id(d: Dict[str, Any]) -> Optional[int]:
    if not isinstance(d, dict):
        return None
    possible = []
    for key in ("issue_id", "issueId", "issue", "id"):
        v = d.get(key)
        if v is not None:
            possible.append(v)
    if isinstance(d.get("data"), dict):
        for key in ("issue_id", "issueId", "issue", "id"):
            v = d["data"].get(key)
            if v is not None:
                possible.append(v)
    for p in possible:
        try:
            return int(p)
        except Exception:
            try:
                return int(str(p))
            except Exception:
                continue
    return None

def on_open(ws):
    global _ws_status, last_msg_ts
    _ws["ws"] = ws
    _ws_status = "✅ Đã kết nối"
    last_msg_ts = time.time()
    safe_send_enter_game(ws)
    # gửi lại enter sau 1.5s (tránh miss gói đầu)
    def _reenter():
        time.sleep(1.5)
        if not stop_flag:
            safe_send_enter_game(ws)
    threading.Thread(target=_reenter, daemon=True).start()


def _vth_begin_new_issue(new_issue) -> bool:
    """Chuyển sang kỳ mới: mở khóa, xóa target, cho phép cược lại. True nếu kỳ đổi."""
    global issue_id, killed_room, prediction_locked, predicted_room, predicted_rooms, ui_state, round_warning
    global analysis_start_ts, issue_start_ts, issue_end_ts, round_index, count_down
    if new_issue is None:
        return False
    try:
        ni = int(new_issue)
    except Exception:
        ni = new_issue
    try:
        cur = int(issue_id) if issue_id is not None else None
    except Exception:
        cur = issue_id
    if cur is not None and ni == cur:
        return False
    # Chỉ tiến kỳ (tránh gói result kỳ cũ kéo ngược)
    try:
        if cur is not None and int(ni) < int(cur):
            return False
    except Exception:
        pass
    issue_id = ni
    killed_room = None
    prediction_locked = False
    predicted_room = None
    predicted_rooms = []
    round_warning = ""
    ui_state = "ANALYZING"
    analysis_start_ts = time.time()
    issue_start_ts = time.time()
    issue_end_ts = issue_start_ts + 60.0
    round_index += 1
    try:
        if len(bet_sent_for_issue) > 40:
            bet_sent_for_issue.clear()
        if len(bet_room_sent) > 80:
            bet_room_sent.clear()
        if len(skipped_for_issue) > 40:
            skipped_for_issue.clear()
    except Exception:
        pass
    return True


def on_message(ws, message):
    global issue_id, count_down, killed_room, round_index, ui_state, analysis_start_ts, issue_start_ts, issue_end_ts
    global prediction_locked, predicted_room, last_killed_room, last_killed_room_delayed, last_msg_ts, current_bet, last_finished_issue, last_finished_label
    global win_streak, lose_streak, max_win_streak, max_lose_streak, cumulative_profit, _skip_rounds_remaining, stop_flag
    
    last_msg_ts = time.time()
    try:
        if isinstance(message, bytes):
            try:
                message = message.decode("utf-8", errors="replace")
            except Exception:
                message = str(message)
        data = None
        try:
            data = json.loads(message)
        except Exception:
            try:
                data = json.loads(message.replace("'", '"'))
            except Exception:
                return
        if isinstance(data, dict) and isinstance(data.get("data"), str):
            try:
                inner = json.loads(data.get("data"))
                merged = dict(data)
                merged.update(inner)
                data = merged
            except Exception:
                pass
        msg_type = data.get("msg_type") or data.get("type") or ""
        msg_type = str(msg_type)
        new_issue = _extract_issue_id(data)
        # Nhảy kỳ từ mọi gói có issue_id mới (không chỉ issue_stat)
        if new_issue is not None:
            try:
                _vth_begin_new_issue(new_issue)
            except Exception:
                if issue_id is None:
                    issue_id = new_issue
        if msg_type == "notify_enter_game":
            info = data.get("info", {})
            if isinstance(info, dict):
                if info.get("start_time"):
                    st = float(info.get("start_time"))
                    if st > time.time() * 500: st /= 1000.0
                    issue_start_ts = st
                if info.get("end_time"):
                    et = float(info.get("end_time"))
                    if et > time.time() * 500: et /= 1000.0
                    issue_end_ts = et
                # issue trong info
                ei = _extract_issue_id(info) or _extract_issue_id(data)
                if ei is not None:
                    issue_id = ei
            if data.get("last_killed_room_id"):
                try:
                    last_killed_room = int(data["last_killed_room_id"])
                except Exception:
                    pass
            room_stat = data.get("room_stat", [])
            if not room_stat and isinstance(data.get("data"), dict):
                room_stat = data["data"].get("room_stat", []) or data["data"].get("rooms", [])
            if isinstance(room_stat, list):
                for rm in room_stat:
                    _process_room_update(rm)
            if ui_state in ("WAITING", "IDLE", "CHỜ") and (issue_id or any(room_state[r].get("players", 0) > 0 for r in ROOM_ORDER)):
                ui_state = "ANALYZING"
                analysis_start_ts = time.time()
        if msg_type == "notify_issue_stat" or "issue_stat" in msg_type:
            rooms = data.get("rooms") or []
            if not rooms and isinstance(data.get("data"), dict):
                rooms = data["data"].get("rooms", [])
            for rm in (rooms or []):
                _process_room_update(rm)
                try:
                    rid = int(rm.get("room_id") or rm.get("roomId") or rm.get("id"))
                except Exception:
                    continue
                players = int(rm.get("user_cnt") or rm.get("userCount") or 0) or 0
                bet = int(rm.get("total_bet_amount") or rm.get("totalBet") or rm.get("bet") or 0) or 0
                room_state[rid] = {"players": players, "bet": bet}
                room_stats[rid]["last_players"] = players
                room_stats[rid]["last_bet"] = bet
            if new_issue is not None:
                changed = _vth_begin_new_issue(new_issue)
                if data.get("start_time"):
                    try:
                        st = float(data.get("start_time"))
                        if st > time.time() * 500:
                            st /= 1000.0
                        issue_start_ts = st
                        issue_end_ts = st + 60.0
                    except Exception:
                        pass
                # Nếu cùng kỳ nhưng vẫn đang RESULT → về ANALYZING để cược tiếp
                if not changed and ui_state == "RESULT" and issue_id is not None:
                    try:
                        already = int(issue_id) in {int(x) for x in bet_sent_for_issue}
                    except Exception:
                        already = issue_id in bet_sent_for_issue
                    if not already:
                        prediction_locked = False
                        predicted_room = None
                        ui_state = "ANALYZING"
                        analysis_start_ts = time.time()
        elif msg_type == "notify_count_down" or "count_down" in msg_type:
            count_down = data.get("count_down") or data.get("countDown") or data.get("count") or count_down
            try:
                count_val = int(count_down)
            except Exception:
                count_val = None
            # Countdown: tôn trọng setting; chỉ ép khi còn <=8s
            if count_val is not None and count_val <= 8:
                if str(ui_state) == "SKIP":
                    pass
                else:
                    if ui_state == "RESULT":
                        ui_state = "ANALYZING"
                        if not prediction_locked:
                            analysis_start_ts = time.time()
                    lock_prediction_if_needed(force=False)
        elif msg_type == "notify_result" or "result" in msg_type:
            # --- lấy phòng sát thủ ---
            kr = None
            possible_keys = [
                "killed_room", "killed_room_id", "killedRoom", "killedRoomId",
                "kill_room", "room_id", "roomId", "result_room", "win_room",
            ]
            for key in possible_keys:
                if data.get(key) is not None:
                    kr = data.get(key)
                    break
            if kr is None and isinstance(data.get("data"), dict):
                for key in possible_keys:
                    if data["data"].get(key) is not None:
                        kr = data["data"].get(key)
                        break
            if kr is None and isinstance(data.get("info"), dict):
                for key in possible_keys:
                    if data["info"].get(key) is not None:
                        kr = data["info"].get(key)
                        break

            # Kỳ của kết quả (ưu tiên issue trong message, không dùng issue hiện tại đã sang ván mới)
            result_issue = None
            try:
                result_issue = _extract_issue_id(data)
            except Exception:
                result_issue = None
            if result_issue is None:
                result_issue = issue_id

            def _same_issue(a, b) -> bool:
                try:
                    return int(a) == int(b)
                except Exception:
                    return str(a) == str(b)

            def _is_pending(res) -> bool:
                s = str(res or "").strip().lower()
                return s in ("đang", "dang", "pending", "wait", "chờ", "cho", "")

            if kr is not None:
                try:
                    krid = int(kr)
                except Exception:
                    krid = kr
                killed_room = krid
                game_kill_log.append(krid)
                update_killer_history(krid)
                last_killed_room = krid
                try:
                    last_finished_issue = result_issue if result_issue is not None else issue_id
                    last_finished_label = ROOM_NAMES.get(krid, f"Phòng {krid}")
                except Exception:
                    pass
                last_killed_room_delayed = krid
                for rid in ROOM_ORDER:
                    if rid == krid:
                        room_stats[rid]["kills"] += 1
                        room_stats[rid]["last_kill_round"] = round_index
                    else:
                        room_stats[rid]["survives"] += 1

                balance_before_payout = current_build

                # Tìm lệnh cược còn "Đang" — khớp kỳ kết quả; fallback lệnh pending gần nhất
                pending = [b for b in bet_history if _is_pending(b.get("result"))]
                matched = [b for b in pending if _same_issue(b.get("issue"), result_issue)]
                if not matched and pending:
                    # issue_id đã nhảy kỳ mới → lấy pending mới nhất
                    matched = [pending[-1]]

                # Gán kết quả từng phòng; streak/martingale theo CẢ VÁN (1 lần)
                round_lost = False
                for rec in matched:
                    try:
                        placed_room = int(rec.get("room"))
                        win = placed_room != int(krid)
                        rec["result"] = "Thắng" if win else "Thua"
                        rec["killed_room"] = krid
                        if not win:
                            round_lost = True
                    except Exception:
                        continue
                if matched:
                    if round_lost:
                        lose_streak += 1
                        win_streak = 0
                        if lose_streak > max_lose_streak:
                            max_lose_streak = lose_streak
                        try:
                            if current_bet is not None:
                                current_bet = calculate_smart_bet(
                                    base_bet, multiplier, lose_streak, current_build or 0
                                )
                        except Exception:
                            current_bet = base_bet
                        if pause_after_losses > 0:
                            _skip_rounds_remaining = pause_after_losses
                    else:
                        win_streak += 1
                        lose_streak = 0
                        current_bet = base_bet
                        if win_streak > max_win_streak:
                            max_win_streak = win_streak
                    for rec in matched:
                        rec["win_streak"] = win_streak
                        rec["lose_streak"] = lose_streak
                        try:
                            algo = rec.get("algo") or settings.get("algo", "FREE")
                            key = str(algo)
                            AI_PERFORMANCE[key]["total"] += 1
                            if rec.get("result") == "Thắng":
                                AI_PERFORMANCE[key]["wins"] += 1
                            else:
                                AI_PERFORMANCE[key]["losses"] += 1
                        except Exception:
                            pass
                        threading.Thread(
                            target=_background_update_balance_after_result,
                            args=(rec, balance_before_payout),
                            daemon=True,
                        ).start()
            ui_state = "RESULT"
            try:
                if stop_when_profit_reached and profit_target is not None and isinstance(current_build, (int, float)) and current_build >= profit_target and not stop_flag:
                    safe_console_print(f"[bold green]🎉 MỤC TIÊU LÃI ĐẠT: {current_build} >= {profit_target}. Dừng tool.[/]")
                    stop_flag = True
                    try:
                        wsobj = _ws.get("ws")
                        if wsobj:
                            wsobj.close()
                    except Exception:
                        pass
                if stop_when_loss_reached and stop_loss_target is not None and isinstance(current_build, (int, float)) and current_build <= stop_loss_target and not stop_flag:
                    safe_console_print(f"[bold red]💀 CẮT LỖ: {current_build:,.2f} <= {stop_loss_target:,.2f}. Dừng tool.[/]")
                    stop_flag = True
                    try:
                        wsobj = _ws.get("ws")
                        if wsobj:
                            wsobj.close()
                    except Exception:
                        pass
            except Exception:
                pass
    except Exception:
        pass

def _background_update_balance_after_result(rec: dict, balance_before: Optional[float]):
    global cumulative_profit
    try:
        time.sleep(2.5)
        new_balance, _, _ = fetch_balances_3games(retries=2, timeout=5)
        if rec and isinstance(new_balance, (int, float)):
            if isinstance(balance_before, (int, float)):
                delta = new_balance - balance_before
                rec['delta'] = delta
            else:
                if rec.get('result') == 'Thắng':
                    rec['delta'] = float(rec.get('amount', 0)) * 7
                elif rec.get('result') == 'Thua':
                    rec['delta'] = -float(rec.get('amount', 0))
    except Exception:
        pass

def update_killer_history(killed_room_id):
    if killed_room_id in room_state:
        killer_history.append({'players': room_state[killed_room_id].get('players', 0), 'bet': room_state[killed_room_id].get('bet', 0)})

def _process_room_update(room_data: dict):
    if not isinstance(room_data, dict):
        return
    try:
        rid = int(room_data.get("room_id") or room_data.get("roomId") or room_data.get("id"))
        players = int(room_data.get("user_cnt") or room_data.get("userCount") or 0) or 0
        bet = _parse_number(room_data.get("total_bet_amount") or room_data.get("totalBet") or room_data.get("bet") or 0) or 0
        room_state[rid] = {"players": players, "bet": bet}
        room_stats[rid]["last_players"] = players
        room_stats[rid]["last_bet"] = bet
    except (ValueError, TypeError):
        pass

def on_close(ws, code, reason):
    global _ws_status
    _ws_status = f"⏳ Đã đóng ({code})"

def on_error(ws, err):
    global _ws_status
    _ws_status = f"❌ Lỗi: {str(err)[:30]}"

def start_ws():
    WS_URL = "wss://api.escapemaster.net/escape_master/ws"
    backoff = 1.0
    global _ws_status
    while not stop_flag:
        try:
            _ws_status = "⏳ Đang kết nối..."
            ws_app = websocket.WebSocketApp(WS_URL, on_open=on_open, on_message=on_message, on_close=on_close, on_error=on_error)
            _ws["ws"] = ws_app
            ws_app.run_forever(ping_interval=15, ping_timeout=6)
        except Exception:
            _ws_status = f"❌ Lỗi kết nối"
        t = min(backoff + random.random() * 0.8, 30)
        if not stop_flag:
            time.sleep(t)
            backoff = min(backoff * 1.8, 30)

class BalancePoller(threading.Thread):
    def __init__(self, uid: Optional[int], secret: Optional[str], poll_seconds: int = 2, on_balance=None, on_error=None, on_status=None):
        super().__init__(daemon=True)
        self.uid = uid
        self.secret = secret
        self.poll_seconds = max(1, int(poll_seconds))
        self._running = True
        self._last_balance_local: Optional[float] = None
        self.on_balance = on_balance
        self.on_error = on_error
        self.on_status = on_status

    def stop(self):
        self._running = False

    def run(self):
        if self.on_status:
            self.on_status("Kết nối...")
        while self._running and not stop_flag:
            try:
                build, world, usdt = fetch_balances_3games(params={"userId": str(self.uid)} if self.uid else None, uid=self.uid, secret=self.secret)
                if build is None:
                    raise RuntimeError("Không đọc được balance từ response")
                delta = 0.0 if self._last_balance_local is None else (build - self._last_balance_local)
                first_time = (self._last_balance_local is None)
                if first_time or abs(delta) > 0:
                    self._last_balance_local = build
                    if self.on_balance:
                        self.on_balance(float(build), float(delta), {"ts": human_ts()})
                    if self.on_status:
                        self.on_status("Đang theo dõi")
                else:
                    if self.on_status:
                        self.on_status("Đang theo dõi (không đổi)")
            except Exception as e:
                if self.on_error:
                    self.on_error(str(e))
                if self.on_status:
                    self.on_status("Lỗi kết nối (thử lại...)")
            for _ in range(max(1, int(self.poll_seconds * 5))):
                if not self._running or stop_flag:
                    break
                time.sleep(0.2)
        if self.on_status:
            self.on_status("Đã dừng")

def monitor_loop():
    global last_balance_fetch_ts, last_msg_ts, stop_flag
    while not stop_flag:
        if check_key_expiry_and_stop("monitor VTH"):
            break
        now = time.time()
        if now - last_balance_fetch_ts >= BALANCE_POLL_INTERVAL:
            last_balance_fetch_ts = now
            try:
                fetch_balances_3games(params={"userId": str(USER_ID)} if USER_ID else None)
            except Exception:
                pass
        if now - last_msg_ts > 12:
            try:
                safe_send_enter_game(_ws.get("ws"))
            except Exception:
                pass
        if now - last_msg_ts > 45:
            try:
                wsobj = _ws.get("ws")
                if wsobj:
                    try:
                        wsobj.close()
                    except Exception:
                        pass
            except Exception:
                pass
        try:
            already = False
            if issue_id is not None:
                try:
                    already = (
                        int(issue_id) in {int(x) for x in bet_sent_for_issue}
                        or int(issue_id) in {int(x) for x in skipped_for_issue}
                    )
                except Exception:
                    already = issue_id in bet_sent_for_issue or issue_id in skipped_for_issue
            # Không mở khóa nếu đang SKIP / DANGER (theo setting)
            if prediction_locked and issue_id is not None and not already:
                if str(ui_state) == "SKIP":
                    pass
                elif analysis_start_ts and (time.time() - analysis_start_ts > max(float(analysis_duration or 45), 20) + 15):
                    # chỉ mở nếu kẹt quá lâu thật sự
                    prediction_locked = False
            try:
                cd = int(count_down) if count_down is not None else None
            except Exception:
                cd = None
            ready = False
            # Tôn trọng analysis_duration trong setting
            if analysis_start_ts and (time.time() - analysis_start_ts >= float(analysis_duration or 45)):
                ready = True
            # Countdown gấp mới ép sớm (không phá setting 45s quá sớm)
            if cd is not None and cd <= 8:
                ready = True
            if ready and issue_id is not None and not already and str(ui_state) != "SKIP":
                if ui_state == "RESULT":
                    ui_state = "ANALYZING"
                lock_prediction_if_needed(force=False)
        except Exception:
            pass
        time.sleep(0.6)
        # ================== CDTD (CHẠY ĐUA TỐC ĐỘ) ==================

cdtd_session = requests.Session()
cdtd_headers = {}

NV = {1: 'Bậc thầy tấn công', 2: 'Quyền sắt', 3: 'Thợ lặn sâu', 4: 'Cơn lốc sân cỏ', 5: 'Hiệp sĩ phi nhanh', 6: 'Vua home run'}
NV_ICONS = {1: '🥋', 2: '👊', 3: '🤿', 4: '🌪️', 5: '🏇', 6: '⚾'}

CDTD_ALGORITHMS = {
    "RANDOM": "1. NGẪU NHIÊN",
    "CHAIN_WIN": "2. CHUỖI THẮNG",
    "CHAIN_LOSE": "3. CHUỖI THUA",
    "HOT_TRACK": "4. BẮT SÓNG NÓNG",
    "COLD_TRACK": "5. BẮT SÓNG LẠNH",
    "BALANCE": "6. CÂN BẰNG",
    "PATTERN_3": "7. MẪU 3 LẦN",
    "PATTERN_5": "8. MẪU 5 LẦN",
    "PROBABILITY": "9. XÁC SUẤT",
    "FOLLOW_WIN": "10. THEO NGƯỜI THẮNG",
    "AVOID_WIN": "11. TRÁNH NGƯỜI THẮNG",
    "SMART": "12. THÔNG MINH",
    "CYCLE_6": "13. CHU KỲ 6",
    "CYCLE_12": "14. CHU KỲ 12",
    "TREND_UP": "15. XU HƯỚNG TĂNG",
    "TREND_DOWN": "16. XU HƯỚNG GIẢM",
    "MARKOV": "17. MARKOV",
    "BAYES": "18. BAYES",
    "NEURAL": "19. NƠ-RON",
    "GENETIC": "20. DI TRUYỀN",
    "REINFORCE": "21. TĂNG CƯỜNG",
    "KNN_3": "22. KNN 3",
    "KNN_5": "23. KNN 5",
    "DECISION": "24. CÂY QUYẾT ĐỊNH",
    "FOREST": "25. RỪNG NGẪU NHIÊN",
    "GRADIENT": "26. GRADIENT",
    "ENSEMBLE": "27. TỔNG HỢP",
    "TREND_FOLLOW": "28. THEO XU HƯỚNG",
    "MEAN_REVERT": "29. ĐẢO CHIỀU",
    "MOMENTUM": "30. ĐỘNG LƯỢNG",
    "VOLATILITY": "31. BIẾN ĐỘNG",
    "SEASONAL": "32. CHU KỲ MÙA",
    "CORRELATION": "33. TƯƠNG QUAN",
    "CLUSTER": "34. PHÂN CỤM",
    "ANOMALY": "35. BẤT THƯỜNG",
    "ENTROPY": "36. ENTROPY",
    "FUZZY": "37. MỜ",
    "LSTM": "38. LSTM",
    "TRANSFORMER": "39. TRANSFORMER",
    "ATTENTION": "40. ATTENTION",
    "DEEP_Q": "41. DEEP Q",
    "META": "42. META LEARNING",
    "SAFE_RISK": "43. RỦI RO AN TOÀN (VIP)",
}

# KEY FREE CDTD: chỉ 10 AI
CDTD_FREE_AI_LIST = [
    "RANDOM", "CHAIN_WIN", "CHAIN_LOSE", "HOT_TRACK", "COLD_TRACK",
    "BALANCE", "PATTERN_3", "PROBABILITY", "FOLLOW_WIN", "SMART",
]


def get_available_cdtd_ai_list(key_type: str = "free") -> List[str]:
    """CDTD: FREE = 10 AI, VIP = full (gồm SAFE_RISK)."""
    if key_type == "vip":
        return list(CDTD_ALGORITHMS.keys())
    return list(CDTD_FREE_AI_LIST)


cdtd_settings = {"algo": "ENSEMBLE"}
cdtd_coin = "BUILD"
cdtd_base_bet = 1.0
cdtd_multiplier = 2.0
cdtd_current_bet = 1.0
cdtd_num_athletes = 1  # Số nhân vật đặt cược mỗi ván (1–5)
cdtd_win_streak = 0
cdtd_lose_streak = 0
cdtd_max_win_streak = 0
cdtd_max_lose_streak = 0
cdtd_stats = {'win': 0, 'lose': 0, 'asset_0': 0}
cdtd_bet_history = deque(maxlen=50)
cdtd_stop_flag = False
cdtd_issue_id = None
cdtd_predicted_nv = None       # NV chính (tương thích UI cũ)
cdtd_predicted_nvs = []        # Danh sách NV đã chọn (multi-bet)
cdtd_round_warning = ""       # cảnh báo bỏ ván CDTD
cdtd_ui_state = "WAITING"
cdtd_analysis_start_ts = None
cdtd_analysis_duration = 25.0
cdtd_pause_rounds = 0
cdtd_pause_remaining = 0
cdtd_stop_loss_target = None  # số dư cắt lỗ
cdtd_profit_target = None
cdtd_stop_when_loss = False
cdtd_stop_when_profit = False
cdtd_random_skip_pct = 0.0
cdtd_starting_balance = None

cdtd_bet_rounds_before_skip = 0
cdtd_rounds_placed = 0
cdtd_skip_next = False
cdtd_last_winner = None
cdtd_previous_issue = None
cdtd_bet_placed_this_round = False
cdtd_checked_result = False

def parse_xworld_credentials(link_or_text: str):
    """Parse userId + secretKey từ link xworld / query / text thô."""
    if not link_or_text:
        return None
    text = str(link_or_text).strip()
    uid, skey = None, None
    try:
        parsed = urlparse(text)
        qs = parse_qs(parsed.query)
        for k in ("userId", "userid", "user_id"):
            if qs.get(k):
                uid = qs[k][0]
                break
        for k in ("secretKey", "secretkey", "user_secret_key", "secret_key"):
            if qs.get(k):
                skey = qs[k][0]
                break
        if (not uid or not skey) and parsed.fragment:
            qs2 = parse_qs(parsed.fragment.lstrip("?"))
            if not uid:
                for k in ("userId", "userid", "user_id"):
                    if qs2.get(k):
                        uid = qs2[k][0]
                        break
            if not skey:
                for k in ("secretKey", "secretkey", "user_secret_key", "secret_key"):
                    if qs2.get(k):
                        skey = qs2[k][0]
                        break
    except Exception:
        pass
    if not uid or not skey:
        m_uid = re.search(r"(?:userId|userid|user_id)[=:]\s*([0-9]+)", text, re.I)
        m_key = re.search(r"(?:secretKey|secretkey|user_secret_key|secret_key)[=:]\s*([A-Za-z0-9_\-]+)", text, re.I)
        if m_uid:
            uid = m_uid.group(1)
        if m_key:
            skey = m_key.group(1)
    if uid and skey:
        return str(uid).strip(), str(skey).strip()
    return None


def _save_cdtd_cred(user_id, user_secretkey) -> dict:
    json_data = {"user-id": str(user_id), "user-secret-key": str(user_secretkey)}
    try:
        with open("data-xw-cdtd.txt", "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=4, ensure_ascii=False)
    except Exception:
        pass
    return json_data


def load_data_cdtd(force_new: bool = False):
    """
    Lấy tài khoản CDTD:
      1) USER_ID/SECRET_KEY đã chọn
      2) accounts.json
      3) data-xw-cdtd.txt
      4) Nhập link / tay
    """
    global USER_ID, SECRET_KEY

    if not force_new and USER_ID and SECRET_KEY:
        data = _save_cdtd_cred(USER_ID, SECRET_KEY)
        console.print(f"[green]✅ CDTD dùng tài khoản đã chọn: {USER_ID}[/green]")
        return data

    if not force_new:
        try:
            accounts = load_accounts()
        except Exception:
            accounts = []
        if accounts:
            if len(accounts) == 1:
                uid = accounts[0].get("userId")
                skey = accounts[0].get("secretKey")
                if uid and skey:
                    USER_ID = int(uid) if str(uid).isdigit() else uid
                    SECRET_KEY = str(skey)
                    data = _save_cdtd_cred(USER_ID, SECRET_KEY)
                    console.print(f"[green]✅ CDTD dùng account: {USER_ID}[/green]")
                    return data
            console.print(Rule(f"[bold {TST_COLORS['gold']}]📋 CHỌN TÀI KHOẢN CDTD[/]", style=TST_COLORS["gold"]))
            for i, acc in enumerate(accounts, 1):
                console.print(f"  [{i}] userId={acc.get('userId')}")
            console.print("  [0] Nhập link / ID mới")
            try:
                ci = int(Prompt.ask(">> Chọn", default="1"))
            except Exception:
                ci = 1
            if 1 <= ci <= len(accounts):
                acc = accounts[ci - 1]
                uid, skey = acc.get("userId"), acc.get("secretKey")
                if uid and skey:
                    USER_ID = int(uid) if str(uid).isdigit() else uid
                    SECRET_KEY = str(skey)
                    data = _save_cdtd_cred(USER_ID, SECRET_KEY)
                    console.print(f"[green]✅ Đã chọn CDTD: {USER_ID}[/green]")
                    return data

    if not force_new and os.path.exists("data-xw-cdtd.txt"):
        try:
            with open("data-xw-cdtd.txt", "r", encoding="utf-8") as f:
                data = json.load(f)
            uid = data.get("user-id") or data.get("userId")
            skey = data.get("user-secret-key") or data.get("secretKey")
            if uid and skey:
                USER_ID = int(uid) if str(uid).isdigit() else uid
                SECRET_KEY = str(skey)
                console.print(f"[green]✅ CDTD load file: {USER_ID}[/green]")
                return {"user-id": str(uid), "user-secret-key": str(skey)}
        except Exception:
            pass

    console.print(Rule(f"[bold {TST_COLORS['gold']}]📋 NHẬP THÔNG TIN CDTD[/]", style=TST_COLORS["gold"]))
    console.print("1. Vào xworld.info / xworld.io → đăng nhập → Chạy đua tốc độ")
    console.print("2. Copy link có userId & secretKey")
    console.print("   vd: https://xworld.info/?userId=123&secretKey=abc\n")
    link = Prompt.ask(f'[bold {TST_COLORS["gold"]}]📋 Dán link (Enter = nhập tay)[/]', default="")

    user_id, user_secretkey = None, None
    if link.strip():
        parsed = parse_xworld_credentials(link)
        if parsed:
            user_id, user_secretkey = parsed
        else:
            console.print("[yellow]⚠️ Không parse được link — nhập tay.[/yellow]")

    if not user_id or not user_secretkey:
        user_id = Prompt.ask(f'[bold {TST_COLORS["gold"]}]👤 User ID[/]')
        user_secretkey = Prompt.ask(f'[bold {TST_COLORS["gold"]}]🔑 Secret Key[/]')

    if not user_id or not user_secretkey:
        console.print("[red]❌ Thiếu User ID hoặc Secret Key![/red]")
        return {"user-id": "", "user-secret-key": ""}

    try:
        USER_ID = int(user_id) if str(user_id).isdigit() else user_id
    except Exception:
        USER_ID = user_id
    SECRET_KEY = str(user_secretkey)
    data = _save_cdtd_cred(USER_ID, SECRET_KEY)
    console.print(f"[green]✅ Đã lưu CDTD account: {USER_ID}[/green]")
    return data


def setup_cdtd_headers(data: dict):
    global cdtd_headers, USER_ID, SECRET_KEY
    uid = data.get("user-id") or data.get("userId") or USER_ID or ""
    skey = data.get("user-secret-key") or data.get("secretKey") or SECRET_KEY or ""
    uid = str(uid).strip()
    skey = str(skey).strip()
    if uid:
        try:
            USER_ID = int(uid) if uid.isdigit() else uid
        except Exception:
            USER_ID = uid
    if skey:
        SECRET_KEY = skey
    # Headers chuẩn giống VTH (wallet nhận số dư)
    base = balance_headers_for(uid if str(uid).isdigit() else None, skey or None)
    if uid:
        base["user-id"] = str(uid)
    if skey:
        base["user-secret-key"] = str(skey)
    base["content-type"] = "application/json"
    cdtd_headers = base



def top_100_cdtd():
    try:
        response = cdtd_session.get(
            'https://api.sprintrun.win/sprint/recent_100_issues',
            headers={'accept': '*/*', 'origin': 'https://sprintrun.win', 'referer': 'https://sprintrun.win/', 'user-agent': 'Mozilla/5.0'},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == 0 and 'data' in data:
                win_times = data['data'].get('athlete_2_win_times', {})
                return [1, 2, 3, 4, 5, 6], [win_times.get(str(i), 0) for i in range(1, 7)]
    except Exception as e:
        safe_console_print(f"[yellow]⚠️ Lỗi top_100: {e}[/yellow]")
    return [1, 2, 3, 4, 5, 6], [0, 0, 0, 0, 0, 0]

def top_10_cdtd():
    try:
        response = cdtd_session.get(
            'https://api.sprintrun.win/sprint/recent_10_issues',
            headers=cdtd_headers,
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == 0 and 'data' in data:
                recent = data['data'].get('recent_10', [])
                issues = [i['issue_id'] for i in recent]
                results = [i['result'][0] if i.get('result') else 1 for i in recent]
                return issues, results
    except Exception as e:
        safe_console_print(f"[yellow]⚠️ Lỗi top_10: {e}[/yellow]")
    return [0], [1]

def user_asset_cdtd(retries: int = 3) -> dict:
    """
    Lấy số dư CDTD — dùng cùng headers/API với VTH (wallet.3games.io).
    Không phụ thuộc cdtd_headers lỗi; fallback USER_ID/SECRET_KEY.
    """
    uid = cdtd_headers.get("user-id") if isinstance(cdtd_headers, dict) else None
    secret = cdtd_headers.get("user-secret-key") if isinstance(cdtd_headers, dict) else None
    uid = uid or USER_ID
    secret = secret or SECRET_KEY
    empty = {"USDT": 0.0, "WORLD": 0.0, "BUILD": 0.0}
    if not uid or not secret:
        safe_console_print("[yellow]⚠️ user_asset: thiếu user-id hoặc secret-key[/yellow]")
        return empty

    try:
        uid_int = int(str(uid).strip())
    except Exception:
        safe_console_print(f"[yellow]⚠️ user_asset: user-id không hợp lệ: {uid}[/yellow]")
        return empty

    headers = balance_headers_for(uid_int, str(secret))
    # bổ sung content-type JSON
    headers["content-type"] = "application/json"
    payload = {"user_id": uid_int, "source": "home"}
    last_err = ""

    for attempt in range(1, max(1, retries) + 1):
        try:
            r = cdtd_session.post(
                "https://wallet.3games.io/api/wallet/user_asset",
                headers=headers,
                json=payload,
                timeout=12,
            )
            if r.status_code != 200:
                last_err = f"HTTP {r.status_code}"
                time.sleep(0.4 * attempt)
                continue
            data = r.json() if r.content else {}
            code = data.get("code")
            if code == 0 and isinstance(data.get("data"), dict):
                ua = data["data"].get("user_asset") or {}
                out = {
                    "USDT": float(_parse_number(ua.get("USDT")) or 0),
                    "WORLD": float(_parse_number(ua.get("WORLD")) or 0),
                    "BUILD": float(_parse_number(ua.get("BUILD")) or 0),
                }
                return out
            # code != 0
            last_err = str(data.get("msg") or data.get("message") or f"code={code}")
            # thử lại 1 lần với session sạch
            if attempt == 1:
                try:
                    b, w, u = fetch_balances_3games(retries=1, timeout=8, uid=uid_int, secret=str(secret))
                    return {
                        "USDT": float(u or 0),
                        "WORLD": float(w or 0),
                        "BUILD": float(b or 0),
                    }
                except Exception as e2:
                    last_err = f"{last_err} | fallback: {e2}"
            time.sleep(0.4 * attempt)
        except Exception as e:
            last_err = str(e)
            time.sleep(0.4 * attempt)

    # Fallback cuối: fetch_balances_3games
    try:
        b, w, u = fetch_balances_3games(retries=2, timeout=10, uid=uid_int, secret=str(secret))
        if b is not None or w is not None or u is not None:
            return {
                "USDT": float(u or 0),
                "WORLD": float(w or 0),
                "BUILD": float(b or 0),
            }
    except Exception as e:
        last_err = f"{last_err} | {e}"

    safe_console_print(f"[yellow]⚠️ Không lấy được số dư CDTD: {last_err}[/yellow]")
    safe_console_print(f"[dim]user-id={uid_int} · secret={'có' if secret else 'không'}[/dim]")
    return empty

def bet_cdtd(issue_id, nv_id, amount):
    try:
        human_bet_delay(f"NV{nv_id} · kỳ {issue_id}")
        response = cdtd_session.post(
            'https://api.sprintrun.win/sprint/bet',
            headers=cdtd_headers,
            json={
                'issue_id': int(issue_id),
                'bet_group': 'not_winner',
                'asset_type': cdtd_coin,
                'athlete_id': nv_id,
                'bet_amount': float(amount)
            },
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == 0:
                return True, "ok"
            else:
                return False, data.get('msg', 'Unknown error')
        else:
            return False, f"HTTP {response.status_code}"
    except Exception as e:
        return False, str(e)

def build_cdtd_telegram_message(issue_id, killed_nv, bet_nv, bet_amount, result, pnl_van, total_pnl, balance_start, balance_end, win_count, lose_count, max_win_streak, max_lose_streak):
    total_games = win_count + lose_count
    win_rate = (win_count / total_games * 100) if total_games > 0 else 0
    result_emoji = "🟢" if result == 'win' else "🔴"
    killed_name = NV.get(killed_nv, f"NV{killed_nv}")
    bet_name = NV.get(bet_nv, f"NV{bet_nv}")
    bal_start = f"{balance_start:,.2f}" if balance_start >= 1000 else f"{balance_start:.4f}"
    bal_end = f"{balance_end:,.2f}" if balance_end >= 1000 else f"{balance_end:.4f}"
    message = f"""{result_emoji} <b>Ván #{issue_id}</b> | {NV_ICONS.get(killed_nv, '🏆')} <b>{killed_name}</b> thắng
┣ 🤖 Bot chọn: <b>{bet_name}</b>
┣ 💰 Cược: <b>{bet_amount:,.0f} {cdtd_coin}</b>
┣ 💵 Lãi: <b>{pnl_van:+,.4f}</b> | Tổng: <b>{total_pnl:+,.2f}</b>
┣ 📊 {win_count}W/{lose_count}L ({win_rate:.0f}%) | {bal_start} → {bal_end}
┗ 🔥 Max: 🟢{max_win_streak} 🔴{max_lose_streak} | 🕐 {datetime.now(tz).strftime('%H:%M %d/%m')}"""
    return message

# ================== CDTD AI FUNCTIONS ==================

def _cdtd_recent(data_top10) -> List[int]:
    """Chuỗi NV thắng gần đây (int 1–6)."""
    out = []
    if data_top10 and len(data_top10) > 1 and data_top10[1]:
        for x in data_top10[1]:
            try:
                n = int(x)
                if 1 <= n <= 6:
                    out.append(n)
            except Exception:
                continue
    return out


def _cdtd_wins100(data_top100) -> List[int]:
    wins = [0] * 6
    if data_top100 and len(data_top100) > 1 and data_top100[1]:
        try:
            raw = list(data_top100[1])[:6]
            for i, w in enumerate(raw):
                wins[i] = int(w or 0)
        except Exception:
            pass
    return wins


def _cdtd_softmax(scores: Dict[int, float], temperature: float = 1.0) -> Dict[int, float]:
    if not scores:
        return {i: 1 / 6 for i in range(1, 7)}
    t = max(0.05, float(temperature))
    m = max(scores.values())
    exps = {k: math.exp((v - m) / t) for k, v in scores.items()}
    s = sum(exps.values()) or 1.0
    return {k: v / s for k, v in exps.items()}


def _cdtd_weighted_pick(scores: Dict[int, float], temperature: float = 0.85) -> int:
    probs = _cdtd_softmax(scores, temperature)
    keys = list(probs.keys())
    weights = [max(1e-9, probs[k]) for k in keys]
    return int(random.choices(keys, weights=weights, k=1)[0])


def _cdtd_transition_matrix(recent: List[int]) -> Dict[int, Dict[int, float]]:
    """P(next|current) với Laplace smoothing."""
    trans = {i: Counter() for i in range(1, 7)}
    for a, b in zip(recent, recent[1:]):
        trans[a][b] += 1
    probs = {}
    for i in range(1, 7):
        total = sum(trans[i].values()) + 6 * 0.5
        probs[i] = {j: (trans[i].get(j, 0) + 0.5) / total for j in range(1, 7)}
    return probs


def _cdtd_ewma_form(recent: List[int], alpha: float = 0.35) -> Dict[int, float]:
    """Form gần đây — trọng số giảm dần theo thời gian."""
    form = {i: 0.0 for i in range(1, 7)}
    if not recent:
        return form
    w = 1.0
    total_w = 0.0
    for nv in reversed(recent):
        form[nv] += w
        total_w += w
        w *= (1.0 - alpha)
    if total_w > 0:
        for i in range(1, 7):
            form[i] /= total_w
    return form


def _cdtd_base_scores(data_top10, data_top100) -> Dict[int, float]:
    """Điểm nền kết hợp win100 + form EWMA + anti-streak."""
    wins = _cdtd_wins100(data_top100)
    total = sum(wins) or 1
    recent = _cdtd_recent(data_top10)
    form = _cdtd_ewma_form(recent)
    scores = {}
    for i in range(1, 7):
        long = wins[i - 1] / total
        short = form.get(i, 0.0)
        scores[i] = 0.38 * long + 0.42 * short + 0.20 * (1.0 - short)  # mean-revert nhẹ
    return scores


def cdtd_execute_ai(mode: str, data_top10, data_top100) -> int:
    """
    CDTD AI v2 — logic đầy đủ cho 42 engine.
    Dùng top10 (form ngắn) + top100 (form dài) + Markov / Bayes / ensemble có trọng số.
    """
    global _key_type
    mode = (mode or "RANDOM").upper()
    allowed = get_available_cdtd_ai_list(_key_type)
    if mode not in allowed:
        mode = "RANDOM"

    candidates = list(range(1, 7))
    recent = _cdtd_recent(data_top10)
    wins = _cdtd_wins100(data_top100)
    total100 = sum(wins) or 1
    base = _cdtd_base_scores(data_top10, data_top100)

    def pick_max(sc: Dict[int, float]) -> int:
        if not sc:
            return random.choice(candidates)
        best = max(sc.values())
        tops = [k for k, v in sc.items() if abs(v - best) < 1e-9]
        return random.choice(tops)

    def pick_min(sc: Dict[int, float]) -> int:
        if not sc:
            return random.choice(candidates)
        worst = min(sc.values())
        lows = [k for k, v in sc.items() if abs(v - worst) < 1e-9]
        return random.choice(lows)

    # ---------- core modes ----------
    if mode == "RANDOM":
        return random.choice(candidates)

    if mode == "CHAIN_WIN":
        mx = max(wins)
        return random.choice([i + 1 for i, w in enumerate(wins) if w == mx])

    if mode == "CHAIN_LOSE":
        mn = min(wins)
        return random.choice([i + 1 for i, w in enumerate(wins) if w == mn])

    if mode == "HOT_TRACK":
        window = recent[-5:] if len(recent) >= 5 else recent
        if not window:
            return pick_max(base)
        c = Counter(window)
        mx = max(c.values())
        return random.choice([k for k, v in c.items() if v == mx])

    if mode == "COLD_TRACK":
        window = recent[-5:] if len(recent) >= 5 else recent
        c = Counter(window) if window else Counter()
        # số chưa xuất hiện = lạnh nhất
        cold_scores = {i: -c.get(i, 0) for i in candidates}
        return pick_max(cold_scores)

    if mode == "BALANCE":
        avg = total100 / 6.0
        balanced = [i + 1 for i, w in enumerate(wins) if abs(w - avg) <= max(1.0, avg * 0.15)]
        return random.choice(balanced) if balanced else pick_max(base)

    if mode == "PATTERN_3":
        if len(recent) >= 3 and recent[-3] == recent[-1]:
            return recent[-2]
        return pick_max(base)

    if mode == "PATTERN_5":
        if len(recent) >= 5:
            for i in range(len(recent) - 2, 0, -1):
                if recent[i - 1] == recent[i + 1]:
                    return recent[i]
        return pick_max(base)

    if mode == "PROBABILITY":
        weights = [max(0.01, w / total100) for w in wins]
        return int(random.choices(candidates, weights=weights, k=1)[0])

    if mode == "FOLLOW_WIN":
        return recent[-1] if recent else random.choice(candidates)

    if mode == "AVOID_WIN":
        if recent:
            filt = [c for c in candidates if c != recent[-1]]
            return random.choice(filt) if filt else random.choice(candidates)
        return random.choice(candidates)

    if mode == "SMART":
        sc = dict(base)
        # bonus risk thấp (form tốt + không streak)
        for i in candidates:
            sc[i] += 0.08 * (wins[i - 1] / total100)
        if recent:
            sc[recent[-1]] -= 0.12
        return _cdtd_weighted_pick(sc, 0.7)

    if mode == "CYCLE_6":
        if len(recent) >= 6:
            # dự đoán theo chu kỳ 6: lặp pattern gần nhất
            return recent[-6]
        if recent:
            return candidates[(recent[-1]) % 6]
        return random.choice(candidates)

    if mode == "CYCLE_12":
        if len(recent) >= 12:
            return recent[-12]
        return cdtd_execute_ai("CYCLE_6", data_top10, data_top100)

    if mode == "TREND_UP":
        # NV đang tăng tần suất nửa sau vs nửa trước
        if len(recent) < 6:
            return pick_max(base)
        mid = len(recent) // 2
        c1, c2 = Counter(recent[:mid]), Counter(recent[mid:])
        sc = {i: c2.get(i, 0) - c1.get(i, 0) + 0.1 * (wins[i - 1] / total100) for i in candidates}
        return pick_max(sc)

    if mode == "TREND_DOWN":
        if len(recent) < 6:
            return pick_min(base)
        mid = len(recent) // 2
        c1, c2 = Counter(recent[:mid]), Counter(recent[mid:])
        sc = {i: c1.get(i, 0) - c2.get(i, 0) for i in candidates}
        return pick_max(sc)

    if mode == "MARKOV":
        if len(recent) < 3:
            return pick_max(base)
        tm = _cdtd_transition_matrix(recent)
        last = recent[-1]
        return pick_max(tm.get(last, {i: 1 / 6 for i in candidates}))

    if mode == "BAYES":
        # posterior ∝ prior(uniform) * likelihood(form)
        prior = 1 / 6
        like = {i: (wins[i - 1] + 1) / (total100 + 6) for i in candidates}
        if recent:
            form = _cdtd_ewma_form(recent)
            for i in candidates:
                like[i] *= 0.5 + form.get(i, 0)
        post = {i: prior * like[i] for i in candidates}
        s = sum(post.values()) or 1
        post = {i: v / s for i, v in post.items()}
        return _cdtd_weighted_pick(post, 0.6)

    if mode == "NEURAL":
        # MLP giả lập 1 hidden layer trên feature [long, short, last_onehot, gap]
        form = _cdtd_ewma_form(recent)
        last = recent[-1] if recent else 0
        sc = {}
        for i in candidates:
            x1 = wins[i - 1] / total100
            x2 = form.get(i, 0.0)
            x3 = 1.0 if i == last else 0.0
            gap = 0
            if recent:
                try:
                    gap = (len(recent) - 1 - recent[::-1].index(i)) / max(1, len(recent))
                except ValueError:
                    gap = 1.0
            h = 0.55 * x1 + 0.70 * x2 - 0.35 * x3 + 0.25 * gap
            sc[i] = 1 / (1 + math.exp(-3.0 * (h - 0.35)))
        return _cdtd_weighted_pick(sc, 0.65)

    if mode == "GENETIC":
        # fitness = survival proxy = win rate + diversity bonus
        sc = {i: (wins[i - 1] + 1) / (total100 + 6) for i in candidates}
        if recent:
            c = Counter(recent[-8:])
            for i in candidates:
                sc[i] += 0.05 * (1.0 - c.get(i, 0) / 8.0)
        return pick_max(sc)

    if mode == "REINFORCE":
        # reward theo lịch sử cược session (nếu có) + form
        sc = dict(base)
        try:
            for b in list(cdtd_bet_history)[-12:]:
                nv = b.get("chosen")
                res = b.get("result")
                if nv in sc and res == "win":
                    sc[nv] += 0.15
                elif nv in sc and res == "lose":
                    sc[nv] -= 0.10
        except Exception:
            pass
        return pick_max(sc)

    if mode in ("KNN_3", "KNN_5"):
        k = 3 if mode == "KNN_3" else 5
        window = recent[-k:] if recent else []
        if not window:
            return random.choice(candidates)
        c = Counter(window)
        # KNN cold trong cửa sổ
        return pick_min({i: float(c.get(i, 0)) for i in candidates}) if mode == "KNN_3" else pick_max({i: float(c.get(i, 0)) for i in candidates})

    if mode == "DECISION":
        if not recent:
            return pick_max(base)
        last = recent[-1]
        # rule: nếu last hot trong top100 → tránh; ngược lại follow form
        if wins[last - 1] >= max(wins) * 0.9:
            filt = [i for i in candidates if i != last]
            sc = {i: base[i] for i in filt}
            return pick_max(sc)
        return pick_max(base)

    if mode == "FOREST":
        votes = Counter()
        for m in ("HOT_TRACK", "COLD_TRACK", "SMART", "MARKOV", "BAYES", "MEAN_REVERT"):
            try:
                votes[cdtd_execute_ai(m, data_top10, data_top100)] += 1
            except Exception:
                continue
        return votes.most_common(1)[0][0] if votes else pick_max(base)

    if mode == "GRADIENT":
        sc = dict(base)
        # residual boost: NV under-performing recent vs long
        form = _cdtd_ewma_form(recent)
        for i in candidates:
            residual = (wins[i - 1] / total100) - form.get(i, 0)
            sc[i] += 0.2 * residual  # mean reversion nhẹ
        return pick_max(sc)

    if mode == "TREND_FOLLOW":
        return cdtd_execute_ai("TREND_UP", data_top10, data_top100)

    if mode == "MEAN_REVERT":
        # chọn NV lạnh so với kỳ vọng dài hạn
        form = _cdtd_ewma_form(recent)
        sc = {i: (wins[i - 1] / total100) - form.get(i, 0) for i in candidates}
        return pick_max(sc)

    if mode == "MOMENTUM":
        if len(recent) < 4:
            return pick_max(base)
        sc = Counter(recent[-4:])
        return pick_max({i: float(sc.get(i, 0)) for i in candidates})

    if mode == "VOLATILITY":
        # NV có tần suất ổn định (ít biến động xuất hiện)
        if len(recent) < 8:
            return pick_max(base)
        mid = len(recent) // 2
        c1, c2 = Counter(recent[:mid]), Counter(recent[mid:])
        sc = {i: -abs(c1.get(i, 0) - c2.get(i, 0)) + 0.5 * (wins[i - 1] / total100) for i in candidates}
        return pick_max(sc)

    if mode == "SEASONAL":
        # theo vị trí trong chu kỳ 6
        if not recent:
            return random.choice(candidates)
        phase = len(recent) % 6
        # ưu tiên NV từng thắng ở cùng phase
        hits = [recent[i] for i in range(phase, len(recent), 6)]
        if hits:
            return Counter(hits).most_common(1)[0][0]
        return pick_max(base)

    if mode == "CORRELATION":
        # NV hay đi sau last
        if len(recent) < 3:
            return pick_max(base)
        tm = _cdtd_transition_matrix(recent)
        return pick_max(tm.get(recent[-1], base))

    if mode == "CLUSTER":
        # cụm hot vs cold — chọn trong cụm đang "đến lượt"
        sorted_nv = sorted(candidates, key=lambda i: wins[i - 1], reverse=True)
        hot, cold = sorted_nv[:3], sorted_nv[3:]
        # nếu 2 ván gần thuộc hot → nghiêng cold
        if len(recent) >= 2 and recent[-1] in hot and recent[-2] in hot:
            return random.choice(cold)
        return random.choice(hot)

    if mode == "ANOMALY":
        # NV lệch mạnh so với trung bình (bất thường)
        avg = total100 / 6.0
        sc = {i: abs(wins[i - 1] - avg) for i in candidates}
        # đánh vào phía đang "bất thường thấp" (sắp bắt kịp)
        low = [i for i in candidates if wins[i - 1] < avg]
        if low:
            return random.choice(low)
        return pick_min({i: wins[i - 1] for i in candidates})

    if mode == "ENTROPY":
        # phân phối gần đều → random; lệch → theo probability
        probs = [w / total100 for w in wins]
        ent = -sum(p * math.log(p + 1e-12) for p in probs)
        max_ent = math.log(6)
        if ent > 0.9 * max_ent:
            return random.choice(candidates)
        return cdtd_execute_ai("PROBABILITY", data_top10, data_top100)

    if mode == "FUZZY":
        form = _cdtd_ewma_form(recent)
        sc = {}
        for i in candidates:
            hot = min(1.0, form.get(i, 0) * 3)
            long = min(1.0, wins[i - 1] / max(1, max(wins)))
            # fuzzy rules
            sc[i] = 0.6 * max(hot, long) + 0.4 * min(hot + 0.2, 1.0)
            if recent and i == recent[-1]:
                sc[i] *= 0.75
        return pick_max(sc)

    if mode == "LSTM":
        # pattern sequence đơn giản: nếu A-B-A → đoán B
        if len(recent) >= 3 and recent[-3] == recent[-1]:
            return recent[-2]
        if len(recent) >= 5 and recent[-5] == recent[-2] and recent[-4] == recent[-1]:
            return recent[-3]
        return cdtd_execute_ai("MARKOV", data_top10, data_top100)

    if mode in ("TRANSFORMER", "ATTENTION"):
        # attention trên lịch sử: trọng số theo khoảng cách
        if not recent:
            return pick_max(base)
        attn = {i: 0.0 for i in candidates}
        n = len(recent)
        for idx, nv in enumerate(recent):
            w = math.exp(-0.15 * (n - 1 - idx))
            attn[nv] += w
        # query = last → value = transition
        tm = _cdtd_transition_matrix(recent)
        last = recent[-1]
        sc = {i: 0.55 * tm[last].get(i, 0) + 0.45 * (attn[i] / (sum(attn.values()) or 1)) for i in candidates}
        return pick_max(sc)

    if mode == "DEEP_Q":
        # Q-value: reward nếu chọn NV theo form + phạt streak
        sc = dict(base)
        if recent:
            sc[recent[-1]] -= 0.2
        try:
            for b in list(cdtd_bet_history)[-8:]:
                nv = b.get("chosen")
                if nv in sc:
                    sc[nv] += 0.12 if b.get("result") == "win" else -0.08
        except Exception:
            pass
        return pick_max(sc)

    if mode == "META":
        # meta: chọn strategy phụ theo entropy + streak gần đây
        if len(recent) >= 3 and recent[-1] == recent[-2] == recent[-3]:
            return cdtd_execute_ai("MEAN_REVERT", data_top10, data_top100)
        if len(recent) >= 4 and len(set(recent[-4:])) <= 2:
            return cdtd_execute_ai("COLD_TRACK", data_top10, data_top100)
        return cdtd_execute_ai("SMART", data_top10, data_top100)


    if mode == "SAFE_RISK":
        # VIP: chọn NV rủi ro thấp nhất (risk% + form + tránh vừa thắng)
        sc = {i: 0.0 for i in candidates}
        try:
            rows = compute_cdtd_nv_risk(data_top10, data_top100)
            for row in rows or []:
                nv = int(row.get("id") or 0)
                if nv not in sc:
                    continue
                risk = float(row.get("risk_pct", 50) or 50) / 100.0
                form = float(row.get("form10", 0) or 0)
                sc[nv] += 0.60 * (1.0 - risk) + 0.25 * form
        except Exception:
            for i in candidates:
                sc[i] = float(base.get(i, 0))
        # kết hợp base nhẹ
        for i in candidates:
            sc[i] += 0.20 * float(base.get(i, 0))
        return pick_max(sc)

    if mode == "ENSEMBLE":
        # tổng hợp có trọng số + bonus performance
        voters = [
            ("HOT_TRACK", 1.0),
            ("COLD_TRACK", 0.9),
            ("SMART", 1.2),
            ("MARKOV", 1.1),
            ("BAYES", 1.0),
            ("NEURAL", 1.15),
            ("MEAN_REVERT", 0.95),
            ("MOMENTUM", 0.85),
            ("TREND_UP", 0.9),
            ("ATTENTION", 1.05),
            ("SAFE_RISK", 1.55),
            ("COLD_TRACK", 1.1),
        ]
        votes = defaultdict(float)
        for name, w in voters:
            try:
                # tránh đệ quy ensemble
                if name == "ENSEMBLE":
                    continue
                v = cdtd_execute_ai(name, data_top10, data_top100)
                # adaptive weight từ AI_PERFORMANCE nếu có
                perf = AI_PERFORMANCE.get(f"CDTD_{name}", {})
                total_p = int(perf.get("total", 0) or 0)
                if total_p >= 5:
                    wr = float(perf.get("wins", 0)) / total_p
                    w *= 0.6 + 0.8 * wr
                votes[v] += w
            except Exception:
                continue
        if votes:
            return pick_max(dict(votes))
        return pick_max(base)

    # fallback
    return _cdtd_weighted_pick(base, 0.9)


def cdtd_score_athletes(data_top10, data_top100) -> Dict[int, float]:
    """Điểm xếp hạng NV (multi-bet) — dùng base score + noise nhỏ."""
    scores = _cdtd_base_scores(data_top10, data_top100)
    for i in range(1, 7):
        scores[i] = float(scores.get(i, 0)) + random.uniform(0, 0.03)
    return scores




def cdtd_execute_ai_multi(mode: str, data_top10, data_top100, n: int = 1) -> List[int]:
    """
    Chọn n NV — AI + lọc risk thấp (giảm thua).
    Trả [] nếu toàn bộ quá rủi ro → bỏ ván.
    """
    n = max(1, min(5, int(n or 1)))
    primary = cdtd_execute_ai(mode, data_top10, data_top100)
    try:
        primary = int(primary)
    except (TypeError, ValueError):
        primary = random.randint(1, 6)

    scores = cdtd_score_athletes(data_top10, data_top100)
    # ưu tiên risk thấp trong score
    try:
        for row in compute_cdtd_nv_risk(data_top10, data_top100) or []:
            nv = int(row.get("id") or 0)
            if nv in scores:
                scores[nv] += 0.45 * (1.0 - float(row.get("risk_pct", 50) or 50) / 100.0)
    except Exception:
        pass
    if primary in scores:
        scores[primary] += 0.2
    ranked = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
    filtered = _cdtd_conservative_pick(ranked, n, data_top10, data_top100)
    return filtered


def cdtd_game_loop():
    global cdtd_issue_id, cdtd_previous_issue, cdtd_last_winner, cdtd_predicted_nv, cdtd_predicted_nvs
    global cdtd_ui_state, cdtd_analysis_start_ts, cdtd_round_warning
    global cdtd_current_bet, cdtd_win_streak, cdtd_lose_streak, cdtd_max_win_streak, cdtd_max_lose_streak, cdtd_stop_flag
    global cdtd_stats, cdtd_pause_remaining, cdtd_skip_next, cdtd_rounds_placed, cdtd_bet_placed_this_round, cdtd_checked_result
    
    cdtd_stop_flag = False
    cdtd_issue_id = None
    cdtd_previous_issue = None
    cdtd_last_winner = None
    cdtd_predicted_nv = None
    cdtd_predicted_nvs = []
    cdtd_ui_state = "WAITING"
    cdtd_analysis_start_ts = None
    cdtd_win_streak = 0
    cdtd_lose_streak = 0
    cdtd_max_win_streak = 0
    cdtd_max_lose_streak = 0
    cdtd_rounds_placed = 0
    cdtd_skip_next = False
    cdtd_pause_remaining = 0
    cdtd_bet_placed_this_round = False
    cdtd_checked_result = False
    cdtd_current_bet = cdtd_base_bet
    cdtd_bet_history.clear()
    cdtd_stats = {'win': 0, 'lose': 0, 'asset_0': user_asset_cdtd().get(cdtd_coin, 0)}
    
    with Live(cdtd_generate_layout(), refresh_per_second=4, console=console, screen=True) as live:
        while not cdtd_stop_flag:
            if check_key_expiry_and_stop("CDTD live"):
                break
            try:
                data_top10 = top_10_cdtd()
                if not data_top10 or len(data_top10) < 1:
                    time.sleep(1)
                    continue
                    
                current_issue = data_top10[0][0] if data_top10[0] else None
                
                if current_issue and current_issue != cdtd_previous_issue:
                    has_prediction = (cdtd_predicted_nv is not None) or (cdtd_predicted_nvs)
                    if cdtd_previous_issue is not None and has_prediction and not cdtd_checked_result:
                        try:
                            # Map kỳ → NV thắng (tỷ lệ thật theo từng issue)
                            issue_to_winner = {}
                            try:
                                issues_l = list(data_top10[0]) if data_top10 and data_top10[0] else []
                                results_l = list(data_top10[1]) if data_top10 and len(data_top10) > 1 and data_top10[1] else []
                                for iss, res in zip(issues_l, results_l):
                                    try:
                                        issue_to_winner[int(iss)] = int(res)
                                    except Exception:
                                        pass
                            except Exception:
                                issue_to_winner = {}
                            # fallback: kết quả mới nhất
                            fallback_winner = None
                            try:
                                if data_top10 and len(data_top10) > 1 and data_top10[1]:
                                    fallback_winner = int(data_top10[1][-1])
                            except Exception:
                                fallback_winner = None

                            pending_bets = [b for b in cdtd_bet_history if str(b.get('result', '')).lower() in ('pending', 'đang', 'dang', 'chờ', 'cho')]
                            balance_before = user_asset_cdtd().get(cdtd_coin, 0)
                            result_type = 'win'
                            round_lost = True if pending_bets else False
                            last_w = fallback_winner

                            for b in pending_bets:
                                try:
                                    b_iss = int(b.get('issue'))
                                except Exception:
                                    b_iss = b.get('issue')
                                winner = issue_to_winner.get(b_iss, fallback_winner)
                                if winner is None:
                                    continue
                                last_w = winner
                                b['winner'] = winner
                                try:
                                    chosen = int(b.get('chosen'))
                                except Exception:
                                    chosen = b.get('chosen')
                                # API bet_group=not_winner: THẮNG khi NV chọn KHÔNG về nhất
                                if chosen != winner:
                                    b['result'] = 'win'
                                    round_lost = False
                                else:
                                    b['result'] = 'lose'

                            if last_w is not None:
                                cdtd_last_winner = last_w
                            winner = last_w

                            # Streak / martingale theo VÁN
                            if pending_bets:
                                if round_lost:
                                    cdtd_lose_streak += 1
                                    cdtd_win_streak = 0
                                    cdtd_max_lose_streak = max(cdtd_max_lose_streak, cdtd_lose_streak)
                                    cdtd_current_bet *= cdtd_multiplier
                                    cdtd_stats['lose'] += 1
                                    try:
                                        _algo = str((cdtd_settings or {}).get('algo', 'FREE'))
                                        AI_PERFORMANCE[f'CDTD_{_algo}']['losses'] += 1
                                        AI_PERFORMANCE[f'CDTD_{_algo}']['total'] += 1
                                    except Exception:
                                        pass
                                    result_type = 'lose'
                                    if cdtd_pause_rounds > 0:
                                        cdtd_pause_remaining = cdtd_pause_rounds
                                else:
                                    cdtd_win_streak += 1
                                    cdtd_lose_streak = 0
                                    cdtd_max_win_streak = max(cdtd_max_win_streak, cdtd_win_streak)
                                    cdtd_current_bet = cdtd_base_bet
                                    cdtd_stats['win'] += 1
                                    result_type = 'win'
                                    try:
                                        _algo = str((cdtd_settings or {}).get('algo', 'FREE'))
                                        AI_PERFORMANCE[f'CDTD_{_algo}']['wins'] += 1
                                        AI_PERFORMANCE[f'CDTD_{_algo}']['total'] += 1
                                    except Exception:
                                        pass
                                
                                time.sleep(1)
                                balance_after = user_asset_cdtd().get(cdtd_coin, 0)
                                pnl_van = balance_after - balance_before
                                total_pnl = balance_after - cdtd_stats['asset_0']
                                
                                if TELEGRAM_ENABLED and TELEGRAM_CHAT_ID and pending_bets:
                                    bet_nv = cdtd_predicted_nv
                                    # Tổng tiền cược cả ván (multi)
                                    bet_amount = sum(float(b.get('amount', 0) or 0) for b in pending_bets)
                                    telegram_msg = build_cdtd_telegram_message(
                                        cdtd_previous_issue, winner, bet_nv, bet_amount,
                                        result_type, pnl_van, total_pnl,
                                        balance_before, balance_after,
                                        cdtd_stats['win'], cdtd_stats['lose'],
                                        cdtd_max_win_streak, cdtd_max_lose_streak
                                    )
                                    threading.Thread(target=send_telegram_message, args=(telegram_msg,), daemon=True).start()
                                
                                cdtd_checked_result = True
                                cdtd_ui_state = "RESULT"
                                # Cắt lỗ / chốt lời CDTD
                                try:
                                    bal_now = user_asset_cdtd().get(cdtd_coin, 0)
                                    if cdtd_stop_when_profit and cdtd_profit_target is not None and bal_now >= float(cdtd_profit_target):
                                        safe_console_print(f"[bold green]🎉 CDTD CHỐT LÃI: {bal_now:,.4f} >= {cdtd_profit_target}. Dừng.[/]")
                                        cdtd_stop_flag = True
                                    if cdtd_stop_when_loss and cdtd_stop_loss_target is not None and bal_now <= float(cdtd_stop_loss_target):
                                        safe_console_print(f"[bold red]💀 CDTD CẮT LỖ: {bal_now:,.4f} <= {cdtd_stop_loss_target}. Dừng.[/]")
                                        cdtd_stop_flag = True
                                except Exception:
                                    pass
                                live.update(cdtd_generate_layout())
                                time.sleep(2)
                        except Exception as e:
                            safe_console_print(f"[yellow]⚠️ Lỗi xử lý kết quả: {e}[/yellow]")
                    
                    cdtd_previous_issue = current_issue
                    cdtd_issue_id = current_issue
                    cdtd_predicted_nv = None
                    cdtd_predicted_nvs = []
                    cdtd_bet_placed_this_round = False
                    cdtd_checked_result = False
                    cdtd_analysis_start_ts = time.time()
                    cdtd_ui_state = "ANALYZING"
                    live.update(cdtd_generate_layout())
                
                if cdtd_ui_state == "ANALYZING":
                    elapsed = time.time() - (cdtd_analysis_start_ts or time.time())
                    if elapsed >= cdtd_analysis_duration - 8 and not cdtd_bet_placed_this_round:
                        mode = cdtd_settings.get("algo", "ENSEMBLE")
                        data_top100 = top_100_cdtd()
                        n_pick = max(1, min(5, int(cdtd_num_athletes or 1)))
                        chosen_list = cdtd_execute_ai_multi(mode, data_top10, data_top100, n_pick)
                        if not chosen_list:
                            chosen_list = [random.randint(1, 6)]
                        cdtd_round_warning = ""

                        cdtd_predicted_nvs = list(chosen_list)
                        cdtd_predicted_nv = chosen_list[0] if chosen_list else None
                        cdtd_ui_state = "PREDICTED"
                        live.update(cdtd_generate_layout())
                        
                        should_bet = True
                        if cdtd_pause_remaining > 0:
                            cdtd_pause_remaining -= 1
                            should_bet = False
                        if cdtd_skip_next:
                            cdtd_skip_next = False
                            should_bet = False
                        try:
                            _rsp = float(cdtd_random_skip_pct or 0)
                        except Exception:
                            _rsp = 0.0
                        if should_bet and _rsp > 0 and random.random() * 100.0 < min(40.0, _rsp):
                            should_bet = False
                            safe_console_print(f"[yellow]🎲 CDTD bỏ ngẫu nhiên ván ({_rsp:.0f}%).[/]")
                        
                        if check_key_expiry_and_stop("CDTD trước cược"):
                            break
                        if should_bet and cdtd_issue_id is not None and chosen_list:
                            next_issue = cdtd_issue_id + 1
                            bet_amount = cdtd_current_bet if cdtd_current_bet else cdtd_base_bet
                            asset = user_asset_cdtd()
                            total_need = bet_amount * len(chosen_list)
                            if total_need > asset.get(cdtd_coin, 0):
                                cdtd_current_bet = cdtd_base_bet
                                bet_amount = cdtd_base_bet
                                # Nếu vẫn không đủ cho multi → giảm số NV
                                while len(chosen_list) > 1 and bet_amount * len(chosen_list) > asset.get(cdtd_coin, 0):
                                    chosen_list = chosen_list[:-1]
                                cdtd_predicted_nvs = list(chosen_list)
                                cdtd_predicted_nv = chosen_list[0] if chosen_list else None
                            
                            any_ok = False
                            for nv in chosen_list:
                                success, msg = bet_cdtd(next_issue, nv, bet_amount)
                                if success:
                                    any_ok = True
                                    cdtd_bet_history.append({
                                        'issue': next_issue,
                                        'chosen': nv,
                                        'amount': bet_amount,
                                        'result': 'pending',
                                        'algo': mode,
                                        'multi': len(chosen_list),
                                    })
                                else:
                                    safe_console_print(f"[red]❌ Đặt cược NV {nv} thất bại: {msg}[/red]")
                            
                            if any_ok:
                                cdtd_rounds_placed += 1
                                cdtd_bet_placed_this_round = True
                                if cdtd_bet_rounds_before_skip > 0 and cdtd_rounds_placed >= cdtd_bet_rounds_before_skip:
                                    cdtd_skip_next = True
                                    cdtd_rounds_placed = 0
                        
                        live.update(cdtd_generate_layout())
                    
                    elif elapsed >= cdtd_analysis_duration + 15:
                        cdtd_ui_state = "WAITING"
                        # giữ cdtd_issue_id — header vẫn hiện kỳ đang chờ
                        live.update(cdtd_generate_layout())
                
                live.update(cdtd_generate_layout())
                time.sleep(0.5)
                
            except KeyboardInterrupt:
                cdtd_stop_flag = True
                break
            except Exception as e:
                safe_console_print(f"[yellow]⚠️ Lỗi CDTD: {e}[/yellow]")
                time.sleep(3)
                # ================== GIAO DIỆN CDTD ==================



# Cache risk CDTD ~2.5s để live UI không spam API mỗi frame
_cdtd_risk_cache: Dict[str, Any] = {"ts": 0.0, "rows": None, "top10": None, "top100": None, "by_id": {}}


def _cdtd_risk_bundle(force: bool = False) -> Dict[str, Any]:
    """Lấy top10/top100 + risk từng NV, cache ngắn để cập nhật mỗi ván."""
    global _cdtd_risk_cache
    now = time.time()
    # hết hạn cache hoặc sang issue mới → tính lại risk mỗi ván
    cached_issue = _cdtd_risk_cache.get("issue_id")
    issue_changed = (cdtd_issue_id is not None and cached_issue is not None and cached_issue != cdtd_issue_id)
    if (
        not force
        and not issue_changed
        and _cdtd_risk_cache.get("rows") is not None
        and (now - float(_cdtd_risk_cache.get("ts") or 0)) < 2.5
    ):
        return _cdtd_risk_cache
    try:
        top10 = top_10_cdtd()
    except Exception:
        top10 = ([0], [1])
    try:
        top100 = top_100_cdtd()
    except Exception:
        top100 = ([1, 2, 3, 4, 5, 6], [0, 0, 0, 0, 0, 0])
    try:
        rows = compute_cdtd_nv_risk(top10, top100)
    except Exception:
        rows = []
    by_id = {int(r["id"]): r for r in rows if r.get("id") is not None}
    _cdtd_risk_cache = {
        "ts": now,
        "rows": rows,
        "top10": top10,
        "top100": top100,
        "by_id": by_id,
        "issue_id": cdtd_issue_id,
    }
    return _cdtd_risk_cache


def cdtd_active_issue():
    """Kỳ đang chờ / đang cược (pending) — ưu tiên hiển thị trên header."""
    # 1) Lệnh cược còn pending
    try:
        for b in reversed(list(cdtd_bet_history)):
            if b.get("result") == "pending" and b.get("issue") is not None:
                try:
                    return int(b["issue"])
                except Exception:
                    return b["issue"]
    except Exception:
        pass
    # 2) Đã khóa dự đoán → cược cho kỳ kế tiếp
    if cdtd_issue_id is not None and (cdtd_predicted_nv is not None or cdtd_predicted_nvs):
        try:
            return int(cdtd_issue_id) + 1
        except Exception:
            return cdtd_issue_id
    # 3) Kỳ API hiện tại
    return cdtd_issue_id


def build_cdtd_header():
    """CDTD / NOVA: status cockpit ngang, tối ưu cho terminal rộng và điện thoại."""
    asset = user_asset_cdtd().get(cdtd_coin, 0)
    pnl = asset - cdtd_stats["asset_0"]
    pnl_color = TST_COLORS["emerald"] if pnl >= 0 else TST_COLORS["ruby"]
    title = Text()
    title.append("CDTD", style=f"bold {TST_COLORS['sapphire']}")
    title.append("  /  ", style=TST_COLORS["muted"])
    title.append("ĐIỀU KHIỂN ĐUA", style=f"bold {TST_COLORS['platinum']}")
    title.append("   TRỰC TIẾP", style=f"bold {TST_COLORS['emerald']}")
    cells = [
        ("USER", str(USER_ID or "N/A"), TST_COLORS["sapphire"]),
        ("SỐ DƯ", f"{asset:,.4f} {cdtd_coin}", TST_COLORS["gold"]),
        ("P&L", f"{pnl:+,.4f}", pnl_color),
        ("CHUỖI", f"{cdtd_win_streak}T / {cdtd_lose_streak}B", TST_COLORS["neon_pink"]),
        ("HẠN KEY", _key_countdown_str(), TST_COLORS["gold"]),
        ("GIỜ VN", (_vn_now_str().split("  ")[0] if "  " in _vn_now_str() else _vn_now_str()[:8]), TST_COLORS["sky"]),
        ("KỲ", str(cdtd_active_issue() or "—"), TST_COLORS["muted"]),
    ]
    g = Table.grid(expand=True, padding=(0, 1))
    for _ in cells:
        g.add_column(ratio=1)
    g.add_row(*[
        Text.from_markup(f"[bold {c}]{label}[/]" + chr(10) + f"[bold white]{value}[/]")
        for label, value, c in cells
    ])
    return Group(
        build_live_brand("CDTD"),
        Align.center(title),
        Rule(style=TST_COLORS["sapphire"]),
        Panel(g, border_style=TST_COLORS["onyx"], box=box.SIMPLE, padding=(0,1)),
    )




def build_cdtd_racers():
    """Athlete board + risk mỗi ván (cập nhật theo top10/top100)."""
    bundle = _cdtd_risk_bundle()
    data_top100 = bundle.get("top100")
    data_top10 = bundle.get("top10")
    risk_by = bundle.get("by_id") or {}
    pred_set = set(cdtd_predicted_nvs) if cdtd_predicted_nvs else ({cdtd_predicted_nv} if cdtd_predicted_nv else set())
    # last winner = kết quả gần nhất (cuối list recent)
    last = None
    if data_top10 and len(data_top10) > 1 and data_top10[1]:
        try:
            last = int(data_top10[1][-1])
        except Exception:
            try:
                last = int(data_top10[1][0])
            except Exception:
                last = None

    grid = Table.grid(expand=True, padding=(1, 1))
    grid.add_column(ratio=1)
    grid.add_column(ratio=1)
    grid.add_column(ratio=1)
    cards = []
    for i in range(1, 7):
        wins = 0
        if data_top100 and len(data_top100) > 1 and data_top100[1] and i - 1 < len(data_top100[1]):
            try:
                wins = int(data_top100[1][i - 1] or 0)
            except Exception:
                wins = 0
        rr = risk_by.get(i) or {}
        risk_pct = float(rr.get("risk_pct", 50.0) or 50.0)
        if risk_pct >= 70:
            risk_col = TST_COLORS["ruby"]
            risk_tag = "RỦI RO CAO"
        elif risk_pct >= 40:
            risk_col = TST_COLORS["neon_orange"]
            risk_tag = "RỦI RO TB"
        else:
            risk_col = TST_COLORS["emerald"]
            risk_tag = "RỦI RO THẤP"

        if i in pred_set:
            accent, tag = TST_COLORS["emerald"], "MỤC TIÊU"
        elif i == last:
            accent, tag = TST_COLORS["gold"], "VỪA THẮNG"
        else:
            accent, tag = TST_COLORS["onyx"], "SẴN SÀNG"

        body = Text()
        body.append(f"{i:02d}  ", style=f"bold {accent}")
        body.append(f"{NV_ICONS.get(i, '•')} {NV.get(i, 'NV ' + str(i))}\n", style="bold white")
        body.append(f"{wins:>3} THẮNG  ", style=TST_COLORS["muted"])
        body.append(f"{tag}\n", style=f"bold {accent}")
        body.append(f"RỦI RO {risk_pct:4.0f}%  ", style=f"bold {risk_col}")
        body.append(risk_tag, style=risk_col)
        body.append("\n")
        # thanh risk (đầy = rủi ro cao)
        filled = max(1, min(18, int(risk_pct / 100 * 18)))
        body.append("━" * filled, style=risk_col)
        body.append("─" * (18 - filled), style=TST_COLORS["onyx"])
        cards.append(Panel(body, border_style=accent, box=box.ROUNDED, padding=(0, 1)))
    for row in range(2):
        grid.add_row(*cards[row * 3:(row + 1) * 3])
    return Panel(
        grid,
        title=f"[bold {TST_COLORS['sapphire']}]01  BẢNG NHÂN VẬT[/]",
        subtitle="mục tiêu • vừa thắng • rủi ro mỗi ván",
        border_style=TST_COLORS["sapphire"],
        box=box.ROUNDED,
        padding=(0, 1),
    )




def build_cdtd_mid():
    body = Text()
    if False and cdtd_ui_state == "DANGER":  # đã tắt cảnh báo nguy hiểm
        body.append("⚠ CẢNH BÁO NGUY HIỂM" + chr(10) + chr(10), style=f"bold {TST_COLORS['ruby']}")
        body.append((cdtd_round_warning or "Phân tích không ổn") + chr(10) + chr(10), style="bold white")
        body.append("BỎ VÁN NÀY", style=f"bold {TST_COLORS['neon_orange']}")
        body.append(chr(10) + chr(10) + "Chờ kỳ sau…", style=TST_COLORS["muted"])
        accent, title = TST_COLORS["ruby"], "02  NGUY HIỂM · BỎ VÁN"
    elif cdtd_ui_state == "ANALYZING":

        elapsed = time.time() - (cdtd_analysis_start_ts or time.time())
        progress = min(1.0, elapsed / max(cdtd_analysis_duration, 0.1))
        filled = int(30 * progress)
        body.append("LUỒNG QUYẾT ĐỊNH AI\n\n", style=f"bold {TST_COLORS['sapphire']}")
        body.append("[" + "■"*filled + "·"*(30-filled) + "]\n", style=f"bold {TST_COLORS['neon_pink']}")
        body.append(f"\n{progress*100:05.1f}%  ", style=f"bold {TST_COLORS['gold']}")
        body.append(f"Còn {max(0,int(cdtd_analysis_duration-elapsed))}s", style=TST_COLORS["muted"])
        accent, title = TST_COLORS["sapphire"], "02  AI PHÂN TÍCH"
    elif cdtd_ui_state == "PREDICTED":
        bet_amt = cdtd_current_bet or cdtd_base_bet
        nvs = cdtd_predicted_nvs if cdtd_predicted_nvs else ([cdtd_predicted_nv] if cdtd_predicted_nv else [])
        names = "  •  ".join(f"{NV_ICONS.get(n,'•')} {NV.get(n,'NV'+str(n))}" for n in nvs) or "N/A"
        total = bet_amt * max(1, len(nvs))
        body.append("DỰ ĐOÁN ĐÃ KHÓA\n\n", style=f"bold {TST_COLORS['emerald']}")
        body.append(names + "\n\n", style="bold white")
        body.append(f"CƯỢC  {bet_amt:.2f} × {max(1,len(nvs))}\n", style=TST_COLORS["muted"])
        body.append(f"TỔNG  {total:.2f} {cdtd_coin}", style=f"bold {TST_COLORS['gold']}")
        accent, title = TST_COLORS["emerald"], "02  KHÓA MỤC TIÊU"
    elif cdtd_ui_state == "RESULT":
        last_bet = cdtd_bet_history[-1] if cdtd_bet_history else None
        win = bool(last_bet and last_bet.get("result") == "win")
        accent = TST_COLORS["emerald"] if win else TST_COLORS["ruby"] if last_bet else TST_COLORS["gold"]
        body.append("KẾT THÚC VÁN\n\n", style=f"bold {accent}")
        if cdtd_previous_issue is not None:
            body.append(f"KỲ {cdtd_previous_issue} vừa xong\n", style=TST_COLORS["gold"])
        body.append(
            f"NV THẮNG  {NV_ICONS.get(cdtd_last_winner, chr(8226))} {NV.get(cdtd_last_winner, 'N/A')}\n\n",
            style="bold white",
        )
        body.append("SẴN SÀNG VÁN SAU", style=TST_COLORS["muted"])
        title = "02  KẾT QUẢ VÁN"
    else:
        accent, title = TST_COLORS["gold"], "02  CHỜ ENGINE"
        body.append("ĐANG CHỜ DỮ LIỆU ĐUA\n\n", style=f"bold {accent}")
        body.append("ĐANG KẾT NỐI ENGINE", style=TST_COLORS["muted"])
    return Panel(Align.center(body, vertical="middle"), title=f"[bold]{title}[/]", border_style=accent, box=box.ROUNDED, padding=(1,2))




def build_cdtd_history():
    t = Table(show_header=True, box=box.SIMPLE_HEAVY, expand=True, padding=(0,1))
    t.add_column("KỲ", style=TST_COLORS["muted"], no_wrap=True)
    t.add_column("MỤC TIÊU")
    t.add_column("CƯỢC", justify="right", style=TST_COLORS["gold"])
    t.add_column("KẾT QUẢ", justify="right")
    rows = list(cdtd_bet_history)[-6:]
    if not rows:
        t.add_row("—", "Chưa có", "0.00", Text("CHỜ", style=TST_COLORS["muted"]))
    for b in rows:
        res = b.get("result")
        rc = TST_COLORS["emerald"] if res == "win" else TST_COLORS["ruby"] if res == "lose" else TST_COLORS["gold"]
        t.add_row(str(b.get("issue","-")), NV.get(b.get("chosen"), str(b.get("chosen","-"))),
                  f"{b.get('amount',0):.2f}", Text({"win":"THẮNG","lose":"THUA"}.get(str(res), str(res or "CHỜ")).upper(), style=f"bold {rc}"))
    return Panel(t, title="[bold]03  SỔ CƯỢC[/]", border_style=TST_COLORS["onyx"], box=box.ROUNDED, padding=(0,1))




def build_cdtd_stats():
    """Performance matrix + RISK mỗi ván."""
    bundle = _cdtd_risk_bundle()
    data = bundle.get("top100")
    risk_by = bundle.get("by_id") or {}
    rows_risk = bundle.get("rows") or []

    t = Table(show_header=True, box=box.SIMPLE, expand=True, padding=(0, 1))
    t.add_column("STT", width=3, style=TST_COLORS["muted"])
    t.add_column("NHÂN VẬT")
    t.add_column("THẮNG", justify="right", style=TST_COLORS["emerald"])
    t.add_column("TỶ LỆ", justify="right", style=TST_COLORS["neon_pink"])
    t.add_column("P(THẮNG)", justify="right")
    t.add_column("P(THUA)", justify="right")
    t.add_column("MỨC", justify="center")
    vals = data[1] if data and len(data) > 1 and data[1] else [0] * 6
    total = max(1, sum(int(x or 0) for x in vals))
    for i in range(6):
        wins = int(vals[i] if i < len(vals) else 0)
        rr = risk_by.get(i + 1) or {}
        risk_pct = float(rr.get("risk_pct", 50.0) or 50.0)
        win_p = float(rr.get("win_prob", 100.0 - risk_pct) or (100.0 - risk_pct))
        lose_p = float(rr.get("lose_prob", 100.0 - win_p) or (100.0 - win_p))
        lvl, col = _risk_level(risk_pct)
        wcol = TST_COLORS["emerald"] if win_p >= 22 else TST_COLORS["neon_orange"] if win_p >= 14 else TST_COLORS["ruby"]
        lcol = TST_COLORS["ruby"] if lose_p >= 75 else TST_COLORS["neon_orange"] if lose_p >= 60 else TST_COLORS["emerald"]
        t.add_row(
            str(i + 1),
            f"{NV_ICONS.get(i + 1, '•')} {NV.get(i + 1, 'NV' + str(i + 1))}",
            str(wins),
            f"{wins / total * 100:.1f}%",
            Text(f"{win_p:.0f}%", style=f"bold {wcol}"),
            Text(f"{lose_p:.0f}%", style=f"bold {lcol}"),
            Text(lvl, style=f"bold {col}"),
        )

    pnl = user_asset_cdtd().get(cdtd_coin, 0) - cdtd_stats["asset_0"]
    summary = Text()
    summary.append("PHIÊN" + chr(10), style=f"bold {TST_COLORS['sapphire']}")
    summary.append(f"VÁN      {cdtd_stats['win'] + cdtd_stats['lose']}" + chr(10))
    summary.append(f"THẮNG    {cdtd_stats['win']}" + chr(10), style=TST_COLORS["emerald"])
    summary.append(f"THUA     {cdtd_stats['lose']}" + chr(10), style=TST_COLORS["ruby"])
    summary.append(f"MAX T    {cdtd_max_win_streak}" + chr(10))
    summary.append(f"MAX B    {cdtd_max_lose_streak}" + chr(10))
    summary.append(
        f"P&L      {pnl:+.4f} {cdtd_coin}" + chr(10),
        style=f"bold {TST_COLORS['emerald'] if pnl >= 0 else TST_COLORS['ruby']}",
    )
    try:
        if cdtd_stop_when_profit and cdtd_profit_target:
            summary.append(f"CHỐT LÃI ≥ {float(cdtd_profit_target):.2f}" + chr(10), style=TST_COLORS["emerald"])
        if cdtd_stop_when_loss and cdtd_stop_loss_target:
            summary.append(f"CẮT LỖ  ≤ {float(cdtd_stop_loss_target):.2f}" + chr(10), style=TST_COLORS["ruby"])
        if float(cdtd_random_skip_pct or 0) > 0:
            summary.append(f"SKIP RD  {float(cdtd_random_skip_pct):.0f}%" + chr(10), style=TST_COLORS["muted"])
    except Exception:
        pass
    try:
        summary.append(chr(10))
        summary.append(format_ai_stats_text(str((cdtd_settings or {}).get("algo", "")), "CDTD_"))
    except Exception:
        pass
    if rows_risk:
        safest = min(rows_risk, key=lambda x: x["risk_pct"])
        riskiest = max(rows_risk, key=lambda x: x["risk_pct"])
        best_win = max(rows_risk, key=lambda x: float(x.get("win_prob", 0) or 0))
        summary.append(chr(10) + "XÁC SUẤT THẮNG / THUA" + chr(10), style=f"bold {TST_COLORS['gold']}")
        summary.append(
            f"CAO NHẤT {best_win.get('icon','•')} {best_win.get('name','?')}  P≈{float(best_win.get('win_prob',0)):.0f}%" + chr(10),
            style=TST_COLORS["emerald"],
        )
        summary.append(
            f"NÊN CƯỢC  {safest.get('icon','•')} {safest.get('name','?')} risk {safest['risk_pct']:.0f}%" + chr(10),
            style=TST_COLORS["emerald"],
        )
        summary.append(
            f"NÊN TRÁNH {riskiest.get('icon','•')} {riskiest.get('name','?')} risk {riskiest['risk_pct']:.0f}%",
            style=TST_COLORS["ruby"],
        )

    return Panel(
        Columns(
            [
                Panel(t, border_style=TST_COLORS["onyx"], box=box.SIMPLE),
                Panel(summary, border_style=TST_COLORS["gold"], box=box.SIMPLE, padding=(1, 2)),
            ],
            equal=True,
            expand=True,
        ),
        title="[bold]04  XÁC SUẤT THẮNG · THUA[/]",
        border_style=TST_COLORS["sky"],
        box=box.ROUNDED,
        padding=(0, 1),
    )




def build_cdtd_marquee():
    text = Text()
    text.append("ENGINE  ", style=f"bold {TST_COLORS['muted']}")
    text.append(CDTD_ALGORITHMS.get(cdtd_settings.get('algo','FREE'),'N/A'), style=f"bold {TST_COLORS['sapphire']}")
    text.append("   │   ", style=TST_COLORS["onyx"])
    text.append(f"CƯỢC {cdtd_base_bet} × {cdtd_num_athletes}", style=TST_COLORS["gold"])
    text.append("   │   ", style=TST_COLORS["onyx"])
    text.append(f"x{cdtd_multiplier}", style=TST_COLORS["neon_pink"])
    text.append("   │   ", style=TST_COLORS["onyx"])
    text.append(f"W {cdtd_stats['win']}  /  L {cdtd_stats['lose']}", style=TST_COLORS["muted"])
    if cdtd_previous_issue is not None and cdtd_last_winner:
        text.append("   │   ", style=TST_COLORS["onyx"])
        text.append(f"VỪA XONG {cdtd_previous_issue}", style=TST_COLORS["gold"])
        text.append(
            f" · THẮNG {NV_ICONS.get(cdtd_last_winner, '•')} {NV.get(cdtd_last_winner, cdtd_last_winner)}",
            style=TST_COLORS["emerald"],
        )
    return Panel(Align.center(text), border_style=TST_COLORS["onyx"], box=box.SIMPLE, padding=(0,1))




def cdtd_generate_layout():
    """CDTD NOVA: bố cục 4 tầng, không còn dashboard cũ."""
    root = Table.grid(expand=True, pad_edge=False)
    root.add_row(build_cdtd_header())
    root.add_row(build_cdtd_marquee())

    middle = Table.grid(expand=True, pad_edge=False)
    middle.add_column(ratio=60)
    middle.add_column(ratio=40)
    middle.add_row(build_cdtd_racers(), build_cdtd_mid())
    root.add_row(middle)

    root.add_row(build_cdtd_history())
    root.add_row(build_cdtd_stats())
    return root


def cdtd_prompt_settings():
    global cdtd_base_bet, cdtd_multiplier, cdtd_coin, cdtd_current_bet, cdtd_pause_rounds
    global cdtd_bet_rounds_before_skip, cdtd_settings, _key_type, cdtd_num_athletes

    console.clear()
    brand = Text()
    brand.append(" ▶▶ ", style=f"bold {TST_COLORS['bg_deep']} on {TST_COLORS['neon_blue']}")
    brand.append("  CHẠY ĐUA TỐC ĐỘ  ", style=f"bold {TST_COLORS['gold']}")
    brand.append("  ·  CẤU HÌNH ĐUA  ", style=TST_COLORS["muted"])
    console.print(Align.center(brand))
    console.print(Rule(f"[bold {TST_COLORS['neon_blue']}]  ▶  CẤU HÌNH CƯỢC  [/]", style=TST_COLORS["sapphire"]))
    console.print()

    console.print(Text.assemble(("▌ ", f"bold {TST_COLORS['gold']}"), ("HỆ THỐNG CƯỢC", f"bold {TST_COLORS['gold']}")))
    coin_choice = Prompt.ask(
        f"  [{TST_COLORS['muted']}]Tiền tệ[/{TST_COLORS['muted']}] [bold {TST_COLORS['gold']}]1[/]=USDT  [bold {TST_COLORS['neon_blue']}]2[/]=BUILD  [bold {TST_COLORS['neon_pink']}]3[/]=WORLD",
        choices=["1","2","3"], default="2"
    )
    cdtd_coin = {"1":"USDT","2":"BUILD","3":"WORLD"}[coin_choice]
    cdtd_base_bet = FloatPrompt.ask(f"  Cược gốc ({cdtd_coin})", default=1.0)
    cdtd_multiplier = FloatPrompt.ask("  Hệ số nhân", default=2.0)
    cdtd_current_bet = cdtd_base_bet
    cdtd_num_athletes = int(IntPrompt.ask("  Số nhân vật [1-5]", choices=["1","2","3","4","5"], default=str(cdtd_num_athletes or 1)))
    global cdtd_stop_loss_target, cdtd_profit_target, cdtd_stop_when_loss, cdtd_stop_when_profit, cdtd_random_skip_pct
    cdtd_bet_rounds_before_skip = IntPrompt.ask("  Bỏ qua sau N ván (0=tắt)", default=0)
    cdtd_pause_rounds = IntPrompt.ask("  Tạm dừng N ván sau thua (0=tắt)", default=0)
    cdtd_random_skip_pct = FloatPrompt.ask("  Bỏ ngẫu nhiên % kỳ (0–40, gợi ý 15–25)", default=float(cdtd_random_skip_pct or 0))
    try:
        cdtd_random_skip_pct = max(0.0, min(40.0, float(cdtd_random_skip_pct)))
    except Exception:
        cdtd_random_skip_pct = 0.0
    cdtd_stop_when_profit = Prompt.ask("  Chốt lời khi số dư ≥ mức (y/n)", choices=["y", "n"], default="n") == "y"
    cdtd_profit_target = FloatPrompt.ask(f"  Mức chốt lời ({cdtd_coin})", default=0.0) if cdtd_stop_when_profit else None
    cdtd_stop_when_loss = Prompt.ask("  Cắt lỗ khi số dư ≤ mức (y/n)", choices=["y", "n"], default="n") == "y"
    cdtd_stop_loss_target = FloatPrompt.ask(f"  Mức cắt lỗ ({cdtd_coin})", default=0.0) if cdtd_stop_when_loss else None

    available = get_available_cdtd_ai_list(_key_type)
    console.print()
    console.print(Rule(f"[bold {TST_COLORS['sapphire']}]  ◉  ENGINE AI  ·  {len(available)} KHẢ DỤNG  [/]", style=TST_COLORS["accent_line"]))
    t = Table(show_header=True, box=box.SIMPLE_HEAVY, expand=True, padding=(0,1))
    t.add_column("#", width=4, style=TST_COLORS["muted"])
    t.add_column("ENGINE", style=f"bold {TST_COLORS['platinum']}")
    for i, k in enumerate(available, 1):
        row_style = TST_COLORS["sapphire"] if i % 2 == 0 else TST_COLORS["neon_pink"]
        t.add_row(Text(str(i), style=f"bold {row_style}"), CDTD_ALGORITHMS.get(k, k))
    console.print(t)
    idx = IntPrompt.ask(
        f"  [bold {TST_COLORS['gold']}]▶ Chọn engine[/bold {TST_COLORS['gold']}]",
        choices=[str(i) for i in range(1, len(available)+1)], default=1
    )
    cdtd_settings["algo"] = available[idx-1]


    console.print()
    console.print(Rule(style=TST_COLORS["accent_line"]))
    if Prompt.ask(f"  [bold {TST_COLORS['neon_orange']}]◈ Tích hợp Telegram (y/n)[/bold {TST_COLORS['neon_orange']}]", choices=["y","n"], default="n") == "y":
        setup_telegram()
    console.print()
    console.print(Panel(
        Text.assemble(
            ("✓  ĐÃ LƯU CẤU HÌNH\n", f"bold {TST_COLORS['emerald']}"),
            ("ENGINE  ", TST_COLORS["muted"]),
            (CDTD_ALGORITHMS.get(cdtd_settings['algo'], cdtd_settings['algo']), f"bold {TST_COLORS['gold']}"),
        ),
        border_style=TST_COLORS["emerald"],
        box=box.SIMPLE,
        padding=(0, 2),
    ))
    time.sleep(0.8)
    return True


def main_cdtd_v3():
    console.clear()
    brand = Text()
    brand.append(" ▶▶ ", style=f"bold {TST_COLORS['bg_deep']} on {TST_COLORS['neon_blue']}")
    brand.append("  CHẠY ĐUA TỐC ĐỘ  ", style=f"bold {TST_COLORS['platinum']}")
    brand.append("·  ENGINE 42 AI ĐUA", style=TST_COLORS["muted"])
    console.print(Panel(
        Align.center(brand),
        border_style=TST_COLORS["neon_blue"],
        box=box.HEAVY_HEAD,
        padding=(0, 1),
    ))
    console.print(Align.center(Text("◈ Support: @tst-tool88  ·  42 AI  ·  Telegram", style=TST_COLORS["muted"])))
    console.print()
    
    data = load_data_cdtd()
    setup_cdtd_headers(data)

    if not (data.get("user-id") and data.get("user-secret-key")):
        console.print("[bold red]❌ CDTD chưa nhận tài khoản (thiếu user-id / secret).[/]")
        console.print("[dim]Menu Thêm tài khoản hoặc dán link userId & secretKey.[/dim]")
        Prompt.ask("Nhấn Enter để quay lại", default="")
        return

    if Prompt.ask("Dùng account này? (y=tiếp / n=nhập lại)", choices=["y", "n"], default="y") == "n":
        data = load_data_cdtd(force_new=True)
        setup_cdtd_headers(data)
        if not (data.get("user-id") and data.get("user-secret-key")):
            console.print("[red]❌ Vẫn thiếu tài khoản CDTD.[/red]")
            Prompt.ask("Nhấn Enter", default="")
            return

    if not cdtd_prompt_settings():
        return

    console.clear()
    console.print(f"[bold {TST_COLORS['neon_orange']}]🏎️ KHỞI ĐỘNG CDTD · user {data.get('user-id')}...[/]")

    with console.status(f"[bold {TST_COLORS['gold']}]🔍 Đang kiểm tra số dư...[/]", spinner="dots"):
        asset = user_asset_cdtd()
        time.sleep(0.8)

    console.print(
        f"[dim]USDT={asset.get('USDT', 0):.4f} · BUILD={asset.get('BUILD', 0):.4f} · WORLD={asset.get('WORLD', 0):.4f}[/dim]"
    )
    if sum(float(v or 0) for v in asset.values()) <= 0:
        console.print("[yellow]⚠️ Số dư toàn 0 — thử sync headers + API lại...[/yellow]")
        if USER_ID and SECRET_KEY:
            setup_cdtd_headers({"user-id": str(USER_ID), "user-secret-key": str(SECRET_KEY)})
            asset = user_asset_cdtd(retries=3)
            console.print(
                f"[dim]Retry: USDT={asset.get('USDT', 0):.4f} · BUILD={asset.get('BUILD', 0):.4f} · WORLD={asset.get('WORLD', 0):.4f}[/dim]"
            )
        # Cho phép tiếp tục nếu coin cược > 0; nếu vẫn 0 thì hỏi
        if asset.get(cdtd_coin, 0) <= 0:
            console.print(f"[red]❌ Số dư {cdtd_coin} = 0 — không thể cược coin này.[/red]")
            console.print(f"[dim]user-id={cdtd_headers.get('user-id')} · kiểm tra secretKey đúng chưa[/dim]")
            if Prompt.ask("Vẫn vào (xem live, không cược được)?", choices=["y", "n"], default="n") != "y":
                time.sleep(1)
                return
    
    console.print(f'[green]✅ Số dư: {asset[cdtd_coin]:.4f} {cdtd_coin}[/]')
    if TELEGRAM_ENABLED:
        console.print(f'[green]✅ Telegram: BẬT[/]')
    
    time.sleep(2)
    cdtd_game_loop()
    
    console.clear()
    final_asset = user_asset_cdtd()
    pnl = final_asset.get(cdtd_coin, 0) - cdtd_stats['asset_0']
    pnl_col = TST_COLORS["emerald"] if pnl >= 0 else TST_COLORS["ruby"]
    sum_grid = Table.grid(expand=True, padding=(0, 3))
    sum_grid.add_column(ratio=1); sum_grid.add_column(ratio=1); sum_grid.add_column(ratio=1)
    sum_grid.add_row(
        Panel(Text.assemble(("THẮNG\n", TST_COLORS["muted"]), (str(cdtd_stats['win']), f"bold {TST_COLORS['emerald']}")), border_style=TST_COLORS["emerald"], box=box.SIMPLE, padding=(0,2)),
        Panel(Text.assemble(("THUA\n",  TST_COLORS["muted"]), (str(cdtd_stats['lose']), f"bold {TST_COLORS['ruby']}")),   border_style=TST_COLORS["ruby"],    box=box.SIMPLE, padding=(0,2)),
        Panel(Text.assemble(("P&L\n",   TST_COLORS["muted"]), (f"{pnl:+.4f} {cdtd_coin}", f"bold {pnl_col}")),             border_style=pnl_col,                 box=box.SIMPLE, padding=(0,2)),
    )
    summary = Panel(
        Group(
            Align.center(Text("◈  TỔNG KẾT PHIÊN  ◈", style=f"bold {TST_COLORS['gold']}")),
            Rule(style=TST_COLORS["accent_line"]),
            sum_grid,
        ),
        border_style=TST_COLORS["gold"],
        box=box.HEAVY_HEAD,
        padding=(0, 1),
    )
    console.print(summary)
    console.print("\n[dim]Nhấn Enter để quay lại menu...[/]")
    input()
    # ================== LOGO / CẤU HÌNH / GAME FLOW ==================

def build_logo_with_gradient(logo: str) -> Text:
    """Render logo với màu gradient vàng."""
    text = Text()
    colors = [
        TST_COLORS["gold"],
        TST_COLORS["gold_dark"],
        TST_COLORS["neon_orange"],
        TST_COLORS["gold"],
    ]
    lines = logo.split("\n")
    for i, line in enumerate(lines):
        if not line.strip():
            text.append("\n")
            continue
        color = colors[i % len(colors)]
        text.append(line + "\n", style=f"bold {color}")
    return text


def save_strategy_config() -> bool:
    """Lưu cấu hình chiến lược ra file."""
    global base_bet, multiplier, run_mode, bet_rounds_before_skip, num_rooms
    global pause_after_losses, profit_target, stop_when_profit_reached
    global stop_loss_target, stop_when_loss_reached, analysis_duration, settings, random_skip_pct
    try:
        cfg = {
            "algo": settings.get("algo", "FREE"),
            "base_bet": base_bet,
            "num_rooms": num_rooms,
            "multiplier": multiplier,
            "run_mode": run_mode,
            "bet_rounds_before_skip": bet_rounds_before_skip,
            "pause_after_losses": pause_after_losses,
            "profit_target": profit_target,
            "stop_when_profit_reached": stop_when_profit_reached,
            "stop_loss_target": stop_loss_target,
            "stop_when_loss_reached": stop_when_loss_reached,
            "analysis_duration": analysis_duration,
            "random_skip_pct": random_skip_pct,
        }
        with open(STRATEGY_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
        console.print(f"[green]✅ Đã lưu cấu hình vào {STRATEGY_CONFIG_FILE}[/green]")
        return True
    except Exception as e:
        console.print(f"[red]❌ Lỗi lưu config: {e}[/red]")
        return False


def load_strategy_config() -> bool:
    """Load cấu hình chiến lược từ file."""
    global base_bet, multiplier, run_mode, bet_rounds_before_skip, num_rooms
    global pause_after_losses, profit_target, stop_when_profit_reached
    global stop_loss_target, stop_when_loss_reached, analysis_duration, settings, current_bet, _key_type, random_skip_pct
    if not os.path.exists(STRATEGY_CONFIG_FILE):
        console.print(f"[yellow]⚠️ Chưa có file {STRATEGY_CONFIG_FILE}. Hãy SAVE CONFIG trước.[/yellow]")
        return False
    try:
        with open(STRATEGY_CONFIG_FILE, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        loaded_algo = cfg.get("algo", settings.get("algo", "FREE"))
        available = get_available_ai_list(_key_type)
        if loaded_algo not in available:
            loaded_algo = available[0] if available else "FREE"
            console.print(f"[yellow]⚠️ AI trong config không khả dụng với key {_key_type} → dùng {loaded_algo}[/yellow]")
        settings["algo"] = loaded_algo
        base_bet = float(cfg.get("base_bet", base_bet))
        num_rooms = int(cfg.get("num_rooms", num_rooms or 1))
        multiplier = float(cfg.get("multiplier", multiplier))
        run_mode = cfg.get("run_mode", run_mode)
        bet_rounds_before_skip = int(cfg.get("bet_rounds_before_skip", bet_rounds_before_skip))
        pause_after_losses = int(cfg.get("pause_after_losses", pause_after_losses))
        profit_target = cfg.get("profit_target")
        stop_when_profit_reached = bool(cfg.get("stop_when_profit_reached", False))
        stop_loss_target = cfg.get("stop_loss_target")
        stop_when_loss_reached = bool(cfg.get("stop_when_loss_reached", False))
        analysis_duration = float(cfg.get("analysis_duration", analysis_duration))
        current_bet = base_bet
        console.print(f"[green]✅ Đã load config: LOGIC={settings['algo']} | Cược={base_bet} | x{multiplier}[/green]")
        return True
    except Exception as e:
        console.print(f"[red]❌ Lỗi load config: {e}[/red]")
        return False


def prompt_settings() -> bool:
    global base_bet, multiplier, run_mode, bet_rounds_before_skip, num_rooms
    global pause_after_losses, profit_target, stop_when_profit_reached
    global stop_loss_target, stop_when_loss_reached, analysis_duration, settings, current_bet, _key_type

    console.clear()
    brand = Text()
    brand.append(" ♛ ", style=f"bold {TST_COLORS['bg_deep']} on {TST_COLORS['emerald']}")
    brand.append("  VUA THOÁT HIỂM  ", style=f"bold {TST_COLORS['platinum']}")
    brand.append("·  STRATEGY CONFIG", style=TST_COLORS["muted"])
    console.print(Panel(Align.center(brand), border_style=TST_COLORS["emerald"], box=box.HEAVY_HEAD, padding=(0,1)))
    console.print()

    console.print(Text.assemble(("▌ ", f"bold {TST_COLORS['gold']}"), ("HỆ THỐNG CƯỢC", f"bold {TST_COLORS['gold']}")))
    base_bet = FloatPrompt.ask(f"  [{TST_COLORS['muted']}]Cược gốc (BUILD)[/{TST_COLORS['muted']}]", default=float(base_bet or 1.0))
    multiplier = FloatPrompt.ask(f"  [{TST_COLORS['muted']}]Hệ số nhân[/{TST_COLORS['muted']}]", default=float(multiplier or 2.0))
    num_rooms = int(IntPrompt.ask(
        f"  [{TST_COLORS['muted']}]Số phòng mỗi ván [1-4] (TỔNG HỢP cũng cược đủ số này)[/{TST_COLORS['muted']}]",
        choices=["1", "2", "3", "4"],
        default=str(num_rooms or 1),
    ))
    current_bet = base_bet
    run_mode = "AUTO" if Prompt.ask(
        f"  [{TST_COLORS['muted']}]Mode[/{TST_COLORS['muted']}] [bold {TST_COLORS['gold']}]1[/]=AUTO  [bold {TST_COLORS['sapphire']}]2[/]=MANUAL",
        choices=["1","2"], default="1"
    ) == "1" else "MANUAL"

    console.print()
    console.print(Rule(f"[bold {TST_COLORS['ruby']}]  ◈  KIỂM SOÁT RỦI RO  [/]", style=TST_COLORS["accent_line"]))
    global random_skip_pct
    bet_rounds_before_skip = IntPrompt.ask(f"  [{TST_COLORS['muted']}]Bỏ qua sau N ván (0=tắt)[/{TST_COLORS['muted']}]", default=int(bet_rounds_before_skip or 0))
    pause_after_losses = IntPrompt.ask(f"  [{TST_COLORS['muted']}]Tạm dừng N ván sau thua (0=tắt)[/{TST_COLORS['muted']}]", default=int(pause_after_losses or 0))
    analysis_duration = FloatPrompt.ask(f"  [{TST_COLORS['muted']}]Thời gian phân tích (giây)[/{TST_COLORS['muted']}]", default=float(analysis_duration or 45.0))
    random_skip_pct = FloatPrompt.ask(
        f"  [{TST_COLORS['muted']}]Bỏ ngẫu nhiên % kỳ (0–40, khuyến nghị 15–25)[/{TST_COLORS['muted']}]",
        default=float(random_skip_pct or 0),
    )
    try:
        random_skip_pct = max(0.0, min(40.0, float(random_skip_pct)))
    except Exception:
        random_skip_pct = 0.0

    stop_when_profit_reached = Prompt.ask(
        f"  [bold {TST_COLORS['emerald']}]◈ Chốt lời khi số dư ≥ mức (y/n)[/bold {TST_COLORS['emerald']}]", choices=["y","n"], default="n"
    ) == "y"
    profit_target = FloatPrompt.ask(f"  [{TST_COLORS['muted']}]Mức chốt lời (BUILD)[/{TST_COLORS['muted']}]", default=0.0) if stop_when_profit_reached else None
    stop_when_loss_reached = Prompt.ask(
        f"  [bold {TST_COLORS['ruby']}]◈ Cắt lỗ khi số dư ≤ mức (y/n)[/bold {TST_COLORS['ruby']}]", choices=["y","n"], default="n"
    ) == "y"
    stop_loss_target = FloatPrompt.ask(f"  [{TST_COLORS['muted']}]Mức cắt lỗ (BUILD)[/{TST_COLORS['muted']}]", default=0.0) if stop_when_loss_reached else None

    available = get_available_ai_list(_key_type)
    console.print()
    console.print(Rule(f"[bold {TST_COLORS['sapphire']}]  ◉  ENGINE AI  ·  {len(available)} KHẢ DỤNG  [/]", style=TST_COLORS["accent_line"]))
    ai_table = Table(show_header=True, box=box.SIMPLE_HEAVY, expand=True, padding=(0,1))
    ai_table.add_column("#", width=4, style=TST_COLORS["muted"])
    ai_table.add_column("ENGINE", style=f"bold {TST_COLORS['platinum']}")
    for i, k in enumerate(available, 1):
        row_col = TST_COLORS["sapphire"] if i % 2 == 0 else TST_COLORS["neon_pink"]
        ai_table.add_row(Text(str(i), style=f"bold {row_col}"), SELECTION_MODES.get(k, k))
    console.print(ai_table)
    idx = IntPrompt.ask(
        f"  [bold {TST_COLORS['gold']}]▶ Chọn engine[/bold {TST_COLORS['gold']}]",
        choices=[str(i) for i in range(1, len(available)+1)], default=1
    )
    settings["algo"] = available[idx-1]


    console.print()
    console.print(Rule(style=TST_COLORS["accent_line"]))
    if Prompt.ask(
        f"  [bold {TST_COLORS['neon_orange']}]◈ Tích hợp Telegram (y/n)[/bold {TST_COLORS['neon_orange']}]",
        choices=["y","n"], default="n"
    ) == "y":
        setup_telegram()
    console.print()
    console.print(Panel(
        Text.assemble(
            ("✓  ĐÃ LƯU CẤU HÌNH\n", f"bold {TST_COLORS['emerald']}"),
            ("ENGINE  ", TST_COLORS["muted"]),
            (SELECTION_MODES.get(settings['algo'], settings['algo']), f"bold {TST_COLORS['gold']}"),
            (f"  ·  {num_rooms} phòng", TST_COLORS["muted"]),
        ),
        border_style=TST_COLORS["emerald"],
        box=box.SIMPLE,
        padding=(0, 2),
    ))
    time.sleep(0.8)
    return True





def _vth_active_issue():
    """Kỳ VTH đang chờ kết quả (pending) hoặc kỳ hiện tại."""
    try:
        for b in reversed(list(bet_history)):
            res = str(b.get("result") or "").strip().lower()
            if res in ("đang", "dang", "pending", "wait", "chờ", "cho", "") and b.get("issue") is not None:
                try:
                    return int(b["issue"])
                except Exception:
                    return b["issue"]
    except Exception:
        pass
    return issue_id


def build_vth_header():
    """Header VTH giống CDTD — Text 2 dòng, không dùng \\n markup lỗi."""
    asset_build = current_build if current_build is not None else 0.0
    pnl = cumulative_profit if cumulative_profit is not None else 0.0
    pnl_color = TST_COLORS["emerald"] if pnl >= 0 else TST_COLORS["ruby"]
    title = Text()
    title.append("VTH", style=f"bold {TST_COLORS['emerald']}")
    title.append("  /  ", style=TST_COLORS["muted"])
    title.append("ĐIỀU KHIỂN THOÁT HIỂM", style=f"bold {TST_COLORS['platinum']}")
    title.append("   TRỰC TIẾP", style=f"bold {TST_COLORS['emerald']}")
    cells = [
        ("USER", str(USER_ID or "N/A"), TST_COLORS["sapphire"]),
        ("SỐ DƯ", f"{asset_build:,.4f} BUILD", TST_COLORS["gold"]),
        ("P&L", f"{pnl:+,.4f}", pnl_color),
        ("CHUỖI", f"{win_streak}T / {lose_streak}B", TST_COLORS["neon_pink"]),
        ("HẠN KEY", _key_countdown_str(), TST_COLORS["gold"]),
        ("GIỜ VN", (_vn_now_str().split("  ")[0] if "  " in _vn_now_str() else _vn_now_str()[:8]), TST_COLORS["sky"]),
        ("KỲ", str(_vth_active_issue() or "—"), TST_COLORS["muted"]),
    ]
    g = Table.grid(expand=True, padding=(0, 1))
    for _ in cells:
        g.add_column(ratio=1)
    g.add_row(*[
        Text.from_markup(f"[bold {c}]{label}[/]" + chr(10) + f"[bold white]{value}[/]")
        for label, value, c in cells
    ])
    return Group(
        build_live_brand("VTH"),
        Align.center(title),
        Rule(style=TST_COLORS["emerald"]),
        Panel(g, border_style=TST_COLORS["onyx"], box=box.SIMPLE, padding=(0, 1)),
    )


def build_vth_marquee():
    algo_name = SELECTION_MODES.get(settings.get("algo", "FREE"), settings.get("algo", "FREE"))
    text = Text()
    text.append("ENGINE  ", style=f"bold {TST_COLORS['muted']}")
    text.append(str(algo_name), style=f"bold {TST_COLORS['emerald']}")
    text.append("   │   ", style=TST_COLORS["onyx"])
    text.append(f"CƯỢC {base_bet} × {max(1, int(num_rooms or 1))}", style=TST_COLORS["gold"])
    text.append("   │   ", style=TST_COLORS["onyx"])
    text.append(f"x{multiplier}", style=TST_COLORS["neon_pink"])
    text.append("   │   ", style=TST_COLORS["onyx"])
    text.append(f"T {win_streak}  /  B {lose_streak}", style=TST_COLORS["muted"])
    if count_down is not None:
        text.append("   │   ", style=TST_COLORS["onyx"])
        text.append(f"ĐẾM {count_down}s", style=TST_COLORS["sky"])
    text.append("   │   ", style=TST_COLORS["onyx"])
    st = str(_ws_status or "…")
    if st.startswith("✅"):
        text.append(st[:28], style=TST_COLORS["emerald"])
    elif st.startswith("❌"):
        text.append(st[:28], style=TST_COLORS["ruby"])
    else:
        text.append(st[:28], style=TST_COLORS["gold"])
    if last_finished_issue is not None:
        text.append("   │   ", style=TST_COLORS["onyx"])
        text.append(f"VỪA XONG {last_finished_issue}", style=TST_COLORS["gold"])
        if last_finished_label:
            text.append(f" · SÁT THỦ {last_finished_label}", style=TST_COLORS["ruby"])
    if False and (round_warning or str(ui_state) == "DANGER"):
        text.append("   │   ", style=TST_COLORS["onyx"])
        text.append("⚠ BỎ VÁN · NGUY HIỂM", style=f"bold {TST_COLORS['ruby']}")
    return Panel(Align.center(text), border_style=TST_COLORS["onyx"], box=box.SIMPLE, padding=(0, 1))


def build_vth_rooms():
    """Bảng phòng dạng card — giống Athlete Board CDTD + risk."""
    try:
        risk_rows = compute_vth_room_risk()
        risk_by = {r["id"]: r for r in risk_rows}
    except Exception:
        risk_by = {}

    grid = Table.grid(expand=True, padding=(0, 1))
    grid.add_column(ratio=1)
    grid.add_column(ratio=1)
    grid.add_column(ratio=1)
    grid.add_column(ratio=1)
    cards = []
    for r in ROOM_ORDER:
        players = int(room_state[r].get("players", 0) or 0)
        bet = float(room_state[r].get("bet", 0) or 0)
        kills = int(room_stats[r].get("kills", 0) or 0)
        rr = risk_by.get(r) or {}
        risk_pct = float(rr.get("risk_pct", 50.0) or 50.0)
        if risk_pct >= 70:
            risk_col, risk_tag = TST_COLORS["ruby"], "RỦI RO CAO"
        elif risk_pct >= 40:
            risk_col, risk_tag = TST_COLORS["neon_orange"], "RỦI RO TB"
        else:
            risk_col, risk_tag = TST_COLORS["emerald"], "RỦI RO THẤP"

        if (predicted_rooms and r in predicted_rooms) or predicted_room == r:
            accent, tag = TST_COLORS["emerald"], "MỤC TIÊU"
        else:
            accent, tag = TST_COLORS["onyx"], "SẴN SÀNG"

        body = Text()
        body.append(f"{r:02d}  ", style=f"bold {accent}")
        name = ROOM_NAMES.get(r, f"Phòng {r}")
        # rút gọn tên nếu dài
        short = name if len(name) <= 18 else name[:16] + "…"
        body.append(f"{short}\n", style="bold white")
        body.append(f"{players} người  ·  {bet:.0f}\n", style=TST_COLORS["muted"])
        body.append(f"KILL {kills}  ", style=TST_COLORS["muted"])
        body.append(f"{tag}\n", style=f"bold {accent}")
        body.append(f"RỦI RO {risk_pct:4.0f}%  ", style=f"bold {risk_col}")
        body.append(risk_tag, style=risk_col)
        body.append("\n")
        filled = max(1, min(16, int(risk_pct / 100 * 16)))
        body.append("━" * filled, style=risk_col)
        body.append("─" * (16 - filled), style=TST_COLORS["onyx"])
        cards.append(Panel(body, border_style=accent, box=box.ROUNDED, padding=(0, 1)))

    for row in range(2):
        grid.add_row(*cards[row * 4:(row + 1) * 4])
    return Panel(
        grid,
        title=f"[bold {TST_COLORS['sapphire']}]01  BẢNG PHÒNG[/]",
        subtitle="mục tiêu • rủi ro mỗi ván",
        border_style=TST_COLORS["sapphire"],
        box=box.ROUNDED,
        padding=(0, 1),
    )


def build_vth_mid():
    """Panel 02 — giống CDTD: thanh tiến trình AI / khóa mục tiêu / kết quả."""
    state_map = {
        "IDLE": "CHỜ",
        "WAITING": "CHỜ",
        "ANALYZING": "ĐANG PHÂN TÍCH",
        "PREDICTED": "ĐÃ DỰ ĐOÁN",
        "RESULT": "KẾT QUẢ",
        "BETTING": "ĐANG CƯỢC",
    }
    st = state_map.get(str(ui_state), str(ui_state))
    algo_name = SELECTION_MODES.get(settings.get("algo", "FREE"), settings.get("algo", "FREE"))
    body = Text()

    if str(ui_state) == "SKIP":  # chỉ nghỉ theo setting user, không danger
        body.append("⚠ CẢNH BÁO NGUY HIỂM" + chr(10) + chr(10), style=f"bold {TST_COLORS['ruby']}")
        body.append((round_warning or "Phân tích không ổn") + chr(10) + chr(10), style="bold white")
        body.append("BỎ VÁN NÀY", style=f"bold {TST_COLORS['neon_orange']}")
        body.append(chr(10) + chr(10) + "Chờ kỳ sau…", style=TST_COLORS["muted"])
        accent, title = TST_COLORS["ruby"], "02  NGUY HIỂM · BỎ VÁN"
    elif str(ui_state) == "ANALYZING":

        elapsed = time.time() - (analysis_start_ts or time.time())
        dur = max(float(analysis_duration or 45.0), 0.1)
        progress = min(1.0, elapsed / dur)
        filled = int(30 * progress)
        body.append("LUỒNG QUYẾT ĐỊNH AI" + chr(10) + chr(10), style=f"bold {TST_COLORS['sapphire']}")
        body.append("[" + "■" * filled + "·" * (30 - filled) + "]" + chr(10), style=f"bold {TST_COLORS['neon_pink']}")
        body.append(f"{chr(10)}{progress * 100:05.1f}%  ", style=f"bold {TST_COLORS['gold']}")
        body.append(f"Còn {max(0, int(dur - elapsed))}s", style=TST_COLORS["muted"])
        body.append(f"{chr(10)}{chr(10)}{algo_name}", style=TST_COLORS["muted"])
        accent, title = TST_COLORS["sapphire"], "02  AI PHÂN TÍCH"
    elif (predicted_rooms or predicted_room is not None) and str(ui_state) in ("PREDICTED", "BETTING", "WAITING", "IDLE"):
        rooms = predicted_rooms if predicted_rooms else ([predicted_room] if predicted_room is not None else [])
        names = "  •  ".join(ROOM_NAMES.get(r, f"P{r}") for r in rooms) or "N/A"
        bet_amt = current_bet or base_bet
        n = max(1, len(rooms))
        body.append("DỰ ĐOÁN ĐÃ KHÓA" + chr(10) + chr(10), style=f"bold {TST_COLORS['emerald']}")
        body.append(names + chr(10) + chr(10), style="bold white")
        body.append(f"CƯỢC  {float(bet_amt):.2f} × {n}" + chr(10), style=TST_COLORS["muted"])
        body.append(f"TỔNG  {float(bet_amt) * n:.2f} BUILD" + chr(10), style=f"bold {TST_COLORS['gold']}")
        try:
            rm = {int(r["id"]): float(r.get("win_prob", 50)) for r in (compute_vth_room_risk() or [])}
            ps = [rm.get(int(r), 50.0) for r in rooms]
            if len(ps) == 1:
                body.append(chr(10) + f"P(THẮNG) ≈ {ps[0]:.0f}%", style=TST_COLORS["emerald"])
                body.append(chr(10) + f"P(THUA)   ≈ {100.0-ps[0]:.0f}%", style=TST_COLORS["ruby"])
            elif ps:
                p_all = 1.0
                for p in ps:
                    p_all *= p / 100.0
                body.append(chr(10) + f"P(SỐNG CẢ) ≈ {p_all*100:.0f}%", style=TST_COLORS["emerald"])
                body.append(chr(10) + f"P(DÍNH ≥1) ≈ {(1-p_all)*100:.0f}%", style=TST_COLORS["ruby"])
        except Exception:
            pass
        accent, title = TST_COLORS["emerald"], "02  KHÓA MỤC TIÊU"
    elif str(ui_state) == "RESULT":
        last = None
        try:
            if bet_history:
                last = bet_history[-1]
        except Exception:
            last = None
        win = bool(last and last.get("result") == "Thắng")
        accent = TST_COLORS["emerald"] if win else TST_COLORS["ruby"] if last else TST_COLORS["gold"]
        body.append("KẾT THÚC VÁN" + chr(10) + chr(10), style=f"bold {accent}")
        fin = last_finished_issue or (last.get("issue") if last else None)
        if fin is not None:
            body.append(f"KỲ {fin} vừa xong" + chr(10), style=TST_COLORS["gold"])
        room_show = killed_room or last_killed_room
        if room_show:
            body.append(f"SÁT THỦ  {ROOM_NAMES.get(room_show, room_show)}" + chr(10) + chr(10), style="bold white")
        elif last_finished_label:
            body.append(f"SÁT THỦ  {last_finished_label}" + chr(10) + chr(10), style="bold white")
        body.append("SẴN SÀNG VÁN SAU", style=TST_COLORS["muted"])
        title = "02  KẾT QUẢ VÁN"
    else:
        accent, title = TST_COLORS["gold"], "02  CHỜ ENGINE"
        body.append("ĐANG CHỜ DỮ LIỆU THOÁT HIỂM" + chr(10) + chr(10), style=f"bold {accent}")
        body.append(str(_ws_status or "Kết nối...") + chr(10), style=TST_COLORS["muted"])
        if not USER_ID or not SECRET_KEY:
            body.append(chr(10) + "⚠ Chưa chọn tài khoản game", style=TST_COLORS["ruby"])
        elif issue_id:
            body.append(chr(10) + f"Kỳ: {issue_id}", style=TST_COLORS["sky"])

    return Panel(
        Align.center(body, vertical="middle"),
        title=f"[bold]{title}[/]",
        border_style=accent,
        box=box.ROUNDED,
        padding=(1, 2),
    )




def build_vth_history():
    t = Table(show_header=True, box=box.SIMPLE_HEAVY, expand=True, padding=(0, 1))
    t.add_column("KỲ", style=TST_COLORS["muted"], no_wrap=True)
    t.add_column("PHÒNG")
    t.add_column("CƯỢC", justify="right", style=TST_COLORS["gold"])
    t.add_column("KẾT QUẢ", justify="right")
    rows = list(bet_history)[-6:]
    if not rows:
        t.add_row("—", "Chưa có", "0.00", Text("CHỜ", style=TST_COLORS["muted"]))
    for b in rows:
        res = str(b.get("result", "Đang") or "Đang")
        if res.lower() in ("đang", "dang", "pending", "wait", "chờ", "cho"):
            res_show, rc = "CHỜ", TST_COLORS["gold"]
        elif res == "Thắng":
            res_show, rc = "THẮNG", TST_COLORS["emerald"]
        elif res == "Thua":
            res_show, rc = "THUA", TST_COLORS["ruby"]
        else:
            res_show, rc = res.upper(), TST_COLORS["gold"]
        room_id = b.get("room")
        room_label = ROOM_NAMES.get(room_id, str(room_id))
        t.add_row(
            str(b.get("issue", "-")),
            str(room_label),
            f"{float(b.get('amount', 0) or 0):.2f}",
            Text(res_show, style=f"bold {rc}"),
        )
    return Panel(t, title="[bold]03  SỔ CƯỢC[/]", border_style=TST_COLORS["onyx"], box=box.ROUNDED, padding=(0, 1))


def build_vth_stats():
    """Ma trận phòng + session — giống PERFORMANCE MATRIX CDTD."""
    try:
        risk_rows = compute_vth_room_risk()
    except Exception:
        risk_rows = []
    risk_by = {r["id"]: r for r in risk_rows}

    t = Table(show_header=True, box=box.SIMPLE, expand=True, padding=(0, 1))
    t.add_column("STT", width=3, style=TST_COLORS["muted"])
    t.add_column("PHÒNG")
    t.add_column("NGƯỜI", justify="right")
    t.add_column("CƯỢC", justify="right", style=TST_COLORS["gold"])
    t.add_column("KILL", justify="right")
    t.add_column("P(THẮNG)", justify="right")
    t.add_column("P(THUA)", justify="right")
    t.add_column("MỨC", justify="center")
    for r in ROOM_ORDER:
        rr = risk_by.get(r) or {}
        risk_pct = float(rr.get("risk_pct", 50.0) or 50.0)
        win_p = float(rr.get("win_prob", 100.0 - risk_pct) or (100.0 - risk_pct))
        lose_p = float(rr.get("lose_prob", 100.0 - win_p) or (100.0 - win_p))
        lvl, col = _risk_level(risk_pct)
        wcol = TST_COLORS["emerald"] if win_p >= 55 else TST_COLORS["neon_orange"] if win_p >= 40 else TST_COLORS["ruby"]
        lcol = TST_COLORS["ruby"] if lose_p >= 55 else TST_COLORS["neon_orange"] if lose_p >= 40 else TST_COLORS["emerald"]
        t.add_row(
            str(r),
            ROOM_NAMES.get(r, str(r)),
            str(room_state[r].get("players", 0)),
            f"{float(room_state[r].get('bet', 0) or 0):.0f}",
            str(room_stats[r].get("kills", 0)),
            Text(f"{win_p:.0f}%", style=f"bold {wcol}"),
            Text(f"{lose_p:.0f}%", style=f"bold {lcol}"),
            Text(lvl, style=f"bold {col}"),
        )

    pnl = cumulative_profit if cumulative_profit is not None else 0.0
    wins = sum(1 for b in bet_history if b.get("result") == "Thắng")
    losses = sum(1 for b in bet_history if b.get("result") == "Thua")
    summary = Text()
    summary.append("PHIÊN" + chr(10), style=f"bold {TST_COLORS['emerald']}")
    summary.append(f"VÁN      {wins + losses}" + chr(10))
    summary.append(f"THẮNG    {wins}" + chr(10), style=TST_COLORS["emerald"])
    summary.append(f"THUA     {losses}" + chr(10), style=TST_COLORS["ruby"])
    summary.append(f"MAX T    {max_win_streak}" + chr(10))
    summary.append(f"MAX B    {max_lose_streak}" + chr(10))
    summary.append(
        f"P&L      {pnl:+.4f} BUILD" + chr(10),
        style=f"bold {TST_COLORS['emerald'] if pnl >= 0 else TST_COLORS['ruby']}",
    )
    try:
        if stop_when_profit_reached and profit_target:
            summary.append(f"CHỐT LÃI ≥ {float(profit_target):.2f}" + chr(10), style=TST_COLORS["emerald"])
        if stop_when_loss_reached and stop_loss_target:
            summary.append(f"CẮT LỖ  ≤ {float(stop_loss_target):.2f}" + chr(10), style=TST_COLORS["ruby"])
        if float(random_skip_pct or 0) > 0:
            summary.append(f"SKIP RD  {float(random_skip_pct):.0f}%" + chr(10), style=TST_COLORS["muted"])
    except Exception:
        pass
    try:
        summary.append(chr(10))
        summary.append(format_ai_stats_text(str(settings.get("algo", "")), ""))
    except Exception:
        pass
    if risk_rows:
        safest = min(risk_rows, key=lambda x: x["risk_pct"])
        riskiest = max(risk_rows, key=lambda x: x["risk_pct"])
        best_win = max(risk_rows, key=lambda x: float(x.get("win_prob", 0) or 0))
        summary.append(chr(10) + "XÁC SUẤT THẮNG / THUA" + chr(10), style=f"bold {TST_COLORS['gold']}")
        summary.append(
            f"CAO NHẤT {best_win.get('name', '?')}  P≈{float(best_win.get('win_prob', 0)):.0f}%" + chr(10),
            style=TST_COLORS["emerald"],
        )
        summary.append(
            f"AN TOÀN  {safest.get('name', '?')}  risk {safest['risk_pct']:.0f}%" + chr(10),
            style=TST_COLORS["emerald"],
        )
        summary.append(
            f"NGUY HIỂM {riskiest.get('name', '?')}  risk {riskiest['risk_pct']:.0f}%" + chr(10),
            style=TST_COLORS["ruby"],
        )
        try:
            sel = predicted_rooms if predicted_rooms else ([predicted_room] if predicted_room else [])
            if sel:
                ps = [float((risk_by.get(rid) or {}).get("win_prob", 50)) for rid in sel]
                if len(ps) == 1:
                    summary.append(f"MỤC TIÊU P≈{ps[0]:.0f}%", style=TST_COLORS["sapphire"])
                else:
                    p_all = 1.0
                    for p in ps:
                        p_all *= p / 100.0
                    summary.append(f"MULTI P(sống)≈{p_all*100:.0f}%", style=TST_COLORS["sapphire"])
        except Exception:
            pass

    return Panel(
        Columns(
            [
                Panel(t, border_style=TST_COLORS["onyx"], box=box.SIMPLE),
                Panel(summary, border_style=TST_COLORS["gold"], box=box.SIMPLE, padding=(1, 2)),
            ],
            equal=True,
            expand=True,
        ),
        title="[bold]04  XÁC SUẤT THẮNG · THUA[/]",
        border_style=TST_COLORS["sky"],
        box=box.ROUNDED,
        padding=(0, 1),
    )


def vth_generate_layout():
    """VTH NOVA — bố cục 4 tầng giống CDTD (Rich Live)."""
    root = Table.grid(expand=True, pad_edge=False)
    root.add_row(build_vth_header())
    root.add_row(build_vth_marquee())

    middle = Table.grid(expand=True, pad_edge=False)
    middle.add_column(ratio=60)
    middle.add_column(ratio=40)
    middle.add_row(build_vth_rooms(), build_vth_mid())
    root.add_row(middle)

    root.add_row(build_vth_history())
    root.add_row(build_vth_stats())
    return root




def start_game_flow():
    """Khởi động WebSocket + monitor + UI live Vua Thoát Hiểm."""
    global stop_flag, current_bet, starting_balance, cumulative_profit
    global issue_id, killed_room, predicted_room, prediction_locked, ui_state
    global last_msg_ts, _ws_status, analysis_start_ts, round_index
    global win_streak, lose_streak, max_win_streak, max_lose_streak
    stop_flag = False
    current_bet = base_bet
    starting_balance = None
    cumulative_profit = None
    # reset session state
    issue_id = None
    killed_room = None
    predicted_room = None
    prediction_locked = False
    ui_state = "WAITING"
    analysis_start_ts = None
    last_msg_ts = time.time()
    _ws_status = "⏳ Đang kết nối..."
    win_streak = 0
    lose_streak = 0
    for r in ROOM_ORDER:
        room_state[r] = {"players": 0, "bet": 0}
    if check_key_expiry_and_stop("bắt đầu VTH"):
        console.print("[bold red]Key đã hết hạn. Gia hạn key rồi chạy lại.[/]")
        Prompt.ask("Nhấn Enter để quay lại", default="")
        return
    if not USER_ID or not SECRET_KEY:
        console.print("[bold red]⚠ Chưa chọn tài khoản game (USER_ID / SECRET_KEY). Vào menu Thêm/Chọn tài khoản trước.[/]")
        Prompt.ask("Nhấn Enter để quay lại", default="")
        return

    console.clear()
    brand = Text()
    brand.append(" ♛ ", style=f"bold {TST_COLORS['bg_deep']} on {TST_COLORS['emerald']}")
    brand.append("  VUA THOÁT HIỂM  ", style=f"bold {TST_COLORS['platinum']}")
    brand.append("·  KHỞI ĐỘNG", style=TST_COLORS["muted"])
    console.print(Panel(Align.center(brand), border_style=TST_COLORS["emerald"], box=box.HEAVY_HEAD, padding=(0, 1)))
    console.print(Align.center(Text(
        f"AI: {SELECTION_MODES.get(settings.get('algo'), settings.get('algo'))}  ·  Cược: {base_bet}  ·  x{multiplier}",
        style=TST_COLORS["muted"]
    )))
    console.print()

    # Fetch balance lần đầu
    try:
        fetch_balances_3games(retries=2, timeout=8)
    except Exception:
        pass

    ws_thread = threading.Thread(target=start_ws, daemon=True)
    ws_thread.start()
    mon_thread = threading.Thread(target=monitor_loop, daemon=True)
    mon_thread.start()

    try:
        with Live(vth_generate_layout(), refresh_per_second=4, console=console, screen=True) as live:
            while not stop_flag:
                live.update(vth_generate_layout())
                time.sleep(0.5)
    except KeyboardInterrupt:
        stop_flag = True
    finally:
        stop_flag = True
        try:
            wsobj = _ws.get("ws")
            if wsobj:
                wsobj.close()
        except Exception:
            pass

    console.clear()
    final_pnl = cumulative_profit or 0
    pnl_col = TST_COLORS["emerald"] if final_pnl >= 0 else TST_COLORS["ruby"]
    end_grid = Table.grid(expand=True, padding=(0, 2))
    end_grid.add_column(ratio=1); end_grid.add_column(ratio=1); end_grid.add_column(ratio=1); end_grid.add_column(ratio=1)
    end_grid.add_row(
        Panel(Text.assemble(("MAX W\n", TST_COLORS["muted"]), (str(max_win_streak),  f"bold {TST_COLORS['emerald']}")), border_style=TST_COLORS["emerald"], box=box.SIMPLE, padding=(0,1)),
        Panel(Text.assemble(("MAX L\n", TST_COLORS["muted"]), (str(max_lose_streak), f"bold {TST_COLORS['ruby']}")),    border_style=TST_COLORS["ruby"],    box=box.SIMPLE, padding=(0,1)),
        Panel(Text.assemble(("W/L\n",   TST_COLORS["muted"]), (f"{win_streak}/{lose_streak}", f"bold {TST_COLORS['gold']}")), border_style=TST_COLORS["gold"], box=box.SIMPLE, padding=(0,1)),
        Panel(Text.assemble(("P&L\n",   TST_COLORS["muted"]), (f"{final_pnl:+.4f}", f"bold {pnl_col}")), border_style=pnl_col, box=box.SIMPLE, padding=(0,1)),
    )
    console.print(Panel(
        Group(
            Align.center(Text("♛  KẾT THÚC PHIÊN  ♛", style=f"bold {TST_COLORS['gold']}")),
            Rule(style=TST_COLORS["accent_line"]),
            end_grid,
        ),
        border_style=TST_COLORS["gold"],
        box=box.HEAVY_HEAD,
        padding=(0, 1),
    ))
    console.print("\n[dim]Nhấn Enter để quay lại menu...[/]")
    input()



# ================== PHÂN TÍCH RỦI RO VTH / CDTD ==================

def _risk_bar(pct: float, width: int = 12) -> str:
    pct = max(0.0, min(100.0, float(pct)))
    filled = int(round(pct / 100.0 * width))
    return "█" * filled + "░" * (width - filled)


def _risk_level(pct: float) -> tuple:
    if pct >= 70:
        return "CAO", TST_COLORS["ruby"]
    if pct >= 40:
        return "TB", TST_COLORS["neon_orange"]
    return "THẤP", TST_COLORS["emerald"]


def compute_vth_room_risk() -> List[Dict[str, Any]]:
    """
    Rủi ro VTH v4 — Bayesian + realtime + volatility.

    P_base   = Dirichlet-smoothed kill rate (ổn định khi ít mẫu)
    P_ewma   = EWMA kill gần (20 ván, decay 0.86)
    P_markov = Markov 1 + 2 bậc
    crowd/money/gap/streak như v3
    vol      = độ biến thiên kill gần → tăng risk (không ổn định)

    conf cao → tin base; conf thấp → tin realtime.
    """
    rows = []
    n_rooms = max(1, len(ROOM_ORDER))
    max_players = max((int(room_state[r].get("players", 0) or 0) for r in ROOM_ORDER), default=0) or 1
    max_bet = max((float(room_state[r].get("bet", 0) or 0) for r in ROOM_ORDER), default=0.0) or 1.0
    log = list(game_kill_log) if game_kill_log else []
    n_log = len(log)

    # EWMA 20
    ewma = {r: 0.0 for r in ROOM_ORDER}
    if log:
        window = log[-20:]
        decay = 0.86
        w = 1.0
        wsum = 0.0
        for k in reversed(window):
            if k in ewma:
                ewma[k] += w
            wsum += w
            w *= decay
        if wsum > 0:
            for r in ewma:
                ewma[r] /= wsum

    # Markov 1 + 2
    markov = {r: 1.0 / n_rooms for r in ROOM_ORDER}
    if len(log) >= 2:
        last = log[-1]
        cnt = defaultdict(float)
        tot = 0.0
        for a, b in zip(log, log[1:]):
            if a == last:
                cnt[b] += 1.0
                tot += 1.0
        alpha = 0.85
        for r in ROOM_ORDER:
            markov[r] = (cnt.get(r, 0.0) + alpha) / (tot + alpha * n_rooms)
    if len(log) >= 3:
        a2, b2 = log[-2], log[-1]
        cnt2 = defaultdict(float)
        tot2 = 0.0
        for i in range(len(log) - 2):
            if log[i] == a2 and log[i + 1] == b2:
                cnt2[log[i + 2]] += 1.0
                tot2 += 1.0
        if tot2 > 0:
            alpha2 = 0.55
            for r in ROOM_ORDER:
                p2 = (cnt2.get(r, 0.0) + alpha2) / (tot2 + alpha2 * n_rooms)
                markov[r] = 0.60 * markov[r] + 0.40 * p2

    recent8 = log[-8:] if log else []
    streak_map = {r: recent8.count(r) for r in ROOM_ORDER}

    # volatility: biến thiên tần suất kill theo nửa log
    vol_map = {r: 0.0 for r in ROOM_ORDER}
    if n_log >= 8:
        half = n_log // 2
        first, second = log[:half], log[half:]
        for r in ROOM_ORDER:
            f1 = first.count(r) / float(len(first) or 1)
            f2 = second.count(r) / float(len(second) or 1)
            vol_map[r] = abs(f2 - f1)

    for r in ROOM_ORDER:
        kills = int(room_stats[r].get("kills", 0) or 0)
        survives = int(room_stats[r].get("survives", 0) or 0)
        samples = kills + survives
        k_log = log.count(r) if log else 0

        # Dirichlet prior alpha=1 (đều)
        if samples >= 2:
            p_base = (kills + 1.0) / (samples + float(n_rooms))
            conf = min(1.0, samples / 24.0)
        elif n_log >= 4:
            p_base = (k_log + 1.0) / (n_log + float(n_rooms))
            conf = min(1.0, n_log / 20.0) * 0.75
        else:
            p_base = 1.0 / n_rooms
            conf = 0.12

        p_ewma = float(ewma.get(r, 0.0))
        p_mk = float(markov.get(r, 1.0 / n_rooms))
        players = int(room_state[r].get("players", 0) or 0)
        bet = float(room_state[r].get("bet", 0) or 0)
        crowd = players / max_players
        money = bet / max_bet

        gap = float(n_rooms + 3)
        if log:
            for i in range(len(log) - 1, -1, -1):
                if log[i] == r:
                    gap = float(len(log) - 1 - i)
                    break
        gap_factor = min(1.0, gap / 12.0)
        streak_n = min(1.0, float(streak_map.get(r, 0)) / 3.0)
        vol = float(vol_map.get(r, 0.0))

        w_base = 0.24 + 0.26 * conf
        w_ewma = 0.18 + 0.10 * (1.0 - conf)
        w_mk = 0.14 + 0.06 * (1.0 - conf)
        w_crowd = 0.09
        w_money = 0.07
        w_gap = 0.09
        w_streak = 0.08
        w_vol = 0.05
        wsum = w_base + w_ewma + w_mk + w_crowd + w_money + w_gap + w_streak + w_vol
        p_lose = (
            w_base * p_base
            + w_ewma * p_ewma
            + w_mk * p_mk
            + w_crowd * crowd
            + w_money * money
            + w_gap * gap_factor * (1.0 / n_rooms) * 2.2
            + w_streak * streak_n * 0.48
            + w_vol * min(1.0, vol * 4.0) * 0.35
        ) / max(wsum, 1e-6)
        p_lose = max(0.02, min(0.95, p_lose))
        p_win = 1.0 - p_lose

        rows.append({
            "id": r,
            "name": ROOM_NAMES.get(r, f"Phòng {r}"),
            "kills": kills,
            "survives": survives,
            "samples": samples,
            "kill_rate": p_base,
            "players": players,
            "bet": bet,
            "risk_pct": p_lose * 100.0,
            "win_prob": p_win * 100.0,
            "lose_prob": p_lose * 100.0,
            "ewma": p_ewma,
            "markov": p_mk,
            "gap": gap,
            "streak": streak_map.get(r, 0),
            "volatility": vol,
            "confidence": conf,
            "last_kill_round": room_stats[r].get("last_kill_round"),
        })

    if rows:
        mx = max(x["risk_pct"] for x in rows) or 1.0
        mn = min(x["risk_pct"] for x in rows)
        span = max(1e-6, mx - mn)
        for x in rows:
            rel = (x["risk_pct"] - mn) / span * 100.0
            x["risk_pct"] = 0.78 * x["risk_pct"] + 0.22 * rel
            x["risk_pct"] = max(1.0, min(99.0, x["risk_pct"]))
            x["lose_prob"] = x["risk_pct"]
            x["win_prob"] = 100.0 - x["risk_pct"]
        s = sum(float(x["win_prob"]) for x in rows) or 1.0
        for x in rows:
            x["win_prob_rel"] = float(x["win_prob"]) / s * 100.0
    rows.sort(key=lambda x: x["risk_pct"], reverse=True)
    return rows


def compute_cdtd_nv_risk(data_top10=None, data_top100=None) -> List[Dict[str, Any]]:
    """
    Rủi ro CDTD v4 — not_winner + Bayesian form + streak + volatility.

    risk% = P(NV về nhất) * 100  (cược not_winner thua khi NV thắng đua)
    P_race blend: form100, form10, EWMA, Markov, streak, cold mean-revert, volatility.
    """
    if data_top10 is None:
        data_top10 = top_10_cdtd()
    if data_top100 is None:
        data_top100 = top_100_cdtd()

    win100 = [0] * 6
    if data_top100 and len(data_top100) > 1 and data_top100[1]:
        try:
            win100 = [int(x or 0) for x in data_top100[1][:6]]
            while len(win100) < 6:
                win100.append(0)
        except Exception:
            win100 = [0] * 6
    total100 = sum(win100) or 1

    recent = []
    if data_top10 and len(data_top10) > 1 and data_top10[1]:
        try:
            recent = [int(x) for x in data_top10[1] if x is not None]
        except Exception:
            recent = list(data_top10[1])
    n_recent = len(recent)

    ewma = {i: 0.0 for i in range(1, 7)}
    if recent:
        decay = 0.82
        w = 1.0
        wsum = 0.0
        for nv in reversed(recent[-16:]):
            try:
                nv = int(nv)
            except Exception:
                continue
            if nv in ewma:
                ewma[nv] += w
            wsum += w
            w *= decay
        if wsum > 0:
            for i in ewma:
                ewma[i] /= wsum

    markov = {i: 1.0 / 6 for i in range(1, 7)}
    if len(recent) >= 2:
        last = recent[-1]
        cnt = defaultdict(float)
        tot = 0.0
        for a, b in zip(recent, recent[1:]):
            if a == last:
                cnt[b] += 1.0
                tot += 1.0
        alpha = 0.6
        for i in range(1, 7):
            markov[i] = (cnt.get(i, 0.0) + alpha) / (tot + alpha * 6)

    # volatility half-split
    vol = {i: 0.0 for i in range(1, 7)}
    if n_recent >= 8:
        half = n_recent // 2
        f, s = recent[:half], recent[half:]
        for i in range(1, 7):
            vol[i] = abs(s.count(i) / float(len(s) or 1) - f.count(i) / float(len(f) or 1))

    last_winner = recent[-1] if recent else None
    rows = []
    for i in range(1, 7):
        w100 = win100[i - 1]
        # Dirichlet smooth
        p100 = (w100 + 0.9) / (total100 + 0.9 * 6)
        wins10 = sum(1 for x in recent if x == i)
        p10 = (wins10 + 0.5) / (n_recent + 0.5 * 6) if n_recent > 0 else p100
        p_ew = float(ewma.get(i, 0.0))
        p_mk = float(markov.get(i, 1.0 / 6))

        streak = 0
        for x in reversed(recent):
            if x == i:
                streak += 1
            else:
                break
        streak_n = min(1.0, streak / 3.0)
        cold_gap = max(0.0, (1.0 / 6) - p_ew)
        conf = min(1.0, n_recent / 14.0) if n_recent else 0.18

        w100_ = 0.30
        w10_ = 0.12 + 0.10 * conf
        wew = 0.16 + 0.08 * conf
        wmk = 0.12 + 0.05 * (1.0 - conf)
        wst = 0.14
        wmr = 0.08
        wvo = 0.05
        wsum = w100_ + w10_ + wew + wmk + wst + wmr + wvo
        p_race = (
            w100_ * p100
            + w10_ * p10
            + wew * p_ew
            + wmk * p_mk
            + wst * streak_n * 0.58
            + wmr * (p100 + cold_gap * 0.45)
            + wvo * min(1.0, vol.get(i, 0) * 5.0) * 0.30
        ) / max(wsum, 1e-6)
        p_race = max(0.02, min(0.72, p_race))
        p_bet_win = 1.0 - p_race
        p_bet_lose = p_race

        rows.append({
            "id": i,
            "name": NV.get(i, f"NV{i}"),
            "icon": NV_ICONS.get(i, "◆"),
            "wins_100": w100,
            "rate_100": p100,
            "wins_10": wins10,
            "rate_10": p10,
            "form10": p_ew,
            "markov": p_mk,
            "streak": streak,
            "volatility": vol.get(i, 0),
            "p_win": p_bet_win,
            "win_prob": p_bet_win * 100.0,
            "lose_prob": p_bet_lose * 100.0,
            "risk_pct": p_bet_lose * 100.0,
            "race_win_prob": p_race * 100.0,
            "confidence": conf,
            "last_winner": last_winner == i,
        })

    if rows:
        mx = max(x["risk_pct"] for x in rows) or 1.0
        mn = min(x["risk_pct"] for x in rows)
        span = max(1e-6, mx - mn)
        for x in rows:
            rel = (x["risk_pct"] - mn) / span * 100.0
            x["risk_pct"] = 0.82 * x["risk_pct"] + 0.18 * rel
            x["risk_pct"] = max(1.0, min(99.0, x["risk_pct"]))
            x["lose_prob"] = x["risk_pct"]
            x["win_prob"] = 100.0 - x["risk_pct"]
        s = sum(float(x["win_prob"]) for x in rows) or 1.0
        for x in rows:
            x["win_prob_rel"] = float(x["win_prob"]) / s * 100.0
    rows.sort(key=lambda x: x["risk_pct"], reverse=True)
    return rows



def compute_cdtd_nv_risk(data_top10=None, data_top100=None) -> List[Dict[str, Any]]:
    """
    Rủi ro CDTD v3 — cược bet_group=not_winner.

    Ý nghĩa:
      P_race   = P(NV về nhất)  — từ top100 + top10 + EWMA + Markov + streak
      P(thắng cược not_winner) = 1 - P_race
      risk%    = P_race * 100   (NV hay về nhất = rủi ro cao khi not_winner)

    Trọng số:
      • form100      32%
      • form10/EWMA  28%
      • Markov       15%
      • streak hot   15%
      • mean-revert  10%  (quá lạnh hơi tăng P_race nhẹ)
    """
    if data_top10 is None:
        data_top10 = top_10_cdtd()
    if data_top100 is None:
        data_top100 = top_100_cdtd()

    win100 = [0] * 6
    if data_top100 and len(data_top100) > 1 and data_top100[1]:
        try:
            win100 = [int(x or 0) for x in data_top100[1][:6]]
            while len(win100) < 6:
                win100.append(0)
        except Exception:
            win100 = [0] * 6
    total100 = sum(win100) or 1

    recent = []
    if data_top10 and len(data_top10) > 1 and data_top10[1]:
        try:
            recent = [int(x) for x in data_top10[1] if x is not None]
        except Exception:
            recent = list(data_top10[1])
    n_recent = len(recent)

    # EWMA form ngắn
    ewma = {i: 0.0 for i in range(1, 7)}
    if recent:
        decay = 0.80
        w = 1.0
        wsum = 0.0
        for nv in reversed(recent[-14:]):
            try:
                nv = int(nv)
            except Exception:
                continue
            if nv in ewma:
                ewma[nv] += w
            wsum += w
            w *= decay
        if wsum > 0:
            for i in ewma:
                ewma[i] /= wsum

    # Markov next
    markov = {i: 1.0 / 6 for i in range(1, 7)}
    if len(recent) >= 2:
        last = recent[-1]
        cnt = defaultdict(float)
        tot = 0.0
        for a, b in zip(recent, recent[1:]):
            if a == last:
                cnt[b] += 1.0
                tot += 1.0
        alpha = 0.55
        for i in range(1, 7):
            markov[i] = (cnt.get(i, 0.0) + alpha) / (tot + alpha * 6)

    last_winner = recent[-1] if recent else None
    rows = []
    for i in range(1, 7):
        w100 = win100[i - 1]
        p100 = (w100 / float(total100)) if total100 > 0 else (1.0 / 6)
        wins10 = sum(1 for x in recent if x == i)
        p10 = (wins10 / float(n_recent)) if n_recent > 0 else p100
        p_ew = float(ewma.get(i, 0.0))
        p_mk = float(markov.get(i, 1.0 / 6))

        streak = 0
        for x in reversed(recent):
            if x == i:
                streak += 1
            else:
                break
        streak_n = min(1.0, streak / 3.0)

        # mean-revert: quá lạnh so với 1/6 → hơi tăng P_race
        cold_gap = max(0.0, (1.0 / 6) - p_ew)
        # conf theo mẫu gần
        conf = min(1.0, n_recent / 12.0) if n_recent else 0.2

        w100_ = 0.32
        w10_ = 0.12 + 0.10 * conf
        wew = 0.16 + 0.08 * conf
        wmk = 0.12 + 0.05 * (1.0 - conf)
        wst = 0.15
        wmr = 0.08
        wsum = w100_ + w10_ + wew + wmk + wst + wmr
        p_race = (
            w100_ * p100
            + w10_ * p10
            + wew * p_ew
            + wmk * p_mk
            + wst * streak_n * 0.55  # hot streak → dễ về nhất tiếp
            + wmr * (p100 + cold_gap * 0.5)
        ) / max(wsum, 1e-6)
        p_race = max(0.02, min(0.70, p_race))

        # not_winner: thắng cược khi NV KHÔNG về nhất
        p_bet_win = 1.0 - p_race
        p_bet_lose = p_race

        rows.append({
            "id": i,
            "name": NV.get(i, f"NV{i}"),
            "icon": NV_ICONS.get(i, "◆"),
            "wins_100": w100,
            "rate_100": p100,
            "wins_10": wins10,
            "rate_10": p10,
            "form10": p_ew,
            "markov": p_mk,
            "streak": streak,
            "p_win": p_bet_win,  # xác suất thắng CƯỢC not_winner
            "win_prob": p_bet_win * 100.0,
            "lose_prob": p_bet_lose * 100.0,
            "risk_pct": p_bet_lose * 100.0,  # risk = P(NV về nhất)
            "race_win_prob": p_race * 100.0,
            "confidence": conf,
            "last_winner": last_winner == i,
        })

    # relative nhẹ để UI tách hạng
    if rows:
        mx = max(x["risk_pct"] for x in rows) or 1.0
        mn = min(x["risk_pct"] for x in rows)
        span = max(1e-6, mx - mn)
        for x in rows:
            rel = (x["risk_pct"] - mn) / span * 100.0
            x["risk_pct"] = 0.80 * x["risk_pct"] + 0.20 * rel
            x["risk_pct"] = max(1.0, min(99.0, x["risk_pct"]))
            x["lose_prob"] = x["risk_pct"]
            x["win_prob"] = 100.0 - x["risk_pct"]
        s = sum(float(x["win_prob"]) for x in rows) or 1.0
        for x in rows:
            x["win_prob_rel"] = float(x["win_prob"]) / s * 100.0
    rows.sort(key=lambda x: x["risk_pct"], reverse=True)
    return rows



def display_vth_risk_table(rows: List[Dict[str, Any]]) -> None:
    t = Table(
        title=f"[bold {TST_COLORS['emerald']}]♛ RỦI RO PHÒNG — VUA THOÁT HIỂM[/]",
        box=box.SIMPLE_HEAVY,
        expand=True,
        padding=(0, 1),
    )
    t.add_column("#", width=3, style=TST_COLORS["muted"])
    t.add_column("PHÒNG", style=f"bold {TST_COLORS['platinum']}")
    t.add_column("KILL", justify="right")
    t.add_column("SỐNG", justify="right")
    t.add_column("PLAYERS", justify="right")
    t.add_column("BET", justify="right")
    t.add_column("RỦI RO", justify="left")
    t.add_column("MỨC", justify="center")
    for i, r in enumerate(rows, 1):
        lvl, col = _risk_level(r["risk_pct"])
        bar = _risk_bar(r["risk_pct"])
        t.add_row(
            str(i),
            r["name"],
            str(r["kills"]),
            str(r["survives"]),
            str(r["players"]),
            f"{r['bet']:.0f}",
            Text(f"{bar} {r['risk_pct']:.0f}%", style=col),
            Text(lvl, style=f"bold {col}"),
        )
    console.print(t)
    if rows:
        safest = min(rows, key=lambda x: x["risk_pct"])
        riskiest = max(rows, key=lambda x: x["risk_pct"])
        tip = Text()
        tip.append("AN TOÀN NHẤT  ", style=TST_COLORS["muted"])
        tip.append(f"{safest['name']} ({safest['risk_pct']:.0f}%)", style=f"bold {TST_COLORS['emerald']}")
        tip.append("    │    ", style=TST_COLORS["accent_line"])
        tip.append("NGUY HIỂM NHẤT  ", style=TST_COLORS["muted"])
        tip.append(f"{riskiest['name']} ({riskiest['risk_pct']:.0f}%)", style=f"bold {TST_COLORS['ruby']}")
        console.print(Panel(Align.center(tip), border_style=TST_COLORS["accent_line"], box=box.SIMPLE, padding=(0, 1)))
        if all(r["samples"] == 0 for r in rows):
            console.print(Panel(
                Text(
                    "⚠ Chưa có lịch sử kill trong session.\n"
                    "Chạy VTH một lúc rồi mở lại menu này để số liệu chính xác hơn.\n"
                    "Điểm hiện tại dựa trên players/bet realtime (nếu có).",
                    style=TST_COLORS["neon_orange"],
                ),
                border_style=TST_COLORS["neon_orange"],
                box=box.ROUNDED,
                title="[bold]Gợi ý[/]",
            ))


def display_cdtd_risk_table(rows: List[Dict[str, Any]]) -> None:
    t = Table(
        title=f"[bold {TST_COLORS['neon_blue']}]▶▶ RỦI RO NHÂN VẬT — CHẠY ĐUA TỐC ĐỘ[/]",
        box=box.SIMPLE_HEAVY,
        expand=True,
        padding=(0, 1),
    )
    t.add_column("#", width=3, style=TST_COLORS["muted"])
    t.add_column("NHÂN VẬT", style=f"bold {TST_COLORS['platinum']}")
    t.add_column("THẮNG/100", justify="right")
    t.add_column("%100", justify="right")
    t.add_column("THẮNG/10", justify="right")
    t.add_column("%10", justify="right")
    t.add_column("RỦI RO CƯỢC", justify="left")
    t.add_column("MỨC", justify="center")
    for i, r in enumerate(rows, 1):
        lvl, col = _risk_level(r["risk_pct"])
        bar = _risk_bar(r["risk_pct"])
        name = f"{r['icon']} {r['name']}"
        if r.get("last_winner"):
            name += " ← vừa thắng"
        t.add_row(
            str(i),
            name,
            str(r["wins_100"]),
            f"{r['rate_100']*100:.0f}%",
            str(r["wins_10"]),
            f"{r['rate_10']*100:.0f}%",
            Text(f"{bar} {r['risk_pct']:.0f}%", style=col),
            Text(lvl, style=f"bold {col}"),
        )
    console.print(t)
    if rows:
        safest = min(rows, key=lambda x: x["risk_pct"])
        riskiest = max(rows, key=lambda x: x["risk_pct"])
        tip = Text()
        tip.append("NÊN CƯỢC  ", style=TST_COLORS["muted"])
        tip.append(f"{safest['icon']} {safest['name']} (risk {safest['risk_pct']:.0f}%)", style=f"bold {TST_COLORS['emerald']}")
        tip.append("    │    ", style=TST_COLORS["accent_line"])
        tip.append("TRÁNH  ", style=TST_COLORS["muted"])
        tip.append(f"{riskiest['icon']} {riskiest['name']} (risk {riskiest['risk_pct']:.0f}%)", style=f"bold {TST_COLORS['ruby']}")
        console.print(Panel(Align.center(tip), border_style=TST_COLORS["accent_line"], box=box.SIMPLE, padding=(0, 1)))


def risk_analysis_vth() -> None:
    console.clear()
    brand = Text()
    brand.append(" ♛ ", style=f"bold {TST_COLORS['bg_deep']} on {TST_COLORS['emerald']}")
    brand.append("  RỦI RO PHÒNG VTH  ", style=f"bold {TST_COLORS['platinum']}")
    brand.append("·  RISK MATRIX", style=TST_COLORS["muted"])
    console.print(Panel(Align.center(brand), border_style=TST_COLORS["emerald"], box=box.HEAVY_HEAD, padding=(0, 1)))
    console.print(Align.center(Text("Cao = phòng dễ bị sát thủ chọn  ·  Thấp = an toàn hơn", style=TST_COLORS["muted"])))
    console.print()
    with console.status(f"[bold {TST_COLORS['gold']}]Đang tính rủi ro phòng...[/]", spinner="dots"):
        rows = compute_vth_room_risk()
        time.sleep(0.35)
    display_vth_risk_table(rows)
    console.print()
    console.print(Text("Công thức: kill_rate×45% + đông người×20% + tiền cược×15% + gần đây bị kill×20%", style=TST_COLORS["muted"]))
    input("\n[dim]Nhấn Enter để quay lại...[/dim]")


def risk_analysis_cdtd() -> None:
    console.clear()
    brand = Text()
    brand.append(" ▶▶ ", style=f"bold {TST_COLORS['bg_deep']} on {TST_COLORS['neon_blue']}")
    brand.append("  RỦI RO NHÂN VẬT CDTD  ", style=f"bold {TST_COLORS['platinum']}")
    brand.append("·  RISK MATRIX", style=TST_COLORS["muted"])
    console.print(Panel(Align.center(brand), border_style=TST_COLORS["neon_blue"], box=box.HEAVY_HEAD, padding=(0, 1)))
    console.print(Align.center(Text("Cao = cược NV này dễ thua  ·  Thấp = form tốt, nên cân nhắc", style=TST_COLORS["muted"])))
    console.print()
    try:
        data = load_data_cdtd()
        setup_cdtd_headers(data)
    except Exception as e:
        console.print(f"[red]Không tải được tài khoản CDTD: {e}[/red]")
        input("\n[dim]Enter...[/dim]")
        return
    with console.status(f"[bold {TST_COLORS['gold']}]Đang tải top 10 / top 100...[/]", spinner="dots"):
        top10 = top_10_cdtd()
        top100 = top_100_cdtd()
        rows = compute_cdtd_nv_risk(top10, top100)
        time.sleep(0.3)
    display_cdtd_risk_table(rows)
    console.print()
    console.print(Text("Công thức: risk ≈ 100% − (win100×55% + form10×45%)  ·  +8% nếu vừa thắng", style=TST_COLORS["muted"]))
    input("\n[dim]Nhấn Enter để quay lại...[/dim]")


def risk_analysis_menu() -> None:
    """Menu chính: phân tích rủi ro phòng VTH & nhân vật CDTD."""
    while True:
        console.clear()
        brand = Text()
        brand.append(" ◈ ", style=f"bold {TST_COLORS['bg_deep']} on {TST_COLORS['neon_orange']}")
        brand.append("  PHÂN TÍCH RỦI RO  ", style=f"bold {TST_COLORS['platinum']}")
        brand.append("·  VTH / CDTD", style=TST_COLORS["muted"])
        console.print(Panel(Align.center(brand), border_style=TST_COLORS["neon_orange"], box=box.HEAVY_HEAD, padding=(0, 1)))
        console.print()
        t = Table(show_header=False, box=box.SIMPLE, expand=True, padding=(0, 1))
        t.add_column(width=4)
        t.add_column()
        t.add_column()
        t.add_row(
            Text(" 1 ", style=f"bold {TST_COLORS['bg_deep']} on {TST_COLORS['emerald']}"),
            Text(" ♛  VTH — Rủi ro phòng", style=f"bold {TST_COLORS['platinum']}"),
            Text("8 phòng · kill / players / bet", style=TST_COLORS["muted"]),
        )
        t.add_row(
            Text(" 2 ", style=f"bold {TST_COLORS['bg_deep']} on {TST_COLORS['neon_blue']}"),
            Text(" ▶▶ CDTD — Rủi ro nhân vật", style=f"bold {TST_COLORS['platinum']}"),
            Text("6 NV · win rate 10/100", style=TST_COLORS["muted"]),
        )
        t.add_row(
            Text(" q ", style=f"bold {TST_COLORS['bg_deep']} on {TST_COLORS['muted']}"),
            Text(" Quay lại menu chính", style=TST_COLORS["muted"]),
            Text(""),
        )
        console.print(Panel(t, border_style=TST_COLORS["neon_orange"], box=box.HEAVY_HEAD, padding=(0, 1)))
        choice = Prompt.ask(
            f"[bold {TST_COLORS['gold']}] ♛  CHỌN[/bold {TST_COLORS['gold']}]",
            choices=["1", "2", "q"],
            default="q",
        )
        if choice == "1":
            risk_analysis_vth()
        elif choice == "2":
            risk_analysis_cdtd()
        else:
            break



# ================== ADMIN MENU (ẨN) ==================

def supabase_list_keys(limit: int = 50) -> list:
    """Lấy danh sách key từ Supabase."""
    try:
        url = f"{SUPABASE_URL}/rest/v1/keys?select=*&order=created_at.desc&limit={limit}"
        r = requests.get(url, headers=supabase_headers(), timeout=15)
        if r.status_code == 200:
            return r.json() if isinstance(r.json(), list) else []
        # fallback không có created_at
        url2 = f"{SUPABASE_URL}/rest/v1/keys?select=*&limit={limit}"
        r2 = requests.get(url2, headers=supabase_headers(), timeout=15)
        if r2.status_code == 200:
            return r2.json() if isinstance(r2.json(), list) else []
        return []
    except Exception as e:
        safe_console_print(f"[red]Lỗi list keys: {e}[/red]")
        return []


def supabase_deactivate_key(key_code: str) -> tuple:
    try:
        url = f"{SUPABASE_URL}/rest/v1/keys?key_code=eq.{key_code}"
        r = requests.patch(url, headers=supabase_headers(prefer="return=representation"),
                           json={"status": "inactive"}, timeout=15)
        if r.status_code in (200, 204):
            return True, "Đã vô hiệu hóa key"
        return False, f"HTTP {r.status_code}: {r.text[:200]}"
    except Exception as e:
        return False, str(e)


def admin_create_key_interactive(key_type: str = "free") -> None:
    """Admin tạo key FREE hoặc VIP trên Supabase."""
    prefix = "VIP_" if key_type == "vip" else "FREE_"
    default_ai = 42 if key_type == "vip" else 10
    default_hours = 720 if key_type == "vip" else 13  # VIP mặc định 30 ngày

    console.print(f"\n[bold]Tạo KEY {key_type.upper()}[/bold]")
    custom = Prompt.ask("Key code (Enter = tự sinh)", default="")
    if custom:
        key_code = custom.strip().upper()
    else:
        key_code = prefix + secrets.token_hex(5).upper()

    max_ai = IntPrompt.ask("max_ai", default=default_ai)
    hours = IntPrompt.ask("Thời hạn (giờ)", default=default_hours)
    note = Prompt.ask("Ghi chú", default=f"Admin tạo {key_type}")

    ok, result = create_key_on_supabase(
        key_code=key_code,
        key_type=key_type,
        max_ai=max_ai,
        duration_hours=hours,
        note=note,
    )
    if ok:
        console.print(Panel(
            Text.assemble(
                ("✅ TẠO KEY THÀNH CÔNG\n\n", "bold green"),
                ("KEY: ", "white"), (f"{key_code}\n", f"bold {TST_COLORS['gold']}"),
                ("Loại: ", "white"), (f"{key_type.upper()}\n", "bold cyan"),
                ("AI: ", "white"), (f"{max_ai}\n", "bold"),
                ("Hạn: ", "white"), (f"{hours} giờ\n", "bold"),
            ),
            border_style=TST_COLORS["emerald"], box=box.ROUNDED
        ))
    else:
        console.print(f"[red]❌ {result}[/red]")


def admin_menu() -> None:
    """Đã tắt — không còn menu admin."""
    console.print("[yellow]Menu admin đã bị vô hiệu hóa.[/yellow]")
    time.sleep(1.2)
    return
    while True:
        console.clear()
        console.print(Panel(
            Align.center(Text.assemble(
                ("🔐 ADMIN PANEL\n", f"bold {TST_COLORS['ruby']}"),
                ("Kết nối Supabase · Quản lý key & user", "dim"),
            )),
            border_style=TST_COLORS["ruby"],
            box=box.ROUNDED
        ))
        console.print("[1] 📋 Xem toàn bộ key (Supabase)")
        console.print("[2] 🔑 Thêm KEY FREE (10 AI, Lotto 5 AI)")
        console.print("[3] 👑 Thêm KEY VIP (toàn bộ AI)")
        console.print("[4] ❌ Vô hiệu hóa key")
        console.print("[5] 👥 Xem user local (xu/key)")
        console.print("[6] ☁️  Xem user Supabase (user_id + IP)")
        console.print("[7] 🔓 Gỡ BAN user (Supabase)")
        console.print("[q] 🔙 Thoát admin")
        console.print()
        choice = Prompt.ask(">>", choices=["1", "2", "3", "4", "5", "6", "7", "q"], default="q")

        if choice == "q":
            break
        elif choice == "1":
            keys = supabase_list_keys(100)
            if not keys:
                console.print("[yellow]Không có key hoặc không đọc được Supabase.[/yellow]")
            else:
                t = Table(box=box.ROUNDED, border_style=TST_COLORS["gold"], title=f"Keys ({len(keys)})")
                t.add_column("key_code", style=TST_COLORS["neon_blue"])
                t.add_column("type")
                t.add_column("status")
                t.add_column("max_ai", justify="right")
                t.add_column("expires")
                t.add_column("used", justify="right")
                t.add_column("note", style="dim")
                for k in keys:
                    t.add_row(
                        str(k.get("key_code", ""))[:24],
                        str(k.get("key_type", "")),
                        str(k.get("status", "")),
                        str(k.get("max_ai", "")),
                        str(k.get("expires_at", ""))[:19],
                        str(k.get("used_count", 0)),
                        str(k.get("note", ""))[:20],
                    )
                console.print(t)
            input("\n[dim]Enter...[/dim]")
        elif choice == "2":
            admin_create_key_interactive("free")
            input("\n[dim]Enter...[/dim]")
        elif choice == "3":
            admin_create_key_interactive("vip")
            input("\n[dim]Enter...[/dim]")
        elif choice == "4":
            kc = Prompt.ask("Nhập key_code cần khóa").strip()
            if kc:
                ok, msg = supabase_deactivate_key(kc)
                console.print(f"[green]✅ {msg}[/green]" if ok else f"[red]❌ {msg}[/red]")
            input("\n[dim]Enter...[/dim]")
        elif choice == "5":
            data = load_user_data_secure()
            if not data:
                console.print("[yellow]Chưa có user local.[/yellow]")
            else:
                t = Table(box=box.ROUNDED, border_style=TST_COLORS["sapphire"], title=f"Users ({len(data)})")
                t.add_column("ID")
                t.add_column("IP")
                t.add_column("Xu", justify="right")
                t.add_column("Keys", justify="right")
                t.add_column("Tạo lúc", style="dim")
                for uid, ud in data.items():
                    t.add_row(
                        str(uid)[:12],
                        str(ud.get("ip", ""))[:18],
                        f"{ud.get('coins', 0):.1f}",
                        str(len(ud.get("keys", []) or [])),
                        str(ud.get("created_at", ""))[:19],
                    )
                console.print(t)
            input("\n[dim]Enter...[/dim]")
        elif choice == "6":
            users = supabase_list_users(100)
            if not users:
                console.print("[yellow]Không có user trên Supabase hoặc bảng users chưa tạo.[/yellow]")
                console.print("[dim]Chạy SQL tạo bảng users trong Supabase SQL Editor (xem comment trong code).[/dim]")
            else:
                t = Table(box=box.ROUNDED, border_style=TST_COLORS["emerald"], title=f"Supabase Users ({len(users)})")
                t.add_column("user_id", style=TST_COLORS["neon_blue"])
                t.add_column("IP")
                t.add_column("Xu", justify="right")
                t.add_column("Keys", justify="right")
                t.add_column("status")
                t.add_column("updated", style="dim")
                for u in users:
                    t.add_row(
                        str(u.get("user_id", ""))[:14],
                        str(u.get("ip", ""))[:18],
                        f"{float(u.get('coins', 0) or 0):.1f}",
                        str(u.get("keys_count", 0)),
                        str(u.get("status", "")),
                        str(u.get("updated_at", "") or u.get("last_seen_at", ""))[:19],
                    )
                console.print(t)
            input("\n[dim]Enter...[/dim]")
        elif choice == "7":
            uid = Prompt.ask("Nhập user_id cần gỡ ban").strip()
            if uid:
                ok, msg = supabase_unban_user(uid)
                console.print(f"[green]✅ {msg}[/green]" if ok else f"[red]❌ {msg}[/red]")
            input("\n[dim]Enter...[/dim]")


# ================== MAIN MENU ==================

def build_main_menu():
    global _in_menu, _ws_status, _secure_mode
    _in_menu = True
    console.clear()

    # ── HEADER BRAND ─────────────────────────────────────────────
    print_tst_logo()
    console.print()

    # ── MODULE GRID ───────────────────────────────────────────────
    # Left column: game modules. Right column: tools.
    LEFT = [
        ("1", "♛", "VUA THOÁT HIỂM", "42 AI  ·  chiến lược tự động", TST_COLORS["emerald"]),
        ("2", "▶▶", "CHẠY ĐUA TỐC ĐỘ", "42 AI  ·  dự đoán đua",       TST_COLORS["neon_blue"]),
        ("3", "★", "WINHASH LOTTO",   "Logic FREE / VIP",             TST_COLORS["gold"]),
    ]
    RIGHT = [
        ("4", "◉", "THÊM TÀI KHOẢN", "quản lý tài khoản",   TST_COLORS["sapphire"]),
        ("5", "✕", "XÓA TÀI KHOẢN",  "quản lý tài khoản",   TST_COLORS["ruby"]),
        ("6", "◈", "CẤU HÌNH",       "cấu hình workspace",  TST_COLORS["lavender"]),
        ("7", "▲", "CHẠY CẤU HÌNH",  "chạy config đã lưu",  TST_COLORS["neon_orange"]),
        ("8", "▦", "PHÂN TÍCH RỦI RO", "phòng VTH · NV CDTD", TST_COLORS["neon_orange"]),
    ]

    def _module_row(no, icon, name, desc, accent):
        num_txt = Text(f" {no} ", style=f"bold {TST_COLORS['bg_deep']} on {accent}")
        ico_txt = Text(f" {icon} ", style=f"bold {accent}")
        name_txt = Text(name, style=f"bold {TST_COLORS['platinum']}")
        desc_txt = Text(f"  {desc}", style=TST_COLORS["muted"])
        line = Text()
        line.append_text(num_txt)
        line.append_text(ico_txt)
        line.append_text(name_txt)
        line.append_text(desc_txt)
        return line

    # Game modules in a highlighted panel
    game_table = Table(show_header=False, box=box.SIMPLE, expand=True, padding=(0, 1))
    game_table.add_column(width=3)
    game_table.add_column(width=3)
    game_table.add_column()
    game_table.add_column()
    for no, icon, name, desc, accent in LEFT:
        game_table.add_row(
            Text(f" {no} ", style=f"bold {TST_COLORS['bg_deep']} on {accent}"),
            Text(f" {icon} ", style=f"bold {accent}"),
            Text(name, style=f"bold {TST_COLORS['platinum']}"),
            Text(desc, style=TST_COLORS["muted"]),
        )
    game_panel = Panel(
        game_table,
        title=f"[bold {TST_COLORS['emerald']}]  ▶  MODULE GAME  [/]",
        border_style=TST_COLORS["emerald"],
        box=box.HEAVY_HEAD,
        padding=(0, 1),
    )

    tool_table = Table(show_header=False, box=box.SIMPLE, expand=True, padding=(0, 1))
    tool_table.add_column(width=3)
    tool_table.add_column(width=3)
    tool_table.add_column()
    tool_table.add_column()
    for no, icon, name, desc, accent in RIGHT:
        tool_table.add_row(
            Text(f" {no} ", style=f"bold {TST_COLORS['bg_deep']} on {accent}"),
            Text(f" {icon} ", style=f"bold {accent}"),
            Text(name, style=f"bold {TST_COLORS['platinum']}"),
            Text(desc, style=TST_COLORS["muted"]),
        )
    tool_panel = Panel(
        tool_table,
        title=f"[bold {TST_COLORS['sapphire']}]  ◈  CÔNG CỤ  [/]",
        border_style=TST_COLORS["sapphire"],
        box=box.HEAVY_HEAD,
        padding=(0, 1),
    )

    grid = Table.grid(expand=True, padding=(0, 1))
    grid.add_column(ratio=45)
    grid.add_column(ratio=55)
    grid.add_row(game_panel, tool_panel)
    console.print(grid)

    # ── STATUS STRIP ──────────────────────────────────────────────
    key_color = TST_COLORS["gold"] if _key_type == "vip" else TST_COLORS["diamond"]
    status = Text()
    status.append("  ◉ ", style=TST_COLORS["muted"])
    status.append(f"QUYỀN ", style=TST_COLORS["muted"])
    status.append(f"{str(_key_type).upper()} ", style=f"bold {key_color}")
    status.append("  │  ", style=TST_COLORS["accent_line"])
    status.append("HẠN ", style=TST_COLORS["muted"])
    exp = _key_expiry_info or "—"
    # rút gọn nếu quá dài cho status
    exp_short = exp if len(exp) <= 42 else (exp[:40] + "…")
    status.append(f"{exp_short} ", style=f"bold {TST_COLORS['gold']}")
    status.append("  │  ", style=TST_COLORS["accent_line"])
    status.append(f"WS ", style=TST_COLORS["muted"])
    status.append(f"{_ws_status} ", style=TST_COLORS["diamond"])
    status.append("  │  ", style=TST_COLORS["accent_line"])
    status.append(f"IP ", style=TST_COLORS["muted"])
    status.append(f"{_ip_info.get('public_ip','N/A')}  ", style=TST_COLORS["sky"])
    console.print(Panel(Align.center(status), border_style=TST_COLORS["accent_line"], box=box.SIMPLE, padding=(0,0)))

    raw = _ui_prompt("CHỌN MODULE  [1-9 / q]").lower()
    if raw == ADMIN_SECRET_CODE or raw == "9826665":
        try: admin_menu()
        except NameError: console.print("[red]Admin menu chưa sẵn sàng.[/red]"); time.sleep(1)
        return build_main_menu()
    return raw if raw in ["1","2","3","4","5","6","7","8","9","q"] else "q"


def load_accounts() -> list:
    acc_file = Path("accounts.json")
    if not acc_file.exists():
        return []
    try:
        return json.loads(acc_file.read_text())
    except (json.JSONDecodeError, IOError):
        return []

def save_accounts(accounts: list):
    acc_file = Path("accounts.json")
    with acc_file.open("w", encoding="utf-8") as f:
        json.dump(accounts, f, indent=2)

def add_new_account(accounts: list) -> bool:
    console.clear()
    header = Panel(Align.center(Text.assemble((f"{ICONS['user']} ", f"bold {TST_COLORS['gold']}"), ("THÊM TÀI KHOẢN", f"bold {TST_COLORS['neon_blue']}"), (f" {ICONS['user']}", f"bold {TST_COLORS['gold']}"))), border_style=TST_COLORS["gold"], box=box.ROUNDED)
    console.print(header)
    console.print()
    console.print(Panel(Text.assemble((f"{ICONS['info']} ", "bold yellow"), ("Dán link trò chơi vào bên dưới", "white"), ("\n", ""), ("Ví dụ: ", "dim"), ("https://xworld.info/?userId=12345&secretKey=abc123", "dim cyan")), border_style=TST_COLORS["sapphire"], box=box.ROUNDED))
    console.print()
    link = Prompt.ask(f"[bold {TST_COLORS['gold']}]>> Dán link[/bold {TST_COLORS['gold']}]")
    if not link:
        console.print("[yellow]Đã hủy.[/yellow]")
        time.sleep(1)
        return False
    try:
        parsed = urlparse(link)
        params = parse_qs(parsed.query)
        if 'userId' in params and 'secretKey' in params:
            uid = int(params.get('userId')[0])
            skey = params.get('secretKey', [None])[0]
            if any(acc.get('userId') == uid for acc in accounts):
                console.print(f"[yellow]⚠️ Tài khoản userId: {uid} đã tồn tại.[/yellow]")
                time.sleep(2)
                return False
            accounts.append({"userId": uid, "secretKey": skey})
            save_accounts(accounts)
            console.print(Panel(Align.center(Text.assemble((f"{ICONS['check']} ", "bold green"), (f"Đã thêm tài khoản: ", "bold white"), (f"{uid}", f"bold {TST_COLORS['gold']}"))), border_style=TST_COLORS["emerald"], box=box.ROUNDED))
            time.sleep(2)
            return True
        else:
            console.print("[red]❌ Link không hợp lệ! Thiếu 'userId' hoặc 'secretKey'.[/red]")
            time.sleep(2)
            return False
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        time.sleep(2)
        return False

def delete_account(accounts: list) -> bool:
    console.clear()
    header = Panel(Align.center(Text.assemble((f"{ICONS['fire']} ", f"bold {TST_COLORS['ruby']}"), ("XÓA TÀI KHOẢN", f"bold {TST_COLORS['neon_blue']}"), (f" {ICONS['fire']}", f"bold {TST_COLORS['ruby']}"))), border_style=TST_COLORS["ruby"], box=box.ROUNDED)
    console.print(header)
    console.print()
    if not accounts:
        console.print("[yellow]Không có tài khoản để xóa.[/yellow]")
        time.sleep(2)
        return False
    table = Table(box=box.ROUNDED, border_style=TST_COLORS["ruby"])
    table.add_column("STT", style=f"bold {TST_COLORS['gold']}", width=6)
    table.add_column("User ID", style=TST_COLORS["neon_blue"])
    for i, acc in enumerate(accounts, 1):
        table.add_row(str(i), str(acc.get('userId')))
    console.print(table)
    console.print()
    choice_str = Prompt.ask(f"[bold {TST_COLORS['ruby']}]>> Chọn tài khoản cần xóa[/bold {TST_COLORS['ruby']}]", default="")
    if not choice_str:
        console.print("[yellow]Đã hủy.[/yellow]")
        time.sleep(1)
        return False
    try:
        choice_idx = int(choice_str) - 1
        if 0 <= choice_idx < len(accounts):
            removed_acc = accounts.pop(choice_idx)
            save_accounts(accounts)
            console.print(f"[green]✅ Đã xóa tài khoản: {removed_acc.get('userId')}[/green]")
            time.sleep(2)
            return True
        else:
            console.print("[red]❌ Lựa chọn không hợp lệ.[/red]")
            time.sleep(1)
            return False
    except ValueError:
        console.print("[red]❌ Nhập liệu không hợp lệ.[/red]")
        time.sleep(1)
        return False

def select_account_premium() -> bool:
    global USER_ID, SECRET_KEY
    while True:
        console.clear()
        header = Panel(Align.center(Text.assemble((f"{ICONS['user']} ", f"bold {TST_COLORS['gold']}"), ("CHỌN TÀI KHOẢN", f"bold {TST_COLORS['neon_blue']}"), (f" {ICONS['user']}", f"bold {TST_COLORS['gold']}"))), border_style=TST_COLORS["gold"], box=box.ROUNDED)
        console.print(header)
        console.print()
        accounts = load_accounts()
        if not accounts:
            console.print(Panel(Align.center(Text.assemble((f"{ICONS['warning']} ", "bold yellow"), ("Không có tài khoản nào!", "bold white"), ("\n", ""), ("Vui lòng dùng tùy chọn [5] để thêm tài khoản", "dim"))), border_style=TST_COLORS["ruby"], box=box.ROUNDED))
            time.sleep(2)
            return False
        table = Table(title=f"[bold {TST_COLORS['gold']}]📋 DANH SÁCH TÀI KHOẢN[/bold {TST_COLORS['gold']}]", box=box.ROUNDED, border_style=TST_COLORS["sapphire"])
        table.add_column("STT", style=f"bold {TST_COLORS['gold']}", width=6)
        table.add_column("User ID", style=TST_COLORS["neon_blue"])
        table.add_column("Số dư", justify="right")
        table.add_column("Trạng thái", justify="center")
        with console.status(f"[bold {TST_COLORS['neon_blue']}]🔍 Đang kiểm tra số dư...[/bold {TST_COLORS['neon_blue']}]", spinner="dots") as status:
            for i, acc in enumerate(accounts, 1):
                uid = acc.get('userId')
                skey = acc.get('secretKey')
                status.update(f"[{TST_COLORS['neon_blue']}]Đang kiểm tra tài khoản {uid}...[/{TST_COLORS['neon_blue']}]")
                build, _, _ = fetch_balances_3games(uid=uid, secret=skey)
                if build is not None:
                    balance_str = f"[bold {TST_COLORS['emerald']}]{build:,.4f}[/bold {TST_COLORS['emerald']}]"
                    status_str = f"[{TST_COLORS['emerald']}]✅ Trực tuyến[/{TST_COLORS['emerald']}]"
                else:
                    balance_str = f"[{TST_COLORS['ruby']}]❌ Error[/{TST_COLORS['ruby']}]"
                    status_str = f"[{TST_COLORS['ruby']}]❌ Ngoại tuyến[/{TST_COLORS['ruby']}]"
                table.add_row(str(i), str(uid), balance_str, status_str)
        console.print(table)
        console.print()
        choices = [str(i) for i in range(1, len(accounts) + 1)]
        choice_str = Prompt.ask(f"[bold {TST_COLORS['gold']}]>> Chọn số tài khoản[/bold {TST_COLORS['gold']}]", choices=choices, default="")
        if not choice_str:
            return False
        try:
            choice_idx = int(choice_str) - 1
            if 0 <= choice_idx < len(accounts):
                selected_account = accounts[choice_idx]
                USER_ID = selected_account['userId']
                SECRET_KEY = selected_account['secretKey']
                console.print(Panel(Align.center(Text.assemble((f"{ICONS['check']} ", "bold green"), (f"Đã chọn tài khoản: ", "bold white"), (f"{USER_ID}", f"bold {TST_COLORS['gold']}"))), border_style=TST_COLORS["emerald"], box=box.ROUNDED))
                time.sleep(1.5)
                return True
            else:
                console.print("[red]❌ Lựa chọn không hợp lệ![/red]")
                time.sleep(1)
                return False
        except ValueError:
            console.print("[red]❌ Nhập liệu không hợp lệ![/red]")
            time.sleep(1)
            return False

# ================== MAIN PROGRAM ==================

def main_vth():
    global _in_menu, _is_authenticated, _user_key, _key_type

    force_clear()          # Xóa sạch màn hình ngay khi bắt đầu
    migrate_old_data()

    # Chỉ kiểm tra ban theo IP (đã bỏ rule cùng máy / fingerprint)
    try:
        ok_dev, msg_dev, _uid_dev = check_device_ip_integrity()
        if not ok_dev:
            safe_console_print(f"[bold red]{msg_dev}[/bold red]")
            input("\n[dim]Enter để thoát...[/dim]")
            return
    except Exception as e:
        safe_console_print(f"[yellow]⚠️ Không kiểm tra được IP/ban: {e}[/yellow]")

    while not _is_authenticated:
        force_clear()      # Xóa sạch trước mỗi lần hiện menu đăng nhập
        success, key, key_type = show_auth_choice_menu()
        if success:
            _is_authenticated = True
            _user_key = key
            _key_type = key_type
            break

        console.print()
        retry = Prompt.ask(
            "[bold yellow]Bạn có muốn thử lại không? (y/n)[/bold yellow]",
            choices=['y', 'n'],
            default='y'
        )
        if retry.lower() == 'n':
            console.print("[red]👋 Tạm biệt![/red]")
            return

    force_clear()          # Xóa sạch trước khi hiện logo + menu chính
    key_col = TST_COLORS["gold"] if _key_type == "vip" else TST_COLORS["diamond"]
    print_tst_logo()
    console.print()
    info_strip = Text()
    info_strip.append(" ♛ ACCESS ", style=f"bold {TST_COLORS['muted']}")
    info_strip.append(f"{_key_type.upper()}  ", style=f"bold {key_col}")
    info_strip.append("│  KEY ", style=TST_COLORS["accent_line"])
    info_strip.append(f"{_user_key}  ", style=TST_COLORS["muted"])
    info_strip.append("│  HẠN ", style=TST_COLORS["accent_line"])
    info_strip.append(f"{_key_expiry_info or '—'}  ", style=f"bold {TST_COLORS['gold']}")
    if _key_type == "free":
        info_strip.append("│  FREE LOGIC · VIP LOGIC", style=TST_COLORS["muted"])
    info_strip.append("│  @tst-tool88", style=TST_COLORS["accent_line"])
    console.print(Panel(Align.center(info_strip), border_style=key_col, box=box.SIMPLE, padding=(0,0)))
    console.print()
    time.sleep(1)

    while True:
        global stop_flag
        stop_flag = False
        choice = build_main_menu()

        if choice == '1':
            force_clear()
            if select_account_premium():
                if prompt_settings():
                    start_game_flow()

        elif choice == '2':
            main_cdtd_v3()

        elif choice == '3':
            console.print("[yellow]⚠️ Chức năng WINHASH LOTTO chưa có hàm xử lý trong file hiện tại.[/yellow]")
            console.print("[dim]FREE key: tối đa 5 AI Lotto | VIP: full AI[/dim]")
            time.sleep(2)

        elif choice == '4':
            accounts = load_accounts()
            add_new_account(accounts)

        elif choice == '5':
            accounts = load_accounts()
            delete_account(accounts)

        elif choice == '6':
            force_clear()
            if prompt_settings():
                save_strategy_config()
            time.sleep(2)

        elif choice == '7':
            force_clear()
            if select_account_premium():
                if load_strategy_config():
                    start_game_flow()
                else:
                    time.sleep(2)

        elif choice == '8':
            try:
                risk_analysis_menu()
            except Exception as e:
                console.print(f"[red]❌ Lỗi phân tích rủi ro: {e}[/red]")
                time.sleep(2)

        elif choice == 'q':
            stop_heartbeat()
            stop_flag = True
            console.print(Panel(
                Group(
                    Align.center(Text("♛  ♛  ♛", style=f"bold {TST_COLORS['gold']}")),
                    Align.center(Text("THANK YOU FOR USING  TST-TOOL", style=f"bold {TST_COLORS['platinum']}")),
                    Align.center(Text("◈ Support: @tst-tool88  ·  Version 3.0  ◈", style=TST_COLORS["muted"])),
                ),
                border_style=TST_COLORS["gold"],
                box=box.HEAVY_HEAD,
                padding=(1, 2),
            ))
            break


if __name__ == "__main__":
    try:
        main_vth()
    except KeyboardInterrupt:
        stop_flag = True
        stop_heartbeat()
        console.print(Panel(
            Align.center(Text.assemble(
                ("♛  ", f"bold {TST_COLORS['gold']}"),
                ("TST-TOOL  —  ĐÃ DỪNG  ", f"bold {TST_COLORS['platinum']}"),
                ("♛", f"bold {TST_COLORS['gold']}"),
            )),
            border_style=TST_COLORS["accent_line"],
            box=box.SIMPLE,
            padding=(0, 2),
        ))
        sys.exit(0)