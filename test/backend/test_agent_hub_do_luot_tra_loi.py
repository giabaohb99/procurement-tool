"""ai-CR-160 (phase 16.1) — đo từng lượt trả lời: sổ ý định ghi token / tiền / thời gian / số khai báo công cụ đã gửi;
lượt Trợ lý trả lời trên Telegram ghi sổ chi phí (trước đây không, nên báo chi phí «AI theo khóa» thiếu phần lớn nhất)."""
from app.modules.agent_hub import intent_ledger as il


def test_cot_chi_phi_tu_khoi_usage():
    f = il.usage_fields({"model": "deepseek-v4.1-flash", "input_tokens": 20000, "output_tokens": 300,
                         "thinking_tokens": 50, "cache_read_tokens": 15000, "duration_ms": 4200, "tools_offered": 69})
    assert f["tokens_in"] == 20000 and f["tokens_out"] == 350 and f["cache_read"] == 15000
    assert f["duration_ms"] == 4200 and f["tools_offered"] == 69 and f["model"] == "deepseek-v4.1-flash"
    assert f["cost_usd"] > 0
    assert il.usage_fields(None) == {"model": "", "tokens_in": 0, "tokens_out": 0, "cache_read": 0, "cost_usd": 0.0,
                                     "duration_ms": 0, "tools_offered": 0}


def test_so_y_dinh_ghi_chi_phi_luot(db, seed):
    row = il.record(db, user_id=seed.u_req_id, channel=il.Channel.WEB, scope=2, scope_key="9", intent=il.Intent.ASK,
                    question="công nợ tháng này", answer="Công nợ…", usage={"model": "gemini-2.5-flash",
                                                                            "input_tokens": 1000, "output_tokens": 100,
                                                                            "duration_ms": 900, "tools_offered": 12})
    db.refresh(row)
    assert row.tokens_in == 1000 and row.tokens_out == 100 and row.tools_offered == 12 and row.duration_ms == 900


def test_luot_tra_loi_telegram_ghi_so_chi_phi(db, monkeypatch):
    from app.core.config import settings
    from app.modules.agent_hub import service
    from app.modules.agent_hub.constants import STAGE_ANSWER
    from app.modules.agent_hub.model import AgentRun

    monkeypatch.setattr(settings, "AGENT_TELEGRAM_CHAT_ID", "12345")
    run = service.start_run(db, 0, STAGE_ANSWER)
    db.commit()
    service._close_answer_run(db, run, {"provider": "deepseek", "model": "deepseek-v4.1-flash", "text": "bí mật",
                                        "tool_calls": [{"name": "payable_lookup"}],
                                        "usage": {"input_tokens": 21000, "output_tokens": 400, "tools_offered": 69}})
    row = db.get(AgentRun, run.id)
    assert row.stage == STAGE_ANSWER and row.status == 2 and row.input_tokens == 21000 and row.cost_usd > 0
    assert row.artifact == {"tools": ["payable_lookup"], "tools_offered": 69}     # không giữ chữ câu trả lời
    bad = service.start_run(db, 0, STAGE_ANSWER)
    db.commit()
    service._close_answer_run(db, bad, None, error="429 hết hạn mức")
    assert db.get(AgentRun, bad.id).status == 3
