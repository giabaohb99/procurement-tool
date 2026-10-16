"""ai-CR-207 — bốn lỗi cổng MCP Agent 1 tìm khi giả lập trên dev (đại ca 16/10: «vá 4 lỗi đó luôn»)."""
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.modules.agent_hub import mcp, mcp_keys


# 1) tools/list phải truyền chủ khóa xuống erp.tool_defs (chế độ tách dịch vụ: cổng B cần user_id).
def test_liet_ke_tool_truyen_chu_khoa(db, monkeypatch):
    from app.modules.agent_hub import erp
    from app.modules.assistant.provider.base import ToolDef

    seen: list = []
    monkeypatch.setattr(erp, "tool_defs", lambda db_, user=None: seen.append(user) or [
        ToolDef(name="purchase_report", description="x", parameters={}),
        ToolDef(name="payable_lookup", description="x", parameters={})])
    owner = SimpleNamespace(id=238, is_active=True)
    names = {t["name"] for t in mcp.list_tools(db, owner, mcp_keys.SCOPE_READ)}
    assert seen == [owner] and {"purchase_report", "payable_lookup", "report_issue"} <= names


# 2) Khóa chỉ đọc: danh sách TRẮNG — mọi tool khóa đọc thấy phải thuộc READ_TOOLS.
def test_khoa_chi_doc_chi_thay_tool_chi_doc():
    from app.modules.assistant.tools import tool_defs

    owner = SimpleNamespace(id=1, is_active=True)
    names = {t["name"] for t in mcp.list_tools(None, owner, mcp_keys.SCOPE_READ)} - {"report_issue"}
    assert names and names <= mcp.READ_TOOLS
    for bad in ("create_calendar_event", "update_calendar_event", "delete_calendar_event", "remember_fact", "forget_fact",
                "save_note", "add_personal_item", "mark_personal_item", "manage_briefs", "rewrite_meeting_minutes",
                "save_meeting_template", "deep_research", "ticket_create", "export_report_file"):
        assert bad not in names and mcp.is_write_tool(bad), bad
        assert "error" in mcp.call_tool(None, owner, mcp_keys.SCOPE_READ, bad, {})
    #  Danh sách trắng chỉ gồm tool có thật (gõ sai tên thì tool thật bị giấu oan).
    assert mcp.READ_TOOLS <= {d.name for d in tool_defs(None)}
    write_names = {t["name"] for t in mcp.list_tools(None, owner, mcp_keys.SCOPE_WRITE)}
    assert {"deep_research", "create_calendar_event", "confirm_draft"} <= write_names
    assert not write_names & {"propose_glossary_term", "report_missing_feature", "propose_document_update"}


# 3) Tool báo cáo đòi đúng quyền xem báo cáo (duoc-CR-562) — chung cho Trợ lý web / bot / MCP.
@pytest.mark.parametrize("name", ["purchase_report", "analytics_query", "top_suppliers_by_purchase"])
def test_tool_bao_cao_doi_quyen_xem_bao_cao(db, seed, monkeypatch, name):
    from app.modules.assistant import tools as T
    from app.modules.report_access import service as ra
    from app.modules.user.model import User

    user = db.get(User, seed.u_req_id)
    monkeypatch.setattr(ra, "can_view_report", lambda db_, u, key, profile=None: False)
    out = T.run_tool(db, user, name, {})
    assert out["denied"] and "Báo cáo mua hàng" in out["error"]
    monkeypatch.setattr(ra, "can_view_report", lambda db_, u, key, profile=None: True)
    assert "Chưa được giao xem báo cáo" not in str(T.run_tool(db, user, name, {}))     # qua lớp này, tới quyền vai trò
    #  Tool không gắn báo cáo thì không bị lớp này đụng.
    monkeypatch.setattr(ra, "can_view_report", lambda *a, **k: pytest.fail("không được hỏi"))
    T.run_tool(db, user, "product_search", {"q": "x"})


# 4) Tệp xuất: đường tải một lần, ký HMAC, 15 phút, không cần đăng nhập; MCP nối thành tuyệt đối.
def test_ma_tai_mot_lan_ky_hmac_va_het_han():
    from app.modules.assistant import download_tokens as dt

    tok = dt.make_token(42, 7, now=1000)
    assert dt.read_token(tok, now=1000 + 60)[:2] == (42, 7)
    assert dt.read_token(tok, now=1000 + dt.TTL_SEC + 1) is None                     # hết hạn
    fid, uid, exp, nonce, sig = tok.split(".")
    assert dt.read_token(".".join(["43", uid, exp, nonce, sig]), now=1000) is None   # sửa id → sai chữ ký
    assert dt.read_token("rac", now=1000) is None


def test_duong_tai_mot_lan_dung_xong_la_het(db, seed, monkeypatch):
    from app.core import storage
    from app.modules.assistant import controller, download_tokens as dt
    from app.modules.attachment.model import StoredFile

    sf = StoredFile(filename="bao-cao.xlsx", file_key="2026/10/assistant-report/7-bao-cao.xlsx", url="",
                    content_type="application/vnd.ms-excel", size=3, created_by=seed.u_req_id, updated_by=seed.u_req_id)
    db.add(sf)
    db.commit()
    monkeypatch.setattr(storage, "download_bytes", lambda key: b"abc")
    monkeypatch.setattr(controller, "_guard", lambda: None)
    tok = dt.make_token(sf.id, seed.u_req_id)
    resp = controller.download_report_file_once(tok, db)
    assert resp.body == b"abc" and "bao-c" in resp.headers["Content-Disposition"]
    with pytest.raises(HTTPException) as e:
        controller.download_report_file_once(tok, db)                              # lần hai: đã dùng
    assert e.value.status_code == 410
    with pytest.raises(HTTPException) as e:
        controller.download_report_file_once(dt.make_token(sf.id, seed.u_req_id + 1), db)   # không phải chủ tệp
    assert e.value.status_code == 404


def test_mcp_tra_duong_tai_tuyet_doi(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "AGENT_ERP_URL", "https://deverp.degoholding.vn")
    out = mcp._absolute_downloads({"file": {"id": 1, "download_url": "/api/assistant/files/1/download",
                                            "download_once_path": "/api/assistant/files/dl/abc"}})
    assert out["file"]["download_url"] == "https://deverp.degoholding.vn/api/assistant/files/dl/abc"
    assert "MỘT lần" in out["file"]["note"]
