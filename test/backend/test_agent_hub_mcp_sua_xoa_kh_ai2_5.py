"""kh-AI2-5 — sửa / xóa phiếu qua cổng MCP: propose_document_update / propose_document_delete trả đề xuất kèm token,
confirm_draft(kind="update" / "delete") mới ghi, ERP kiểm lại từ đầu như nút Xác nhận của Trợ lý web. Chỉ khóa được ghi,
chỉ khi nhóm G7 «edit» bật; giữ luật cũ: chỉ xóa phiếu của chính mình, còn Nháp / Bị trả lại; YCTT không xóa qua AI."""
import json

import pytest

from app.modules.agent_hub import mcp, mcp_keys, mcp_settings
from app.modules.purchase_request.model import PurchaseRequest
from app.modules.user.model import User

from test_assistant_update_tool import _tao_ycmh


@pytest.fixture
def edit_on(monkeypatch):
    real = mcp_settings.tool_blocked
    monkeypatch.setattr(mcp_settings, "tool_blocked",
                        lambda db, name, args=None: None if name in mcp.PROPOSAL_TOOLS else real(db, name, args))


def _call(db, user, name, args, scope=mcp_keys.SCOPE_WRITE):
    class _Key:
        pass

    key = _Key()
    key.scope, key.id = scope, 1
    res = mcp.handle(db, user, key, {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                                     "params": {"name": name, "arguments": args}}, {})
    return json.loads(res["result"]["content"][0]["text"])


def _boss(db, seed, cap_quyen, **actions):
    cap_quyen(seed.u_req_id, "purchase_request", scope="own", read=True, **actions)
    return db.get(User, seed.u_req_id)


def test_sua_qua_mcp_hai_buoc_ghi_dung_service(db, seed, cap_quyen, edit_on):
    user = _boss(db, seed, cap_quyen, write=True)
    pr = _tao_ycmh(db, seed, created_by=seed.u_req_id)
    out = _call(db, user, "propose_document_update",
                {"entity": "purchase_request", "code": "YCMH-TEST-1", "changes": {"purpose": "Mua giấy A5"}})
    proposal = out["proposal"]
    assert "confirm_draft" in out["reminder"] and 'kind="update"' in out["reminder"]
    db.refresh(pr)
    assert pr.purpose == "Mua giấy A4"                                            # chưa xác nhận thì chưa ghi
    #  Sai kind thì không ghi gì.
    assert "kind không khớp" in _call(db, user, "confirm_draft", {"kind": "delete", "draft": proposal})["error"]
    done = _call(db, user, "confirm_draft", {"kind": "update", "draft": proposal})
    assert done["ok"] is True and done["code"] == "YCMH-TEST-1"
    db.refresh(pr)
    assert pr.purpose == "Mua giấy A5"


def test_xac_nhan_kiem_lai_tu_dau(db, seed, cap_quyen, edit_on):
    user = _boss(db, seed, cap_quyen, write=True)
    pr = _tao_ycmh(db, seed, created_by=seed.u_req_id)
    proposal = _call(db, user, "propose_document_update",
                     {"entity": "purchase_request", "code": "YCMH-TEST-1", "changes": {"purpose": "X"}})["proposal"]
    pr.status = "submitted"                                                       # phiếu đổi trạng thái giữa hai bước
    db.commit()
    out = _call(db, user, "confirm_draft", {"kind": "update", "draft": proposal})
    assert "error" in out and "Chưa ghi gì" in out["error"]
    db.refresh(pr)
    assert pr.purpose == "Mua giấy A4"
    assert "confirm_token" in _call(db, user, "confirm_draft", {"kind": "update", "draft": {}})["error"]


def test_xoa_chi_phieu_nhap_cua_minh(db, seed, cap_quyen, edit_on):
    user = _boss(db, seed, cap_quyen, write=True, delete=True)
    pr = _tao_ycmh(db, seed, created_by=seed.u_req_id)
    out = _call(db, user, "propose_document_delete", {"entity": "purchase_request", "code": "YCMH-TEST-1"})
    assert 'kind="delete"' in out["reminder"]
    done = _call(db, user, "confirm_draft", {"kind": "delete", "draft": out["proposal"]})
    assert done["ok"] is True and done["deleted"] is True
    db.refresh(pr)
    assert pr.is_deleted
    #  Đề nghị thanh toán không xóa qua AI.
    assert "error" in _call(db, user, "propose_document_delete", {"entity": "payment_request", "code": "YCTT-1"})


def test_khoa_chi_doc_va_nhom_tat_khong_dung_duoc(db, seed, cap_quyen):
    user = _boss(db, seed, cap_quyen, write=True)
    _tao_ycmh(db, seed, created_by=seed.u_req_id)
    args = {"entity": "purchase_request", "code": "YCMH-TEST-1", "changes": {"purpose": "X"}}
    assert _call(db, user, "propose_document_update", args, scope=mcp_keys.SCOPE_READ).get("denied") is True
    #  Nhóm «edit» tắt mặc định: khóa được ghi cũng bị chặn, kể cả đường xác nhận.
    assert _call(db, user, "propose_document_update", args).get("denied") is True
    assert _call(db, user, "confirm_draft", {"kind": "update", "draft": {"confirm_token": "x"}}).get("denied") is True
    assert db.query(PurchaseRequest).one().purpose == "Mua giấy A4"
    names = {t["name"] for t in mcp.list_tools(db, user, mcp_keys.SCOPE_READ)}
    assert not names & mcp.PROPOSAL_TOOLS
    assert mcp_settings.GROUP_OF["propose_document_delete"].key == "edit"


def test_server_discover_tra_rong(db, seed):
    user = db.get(User, seed.u_req_id)
    res = mcp.handle(db, user, None, {"jsonrpc": "2.0", "id": 7, "method": "server/discover"}, {})
    assert res == {"jsonrpc": "2.0", "id": 7, "result": {}}
