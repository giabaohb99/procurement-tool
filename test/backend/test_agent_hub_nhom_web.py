"""ai-CR-123: màn «Nhóm chat» trên ERP v2 — danh sách theo kênh / loại, đọc tin, tệp, bản tóm tắt, quyền quản lý bot AI.

Đại ca chốt 08/10: người thường xem nhóm mình là thành viên; người có `agent_group.read` (quản lý AI) thấy HẾT kể cả
nội dung, có nhật ký xem; `agent_group.write` phân loại / ngừng ghi / đăng nhập Zalo công ty.
"""
from datetime import datetime, timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.auth import get_current_user
from app.core.config import settings
from app.core.database import get_db


@pytest.fixture
def web(db, seed, monkeypatch):
    from app.modules.agent_hub import controller, groups, telegram
    from app.modules.user.model import User

    monkeypatch.setattr(telegram, "_call", lambda *a, **kw: pytest.fail("không được gọi Telegram thật"))
    groups._MEMBER_CACHE.clear()
    app = FastAPI()
    app.include_router(controller.router)
    who = {"id": seed.u_req_id}
    app.dependency_overrides[get_current_user] = lambda: db.get(User, who["id"])
    app.dependency_overrides[get_db] = lambda: db
    return TestClient(app), who


def _zalo_group(db, gid: str, title: str, members: list[str], owner: int = 0):
    from app.modules.agent_hub import zalo_account as za

    g = za.apply_group(db, {"group_id": gid, "name": title, "member_ids": members})
    g.owner_user_id = owner
    db.commit()
    return g


def _link(db, user_id: int, chat: str):
    from app.modules.agent_hub.model import AgentChatLink

    db.add(AgentChatLink(user_id=user_id, chat_id=chat, linked_at=datetime.now(),
                         expires_at=datetime.now() + timedelta(days=30), created_by=0, updated_by=0))
    db.commit()


def _say(db, chat: str, text: str, uid: str = "u1", name: str = "Chị Mi", mid: str = "m", **content):
    from app.modules.agent_hub import service, zalo_account as za

    ev = {"kind": "message", "thread_type": "group", "thread_id": chat, "msg_id": mid, "from_uid": uid,
          "from_name": name, "ts": int(datetime.now().timestamp() * 1000), "content": content or text,
          "msg_type": "share.file" if content else "webchat"}
    service.handle_message(db, za.normalize(ev))
    db.commit()


def test_nguoi_thuong_chi_thay_nhom_minh_quan_ly_ai_thay_het_co_nhat_ky(db, seed, web, cap_quyen):
    from app.modules.agent_hub.model import AgentGroup, AgentGroupView

    client, who = web
    _link(db, seed.u_req_id, "zu:u1")
    kt = _zalo_group(db, "g1", "Kế toán DEGO", ["u1", "u2"], owner=seed.u_req_id)
    _zalo_group(db, "g2", "Ban giám đốc", ["u9"])
    _say(db, "g1", "chốt thanh toán thứ 6", mid="a")
    _say(db, "g2", "lương tháng 10", uid="u9", name="Sếp", mid="b")

    mine = client.get("/api/agent-hub/groups").json()["data"]
    assert [i["title"] for i in mine["items"]] == ["Kế toán DEGO"] and mine["can_view_all"] is False
    item = mine["items"][0]
    assert item["channel"] == "zalo_account" and item["message_count"] == 1 and item["is_owner"] and item["can_edit"]
    #  Người thường xin «tất cả» vẫn chỉ ra nhóm mình; nhóm khác là 404 (không lộ nhóm tồn tại).
    assert len(client.get("/api/agent-hub/groups?scope=all").json()["data"]["items"]) == 1
    other = db.query(AgentGroup).filter_by(title="Ban giám đốc").one()
    assert client.get(f"/api/agent-hub/groups/{other.id}/messages").status_code == 404

    #  Quản lý bot AI: thấy hết, đọc được nội dung, mỗi lần mở nhóm mình không ở thì có dòng nhật ký.
    who["id"] = seed.u_nstm_id
    cap_quyen(seed.u_nstm_id, "agent_group", read=True)
    all_ = client.get("/api/agent-hub/groups?scope=all").json()["data"]
    assert {i["title"] for i in all_["items"]} == {"Kế toán DEGO", "Ban giám đốc"} and all_["can_view_all"]
    assert client.get("/api/agent-hub/groups").json()["data"]["items"] == []          # «của tôi» vẫn là của tôi
    msgs = client.get(f"/api/agent-hub/groups/{other.id}/messages").json()["data"]
    assert msgs["items"][0]["text"] == "lương tháng 10" and msgs["items"][0]["from_name"] == "Sếp"
    #  Giờ trả cho web là UTC trần, giao diện tự đổi sang giờ VN — đổi ở máy chủ là lệch 7 tiếng hai lần (08/10: tin
    #  16:37 hiện 23:37).
    from app.modules.agent_hub.model import AgentGroupMessage
    stored = db.query(AgentGroupMessage).filter_by(group_id=other.id).one().sent_at
    assert msgs["items"][0]["sent_at"] == stored.isoformat()
    log = db.query(AgentGroupView).all()
    assert [(v.group_id, v.user_id, v.what) for v in log] == [(other.id, seed.u_nstm_id, "tin nhắn")]
    views = client.get(f"/api/agent-hub/groups/{other.id}/views").json()["data"]["items"]
    assert views[0]["what"] == "tin nhắn"
    #  Lọc theo kênh / loại.
    assert client.get("/api/agent-hub/groups?scope=all&channel=telegram").json()["data"]["items"] == []
    assert client.get(f"/api/agent-hub/groups/{kt.id}").json()["data"]["title"] == "Kế toán DEGO"


def test_phan_loai_ngung_ghi_va_quyen_sua(db, seed, web, cap_quyen):
    client, who = web
    _link(db, seed.u_req_id, "zu:u1")
    _link(db, seed.u_nstm_id, "zu:u2")
    g = _zalo_group(db, "g1", "Dự án kho lạnh", ["u1", "u2"], owner=seed.u_req_id)
    meta = client.get("/api/agent-hub/groups/meta").json()["data"]
    assert {"value": 2, "label": "Dự án"} in meta["categories"] and meta["retention_days"] == 90
    #  Chủ nhóm tự phân loại được; không ngừng ghi được.
    assert client.patch(f"/api/agent-hub/groups/{g.id}", json={"category": 2}).status_code == 200
    assert client.patch(f"/api/agent-hub/groups/{g.id}", json={"paused": True}).status_code == 403
    assert client.patch(f"/api/agent-hub/groups/{g.id}", json={"category": 77}).status_code == 422
    assert client.get("/api/agent-hub/groups?category=2").json()["data"]["items"][0]["category_label"] == "Dự án"
    #  Thành viên thường (không phải chủ) không phân loại được.
    who["id"] = seed.u_nstm_id
    assert client.patch(f"/api/agent-hub/groups/{g.id}", json={"category": 1}).status_code == 403
    #  Quản lý bot AI (write) ngừng ghi → tin mới không vào kho.
    cap_quyen(seed.u_nstm_id, "agent_group", read=True, write=True)
    assert client.patch(f"/api/agent-hub/groups/{g.id}", json={"paused": True}).json()["data"]["paused"] is True
    _say(db, "g1", "tin sau khi tắt", mid="z")
    assert client.get(f"/api/agent-hub/groups/{g.id}/messages").json()["data"]["items"] == []


def test_ban_tom_tat_luu_tu_cau_tra_loi_va_nut_tom_tat(db, seed, web, monkeypatch):
    from app.modules.agent_hub import groups
    from app.modules.assistant import service as assistant_service
    from app.modules.user.model import User

    client, _ = web
    _link(db, seed.u_req_id, "zu:u1")
    g = _zalo_group(db, "g1", "Kế toán DEGO", ["u1"])
    _say(db, "g1", "chốt thanh toán NCC Hòa Phát thứ 6", mid="a")
    #  Câu trả lời của bot / Trợ lý web có gọi công cụ đọc nhóm → lưu làm bản tóm tắt.
    owner = db.get(User, seed.u_req_id)
    n = groups.record_answers(db, owner, "nhóm kế toán hôm nay bàn gì",
                              [{"name": "read_group_messages", "args": {"group": "kế toán", "hours": 24}},
                               {"name": "search_po", "args": {}}], "Nhóm chốt thanh toán Hòa Phát thứ 6.")
    db.commit()
    assert n == 1
    #  Nút «Tóm tắt» trên web: model đọc đúng tin của nhóm, kết quả được lưu.
    seen: list[str] = []
    monkeypatch.setattr(assistant_service, "ask", lambda prompt, **kw: seen.append(prompt) or {"text": "- Chốt Hòa Phát"})
    out = client.post(f"/api/agent-hub/groups/{g.id}/summarize", json={"hours": 48}).json()["data"]
    assert out["text"] == "- Chốt Hòa Phát" and "Hòa Phát thứ 6" in seen[0] and "Kế toán DEGO" in seen[0]
    items = client.get(f"/api/agent-hub/groups/{g.id}/summaries").json()["data"]["items"]
    assert [i["source"] for i in items] == [2, 1] and items[1]["question"] == "nhóm kế toán hôm nay bàn gì"
    assert items[0]["hours"] == 48


def test_tai_tep_nhom_va_trang_thai_zalo_chi_nguoi_quan_ly(db, seed, web, cap_quyen, monkeypatch):
    from app.modules.agent_hub import telegram, zalo_account as za

    client, who = web
    _link(db, seed.u_req_id, "zu:u1")
    g = _zalo_group(db, "g1", "Kế toán DEGO", ["u1"])
    _say(db, "g1", "", mid="f", href="https://f21-zpc.zdn.vn/x", title="bao-cao.xlsx")
    files = client.get(f"/api/agent-hub/groups/{g.id}/messages?files_only=true").json()["data"]["items"]
    assert files[0]["file"]["name"] == "bao-cao.xlsx"
    monkeypatch.setattr(telegram, "download_file", lambda fid, *, max_bytes: (b"PKdata", "x"))
    r = client.get(f"/api/agent-hub/groups/{g.id}/files/{files[0]['id']}")
    assert r.status_code == 200 and r.content == b"PKdata" and "bao-cao.xlsx" in r.headers["content-disposition"]
    #  Zalo công ty: người thường không xem được; người quản lý đọc thấy trạng thái, chỉ người có write thấy ảnh QR.
    monkeypatch.setattr(settings, "AGENT_ZALO_LISTENER_URL", "http://zalo-listener:3100")
    monkeypatch.setattr(za, "status", lambda: {"ok": True, "state": "qr", "qr_image": "QRBASE64", "name": ""})
    assert client.get("/api/agent-hub/zalo/status").status_code == 403
    who["id"] = seed.u_nstm_id
    cap_quyen(seed.u_nstm_id, "agent_group", read=True)
    st = client.get("/api/agent-hub/zalo/status").json()["data"]
    assert st["state"] == "qr" and st["qr_image"] == ""
    assert client.post("/api/agent-hub/zalo/login").status_code == 403
    cap_quyen(seed.u_nstm_id, "agent_group", read=True, write=True)
    assert client.get("/api/agent-hub/zalo/status").json()["data"]["qr_image"] == "QRBASE64"
    asked: list[int] = []
    monkeypatch.setattr(za, "request_login", lambda: asked.append(1) or {"ok": True})
    assert client.post("/api/agent-hub/zalo/login").status_code == 200 and asked == [1]
