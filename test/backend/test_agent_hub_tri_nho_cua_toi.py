"""ai-CR-138 — phase 13 đợt B: màn «Bot đang nhớ gì về tôi» (chỉ chủ sổ), thu hồi xóa sạch, điền đối tượng theo thói
quen + nói rõ giả định, gợi ý chỉ là đề xuất, bộ đo độ đúng (bộ câu mẫu cố định, chấm nhãn tay, tỷ lệ hỏi lại)."""
import json
import os
from datetime import datetime, timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.auth import get_current_user
from app.core.database import get_db
from app.modules.agent_hub import auto_memory as am
from app.modules.agent_hub import intent_eval as ie
from app.modules.agent_hub import intent_ledger as il
from app.modules.agent_hub import personal_memory as pm

DAY1 = datetime.utcnow().replace(hour=3, minute=0, second=0, microsecond=0)


@pytest.fixture(autouse=True)
def _clean():
    pm.clear_cache()
    yield
    pm.clear_cache()


@pytest.fixture
def web(db, seed):
    from app.modules.agent_hub import controller
    from app.modules.user.model import User

    app = FastAPI()
    app.include_router(controller.router)
    who = {"id": seed.u_req_id}
    app.dependency_overrides[get_current_user] = lambda: db.get(User, who["id"])
    app.dependency_overrides[get_db] = lambda: db
    return TestClient(app), who


def _promote(db, uid: int, fact: str, section: str = "cach_lam_viec"):
    for now in (DAY1, DAY1 + timedelta(hours=1), DAY1 + timedelta(days=1)):
        am.observe(db, uid, [{"section": section, "fact": fact}], now=now)


# ---------------------------------------------------------------------------
# 13.4 — xem / sửa / xóa, chỉ chủ sổ
# ---------------------------------------------------------------------------
def test_chu_so_xem_sua_xoa_tung_dong(db, seed, web):
    client, _ = web
    uid = seed.u_req_id
    pm.remember(db, uid, "Làm ở phòng Thu mua", "ban_than")
    db.commit()
    _promote(db, uid, "Muốn trả lời ngắn gọn")
    am.observe(db, uid, [{"section": "so_thich", "fact": "Thích bảng hơn đoạn văn"}], now=DAY1)

    data = client.get("/api/agent-hub/me/memory").json()["data"]
    lines = {ln["fact"]: ln for s in data["sections"] for ln in s["lines"]}
    assert lines["Làm ở phòng Thu mua"]["auto"] is False
    auto = lines["Muốn trả lời ngắn gọn"]
    assert auto["auto"] is True and auto["until"]
    assert [w["fact"] for w in data["watching"]] == ["Thích bảng hơn đoạn văn"]

    #  Sửa dòng tự rút: thành dòng của người dùng (bỏ đuôi), điều gốc thành bia mộ — không rút chen lại câu cũ.
    r = client.patch("/api/agent-hub/me/memory/lines", json={"section": "cach_lam_viec", "old": auto["text"],
                                                              "text": "Trả lời ngắn, có số liệu"})
    assert r.status_code == 200
    core = pm.load_core(db, uid)
    assert "Trả lời ngắn, có số liệu" in core and "(tự rút)" not in core
    _promote(db, uid, "Muốn trả lời ngắn gọn")
    assert "Muốn trả lời ngắn gọn" not in pm.load_core(db, uid)

    #  Sửa bằng dòng cũ đã đổi ở tab khác → 409, không sửa nhầm dòng bên cạnh.
    r = client.patch("/api/agent-hub/me/memory/lines", json={"section": "cach_lam_viec", "old": auto["text"],
                                                              "text": "x"})
    assert r.status_code == 409
    #  Không ghi bí mật qua đường sửa.
    r = client.patch("/api/agent-hub/me/memory/lines", json={"section": "ban_than", "old": "Làm ở phòng Thu mua",
                                                              "text": "Mật khẩu email là abc"})
    assert r.status_code == 400 and "Thu mua" in pm.load_core(db, uid)

    r = client.post("/api/agent-hub/me/memory/lines/delete", json={"section": "ban_than", "old": "Làm ở phòng Thu mua"})
    assert r.status_code == 200 and "Thu mua" not in pm.load_core(db, uid)

    wid = data["watching"][0]["id"]
    assert client.delete(f"/api/agent-hub/me/memory/watching/{wid}").status_code == 200
    assert client.get("/api/agent-hub/me/memory").json()["data"]["watching"] == []

    r = client.post("/api/agent-hub/me/memory/lines", json={"section": "so_thich", "text": "Uống cà phê đen"})
    assert r.status_code == 200 and "Uống cà phê đen" in pm.load_core(db, uid)
    assert client.post("/api/agent-hub/me/memory/lines", json={"section": "khong_co", "text": "x"}).status_code == 400
    #  Trần độ dài ở tầng schema (MySQL không được là chỗ đầu tiên phản đối).
    assert client.post("/api/agent-hub/me/memory/lines",
                       json={"section": "so_thich", "text": "a" * 601}).status_code == 422


def test_nguoi_a_khong_doc_khong_xoa_duoc_tri_nho_nguoi_b(db, seed, web):
    client, who = web
    a, b = seed.u_req_id, seed.u_nstm_id
    pm.remember(db, b, "Phụ trách kho Hậu Giang", "ban_than")
    note = pm.add_note(db, b, "Ghi chú riêng của B", "nội dung bí mật của B")
    db.commit()
    am.observe(db, b, [{"section": "so_thich", "fact": "Thích đi sớm"}], now=DAY1)
    cand_b = am.active(db, b)[0].id

    who["id"] = a
    data = client.get("/api/agent-hub/me/memory").json()["data"]
    dump = json.dumps(data, ensure_ascii=False)
    assert "Hậu Giang" not in dump and "Ghi chú riêng của B" not in dump and "Thích đi sớm" not in dump
    #  Không có tham số nào chọn được người khác; id của B qua đường của A → 404, sổ B còn nguyên.
    assert client.get(f"/api/agent-hub/me/memory?user_id={b}").json()["data"]["sections"] == data["sections"]
    assert client.delete(f"/api/agent-hub/me/memory/watching/{cand_b}").status_code == 404
    assert client.delete(f"/api/agent-hub/me/memory/notes/{note['note_id']}").status_code == 404
    assert client.post("/api/agent-hub/me/memory/lines/delete",
                       json={"section": "ban_than", "old": "Phụ trách kho Hậu Giang"}).status_code == 409
    assert client.delete("/api/agent-hub/me/memory").status_code == 200        # A xóa sạch sổ CỦA A
    assert "Hậu Giang" in pm.load_core(db, b) and am.active(db, b)[0].id == cand_b
    assert [n.id for n in pm.list_notes(db, b)] == [note["note_id"]]


def test_thu_hoi_nhan_su_xoa_sach_tri_nho(db, seed, monkeypatch):
    from app.modules.agent_hub.model import AgentCursor, AgentIntent, AgentMemory, AgentMemoryCandidate, AgentNote
    from app.modules.agent_hub.service import revoke_user_access

    monkeypatch.setattr(pm, "_store", lambda: (_ for _ in ()).throw(RuntimeError("không có qdrant trong bài kiểm")))
    uid, other = seed.u_req_id, seed.u_nstm_id
    for u in (uid, other):
        pm.remember(db, u, "Ở Cần Thơ", "ban_than")
        pm.add_note(db, u, "Buổi 09/10", "- hỏi công nợ")
        il.record(db, user_id=u, channel=il.Channel.TELEGRAM, scope_key="555", intent="hoi")
        am.observe(db, u, [{"section": "so_thich", "fact": "Thích bảng"}], now=DAY1)
    db.add(AgentCursor(name=f"{am.NOTICE_CURSOR}{uid}", value=1))
    db.commit()
    revoke_user_access(db, uid)
    db.commit()
    pm.clear_cache()
    assert pm.load_core(db, uid) == "" and db.query(AgentMemory).filter_by(user_id=uid).count() == 0
    assert db.query(AgentNote).filter_by(user_id=uid, revoked_at=None).count() == 0
    assert db.query(AgentIntent).filter_by(user_id=uid).count() == 0
    assert db.query(AgentMemoryCandidate).filter_by(user_id=uid).count() == 0
    assert db.query(AgentCursor).filter_by(name=f"{am.NOTICE_CURSOR}{uid}").count() == 0
    #  Người khác không bị đụng.
    assert "Cần Thơ" in pm.load_core(db, other) and db.query(AgentIntent).filter_by(user_id=other).count() == 1


def test_lenh_chat_em_nho_gi_ve_anh_hien_ca_dieu_dang_de_y(db, seed, monkeypatch):
    from app.modules.agent_hub import service
    from app.modules.agent_hub.constants import DIR_IN
    from app.modules.agent_hub.model import AgentChatLink

    db.add(AgentChatLink(user_id=seed.u_req_id, chat_id="777", linked_at=datetime.now(),
                         expires_at=datetime.now() + timedelta(days=30), created_by=0, updated_by=0))
    db.commit()
    am.observe(db, seed.u_req_id, [{"section": "so_thich", "fact": "Thích bảng hơn đoạn văn"}], now=DAY1)
    sent: list[str] = []
    monkeypatch.setattr(service, "reply", lambda db, chat_id, text, **kw: sent.append(text))
    for text in ("em nhớ gì về chị", "bot nhớ gì về mình?"):
        row = service.log_message(db, DIR_IN, "777", 1, text)
        assert service._memory_by_text(db, "777", row, text) is True
    assert len(sent) == 2 and "Em đang để ý" in sent[0] and "Thích bảng hơn đoạn văn" in sent[0]
    assert "Bot nhớ gì về tôi" in sent[0]


# ---------------------------------------------------------------------------
# 13.5 — điền đối tượng theo thói quen, nói rõ giả định; gợi ý chỉ là đề xuất
# ---------------------------------------------------------------------------
def _ask(db, uid, company: str, when=None):
    row = il.record(db, user_id=uid, channel=il.Channel.TELEGRAM, scope_key="555", intent="hoi",
                    tool_calls=[{"name": "payable_lookup", "args": {"company": company}}])
    if when is not None:
        row.created_at = when
        db.commit()


def test_thoi_quen_chi_khi_du_lan_va_ap_dao(db):
    for _ in range(2):
        _ask(db, 7, "DEGO")
    assert il.habit_block(db, 7) == ""                       # 2 lần: chưa đủ
    _ask(db, 7, "DEGO")
    _ask(db, 7, "Hưng Phát")
    block = il.habit_block(db, 7)
    assert "pháp nhân hay hỏi: DEGO (3/4" in block and "nói rõ giả định" in block and "như mọi lần" in block
    #  Không áp đảo (3 / 6 = 50% < 60%): không đoán.
    for _ in range(2):
        _ask(db, 7, "Hưng Phát")
    assert il.habit_block(db, 7) == ""
    #  Thói quen là của TỪNG người.
    assert il.habit_block(db, 8) == "" and il.habit_block(db, 0) == ""


def test_bot_tra_loi_nap_thoi_quen_vao_phan_luat(db, monkeypatch):
    from app.core.config import settings
    from app.modules.agent_hub import service
    from app.modules.agent_hub.model import AgentChatLink
    from app.modules.assistant import service as assistant_service
    from app.modules.user.model import User

    u = User(email="u7@x", employee_id=0, password_hash="x", is_active=True)
    db.add(u)
    db.commit()
    db.add(AgentChatLink(user_id=u.id, chat_id="12399", linked_at=datetime.now(),
                         expires_at=datetime.now() + timedelta(days=30), created_by=0, updated_by=0))
    db.commit()
    for _ in range(3):
        _ask(db, u.id, "DEGO")
    monkeypatch.setattr(settings, "AGENT_TELEGRAM_CHAT_ID", "1")
    monkeypatch.setattr(service.telegram, "send", lambda text, **kw: 1)
    monkeypatch.setattr(service.telegram, "send_chat_action", lambda *a, **kw: None)
    monkeypatch.setattr(service.user_keys, "active_key", lambda: "k")
    seen: dict = {}
    monkeypatch.setattr(assistant_service, "ask",
                        lambda message, **kw: seen.update(kw) or {"text": "Em hiểu là pháp nhân DEGO như mọi lần…",
                                                                  "tool_calls": []})
    q = service.log_message(db, 1, "12399", 5, "công nợ tháng này")
    service.answer_question(db, "12399", "công nợ tháng này", before_id=q.id)
    assert "pháp nhân hay hỏi: DEGO" in seen["system"]
    last = db.query(il.AgentIntent).order_by(il.AgentIntent.id.desc()).first()
    assert last.message_id == q.id                       # con trỏ tin để gắn nhãn tay — không chép chữ


def test_goi_y_chu_dong_chi_la_de_xuat(db):
    monday = datetime(2026, 9, 7, 2, 0)                  # thứ hai, 09:00 giờ VN
    now = monday + timedelta(weeks=3, days=1)
    for w in range(3):
        _ask(db, 7, "DEGO", when=monday + timedelta(weeks=w))
    out = il.suggestions_of(db, 7, now=now)
    assert len(out) == 1 and out[0]["weekday"] == 0 and out[0]["sub"] == "tra_cuu.cong_no" and out[0]["weeks"] == 3
    assert "Thứ hai" in out[0]["text"]
    #  Hai tuần thôi thì chưa phải thói quen; người khác không thấy.
    assert il.suggestions_of(db, 8, now=now) == []
    db.query(il.AgentIntent).filter(il.AgentIntent.created_at < monday + timedelta(days=1)).delete()
    db.commit()
    assert il.suggestions_of(db, 7, now=now) == []


# ---------------------------------------------------------------------------
# 13.6 — đo
# ---------------------------------------------------------------------------
def test_bo_cau_mau_co_dinh_hop_le():
    data = ie.load_samples()
    labels = [s["intent"] for s in data["samples"]]
    for code in il.INTENT_CODES.values():
        assert labels.count(code) >= 4, f"nhãn {code} cần ít nhất 4 câu mẫu"
    assert 0.5 <= data["min_accuracy"] <= 1 and data["tasks"]
    assert len({s["text"] for s in data["samples"]}) == len(labels)


def test_cham_bo_mau_va_nhan_tay():
    data = ie.load_samples()
    perfect = ie.run_fixed(lambda text, ctx, tasks: next(s["intent"] for s in data["samples"] if s["text"] == text), data)
    assert perfect["accuracy"] == 1.0 and perfect["misses"] == []
    #  Bộ phân loại «trả hoi cho mọi câu» phải trượt ngưỡng — bài kiểm không được xanh giả.
    lazy = ie.run_fixed(lambda *a: "hoi", data)
    assert lazy["accuracy"] < data["min_accuracy"]
    rows = [{"intent": "hoi", "sub_intent": "tra_cuu.cong_no", "true_intent": "hoi", "true_sub": "tra_cuu.cong_no",
             "entities_ok": "1"},
            {"intent": "hoi", "sub_intent": "hoi.chung", "true_intent": "tra_cuu", "true_sub": "nghien_cuu.web",
             "entities_ok": "0"},
            {"intent": "viec", "sub_intent": "viec.ghi", "true_intent": "", "true_sub": "", "entities_ok": ""}]
    s = ie.score_rows(rows)
    assert s["intent"] == {"labelled": 2, "correct": 1, "accuracy": 0.5}
    assert s["sub"]["accuracy"] == 0.5 and s["entities"] == {"labelled": 2, "ok": 1}
    assert s["confusion"] == [("tra_cuu -> hoi", 1)]


def test_ty_le_hoi_lai_truoc_sau_moc(db):
    pivot = datetime(2026, 10, 10)
    for i, (days, answer) in enumerate([(-3, "Anh muốn xem pháp nhân nào?"), (-2, "Dạ đây ạ."),
                                        (2, "Dạ đây ạ."), (3, "Dạ đây ạ.")]):
        row = il.record(db, user_id=7, channel=il.Channel.TELEGRAM, scope_key="555", intent="hoi", answer=answer)
        row.created_at = pivot + timedelta(days=days)
    db.commit()
    out = ie.clarify_rates(db, pivot=pivot, days=14)
    assert out["truoc"]["telegram"] == {"total": 2, "clarify": 1, "rate": 0.5}
    assert out["sau"]["telegram"] == {"total": 2, "clarify": 0, "rate": 0.0}


def test_xuat_mau_gan_nhan_lay_chu_qua_con_tro_tin(db, tmp_path):
    from app.modules.agent_hub import service
    from app.modules.agent_hub.constants import DIR_IN

    q = service.log_message(db, DIR_IN, "555", 1, "công nợ DEGO tháng 9")
    db.commit()
    il.record(db, user_id=7, channel=il.Channel.TELEGRAM, scope_key="555", intent="hoi", message_id=q.id,
              tool_calls=[{"name": "payable_lookup", "args": {"company": "DEGO"}}])
    il.record(db, user_id=7, channel=il.Channel.TELEGRAM, scope_key="555", intent="hoi")   # không con trỏ → bỏ
    rows = ie.export_rows(db, days=30, limit=200)
    assert len(rows) == 1 and rows[0]["text"] == "công nợ DEGO tháng 9" and rows[0]["sub_intent"] == "tra_cuu.cong_no"
    path = tmp_path / "y.csv"
    ie.write_csv(rows, path)
    assert ie.read_csv(path)[0]["intent"] == "hoi"


@pytest.mark.skipif(os.environ.get("AI_EVAL") != "1", reason="chạy bộ mẫu qua model thật: đặt AI_EVAL=1 + khóa AI")
def test_bo_phan_loai_that_khong_tut_duoi_nguong(db):
    from app.modules.agent_hub import manager, user_keys

    with user_keys.for_admin(db):
        res = ie.run_fixed(lambda text, ctx, tasks: manager.run_intent(text, context=ctx, tasks=tasks)[0]["intent"])
    assert res["accuracy"] >= res["min_accuracy"], res["misses"]
