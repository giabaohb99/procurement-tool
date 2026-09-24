"""Agent Hub bậc 1 — canh mấy chỗ hỏng thì hỏng im lặng.

Không kiểm phần gọi Gemini hay gọi Telegram (đó là mạng, không phải logic). Kiểm đúng
bốn chốt mà sai thì không ai thấy cho tới lúc muộn:
  1. `is_allowed_chat` — hàng rào DUY NHẤT của bậc 1.
  2. `_clean_groups` — model bịa id thì task trỏ vào hư không, tin thật kẹt INBOX.
  3. `parse_json` — model bọc rào ```json, và phải NÉM khi không ra JSON (luật B1).
  4. `needs_clarification` — `plan_files` rỗng là CẤM đi tiếp (luật B2).
"""
import pytest

from app.core.config import settings
from app.modules.agent_hub import telegram
from app.modules.agent_hub.constants import estimate_cost_usd
from app.modules.agent_hub.manager import _clean_groups, parse_json
from app.modules.assistant.provider.base import ProviderError


# --- Hàng rào chat_id -------------------------------------------------------
def test_chat_la_bi_chan(monkeypatch):
    monkeypatch.setattr(settings, "AGENT_TELEGRAM_CHAT_ID", "12345")
    assert telegram.is_allowed_chat("12345")
    assert telegram.is_allowed_chat(12345)      # Telegram trả số, config là chuỗi
    assert not telegram.is_allowed_chat("999")


def test_chua_khai_chat_id_la_chan_het(monkeypatch):
    """Chưa cấu hình = CHẶN, không phải cho tất cả. Đảo chiều là mở cửa cho người lạ."""
    monkeypatch.setattr(settings, "AGENT_TELEGRAM_CHAT_ID", "")
    assert not telegram.is_allowed_chat("12345")
    assert not telegram.is_allowed_chat("")


# --- Lọc kết quả gom --------------------------------------------------------
def test_bo_id_model_bia_ra():
    groups = _clean_groups(
        [{"title": "A", "summary": "s", "message_ids": [1, 777], "risk_level": 3}],
        {1, 2},
    )
    #  777 bị loại; 2 bị model bỏ quên nên rơi vào việc "chưa phân loại".
    assert groups[0]["message_ids"] == [1]
    assert groups[0]["risk_level"] == 3
    assert groups[-1]["message_ids"] == [2]


def test_khong_tin_nao_bi_bo_lai_inbox():
    """Mọi id vào phải ra đúng một lần — không thì tin kẹt INBOX vĩnh viễn."""
    groups = _clean_groups([], {1, 2, 3})
    got = [i for g in groups for i in g["message_ids"]]
    assert sorted(got) == [1, 2, 3]


def test_id_trung_o_hai_nhom_chi_tinh_mot_lan():
    """Một tin thuộc hai task = hai thẻ Telegram cho cùng một việc."""
    groups = _clean_groups(
        [{"title": "A", "summary": "", "message_ids": [1, 2], "risk_level": 2},
         {"title": "B", "summary": "", "message_ids": [2], "risk_level": 2}],
        {1, 2},
    )
    assert len(groups) == 1
    assert groups[0]["message_ids"] == [1, 2]


def test_muc_rui_ro_la_thi_ve_vua():
    g = _clean_groups([{"title": "A", "summary": "", "message_ids": [1],
                        "risk_level": "cao"}], {1})
    assert g[0]["risk_level"] == 2


# --- Bóc JSON ---------------------------------------------------------------
def test_boc_duoc_json_trong_rao_va_co_cau_dan():
    assert parse_json('Đây là kết quả:\n```json\n{"groups": []}\n```')["groups"] == []
    assert parse_json('{"a": 1}')["a"] == 1


def test_khong_ra_json_thi_nem_loi():
    """Luật B1 — không đoán tiếp từ văn xuôi."""
    with pytest.raises(ProviderError):
        parse_json("Xin lỗi, tôi không hiểu yêu cầu.")
    with pytest.raises(ProviderError):
        parse_json('[1, 2, 3]')   # JSON hợp lệ nhưng không phải object


# --- Ước chi phí ------------------------------------------------------------
def test_uoc_chi_phi_va_model_la_tra_khong():
    # 1 triệu token vào + 1 triệu ra của gemini-flash-latest = 0.30 + 2.50
    assert estimate_cost_usd("gemini-flash-latest", 1_000_000, 1_000_000) == 2.80
    assert estimate_cost_usd("gemini-flash-latest-002", 1_000_000, 0) == 0.30  # khớp tiền tố
    #  Model lạ trả 0 chứ không đoán — thà 0 rõ ràng còn hơn một con số có người tin.
    assert estimate_cost_usd("model-la-hoac", 1_000_000, 1_000_000) == 0.0


# --- Rẽ tin chữ thường: hỏi hay giao việc (ai-CR-003) -----------------------
def _msg(text: str) -> dict:
    return {"chat": {"id": "12345"}, "message_id": 7, "text": text}


@pytest.fixture
def bot(monkeypatch):
    """Cắm bot vào chỗ trống: chặn mọi lượt gọi mạng, ghi lại thứ bot định gửi."""
    from app.modules.agent_hub import service

    monkeypatch.setattr(settings, "AGENT_TELEGRAM_CHAT_ID", "12345")
    #  Bài kiểm KHÔNG được đẩy việc vào hàng đợi thật: container bot bật AGENT_CODER_ENABLED, và
    #  ngày 23/09 một bài gom việc đã gửi `agent.scan_task` thật sang Redis của runner (ai-CR-017).
    #  Cờ runner tắt mặc định; mọi lệnh giao runner chỉ được ghi lại. Bài nào cần thì tự đè lại.
    from app.modules.agent_hub import coder as _coder

    monkeypatch.setattr(settings, "AGENT_CODER_ENABLED", False)
    #  Bài cũ viết cho thẻ có nút; chế độ gọn (ai-CR-027) bật riêng trong bài mới.
    monkeypatch.setattr(settings, "AGENT_TG_COMPACT", False)
    for name in ("dispatch", "dispatch_scan", "dispatch_publish", "dispatch_question", "dispatch_continue", "dispatch_fix_gate",
                 "dispatch_deploy", "dispatch_revert", "dispatch_cleanup"):
        monkeypatch.setattr(_coder, name, lambda *a, **kw: None)
    sent: list[str] = []
    asked: list[str] = []
    typing: list[str] = []
    monkeypatch.setattr(service.telegram, "send", lambda text, **kw: sent.append(text) or 1)
    monkeypatch.setattr(service.telegram, "send_chat_action",
                        lambda chat_id="", action="typing": typing.append(chat_id))
    monkeypatch.setattr(service, "answer_question",
                        lambda db, chat_id, q, **kw: asked.append(q))
    service._typing_log = typing  # bài kiểm ai-CR-008 đọc qua đây
    return service, sent, asked


def _fake_intent(monkeypatch, service, intent: str):
    from app.modules.assistant.provider.base import ChatResult

    ket_qua = ChatResult(text="", provider="agent_gemini", model="x",
                         input_tokens=0, output_tokens=0)
    monkeypatch.setattr(service.manager, "run_intent",
                        lambda text, **kw: ({"intent": intent, "reason": ""}, ket_qua))


def test_hoi_khong_can_go_tien_to(db, bot, monkeypatch):
    """Đại ca nhắn chữ thường mà là câu hỏi thì được trả lời ngay, không cần `/hoi`."""
    service, _sent, asked = bot
    _fake_intent(monkeypatch, service, "hoi")

    service.handle_message(db, _msg("3 đơn mua hàng gần nhất"))

    assert asked == ["3 đơn mua hàng gần nhất"]
    row = db.query(service.AgentMessage).one()
    #  Đóng dấu = rút khỏi INBOX. Quên là câu hỏi vừa được trả lời lại thành một đầu việc.
    assert row.action == "hoi"


def test_giao_viec_van_nam_lai_inbox(db, bot, monkeypatch):
    service, _sent, asked = bot
    _fake_intent(monkeypatch, service, "viec")

    service.handle_message(db, _msg("cho thêm cột ngày giao vào bảng đơn hàng"))

    assert asked == []
    assert db.query(service.AgentMessage).filter_by(direction=service.DIR_IN).one().action == ""
    #  ai-CR-021: kèm một câu báo nhận (dấu riêng, không phải lượt hội thoại).
    assert db.query(service.AgentMessage).filter_by(direction=service.DIR_OUT).one().action == \
        service.ACT_ACK


def test_map_mo_thi_hoi_lai_chu_khong_doan(db, bot, monkeypatch):
    service, sent, asked = bot
    _fake_intent(monkeypatch, service, "mo_ho")

    service.handle_message(db, _msg("xem lại giúp anh"))

    assert asked == []
    assert len(sent) == 1
    assert db.query(service.AgentMessage).filter_by(direction=2).first().action == "cho_y"


def test_phan_loai_hong_thi_hoi_lai_chu_khong_thanh_viec(db, bot, monkeypatch):
    """Gemini chết (429) thì hỏi lại kèm hai nút — tin không bốc hơi, cũng không tự thành việc.

    Bản trước rơi về giao việc: một câu hỏi gặp lúc hết hạn mức là 90 giây sau có
    một thẻ việc sửa mã. Đó là một nửa nguyên nhân của ca AI-0004.
    """
    service, sent, asked = bot

    def no(text, **kw):
        raise ProviderError("hết hạn mức")

    monkeypatch.setattr(service.manager, "run_intent", no)
    service.handle_message(db, _msg("sửa giúp anh chỗ này"))

    assert asked == []
    assert len(sent) == 1
    assert db.query(service.AgentMessage).filter_by(direction=2).one().action == "cho_y"


def test_lenh_khong_bao_gio_thanh_viec(db, bot, monkeypatch):
    """`/start` từng bị vòng gom đẻ ra task "Xử lý tin nhắn lệnh /start"."""
    service, sent, _asked = bot
    monkeypatch.setattr(service.manager, "run_intent",
                        lambda text, **kw: pytest.fail("lệnh không được tốn một lượt gọi model"))

    service.handle_message(db, _msg("/start"))

    assert db.query(service.AgentMessage).filter_by(direction=2).first().action == "lenh"
    assert len(sent) == 1


def test_gom_viec_ra_thang_ke_hoach(db, bot, monkeypatch):
    """Gom xong phải ra PHƯƠNG ÁN để duyệt luôn.

    Trước đây gom xong chỉ gửi một tấm thẻ nhai lại lời đại ca kèm nút "Lập kế hoạch".
    Đại ca quan tâm thông tin, không quan tâm thủ tục bấm nút.
    """
    from app.modules.assistant.provider.base import ChatResult

    service, _sent, _asked = bot
    ket_qua = ChatResult(text="", provider="agent_gemini", model="x",
                         input_tokens=0, output_tokens=0)
    cards: list[tuple[str, list]] = []
    monkeypatch.setattr(service.telegram, "send",
                        lambda text, **kw: cards.append((text, kw.get("buttons") or [])) or 1)

    row = service.log_message(db, service.DIR_IN, "12345", 9, "thêm cột ngày giao")
    db.commit()
    monkeypatch.setattr(service.manager, "run_triage", lambda msgs: (
        {"groups": [{"title": "Thêm cột ngày giao", "summary": "Bảng đơn hàng thiếu cột",
                     "risk_level": 1, "message_ids": [row.id]}]}, ket_qua))
    monkeypatch.setattr(service.memory, "recall", lambda text: [])
    monkeypatch.setattr(service.manager, "run_plan", lambda title, summary, docs, **kw: (
        {"plan": "Thêm cột rồi viết migration", "plan_files": ["backend/app/x.py"],
         "test_plan": "", "related_docs": [], "questions": [], "risk_level": 1,
         "needs_clarification": False}, ket_qua))

    assert service.triage_inbox(db, force=True) == 1

    nhan = [b[0] for _text, buttons in cards for b in buttons]
    assert "Lập kế hoạch" not in nhan
    assert nhan == ["Duyệt", "Sửa lại", "Bỏ việc này"]
    assert len(cards) == 1


# --- Nối mạch: bot vừa hỏi lại thì tin kế là câu trả lời (ai-CR-007) ----------
def _cuoc_hoi_dap(service, db, bot_reply: str):
    """Một lượt Trợ lý AI đã hỏi lại. Trả về id tin bot gửi."""
    service.log_message(db, service.DIR_IN, "12345", 1, "tạo đơn nghỉ phép cho anh", action="hoi")
    out = service.log_message(db, service.DIR_OUT, "12345", 2, bot_reply, action="tra_loi")
    db.commit()
    return out


def test_bot_vua_hoi_lai_thi_tin_ke_la_cau_tra_loi(db, bot, monkeypatch):
    """Ca AI-0004: Trợ lý hỏi ngày/lý do, đại ca đáp, câu đáp KHÔNG được thành việc sửa mã.

    Nối thẳng, không tốn lượt phân loại — nên cũng không phụ thuộc Gemini còn hạn mức.
    """
    service, _sent, asked = bot
    _cuoc_hoi_dap(service, db, "Anh muốn nghỉ ngày nào và lý do gì?")
    monkeypatch.setattr(service.manager, "run_intent",
                        lambda text, **kw: pytest.fail("đang trả lời bot thì không phân loại"))

    service.handle_message(db, _msg("cho anh nghỉ vào thứ 6 tuần này, lý do là đi du lịch"))

    assert asked == ["cho anh nghỉ vào thứ 6 tuần này, lý do là đi du lịch"]
    moi = db.query(service.AgentMessage).filter_by(tg_message_id=7).one()
    assert moi.action == "hoi"


def test_bot_hoi_lai_qua_lau_thi_la_chuyen_moi(db, bot, monkeypatch):
    """Câu hỏi của bot từ nửa tiếng trước không còn 'đang chờ' — tin mới phải đi phân loại."""
    from datetime import datetime, timedelta

    service, _sent, asked = bot
    out = _cuoc_hoi_dap(service, db, "Anh muốn nghỉ ngày nào?")
    out.created_at = datetime.now() - timedelta(minutes=30)
    db.commit()
    _fake_intent(monkeypatch, service, "viec")

    service.handle_message(db, _msg("màn đơn hàng không lọc được theo ngày"))

    assert asked == []
    assert db.query(service.AgentMessage).filter_by(tg_message_id=7).one().action == ""


def test_bot_tra_loi_xuoi_thi_van_phan_loai_nhung_kem_mach(db, bot, monkeypatch):
    """Bot trả lời xuôi (không hỏi) thì tin kế vẫn phân loại, nhưng model được đọc mạch trước đó."""
    from app.modules.assistant.provider.base import ChatResult

    service, _sent, asked = bot
    _cuoc_hoi_dap(service, db, "Đã tạo đơn NP012 cho anh.")
    seen: dict = {}

    def phan_loai(text, **kw):
        seen["context"] = kw.get("context")
        return ({"intent": "hoi", "reason": ""},
                ChatResult(text="", provider="agent_gemini", model="x",
                           input_tokens=0, output_tokens=0))

    monkeypatch.setattr(service.manager, "run_intent", phan_loai)
    service.handle_message(db, _msg("còn bao nhiêu ngày phép?"))

    assert asked == ["còn bao nhiêu ngày phép?"]
    assert seen["context"] == ("Người dùng: tạo đơn nghỉ phép cho anh\n"
                               "Bot: Đã tạo đơn NP012 cho anh.")


# --- Như Trợ lý AI trên web, nhưng ở Telegram (ai-CR-006) -------------------
def test_markdown_ra_html_telegram(monkeypatch):
    """Web render Markdown; Telegram in thô `**[X](/y)**`. Bộ đổi phải ra đúng năm thẻ."""
    monkeypatch.setattr(settings, "FRONTEND_URL", "https://erp.test")
    got = telegram.md_to_html(
        "### Ba đơn\n"
        "1. **[PO-01](/procurement/purchase-orders/372)** — 1.350.000 đ & *chờ*\n"
        "- xem `ma_x` rồi _nhấn_ plan_files\n"
        "| Mã | Tên |\n|---|---|\n| PO1 | Bao <x> |\n"
        "```sql\nselect 1\n```"
    )
    assert got.splitlines() == [
        "<b>Ba đơn</b>",
        '1. <b><a href="https://erp.test/procurement/purchase-orders/372">PO-01</a></b> '
        "— 1.350.000 đ &amp; <i>chờ</i>",
        "• xem <code>ma_x</code> rồi <i>nhấn</i> plan_files",
        "Mã · Tên",
        "PO1 · Bao &lt;x&gt;",
        "<pre>select 1</pre>",
    ]


def test_mach_hoi_thoai_chi_lay_hoi_va_tra_loi(db, bot):
    """Lệnh, nút bấm, thẻ việc không phải hội thoại — chỉ cặp hỏi/trả lời đi vào history."""
    service, _sent, _asked = bot
    L = service.log_message
    L(db, service.DIR_IN, "12345", 1, "/ds", action="lenh")
    L(db, service.DIR_IN, "12345", 2, "3 đơn gần nhất", action="hoi")
    L(db, service.DIR_OUT, "12345", 3, "**PO-01**, PO-02", action="tra_loi")
    L(db, service.DIR_OUT, "12345", 4, "Thẻ việc AI-0001")          # thẻ task
    L(db, service.DIR_IN, "999", 5, "câu hỏi chat khác", action="hoi")
    hien_tai = L(db, service.DIR_IN, "12345", 6, "còn đơn nào chờ duyệt?", action="hoi")
    db.commit()

    turns = service._recent_turns(db, "12345", hien_tai.id)

    assert turns == [{"role": "user", "content": "3 đơn gần nhất"},
                     {"role": "assistant", "content": "**PO-01**, PO-02"}]


def test_tra_loi_gui_html_nhung_so_giu_markdown(db, monkeypatch):
    """Sổ giữ Markdown gốc để lượt sau đưa lại cho model đúng như web; dây gửi là HTML."""
    from app.modules.agent_hub import service
    from app.modules.assistant import service as assistant_service
    from app.modules.user.model import User

    #  Không dùng fixture `bot`: nó thay luôn `answer_question`, mà đây là bài kiểm chính nó.
    sent: list[str] = []
    monkeypatch.setattr(service.telegram, "send", lambda text, **kw: sent.append(text) or 1)
    monkeypatch.setattr(settings, "AGENT_ASSISTANT_USER", "BOT01")
    db.add(User(email="BOT01", employee_id=0, password_hash="x", is_active=True))
    db.commit()
    seen: dict = {}

    def fake_ask(message, *, db, user, history=None, **kw):
        seen["history"] = history
        return {"text": "**Hai** đơn"}

    monkeypatch.setattr(assistant_service, "ask", fake_ask)
    cu = service.log_message(db, service.DIR_IN, "12345", 1, "câu trước", action="hoi")
    service.log_message(db, service.DIR_OUT, "12345", 2, "đáp trước", action="tra_loi")
    moi = service.log_message(db, service.DIR_IN, "12345", 3, "câu mới", action="hoi")

    service.answer_question(db, "12345", "câu mới", before_id=moi.id)

    assert seen["history"] == [{"role": "user", "content": "câu trước"},
                               {"role": "assistant", "content": "đáp trước"}]
    assert sent == ["<b>Hai</b> đơn"]
    out = db.query(service.AgentMessage).filter_by(direction=1, tg_message_id=1).one()
    assert (out.body, out.action) == ("**Hai** đơn", "tra_loi")
    assert cu.id < moi.id


def test_con_tro_khong_troi_khi_tool_rollback(db, bot, monkeypatch):
    """bao-CR-463: sổ audit của tool rollback cả phiên -> con trỏ trôi -> trả lời bốn lần.

    Nay con trỏ và tin vào phải được chốt TRƯỚC khi gọi model, nên một cú rollback
    giữa chừng không kéo chúng đi.
    """
    service, _sent, _asked = bot
    monkeypatch.setattr(service.telegram, "fetch_updates",
                        lambda offset, **kw: [{"update_id": 41, "message": _msg("3 đơn gần nhất")}])

    def rollback_roi_chet(text):
        db.rollback()
        raise ProviderError("tool làm hỏng phiên")

    monkeypatch.setattr(service.manager, "run_intent", rollback_roi_chet)

    assert service.poll_once(db) == 1
    db.expire_all()
    assert service.get_cursor(db).value == 42
    assert db.query(service.AgentMessage).filter_by(direction=2).count() == 1


# --- Bot chậm: giữ kết nối chờ tin + báo đang soạn (ai-CR-008) -----------------
def test_nhan_tin_la_bao_dang_soan_truoc_khi_hoi_model(db, bot, monkeypatch):
    """Đại ca phải thấy "đang soạn tin..." NGAY khi bot nhận tin, trước lượt phân loại."""
    service, _sent, asked = bot
    thu_tu: list[str] = []
    monkeypatch.setattr(service.telegram, "send_chat_action",
                        lambda chat_id="", action="typing": thu_tu.append("typing"))

    def phan_loai(text, **kw):
        thu_tu.append("intent")
        from app.modules.assistant.provider.base import ChatResult
        return ({"intent": "hoi", "reason": ""},
                ChatResult(text="", provider="agent_gemini", model="x",
                           input_tokens=0, output_tokens=0))

    monkeypatch.setattr(service.manager, "run_intent", phan_loai)
    service.handle_message(db, _msg("3 đơn gần nhất"))
    assert thu_tu == ["typing", "intent"]
    assert asked == ["3 đơn gần nhất"]


def test_chat_la_thi_khong_bao_dang_soan(db, bot):
    """Người lạ nhắn thì im hẳn — kể cả cái nhấp nháy "đang soạn" cũng là xác nhận bot sống."""
    service, sent, _asked = bot
    service.handle_message(db, {"chat": {"id": "999"}, "message_id": 1, "text": "hi"})
    assert service._typing_log == []
    assert sent == []


def test_fetch_updates_giu_ket_noi_va_cho_http_lau_hon(monkeypatch):
    """Giữ kết nối n giây thì trần HTTP phải > n, không thì `requests` tự cắt trước Telegram."""
    monkeypatch.setattr(settings, "AGENT_TELEGRAM_BOT_TOKEN", "x")
    goi: list[dict] = []

    class _Resp:
        status_code = 200

        @staticmethod
        def json():
            return {"ok": True, "result": []}

    monkeypatch.setattr(telegram.requests, "post",
                        lambda url, json, timeout: goi.append({**json, "_http": timeout}) or _Resp())
    telegram.fetch_updates(7, timeout=telegram.LONG_POLL_TIMEOUT)
    telegram.fetch_updates(7)
    assert goi[0]["timeout"] == telegram.LONG_POLL_TIMEOUT
    assert goi[0]["_http"] > telegram.LONG_POLL_TIMEOUT
    assert goi[1]["timeout"] == 0  # vòng beat cũ vẫn hỏi-rồi-về


def test_poller_giu_ket_noi_va_khong_chet_khi_mot_luot_hong(monkeypatch):
    """Poller: kéo bằng LONG_POLL_TIMEOUT, một lượt hỏng thì rollback + nghỉ ngắn rồi kéo tiếp."""
    from unittest.mock import MagicMock

    from app.modules.agent_hub import poller, service

    monkeypatch.setattr(telegram, "is_enabled", lambda: True)
    luot: list[int] = []
    ngu: list[float] = []

    def keo(db, *, timeout):
        luot.append(timeout)
        if len(luot) == 1:
            raise RuntimeError("Telegram sập")
        return 0

    monkeypatch.setattr(service, "poll_once", keo)
    phien = MagicMock()
    n = poller.run(session_factory=lambda: phien, should_stop=lambda: len(luot) >= 2,
                   sleep=ngu.append)
    assert n == 2
    assert luot == [telegram.LONG_POLL_TIMEOUT] * 2
    assert phien.rollback.call_count == 1
    assert phien.commit.call_count == 1
    assert phien.close.call_count == 2
    assert ngu == [poller.ERROR_SLEEP]


def test_poller_cau_dao_tat_thi_ngu_khong_mo_phien(monkeypatch):
    from app.modules.agent_hub import poller

    monkeypatch.setattr(telegram, "is_enabled", lambda: False)
    ngu: list[float] = []
    mo_phien: list[int] = []
    poller.run(session_factory=lambda: mo_phien.append(1), should_stop=lambda: len(ngu) >= 1,
               sleep=ngu.append)
    assert ngu == [poller.IDLE_SLEEP]
    assert mo_phien == []


def test_vong_beat_nhuong_khi_co_poller(monkeypatch):
    """Hai bên cùng đọc một con trỏ là xử trùng một tin: có poller thì việc beat phải rỗng."""
    from app.modules.agent_hub import tasks

    monkeypatch.setattr(settings, "AGENT_HUB_ENABLED", True)
    monkeypatch.setattr(settings, "AGENT_TELEGRAM_BOT_TOKEN", "x")
    monkeypatch.setattr(settings, "AGENT_TELEGRAM_CHAT_ID", "12345")
    monkeypatch.setattr(settings, "AGENT_LONG_POLL", True)
    monkeypatch.setattr(tasks, "SessionLocal", lambda: pytest.fail("không được mở phiên DB"))
    assert tasks.poll_telegram_task()["status"] == "skipped"


# --- Kết quả tool của Trợ lý AI ra Telegram (ai-CR-009) ----------------------
def _bot_user(db, monkeypatch):
    from app.modules.user.model import User

    monkeypatch.setattr(settings, "AGENT_ASSISTANT_USER", "BOT01")
    u = User(email="BOT01", employee_id=0, password_hash="x", is_active=True)
    db.add(u)
    db.commit()
    return u


def _ask_returning(monkeypatch, tool_calls):
    from app.modules.assistant import service as assistant_service

    monkeypatch.setattr(assistant_service, "ask",
                        lambda message, **kw: {"text": "Xong", "tool_calls": tool_calls})


def _report_file(db, owner_id: int):
    from app.modules.attachment.model import StoredFile

    f = StoredFile(filename="bao-cao.xlsx", file_key="2026/09/assistant-report/1_bao-cao.xlsx",
                   content_type="application/vnd.ms-excel", size=3, created_by=owner_id)
    db.add(f)
    db.commit()
    return f


def test_tool_xuat_tep_thi_bot_gui_tep_dinh_kem(db, monkeypatch):
    """Web có nút «Tải báo cáo» cần Bearer; Telegram không đăng nhập được nên phải đẩy tệp."""
    import app.core.storage as storage
    from app.modules.agent_hub import service

    u = _bot_user(db, monkeypatch)
    f = _report_file(db, u.id)
    sent: list[str] = []
    docs: list[tuple] = []
    monkeypatch.setattr(service.telegram, "send", lambda text, **kw: sent.append(text) or 1)
    monkeypatch.setattr(service.telegram, "send_chat_action", lambda *a, **kw: None)
    monkeypatch.setattr(service.telegram, "send_document",
                        lambda chat_id, filename, data, **kw: docs.append((filename, data)) or 9)
    monkeypatch.setattr(storage, "download_bytes", lambda key: b"abc" if key == f.file_key else b"")
    _ask_returning(monkeypatch, [{"name": "export_report_file", "file": {
        "id": f.id, "filename": f.filename, "size": 3,
        "download_url": f"/api/assistant/files/{f.id}/download"}}])

    service.answer_question(db, "12345", "xuất báo cáo")

    assert sent == ["Xong"]
    assert docs == [("bao-cao.xlsx", b"abc")]
    row = db.query(service.AgentMessage).filter_by(action="tep").one()
    assert (row.direction, row.tg_message_id) == (service.DIR_OUT, 9)


def test_tep_khong_phai_cua_tai_khoan_bot_thi_khong_gui(db, monkeypatch):
    """Chốt sở hữu chép đúng endpoint tải web: khối `file` bịa id không thành lối tải kho."""
    from app.modules.agent_hub import service

    u = _bot_user(db, monkeypatch)
    f = _report_file(db, u.id + 100)
    sent: list[str] = []
    monkeypatch.setattr(service.telegram, "send", lambda text, **kw: sent.append(text) or 1)
    monkeypatch.setattr(service.telegram, "send_chat_action", lambda *a, **kw: None)
    monkeypatch.setattr(service.telegram, "send_document",
                        lambda *a, **kw: pytest.fail("không được gửi tệp của người khác"))
    _ask_returning(monkeypatch, [{"name": "export_report_file",
                                  "file": {"id": f.id, "filename": f.filename}}])

    service.answer_question(db, "12345", "xuất báo cáo")

    assert len(sent) == 2 and "không tìm thấy" in sent[1]
    assert db.query(service.AgentMessage).filter_by(action="tep").count() == 0


def test_de_xuat_sua_phieu_thanh_the_hai_nut_va_so_giu_token(db, monkeypatch):
    """Token dài hơn 64 byte của `callback_data`, nên nút mang id dòng sổ, sổ giữ khối đề xuất."""
    import json

    from app.modules.agent_hub import service

    _bot_user(db, monkeypatch)
    cards: list[tuple[str, list]] = []
    monkeypatch.setattr(service.telegram, "send",
                        lambda text, **kw: cards.append((text, kw.get("buttons") or [])) or 5)
    monkeypatch.setattr(service.telegram, "send_chat_action", lambda *a, **kw: None)
    token = "t" * 200
    _ask_returning(monkeypatch, [{"name": "propose_document_update", "proposal": {
        "kind": "update_proposal", "entity": "purchase_request", "entity_label": "Yêu cầu mua hàng",
        "code": "PR001", "doc_status_label": "Nháp",
        "changes": [{"field": "note", "label": "Ghi chú", "old": "cũ", "new": "mới"}],
        "confirm_token": token, "url": "/procurement/purchase-requests/1"}}])

    service.answer_question(db, "12345", "đổi ghi chú PR001 thành mới")

    row = db.query(service.AgentMessage).filter_by(action="de_xuat").one()
    assert cards[1][1] == [("Xác nhận sửa", f"sua:{row.id}"), ("Không sửa", f"khong_sua:{row.id}")]
    assert all(len(data.encode()) <= 64 for _, data in cards[1][1])
    assert "<s>cũ</s> → <b>mới</b>" in cards[1][0] and "PR001" in cards[1][0]
    assert json.loads(row.body)["confirm_token"] == token
    assert row.tg_message_id == 5


def _callback(data: str) -> dict:
    return {"id": "cb1", "data": data, "message": {"chat": {"id": "12345"}, "message_id": 5}}


def _proposal_row(db, service, token="tk"):
    import json

    row = service.log_message(db, service.DIR_OUT, "12345", 5, json.dumps(
        {"entity": "purchase_request", "code": "PR001", "confirm_token": token}),
        action="de_xuat")
    db.commit()
    return row


def test_bam_xac_nhan_thi_ghi_phieu_bang_dung_token_va_khong_bam_lai_duoc(db, bot, monkeypatch):
    """Ghi phiếu đi qua ĐÚNG `confirm_update` của web; bấm lần hai không ghi lần hai."""
    from app.modules.assistant.tools import update_tool

    service, sent, _asked = bot
    u = _bot_user(db, monkeypatch)
    row = _proposal_row(db, service, token="tk-123")
    calls: list[tuple] = []
    toasts: list[str] = []

    def fake_confirm(db_, user, token):
        calls.append((user.id, token))
        return {"entity": "purchase_request", "entity_label": "Yêu cầu mua hàng", "code": "PR001",
                "updated_fields": ["Ghi chú"], "url": "/procurement/purchase-requests/1"}

    monkeypatch.setattr(update_tool, "confirm_update", fake_confirm)
    monkeypatch.setattr(service.telegram, "answer_callback", lambda cb, text="": toasts.append(text))
    monkeypatch.setattr(service.telegram, "clear_buttons", lambda *a, **kw: None)

    service.handle_callback(db, _callback(f"sua:{row.id}"))
    service.handle_callback(db, _callback(f"sua:{row.id}"))

    assert calls == [(u.id, "tk-123")]
    assert db.get(service.AgentMessage, row.id).action == "da_sua"
    assert toasts == ["Đã sửa", "Đề xuất này đã xử rồi"]
    assert len(sent) == 1 and "Đã sửa" in sent[0] and "Ghi chú" in sent[0]


def test_bam_khong_sua_thi_dong_de_xuat_khong_ghi_gi(db, bot, monkeypatch):
    from app.modules.assistant.tools import update_tool

    service, sent, _asked = bot
    _bot_user(db, monkeypatch)
    row = _proposal_row(db, service)
    monkeypatch.setattr(update_tool, "confirm_update",
                        lambda *a, **kw: pytest.fail("bấm Không sửa mà vẫn ghi phiếu"))
    monkeypatch.setattr(service.telegram, "answer_callback", lambda *a, **kw: None)
    monkeypatch.setattr(service.telegram, "clear_buttons", lambda *a, **kw: None)

    service.handle_callback(db, _callback(f"khong_sua:{row.id}"))

    assert db.get(service.AgentMessage, row.id).action == "bo_sua"
    assert len(sent) == 1 and "giữ nguyên" in sent[0]


def test_xac_nhan_het_han_thi_bao_ly_do_va_dong_de_xuat(db, bot, monkeypatch):
    """Token hết hạn / mất quyền: câu lỗi của web phải tới tay đại ca, và thẻ không bấm lại được."""
    from fastapi import HTTPException

    from app.modules.assistant.tools import update_tool

    service, sent, _asked = bot
    _bot_user(db, monkeypatch)
    row = _proposal_row(db, service)

    def het_han(*a, **kw):
        raise HTTPException(400, "Đề xuất sửa đã hết hạn hoặc không hợp lệ")

    monkeypatch.setattr(update_tool, "confirm_update", het_han)
    monkeypatch.setattr(service.telegram, "answer_callback", lambda *a, **kw: None)
    monkeypatch.setattr(service.telegram, "clear_buttons", lambda *a, **kw: None)

    service.handle_callback(db, _callback(f"sua:{row.id}"))

    assert db.get(service.AgentMessage, row.id).action == "bo_sua"
    assert len(sent) == 1 and "hết hạn" in sent[0]


def test_gui_tep_di_duong_multipart_va_chan_tep_qua_nang(monkeypatch):
    """`sendDocument` phải là multipart (JSON không chở được byte); quá 50 MB thì chặn tại chỗ."""
    monkeypatch.setattr(settings, "AGENT_TELEGRAM_BOT_TOKEN", "x")
    got: dict = {}

    class _Resp:
        status_code = 200

        @staticmethod
        def json():
            return {"ok": True, "result": {"message_id": 42}}

    def post(url, **kw):
        got.update(kw)
        return _Resp()

    monkeypatch.setattr(telegram.requests, "post", post)
    assert telegram.send_document("12345", "bao-cao.xlsx", b"abc", caption="<b>x</b>",
                                  content_type="application/vnd.ms-excel") == 42
    assert got["files"]["document"] == ("bao-cao.xlsx", b"abc", "application/vnd.ms-excel")
    assert got["data"]["chat_id"] == "12345" and got["data"]["parse_mode"] == "HTML"
    assert "json" not in got

    with pytest.raises(telegram.TelegramError):
        telegram.send_document("12345", "to.bin", b"0" * (telegram.MAX_DOCUMENT_BYTES + 1))


# ===========================================================================
# ai-CR-011 — bậc 2: bấm Duyệt là bot sửa mã (coder.py + agent-runner)
# ===========================================================================
from datetime import datetime  # noqa: E402
from app.modules.agent_hub.constants import ST_FAILED, ST_REVIEW  # noqa: E402


def _task_with_plan(db, service, plan_files, **kw):
    from app.modules.agent_hub.model import AgentTask

    row = AgentTask(code=service.next_code(db), title="Sửa lỗi lọc nghỉ phép",
                    summary="Lọc theo phòng ban ra sai", plan="Sửa điều kiện lọc",
                    plan_files=plan_files, status=kw.pop("status", service.ST_PLAN), **kw)
    db.add(row)
    db.commit()
    return row


def test_duyet_khi_coder_tat_thi_noi_ro_dang_tat_va_khong_giao(db, bot, monkeypatch):
    """Cờ tắt = bậc 1 nguyên vẹn: việc đứng ở PLAN, không ném gì vào hàng đợi, câu trả lời nói rõ TẮT."""
    from app.modules.agent_hub import coder

    service, sent, _ = bot
    monkeypatch.setattr(settings, "AGENT_CODER_ENABLED", False)
    dispatched: list[int] = []
    monkeypatch.setattr(coder, "dispatch", lambda tid: dispatched.append(tid))
    task = _task_with_plan(db, service, ["backend/app/modules/leave/service.py"])

    service.handle_callback(db, _callback(f"ok:{task.id}"))
    assert task.status == service.ST_PLAN and task.approved_at is not None
    assert dispatched == []
    assert "TẮT" in sent[-1]


def test_duyet_khi_coder_bat_thi_sang_code_va_giao_hang_doi(db, bot, monkeypatch):
    from app.modules.agent_hub import coder

    service, sent, _ = bot
    monkeypatch.setattr(settings, "AGENT_CODER_ENABLED", True)
    dispatched: list[int] = []
    monkeypatch.setattr(coder, "dispatch", lambda tid: dispatched.append(tid))
    task = _task_with_plan(db, service, ["backend/app/modules/leave/service.py"])

    service.handle_callback(db, _callback(f"ok:{task.id}"))
    assert task.status == service.ST_CODE
    assert dispatched == [task.id]
    assert "giao bot sửa mã" in sent[-1]


def test_duyet_ke_hoach_khong_co_pham_vi_tep_thi_khong_giao(db, bot, monkeypatch):
    """Luật B2: plan_files rỗng là chốt chặn, không phải ô chưa điền — việc sang NEEDS_INPUT."""
    from app.modules.agent_hub import coder

    service, sent, _ = bot
    monkeypatch.setattr(settings, "AGENT_CODER_ENABLED", True)
    dispatched: list[int] = []
    monkeypatch.setattr(coder, "dispatch", lambda tid: dispatched.append(tid))
    task = _task_with_plan(db, service, [])

    service.handle_callback(db, _callback(f"ok:{task.id}"))
    assert task.status == service.ST_NEEDS_INPUT
    assert dispatched == []
    assert "phạm vi tệp" in sent[-1]


def test_duyet_ke_hoach_dung_tep_cam_thi_khong_giao(db, bot, monkeypatch):
    from app.modules.agent_hub import coder

    service, sent, _ = bot
    monkeypatch.setattr(settings, "AGENT_CODER_ENABLED", True)
    dispatched: list[int] = []
    monkeypatch.setattr(coder, "dispatch", lambda tid: dispatched.append(tid))
    task = _task_with_plan(db, service, ["backend/migrations/versions/abc_new.py"])

    service.handle_callback(db, _callback(f"ok:{task.id}"))
    assert task.status == service.ST_NEEDS_INPUT and dispatched == []
    assert "cấm" in sent[-1]


def test_giao_hang_doi_hong_thi_tra_ve_plan_chu_khong_treo_o_code(db, bot, monkeypatch):
    from app.modules.agent_hub import coder

    service, sent, _ = bot
    monkeypatch.setattr(settings, "AGENT_CODER_ENABLED", True)

    def boom(tid):
        raise RuntimeError("redis chết")

    monkeypatch.setattr(coder, "dispatch", boom)
    task = _task_with_plan(db, service, ["backend/app/modules/leave/service.py"])
    service.handle_callback(db, _callback(f"ok:{task.id}"))
    assert task.status == service.ST_PLAN
    assert "không giao được" in sent[-1]


def test_tep_cam_so_ca_duong_dan_lan_ten_tep():
    from app.modules.agent_hub import coder

    assert coder.is_banned_path(".env")
    assert coder.is_banned_path("./.env.production")
    assert coder.is_banned_path("backend/migrations/versions/x.py")
    assert coder.is_banned_path("backend/app/core/permissions.py")
    assert coder.is_banned_path("backend/.claude/rules/naming.md")
    assert coder.is_banned_path("docker/certs/server.key")
    assert not coder.is_banned_path("backend/app/modules/leave/service.py")
    assert not coder.is_banned_path("backend/app/core/config.py")
    assert not coder.is_banned_path("environment.md")


def test_lech_ke_hoach_luat_c1():
    from app.modules.agent_hub import coder

    plan = ["backend/app/modules/leave/service.py", "frontend-v2/src/modules/hr/"]
    # đúng kế hoạch + bài kiểm (không tính) -> qua
    assert coder.check_drift(
        ["backend/app/modules/leave/service.py", "test/backend/test_leave_x.py",
         "frontend-v2/src/modules/hr/pages/a.tsx", "frontend-v2/src/modules/hr/a.test.tsx"],
        plan, max_files=25) == ""
    # tệp cấm -> dừng, bất kể tỷ lệ
    assert "cấm" in coder.check_drift(["backend/app/modules/leave/service.py", ".env"], plan, max_files=25)
    # quá trần tệp
    assert "vượt trần" in coder.check_drift([f"backend/a{i}.py" for i in range(30)], plan, max_files=25)
    # 2/3 ngoài kế hoạch (>30%) -> dừng
    assert "ngoài kế hoạch" in coder.check_drift(
        ["backend/app/modules/leave/service.py", "backend/app/x.py", "backend/app/y.py"],
        plan, max_files=25)
    # 1/4 ngoài kế hoạch (25%) -> qua
    assert coder.check_drift(
        ["backend/app/modules/leave/service.py", "frontend-v2/src/modules/hr/a.tsx",
         "frontend-v2/src/modules/hr/b.tsx", "backend/app/x.py"], plan, max_files=25) == ""


def test_moi_truong_cho_claude_sach_va_chi_co_dung_mot_khoa(monkeypatch):
    """Khóa Telegram/Gemini/DB của tiến trình cha KHÔNG được xuống tiến trình `claude`."""
    from app.modules.agent_hub import coder

    monkeypatch.setenv("AGENT_TELEGRAM_BOT_TOKEN", "tg-secret")
    monkeypatch.setenv("AGENT_GEMINI_API_KEY", "gm-secret")
    monkeypatch.setenv("DB_PASSWORD", "db-secret")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-should-not-pass")
    monkeypatch.setenv("CLAUDE_CODE_OAUTH_TOKEN", "oauth-ok")
    env = coder.build_env("/worktrees/AI-0001")
    assert env["CLAUDE_CODE_OAUTH_TOKEN"] == "oauth-ok"
    assert env["PYTHONPATH"].replace("\\", "/").endswith("AI-0001/backend")
    for k in ("AGENT_TELEGRAM_BOT_TOKEN", "AGENT_GEMINI_API_KEY", "DB_PASSWORD", "ANTHROPIC_API_KEY"):
        assert k not in env
    # git/pytest không nhận cả khóa Claude
    assert "CLAUDE_CODE_OAUTH_TOKEN" not in coder.build_env("/worktrees/AI-0001", with_token=False)
    # thiếu khóa thì báo ngay, không spawn
    monkeypatch.delenv("CLAUDE_CODE_OAUTH_TOKEN")
    with pytest.raises(coder.CoderError, match="CLAUDE_CODE_OAUTH_TOKEN"):
        coder.build_env("/worktrees/AI-0001")


def test_boc_json_cua_cli_va_loi_401_thanh_coder_error():
    from app.modules.agent_hub import coder

    ok = coder.parse_cli_json('[claude-code:warn] x\n{"type":"result","subtype":"success",'
                              '"is_error":false,"result":"xong","usage":{"input_tokens":3}}\n')
    assert ok["result"] == "xong"
    with pytest.raises(coder.CoderError, match="setup-token"):
        coder.parse_cli_json('{"type":"result","subtype":"error_during_execution","is_error":true,'
                             '"api_error_status":401,"result":"Not logged in"}')
    with pytest.raises(coder.CoderError, match="không trả JSON"):
        coder.parse_cli_json("segfault")


def _fake_runner(monkeypatch, coder, *, touched, report="## TỔNG KẾT\n1. đã sửa", gate_rc=0):
    """Giả git + claude + pytest: ghi lại mọi lệnh, trả kết quả theo kịch bản."""
    calls: list[list[str]] = []

    def fake_git(cwd, *args, timeout=0, extra_env=None):
        #  `git push` (ai-CR-012) ghi kèm env phụ làm phần tử cuối để bài kiểm soi khóa đi đâu.
        calls.append(["git", *args] + ([extra_env] if extra_env else []))
        if args[:3] == ("diff", "--cached", "--name-only"):
            return "\n".join(touched)
        if args[:3] == ("diff", "--cached", "--numstat"):
            return "\n".join(f"3\t1\t{f}" for f in touched)
        if args[:2] == ("diff", "--cached"):
            return "--- a\n+++ b\n" if touched else ""
        return ""

    monkeypatch.setattr(coder, "_git", fake_git)
    monkeypatch.setattr(coder, "prepare_worktree", lambda task: ("/worktrees/X", "bot/x"))
    monkeypatch.setattr(coder.memory, "recall", lambda q, limit=6: [])
    monkeypatch.setattr(coder, "run_claude", lambda wt, brief, *, session_id, timeout, **kw: {
        "result": report, "num_turns": 7, "duration_ms": 90000, "total_cost_usd": 0.42,
        "usage": {"input_tokens": 100, "output_tokens": 50}, "modelUsage": {"claude-x": {}}})
    monkeypatch.setattr(coder, "run_gate", lambda wt, t, **kw: {
        "status": "pass" if gate_rc == 0 else "fail",
        "tests": [f for f in t if f.startswith("test/")], "output": "1 failed" if gate_rc else ""})
    return calls


def test_luot_sua_ma_tron_ven_ra_the_ket_qua_va_tep_diff(db, bot, monkeypatch):
    from app.modules.agent_hub import coder
    from app.modules.agent_hub.model import AgentRun

    service, sent, _ = bot
    docs: list[tuple] = []
    monkeypatch.setattr(coder.telegram, "send_document",
                        lambda chat_id, fn, data, **kw: docs.append((fn, data)) or 1)
    task = _task_with_plan(db, service, ["backend/app/modules/leave/service.py"],
                           status=service.ST_CODE)
    calls = _fake_runner(monkeypatch, coder, touched=[
        "backend/app/modules/leave/service.py", "test/backend/test_leave_loc.py"])

    out = coder.run_code_task(db, task)
    assert task.status == ST_REVIEW and task.branch_name == "bot/x"
    assert out["escalation"] == ""
    assert any(c[0] == "git" and "commit" in c for c in calls)
    run = db.query(AgentRun).filter_by(task_id=task.id).one()
    assert run.provider == "claude_code" and run.model == "claude-x" and run.status == coder.RUN_OK
    assert run.input_tokens == 100 and run.cost_usd == 0.42
    assert [f["path"] for f in run.artifact["files"]] == [
        "backend/app/modules/leave/service.py", "test/backend/test_leave_loc.py"]
    assert run.artifact["gate"]["status"] == "pass"
    card = sent[-1]
    assert task.code in card and "XANH" in card and "Bot tổng kết" in card and "bot/x" in card
    assert docs and docs[0][0] == f"{task.code}.diff"


def test_lech_ke_hoach_thi_khong_commit_va_hoi_lai(db, bot, monkeypatch):
    from app.modules.agent_hub import coder

    service, sent, _ = bot
    monkeypatch.setattr(coder.telegram, "send_document", lambda *a, **kw: 1)
    task = _task_with_plan(db, service, ["backend/app/modules/leave/service.py"],
                           status=service.ST_CODE)
    calls = _fake_runner(monkeypatch, coder, touched=[
        "backend/app/modules/leave/service.py", "backend/app/a.py", "backend/app/b.py"])

    out = coder.run_code_task(db, task)
    assert task.status == service.ST_NEEDS_INPUT
    assert "ngoài kế hoạch" in out["escalation"] and "ngoài kế hoạch" in task.note
    assert not any("commit" in c for c in calls)
    assert any(c[:2] == ["git", "reset"] for c in calls)
    assert "KHÔNG COMMIT" in sent[-1] and "NGOÀI kế hoạch" in sent[-1]


def test_bot_khong_sua_gi_thi_hoi_lai_chu_khong_bao_xong(db, bot, monkeypatch):
    from app.modules.agent_hub import coder

    service, sent, _ = bot
    sent_docs: list = []
    monkeypatch.setattr(coder.telegram, "send_document", lambda *a, **kw: sent_docs.append(a) or 1)
    task = _task_with_plan(db, service, ["backend/app/x.py"], status=service.ST_CODE)
    _fake_runner(monkeypatch, coder, touched=[], report="Không tái hiện được lỗi")
    coder.run_code_task(db, task)
    assert task.status == service.ST_NEEDS_INPUT
    assert "không sửa tệp nào" in sent[-1] and sent_docs == []


def test_claude_qua_gio_thi_run_ghi_loi_va_nem_coder_error(db, bot, monkeypatch):
    import subprocess

    from app.modules.agent_hub import coder
    from app.modules.agent_hub.model import AgentRun

    service, sent, _ = bot
    task = _task_with_plan(db, service, ["backend/app/x.py"], status=service.ST_CODE)
    _fake_runner(monkeypatch, coder, touched=[])

    def slow(*a, **kw):
        raise subprocess.TimeoutExpired(cmd="claude", timeout=1)

    monkeypatch.setattr(coder, "run_claude", slow)
    with pytest.raises(coder.CoderError, match="quá"):
        coder.run_code_task(db, task)
    run = db.query(AgentRun).filter_by(task_id=task.id).one()
    assert run.status == coder.RUN_ERROR and "quá" in run.error


def test_code_task_bo_qua_viec_khong_o_tram_code_va_dong_failed_khi_hong(db, bot, monkeypatch):
    from app.modules.agent_hub import coder, tasks

    service, sent, _ = bot
    monkeypatch.setattr(settings, "AGENT_CODER_ENABLED", True)
    monkeypatch.setattr(tasks, "_off", lambda: None)
    monkeypatch.setattr(tasks, "SessionLocal", lambda: db)
    monkeypatch.setattr(db, "close", lambda: None)

    # việc đang ở PLAN (chưa duyệt / bị giao trùng) -> bỏ qua, không chạy gì
    task = _task_with_plan(db, service, ["backend/app/x.py"])
    ran: list[int] = []
    monkeypatch.setattr(coder, "run_code_task", lambda d, t: ran.append(t.id) or {})
    assert tasks.code_task(task.id)["status"] == "skipped"
    assert ran == []

    # việc ở CODE mà runner hỏng -> FAILED + một câu Telegram
    task.status = service.ST_CODE
    db.commit()

    def boom(d, t, **kw):
        raise coder.CoderError("CLAUDE_CODE_OAUTH_TOKEN chưa khai")

    monkeypatch.setattr(coder, "run_code_task", boom)
    assert tasks.code_task(task.id)["status"] == "error"
    assert task.status == ST_FAILED and "CLAUDE_CODE_OAUTH_TOKEN" in task.note
    assert "hỏng" in sent[-1]


def test_de_bai_co_ke_hoach_luat_va_yeu_cau_tong_ket(db, bot):
    from app.modules.agent_hub import coder

    service, _, _ = bot
    task = _task_with_plan(db, service, ["backend/app/modules/leave/service.py"],
                           test_plan="pytest test_leave", related_docs=[{"path": "doc/x.md"}])
    brief = coder.build_brief(task, [{"path": "doc/y.md", "title": "Y", "text": "nội dung"}])
    for needle in (task.code, "backend/app/modules/leave/service.py", "pytest test_leave",
                   "doc/x.md", "doc/y.md", "C1.", "C10.", "§D", "TỔNG KẾT",
                   str(settings.AGENT_MAX_FILES_TOUCHED)):
        assert needle in brief
    assert "CLAUDE_CODE_OAUTH_TOKEN" not in brief


def test_ten_nhanh_theo_ma_viec_khong_dau():
    from app.modules.agent_hub import coder

    class T:
        code = "AI-0007"
        title = "Sửa lỗi lọc Nghỉ phép theo phòng ban!!"

    assert coder.branch_name_for(T()) == "bot/ai-0007-sua-loi-loc-nghi-phep-theo-phong-ban"


# ---------------------------------------------------------------------------
# ai-CR-012 — GĐ2a: đẩy nhánh lên GitHub + mở PR
# ---------------------------------------------------------------------------
def _capture_send(monkeypatch, service):
    """Như fixture `bot` nhưng giữ cả nút bấm, vì thẻ GĐ2a khác nhau ở đúng cái nút."""
    sent: list[tuple[str, list]] = []
    monkeypatch.setattr(service.telegram, "send",
                        lambda text, **kw: sent.append((text, kw.get("buttons") or [])) or 1)
    return sent


def _fake_github(monkeypatch, coder, *, post=(201, {"html_url": "https://github.com/g/p/pull/7",
                                                   "number": 7}), get=(200, [])):
    calls: list[tuple] = []

    def fake_request(method, path, payload=None):
        calls.append((method, path, payload))
        return post if method == "POST" else get

    monkeypatch.setattr(coder, "github_request", fake_request)
    return calls


def test_bat_pr_thi_day_nhanh_bang_khoa_trong_env_va_mo_pr(db, bot, monkeypatch):
    """Khóa GitHub chỉ đi vào `git push` qua GIT_CONFIG_*, không nằm trên dòng lệnh; PR ghi vào việc."""
    from app.modules.agent_hub import coder
    from app.modules.agent_hub.model import AgentRun

    service, _, _ = bot
    sent = _capture_send(monkeypatch, service)
    monkeypatch.setattr(coder.telegram, "send_document", lambda *a, **kw: 1)
    monkeypatch.setattr(settings, "AGENT_PR_ENABLED", True)
    monkeypatch.setenv("AGENT_GITHUB_TOKEN", "github_pat_GIA")
    task = _task_with_plan(db, service, ["backend/app/modules/leave/service.py"],
                           status=service.ST_CODE)
    calls = _fake_runner(monkeypatch, coder, touched=[
        "backend/app/modules/leave/service.py", "test/backend/test_leave_loc.py"])
    gh = _fake_github(monkeypatch, coder)

    coder.run_code_task(db, task)
    push = [c for c in calls if c[:2] == ["git", "push"]]
    assert len(push) == 1 and push[0][2] == "--force" and "HEAD:refs/heads/bot/x" in push[0]
    assert push[0][-1]["GIT_CONFIG_KEY_0"] == "http.extraheader"
    assert "github_pat_GIA" not in " ".join(str(a) for a in push[0][:-1])
    assert task.status == ST_REVIEW and task.pr_url == "https://github.com/g/p/pull/7"
    method, path, payload = gh[0]
    assert method == "POST" and path.endswith("/pulls") and payload["base"] == "erp-v2"
    assert payload["head"] == "bot/x" and payload["title"].startswith(task.code)
    assert "test_leave_loc.py" in payload["body"] and "XANH" in payload["body"]
    assert "Generated with" in payload["body"] and "KHÔNG tự merge" in payload["body"]
    run = db.query(AgentRun).filter_by(task_id=task.id).one()
    assert run.artifact["pr"]["number"] == 7
    text, buttons = sent[-1]
    assert "PR #7" in text and ("Mở PR trên GitHub", "https://github.com/g/p/pull/7") in buttons


def test_tat_pr_thi_khong_day_va_the_co_nut_day_tay(db, bot, monkeypatch):
    from app.modules.agent_hub import coder

    service, _, _ = bot
    sent = _capture_send(monkeypatch, service)
    monkeypatch.setattr(coder.telegram, "send_document", lambda *a, **kw: 1)
    monkeypatch.setattr(settings, "AGENT_PR_ENABLED", False)
    task = _task_with_plan(db, service, ["backend/app/x.py"], status=service.ST_CODE)
    calls = _fake_runner(monkeypatch, coder, touched=["backend/app/x.py"])
    gh = _fake_github(monkeypatch, coder)

    coder.run_code_task(db, task)
    assert not any(c[:2] == ["git", "push"] for c in calls) and gh == []
    assert task.pr_url == ""
    text, buttons = sent[-1]
    assert "Chưa đẩy GitHub" in text and ("Gửi link PR để anh tự merge", f"pr:{task.id}") in buttons


def test_day_github_hong_thi_viec_van_o_review_va_co_nut_day_lai(db, bot, monkeypatch):
    """Thiếu khóa → không đẩy được, nhưng commit đã có trong runner nên việc KHÔNG hỏng."""
    from app.modules.agent_hub import coder

    service, _, _ = bot
    sent = _capture_send(monkeypatch, service)
    monkeypatch.setattr(coder.telegram, "send_document", lambda *a, **kw: 1)
    monkeypatch.setattr(settings, "AGENT_PR_ENABLED", True)
    monkeypatch.delenv("AGENT_GITHUB_TOKEN", raising=False)
    task = _task_with_plan(db, service, ["backend/app/x.py"], status=service.ST_CODE)
    _fake_runner(monkeypatch, coder, touched=["backend/app/x.py"])
    _fake_github(monkeypatch, coder)

    out = coder.run_code_task(db, task)
    assert out["status"] == ST_REVIEW and task.pr_url == ""
    text, buttons = sent[-1]
    assert "HỎNG" in text and "AGENT_GITHUB_TOKEN" in text
    assert ("Đẩy GitHub lại", f"pr:{task.id}") in buttons


def test_mo_pr_trung_nhanh_thi_lay_pr_dang_mo(monkeypatch):
    from app.modules.agent_hub import coder

    class T:
        code = "AI-0005"
        title = "x"

    _fake_github(monkeypatch, coder, post=(422, {"message": "A pull request already exists"}),
                 get=(200, [{"html_url": "https://github.com/g/p/pull/3", "number": 3}]))
    pr = coder.open_pull_request(T(), "bot/ai-0005-x", body="")
    assert pr == {"url": "https://github.com/g/p/pull/3", "number": 3, "created": False}

    _fake_github(monkeypatch, coder, post=(403, {"message": "Resource not accessible"}))
    with pytest.raises(coder.CoderError, match="403"):
        coder.open_pull_request(T(), "bot/ai-0005-x", body="")


def test_nut_pr_chi_nhan_viec_o_review_va_giao_cho_runner(db, bot, monkeypatch):
    from app.modules.agent_hub import coder

    service, _, _ = bot
    sent = _capture_send(monkeypatch, service)
    toasts: list[str] = []
    monkeypatch.setattr(service.telegram, "answer_callback", lambda cb, text="": toasts.append(text))
    monkeypatch.setattr(service.telegram, "clear_buttons", lambda *a, **kw: None)
    monkeypatch.setattr(settings, "AGENT_CODER_ENABLED", True)
    dispatched: list[int] = []
    monkeypatch.setattr(coder, "dispatch_publish", lambda tid: dispatched.append(tid))

    task = _task_with_plan(db, service, ["backend/app/x.py"])  # còn ở PLAN
    service.handle_callback(db, _callback(f"pr:{task.id}"))
    assert dispatched == [] and "chưa có bản vá" in toasts[-1]

    task.status = service.ST_REVIEW
    db.commit()
    service.handle_callback(db, _callback(f"pr:{task.id}"))
    assert dispatched == [task.id] and "đang đẩy nhánh" in sent[-1][0]

    task.pr_url = "https://github.com/g/p/pull/9"
    db.commit()
    service.handle_callback(db, _callback(f"pr:{task.id}"))
    assert dispatched == [task.id] and ("Mở PR trên GitHub", task.pr_url) in sent[-1][1]


def test_day_nhanh_da_commit_lay_mo_ta_tu_artifact(db, bot, monkeypatch, tmp_path):
    from app.modules.agent_hub import coder
    from app.modules.agent_hub.model import AgentRun

    service, _, _ = bot
    sent = _capture_send(monkeypatch, service)
    monkeypatch.setenv("AGENT_GITHUB_TOKEN", "github_pat_GIA")
    monkeypatch.setattr(settings, "AGENT_WORKTREE_ROOT", str(tmp_path))
    task = _task_with_plan(db, service, ["backend/app/x.py"], status=service.ST_REVIEW,
                           branch_name="bot/x")
    (tmp_path / task.code).mkdir()
    run = AgentRun(task_id=task.id, stage=coder.STAGE_CODE, provider="claude_code", model="m",
                   status=coder.RUN_OK, started_at=datetime.now(), artifact={
                       "session_id": "s-1", "files": [{"path": "backend/app/x.py", "added": 3,
                                                       "deleted": 1, "in_plan": True}],
                       "gate": {"status": "none", "tests": [], "output": ""}, "report": "đã sửa x"})
    db.add(run)
    db.commit()
    calls: list = []

    def fake_git(cwd, *args, timeout=0, extra_env=None):
        calls.append(["git", *args])
        return "bot/khac" if args[:1] == ("rev-parse",) and calls.__len__() == 1 else "bot/x"

    monkeypatch.setattr(coder, "_git", fake_git)
    gh = _fake_github(monkeypatch, coder)

    with pytest.raises(coder.CoderError, match="không phải bot/x"):
        coder.publish_existing(db, task)
    pr = coder.publish_existing(db, task)
    assert pr["number"] == 7 and task.pr_url.endswith("/pull/7")
    assert "backend/app/x.py" in gh[-1][2]["body"] and "đã sửa x" in gh[-1][2]["body"]
    assert run.artifact["pr"]["number"] == 7
    assert "Đã mở PR #7" in sent[-1][0]


def test_publish_task_hong_thi_nhan_ly_do_kem_nut_day_lai(db, bot, monkeypatch):
    from app.modules.agent_hub import coder, tasks

    service, _, _ = bot
    sent = _capture_send(monkeypatch, service)
    monkeypatch.setattr(settings, "AGENT_CODER_ENABLED", True)
    monkeypatch.setattr(tasks, "_off", lambda: None)
    monkeypatch.setattr(tasks, "SessionLocal", lambda: db)
    monkeypatch.setattr(db, "close", lambda: None)
    task = _task_with_plan(db, service, ["backend/app/x.py"])
    assert tasks.publish_task(task.id)["status"] == "skipped"

    task.status = service.ST_REVIEW
    db.commit()

    def boom(d, t):
        raise coder.CoderError("worktree không còn")

    monkeypatch.setattr(coder, "publish_existing", boom)
    assert tasks.publish_task(task.id)["status"] == "error"
    assert task.status == service.ST_REVIEW
    assert "hỏng" in sent[-1][0] and ("Đẩy GitHub lại", f"pr:{task.id}") in sent[-1][1]


def test_nut_telegram_la_url_thi_thanh_nut_lien_ket():
    from app.modules.agent_hub import telegram

    assert telegram._button("Mở PR", "https://github.com/g/p/pull/7") == {
        "text": "Mở PR", "url": "https://github.com/g/p/pull/7"}
    assert telegram._button("Bỏ", "no:5") == {"text": "Bỏ", "callback_data": "no:5"}


# ---------------------------------------------------------------------------
# GĐ2b phần 1 (ai-CR-013): hỏi thêm về bản vá bằng đúng phiên đã sửa việc
# ---------------------------------------------------------------------------
def _task_with_session(db, service, coder, session_id="11111111-2222-4333-8444-555555555555"):
    """Việc đã sửa xong (REVIEW) kèm lượt CODE OK giữ `session_id` — thứ nút hỏi cần."""
    from app.modules.agent_hub.model import AgentRun

    task = _task_with_plan(db, service, ["backend/app/x.py"], status=service.ST_REVIEW,
                           branch_name="bot/x")
    run = AgentRun(task_id=task.id, stage=coder.STAGE_CODE, provider="claude_code", model="m",
                   status=coder.RUN_OK, started_at=datetime.now(),
                   artifact={"session_id": session_id, "files": [], "gate": {"status": "pass"}})
    db.add(run)
    db.commit()
    return task


def test_the_ket_qua_doi_markdown_sang_html_va_co_nut_hoi_them(db, bot, monkeypatch):
    """Tổng kết của Claude Code là Markdown: `**đậm**` phải thành <b>, không hiện dấu sao thô."""
    from app.modules.agent_hub import coder

    service, _, _ = bot
    sent = _capture_send(monkeypatch, service)
    monkeypatch.setattr(coder.telegram, "send_document", lambda *a, **kw: 1)
    task = _task_with_plan(db, service, ["backend/app/x.py"], status=service.ST_CODE)
    _fake_runner(monkeypatch, coder, touched=["backend/app/x.py"],
                 report="## TỔNG KẾT\n1. Đã sửa **điều kiện lọc**\n2. Test `x` xanh")
    coder.run_code_task(db, task)
    text, buttons = sent[-1]
    assert "<b>điều kiện lọc</b>" in text and "**" not in text
    assert ("Hỏi thêm về bản vá", f"ask:{task.id}") in buttons
    assert ("Bỏ việc này", f"no:{task.id}") in buttons


def test_nut_hoi_them_giu_nguyen_nut_the_va_moi_hoi(db, bot, monkeypatch):
    from app.modules.agent_hub import coder
    from app.modules.agent_hub.model import AgentMessage

    service, sent, _ = bot
    cleared: list[int] = []
    toasts: list[str] = []
    monkeypatch.setattr(service.telegram, "clear_buttons", lambda c, m: cleared.append(m))
    monkeypatch.setattr(service.telegram, "answer_callback", lambda cb, t="": toasts.append(t))
    monkeypatch.setattr(settings, "AGENT_CODER_ENABLED", True)
    task = _task_with_session(db, service, coder)

    service.handle_callback(db, _callback(f"ask:{task.id}"))
    assert cleared == []  # «Mở PR» / «Bỏ việc này» vẫn còn trên thẻ
    assert "Nhắn câu hỏi" in toasts[-1]
    assert "hỏi gì về bản vá" in sent[-1] and task.code in sent[-1]
    last = db.query(AgentMessage).order_by(AgentMessage.id.desc()).first()
    assert last.action == service.ACT_WAIT_PATCH_Q and last.task_id == task.id


def test_nut_hoi_them_khi_chua_co_phien_thi_chi_toast(db, bot, monkeypatch):
    service, sent, _ = bot
    toasts: list[str] = []
    monkeypatch.setattr(service.telegram, "clear_buttons", lambda c, m: None)
    monkeypatch.setattr(service.telegram, "answer_callback", lambda cb, t="": toasts.append(t))
    task = _task_with_plan(db, service, ["backend/app/x.py"], status=service.ST_REVIEW)
    service.handle_callback(db, _callback(f"ask:{task.id}"))
    assert "chưa có phiên" in toasts[-1] and sent == []


def test_tin_ke_sau_loi_moi_la_cau_hoi_giao_runner_khong_phan_loai(db, bot, monkeypatch):
    """Sau lời mời, tin chữ kế tiếp KHÔNG qua Gemini phân loại: đóng dấu `hoi_va` + vào hàng đợi."""
    from app.modules.agent_hub import coder
    from app.modules.agent_hub.model import AgentMessage

    service, sent, _ = bot
    monkeypatch.setattr(service.telegram, "clear_buttons", lambda c, m: None)
    monkeypatch.setattr(service.telegram, "answer_callback", lambda cb, t="": None)
    monkeypatch.setattr(settings, "AGENT_CODER_ENABLED", True)
    intents: list[str] = []
    monkeypatch.setattr(service.manager, "run_intent",
                        lambda text, **kw: intents.append(text) or (_ for _ in ()).throw(
                            AssertionError("không được phân loại")))
    dispatched: list[tuple[int, int]] = []
    monkeypatch.setattr(coder, "dispatch_question", lambda t, m: dispatched.append((t, m)))
    task = _task_with_session(db, service, coder)
    service.handle_callback(db, _callback(f"ask:{task.id}"))

    service.handle_message(db, _msg("Sao lại bỏ điều kiện company_id?"))
    q = db.query(AgentMessage).filter_by(direction=service.DIR_IN).order_by(
        AgentMessage.id.desc()).first()
    assert q.action == service.ACT_PATCH_Q and q.task_id == task.id
    assert dispatched == [(task.id, q.id)] and intents == []
    #  Sau câu trả lời của phiên, nhắn tiếp vẫn là hỏi tiếp (dấu `tra_loi_va`).
    service.reply(db, "12345", f"**{task.code}** — vì cột đó...", task_id=task.id,
                  markdown=True, action=service.ACT_PATCH_ANSWER)
    db.commit()
    service.handle_message(db, _msg("Thế còn test?"))
    assert len(dispatched) == 2 and intents == []


def test_qua_muoi_phut_sau_loi_moi_thi_tin_ke_di_phan_loai_binh_thuong(db, bot, monkeypatch):
    from datetime import timedelta

    from app.modules.agent_hub import coder
    from app.modules.agent_hub.model import AgentMessage

    service, _, _ = bot
    monkeypatch.setattr(settings, "AGENT_CODER_ENABLED", True)
    dispatched: list = []
    monkeypatch.setattr(coder, "dispatch_question", lambda t, m: dispatched.append(t))
    _fake_intent(monkeypatch, service, "khong_ro")
    task = _task_with_session(db, service, coder)
    invite = service.log_message(db, service.DIR_OUT, "12345", 9, "hỏi gì?",
                                 action=service.ACT_WAIT_PATCH_Q, task_id=task.id)
    invite.created_at = datetime.now() - timedelta(minutes=11)
    db.commit()

    service.handle_message(db, _msg("Màn đơn hàng lỗi lọc ngày"))
    row = db.query(AgentMessage).filter_by(direction=service.DIR_IN).order_by(
        AgentMessage.id.desc()).first()
    assert row.action != service.ACT_PATCH_Q and dispatched == []


def test_tra_loi_cau_hoi_dung_phien_cu_chi_doc_va_ghi_so(db, bot, monkeypatch):
    from app.modules.agent_hub import coder
    from app.modules.agent_hub.model import AgentRun

    service, _, _ = bot
    sent = _capture_send(monkeypatch, service)
    monkeypatch.setattr(coder.telegram, "send_chat_action", lambda *a, **kw: None)
    monkeypatch.setattr(coder.Path, "exists", lambda self: True)
    cmds: list[list[str]] = []

    def fake_cli(cmd, stdin, worktree, timeout):
        cmds.append(cmd)
        assert "Sao lại bỏ" in stdin and "KHÔNG sửa tệp" in stdin
        return {"result": "Vì **cột đó** không còn dùng", "num_turns": 3, "duration_ms": 8000,
                "total_cost_usd": 0.05, "usage": {"input_tokens": 10, "output_tokens": 5}}

    monkeypatch.setattr(coder, "_run_cli", fake_cli)
    task = _task_with_session(db, service, coder, session_id="abc-session")

    answer = coder.answer_patch_question(db, task, "Sao lại bỏ điều kiện?")
    assert answer.startswith("Vì")
    cmd = cmds[0]
    assert cmd[cmd.index("--resume") + 1] == "abc-session"
    assert "Edit" not in cmd[cmd.index("--allowedTools") + 1]
    assert "Bash(pytest" not in cmd[cmd.index("--allowedTools") + 1]
    run = db.query(AgentRun).filter_by(task_id=task.id, stage=coder.STAGE_ASK).one()
    assert run.status == coder.RUN_OK and run.artifact["question"].startswith("Sao lại bỏ")
    assert run.artifact["session_id"] == "abc-session" and run.cost_usd == 0.05
    text, buttons = sent[-1]
    assert "<b>cột đó</b>" in text and f"<b>{task.code}</b>" in text
    assert ("Hỏi tiếp", f"ask:{task.id}") in buttons
    assert task.status == service.ST_REVIEW


def test_phien_khong_con_thi_noi_bang_tieng_nguoi(db, bot, monkeypatch):
    from app.modules.agent_hub import coder
    from app.modules.agent_hub.model import AgentRun

    service, _, _ = bot
    monkeypatch.setattr(coder.telegram, "send_chat_action", lambda *a, **kw: None)
    monkeypatch.setattr(coder.Path, "exists", lambda self: True)

    def gone(cmd, stdin, worktree, timeout):
        raise coder.CoderError("claude lỗi: No conversation found with session ID: abc")

    monkeypatch.setattr(coder, "_run_cli", gone)
    task = _task_with_session(db, service, coder)
    with pytest.raises(coder.CoderError, match="không còn trong runner"):
        coder.answer_patch_question(db, task, "hỏi gì đó")
    run = db.query(AgentRun).filter_by(task_id=task.id, stage=coder.STAGE_ASK).one()
    assert run.status == coder.RUN_ERROR and "không còn trong runner" in run.error


def test_ask_task_hong_thi_nhan_ly_do_kem_nut_hoi_lai(db, bot, monkeypatch):
    from app.modules.agent_hub import coder, tasks

    service, _, _ = bot
    sent = _capture_send(monkeypatch, service)
    monkeypatch.setattr(settings, "AGENT_CODER_ENABLED", True)
    monkeypatch.setattr(tasks, "_off", lambda: None)
    monkeypatch.setattr(tasks, "SessionLocal", lambda: db)
    monkeypatch.setattr(db, "close", lambda: None)
    task = _task_with_session(db, service, coder)
    q = service.log_message(db, service.DIR_IN, "12345", 8, "hỏi?", action=service.ACT_PATCH_Q,
                            task_id=task.id)
    db.commit()

    def boom(d, t, question):
        raise coder.CoderError("worktree không còn")

    monkeypatch.setattr(coder, "answer_patch_question", boom)
    assert tasks.ask_task(task.id, q.id)["status"] == "error"
    assert task.status == service.ST_REVIEW
    assert "Hỏi thêm về" in sent[-1][0] and ("Hỏi lại", f"ask:{task.id}") in sent[-1][1]
    #  Việc đã đóng thì bỏ qua, không gọi phiên.
    task.status = ST_FAILED
    db.commit()
    assert tasks.ask_task(task.id, q.id)["status"] == "skipped"


def test_phien_claude_cat_trong_volume_worktree(monkeypatch):
    """CLAUDE_CONFIG_DIR trỏ vào volume worktree: phiên sống qua `up --force-recreate`."""
    from app.modules.agent_hub import coder

    monkeypatch.setenv("CLAUDE_CODE_OAUTH_TOKEN", "oauth-ok")
    monkeypatch.setattr(settings, "AGENT_WORKTREE_ROOT", "/worktrees")
    env = coder.build_env("/worktrees/AI-0001")
    assert env["CLAUDE_CONFIG_DIR"].replace("\\", "/") == "/worktrees/.claude"


# ---------------------------------------------------------------------------
# GĐ2b·2 (ai-CR-014): gộp erp-v2 + deploy dev có hỏi trước, hẹn giờ, thu hồi
# ---------------------------------------------------------------------------
from datetime import timedelta  # noqa: E402
from app.modules.agent_hub.constants import (  # noqa: E402
    ACT_WAIT_DEPLOY_TIME, RUN_ERROR, RUN_OK, RUN_RUNNING, ST_NEEDS_INPUT, ST_PROD,
    STAGE_DEPLOY, STAGE_REVERT,
)


def _deploy_on(monkeypatch):
    monkeypatch.setattr(settings, "AGENT_CODER_ENABLED", True)
    monkeypatch.setattr(settings, "AGENT_DEPLOY_ENABLED", True)
    monkeypatch.setattr(settings, "AGENT_BASE_BRANCH", "erp-v2")
    monkeypatch.setattr(settings, "AGENT_WORKTREE_ROOT", "/worktrees")
    monkeypatch.setattr(settings, "AGENT_VPS_HOST", "vps.test")
    monkeypatch.setattr(settings, "AGENT_VPS_USER", "deploy")
    monkeypatch.setattr(settings, "AGENT_VPS_PORT", 51251)
    monkeypatch.setattr(settings, "AGENT_DEV_UI_URL", "https://deverp.test")


def _fake_merge_stack(monkeypatch, coder, *, changed=("backend/app/x.py", "frontend-v2/src/a.ts"),
                      merge_error="", ssh_error="", health=200):
    """Giả git + ssh + health cho lượt gộp/thu hồi. Trả (git_calls, ssh_scripts)."""
    git_calls: list[list] = []
    scripts: list[str] = []

    def fake_git(cwd, *args, timeout=0, extra_env=None):
        git_calls.append(["git", *args] + ([extra_env] if extra_env else []))
        if args[0] == "merge" and merge_error and "--abort" not in args:
            raise coder.CoderError(merge_error)
        if args[:2] == ("rev-parse", "HEAD"):
            return "abc1234def5678\n"
        if args[:2] == ("diff", "--name-only"):
            return "\n".join(changed) + "\n"
        return ""

    def fake_ssh(script, *, timeout=0):
        scripts.append(script)
        if ssh_error:
            raise coder.CoderError(ssh_error)
        return "HEAD=abc1234def5678\nbuilt\n"

    monkeypatch.setenv("AGENT_GITHUB_TOKEN", "ghp_test")
    monkeypatch.setattr(coder, "_git", fake_git)
    monkeypatch.setattr(coder, "_merge_worktree", lambda: "/worktrees/merge")
    monkeypatch.setattr(coder, "run_ssh", fake_ssh)
    monkeypatch.setattr(coder, "wait_dev_health", lambda: health)
    return git_calls, scripts


def _deploy_runs(db, task, stage=STAGE_DEPLOY):
    from app.modules.agent_hub.model import AgentRun
    return [r for r in db.query(AgentRun).filter_by(task_id=task.id).order_by(AgentRun.id)
            if r.stage == stage]


def test_the_ket_qua_co_nut_gop_chi_khi_bat_co(db, bot, monkeypatch):
    from app.modules.agent_hub import coder

    service, _, _ = bot
    _deploy_on(monkeypatch)
    sent = _capture_send(monkeypatch, service)
    task = _task_with_session(db, service, coder)
    run = coder.latest_code_run(db, task)
    gate = {"status": "pass", "tests": [], "output": ""}
    coder.send_review_card(db, task, run, files=[], gate=gate, escalation="", report="", data={})
    assert ("Gộp erp-v2 + deploy dev", f"mg:{task.id}") in sent[-1][1]
    monkeypatch.setattr(settings, "AGENT_DEPLOY_ENABLED", False)
    coder.send_review_card(db, task, run, files=[], gate=gate, escalation="", report="", data={})
    assert not any(b[1].startswith("mg:") for b in sent[-1][1])
    #  Bot dừng vì lệch kế hoạch: không có gì để gộp, nút không hiện dù cờ bật.
    monkeypatch.setattr(settings, "AGENT_DEPLOY_ENABLED", True)
    coder.send_review_card(db, task, run, files=[], gate=gate, escalation="lệch", report="", data={})
    assert not any(b[1].startswith("mg:") for b in sent[-1][1])


def test_nut_gop_chi_mo_the_hoi_khong_gop_gi(db, bot, monkeypatch):
    """Điều đại ca chốt: muốn gộp là phải hỏi. Nút «Gộp» chỉ kể ba bước + hỏi, không giao runner."""
    from app.modules.agent_hub import coder

    service, _, _ = bot
    _deploy_on(monkeypatch)
    sent = _capture_send(monkeypatch, service)
    monkeypatch.setattr(coder, "dispatch_deploy", lambda *a: pytest.fail("chưa đồng ý mà đã giao"))
    task = _task_with_session(db, service, coder)
    run = coder.latest_code_run(db, task)
    run.artifact = {**run.artifact, "files": [{"path": "backend/app/x.py", "added": 3, "deleted": 1,
                                               "in_plan": True}]}
    db.commit()

    service.handle_callback(db, _callback(f"mg:{task.id}"))
    text, buttons = sent[-1]
    assert "ba bước" in text and "merge --no-ff" in text and "<code>api</code>" in text
    assert "có muốn em gộp" in text
    assert [b[1] for b in buttons] == [f"mgok:{task.id}", f"mgat:{task.id}", f"ask:{task.id}",
                                       f"mgno:{task.id}"]
    assert task.status == ST_REVIEW and _deploy_runs(db, task) == []
    #  Cờ tắt: không có thẻ hỏi, nói rõ tắt.
    monkeypatch.setattr(settings, "AGENT_DEPLOY_ENABLED", False)
    service.handle_callback(db, _callback(f"mg:{task.id}"))
    assert "AGENT_DEPLOY_ENABLED=false" in sent[-1][0]


def test_dong_y_thi_ghi_so_va_giao_runner_dung_mot_lan(db, bot, monkeypatch):
    from app.modules.agent_hub import coder

    service, _, _ = bot
    _deploy_on(monkeypatch)
    sent = _capture_send(monkeypatch, service)
    dispatched: list[tuple] = []
    monkeypatch.setattr(coder, "dispatch_deploy", lambda tid, rid: dispatched.append((tid, rid)))
    task = _task_with_session(db, service, coder)

    service.handle_callback(db, _callback(f"mgok:{task.id}"))
    runs = _deploy_runs(db, task)
    assert len(runs) == 1 and runs[0].status == RUN_RUNNING and runs[0].artifact["phase"] == "ngay"
    assert dispatched == [(task.id, runs[0].id)]
    assert "đang gộp" in sent[-1][0]
    #  Bấm lại khi lượt đang chạy: không giao thêm, nói rõ đang chạy.
    service.handle_callback(db, _callback(f"mgok:{task.id}"))
    assert len(dispatched) == 1 and "Đang có một lượt" in sent[-1][0]
    service.handle_callback(db, _callback(f"mg:{task.id}"))
    assert len(_deploy_runs(db, task)) == 1 and "Đang có một lượt" in sent[-1][0]
    #  Việc chưa có bản vá (còn ở PLAN) thì không gộp được.
    plan_task = _task_with_plan(db, service, ["backend/app/y.py"])
    service.handle_callback(db, _callback(f"mgok:{plan_task.id}"))
    assert "Chưa có bản vá" in sent[-1][0] and len(dispatched) == 1


def test_parse_schedule_time_cac_kieu_dai_ca_nhan():
    from app.modules.agent_hub.service import parse_schedule_time as p

    now = datetime(2026, 9, 22, 10, 0, 0)
    assert p("14:30", now) == datetime(2026, 9, 22, 14, 30)
    assert p("20h", now) == datetime(2026, 9, 22, 20, 0)
    assert p("20h30", now) == datetime(2026, 9, 22, 20, 30)
    assert p("8 giờ sáng mai", now) == datetime(2026, 9, 23, 8, 0)
    assert p("9h", now) == datetime(2026, 9, 23, 9, 0)            # đã qua hôm nay -> ngày mai
    assert p("3h chiều", now) == datetime(2026, 9, 22, 15, 0)
    assert p("45 phút nữa", now) == datetime(2026, 9, 22, 10, 45)
    assert p("2 tiếng nữa", now) == datetime(2026, 9, 22, 12, 0)
    assert p("sau 30 phút", now) == datetime(2026, 9, 22, 10, 30)
    assert p("ngay", now) == now
    assert p("25:00", now) is None
    assert p("14:75", now) is None
    assert p("để anh xem đã", now) is None
    assert p("", now) is None


def test_hen_gio_roi_nhan_gio_thi_ghi_lich_va_vong_beat_giao_khi_toi_gio(db, bot, monkeypatch):
    from app.modules.agent_hub import coder
    from app.modules.agent_hub.model import AgentMessage

    service, _, _ = bot
    _deploy_on(monkeypatch)
    sent = _capture_send(monkeypatch, service)
    dispatched: list[tuple] = []
    monkeypatch.setattr(coder, "dispatch_deploy", lambda tid, rid: dispatched.append((tid, rid)))
    task = _task_with_session(db, service, coder)

    service.handle_callback(db, _callback(f"mgat:{task.id}"))
    last = db.query(AgentMessage).order_by(AgentMessage.id.desc()).first()
    assert last.action == ACT_WAIT_DEPLOY_TIME and last.task_id == task.id
    #  Giờ không đọc được: hỏi lại và VẪN mở mạch (dấu chờ giữ nguyên), không đi phân loại.
    service.handle_message(db, _msg("để anh xem đã"))
    assert "chưa hiểu giờ" in sent[-1][0]
    assert db.query(AgentMessage).order_by(AgentMessage.id.desc()).first().action == ACT_WAIT_DEPLOY_TIME
    service.handle_message(db, _msg("45 phút nữa"))
    runs = _deploy_runs(db, task)
    assert len(runs) == 1 and runs[0].artifact["phase"] == "hen_gio"
    assert "Đã hẹn" in sent[-1][0] and ("Hủy hẹn", f"mgno:{task.id}") in sent[-1][1]
    assert dispatched == []
    #  Chưa tới giờ: vòng beat không giao.
    assert service.dispatch_due_deploys(db, datetime.now()) == 0
    #  Tới giờ: giao đúng một lần, pha đổi sang `dispatched` nên vòng sau không giao lại.
    assert service.dispatch_due_deploys(db, datetime.now() + timedelta(hours=1)) == 1
    assert dispatched == [(task.id, runs[0].id)] and runs[0].artifact["phase"] == "dispatched"
    assert "Tới giờ hẹn" in sent[-1][0]
    assert service.dispatch_due_deploys(db, datetime.now() + timedelta(hours=2)) == 0


def test_huy_hen_dong_luot_va_cho_bam_lai(db, bot, monkeypatch):
    from app.modules.agent_hub import coder

    service, _, _ = bot
    _deploy_on(monkeypatch)
    sent = _capture_send(monkeypatch, service)
    task = _task_with_session(db, service, coder)
    #  Sổ giữ giờ UTC (13:00), thẻ nói giờ Việt Nam (20:00) — ai-CR-020.
    service._new_deploy_run(db, task, STAGE_DEPLOY, "hen_gio", scheduled_for="2026-09-22T13:00")
    #  Có lịch rồi thì bấm «Gộp» chỉ nhắc lịch + nút hủy, không mở thẻ hỏi mới.
    service.handle_callback(db, _callback(f"mg:{task.id}"))
    assert "lịch hẹn lúc 20:00" in sent[-1][0] and ("Hủy hẹn", f"mgno:{task.id}") in sent[-1][1]
    service.handle_callback(db, _callback(f"mgno:{task.id}"))
    run = _deploy_runs(db, task)[0]
    assert run.status == RUN_ERROR and run.error == "Đại ca hủy hẹn"
    assert ("Gộp erp-v2 + deploy dev", f"mg:{task.id}") in sent[-1][1]
    #  Tới giờ mà việc không còn chờ gộp (đã đóng): lượt đóng lỗi, không giao.
    run2 = service._new_deploy_run(db, task, STAGE_DEPLOY, "hen_gio", scheduled_for="2026-09-22T20:00")
    task.status = ST_FAILED
    db.commit()
    assert service.dispatch_due_deploys(db, datetime(2026, 9, 22, 20, 1)) == 0
    assert run2.status == RUN_ERROR


def test_deploy_services_for_theo_thu_muc():
    from app.modules.agent_hub.coder import deploy_services_for as f

    assert f(["backend/app/x.py", "test/backend/t.py"]) == ["api", "celery-worker", "celery-beat"]
    assert f(["frontend-v2/src/a.ts"]) == ["erp"]
    assert f(["frontend/src/a.tsx", "help-center/x.ts"]) == ["web", "help"]
    assert f(["doc/a.md"]) == []
    assert f(["backend/a.py", "backend/b.py", "frontend-v2/c.ts"]) == ["api", "celery-worker",
                                                                       "celery-beat", "erp"]


def test_gop_va_deploy_tron_ven(db, bot, monkeypatch):
    """merge --no-ff, push KHÔNG --force với khóa qua GIT_CONFIG, ssh reset cứng + build đúng service."""
    from app.modules.agent_hub import coder

    service, _, _ = bot
    _deploy_on(monkeypatch)
    sent = _capture_send(monkeypatch, service)
    git_calls, scripts = _fake_merge_stack(monkeypatch, coder)
    task = _task_with_session(db, service, coder)
    run = service._new_deploy_run(db, task, STAGE_DEPLOY, "ngay")

    out = coder.merge_and_deploy(db, task, run)
    assert out["status"] == "ok" and out["merge_sha"] == "abc1234def5678"
    merge = next(c for c in git_calls if c[1] == "merge")
    assert "--no-ff" in merge and "bot/x" in merge and merge[-1]["GIT_AUTHOR_NAME"] == "Agent Hub bot"
    push = next(c for c in git_calls if c[1] == "push")
    assert "--force" not in push and push[3] == "HEAD:refs/heads/erp-v2"
    assert push[-1]["GIT_CONFIG_KEY_0"] == "http.extraheader"
    assert len(scripts) == 1
    assert "git reset --hard origin/erp-v2" in scripts[0]
    assert "up -d --build api celery-worker celery-beat erp" in scripts[0]
    assert "-f docker-compose.dev.yml" in scripts[0]
    assert task.status == ST_PROD and task.deployed_dev_at is not None
    assert run.status == RUN_OK and run.artifact["merged"] and run.artifact["health"] == 200
    assert coder.merged_sha_for(db, task) == "abc1234def5678"
    text, buttons = sent[-1]
    assert "Đã gộp vào" in text and "200 OK" in text and "deverp.test" in text
    assert [b[1] for b in buttons] == [f"rv:{task.id}", f"ask:{task.id}", f"done:{task.id}"]
    #  «Xong»: đóng việc.
    service.handle_callback(db, _callback(f"done:{task.id}"))
    assert task.status == service.ST_DONE and task.closed_at is not None


def test_gop_xung_dot_thi_abort_va_viec_ve_review(db, bot, monkeypatch):
    from app.modules.agent_hub import coder

    service, _, _ = bot
    _deploy_on(monkeypatch)
    sent = _capture_send(monkeypatch, service)
    git_calls, scripts = _fake_merge_stack(monkeypatch, coder, merge_error="CONFLICT service.py")
    task = _task_with_session(db, service, coder)
    run = service._new_deploy_run(db, task, STAGE_DEPLOY, "ngay")

    out = coder.merge_and_deploy(db, task, run)
    assert out["status"] == "error" and out["pushed"] is False
    assert ["git", "merge", "--abort"] in git_calls
    assert not any(c[1] == "push" for c in git_calls) and scripts == []
    assert task.status == ST_REVIEW and task.deployed_dev_at is None
    assert run.status == RUN_ERROR and "xung đột" in run.error
    assert coder.merged_sha_for(db, task) == ""
    text, buttons = sent[-1]
    assert "chưa gộp được" in text and "Nhánh nền không đổi" in text
    assert [b[1] for b in buttons] == [f"mg:{task.id}", f"pr:{task.id}"]


def test_deploy_hong_sau_khi_day_thi_o_prod_va_chay_lai_khong_gop_lan_hai(db, bot, monkeypatch):
    from app.modules.agent_hub import coder

    service, _, _ = bot
    _deploy_on(monkeypatch)
    sent = _capture_send(monkeypatch, service)
    git_calls, scripts = _fake_merge_stack(monkeypatch, coder, ssh_error="rc=1 build lỗi")
    task = _task_with_session(db, service, coder)
    run = service._new_deploy_run(db, task, STAGE_DEPLOY, "ngay")

    out = coder.merge_and_deploy(db, task, run)
    assert out["status"] == "error" and out["pushed"] is True
    assert task.status == ST_PROD and task.deployed_dev_at is None
    assert run.artifact["merged"] and run.artifact["merge_sha"] == "abc1234def5678"
    text, buttons = sent[-1]
    assert "đã gộp vào" in text and "deploy dev HỎNG" in text
    assert [b[1] for b in buttons] == [f"mgok:{task.id}", f"rv:{task.id}"]
    #  Thẻ hỏi lần hai nói rõ chỉ làm lại bước deploy.
    service.handle_callback(db, _callback(f"mg:{task.id}"))
    assert "chỉ làm lại bước deploy" in sent[-1][0]
    #  Chạy lại: KHÔNG merge/push lần hai, đi thẳng ssh.
    monkeypatch.setattr(coder, "run_ssh", lambda s, *, timeout=0: scripts.append(s) or "HEAD=abc1234def5678\n")
    before = len(git_calls)
    run2 = service._new_deploy_run(db, task, STAGE_DEPLOY, "ngay")
    assert coder.merge_and_deploy(db, task, run2)["status"] == "ok"
    assert not any(c[1] in ("merge", "push") for c in git_calls[before:])
    assert len(scripts) == 2 and task.deployed_dev_at is not None


def test_thu_hoi_revert_m1_va_viec_ve_dang_hoi_lai(db, bot, monkeypatch):
    from app.modules.agent_hub import coder

    service, _, _ = bot
    _deploy_on(monkeypatch)
    sent = _capture_send(monkeypatch, service)
    git_calls, scripts = _fake_merge_stack(monkeypatch, coder)
    task = _task_with_session(db, service, coder)
    #  Chưa gộp thì không có gì để thu hồi.
    service.handle_callback(db, _callback(f"rv:{task.id}"))
    assert "không có gì để thu hồi" in sent[-1][0]
    run = service._new_deploy_run(db, task, STAGE_DEPLOY, "ngay")
    coder.merge_and_deploy(db, task, run)
    #  Thẻ hỏi thu hồi, rồi đồng ý.
    dispatched: list[tuple] = []
    monkeypatch.setattr(coder, "dispatch_revert", lambda tid, rid: dispatched.append((tid, rid)))
    service.handle_callback(db, _callback(f"rv:{task.id}"))
    assert "git revert -m 1 abc1234def" in sent[-1][0]
    assert [b[1] for b in sent[-1][1]] == [f"rvok:{task.id}", f"rvno:{task.id}"]
    service.handle_callback(db, _callback(f"rvok:{task.id}"))
    rrun = _deploy_runs(db, task, STAGE_REVERT)[0]
    assert dispatched == [(task.id, rrun.id)]

    before = len(git_calls)
    out = coder.revert_and_deploy(db, task, rrun)
    assert out["status"] == "ok"
    tail = git_calls[before:]
    assert ["git", "merge-base", "--is-ancestor", "abc1234def5678", "HEAD"] in tail
    revert = next(c for c in tail if c[1] == "revert")
    assert revert[2:6] == ["--no-edit", "-m", "1", "abc1234def5678"]
    push = next(c for c in tail if c[1] == "push")
    assert "--force" not in push
    assert len(scripts) == 2 and "git reset --hard origin/erp-v2" in scripts[1]
    assert task.status == ST_NEEDS_INPUT and task.deployed_dev_at is None
    assert "Đã thu hồi" in task.note
    assert coder.merged_sha_for(db, task) == ""
    assert "THU HỒI" in sent[-1][0] and "Đang hỏi lại" in sent[-1][0]
    #  Sau thu hồi, đã lên dev không còn đúng nữa -> «Thu hồi» lần hai bị chặn.
    service.handle_callback(db, _callback(f"rv:{task.id}"))
    assert "không có gì để thu hồi" in sent[-1][0]


def test_khoa_ssh_chep_ra_ban_0600_roi_xoa_va_khong_vao_env_claude(monkeypatch, tmp_path):
    from app.modules.agent_hub import coder

    key = tmp_path / "vps_key"
    key.write_bytes(b"-----BEGIN OPENSSH PRIVATE KEY-----\r\nabc\r\n-----END OPENSSH PRIVATE KEY-----\r\n")
    monkeypatch.setattr(settings, "AGENT_VPS_SSH_KEY_PATH", str(key))
    orig_mkstemp = coder.tempfile.mkstemp
    monkeypatch.setattr(coder.tempfile, "mkstemp",
                        lambda prefix="", dir=None: orig_mkstemp(prefix=prefix, dir=str(tmp_path)))
    with coder._ssh_key_file() as tmp:
        p = coder.Path(tmp)
        assert p.exists() and p != key
        assert b"\r" not in p.read_bytes()
        if hasattr(coder.os, "geteuid"):
            assert oct(p.stat().st_mode & 0o777) == "0o600"
    assert not coder.Path(tmp).exists()
    #  Tệp giữ chỗ (chưa khai AGENT_VPS_SSH_KEY_FILE) -> lỗi nói rõ phải làm gì, không ssh mù.
    key.write_text("# placeholder\n", encoding="utf-8")
    with pytest.raises(coder.CoderError, match="AGENT_VPS_SSH_KEY_FILE"):
        coder._ssh_key_path()
    #  Môi trường của `claude` không có gì dính tới VPS.
    monkeypatch.setenv("CLAUDE_CODE_OAUTH_TOKEN", "oauth-ok")
    monkeypatch.setattr(settings, "AGENT_WORKTREE_ROOT", "/worktrees")
    env = coder.build_env("/worktrees/X")
    assert not any("VPS" in k or "SSH" in k for k in env)


def test_run_ssh_chay_bang_root_moi_truong_sach_script_qua_stdin(monkeypatch, tmp_path):
    from app.modules.agent_hub import coder

    _deploy_on(monkeypatch)
    key = tmp_path / "k"
    key.write_text("-----BEGIN OPENSSH PRIVATE KEY-----\nx\n", encoding="utf-8")
    monkeypatch.setattr(settings, "AGENT_VPS_SSH_KEY_PATH", str(key))
    orig_mkstemp = coder.tempfile.mkstemp
    monkeypatch.setattr(coder.tempfile, "mkstemp",
                        lambda prefix="", dir=None: orig_mkstemp(prefix=prefix, dir=str(tmp_path)))
    seen: dict = {}

    class Proc:
        returncode = 0
        stdout = "HEAD=abc\n"
        stderr = ""

    def fake_run(cmd, **kw):
        seen.update(cmd=cmd, **kw)
        return Proc()

    monkeypatch.setattr(coder.subprocess, "run", fake_run)
    script = coder.deploy_script(["api"])
    assert coder.run_ssh(script).startswith("HEAD=abc")
    assert seen["input"] == script and "user" not in seen and "group" not in seen
    assert set(seen["env"]) == {"PATH", "HOME", "LANG"}
    cmd = seen["cmd"]
    assert cmd[0] == "ssh" and "BatchMode=yes" in cmd and cmd[-3:] == ["deploy@vps.test", "bash", "-s"]
    assert cmd[cmd.index("-p") + 1] == "51251"
    assert coder._parse_head("x\nHEAD=abc1234\n") == "abc1234"
    #  Chưa khai host/user: dừng trước khi spawn.
    monkeypatch.setattr(settings, "AGENT_VPS_HOST", "")
    with pytest.raises(coder.CoderError, match="AGENT_VPS_HOST"):
        coder.run_ssh("echo")


def test_deploy_task_bo_qua_luot_da_huy_va_do_loi_bat_ngo(db, bot, monkeypatch):
    from app.modules.agent_hub import coder, tasks

    service, _, _ = bot
    _deploy_on(monkeypatch)
    monkeypatch.setattr(settings, "AGENT_HUB_ENABLED", True)
    monkeypatch.setattr(tasks, "SessionLocal", lambda: db)
    monkeypatch.setattr(db, "close", lambda: None)
    sent = _capture_send(monkeypatch, service)
    task = _task_with_session(db, service, coder)
    run = service._new_deploy_run(db, task, STAGE_DEPLOY, "hen_gio", scheduled_for="2026-09-22T20:00")
    coder._close_run(run, status=RUN_ERROR, error="Đại ca hủy hẹn")
    db.commit()
    assert tasks.deploy_task(task.id, run.id)["status"] == "skipped"
    assert task.status == ST_REVIEW and sent == []

    run2 = service._new_deploy_run(db, task, STAGE_DEPLOY, "ngay")

    def boom(d, t, r):
        raise RuntimeError("mất điện")

    monkeypatch.setattr(coder, "merge_and_deploy", boom)
    assert tasks.deploy_task(task.id, run2.id)["status"] == "error"
    assert run2.status == RUN_ERROR and task.status == ST_REVIEW
    assert "hỏng ngoài dự kiến" in sent[-1][0]


# ---------------------------------------------------------------------------
# ai-CR-015: sổ quyết định + trả lời hỏi lại gắn vào việc cũ + nút «lần sau tự làm»
# ---------------------------------------------------------------------------
from app.modules.agent_hub.constants import (  # noqa: E402
    ACT_PLAN_ANSWER, ACT_WAIT_PLAN_ANSWER, RISK_HIGH, ST_NEEDS_INPUT as _ST_NI, STAGE_RULE,
)

_SO_MAU = """# Sổ quyết định

Phần giới thiệu, bot không đọc.

## QĐ-01 | Lỗi không tái hiện được
- Tình huống: đại ca báo lỗi không kèm mã phiếu.
- Bot làm: sửa theo mô tả, ghi giả định.
- Không áp khi: dính tiền.
- Nguồn: thử.
"""


def _so_tam(monkeypatch, tmp_path, text=_SO_MAU):
    path = tmp_path / "03-so-quyet-dinh.md"
    path.write_text(text, encoding="utf-8")
    monkeypatch.setattr(settings, "AGENT_PLAYBOOK_PATH", str(path))
    return path


def _ket_qua_model():
    from app.modules.assistant.provider.base import ChatResult

    return ChatResult(text="", provider="agent_gemini", model="x", input_tokens=0, output_tokens=0)


def _fake_plan(monkeypatch, service, *, seen=None, **out):
    data = {"plan": "Sửa điều kiện lọc", "plan_files": ["backend/app/x.py"], "test_plan": "",
            "related_docs": [], "questions": [], "risk_level": 2, "needs_clarification": False,
            "assumptions": []}
    data.update(out)

    def fake(title, summary, docs, **kw):
        if seen is not None:
            seen.append({"summary": summary, **kw})
        return dict(data), _ket_qua_model()

    monkeypatch.setattr(service.memory, "recall", lambda text: [])
    monkeypatch.setattr(service.manager, "run_plan", fake)


def _fake_rule(monkeypatch, service, calls=None, **out):
    draft = {"generalizable": True, "title": "Thiếu mã phiếu thì sửa theo mô tả",
             "situation": "Đại ca báo lỗi nhưng không đưa mã phiếu.",
             "action": "Sửa theo mô tả và ghi giả định trong tổng kết.",
             "not_when": "Lỗi hiện sai số liệu báo cáo."}
    draft.update(out)

    def fake(title, questions, answer, known):
        if calls is not None:
            calls.append({"questions": questions, "answer": answer, "known": known})
        return dict(draft), _ket_qua_model()

    monkeypatch.setattr(service.manager, "run_rule_draft", fake)


def _task_hoi_lai(db, service, **kw):
    kw.setdefault("questions", ["Lỗi ở màn nào, có mã phiếu không?"])
    return _task_with_plan(db, service, [], status=_ST_NI, **kw)


def test_so_doc_phan_muc_so_ke_tiep_va_noi_muc_moi(monkeypatch, tmp_path):
    from app.modules.agent_hub import playbook

    path = _so_tam(monkeypatch, tmp_path, _SO_MAU + "\n## QĐ-03 | Mục ba\n- Tình huống: x.\n")
    text = playbook.load_text()
    assert text.startswith("## QĐ-01") and "Phần giới thiệu" not in text
    assert playbook.titles() == ["QĐ-01 | Lỗi không tái hiện được", "QĐ-03 | Mục ba"]
    assert playbook.next_id(text) == "QĐ-04"
    assert playbook.prompt_block(RISK_HIGH) == "" and "QĐ-01" in playbook.prompt_block(2)

    qd = playbook.append_entry({"title": "Câu chữ nút", "situation": "Đại ca không\ncho chữ.",
                                "action": "Chọn câu   như màn quanh đó.", "not_when": ""},
                               source="thử 23/09")
    assert qd == "QĐ-04"
    raw = path.read_text(encoding="utf-8")
    assert raw.endswith("## QĐ-04 | Câu chữ nút\n- Tình huống: Đại ca không cho chữ.\n"
                        "- Bot làm: Chọn câu như màn quanh đó.\n- Không áp khi: chưa ghi\n"
                        "- Nguồn: thử 23/09\n")
    assert "\n\n## QĐ-04" in raw
    #  Thiếu ý chính thì không ghi; không có tệp thì đọc ra rỗng, ghi thì báo lỗi rõ.
    with pytest.raises(playbook.PlaybookError, match="action"):
        playbook.append_entry({"title": "a", "situation": "b", "action": ""}, source="x")
    monkeypatch.setattr(settings, "AGENT_PLAYBOOK_PATH", str(tmp_path / "khong-co.md"))
    assert playbook.load_text() == ""
    with pytest.raises(playbook.PlaybookError, match="không đọc được"):
        playbook.append_entry({"title": "a", "situation": "b", "action": "c"}, source="x")


def test_so_chan_chu_de_luon_hoi(monkeypatch, tmp_path):
    from app.modules.agent_hub import playbook

    assert playbook.protected_topic("công nợ để âm cũng được") == "công nợ"
    assert playbook.protected_topic("cho phòng kế toán thêm quyền duyệt") == "phân quyền"
    assert playbook.protected_topic("thêm cột ngày giao dưới cơ sở dữ liệu") == "cấu trúc cơ sở dữ liệu"
    assert playbook.protected_topic("cần migration thêm bảng") == "cấu trúc cơ sở dữ liệu"
    #  Cột của bảng GIAO DIỆN không phải cấu trúc DB (bắt nhầm ở lượt thử thật 23/09).
    assert playbook.protected_topic("cột mới thêm vào bảng danh sách thì để ẩn mặc định") == ""
    assert playbook.protected_topic("sửa câu feedback khi debug lỗi") == ""
    assert playbook.protected_topic("đổi kiểu cột trong DB") == "cấu trúc cơ sở dữ liệu"
    assert playbook.protected_topic("gộp thẳng vào nhánh erp-v2") == "gộp mã vào nhánh nền"
    assert playbook.protected_topic("đơn giá lấy 4 số lẻ") == "tiền"
    assert playbook.protected_topic("đổi nhãn nút Lưu thành Ghi lại") == ""
    assert playbook.protected_topic("gộp dòng trùng số chứng từ trên bản in") == ""
    path = _so_tam(monkeypatch, tmp_path)
    before = path.read_text(encoding="utf-8")
    with pytest.raises(playbook.PlaybookError, match="thanh toán|tiền"):
        playbook.append_entry({"title": "Làm tròn", "situation": "Phiếu thanh toán lệch lẻ.",
                               "action": "Làm tròn xuống."}, source="x")
    assert path.read_text(encoding="utf-8") == before


def test_lech_ke_hoach_khong_tinh_tai_lieu_md_nhung_cam_sua_so():
    from app.modules.agent_hub.coder import check_drift, is_banned_path

    plan = ["backend/app/a.py"]
    assert check_drift(["backend/app/a.py", "doc/x.md", "doc/y.md", "frontend-v2/README.md"],
                       plan, max_files=25) == ""
    assert "ngoài kế hoạch" in check_drift(["backend/app/a.py", "backend/app/b.py"], plan, max_files=25)
    assert "vượt trần" in check_drift([f"doc/{i}.md" for i in range(4)], plan, max_files=3)
    #  Sổ quyết định chỉ ghi qua nút đại ca duyệt; `claude` sửa vào là tệp cấm.
    assert is_banned_path("doc/agent-hub/03-so-quyet-dinh.md")
    assert "tệp cấm" in check_drift(["doc/agent-hub/03-so-quyet-dinh.md"], plan, max_files=25)


def test_ke_hoach_nap_so_va_ghi_gia_dinh_vao_ban_ke_hoach(db, bot, monkeypatch, tmp_path):
    service, _, _ = bot
    _so_tam(monkeypatch, tmp_path)
    seen: list[dict] = []
    _fake_plan(monkeypatch, service, seen=seen,
               assumptions=["Theo QĐ-01: không có mã phiếu, sửa theo mô tả."])
    task = _task_with_plan(db, service, [], status=service.ST_TRIAGE, risk_level=2)
    service.plan_task(db, task)
    assert seen[0]["strict"] is False and "## QĐ-01" in seen[0]["playbook"]
    assert task.status == service.ST_PLAN
    assert "**Em tự quyết, không hỏi lại:**\n- Theo QĐ-01" in task.plan


def test_viec_rui_ro_cao_khong_nap_so_va_moi_gia_dinh_thanh_cau_hoi(db, bot, monkeypatch, tmp_path):
    service, _, _ = bot
    _so_tam(monkeypatch, tmp_path)
    seen: list[dict] = []
    _fake_plan(monkeypatch, service, seen=seen, risk_level=3,
               assumptions=["Em giả định: làm tròn tiền xuống hàng đồng."])
    task = _task_with_plan(db, service, [], status=service.ST_TRIAGE, risk_level=RISK_HIGH)
    service.plan_task(db, task)
    assert seen[0]["strict"] is True and seen[0]["playbook"] == ""
    assert task.status == _ST_NI and "Em tự quyết" not in task.plan
    assert task.questions == ["làm tròn tiền xuống hàng đồng — đại ca đồng ý không?"]
    #  Việc vào ở mức vừa nhưng chính lượt lập kế hoạch nâng lên cao: giả định vẫn thành câu hỏi.
    task2 = _task_with_plan(db, service, [], status=service.ST_TRIAGE, risk_level=2)
    service.plan_task(db, task2)
    assert task2.status == _ST_NI and task2.questions


def test_tra_loi_hoi_lai_gan_vao_viec_cu_lap_lai_ke_hoach_va_de_xuat_ghi_so(db, bot, monkeypatch, tmp_path):
    """Lỗ cũ: câu trả lời rơi vào INBOX và đẻ việc MỚI, việc cũ treo mãi ở «Đang hỏi lại»."""
    from app.modules.agent_hub.model import AgentMessage, AgentRun, AgentTask, AgentTaskItem

    service, _, _ = bot
    path = _so_tam(monkeypatch, tmp_path)
    sent = _capture_send(monkeypatch, service)
    seen: list[dict] = []
    calls: list[dict] = []
    _fake_plan(monkeypatch, service, seen=seen)
    _fake_rule(monkeypatch, service, calls=calls)
    monkeypatch.setattr(service.manager, "run_intent",
                        lambda *a, **kw: pytest.fail("câu trả lời không được đi phân loại"))
    task = _task_hoi_lai(db, service)
    service.send_plan_card(db, task)
    assert [b[1] for b in sent[-1][1]] == [f"ans:{task.id}", f"no:{task.id}"]
    assert "/gom" not in sent[-1][0]
    n_tasks = db.query(AgentTask).count()

    service.handle_message(db, _msg("màn đơn hàng, không có mã phiếu, cứ sửa theo mô tả"))
    row = db.query(AgentMessage).filter_by(direction=service.DIR_IN).order_by(AgentMessage.id.desc()).first()
    assert row.action == ACT_PLAN_ANSWER and row.task_id == task.id
    assert db.query(AgentTask).count() == n_tasks
    assert db.query(AgentTaskItem).filter_by(task_id=task.id, ref_id=row.id).count() == 1
    assert "Bot hỏi: Lỗi ở màn nào, có mã phiếu không?" in task.summary
    assert "Đại ca trả lời: màn đơn hàng" in task.summary
    assert "Đại ca trả lời: màn đơn hàng" in seen[0]["summary"]
    assert task.status == service.ST_PLAN and task.questions == []
    assert calls[0]["questions"] == ["Lỗi ở màn nào, có mã phiếu không?"]
    assert calls[0]["known"] == ["QĐ-01 | Lỗi không tái hiện được"]
    text, buttons = sent[-1]
    assert "lần sau gặp tình huống tương tự" in text and "Thiếu mã phiếu" in text
    assert [b[1] for b in buttons] == [f"qdok:{task.id}", f"qdno:{task.id}"]

    service.handle_callback(db, _callback(f"qdok:{task.id}"))
    raw = path.read_text(encoding="utf-8")
    assert "## QĐ-02 | Thiếu mã phiếu thì sửa theo mô tả" in raw
    assert f"từ việc {task.code}" in raw
    assert "Đã ghi <b>QĐ-02" in sent[-1][0]
    rule = db.query(AgentRun).filter_by(task_id=task.id, stage=STAGE_RULE).one()
    assert rule.artifact["state"] == "da_ghi" and rule.artifact["qd_id"] == "QĐ-02"
    #  Bấm lần hai: không ghi thêm mục nào.
    service.handle_callback(db, _callback(f"qdok:{task.id}"))
    assert path.read_text(encoding="utf-8") == raw


def test_bam_khong_thi_khong_ghi_va_cau_dinh_tien_thi_khong_de_xuat(db, bot, monkeypatch, tmp_path):
    from app.modules.agent_hub.model import AgentRun

    service, _, _ = bot
    path = _so_tam(monkeypatch, tmp_path)
    before = path.read_text(encoding="utf-8")
    sent = _capture_send(monkeypatch, service)
    _fake_plan(monkeypatch, service)
    _fake_rule(monkeypatch, service)
    task = _task_hoi_lai(db, service)
    service.send_plan_card(db, task)
    service.handle_message(db, _msg("cứ sửa theo mô tả"))
    service.handle_callback(db, _callback(f"qdno:{task.id}"))
    assert path.read_text(encoding="utf-8") == before
    assert db.query(AgentRun).filter_by(task_id=task.id, stage=STAGE_RULE).one().artifact["state"] == "bo"

    #  Câu trả lời dính công nợ: không gọi model nháp, nói rõ lần sau vẫn hỏi.
    monkeypatch.setattr(service.manager, "run_rule_draft",
                        lambda *a, **kw: pytest.fail("chủ đề luôn hỏi không được nháp mục sổ"))
    task2 = _task_hoi_lai(db, service)
    service.send_plan_card(db, task2)
    service.handle_message(db, _msg("công nợ để âm cũng được"))
    #  ai-CR-021: im lặng, không nhắn «dính tiền nên em vẫn hỏi» mỗi lần nữa.
    assert not any("lần sau gặp em vẫn hỏi" in s for s, _b in sent)
    #  Model nói không dùng lại được: im lặng, không thẻ.
    _fake_rule(monkeypatch, service, generalizable=False)
    task3 = _task_hoi_lai(db, service)
    service.send_plan_card(db, task3)
    n = len(sent)
    service.handle_message(db, _msg("lần này thì bỏ qua bước 2"))
    assert not any("qdok" in b[1] for _t, bs in sent[n:] for b in bs)
    assert db.query(AgentRun).filter_by(task_id=task3.id, stage=STAGE_RULE).one().artifact["state"] == "khong_ap"


def test_tin_xen_giua_thi_khong_gan_va_nut_tra_loi_mo_lai_cua(db, bot, monkeypatch, tmp_path):
    service, _, asked = bot
    _so_tam(monkeypatch, tmp_path)
    _capture_send(monkeypatch, service)
    _fake_plan(monkeypatch, service)
    _fake_rule(monkeypatch, service, generalizable=False)
    _fake_intent(monkeypatch, service, "hoi")
    task = _task_hoi_lai(db, service)
    service.send_plan_card(db, task)
    service.log_message(db, service.DIR_IN, "12345", 8, "tồn kho hôm nay bao nhiêu", action="hoi")
    db.commit()
    service.handle_message(db, _msg("màn đơn hàng"))
    assert asked == ["màn đơn hàng"] and task.status == _ST_NI
    #  Bấm «Trả lời câu hỏi»: cửa mở lại, tin kế gắn vào việc.
    service.handle_callback(db, _callback(f"ans:{task.id}"))
    service.handle_message(db, _msg("màn đơn hàng"))
    assert task.status == service.ST_PLAN and "Đại ca trả lời: màn đơn hàng" in task.summary
    #  Việc không còn chờ trả lời thì nút không mở cửa.
    service.handle_callback(db, _callback(f"ans:{task.id}"))
    from app.modules.agent_hub.model import AgentMessage
    last = db.query(AgentMessage).order_by(AgentMessage.id.desc()).first()
    assert last.action != ACT_WAIT_PLAN_ANSWER


def test_sua_lai_mo_cua_nhan_y_kien_khong_can_gom(db, bot, monkeypatch, tmp_path):
    service, _, _ = bot
    _so_tam(monkeypatch, tmp_path)
    sent = _capture_send(monkeypatch, service)
    _fake_plan(monkeypatch, service)
    _fake_rule(monkeypatch, service, generalizable=False)
    task = _task_with_plan(db, service, ["backend/app/x.py"])
    service.handle_callback(db, _callback(f"fix:{task.id}"))
    assert task.status == _ST_NI and "cần sửa kế hoạch thế nào" in sent[-1][0]
    service.handle_message(db, _msg("bỏ bước 2, chỉ sửa backend"))
    assert "Bot hỏi: Đại ca muốn sửa kế hoạch thế nào?" in task.summary
    assert task.status == service.ST_PLAN


def test_de_bai_claude_nap_so_tru_viec_rui_ro_cao(db, bot, monkeypatch, tmp_path):
    from app.modules.agent_hub import coder

    service, _, _ = bot
    _so_tam(monkeypatch, tmp_path)
    task = _task_with_plan(db, service, ["backend/app/x.py"], risk_level=2)
    brief = coder.build_brief(task, [])
    assert "## Sổ quyết định của đại ca" in brief and "## QĐ-01" in brief
    assert "KHÔNG còn là lý do dừng" in brief and "«Theo QĐ-xx:»" in brief
    assert "tài liệu `.md` không tính" in brief
    high = _task_with_plan(db, service, ["backend/app/x.py"], risk_level=RISK_HIGH)
    brief = coder.build_brief(high, [])
    assert "Sổ quyết định" not in brief and "## QĐ-01" not in brief
    assert "không tái hiện được lỗi · thiếu dữ liệu để quyết" in brief and "RỦI RO CAO" in brief


# ---------------------------------------------------------------------------
# ai-CR-016: bot tự xưng Đậu Đậu trên Telegram, Trợ lý AI web giữ nguyên
# ---------------------------------------------------------------------------
def test_tro_ly_tren_telegram_nhan_persona_dau_dau(db, monkeypatch):
    from app.modules.agent_hub import service
    from app.modules.assistant import service as assistant_service

    monkeypatch.setattr(settings, "AGENT_TELEGRAM_CHAT_ID", "12345")
    sent: list[str] = []
    monkeypatch.setattr(service.telegram, "send", lambda text, **kw: sent.append(text) or 1)
    monkeypatch.setattr(service.telegram, "send_chat_action", lambda *a, **kw: None)
    monkeypatch.setattr(service, "_assistant_user", lambda db: object())
    seen: dict = {}

    def fake_ask(question, **kw):
        seen.update(kw)
        return {"text": "Em là Đậu Đậu.", "tool_calls": []}

    monkeypatch.setattr(assistant_service, "ask", fake_ask)
    service.answer_question(db, "12345", "em tên gì")
    assert "Đậu Đậu" in seen["system"] and "«em»" in seen["system"]
    assert sent[-1] == "Em là Đậu Đậu."

    def boom(question, **kw):
        raise RuntimeError("429")

    monkeypatch.setattr(assistant_service, "ask", boom)
    service.answer_question(db, "12345", "em tên gì")
    assert sent[-1].startswith("Đậu Đậu chưa trả lời được")


def test_loi_chao_va_de_bai_claude_goi_ten_dau_dau(db, bot, monkeypatch):
    from app.modules.agent_hub import coder
    from app.modules.assistant import knowledge

    service, sent, _ = bot
    service._run_command(db, "12345", "/start")
    assert sent[-1].startswith("Em là <b>Đậu Đậu</b>.")
    task = _task_with_plan(db, service, ["backend/app/x.py"])
    assert "Bạn là Đậu Đậu, bot sửa mã" in coder.build_brief(task, [])
    #  Trợ lý AI trên web KHÔNG đổi tên: định nghĩa gốc không nhắc Đậu Đậu.
    assert "Đậu Đậu" not in knowledge.DEFINITION


def test_viec_ket_o_tram_gom_duoc_lap_lai_ke_hoach(db, bot, monkeypatch):
    """Ca AI-0006: worker bị khởi động lại giữa lượt PLAN, việc nằm ở TRIAGE mãi, đại ca chờ mãi."""
    from datetime import timedelta as _td

    from app.modules.agent_hub.model import AgentRun

    service, _, _ = bot
    planned: list[str] = []
    monkeypatch.setattr(service, "plan_task", lambda db, task: planned.append(task.code))
    task = _task_with_plan(db, service, [], status=service.ST_TRIAGE)
    now = task.updated_at + _td(minutes=1)
    assert service.resume_stuck_plans(db, now) == 0          # vừa gom, lượt PLAN có thể đang chạy
    now = task.updated_at + _td(minutes=4)
    assert service.resume_stuck_plans(db, now) == 1 and planned == [task.code]
    #  Gemini hỏng thật hai lần (có ghi sổ, đã nhắn lỗi): thôi thử, khỏi mỗi phút một tin lỗi.
    for _ in range(2):
        db.add(AgentRun(task_id=task.id, stage=service.STAGE_PLAN, provider="agent_gemini", model="x",
                        status=service.RUN_ERROR, started_at=datetime.now()))
    db.commit()
    assert service.resume_stuck_plans(db, now) == 0 and planned == [task.code]
    #  Việc đã sang trạm khác thì không đụng.
    other = _task_with_plan(db, service, ["backend/app/x.py"])
    assert service.resume_stuck_plans(db, other.updated_at + _td(minutes=10)) == 0



# ---------------------------------------------------------------------------
# ai-CR-017: rà soát mã thật trước khi lập kế hoạch + nhánh nền lấy từ GitHub
# ---------------------------------------------------------------------------
from app.modules.agent_hub.constants import ST_SCANNING, STAGE_SCAN  # noqa: E402

_SCAN_OUT = (
    "**Kết luận:** màn v1 đã tự điền phòng ban từ bao-CR-376, màn v2 thì chưa.\n"
    "- v2 lập phiếu mới với `head_of_dept_id: 0` và không chờ hồ sơ nhân sự.\n\n"
    "```json\n"
    '{"already_fixed": "v1 đã có ở bao-CR-376", "root_cause": "v2 không chờ hồ sơ nhân sự", '
    '"files": ["frontend-v2/src/modules/procurement/pages/purchase-request-detail-page.tsx", ".env"], '
    '"risk_level": 2, "questions": []}\n'
    "```"
)


def test_nhanh_nen_lay_tu_github_khi_co_khoa_lui_ve_ban_o_may_khi_khong(monkeypatch):
    from app.modules.agent_hub import coder

    calls: list[tuple] = []
    fail = {"on": False}

    def fake_git(cwd, *args, timeout=0, extra_env=None):
        calls.append((args, extra_env))
        if fail["on"] and "github.com" in " ".join(args):
            raise coder.CoderError("mạng hỏng")
        return ""

    monkeypatch.setattr(coder, "_git", fake_git)
    monkeypatch.setattr(settings, "AGENT_BASE_BRANCH", "erp-v2")
    monkeypatch.setattr(settings, "AGENT_GITHUB_REPO", "g/p")
    monkeypatch.setattr(settings, "AGENT_MAIN_BRANCH", "main")
    monkeypatch.setenv("AGENT_GITHUB_TOKEN", "ghp_x")
    coder.fetch_base("/w/base")
    args, env = calls[-1]
    #  ai-CR-018: kéo cả main để lượt rà soát so được main với nhánh nền.
    assert args == ("fetch", "https://github.com/g/p.git", "+refs/heads/erp-v2:refs/remotes/origin/erp-v2",
                    "+refs/heads/main:refs/remotes/origin/main")
    assert env["GIT_CONFIG_KEY_0"] == "http.extraheader" and len(calls) == 1
    fail["on"] = True
    calls.clear()
    coder.fetch_base("/w/base")
    assert [c[0] for c in calls[1:]] == [("fetch", "--prune", "origin", "erp-v2"), ("fetch", "origin", "main")]
    calls.clear()
    monkeypatch.delenv("AGENT_GITHUB_TOKEN")
    coder.fetch_base("/w/base")
    assert [c[0] for c in calls] == [("fetch", "--prune", "origin", "erp-v2"), ("fetch", "origin", "main")]


def test_tach_tin_nhan_va_json_cua_luot_ra_soat():
    from app.modules.agent_hub.coder import parse_scan

    message, info = parse_scan(_SCAN_OUT)
    assert message.startswith("**Kết luận:**") and "```" not in message
    assert info["root_cause"] == "v2 không chờ hồ sơ nhân sự"
    #  Tệp cấm lọt vào danh sách thì bị gạt ra, không đi tiếp vào kế hoạch.
    assert info["files"] == ["frontend-v2/src/modules/procurement/pages/purchase-request-detail-page.tsx"]
    assert parse_scan("chỉ có chữ, quên khối json") == ("chỉ có chữ, quên khối json", {})


def test_gom_xong_thi_giao_ra_soat_va_bao_da_nhan_viec(db, bot, monkeypatch):
    from app.modules.agent_hub import coder

    service, _, _ = bot
    sent = _capture_send(monkeypatch, service)
    monkeypatch.setattr(settings, "AGENT_CODER_ENABLED", True)
    dispatched: list[int] = []
    monkeypatch.setattr(coder, "dispatch_scan", lambda tid: dispatched.append(tid))
    monkeypatch.setattr(service, "plan_task", lambda db, t: pytest.fail("chưa rà soát đã lập kế hoạch"))
    task = _task_with_plan(db, service, [], status=service.ST_TRIAGE)
    service.start_scan(db, task)
    assert task.status == ST_SCANNING and dispatched == [task.id]
    assert "Đậu Đậu nhận việc" in sent[-1][0] and "đang đọc mã" in sent[-1][0]
    #  Broker chết: không bỏ rơi việc, lập kế hoạch theo tài liệu ngay.
    planned: list[str] = []
    monkeypatch.setattr(service, "plan_task", lambda db, t: planned.append(t.code))
    monkeypatch.setattr(coder, "dispatch_scan", lambda tid: (_ for _ in ()).throw(RuntimeError("redis")))
    task2 = _task_with_plan(db, service, [], status=service.ST_TRIAGE)
    service.start_scan(db, task2)
    assert planned == [task2.code] and task2.status == service.ST_TRIAGE
    #  Runner tắt: như trước ai-CR-017.
    monkeypatch.setattr(settings, "AGENT_CODER_ENABLED", False)
    task3 = _task_with_plan(db, service, [], status=service.ST_TRIAGE)
    service.start_scan(db, task3)
    assert planned[-1] == task3.code


def _fake_scan_env(monkeypatch, coder, service, *, out=_SCAN_OUT, error=None):
    monkeypatch.setattr(coder, "prepare_worktree", lambda task: ("/worktrees/X", "bot/x"))
    monkeypatch.setattr(coder, "_git", lambda cwd, *a, **kw: "abc123def4567890\n")
    monkeypatch.setattr(coder.memory, "recall", lambda text: [])
    monkeypatch.setattr(coder.telegram, "send_chat_action", lambda *a, **kw: None)
    briefs: list[str] = []

    def fake_scan(wt, brief, *, session_id, timeout):
        briefs.append(brief)
        if error:
            raise coder.CoderError(error)
        return {"result": out, "num_turns": 7}

    monkeypatch.setattr(coder, "run_claude_scan", fake_scan)
    return briefs


def test_ra_soat_nhan_phan_tich_roi_lap_ke_hoach_tren_ma_that(db, bot, monkeypatch, tmp_path):
    from app.modules.agent_hub import coder
    from app.modules.agent_hub.model import AgentRun

    service, _, _ = bot
    _so_tam(monkeypatch, tmp_path)
    sent = _capture_send(monkeypatch, service)
    briefs = _fake_scan_env(monkeypatch, coder, service)
    seen: list[dict] = []
    _fake_plan(monkeypatch, service, seen=seen, plan_files=["purchase-request-detail-page.tsx"])
    task = _task_with_plan(db, service, [], status=ST_SCANNING)

    out = coder.scan_task(db, task)
    assert out["status"] == "ok" and out["head"].startswith("abc123")
    assert "CHỈ ĐỌC" in briefs[0] and "frontend-v2/" in briefs[0] and "`abc123def4`" in briefs[0]
    run = db.query(AgentRun).filter_by(task_id=task.id, stage=STAGE_SCAN).one()
    assert run.status == service.RUN_OK and run.artifact["info"]["already_fixed"].startswith("v1")
    texts = [t for t, _b in sent]
    analysis = next(t for t in texts if "em đã đọc mã" in t)
    assert "Kết luận:" in analysis and "```" not in analysis and "abc123de" in analysis
    #  Kế hoạch đọc kết quả rà soát, và tên tệp trơn được nối đủ đường dẫn từ rà soát.
    assert "Đã sửa sẵn: v1 đã có ở bao-CR-376" in seen[0]["review"]
    assert task.plan_files == ["frontend-v2/src/modules/procurement/pages/purchase-request-detail-page.tsx"]
    assert task.status == service.ST_PLAN
    #  Đề bài sửa mã sau này cũng mang theo kết quả rà soát.
    assert "Kết quả rà soát mã trước khi lập kế hoạch" in coder.build_brief(task, [])


def test_ra_soat_hong_van_lap_ke_hoach_theo_tai_lieu(db, bot, monkeypatch, tmp_path):
    from app.modules.agent_hub import coder
    from app.modules.agent_hub.model import AgentRun

    service, _, _ = bot
    _so_tam(monkeypatch, tmp_path)
    sent = _capture_send(monkeypatch, service)
    _fake_scan_env(monkeypatch, coder, service, error="claude thoát mã 1: hết hạn mức")
    seen: list[dict] = []
    _fake_plan(monkeypatch, service, seen=seen)
    task = _task_with_plan(db, service, [], status=ST_SCANNING)
    assert coder.scan_task(db, task)["status"] == "error"
    assert db.query(AgentRun).filter_by(task_id=task.id, stage=STAGE_SCAN).one().status == service.RUN_ERROR
    assert any("chưa rà soát được mã" in t and "hết hạn mức" in t for t, _b in sent)
    assert seen[0]["review"] == "" and task.status == service.ST_PLAN


def test_luot_ra_soat_bo_qua_khi_viec_khong_con_o_tram(db, bot, monkeypatch):
    from app.modules.agent_hub import coder, tasks

    service, _, _ = bot
    monkeypatch.setattr(settings, "AGENT_HUB_ENABLED", True)
    monkeypatch.setattr(settings, "AGENT_CODER_ENABLED", True)
    monkeypatch.setattr(tasks, "SessionLocal", lambda: db)
    monkeypatch.setattr(db, "close", lambda: None)
    monkeypatch.setattr(coder, "scan_task", lambda *a: pytest.fail("không được rà soát"))
    task = _task_with_plan(db, service, ["backend/app/x.py"])
    assert tasks.scan_task(task.id)["status"] == "skipped"


def test_viec_ket_o_ra_soat_duoc_lap_ke_hoach_theo_tai_lieu(db, bot, monkeypatch):
    from datetime import timedelta as _td

    from app.modules.agent_hub.model import AgentRun

    service, _, _ = bot
    sent = _capture_send(monkeypatch, service)
    planned: list[str] = []

    def fake_plan(db, t):
        planned.append(t.code)
        t.status = service.ST_PLAN        # như plan_task thật: có kế hoạch là rời TRIAGE

    monkeypatch.setattr(service, "plan_task", fake_plan)
    queued = _task_with_plan(db, service, [], status=ST_SCANNING)
    base = queued.updated_at
    #  Chưa có lượt rà soát: có thể đang xếp hàng sau một lượt sửa mã, chờ tới 45 phút.
    assert service.resume_stuck_plans(db, base + _td(minutes=20)) == 0
    assert service.resume_stuck_plans(db, base + _td(minutes=50)) == 1
    assert planned == [queued.code] and "không bắt đầu được" in sent[-1][0]
    #  Lượt rà soát đang chạy quá trần: đóng lỗi rồi lập kế hoạch; còn trong trần thì để yên.
    busy = _task_with_plan(db, service, [], status=ST_SCANNING)
    run = AgentRun(task_id=busy.id, stage=STAGE_SCAN, provider="claude_code", model="m",
                   status=service.RUN_RUNNING, started_at=busy.updated_at)
    db.add(run)
    db.commit()
    assert service.resume_stuck_plans(db, busy.updated_at + _td(minutes=5)) == 0
    assert service.resume_stuck_plans(db, busy.updated_at + _td(minutes=30)) == 1
    assert run.status == service.RUN_ERROR and "mất dấu" in run.error and planned[-1] == busy.code


def test_ra_soat_cat_cau_dan_va_hien_cau_can_dai_ca_quyet(db, bot, monkeypatch, tmp_path):
    """Lượt thật AI-0006: mở bằng «Giờ trả lời», và câu nghiệp vụ chỉ nằm trong JSON."""
    from app.modules.agent_hub import coder

    out = ("Đã xác minh đủ chắc chắn để báo cáo. Giờ trả lời.\n\n**Kết luận:** gửi thiếu mã phòng.\n"
           '```json\n{"files": ["backend/app/x.py"], "questions": ["Có chặn gửi duyệt không?"]}\n```')
    message, info = coder.parse_scan(out)
    assert message.startswith("**Kết luận:**") and info["questions"] == ["Có chặn gửi duyệt không?"]

    service, _, _ = bot
    _so_tam(monkeypatch, tmp_path)
    sent = _capture_send(monkeypatch, service)
    _fake_scan_env(monkeypatch, coder, service, out=out)
    seen: list[dict] = []
    _fake_plan(monkeypatch, service, seen=seen)
    task = _task_with_plan(db, service, [], status=ST_SCANNING)
    coder.scan_task(db, task)
    analysis = next(t for t, _b in sent if "em đã đọc mã" in t)
    assert "Giờ trả lời" not in analysis
    #  ai-CR-021: câu hỏi KHÔNG liệt kê ở đoạn phân tích nữa — thẻ kế hoạch là chỗ duy nhất hỏi,
    #  và câu kế hoạch quên nhắc thì tự thêm vào đó.
    assert "Có chặn gửi duyệt không?" not in analysis
    assert "đại ca CHƯA trả lời: Có chặn gửi duyệt không?" in seen[0]["review"]
    assert "**Còn chờ đại ca quyết:**\n- Có chặn gửi duyệt không?" in task.plan


def test_the_ke_hoach_doi_markdown_sang_html(db, bot, monkeypatch):
    """Đại ca báo 23/09: thẻ kế hoạch in thô dấu nháy `tệp` và dấu sao, không đậm nhạt gì."""
    service, _, _ = bot
    sent = _capture_send(monkeypatch, service)
    task = _task_with_plan(db, service, ["backend/app/x.py"])
    task.plan = "1. Sửa `backend/app/x.py` cho **đúng**.\n\n**Em tự quyết, không hỏi lại:**\n- Theo QĐ-01: a < b"
    task.test_plan = "Kiểm `x`"
    service.send_plan_card(db, task)
    text = sent[-1][0]
    assert "<code>backend/app/x.py</code>" in text and "<b>đúng</b>" in text
    assert "<b>Em tự quyết, không hỏi lại:</b>" in text and "a &lt; b" in text
    assert "`" not in text and "**" not in text
    #  Quá dài thì lùi về chữ thường đã thoát, không để Telegram từ chối cả tin.
    assert service._card_md("**x** " * 2000).startswith("**x**")



# ---------------------------------------------------------------------------
# ai-CR-018: rà soát so main với nhánh nền + đọc tài liệu ở máy đại ca
# ---------------------------------------------------------------------------
def test_de_bai_ra_soat_so_main_va_mo_thu_muc_tai_lieu_o_may(db, bot, monkeypatch, tmp_path):
    from app.modules.agent_hub import coder

    service, _, _ = bot
    monkeypatch.setattr(settings, "AGENT_BASE_BRANCH", "erp-v2")
    monkeypatch.setattr(settings, "AGENT_MAIN_BRANCH", "main")
    local = tmp_path / "local-docs"
    local.mkdir()
    monkeypatch.setattr(settings, "AGENT_LOCAL_DOCS_DIR", str(local))
    task = _task_with_plan(db, service, [], status=ST_SCANNING)
    brief = coder.build_scan_brief(task, [], "abc1234567890", "def9876543210")
    assert "git log --oneline origin/erp-v2..origin/main" in brief and "`def9876543`" in brief
    assert f"{local}/tai-lieu-ky-thuat/change-log-bao.md" in brief and "CHƯA COMMIT" in brief
    seen: list[list] = []
    monkeypatch.setattr(coder, "_run_cli", lambda cmd, stdin, wt, timeout: seen.append(cmd) or {})
    #  Tách khỏi thư mục ảnh (ai-CR-035): trong container thật /agent-files có sẵn nên lệnh mở thêm nó.
    monkeypatch.setattr(settings, "AGENT_FILES_DIR", "")
    coder.run_claude_scan("/wt", "x", session_id="s", timeout=1)
    assert seen[-1][-2:] == ["--add-dir", str(local)]
    #  Không có main hay không mount thư mục: đề bài không nhắc, lệnh không mở thêm thư mục.
    monkeypatch.setattr(settings, "AGENT_LOCAL_DOCS_DIR", str(tmp_path / "khong-co"))
    brief = coder.build_scan_brief(task, [], "abc1234567890", "")
    assert "origin/main" not in brief and "máy đại ca" not in brief
    coder.run_claude_scan("/wt", "x", session_id="s", timeout=1)
    assert "--add-dir" not in seen[-1]


def test_kho_tai_lieu_lay_them_tai_lieu_bot_khi_thu_muc_o_may_khong_co(monkeypatch, tmp_path):
    from app.modules.agent_hub import memory

    root = tmp_path / "app"
    (root / "doc" / "tai-lieu-ky-thuat").mkdir(parents=True)
    (root / "doc" / "tai-lieu-ky-thuat" / "change-log-bao.md").write_text("x", encoding="utf-8")
    bot_docs = tmp_path / "agent-docs"
    bot_docs.mkdir()
    (bot_docs / "03-so-quyet-dinh.md").write_text("y", encoding="utf-8")
    monkeypatch.setattr(memory, "find_doc_root", lambda: root)
    monkeypatch.setattr(settings, "AGENT_PLAYBOOK_PATH", str(bot_docs / "03-so-quyet-dinh.md"))
    files = memory.collect_files()
    rels = sorted(memory.rel_path(p, root) for p in files)
    assert rels == ["doc/agent-hub/03-so-quyet-dinh.md", "doc/tai-lieu-ky-thuat/change-log-bao.md"]
    #  Thư mục ở máy đã có doc/agent-hub thì không lấy đôi.
    (root / "doc" / "agent-hub").mkdir()
    assert all("agent-docs" not in str(p) for p in memory.collect_files())



# ---------------------------------------------------------------------------
# ai-CR-019: cổng kiểm frontend-v2 trong runner
# ---------------------------------------------------------------------------
def _fe_worktree(tmp_path, lock="lock-1", with_modules=False):
    wt = tmp_path / "wt"
    fe = wt / "frontend-v2"
    (fe / "src" / "modules" / "procurement").mkdir(parents=True)
    (fe / "package.json").write_text('{"name": "erp"}', encoding="utf-8")
    (fe / "package-lock.json").write_text(lock, encoding="utf-8")
    (fe / "src" / "modules" / "procurement" / "a.tsx").write_text("x", encoding="utf-8")
    if with_modules:
        (fe / "node_modules").mkdir()
    return str(wt)


def test_vitest_chi_chay_thu_muc_vua_dung():
    from app.modules.agent_hub.coder import fe_vitest_targets

    assert fe_vitest_targets([
        "frontend-v2/src/modules/procurement/pages/a.tsx",
        "frontend-v2/src/modules/procurement/b.test.ts",
        "frontend-v2/src/shared/data-table/x.tsx",
        "frontend-v2/src/core/api/y.ts",
        "frontend-v2/src/main.tsx",
        "frontend/src/pages/Z.tsx",
        "backend/app/x.py",
    ]) == ["src/modules/procurement", "src/shared/data-table", "src/core/api"]
    #  Tệp nằm thẳng dưới src/modules (không thuộc phân hệ nào) thì không đẻ ra đường dẫn lạ.
    assert fe_vitest_targets(["frontend-v2/src/modules/index.ts"]) == []


def test_cong_frontend_typecheck_lint_vitest_theo_dung_thu_tu(monkeypatch, tmp_path):
    from app.modules.agent_hub import coder

    monkeypatch.setattr(coder, "_drop_privileges_kwargs", lambda: {})
    monkeypatch.setattr(settings, "AGENT_WORKTREE_ROOT", str(tmp_path))
    wt = _fe_worktree(tmp_path, with_modules=True)
    touched = ["frontend-v2/src/modules/procurement/a.tsx", "backend/app/x.py"]
    runs: list[tuple] = []
    rc = {"vitest": 1}

    class Proc:
        def __init__(self, code, out):
            self.returncode, self.stdout, self.stderr = code, out, ""

    def fake_run(cmd, cwd=None, **kw):
        runs.append((cmd, cwd, kw["env"]))
        name = cmd[0].rsplit("/", 1)[-1]
        return Proc(rc.get(name, 0), f"{name} out")

    monkeypatch.setattr(coder.subprocess, "run", fake_run)
    assert coder.run_fe_gate(wt, ["backend/app/x.py"])["status"] == "none"
    out = coder.run_fe_gate(wt, touched)
    assert [r[0] for r in runs] == [
        ["node_modules/.bin/tsc", "--noEmit"],
        ["node_modules/.bin/eslint", "src/modules/procurement/a.tsx"],
        ["node_modules/.bin/vitest", "run", "src/modules/procurement"],
    ]
    assert all(r[1].endswith("frontend-v2") for r in runs) and runs[0][2]["CI"] == "1"
    assert "CLAUDE_CODE_OAUTH_TOKEN" not in runs[0][2]
    assert out["status"] == "fail" and [s["ok"] for s in out["steps"]] == [True, True, False]
    assert "[vitest src/modules/procurement]" in out["output"]
    rc.clear()
    assert coder.run_fe_gate(wt, touched)["status"] == "pass"
    #  Không có thư viện: KHÔNG tính là xanh, nói rõ chưa kiểm được.
    skip = coder.run_fe_gate(wt, touched, note="cài thư viện hỏng: mạng")
    assert skip["status"] == "skip" and "mạng" in skip["output"]


def test_thu_vien_cai_mot_lan_moi_lockfile_va_gan_lien_ket(monkeypatch, tmp_path):
    from app.modules.agent_hub import coder

    monkeypatch.setattr(coder, "_drop_privileges_kwargs", lambda: {})
    monkeypatch.setattr(settings, "AGENT_WORKTREE_ROOT", str(tmp_path))
    installs: list[str] = []

    class Proc:
        returncode, stdout, stderr = 0, "", ""

    def fake_run(cmd, cwd=None, **kw):
        installs.append(cwd)
        (coder.Path(cwd) / "node_modules" / "vitest").mkdir(parents=True)
        return Proc()

    monkeypatch.setattr(coder.subprocess, "run", fake_run)
    wt = _fe_worktree(tmp_path)
    first = coder.ensure_fe_deps(wt)
    assert coder.ensure_fe_deps(wt) == first and len(installs) == 1
    assert installs[0].startswith(str(tmp_path / ".deps" / "fe-v2-"))
    exclude = tmp_path / "exclude"
    monkeypatch.setattr(coder, "_git", lambda cwd, *a, **kw: str(exclude) + "\n")
    assert coder.link_fe_deps(wt) == ""
    link = coder.Path(wt) / "frontend-v2" / "node_modules"
    assert link.is_symlink() and (link / "vitest").is_dir()
    assert coder.link_fe_deps(wt) == ""
    assert exclude.read_text(encoding="utf-8").splitlines() == ["/frontend-v2/node_modules"]
    #  Lockfile đổi: cài bộ mới, bộ cũ giữ lại tối đa FE_DEPS_KEEP bộ.
    for i in range(3):
        other = tmp_path / f"o{i}"
        other.mkdir()
        (other / "frontend-v2").mkdir()
        (other / "frontend-v2" / "package.json").write_text("{}", encoding="utf-8")
        (other / "frontend-v2" / "package-lock.json").write_text(f"lock-{i + 2}", encoding="utf-8")
        coder.ensure_fe_deps(str(other))
    assert len(list((tmp_path / ".deps").glob("fe-v2-*"))) == coder.FE_DEPS_KEEP
    #  Cài hỏng: lượt sửa mã vẫn chạy, chỉ trả lý do.
    monkeypatch.setattr(coder, "ensure_fe_deps", lambda wt, fe_dir=None: (_ for _ in ()).throw(coder.CoderError("npm 500")))
    wt2 = tmp_path / "wt2"
    (wt2 / "frontend-v2").mkdir(parents=True)
    (wt2 / "frontend-v2" / "package.json").write_text("{}", encoding="utf-8")
    assert coder.link_fe_deps(str(wt2)) == "npm 500"


def test_run_gate_gop_backend_va_frontend_va_the_hien_dong_rieng(db, bot, monkeypatch):
    from app.modules.agent_hub import coder

    service, _, _ = bot
    monkeypatch.setattr(coder, "_run_backend_gate",
                        lambda wt, t: {"status": "pass", "tests": ["test/backend/t.py"], "output": ""})
    fe = {"status": "fail", "steps": [{"name": "typecheck", "ok": True},
                                      {"name": "vitest src/modules/procurement", "ok": False}],
          "output": "[vitest] 1 failed"}
    monkeypatch.setattr(coder, "run_fe_gate", lambda wt, t, note="": fe)
    gate = coder.run_gate("/wt", ["frontend-v2/src/modules/procurement/a.tsx"])
    assert gate["status"] == "fail" and gate["backend"] == "pass" and "1 failed" in gate["output"]
    sent = _capture_send(monkeypatch, service)
    task = _task_with_session(db, service, coder)
    run = coder.latest_code_run(db, task)
    files = [{"path": "frontend-v2/src/modules/procurement/a.tsx", "added": 1, "deleted": 0, "in_plan": True}]
    coder.send_review_card(db, task, run, files=files, gate=gate, escalation="", report="", data={})
    text = sent[-1][0]
    assert "Cổng kiểm: <b>XANH</b>" in text
    assert "Frontend v2: <b>ĐỎ</b> ở vitest src/modules/procurement" in text and "1 failed" in text
    assert "CHƯA chạy" not in text
    body = coder.build_pr_body(task, files=files, gate=gate, report="", session_id="s")
    assert "Backend XANH" in body and "Frontend v2: **ĐỎ**" in body
    #  Không kiểm được thì nói thẳng, không gộp thành xanh.
    monkeypatch.setattr(coder, "run_fe_gate", lambda wt, t, note="": {"status": "skip", "steps": [],
                                                                       "output": "npm 500"})
    monkeypatch.setattr(coder, "_run_backend_gate", lambda wt, t: {"status": "none", "tests": [], "output": ""})
    gate = coder.run_gate("/wt", ["frontend-v2/src/a.ts"])
    assert gate["status"] == "none"
    assert coder.fe_gate_line(gate, html=True) == "Frontend v2: <b>CHƯA kiểm được</b> (npm 500)"



# ---------------------------------------------------------------------------
# ai-CR-020: /xem lịch sử một việc + dòng xác nhận khi bỏ + giờ Việt Nam
# ---------------------------------------------------------------------------
def test_gio_viet_nam_cho_nhung_gi_bot_noi():
    from app.modules.agent_hub import timeutil

    utc = datetime(2026, 9, 23, 3, 10)
    assert timeutil.fmt_local(utc) == "10:10 23/09"
    assert timeutil.fmt_local(datetime(2026, 9, 22, 20, 30), "%H:%M %d/%m") == "03:30 23/09"
    assert timeutil.to_utc(datetime(2026, 9, 23, 14, 30)) == datetime(2026, 9, 23, 7, 30)
    assert timeutil.fmt_local(None) == ""


def test_hen_14h30_la_gio_viet_nam_khong_phai_utc(db, bot, monkeypatch):
    """Lỗi có sẵn từ ai-CR-014: container chạy UTC nên «14:30» thành 21:30 giờ Việt Nam."""
    from app.modules.agent_hub import coder

    service, _, _ = bot
    _deploy_on(monkeypatch)
    sent = _capture_send(monkeypatch, service)
    monkeypatch.setattr(service, "now_local", lambda: datetime(2026, 9, 23, 10, 0))
    task = _task_with_session(db, service, coder)
    service.handle_callback(db, _callback(f"mgat:{task.id}"))
    service.handle_message(db, _msg("14:30"))
    run = _deploy_runs(db, task)[0]
    assert run.artifact["scheduled_for"] == "2026-09-23T07:30"
    assert "Đã hẹn <b>14:30 23/09</b>" in sent[-1][0]
    service.handle_callback(db, _callback(f"mg:{task.id}"))
    assert "lịch hẹn lúc 14:30 23/09" in sent[-1][0]
    #  Vòng beat so bằng giờ UTC của container: 07:29 UTC chưa tới, 07:31 tới.
    assert service.dispatch_due_deploys(db, datetime(2026, 9, 23, 7, 29)) == 0
    assert service.dispatch_due_deploys(db, datetime(2026, 9, 23, 7, 31)) == 1
    assert "Tới giờ hẹn 14:30" in sent[-1][0]


def test_tran_viec_moi_ngay_tinh_theo_ngay_viet_nam(db, bot, monkeypatch):
    from app.modules.agent_hub.model import AgentTask

    service, _, _ = bot
    monkeypatch.setattr(settings, "AGENT_DAILY_TASK_CAP", 5)
    #  06:00 sáng 23/09 giờ Việt Nam = 23:00 ngày 22/09 UTC.
    monkeypatch.setattr(service, "now_local", lambda: datetime(2026, 9, 23, 6, 0))
    for code, created in (("AI-0901", datetime(2026, 9, 22, 17, 30)),    # 00:30 23/09 VN: hôm nay
                          ("AI-0902", datetime(2026, 9, 22, 16, 30))):   # 23:30 22/09 VN: hôm qua
        db.add(AgentTask(code=code, title="x", summary="", status=service.ST_PLAN, created_at=created))
    db.commit()
    assert service._quota_left(db) == 4


def test_lenh_xem_ke_ca_viec_da_bo(db, bot, monkeypatch):
    from app.modules.agent_hub.model import AgentRun

    service, _, _ = bot
    sent = _capture_send(monkeypatch, service)
    task = _task_with_plan(db, service, ["backend/app/x.py"])
    task.plan = "1. Sửa `backend/app/x.py` cho **đúng**."
    db.add_all([
        AgentRun(task_id=task.id, stage=service.STAGE_PLAN, provider="agent_gemini", model="g",
                 status=service.RUN_OK, started_at=datetime(2026, 9, 23, 3, 14), duration_ms=25000),
        AgentRun(task_id=task.id, stage=STAGE_SCAN, provider="claude_code", model="c",
                 status=service.RUN_OK, started_at=datetime(2026, 9, 23, 3, 32), duration_ms=376000,
                 artifact={"message": "**Kết luận:** giao diện chỉ gửi tên phòng ban.", "info": {}}),
    ])
    db.commit()
    #  Bấm Bỏ: có dòng xác nhận trong khung chat, chỉ luôn cách xem lại.
    service.handle_callback(db, _callback(f"no:{task.id}"))
    assert task.status == service.ST_CANCELLED
    assert f"Đã bỏ <b>{task.code}</b>" in sent[-1][0] and f"/xem {task.code}" in sent[-1][0]

    num = int(task.code.split("-")[1])
    service._run_command(db, "12345", f"/xem ai-{num}")
    text = sent[-1][0]
    assert text.startswith(f"<b>{task.code}</b>") and "Trạng thái: <b>Đã bỏ</b>" in text
    assert "Ghi chú: Đại ca bỏ từ Telegram" in text
    assert "<pre>" in text and "10:14 Kế hoạch  xong  25s" in text and "10:32 Rà soát   xong  6p16" in text
    assert "<b>Rà soát mã</b>\n<b>Kết luận:</b>" in text
    assert "<b>Kế hoạch cuối</b>" in text and "<code>backend/app/x.py</code>" in text
    assert "`" not in text and "**" not in text
    service._run_command(db, "12345", "/xem AI-9999")
    assert "Không có việc <b>AI-9999</b>" in sent[-1][0]
    service._run_command(db, "12345", "/xem")
    assert "Cú pháp" in sent[-1][0]
    assert [service._task_code(a) for a in ("AI-0006", "ai-6", "AI6", "6", "ai 06", "abc")] == \
        ["AI-0006"] * 5 + [""]



# ---------------------------------------------------------------------------
# ai-CR-021: báo nhận ngay + báo đang chạy khi im quá 90 giây
# ---------------------------------------------------------------------------
def test_tin_giao_viec_duoc_bao_nhan_mot_lan_cho_ca_chum(db, bot, monkeypatch):
    from app.modules.agent_hub.model import AgentMessage

    service, _, _ = bot
    sent = _capture_send(monkeypatch, service)
    _fake_intent(monkeypatch, service, "viec")
    service.handle_message(db, _msg("màn công nợ lọc sai"))
    first = db.query(AgentMessage).filter_by(direction=service.DIR_IN).order_by(AgentMessage.id.desc()).first()
    assert first.action == "" and first.task_id == 0          # vẫn nằm INBOX cho vòng gom
    assert "Em nhận tin rồi, anh chờ em xíu" in sent[-1][0]
    acks = db.query(AgentMessage).filter_by(action=service.ACT_ACK).count()
    assert acks == 1
    #  Câu thứ hai trong cùng chùm (tin trước còn chờ gom): không kêu chuông thêm.
    n = len(sent)
    service.handle_message(db, _msg("cả màn yêu cầu thanh toán nữa"))
    assert len(sent) == n and db.query(AgentMessage).filter_by(action=service.ACT_ACK).count() == 1


def test_bao_dang_chay_sau_90_giay_roi_sua_chinh_tin_do(db, bot, monkeypatch):
    from datetime import timedelta as _td

    from app.modules.agent_hub.model import AgentMessage, AgentRun

    service, _, _ = bot
    sent = _capture_send(monkeypatch, service)
    edits: list[tuple] = []
    monkeypatch.setattr(service.telegram, "edit_text", lambda c, mid, text: edits.append((mid, text)) or True)
    task = _task_with_plan(db, service, [], status=ST_SCANNING)
    t0 = datetime(2026, 9, 23, 3, 0)
    db.add(AgentRun(task_id=task.id, stage=STAGE_SCAN, provider="claude_code", model="c",
                    status=service.RUN_RUNNING, started_at=t0))
    nhan = service.log_message(db, service.DIR_OUT, "12345", 50, "Đậu Đậu nhận việc", task_id=task.id)
    nhan.created_at = t0
    db.commit()

    assert service.heartbeat(db, t0 + _td(seconds=60)) == 0 and not sent
    assert service.heartbeat(db, t0 + _td(seconds=100)) == 1
    assert "em vẫn đang đọc mã" in sent[-1][0] and "đã 1 phút" in sent[-1][0]
    hb = db.query(AgentMessage).filter_by(action=service.ACT_HEARTBEAT).one()
    hb.created_at = t0 + _td(seconds=100)
    db.commit()
    #  Phút sau: SỬA tin cũ, không gửi tin mới; cùng phút thì không sửa lại.
    assert service.heartbeat(db, t0 + _td(seconds=200)) == 1
    assert len(sent) == 1 and "đã 3 phút" in edits[-1][1]
    assert service.heartbeat(db, t0 + _td(seconds=230)) == 0 and len(edits) == 1
    #  Quá 60 phút thì thôi; việc xong (sang PLAN) thì thôi.
    assert service.heartbeat(db, t0 + _td(minutes=70)) == 0
    task.status = service.ST_PLAN
    db.commit()
    assert service.heartbeat(db, t0 + _td(seconds=320)) == 0


def test_bao_dang_chay_khi_con_cho_runner(db, bot, monkeypatch):
    from datetime import timedelta as _td

    service, _, _ = bot
    sent = _capture_send(monkeypatch, service)
    task = _task_with_plan(db, service, [], status=ST_SCANNING)
    assert service.heartbeat(db, task.updated_at + _td(minutes=2)) == 1
    assert "chờ runner rảnh" in sent[-1][0]


def test_tin_bao_khong_lam_dut_mach_hen_gio(db, bot, monkeypatch):
    """Tin báo đang chạy của VIỆC KHÁC chen giữa lời mời hẹn giờ và câu trả lời: vẫn hẹn được."""
    from app.modules.agent_hub import coder

    service, _, _ = bot
    _deploy_on(monkeypatch)
    sent = _capture_send(monkeypatch, service)
    task = _task_with_session(db, service, coder)
    other = _task_with_plan(db, service, [], status=ST_SCANNING)
    service.handle_callback(db, _callback(f"mgat:{task.id}"))
    service.reply(db, "12345", "AI-x: em vẫn đang đọc mã", task_id=other.id, action=service.ACT_HEARTBEAT)
    db.commit()
    service.handle_message(db, _msg("45 phút nữa"))
    assert len(_deploy_runs(db, task)) == 1 and "Đã hẹn" in sent[-1][0]



def test_viec_rui_ro_cao_chi_hoi_mot_lan_moi_cau(db, bot, monkeypatch, tmp_path):
    """Ca AI-0007 (23/09): đoạn phân tích hỏi 2 câu, thẻ kế hoạch hỏi lại 3 câu bọc lời dẫn dài."""
    from app.modules.agent_hub.model import AgentRun

    service, _, _ = bot
    _so_tam(monkeypatch, tmp_path)
    _fake_plan(monkeypatch, service, risk_level=3, assumptions=[
        "Theo QĐ-09: đổi giá trị ô lọc thì về trang 1.",
        "Chưa làm: bỏ ô Số tiền — chờ đại ca quyết: Ô Số tiền bỏ hẳn, không dời đi đâu?",
    ])
    task = _task_with_plan(db, service, [], status=service.ST_TRIAGE, risk_level=2)
    db.add(AgentRun(task_id=task.id, stage=STAGE_SCAN, provider="claude_code", model="c",
                    status=service.RUN_OK, started_at=datetime.now(),
                    artifact={"message": "**Kết luận:** lệch hai ô.", "info": {"questions": [
                        "Ô Số tiền bỏ hẳn, không dời đi đâu?", "Hai ô Loại nợ giữ ở thanh nhanh hay dời?"]}}))
    db.commit()
    service.plan_task(db, task)
    assert task.status == _ST_NI
    assert task.questions == [
        "Theo QĐ-09: đổi giá trị ô lọc thì về trang 1 — đại ca đồng ý không?",
        "Ô Số tiền bỏ hẳn, không dời đi đâu?",
        "Hai ô Loại nợ giữ ở thanh nhanh hay dời?",
    ]
    assert not any("xác nhận giúp" in q or "Chưa làm" in q for q in task.questions)



def test_tran_suy_nghi_cua_bot_va_thu_lai_khi_json_cut(monkeypatch):
    """AI-0007 (23/09): Gemini nghĩ ~14 nghìn token, chạm trần, JSON bị cắt giữa chuỗi."""
    from app.modules.agent_hub import manager

    p = manager.AgentGeminiProvider()
    cfg = p._gen_config("gemini-flash-latest", 8192, 0.3, True)
    assert cfg["thinkingConfig"] == {"thinkingBudget": manager.THINKING_BUDGET}
    assert cfg["maxOutputTokens"] == 8192 + manager.THINKING_BUDGET
    assert p._gen_config("gemini-flash-latest", 4096, 0.2, False)["maxOutputTokens"] == 4096
    #  ai-CR-022: tắt hẳn, kể cả với bí danh mà lớp dùng chung không dám gửi 0.
    assert p._gen_config("gemini-flash-latest", 4096, 0.2, False)["thinkingConfig"] == {"thinkingBudget": 0}

    calls: list[bool] = []
    good = '{"plan": "1. Sửa", "plan_files": ["backend/app/x.py"], "test_plan": "", "risk_level": 2}'

    class Fake:
        def ask(self, messages, *, model, system, max_tokens, temperature, thinking=False):
            from dataclasses import replace

            calls.append(thinking)
            return replace(_ket_qua_model(), text='{"plan": "1. Màn Công nợ (cụt' if thinking else good)

    monkeypatch.setattr(manager, "get_provider", lambda: Fake())
    data, _ = manager.run_plan("t", "s", [])
    assert calls == [True, False] and data["plan_files"] == ["backend/app/x.py"]


def test_lap_ke_hoach_hong_thi_co_nut_lap_lai_khong_ket(db, bot, monkeypatch):
    service, _, _ = bot
    sent = _capture_send(monkeypatch, service)
    monkeypatch.setattr(service.memory, "recall", lambda text: [])

    def boom(*a, **kw):
        raise service.manager.ProviderError("Model không trả JSON: cụt")

    monkeypatch.setattr(service.manager, "run_plan", boom)
    task = _task_hoi_lai(db, service, questions=[])
    service.plan_task(db, task)
    text, buttons = sent[-1]
    assert "Lập kế hoạch cho" in text and "lỗi" in text
    assert [b[1] for b in buttons] == [f"plan:{task.id}", f"no:{task.id}"]



# ---------------------------------------------------------------------------
# ai-CR-022: bot nói gọn, bớt tiền Gemini
# ---------------------------------------------------------------------------
def test_bang_gia_biet_ten_that_cua_model_va_ke_hoach_co_ra_soat_thi_khong_suy_nghi(monkeypatch):
    from dataclasses import replace

    from app.modules.agent_hub import manager
    from app.modules.agent_hub.constants import estimate_cost_usd

    #  Google trả tên thật gemini-3.8-flash cho bí danh flash-latest; thiếu nó cột chi phí toàn 0.
    assert estimate_cost_usd("gemini-3.8-flash", 1_000_000, 1_000_000) == 2.8
    calls: list[bool] = []
    good = '{"plan": "1. Sửa", "plan_files": ["backend/app/x.py"], "test_plan": "", "risk_level": 2}'

    class Fake:
        def ask(self, messages, *, model, system, max_tokens, temperature, thinking=False):
            calls.append(thinking)
            return replace(_ket_qua_model(), text=good)

    monkeypatch.setattr(manager, "get_provider", lambda: Fake())
    manager.run_plan("t", "s", [], review="**Kết luận:** lỗi ở x.py")
    manager.run_plan("t", "s", [])
    assert calls == [False, True]
    assert manager.THINKING_BUDGET == 4096


def test_the_ke_hoach_gon_khong_liet_ke_tai_lieu(db, bot, monkeypatch):
    service, _, _ = bot
    sent = _capture_send(monkeypatch, service)
    task = _task_with_plan(db, service, ["backend/app/x.py"], risk_level=RISK_HIGH)
    task.related_docs = [{"path": "doc/tai-lieu-ky-thuat/change-log.md", "score": 0.7}] * 4
    service.send_plan_card(db, task)
    text = sent[-1][0]
    assert "Tài liệu đã tra" not in text and "change-log.md" not in text
    assert f"Rủi ro: <b>{service.RISK_LABELS[RISK_HIGH]}</b>" in text
    assert "Đụng tiền, phân quyền" not in text


def test_cau_ra_soat_da_tra_loi_thi_khong_hoi_lai(db, bot, monkeypatch, tmp_path):
    """AI-0007: đại ca đáp «oke theo ý của em», thẻ kế hoạch mới vẫn «Còn chờ đại ca quyết» hai câu cũ."""
    from app.modules.agent_hub import coder
    from app.modules.agent_hub.model import AgentRun

    service, _, _ = bot
    _so_tam(monkeypatch, tmp_path)
    _capture_send(monkeypatch, service)
    seen: list[dict] = []
    _fake_plan(monkeypatch, service, seen=seen)
    _fake_rule(monkeypatch, service, generalizable=False)
    task = _task_hoi_lai(db, service, questions=["Ô Số tiền bỏ hẳn không?"])
    db.add(AgentRun(task_id=task.id, stage=STAGE_SCAN, provider="claude_code", model="c",
                    status=service.RUN_OK, started_at=datetime.now(),
                    artifact={"message": "**Kết luận:** lệch.", "info": {"questions": ["Ô Số tiền bỏ hẳn không?"]}}))
    db.commit()
    service.send_plan_card(db, task)
    service.handle_message(db, _msg("oke theo ý của em nhé"))
    assert task.status == service.ST_PLAN and task.questions == []
    assert "Còn chờ đại ca quyết" not in (task.plan or "")
    assert "CHƯA trả lời" not in seen[0]["review"]
    assert "CHƯA trả lời" not in coder.scan_message_for(task)


def test_nap_kho_tai_lieu_chi_nhung_tep_co_doi(monkeypatch, tmp_path):
    """Nạp đè cả kho là ~1,2 triệu token nhúng mỗi lần cho vài dòng sửa — khoản tốn nhất của bot."""
    from types import SimpleNamespace

    from app.modules.agent_hub import memory

    root = tmp_path / "app"
    (root / "doc").mkdir(parents=True)
    same, changed = root / "doc" / "a.md", root / "doc" / "b.md"
    same.write_text("Nội dung A không đổi.", encoding="utf-8")
    changed.write_text("Nội dung B mới sửa.", encoding="utf-8")
    stored = {"doc/a.md": memory.chunk_text("Nội dung A không đổi."),
              "doc/b.md": memory.chunk_text("Nội dung B cũ.")}
    retagged: list[str] = []
    embedded: list[str] = []

    class Client:
        def scroll(self, collection_name, scroll_filter, limit, with_payload, with_vectors):
            rel = scroll_filter.must[0].match.value
            return [SimpleNamespace(payload={"chunk_index": i, "text": t})
                    for i, t in enumerate(stored.get(rel, []))], None

        def set_payload(self, collection_name, payload, points, wait):
            retagged.append(points.must[0].match.value)

        def delete(self, **kw):
            pass

    class Store:
        client = Client()

        def ensure_collection(self):
            pass

        def upsert(self, points):
            embedded.extend(p["payload"]["path"] for p in points)

    class Embedder:
        def embed(self, texts, is_query=False):
            return [[0.0] for _ in texts]

    monkeypatch.setattr(memory, "is_configured", lambda: True)
    monkeypatch.setattr(memory, "_get_store", lambda: Store())
    monkeypatch.setattr(memory, "_get_embedder", lambda: Embedder())
    monkeypatch.setattr(memory, "find_doc_root", lambda: root)
    monkeypatch.setattr(memory, "collect_files", lambda: [same, changed])
    out = memory.reindex()
    assert retagged == ["doc/a.md"] and set(embedded) == {"doc/b.md"}
    assert out["files"] == 2 and out["reused"] == 1



# ---------------------------------------------------------------------------
# ai-CR-023: hết lượt thì giữ phần dở + nút «Làm tiếp» nối đúng phiên
# ---------------------------------------------------------------------------
def test_het_luot_khong_con_la_that_bai_ma_co_nut_lam_tiep(db, bot, monkeypatch):
    """AI-0007 (23/09): hết 80 lượt khi mới sửa xong nửa việc, bot đóng «Thất bại», bỏ phần đã làm."""
    from app.modules.agent_hub import coder
    from app.modules.agent_hub.model import AgentRun

    service, _, _ = bot
    sent = _capture_send(monkeypatch, service)
    with pytest.raises(coder.MaxTurnsError):
        coder.parse_cli_json('{"subtype": "error_max_turns", "is_error": true, "num_turns": 81}')
    calls = _fake_runner(monkeypatch, coder, touched=["frontend-v2/src/a.tsx", "frontend-v2/src/b.tsx"])

    def out_of_turns(wt, brief, *, session_id, timeout, resume=False):
        assert "## Ngân sách lượt" in brief
        raise coder.MaxTurnsError("claude hết 81 lượt khi đang làm dở", {"num_turns": 81})

    monkeypatch.setattr(coder, "run_claude", out_of_turns)
    task = _task_with_plan(db, service, ["frontend-v2/src/a.tsx"], status=service.ST_CODE)
    out = coder.run_code_task(db, task)
    assert out["escalation"] == "max_turns" and task.status == _ST_NI
    run = db.query(AgentRun).filter_by(task_id=task.id, stage=coder.STAGE_CODE).one()
    assert run.status == service.RUN_ERROR and run.artifact["stopped"] == "max_turns"
    assert run.artifact["session_id"] and coder.resumable_session(db, task) == run.artifact["session_id"]
    assert ["git", "reset", "-q"] in calls           # không commit phần dở
    text, buttons = sent[-1]
    assert "đã sửa 2 tệp (+6/−2 dòng)" in text
    assert [b[1] for b in buttons] == [f"cont:{task.id}", f"no:{task.id}"]


def test_lam_tiep_noi_dung_phien_tren_dung_worktree(db, bot, monkeypatch, tmp_path):
    from app.modules.agent_hub import coder
    from app.modules.agent_hub.model import AgentRun

    service, _, _ = bot
    sent = _capture_send(monkeypatch, service)
    monkeypatch.setattr(settings, "AGENT_WORKTREE_ROOT", str(tmp_path))
    _fake_runner(monkeypatch, coder, touched=["frontend-v2/src/a.tsx"])
    monkeypatch.setattr(coder, "prepare_worktree", lambda task: pytest.fail("làm tiếp không được cắt lại worktree"))
    monkeypatch.setattr(coder, "run_claude", lambda *a, **kw: pytest.fail("làm tiếp phải nối phiên cũ"))
    resumed: list[str] = []
    monkeypatch.setattr(coder, "run_claude_continue", lambda wt, *, session_id, timeout: resumed.append(
        (wt, session_id)) or {"result": "## TỔNG KẾT\n1. xong", "num_turns": 20})
    task = _task_with_plan(db, service, ["frontend-v2/src/a.tsx"], status=_ST_NI, branch_name="bot/x")
    (tmp_path / task.code).mkdir()
    db.add(AgentRun(task_id=task.id, stage=coder.STAGE_CODE, provider="claude_code", model="m",
                    status=service.RUN_ERROR, started_at=datetime.now(),
                    artifact={"session_id": "sid-1", "stopped": "max_turns"}))
    db.commit()
    dispatched: list[int] = []
    monkeypatch.setattr(coder, "dispatch_continue", lambda tid: dispatched.append(tid))
    service.handle_callback(db, _callback(f"cont:{task.id}"))
    assert task.status == service.ST_CODE and dispatched == [task.id]
    assert "Em làm tiếp" in sent[-1][0]

    coder.run_code_task(db, task, resume=True)
    assert resumed == [(str(tmp_path / task.code), "sid-1")]
    assert task.status == service.ST_REVIEW
    #  Không còn phiên dở: nút «Làm tiếp» không giao gì.
    service.handle_callback(db, _callback(f"cont:{task.id}"))
    assert dispatched == [task.id]



# ---------------------------------------------------------------------------
# ai-CR-024: lượt sửa mã đi tiếp phiên rà soát, khỏi đọc lại mã từ đầu
# ---------------------------------------------------------------------------
def _scan_ready(db, service, coder, tmp_path, monkeypatch, *, age_hours=0.1):
    from datetime import timedelta as _td

    from app.modules.agent_hub.model import AgentRun

    monkeypatch.setattr(settings, "AGENT_WORKTREE_ROOT", str(tmp_path))
    task = _task_with_plan(db, service, ["frontend-v2/src/a.tsx"], status=service.ST_CODE)
    (tmp_path / task.code).mkdir()
    done = datetime.now() - _td(hours=age_hours)
    db.add(AgentRun(task_id=task.id, stage=STAGE_SCAN, provider="claude_code", model="c",
                    status=service.RUN_OK, started_at=done, finished_at=done,
                    artifact={"session_id": "scan-1", "message": "**Kết luận:** sửa a.tsx.", "info": {}}))
    db.commit()
    return task


def test_sua_ma_di_tiep_phien_ra_soat_tren_dung_worktree(db, bot, monkeypatch, tmp_path):
    """AI-0007: phiên sửa mã mới đọc lại từ đầu 40 tệp mà phiên rà soát vừa đọc xong."""
    from app.modules.agent_hub import coder
    from app.modules.agent_hub.model import AgentRun

    service, _, _ = bot
    _capture_send(monkeypatch, service)
    _fake_runner(monkeypatch, coder, touched=["frontend-v2/src/a.tsx"])
    monkeypatch.setattr(coder, "prepare_worktree", lambda task: pytest.fail("không được cắt lại worktree"))
    seen: list[dict] = []
    monkeypatch.setattr(coder, "run_claude", lambda wt, brief, *, session_id, timeout, resume=False: seen.append(
        {"wt": wt, "brief": brief, "sid": session_id, "resume": resume}) or {"result": "## TỔNG KẾT\n1. xong"})
    task = _scan_ready(db, service, coder, tmp_path, monkeypatch)
    coder.run_code_task(db, task)
    call = seen[0]
    assert call["resume"] is True and call["sid"] == "scan-1" and call["wt"] == str(tmp_path / task.code)
    assert "## Tiếp theo lượt rà soát" in call["brief"]
    assert "Kết quả rà soát mã trước khi lập kế hoạch" not in call["brief"]
    assert "## Kế hoạch đã duyệt" in call["brief"] and "## Luật bắt buộc" in call["brief"]
    run = db.query(AgentRun).filter_by(task_id=task.id, stage=coder.STAGE_CODE).one()
    assert run.artifact["session_id"] == "scan-1" and task.status == service.ST_REVIEW


def test_khong_noi_phien_ra_soat_khi_qua_cu_hoac_worktree_ban(db, bot, monkeypatch, tmp_path):
    from app.modules.agent_hub import coder

    service, _, _ = bot
    _capture_send(monkeypatch, service)
    #  Quá 6 tiếng: nhánh nền có thể đã đổi nhiều, mở phiên mới như cũ.
    old = _scan_ready(db, service, coder, tmp_path, monkeypatch, age_hours=7)
    assert coder.scan_session_to_reuse(db, old) == ""
    #  Worktree có thay đổi lạ: không nối.
    monkeypatch.setattr(coder, "_git", lambda cwd, *a, **kw: " M frontend-v2/src/a.tsx\n")
    task2 = _task_with_plan(db, service, ["frontend-v2/src/a.tsx"], status=service.ST_CODE)
    (tmp_path / task2.code).mkdir()
    from app.modules.agent_hub.model import AgentRun
    db.add(AgentRun(task_id=task2.id, stage=STAGE_SCAN, provider="claude_code", model="c",
                    status=service.RUN_OK, started_at=datetime.now(), finished_at=datetime.now(),
                    artifact={"session_id": "scan-2", "message": "x", "info": {}}))
    db.commit()
    assert coder.scan_session_to_reuse(db, task2) == ""
    monkeypatch.setattr(coder, "_git", lambda cwd, *a, **kw: "")
    assert coder.scan_session_to_reuse(db, task2) == "scan-2"


def test_phien_ra_soat_mat_thi_lui_ve_phien_moi(db, bot, monkeypatch, tmp_path):
    from app.modules.agent_hub import coder
    from app.modules.agent_hub.model import AgentRun

    service, _, _ = bot
    _capture_send(monkeypatch, service)
    _fake_runner(monkeypatch, coder, touched=["frontend-v2/src/a.tsx"])
    calls: list[tuple] = []

    def fake(wt, brief, *, session_id, timeout, resume=False):
        calls.append((resume, session_id))
        if resume:
            raise coder.CoderError("claude thoát mã 1: No conversation found with session ID: scan-1")
        return {"result": "## TỔNG KẾT\n1. xong"}

    monkeypatch.setattr(coder, "run_claude", fake)
    task = _scan_ready(db, service, coder, tmp_path, monkeypatch)
    coder.run_code_task(db, task)
    assert calls[0] == (True, "scan-1") and calls[1][0] is False and calls[1][1] != "scan-1"
    run = db.query(AgentRun).filter_by(task_id=task.id, stage=coder.STAGE_CODE).one()
    assert run.artifact["session_id"] == calls[1][1] and task.status == service.ST_REVIEW



def test_keo_tin_dong_giao_dich_truoc_khi_cho_telegram(db, bot, monkeypatch):
    """ai-CR-025: giữ giao dịch mở suốt 25 giây long-poll thì MySQL (REPEATABLE READ) cho bot xử
    nút bấm trên ảnh chụp CŨ — «Làm tiếp» AI-0007 bị bỏ qua im lặng."""
    service, _, _ = bot
    open_while_waiting: list[bool] = []

    def fake_fetch(offset, timeout=0):
        open_while_waiting.append(db.in_transaction())
        return []

    monkeypatch.setattr(service.telegram, "fetch_updates", fake_fetch)
    service.get_cursor(db)            # có giao dịch đang mở trước lượt kéo, như vòng thật
    assert db.in_transaction()
    service.poll_once(db, timeout=25)
    assert open_while_waiting == [False]



# ---------------------------------------------------------------------------
# ai-CR-026: quyền chạy vitest theo từng thư mục + nút «Sửa cho xanh»
# ---------------------------------------------------------------------------
def test_quyen_vitest_khai_theo_tung_thu_muc_co_that(tmp_path):
    """AI-0007: mẫu `… -- src/:*` không khớp `… -- src/modules/finance` (so theo nguyên từ)."""
    from app.modules.agent_hub import coder

    for d in ("modules/finance", "modules/procurement", "shared/data-table", "core/api"):
        (tmp_path / "frontend-v2" / "src" / d).mkdir(parents=True)
    tools = coder.allowed_tools(str(tmp_path)).split(",")
    assert "Bash(npm --prefix frontend-v2 run test -- src/modules/finance:*)" in tools
    assert "Bash(npm --prefix frontend-v2 run test -- src/shared/data-table:*)" in tools
    assert "Bash(npm --prefix frontend-v2 run test -- src/core/api:*)" in tools
    #  Không có mẫu nào chạy được cả bộ bài.
    assert not any(x.endswith("run test:*)") or x.endswith("run test --:*)") or "src/:*" in x for x in tools)
    assert coder.allowed_tools(str(tmp_path / "khong-co")) == coder.ALLOWED_TOOLS


def _red_review_task(db, service, coder):
    from app.modules.agent_hub.model import AgentRun

    task = _task_with_plan(db, service, ["frontend-v2/src/modules/finance/a.tsx"], status=service.ST_REVIEW,
                           branch_name="bot/x")
    gate = {"status": "fail", "backend": "none", "tests": [], "output": "",
            "frontend": {"status": "fail", "steps": [{"name": "vitest src/modules/finance", "ok": False}],
                         "output": "[vitest src/modules/finance] getByRole combobox «Mọi hình thức» không thấy"}}
    db.add(AgentRun(task_id=task.id, stage=coder.STAGE_CODE, provider="claude_code", model="m",
                    status=service.RUN_OK, started_at=datetime.now(),
                    artifact={"session_id": "code-1", "files": [], "gate": gate}))
    db.commit()
    return task, gate


def test_cong_do_thi_the_co_nut_sua_cho_xanh_va_nut_giao_runner(db, bot, monkeypatch):
    from app.modules.agent_hub import coder

    service, _, _ = bot
    sent = _capture_send(monkeypatch, service)
    task, gate = _red_review_task(db, service, coder)
    run = coder.latest_code_run(db, task)
    coder.send_review_card(db, task, run, files=[], gate=gate, escalation="", report="", data={})
    assert sent[-1][1][0] == ("Sửa cho xanh", f"fixg:{task.id}")
    dispatched: list[int] = []
    monkeypatch.setattr(coder, "dispatch_fix_gate", lambda tid: dispatched.append(tid))
    service.handle_callback(db, _callback(f"fixg:{task.id}"))
    assert task.status == service.ST_CODE and dispatched == [task.id]
    #  Cổng xanh: nút không có trên thẻ, bấm cũng không giao gì.
    task.status = service.ST_REVIEW
    run.artifact = {**run.artifact, "gate": {"status": "pass", "tests": [], "output": ""}}
    db.commit()
    coder.send_review_card(db, task, run, files=[], gate=run.artifact["gate"], escalation="", report="", data={})
    assert not any(b[1].startswith("fixg:") for b in sent[-1][1])
    service.handle_callback(db, _callback(f"fixg:{task.id}"))
    assert dispatched == [task.id]


def test_sua_cho_xanh_noi_phien_go_commit_cu_va_commit_lai(db, bot, monkeypatch, tmp_path):
    from app.modules.agent_hub import coder

    service, _, _ = bot
    _capture_send(monkeypatch, service)
    monkeypatch.setattr(settings, "AGENT_WORKTREE_ROOT", str(tmp_path))
    calls = _fake_runner(monkeypatch, coder, touched=["frontend-v2/src/modules/finance/a.test.tsx"])
    base_git = coder._git
    holder: dict = {}

    def git_with_log(cwd, *args, **kw):
        if args[:2] == ("log", "-1"):
            calls.append(["git", *args])
            return f"{holder['code']}: Sửa lỗi lọc nghỉ phép\n"
        return base_git(cwd, *args, **kw)

    monkeypatch.setattr(coder, "_git", git_with_log)
    monkeypatch.setattr(coder, "run_claude", lambda *a, **kw: pytest.fail("phải nối phiên, không mở mới"))
    seen: list[tuple] = []
    monkeypatch.setattr(coder, "run_claude_fix", lambda wt, brief, *, session_id, timeout: seen.append(
        (session_id, brief)) or {"result": "## TỔNG KẾT\n1. sửa bài kiểm"})
    task, _gate = _red_review_task(db, service, coder)
    holder["code"] = task.code
    task.status = service.ST_CODE
    db.commit()
    (tmp_path / task.code).mkdir()
    coder.run_code_task(db, task, fix_gate=True)
    sid, brief = seen[0]
    assert sid == "code-1" and "combobox «Mọi hình thức» không thấy" in brief and "Sửa cho XANH" in brief
    assert ["git", "reset", "--soft", "HEAD~1"] in calls
    assert any(c[:2] == ["git", "-c"] and "commit" in c for c in calls)
    assert task.status == service.ST_REVIEW



# ---------------------------------------------------------------------------
# ai-CR-027: thẻ gọn, không nút, ra lệnh bằng chữ
# ---------------------------------------------------------------------------
def _compact(monkeypatch):
    monkeypatch.setattr(settings, "AGENT_TG_COMPACT", True)


def test_the_ket_qua_gon_chi_noi_logic_da_kiem_va_lenh_tiep(db, bot, monkeypatch):
    from app.modules.agent_hub import coder

    service, _, _ = bot
    _compact(monkeypatch)
    sent = _capture_send(monkeypatch, service)
    task = _task_with_session(db, service, coder)
    run = coder.latest_code_run(db, task)
    report = ("## TỔNG KẾT\n1. Từng tệp: a.tsx +10 …(dài)\n2. …\n\n"
              "TÓM TẮT: Đưa 3 ô lọc ra thanh ngoài, dời ô khoảng tiền vào bộ lọc. Đã chạy vitest phân hệ "
              "Tài chính xanh. Rủi ro thấp, chỉ giao diện.")
    gate = {"status": "pass", "backend": "none", "tests": [],
            "frontend": {"status": "pass", "steps": [{"name": "typecheck", "ok": True},
                                                     {"name": "vitest src/modules/finance", "ok": True}]}}
    files = [{"path": "frontend-v2/src/a.tsx", "added": 10, "deleted": 1, "in_plan": True}]
    coder.send_review_card(db, task, run, files=files, gate=gate, escalation="", report=report, data={})
    text, buttons = sent[-1]
    assert buttons == [] and "Tệp đã sửa" not in text and "TỔNG KẾT" not in text
    assert "Đưa 3 ô lọc ra thanh ngoài" in text and "Rủi ro thấp" in text
    assert "giao diện v2 XANH (typecheck · vitest src/modules/finance)" in text
    assert f"«gộp {task.code}»" in text and f"«chi tiết {task.code}»" in text
    assert len(text) < 700
    #  Cổng đỏ: gợi ý sửa cho xanh, không gợi ý gộp.
    red = {**gate, "status": "fail", "frontend": {"status": "fail", "steps": [{"name": "vitest x", "ok": False}]}}
    coder.send_review_card(db, task, run, files=files, gate=red, escalation="", report=report, data={})
    assert f"«sửa cho xanh {task.code}»" in sent[-1][0] and "«gộp" not in sent[-1][0]
    #  Không có dòng TÓM TẮT thì lấy đoạn đầu, cắt ngắn.
    assert coder.report_summary("## TỔNG KẾT\n\nĐã sửa lọc ngày.\n\n2. chi tiết") == "Đã sửa lọc ngày."


def _review_task(db, service, coder, **kw):
    return _task_with_session(db, service, coder, **kw) if kw else _task_with_session(db, service, coder)


def test_nhan_chu_gop_viec_vua_sua_thi_gop_ngay(db, bot, monkeypatch):
    """Đại ca 23/09: «ví dụ anh muốn bot tự merge code từ commit sửa mới này qua erp thì sao»."""
    from app.modules.agent_hub import coder
    from app.modules.agent_hub.model import AgentMessage

    service, _, _ = bot
    _compact(monkeypatch)
    _capture_send(monkeypatch, service)
    merged: list[str] = []
    monkeypatch.setattr(service, "_dispatch_deploy", lambda db, chat, cb, task, deploy=True: merged.append(task.code))
    monkeypatch.setattr(service.manager, "run_intent", lambda *a, **kw: pytest.fail("lệnh không đi phân loại"))
    task = _task_with_session(db, service, coder)
    service.handle_message(db, _msg("tự merge code từ commit sửa mới này qua erp"))
    assert merged == [task.code]
    row = db.query(AgentMessage).filter_by(direction=service.DIR_IN).order_by(AgentMessage.id.desc()).first()
    assert row.action == service.ACT_COMMAND and row.task_id == task.id
    service.handle_message(db, _msg(f"gộp {task.code.lower()} đi"))
    assert merged == [task.code, task.code]


def test_gop_kem_gio_thi_hen_gio(db, bot, monkeypatch):
    from app.modules.agent_hub import coder

    service, _, _ = bot
    _compact(monkeypatch)
    _deploy_on(monkeypatch)
    sent = _capture_send(monkeypatch, service)
    monkeypatch.setattr(service, "now_local", lambda: datetime(2026, 9, 23, 10, 0))
    task = _task_with_session(db, service, coder)
    service.handle_message(db, _msg(f"gộp {task.code} lúc 20h"))
    run = _deploy_runs(db, task)[0]
    assert run.artifact["phase"] == "hen_gio" and run.artifact["scheduled_for"] == "2026-09-23T13:00"
    assert "Đã hẹn <b>20:00 23/09</b>" in sent[-1][0]


def test_cau_hoi_ve_viec_chi_tra_loi_tinh_trang_khong_lam_gi(db, bot, monkeypatch):
    from app.modules.agent_hub import coder

    service, _, _ = bot
    _compact(monkeypatch)
    sent = _capture_send(monkeypatch, service)
    monkeypatch.setattr(service, "_dispatch_deploy", lambda *a, **kw: pytest.fail("câu hỏi không được gộp"))
    task = _task_with_session(db, service, coder)
    service.handle_message(db, _msg("cái fix này đang trên nhánh nào, có merge sang erp-v2 được không"))
    text = sent[-1][0]
    assert "bot/x" in text and task.code in text and f"«gộp {task.code}»" in text


def test_yeu_cau_moi_co_chu_bo_hay_gop_khong_bi_hieu_nham_la_lenh(db, bot, monkeypatch):
    from app.modules.agent_hub import coder
    from app.modules.agent_hub.model import AgentMessage

    service, _, _ = bot
    _compact(monkeypatch)
    _capture_send(monkeypatch, service)
    _fake_intent(monkeypatch, service, "viec")
    monkeypatch.setattr(service, "_dispatch_deploy", lambda *a, **kw: pytest.fail("không được gộp"))
    task = _task_with_session(db, service, coder)
    for msg in ("bỏ nút tạo mới trên màn công nợ", "gộp hai cột ngày giao và ngày nhận", "bỏ ô từ đến"):
        service.handle_message(db, _msg(msg))
        row = db.query(AgentMessage).filter_by(direction=service.DIR_IN).order_by(AgentMessage.id.desc()).first()
        assert row.action == "" and row.task_id == 0, msg        # vẫn là việc MỚI chờ gom
    assert task.status == service.ST_REVIEW


def test_nhieu_viec_thi_hoi_lai_viec_nao(db, bot, monkeypatch):
    from app.modules.agent_hub import coder

    service, _, _ = bot
    _compact(monkeypatch)
    sent = _capture_send(monkeypatch, service)
    monkeypatch.setattr(service, "_dispatch_deploy", lambda *a, **kw: pytest.fail("chưa rõ việc nào"))
    a = _task_with_session(db, service, coder)
    b = _task_with_session(db, service, coder)
    service.handle_message(db, _msg("gộp đi"))
    assert "việc nào" in sent[-1][0] and a.code in sent[-1][0] and b.code in sent[-1][0]


def test_duyet_xong_bo_sua_chi_tiet_bang_chu(db, bot, monkeypatch, tmp_path):
    from app.modules.agent_hub import coder

    service, _, _ = bot
    _compact(monkeypatch)
    _so_tam(monkeypatch, tmp_path)
    sent = _capture_send(monkeypatch, service)
    approved: list[str] = []
    monkeypatch.setattr(service, "_dispatch_coder", lambda db, chat, task: approved.append(task.code))
    plan = _task_with_plan(db, service, ["backend/app/x.py"])
    service.handle_message(db, _msg("duyệt"))
    assert approved == [plan.code] and plan.approved_at is not None
    #  «sửa: …» lập lại kế hoạch với ý của đại ca.
    seen: list[dict] = []
    _fake_plan(monkeypatch, service, seen=seen)
    _fake_rule(monkeypatch, service, generalizable=False)
    plan2 = _task_with_plan(db, service, ["backend/app/y.py"])
    service.handle_message(db, _msg(f"sửa: bỏ bước 2 {plan2.code}"))
    assert "Đại ca trả lời: bỏ bước 2" in plan2.summary
    #  xong / chi tiết / bỏ theo mã việc.
    done = _task_with_session(db, service, coder)
    service.handle_message(db, _msg(f"xong {done.code}"))
    assert done.status == service.ST_DONE
    service.handle_message(db, _msg(f"chi tiết {done.code}"))
    assert sent[-1][0].startswith(f"<b>{done.code}</b>") and "Trạng thái:" in sent[-1][0]
    other = _task_with_session(db, service, coder)
    service.handle_message(db, _msg(f"bỏ {other.code}"))
    assert other.status == service.ST_CANCELLED
    #  Chế độ gọn: không có nút nào đi ra.
    assert all(b == [] for _t, b in sent)


def test_chon_lam_luon_hay_ghi_viec_bang_chu(db, bot, monkeypatch):
    service, _, asked = bot
    _compact(monkeypatch)
    sent = _capture_send(monkeypatch, service)
    _fake_intent(monkeypatch, service, "mo_ho")
    service.handle_message(db, _msg("xem lại giúp anh"))
    assert "«làm luôn» hoặc «ghi việc»" in sent[-1][0]
    service.handle_message(db, _msg("làm luôn"))
    assert asked == ["xem lại giúp anh"]


# ---------------------------------------------------------------------------
# ai-CR-028: hiểu ý thao tác theo ngữ cảnh («đồng ý» thay cho lệnh)
# ---------------------------------------------------------------------------
def _fake_act(monkeypatch, service, seen=None, **data):
    from app.modules.assistant.provider.base import ChatResult

    ket_qua = ChatResult(text="", provider="agent_gemini", model="x", input_tokens=0, output_tokens=0)

    def fake(text, **kw):
        if seen is not None:
            seen.append(kw)
        return {"intent": "thao_tac", "reason": "", "when": "", "detail": "", **data}, ket_qua

    monkeypatch.setattr(service.manager, "run_intent", fake)


def test_dong_y_sau_de_nghi_gop_thi_gop_luon(db, bot, monkeypatch):
    from app.modules.agent_hub import coder

    service, _, _ = bot
    _compact(monkeypatch)
    _capture_send(monkeypatch, service)
    merged: list[str] = []
    monkeypatch.setattr(service, "_dispatch_deploy", lambda db, chat, cb, task, deploy=True: merged.append(task.code))
    task = _task_with_session(db, service, coder)
    service.reply(db, "12345", f"Gộp được: nhắn «gộp {task.code}».", task_id=task.id)
    seen: list[dict] = []
    _fake_act(monkeypatch, service, seen, action="merge", task=task.code, confident=True)
    service.handle_message(db, _msg("đồng ý"))
    assert merged == [task.code]
    #  Model được đọc cả việc đang mở lẫn tin bot vừa nhắn, chữ trơn không thẻ HTML.
    ctx = seen[0]["tasks"]
    assert task.code in ctx and "TIN BOT VỪA NHẮN" in ctx and "<b>" not in ctx


def test_chua_chac_thi_hoi_lai_roi_dung_moi_lam(db, bot, monkeypatch):
    from app.modules.agent_hub import coder
    from app.modules.agent_hub.model import AgentMessage

    service, _, _ = bot
    _compact(monkeypatch)
    sent = _capture_send(monkeypatch, service)
    merged: list[str] = []
    monkeypatch.setattr(service, "_dispatch_deploy", lambda db, chat, cb, task, deploy=True: merged.append(task.code))
    task = _task_with_session(db, service, coder)
    _fake_act(monkeypatch, service, action="merge", task=task.code, confident=False)
    service.handle_message(db, _msg("đẩy cái đó lên luôn đi em"))
    assert merged == [] and "phải không" in sent[-1][0] and task.code in sent[-1][0]
    #  «đúng» chạy bằng dấu đã ghi, không hỏi model lần hai.
    monkeypatch.setattr(service.manager, "run_intent", lambda *a, **kw: pytest.fail("không hỏi lại model"))
    service.handle_message(db, _msg("đúng rồi"))
    assert merged == [task.code]
    #  «đúng» lần nữa không gộp lần hai.
    _fake_intent(monkeypatch, service, "hoi")
    service.handle_message(db, _msg("đúng"))
    assert merged == [task.code]
    row = db.query(AgentMessage).filter_by(direction=service.DIR_IN).order_by(AgentMessage.id.desc()).first()
    assert row.action != service.ACT_COMMAND


def test_khong_thi_khong_lam(db, bot, monkeypatch):
    from app.modules.agent_hub import coder

    service, _, _ = bot
    _compact(monkeypatch)
    sent = _capture_send(monkeypatch, service)
    monkeypatch.setattr(service, "_dispatch_deploy", lambda *a, **kw: pytest.fail("đại ca đã nói không"))
    task = _task_with_session(db, service, coder)
    _fake_act(monkeypatch, service, action="merge", task=task.code, confident=False)
    service.handle_message(db, _msg("cho nó lên dev nhé"))
    service.handle_message(db, _msg("không"))
    assert "không làm" in sent[-1][0] and task.status == service.ST_REVIEW


def test_model_chac_nhung_viec_sai_buoc_thi_van_hoi_lai(db, bot, monkeypatch):
    """Gộp / thu hồi / bỏ: model nói chắc mà việc không ở bước hợp lệ thì vẫn hỏi, không làm."""
    service, _, _ = bot
    _compact(monkeypatch)
    sent = _capture_send(monkeypatch, service)
    monkeypatch.setattr(service, "_dispatch_revert", lambda *a: pytest.fail("chưa gộp thì không thu hồi"))
    plan = _task_with_plan(db, service, ["backend/app/x.py"])
    _fake_act(monkeypatch, service, action="revert", task=plan.code, confident=True)
    service.handle_message(db, _msg("rút cái đó lại đi"))
    assert "phải không" in sent[-1][0]


def test_dong_y_duyet_ke_hoach_khong_can_ma_viec(db, bot, monkeypatch, tmp_path):
    service, _, _ = bot
    _compact(monkeypatch)
    _so_tam(monkeypatch, tmp_path)
    _capture_send(monkeypatch, service)
    approved: list[str] = []
    monkeypatch.setattr(service, "_dispatch_coder", lambda db, chat, task: approved.append(task.code))
    plan = _task_with_plan(db, service, ["backend/app/x.py"])
    _fake_act(monkeypatch, service, action="approve", task="", confident=True)
    service.handle_message(db, _msg("ok em làm theo kế hoạch đó đi"))
    assert approved == [plan.code]


def test_run_intent_doc_thao_tac_va_ha_nhan_la_ve_mo_ho(monkeypatch):
    from app.modules.agent_hub import manager
    from app.modules.assistant.provider.base import ChatResult

    replies = iter([
        '{"intent":"thao_tac","action":"gop","task":"ai-0007","confident":true,"when":"20h"}',
        '{"intent":"thao_tac","action":"xoa_nhanh","task":"AI-0007","confident":true}',
    ])
    seen: list[str] = []

    class Fake:
        def ask(self, messages, **kw):
            seen.append(messages[0].content)
            return ChatResult(text=next(replies), provider="p", model="m", input_tokens=0, output_tokens=0)

    monkeypatch.setattr(manager, "get_provider", lambda: Fake())
    data, _ = manager.run_intent("đồng ý", tasks="VIỆC ĐANG MỞ:\n- AI-0007")
    assert data["intent"] == "thao_tac" and data["action"] == "merge"
    assert data["task"] == "AI-0007" and data["confident"] is True and data["when"] == "20h"
    assert "VIỆC ĐANG MỞ" in seen[0] and "Tin nhắn mới:\nđồng ý" in seen[0]
    data, _ = manager.run_intent("xóa nhánh đi")
    assert data["intent"] == "mo_ho"


# ---------------------------------------------------------------------------
# ai-CR-029: «gộp» chỉ gộp vào nhánh nền, lên dev phải nói ra
# ---------------------------------------------------------------------------
def test_lenh_gop_chi_gop_con_deploy_phai_noi_ra(db, bot, monkeypatch):
    from app.modules.agent_hub import coder

    service, _, _ = bot
    _compact(monkeypatch)
    _capture_send(monkeypatch, service)
    calls: list[tuple] = []
    monkeypatch.setattr(service, "_dispatch_deploy",
                        lambda db, chat, cb, task, deploy=True: calls.append((task.code, deploy)))
    a = _task_with_session(db, service, coder)
    service.handle_message(db, _msg(f"gộp {a.code}"))
    service.handle_message(db, _msg(f"gộp và deploy dev {a.code}"))
    service.handle_message(db, _msg(f"gộp {a.code} rồi đẩy lên dev luôn"))
    assert calls == [(a.code, False), (a.code, True), (a.code, True)]


def test_chi_gop_thi_khong_ssh_va_viec_cho_deploy(db, bot, monkeypatch):
    from app.modules.agent_hub import coder

    service, _, _ = bot
    _compact(monkeypatch)
    _deploy_on(monkeypatch)
    sent = _capture_send(monkeypatch, service)
    git_calls, scripts = _fake_merge_stack(monkeypatch, coder)
    task = _task_with_session(db, service, coder)
    run = service._new_deploy_run(db, task, STAGE_DEPLOY, "ngay", deploy=False)
    out = coder.merge_and_deploy(db, task, run)
    assert out["deployed"] is False and scripts == []
    assert any(c[1] == "merge" for c in git_calls) and any(c[1] == "push" for c in git_calls)
    assert task.status == service.ST_PROD and task.deployed_dev_at is None
    assert "Dev CHƯA deploy" in sent[-1][0] and f"«deploy dev {task.code}»" in sent[-1][0]
    #  «gộp» lần nữa không gộp lại, chỉ nhắc cách lên dev.
    monkeypatch.setattr(coder, "dispatch_deploy", lambda *a: pytest.fail("đã gộp rồi"))
    service.handle_message(db, _msg(f"gộp {task.code}"))
    assert "dev chưa lên" in sent[-1][0]
    #  «deploy dev» (không cần mã: chỉ một việc đang chờ lên dev) -> lượt deploy, bỏ qua bước gộp.
    dispatched: list[int] = []
    monkeypatch.setattr(coder, "dispatch_deploy", lambda tid, rid: dispatched.append(rid))
    service.handle_message(db, _msg("deploy dev đi"))
    run2 = _deploy_runs(db, task)[-1]
    assert dispatched == [run2.id] and run2.artifact["deploy"] is True
    before = len(git_calls)
    assert coder.merge_and_deploy(db, task, run2)["status"] == "ok"
    assert not any(c[1] == "merge" for c in git_calls[before:]) and len(scripts) == 1
    assert task.deployed_dev_at is not None


def test_deploy_dev_khi_chua_gop_thi_noi_can_gop_truoc(db, bot, monkeypatch):
    from app.modules.agent_hub import coder

    service, _, _ = bot
    _compact(monkeypatch)
    sent = _capture_send(monkeypatch, service)
    monkeypatch.setattr(service, "_dispatch_deploy", lambda *a, **kw: pytest.fail("chưa gộp"))
    task = _task_with_session(db, service, coder)
    service.handle_message(db, _msg(f"deploy dev {task.code}"))
    assert "chưa gộp" in sent[-1][0] and f"«gộp và deploy dev {task.code}»" in sent[-1][0]


def test_thu_hoi_ban_chi_gop_thi_khong_deploy_lai(db, bot, monkeypatch):
    from app.modules.agent_hub import coder

    service, _, _ = bot
    _compact(monkeypatch)
    _deploy_on(monkeypatch)
    sent = _capture_send(monkeypatch, service)
    _git_calls, scripts = _fake_merge_stack(monkeypatch, coder)
    task = _task_with_session(db, service, coder)
    coder.merge_and_deploy(db, task, service._new_deploy_run(db, task, STAGE_DEPLOY, "ngay", deploy=False))
    rrun = service._new_deploy_run(db, task, STAGE_REVERT, "ngay")
    assert coder.revert_and_deploy(db, task, rrun)["status"] == "ok"
    assert scripts == [] and "không deploy lại" in sent[-1][0]
    assert task.status == ST_NEEDS_INPUT


# ---------------------------------------------------------------------------
# ai-CR-032: đo thời gian một việc
# ---------------------------------------------------------------------------
def test_dong_thoi_gian_cong_tung_buoc_va_phan_cho(db, bot):
    from datetime import timedelta

    from app.modules.agent_hub import coder
    from app.modules.agent_hub.model import AgentRun

    service, _, _ = bot
    task = _task_with_plan(db, service, ["backend/app/x.py"])
    start = datetime(2026, 9, 24, 8, 0)
    task.created_at = start
    for stage, sec in ((coder.STAGE_SCAN, 396), (coder.STAGE_PLAN, 72), (coder.STAGE_CODE, 720),
                       (coder.STAGE_CODE, 282)):
        db.add(AgentRun(task_id=task.id, stage=stage, provider="p", model="m", status=coder.RUN_OK,
                        started_at=start, duration_ms=sec * 1000))
    db.commit()
    line = coder.timing_line(db, task, now=start + timedelta(minutes=33))
    assert line.startswith("Thời gian: 33 phút từ lúc nhận việc; bot chạy 24 phút")
    assert "rà soát 6,6 phút" in line and "kế hoạch 1,2 phút" in line and "sửa mã 17 phút" in line
    assert "chờ duyệt/hàng đợi 8,5 phút" in line
    assert coder.fmt_minutes(45_000) == "45 giây"


def test_viec_chua_chay_buoc_nao_thi_khong_co_dong_thoi_gian(db, bot):
    from app.modules.agent_hub import coder

    service, _, _ = bot
    task = _task_with_plan(db, service, ["backend/app/x.py"])
    assert coder.timing_line(db, task) == ""


# ---------------------------------------------------------------------------
# ai-CR-033: dọn nhánh bot khi việc đóng
# ---------------------------------------------------------------------------
def test_xong_hoac_bo_thi_giao_runner_don_nhanh(db, bot, monkeypatch):
    from app.modules.agent_hub import coder

    service, _, _ = bot
    _compact(monkeypatch)
    _capture_send(monkeypatch, service)
    monkeypatch.setattr(settings, "AGENT_CODER_ENABLED", True)
    cleaned: list[int] = []
    monkeypatch.setattr(coder, "dispatch_cleanup", lambda tid: cleaned.append(tid))
    done = _task_with_session(db, service, coder)
    service.handle_message(db, _msg(f"xong {done.code}"))
    dropped = _task_with_session(db, service, coder)
    service.handle_message(db, _msg(f"bỏ {dropped.code}"))
    assert cleaned == [done.id, dropped.id]
    #  Việc không có nhánh bot (chưa sửa mã) thì không giao gì.
    plan = _task_with_plan(db, service, ["backend/app/x.py"])
    service.handle_message(db, _msg(f"bỏ {plan.code}"))
    assert cleaned == [done.id, dropped.id]


def test_don_nhanh_xoa_worktree_nhanh_runner_va_github(db, bot, monkeypatch, tmp_path):
    from app.modules.agent_hub import coder

    service, _, _ = bot
    monkeypatch.setattr(settings, "AGENT_WORKTREE_ROOT", str(tmp_path))
    (tmp_path / "base" / ".git").mkdir(parents=True)
    task = _task_with_session(db, service, coder)
    task.branch_name = "bot/ai-0001-x"
    (tmp_path / task.code).mkdir()
    db.commit()
    calls: list[tuple] = []

    def fake_git(cwd, *args, timeout=0, extra_env=None):
        calls.append(args)
        if args[0] == "push":
            raise coder.CoderError("error: unable to delete 'x': remote ref does not exist")
        return ""

    monkeypatch.setattr(coder, "_git", fake_git)
    monkeypatch.setenv("AGENT_GITHUB_TOKEN", "ghp_test")
    out = coder.cleanup_task_branch(db, task)
    assert ("branch", "-D", "bot/ai-0001-x") in calls
    assert any(c[0] == "push" and "--delete" in c and "refs/heads/bot/ai-0001-x" in c for c in calls)
    assert out["removed"] == ["worktree", "nhánh trong runner"]      # GitHub không có ref: bỏ qua êm
    assert "Đã dọn nhánh bot/ai-0001-x" in task.note
    #  Nhánh không phải của bot thì không đụng.
    task.branch_name = "erp-v2"
    calls.clear()
    assert coder.cleanup_task_branch(db, task)["status"] == "skip" and calls == []


# ---------------------------------------------------------------------------
# ai-CR-034: cổng kiểm frontend/ bản cũ
# ---------------------------------------------------------------------------
def _fake_tsc(monkeypatch, coder, tmp_path, output: str):
    (tmp_path / "frontend" / "node_modules").mkdir(parents=True)
    monkeypatch.setattr(coder, "link_fe_deps", lambda wt, fe_dir=coder.FE_DIR: "")
    monkeypatch.setattr(coder, "_fe_env", lambda wt: {})
    monkeypatch.setattr(coder, "_drop_privileges_kwargs", lambda: {})

    class Proc:
        returncode = 2
        stdout = output
        stderr = ""

    monkeypatch.setattr(coder.subprocess, "run", lambda *a, **kw: Proc())


def test_cong_v1_chi_do_khi_loi_nam_trong_tep_vua_sua(monkeypatch, tmp_path):
    from app.modules.agent_hub import coder

    old = "src/pages/Old.tsx(3,5): error TS2322: Type 'x' is not assignable.\n"
    _fake_tsc(monkeypatch, coder, tmp_path, old + "src/pages/Mine.tsx(10,2): error TS2304: Cannot find name 'y'.\n")
    gate = coder.run_fe_v1_gate(str(tmp_path), ["frontend/src/pages/Mine.tsx", "backend/app/x.py"])
    assert gate["status"] == "fail" and "Mine.tsx(10,2)" in gate["output"] and "Old.tsx" not in gate["output"]
    assert gate["other"] == 1
    assert "Frontend v1: <b>ĐỎ</b>" in coder.fe_v1_gate_line({"frontend_v1": gate}, html=True)


def test_cong_v1_loi_cu_o_tep_khac_khong_chan(monkeypatch, tmp_path):
    from app.modules.agent_hub import coder

    _fake_tsc(monkeypatch, coder, tmp_path, "src/pages/Old.tsx(3,5): error TS2322: Type 'x'.\n")
    gate = coder.run_fe_v1_gate(str(tmp_path), ["frontend/src/pages/Mine.tsx"])
    assert gate["status"] == "pass" and gate["other"] == 1
    line = coder.fe_v1_gate_line({"frontend_v1": gate}, html=False)
    assert "**XANH**" in line and "1 lỗi kiểu ở tệp khác, có thể là lỗi cũ" in line
    assert "giao diện v1 XANH" in coder._gate_brief({"frontend_v1": gate})
    #  Không đụng bản cũ thì cổng không chạy.
    assert coder.run_fe_v1_gate(str(tmp_path), ["frontend-v2/src/a.ts"])["status"] == "none"


# ---------------------------------------------------------------------------
# ai-CR-035: ảnh chụp lỗi gửi kèm
# ---------------------------------------------------------------------------
def _photo(mid: int, *, caption: str = "", group: str = "") -> dict:
    msg = {"chat": {"id": "12345"}, "message_id": mid,
           "photo": [{"file_id": f"small{mid}"}, {"file_id": f"big{mid}"}]}
    if caption:
        msg["caption"] = caption
    if group:
        msg["media_group_id"] = group
    return msg


def _fake_download(monkeypatch, service, tmp_path, *, fail: bool = False):
    monkeypatch.setattr(settings, "AGENT_FILES_DIR", str(tmp_path))
    got: list[str] = []

    def fake(file_id, *, max_bytes):
        if fail:
            raise service.telegram.TelegramError("mạng hỏng")
        got.append(file_id)
        return b"\x89PNG fake", "photos/file_1.png"

    monkeypatch.setattr(service.telegram, "download_file", fake)
    return got


def _last_in(db, service):
    from app.modules.agent_hub.model import AgentMessage
    return db.query(AgentMessage).filter_by(direction=service.DIR_IN).order_by(AgentMessage.id.desc()).first()


def test_anh_kem_chu_thich_la_mot_yeu_cau_co_anh(db, bot, monkeypatch, tmp_path):
    service, _, _ = bot
    _compact(monkeypatch)
    _capture_send(monkeypatch, service)
    got = _fake_download(monkeypatch, service, tmp_path)
    _fake_intent(monkeypatch, service, "viec")
    service.handle_message(db, _photo(21, caption="màn công nợ lệch tổng như ảnh"))
    row = _last_in(db, service)
    assert got == ["big21"] and row.body == "màn công nợ lệch tổng như ảnh" and row.action == ""
    path = row.files[0]["path"]
    assert path.endswith("12345_21.png") and open(path, "rb").read().startswith(b"\x89PNG")


def test_anh_khong_chu_cho_mo_ta_roi_ghep_vao_viec(db, bot, monkeypatch, tmp_path):
    from app.modules.agent_hub import coder
    from app.modules.assistant.provider.base import ChatResult

    service, _, _ = bot
    _compact(monkeypatch)
    sent = _capture_send(monkeypatch, service)
    _fake_download(monkeypatch, service, tmp_path)
    service.handle_message(db, _photo(31, group="alb"))
    assert _last_in(db, service).action == service.ACT_PHOTO_WAIT and "nhắn thêm mô tả" in sent[-1][0]
    n = len(sent)
    service.handle_message(db, _photo(32, group="alb"))          # cùng album: ghép, không báo lại
    assert len(sent) == n and _last_in(db, service).action == service.ACT_PHOTO_USED
    _fake_intent(monkeypatch, service, "viec")
    service.handle_message(db, _msg("nút lưu ở màn này bị mờ"))
    row = _last_in(db, service)
    assert [f["path"].rsplit("_", 1)[-1] for f in row.files] == ["31.png", "32.png"]
    #  Gom thành việc: mô tả ghi số ảnh, đề bài runner liệt kê ảnh.
    ket_qua = ChatResult(text="", provider="agent_gemini", model="x", input_tokens=0, output_tokens=0)
    monkeypatch.setattr(service.manager, "run_triage", lambda msgs: (
        {"groups": [{"title": "Nút lưu bị mờ", "summary": "Nút lưu mờ", "risk_level": 1,
                     "message_ids": [row.id]}]}, ket_qua))
    monkeypatch.setattr(service, "start_scan", lambda db, task: None)
    assert service.triage_inbox(db, force=True) == 1
    task = db.get(service.AgentTask, row.task_id)
    assert "(Kèm 2 ảnh chụp màn hình" in task.summary
    images = coder.task_images(db, task)
    assert len(images) == 2
    brief = coder.build_brief(task, [], images=images)
    assert "## Ảnh chụp đại ca gửi kèm" in brief and images[0] in brief


def test_anh_tai_hong_thi_bao_gui_lai(db, bot, monkeypatch, tmp_path):
    service, _, _ = bot
    _compact(monkeypatch)
    sent = _capture_send(monkeypatch, service)
    _fake_download(monkeypatch, service, tmp_path, fail=True)
    service.handle_message(db, _photo(41))
    assert "không tải được ảnh" in sent[-1][0]
    assert _last_in(db, service).action == service.ACT_PHOTO_USED     # không nằm chờ, không vào hàng việc


def test_claude_duoc_mo_thu_muc_anh(monkeypatch, tmp_path):
    from app.modules.agent_hub import coder

    monkeypatch.setattr(settings, "AGENT_FILES_DIR", str(tmp_path))
    assert coder._with_files_dir(["claude", "-p"])[-2:] == ["--add-dir", str(tmp_path)]
    monkeypatch.setattr(settings, "AGENT_FILES_DIR", str(tmp_path / "khong-co"))
    assert coder._with_files_dir(["claude", "-p"]) == ["claude", "-p"]


# ---------------------------------------------------------------------------
# ai-CR-036: màn Việc của bot trong ERP v2 (API chỉ đọc)
# ---------------------------------------------------------------------------
def _json(resp) -> dict:
    import json as _j
    return _j.loads(resp.body)["data"]


def _pg(page=1, size=20):
    return {"page": page, "page_size": size, "offset": (page - 1) * size, "limit": size}


def test_api_danh_sach_viec_co_chi_phi_va_loc(db, bot):
    from app.modules.agent_hub import coder, controller
    from app.modules.agent_hub.model import AgentRun

    service, _, _ = bot
    a = _task_with_session(db, service, coder)
    b = _task_with_plan(db, service, ["backend/app/y.py"])
    b.title = "Sửa màn công nợ"
    for cost in (0.01, 0.02):
        db.add(AgentRun(task_id=a.id, stage=coder.STAGE_PLAN, provider="agent_gemini", model="m",
                        status=coder.RUN_OK, started_at=datetime.now(), duration_ms=1000, cost_usd=cost))
    db.commit()
    data = _json(controller.list_tasks(status=0, q="", user=None, db=db, pg=_pg()))
    assert data["total"] == 2 and data["items"][0]["code"] == b.code          # mới nhất trước
    row_a = next(i for i in data["items"] if i["code"] == a.code)
    assert row_a["cost_usd"] == 0.03 and row_a["runs"] == 3 and row_a["status_label"] == "Chờ đại ca xem"
    assert _json(controller.list_tasks(status=0, q="công nợ", user=None, db=db, pg=_pg()))["total"] == 1
    assert _json(controller.list_tasks(status=service.ST_PLAN, q="", user=None, db=db, pg=_pg()))["total"] == 1


def test_api_chi_tiet_viec_va_404(db, bot):
    from fastapi import HTTPException

    from app.modules.agent_hub import coder, controller

    service, _, _ = bot
    task = _task_with_session(db, service, coder)
    service.reply(db, "12345", "Em nhận việc", task_id=task.id)
    db.commit()
    data = _json(controller.get_task(task.id, user=None, db=db))
    assert data["code"] == task.code and data["plan"] == "Sửa điều kiện lọc"
    assert data["run_list"][0]["stage_label"] == "Sửa mã" and data["messages"][0]["body"] == "Em nhận việc"
    with pytest.raises(HTTPException):
        controller.get_task(999999, user=None, db=db)


def test_api_thong_ke_chi_phi_theo_ngay_va_buoc(db, bot):
    from app.modules.agent_hub import coder, controller
    from app.modules.agent_hub.model import AgentRun

    service, _, _ = bot
    task = _task_with_plan(db, service, ["backend/app/x.py"])
    db.add(AgentRun(task_id=task.id, stage=coder.STAGE_SCAN, provider="claude_code", model="m",
                    status=coder.RUN_OK, started_at=datetime.now(), cost_usd=0.5))
    db.add(AgentRun(task_id=0, stage=coder.STAGE_INTENT if hasattr(coder, "STAGE_INTENT") else 20,
                    provider="agent_gemini", model="m", status=coder.RUN_OK, started_at=datetime.now(),
                    cost_usd=0.001))
    db.commit()
    data = _json(controller.stats(days=30, user=None, db=db))
    assert data["total_cost_usd"] == 0.501 and data["run_count"] == 2
    assert data["cost_by_stage"][0]["label"] == "Rà soát mã"


def test_khoa_quyen_agent_task_khong_lot_vao_quan_ly_thu_mua():
    from app.core.permissions import ENTITIES
    from app.core.scoping import SCOPE_FIELDS
    from app.seed import _SYS_ENTITIES

    assert "agent_task" in ENTITIES and "agent_task" in SCOPE_FIELDS and "agent_task" in _SYS_ENTITIES


# ---------------------------------------------------------------------------
# ai-CR-037: phiếu hỗ trợ ERP làm nguồn việc
# ---------------------------------------------------------------------------
def _ticket(db, code: str, *, subject="Màn công nợ lệch tổng", department="", assignee_id=0, status="open",
            body="Tổng cuối trang không khớp cột"):
    from app.modules.ticket.model import Ticket, TicketMessage

    t = Ticket(code=code, subject=subject, department=department, priority="high", status=status,
               assignee_id=assignee_id, origin_url="/finance/payables")
    db.add(t)
    db.flush()
    db.add(TicketMessage(ticket_id=t.id, body=body, is_staff=False))
    db.commit()
    return t


def _ticket_setup(db, monkeypatch, service, *, departments=""):
    from app.modules.user.model import User

    bot_user = User(email="dau-dau@bot.local", employee_id=0, password_hash="x", is_active=True)
    db.add(bot_user)
    db.commit()
    monkeypatch.setattr(settings, "AGENT_TICKET_ASSIGNEE", "dau-dau@bot.local")
    monkeypatch.setattr(settings, "AGENT_TICKET_DEPARTMENTS", departments)
    scanned: list[str] = []
    monkeypatch.setattr(service, "start_scan", lambda db, task: scanned.append(task.code))
    return bot_user, scanned


def test_phieu_giao_cho_bot_thanh_viec_va_bao_lai_tren_phieu(db, bot, monkeypatch):
    from app.modules.ticket.model import TicketMessage

    service, _, _ = bot
    _compact(monkeypatch)
    sent = _capture_send(monkeypatch, service)
    bot_user, scanned = _ticket_setup(db, monkeypatch, service)
    old = _ticket(db, "HT-0001", assignee_id=bot_user.id)        # phiếu CŨ nhưng giao cho bot: vẫn nhận
    other = _ticket(db, "HT-0002", subject="Quên mật khẩu")        # không giao, không nhãn: không nhận
    assert service.pull_tickets(db) == 1
    task = db.query(service.AgentTask).filter_by(source=service.SRC_ERP_TICKET).one()
    assert scanned == [task.code] and task.title == "Màn công nợ lệch tổng"
    assert "Phiếu hỗ trợ HT-0001" in task.summary and "Tổng cuối trang không khớp cột" in task.summary
    assert "/finance/payables" in task.summary
    assert "HT-0001" in sent[-1][0] and task.code in sent[-1][0]
    note = db.query(TicketMessage).filter_by(ticket_id=old.id, is_staff=True).one()
    assert task.code in note.body and old.status == "in_progress" and other.status == "open"
    #  Chạy lại không tạo trùng.
    assert service.pull_tickets(db) == 0
    #  Đóng «xong» -> phiếu «Đã trả lời» + dòng báo.
    task.status = service.ST_PROD
    db.commit()
    service.handle_message(db, _msg(f"xong {task.code}"))
    assert old.status == "answered"
    assert "đã sửa xong" in db.query(TicketMessage).filter_by(ticket_id=old.id).order_by(TicketMessage.id.desc()).first().body


def test_phieu_theo_nhan_bo_phan_chi_nhan_phieu_moi_va_bo_viec_tra_phieu_ve(db, bot, monkeypatch):
    service, _, _ = bot
    _compact(monkeypatch)
    _capture_send(monkeypatch, service)
    bot_user, _scanned = _ticket_setup(db, monkeypatch, service, departments="Phần mềm, IT")
    _ticket(db, "HT-0010", department="IT")          # có trước lúc bật: không kéo lịch sử
    assert service.pull_tickets(db) == 0                  # lần đầu: đặt mốc
    new = _ticket(db, "HT-0011", department=" phần mềm ")
    _ticket(db, "HT-0012", department="Kế toán")
    closed = _ticket(db, "HT-0013", department="IT", status="closed")
    assert service.pull_tickets(db) == 1
    task = db.query(service.AgentTask).filter_by(source=service.SRC_ERP_TICKET).one()
    assert "HT-0011" in task.summary and closed.status == "closed"
    service.handle_message(db, _msg(f"bỏ {task.code}"))
    assert new.status == "open"


def test_khong_khai_cua_nao_thi_khong_doc_phieu(db, bot, monkeypatch):
    service, _, _ = bot
    monkeypatch.setattr(settings, "AGENT_TICKET_ASSIGNEE", "")
    monkeypatch.setattr(settings, "AGENT_TICKET_DEPARTMENTS", "")
    _ticket(db, "HT-0020", department="IT")
    assert service.pull_tickets(db) == 0
    assert db.query(service.AgentCursor).filter_by(name=service.TICKET_CURSOR).first() is None


def test_phieu_cham_tran_viec_ngay_thi_cho_luot_sau(db, bot, monkeypatch):
    service, _, _ = bot
    _compact(monkeypatch)
    _capture_send(monkeypatch, service)
    bot_user, _ = _ticket_setup(db, monkeypatch, service)
    monkeypatch.setattr(settings, "AGENT_DAILY_TASK_CAP", 0)
    t = _ticket(db, "HT-0030", assignee_id=bot_user.id)
    assert service.pull_tickets(db) == 0 and t.status == "open"
