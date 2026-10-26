"""kh-AI2-7 — AI duyệt phiếu đợt 1 (đặt xe, đặt phòng họp, nghỉ phép): propose_approval chỉ đề xuất + token; xác nhận mới ghi,
kiểm lại từ đầu bằng đúng đường duyệt của web. Năm ca A1 yêu cầu: không phải người duyệt bị chặn, loại phiếu ngoài danh sách
bị chặn, đổi trạng thái giữa hai bước bị chặn, từ chối phải có lý do, nhóm G7 «approve» tắt bị chặn."""
import json

import pytest
from fastapi import HTTPException

from app.modules.agent_hub import mcp, mcp_keys, mcp_settings
from app.modules.assistant import tools as T
from app.modules.assistant.tools.update_tool import confirm_update
from app.modules.audit.model import AuditLog
from app.modules.vehicle_booking import model as m
from app.modules.vehicle_booking.service import create_booking

from test_dat_xe_chon_nguoi_duyet_cr681 import (_engine_with_permission_step, _fresh_perm_cache,  # noqa: F401
                                                 _payload, org)


def _pending(db, org):  # noqa: F811
    return create_booking(db, _payload(company_id=3, first_approver_id=org.picked.id), org.creator, submit=True)


def _propose(db, user, **kw):
    return T.run_tool(db, user, "propose_approval", {"entity": "vehicle_booking", "action": "approve", **kw})


def test_nguoi_duoc_giao_duyet_qua_hai_buoc(db, org):  # noqa: F811
    bk = _pending(db, org)
    out = _propose(db, org.other, code=bk.code, note="Đồng ý")
    p = out["proposal"]
    assert p["kind"] == "approval_proposal" and p["step"] == "duyệt một bước" and "Lộ trình" in str(p["summary"])
    db.refresh(bk)
    assert bk.status == m.BK_PENDING                                                   # chưa xác nhận thì chưa duyệt
    done = confirm_update(db, org.other, p["confirm_token"])
    db.refresh(bk)
    assert done["approved"] is True and bk.status == m.BK_APPROVED
    log = db.query(AuditLog).filter(AuditLog.entity == "vehicle_booking", AuditLog.entity_id == bk.id).all()
    assert any("qua AI" in (r.message or "") for r in log)
    with pytest.raises(HTTPException):                                                # token dùng lại: phiếu đã xong
        confirm_update(db, org.other, p["confirm_token"])


def test_khong_phai_nguoi_duyet_bi_chan(db, org):  # noqa: F811
    bk = _pending(db, org)
    for who in (org.creator, org.own_only):                                           # người đặt; phạm vi «của mình»
        out = _propose(db, who, id=bk.id)
        assert out.get("denied") is True and "đang chờ bạn duyệt" in out["reason"]
    ghost = _propose(db, org.other, code="DX99999")
    assert ghost["reason"].replace("DX99999", "?") == _propose(db, org.creator, code=bk.code)["reason"].replace(bk.code, "?")


def test_luong_nhieu_buoc_chi_nguoi_co_viec_cho(db, org):  # noqa: F811
    _engine_with_permission_step(db)
    bk = _pending(db, org)
    assert _propose(db, org.other, id=bk.id).get("denied") is True                   # có quyền nhưng không được giao việc
    p = _propose(db, org.picked, id=bk.id, note="ok")["proposal"]
    assert p["step"] == "chặng 1"
    confirm_update(db, org.picked, p["confirm_token"])
    db.refresh(bk)
    assert bk.status == m.BK_APPROVED


def test_loai_ngoai_danh_sach_va_tu_choi_can_ly_do(db, org):  # noqa: F811
    bk = _pending(db, org)
    for entity in ("payment_request", "purchase_order", "seal_request", "document"):
        out = T.run_tool(db, org.other, "propose_approval", {"entity": entity, "id": 1, "action": "approve"})
        assert "chỉ duyệt phiếu đặt xe, đặt phòng họp và đơn nghỉ phép" in out["error"]
    assert "lý do" in _propose(db, org.other, id=bk.id, action="reject")["error"]
    p = _propose(db, org.other, id=bk.id, action="reject", note="Trùng lịch xe")["proposal"]
    confirm_update(db, org.other, p["confirm_token"])
    db.refresh(bk)
    assert bk.status != m.BK_PENDING and bk.status != m.BK_APPROVED


def test_doi_trang_thai_giua_hai_buoc_bi_chan(db, org):  # noqa: F811
    bk = _pending(db, org)
    p = _propose(db, org.other, id=bk.id)["proposal"]
    bk.purpose = "Người đặt sửa phiếu"                                                 # phiếu đổi (updated_at) sau đề xuất
    db.commit()
    from datetime import datetime, timedelta
    bk.updated_at = datetime.utcnow() + timedelta(minutes=1)
    db.commit()
    with pytest.raises(HTTPException) as e:
        confirm_update(db, org.other, p["confirm_token"])
    assert e.value.status_code == 409
    db.refresh(bk)
    assert bk.status == m.BK_PENDING


def test_cong_mcp_nhom_approve_tat_bi_chan_va_kind_phai_khop(db, org, monkeypatch):  # noqa: F811
    bk = _pending(db, org)

    class _Key:
        scope, id = mcp_keys.SCOPE_WRITE, 1

    def call(name, args):
        res = mcp.handle(db, org.other, _Key(), {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                                                  "params": {"name": name, "arguments": args}}, {})
        return json.loads(res["result"]["content"][0]["text"])

    assert call("propose_approval", {"entity": "vehicle_booking", "id": bk.id, "action": "approve"}).get("denied") is True
    assert mcp_settings.GROUP_OF["propose_approval"].key == "approve"
    real = mcp_settings.tool_blocked
    monkeypatch.setattr(mcp_settings, "tool_blocked",
                        lambda db_, name, args=None: None if name == "propose_approval" else real(db_, name, args))
    out = call("propose_approval", {"entity": "vehicle_booking", "id": bk.id, "action": "approve"})
    assert 'kind=\\"approval\\"' in json.dumps(out) or 'kind="approval"' in out["reminder"]
    #  Xác nhận nhầm kind (update) không bao giờ thành duyệt: bị nhóm sửa / xóa chặn hoặc báo kind không khớp.
    wrong = call("confirm_draft", {"kind": "update", "draft": out["proposal"]})
    assert wrong.get("denied") or "kind không khớp" in wrong.get("error", "")
    db.refresh(bk)
    assert bk.status == m.BK_PENDING
    done = call("confirm_draft", {"kind": "approval", "draft": out["proposal"]})
    db.refresh(bk)
    assert done["ok"] is True and bk.status == m.BK_APPROVED


def test_route_duyet_phong_hop_nghi_phep_dung_chu_ky():
    """Phòng họp và nghỉ phép chưa có ca dữ liệu ở đây — canh chữ ký hàm route mà confirm_approval gọi thẳng."""
    import inspect

    from app.modules.leave import request_controller as lr
    from app.modules.meeting_room import controller as mr

    for fn in (lr.approve_request, mr.approve_booking):
        assert list(inspect.signature(fn).parameters)[:3] == [list(inspect.signature(fn).parameters)[0], "db", "user"]
    for fn in (lr.reject_request, mr.reject_booking):
        assert list(inspect.signature(fn).parameters)[1:4] == ["reason", "db", "user"]
