"""Lịch làm việc, phase 01: bộ mã + khóa quyền + seed vai trò.

Bắt các lỗi âm thầm: số 0 lọt vào bộ mã, thứ tự ưu tiên thiếu cấp, vai trò
thường (hoặc Quản lý thu mua) tự có quyền sửa lịch.
"""
from app.core import status_catalog
from app.core.permissions import ENTITIES, ENTITY_LABELS
from app.core.scoping import PUBLIC, SCOPE_FIELDS
from app.core.work_schedule_codes import (LEVEL_PRECEDENCE, WorkDayKind,
                                          WorkScheduleLevel)
from app.seed import STD_ROLES

WRITE_ACTIONS = {"create", "write", "delete"}


def _actions(role: str) -> set[str]:
    perm = STD_ROLES[role]["perms"].get("work_schedule")
    return set(perm[0]) if perm else set()


def test_bo_ma_dang_ky_du_va_khong_co_so_0():
    for name, enum in (("work_day_kind", WorkDayKind), ("work_schedule_level", WorkScheduleLevel)):
        code_set = status_catalog.get(name)
        values = [c.value for c in code_set.codes] if hasattr(code_set, "codes") else list(code_set.ordered_values())
        assert sorted(values) == sorted(str(int(m)) for m in enum)
        assert "0" not in values  # 0 = "chưa khai", không hợp lệ
        assert len(set(values)) == len(values)


def test_so_da_cap_khong_doi():
    # Đổi các số này là đổi nghĩa mọi dòng đã lưu.
    assert {m.name: int(m) for m in WorkDayKind} == {"OFF": 1, "FULL": 2, "MORNING": 3, "AFTERNOON": 4}
    assert {m.name: int(m) for m in WorkScheduleLevel} == {
        "SYSTEM": 1, "COMPANY": 2, "DEPARTMENT": 3, "EMPLOYEE": 4}


def test_thu_tu_uu_tien_phu_du_4_cap_hep_thang_rong():
    assert len(LEVEL_PRECEDENCE) == len(set(LEVEL_PRECEDENCE)) == 4
    assert set(LEVEL_PRECEDENCE) == set(WorkScheduleLevel)
    assert LEVEL_PRECEDENCE[0] is WorkScheduleLevel.EMPLOYEE
    assert LEVEL_PRECEDENCE[-1] is WorkScheduleLevel.SYSTEM


def test_khoa_work_schedule_khai_du_nhan_public():
    assert "work_schedule" in ENTITIES
    assert ENTITY_LABELS["work_schedule"]
    assert SCOPE_FIELDS["work_schedule"] is PUBLIC


def test_hr_leave_va_hr_profile_duoc_sua_lich():
    for role in ("hr_leave", "hr_profile"):
        assert {"read"} | WRITE_ACTIONS <= _actions(role), role


def test_vai_tro_khac_chi_doc_ke_ca_quan_ly_thu_mua():
    for role in STD_ROLES:
        if role in ("hr_leave", "hr_profile", "admin"):
            continue
        acts = _actions(role)
        assert not (acts & WRITE_ACTIONS), f"{role} không được sửa lịch: {acts}"
    # Bẫy _PUR_MANAGER_PERMS: vét cạn ENTITIES trừ _SYS_ENTITIES.
    assert not (_actions("pur_manager") & WRITE_ACTIONS)
