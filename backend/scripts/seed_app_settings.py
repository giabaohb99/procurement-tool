# -*- coding: utf-8 -*-
"""Nạp giá trị `.env` đang chạy xuống bảng `tab_setting` (bao-CR-429).

Chạy: docker compose exec -T api python -m scripts.seed_app_settings [--dry-run] [--force]

VÌ SAO CẦN: sau khi dời cấu hình sang màn Cấu hình hệ thống, ô nào chưa có dòng
dưới DB sẽ hiện TRỐNG — trong khi hệ thống vẫn chạy bằng giá trị `.env` phía sau.
Ô trống đọc như "chưa cấu hình", và người xem rất dễ kết luận nhầm là đường đồng
bộ đang tắt rồi đi bật lại thứ vốn đang bật. Nạp một lần cho màn hình nói đúng
những gì hệ thống đang dùng.

KHÔNG ĐÈ: mặc định chỉ điền khóa CHƯA có dòng (hoặc dòng rỗng). DB là nguồn sự
thật của cấu hình — giống luật của `seed_prod.py` — nên thứ người dùng đã tự đặt
trên màn hình không bị `.env` cũ kéo ngược lại. `--force` mới ghi đè, và chỉ nên
dùng khi biết rõ đang muốn kéo ngược.

CHẠY RIÊNG TỪNG MÔI TRƯỜNG: bản mã của khóa bí mật suy từ `JWT_SECRET` của chính
môi trường đó (xem `app_settings._fernet`). Chép dòng bí mật từ local sang dev là
ra bản mã giải không nổi, `_decrypt` nuốt lỗi trả chuỗi rỗng, và hệ thống lặng lẽ
rơi về `.env`. Phải chạy script này TRONG từng môi trường, đọc `.env` của nó.
"""
import argparse
import sys

import app.core.all_models  # noqa: F401 — nạp toàn bộ model để mapper resolve quan hệ
from app.core import app_settings
from app.core.config import settings as env
from app.core.database import SessionLocal
from app.modules.setting.model import Setting
from app.modules.setting.service import _upsert

#  Người chạy script là "hệ thống", không mượn danh tài khoản nào.
SYSTEM_USER_ID = 0


def env_text(key: str) -> str:
    """Giá trị `.env` của một khóa, đưa về đúng dạng chuỗi sẽ nằm dưới DB."""
    if key in app_settings.SECRETS:
        return str(getattr(env, app_settings.SECRETS[key], "") or "")
    kind, attr = app_settings.REGISTRY[key]
    raw = getattr(env, attr, None)
    if raw is None:
        return ""
    if kind == "bool":
        return "true" if raw else "false"
    if kind == "int":
        return str(int(raw))
    return str(raw)


def mask(key: str, text: str) -> str:
    """Bí mật chỉ khoe độ dài — sổ tay chạy script cũng là một chỗ rò."""
    if key in app_settings.SECRETS:
        return f"<{len(text)} ký tự>"
    return text


def main() -> int:
    ap = argparse.ArgumentParser(description="Nạp cấu hình từ .env xuống tab_setting")
    ap.add_argument("--dry-run", action="store_true", help="chỉ in, không ghi")
    ap.add_argument("--force", action="store_true", help="ghi đè cả khóa đã có giá trị")
    args = ap.parse_args()

    db = SessionLocal()
    written: list[str] = []
    kept: list[str] = []
    empty: list[str] = []
    try:
        rows = {s.skey: s.svalue for s in db.query(Setting).all()}
        for key in list(app_settings.REGISTRY) + list(app_settings.SECRETS):
            text = env_text(key)
            has_row = bool(rows.get(key))
            if has_row and not args.force:
                kept.append(key)
                continue
            if not text:
                #  Cả DB lẫn `.env` đều trống thì đúng là CHƯA cấu hình — ghi
                #  chuỗi rỗng xuống chẳng thêm thông tin gì, chỉ thêm một dòng.
                empty.append(key)
                continue
            stored = app_settings.encrypt(text) if key in app_settings.SECRETS else text
            if args.dry_run:
                written.append(key)
            elif _upsert(db, key, stored, SYSTEM_USER_ID, masked=key in app_settings.SECRETS):
                written.append(key)
            print(f"  [ghi ] {key} = {mask(key, text)}")
        if args.dry_run:
            db.rollback()
        else:
            db.commit()
            app_settings.refresh()
    finally:
        db.close()

    print("")
    print(f"Đã ghi   : {len(written)} khóa" + (" (dry-run, chưa ghi thật)" if args.dry_run else ""))
    print(f"Giữ nguyên: {len(kept)} khóa đã có giá trị dưới DB" + ("" if args.force else " (dùng --force để đè)"))
    print(f"Bỏ qua   : {len(empty)} khóa cả DB lẫn .env đều trống")
    if kept:
        print("  giữ nguyên: " + ", ".join(kept))
    if empty:
        print("  bỏ qua   : " + ", ".join(empty))
    return 0


if __name__ == "__main__":
    sys.exit(main())
