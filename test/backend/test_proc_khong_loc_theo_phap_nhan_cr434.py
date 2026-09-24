"""bao-CR-434 — ĐẢO P1-1: bậc `proc` KHÔNG còn tự thu hẹp theo pháp nhân trên hồ sơ nhân sự.

Lịch sử: P1-1 (kế hoạch 12, CR-164) từng AND thêm `company_id` của người xem vào nhánh
"nhặt việc" của bậc `proc`, với lý do "bật đa pháp nhân là thu mua công ty con nhặt được
phiếu của mọi công ty". Đại ca chốt 21/09/2026 rằng tiền đề đó sai với cách công ty đang
vận hành: pháp nhân trên hồ sơ nhân sự chỉ là chuyện PHÁP LÝ (hợp đồng lao động ký với
công ty nào), còn ngoài đời một phòng — điển hình là nhà máy Dego Organic — mua hàng cho
nhiều pháp nhân, và hóa đơn của đơn đó có thể về một công ty khác công ty của chính
người mua. Tự thu hẹp theo hồ sơ là cắt mất đúng phiếu họ phải xử lý.

Luật mới (xem `_proc_status_cond` trong `app/core/scoping.py`):

  1. Hồ sơ đã gắn pháp nhân hay chưa đều KHÔNG ảnh hưởng — `proc` nhặt mọi phiếu ở trạng
     thái sau duyệt, bất kể pháp nhân trên phiếu.
  2. Muốn nhốt một tài khoản vào một pháp nhân thì khai TẬN TAY ở ô «Chỉ trong công ty»
     của hộp thoại Phạm vi (`_explicit_cond`, chiều `company`) — ca đó nằm ở
     `test_pham_vi_cap_bac_ma_tran.py::test_b1b_...`, vì cần dựng cả bảng `tab_user_scope`.
  3. Bậc `dept_proc` (bao-CR-414) cũng vậy: nhốt theo PHÒNG, không nhốt theo pháp nhân —
     người nhà máy gắn pháp nhân A vẫn thấy phiếu phòng nhà máy đứng tên pháp nhân B.

Test gọi thẳng `_role_scope_cond(...)` — cùng đường mà `apply_scope` đi, nhưng khỏi phải
dựng cả controller. Phải có DỮ LIỆU THẬT của HAI pháp nhân mới chứng minh được là KHÔNG
lọc: bảng một công ty thì điều kiện nào cũng ra kết quả giống nhau.
"""
from types import SimpleNamespace

from app.core.scoping import _role_scope_cond


# Người xem là NGƯỜI LẠ với mọi phiếu bên dưới (không tạo phiếu nào, chưa gắn nhân sự) — nên
# nhánh `created_by == user.id` và nhánh "được giao" đều không khớp, chỉ còn nhánh nhặt-việc
# theo trạng thái. Đúng tư thế cần soi: thu mua đi nhặt phiếu của người khác.
_STRANGER_UID = 999_999


def _viewer(company_id: int, **extra):
    profile = {"company_id": company_id, "dept_id": 0, "dept_name": "",
               "employee_id": 0, "emp_code": "", "emp_name": ""}
    profile.update(extra)
    return SimpleNamespace(id=_STRANGER_UID), profile


def _codes(db, model, cond):
    return {row.code for row in db.query(model).filter(cond).all()}


# ── purchase_request ─────────────────────────────────────────────────────────────

def _three_prs(db, company_a: int, company_b: int):
    """Hai phiếu ĐÃ DUYỆT ở hai pháp nhân + một phiếu NHÁP (bẫy: proc không được nhặt nháp)."""
    from app.modules.purchase_request.model import PurchaseRequest
    db.add_all([
        PurchaseRequest(code="PR-A", company_id=company_a, status="approved", created_by=1),
        PurchaseRequest(code="PR-B", company_id=company_b, status="approved", created_by=1),
        PurchaseRequest(code="PR-A-NHAP", company_id=company_a, status="draft", created_by=1),
    ])
    db.flush()
    return PurchaseRequest


def test_pr_gan_phap_nhan_van_nhat_phieu_da_duyet_cua_moi_phap_nhan(db):
    """Luật 1 — hồ sơ gắn pháp nhân A: proc vẫn nhặt cả PR-A lẫn PR-B, chỉ bỏ phiếu nháp.

    Đây chính là ca mà P1-1 từng khẳng định ngược lại (`== {"PR-A"}`)."""
    PR = _three_prs(db, 10, 20)

    user, profile = _viewer(company_id=10)
    cond = _role_scope_cond(PR, "purchase_request", "proc", user, profile)

    assert _codes(db, PR, cond) == {"PR-A", "PR-B"}, "hồ sơ gắn pháp nhân mà lại tự thu hẹp"


def test_pr_chua_gan_phap_nhan_nhat_het_nhu_cu(db):
    """Luật 1 — company_id=0 giữ nguyên hành vi: mọi phiếu đã duyệt, không nháp."""
    PR = _three_prs(db, 10, 20)

    user, profile = _viewer(company_id=0)
    cond = _role_scope_cond(PR, "purchase_request", "proc", user, profile)

    assert _codes(db, PR, cond) == {"PR-A", "PR-B"}


def test_pr_gan_hay_khong_gan_phap_nhan_cho_cung_mot_ket_qua(db):
    """Ghim cái lõi của CR-434: `company_id` trên hồ sơ KHÔNG phải một tham số của nhánh proc.
    Hai hồ sơ chỉ khác ô pháp nhân phải cho ra đúng một tập phiếu."""
    PR = _three_prs(db, 10, 20)

    seen = []
    for company_id in (0, 10, 20, 999):
        user, profile = _viewer(company_id=company_id)
        seen.append(_codes(db, PR, _role_scope_cond(PR, "purchase_request", "proc", user, profile)))
    assert all(s == seen[0] for s in seen), f"kết quả đổi theo pháp nhân hồ sơ: {seen}"


# ── purchase_order ───────────────────────────────────────────────────────────────

def _three_pos(db, company_a: int, company_b: int):
    from app.modules.purchase_order.model import PurchaseOrder
    db.add_all([
        PurchaseOrder(code="PO-A", company_id=company_a, status="approved", created_by=1),
        PurchaseOrder(code="PO-B", company_id=company_b, status="approved", created_by=1),
        PurchaseOrder(code="PO-A-NHAP", company_id=company_a, status="draft", created_by=1),
    ])
    db.flush()
    return PurchaseOrder


def test_po_gan_phap_nhan_van_nhat_don_da_duyet_cua_moi_phap_nhan(db):
    """ĐMH cùng luật với YCMH — hồ sơ gắn pháp nhân A vẫn nhặt đơn đã duyệt của B."""
    PO = _three_pos(db, 10, 20)

    user, profile = _viewer(company_id=10)
    cond = _role_scope_cond(PO, "purchase_order", "proc", user, profile)

    assert _codes(db, PO, cond) == {"PO-A", "PO-B"}, "ĐMH tự thu hẹp theo pháp nhân hồ sơ"


def test_po_chua_gan_phap_nhan_nhat_het_nhu_cu(db):
    PO = _three_pos(db, 10, 20)

    user, profile = _viewer(company_id=0)
    cond = _role_scope_cond(PO, "purchase_order", "proc", user, profile)

    assert _codes(db, PO, cond) == {"PO-A", "PO-B"}


# ── Người tạo vẫn thấy phiếu của mình, kể cả khác công ty ─────────────────────────

def test_pr_van_thay_phieu_minh_tao_du_khac_cong_ty(db):
    """Phiếu do CHÍNH mình tạo thì thấy dù thuộc công ty khác và còn nháp — nhánh
    `created_by` không phụ thuộc gì vào pháp nhân, trước hay sau CR-434 đều vậy."""
    from app.modules.purchase_request.model import PurchaseRequest
    db.add(PurchaseRequest(code="PR-MINE", company_id=20, status="draft",
                           created_by=_STRANGER_UID))
    db.flush()

    user, profile = _viewer(company_id=10)
    cond = _role_scope_cond(PurchaseRequest, "purchase_request", "proc", user, profile)

    assert "PR-MINE" in _codes(db, PurchaseRequest, cond)


# ── dept_proc: nhốt theo PHÒNG, không nhốt theo pháp nhân ─────────────────────────

def test_dept_proc_nguoi_nha_may_thay_phieu_phong_minh_o_moi_phap_nhan(db):
    """Luật 3 — ca Dego Organic: một phòng nhà máy mua cho nhiều pháp nhân.

    Người nhà máy có hồ sơ gắn pháp nhân A (10), phòng nhà máy id 5. Bốn phiếu đã duyệt:
    phòng 5 của A · phòng 5 của B · phòng khác của A · phòng khác của B. Phải thấy đúng
    hai phiếu của phòng 5 — pháp nhân trên phiếu không được là tiêu chí."""
    from app.modules.purchase_request.model import PurchaseRequest
    FACTORY_DEPT, OTHER_DEPT = 5, 7
    db.add_all([
        PurchaseRequest(code="NM-A", company_id=10, department_id=FACTORY_DEPT,
                        status="approved", created_by=1),
        PurchaseRequest(code="NM-B", company_id=20, department_id=FACTORY_DEPT,
                        status="approved", created_by=1),
        PurchaseRequest(code="KHAC-A", company_id=10, department_id=OTHER_DEPT,
                        status="approved", created_by=1),
        PurchaseRequest(code="KHAC-B", company_id=20, department_id=OTHER_DEPT,
                        status="approved", created_by=1),
        PurchaseRequest(code="NM-B-NHAP", company_id=20, department_id=FACTORY_DEPT,
                        status="draft", created_by=1),
    ])
    db.flush()

    user, profile = _viewer(company_id=10, dept_id=FACTORY_DEPT, dept_ids=[FACTORY_DEPT],
                            dept_name="Dego Organic")
    cond = _role_scope_cond(PurchaseRequest, "purchase_request", "dept_proc", user, profile)

    assert _codes(db, PurchaseRequest, cond) == {"NM-A", "NM-B"}, (
        "dept_proc phải nhốt theo phòng: thấy cả hai pháp nhân của phòng mình, không thấy phòng khác")
