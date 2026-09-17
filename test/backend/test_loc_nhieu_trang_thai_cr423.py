"""bao-CR-423 — ô lọc CHỌN NHIỀU giá trị trên hai màn Tiến độ.

Trước đây `company_id` / `status` (Tiến độ mua hàng) và `company_id` / `state` (Tiến độ báo
giá) chỉ nhận MỘT giá trị: gửi `status=a,b` là lọc theo chuỗi "a,b" — không dòng nào khớp, bảng
rỗng mà không báo gì. Nay ba ô đó nhận nhiều giá trị (lặp khóa hoặc nối bằng dấu phẩy).

Bốn chốt:
1. `read_multi_param` đọc được cả hai kiểu gửi, khử trùng, bỏ rỗng, GIỮ thứ tự.
2. Tiến độ mua hàng: hai trạng thái ra HỢP của hai nhóm; hai công ty cũng vậy; một giá trị vẫn
   chạy y như cũ (không phá đường dẫn đã lưu).
3. Tiến độ báo giá: `state` là cột TÍNH — chọn hai nhãn phải ra HỢP (OR) của hai điều kiện;
   nhãn lạ bị bỏ qua chứ không làm rỗng bảng.
4. Xuất Excel dùng chung `_build_query` nên không kiểm riêng — chốt ở test CR-068.
"""
from types import SimpleNamespace

import pytest
from starlette.datastructures import QueryParams

from app.core.auth import get_perm_profile
from app.core.base_controller import read_multi_param
from app.modules.purchase_order.model import PODelivery, POItem, PurchaseOrder
from app.modules.purchase_progress import controller as pp
from app.modules.survey_progress import controller as sp
from app.modules.survey_progress import export as ex
from app.modules.survey_request.model import SurveyRequest, SurveyRequestLine
from app.modules.user.model import User


def req(qs: str):
    """Request giả — `_build_query` chỉ đụng tới `.query_params`."""
    return SimpleNamespace(query_params=QueryParams(qs))


# ── 1. Hàm đọc tham số nhiều giá trị ─────────────────────────────────────────────
def test_read_multi_param_accepts_both_repeated_key_and_comma_joined():
    assert read_multi_param(req("status=a&status=b"), "status") == ["a", "b"]
    assert read_multi_param(req("status=a,b"), "status") == ["a", "b"]
    assert read_multi_param(req("status=a,b&status=c"), "status") == ["a", "b", "c"]


def test_read_multi_param_trims_dedupes_and_keeps_order():
    assert read_multi_param(req("status=%20b%20,a,,b,a"), "status") == ["b", "a"]
    assert read_multi_param(req("status="), "status") == []
    assert read_multi_param(req("other=x"), "status") == []


# ── 2. Tiến độ mua hàng ───────────────────────────────────────────────────────────
@pytest.fixture
def po_viewer(db, cap_quyen):
    user = User(email="pp422@test.local", employee_id=0, is_active=True)
    db.add(user)
    db.flush()
    cap_quyen(user.id, "purchase_order", scope="all", read=True)
    db.commit()
    return user


@pytest.fixture
def four_po_rows(db):
    """4 dòng: (mã, công ty, tiến độ dòng)."""
    data = [
        ("PO001", 1, "ordered"),
        ("PO002", 1, "received"),
        ("PO003", 2, "completed"),
        ("PO004", 3, "ordered"),
    ]
    for code, company_id, status in data:
        po = PurchaseOrder(code=code, status="approved", company_id=company_id,
                           order_date="2026-09-01")
        db.add(po)
        db.flush()
        it = POItem(po_id=po.id, product_code="SP1", qty_order=1, price=1,
                    progress_status=status)
        db.add(it)
        db.flush()
        db.add(PODelivery(po_id=po.id, po_item_id=it.id, delivery_no=1))
    db.commit()


def _po_codes(db, user, qs: str) -> set[str]:
    prof = get_perm_profile(db, user)
    q = pp._build_query(req(qs), db, user, prof, True, True)
    return {po.code for po, _it, _dl in q.all()}


def test_purchase_progress_single_status_still_works(db, po_viewer, four_po_rows):
    assert _po_codes(db, po_viewer, "status=ordered") == {"PO001", "PO004"}


def test_purchase_progress_two_statuses_return_union(db, po_viewer, four_po_rows):
    assert _po_codes(db, po_viewer, "status=ordered,completed") == {"PO001", "PO003", "PO004"}
    assert _po_codes(db, po_viewer, "status=ordered&status=completed") == {"PO001", "PO003", "PO004"}


def test_purchase_progress_two_companies_return_union(db, po_viewer, four_po_rows):
    assert _po_codes(db, po_viewer, "company_id=1") == {"PO001", "PO002"}
    assert _po_codes(db, po_viewer, "company_id=2,3") == {"PO003", "PO004"}
    # Rác không phải số bị bỏ qua, phần số còn lại vẫn lọc
    assert _po_codes(db, po_viewer, "company_id=abc,2") == {"PO003"}


def test_purchase_progress_company_and_status_combine_with_and(db, po_viewer, four_po_rows):
    assert _po_codes(db, po_viewer, "company_id=1,3&status=ordered") == {"PO001", "PO004"}


# ── 3. Tiến độ báo giá — cột TÍNH "Tiến độ dòng" ─────────────────────────────────
@pytest.fixture
def sr_viewer(db, cap_quyen):
    user = User(email="sp422@test.local", employee_id=0, is_active=True)
    db.add(user)
    db.flush()
    cap_quyen(user.id, "survey_request", scope="all", read=True)
    db.commit()
    return user


@pytest.fixture
def four_sr_lines(db):
    """4 dòng ở 4 tiến độ khác nhau: Chưa tiếp nhận · Đã tiếp nhận · Đã tạo YCMH · Hoàn thành."""
    data = [
        ("YCBG1", 1, dict()),
        ("YCBG2", 1, dict(assignee="NV01")),
        ("YCBG3", 2, dict(assignee="NV01", pr_code="PYC001")),
        ("YCBG4", 2, dict(assignee="NV01", pr_code="PYC002", line_status="completed")),
    ]
    for code, company_id, extra in data:
        s = SurveyRequest(code=code, status="processing", company_id=company_id)
        db.add(s)
        db.flush()
        base = dict(survey_request_id=s.id, item_group="Bao bì", assignee="",
                    received_date="", result_due_date="", result_date="",
                    line_status="", no_option=False, pr_code="")
        base.update(extra)
        db.add(SurveyRequestLine(**base))
    db.commit()


def _sr_codes(db, user, qs: str) -> set[str]:
    prof = get_perm_profile(db, user)
    q = sp._build_query(req(qs), db, user, prof, True)
    return {s.code for s, _ln in q.all()}


def test_survey_progress_single_state_still_works(db, sr_viewer, four_sr_lines):
    assert _sr_codes(db, sr_viewer, f"state={ex.STATE_PR_CREATED}") == {"YCBG3"}
    assert _sr_codes(db, sr_viewer, f"state={ex.STATE_DONE}") == {"YCBG4"}


def test_survey_progress_two_states_return_union(db, sr_viewer, four_sr_lines):
    two = f"state={ex.STATE_NOT_RECEIVED},{ex.STATE_DONE}"
    assert _sr_codes(db, sr_viewer, two) == {"YCBG1", "YCBG4"}
    repeated = f"state={ex.STATE_RECEIVED}&state={ex.STATE_PR_CREATED}"
    assert _sr_codes(db, sr_viewer, repeated) == {"YCBG2", "YCBG3"}


def test_survey_progress_unknown_state_is_ignored_not_emptying(db, sr_viewer, four_sr_lines):
    """Nhãn lạ đứng cạnh nhãn thật thì chỉ nhãn thật có tác dụng; toàn nhãn lạ thì không lọc
    (đúng nết cũ của ô một giá trị)."""
    assert _sr_codes(db, sr_viewer, f"state=khong-co,{ex.STATE_DONE}") == {"YCBG4"}
    assert _sr_codes(db, sr_viewer, "state=khong-co") == {"YCBG1", "YCBG2", "YCBG3", "YCBG4"}


def test_survey_progress_two_companies_return_union(db, sr_viewer, four_sr_lines):
    assert _sr_codes(db, sr_viewer, "company_id=1") == {"YCBG1", "YCBG2"}
    assert _sr_codes(db, sr_viewer, "company_id=1,2") == {"YCBG1", "YCBG2", "YCBG3", "YCBG4"}
    assert _sr_codes(db, sr_viewer, f"company_id=1,2&state={ex.STATE_PR_CREATED}") == {"YCBG3"}
