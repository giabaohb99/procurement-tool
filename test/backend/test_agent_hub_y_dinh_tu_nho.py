"""ai-CR-137 — phase 13 đợt A «Hiểu ý định + tự ghi nhớ»: sổ ý định (không nguyên văn câu hỏi), nhãn con tất định theo
công cụ, tự rút ghi nhớ chỉ khi nhắc lại ≥ 3 lần trên ≥ 2 ngày, không đọc nhóm, không ghi bí mật, «quên» thành bia mộ."""
import json
from datetime import datetime, timedelta

import pytest

from app.modules.agent_hub import auto_memory as am
from app.modules.agent_hub import intent_ledger as il
from app.modules.agent_hub import personal_memory as pm
from app.modules.assistant.provider.base import ChatResult

SECRET_PHRASE = "câu hỏi riêng tư tháng mười của chị Mai"


@pytest.fixture(autouse=True)
def _clean():
    pm.clear_cache()
    yield
    pm.clear_cache()


def _result(text: str) -> ChatResult:
    return ChatResult(text=text, provider="gemini", model="gemini-flash-latest", input_tokens=50, output_tokens=20)


# ---------------------------------------------------------------------------
# 13.1 — sổ ý định
# ---------------------------------------------------------------------------
def test_so_y_dinh_khong_luu_nguyen_van_cau_hoi(db):
    from app.modules.agent_hub.model import AgentIntent

    calls = [{"name": "payable_lookup", "args": {"supplier": "Hòa Phát", "company": "DEGO", "query": SECRET_PHRASE},
              "rows": 3},
             {"name": "procurement_doc_read", "args": {"entity": "purchase_order", "code": "po00045"}, "rows": 1}]
    row = il.record(db, user_id=7, channel=il.Channel.TELEGRAM, scope_key="555", intent="hoi", tool_calls=calls,
                    question=f"{SECRET_PHRASE}, đối chiếu YCTT00012 giúp em", answer="Còn nợ 12 triệu.")
    assert row is not None
    stored = db.query(AgentIntent).one()
    dump = json.dumps({c.name: getattr(stored, c.key) for c in AgentIntent.__table__.columns}, default=str,
                      ensure_ascii=False)
    assert SECRET_PHRASE not in dump and "đối chiếu" not in dump and "12 triệu" not in dump
    assert stored.sub_intent == il.Sub.LOOKUP_PAYABLE and stored.outcome == il.Outcome.OK
    assert stored.tools == ["payable_lookup", "procurement_doc_read"]
    #  Đối tượng: mã chuẩn hóa in hoa, `entity` (loại chứng từ) KHÔNG bị hiểu nhầm thành pháp nhân.
    assert {"type": "ncc", "ref": "Hòa Phát"} in stored.entities
    assert {"type": "phap_nhan", "ref": "DEGO"} in stored.entities
    assert {"type": "chung_tu", "code": "PO00045"} in stored.entities
    assert {"type": "chung_tu", "code": "YCTT00012"} in stored.entities
    assert not any(e.get("ref") == "purchase_order" for e in stored.entities)


def test_so_y_dinh_bo_qua_nhom_va_nguoi_chua_dang_nhap(db):
    from app.modules.agent_hub.model import AgentIntent

    assert il.record(db, user_id=0, channel=il.Channel.TELEGRAM, scope_key="555", intent="hoi") is None
    assert il.record(db, user_id=7, channel=il.Channel.TELEGRAM, scope_key="-100123", intent="hoi") is None
    assert il.record(db, user_id=7, channel=il.Channel.ZALO, scope_key="zg:998", intent="hoi") is None
    assert db.query(AgentIntent).count() == 0


def test_ket_cuc_hoi_lai_va_loi(db):
    assert il.outcome_of("Anh muốn xem công nợ của pháp nhân nào?") == il.Outcome.CLARIFY
    #  Có gọi công cụ thì câu kết bằng dấu hỏi là lời mời («cần em xuất Excel không?»), không phải hỏi lại.
    assert il.outcome_of("Còn nợ 12 triệu. Anh cần xuất Excel không?", tools=["payable_lookup"]) == il.Outcome.OK
    assert il.outcome_of("", error=True) == il.Outcome.ERROR
    assert il.outcome_of("Dạ được ạ.") == il.Outcome.OK


def test_so_y_dinh_don_sau_180_ngay(db):
    from app.modules.agent_hub.model import AgentIntent

    old = il.record(db, user_id=7, channel=il.Channel.WEB, scope=1, scope_key="3", intent="hoi")
    il.record(db, user_id=7, channel=il.Channel.WEB, scope=1, scope_key="3", intent="hoi")
    old.created_at = datetime.utcnow() - timedelta(days=il.RETENTION_DAYS + 1)
    db.commit()
    assert il.purge(db) == 1 and db.query(AgentIntent).count() == 1


def test_bot_tra_loi_xong_thi_ghi_mot_dong_so(db, monkeypatch):
    from app.core.config import settings
    from app.modules.agent_hub import service
    from app.modules.agent_hub.model import AgentIntent
    from app.modules.assistant import service as assistant_service
    from app.modules.user.model import User

    monkeypatch.setattr(settings, "AGENT_ASSISTANT_USER", "BOT01")
    monkeypatch.setattr(settings, "AGENT_TELEGRAM_CHAT_ID", "12345")
    u = User(email="BOT01", employee_id=0, password_hash="x", is_active=True)
    db.add(u)
    db.commit()
    monkeypatch.setattr(service.telegram, "send", lambda text, **kw: 1)
    monkeypatch.setattr(service.telegram, "send_chat_action", lambda *a, **kw: None)
    monkeypatch.setattr(service.user_keys, "active_key", lambda: "k")
    monkeypatch.setattr(assistant_service, "ask", lambda message, **kw: {
        "text": "Đã soạn nháp", "tool_calls": [{"name": "supplier_search", "args": {"query": SECRET_PHRASE}},
                                               {"name": "draft_purchase_request", "args": {"company": "DEGO"}}]})
    service.answer_question(db, "12345", SECRET_PHRASE, intent="hoi")
    row = db.query(AgentIntent).one()
    assert row.user_id == u.id and row.channel == il.Channel.TELEGRAM and row.scope_key == "12345"
    #  Công cụ ghi (soạn nháp YCMH) thắng công cụ đọc gọi trước nó.
    assert il.sub_code(row.sub_intent) == "thao_tac.tao_ycmh"
    assert SECRET_PHRASE not in json.dumps(row.entities, ensure_ascii=False)


# ---------------------------------------------------------------------------
# 13.2 — nhãn con tất định theo công cụ (bộ mẫu cố định: đổi luật mà tụt là đỏ)
# ---------------------------------------------------------------------------
SAMPLES = [
    ("hoi", [], "", "hoi.chung"),
    ("mo_ho", [], "", "hoi.chung"),
    ("hoi", ["payable_lookup"], "", "tra_cuu.cong_no"),
    ("hoi", ["payment_request_read"], "", "tra_cuu.cong_no"),
    ("hoi", ["recent_purchase_orders", "supplier_search"], "", "tra_cuu.mua_hang"),
    ("hoi", ["product_best_price"], "", "tra_cuu.san_pham"),
    ("hoi", ["customs_price_stats"], "", "tra_cuu.hai_quan"),
    ("hoi", ["my_approval_tasks"], "", "tra_cuu.duyet"),
    ("hoi", ["supplier_contracts"], "", "tra_cuu.hop_dong"),
    ("hoi", ["read_group_messages"], "", "tra_cuu.nhom"),
    ("hoi", ["search_notes"], "", "tra_cuu.ca_nhan"),
    ("hoi", ["payable_lookup", "draft_payment_request"], "", "thao_tac.tao_yctt"),
    ("hoi", ["product_search", "draft_survey_request"], "", "thao_tac.tao_ycbg"),
    ("hoi", ["draft_leave_request"], "", "thao_tac.tao_nghi_phep"),
    ("hoi", ["create_calendar_event"], "", "thao_tac.lich"),
    ("hoi", ["remember_fact"], "", "thao_tac.ghi_nho"),
    ("hoi", ["export_excel_file"], "", "thao_tac.xuat_file"),
    ("hoi", ["tool_moi_chua_khai"], "", "tra_cuu.khac"),
    ("tra_cuu", [], "web", "nghien_cuu.web"),
    ("tra_cuu", [], "doc_link", "nghien_cuu.link"),
    ("tra_cuu", [], "doc", "nghien_cuu.tai_lieu"),
    ("viec", [], "", "viec.ghi"),
    ("thao_tac", [], "", "thao_tac.viec_bot"),
    ("du_lieu", [], "", "du_lieu.sua"),
]


@pytest.mark.parametrize("intent,tools,mode,expected", SAMPLES)
def test_nhan_con_suy_tu_cong_cu(intent, tools, mode, expected):
    assert il.sub_code(il.sub_of(il.intent_of(intent), tools, mode)) == expected


def test_moi_cong_cu_deu_co_nhan_con():
    """Thêm công cụ mới cho Trợ lý mà quên khai nhãn con thì sổ ý định gom nó vào «tra_cuu.khac» — chặn ở đây."""
    from app.modules.assistant.tools import _active_specs
    from app.modules.assistant.tools.rag_tool import SEARCH_DOCS_SPEC

    names = {s.name for s in _active_specs()} | {SEARCH_DOCS_SPEC.name}
    missing = sorted(n for n in names if n not in il.TOOL_SUB)
    assert not missing, f"công cụ chưa có nhãn con ở intent_ledger.TOOL_SUB: {missing}"
    assert set(il.SUB_CODES) == set(il.Sub)
    codes = [c for c, _ in il.SUB_CODES.values()]
    assert len(codes) == len(set(codes))


# ---------------------------------------------------------------------------
# 13.3 — tự rút ghi nhớ
# ---------------------------------------------------------------------------
#  Mốc theo ngày CHẠY bài (03:00 UTC = 10:00 giờ VN): dòng ghi vào lõi có hạn tính từ đây, so với hôm nay thật.
DAY1 = datetime.utcnow().replace(hour=3, minute=0, second=0, microsecond=0)
DAY2 = DAY1 + timedelta(days=1)


def _fact(text: str, section: str = "cach_lam_viec") -> list[dict]:
    return [{"section": section, "fact": text}]


def test_chi_ghi_khi_nhac_lai_3_lan_tren_2_ngay(db):
    fact = "Hay hỏi công nợ của pháp nhân DEGO"
    assert am.observe(db, 7, _fact(fact), now=DAY1)["written"] == []
    assert am.observe(db, 7, _fact(fact), now=DAY1 + timedelta(hours=2))["written"] == []
    #  Ba lần nhưng cùng MỘT ngày: chưa đủ.
    assert am.observe(db, 7, _fact(fact), now=DAY1 + timedelta(hours=4))["written"] == []
    assert pm.load_core(db, 7) == ""
    out = am.observe(db, 7, _fact(fact), now=DAY2)
    assert out["written"] == [fact]
    core = pm.load_core(db, 7)
    assert f"{fact} (tự rút)" in core and "(đến " in core and "## Cách làm việc" in core
    #  Gặp lại sau khi đã ghi: không ghi đôi.
    assert am.observe(db, 7, _fact(fact), now=DAY2 + timedelta(hours=1))["written"] == []
    assert pm.load_core(db, 7).count(fact) == 1


def test_noi_mot_lan_khong_bao_gio_vao_so(db):
    from app.modules.agent_hub.model import AgentMemoryCandidate

    am.observe(db, 7, _fact("Thích nhận báo cáo bằng Excel", "so_thich"), now=DAY1)
    assert pm.load_core(db, 7) == ""
    cand = db.query(AgentMemoryCandidate).one()
    assert cand.status == am.CandidateStatus.PENDING and cand.hits == 1 and cand.confidence < 1
    #  Quá hạn chờ mà không gặp lại → hết hạn.
    assert am.expire(db, now=DAY1 + timedelta(days=am.PENDING_TTL_DAYS + 1)) == 1
    db.refresh(cand)
    assert cand.status == am.CandidateStatus.EXPIRED


def test_khong_ghi_bi_mat(db):
    from app.modules.agent_hub.model import AgentMemoryCandidate

    for now in (DAY1, DAY1 + timedelta(hours=1), DAY2):
        am.observe(db, 7, _fact("Mật khẩu wifi phòng họp là degO2026"), now=now)
        am.observe(db, 7, _fact("Số tài khoản nhận lương 0123456789012"), now=now)
    assert db.query(AgentMemoryCandidate).count() == 0 and pm.load_core(db, 7) == ""


def test_nguoi_a_khong_dung_duoc_diem_cua_nguoi_b(db):
    from app.modules.agent_hub.model import AgentMemoryCandidate

    am.observe(db, 8, _fact("Phụ trách mua hàng nhà máy Hậu Giang", "ban_than"), now=DAY1)
    b = db.query(AgentMemoryCandidate).one()
    #  Model (hay kẻ chèn lệnh) trả số thứ tự điều của người B trong lượt rút của người A → bỏ.
    for now in (DAY1, DAY1 + timedelta(hours=1), DAY2, DAY2 + timedelta(hours=1)):
        am.observe(db, 7, [{"id": b.id}], now=now)
    db.refresh(b)
    assert b.hits == 1 and b.user_id == 8
    assert pm.load_core(db, 7) == "" and pm.load_core(db, 8) == ""
    assert am.active(db, 7) == [] and [c.id for c in am.active(db, 8)] == [b.id]


def test_quen_thi_xoa_khoi_so_va_khong_rut_lai_ngay(db):
    from app.modules.agent_hub.model import AgentMemoryCandidate

    fact = "Muốn trả lời ngắn gọn, không chào hỏi"
    for now in (DAY1, DAY1 + timedelta(hours=1), DAY2):
        am.observe(db, 7, _fact(fact), now=now)
    assert fact in pm.load_core(db, 7)
    removed = pm.forget(db, 7, "ngắn gọn")
    db.commit()
    assert removed and fact not in pm.load_core(db, 7)
    cand = db.query(AgentMemoryCandidate).one()
    assert cand.status == am.CandidateStatus.FORGOTTEN
    #  Buổi sau model lại đề xuất đúng điều đó → không đếm, không ghi lại.
    later = DAY2 + timedelta(days=3)
    for now in (later, later + timedelta(hours=1), later + timedelta(days=1)):
        assert am.observe(db, 7, _fact(fact), now=now)["written"] == []
    assert fact not in pm.load_core(db, 7)
    #  Hết thời gian bia mộ → đếm lại TỪ ĐẦU, một lần chưa đủ.
    after = DAY2 + timedelta(days=am.TOMBSTONE_DAYS + 1)
    assert am.observe(db, 7, _fact(fact), now=after)["written"] == []
    db.refresh(cand)
    assert cand.status == am.CandidateStatus.PENDING and cand.hits == 1


def test_quen_dieu_dang_dem_cung_thanh_bia_mo(db):
    from app.modules.agent_hub.model import AgentMemoryCandidate

    am.observe(db, 7, _fact("Hay đặt xe đi Hậu Giang thứ hai"), now=DAY1)
    assert pm.forget(db, 7, "hậu giang") == []           # lõi chưa có dòng nào
    db.commit()
    assert db.query(AgentMemoryCandidate).one().status == am.CandidateStatus.FORGOTTEN


def test_dieu_nguoi_dung_tu_ghi_roi_thi_khong_rut_doi(db):
    from app.modules.agent_hub.model import AgentMemoryCandidate

    pm.remember(db, 7, "Làm ở phòng Thu mua", "ban_than")
    db.commit()
    for now in (DAY1, DAY1 + timedelta(hours=1), DAY2):
        am.observe(db, 7, _fact("Làm ở phòng Thu mua", "ban_than"), now=now)
    assert db.query(AgentMemoryCandidate).count() == 0
    assert pm.load_core(db, 7).count("Thu mua") == 1


def _linked_chat(db, user_id: int, chat_id: str):
    from app.modules.agent_hub.model import AgentChatLink

    db.add(AgentChatLink(user_id=user_id, chat_id=chat_id, linked_at=datetime.now(),
                         expires_at=datetime.now() + timedelta(days=30), created_by=0, updated_by=0))
    db.commit()


def test_rut_sau_buoi_chat_bao_mot_lan_va_khong_dung_tin_nhom(db, monkeypatch):
    from app.modules.agent_hub import manager, service, sessions
    from app.modules.agent_hub.constants import DIR_IN, DIR_OUT
    from app.modules.agent_hub.model import AgentCursor

    monkeypatch.setattr(am, "enabled", lambda: True)
    monkeypatch.setattr(service.user_keys, "active_key", lambda: "k")
    sent: list[tuple[str, str]] = []
    monkeypatch.setattr(service, "reply", lambda db, chat_id, text, **kw: sent.append((chat_id, text)))
    prompts: list[str] = []
    facts = ["Hay hỏi công nợ pháp nhân DEGO"]

    class P:
        def ask(self, messages, **kw):
            prompts.append(messages[0].content)
            return _result(json.dumps({"facts": [{"section": "cach_lam_viec", "fact": facts[0]}]}, ensure_ascii=False))

    monkeypatch.setattr(manager, "get_provider", lambda: P())
    #  Nhóm: không bao giờ rút, không tốn lượt model.
    assert am.extract(db, "-100777", 7, "- hỏi công nợ")["ok"] is False
    assert am.extract(db, "zg:42", 7, "- hỏi công nợ")["ok"] is False
    _linked_chat(db, 7, "-100777")
    for i, (d, a, body) in enumerate([(DIR_IN, "hoi", "a"), (DIR_OUT, "tra_loi", "b")] * 3):
        service.log_message(db, d, "-100777", 300 + i, body, action=a)
    db.commit()
    assert sessions.tick(db, now=sessions.now_utc() + timedelta(hours=2)) == {"summarized": 0, "skipped": 0}
    assert prompts == []
    #  Chat riêng: ba buổi trên hai ngày → ghi, báo đúng MỘT lần.
    for now in (DAY1, DAY1 + timedelta(hours=3), DAY2):
        am.extract(db, "555", 7, "- Hỏi công nợ DEGO tháng 9", now=now)
    assert len(prompts) == 3 and "BẢN TÓM TẮT BUỔI" in prompts[0]
    assert "Hay hỏi công nợ pháp nhân DEGO (tự rút)" in pm.load_core(db, 7)
    assert len(sent) == 1 and sent[0][0] == "555" and "tự rút" in sent[0][1]
    assert db.query(AgentCursor).filter_by(name=f"{am.NOTICE_CURSOR}7").one().value == 1
    #  Điều thứ hai được ghi sau đó: không báo lại.
    facts[0] = "Thích bảng hơn đoạn văn"
    for now in (DAY2 + timedelta(hours=1), DAY2 + timedelta(hours=2), DAY2 + timedelta(days=1)):
        am.extract(db, "555", 7, "- buổi khác", now=now)
    assert "Thích bảng hơn đoạn văn (tự rút)" in pm.load_core(db, 7)
    assert len(sent) == 1


def test_dau_vao_rut_co_dem_tu_so_y_dinh_va_dieu_dang_theo_doi(db):
    for _ in range(3):
        il.record(db, user_id=7, channel=il.Channel.TELEGRAM, scope_key="555", intent="hoi",
                  tool_calls=[{"name": "payable_lookup", "args": {"company": "DEGO"}}])
    am.observe(db, 7, _fact("Hay hỏi công nợ"), now=DAY1)
    prompt = am.build_prompt("- tóm tắt", il.habit_lines(db, 7), pm.load_core(db, 7), am.active(db, 7))
    assert "tra_cuu.cong_no: 3 lần" in prompt and "phap_nhan: DEGO" in prompt
    assert "ĐANG THEO DÕI" in prompt and "Hay hỏi công nợ" in prompt
    #  Model trả rác / sai dạng: không có gì được đếm.
    assert am.parse_facts("không phải JSON") == [] and am.parse_facts('{"facts": "x"}') == []
    assert am.parse_facts('```json\n{"facts": [{"id": 3}]}\n```') == [{"id": 3}]
