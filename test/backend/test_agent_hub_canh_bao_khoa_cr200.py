"""ai-CR-200 — cảnh báo khóa AI hết tiền / hỏng: nhắn chủ khóa, gom theo trạm, 3 giờ một lần.

14/10/2026 17:16: ví trạm modelapi.vn âm tiền («用户额度不足, 剩余额度: $-0.035204», mã 403) → 3 khóa trạm hỏng cùng
lúc, bot rơi xuống Gemini lite, không ai được báo.
"""
from types import SimpleNamespace

import pytest

from app.core.config import settings
from app.modules.agent_hub import ai_keys, key_alerts, manager, user_keys
from app.modules.agent_hub.ai_keys import KeyRef
from app.modules.agent_hub.model import AgentMessage
from app.modules.assistant.provider.base import ChatMessage, ChatResult, ProviderError

TRAM = "https://modelapi.vn/v1"
LOI_VI = 'openai_compat trả lỗi 403: {"error":{"message":"用户额度不足, 剩余额度: ＄-0.035204"}}'


@pytest.fixture
def env(db, monkeypatch):
    sent = []
    monkeypatch.setattr(settings, "AGENT_TELEGRAM_CHAT_ID", "12345")
    from app.modules.agent_hub import telegram

    monkeypatch.setattr(telegram, "send", lambda text, buttons=None, chat_id="": sent.append((chat_id, text)) or 1)
    import app.core.database as database

    monkeypatch.setattr(database, "SessionLocal", lambda: db)
    monkeypatch.setattr(db, "close", lambda: None)
    monkeypatch.setattr(manager, "TRANSIENT_WAIT_SEC", 0)
    return SimpleNamespace(sent=sent)


def test_loi_vi_tram_tieng_trung_la_het_tien():
    assert ai_keys.is_key_problem(LOI_VI) and "hết tiền" in ai_keys.key_problem(LOI_VI)
    assert key_alerts.kind_of(LOI_VI) == key_alerts.KIND_MONEY


def test_ba_khoa_chung_vi_chi_mot_tin_va_nhay_xuong_khoa_ke(db, env, monkeypatch):
    class Relay:
        def ask(self, msgs, *, model=None, **kw):
            if user_keys.active_ref().base_url == TRAM:
                raise ProviderError(LOI_VI)
            return ChatResult(text="ok từ khóa dự phòng", provider="openai_compat", model="x")
    monkeypatch.setitem(manager._DELEGATES, "openai_compat", Relay())
    chain = [KeyRef(provider="openai_compat", key=f"k-{m}-000{i}", model=m, base_url=TRAM, row_id=i, hint=f"000{i}",
                    owner_type=ai_keys.OWNER_COMPANY)
             for i, m in enumerate(("claude-sonnet-5-5", "kimi-k3", "deepseek-v4.1-flash"), 1)]
    chain.append(KeyRef(provider="openai_compat", key="k-khac-0009", model="gpt-x", base_url="https://khac.vn/v1",
                        row_id=9, hint="0009", owner_type=ai_keys.OWNER_COMPANY))
    with user_keys.use_chain(chain, 0):
        out = manager.get_provider().ask([ChatMessage(role="user", content="hi")])
    assert out.text == "ok từ khóa dự phòng"
    assert len(env.sent) == 1                                       # 3 khóa cùng trạm + cùng loại lỗi → 1 tin
    chat, text = env.sent[0]
    assert chat == "12345" and "HẾT TIỀN" in text and "modelapi.vn" in text and "chung một ví" in text
    assert db.query(AgentMessage).filter(AgentMessage.action == key_alerts.ACT_KEY_ALERT).count() == 1
    #  Lượt sau trong 3 giờ: không nhắn lại.
    with user_keys.use_chain(chain, 0):
        manager.get_provider().ask([ChatMessage(role="user", content="hi")])
    assert len(env.sent) == 1


def test_het_khoa_thi_bao_khong_con_du_phong(db, env, monkeypatch):
    class Relay:
        def ask(self, msgs, *, model=None, **kw):
            raise ProviderError(LOI_VI)
    monkeypatch.setitem(manager._DELEGATES, "openai_compat", Relay())
    chain = [KeyRef(provider="openai_compat", key="k-0001", model="kimi-k3", base_url=TRAM, row_id=1, hint="0001",
                    owner_type=ai_keys.OWNER_COMPANY)]
    with user_keys.use_chain(chain, 0), pytest.raises(ProviderError):
        manager.get_provider().ask([ChatMessage(role="user", content="hi")])
    assert env.sent and "Không còn khóa dự phòng" in env.sent[0][1]
