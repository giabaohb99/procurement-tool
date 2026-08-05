"""Nhận / trả phiếu hỗ trợ (service.assign) + phân biệt handler.

Màn quản lý /tickets có nút "Nhận" gọi POST /api/tickets/{id}/assign.
Nghiệp vụ: nhận phiếu còn 'Mới' thì tự chuyển 'Đang xử lý'; trả phiếu = assignee_id 0.
"""
from types import SimpleNamespace

from app.modules.ticket import service
from app.modules.ticket.controller import _is_handler


def _phieu(db, status="open", assignee_id=0):
    data = SimpleNamespace(subject="Không đăng nhập được", department="Kỹ thuật / Phần mềm",
                           priority="normal", body="Mô tả lỗi", company_id=1,
                           origin_url="/purchase-orders", file_ids=[])
    t = service.create_ticket(db, data, user_id=10, requester_emp_id=5)
    if status != "open" or assignee_id:
        t.status = status
        t.assignee_id = assignee_id
        db.commit()
    return t


def test_nhan_phieu_moi_thi_tu_chuyen_dang_xu_ly(db):
    t = _phieu(db)
    assert t.status == "open" and t.assignee_id == 0
    service.assign(db, t.id, assignee_id=7, user_id=7)
    db.refresh(t)
    assert t.assignee_id == 7
    assert t.status == "in_progress"


def test_nhan_phieu_da_tra_loi_khong_keo_lui_trang_thai(db):
    """Phiếu đang 'Đã trả lời' mà người khác nhận thì giữ nguyên trạng thái."""
    t = _phieu(db, status="answered")
    service.assign(db, t.id, assignee_id=7, user_id=7)
    db.refresh(t)
    assert t.assignee_id == 7
    assert t.status == "answered"


def test_tra_phieu_ve_hang_cho(db):
    t = _phieu(db, status="in_progress", assignee_id=7)
    service.assign(db, t.id, assignee_id=0, user_id=7)
    db.refresh(t)
    assert t.assignee_id == 0
    assert t.status == "in_progress"      # trả phiếu không đổi trạng thái


def test_is_handler_chi_dung_cho_scope_rong():
    """Nhân viên thường có ticket read scope 'own' → KHÔNG phải nhóm Hỗ trợ."""
    nv = {"grants": [{"perms": {"ticket": {"read": True, "scope": "own"}}}]}
    ht = {"grants": [{"perms": {"ticket": {"read": True, "scope": "all"}}}]}
    khong = {"grants": [{"perms": {"purchase_order": {"read": True, "scope": "all"}}}]}
    assert _is_handler(nv) is False
    assert _is_handler(ht) is True
    assert _is_handler(khong) is False
