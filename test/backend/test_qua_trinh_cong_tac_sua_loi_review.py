"""Quá trình công tác — sửa finding BACKEND của code review 03/10/2026
(M1/M2/M3/M7, plan `261003-0837-qua-trinh-lam-viec-nhan-su`).

Luật thấp (H2, Low) nằm ở `test_qua_trinh_cong_tac_gio_vn.py` và
`test_qua_trinh_cong_tac_sua_loi_review_low.py` — tách riêng để mỗi tệp dưới
200 dòng.
"""
from datetime import date

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.modules.attachment import controller as ac
from app.modules.attachment.model import FileLink, StoredFile
from app.modules.employee import work_history_controller as whc
from app.modules.employee import work_history_service as whs
from app.modules.employee.work_history_model import EmployeeWorkHistory
from app.modules.employee.work_history_schema import WorkHistoryUpdate

ACTOR = 1


def _row(db, eid, event_type=3, from_date=date(2025, 1, 1), **kw) -> EmployeeWorkHistory:
    row = EmployeeWorkHistory(employee_id=eid, event_type=event_type, from_date=from_date,
                              created_by=ACTOR, updated_by=ACTOR, **kw)
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


# ══════════════════════════════════════════════════════════════════════════════
#  M1 — PATCH gửi null TƯỜNG MINH cho ô bắt buộc
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("field", ["event_type", "from_date", "company_id", "department_id",
                                   "position_id", "note", "decision_no"])
def test_patch_gui_null_tuong_minh_cho_o_bat_buoc_thi_422(field):
    with pytest.raises(ValidationError):
        WorkHistoryUpdate(**{field: None})


def test_patch_to_date_null_tuong_minh_van_duoc_cho_phep():
    assert WorkHistoryUpdate(to_date=None).to_date is None


def test_patch_decision_date_null_tuong_minh_van_duoc_cho_phep():
    assert WorkHistoryUpdate(decision_date=None).decision_date is None


def test_patch_khong_gui_khoa_nao_thi_khong_loi():
    assert WorkHistoryUpdate(note="ghi chú mới").note == "ghi chú mới"


# ══════════════════════════════════════════════════════════════════════════════
#  M2 — xóa dòng có tệp của NGƯỜI KHÁC mà thiếu employee_sensitive.read
# ══════════════════════════════════════════════════════════════════════════════

def test_xoa_dong_nguoi_khac_co_tep_thieu_sensitive_thi_403_tep_khong_mat(world):
    a1 = world.grant("a1", "employee", scope="all", actions=("read", "write"))
    row = _row(world.db, world.emp["a3"])
    lk, _f = _attach_fake_file(world.db, row.id)

    with pytest.raises(HTTPException) as e:
        whc.delete_work_history(world.emp["a3"], row.id, world.db, a1.user)
    assert e.value.status_code == 403
    world.db.rollback()

    assert world.db.get(FileLink, lk.id) is not None
    assert world.db.get(EmployeeWorkHistory, row.id) is not None


def test_xoa_dong_nguoi_khac_co_sensitive_thi_xoa_duoc(world):
    a1 = world.grant("a1", "employee", scope="all", actions=("read", "write"))
    a1.grant("employee_sensitive", scope="all", actions=("read",))
    row = _row(world.db, world.emp["a3"])
    lk, _f = _attach_fake_file(world.db, row.id)

    whc.delete_work_history(world.emp["a3"], row.id, world.db, a1.user)

    assert world.db.get(FileLink, lk.id) is None
    assert world.db.get(EmployeeWorkHistory, row.id) is None


def test_xoa_dong_khong_tep_khong_can_sensitive(world):
    a1 = world.grant("a1", "employee", scope="all", actions=("read", "write"))
    row = _row(world.db, world.emp["a3"])

    whc.delete_work_history(world.emp["a3"], row.id, world.db, a1.user)
    assert world.db.get(EmployeeWorkHistory, row.id) is None


# ══════════════════════════════════════════════════════════════════════════════
#  M3 — gắn/gỡ tệp của NGƯỜI KHÁC phải có `employee.write`, không nhận `create`
# ══════════════════════════════════════════════════════════════════════════════

def test_chi_co_create_khong_the_thay_the_write_khi_gan_go_tep_nguoi_khac(world):
    a1 = world.grant("a1", "employee", scope="all", actions=("create",))
    a1.grant("employee_sensitive", scope="all", actions=("read",))
    row = _row(world.db, world.emp["a3"])

    with pytest.raises(HTTPException) as e:
        ac._check(world.db, a1.user, "employee_work_history", "manage", row.id)
    assert e.value.status_code == 403


def test_co_write_thuc_su_thi_gan_go_tep_nguoi_khac_qua(world):
    a1 = world.grant("a1", "employee", scope="all", actions=("write",))
    a1.grant("employee_sensitive", scope="all", actions=("read",))
    row = _row(world.db, world.emp["a3"])

    exts, _max_mb = ac._check(world.db, a1.user, "employee_work_history", "manage", row.id)
    assert exts   # không ném lỗi — qua được


# ══════════════════════════════════════════════════════════════════════════════
#  M7 — `delete_all_of` không tự commit (đi chung giao dịch `delete_employee`)
# ══════════════════════════════════════════════════════════════════════════════

def test_delete_all_of_khong_tu_commit(world):
    row = _row(world.db, world.emp["a3"])
    lk, _f = _attach_fake_file(world.db, row.id)

    whs.delete_all_of(world.db, world.emp["a3"])
    world.db.rollback()   # mô phỏng một lỗi SAU `delete_all_of`, TRƯỚC commit cuối

    assert world.db.get(FileLink, lk.id) is not None, "chưa commit — rollback phải khôi phục tệp"
    assert world.db.query(EmployeeWorkHistory).filter(
        EmployeeWorkHistory.employee_id == world.emp["a3"]).count() == 1
