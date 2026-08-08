"""Đồng bộ MÃ PO cho các dòng LỊCH SỬ MUA HÀNG CŨ (`source='legacy'`).

Dòng nhập từ file Excel (`import_purchase_history_legacy`) không có Đơn mua hàng nên
`po_code`/`po_id` để trống → cột "MÃ PO" ở bảng Lịch sử mua hàng bị rỗng. Script này dò
ngược trong hệ thống xem lần mua đó có ĐMH tương ứng không rồi điền mã PO vào.

CÁCH KHỚP (1 dòng lịch sử ↔ 1 dòng hàng của ĐMH):
  bắt buộc : cùng MÃ NCC + cùng MÃ SẢN PHẨM, đơn không bị hủy
  chấm điểm: ngày đặt lệch ít nhất (ngưỡng --days, mặc định 30) → rồi tới SL đặt lệch ít nhất
  Nhiều ứng viên bằng điểm nhau → BỎ QUA và liệt kê là "mơ hồ", không đoán bừa.

Chạy TRONG container api (mặc định chạy thử, chỉ ghi khi có --apply):
    docker compose exec -T api python -m scripts.backfill_legacy_po_code
    docker compose exec -T api python -m scripts.backfill_legacy_po_code --apply
    docker compose exec -T api python -m scripts.backfill_legacy_po_code --days 7 --match-qty --apply
    docker compose exec -T api python -m scripts.backfill_legacy_po_code --clear --apply   # gỡ mã PO đã gán

Chỉ ghi `po_id` + `po_code` (và ghi vết vào `extra.linked_po_item_id`). KHÔNG đụng
`po_item_id` — cột đó unique và đang dành cho dòng `source='system'`; gán vào sẽ đụng khóa
khi dòng ĐMH đó cũng đã tự chốt lịch sử.
"""
import argparse
import csv
import json
from collections import defaultdict
from datetime import datetime

from sqlalchemy import or_

import app.core.all_models  # noqa: F401 — nạp đủ model để SQLAlchemy dựng được mapper
from app.core.database import SessionLocal
from app.modules.purchase_history.model import PurchaseHistory
from app.modules.purchase_order.model import POItem, PurchaseOrder

BATCH = 200


def _day_diff(a: str, b: str) -> int | None:
    """Số ngày lệch giữa 2 chuỗi YYYY-MM-DD; None nếu thiếu/không đọc được."""
    try:
        d1 = datetime.strptime((a or "").strip(), "%Y-%m-%d")
        d2 = datetime.strptime((b or "").strip(), "%Y-%m-%d")
    except ValueError:
        return None
    return abs((d1 - d2).days)


def _pick(h: PurchaseHistory, cands: list, max_days: int, match_qty: bool):
    """Chọn ứng viên tốt nhất. Trả (ứng_viên | None, lý_do)."""
    scored = []
    for po, it in cands:
        dd = _day_diff(po.order_date, h.order_date)
        if dd is None:
            dd = 10 ** 6            # thiếu ngày: vẫn xét nhưng luôn xếp sau ứng viên có ngày
        elif dd > max_days:
            continue
        qty_h, qty_i = float(h.qty_order or 0), float(it.qty_order or 0)
        qd = abs(qty_i - qty_h)
        if match_qty and qd > max(0.001, qty_h * 0.01):   # lệch quá 1% thì loại
            continue
        scored.append((dd, qd, po, it))
    if not scored:
        return None, "không khớp"
    scored.sort(key=lambda x: (x[0], x[1]))
    if len(scored) > 1 and scored[1][:2] == scored[0][:2]:
        return None, "mơ hồ"        # 2 đơn giống hệt điểm → không đoán bừa
    return scored[0], "khớp"


def _clear(db, apply: bool) -> None:
    rows = (db.query(PurchaseHistory)
            .filter(PurchaseHistory.source == "legacy", PurchaseHistory.po_code != "").all())
    print(f"Dòng legacy đang có mã PO: {len(rows)}")
    if apply:
        for h in rows:
            h.po_code, h.po_id = "", 0
            extra = json.loads(h.extra or "{}")
            extra.pop("linked_po_item_id", None)
            h.extra = json.dumps(extra, ensure_ascii=False)
        db.commit()
        print("Đã gỡ mã PO khỏi các dòng trên.")
    else:
        print("(chạy thử) thêm --apply để gỡ thật.")


def _delete_dup(db, apply: bool, max_days: int, match_qty: bool, csv_path: str, limit: int) -> None:
    """XÓA dòng legacy TRÙNG với lịch sử hệ thống đã tự chốt.

    Cùng một lần mua bị đếm 2 lần (1 dòng nhập từ Excel + 1 dòng hệ thống chốt khi ĐMH
    "Hoàn thành") thì bảng lịch sử hiện 2 dòng giống nhau, tham chiếu giá đọc ra sai.
    Bản hệ thống mới là bản đúng (gắn với ĐMH thật) nên giữ lại, bỏ bản legacy.
    """
    legacy = (db.query(PurchaseHistory).filter(PurchaseHistory.source == "legacy")
              .order_by(PurchaseHistory.order_date.asc()).all())
    cands: dict[tuple, list] = defaultdict(list)
    for po, it in (db.query(PurchaseOrder, POItem)
                   .join(POItem, POItem.po_id == PurchaseOrder.id)
                   .filter(PurchaseOrder.status != "cancelled").all()):
        cands[(po.supplier_code or "", it.product_code or "")].append((po, it))
    has_system = {i for (i,) in db.query(PurchaseHistory.po_item_id)
                  .filter(PurchaseHistory.source == "system",
                          PurchaseHistory.po_item_id.isnot(None)).all()}

    dup, plan = [], []
    for h in legacy:
        best, why = _pick(h, cands.get((h.supplier_code or "", h.product_code or ""), []),
                          max_days, match_qty)
        if why != "khớp":
            continue
        dd, _qd, po, it = best
        if it.id not in has_system:
            continue                      # khớp nhưng chưa có bản hệ thống → KHÔNG phải trùng
        dup.append(h)
        plan.append({"history_id": h.id, "product_code": h.product_code,
                     "supplier_code": h.supplier_code, "ngay_lich_su": h.order_date,
                     "sl": float(h.qty_order or 0), "gia": float(h.price or 0),
                     "po_code": po.code, "ngay_don": po.order_date, "lech_ngay": dd})
        if len(dup) <= limit:
            print(f"  {h.product_code:<14} {h.order_date} ≡ {po.code} (lệch {dd} ngày)")

    if csv_path and plan:
        with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=list(plan[0].keys()))
            w.writeheader()
            w.writerows(plan)
        print(f"\nĐã xuất {len(plan)} dòng nghi trùng ra {csv_path}")

    print(f"\nDòng legacy TRÙNG với lịch sử hệ thống: {len(dup)}")
    if not dup:
        return
    if not apply:
        print("(chạy thử) thêm --apply để XÓA thật. XÓA LÀ KHÔNG HOÀN TÁC — sao lưu CSDL trước.")
        return
    for h in dup:
        db.delete(h)
    db.commit()
    print(f"Đã xóa {len(dup)} dòng legacy trùng. Còn lại: "
          f"{db.query(PurchaseHistory.id).filter(PurchaseHistory.source == 'legacy').count()} dòng legacy")


def main(apply: bool, max_days: int, match_qty: bool, clear: bool, limit: int, csv_path: str,
         delete_dup: bool = False) -> None:
    db = SessionLocal()
    try:
        if clear:
            _clear(db, apply)
            return
        if delete_dup:
            _delete_dup(db, apply, max_days, match_qty, csv_path, limit)
            return

        legacy = (db.query(PurchaseHistory)
                  .filter(PurchaseHistory.source == "legacy",
                          or_(PurchaseHistory.po_code == "", PurchaseHistory.po_code.is_(None)))
                  .order_by(PurchaseHistory.order_date.asc()).all())
        total_legacy = db.query(PurchaseHistory.id).filter(PurchaseHistory.source == "legacy").count()
        print(f"Dòng lịch sử cũ (legacy): {total_legacy} | chưa có mã PO: {len(legacy)}")
        if not legacy:
            print("Không có gì để đồng bộ.")
            return

        # Nạp toàn bộ dòng ĐMH 1 lần rồi gom theo (NCC, sản phẩm) — tránh query trong vòng lặp
        cands: dict[tuple, list] = defaultdict(list)
        for po, it in (db.query(PurchaseOrder, POItem)
                       .join(POItem, POItem.po_id == PurchaseOrder.id)
                       .filter(PurchaseOrder.status != "cancelled").all()):
            cands[(po.supplier_code or "", it.product_code or "")].append((po, it))
        print(f"Dòng hàng ĐMH trong hệ thống để đối chiếu: {sum(len(v) for v in cands.values())}\n")

        # Dòng ĐMH đã tự chốt lịch sử → nếu khớp vào đây thì dòng legacy nhiều khả năng bị TRÙNG
        has_system = {i for (i,) in db.query(PurchaseHistory.po_item_id)
                      .filter(PurchaseHistory.source == "system",
                              PurchaseHistory.po_item_id.isnot(None)).all()}

        stat = {"khớp": 0, "mơ hồ": 0, "không khớp": 0}
        dup = 0
        shown = 0
        plan: list[dict] = []           # xuất CSV để rà TỪNG cặp khớp trước khi --apply
        for h in legacy:
            best, why = _pick(h, cands.get((h.supplier_code or "", h.product_code or ""), []),
                              max_days, match_qty)
            stat[why] += 1
            if not best:
                plan.append({"ket_qua": why, "history_id": h.id, "product_code": h.product_code,
                             "supplier_code": h.supplier_code, "ngay_lich_su": h.order_date,
                             "sl_lich_su": float(h.qty_order or 0), "po_code": "",
                             "ngay_don": "", "sl_don": "", "lech_ngay": "", "nghi_trung": ""})
                continue
            dd, _qd, po, it = best
            is_dup = it.id in has_system
            dup += is_dup
            shown += 1
            plan.append({"ket_qua": why, "history_id": h.id, "product_code": h.product_code,
                         "supplier_code": h.supplier_code, "ngay_lich_su": h.order_date,
                         "sl_lich_su": float(h.qty_order or 0), "po_code": po.code,
                         "ngay_don": po.order_date, "sl_don": float(it.qty_order or 0),
                         "lech_ngay": dd if dd < 10 ** 6 else "", "nghi_trung": "x" if is_dup else ""})
            if shown <= limit:
                print(f"  {h.product_code:<14} {h.order_date} → {po.code:<12} "
                      f"(lệch {dd if dd < 10**6 else '?'} ngày{', NGHI TRÙNG với lịch sử hệ thống' if is_dup else ''})")
            if apply:
                h.po_id, h.po_code = po.id, po.code or ""
                extra = json.loads(h.extra or "{}")
                extra["linked_po_item_id"] = it.id
                h.extra = json.dumps(extra, ensure_ascii=False)
                if stat["khớp"] % BATCH == 0:
                    db.commit()

        if apply:
            db.commit()
        if csv_path and plan:
            with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
                w = csv.DictWriter(f, fieldnames=list(plan[0].keys()))
                w.writeheader()
                w.writerows(plan)
            print(f"\nĐã xuất {len(plan)} dòng đối chiếu ra {csv_path} — mở rà cột po_code/lech_ngay "
                  f"trước khi --apply; gỡ lại bằng --clear --apply.")
        print(f"\nKết quả: khớp={stat['khớp']} · mơ hồ={stat['mơ hồ']} · không khớp={stat['không khớp']}")
        if dup:
            print(f"CẢNH BÁO: {dup} dòng khớp vào dòng ĐMH ĐÃ CÓ lịch sử tự chốt → nhiều khả năng "
                  f"lần mua đó bị đếm 2 lần (1 legacy + 1 system), nên rà lại rồi xóa bớt dòng legacy.")
        print("Đã ghi vào DB." if apply else "(chạy thử) thêm --apply để ghi thật.")
    finally:
        db.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Điền mã PO cho lịch sử mua hàng cũ (legacy)")
    ap.add_argument("--apply", action="store_true", help="Ghi vào DB (mặc định chỉ chạy thử)")
    ap.add_argument("--days", type=int, default=30, help="Ngày đặt được phép lệch tối đa (mặc định 30)")
    ap.add_argument("--match-qty", action="store_true", help="Bắt buộc SL đặt khớp (lệch <= 1%%)")
    ap.add_argument("--clear", action="store_true", help="Gỡ mã PO đã gán cho dòng legacy")
    ap.add_argument("--limit", type=int, default=30, help="Số dòng khớp in ra để kiểm (mặc định 30)")
    ap.add_argument("--csv", default="/app/backfill_legacy_po_code.csv",
                    help="File CSV đối chiếu từng cặp legacy ↔ ĐMH (mặc định /app/backfill_legacy_po_code.csv)")
    ap.add_argument("--delete-dup", action="store_true",
                    help="XÓA dòng legacy trùng với lịch sử hệ thống đã tự chốt (thay vì gán mã PO)")
    a = ap.parse_args()
    main(a.apply, a.days, a.match_qty, a.clear, a.limit, a.csv, a.delete_dup)
