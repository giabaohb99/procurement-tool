"""bao-CR-294 (ticket 21) — cột "Ngày cập nhật" + sắp xếp theo lần cập nhật gần nhất.

Cơ chế sort server-side (`sort_by`/`sort_dir` -> apply_sort, whitelist cột thật) có sẵn từ
trước; CR này chỉ (1) trả `updated_at` ra mọi danh sách và (2) thêm cột lên bảng. Test canh:
  - apply_sort theo `updated_at` ra đúng thứ tự cả hai chiều;
  - `updated_at` là cột thật nên lọt whitelist (không bị rơi về mặc định id desc);
  - OutSchema của danh mục (ProductOut làm đại diện) đã khai `updated_at`.
"""
from datetime import datetime

from app.core.base_controller import apply_sort
from app.modules.purchase_request.model import PurchaseRequest


def _make_pr(db, seed, code: str, updated_at: datetime) -> PurchaseRequest:
    pr = PurchaseRequest(code=code, company_id=seed.company_id, requester="Người YC",
                         requester_id=seed.emp_req_id, department="Phòng Test",
                         status="draft", request_date="2026-09-01",
                         created_by=seed.u_req_id, updated_by=seed.u_req_id,
                         updated_at=updated_at)   # đặt tay để hai phiếu cách nhau rõ ràng
    db.add(pr)
    db.commit()
    db.refresh(pr)
    return pr


class TestSortNgayCapNhat:
    def test_sort_updated_at_desc_gan_nhat_truoc(self, db, seed):
        cu = _make_pr(db, seed, "PYC-T21-A", datetime(2026, 1, 1, 8, 0, 0))
        moi = _make_pr(db, seed, "PYC-T21-B", datetime(2026, 2, 2, 8, 0, 0))
        rows = apply_sort(db.query(PurchaseRequest), PurchaseRequest,
                          "updated_at", "desc").all()
        assert [r.code for r in rows[:2]] == [moi.code, cu.code]

    def test_sort_updated_at_asc(self, db, seed):
        cu = _make_pr(db, seed, "PYC-T21-C", datetime(2026, 1, 1, 8, 0, 0))
        moi = _make_pr(db, seed, "PYC-T21-D", datetime(2026, 2, 2, 8, 0, 0))
        rows = apply_sort(db.query(PurchaseRequest), PurchaseRequest,
                          "updated_at", "asc").all()
        assert [r.code for r in rows] == [cu.code, moi.code]

    def test_cot_rac_roi_ve_mac_dinh_id_desc(self, db, seed):
        """Cột không có thật (vd người dùng sửa tay query param) -> whitelist bỏ qua, id desc."""
        a = _make_pr(db, seed, "PYC-T21-E", datetime(2026, 2, 2, 8, 0, 0))
        b = _make_pr(db, seed, "PYC-T21-F", datetime(2026, 1, 1, 8, 0, 0))
        rows = apply_sort(db.query(PurchaseRequest), PurchaseRequest,
                          "khong_ton_tai", "desc").all()
        assert [r.code for r in rows[:2]] == [b.code, a.code]   # id desc: tạo sau đứng trước

    def test_product_out_khai_updated_at(self):
        from app.modules.product.schema import ProductOut
        assert "updated_at" in ProductOut.model_fields
