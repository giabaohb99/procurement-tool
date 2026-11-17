"""duoc-CR-775 — NSPT của màn Tiến độ đơn mua hàng: API trả MÃ kèm TÊN tra từ hồ sơ nhân sự.

Lỗi thật trên dev (17/11/2026): 2 đơn lưu `nspt = "NM_NV"` (mã nhân sự) với `nspt_id = 0`, vì giao diện tạo ĐMH từ
YCMH gửi mã vào ô tên và máy chủ chỉ tra người theo TÊN. Màn Tiến độ in thẳng chữ đã lưu nên hiện mã thay tên.

Bốn chốt:
1. Đơn có liên kết hồ sơ: API trả `nspt_code` + `nspt_name` theo hồ sơ HIỆN HÀNH (đổi tên là thấy tên mới).
2. Đơn chưa liên kết (dữ liệu cũ kiểu "Mr Tiên"): `nspt_code` rỗng, `nspt_name` = chữ đã lưu — không đoán.
3. Tệp xuất ghi "Mã · Tên" (mã trước, anh Được chốt) và cột xếp theo MÃ cho khớp chữ đang hiện.
4. Lúc lưu, ô nhân sự nhận MÃ thì tra theo mã, gắn id và thay chữ bằng họ tên; họ tên thật vẫn tra theo tên.
"""
import json
from types import SimpleNamespace

import pytest
from starlette.datastructures import QueryParams

from app.modules.employee.model import Employee
from app.modules.employee.service import sync_employee_ref
from app.modules.purchase_order.model import POItem, PurchaseOrder
from app.modules.purchase_progress import controller as pp
from app.modules.purchase_progress.nspt_people import load_nspt_people, nspt_label
from app.modules.user.model import User


@pytest.fixture
def viewer(db, cap_quyen):
    user = User(email="cr775@test.local", employee_id=0, is_active=True)
    db.add(user)
    db.flush()
    cap_quyen(user.id, "purchase_order", scope="all", read=True)
    db.commit()
    return user


@pytest.fixture
def staff(db):
    emp = Employee(code="NSU775", full_name="Nguyễn Thu Mua", company_id=1, is_active=True)
    db.add(emp)
    db.commit()
    return emp


def _order(db, code: str, nspt: str, nspt_id: int = 0) -> PurchaseOrder:
    po = PurchaseOrder(code=code, status="approved", order_date="2026-11-17", nspt=nspt, nspt_id=nspt_id)
    db.add(po)
    db.flush()
    db.add(POItem(po_id=po.id, product_code=f"SP-{code}", qty_order=1, price=1000))
    db.commit()
    return po


def _rows(db, user) -> dict[str, dict]:
    resp = pp.list_progress(SimpleNamespace(query_params=QueryParams("")), {"offset": 0, "limit": 50}, db, user)
    items = json.loads(resp.body)["data"]["items"]
    return {row["po_code"]: row for row in items}


def test_linked_order_returns_code_and_current_name(db, viewer, staff):
    _order(db, "PO775A", "Tên cũ đã chụp", nspt_id=staff.id)
    row = _rows(db, viewer)["PO775A"]
    assert row["nspt_code"] == "NSU775"
    #  Tên theo hồ sơ hiện hành, không phải chữ chụp lúc lưu đơn.
    assert row["nspt_name"] == "Nguyễn Thu Mua"


def test_unlinked_legacy_text_is_kept_as_is_without_guessing(db, viewer, staff):
    _order(db, "PO775B", "Mr Tiên")
    row = _rows(db, viewer)["PO775B"]
    assert row["nspt_code"] == ""
    assert row["nspt_name"] == "Mr Tiên"


def test_export_label_puts_code_first_then_name(db, staff):
    linked = _order(db, "PO775C", "x", nspt_id=staff.id)
    legacy = _order(db, "PO775D", "Ms Quyên")
    people = load_nspt_people(db, [linked, legacy])
    assert nspt_label(linked, people) == "NSU775 · Nguyễn Thu Mua"
    assert nspt_label(legacy, people) == "Ms Quyên"


def test_list_loads_people_in_one_query_for_the_whole_page(db, viewer, staff):
    """Một truy vấn nhân sự cho cả trang, không theo từng dòng."""
    other = Employee(code="NSU776", full_name="Trần Hai", company_id=1, is_active=True)
    db.add(other)
    db.commit()
    for i in range(6):
        _order(db, f"PO775E{i}", "", nspt_id=(staff.id if i % 2 else other.id))

    from sqlalchemy import event

    statements: list[str] = []
    listener = lambda *args: statements.append(str(args[2]))   # noqa: E731
    event.listen(db.get_bind(), "before_cursor_execute", listener)
    try:
        _rows(db, viewer)
    finally:
        event.remove(db.get_bind(), "before_cursor_execute", listener)
    employee_reads = [s for s in statements if "FROM tab_employee" in s and "tab_employee.full_name" in s]
    assert len(employee_reads) == 1


def test_saving_an_employee_code_links_by_code_and_stores_the_full_name(db, staff):
    obj = SimpleNamespace(nspt="NSU775", nspt_id=0, company_id=1)
    sync_employee_ref(db, obj, "nspt_id", "nspt")
    assert obj.nspt_id == staff.id
    assert obj.nspt == "Nguyễn Thu Mua"


def test_saving_a_real_name_still_resolves_by_name_and_unknown_text_stays_unlinked(db, staff):
    by_name = SimpleNamespace(nspt="Nguyễn Thu Mua", nspt_id=0, company_id=1)
    sync_employee_ref(db, by_name, "nspt_id", "nspt")
    assert by_name.nspt_id == staff.id

    unknown = SimpleNamespace(nspt="Mr Tiên", nspt_id=0, company_id=1)
    sync_employee_ref(db, unknown, "nspt_id", "nspt")
    assert (unknown.nspt_id, unknown.nspt) == (0, "Mr Tiên")


def test_sorting_follows_the_employee_code_shown_first(db, viewer):
    """Ô bày "MÃ · Tên" thì bấm xếp phải theo MÃ, không theo tên đã lưu (luật §8 xếp theo giá trị đang hiện)."""
    a = Employee(code="NSU001", full_name="Zô Cuối Bảng", company_id=1, is_active=True)
    b = Employee(code="NSU999", full_name="An Đầu Bảng", company_id=1, is_active=True)
    db.add_all([a, b])
    db.commit()
    _order(db, "PO775S1", "Zô Cuối Bảng", nspt_id=a.id)
    _order(db, "PO775S2", "An Đầu Bảng", nspt_id=b.id)
    _order(db, "PO775S3", "")   # trống: xuống cuối cả hai chiều

    def codes(direction):
        resp = pp.list_progress(SimpleNamespace(query_params=QueryParams(f"sort_by=nspt&sort_dir={direction}")),
                                {"offset": 0, "limit": 50}, db, viewer)
        return [r["po_code"] for r in json.loads(resp.body)["data"]["items"] if r["po_code"].startswith("PO775S")]

    assert codes("asc") == ["PO775S1", "PO775S2", "PO775S3"]
    assert codes("desc") == ["PO775S2", "PO775S1", "PO775S3"]
