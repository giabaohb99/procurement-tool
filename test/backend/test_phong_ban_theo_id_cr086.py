"""CR-086 — PHÒNG BAN NEO BẰNG ID, TÊN CHỈ CÒN LÀ ẢNH CHỤP ĐỂ IN.

Bài kiểm chốt đúng ba điều, vì đây là ba chỗ từng vỡ khi phòng ban đổi tên:

```
đổi tên phòng   →  phiếu cũ VẪN thuộc phạm vi người đó (so bằng id)
phiếu cũ id = 0 →  vẫn so bằng tên (nhánh lùi, sẽ bỏ ở N-008)
lưu phạm vi     →  giao diện gửi TÊN, DB lưu ID, đọc ra lại trả TÊN hiện hành
```

Không đi qua API vì `get_perm_profile` có bộ đệm 60 giây — dựng thẳng hồ sơ quyền
cho từng tình huống thì mỗi bài một trạng thái rõ ràng.
"""
from types import SimpleNamespace

import pytest

from app.core.scoping import apply_scope
from app.modules.department.model import Department
from app.modules.department.service import dept_id_by_name, sync_department_ref
from app.modules.purchase_request.model import PurchaseRequest

USER_ID = 10


def _profile(dept_id=0, dept_name="", company_id=0, scope="dept", inc=None, exc=None):
    """Hồ sơ quyền tối thiểu, đúng hình dạng `get_perm_profile` trả về."""
    perms = {a: a in ("read", "write") for a in ("read", "create", "write", "delete",
                                                 "approve", "cancel", "print", "export")}
    perms["scope"] = scope
    return {
        "grants": [{"role_id": 1, "perms": {"purchase_request": perms},
                    "scope": {"inc": inc or {}, "exc": exc or {}}}],
        "company_id": company_id, "dept_id": dept_id, "dept_name": dept_name,
        "employee_id": 0, "emp_code": "", "emp_name": "",
    }


def _pr(db, code, company_id, department_id=0, department=""):
    pr = PurchaseRequest(code=code, company_id=company_id, department_id=department_id,
                         department=department, status="submitted", created_by=99)
    db.add(pr)
    db.commit()
    return pr


def _visible(db, profile):
    user = SimpleNamespace(id=USER_ID)
    q = apply_scope(db.query(PurchaseRequest), PurchaseRequest, "purchase_request", user, profile)
    return sorted(p.code for p in q.all())


# ── Tra id từ tên ────────────────────────────────────────────────────────────────
def test_tra_id_theo_ten(db, seed):
    assert dept_id_by_name(db, "Phòng Test") == seed.dept_id
    assert dept_id_by_name(db, "  Phòng Test  ".strip()) == seed.dept_id
    assert dept_id_by_name(db, "Phòng Không Có") == 0
    assert dept_id_by_name(db, "") == 0


def test_ten_trung_nhau_thi_khong_doan_bua(db, seed):
    """Tên phòng KHÔNG duy nhất trong DB. Trùng tên mà không có pháp nhân để phân biệt
    thì trả 0 (giữ tên, chạy nhánh lùi) chứ không gán bừa một id."""
    db.add(Department(code="DEPT02", name="Phòng Test", company_id=777, is_active=True))
    db.commit()
    assert dept_id_by_name(db, "Phòng Test") == 0
    assert dept_id_by_name(db, "Phòng Test", company_id=seed.company_id) == seed.dept_id


# ── Ghi hai chiều id ↔ tên ───────────────────────────────────────────────────────
def test_ghi_hai_chieu(db, seed):
    pr = PurchaseRequest(code="YC-A", company_id=seed.company_id, department_id=seed.dept_id)
    sync_department_ref(db, pr)
    assert pr.department == "Phòng Test"          # có id → tên chạy theo id

    pr2 = PurchaseRequest(code="YC-B", company_id=seed.company_id, department="Phòng Test")
    sync_department_ref(db, pr2)
    assert pr2.department_id == seed.dept_id      # chỉ có tên → suy ra id

    pr3 = PurchaseRequest(code="YC-C", company_id=seed.company_id,
                          department_id=999_999, department="Phòng Test")
    sync_department_ref(db, pr3)
    assert pr3.department_id == seed.dept_id      # id rác → quay về tra theo tên

    pr4 = PurchaseRequest(code="YC-D", company_id=seed.company_id, department="Phòng Lạ")
    sync_department_ref(db, pr4)
    assert (pr4.department_id, pr4.department) == (0, "Phòng Lạ")   # không suy ra được → giữ tên


# ── Phạm vi 'dept' ───────────────────────────────────────────────────────────────
def test_doi_ten_phong_van_giu_pham_vi(db, seed):
    """Điểm mấu chốt của CR-086: phiếu lưu tên CŨ, phòng đã đổi tên → vẫn phải thấy."""
    _pr(db, "YC-CU", seed.company_id, seed.dept_id, "Phòng Test")
    dep = db.get(Department, seed.dept_id)
    dep.name = "Phòng Test (đổi tên)"
    db.commit()

    prof = _profile(dept_id=seed.dept_id, dept_name=dep.name, company_id=seed.company_id)
    assert _visible(db, prof) == ["YC-CU"]


def test_phieu_chua_dien_lui_duoc_id_thi_so_bang_ten(db, seed):
    """Nhánh lùi: phiếu `department_id = 0` (backfill không suy ra được) vẫn so bằng tên."""
    _pr(db, "YC-CU", seed.company_id, 0, "Phòng Test")
    _pr(db, "YC-KHAC", seed.company_id, 0, "Phòng Khác")

    prof = _profile(dept_id=seed.dept_id, dept_name="Phòng Test", company_id=seed.company_id)
    assert _visible(db, prof) == ["YC-CU"]


def test_ten_trung_nhung_id_khac_thi_khong_lot(db, seed):
    """Phiếu ĐÃ có id của phòng khác thì tên trùng cũng không lọt — id là nguồn sự thật."""
    other = Department(code="DEPT02", name="Phòng Test", company_id=seed.company_id, is_active=True)
    db.add(other)
    db.commit()
    _pr(db, "YC-PHONG-KHAC", seed.company_id, other.id, "Phòng Test")

    prof = _profile(dept_id=seed.dept_id, dept_name="Phòng Test", company_id=seed.company_id)
    assert _visible(db, prof) == []


def test_khong_gan_phong_thi_khong_thay_gi(db, seed):
    _pr(db, "YC-CU", seed.company_id, seed.dept_id, "Phòng Test")
    assert _visible(db, _profile(company_id=seed.company_id)) == []


# ── 'Phòng ban được xem' / loại trừ (tab_user_scope) ─────────────────────────────
def test_phong_ban_duoc_xem_cong_them_theo_id(db, seed):
    other = Department(code="DEPT02", name="Phòng Kia", company_id=seed.company_id, is_active=True)
    db.add(other)
    db.commit()
    _pr(db, "YC-MINH", seed.company_id, seed.dept_id, "Phòng Test")
    _pr(db, "YC-KIA", seed.company_id, other.id, "Phòng Kia")
    _pr(db, "YC-CU-KIA", seed.company_id, 0, "Phòng Kia")     # phiếu cũ chưa có id

    prof = _profile(dept_id=seed.dept_id, dept_name="Phòng Test", company_id=seed.company_id,
                    inc={"department": [other.id], "department_name": ["Phòng Kia"]})
    assert _visible(db, prof) == ["YC-CU-KIA", "YC-KIA", "YC-MINH"]


def test_loai_tru_phong_theo_id(db, seed):
    other = Department(code="DEPT02", name="Phòng Kia", company_id=seed.company_id, is_active=True)
    db.add(other)
    db.commit()
    _pr(db, "YC-MINH", seed.company_id, seed.dept_id, "Phòng Test")
    _pr(db, "YC-KIA", seed.company_id, other.id, "Phòng Kia")

    prof = _profile(company_id=seed.company_id, scope="company",
                    exc={"department": [other.id], "department_name": ["Phòng Kia"]})
    assert _visible(db, prof) == ["YC-MINH"]


# ── Đọc/ghi phạm vi phòng ban trong tab_user_scope ───────────────────────────────
def test_luu_pham_vi_bang_ten_thi_db_giu_id(db, seed):
    from app.modules.user.service import get_user_scope, set_user_scope
    from app.modules.user.schema import ScopeUpdate
    from app.modules.user.model import UserScope

    set_user_scope(db, USER_ID, 1, ScopeUpdate(departments=["Phòng Test"],
                                               exclude_departments=["Phòng Lạ"]), USER_ID)
    db.commit()
    rows = {r.is_exclude: r.value for r in db.query(UserScope).filter(
        UserScope.dim == "department").all()}
    assert rows[False] == str(seed.dept_id)     # tên → id
    assert rows[True] == "Phòng Lạ"             # không suy ra được → giữ nguyên tên

    # Đọc ra thì trả TÊN HIỆN HÀNH, nên đổi tên phòng là màn phân quyền hiện tên mới.
    dep = db.get(Department, seed.dept_id)
    dep.name = "Phòng Test (đổi tên)"
    db.commit()
    out = get_user_scope(db, USER_ID, 1)
    assert out["departments"] == ["Phòng Test (đổi tên)"]
    assert out["exclude_departments"] == ["Phòng Lạ"]
