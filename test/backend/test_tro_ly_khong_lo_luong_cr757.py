"""duoc-CR-757 — trợ lý AI / bot / cổng MCP KHÔNG BAO GIỜ nói lương của người khác (luật tuyệt đối của chủ dự án).

Canh từng công cụ đụng tới nhân sự / hợp đồng / tiền gắn với một người:
  - quản trị đủ mọi quyền hỏi người khác → con số lương / tiền thanh toán nghỉ phép KHÔNG có trong kết quả (soi cả
    chuỗi JSON, không chỉ tên khóa);
  - chính chủ ở kênh riêng (Trợ lý web, chat riêng bot) → thấy lương của mình qua `my_salary`;
  - chính chủ ở nhóm chat / chat chưa liên kết / cổng MCP / kênh không rõ → từ chối, dặn hỏi ở chat riêng;
  - cờ chat riêng do MÁY gắn (`handle_message`, header đã ký ở cổng B), không lấy từ tham số công cụ;
  - lịch sử chat / ghi chú qua cổng MCP không trả lượt lương (C1 của bản rà).
"""
from datetime import date

import pytest

from app.core.logging_codes import AI_CHANNEL_MCP, AI_CHANNEL_TELEGRAM, AI_CHANNEL_WEB, AI_CHANNEL_ZALO
from app.core.labor_contract_codes import LaborContractType
from app.core.report_keys import ReportKey
from app.core.request_context import ai_channel_scope
from app.modules.assistant.private_chat import PRIVATE_CHAT_HEADER, current_private_chat, private_chat_scope
from app.core.subject_match import SUBJECT_ROLE
from app.modules.assistant import tools as T
from app.modules.assistant.tools import salary_privacy as sp
from app.modules.employee.model import Employee
from app.modules.labor_contract.model import LaborContract
from app.modules.payment_request.model import PaymentRequest, PaymentRequestLine
from app.modules.user.model import User

OTHER_SALARY, OTHER_ALLOWANCE = 31_234_567, 2_345_678
MY_SALARY, MY_ALLOWANCE = 25_111_222, 1_222_333
OTHER_PAYOUT, MY_PAYOUT, GOODS_PAYMENT = 1_234_567, 987_654, 500_000
CONTRACT_SALARY = 9_876_543
POLICY = "chỉ chính nhân sự đó mới xem được"


def _absent(out, *values):
    text = str(out)
    for v in values:
        for form in (str(v), f"{v:,}", f"{v:,}".replace(",", ".")):
            assert form not in text, f"lộ {form}"


@pytest.fixture
def world(db, seed, cap_quyen, gan_bao_cao):
    """Lương trên hồ sơ của hai người, HĐLĐ của người khác, YCTT thanh toán nghỉ phép của cả hai + một YCTT tiền hàng.
    `admin` (u_nstm) có MỌI quyền phạm vi tất cả, kể cả xem nhóm nhạy cảm, HĐLĐ, YCTT nghỉ phép."""
    other = db.get(Employee, seed.emp_tp_id)
    other.salary_monthly, other.allowance_monthly = OTHER_SALARY, OTHER_ALLOWANCE
    me = db.get(Employee, seed.emp_req_id)
    me.salary_monthly, me.allowance_monthly = MY_SALARY, MY_ALLOWANCE
    db.add(LaborContract(code="HDLD757", employee_id=other.id, company_id=seed.company_id, department_id=seed.dept_id,
                         contract_type=int(LaborContractType.INDEFINITE), status=2, start_date=date(2026, 1, 1),
                         base_salary=CONTRACT_SALARY, insurance_salary=CONTRACT_SALARY, allowance=OTHER_ALLOWANCE))
    rows = [
        PaymentRequest(code="YCTT-TTP-KHAC", source_type="leave_encashment", payee_employee_id=other.id,
                       total=OTHER_PAYOUT, status="submitted", company_id=seed.company_id, department_id=seed.dept_id,
                       request_date="2026-11-01", print_texts=f'{{"content": "Chi {OTHER_PAYOUT} đồng"}}'),
        PaymentRequest(code="YCTT-TTP-TOI", source_type="leave_encashment", payee_employee_id=me.id,
                       total=MY_PAYOUT, status="submitted", company_id=seed.company_id, department_id=seed.dept_id,
                       request_date="2026-11-01"),
        PaymentRequest(code="YCTT-HANG", source_type="goods", total=GOODS_PAYMENT, status="submitted",
                       company_id=seed.company_id, department_id=seed.dept_id, request_date="2026-11-01",
                       supplier_code="NCC1", supplier_name="NCC Một"),
    ]
    db.add_all(rows)
    db.flush()
    db.add_all([PaymentRequestLine(request_id=r.id, amount=r.total) for r in rows])
    db.commit()
    for uid in (seed.u_nstm_id, seed.u_req_id):
        for entity in ("employee", "employee_sensitive", "labor_contract", "payment_request", "leave_encashment",
                       "leave_balance", "leave_request"):
            cap_quyen(uid, entity, scope="all", read=True, approve=True, write=True)
    role = cap_quyen(seed.u_nstm_id, "labor_contract", scope="all", read=True)
    gan_bao_cao(SUBJECT_ROLE, role.id, ReportKey.LABOR_CONTRACT)
    return db.get(User, seed.u_nstm_id), db.get(User, seed.u_req_id), other


def _run(db, user, name, args, channel=AI_CHANNEL_WEB, private=False):
    with ai_channel_scope(channel), private_chat_scope(private):
        return T.run_tool(db, user, name, args)


# ── Quản trị hỏi người khác: không lộ con số ──────────────────────────────────────

def test_danh_ba_va_tra_phep_khong_lo_luong_nguoi_khac(db, world):
    admin, _me, other = world
    _absent(_run(db, admin, "employee_lookup", {"query": other.code}), OTHER_SALARY, OTHER_ALLOWANCE)
    out = _run(db, admin, "employee_leave_summary", {"employee": other.code})
    assert out["employees"] and out["employees"][0]["code"] == other.code
    _absent(out, OTHER_SALARY, OTHER_ALLOWANCE, CONTRACT_SALARY)


def test_my_salary_khong_co_cach_chon_nguoi_khac(db, world):
    admin, _me, other = world
    assert T.MY_SALARY_SPEC.parameters["properties"] == {}
    out = _run(db, admin, "my_salary", {"employee": other.code, "employee_id": other.id})
    _absent(out, OTHER_SALARY, OTHER_ALLOWANCE)


def test_yctt_thanh_toan_nghi_phep_cua_nguoi_khac_giau_so_tien(db, world):
    admin, _me, _other = world
    out = _run(db, admin, "payment_request_read", {"code": "YCTT-TTP-KHAC"})
    assert out["money_hidden"] is True and POLICY in out["note"] and "url" in out
    _absent(out, OTHER_PAYOUT)
    #  YCTT tiền hàng vẫn đọc đủ số như cũ.
    assert _run(db, admin, "payment_request_read", {"code": "YCTT-HANG"})["total"] == GOODS_PAYMENT


def test_danh_sach_cho_duyet_va_bang_so_khong_lo_tien_nghi_phep(db, world):
    admin, _me, _other = world
    out = _run(db, admin, "pending_procurement_approvals", {"entity": "payment_request"})
    items = {i["code"]: i for g in out["groups"] for i in g["items"]}
    assert items["YCTT-TTP-KHAC"]["total"] is None and items["YCTT-TTP-KHAC"]["money_hidden"] is True
    assert items["YCTT-HANG"]["total"] == GOODS_PAYMENT
    _absent(out, OTHER_PAYOUT)

    agg = _run(db, admin, "dataset_query", {"dataset": "payment_request", "measures": ["total"],
                                            "dimensions": ["department"]})
    _absent(agg, OTHER_PAYOUT, MY_PAYOUT, OTHER_PAYOUT + MY_PAYOUT + GOODS_PAYMENT)
    assert str(GOODS_PAYMENT) in str(agg)


def test_de_xuat_sua_yctt_nghi_phep_khong_doc_duoc(db, world):
    admin, _me, _other = world
    out = _run(db, admin, "propose_document_update", {"entity": "payment_request", "code": "YCTT-TTP-KHAC",
                                                      "changes": {"print_content": "x"}})
    _absent(out, OTHER_PAYOUT)
    assert "error" in out


def test_bao_cao_hop_dong_va_quy_luong(db, world):
    admin, _me, _other = world
    out = _run(db, admin, "report_summary", {"report_key": "labor_contract"})
    assert "error" not in out, out
    _absent(out, CONTRACT_SALARY, OTHER_ALLOWANCE)
    assert _run(db, admin, "report_summary", {"report_key": "21"})["denied"] is True


# ── Chính chủ: chỉ ở kênh riêng ──────────────────────────────────────────────────

@pytest.mark.parametrize("channel,private", [(AI_CHANNEL_WEB, False), (AI_CHANNEL_TELEGRAM, True),
                                             (AI_CHANNEL_ZALO, True)])
def test_chinh_chu_kenh_rieng_thay_luong_cua_minh(db, world, channel, private):
    _admin, me, _other = world
    out = _run(db, me, "my_salary", {}, channel, private)
    assert out["salary_monthly"] == MY_SALARY and out["allowance_monthly"] == MY_ALLOWANCE
    _absent(out, OTHER_SALARY)
    yctt = _run(db, me, "payment_request_read", {"code": "YCTT-TTP-TOI"}, channel, private)
    assert yctt["total"] == MY_PAYOUT


@pytest.mark.parametrize("channel,private", [(AI_CHANNEL_TELEGRAM, False), (AI_CHANNEL_ZALO, False),
                                             (AI_CHANNEL_MCP, True), (0, True)])
def test_chinh_chu_o_nhom_hay_mcp_bi_tu_choi(db, world, channel, private):
    _admin, me, _other = world
    #  Tham số lạ do model / ứng dụng ngoài tự điền KHÔNG mở được gì nữa.
    out = _run(db, me, "my_salary", {"_conversation": "private", "private": True}, channel, private)
    assert out["denied"] is True and "chat riêng" in out["reason"]
    _absent(out, MY_SALARY, MY_ALLOWANCE)
    yctt = _run(db, me, "payment_request_read", {"code": "YCTT-TTP-TOI"}, channel, private)
    assert yctt["money_hidden"] is True
    _absent(yctt, MY_PAYOUT)


def test_tai_khoan_chua_gan_nhan_su_khong_co_luong(db, seed):
    admin = User(email="admin757@dego.vn", employee_id=0, password_hash="x", is_active=True)
    db.add(admin)
    db.commit()
    out = _run(db, admin, "my_salary", {})
    assert "error" in out and "salary_monthly" not in out


# ── Cờ chat riêng do máy gắn ─────────────────────────────────────────────────────

def _link(db, user_id: int, chat_id: str):
    from datetime import datetime, timedelta

    from app.modules.agent_hub.model import AgentChatLink

    db.add(AgentChatLink(user_id=user_id, chat_id=chat_id, linked_at=datetime.now(),
                         expires_at=datetime.now() + timedelta(days=30)))
    db.commit()


def test_handle_message_gan_co_chat_rieng_theo_ma_chat_va_lien_ket(db, seed, monkeypatch):
    from app.modules.agent_hub import service

    seen = []
    monkeypatch.setattr(service, "_handle_message", lambda db_, msg, chat_id: seen.append(current_private_chat()))
    _link(db, seed.u_req_id, "7001")
    _link(db, seed.u_req_id, "-1007001")
    for chat in ({"id": 7001, "type": "private"}, {"id": 7002, "type": "private"},
                 {"id": -1007001, "type": "supergroup"}):
        service.handle_message(db, {"chat": chat, "text": "lương của tôi"})
    assert seen == [True, False, False]          # riêng đã liên kết · riêng chưa liên kết (tài khoản lùi) · nhóm
    assert current_private_chat() is False       # ra khỏi lượt thì trả về mặc định


def test_cong_b_chi_doc_co_chat_rieng_tu_header(monkeypatch):
    from types import SimpleNamespace

    from app.modules.agent_gateway import controller as gw

    gw._take_ai_channel(SimpleNamespace(headers={PRIVATE_CHAT_HEADER: "1", "x-agent-ai-channel": "2"}))
    assert current_private_chat() is True
    gw._take_ai_channel(SimpleNamespace(headers={}))
    assert current_private_chat() is False


def test_dich_vu_ai_gui_header_chat_rieng_da_ky(monkeypatch):
    from types import SimpleNamespace

    from app.core import agent_signature
    from app.core.config import settings
    from app.modules.agent_hub import erp

    sent = []
    monkeypatch.setattr(settings, "AGENT_SERVICE_SECRET", "khoa-thu-757")
    monkeypatch.setattr(settings, "AGENT_GATEWAY_URL", "http://erp.test")
    monkeypatch.setattr(erp.requests, "request", lambda method, url, **kw: sent.append(kw) or SimpleNamespace(
        status_code=200, json=lambda: {"success": True, "data": {}}))
    with ai_channel_scope(AI_CHANNEL_TELEGRAM), private_chat_scope(True):
        erp._Remote()._call("POST", "/tools/run", user_id=1, body={})
    erp._Remote()._call("POST", "/tools/run", user_id=1, body={})
    assert sent[0]["headers"].get(PRIVATE_CHAT_HEADER) == "1" and PRIVATE_CHAT_HEADER not in sent[1]["headers"]
    for kw in sent:   # hai header ngữ cảnh nằm trong chữ ký: bên nhận kiểm đúng
        assert agent_signature.verify("POST", "/api/agent-gw/tools/run", kw["data"] or b"", kw["headers"])[0]
    forged = {**sent[1]["headers"], PRIVATE_CHAT_HEADER: "1"}
    assert not agent_signature.verify("POST", "/api/agent-gw/tools/run", sent[1]["data"] or b"", forged)[0]


def test_my_salary_khong_doc_tham_so_an_va_mcp_khong_co(db, seed, monkeypatch):
    from app.modules.agent_hub import mcp

    assert "my_salary" in mcp.HIDDEN
    assert not hasattr(sp, "CONVERSATION_ARG")


# ── C1: lịch sử chat / ghi chú qua cổng MCP không trả lượt lương ────────────────────

def _history_world(db, seed):
    from app.modules.agent_hub.constants import ACT_ANSWER, DIR_IN, DIR_OUT
    from app.modules.agent_hub.model import AgentIntent, AgentMessage

    _link(db, seed.u_req_id, "8001")
    rows = [AgentMessage(chat_id="8001", direction=DIR_IN, body="lương của tôi tháng này bao nhiêu", action="hoi"),
            AgentMessage(chat_id="8001", direction=DIR_OUT, body="Dạ của anh là 25.111.222 đồng ZZMOC1", action=ACT_ANSWER),
            AgentMessage(chat_id="8001", direction=DIR_IN, body="còn khoản kia thì sao ZZMOC2", action="hoi"),
            AgentMessage(chat_id="8001", direction=DIR_OUT, body="Khoản kia là 1.222.333 đồng ZZMOC2", action=ACT_ANSWER),
            AgentMessage(chat_id="8001", direction=DIR_IN, body="giá thép ZZMOC3 hôm nay", action="hoi")]
    db.add_all(rows)
    db.flush()
    #  Lượt 2 gọi my_salary nhưng câu trả lời KHÔNG có chữ lương — chỉ nhãn ở sổ ý định mới bắt được.
    db.add(AgentIntent(user_id=seed.u_req_id, scope_key="8001", message_id=rows[2].id, tools=["my_salary"]))
    db.commit()


def test_lich_su_chat_qua_mcp_khong_tra_luot_luong(db, seed, monkeypatch):
    from types import SimpleNamespace

    from app.modules.agent_hub import mcp, mcp_keys, mcp_log

    monkeypatch.setattr(mcp_log, "_redis", lambda: (_ for _ in ()).throw(ConnectionError("không Redis")))
    monkeypatch.setattr(mcp_log, "_mem", {})
    _history_world(db, seed)
    user = db.get(User, seed.u_req_id)
    msg = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
           "params": {"name": "search_chat_history", "arguments": {"query": "ZZMOC1 ZZMOC2 ZZMOC3", "days": 30}}}
    out = mcp.handle(db, user, SimpleNamespace(id=757, scope=mcp_keys.SCOPE_READ), msg, {})
    text = str(out)
    assert "ZZMOC3" in text                                    # tin thường vẫn tìm được
    _absent(text, MY_SALARY, MY_ALLOWANCE)
    assert "ZZMOC1" not in text and "ZZMOC2" not in text and "lương của tôi" not in text
    #  Ở chat riêng (web) thì chính chủ vẫn tìm lại được.
    mine = _run(db, user, "search_chat_history", {"query": "ZZMOC1 ZZMOC2", "days": 30})
    assert "25.111.222" in str(mine) and "1.222.333" in str(mine)


def test_ghi_chu_co_chu_luong_khong_ra_kenh_chung(db, seed, monkeypatch):
    from app.modules.agent_hub import personal_memory as pm

    hits = [{"note_id": 1, "title": "Lương", "text": "phụ cấp 1.222.333"}, {"note_id": 2, "title": "Thép", "text": "giá"}]
    monkeypatch.setattr(pm, "search_notes", lambda db_, uid, q: [dict(h) for h in hits])
    user = db.get(User, seed.u_req_id)
    assert [n["note_id"] for n in _run(db, user, "search_notes", {"query": "x"}, AI_CHANNEL_MCP)["notes"]] == [2]
    assert len(_run(db, user, "search_notes", {"query": "x"})["notes"]) == 2


def test_so_nho_khong_tu_rut_luong_va_bo_loc_khong_nham_luong_duyet():
    from app.modules.agent_hub import personal_memory as pm
    from app.modules.assistant import tool_router

    assert pm.is_secret("lương em tháng này 20 triệu") and pm.is_secret("phụ cấp xăng 1tr")
    assert not pm.is_secret("luồng duyệt YCMH có 2 bước")
    assert sp.mentions_salary("Luong cua toi bao nhieu") and not sp.mentions_salary("luồng duyệt phiếu thanh toán")
    assert "salary" in tool_router.groups_for("lương của tôi bao nhiêu")
    assert "salary" not in tool_router.groups_for("luồng duyệt YCTT thế nào")


def test_mo_ta_cong_cu_chu_tu_do_va_mcp_co_luat_luong():
    from app.modules.agent_hub import mcp
    from app.modules.assistant.tools import (document_tool, google_tool, group_tool, leave_encashment_tool,
                                             personal_tool)

    assert sp.POLICY_SENTENCE in mcp.INSTRUCTIONS
    for spec in (document_tool.DOCUMENT_READ_SPEC, google_tool.DRIVE_READ_SPEC, group_tool.READ_GROUP_MESSAGES_SPEC,
                 group_tool.READ_GROUP_FILE_SPEC, personal_tool.SEARCH_CHAT_HISTORY_SPEC):
        assert sp.POLICY_SENTENCE in spec.description, spec.name
    import inspect
    assert '"decision_note"' not in inspect.getsource(leave_encashment_tool.my_encashments)


def test_loi_dan_va_cam_nang_co_cau_chinh_sach():
    from app.modules.agent_hub import core_v2
    from app.modules.agent_hub.core_eval_samples import SAMPLES
    from app.modules.assistant import service

    assert sp.POLICY_SENTENCE == "Thông tin lương là dữ liệu riêng tư, chỉ chính nhân sự đó mới xem được."
    assert sp.POLICY_SENTENCE in service.TOOL_GUIDE.replace("\n  ", " ")
    assert POLICY in core_v2.CORE_RULES
    assert {s.id for s in SAMPLES if POLICY in " ".join(s.turns[0].contains)} == {"21", "22"}
