"""ai-CR-149 — đại ca 09/10/2026: «kế hoạch code thì thằng Claude CLI ở local mới biết … chắc cũng không cần lên plan đâu,
làm gọn phần code này lại đi, hỏi xác nhận vài câu okee thì làm thôi». Rà soát (Claude Code) → thẻ xác nhận / câu hỏi →
«ok» → Claude Code làm; không còn lượt model quản lý viết kế hoạch."""
import pytest

from app.core.config import settings


@pytest.fixture
def flow(db, monkeypatch):
    from app.modules.agent_hub import coder, manager, service
    from app.modules.agent_hub.model import AgentTask

    monkeypatch.setattr(settings, "AGENT_TELEGRAM_CHAT_ID", "12345")
    monkeypatch.setattr(settings, "AGENT_CODE_FLOW_SIMPLE", True)
    monkeypatch.setattr(manager, "run_plan", lambda *a, **k: pytest.fail("dây chuyền gọn không gọi model viết kế hoạch"))
    sent: list[tuple[str, int]] = []
    monkeypatch.setattr(service.telegram, "send", lambda text, **kw: sent.append(text) or len(sent))
    dispatched: list[int] = []
    monkeypatch.setattr(service, "_dispatch_coder", lambda db, chat_id, task, **kw: dispatched.append(task.id))
    task = AgentTask(code="AI-0042", title="Cho bot sửa đơn nghỉ phép", summary="sửa lý do, ngày, loại nghỉ", status=1,
                     risk_level=2, created_by=0, updated_by=0)
    db.add(task)
    db.commit()
    return service, coder, task, sent, dispatched


def _scan(db, coder, task, *, questions=(), files=(), outcomes=()):
    from datetime import datetime

    from app.modules.agent_hub.model import AgentRun

    db.add(AgentRun(task_id=task.id, stage=coder.STAGE_SCAN, provider=coder.PROVIDER, model="m", status=coder.RUN_OK,
                    started_at=datetime.now(), artifact={"message": "Cần thêm tool update_leave_request gọi "
                                                                    "request_service.update.",
                                                         "info": {"files": list(files), "questions": list(questions),
                                                                  "outcomes": list(outcomes)}}))
    db.commit()


def test_khong_cau_hoi_thi_the_xac_nhan_roi_ok_la_lam(db, flow):
    from app.modules.agent_hub.constants import DIR_IN, ST_PLAN

    service, coder, task, sent, dispatched = flow
    _scan(db, coder, task, files=["backend/app/modules/assistant/tools/update_tool.py"])
    service._plan_task(db, task)
    db.refresh(task)
    assert task.status == ST_PLAN and "request_service.update" in task.plan
    card = sent[-1]
    assert "Em hiểu việc" in card and "update_tool.py" in card and "<code>ok</code>" in card and "«" not in card
    row = service.log_message(db, DIR_IN, "12345", 77, "oke làm đi")
    db.commit()
    assert service._ok_by_text(db, "12345", row, "oke làm đi")
    assert dispatched == [task.id]
    #  «ok» khi tin bot gần nhất KHÔNG phải thẻ xác nhận → không đụng việc nào.
    service.reply(db, "12345", "Câu trả lời thường của Trợ lý")
    row = service.log_message(db, DIR_IN, "12345", 78, "ok")
    db.commit()
    assert service._ok_by_text(db, "12345", row, "ok") is False and dispatched == [task.id]


def test_con_cau_hoi_thi_hoi_toi_da_3_cau_khong_moi_lam(db, flow):
    from app.modules.agent_hub.constants import DIR_IN, ST_NEEDS_INPUT

    service, coder, task, sent, dispatched = flow
    _scan(db, coder, task, questions=["Sửa được loại nghỉ không?", "Đơn đã gửi duyệt có sửa không?",
                                      "Ai được sửa?", "Có ghi nhật ký không?"])
    service._plan_task(db, task)
    db.refresh(task)
    assert task.status == ST_NEEDS_INPUT and len(task.questions) == 3
    assert "đang hỏi lại" in sent[-1] and "Sửa được loại nghỉ không?" in sent[-1]
    row = service.log_message(db, DIR_IN, "12345", 77, "ok")
    db.commit()
    assert service._ok_by_text(db, "12345", row, "ok") is False and dispatched == []


def test_chua_chot_tep_van_giao_duoc_va_khong_tinh_lech_pham_vi(flow):
    from types import SimpleNamespace

    service, coder, task, sent, dispatched = flow
    assert coder.approve_gate(SimpleNamespace(plan_files=[])) == ""
    assert "cấm sửa" in coder.approve_gate(SimpleNamespace(plan_files=["backend/app/modules/agent_hub/ops.py"]))
    assert coder.check_drift(["backend/app/x.py", "backend/app/y.py"], [], max_files=12) == ""
    assert "tệp cấm" in coder.check_drift(["backend/app/modules/agent_hub/ops.py"], [], max_files=12)


def test_o_model_cu_khong_con_o_tram_thi_tu_doi_model_cung_ho(monkeypatch):
    """Đại ca đổi nhóm trên modelapi.vn → ô Model cũ «model_not_found» → bot lấy model trạm đang có thay vì chết."""
    from app.modules.agent_hub import ai_keys, manager, user_keys
    from app.modules.agent_hub.ai_keys import KeyRef
    from app.modules.assistant.provider.base import ChatResult, ProviderError

    manager._MODEL_SWAP.clear()
    ref = KeyRef(provider="openai_compat", key="k", model="deepseek-v4-flash", base_url="https://x/v1", row_id=4)
    monkeypatch.setattr(ai_keys, "custom_models", lambda base, key: ["gpt-5", "deepseek-v4.1-flash"])
    used: list[str] = []

    def fake_ask(messages, model=None, **kw):
        used.append(model)
        if model == "deepseek-v4-flash":
            raise ProviderError('503 {"error":{"code":"model_not_found"}}')
        return ChatResult(text="ok", provider="openai_compat", model=model, input_tokens=1, output_tokens=1)

    monkeypatch.setattr(manager._DELEGATES["openai_compat"], "ask", fake_ask)
    with user_keys.use_chain([ref]):
        out = manager.get_provider().ask([], max_tokens=5)
    assert out.text == "ok" and used == ["deepseek-v4-flash", "deepseek-v4.1-flash"]
    manager._MODEL_SWAP.clear()


def test_giuc_sua_no_di_sau_chi_tiet_viec_la_lam_luon(db, flow):
    """ai-CR-150: «chi tiết AI-0006» rồi «sửa nó đi em» → bot từng trả «em không sửa được». Nay là giao việc đó luôn,
    kể cả khi việc đang ở «đang hỏi lại» (các câu còn mở để Claude tự quyết theo mạch đã bàn)."""
    from app.modules.agent_hub.constants import DIR_IN, ST_NEEDS_INPUT

    service, coder, task, sent, dispatched = flow
    _scan(db, coder, task, questions=["Sửa được loại nghỉ không?"], files=["backend/app/x.py"])
    task.status = ST_NEEDS_INPUT
    task.questions = ["Sửa được loại nghỉ không?"]
    db.commit()
    service.reply(db, "12345", "<b>AI-0042</b> · chi tiết …", task_id=task.id)
    row = service.log_message(db, DIR_IN, "12345", 90, "sửa nó đi em")
    db.commit()
    assert service._ok_by_text(db, "12345", row, "sửa nó đi em")
    assert dispatched == [task.id] and task.questions == [] and task.plan_files == ["backend/app/x.py"]
    for text in ("sửa đơn NP011 giúp anh", "làm sao để sửa", "sửa: thêm phần xóa"):
        row = service.log_message(db, DIR_IN, "12345", 91, text)
        assert service._ok_by_text(db, "12345", row, text) is False, text


def test_day_chuyen_gon_khong_dung_vi_tep_ngoai_du_kien():
    """ai-CR-151 — AI-0006 làm xong, xanh, mà dừng không commit vì 4 tệp nhỏ ngoài danh sách dự kiến. Dây chuyền gọn
    chỉ còn chặn tệp cấm và trần số tệp."""
    from app.modules.agent_hub import coder

    plan = ["backend/app/a.py"]
    touched = ["backend/app/a.py", "backend/app/b.py", "backend/app/c.py"]
    assert coder.check_drift(touched, plan, max_files=25) == ""
    assert "ngoài kế hoạch" in coder.check_drift(touched, plan, max_files=25, ratio=True)
    assert "cấm" in coder.check_drift(touched + [".env"], plan, max_files=25)
    assert "vượt trần" in coder.check_drift([f"backend/a{i}.py" for i in range(30)], plan, max_files=25)
    assert "DỰ KIẾN" in coder._c1_rule() and "30%" not in coder._c1_rule()


@pytest.mark.parametrize("raw,expected", [
    ("<thinking> </thinking>\nĐại ca ơi, em sửa rồi", "Đại ca ơi, em sửa rồi"),
    ("<think>nháp\nnháp</think>Trả lời", "Trả lời"),
    ("<reasoning>x</reasoning> Có", "Có"),
    ("</thinking>Còn thẻ lẻ", "Còn thẻ lẻ"),
    ("Câu bình thường", "Câu bình thường"),
])
def test_bo_the_suy_nghi_lot_vao_cau_tra_loi(raw, expected):
    from app.modules.assistant.provider.openai_compat import clean_reply

    assert clean_reply(raw) == expected


def test_the_xac_nhan_va_de_bai_co_dieu_kien_xong(db, flow):
    """ai-CR-153 — AI-0006 thiếu đúng phần sửa lý do nghỉ mà thẻ xác nhận chỉ liệt kê tệp nên không ai thấy. Thẻ nay ghi
    các câu người dùng làm được sau khi xong; đề bài sửa mã bắt mỗi câu có một bài kiểm."""
    service, coder, task, sent, dispatched = flow
    outcomes = ["Nhắn bot sửa lý do đơn nghỉ NP011 rồi bấm Xác nhận", "Nhắn bot đổi ngày nghỉ sang thứ ba"]
    _scan(db, coder, task, files=["backend/app/modules/assistant/tools/update_tool.py"], outcomes=outcomes)
    service._plan_task(db, task)
    card = sent[-1]
    assert "Xong việc này, đại ca làm được" in card and outcomes[0] in card and outcomes[1] in card
    brief = coder.build_brief(task, [])
    assert "## Điều kiện xong" in brief and f"1. {outcomes[0]}" in brief and "ít nhất MỘT bài kiểm" in brief
    assert "C11." in brief and "test_agent_hub_ranh_gioi_erp.py" in brief


def test_ra_soat_khong_ghi_dieu_kien_xong_thi_the_nhu_cu(db, flow):
    service, coder, task, sent, dispatched = flow
    _scan(db, coder, task)
    service._plan_task(db, task)
    assert "Xong việc này" not in sent[-1] and "## Điều kiện xong" not in coder.build_brief(task, [])


def test_doc_dieu_kien_xong_tu_ket_qua_ra_soat():
    from app.modules.agent_hub import coder

    text = ("**Kết luận:** thiếu tool sửa lý do.\n```json\n"
            '{"files": [], "questions": [], "outcomes": ["  sửa lý do đơn nghỉ  ", "", "x", "y", "z", "w", "v"]}'
            "\n```")
    _, info = coder.parse_scan(text)
    assert info["outcomes"][0] == "sửa lý do đơn nghỉ" and len(info["outcomes"]) == coder.OUTCOMES_MAX


def test_ok_tren_the_la_dong_y_luon_buoc_gop_va_dua_len_dev(db, flow, monkeypatch):
    """ai-CR-154 — đại ca 09/10: «em cảnh báo trước mà anh vẫn chấp nhận làm thì có thể đẩy code luôn». Thẻ xác nhận nói
    trước; sửa xong mà bài kiểm không đỏ thì tự gộp + deploy dev, đỏ thì dừng ở thẻ kết quả như cũ."""
    from app.modules.agent_hub.constants import ST_REVIEW

    service, coder, task, sent, dispatched = flow
    monkeypatch.setattr(settings, "AGENT_DEPLOY_ENABLED", True)
    monkeypatch.setattr(settings, "AGENT_CODER_ENABLED", True)
    task.risk_level = 3
    db.commit()
    _scan(db, coder, task, files=["backend/app/modules/assistant/tools/update_tool.py"])
    service._plan_task(db, task)
    card = sent[-1]
    assert "tự gộp vào" in card and "không hỏi lại" in card and "Cảnh báo:" in card

    deploys: list[int] = []
    monkeypatch.setattr(service, "_dispatch_deploy", lambda db, chat_id, cb_id, t, **kw: deploys.append(t.id))
    task.status = ST_REVIEW
    db.commit()
    assert service.auto_deploy_after_code(db, task, {"status": "fail"}) is False and deploys == []
    assert service.auto_deploy_after_code(db, task, {"status": "pass"}) is True and deploys == [task.id]
    monkeypatch.setattr(settings, "AGENT_AUTO_DEPLOY_AFTER_OK", False)
    assert service.auto_deploy_after_code(db, task, {"status": "pass"}) is False and len(deploys) == 1
    service._plan_task(db, task)
    assert "tự gộp vào" not in sent[-1]
