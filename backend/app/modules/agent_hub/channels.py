"""Lớp «kênh» của bot (ai-CR-111, lộ trình Z-1 ở `doc/agent-hub/12-de-xuat-tom-tat-nhom.md`).

Một lõi xử lý tin dùng chung cho nhiều kênh nhắn tin. Mã chat mang TIỀN TỐ kênh để mọi chỗ trong lõi (sổ tin, liên kết
ERP, sổ ghi nhớ, chuông, nhóm) không phải biết tin tới từ đâu:

  - Telegram: giữ nguyên số id cũ, KHÔNG thêm tiền tố — dữ liệu đã có trên dev/prod không phải đổi.
  - Zalo (bot chính thức, Zalo Bot Platform): `zl:<id Zalo>`.

Gửi đi: `telegram.send` / `send_document` / `send_chat_action` / `edit_text` … tự rẽ sang `zalo` khi mã chat mang tiền
tố `zl:` — nên hơn hai trăm chỗ gọi trong lõi không phải sửa. Nhận về: `zalo.normalize` đổi update Zalo thành đúng hình
dạng tin Telegram mà `service.handle_message` đang đọc.
"""
from __future__ import annotations

import hashlib

ZALO = "zalo"
TELEGRAM = "telegram"
ZALO_PREFIX = "zl:"
#  Tệp Zalo gửi kèm (ảnh, tin thoại) là một đường tải, không có file_id kiểu Telegram. Gói đường đó vào «file_id» có
#  tiền tố riêng để các chỗ tải tệp trong lõi đi chung một hàm `telegram.download_file`.
ZALO_FILE_PREFIX = "zlurl:"
#  Cột chat_id ở các bảng của bot là String(50).
CHAT_ID_MAX = 50


def is_zalo(chat_id) -> bool:
    return str(chat_id or "").startswith(ZALO_PREFIX)


def channel_of(chat_id) -> str:
    return ZALO if is_zalo(chat_id) else TELEGRAM


def zalo_chat(raw_id) -> str:
    """Mã chat trong lõi của một id Zalo. Rỗng nếu id rỗng hoặc dài quá cột."""
    raw = str(raw_id or "").strip()
    out = f"{ZALO_PREFIX}{raw}" if raw else ""
    return out if len(out) <= CHAT_ID_MAX else ""


def raw_id(chat_id) -> str:
    """Id gốc phía kênh (bỏ tiền tố)."""
    s = str(chat_id or "")
    return s[len(ZALO_PREFIX):] if s.startswith(ZALO_PREFIX) else s


def number_of(text) -> int:
    """Số nguyên ổn định (60 bit, vừa BIGINT) cho id dạng chuỗi của Zalo — dùng ở các cột số vốn chứa id Telegram
    (`tg_message_id`, `from_tg_id`). Cùng chuỗi luôn ra cùng số."""
    s = str(text or "")
    if not s:
        return 0
    if s.isdigit() and len(s) <= 18:
        return int(s)
    return int(hashlib.sha1(s.encode("utf-8")).hexdigest()[:15], 16)


def safe_name(chat_id) -> str:
    """Mã chat dùng được trong tên tệp (bỏ dấu «:»)."""
    return str(chat_id or "").replace(":", "_")
