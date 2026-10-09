"""ai-CR-144 — AI-0006 (09/10/2026): model rẻ xả suy nghĩ tiếng Anh ra phần chữ, trong đó có mảnh «{…}» lẻ → kế hoạch
rỗng mà vẫn đi tiếp: thẻ trắng kèm «nhắn duyệt», việc kẹt ở «đang hỏi lại», đại ca nhắn duyệt thì bot báo không có việc."""
import json

import pytest

from app.modules.agent_hub import manager
from app.modules.assistant.provider.base import ChatResult

@pytest.fixture(autouse=True)
def _old_code_flow(monkeypatch):
    """ai-CR-149: dây chuyền gọn (không model quản lý viết kế hoạch) bật mặc định; các bài ở tệp này canh dây chuyền CŨ
    (vẫn còn khi tắt AGENT_CODE_FLOW_SIMPLE). Dây chuyền gọn canh ở test_agent_hub_day_chuyen_gon.py."""
    from app.core.config import settings as _s

    monkeypatch.setattr(_s, "AGENT_CODE_FLOW_SIMPLE", False)

PLAN = {"plan": "1. Thêm tool xóa nháp.", "plan_files": ["backend/app/modules/agent_hub/draft_create.py"],
        "test_plan": "- xóa đúng phiếu", "risk_level": 2, "needs_clarification": False, "questions": [],
        "assumptions": []}
LEAK = ('Let me analyze this task. The rule says {"needs_clarification": true} when unsure. Hmm, {} maybe. '
        "Actually let me reconsider...")


def _res(text):
    return ChatResult(text=text, provider="openai_compat", model="deepseek-v4.1-flash", input_tokens=1, output_tokens=1)


def test_lay_dung_object_co_khoa_plan_giua_doan_suy_nghi():
    assert manager.extract_json_with(LEAK, "plan") is None                      # mảnh lẻ không có «plan» → không nhận
    text = LEAK + "\n```json\n" + json.dumps(PLAN, ensure_ascii=False) + "\n```\nDone."
    assert manager.extract_json_with(text, "plan")["plan_files"] == PLAN["plan_files"]
    assert manager.extract_json_with('{"plan": ""}', "plan") is None


def test_xa_suy_nghi_thi_thu_lai_mot_lan_roi_bao_loi(monkeypatch):
    calls: list[str] = []

    class P:
        def __init__(self, outputs):
            self.outputs = outputs

        def ask(self, messages, **kw):
            calls.append(messages[0].content)
            return _res(self.outputs.pop(0))

    monkeypatch.setattr(manager, "get_provider", lambda: prov)
    prov = P([LEAK, json.dumps(PLAN)])
    data, _ = manager.run_plan("Phát triển sửa và xóa", "mô tả", [])
    assert data["plan"] == PLAN["plan"] and len(calls) == 2 and "CHỈ trả MỘT object JSON" in calls[1]
    calls.clear()
    prov = P([LEAK, LEAK])
    with pytest.raises(manager.ProviderError, match="không trả kế hoạch"):
        manager.run_plan("Phát triển sửa và xóa", "mô tả", [])


def test_can_hoi_ma_khong_co_cau_hoi_thi_van_hoi_khong_moi_duyet(db, monkeypatch):
    from app.core.config import settings
    from app.modules.agent_hub import service
    from app.modules.agent_hub.constants import ST_NEEDS_INPUT
    from app.modules.agent_hub.model import AgentTask

    monkeypatch.setattr(settings, "AGENT_TELEGRAM_CHAT_ID", "12345")
    task = AgentTask(code="AI-0099", title="Phát triển sửa và xóa", summary="x", status=1, risk_level=2,
                     created_by=0, updated_by=0)
    db.add(task)
    db.commit()
    plan = dict(PLAN, plan_files=[], related_docs=[])
    monkeypatch.setattr(service.manager, "run_plan", lambda *a, **k: (dict(plan, needs_clarification=True), _res("x")))
    monkeypatch.setattr(service.memory, "recall", lambda q: [])
    monkeypatch.setattr(service.coder, "scan_message_for", lambda t: "")
    sent: list[str] = []
    monkeypatch.setattr(service, "reply", lambda db, chat_id, text, **kw: sent.append(text))
    service._plan_task(db, task)
    db.refresh(task)
    assert task.status == ST_NEEDS_INPUT and task.questions
    assert "đang hỏi lại" in sent[-1] and "duyệt" not in sent[-1].lower().replace("chưa đủ", "")


def test_lap_ke_hoach_uu_tien_khoa_claude_neu_co(monkeypatch):
    """ai-CR-145: chuỗi khóa có Claude thì bước lập kế hoạch dùng Claude trước (DeepSeek flash xả suy nghĩ ra chữ);
    không có thì giữ chuỗi cũ. Ngoài bước lập kế hoạch, thứ tự chuỗi không đổi."""
    from app.core.config import settings
    from app.modules.agent_hub import user_keys
    from app.modules.agent_hub.ai_keys import KeyRef

    ds = KeyRef(provider="openai_compat", key="k1", model="deepseek-v4.1-flash", base_url="https://x/v1")
    gm = KeyRef(provider="gemini", key="k2")
    cl = KeyRef(provider="claude", key="k3")
    monkeypatch.setattr(settings, "AGENT_PLAN_PROVIDERS", "claude,openai")
    monkeypatch.setattr(settings, "AGENT_PLAN_MODEL", "claude-sonnet-5-5")
    seen: list[tuple] = []

    class P:
        def ask(self, messages, **kw):
            ref = user_keys.active_ref()
            seen.append((ref.provider, kw.get("model")))
            return _res(json.dumps(PLAN))

    monkeypatch.setattr(manager, "get_provider", lambda: P())
    with user_keys.use_chain([ds, gm, cl]):
        manager.run_plan("t", "s", [])
        assert user_keys.active_ref().provider == "openai_compat"          # ra khỏi bước kế hoạch: chuỗi như cũ
    assert seen == [("claude", "claude-sonnet-5-5")]
    assert manager.AgentGeminiProvider._model_for(cl, "claude-sonnet-5-5") == "claude-sonnet-5-5"
    assert manager.AgentGeminiProvider._model_for(cl, "gemini-flash-latest") is None
    seen.clear()
    with user_keys.use_chain([ds, gm]):
        manager.run_plan("t", "s", [])
    assert seen[0][0] == "openai_compat"


def test_khoa_claude_qua_tram_tuy_chinh_cung_duoc_uu_tien(monkeypatch):
    """ai-CR-146: khóa modelapi.vn nhóm «claude» khai là openai_compat + model claude-… → vẫn được ưu tiên lập kế hoạch."""
    from app.core.config import settings
    from app.modules.agent_hub import user_keys
    from app.modules.agent_hub.ai_keys import KeyRef

    ds = KeyRef(provider="openai_compat", key="k1", model="deepseek-v4.1-flash", base_url="https://x/v1")
    cl = KeyRef(provider="openai_compat", key="k2", model="claude-sonnet-4-5", base_url="https://x/v1")
    monkeypatch.setattr(settings, "AGENT_PLAN_PROVIDERS", "claude,openai")
    with user_keys.use_chain([ds, cl]):
        with user_keys.prefer(["claude", "openai"]):
            assert user_keys.active_ref().model == "claude-sonnet-4-5"
        assert user_keys.active_ref().model == "deepseek-v4.1-flash"


def test_lap_ke_hoach_dung_ban_manh_cung_ho_con_chat_dung_ban_nhanh(monkeypatch):
    """ai-CR-146: khóa modelapi.vn ghi deepseek-v4-flash (chat nhanh, rẻ); riêng bước lập kế hoạch dùng deepseek-v4-pro.
    Khóa khác họ (Claude qua trạm) không bị đổi model."""
    from app.modules.agent_hub import user_keys
    from app.modules.agent_hub.ai_keys import KeyRef

    ds = KeyRef(provider="openai_compat", key="k1", model="deepseek-v4-flash", base_url="https://x/v1")
    cl = KeyRef(provider="openai_compat", key="k2", model="claude-sonnet-4-5", base_url="https://x/v1")
    with user_keys.use_chain([ds, cl]):
        with user_keys.prefer([], model="deepseek-v4-pro"):
            assert [r.model for r in user_keys.chain()] == ["deepseek-v4-pro", "claude-sonnet-4-5"]
        assert user_keys.active_ref().model == "deepseek-v4-flash"
    monkeypatch.setattr(manager, "plan_model_setting", lambda: "deepseek-v4-pro")
    monkeypatch.setattr(manager, "plan_providers", lambda: ["claude", "openai"])
    seen: list = []

    class P:
        def ask(self, messages, **kw):
            seen.append(user_keys.active_ref().model)
            return _res(json.dumps(PLAN))

    monkeypatch.setattr(manager, "get_provider", lambda: P())
    with user_keys.use_chain([ds]):
        manager.run_plan("t", "s", [])
    assert seen == ["deepseek-v4-pro"]


def test_bang_gia_deepseek_qua_tram_khong_con_tinh_0():
    """ai-CR-147: «/chiphi» báo $0.00 vì bảng giá chỉ có Gemini. Nay có giá DeepSeek qua modelapi.vn (theo nhóm của trạm)."""
    from app.modules.agent_hub.constants import estimate_cost_usd

    assert estimate_cost_usd("deepseek-v4-flash", 1_000_000, 0) == pytest.approx(9.50)
    assert estimate_cost_usd("deepseek-v4-pro", 0, 1_000_000) == pytest.approx(85.54)
    assert estimate_cost_usd("deepseek-v4.1-flash", 1_000_000, 1_000_000) == pytest.approx(10.50)
    #  Bản v4 nhóm «deepseek» đắt hơn bản v4.1 nhóm tự host khoảng 4,5 lần mỗi token vào.
    assert estimate_cost_usd("deepseek-v4-flash", 1000, 0) / estimate_cost_usd("deepseek-v4.1-flash", 1000, 0) > 4
