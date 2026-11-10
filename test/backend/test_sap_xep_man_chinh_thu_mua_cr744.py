"""duoc-CR-744 (đợt W2) — sắp xếp cột ở các màn danh sách CHÍNH của Thu mua và Báo cáo khảo sát.

Kiểm bằng cách gọi đúng hàm của controller (đường chung của danh sách và xuất Excel) với `sort_by`
thật, cả hai chiều:
- Trạng thái / Hồ sơ / Loại xếp theo DÒNG ĐỜI / thứ tự nhãn, không theo chữ cái của mã tiếng Anh;
- Nhà cung cấp (ĐMH) xếp theo chữ đang hiện (tên, thiếu thì mã);
- ô trống luôn xuống CUỐI cả hai chiều, các dòng trùng giá trị giữ thứ tự `id` giảm dần;
- Báo cáo khảo sát: ô trống không lên đầu khi giảm dần, cột nhãn xếp theo hạng, mọi cột đã bật đều xếp được.

SQLite thay MySQL nên cũng canh luôn việc biểu thức chạy được ở cả hai (không dùng `NULLS LAST`).
"""
import json
from datetime import datetime
from types import SimpleNamespace

import pytest
from starlette.datastructures import QueryParams

from app.modules.purchase_order import controller as po_controller
from app.modules.purchase_order.model import PurchaseOrder
from app.modules.purchase_request import controller as pr_controller
from app.modules.purchase_request.model import PurchaseRequest
from app.modules.survey import controller as survey_controller
from app.modules.survey import service as survey_service
from app.modules.survey.model import Survey
from app.modules.survey_request import controller as sr_controller
from app.modules.survey_request.model import SurveyRequest

PG = {"page": 1, "page_size": 100, "offset": 0, "limit": 100}


class _Req:
    """Chỉ cần `query_params` (QueryParams thật vì bộ lọc gọi `multi_items()`)."""

    def __init__(self, **params):
        self.query_params = QueryParams(params)


def _user(seed, cap_quyen, entity):
    cap_quyen(seed.u_nstm_id, entity, scope="all", read=True)
    return SimpleNamespace(id=seed.u_nstm_id, employee_id=seed.emp_nstm_id)


def _codes(query):
    return [x.code for x in query.all()]


def _list_json(handler, db, user, **params):
    """Gọi handler `GET ""` của controller, trả `data.items` đã bóc phong bì."""
    resp = handler(_Req(**params), PG, db, user)
    return json.loads(resp.body)["data"]["items"]


def _only(items, prefix):
    """Giữ dòng do bài này tạo (mã mở đầu `prefix`): fixture `seed` đã có sẵn vài phiếu."""
    return [x for x in items if x["code"].startswith(prefix)]


# ═════════════════════════ ĐMH ═════════════════════════
def _po(db, seed, code, **kw):
    vals = dict(code=code, company_id=seed.company_id, department_id=seed.dept_id, status="draft")
    vals.update(kw)
    po = PurchaseOrder(**vals)
    db.add(po)
    db.commit()
    return po


@pytest.mark.parametrize("key,field,order", [
    #  Dòng đời: Nháp < Chờ duyệt < Đã duyệt < Đã nhận một phần < Đã nhận đủ < Hoàn thành < Bị trả lại < Từ chối.
    #  Xếp theo chữ cái của mã ra `approved, cancelled, completed, draft…` — sai hẳn.
    ("status", "status", ["draft", "submitted", "approved", "partial", "received", "completed",
                          "rejected", "cancelled"]),
    ("document_status", "document_status", ["none", "partial", "full"]),
])
def test_dmh_trang_thai_ho_so_xep_theo_dong_doi(db, seed, cap_quyen, key, field, order):
    user = _user(seed, cap_quyen, "purchase_order")
    #  Tạo theo thứ tự ĐẢO để thứ tự mặc định (id giảm dần) khác thứ tự cần kiểm.
    for i, value in enumerate(order):
        _po(db, seed, f"PO-{i}", **{field: value})
    got_asc = [getattr(x, field) for x in po_controller._list_query(
        _Req(sort_by=key, sort_dir="asc"), db, user).all()]
    assert got_asc == order
    got_desc = [getattr(x, field) for x in po_controller._list_query(
        _Req(sort_by=key, sort_dir="desc"), db, user).all()]
    assert got_desc == list(reversed(order))


def test_dmh_nha_cung_cap_xep_theo_chu_dang_hien_va_o_trong_cuoi(db, seed, cap_quyen):
    user = _user(seed, cap_quyen, "purchase_order")
    _po(db, seed, "PO-MAI", supplier_name="Mai", supplier_code="Z1")
    #  Đơn chỉ có MÃ NCC: ô bày mã "B-CODE" nên phải đứng giữa "Mai" và "An", không chung chỗ với ô trống.
    _po(db, seed, "PO-MA", supplier_name="", supplier_code="B-CODE")
    _po(db, seed, "PO-AN", supplier_name="An", supplier_code="Z2")
    _po(db, seed, "PO-TRONG", supplier_name="", supplier_code="")
    asc = po_controller._list_query(_Req(sort_by="supplier", sort_dir="asc"), db, user)
    assert _codes(asc) == ["PO-AN", "PO-MA", "PO-MAI", "PO-TRONG"]
    desc = po_controller._list_query(_Req(sort_by="supplier", sort_dir="desc"), db, user)
    assert _codes(desc) == ["PO-MAI", "PO-MA", "PO-AN", "PO-TRONG"]


def test_dmh_ngay_dat_xep_theo_ngay_tao_dung_nhu_o_dang_hien(db, seed, cap_quyen):
    """Ô "Ngày đặt" in `created_at`; giao diện gửi `sort_by=created_at` (không phải `order_date`)."""
    user = _user(seed, cap_quyen, "purchase_order")
    #  `order_date` ngược hẳn `created_at`: sắp theo cột nào ra thứ tự khác nhau.
    _po(db, seed, "PO-CU", order_date="2026-12-01", created_at=datetime(2026, 1, 1, 8, 0))
    _po(db, seed, "PO-GIUA", order_date="2026-06-01", created_at=datetime(2026, 5, 1, 8, 0))
    _po(db, seed, "PO-MOI", order_date="2026-01-01", created_at=datetime(2026, 9, 1, 8, 0))
    assert _codes(po_controller._list_query(_Req(sort_by="created_at", sort_dir="asc"), db, user)) == [
        "PO-CU", "PO-GIUA", "PO-MOI"]
    assert _codes(po_controller._list_query(_Req(sort_by="created_at", sort_dir="desc"), db, user)) == [
        "PO-MOI", "PO-GIUA", "PO-CU"]


def test_dmh_cot_chu_o_trong_xuong_cuoi_ca_hai_chieu_va_khoa_phu_id_giam(db, seed, cap_quyen):
    user = _user(seed, cap_quyen, "purchase_order")
    _po(db, seed, "PO-1", pr_code="")
    _po(db, seed, "PO-2", pr_code="PYC-B")
    _po(db, seed, "PO-3", pr_code="")
    _po(db, seed, "PO-4", pr_code="PYC-A")
    _po(db, seed, "PO-5", pr_code="PYC-B")
    asc = _codes(po_controller._list_query(_Req(sort_by="pr_code", sort_dir="asc"), db, user))
    #  Trùng "PYC-B": id giảm dần (PO-5 trước PO-2); hai ô trống cũng theo id giảm dần ở cuối.
    assert asc == ["PO-4", "PO-5", "PO-2", "PO-3", "PO-1"]
    desc = _codes(po_controller._list_query(_Req(sort_by="pr_code", sort_dir="desc"), db, user))
    assert desc == ["PO-5", "PO-2", "PO-4", "PO-3", "PO-1"]


# ═════════════════════════ YCMH ═════════════════════════
def test_ycmh_trang_thai_xep_theo_dong_doi(db, seed, cap_quyen):
    user = _user(seed, cap_quyen, "purchase_request")
    order = ["draft", "submitted", "approved", "dispatched", "processing", "purchasing", "purchased",
             "completed", "rejected", "cancelled"]
    for i, status in enumerate(order):
        db.add(PurchaseRequest(code=f"PR-{i}", company_id=seed.company_id, department_id=seed.dept_id,
                               status=status, requester="NV", department="Phòng Test"))
    db.commit()
    asc = [x.status for x in pr_controller._list_query(_Req(sort_by="status", sort_dir="asc"), db, user).all()]
    assert asc == order
    desc = [x.status for x in pr_controller._list_query(_Req(sort_by="status", sort_dir="desc"), db, user).all()]
    assert desc == list(reversed(order))


# ═════════════════════════ YCBG ═════════════════════════
def _sr(db, seed, code, **kw):
    vals = dict(code=code, company_id=seed.company_id, department_id=seed.dept_id, status="draft",
                requester="NV", department="Phòng Test")
    vals.update(kw)
    sr = SurveyRequest(**vals)
    db.add(sr)
    db.commit()
    return sr


def test_ycbg_trang_thai_xep_theo_dong_doi(db, seed, cap_quyen):
    user = _user(seed, cap_quyen, "survey_request")
    order = ["draft", "submitted", "approved", "processing", "survey_done", "pr_created", "done",
             "rejected", "cancelled"]
    for i, status in enumerate(order):
        _sr(db, seed, f"SR-{i}", status=status)
    asc = [x["status"] for x in _list_json(sr_controller.list_, db, user, sort_by="status", sort_dir="asc")]
    assert asc == order
    desc = [x["status"] for x in _list_json(sr_controller.list_, db, user, sort_by="status", sort_dir="desc")]
    assert desc == list(reversed(order))


def test_ycbg_ngay_tao_xep_theo_created_at_khong_phai_request_date(db, seed, cap_quyen):
    user = _user(seed, cap_quyen, "survey_request")
    _sr(db, seed, "SR-CU", request_date="2026-12-01", created_at=datetime(2026, 1, 1, 8, 0))
    _sr(db, seed, "SR-MOI", request_date="2026-01-01", created_at=datetime(2026, 9, 1, 8, 0))
    asc = [x["code"] for x in _list_json(sr_controller.list_, db, user, sort_by="created_at", sort_dir="asc")]
    assert asc == ["SR-CU", "SR-MOI"]
    desc = [x["code"] for x in _list_json(sr_controller.list_, db, user, sort_by="created_at", sort_dir="desc")]
    assert desc == ["SR-MOI", "SR-CU"]


def test_ycbg_cot_chu_o_trong_xuong_cuoi(db, seed, cap_quyen):
    user = _user(seed, cap_quyen, "survey_request")
    _sr(db, seed, "SR-1", purpose="")
    _sr(db, seed, "SR-2", purpose="B")
    _sr(db, seed, "SR-3", purpose="A")
    asc = [x["code"] for x in _list_json(sr_controller.list_, db, user, sort_by="purpose", sort_dir="asc")]
    assert asc == ["SR-3", "SR-2", "SR-1"]
    desc = [x["code"] for x in _list_json(sr_controller.list_, db, user, sort_by="purpose", sort_dir="desc")]
    assert desc == ["SR-2", "SR-3", "SR-1"]


# ═════════════════════════ Phiếu khảo sát ═════════════════════════
def _survey(db, code, **kw):
    vals = dict(code=code, survey_type="combined", status="draft")
    vals.update(kw)
    s = Survey(**vals)
    db.add(s)
    db.commit()
    return s


def test_phieu_ks_trang_thai_va_loai_xep_theo_dong_doi_va_nhan(db, seed, cap_quyen):
    user = _user(seed, cap_quyen, "survey")
    statuses = ["draft", "submitted", "approved", "rejected", "cancelled"]
    for i, status in enumerate(statuses):
        _survey(db, f"XS-{i}", status=status)
    asc = [x["status"] for x in _only(_list_json(survey_controller.list_surveys, db, user,
                                                 sort_by="status", sort_dir="asc"), "XS-")]
    assert asc == statuses
    #  Cột Loại: "Khảo sát NCC" < "Khảo sát NCC & SP" < "Khảo sát SP".
    types = ["supplier", "combined", "product"]
    for i, kind in enumerate(types):
        _survey(db, f"XT-{i}", survey_type=kind)
    asc = [x["survey_type"] for x in _only(_list_json(survey_controller.list_surveys, db, user,
                                                      sort_by="survey_type", sort_dir="asc"), "XT-")]
    assert asc == types
    desc = [x["survey_type"] for x in _only(_list_json(survey_controller.list_surveys, db, user,
                                                       sort_by="survey_type", sort_dir="desc"), "XT-")]
    assert desc == list(reversed(types))


def test_phieu_ks_ma_ycbg_rong_xuong_cuoi_ca_hai_chieu(db, seed, cap_quyen):
    """Trước: tăng dần cột "Mã YCBG" là ~54 trang đầu toàn ô trống (2697/2711 phiếu để trống)."""
    user = _user(seed, cap_quyen, "survey")
    _survey(db, "XB-1", sr_code="")
    _survey(db, "XB-2", sr_code="YCBG-B")
    _survey(db, "XB-3", sr_code="")
    _survey(db, "XB-4", sr_code="YCBG-A")
    asc = [x["code"] for x in _only(_list_json(survey_controller.list_surveys, db, user,
                                               sort_by="sr_code", sort_dir="asc"), "XB-")]
    assert asc == ["XB-4", "XB-2", "XB-3", "XB-1"]
    desc = [x["code"] for x in _only(_list_json(survey_controller.list_surveys, db, user,
                                                sort_by="sr_code", sort_dir="desc"), "XB-")]
    assert desc == ["XB-2", "XB-4", "XB-3", "XB-1"]


# ═════════════════════════ Báo cáo khảo sát (sắp xếp trong bộ nhớ) ═════════════════════════
def _row(**kw):
    return {**survey_service._EMPTY_REPORT_ROW, **kw}


@pytest.mark.parametrize("sort_dir,expected", [
    ("asc", [900.0, 12000.5, None, None]),
    ("desc", [12000.5, 900.0, None, None]),
])
def test_bao_cao_cot_so_o_trong_luon_cuoi(sort_dir, expected):
    """Trước: giảm dần "Thành tiền" ra 100/100 dòng đầu trống vì cả rổ trống bị đảo lên đầu."""
    rows = [_row(amount=None, line_id=1), _row(amount=12000.5, line_id=2),
            _row(amount=None, line_id=3), _row(amount=900.0, line_id=4)]
    got = survey_service.sort_report_rows(rows, "amount", sort_dir)
    assert [r["amount"] for r in got] == expected


@pytest.mark.parametrize("sort_dir,expected", [
    ("asc", ["2026-01-02", "2026-03-04", "", ""]),
    ("desc", ["2026-03-04", "2026-01-02", "", ""]),
])
def test_bao_cao_cot_ngay_o_trong_luon_cuoi(sort_dir, expected):
    rows = [_row(reply_date=""), _row(reply_date="2026-03-04"), _row(reply_date="   "),
            _row(reply_date="2026-01-02")]
    got = survey_service.sort_report_rows(rows, "reply_date", sort_dir)
    assert [r["reply_date"].strip() for r in got] == expected


def test_bao_cao_cot_ranh_gioi_so_0_khong_bi_coi_la_o_trong():
    """Số 0 là giá trị thật (cột tiền đã đổi 0 thành None từ `to_report_number`); chỉ None là trống."""
    rows = [_row(vat=None), _row(vat=0.0), _row(vat=8.0)]
    got = survey_service.sort_report_rows(rows, "vat", "desc")
    assert [r["vat"] for r in got] == [8.0, 0.0, None]


def test_bao_cao_cot_nhan_xep_theo_hang_khong_theo_chu_cai_ma():
    rows = [_row(survey_status=s) for s in ("cancelled", "draft", "rejected", "approved", "submitted")]
    asc = survey_service.sort_report_rows(rows, "survey_status", "asc")
    assert [r["survey_status"] for r in asc] == ["draft", "submitted", "approved", "rejected", "cancelled"]

    rows = [_row(survey_type=s) for s in ("product", "combined", "supplier")]
    asc = survey_service.sort_report_rows(rows, "survey_type", "asc")
    assert [r["survey_type"] for r in asc] == ["supplier", "combined", "product"]

    rows = [{**_row(), "kind": k} for k in ("product", "supplier")]
    asc = survey_service.sort_report_rows(rows, "kind", "asc")
    assert [r["kind"] for r in asc] == ["supplier", "product"]

    rows = [_row(line_approve=s) for s in ("Thiếu thông tin", "Không duyệt", "Đã duyệt", "Chờ duyệt")]
    asc = survey_service.sort_report_rows(rows, "line_approve", "asc")
    assert [r["line_approve"] for r in asc] == ["Chờ duyệt", "Đã duyệt", "Không duyệt", "Thiếu thông tin"]
    desc = survey_service.sort_report_rows(rows, "line_approve", "desc")
    assert [r["line_approve"] for r in desc] == ["Thiếu thông tin", "Không duyệt", "Đã duyệt", "Chờ duyệt"]


def test_bao_cao_mac_dinh_la_khoa_phu_o_ca_hai_chieu():
    """Các dòng bằng nhau giữ thứ tự đưa vào (phiếu mới trước) cả khi giảm dần."""
    rows = [_row(reliability="A", line_id=i) for i in range(4)]
    for sort_dir in ("asc", "desc"):
        got = survey_service.sort_report_rows(rows, "reliability", sort_dir)
        assert [r["line_id"] for r in got] == [0, 1, 2, 3]


#  22+ cột giao diện từng không bật sắp xếp dù backend đã nhận (duoc-CR-744 bật hết).
NEWLY_ENABLED_REPORT_KEYS = [
    "contact_person", "contact_phone", "supply_group", "source_of_information", "production_time",
    "nvkd_eval", "invoice_policy", "reliability", "delivery_policy", "defect_return", "invoice_name",
    "spec", "active_ingredient", "requirement_detail", "quote_unit", "volume_range", "shipping_policy",
    "delivery_time", "delivery_place", "sample_ready", "sample_qty", "lab_result", "line_approve_note",
    "nspt_note", "note",
]


@pytest.mark.parametrize("key", NEWLY_ENABLED_REPORT_KEYS)
def test_bao_cao_moi_cot_vua_bat_deu_xep_duoc_o_trong_cuoi(key):
    assert key in survey_service.REPORT_SORTABLE_FIELDS
    is_number = key in survey_service.REPORT_NUMBER_FIELDS
    low, high = (1.0, 2.0) if is_number else ("a", "b")
    blank = None if is_number else ""
    rows = [_row(**{key: blank}), _row(**{key: high}), _row(**{key: low})]
    asc = survey_service.sort_report_rows(rows, key, "asc")
    assert [r[key] for r in asc] == [low, high, blank]
    desc = survey_service.sort_report_rows(rows, key, "desc")
    assert [r[key] for r in desc] == [high, low, blank]
