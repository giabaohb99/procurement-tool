"""bao-CR-542 — cảnh báo công nợ gom theo đơn + bên được trả, ghi tiền còn nợ và số ngày trễ.

Đại ca xem chuông: «Công nợ QUÁ HẠN: … PO00003 (hạn 2026-09-04)» lặp 5 dòng y hệt — khoản nợ
sinh theo TỪNG DÒNG HÀNG của lần giao, đơn 5 dòng là 5 khoản cùng hạn. Nay mỗi đơn + bên được
trả + mức một dòng; khóa nhóm = `payable:{id lớn nhất}:{mức}` (nhóm một khoản giữ đúng khóa cũ).
"""
from datetime import date
from types import SimpleNamespace

from app.modules.alert.controller import build as build_alerts
from app.modules.payable.due_alerts import group_due_payables
from app.modules.payable.model import Payable

TODAY = date(2026, 10, 1)


def _p(pid, due, remaining=1_000_000, po_id=3, po_code="PO00003", source="goods", sup="NCC01",
       name="CÔNG TY TNHH BAO BÌ CẨM HÙNG"):
    return SimpleNamespace(id=pid, due_date=due, remaining=remaining, po_id=po_id, po_code=po_code,
                           source_type=source, supplier_code=sup, supplier_name=name)


def test_five_lines_of_one_order_become_one_alert_with_total_and_days_late():
    rows = [_p(i, "2026-09-04", 2_000_000) for i in (11, 12, 13, 14, 15)]
    [g] = group_due_payables(rows, TODAY)
    assert g.level == "danger" and g.count == 5 and g.days == 27
    assert g.remaining == 10_000_000
    assert g.key == "payable:15:danger"
    assert g.title() == ("Công nợ QUÁ HẠN: CÔNG TY TNHH BAO BÌ CẨM HÙNG · PO00003 — 5 khoản · "
                         "còn nợ 10.000.000 đ · trễ 27 ngày (hạn 04/09/2026)")


def test_single_debt_keeps_the_old_key_and_omits_the_count():
    """Nhóm một khoản ra đúng khóa cũ → việc đã «Đánh dấu làm hết» trước CR vẫn ẩn."""
    [g] = group_due_payables([_p(7, "2026-09-06", 500_000, po_code="PO00010")], TODAY)
    assert g.key == "payable:7:danger"
    assert g.detail() == "còn nợ 500.000 đ · trễ 25 ngày (hạn 06/09/2026)"


def test_days_late_counts_from_the_earliest_due_date_in_the_group():
    [g] = group_due_payables([_p(1, "2026-09-20"), _p(2, "2026-09-04"), _p(3, "2026-09-10")], TODAY)
    assert g.due_date == "2026-09-04" and g.days == 27 and g.key == "payable:3:danger"


def test_groups_split_by_order_payee_flow_and_level():
    rows = [
        _p(1, "2026-09-04"), _p(2, "2026-09-04"),                       # hàng PO00003
        _p(3, "2026-09-04", source="shipping", sup="VC01", name="Vận tải A"),   # vận chuyển PO00003
        _p(4, "2026-09-04", po_id=10, po_code="PO00010"),               # đơn khác
        _p(5, "2026-10-03"),                                            # PO00003 nhưng mới sắp đến hạn
        _p(6, "2026-12-01"),                                            # còn xa — không báo
        _p(7, ""),                                                      # không có hạn — không báo
    ]
    groups = group_due_payables(rows, TODAY)
    assert [(g.level, g.po_code, g.source_type, g.count) for g in groups] == [
        ("danger", "PO00003", "goods", 2),
        ("danger", "PO00003", "shipping", 1),
        ("danger", "PO00010", "goods", 1),
        ("warn", "PO00003", "goods", 1),
    ]
    assert groups[1].party == "Vận tải A (vận chuyển)"
    assert groups[3].detail().startswith("còn nợ 1.000.000 đ · còn 2 ngày")


def test_due_today_is_a_warning_not_overdue():
    [g] = group_due_payables([_p(1, "2026-10-01")], TODAY)
    assert g.level == "warn" and "đến hạn hôm nay" in g.title()


def test_bell_shows_one_line_per_order(db):
    for _ in range(5):
        db.add(Payable(po_id=3, po_code="PO00003", supplier_code="NCC01", supplier_name="Cẩm Hùng",
                       source_type="goods", due_date="2026-01-04", total=100, remaining=100, status="unpaid"))
    db.add(Payable(po_id=3, po_code="PO00003", supplier_code="NCC01", supplier_name="Cẩm Hùng",
                   source_type="goods", due_date="2026-01-04", total=100, paid_amount=100, remaining=0,
                   status="paid"))
    db.commit()

    items = [x for x in build_alerts(db)["items"] if x["type"] == "payable"]
    assert len(items) == 1
    assert "5 khoản" in items[0]["title"] and "còn nợ 500 đ" in items[0]["title"]
