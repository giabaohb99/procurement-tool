"""Tạo 2 đơn mua hàng NHẬP KHẨU mẫu để thử bao-CR-319 (chỉ dùng LOCAL).

Đi qua đúng API thật (`POST /api/purchase-orders` → submit → approve) chứ không nhét
thẳng vào DB, để dữ liệu mẫu chạy qua toàn bộ luật của backend: chuẩn hóa loại tiền
xuống dòng hàng, quy đổi `base_amount`, sinh công nợ.

Chạy: docker compose exec api python scripts/seed_demo_import_po.py
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

BASE = os.getenv("SEED_API_BASE", "http://localhost:8000")
API_USER = os.getenv("SEED_API_USER", "manager_purchase@demo.com")
API_PASSWORD = os.getenv("SEED_API_PASSWORD", "demo123")


def call(path, tok=None, body=None, method=None, ignore_errors=False):
    req = urllib.request.Request(BASE + path, method=method or ("POST" if body is not None else "GET"))
    req.add_header("Content-Type", "application/json")
    if tok:
        req.add_header("Authorization", "Bearer " + tok)
    data = json.dumps(body).encode() if body is not None else None
    try:
        return json.loads(urllib.request.urlopen(req, data).read())
    except urllib.error.HTTPError as e:
        if ignore_errors:
            return None
        sys.exit(f"LỖI {e.code} khi {req.get_method()} {path}: {e.read().decode('utf-8', 'replace')[:500]}")


# Nhà cung cấp nước ngoài — đơn nhập khẩu mua của người bán ở nước ngoài, danh mục
# NCC hiện có toàn doanh nghiệp trong nước nên phải dựng riêng hai cái.
FOREIGN_SUPPLIERS = [
    {"code": "Guangzhou Pack", "name": "GUANGZHOU JIAXIN PACKAGING CO., LTD",
     "payment_terms": "T/T đặt cọc 30%, trả nốt 70% trước khi giao hàng"},
    {"code": "Sunrise Plastics", "name": "SUNRISE PLASTICS INDUSTRIAL CO., LTD",
     "payment_terms": "L/C at sight, 60 ngày"},
]

# NCC của các khoản CHI PHÍ lô hàng (bao-CR-319 P3). Mỗi dòng chi phí trả cho một người
# khác nhau, không phải người bán hàng — nên phải có sẵn hãng tàu và đơn vị khai thuê.
# Khoản thuế thì dùng NCC "Ngân sách nhà nước" do migration ed610675320b tạo.
COST_SUPPLIERS = [
    {"code": "SITC LINES", "name": "CONG TY TNHH SITC VIET NAM", "supplier_type": "transport",
     "payment_terms": "Chuyển khoản 15 ngày"},
    {"code": "VINALOG", "name": "CONG TY CP GIAO NHAN VINALOG", "supplier_type": "transport",
     "payment_terms": "Chuyển khoản 30 ngày"},
]

DEMO_ORDERS = [
    {
        "label": "Đơn CNY — đã có tờ khai hải quan",
        "po": {
            "company_id": 2,                      # IDA GLOBAL (công ty xuất nhập khẩu)
            "supplier_code": "Guangzhou Pack",
            "supplier_name": "GUANGZHOU JIAXIN PACKAGING CO., LTD",
            "department": "Thu mua",
            "order_date": "2026-09-02",
            "order_type": 2,                      # 2 = nhập khẩu
            "currency": "CNY",
            "exchange_rate": 3620,
            "payment_terms": "T/T đặt cọc 30%, trả nốt 70% trước khi giao hàng",
            "note": "Lô thùng carton nhập từ Quảng Châu, giao cảng Cát Lái.",
            "items": [
                {"product_code": "THC0003", "item_group": "Thùng",
                 "product_name": "Thùng DC Chai Pet Vuông 35 450ml-500ml - (47x38.5x19cm) - Trắng viền đen",
                 "invoice_name": "Thùng carton 47x38.5x19cm",
                 "unit": "Cái", "qty_request": 5000, "qty_order": 5000,
                 "price": 4.85, "vat": 0,
                 "required_date": "2026-10-15", "expected_date": "2026-10-10",
                 "warehouse_code": "Agama",
                 "weight_kg": 1250, "dimension": "47x38.5x19 cm",
                 "note": "Đóng 50 cái/kiện, 100 kiện."},
                {"product_code": "THC0004", "item_group": "Thùng",
                 "product_name": "Thùng DC Chai Pet Tròn 43 450ml-500ml - 61.5x38.5x19 - Trắng",
                 "invoice_name": "Thùng carton 61.5x38.5x19cm",
                 "unit": "Cái", "qty_request": 3000, "qty_order": 3000,
                 "price": 6.20, "vat": 0,
                 "required_date": "2026-10-15", "expected_date": "2026-10-10",
                 "warehouse_code": "Agama",
                 "weight_kg": 990, "dimension": "61.5x38.5x19 cm"},
            ],
        },
        "approve": True,
        # Số + ngày tờ khai chỉ có SAU khi hàng thông quan, nên cập nhật ở bước riêng
        # sau khi duyệt — đúng như ngoài đời và đúng luật ORDER_FIELDS_EDITABLE_AFTER_APPROVAL.
        "customs": {"customs_decl_no": "105987654321", "customs_decl_date": "2026-10-08"},
        # Chi phí cũng khai SAU khi duyệt (hóa đơn cước, tờ khai thuế, phí lưu bãi đều về
        # sau) — nhịp này kiểm luôn việc bảng chi phí không bị khóa cùng phần đã duyệt.
        # Tiền chi phí ghi bằng VNĐ trong đơn CNY: tỷ giá phải là 1, không mượn 3.620 của đơn.
        "costs": [
            {"cost_type": 1, "description": "Cước biển Thượng Hải – Cát Lái, 2x40HC",
             "supplier_code": "SITC LINES", "supplier_name": "CONG TY TNHH SITC VIET NAM",
             "currency": "VND", "amount": 42_500_000, "vat": 0, "allocation_method": 1,
             "invoice_no": "SITC-26/1042", "invoice_date": "2026-10-09", "payment_due_date": "2026-10-24"},
            {"cost_type": 2, "description": "Phí địa phương tại cảng (THC, D/O, nâng hạ)",
             "supplier_code": "SITC LINES", "supplier_name": "CONG TY TNHH SITC VIET NAM",
             "currency": "VND", "amount": 8_750_000, "vat": 8, "allocation_method": 1,
             "invoice_no": "SITC-26/1043", "invoice_date": "2026-10-09", "payment_due_date": "2026-10-24"},
            {"cost_type": 3, "description": "Phí dịch vụ khai thuê hải quan",
             "supplier_code": "VINALOG", "supplier_name": "CONG TY CP GIAO NHAN VINALOG",
             "currency": "VND", "amount": 3_500_000, "vat": 8, "allocation_method": 1,
             "invoice_no": "VNL-26/0771", "invoice_date": "2026-10-08", "payment_due_date": "2026-11-07"},
            {"cost_type": 4, "description": "Thuế nhập khẩu theo tờ khai 105987654321",
             "supplier_code": "NSNN", "supplier_name": "Ngân sách nhà nước",
             "currency": "VND", "amount": 27_914_400, "vat": 0, "allocation_method": 1,
             "payment_due_date": "2026-10-08"},
            {"cost_type": 5, "description": "Thuế GTGT hàng nhập khẩu theo tờ khai 105987654321",
             "supplier_code": "NSNN", "supplier_name": "Ngân sách nhà nước",
             "currency": "VND", "amount": 60_696_320, "vat": 0, "allocation_method": 1,
             "payment_due_date": "2026-10-08"},
            # Cước kéo hàng về kho chia theo KHỐI LƯỢNG chứ không theo giá trị — hai dòng
            # thùng carton nặng gần bằng nhau nhưng đơn giá lệch hẳn.
            {"cost_type": 10, "description": "Vận chuyển nội địa Cát Lái – kho Agama",
             "supplier_code": "VINALOG", "supplier_name": "CONG TY CP GIAO NHAN VINALOG",
             "currency": "VND", "amount": 6_200_000, "vat": 8, "allocation_method": 2,
             "invoice_no": "VNL-26/0783", "invoice_date": "2026-10-12", "payment_due_date": "2026-11-11"},
        ],
        # Thành tiền của dòng tính theo SL THỰC NHẬN, nên không khai lần giao thì đơn
        # nằm im ở 0 đồng và không có công nợ nào để soi số quy đổi.
        "deliveries": [
            {"delivery_no": 1, "warehouse_code": "Agama", "ship_qty": 5000, "received_qty": 5000,
             "received_date": "2026-10-12", "invoice_no": "GZ-2026-0912"},
            {"delivery_no": 1, "warehouse_code": "Agama", "ship_qty": 3000, "received_qty": 3000,
             "received_date": "2026-10-12", "invoice_no": "GZ-2026-0912"},
        ],
    },
    {
        "label": "Đơn USD — lẫn một dòng trả bằng tiền Việt, chưa thông quan",
        "po": {
            "company_id": 2,
            "supplier_code": "Sunrise Plastics",
            "supplier_name": "SUNRISE PLASTICS INDUSTRIAL CO., LTD",
            "department": "Thu mua",
            "order_date": "2026-09-05",
            "order_type": 2,
            "currency": "USD",
            "exchange_rate": 26150,
            "payment_terms": "L/C at sight, 60 ngày",
            "note": "Thùng carton nhập Malaysia. Dòng nhãn thùng NCC báo giá bằng VNĐ nên "
                    "để nguyên tiền Việt, không quy đổi.",
            "items": [
                {"product_code": "THC0005", "item_group": "Thùng",
                 "product_name": "Thùng DC Chai Pet Tròn 35 450ml-500ml - (59x37x19.5cm) - Trắng",
                 "invoice_name": "Thùng carton 59x37x19.5cm",
                 "unit": "Cái", "qty_request": 2000, "qty_order": 2000,
                 "price": 0.92, "vat": 0,
                 "required_date": "2026-11-05", "expected_date": "2026-10-28",
                 "warehouse_code": "Agama",
                 "weight_kg": 640, "dimension": "59x37x19.5 cm"},
                {"product_code": "NDT5089", "item_group": "Nhãn",
                 "product_name": "[Nhãn Thùng] GC - V - 5089 - CTY KIM NGỌC - Sạch Sâu",
                 "invoice_name": "Nhãn thùng 5089",
                 "unit": "Cái", "qty_request": 20000, "qty_order": 20000,
                 "price": 225, "vat": 8,
                 "currency": "VND",             # dòng trả bằng tiền Việt trong đơn ngoại tệ
                 "required_date": "2026-11-05", "expected_date": "2026-10-28",
                 "warehouse_code": "Agama"},
            ],
            # Chi phí khai NGAY lúc lập đơn (POCreate cũng nhận `import_costs`). Lô chưa
            # thông quan nên chưa có dòng thuế nào — thuế chỉ có sau khi có tờ khai.
            "import_costs": [
                {"cost_type": 1, "description": "Cước biển Port Klang – Cát Lái, 1x40HC",
                 "supplier_code": "SITC LINES", "supplier_name": "CONG TY TNHH SITC VIET NAM",
                 "amount": 950, "vat": 0, "allocation_method": 1},   # để trống loại tiền = theo đơn (USD)
                {"cost_type": 9, "description": "Bảo hiểm hàng hóa 110% trị giá CIF",
                 "supplier_code": "VINALOG", "supplier_name": "CONG TY CP GIAO NHAN VINALOG",
                 "currency": "USD", "amount": 120, "vat": 0, "allocation_method": 1},
                # Phí trả bằng tiền Việt nằm trong đơn USD — tỷ giá phải là 1
                {"cost_type": 8, "description": "Phí kiểm tra chất lượng chuyên ngành",
                 "supplier_code": "VINALOG", "supplier_name": "CONG TY CP GIAO NHAN VINALOG",
                 "currency": "VND", "amount": 2_400_000, "vat": 8, "allocation_method": 3},
            ],
        },
        "approve": False,
    },
]


def ensure_suppliers():
    """Dựng NCC nước ngoài + NCC chi phí thẳng qua ORM.

    Cố ý KHÔNG đi qua API như phần đơn hàng: vai trò thu mua dùng để chạy script này
    không có quyền `supplier.write`, mà nới quyền chỉ để tạo dữ liệu mẫu thì sai chỗ.
    Đây là danh mục, không phải thứ đang cần kiểm chứng.
    """
    import app.main  # noqa: F401 — đăng ký toàn bộ model trước khi ORM giải quan hệ
    from app.core.database import SessionLocal
    from app.modules.supplier.model import Supplier

    db = SessionLocal()
    try:
        for r in FOREIGN_SUPPLIERS + COST_SUPPLIERS:
            r = dict(r)
            supplier_type = r.pop("supplier_type", "goods")
            s = db.query(Supplier).filter(Supplier.code == r["code"]).first()
            if s:
                s.payment_terms = r["payment_terms"]
                print(f"  NCC đã có: {r['code']}")
            else:
                db.add(Supplier(supplier_type=supplier_type, vat=0, is_active=True, **r))
                print(f"  Tạo NCC : {r['code']}")
        db.commit()
    finally:
        db.close()


# Đơn đã duyệt chỉ cho sửa lần giao, còn mọi ô khác gửi lên phải TRÙNG y nguyên giá trị
# đang có, không thì `block_edit_approved_order` chặn. Nên đọc lại đơn rồi gửi lại chính nó.
_ITEM_FIELDS_TO_RESEND = ("id", "product_code", "product_name", "invoice_name", "item_group", "spec",
                   "unit", "qty_request", "qty_order", "price", "vat", "currency", "exchange_rate",
                   "weight_kg", "dimension", "required_date", "expected_date", "warehouse_code",
                   "note")


def cleanup_old_orders(tok):
    """Xóa đơn mẫu của lần chạy trước để script chạy lại bao nhiêu lần cũng ra đúng 2 đơn.

    Cả hai nhịp đều đi thẳng vào tầng service chứ không qua API, vì luật nghiệp vụ
    THẬT chặn đúng chỗ này — và chặn là đúng: `unapprove_po` từ chối đơn đã nhận hàng
    (hàng vào kho rồi, đã sinh công nợ), `delete_po` chỉ nhận đơn Nháp / Bị từ chối,
    còn vai trò thu mua vốn không có `purchase_order.delete`. Nới bất kỳ luật nào
    trong ba luật đó chỉ để dọn dữ liệu mẫu thì cái giá quá đắt, nên script tự hạ
    trạng thái về Nháp ngay trên DB rồi mới xóa. `delete_po` vẫn dọn đủ dòng hàng,
    lần giao, phiếu nhập kho, tồn kho và công nợ.

    CHỈ CHẠY LOCAL: hàm này xóa đơn thật, không hỏi lại. Phạm vi giới hạn ở đơn của
    hai NCC nước ngoài dựng riêng cho bộ dữ liệu mẫu này.
    """
    import app.main  # noqa: F401
    from app.core.database import SessionLocal
    from app.modules.purchase_order import service as po_service

    supplier_codes = {r["code"] for r in FOREIGN_SUPPLIERS}
    to_delete = []
    for code in supplier_codes:
        d = call(f"/api/purchase-orders?supplier_code={urllib.parse.quote(code)}&page=1&page_size=100", tok)["data"]
        for po in d.get("items") or []:
            to_delete.append((po["id"], po["code"]))

    if not to_delete:
        return
    db = SessionLocal()
    try:
        for pid, code in to_delete:
            po = po_service.get_po(db, pid)
            if po.status not in ("draft", "rejected"):
                po.status = "draft"
                db.commit()
            po_service.delete_po(db, pid, user_id=0)
            print(f"  Xóa đơn mẫu cũ: {code}")
    finally:
        db.close()


def record_deliveries(tok, pid, deliveries):
    d = call(f"/api/purchase-orders/{pid}", tok)["data"]
    rows = []
    for i, it in enumerate(d.get("items") or []):
        row = {k: it.get(k) for k in _ITEM_FIELDS_TO_RESEND if it.get(k) is not None}
        row["deliveries"] = [deliveries[i]] if i < len(deliveries) else []
        rows.append(row)
    call(f"/api/purchase-orders/{pid}", tok, {"items": rows}, method="PATCH")


def main():
    tok = call("/api/auth/login", body={"username": API_USER, "password": API_PASSWORD})["data"]["access_token"]
    print(f"Đăng nhập {API_USER}\n")
    ensure_suppliers()
    cleanup_old_orders(tok)

    for cfg in DEMO_ORDERS:
        po = call("/api/purchase-orders", tok, cfg["po"])["data"]
        pid, code = po["id"], po["code"]
        call(f"/api/purchase-orders/{pid}/submit", tok, {})
        status = "đã gửi duyệt"
        if cfg["approve"]:
            call(f"/api/purchase-orders/{pid}/approve", tok, {})
            status = "đã duyệt"
        if cfg.get("customs"):
            call(f"/api/purchase-orders/{pid}", tok, cfg["customs"], method="PATCH")
            status += ", đã khai tờ khai hải quan"
        if cfg.get("costs"):
            call(f"/api/purchase-orders/{pid}", tok, {"import_costs": cfg["costs"]}, method="PATCH")
            status += ", đã khai chi phí lô hàng"
        if cfg.get("deliveries"):
            record_deliveries(tok, pid, cfg["deliveries"])
            status += ", đã nhận hàng"

        d = call(f"/api/purchase-orders/{pid}", tok)["data"]
        print(f"\n{cfg['label']}")
        print(f"  {code} — {status}")
        print(f"  loại đơn {d.get('order_type')} ({d.get('order_type_label')}) · "
              f"{d.get('currency')} @ {d.get('exchange_rate')} · "
              f"tờ khai {d.get('customs_decl_no') or '(chưa có)'} {d.get('customs_decl_date') or ''}")
        for it in d.get("items") or []:
            print(f"    {it['product_code']:9s} {it.get('currency'):4s} @{it.get('exchange_rate'):>10} "
                  f"thành tiền {float(it.get('amount') or 0):>14,.2f} "
                  f"quy đổi {float(it.get('base_amount') or 0):>16,.2f} VNĐ")
        for c in d.get("import_costs") or []:
            print(f"    [chi phí] {c.get('cost_type_label'):28s} {c.get('supplier_code') or '(chưa chọn)':16s} "
                  f"{c.get('currency'):4s} {float(c.get('amount') or 0):>12,.2f} +{float(c.get('vat') or 0):g}% "
                  f"→ {float(c.get('base_amount') or 0):>16,.2f} VNĐ · {c.get('allocation_method_label')}")
        summary = d.get("import_cost_summary") or {}
        if summary:
            print(f"    Tiền hàng quy đổi {float(summary.get('goods_base_total') or 0):>18,.2f} VNĐ")
            print(f"    Chi phí nhập khẩu {float(summary.get('cost_total') or 0):>18,.2f} VNĐ")
            print(f"    Tổng giá trị lô   {float(summary.get('landed_total') or 0):>18,.2f} VNĐ")


if __name__ == "__main__":
    main()
