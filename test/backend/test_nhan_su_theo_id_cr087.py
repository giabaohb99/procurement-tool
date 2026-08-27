"""CR-087 — NSPT / TRƯỞNG BỘ PHẬN NEO BẰNG ID NHÂN SỰ.

`tab_employee.full_name` KHÔNG duy nhất (prod đang có 1 cặp trùng, dev 4 cặp), nên khớp
`nspt == tên` là cho hai người trùng tên thấy đơn của nhau — không lỗi, không log. Bài kiểm
chốt ba điều:

```
đổi tên nhân sự  →  đơn cũ VẪN thuộc phạm vi người đó (so bằng id)
đơn cũ id = 0    →  vẫn so bằng tên (nhánh lùi, sẽ bỏ ở N-008)
trùng tên, khác id → KHÔNG thấy đơn của nhau  ← chính là lỗ đang rò
```
"""
from types import SimpleNamespace

from app.core.scoping import apply_scope
from app.modules.employee.model import Employee
from app.modules.employee.service import (emp_id_by_code, emp_id_by_name,
                                          sync_employee_ref)
from app.modules.purchase_order.model import PurchaseOrder

USER_ID = 10


def _profile(employee_id=0, emp_name="", company_id=0, scope="assigned"):
    perms = {a: a in ("read", "write") for a in ("read", "create", "write", "delete",
                                                 "approve", "cancel", "print", "export")}
    perms["scope"] = scope
    return {
        "grants": [{"role_id": 1, "perms": {"purchase_order": perms}, "scope": {"inc": {}, "exc": {}}}],
        "company_id": company_id, "dept_id": 0, "dept_name": "",
        "employee_id": employee_id, "emp_code": "", "emp_name": emp_name,
    }


def _po(db, code, company_id, nspt_id=0, nspt="", created_by=99):
    po = PurchaseOrder(code=code, company_id=company_id, nspt_id=nspt_id, nspt=nspt,
                       status="draft", created_by=created_by)
    db.add(po)
    db.commit()
    return po


def _visible(db, profile):
    user = SimpleNamespace(id=USER_ID)
    q = apply_scope(db.query(PurchaseOrder), PurchaseOrder, "purchase_order", user, profile)
    return sorted(p.code for p in q.all())


def _sinh_doi(db, seed, code="SONGSINH"):
    """Thêm một nhân sự TRÙNG TÊN với `emp_nstm` — đúng tình huống đang có trên prod."""
    origin = db.get(Employee, seed.emp_nstm_id)
    doi = Employee(code=code, full_name=origin.full_name, company_id=seed.company_id,
                   department_id=origin.department_id, is_active=True)
    db.add(doi)
    db.commit()
    return origin, doi


# ── Tra id nhân sự ───────────────────────────────────────────────────────────────
def test_tra_id_theo_ten_va_ma(db, seed):
    assert emp_id_by_name(db, "NSTM Chính") == seed.emp_nstm_id
    assert emp_id_by_name(db, "Không Có Ai") == 0
    assert emp_id_by_name(db, "") == 0
    assert emp_id_by_code(db, seed.emp_nstm_code) == seed.emp_nstm_id
    assert emp_id_by_code(db, "MA-LA") == 0


def test_trung_ten_thi_khong_doan_bua(db, seed):
    origin, doi = _sinh_doi(db, seed)
    assert emp_id_by_name(db, origin.full_name) == 0          # hai người, không chọn bừa ai
    # Cùng pháp nhân luôn thì pháp nhân cũng không phân giải được → vẫn 0.
    assert emp_id_by_name(db, origin.full_name, company_id=seed.company_id) == 0
    doi.company_id = 777
    db.commit()
    assert emp_id_by_name(db, origin.full_name, company_id=seed.company_id) == seed.emp_nstm_id


# ── Ghi kép id ↔ tên ─────────────────────────────────────────────────────────────
def test_ghi_hai_chieu(db, seed):
    po = PurchaseOrder(code="PO-A", company_id=seed.company_id, nspt_id=seed.emp_nstm_id)
    sync_employee_ref(db, po, "nspt_id", "nspt")
    assert po.nspt == "NSTM Chính"                 # có id → tên chạy theo id

    po2 = PurchaseOrder(code="PO-B", company_id=seed.company_id, nspt="NSTM Chính")
    sync_employee_ref(db, po2, "nspt_id", "nspt")
    assert po2.nspt_id == seed.emp_nstm_id         # chỉ có tên → suy ra id

    po3 = PurchaseOrder(code="PO-C", company_id=seed.company_id,
                        nspt_id=999_999, nspt="NSTM Chính")
    sync_employee_ref(db, po3, "nspt_id", "nspt")
    assert po3.nspt_id == seed.emp_nstm_id         # id rác → quay về tra theo tên

    po4 = PurchaseOrder(code="PO-D", company_id=seed.company_id, nspt="Người Lạ")
    sync_employee_ref(db, po4, "nspt_id", "nspt")
    assert (po4.nspt_id, po4.nspt) == (0, "Người Lạ")   # không suy ra được → giữ tên


# ── Phạm vi ĐMH theo NSPT ────────────────────────────────────────────────────────
def test_doi_ten_nhan_su_van_giu_pham_vi(db, seed):
    """Đơn lưu tên CŨ, nhân sự đã đổi tên → vẫn phải thấy đơn mình phụ trách."""
    _po(db, "PO-CU", seed.company_id, seed.emp_nstm_id, "NSTM Chính")
    emp = db.get(Employee, seed.emp_nstm_id)
    emp.full_name = "NSTM Chính (đổi tên)"
    db.commit()

    prof = _profile(employee_id=seed.emp_nstm_id, emp_name=emp.full_name,
                    company_id=seed.company_id)
    assert _visible(db, prof) == ["PO-CU"]


def test_don_chua_dien_lui_duoc_id_thi_so_bang_ten(db, seed):
    _po(db, "PO-CU", seed.company_id, 0, "NSTM Chính")
    _po(db, "PO-KHAC", seed.company_id, 0, "Người Khác")

    prof = _profile(employee_id=seed.emp_nstm_id, emp_name="NSTM Chính",
                    company_id=seed.company_id)
    assert _visible(db, prof) == ["PO-CU"]


def test_trung_ten_thi_khong_con_thay_don_cua_nhau(db, seed):
    """LỖ ĐANG RÒ trước CR-087: hai người trùng tên, khớp bằng tên là thấy đơn của nhau."""
    origin, doi = _sinh_doi(db, seed)
    _po(db, "PO-CUA-GOC", seed.company_id, origin.id, origin.full_name)
    _po(db, "PO-CUA-DOI", seed.company_id, doi.id, doi.full_name)

    prof = _profile(employee_id=origin.id, emp_name=origin.full_name, company_id=seed.company_id)
    assert _visible(db, prof) == ["PO-CUA-GOC"]


def test_van_thay_don_minh_tao(db, seed):
    """Điều kiện cũ 'đơn mình tạo' không được rơi mất khi thêm nhánh id."""
    _po(db, "PO-MINH-TAO", seed.company_id, 0, "Người Khác", created_by=USER_ID)
    assert _visible(db, _profile(company_id=seed.company_id)) == ["PO-MINH-TAO"]


# ── Ô Trưởng bộ phận trên YCMH ───────────────────────────────────────────────────
def test_tbp_ycmh_gui_moi_ten_van_ra_duoc_id(db, seed):
    """CR-071 chỉ đồng bộ id → tên. Phiếu (giao diện cũ) gửi mỗi TÊN mà phòng chưa gán trưởng
    thì `head_of_dept_id` nằm 0 vĩnh viễn — đẻ lại đúng món nợ migration vừa điền lùi xong."""
    from app.modules.purchase_request.model import PurchaseRequest
    from app.modules.purchase_request.service import sync_head_of_dept_name

    pr = PurchaseRequest(code="PYC-CR087", company_id=seed.company_id,
                         head_of_dept="Trưởng Phòng", head_of_dept_id=0)
    sync_head_of_dept_name(db, pr)
    assert pr.head_of_dept_id == seed.emp_tp_id       # tên → id (chiều mới)

    pr2 = PurchaseRequest(code="PYC-CR087B", company_id=seed.company_id,
                          head_of_dept=" tên cũ ", head_of_dept_id=seed.emp_tp_id)
    sync_head_of_dept_name(db, pr2)
    assert pr2.head_of_dept == "Trưởng Phòng"          # id → tên (chiều cũ, giữ nguyên)
