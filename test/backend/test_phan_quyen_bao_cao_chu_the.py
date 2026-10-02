"""Phase 03 — `report_access/service.viewable_keys` theo từng chủ thể (gọi thẳng, không HTTP).

Canh: khớp theo người/phòng chính/phòng kiêm nhiệm/pháp nhân/vai trò; CẤM
thắng CHO PHÉP; dòng thu hồi không tính; hạn hiệu lực; người không chủ thể
nào -> rỗng; số truy vấn CỐ ĐỊNH = 1.
"""
from datetime import date, datetime, timedelta

from sqlalchemy import event

from app.core.auth import get_perm_profile
from app.core.report_keys import ReportKey
from app.core.subject_match import (EFFECT_ALLOW, EFFECT_DENY, SUBJECT_COMPANY,
                                    SUBJECT_DEPARTMENT, SUBJECT_EMPLOYEE, SUBJECT_ROLE)
from app.modules.employee.model import Employee
from app.modules.report_access.model import ReportAccess
from app.modules.report_access.service import viewable_keys
from app.modules.user.model import User

KEY = int(ReportKey.DOCUMENT)
OTHER_KEY = int(ReportKey.WORK)


def _allow(subject_kind: int, subject_id: int, key: int = KEY, **kw) -> ReportAccess:
    return ReportAccess(report_key=key, subject_kind=subject_kind, subject_id=subject_id,
                        effect=EFFECT_ALLOW, reason="t", created_by=0, updated_by=0, **kw)


def _deny(subject_kind: int, subject_id: int, key: int = KEY, **kw) -> ReportAccess:
    return ReportAccess(report_key=key, subject_kind=subject_kind, subject_id=subject_id,
                        effect=EFFECT_DENY, reason="t", created_by=0, updated_by=0, **kw)


def test_khop_theo_nhan_su(db, world):
    actor = world.actor("a1")
    db.add(_allow(SUBJECT_EMPLOYEE, actor.employee.id))
    db.commit()
    assert viewable_keys(db, actor.user) == {KEY}


def test_khop_theo_phong_chinh(db, world):
    actor = world.actor("a1")   # phòng chính A.kt
    db.add(_allow(SUBJECT_DEPARTMENT, world.dept["A.kt"]))
    db.commit()
    assert viewable_keys(db, actor.user) == {KEY}


def test_khop_theo_phong_kiem_nhiem(db, world):
    actor = world.actor("a3")   # phòng chính A.mua
    actor.add_department("A.kt")   # kiêm nhiệm thêm A.kt
    db.add(_allow(SUBJECT_DEPARTMENT, world.dept["A.kt"]))
    db.commit()
    assert viewable_keys(db, actor.user) == {KEY}


def test_khop_theo_phap_nhan(db, world):
    actor = world.actor("a1")   # công ty A
    db.add(_allow(SUBJECT_COMPANY, world.co["A"]))
    db.commit()
    assert viewable_keys(db, actor.user) == {KEY}


def test_khop_theo_vai_tro(db, world):
    actor = world.actor("a1")
    actor.grant("document", scope="all", actions=("read",))   # tạo 1 vai trò thật
    role_id = actor.roles[-1].id
    db.add(_allow(SUBJECT_ROLE, role_id))
    db.commit()
    assert viewable_keys(db, actor.user) == {KEY}


def test_cam_thang_qua_vai_tro_de_len_cho_phep_qua_phong(db, world):
    actor = world.actor("a1")
    actor.grant("document", scope="all", actions=("read",))
    role_id = actor.roles[-1].id
    db.add(_allow(SUBJECT_DEPARTMENT, world.dept["A.kt"]))
    db.add(_deny(SUBJECT_ROLE, role_id))
    db.commit()
    assert viewable_keys(db, actor.user) == set()


def test_cam_tren_nhan_su_de_len_cho_phep_tren_phap_nhan(db, world):
    actor = world.actor("a1")
    db.add(_allow(SUBJECT_COMPANY, world.co["A"]))
    db.add(_deny(SUBJECT_EMPLOYEE, actor.employee.id))
    db.commit()
    assert viewable_keys(db, actor.user) == set()


def test_dong_thu_hoi_khong_tinh_ca_cho_phep_lan_cam(db, world):
    actor = world.actor("a1")
    revoked_allow = _allow(SUBJECT_EMPLOYEE, actor.employee.id, key=KEY)
    revoked_allow.revoked_at = datetime.now()
    db.add(revoked_allow)
    db.commit()
    assert viewable_keys(db, actor.user) == set(), "dòng cho phép đã thu hồi không được tính"

    revoked_deny = _deny(SUBJECT_EMPLOYEE, actor.employee.id, key=OTHER_KEY)
    revoked_deny.revoked_at = datetime.now()
    db.add(revoked_deny)
    db.add(_allow(SUBJECT_EMPLOYEE, actor.employee.id, key=OTHER_KEY))
    db.commit()
    #  Thu hồi dòng CẤM -> thấy LẠI (dòng cho phép cùng khóa vẫn còn sống).
    assert viewable_keys(db, actor.user) == {OTHER_KEY}


def test_valid_to_hom_qua_khong_tinh(db, world):
    actor = world.actor("a1")
    row = _allow(SUBJECT_EMPLOYEE, actor.employee.id)
    row.valid_to = date.today() - timedelta(days=1)
    db.add(row)
    db.commit()
    assert viewable_keys(db, actor.user) == set()


def test_valid_from_ngay_mai_khong_tinh(db, world):
    actor = world.actor("a1")
    row = _allow(SUBJECT_EMPLOYEE, actor.employee.id)
    row.valid_from = date.today() + timedelta(days=1)
    db.add(row)
    db.commit()
    assert viewable_keys(db, actor.user) == set()


def test_valid_trong_han_tinh_binh_thuong(db, world):
    actor = world.actor("a1")
    row = _allow(SUBJECT_EMPLOYEE, actor.employee.id)
    row.valid_from = date.today() - timedelta(days=1)
    row.valid_to = date.today() + timedelta(days=1)
    db.add(row)
    db.commit()
    assert viewable_keys(db, actor.user) == {KEY}


def test_khong_employee_id_khong_vai_tro_ra_rong_khong_no(db):
    emp = Employee(code="NOGRANT", full_name="X", is_active=True)
    db.add(emp)
    db.flush()
    user = User(email="nogrant@test.vn", employee_id=0, is_active=True)
    db.add(user)
    db.commit()
    assert viewable_keys(db, user) == set()


def test_so_truy_van_co_dinh_bang_mot(db, world):
    actor = world.actor("a1")
    db.add(_allow(SUBJECT_EMPLOYEE, actor.employee.id))
    db.commit()

    #  Lấy `profile` TRƯỚC khi đếm — `get_perm_profile` tự nạp nhiều bảng (UserRole,
    #  Permission, UserScope, Employee, phòng kiêm nhiệm...), đếm cả nó vào thì sai
    #  mục tiêu (đo chi phí của CHÍNH `viewable_keys`, không phải của hồ sơ quyền).
    profile = get_perm_profile(db, actor.user)

    statements: list[str] = []

    def _on_exec(conn, cursor, statement, *args):
        statements.append(statement)

    engine = db.get_bind()
    event.listen(engine, "before_cursor_execute", _on_exec)
    try:
        viewable_keys(db, actor.user, profile)
    finally:
        event.remove(engine, "before_cursor_execute", _on_exec)
    assert len(statements) == 1, statements
