"""Lớp tool loại A của Trợ lý AI (Phase 2) — gác quyền + allowlist + nhất quán số liệu.

CHỈ kiểm phần vừa làm: bộ chạy `tools.run_tool` và mấy handler ở `tools/catalog.py`.
Không đụng tới provider (gọi model thật) — phần đó verify tay bằng live test.
"""
from datetime import date, timedelta

import pytest

from app.modules.assistant import tools as T
from app.modules.contract.model import Contract
from app.modules.product.model import Product
from app.modules.purchase_history.model import PurchaseHistory
from app.modules.purchase_order.model import POItem, PurchaseOrder


@pytest.fixture
def contracts(db):
    """3 hợp đồng NCC: 1 còn hạn, 1 hết hạn, 1 KHÔNG ghi ngày (unknown)."""
    today = date.today()
    future = (today + timedelta(days=30)).isoformat()
    past = (today - timedelta(days=30)).isoformat()
    rows = [
        Contract(code="HD-ACT", party_type="supplier", party_code="NX",
                 party_name="NCC A", title="Còn hạn", start_date="2020-01-01",
                 end_date=future, status="active"),
        Contract(code="HD-EXP", party_type="supplier", party_code="NX",
                 party_name="NCC A", title="Hết hạn", start_date="2020-01-01",
                 end_date=past, status="active"),
        Contract(code="HD-UNK", party_type="supplier", party_code="NX",
                 party_name="NCC A", title="Không ngày", start_date="2020-01-01",
                 end_date="", status="active"),
    ]
    db.add_all(rows)
    db.commit()
    return rows


def test_bad_tool_name_bi_chan(db, seed):
    """Tên tool ngoài allowlist -> trả error, KHÔNG chạy gì (tầng 2 bảo mật)."""
    from app.modules.user.model import User
    user = db.get(User, seed.u_req_id)
    out = T.run_tool(db, user, "drop_table_users", {})
    assert out.get("error")
    assert "drop_table_users" in out["error"]


def test_thieu_quyen_thi_denied(db, seed, contracts):
    """Người KHÔNG có quyền `contract` -> handler trả denied, không lộ dữ liệu."""
    from app.modules.user.model import User
    user = db.get(User, seed.u_req_id)   # chưa cấp quyền gì
    out = T.run_tool(db, user, "contract_count_by_status", {"group_by": "none"})
    assert out.get("denied") is True
    assert "active" not in out


def test_co_quyen_thi_dem_dung(db, seed, contracts, cap_quyen):
    """Có `contract.read` -> đếm đúng 1 còn hạn / 1 hết hạn / 1 unknown."""
    from app.modules.user.model import User
    cap_quyen(seed.u_req_id, "contract", scope="all", read=True)
    user = db.get(User, seed.u_req_id)
    out = T.run_tool(db, user, "contract_count_by_status", {"group_by": "none"})
    assert out["total"] == 3
    assert out["active"] == 1
    assert out["expired"] == 1
    assert out["unknown"] == 1


def test_dem_va_liet_ke_khop_nhau(db, seed, contracts, cap_quyen):
    """Chốt lỗi vừa vá: hợp đồng KHÔNG ngày phải là unknown ở CẢ đếm lẫn liệt kê,
    nên số 'active' của count == tổng dòng của list active."""
    from app.modules.user.model import User
    cap_quyen(seed.u_req_id, "contract", scope="all", read=True)
    user = db.get(User, seed.u_req_id)
    count = T.run_tool(db, user, "contract_count_by_status", {"group_by": "none"})
    listed = T.run_tool(db, user, "contract_list_by_expiry",
                        {"status": "active", "limit": 100})
    assert count["active"] == listed["total"] == 1
    # Hợp đồng KHÔNG ngày tuyệt đối không lọt vào danh sách còn hạn.
    assert all(it["end_date"] for it in listed["items"])


def test_product_search_can_quyen_product(db, seed, cap_quyen):
    """product_search: thiếu product.read -> denied; có thì tra được theo tên."""
    from app.modules.user.model import User
    db.add(Product(code="THUNG-01", name="Thùng Carton 5 lớp",
                   item_group="Thùng", unit="cái", hh_code=""))
    db.commit()
    user = db.get(User, seed.u_req_id)

    denied = T.run_tool(db, user, "product_search", {"keyword": "thùng"})
    assert denied.get("denied") is True

    cap_quyen(seed.u_req_id, "product", scope="all", read=True)
    user = db.get(User, seed.u_req_id)
    ok = T.run_tool(db, user, "product_search", {"keyword": "thùng"})
    assert ok["total"] == 1
    assert ok["items"][0]["code"] == "THUNG-01"


# ── Nhóm tool tổng hợp toàn hệ ────────────────────────────────────────────────────────
@pytest.fixture
def history(db):
    """Lịch sử mua: NCC-A 2 dòng (1 amount sẵn, 1 để 0 -> lùi qty*price), NCC-B 1 dòng."""
    rows = [
        PurchaseHistory(product_code="P1", product_name="Hàng 1", supplier_code="A",
                        supplier_name="NCC A", order_date="2026-01-10",
                        qty_order=10, price=1000, amount=11000),
        PurchaseHistory(product_code="P2", product_name="Hàng 2", supplier_code="A",
                        supplier_name="NCC A", order_date="2026-02-20",
                        qty_order=5, price=2000, amount=0),   # amount rỗng -> 5*2000=10000
        PurchaseHistory(product_code="P1", product_name="Hàng 1", supplier_code="B",
                        supplier_name="NCC B", order_date="2026-03-05",
                        qty_order=2, price=500, amount=1000),
    ]
    db.add_all(rows)
    db.commit()
    return rows


def test_top_suppliers_can_supplier_va_xep_hang(db, seed, history, cap_quyen):
    """Thiếu supplier.read -> denied; có thì xếp NCC-A (21000/2 lần) trên NCC-B (1000/1)."""
    from app.modules.user.model import User
    user = db.get(User, seed.u_req_id)
    assert T.run_tool(db, user, "top_suppliers_by_purchase", {}).get("denied") is True

    cap_quyen(seed.u_req_id, "supplier", scope="all", read=True)
    user = db.get(User, seed.u_req_id)
    out = T.run_tool(db, user, "top_suppliers_by_purchase", {"top_n": 5})
    items = out["items"]
    assert items[0]["supplier_code"] == "A"
    assert items[0]["total_amount"] == 21000.0   # 11000 + (5*2000 do amount rỗng)
    assert items[0]["times"] == 2
    assert items[1]["supplier_code"] == "B"


def test_recent_purchases_sort_moi_nhat(db, seed, history, cap_quyen):
    """recent_purchases đòi product.read, trả theo ngày mới nhất trước."""
    from app.modules.user.model import User
    cap_quyen(seed.u_req_id, "product", scope="all", read=True)
    user = db.get(User, seed.u_req_id)
    out = T.run_tool(db, user, "recent_purchases", {"limit": 10})
    assert out["items"][0]["order_date"] == "2026-03-05"   # dòng mới nhất
    # Không có supplier.read -> ẩn NCC
    assert "supplier_code" not in out["items"][0]
    assert out.get("note")


def test_purchase_report_tong_chi_tieu(db, seed, history, cap_quyen):
    """Báo cáo: tổng chi tiêu = 11000+10000+1000, đếm đúng mã hàng; NCC ẩn khi thiếu quyền."""
    from app.modules.user.model import User
    cap_quyen(seed.u_req_id, "product", scope="all", read=True)
    user = db.get(User, seed.u_req_id)
    out = T.run_tool(db, user, "purchase_report", {"group_by": "month"})
    assert out["total_spend"] == 22000.0
    assert out["lines"] == 3
    assert out["product_count"] == 2          # P1, P2
    assert "supplier_count" not in out        # chưa có supplier.read
    assert len(out["by_month"]) == 3          # 3 tháng khác nhau


def test_analytics_none_tong_gop(db, seed, history, cap_quyen):
    """analytics_query không chia chiều -> một con số: tổng chi tiêu = 11000+10000+1000."""
    from app.modules.user.model import User
    cap_quyen(seed.u_req_id, "product", scope="all", read=True)
    user = db.get(User, seed.u_req_id)
    out = T.run_tool(db, user, "analytics_query",
                     {"metric": "total_amount", "dimension": "none"})
    assert out["value"] == 22000.0
    # count là số nguyên, không làm tròn float
    cnt = T.run_tool(db, user, "analytics_query", {"metric": "count", "dimension": "none"})
    assert cnt["value"] == 3


def test_analytics_theo_ncc_can_supplier_va_xep_hang(db, seed, history, cap_quyen):
    """Chia theo NCC lộ danh tính NCC -> đòi supplier.read; xếp NCC-A (21000) trên NCC-B (1000)."""
    from app.modules.user.model import User
    cap_quyen(seed.u_req_id, "product", scope="all", read=True)
    user = db.get(User, seed.u_req_id)
    # Có product.read nhưng CHƯA có supplier.read -> chặn khi dimension=supplier
    assert T.run_tool(db, user, "analytics_query",
                      {"dimension": "supplier"}).get("denied") is True

    cap_quyen(seed.u_req_id, "supplier", scope="all", read=True)
    user = db.get(User, seed.u_req_id)
    out = T.run_tool(db, user, "analytics_query",
                     {"metric": "total_amount", "dimension": "supplier"})
    assert out["items"][0]["group"] == "A"
    assert out["items"][0]["value"] == 21000.0
    assert out["items"][1]["group"] == "B"


def test_recent_purchase_orders_gac_scope(db, seed, cap_quyen):
    """PO gần nhất: đòi purchase_order.read; giá trị = tổng amount các dòng."""
    from app.modules.user.model import User
    po = PurchaseOrder(code="PO-001", supplier_code="A", supplier_name="NCC A",
                       order_date="2026-05-01", status="approved", company_id=seed.company_id)
    db.add(po)
    db.flush()
    db.add_all([
        POItem(po_id=po.id, product_code="P1", amount=3000),
        POItem(po_id=po.id, product_code="P2", amount=2000),
    ])
    db.commit()

    user = db.get(User, seed.u_req_id)
    assert T.run_tool(db, user, "recent_purchase_orders", {}).get("denied") is True

    cap_quyen(seed.u_req_id, "purchase_order", scope="all", read=True)
    user = db.get(User, seed.u_req_id)
    out = T.run_tool(db, user, "recent_purchase_orders", {"limit": 10})
    assert out["total"] == 1
    assert out["items"][0]["code"] == "PO-001"
    assert out["items"][0]["amount"] == 5000.0
