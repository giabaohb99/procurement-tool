"""Test bộ lọc điều kiện `<field>__<op>=<value>` trong app/core/filter_operators.py.

Dùng PurchaseOrder làm model mẫu vì có đủ kiểu cột: text (code/status), số (company_id),
bool (is_urgent) và ngày lưu dạng chuỗi (order_date).
"""
from types import SimpleNamespace

import pytest
from starlette.datastructures import QueryParams

from app.core.base_controller import apply_filters
from app.modules.purchase_order.model import PurchaseOrder

FILTERABLE = ["code", "status", "supplier_code", "order_date", "company_id", "is_urgent"]


def req(qs: str):
    """Request giả — apply_filters chỉ đụng tới .query_params."""
    return SimpleNamespace(query_params=QueryParams(qs))


def codes(db, qs: str) -> set[str]:
    q = apply_filters(db.query(PurchaseOrder), PurchaseOrder, req(qs), FILTERABLE)
    return {o.code for o in q.all()}


@pytest.fixture
def pos(db):
    """4 đơn mua hàng phủ các trường hợp: giá trị thường, chuỗi rỗng, ngày sớm/muộn."""
    rows = [
        PurchaseOrder(code="PO001", status="approved", supplier_code="NCC01",
                      order_date="2026-01-15", company_id=1, is_urgent=True),
        PurchaseOrder(code="PO002", status="draft", supplier_code="NCC02",
                      order_date="2026-02-20", company_id=2, is_urgent=False),
        PurchaseOrder(code="PO003", status="approved", supplier_code="",
                      order_date="2026-03-25", company_id=3, is_urgent=False),
        PurchaseOrder(code="PO004", status="cancelled", supplier_code="NCC01",
                      order_date="", company_id=10, is_urgent=False),
    ]
    db.add_all(rows)
    db.commit()
    return rows


# ── Không có param operator -> giữ nguyên hành vi cũ ────────────────────────────
def test_param_tran_van_la_like(db, pos):
    # Param trần = LIKE %val% như trước, KHÔNG bị đổi thành so khớp chính xác
    assert codes(db, "supplier_code=NCC") == {"PO001", "PO002", "PO004"}


def test_khong_co_filter_tra_ve_tat_ca(db, pos):
    assert codes(db, "") == {"PO001", "PO002", "PO003", "PO004"}


# ── Operator so khớp ────────────────────────────────────────────────────────────
def test_eq_la_so_khop_chinh_xac(db, pos):
    assert codes(db, "supplier_code__eq=NCC") == set()
    assert codes(db, "supplier_code__eq=NCC01") == {"PO001", "PO004"}


def test_ne_bao_gom_ca_ban_ghi_khac(db, pos):
    assert codes(db, "status__ne=approved") == {"PO002", "PO004"}


def test_contains_va_not_contains(db, pos):
    assert codes(db, "supplier_code__contains=CC0") == {"PO001", "PO002", "PO004"}
    # not_contains giữ lại cả bản ghi trống (PO003 supplier_code = "")
    assert codes(db, "supplier_code__not_contains=NCC01") == {"PO002", "PO003"}


# ── Operator so sánh thứ tự ─────────────────────────────────────────────────────
def test_so_sanh_so_co_ep_kieu(db, pos):
    assert codes(db, "company_id__gt=2") == {"PO003", "PO004"}
    assert codes(db, "company_id__gte=3") == {"PO003", "PO004"}
    assert codes(db, "company_id__lt=2") == {"PO001"}
    assert codes(db, "company_id__lte=2") == {"PO001", "PO002"}


def test_so_sanh_ngay_luu_dang_chuoi(db, pos):
    # order_date là String(10) 'YYYY-MM-DD' -> so sánh chuỗi vẫn đúng thứ tự
    assert codes(db, "order_date__gte=2026-02-01") == {"PO002", "PO003"}


def test_between_ngay(db, pos):
    assert codes(db, "order_date__between=2026-02-01,2026-03-01") == {"PO002"}


def test_between_thieu_mot_dau_van_loc_duoc(db, pos):
    assert codes(db, "order_date__between=2026-03-01,") == {"PO003"}
    assert codes(db, "order_date__between=,2026-02-01") == {"PO001"}


# ── Danh sách & kiểm tra rỗng ───────────────────────────────────────────────────
def test_in_va_not_in(db, pos):
    assert codes(db, "status__in=draft,cancelled") == {"PO002", "PO004"}
    assert codes(db, "status__not_in=draft,cancelled") == {"PO001", "PO003"}


def test_isnull_coi_chuoi_rong_la_trong(db, pos):
    assert codes(db, "supplier_code__isnull=true") == {"PO003"}
    assert codes(db, "supplier_code__isnull=false") == {"PO001", "PO002", "PO004"}


def test_loc_theo_bool(db, pos):
    assert codes(db, "is_urgent__eq=true") == {"PO001"}
    assert codes(db, "is_urgent__eq=false") == {"PO002", "PO003", "PO004"}


# ── AND / OR ────────────────────────────────────────────────────────────────────
def test_nhieu_dieu_kien_mac_dinh_and(db, pos):
    assert codes(db, "status__eq=approved&company_id__gte=3") == {"PO003"}


def test_conjunction_or(db, pos):
    assert codes(db, "status__eq=approved&company_id__gte=3&conjunction=or") == {
        "PO001", "PO003", "PO004"}


def test_param_tran_luon_and_voi_cum_operator(db, pos):
    # supplier_code=NCC01 (LIKE) thu hẹp trước, OR chỉ áp trong cụm operator
    got = codes(db, "supplier_code=NCC01&status__eq=cancelled&company_id__gte=99&conjunction=or")
    assert got == {"PO004"}


# ── Chống lọc bừa / dữ liệu rác ─────────────────────────────────────────────────
def test_bo_qua_field_ngoai_whitelist(db, pos):
    # note không nằm trong FILTERABLE -> param bị bỏ qua, không lọc gì cả
    assert codes(db, "note__contains=abc") == {"PO001", "PO002", "PO003", "PO004"}


def test_bo_qua_operator_khong_hop_le(db, pos):
    assert codes(db, "status__regex=^app") == {"PO001", "PO002", "PO003", "PO004"}


def test_bo_qua_gia_tri_so_khong_hop_le(db, pos):
    # 'abc' không ép được về số -> bỏ điều kiện thay vì ném lỗi 500
    assert codes(db, "company_id__gt=abc") == {"PO001", "PO002", "PO003", "PO004"}


def test_bo_qua_gia_tri_rong(db, pos):
    assert codes(db, "status__eq=") == {"PO001", "PO002", "PO003", "PO004"}


# ── Các màn nối sau: vai trò, phòng ban, phân công phụ trách ────────────────────
def test_loc_dieu_kien_tren_role(db):
    from app.modules.role.controller import FILTERABLE as ROLE_FILTERABLE
    from app.modules.role.model import Role
    db.add_all([Role(code="R1", name="Nhân viên mua hàng"), Role(code="R2", name="Kế toán")])
    db.commit()
    q = apply_filters(db.query(Role), Role, req("name__contains=Nhân"), ROLE_FILTERABLE)
    assert {r.code for r in q.all()} == {"R1"}


def test_loc_dieu_kien_tren_department(db):
    from app.core.filter_operators import apply_operator_filters
    from app.modules.department.model import Department
    from app.modules.department.service import FILTERABLE as DEPT_FILTERABLE
    db.add_all([
        Department(code="PB1", name="Kinh doanh", is_active=True),
        Department(code="PB2", name="Kế toán", is_active=False),
    ])
    db.commit()
    q = apply_operator_filters(db.query(Department), Department,
                               req("is_active__eq=true"), DEPT_FILTERABLE)
    assert {d.code for d in q.all()} == {"PB1"}


def test_loc_dieu_kien_tren_query_co_join(db):
    """Phân công phụ trách lọc trên query JOIN nhiều bảng — điều kiện phải gắn đúng bảng gốc."""
    from app.core.filter_operators import apply_operator_filters
    from app.modules.catalog.model import ItemGroup
    from app.modules.category_assignee.controller import FILTERABLE as CA_FILTERABLE
    from app.modules.category_assignee.model import CategoryAssignee
    db.add_all([ItemGroup(code="PL1", name="Thùng"), ItemGroup(code="PL2", name="Nhãn")])
    db.commit()
    g1, g2 = db.query(ItemGroup).order_by(ItemGroup.id).all()
    db.add_all([
        CategoryAssignee(item_group_id=g1.id, primary_employee_id=7),
        CategoryAssignee(item_group_id=g2.id, primary_employee_id=9),
    ])
    db.commit()

    q = (db.query(CategoryAssignee, ItemGroup.name)
           .outerjoin(ItemGroup, ItemGroup.id == CategoryAssignee.item_group_id))
    q = apply_operator_filters(q, CategoryAssignee, req(f"item_group_id__eq={g1.id}"), CA_FILTERABLE)
    rows = q.all()
    assert len(rows) == 1 and rows[0][1] == "Thùng"
