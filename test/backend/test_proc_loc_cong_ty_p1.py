"""P1-1 (kế hoạch 12) — bậc `proc` phải AND thêm pháp nhân, không nhặt phiếu công ty khác.

Lỗ hổng gốc: nhánh "nhặt việc" của bậc `proc` trên `purchase_request` và `purchase_order`
CHỈ lọc theo trạng thái (`status in [...]`) mà KHÔNG kèm pháp nhân. Một hệ một công ty thì
vô hại; bật đa pháp nhân (kế hoạch 12) là thu mua công ty con nhặt được mọi phiếu ĐÃ DUYỆT
của MỌI công ty — đúng thứ P1 phải bịt trước khi làm những phase sau.

Cách vá (xem `_proc_status_cond` trong `app/core/scoping.py`): AND thêm `company_id` của
người xem, NHƯNG chỉ khi họ đã gắn pháp nhân (`company_id > 0`). Nhân sự chưa gắn
(`company_id = 0` — trạng thái prod hiện tại) giữ NGUYÊN hành vi cũ để Thu mua không gián
đoạn. Hai khẳng định của bài này bám đúng hai vế đó:

  1. Đã gắn pháp nhân → chỉ nhặt phiếu đã duyệt của CHÍNH công ty mình (vá lỗ).
  2. Chưa gắn (company_id=0) → vẫn nhặt hết như cũ (tương thích ngược, không làm sập prod).

Test gọi thẳng `_role_scope_cond(..., "proc", ...)` — cùng đường mà `apply_scope` đi, nhưng
khỏi phải dựng cả controller. Phải có DỮ LIỆU THẬT của HAI công ty mới chứng minh được là đã
lọc: đếm ra kết quả đúng trên bảng rỗng thì điều kiện nào cũng "đúng".
"""
from types import SimpleNamespace

from app.core.scoping import _role_scope_cond


# Người xem là NGƯỜI LẠ với mọi phiếu bên dưới (không tạo phiếu nào, chưa gắn nhân sự) — nên
# nhánh `created_by == user.id` và nhánh "được giao" đều không khớp, chỉ còn nhánh nhặt-việc
# theo trạng thái. Đúng tư thế cần soi: thu mua đi nhặt phiếu của người khác.
_NGUOI_LA_UID = 999_999


def _ai_do(company_id: int):
    return (SimpleNamespace(id=_NGUOI_LA_UID),
            {"company_id": company_id, "dept_id": 0, "dept_name": "",
             "employee_id": 0, "emp_code": "", "emp_name": ""})


def _dem(db, Model, cond):
    q = db.query(Model)
    return q.count() if cond is None else q.filter(cond).count()


# ── purchase_request ─────────────────────────────────────────────────────────────

def _ba_phieu_pr(db, cty_a: int, cty_b: int):
    """Hai phiếu ĐÃ DUYỆT ở hai pháp nhân + một phiếu NHÁP (bẫy: proc không được nhặt nháp)."""
    from app.modules.purchase_request.model import PurchaseRequest
    db.add_all([
        PurchaseRequest(code="PR-A", company_id=cty_a, status="approved", created_by=1),
        PurchaseRequest(code="PR-B", company_id=cty_b, status="approved", created_by=1),
        PurchaseRequest(code="PR-A-NHAP", company_id=cty_a, status="draft", created_by=1),
    ])
    db.flush()
    return PurchaseRequest


def test_pr_gan_phap_nhan_thi_khong_nhat_phieu_cong_ty_khac(db):
    """Vế 1 — đã gắn pháp nhân: proc công ty A chỉ nhặt phiếu đã duyệt của A, không thấy của B."""
    CTY_A, CTY_B = 10, 20
    PR = _ba_phieu_pr(db, CTY_A, CTY_B)

    user, profile = _ai_do(company_id=CTY_A)
    cond = _role_scope_cond(PR, "purchase_request", "proc", user, profile)
    con_lai = db.query(PR).filter(cond).all()

    ma = {p.code for p in con_lai}
    assert ma == {"PR-A"}, f"proc công ty A nhặt nhầm: {ma}"   # không có PR-B, không có phiếu nháp


def test_pr_chua_gan_phap_nhan_van_nhat_het_nhu_cu(db):
    """Vế 2 — tương thích ngược: company_id=0 (prod hiện tại) vẫn nhặt mọi phiếu đã duyệt."""
    PR = _ba_phieu_pr(db, 10, 20)

    user, profile = _ai_do(company_id=0)
    cond = _role_scope_cond(PR, "purchase_request", "proc", user, profile)

    ma = {p.code for p in db.query(PR).filter(cond).all()}
    assert ma == {"PR-A", "PR-B"}, f"chưa gắn pháp nhân mà đã thu hẹp — sẽ làm sập Thu mua: {ma}"


# ── purchase_order ───────────────────────────────────────────────────────────────

def _hai_don(db, cty_a: int, cty_b: int):
    from app.modules.purchase_order.model import PurchaseOrder
    db.add_all([
        PurchaseOrder(code="PO-A", company_id=cty_a, status="approved", created_by=1),
        PurchaseOrder(code="PO-B", company_id=cty_b, status="approved", created_by=1),
        PurchaseOrder(code="PO-A-NHAP", company_id=cty_a, status="draft", created_by=1),
    ])
    db.flush()
    return PurchaseOrder


def test_po_gan_phap_nhan_thi_khong_nhat_don_cong_ty_khac(db):
    """ĐMH cùng luật với PYC — proc công ty A không nhặt đơn đã duyệt của công ty B."""
    CTY_A, CTY_B = 10, 20
    PO = _hai_don(db, CTY_A, CTY_B)

    user, profile = _ai_do(company_id=CTY_A)
    cond = _role_scope_cond(PO, "purchase_order", "proc", user, profile)

    ma = {p.code for p in db.query(PO).filter(cond).all()}
    assert ma == {"PO-A"}, f"proc công ty A nhặt nhầm đơn: {ma}"


def test_po_chua_gan_phap_nhan_van_nhat_het_nhu_cu(db):
    PO = _hai_don(db, 10, 20)

    user, profile = _ai_do(company_id=0)
    cond = _role_scope_cond(PO, "purchase_order", "proc", user, profile)

    ma = {p.code for p in db.query(PO).filter(cond).all()}
    assert ma == {"PO-A", "PO-B"}, f"chưa gắn pháp nhân mà đã thu hẹp đơn: {ma}"


# ── Người tạo/được giao vẫn thấy phiếu của mình, kể cả khác công ty ───────────────

def test_pr_van_thay_phieu_minh_tao_du_khac_cong_ty(db):
    """Thu hẹp CHỈ đánh vào nhánh nhặt-việc. Phiếu do CHÍNH mình tạo thì vẫn thấy dù thuộc
    công ty khác — nếu không, người vừa lập phiếu hộ công ty khác lại mất luôn phiếu đó."""
    from app.modules.purchase_request.model import PurchaseRequest
    CTY_A, CTY_KHAC = 10, 20
    db.add(PurchaseRequest(code="PR-MINE", company_id=CTY_KHAC, status="draft",
                           created_by=_NGUOI_LA_UID))
    db.flush()

    user, profile = _ai_do(company_id=CTY_A)
    cond = _role_scope_cond(PurchaseRequest, "purchase_request", "proc", user, profile)

    ma = {p.code for p in db.query(PurchaseRequest).filter(cond).all()}
    assert "PR-MINE" in ma, "phiếu do chính mình tạo bị mất sau khi thu hẹp theo pháp nhân"
