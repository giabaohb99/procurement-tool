"""ÉP TẢI — CR-662 (kh-TM1-1) + CR-663 (kh-NT1-4): CHUÔNG DUYỆT + BÁO CÁO/TÊN HÓA ĐƠN

Stress test các yêu cầu:
  1. CR-662: Gửi duyệt ĐMH/YCTT → gọi get_approvers_for_entity(new_rules=True) → làm chuông
     cho người duyệt đúng. Ép tải: 200+ user với role/scope khác nhau, xét phạm vi, chặn
     người không duyệt được, quản lý phòng, fallback admin.
  2. CR-663: Lưu/copy/nhập ĐMH ghi `invoice_name` vào cột. Báo cáo gom theo `department_id`,
     hiển thị tên hiện hành (đổi tên không lệch số). Ép tải: 1000+ dòng, rename dept nhiều
     lần, report query count cố định.
"""
from datetime import date
from types import SimpleNamespace

import pytest
from fastapi import BackgroundTasks

from app.core.auth import perm_cache_clear
from app.modules.department.model import Department
from app.modules.employee.model import Employee
from app.modules.notification.model import Notification
from app.modules.notification import service as notif_service
from app.modules.product.model import Product
from app.modules.purchase_order import controller as po_ctl
from app.modules.purchase_order import service as po_service
from app.modules.purchase_order.model import POItem, PurchaseOrder
from app.modules.purchase_order.schema import POItemIn
from app.modules.payment_request import controller as pay_ctl
from app.modules.report import service as report_service
from app.modules.role.model import Permission, Role
from app.modules.user.model import User, UserRole

from lich_lam_viec_factory import count_queries

ACTIONS = dict(can_read=True, can_write=True, can_approve=True)


# ── CR-662: CHUÔNG DUYỆT ĐMH/YCTT ──────────────────────────────────────────────

def _role(db, code, name=None):
    """Tìm hoặc tạo vai trò."""
    role = db.query(Role).filter(Role.code == code).first()
    if not role:
        role = Role(code=code, name=name or code)
        db.add(role)
        db.flush()
    return role


def _grant(db, user_id, role_code, entity, scope="all", approve=True):
    """Gán role cho user với quyền trên entity."""
    role = _role(db, role_code)
    if not db.query(Permission).filter(
        Permission.role_id == role.id, Permission.entity == entity
    ).first():
        db.add(Permission(
            role_id=role.id, entity=entity, scope=scope,
            **{**ACTIONS, "can_approve": approve}
        ))
    if not db.query(UserRole).filter(
        UserRole.user_id == user_id, UserRole.role_id == role.id
    ).first():
        db.add(UserRole(user_id=user_id, role_id=role.id))
    db.commit()
    perm_cache_clear(user_id)


def _user(db, email, code, dept_id, company_id=1, is_active=True):
    """Tạo user + employee."""
    emp = Employee(code=code, full_name=code, company_id=company_id,
                   department_id=dept_id, is_active=is_active)
    db.add(emp)
    db.flush()
    u = User(email=email, employee_id=emp.id, password_hash="x", is_active=is_active)
    db.add(u)
    db.commit()
    return u


def _po(db, code, submitter_id, dept_id, company_id=1, invoice_name="HĐ"):
    """Tạo ĐMH."""
    po = PurchaseOrder(
        code=code, status="draft", supplier_code="NX", supplier_name="NCC",
        company_id=company_id, department_id=dept_id, created_by=submitter_id
    )
    db.add(po)
    db.flush()
    db.add(POItem(
        po_id=po.id, progress_status="Chưa đặt hàng", product_code="SP1",
        product_name="Hàng", item_group="NL", invoice_name=invoice_name,
        required_date="2026-10-25", expected_date="2026-10-25",
        unit="Cái", warehouse_code="K1", qty_request=1, qty_order=1, price=10
    ))
    db.commit()
    return po


@pytest.fixture
def cr662_world(db, seed):
    """Cảnh CR-662: 5 phòng ban, submitter sẵn sàng."""
    depts = {}
    for i in range(5):
        dept = Department(code=f"D{i}", name=f"Phòng {i}", company_id=seed.company_id,
                         is_active=True)
        db.add(dept)
        depts[i] = dept
    db.commit()

    submitter = db.get(User, seed.u_req_id)
    _grant(db, submitter.id, "requester", "purchase_order", scope="all", approve=False)

    return SimpleNamespace(db=db, seed=seed, depts=depts, submitter=submitter)


def test_cr662_1_approve_without_scope_loai(cr662_world):
    """Người có `can_approve` nhưng scope không thấy PO → không nhận chuông."""
    w = cr662_world
    dept_self = w.depts[0]
    dept_other = w.depts[1]

    w.db.query(Notification).delete()
    w.db.commit()

    # User A: quản lý phòng A, scope="dept" chỉ thấy phòng A
    u_a = _user(w.db, "u_a@test", "A", dept_self.id, w.seed.company_id)
    _grant(w.db, u_a.id, "pur_manager", "purchase_order", scope="dept", approve=True)

    # PO ở phòng B → u_a không thấy dù có `can_approve`
    po = _po(w.db, "PO_SCOPE", w.submitter.id, dept_other.id, w.seed.company_id)
    po_ctl.submit_po(po.id, BackgroundTasks(), db=w.db, user=w.submitter)

    # u_a không nhận chuông (phạm vi chặn)
    u_a_notes = w.db.query(Notification).filter(Notification.user_id == u_a.id).all()
    assert len(u_a_notes) == 0


def test_cr662_2_scope_without_approve_loai(cr662_world):
    """Người có scope thấy PO nhưng không có `can_approve` → không nhận."""
    w = cr662_world
    dept = w.depts[0]

    w.db.query(Notification).delete()
    w.db.commit()

    # User: read quyền trên PO nhưng không approve
    u = _user(w.db, "u_ro@test", "ReadOnly", dept.id, w.seed.company_id)
    _grant(w.db, u.id, "viewer", "purchase_order", scope="all", approve=False)

    po = _po(w.db, "PO_RONLY", w.submitter.id, dept.id, w.seed.company_id)
    po_ctl.submit_po(po.id, BackgroundTasks(), db=w.db, user=w.submitter)

    u_notes = w.db.query(Notification).filter(Notification.user_id == u.id).all()
    assert len(u_notes) == 0


def test_cr662_3_both_approve_and_scope_get_bell(cr662_world):
    """Người vừa có `can_approve` vừa phạm vi thấy → nhận chuông."""
    w = cr662_world
    dept = w.depts[0]

    w.db.query(Notification).delete()
    w.db.commit()

    u = _user(w.db, "u_both@test", "Both", dept.id, w.seed.company_id)
    _grant(w.db, u.id, "pur_manager", "purchase_order", scope="all", approve=True)

    po = _po(w.db, "PO_BOTH", w.submitter.id, dept.id, w.seed.company_id)
    po_ctl.submit_po(po.id, BackgroundTasks(), db=w.db, user=w.submitter)

    u_notes = w.db.query(Notification).filter(Notification.user_id == u.id).all()
    assert len(u_notes) > 0


def test_cr662_4_inactive_user_no_bell(cr662_world):
    """Người không active (is_active=False) → không nhận dù đủ quyền."""
    w = cr662_world
    dept = w.depts[0]

    w.db.query(Notification).delete()
    w.db.commit()

    u = _user(w.db, "u_dead@test", "Inactive", dept.id, w.seed.company_id, is_active=False)
    _grant(w.db, u.id, "pur_manager", "purchase_order", scope="all", approve=True)

    po = _po(w.db, "PO_DEAD", w.submitter.id, dept.id, w.seed.company_id)
    po_ctl.submit_po(po.id, BackgroundTasks(), db=w.db, user=w.submitter)

    u_notes = w.db.query(Notification).filter(Notification.user_id == u.id).all()
    assert len(u_notes) == 0


def test_cr662_5_vua_admin_vua_manager_van_nhan(cr662_world):
    """CR-662 FIX: người vừa có role admin vừa role manager VẪN nhận (không bị loại oan).

    Cũ (pre-CR-662): có thêm role admin → bị loại.
    Mới (post-CR-662): chỉ loại nếu admin mà không có role thường nào.
    """
    w = cr662_world
    dept = w.depts[0]

    w.db.query(Notification).delete()
    w.db.commit()

    u = _user(w.db, "u_both_admin@test", "BothAdmin", dept.id, w.seed.company_id)
    # Gán cả hai vai trò
    _grant(w.db, u.id, "admin", "purchase_order", approve=True)
    _grant(w.db, u.id, "pur_manager", "purchase_order", scope="all", approve=True)

    po = _po(w.db, "PO_ADM_MGR", w.submitter.id, dept.id, w.seed.company_id)
    po_ctl.submit_po(po.id, BackgroundTasks(), db=w.db, user=w.submitter)

    u_notes = w.db.query(Notification).filter(Notification.user_id == u.id).all()
    # Must receive notification (CR-662 fix)
    assert len(u_notes) > 0


def test_cr662_6_no_eligible_fallback_to_admin(cr662_world):
    """Không ai có vai trò thường nào có `can_approve` → rơi về admin có quyền."""
    w = cr662_world
    dept = w.depts[0]

    w.db.query(Notification).delete()
    w.db.commit()

    # Xóa tất cả permission pur_manager trên purchase_order
    pm_role = w.db.query(Role).filter(Role.code == "pur_manager").first()
    if pm_role:
        w.db.query(Permission).filter(
            Permission.role_id == pm_role.id,
            Permission.entity == "purchase_order"
        ).delete()
    w.db.commit()

    # Admin duy nhất
    u_admin = _user(w.db, "u_adm_only@test", "AdminOnly", dept.id, w.seed.company_id)
    _grant(w.db, u_admin.id, "admin", "purchase_order", approve=True)

    po = _po(w.db, "PO_ADMONLY", w.submitter.id, dept.id, w.seed.company_id)
    po_ctl.submit_po(po.id, BackgroundTasks(), db=w.db, user=w.submitter)

    # Admin vẫn nhận (fallback)
    adm_notes = w.db.query(Notification).filter(Notification.user_id == u_admin.id).all()
    assert len(adm_notes) > 0


def test_cr662_7_new_rules_true_vs_false_backward_compat(cr662_world):
    """new_rules=False (cũ) vs new_rules=True (mới) trên dữ liệu cũ: hành vi khác nhau."""
    w = cr662_world

    # Dữ liệu: người có vừa admin vừa pur_manager
    u = _user(w.db, "u_compat@test", "Compat", w.depts[0].id, w.seed.company_id)
    _grant(w.db, u.id, "admin", "purchase_order", approve=True)
    _grant(w.db, u.id, "pur_manager", "purchase_order", approve=True)

    from app.modules.notification import service as notif_svc

    # Cũ: loại vì có role admin
    old_approvers = notif_svc.get_approvers_for_entity(w.db, "purchase_order", new_rules=False)
    old_ids = {usr.id for usr in old_approvers}

    # Mới: giữ vì có role manager
    new_approvers = notif_svc.get_approvers_for_entity(
        w.db, "purchase_order", doc_id=0, new_rules=True)
    new_ids = {usr.id for usr in new_approvers}

    # u phải ở mới nhưng không ở cũ
    assert u.id not in old_ids
    assert u.id in new_ids


def test_cr662_8_payment_request_approvers_called(cr662_world):
    """get_approvers_for_entity(new_rules=True) được gọi cho payment_request entity."""
    w = cr662_world

    from app.modules.notification import service as notif_svc

    # Chỉ kiểm tra rằng hàm này hoạt động với entity payment_request (không lỗi)
    approvers = notif_svc.get_approvers_for_entity(w.db, "payment_request", new_rules=True)

    # Phải trả về danh sách (có thể rỗng hoặc có người)
    assert isinstance(approvers, list)


def test_cr662_9_query_count_constant_20_vs_200_users(cr662_world):
    """get_approvers_for_entity query count: 20 users = 200 users (constant, no N+1)."""
    w = cr662_world

    from app.modules.notification import service as notif_svc

    # Tạo 20 user với pur_manager role
    for i in range(20):
        u = _user(w.db, f"u20_{i:02d}@test", f"U20_{i:02d}", w.depts[i % 5].id, w.seed.company_id)
        _grant(w.db, u.id, "pur_manager", "purchase_order", scope="all", approve=True)

    result1, queries1 = count_queries(w.db, lambda: notif_svc.get_approvers_for_entity(
        w.db, "purchase_order", doc_id=0, new_rules=True))
    notif_svc.get_approvers_for_entity(w.db, "purchase_order", doc_id=0, new_rules=True)  # warm cache

    # Thêm 180 user nữa
    for i in range(200):
        u = _user(w.db, f"u200_{i:03d}@test", f"U200_{i:03d}", w.depts[i % 5].id, w.seed.company_id)
        _grant(w.db, u.id, "pur_manager", "purchase_order", scope="all", approve=True)

    result2, queries2 = count_queries(w.db, lambda: notif_svc.get_approvers_for_entity(
        w.db, "purchase_order", doc_id=0, new_rules=True))

    # Query count phải giống nhau (±1)
    assert abs(len(queries1) - len(queries2)) <= 1, f"20 users: {len(queries1)} queries, 200 users: {len(queries2)} queries"


# ── CR-663: TÊN HÓA ĐƠN + BÁO CÁO THEO ID PHÒNG ─────────────────────────────────

def _po_cr663(db, code, dept_id=None, company_id=1, status="draft", department_id=None, **kw):
    """Tạo ĐMH cho CR-663."""
    # Allow both dept_id and department_id for flexibility
    final_dept_id = department_id if department_id is not None else dept_id
    po = PurchaseOrder(
        code=code, status=status, supplier_code="NX", company_id=company_id,
        department_id=final_dept_id, **kw
    )
    db.add(po)
    db.commit()
    return po


def _line(**kw):
    base = dict(product_code="SP663", product_name="Hàng 663", qty_order=1, price=10, unit="Cái")
    return POItemIn(**{**base, **kw})


@pytest.fixture
def cr663_world(db, seed):
    """Cảnh CR-663: 5 phòng, 200 ĐMH."""
    depts = {}
    for i in range(5):
        dept = Department(code=f"D{i}", name=f"Phòng {i}", company_id=seed.company_id,
                         is_active=True)
        db.add(dept)
        depts[i] = dept
    db.commit()

    # Tạo product với invoice_name
    for i in range(10):
        db.add(Product(code=f"SP663_{i}", name=f"Hàng {i}", invoice_name=f"HĐ_{i}"))
    db.commit()

    return SimpleNamespace(db=db, seed=seed, depts=depts)


def test_cr663_ghi_invoice_name_luc_luu(cr663_world):
    """Lưu ĐMH → `invoice_name` từ master ghi vào cột (không chỉ suy lúc trả)."""
    w = cr663_world
    w.db.add(Product(code="SP_TEST", name="Test", invoice_name="Tên HĐ từ master"))
    w.db.commit()

    po = _po_cr663(w.db, "PO_INV1", w.depts[0].id, w.seed.company_id)
    po_service._save_items(w.db, po, [_line(product_code="SP_TEST")], 1)

    items = w.db.query(POItem).filter(POItem.po_id == po.id).all()
    assert items[0].invoice_name == "Tên HĐ từ master"


def test_cr663_nguoi_dung_go_tay_thi_giu(cr663_world):
    """User gõ tay invoice_name → giữ nguyên (không ghi đè)."""
    w = cr663_world
    w.db.add(Product(code="SP_KEEP", name="Keep", invoice_name="Master name"))
    w.db.commit()

    po = _po_cr663(w.db, "PO_INV2", w.depts[0].id, w.seed.company_id)
    po_service._save_items(w.db, po, [_line(product_code="SP_KEEP", invoice_name="User typed")], 1)

    items = w.db.query(POItem).filter(POItem.po_id == po.id).all()
    assert items[0].invoice_name == "User typed"


def test_cr663_master_khong_co_ten_thi_de_trong(cr663_world):
    """Master không có invoice_name → để trống (không ghi master name)."""
    w = cr663_world
    w.db.add(Product(code="SP_EMPTY", name="Empty", invoice_name=""))
    w.db.commit()

    po = _po_cr663(w.db, "PO_INV3", w.depts[0].id, w.seed.company_id)
    po_service._save_items(w.db, po, [_line(product_code="SP_EMPTY")], 1)

    items = w.db.query(POItem).filter(POItem.po_id == po.id).all()
    assert items[0].invoice_name == ""


def test_cr663_update_dong_cu_bu_invoice_name(cr663_world):
    """Update dòng cũ có để trống invoice_name → bù từ master."""
    w = cr663_world
    w.db.add(Product(code="SP_UPDATE", name="Update", invoice_name="Tên cập nhật"))
    w.db.commit()

    po = _po_cr663(w.db, "PO_INV4", w.depts[0].id, w.seed.company_id)
    po_service._save_items(w.db, po, [_line(product_code="SP_UPDATE")], 1)

    items = w.db.query(POItem).filter(POItem.po_id == po.id).all()
    item_id = items[0].id
    item = items[0]
    item.invoice_name = ""
    w.db.commit()

    # Update lại cùng item
    po_service._save_items(w.db, po, [_line(id=item_id, product_code="SP_UPDATE")], 1)
    items = w.db.query(POItem).filter(POItem.id == item_id).all()
    assert items[0].invoice_name == "Tên cập nhật"


def test_cr663_1000_dong_tao_nhanh(cr663_world):
    """Tạo 1000 dòng ĐMH → không lỗi, tất cả ghi invoice_name."""
    w = cr663_world
    dept = w.depts[0]

    # Tạo 100 product
    for i in range(100):
        w.db.add(Product(code=f"SP_{i:03d}", name=f"Item {i}", invoice_name=f"HĐ_{i}"))
    w.db.commit()

    # Tạo 10 ĐMH, mỗi cái 100 dòng
    for po_idx in range(10):
        po = _po_cr663(w.db, f"PO_1K_{po_idx}", dept.id, w.seed.company_id)
        lines = [_line(product_code=f"SP_{i:03d}") for i in range(100)]
        po_service._save_items(w.db, po, lines, 1)

    total_items = w.db.query(POItem).count()
    assert total_items == 1000

    # Xác minh tất cả có invoice_name
    items_no_name = w.db.query(POItem).filter(POItem.invoice_name == "").count()
    assert items_no_name == 0


def test_cr663_doi_ten_phong_gom_theo_id(cr663_world):
    """Đổi tên phòng: báo cáo gom theo department_id, hiển thị tên mới."""
    w = cr663_world
    dept = w.depts[0]

    # Tạo 2 ĐMH, mỗi cái approved
    for i in range(2):
        po = _po_cr663(w.db, f"PO_RENAME_{i}", dept.id, w.seed.company_id,
                      status="approved", order_date=date(2026, 9, i + 1))
        w.db.add(POItem(po_id=po.id, product_code="SP1", item_group="X", qty_order=1, price=10))
    w.db.commit()

    # Gom theo tên cũ
    rows_old = report_service.compute_dept_range(w.db, "2026-09-01", "2026-09-30",
                                                w.seed.company_id)
    old_name = [r["key"] for r in rows_old if r["department_id"] == dept.id]

    # Đổi tên phòng
    dept.name = "Phòng mới"
    w.db.commit()

    # Gom theo tên mới
    rows_new = report_service.compute_dept_range(w.db, "2026-09-01", "2026-09-30",
                                                w.seed.company_id)
    new_name = [r["key"] for r in rows_new if r["department_id"] == dept.id]

    assert old_name[0] == "Phòng 0"
    assert new_name[0] == "Phòng mới"
    # Số đơn giống nhau (gom theo ID)
    assert len(old_name) == len(new_name)


def test_cr663_report_500_po_query_count_co_dinh(cr663_world):
    """Report 500 ĐMH: query count cố định (không N+1)."""
    w = cr663_world

    # Tạo 50 ĐMH, mỗi cái 10 dòng
    for po_idx in range(50):
        po = _po_cr663(w.db, f"PO_QRY_{po_idx:03d}", w.depts[po_idx % 5].id,
                      w.seed.company_id, status="approved",
                      order_date=date(2026, 9, (po_idx % 28) + 1))
        for line_idx in range(10):
            w.db.add(POItem(po_id=po.id, product_code=f"SP{line_idx % 10}", item_group="X",
                           qty_order=1, price=10))
    w.db.commit()

    result1, queries1 = count_queries(w.db, lambda: report_service.compute_dept_range(
        w.db, "2026-09-01", "2026-09-30", w.seed.company_id))
    report_service.compute_dept_range(w.db, "2026-09-01", "2026-09-30",
                                     w.seed.company_id)  # làm nóng cache

    # Thêm 450 ĐMH nữa
    for po_idx in range(50, 500):
        po = _po_cr663(w.db, f"PO_QRY_{po_idx:03d}", w.depts[po_idx % 5].id,
                      w.seed.company_id, status="approved",
                      order_date=date(2026, 9, (po_idx % 28) + 1))
        for line_idx in range(10):
            w.db.add(POItem(po_id=po.id, product_code=f"SP{line_idx % 10}", item_group="X",
                           qty_order=1, price=10))
    w.db.commit()

    result2, queries2 = count_queries(w.db, lambda: report_service.compute_dept_range(
        w.db, "2026-09-01", "2026-09-30", w.seed.company_id))

    # Query count phải giống nhau (±1)
    assert abs(len(queries1) - len(queries2)) <= 1


def test_cr663_khong_co_id_phong_dung_ten_chup(cr663_world):
    """ĐMH không có department_id → dùng department snapshot name."""
    w = cr663_world
    po = _po_cr663(w.db, "PO_NOID", None, w.seed.company_id, department_id=0,
                  status="approved", order_date=date(2026, 9, 1), department="Phòng ngoài")
    w.db.add(POItem(po_id=po.id, product_code="SP1", item_group="X", qty_order=1, price=10))
    w.db.commit()

    rows = report_service.compute_dept_range(w.db, "2026-09-01", "2026-09-30",
                                           w.seed.company_id)
    matched = [r for r in rows if r["department_id"] == 0]
    assert len(matched) == 1
    assert matched[0]["key"] == "Phòng ngoài"


def test_cr663_invoice_name_qua_255_ky_tu_bi_chan_o_cong_vao():
    """Tên trên hóa đơn dài quá 255 ký tự phải bị chặn ở lớp schema (422), không xuống tới MySQL.

    SQLite không ép độ dài VARCHAR nên không thử ở tầng service được; cổng thật là `Str255`
    của `POItemIn` và `ProductCreate/ProductUpdate` — thiếu nó thì MySQL strict trả 500.
    """
    from pydantic import ValidationError
    from app.modules.product.schema import ProductCreate, ProductUpdate

    long_name = "x" * 256
    with pytest.raises(ValidationError):
        POItemIn(invoice_name=long_name)
    with pytest.raises(ValidationError):
        ProductCreate(code="SP_LONG", name="Long", invoice_name=long_name)
    with pytest.raises(ValidationError):
        ProductUpdate(invoice_name=long_name)
    assert POItemIn(invoice_name="x" * 255).invoice_name == "x" * 255
