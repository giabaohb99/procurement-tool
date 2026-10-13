"""ai-CR-184 (13/10/2026) — phase 15.2: sổ thay đổi do bot ghi + hoàn tác 24 giờ, phía Telegram.
«bot vừa làm gì» → thẻ ≤ 10 dòng đánh số · «hoàn tác» / «hoàn tác n» → thẻ xác nhận → «đúng» gọi `erp.undo_change` đúng
một lần · «thôi» không gọi · lỗi 409 ra chữ rõ · chat chưa đăng nhập → câu hướng dẫn đăng nhập. Lõi ERP (ai-CR-182) được
giả lập qua `erp.my_changes` / `erp.undo_change`, như test_agent_hub_don_nhap.py."""
import json
from types import SimpleNamespace

import pytest

from app.modules.agent_hub import change_undo
from app.modules.agent_hub.constants import ACT_CHANGES_LIST, ACT_COMMAND, ACT_UNDO_DONE, ACT_UNDO_DROPPED, ACT_UNDO_WAIT, DIR_IN


def _item(i, **kw):
    base = {"id": i, "when": "2026-10-13T02:15:00", "user_id": 7, "entity": "purchase_request",
            "entity_label": "Yêu cầu mua hàng", "entity_id": 123, "doc_code": "YCMH00123", "action": 1,
            "action_label": "Tạo", "summary": "Tạo yêu cầu mua hàng (YCMH) YCMH00123", "source": 1,
            "source_label": "Telegram", "undo_status": 0, "undo_status_label": "Chưa", "undo_of": 0,
            "can_undo": True, "undo_reason": "", "url": "/procurement/purchase-requests/123"}
    base.update(kw)
    return base


ITEMS = [
    _item(31),
    _item(30, entity="leave_request", entity_label="Đơn nghỉ phép", entity_id=5, doc_code="NP001", action=2,
          action_label="Sửa", summary="Sửa Đơn nghỉ phép NP001: Đến ngày", url="/hr/leave-requests/5"),
    _item(29, doc_code="YCMH00120", action=4, action_label="Gửi duyệt", summary="Gửi duyệt YCMH YCMH00120",
          can_undo=False, undo_reason="Gửi duyệt không hoàn tác được — rút / trả về bằng tay."),
    _item(28, doc_code="YCBG00007", action=3, action_label="Xóa", summary="Xóa YCBG YCBG00007", undo_status=1,
          undo_status_label="Đã hoàn tác", can_undo=False, undo_reason="Đã hoàn tác rồi."),
]


@pytest.fixture
def chat(db, monkeypatch):
    from app.core.config import settings
    from app.modules.agent_hub import erp, service

    monkeypatch.setattr(settings, "AGENT_TELEGRAM_CHAT_ID", "12345")
    me = SimpleNamespace(id=7)
    monkeypatch.setattr(service, "_assistant_user", lambda db, chat_id="": me)
    sent: list[str] = []
    monkeypatch.setattr(service, "reply", lambda db, chat_id, text, **kw: sent.append(text))
    state = {"items": [dict(x) for x in ITEMS]}
    monkeypatch.setattr(erp, "my_changes", lambda db, user, limit=20: list(state["items"])[:limit])
    undone: list[int] = []

    def fake_undo(db, user, change_id, source=0):
        undone.append(int(change_id))
        return {"id": 99, "undo_of": change_id, "summary": "Hoàn tác: …", "url": "/procurement/purchase-requests/123"}

    monkeypatch.setattr(erp, "undo_change", fake_undo)
    return service, sent, undone, state


_N = [100]


def _say(db, service, text):
    _N[0] += 1
    row = service.log_message(db, DIR_IN, "12345", _N[0], text)
    db.commit()
    return change_undo.handle_text(db, "12345", row, text), row


def _rows(db, *actions):
    from sqlalchemy import select

    from app.modules.agent_hub.model import AgentMessage

    return list(db.scalars(select(AgentMessage).where(AgentMessage.action.in_(actions)).order_by(AgentMessage.id)))


# ---------------------------------------------------------------------------
# Nhận câu
# ---------------------------------------------------------------------------
def test_nhan_dang_cau_khong_dau():
    from app.modules.assistant.glossary import fold

    for s in ("bot vừa làm gì?", "Bot đã ghi gì", "em vừa ghi gì vậy", "sổ thay đổi", "xem sổ thay đổi của tôi"):
        assert change_undo.parse_command(fold(s)) == {"op": "list"}, s
    assert change_undo.parse_command(fold("hoàn tác")) == {"op": "undo", "n": None}
    assert change_undo.parse_command(fold("undo")) == {"op": "undo", "n": None}
    assert change_undo.parse_command(fold("hoàn tác 2")) == {"op": "undo", "n": 2}
    assert change_undo.parse_command(fold("rút lại 3 đi em")) == {"op": "undo", "n": 3}
    assert change_undo.parse_command(fold("hoàn tác dòng 1")) == {"op": "undo", "n": 1}
    for s in ("bot làm được gì", "hoàn tác là gì", "đơn nháp của tôi", "rút lại tiền cho anh", "hướng dẫn"):
        assert change_undo.parse_command(fold(s)) is None, s


# ---------------------------------------------------------------------------
# Liệt kê
# ---------------------------------------------------------------------------
def test_liet_ke_dung_khuon_khong_ngoac(db, chat):
    service, sent, undone, _ = chat
    ok, row = _say(db, service, "bot vừa làm gì?")
    assert ok and row.action == ACT_COMMAND
    card = sent[-1]
    assert "«" not in card and "»" not in card
    assert "1. <b>YCMH00123</b> · Tạo · Tạo yêu cầu mua hàng (YCMH) YCMH00123 · lúc 09:15 13/10" in card   # UTC+7
    assert "2. <b>NP001</b> · Sửa · Sửa Đơn nghỉ phép NP001: Đến ngày" in card
    assert "hoàn tác được — nhắn <code>hoàn tác 1</code>" in card and "<code>hoàn tác 2</code>" in card
    assert "rút / trả về bằng tay" in card                       # dòng 3: lý do không hoàn tác được
    assert "đã hoàn tác" in card                                 # dòng 4
    assert "Nhắn <code>hoàn tác n</code> để rút lại dòng n (trong 24 giờ)." in card
    listed = _rows(db, ACT_CHANGES_LIST)
    assert len(listed) == 1 and json.loads(listed[0].body) == {"user_id": 7, "ids": [31, 30, 29, 28]}
    assert undone == []


def test_khong_co_dong_nao_thi_noi_ro(db, chat):
    service, sent, _, state = chat
    state["items"] = []
    ok, _ = _say(db, service, "sổ thay đổi")
    assert ok and "chưa ghi thay đổi nào" in sent[-1]
    assert _rows(db, ACT_CHANGES_LIST) == []
    ok, _ = _say(db, service, "hoàn tác")
    assert ok and "chưa ghi thay đổi nào" in sent[-1]


def test_chat_chua_dang_nhap(db, chat, monkeypatch):
    service, sent, undone, _ = chat
    monkeypatch.setattr(service, "_assistant_user", lambda db, chat_id="": None)
    ok, _ = _say(db, service, "bot vừa làm gì")
    assert ok and "chưa đăng nhập ERP" in sent[-1] and "/dangnhap" in sent[-1]
    ok, _ = _say(db, service, "hoàn tác")
    assert ok and "chưa đăng nhập ERP" in sent[-1] and undone == []


# ---------------------------------------------------------------------------
# Hoàn tác
# ---------------------------------------------------------------------------
def test_hoan_tac_khong_so_chon_dong_moi_nhat_va_dung_mot_lan(db, chat):
    service, sent, undone, _ = chat
    ok, _ = _say(db, service, "hoàn tác")
    assert ok and "<b>Rút lại:</b> Tạo yêu cầu mua hàng (YCMH) YCMH00123" in sent[-1]
    assert "<code>đúng</code>" in sent[-1] and "<code>thôi</code>" in sent[-1] and "«" not in sent[-1]
    assert undone == []                                          # chưa «đúng» thì chưa làm gì
    wait = _rows(db, ACT_UNDO_WAIT)
    assert len(wait) == 1 and json.loads(wait[0].body)["change_id"] == 31
    ok, row = _say(db, service, "đúng")
    assert ok and row.action == ACT_COMMAND and undone == [31]
    assert "<b>Đã hoàn tác:</b> Tạo yêu cầu mua hàng (YCMH) YCMH00123" in sent[-1]
    assert "/procurement/purchase-requests/123" in sent[-1]
    assert wait[0].action == ACT_UNDO_DONE
    ok, _ = _say(db, service, "đúng")                            # thẻ đã dùng: không nuốt câu, không gọi lại
    assert not ok and undone == [31]


def test_hoan_tac_n_chon_dung_id_cua_the_vua_liet_ke(db, chat):
    service, sent, undone, _ = chat
    assert _say(db, service, "bot vừa làm gì")[0]
    ok, _ = _say(db, service, "hoàn tác 2")
    assert ok and "<b>Rút lại:</b> Sửa Đơn nghỉ phép NP001: Đến ngày" in sent[-1]
    assert json.loads(_rows(db, ACT_UNDO_WAIT)[-1].body)["change_id"] == 30
    assert _say(db, service, "ok")[0] and undone == [30]
    assert "Đã hoàn tác" in sent[-1]


def test_hoan_tac_n_chua_liet_ke_thi_liet_ke_truoc(db, chat):
    service, sent, undone, _ = chat
    ok, _ = _say(db, service, "hoàn tác 2")
    assert ok and "Em liệt kê lại" in sent[-1] and "1. <b>YCMH00123</b>" in sent[-1]
    assert _rows(db, ACT_UNDO_WAIT) == [] and undone == []
    ok, _ = _say(db, service, "hoàn tác 2")                      # giờ đã có thứ tự → thẻ xác nhận
    assert ok and "<b>Rút lại:</b> Sửa Đơn nghỉ phép NP001" in sent[-1]
    ok, _ = _say(db, service, "hoàn tác 9")
    assert ok and "Không có dòng số 9" in sent[-1]


def test_dong_khong_hoan_tac_duoc_thi_noi_ly_do(db, chat):
    service, sent, undone, state = chat
    assert _say(db, service, "bot vừa làm gì")[0]
    ok, _ = _say(db, service, "hoàn tác 3")
    assert ok and "Dòng 3 (<b>YCMH00120</b>) không hoàn tác được: Gửi duyệt không hoàn tác được — rút / trả về bằng tay." in sent[-1]
    assert _rows(db, ACT_UNDO_WAIT) == []
    #  Dòng mới nhất là gửi duyệt → «hoàn tác» trơn nói lý do + liệt kê lại cho chọn số, không mở thẻ.
    state["items"] = [ITEMS[2], ITEMS[0], ITEMS[1]]
    ok, _ = _say(db, service, "hoàn tác")
    assert ok and "Dòng mới nhất (<b>YCMH00120</b> · Gửi duyệt) không hoàn tác được: Gửi duyệt không hoàn tác được" in sent[-1]
    assert "1. <b>YCMH00120</b>" in sent[-1] and "2. <b>YCMH00123</b>" in sent[-1]
    assert _rows(db, ACT_UNDO_WAIT) == [] and undone == []


def test_thoi_thi_giu_nguyen_khong_goi(db, chat):
    service, sent, undone, _ = chat
    assert _say(db, service, "hoàn tác")[0]
    ok, _ = _say(db, service, "thôi")
    assert ok and "giữ nguyên" in sent[-1] and undone == []
    assert _rows(db, ACT_UNDO_WAIT, ACT_UNDO_DROPPED)[0].action == ACT_UNDO_DROPPED
    assert not _say(db, service, "đúng")[0] and undone == []


def test_the_moi_thay_the_cu_va_doi_tai_khoan_thi_khong_lam(db, chat, monkeypatch):
    service, sent, undone, _ = chat
    assert _say(db, service, "hoàn tác")[0]
    assert _say(db, service, "bot vừa làm gì")[0] and _say(db, service, "hoàn tác 2")[0]
    waits = _rows(db, ACT_UNDO_WAIT, ACT_UNDO_DROPPED)
    assert [w.action for w in waits] == [ACT_UNDO_DROPPED, ACT_UNDO_WAIT]       # thẻ cũ bị thay
    monkeypatch.setattr(service, "_assistant_user", lambda db, chat_id="": SimpleNamespace(id=99))
    ok, _ = _say(db, service, "đúng")
    assert ok and "đã đổi" in sent[-1] and undone == []


def test_loi_409_ra_chu_ro_va_khong_goi_lai(db, chat, monkeypatch):
    from fastapi import HTTPException

    from app.modules.agent_hub import erp

    service, sent, undone, _ = chat
    calls: list[int] = []

    def boom(db, user, change_id, source=0):
        calls.append(change_id)
        raise HTTPException(409, "Phiếu đã bị người khác sửa sau đó, không hoàn tác được.")

    monkeypatch.setattr(erp, "undo_change", boom)
    assert _say(db, service, "hoàn tác")[0]
    ok, _ = _say(db, service, "đúng")
    assert ok and calls == [31]
    assert sent[-1] == "Không hoàn tác được: Phiếu đã bị người khác sửa sau đó, không hoàn tác được."
    assert _rows(db, ACT_UNDO_WAIT, ACT_UNDO_DROPPED, ACT_UNDO_DONE)[0].action == ACT_UNDO_DROPPED
    assert not _say(db, service, "đúng")[0] and calls == [31]


def test_the_cho_het_han_15_phut(db, chat):
    from datetime import timedelta

    service, sent, undone, _ = chat
    assert _say(db, service, "hoàn tác")[0]
    wait = _rows(db, ACT_UNDO_WAIT)[0]
    wait.created_at = wait.created_at - timedelta(minutes=16)
    db.commit()
    assert not _say(db, service, "đúng")[0] and undone == []


def test_the_khac_moi_hon_thi_dung_khong_phai_cua_minh(db, chat):
    from app.modules.agent_hub.constants import ACT_DRAFT_DEL_WAIT, DIR_OUT

    service, sent, undone, _ = chat
    assert _say(db, service, "hoàn tác")[0]
    service.log_message(db, DIR_OUT, "12345", 0, json.dumps({"user_id": 7, "items": []}), action=ACT_DRAFT_DEL_WAIT)
    db.commit()
    assert not _say(db, service, "đúng")[0] and undone == []     # «đúng» thuộc thẻ xóa nháp mới hơn


# ---------------------------------------------------------------------------
# Chân thẻ
# ---------------------------------------------------------------------------
def test_chan_the_rut_lai():
    out = change_undo.with_undo_footer("Đã xóa <b>YCMH00123</b>.")
    assert out.endswith("\n<i>Rút lại trong 24 giờ: nhắn hoàn tác</i>") and "«" not in out


def test_xoa_don_nhap_co_chan_the(db, monkeypatch):
    from app.core.config import settings
    from app.modules.agent_hub import erp, service
    from app.modules.agent_hub.constants import ACT_DRAFT_DEL_WAIT, DIR_OUT

    monkeypatch.setattr(settings, "AGENT_TELEGRAM_CHAT_ID", "12345")
    monkeypatch.setattr(service, "_assistant_user", lambda db, chat_id="": SimpleNamespace(id=7))
    sent: list[str] = []
    monkeypatch.setattr(service, "reply", lambda db, chat_id, text, **kw: sent.append(text))
    monkeypatch.setattr(erp, "delete_my_drafts", lambda db, user, items: {"deleted": ["YCMH001"], "skipped": []})
    service.log_message(db, DIR_OUT, "12345", 0, json.dumps({"user_id": 7, "items": [{"kind": "purchase", "id": 21}]}),
                        action=ACT_DRAFT_DEL_WAIT)
    db.commit()
    row = service.log_message(db, DIR_IN, "12345", 5, "đúng")
    db.commit()
    assert service._my_drafts_by_text(db, "12345", row, "đúng")
    assert "Đã xóa 1 phiếu nháp: YCMH001." in sent[-1] and "Rút lại trong 24 giờ" in sent[-1]
