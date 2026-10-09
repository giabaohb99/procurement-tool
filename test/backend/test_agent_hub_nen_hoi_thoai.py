"""ai-CR-136 — phase 14 «Nén hội thoại»: bản tóm tắt theo TỪNG cuộc + ba mức (lược kết quả công cụ cũ · tóm nối tiếp · bỏ
lượt cũ nhất) theo ngân sách token cấu hình được; tóm hỏng thì quay về cửa sổ trượt, không chặn câu trả lời."""
import time
from datetime import datetime, timedelta

import pytest

from app.core.config import settings
from app.modules.assistant import compaction
from app.modules.assistant.provider.base import ChatResult


def _result(text: str) -> ChatResult:
    return ChatResult(text=text, provider="gemini", model="gemini-flash-latest", input_tokens=900, output_tokens=120)


@pytest.fixture
def small_budget(monkeypatch):
    """Ngân sách nhỏ để vài lượt đã chạm ngưỡng: 1.000 token → lược ở 500, tóm ở 700, bỏ ở 900; giữ 2 lượt gần nhất."""
    monkeypatch.setattr(settings, "AI_COMPACT_ENABLED", True)
    monkeypatch.setattr(settings, "AI_CONTEXT_BUDGET_TOKENS", 1000)
    monkeypatch.setattr(settings, "AI_COMPACT_KEEP_TURNS", 2)
    monkeypatch.setattr(settings, "AI_COMPACT_TIMEOUT_SEC", 5)


def _chat(db, chat_id: str, pairs: list[tuple[str, str]], *, tool_from: int = 99) -> list[int]:
    """Ghi các lượt hỏi-đáp vào sổ bot; trả id các tin. Câu trả lời từ cặp thứ `tool_from` trở đi là rút từ công cụ."""
    from app.modules.agent_hub.constants import ACT_ANSWER, ACT_ASKED, DIR_IN, DIR_OUT
    from app.modules.agent_hub.model import AgentMessage

    ids = []
    for i, (q, a) in enumerate(pairs):
        for direction, body, action in ((DIR_IN, q, ACT_ASKED), (DIR_OUT, a, ACT_ANSWER)):
            row = AgentMessage(chat_id=chat_id, direction=direction, body=body, action=action,
                               tool_used=direction == DIR_OUT and i >= tool_from, created_by=0, updated_by=0)
            db.add(row)
            db.flush()
            ids.append(row.id)
    db.commit()
    return ids


def _long_pairs(n: int, chot_at: int = 2) -> list[tuple[str, str]]:
    out = []
    for i in range(n):
        q = f"Lượt {i + 1}: hỏi tiếp về đơn mua hàng " + "chi tiết " * 40
        if i == chot_at:
            q = "Chốt: dùng NCC Hòa Phát cho ĐMH-0012, giao trước 20/10. " + "ghi chú " * 40
        out.append((q, f"Trả lời lượt {i + 1}: " + "số liệu " * 60))
    return out


def test_hoi_thoai_dai_van_giu_dieu_chot_o_luot_3_nho_ban_tom_tat(db, small_budget, monkeypatch):
    from app.modules.agent_hub import manager, service
    from app.modules.agent_hub.constants import STAGE_COMPACT
    from app.modules.agent_hub.model import AgentConvSummary, AgentRun

    ids = _chat(db, "555", _long_pairs(8))
    prompts: list[str] = []

    class P:
        def ask(self, messages, **kw):
            prompts.append(messages[0].content)
            assert "Hòa Phát" in messages[0].content          # điều chốt ở lượt 3 có trong phần đem đi tóm
            return _result("- Đã chốt: NCC Hòa Phát cho ĐMH-0012, giao trước 20/10.")

    monkeypatch.setattr(manager, "get_provider", lambda: P())
    plan = service._compacted_turns(db, "555", 0, "Vậy giao hàng ngày nào?", 7)
    assert plan.level >= compaction.LEVEL_SUMMARY and "Hòa Phát" in plan.summary
    assert "Hòa Phát" in compaction.summary_block(plan.summary)
    assert len(plan.turns) <= 4 and plan.turns[0]["role"] == "user"
    assert not any("Hòa Phát" in t["content"] for t in plan.turns)   # lượt 3 đã nằm trong bản tóm tắt, không gửi lại
    row = db.query(AgentConvSummary).one()
    assert row.scope == 2 and row.scope_key == "555" and ids[0] < row.upto_id < ids[-1]
    #  Token của lượt tóm vào sổ chi phí như mọi lượt.
    run = db.query(AgentRun).filter_by(stage=STAGE_COMPACT).one()
    assert run.input_tokens == 900 and run.artifact["channel"] == "telegram"


def test_luoc_ket_qua_cong_cu_cu_chi_giu_cac_luot_gan_nhat(db, small_budget):
    turns = []
    for i in range(4):
        turns.append(compaction.Turn("user", f"hỏi {i}", i * 2 + 1))
        turns.append(compaction.Turn("assistant", f"BẢNG {i} " + "dòng dữ liệu " * 32, i * 2 + 2, tool=True))
    plan = compaction.compact(db, scope=1, key="77", user_id=1, turns=turns, question="tiếp",
                              summarize=lambda s, p: pytest.fail("chưa tới ngưỡng tóm"), fallback=lambda: [])
    assert plan.level == compaction.LEVEL_CLEAR
    old = [t["content"] for t in plan.turns[:4]]
    recent = [t["content"] for t in plan.turns[4:]]
    assert all(c.startswith("[Kết quả tra cứu cũ đã lược") for c in old if "BẢNG" in c)
    assert sum("dòng dữ liệu dòng dữ liệu" in c for c in recent) == 2       # 2 lượt gần nhất giữ nguyên kết quả


def test_tom_tat_loi_hoac_qua_gio_thi_van_tra_loi_bang_cua_so_truot(db, small_budget, monkeypatch):
    from app.modules.agent_hub.model import AgentConvSummary

    turns = [compaction.Turn("user" if i % 2 == 0 else "assistant", "nội dung " * 60, i + 1) for i in range(10)]
    window = [{"role": "user", "content": "cửa sổ cũ"}]

    def boom(system, prompt):
        raise RuntimeError("Gemini 503")

    plan = compaction.compact(db, scope=2, key="9", user_id=1, turns=turns, question="?", summarize=boom,
                              fallback=lambda: window)
    assert plan.level == compaction.LEVEL_FALLBACK and plan.turns == window
    monkeypatch.setattr(settings, "AI_COMPACT_TIMEOUT_SEC", 1)
    t0 = time.monotonic()
    plan = compaction.compact(db, scope=2, key="9", user_id=1, turns=turns, question="?",
                              summarize=lambda s, p: time.sleep(3) or _result("muộn"), fallback=lambda: window)
    assert plan.turns == window and time.monotonic() - t0 < 2.5            # không chờ lượt tóm quá giờ
    assert db.query(AgentConvSummary).count() == 0


def test_khong_lo_tom_tat_giua_hai_nguoi_hay_hai_hoi_thoai(db, small_budget, monkeypatch):
    from app.modules.agent_hub import manager, service

    class P:
        def ask(self, messages, **kw):
            return _result("- Bí mật của người A: lương tháng 10")

    monkeypatch.setattr(manager, "get_provider", lambda: P())
    _chat(db, "111", _long_pairs(8))
    a = service._compacted_turns(db, "111", 0, "?", 1)
    assert "người A" in a.summary
    _chat(db, "222", [("chào", "chào anh")])
    b = service._compacted_turns(db, "222", 0, "?", 2)
    assert b.summary == "" and "người A" not in str(b.turns)
    #  Web: hai hội thoại khác nhau của cùng một người cũng tách hẳn.
    compaction.save(db, scope=1, key="10", user_id=1, summary="tóm tắt hội thoại 10", upto_id=5, folded=4)
    assert compaction.load(db, 1, "11") is None and compaction.load(db, 2, "10") is None


def test_tom_noi_tiep_khong_tom_lai_phan_da_tom(db, small_budget, monkeypatch):
    from app.modules.agent_hub import manager, service
    from app.modules.agent_hub.model import AgentConvSummary

    prompts: list[str] = []

    class P:
        def ask(self, messages, **kw):
            prompts.append(messages[0].content)
            return _result(f"- tóm lần {len(prompts)}")

    monkeypatch.setattr(manager, "get_provider", lambda: P())
    first = _long_pairs(8)
    _chat(db, "333", first)
    service._compacted_turns(db, "333", 0, "?", 3)
    upto1 = db.query(AgentConvSummary).one().upto_id
    assert "TÓM TẮT CŨ" not in prompts[0]
    second = [(f"Đợt hai câu {i}: " + "mới " * 50, "đáp " * 60) for i in range(6)]
    _chat(db, "333", second)
    service._compacted_turns(db, "333", 0, "?", 3)
    assert len(prompts) == 2
    assert "TÓM TẮT CŨ:\n- tóm lần 1" in prompts[1]
    assert "Lượt 1:" not in prompts[1] and "Hòa Phát" not in prompts[1]     # phần đã tóm không đem tóm lại
    assert db.query(AgentConvSummary).one().upto_id > upto1


def test_cuoc_chat_moi_sau_qua_lau_thi_bo_tom_tat_cu(db, small_budget, monkeypatch):
    from app.modules.agent_hub import service
    from app.modules.agent_hub.constants import ACT_ASKED, DIR_IN
    from app.modules.agent_hub.model import AgentConvSummary, AgentMessage

    compaction.save(db, scope=2, key="444", user_id=1, summary="- chuyện tuần trước", upto_id=0, folded=6)
    row = db.query(AgentConvSummary).one()
    row.updated_at = datetime.now() - timedelta(hours=settings.AI_COMPACT_SESSION_HOURS + 5)
    q = AgentMessage(chat_id="444", direction=DIR_IN, body="hôm nay hỏi chuyện khác", action=ACT_ASKED,
                     created_by=0, updated_by=0)
    db.add(q)
    db.commit()
    plan = service._compacted_turns(db, "444", q.id, q.body, 1)
    assert plan.summary == "" and db.query(AgentConvSummary).count() == 0


def test_web_hoi_thoai_dai_gui_ban_tom_tat_vao_phan_luat(db, seed, small_budget, monkeypatch):
    """Web: hội thoại cũ đi qua nén; bản tóm tắt vào `system`, câu trả lời rút từ công cụ được đánh dấu."""
    from types import SimpleNamespace

    from app.modules.assistant import conversation, service as assistant_service
    from app.modules.assistant.model import AssistantConversation, AssistantMessage, MessageRole
    from app.modules.user.model import User

    user = db.get(User, seed.u_req_id)
    conv = AssistantConversation(title="t", created_by=user.id, updated_by=user.id, last_message_at=datetime.now())
    db.add(conv)
    db.flush()
    for q, a in _long_pairs(8):
        db.add(AssistantMessage(conversation_id=conv.id, role=MessageRole.USER, content=q, created_by=user.id))
        db.add(AssistantMessage(conversation_id=conv.id, role=MessageRole.ASSISTANT, content=a, created_by=user.id))
    db.commit()

    class P:
        def ask(self, messages, **kw):
            return _result("- Đã chốt NCC Hòa Phát cho ĐMH-0012")

    monkeypatch.setattr("app.modules.assistant.provider.get_provider", lambda name=None: P())
    seen: dict = {}

    def fake_ask(message, **kw):
        seen.update(kw)
        return {"text": "ngày 20/10", "provider": "gemini", "model": "m", "tool_calls": [{"name": "search_po"}],
                "usage": {}}

    monkeypatch.setattr(assistant_service, "ask", fake_ask)
    body = SimpleNamespace(conversation_id=conv.id, attachment_ids=[], history=None, message="Giao ngày nào?",
                           provider=None, model=None, kind="general", system=None)
    conversation.chat(db, user, body)
    assert "Hòa Phát" in (seen["system"] or "") and len(seen["history"]) <= 4
    last = db.query(AssistantMessage).order_by(AssistantMessage.id.desc()).first()
    assert last.role == MessageRole.ASSISTANT and last.tool_used is True
    conversation.delete_conversation(db, user, conv.id)
    assert compaction.load(db, 1, str(conv.id)) is None                      # xóa hội thoại thì bỏ luôn bản tóm tắt
