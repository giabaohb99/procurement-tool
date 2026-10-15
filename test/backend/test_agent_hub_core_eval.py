"""ai-CR-203 — bộ hội thoại mẫu tự chạy của lõi mới (doc/agent-hub/20 §7, §10 việc 3).

Ở đây chỉ kiểm LỒNG THỬ và luật chấm bằng provider giả; chất lượng câu trả lời của model thật chấm bằng
`scripts/eval_core_v2.py` trên máy dev.
"""
from datetime import date
from types import SimpleNamespace

import pytest

from app.core.config import settings
from app.modules.agent_hub import core_eval, core_v2
from app.modules.agent_hub.core_eval import Sample, Turn, TurnLog, check_turn
from app.modules.agent_hub.core_eval_samples import SAMPLES
from app.modules.agent_hub.model import AgentMessage
from app.modules.assistant.provider.base import ChatResult

OWNER = "12345"


def _result(text, calls=None):
    return ChatResult(text=text, provider="openai_compat", model="claude-sonnet-5-5", input_tokens=100, output_tokens=10,
                      tool_calls=calls or [])


class Script:
    """Provider giả: mỗi lượt gọi `steps[i](execute)` → ChatResult; `ask` trả lời chấm."""

    name = "agent_gemini"
    supports_tools = True

    def __init__(self, steps, verdict='{"dat": true, "diem": 9, "ly_do": "ổn"}'):
        self.steps = list(steps)
        self.verdict = verdict

    def run_tools(self, msgs, *, tools, execute, system=None, stop_when=None, **kw):
        step = self.steps.pop(0)
        return step(execute, stop_when)

    def ask(self, messages, **kw):
        return _result(self.verdict)


@pytest.fixture
def env(db, monkeypatch):
    monkeypatch.setattr(settings, "AGENT_TELEGRAM_CHAT_ID", OWNER)
    monkeypatch.setattr(core_v2.user_keys, "active_key", lambda: "khoa-gia")
    monkeypatch.setattr(core_v2.erp, "describe", lambda db_, u: ("Trần Minh Được", "Nhân viên IT"))
    monkeypatch.setattr(core_v2.erp, "tool_defs", lambda db_, u=None: [])
    monkeypatch.setattr(core_v2.erp, "caller_context", lambda db_, u: None)
    monkeypatch.setattr(core_v2.erp, "glossary_block", lambda db_, texts: None)
    erp_calls: list[str] = []
    monkeypatch.setattr(core_v2.erp, "run_tool", lambda db_, u, name, args: erp_calls.append(name) or {
        "draft": {"title": "A", "due_date": "2026-10-16"}} if name.startswith("draft_") else {"rows": []})
    return SimpleNamespace(user=SimpleNamespace(id=275, is_active=True, email="d@dego.com"), erp_calls=erp_calls)


def _install(monkeypatch, prov):
    monkeypatch.setattr(core_v2.manager, "get_provider", lambda: prov)


def _draft_then_stop(execute, stop_when):
    res = execute("draft_work_task", {"title": "A"})
    stop_when("draft_work_task", res)
    return _result("", [{"name": "draft_work_task", "draft": res["draft"]}])


def _commit(execute, stop_when):
    res = execute("commit_draft", {})
    stop_when("commit_draft", res)
    return _result("", [{"name": "commit_draft"}])


def test_soan_roi_dong_y_chi_ghi_so_khong_tao_that(db, env, monkeypatch):
    _install(monkeypatch, Script([_draft_then_stop, _commit]))
    sample = Sample("t1", "thử", (Turn("tạo task A hạn thứ sáu", "soạn", must_call=("draft_work_task",), commit=False),
                                  Turn("ok tạo đi", "tạo", commit=True)))
    res = core_eval.run_sample(db, sample, owner_chat=OWNER, owner_user=env.user, tag="x", today=date(2026, 10, 15))
    assert res.passed, (res.failures, res.judge)
    assert res.turns[1].commits == ["tạo"] and "Đã tạo theo nháp" in res.turns[1].replies[0]
    assert env.erp_calls == ["draft_work_task"]                       # không có lệnh ghi nào tới ERP
    assert db.query(AgentMessage).filter(AgentMessage.chat_id.like("eval-%")).count() == 0     # đã dọn


def test_cong_cu_ghi_bi_chan(db, env, monkeypatch):
    def step(execute, stop_when):
        out = execute("ticket_create", {"title": "x"})
        assert out["ok"]
        return _result("Em tạo phiếu hỗ trợ rồi.", [{"name": "ticket_create"}])
    _install(monkeypatch, Script([step]))
    res = core_eval.run_sample(db, Sample("t2", "chặn", (Turn("máy in hỏng", "tạo phiếu"),)), owner_chat=OWNER,
                               owner_user=env.user, tag="x", today=date(2026, 10, 15), use_judge=False)
    assert res.turns[0].blocked == ["ticket_create"] and "ticket_create" not in env.erp_calls
    assert res.passed and res.judge is None


def test_model_cham_truot_thi_mau_truot(db, env, monkeypatch):
    _install(monkeypatch, Script([lambda e, s: _result("Dạ chào đại ca.")], verdict='{"dat": false, "ly_do": "lạc đề"}'))
    res = core_eval.run_sample(db, Sample("t3", "chào", (Turn("hello em", "chào"),)), owner_chat=OWNER,
                               owner_user=env.user, tag="x", today=date(2026, 10, 15))
    assert not res.passed and "lạc đề" in core_eval.report([res])


def test_chat_chua_lien_ket(db, env, monkeypatch):
    _install(monkeypatch, Script([]))
    res = core_eval.run_sample(db, Sample("t4", "chưa liên kết", (Turn("công nợ", "hướng dẫn", contains=("dangnhap",)),),
                                          unlinked=True), owner_chat=OWNER, owner_user=env.user, tag="x",
                               today=date(2026, 10, 15), use_judge=False)
    assert res.passed, res.failures


def test_luat_cung():
    log = TurnLog(text="x", replies=["Em soạn nháp: hạn <b>23/10/2026</b> «x»"], tools=["draft_work_task"], commits=["tạo"])
    fails = check_turn(Turn("x", "y", must_call=("update_draft",), commit=False, dates=("thứ sáu",)), log, date(2026, 10, 15))
    assert any("update_draft" in f for f in fails) and any("GHI NHÁP" in f for f in fails)
    assert any("16/10/2026" in f for f in fails) and any("« »" in f for f in fails)
    assert check_turn(Turn("x", "y", no_model=True), TurnLog(text="x", replies=["ok"], runs=1), date(2026, 10, 15))


def test_bo_mau_du_20_ma_khong_trung():
    ids = [s.id for s in SAMPLES]
    assert len(ids) == 20 and len(set(ids)) == 20
    tools = core_eval.WRITE_TOOLS
    assert "ticket_create" in tools and "deep_research" in tools
