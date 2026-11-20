"""Bộ đếm cho `ledger_sync_service.sync_history_ledger` và script nạp lại sổ giá (duoc-CR-784, phase 02).

Tách riêng để `ledger_sync_service` giữ dưới 200 dòng: chỉ đếm, không đụng DB.
"""
from datetime import date

from .ledger_sync_service import parse_ledger_date


def new_stats() -> dict:
    return {"inserted": 0, "deleted_orphans": 0, "deleted_covered_po_lines": 0, "skipped_bad_row": 0, "skipped_bad_date": 0,
            "future_date": 0, "zero_price": 0, "foreign_currency": 0, "missing_po_item": 0, "ledger_rows": 0}


def count_history_row(stats: dict, ph, rate, item_id) -> None:
    """Cộng các số đếm "đáng chú ý" của một dòng lịch sử (ngày tương lai Q5, giá 0, ngoại tệ, thiếu dòng ĐMH)."""
    if not float(ph.price or 0):
        stats["zero_price"] += 1
    if ph.po_item_id and item_id is None:
        stats["missing_po_item"] += 1
    if rate and float(rate) not in (0.0, 1.0):
        stats["foreign_currency"] += 1
    d = parse_ledger_date(ph.order_date)
    if d is not None and d > date.today():
        stats["future_date"] += 1
