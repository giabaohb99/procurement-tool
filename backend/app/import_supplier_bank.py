"""Nạp thông tin ngân hàng NCC (Số TK + Ngân hàng/CN) từ file mẫu vào tab_supplier.

Nguồn: app/seed_data/nganhangncc.txt (tab-separated: Tên TK | Số TK | Ngân hàng/CN).
Khớp NCC theo tên pháp lý (Supplier.name) — exact trước, fuzzy (difflib) sau.
Tên trùng trong file: last-wins. In log rõ từng dòng UPDATE / SKIP để duyệt.

Chạy:  cat doc/datamau/nganhangncc.txt | docker compose exec -T api python -m app.import_supplier_bank
   hoặc (đọc file trong container):  docker compose exec -T api python -m app.import_supplier_bank
"""
import os
import re
import sys
from difflib import SequenceMatcher

from app.core.database import SessionLocal
from app.modules.supplier.model import Supplier

FUZZY_THRESHOLD = 0.9


def _norm(s: str) -> str:
    """Chuẩn hoá tên để so khớp: bỏ khoảng trắng thừa, hạ chữ thường."""
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def _clean_acc(s: str) -> str:
    """Số TK: bỏ dấu nháy, xuống dòng, khoảng trắng thừa (giữ nguyên chữ số + dấu cách gọn)."""
    s = (s or "").replace('"', " ").replace("\n", " ").strip()
    return re.sub(r"\s+", " ", s)


def _read_rows() -> list[tuple[str, str, str]]:
    """Đọc dữ liệu: ưu tiên file seed_data; nếu có pipe stdin (không rỗng) thì dùng stdin."""
    raw = ""
    if not sys.stdin.isatty():
        raw = sys.stdin.read()
    if not raw.strip():
        path = "/app/app/seed_data/nganhangncc.txt"
        if not os.path.exists(path):
            path = os.path.join(os.path.dirname(__file__), "seed_data/nganhangncc.txt")
        with open(path, "r", encoding="utf-8") as f:
            raw = f.read()
    rows = []
    for ln in raw.splitlines()[1:]:  # bỏ dòng header
        if not ln.strip():
            continue
        parts = ln.split("\t")
        if len(parts) < 3:
            continue
        name, acc, bank = parts[0].strip(), _clean_acc(parts[1]), parts[2].strip()
        if name:
            rows.append((name, acc, bank))
    return rows


def _best_fuzzy(target_norm: str, candidates: dict[str, Supplier]) -> Supplier | None:
    """Tìm NCC gần đúng nhất (ratio >= ngưỡng), ưu tiên quan hệ chứa nhau."""
    best, best_score = None, 0.0
    for k, sup in candidates.items():
        if target_norm in k or k in target_norm:
            score = 0.95
        else:
            score = SequenceMatcher(None, target_norm, k).ratio()
        if score > best_score:
            best, best_score = sup, score
    return best if best_score >= FUZZY_THRESHOLD else None


def run():
    rows = _read_rows()
    db = SessionLocal()
    try:
        suppliers = db.query(Supplier).all()
        by_name = {_norm(s.name): s for s in suppliers}

        # Đồng bộ sạch: xoá TK cũ của TẤT CẢ NCC trước, sau đó chỉ nạp lại các dòng khớp
        # trong file (nguồn dữ liệu TK NCB duy nhất). Tránh sót dữ liệu khớp sai lần trước.
        for s in suppliers:
            s.bank_account_name = ""
            s.bank_account = ""
            s.bank_name = ""

        updated, skipped, fuzzy = 0, [], []
        for name, acc, bank in rows:  # last-wins: dòng sau ghi đè dòng trùng trước
            k = _norm(name)
            sup = by_name.get(k)
            kind = "EXACT"
            if not sup:
                sup = _best_fuzzy(k, by_name)
                kind = "FUZZY"
            if not sup:
                skipped.append(name)
                print(f"SKIP  (no match): {name}")
                continue
            sup.bank_account_name = name.strip()  # Tên TK thụ hưởng (cột 1 của file)
            sup.bank_account = acc
            sup.bank_name = bank
            updated += 1
            if kind == "FUZZY":
                fuzzy.append((name.strip(), sup.code, sup.name))
            print(f"{kind} {sup.code:<20} | {sup.name[:45]:<45} | {acc:<20} | {bank}")

        db.commit()
        print("-" * 60)
        print(f"Xong: cập nhật {updated} NCC ({len(fuzzy)} khớp mờ), bỏ qua {len(skipped)} dòng.")
        if fuzzy:
            print("KHỚP MỜ (fuzzy) — kiểm tra lại xem đúng NCC chưa:")
            for fname, code, sname in fuzzy:
                print(f"  - '{fname}'  ->  [{code}] {sname}")
        if skipped:
            print("Các dòng KHÔNG khớp (điền tay hoặc sửa tên trong file rồi chạy lại):")
            for s in skipped:
                print(f"  - {s}")
    finally:
        db.close()


if __name__ == "__main__":
    run()
