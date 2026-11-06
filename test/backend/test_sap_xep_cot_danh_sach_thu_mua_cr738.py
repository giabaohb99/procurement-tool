"""duoc-CR-738 — SẮP XẾP THEO CỘT TÍNH TOÁN Ở DANH SÁCH YCMH / ĐMH.

Cột *Tổng tiền* (YCMH), *Tiền hàng* / *Nhà cung cấp* / *Phòng xử lý* / *Trưởng phòng phê duyệt*
(ĐMH) không phải cột vật lý nên `apply_sort_from_request` từng im lặng bỏ qua `sort_by`.
Bài này gọi đúng `_list_query` của controller (đường chung của danh sách và xuất Excel) với
`sort_by` thật và kiểm thứ tự ra; SQLite thay MySQL nên cũng canh luôn việc biểu thức chạy
được ở cả hai (truy vấn con tương quan, không dùng `NULLS LAST`).
"""
from types import SimpleNamespace

from starlette.datastructures import QueryParams

from app.modules.department.model import Department
from app.modules.employee.model import Employee
from app.modules.purchase_order import controller as po_controller
from app.modules.purchase_order.model import POItem, PurchaseOrder
from app.modules.purchase_request import controller as pr_controller
from app.modules.purchase_request.model import PurchaseRequest, PurchaseRequestItem


class _Req:
    """Chỉ cần `query_params` (QueryParams thật vì bộ lọc gọi `multi_items()`)."""

    def __init__(self, **params):
        self.query_params = QueryParams(params)


def _user(db, seed, cap_quyen, entity):
    cap_quyen(seed.u_nstm_id, entity, scope="all", read=True)
    return SimpleNamespace(id=seed.u_nstm_id, employee_id=seed.emp_nstm_id)


def _codes(query):
    return [x.code for x in query.all()]


# ── YCMH ─────────────────────────────────────────────────────────────────────────────────
def _make_pr(db, seed, code, amounts):
    pr = PurchaseRequest(code=code, company_id=seed.company_id, department_id=seed.dept_id,
                         status="draft", requester="NV", department="Phòng Test")
    db.add(pr)
    db.flush()
    for i, amount in enumerate(amounts):
        db.add(PurchaseRequestItem(pr_id=pr.id, product_code=f"{code}-{i}", product_name="Hàng",
                                   unit="Cái", qty=1, price=amount, amount=amount))
    db.commit()
    return pr


def test_ycmh_sap_theo_tong_tien_tang_giam(db, seed, cap_quyen):
    user = _user(db, seed, cap_quyen, "purchase_request")
    _make_pr(db, seed, "PR-A", [100, 200])   # 300
    _make_pr(db, seed, "PR-B", [50])         # 50
    _make_pr(db, seed, "PR-C", [])           # 0, chưa có dòng
    _make_pr(db, seed, "PR-D", [1000])       # 1000

    asc = pr_controller._list_query(_Req(sort_by="total", sort_dir="asc"), db, user)
    assert _codes(asc) == ["PR-C", "PR-B", "PR-A", "PR-D"]
    desc = pr_controller._list_query(_Req(sort_by="total", sort_dir="desc"), db, user)
    assert _codes(desc) == ["PR-D", "PR-A", "PR-B", "PR-C"]


def test_ycmh_sap_theo_id_va_khoa_la_ve_mac_dinh(db, seed, cap_quyen):
    user = _user(db, seed, cap_quyen, "purchase_request")
    for code in ("PR-1", "PR-2", "PR-3"):
        _make_pr(db, seed, code, [10])
    assert _codes(pr_controller._list_query(_Req(sort_by="id", sort_dir="asc"), db, user)) == ["PR-1", "PR-2", "PR-3"]
    assert _codes(pr_controller._list_query(_Req(sort_by="id", sort_dir="desc"), db, user)) == ["PR-3", "PR-2", "PR-1"]
    # khóa lạ -> bỏ qua, về mặc định id giảm dần (không nổ)
    assert _codes(pr_controller._list_query(_Req(sort_by="khong_co_cot_nay", sort_dir="asc"), db, user)) == [
        "PR-3", "PR-2", "PR-1"]


# ── ĐMH ──────────────────────────────────────────────────────────────────────────────────
def _make_po(db, seed, code, *, lines=(), supplier="", handler_dept_id=0, approver_id=0):
    po = PurchaseOrder(code=code, company_id=seed.company_id, department_id=seed.dept_id, status="draft",
                       supplier_name=supplier, handler_dept_id=handler_dept_id,
                       approver_employee_id=approver_id)
    db.add(po)
    db.flush()
    for i, (qty, price, vat, rate) in enumerate(lines):
        db.add(POItem(po_id=po.id, product_code=f"{code}-{i}", product_name="Hàng", unit="Cái",
                      qty_order=qty, price=price, vat=vat, exchange_rate=rate))
    db.commit()
    return po


def test_dmh_sap_theo_tien_hang_co_vat_va_ty_gia(db, seed, cap_quyen):
    user = _user(db, seed, cap_quyen, "purchase_order")
    _make_po(db, seed, "PO-A", lines=[(10, 100, 10, 1)])           # 1100
    _make_po(db, seed, "PO-B", lines=[(1, 100, 0, 0)])             # tỷ giá 0 đọc thành 1 -> 100
    _make_po(db, seed, "PO-C", lines=[(2, 10, 0, 25000)])          # 500000 (ngoại tệ quy đổi)
    _make_po(db, seed, "PO-D", lines=[])                           # 0

    asc = po_controller._list_query(_Req(sort_by="amount", sort_dir="asc"), db, user)
    assert _codes(asc) == ["PO-D", "PO-B", "PO-A", "PO-C"]
    desc = po_controller._list_query(_Req(sort_by="amount", sort_dir="desc"), db, user)
    assert _codes(desc) == ["PO-C", "PO-A", "PO-B", "PO-D"]


def test_dmh_sap_theo_nha_cung_cap(db, seed, cap_quyen):
    user = _user(db, seed, cap_quyen, "purchase_order")
    _make_po(db, seed, "PO-1", supplier="Công ty Mai")
    _make_po(db, seed, "PO-2", supplier="Công ty An")
    _make_po(db, seed, "PO-3", supplier="Công ty Bình")
    assert _codes(po_controller._list_query(_Req(sort_by="supplier", sort_dir="asc"), db, user)) == [
        "PO-2", "PO-3", "PO-1"]
    assert _codes(po_controller._list_query(_Req(sort_by="supplier", sort_dir="desc"), db, user)) == [
        "PO-1", "PO-3", "PO-2"]


def test_dmh_sap_theo_phong_xu_ly_va_nguoi_duyet(db, seed, cap_quyen):
    user = _user(db, seed, cap_quyen, "purchase_order")
    phong_b = Department(code="DEPT-B", name="Phòng Bình", company_id=seed.company_id, is_active=True)
    phong_z = Department(code="DEPT-Z", name="Phòng Zeta", company_id=seed.company_id, is_active=True)
    db.add_all([phong_b, phong_z])
    db.flush()
    nv_a = Employee(code="NV-A", full_name="An", company_id=seed.company_id, department_id=seed.dept_id,
                    is_active=True)
    nv_t = Employee(code="NV-T", full_name="Tâm", company_id=seed.company_id, department_id=seed.dept_id,
                    is_active=True)
    db.add_all([nv_a, nv_t])
    db.flush()
    # tạo B trước Z để thứ tự mặc định (id giảm dần = Z, B) KHÁC thứ tự tăng dần cần kiểm
    _make_po(db, seed, "PO-B", handler_dept_id=phong_b.id, approver_id=nv_a.id)
    _make_po(db, seed, "PO-Z", handler_dept_id=phong_z.id, approver_id=nv_t.id)

    assert _codes(po_controller._list_query(_Req(sort_by="handler_dept_name", sort_dir="asc"), db, user)) == [
        "PO-B", "PO-Z"]
    assert _codes(po_controller._list_query(_Req(sort_by="handler_dept_name", sort_dir="desc"), db, user)) == [
        "PO-Z", "PO-B"]
    assert _codes(po_controller._list_query(_Req(sort_by="approver_name", sort_dir="asc"), db, user)) == [
        "PO-B", "PO-Z"]
    assert _codes(po_controller._list_query(_Req(sort_by="approver_name", sort_dir="desc"), db, user)) == [
        "PO-Z", "PO-B"]


def test_dmh_sap_theo_id_cot_vat_ly_va_khoa_la(db, seed, cap_quyen):
    user = _user(db, seed, cap_quyen, "purchase_order")
    for code in ("PO-1", "PO-2", "PO-3"):
        _make_po(db, seed, code)
    assert _codes(po_controller._list_query(_Req(sort_by="id", sort_dir="asc"), db, user)) == [
        "PO-1", "PO-2", "PO-3"]
    assert _codes(po_controller._list_query(_Req(sort_by="code", sort_dir="desc"), db, user)) == [
        "PO-3", "PO-2", "PO-1"]
    assert _codes(po_controller._list_query(_Req(sort_by="khong_co_cot_nay"), db, user)) == [
        "PO-3", "PO-2", "PO-1"]


def test_dmh_sap_theo_nguoi_tao_va_cong_ty_chay_duoc(db, seed, cap_quyen):
    """Hai cột phụ ẩn sẵn: chỉ cần câu SQL biên dịch + chạy được, không nổ."""
    user = _user(db, seed, cap_quyen, "purchase_order")
    _make_po(db, seed, "PO-1")
    for key in ("company_name", "created_by_name"):
        assert _codes(po_controller._list_query(_Req(sort_by=key, sort_dir="desc"), db, user)) == ["PO-1"]


def test_bang_chon_ket_qua_khao_sat_sap_theo_id_va_gia(db):
    """Bảng chọn kết quả khảo sát ở màn Xử lý: cột ID tự thêm gửi `sort_by=id`, cột Đơn giá gửi
    `price_by_volume`. Trước đây `id` không có trong danh sách nên bấm tăng dần vẫn ra mới nhất trước."""
    from app.modules.survey.model import Survey, SurveyProductLine
    from app.modules.survey_request import service as sr_service

    sv = Survey(code="KS-738", survey_type="product", status="approved", item_group="Thùng")
    db.add(sv)
    db.flush()
    for name, price in (("Thùng A", 300), ("Thùng B", 100), ("Thùng C", 200)):
        db.add(SurveyProductLine(survey_id=sv.id, supplier_code="NCC-A", product_name=name,
                                 price_by_volume=price, line_approve="Đã duyệt"))
    db.commit()

    rows, _ = sr_service.available_survey_lines(db, search="Thùng", sort_by="id", sort_dir="asc")
    assert [r.product_name for r in rows] == ["Thùng A", "Thùng B", "Thùng C"]
    rows, _ = sr_service.available_survey_lines(db, search="Thùng", sort_by="price_by_volume", sort_dir="asc")
    assert [r.product_name for r in rows] == ["Thùng B", "Thùng C", "Thùng A"]
    rows, _ = sr_service.available_survey_lines(db, search="Thùng")
    assert [r.product_name for r in rows] == ["Thùng C", "Thùng B", "Thùng A"]
