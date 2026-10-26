"""kh-AI2-6 — AI LẬP phiếu đặt xe / duyệt dấu theo khuôn draft_* + confirm_draft. Tool chỉ soạn nháp; tạo thật bằng ĐÚNG
service của màn web, kiểm lại quyền create, công ty, người duyệt (luật duoc-CR-681). Phiếu duyệt dấu chỉ lưu Nháp (gửi duyệt
cần tệp đính kèm). Qua cổng MCP: nhóm «office_write» tắt mặc định chặn cả bước tạo."""
import json

import pytest

from app.modules.agent_hub import draft_create, mcp, mcp_keys, mcp_settings
from app.modules.assistant import tools as T
from app.modules.seal_request.model import SEAL_DRAFT, SealRequest
from app.modules.vehicle_booking import model as m

from test_dat_xe_chon_nguoi_duyet_cr681 import _fresh_perm_cache, org  # noqa: F401


def _draft(org, **over):
    args = {"purpose": "Đi Cần Thơ gặp khách", "start_location": "Văn phòng", "end_location": "Cần Thơ",
            "start_time": "2026-11-05 07:30", "end_time": "2026-11-05 18:00", "approver": "DP05", "company": "Công ty 5"}
    args.update(over)
    return T.run_tool(org.db, org.creator, "draft_vehicle_booking", args)


@pytest.fixture
def org_db(org, db):  # noqa: F811
    org.db = db
    return org


def test_soan_nhap_dat_xe_hoi_thieu_va_chon_nguoi_duyet(org_db, cap_quyen):
    org = org_db
    out = T.run_tool(org.db, org.creator, "draft_vehicle_booking", {"purpose": "Đi Cần Thơ"})
    assert {q["field"] for q in out["need_info"]} >= {"start_location", "start_time", "approver"}
    d = _draft(org)["draft"]
    assert d["first_approver_id"] == org.picked.id and d["company_id"] == 5 and d["start_time"] == "2026-11-05T07:30"
    assert "need_choice" in _draft(org, approver="ZZKHONGCO")                       # người không có quyền duyệt
    assert "need_choice" in _draft(org, approver="NV01")                            # không tự chọn mình
    assert "error" in _draft(org, end_time="2026-11-05 06:00")
    assert "error" in _draft(org, start_time="5/11 7h30")


def test_xac_nhan_tao_bang_service_web_va_gui_duyet(org_db, cap_quyen):
    org = org_db
    cap_quyen(org.creator.id, "vehicle_booking", scope="own", read=True, write=True)
    d = _draft(org)["draft"]
    code, oid = draft_create.create(org.db, org.creator, "vehicle_booking", d)
    bk = org.db.get(m.VehicleBooking, oid)
    assert bk.code == code and bk.status == m.BK_DRAFT and bk.first_approver_id == org.picked.id and bk.company_id == 5
    assert draft_create.missing_for_submit("vehicle_booking", {**d, "first_approver_id": 0}) == "Còn thiếu Người phê duyệt."
    draft_create.submit(org.db, org.creator, "vehicle_booking", oid)
    org.db.refresh(bk)
    assert bk.status == m.BK_PENDING


def test_xac_nhan_kiem_lai_nguoi_duyet(org_db):
    org = org_db
    d = _draft(org)["draft"]
    #  Người duyệt bị gỡ quyền giữa hai bước → service của web chặn.
    with pytest.raises(draft_create.DraftError, match="quyền duyệt"):
        draft_create.create(org.db, org.creator, "vehicle_booking", {**d, "first_approver_id": org.own_only.id})


def test_duyet_dau_chi_luu_nhap(org_db, cap_quyen):
    org = org_db
    cap_quyen(org.creator.id, "seal_request", scope="own", read=True, create=True)
    out = T.run_tool(org.db, org.creator, "draft_seal_request",
                     {"purpose": "Đóng dấu hợp đồng đại lý", "companies": ["Công ty 3", "Công ty 5"], "copies": 2})
    d = out["draft"]
    assert d["company_ids"] == [3, 5] and d["copies"] == 2 and "Gửi duyệt" in out["note"]
    code, oid = draft_create.create(org.db, org.creator, "seal_request", d)
    req = org.db.get(SealRequest, oid)
    assert req.status == SEAL_DRAFT and req.code == code and req.purpose == "Đóng dấu hợp đồng đại lý"
    assert "seal_request" not in draft_create.SUBMITTABLE
    assert T.run_tool(org.db, org.picked, "draft_seal_request", {"purpose": "x", "companies": ["Công ty 3"]}).get("denied")


def test_cong_mcp_nhom_office_write_tat_thi_chan(org_db, monkeypatch):
    org = org_db
    d = _draft(org)["draft"]

    class _Key:
        scope, id = mcp_keys.SCOPE_WRITE, 1

    def call(name, args):
        res = mcp.handle(org.db, org.creator, _Key(), {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                                                       "params": {"name": name, "arguments": args}}, {})
        return json.loads(res["result"]["content"][0]["text"])

    assert call("confirm_draft", {"kind": "vehicle_booking", "draft": d}).get("denied") is True
    assert org.db.query(m.VehicleBooking).count() == 0
    assert mcp_settings.GROUP_OF["draft_vehicle_booking"].key == "office_write"
    real = mcp_settings.tool_blocked
    monkeypatch.setattr(mcp_settings, "tool_blocked",
                        lambda db, name, args=None: None if name.startswith("draft_") else real(db, name, args))
    out = call("confirm_draft", {"kind": "vehicle_booking", "draft": d})
    assert out["ok"] is True and out["link"].endswith(f"/vehicle-booking/{out['id']}")
