"""
test_dispatch.py — CR-034: YCMH có thêm bước ĐIỀU PHỐI (duyệt lần 2 phía thu mua).

Luồng mới: Nháp → Chờ duyệt → Đã duyệt (TP duyệt, CHƯA có NSTM, chưa tạo được ĐMH)
           → Đã điều phối (thu mua bấm, tự động phân bổ NSTM) → Đang xử lý → Hoàn thành.

Phủ:
1. dispatch_pr: chỉ chạy từ 'approved'; gán NSTM theo phân loại; đổi trạng thái.
2. Đếm dòng chưa có người (phân loại chưa cấu hình) để báo người điều phối chọn tay.
3. Tôn trọng gán tay: dòng đã có NSTM không bị ghi đè.
4. recompute_status: mốc làm việc là 'dispatched', KHÔNG phải 'approved'.
5. _ensure_pr_dispatched: chặn tạo ĐMH khi YCMH chưa điều phối.
6. _can_dispatch: trưởng phòng (phạm vi dept) không điều phối được; thu mua (proc/all) thì được.
7. Trả về phiếu đã điều phối → xóa sạch NSTM.
8. CÔNG TẮC `pr_dispatch_enabled`: tắt thì bỏ hẳn bước 2 — 'approved' trở lại là mốc làm việc được.
"""
import pytest
from fastapi import HTTPException

from app.modules.purchase_request import service as S
from app.modules.purchase_request.controller import _can_dispatch
from app.modules.purchase_request.model import PurchaseRequest, PurchaseRequestItem
from app.modules.purchase_order.service import _ensure_pr_dispatched


def _make_pr(db, seed, status="approved", groups=("Nhãn",), code="PYC-DP-01"):
    pr = PurchaseRequest(code=code, company_id=seed.company_id, requester="Người YC",
                         requester_id=seed.emp_req_id, department="Phòng Test",
                         status=status, created_by=seed.u_req_id, updated_by=seed.u_req_id)
    db.add(pr)
    db.flush()
    for i, g in enumerate(groups):
        db.add(PurchaseRequestItem(pr_id=pr.id, product_code=f"SP{i:02d}", product_name=f"Hàng {g}",
                                   item_group=g, qty=10, unit="cái", price=1000,
                                   created_by=seed.u_req_id, updated_by=seed.u_req_id))
    db.commit()
    db.refresh(pr)
    return pr


class TestDispatch:
    def test_duyet_xong_chua_co_nstm(self, db, seed):
        """Sau khi TP duyệt (approved), dòng hàng KHÔNG được tự gán NSTM nữa."""
        pr = _make_pr(db, seed)
        assert all(not it.assignee for it in S.items_of(db, pr.id))

    def test_dispatch_gan_nstm_va_doi_trang_thai(self, db, seed):
        """Điều phối → gán NSTM theo phân loại + trạng thái 'dispatched'."""
        pr = _make_pr(db, seed, groups=("Nhãn", "Thùng"))
        pr2, n, blank_count = S.dispatch_pr(db, pr.id, seed.u_req_id)
        assert pr2.status == "dispatched"
        assert n == 2 and blank_count == 0
        assert all(it.assignee == seed.emp_nstm_code for it in S.items_of(db, pr.id))

    def test_dispatch_dem_dong_chua_co_nguoi(self, db, seed):
        """Phân loại chưa cấu hình người phụ trách → đếm để báo người điều phối chọn tay."""
        pr = _make_pr(db, seed, groups=("Nhãn", "PhanLoaiChuaCauHinh"))
        _, n, blank_count = S.dispatch_pr(db, pr.id, seed.u_req_id)
        assert n == 1 and blank_count == 1

    def test_dispatch_ton_trong_gan_tay(self, db, seed):
        """Dòng đã được chọn tay trước khi điều phối → giữ nguyên, không bị ghi đè."""
        pr = _make_pr(db, seed, groups=("Nhãn",))
        it = S.items_of(db, pr.id)[0]
        it.assignee = seed.emp_backup_code
        db.commit()
        _, n, blank_count = S.dispatch_pr(db, pr.id, seed.u_req_id)
        assert n == 0 and blank_count == 0
        assert S.items_of(db, pr.id)[0].assignee == seed.emp_backup_code

    @pytest.mark.parametrize("st", ["draft", "submitted", "dispatched", "processing",
                                    "completed", "rejected", "cancelled"])
    def test_chi_dieu_phoi_duoc_tu_da_duyet(self, db, seed, st):
        """Mọi trạng thái khác 'approved' đều bị chặn (không điều phối 2 lần)."""
        pr = _make_pr(db, seed, status=st, code=f"PYC-DP-{st}")
        with pytest.raises(HTTPException) as e:
            S.dispatch_pr(db, pr.id, seed.u_req_id)
        assert e.value.status_code == 400

    def test_tra_ve_xoa_nstm(self, db, seed):
        """Trả phiếu đã điều phối về → xóa NSTM, phải điều phối lại từ đầu."""
        pr = _make_pr(db, seed)
        S.dispatch_pr(db, pr.id, seed.u_req_id)
        pr2 = S.return_pr(db, pr.id, "Sai số lượng", seed.u_req_id)
        assert pr2.status == "rejected"
        assert all(not it.assignee for it in S.items_of(db, pr.id))


class TestRecomputeStatus:
    def test_approved_khong_bi_suy_trang_thai(self, db, seed):
        """Phiếu chờ điều phối KHÔNG bị recompute kéo sang mốc làm việc."""
        pr = _make_pr(db, seed)
        S.recompute_status(db, pr)
        assert pr.status == "approved"

    def test_dispatched_giu_nguyen_khi_chua_dat_hang(self, db, seed):
        """Đã điều phối + mọi dòng 'Chưa đặt hàng' → vẫn là 'dispatched' (không tụt về 'approved')."""
        pr = _make_pr(db, seed)
        S.dispatch_pr(db, pr.id, seed.u_req_id)
        S.recompute_status(db, pr)
        assert pr.status == "dispatched"

    def test_dispatched_sang_processing(self, db, seed):
        """Có dòng đã đặt hàng → 'processing'."""
        pr = _make_pr(db, seed)
        S.dispatch_pr(db, pr.id, seed.u_req_id)
        it = S.items_of(db, pr.id)[0]
        it.line_status = "ordered"
        db.commit()
        S.recompute_status(db, pr)
        assert pr.status == "processing"


class TestChanTaoDMH:
    @pytest.mark.parametrize("st", ["draft", "submitted", "approved", "rejected"])
    def test_chan_khi_chua_dieu_phoi(self, db, seed, st):
        pr = _make_pr(db, seed, status=st, code=f"PYC-PO-{st}")
        with pytest.raises(HTTPException) as e:
            _ensure_pr_dispatched(db, pr.code)
        assert e.value.status_code == 400
        assert "chưa được điều phối" in e.value.detail

    def test_chan_khi_da_tu_choi(self, db, seed):
        pr = _make_pr(db, seed, status="cancelled", code="PYC-PO-CANCEL")
        with pytest.raises(HTTPException) as e:
            _ensure_pr_dispatched(db, pr.code)
        assert e.value.status_code == 400

    @pytest.mark.parametrize("st", ["dispatched", "processing", "completed"])
    def test_cho_qua_khi_da_dieu_phoi(self, db, seed, st):
        pr = _make_pr(db, seed, status=st, code=f"PYC-PO-OK-{st}")
        _ensure_pr_dispatched(db, pr.code)   # không ném lỗi

    def test_bo_qua_ma_khong_khop_phieu_nao(self, db, seed):
        """ĐMH nhập tay mã không có trong hệ thống (dữ liệu cũ) → không chặn."""
        _ensure_pr_dispatched(db, "PYC-KHONG-TON-TAI")
        _ensure_pr_dispatched(db, "")


class TestCongTacDieuPhoi:
    """Công tắc `pr_dispatch_enabled` (màn Cấu hình hệ thống) — tắt = quay về luồng cũ."""

    @pytest.fixture
    def tat_cong_tac(self, monkeypatch):
        monkeypatch.setattr(S, "dispatch_enabled", lambda: False)

    def test_tat_thi_khong_chan_tao_dmh_o_da_duyet(self, db, seed, tat_cong_tac):
        """Phiếu cũ còn kẹt ở 'Đã duyệt' lúc tắt công tắc vẫn tạo được ĐMH (không thì kẹt vĩnh viễn)."""
        pr = _make_pr(db, seed, status="approved", code="PYC-SW-OK")
        _ensure_pr_dispatched(db, pr.code)   # không ném lỗi

    @pytest.mark.parametrize("st", ["draft", "submitted", "rejected"])
    def test_tat_van_chan_phieu_chua_duyet(self, db, seed, tat_cong_tac, st):
        """Tắt công tắc chỉ bỏ bước 2, KHÔNG mở cho phiếu chưa duyệt xong."""
        pr = _make_pr(db, seed, status=st, code=f"PYC-SW-{st}")
        with pytest.raises(HTTPException) as e:
            _ensure_pr_dispatched(db, pr.code)
        assert e.value.status_code == 400

    def test_bat_thi_chan_o_da_duyet(self, db, seed):
        """Mặc định (bật) thì 'Đã duyệt' vẫn bị chặn — đối chứng cho test trên."""
        pr = _make_pr(db, seed, status="approved", code="PYC-SW-BAT")
        with pytest.raises(HTTPException):
            _ensure_pr_dispatched(db, pr.code)

    def test_tat_thi_recompute_chay_o_da_duyet(self, db, seed, tat_cong_tac):
        """Tắt công tắc: phiếu 'Đã duyệt' có dòng đã đặt hàng vẫn tự sang 'Đang xử lý'."""
        pr = _make_pr(db, seed, status="approved", code="PYC-SW-RC")
        it = S.items_of(db, pr.id)[0]
        it.line_status = "ordered"
        db.commit()
        S.recompute_status(db, pr)
        assert pr.status == "processing"


class TestQuyenDieuPhoi:
    def _profile(self, actions, scope):
        return {"grants": [{"perms": {"purchase_request": {**{a: True for a in actions}, "scope": scope}}}]}

    def test_truong_phong_khong_dieu_phoi_duoc(self):
        """dept_head: có approve nhưng phạm vi 'dept' → chỉ duyệt lần 1."""
        assert _can_dispatch(self._profile(["read", "approve"], "dept")) is False

    def test_admin_thu_mua_dieu_phoi_duoc(self):
        """pur_admin: approve + phạm vi 'proc'."""
        assert _can_dispatch(self._profile(["read", "approve"], "proc")) is True

    def test_quan_ly_thu_mua_dieu_phoi_duoc(self):
        """pur_manager: toàn quyền phạm vi 'all'."""
        assert _can_dispatch(self._profile(["read", "approve", "cancel"], "all")) is True

    def test_nhan_vien_thu_mua_khong_dieu_phoi_duoc(self):
        """pur_staff: không có approve."""
        assert _can_dispatch(self._profile(["read", "create", "write"], "assigned")) is False

    def test_khong_co_grant_nao(self):
        assert _can_dispatch({"grants": []}) is False
