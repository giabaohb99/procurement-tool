"""Quá trình công tác — QUYỀN, PHẠM VI, IDOR, `/me`, TỆP (phase 02/03, plan
`261003-0837-qua-trinh-lam-viec-nhan-su`).

Gọi thẳng hàm controller với vai trò THẬT cấp qua `world.grant(...)` (khuôn
`test_nghi_phep_dinh_kem.py`), để lớp vai trò lẫn lớp phạm vi đều chạy đúng như
lúc chạy thật. `world` dựng sẵn hai pháp nhân × bốn phòng × bảy nhân sự
(`scope_factory.py`).
"""
import inspect
import json
from datetime import date
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.core.auth import perm_cache_clear, require
from app.modules.attachment import controller as ac
from app.modules.attachment.model import FileLink, StoredFile
from app.modules.employee import work_history_access, work_history_controller as whc
from app.modules.employee import work_history_service as whs
from app.modules.employee.work_history_model import EmployeeWorkHistory
from app.seed import ensure_admin_role

ACTOR = 1


def _row(db, eid, event_type=3, from_date=date(2025, 1, 1), department_id=0, **kw) -> EmployeeWorkHistory:
    row = EmployeeWorkHistory(employee_id=eid, event_type=event_type, from_date=from_date,
                              department_id=department_id, created_by=ACTOR, updated_by=ACTOR, **kw)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def _attach_fake_file(db, entity_id: int, entity: str = "employee_work_history"):
    f = StoredFile(filename="qd.pdf", file_key="k", url="u", content_type="application/pdf",
                  size=1, sha256="s")
    db.add(f)
    db.flush()
    lk = FileLink(file_id=f.id, entity=entity, entity_id=entity_id, doc_type="", sort_order=0)
    db.add(lk)
    db.commit()
    return lk, f


def _make_admin(db, user) -> None:
    from app.modules.user.model import UserRole
    role = ensure_admin_role(db)
    db.add(UserRole(user_id=user.id, role_id=role.id))
    db.commit()
    perm_cache_clear(user.id)


# ══════════════════════════════════════════════════════════════════════════════
#  Quyền / IDOR
# ══════════════════════════════════════════════════════════════════════════════

def test_thieu_quyen_doc_thi_403(world):
    stranger = SimpleNamespace(id=999, employee_id=0)
    with pytest.raises(HTTPException) as e:
        require("employee", "read")(user=stranger, db=world.db)
    assert e.value.status_code == 403


def test_co_doc_nhung_ngoai_pham_vi_thi_404(world):
    """Phòng khác, scope `dept` — `a3` ở A.mua, `a1` chỉ thấy A.kt."""
    a1 = world.grant("a1", "employee", scope="dept", actions=("read",))
    with pytest.raises(HTTPException) as e:
        whc.list_work_history(world.emp["a3"], world.db, a1.user)
    assert e.value.status_code == 404


def test_co_doc_khong_ghi_thi_403_tren_cua_ghi(world):
    a1 = world.grant("a1", "employee", scope="company", actions=("read",))
    with pytest.raises(HTTPException) as e:
        require("employee", "write")(user=a1.user, db=world.db)
    assert e.value.status_code == 403


def test_hid_nguoi_khac_qua_eid_nguoi_trong_pham_vi_thi_404(world):
    row_b = _row(world.db, world.emp["a3"])
    a2 = world.grant("a2", "employee", scope="company", actions=("read", "write"))
    with pytest.raises(HTTPException) as e:
        whs.get_row_in_employee(world.db, world.emp["a1"], row_b.id)
    assert e.value.status_code == 404
    #  Cùng chốt phải chạy khi đi qua cửa PATCH thật (eid của a1 — trong phạm vi
    #  của a2 — nhưng `hid` lại thuộc a3).
    from app.modules.employee.work_history_schema import WorkHistoryUpdate
    with pytest.raises(HTTPException) as e2:
        whc.update_work_history(world.emp["a1"], row_b.id, WorkHistoryUpdate(note="x"),
                                world.db, a2.user)
    assert e2.value.status_code == 404


def test_tu_them_sua_xoa_ap_dong_cua_minh_thi_403(world):
    a1 = world.grant("a1", "employee", scope="all", actions=("read", "write"))
    row = _row(world.db, world.emp["a1"])
    with pytest.raises(HTTPException) as e:
        work_history_access.block_self_write(world.db, a1.user, world.emp["a1"])
    assert e.value.status_code == 403

    from app.modules.employee.work_history_schema import WorkHistoryIn, WorkHistoryUpdate
    data = WorkHistoryIn(event_type=3, from_date=date(2025, 1, 1), department_id=world.dept["A.kt"])
    with pytest.raises(HTTPException):
        whc.create_work_history(world.emp["a1"], data, world.db, a1.user)
    with pytest.raises(HTTPException):
        whc.update_work_history(world.emp["a1"], row.id, WorkHistoryUpdate(note="x"), world.db, a1.user)
    with pytest.raises(HTTPException):
        whc.delete_work_history(world.emp["a1"], row.id, world.db, a1.user)
    with pytest.raises(HTTPException):
        whc.apply_work_history(world.emp["a1"], row.id, world.db, a1.user)


def test_quan_tri_tu_lam_tren_ho_so_minh_thi_200(world):
    a1 = world.grant("a1", "employee", scope="all", actions=("read", "write"))
    _make_admin(world.db, a1.user)
    row = _row(world.db, world.emp["a1"])

    #  Không bị chặn self-write — xóa thẳng là qua được chốt Q3.
    whc.delete_work_history(world.emp["a1"], row.id, world.db, a1.user)
    assert world.db.get(EmployeeWorkHistory, row.id) is None


# ══════════════════════════════════════════════════════════════════════════════
#  Cờ can_edit / can_open_files (A9)
# ══════════════════════════════════════════════════════════════════════════════

def test_co_write_xem_nguoi_khac_can_edit_true_xem_minh_false(world):
    a1 = world.grant("a1", "employee", scope="company", actions=("read", "write"))
    assert work_history_access.can_edit(world.db, a1.user, a1.profile(), world.emp["a3"]) is True
    assert work_history_access.can_edit(world.db, a1.user, a1.profile(), world.emp["a1"]) is False

    _make_admin(world.db, a1.user)
    assert work_history_access.can_edit(world.db, a1.user, a1.profile(), world.emp["a1"]) is True


def test_thieu_sensitive_thi_can_open_files_false(world):
    a1 = world.grant("a1", "employee", scope="company", actions=("read",))
    assert work_history_access.can_open_files(a1.profile(), world.emp["a3"]) is False
    #  Ngoại lệ `self` — hồ sơ của chính mình luôn mở được, dù thiếu khóa.
    assert work_history_access.can_open_files(a1.profile(), world.emp["a1"]) is True


# ══════════════════════════════════════════════════════════════════════════════
#  /me
# ══════════════════════════════════════════════════════════════════════════════

def test_me_khong_can_grant_van_doc_duoc_cua_minh_va_chi_cua_minh(world):
    mine = _row(world.db, world.emp["a1"])
    _row(world.db, world.emp["a3"])     # của người khác — không được lọt vào
    _row(world.db, 0)                   # dòng MỒ CÔI employee_id=0 — bẫy
    stranger = SimpleNamespace(id=12345, employee_id=world.emp["a1"])

    body = json.loads(whc.my_work_history(world.db, stranger).body)
    assert [it["id"] for it in body["data"]["items"]] == [mine.id]
    assert body["data"]["can_edit"] is False
    assert body["data"]["can_open_files"] is True


def test_me_employee_id_0_thi_rong(world):
    _row(world.db, 0)   # dòng mồ côi — KHÔNG được ra dù employee_id = 0
    stranger = SimpleNamespace(id=1, employee_id=0)
    body = json.loads(whc.my_work_history(world.db, stranger).body)
    assert body["data"]["items"] == []


def test_me_khong_nhan_tham_so_employee_id():
    """Không có tham số nào để trỏ sang người khác — một yêu cầu
    `?employee_id=<khác>` bị FastAPI lờ vì route không khai tham số đó."""
    sig = inspect.signature(whc.my_work_history)
    assert "employee_id" not in sig.parameters


# ══════════════════════════════════════════════════════════════════════════════
#  Tệp đính kèm (Q4)
# ══════════════════════════════════════════════════════════════════════════════

def test_chinh_chu_doc_duoc_tep_cua_minh_khong_can_quyen(world):
    row = _row(world.db, world.emp["a1"])
    _attach_fake_file(world.db, row.id)
    me = SimpleNamespace(id=world.user_id("a1"), employee_id=world.emp["a1"])
    assert ac._check(world.db, me, "employee_work_history", "read", row.id)


def test_chinh_chu_khong_doc_duoc_tep_dong_nguoi_khac(world):
    row_other = _row(world.db, world.emp["a3"])
    _attach_fake_file(world.db, row_other.id)
    me = SimpleNamespace(id=world.user_id("a1"), employee_id=world.emp["a1"])
    with pytest.raises(HTTPException) as e:
        ac._check(world.db, me, "employee_work_history", "read", row_other.id)
    assert e.value.status_code == 403


def test_co_doc_pham_vi_nhung_thieu_sensitive_thi_403_tren_tep_nhung_list_van_200(world):
    a1 = world.grant("a1", "employee", scope="company", actions=("read", "write"))
    row = _row(world.db, world.emp["a3"])
    _attach_fake_file(world.db, row.id)

    with pytest.raises(HTTPException) as e:
        ac._check(world.db, a1.user, "employee_work_history", "read", row.id)
    assert e.value.status_code == 403

    body = json.loads(whc.list_work_history(world.emp["a3"], world.db, a1.user).body)
    item = next(it for it in body["data"]["items"] if it["id"] == row.id)
    assert item["file_count"] == 1
    assert body["data"]["can_open_files"] is False


def test_co_sensitive_thi_200(world):
    a1 = world.grant("a1", "employee", scope="company", actions=("read", "write"))
    a1.grant("employee_sensitive", scope="all", actions=("read",))
    row = _row(world.db, world.emp["a3"])
    _attach_fake_file(world.db, row.id)
    assert ac._check(world.db, a1.user, "employee_work_history", "read", row.id)


def test_co_sensitive_nhung_ngoai_pham_vi_thi_van_chan(world):
    """Sensitive KHÔNG mở rộng phạm vi — `a1` chỉ thấy công ty A."""
    a1 = world.grant("a1", "employee", scope="company", actions=("read",))
    a1.grant("employee_sensitive", scope="all", actions=("read",))
    row_b = _row(world.db, world.emp["b1"])
    _attach_fake_file(world.db, row_b.id)
    with pytest.raises(HTTPException) as e:
        ac._check(world.db, a1.user, "employee_work_history", "read", row_b.id)
    assert e.value.status_code == 403


def test_co_write_thieu_sensitive_thi_gan_go_tep_nguoi_khac_403(world):
    a1 = world.grant("a1", "employee", scope="company", actions=("write",))
    row = _row(world.db, world.emp["a3"])
    with pytest.raises(HTTPException) as e:
        ac._check(world.db, a1.user, "employee_work_history", "manage", row.id)
    assert e.value.status_code == 403


def test_scope_dept_tep_phong_khac_403(world):
    a1 = world.grant("a1", "employee", scope="dept", actions=("read",))
    a1.grant("employee_sensitive", scope="all", actions=("read",))
    row = _row(world.db, world.emp["a3"])   # a3 ở A.mua, a1 chỉ thấy A.kt
    with pytest.raises(HTTPException) as e:
        ac._check(world.db, a1.user, "employee_work_history", "read", row.id)
    assert e.value.status_code == 403


def test_list_khong_co_url_cong_khai(world):
    a1 = world.grant("a1", "employee", scope="company", actions=("read", "write"))
    a1.grant("employee_sensitive", scope="all", actions=("read",))
    row = _row(world.db, world.emp["a3"])
    _attach_fake_file(world.db, row.id)
    out = json.loads(ac.list_attachments(entity="employee_work_history", entity_id=row.id,
                                         db=world.db, user=a1.user).body)["data"]
    assert out[0]["url"] == ""
    assert out[0]["thumb_url"] == ""


def test_xoa_dong_thi_filelink_mat(world):
    row = _row(world.db, world.emp["a1"])
    lk, _f = _attach_fake_file(world.db, row.id)
    a1 = world.grant("a1", "employee", scope="all", actions=("read", "write"))
    whs.delete(world.db, world.emp["a1"], row.id, a1.user)
    assert world.db.get(FileLink, lk.id) is None


def test_xoa_ho_so_thi_moi_dong_va_link_mat(world):
    from app.modules.employee import service as employee_service

    row1 = _row(world.db, world.emp["a3"])
    row2 = _row(world.db, world.emp["a3"], event_type=4, department_id=world.dept["A.mua"])
    lk1, _f1 = _attach_fake_file(world.db, row1.id)
    _attach_fake_file(world.db, row2.id)

    employee_service.delete_employee(world.db, world.emp["a3"], ACTOR)

    assert world.db.query(EmployeeWorkHistory).filter(
        EmployeeWorkHistory.employee_id == world.emp["a3"]).count() == 0
    assert world.db.get(FileLink, lk1.id) is None
