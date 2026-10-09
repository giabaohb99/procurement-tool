"""ai-CR-143 — đại ca 09/10/2026: «tạo nhiều như vậy thì ra nhiều đơn nháp lắm đúng không, có thể tận dụng nó, hoặc anh nhắn
là xóa bớt đơn nháp đi». Đơn nghỉ nháp trùng ngày → sửa đè đơn cũ; «đơn nháp của tôi» / «xóa đơn nháp 2» / «xóa hết đơn
nháp» → thẻ xác nhận → «đúng». Chỉ phiếu NHÁP do chính mình lập."""
from datetime import date

import pytest

from app.modules.agent_hub import draft_create as dc


def _rows(db, me: int, other: int):
    from app.modules.leave.constants import LR_DRAFT
    from app.modules.leave.request_model import LeaveRequest
    from app.modules.purchase_request.model import PurchaseRequest

    rows = [
        LeaveRequest(code="NP001", from_date=date(2026, 10, 12), to_date=date(2026, 10, 12), reason="khám bệnh",
                     status=LR_DRAFT, created_by=me, updated_by=me),
        LeaveRequest(code="NP002", from_date=date(2026, 10, 20), to_date=date(2026, 10, 21), reason="về quê",
                     status=LR_DRAFT, created_by=me, updated_by=me),
        LeaveRequest(code="NP003", from_date=date(2026, 10, 12), to_date=date(2026, 10, 12), reason="đã gửi",
                     status=2, created_by=me, updated_by=me),                                  # đã gửi duyệt
        LeaveRequest(code="NP004", from_date=date(2026, 10, 12), to_date=date(2026, 10, 12), reason="của người khác",
                     status=LR_DRAFT, created_by=other, updated_by=other),
        PurchaseRequest(code="YCMH001", purpose="mua giấy A4", status="draft", created_by=me, updated_by=me),
        PurchaseRequest(code="YCMH002", purpose="đã duyệt", status="approved", created_by=me, updated_by=me),
    ]
    db.add_all(rows)
    db.commit()
    return {r.code: r for r in rows}


def test_chi_liet_ke_phieu_nhap_cua_chinh_minh(db, seed):
    from types import SimpleNamespace

    rows = _rows(db, seed.u_req_id, seed.u_nstm_id)
    mine = dc.list_mine(db, SimpleNamespace(id=seed.u_req_id))
    assert sorted(x["code"] for x in mine) == ["NP001", "NP002", "YCMH001"]
    hit = dc.same_days_leave(mine, {"from_date": "2026-10-12", "to_date": "2026-10-12"})
    assert hit is not None and hit["code"] == "NP001"
    assert dc.same_days_leave(mine, {"from_date": "2026-10-15", "to_date": "2026-10-15"}) is None
    assert dc.same_days_leave(mine, {"from_date": "2026-10-21", "to_date": "2026-10-22"})["code"] == "NP002"
    assert rows["NP004"].created_by != seed.u_req_id


def test_xoa_chi_phieu_nhap_cua_minh(db, seed, monkeypatch):
    import app.core.auth as auth
    from app.modules.leave.request_model import LeaveRequest
    from app.modules.purchase_request.model import PurchaseRequest
    from app.modules.user.model import User

    monkeypatch.setattr(auth, "user_has_permission", lambda db, user, entity, action="read": True)
    rows = _rows(db, seed.u_req_id, seed.u_nstm_id)
    me = db.get(User, seed.u_req_id)
    out = dc.delete_mine(db, me, [{"kind": "leave", "id": rows["NP001"].id},
                                  {"kind": "leave", "id": rows["NP003"].id},       # không còn nháp
                                  {"kind": "leave", "id": rows["NP004"].id},       # của người khác
                                  {"kind": "purchase", "id": rows["YCMH001"].id},
                                  {"kind": "purchase", "id": rows["YCMH002"].id},  # đã duyệt
                                  {"kind": "la", "id": 1}])
    assert out["deleted"] == ["NP001", "YCMH001"] and len(out["skipped"]) == 4
    assert db.get(LeaveRequest, rows["NP001"].id).is_deleted is True
    assert db.get(LeaveRequest, rows["NP004"].id).is_deleted is False
    assert db.get(PurchaseRequest, rows["YCMH002"].id).is_deleted is False


@pytest.fixture
def chat(db, monkeypatch):
    from types import SimpleNamespace

    from app.core.config import settings
    from app.modules.agent_hub import erp, service

    monkeypatch.setattr(settings, "AGENT_TELEGRAM_CHAT_ID", "12345")
    me = SimpleNamespace(id=7)
    monkeypatch.setattr(service, "_assistant_user", lambda db, chat_id="": me)
    sent: list[str] = []
    monkeypatch.setattr(service, "reply", lambda db, chat_id, text, **kw: sent.append(text))
    drafts = [{"kind": "leave", "id": 11, "code": "NP001", "title": "Nghỉ 12/10 · khám bệnh",
               "from_date": "2026-10-12", "to_date": "2026-10-12"},
              {"kind": "purchase", "id": 21, "code": "YCMH001", "title": "mua giấy A4"}]
    monkeypatch.setattr(erp, "my_drafts", lambda db, user: list(drafts))
    deleted: list = []
    monkeypatch.setattr(erp, "delete_my_drafts", lambda db, user, items: deleted.append(items) or {
        "deleted": [d["code"] for d in drafts if {"kind": d["kind"], "id": d["id"]} in items], "skipped": []})
    return service, sent, deleted


def _say(db, service, text):
    from app.modules.agent_hub.constants import DIR_IN

    row = service.log_message(db, DIR_IN, "12345", 1, text)
    db.commit()
    return service._my_drafts_by_text(db, "12345", row, text)


def test_xem_va_xoa_don_nhap_qua_the_xac_nhan(db, chat):
    service, sent, deleted = chat
    assert _say(db, service, "đơn nháp của tôi?") and "NP001" in sent[-1] and "YCMH001" in sent[-1]
    assert "«" not in sent[-1]
    assert _say(db, service, "xóa bớt đơn nháp đi") and "PHIẾU NHÁP CỦA ANH/CHỊ" in sent[-1] and deleted == []
    assert _say(db, service, "xóa đơn nháp 2") and "XÓA 1 PHIẾU NHÁP?" in sent[-1] and "YCMH001" in sent[-1]
    assert deleted == []                                                     # chưa «đúng» thì chưa xóa
    assert _say(db, service, "đúng")
    assert deleted == [[{"kind": "purchase", "id": 21}]] and "Đã xóa 1 phiếu nháp: YCMH001" in sent[-1]
    assert _say(db, service, "xóa hết đơn nháp") and "XÓA 2 PHIẾU NHÁP?" in sent[-1]
    assert _say(db, service, "thôi") and "không xóa" in sent[-1] and len(deleted) == 1
    assert _say(db, service, "xóa đơn nháp 9") and "Không có phiếu nháp số 9" in sent[-1]
    assert not _say(db, service, "đúng")                                      # không còn thẻ chờ: không nuốt câu
    assert not _say(db, service, "đơn nghỉ phép tháng này của tôi")


def test_tao_lai_don_nghi_trung_ngay_thi_sua_don_nhap_cu(db, monkeypatch):
    """Bấm «tạo» cho bản nháp đơn nghỉ trùng ngày với đơn nháp sẵn có → sửa đè, không lập đơn thứ hai."""
    from types import SimpleNamespace

    from app.core.config import settings
    from app.modules.agent_hub import erp, service
    from app.modules.agent_hub.constants import DIR_IN

    monkeypatch.setattr(settings, "AGENT_TELEGRAM_CHAT_ID", "12345")
    me = SimpleNamespace(id=7)
    monkeypatch.setattr(service, "_assistant_user", lambda db, chat_id="": me)
    sent: list[str] = []
    monkeypatch.setattr(service, "reply", lambda db, chat_id, text, **kw: sent.append(text))
    monkeypatch.setattr(erp, "my_drafts", lambda db, user: [{"kind": "leave", "id": 11, "code": "NP001", "title": "x",
                                                             "from_date": "2026-10-12", "to_date": "2026-10-12"}])
    calls: list = []
    monkeypatch.setattr(erp, "update_leave_draft", lambda db, user, oid, draft: calls.append(("update", oid)) or "NP001")
    monkeypatch.setattr(erp, "create_draft", lambda db, user, kind, draft: calls.append(("create",)) or ("NP009", 99))
    monkeypatch.setattr(erp, "created_details", lambda db, kind, oid: [])
    draft = {"kind": "leave_request", "lines": [{"leave_type_id": 1, "leave_type": "Phép năm", "days": 1}],
             "from_date": "2026-10-12", "to_date": "2026-10-12", "from_session": 1, "to_session": 1,
             "reason": "đưa con đi khám"}
    service._offer_draft(db, "12345", me, {"name": "draft_leave_request", "draft": draft})
    row = service.log_message(db, DIR_IN, "12345", 1, "tạo")
    db.commit()
    assert service._draft_by_text(db, "12345", row, "tạo")
    assert calls == [("update", 11)] and "Đã cập nhật đơn nghỉ phép nháp NP001" in sent[-1]
