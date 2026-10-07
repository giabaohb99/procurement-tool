"""HĐLĐ phase 01: bộ mã, khóa quyền, phạm vi, vai trò seed, bảng.

Canh những chỗ lỗi âm thầm: số mã bị tái dùng, quên `_SYS_ENTITIES` (Quản lý thu mua
tự đọc được LƯƠNG toàn công ty), quên `SCOPE_FIELDS` (chặn sạch hoặc mở toang).
"""
from datetime import date

from app.core import code_sets  # noqa: F401
from app.core.labor_contract_codes import (
    FORBIDS_END_DATE, LABOR_CONTRACT_STATUS_LABELS, LABOR_CONTRACT_TYPE_LABELS,
    REQUIRES_END_DATE, LaborContractStatus, LaborContractType,
)
from app.core.permissions import ENTITIES, ENTITY_LABELS
from app.core.scoping import SCOPE_FIELDS
from app.core.status_catalog import all_sets
from app.seed import _PUR_MANAGER_PERMS, _SYS_ENTITIES, STD_ROLES

NEW_KEYS = ("labor_contract", "labor_contract_template")


def test_so_ma_da_cap_khong_doi():
    """Số đã cấp là hợp đồng với dữ liệu cũ — đổi là mọi dòng đổi nghĩa."""
    assert {t.name: int(t) for t in LaborContractType} == {
        "PROBATION": 1, "FIXED_TERM": 2, "INDEFINITE": 3, "SERVICE": 4, "COLLABORATOR": 5, "OTHER": 9}
    assert {s.name: int(s) for s in LaborContractStatus} == {
        "DRAFT": 1, "SIGNED": 2, "EXPIRED": 3, "TERMINATED": 4, "CANCELLED": 5}
    assert set(LABOR_CONTRACT_TYPE_LABELS) == set(LaborContractType)
    assert set(LABOR_CONTRACT_STATUS_LABELS) == set(LaborContractStatus)
    assert 0 not in {int(t) for t in LaborContractType} | {int(s) for s in LaborContractStatus}


def test_luat_ngay_ket_thuc():
    assert REQUIRES_END_DATE == {LaborContractType.PROBATION, LaborContractType.FIXED_TERM,
                                 LaborContractType.SERVICE, LaborContractType.COLLABORATOR}
    assert FORBIDS_END_DATE == {LaborContractType.INDEFINITE}
    assert not (REQUIRES_END_DATE & FORBIDS_END_DATE)
    assert LaborContractType.OTHER not in REQUIRES_END_DATE | FORBIDS_END_DATE


def test_bo_ma_dang_ky_voi_so_dang_chuoi():
    sets = all_sets()
    for name, size in (("labor_contract_type", 6), ("labor_contract_status", 5)):
        assert name in sets, f"{name} chưa register — thiếu import ở code_sets.py"
        codes = sets[name].codes
        assert len(codes) == size
        assert all(c.value.isdigit() for c in codes)
        assert all(c.label.strip() for c in codes)


def test_khoa_quyen_moi_day_du():
    for k in NEW_KEYS:
        assert k in ENTITIES and k in SCOPE_FIELDS and ENTITY_LABELS.get(k), k
    assert SCOPE_FIELDS["labor_contract"]["self"] == "employee_id"
    assert "department_id" in SCOPE_FIELDS["labor_contract"].values()
    assert SCOPE_FIELDS["labor_contract_template"]["company"] == "company_id"


def test_quan_ly_thu_mua_khong_tu_co_quyen_xem_luong():
    for k in NEW_KEYS:
        assert k in _SYS_ENTITIES
        assert k not in _PUR_MANAGER_PERMS


def test_chi_hr_profile_duoc_seed_quyen_hop_dong():
    hr = STD_ROLES["hr_profile"]["perms"]
    assert set(hr["labor_contract"][0]) == {"read", "create", "write", "delete", "print"}
    assert hr["labor_contract_template"] == (["read", "create", "write", "delete"], "all")
    for role, info in STD_ROLES.items():
        if role in ("hr_profile", "admin"):
            continue
        for k in NEW_KEYS:
            assert k not in info["perms"], f"vai trò {role} không được tự có {k}"


def test_hai_bang_tao_va_doc_lai_duoc(db):
    from app.modules.labor_contract.model import LaborContract
    from app.modules.labor_contract.template_model import LaborContractTemplate

    t = LaborContractTemplate(company_id=1, contract_type=2, name="Mẫu XĐTH", file_id=9, placeholders=["ho_ten"])
    c = LaborContract(code="HDLD001", employee_id=5, company_id=1, contract_type=2,
                      start_date=date(2026, 10, 1), base_salary=15_000_000)
    db.add_all([t, c])
    db.commit()
    assert t.is_active is True and t.placeholders == ["ho_ten"]
    assert (c.status, c.allowance, c.generated_file_id, c.signed_file_id) == (1, 0, 0, 0)
    assert c.end_date is None and c.template_id == 0
