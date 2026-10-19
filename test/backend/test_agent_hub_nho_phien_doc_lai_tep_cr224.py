"""ai-CR-224 — đại ca 19/10/2026: 12:09 gửi tệp kế hoạch, 12:31 bàn «tạo 26 sự kiện», 13:34 nhắn «oke tạo đi em» → Lạc Lạc
đáp «không thấy nháp nào đang chờ» (log: lịch sử 0 lượt). Ba lỗi, ba bản vá:
  1. phiên ngắt ở 60 phút → nay 6 giờ (lịch sử vẫn chịu trần ký tự nên không đắt thêm);
  2. nội dung tệp chỉ lượt gửi tệp thấy → công cụ read_chat_file tải lại theo file_id (24 giờ), tệp KÈM câu hỏi nay
     cũng giữ file_id, dòng «[tệp …]» trong lịch sử nhắc model đọc lại được;
  3. «… sự kiện …» không nạp nhóm công cụ lịch Google → bot nói sai «em không xóa được sự kiện».
"""
from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest

from app.modules.agent_hub import core_v2, service
from app.modules.agent_hub.constants import ACT_ANSWER, ACT_ASKED, DIR_IN, DIR_OUT
from app.modules.agent_hub.model import AgentMessage
from app.modules.assistant import tool_router

CHAT = "12345"
PLAN = "\n".join(f"Ngày {i}: chặng {i}, ghé quán {i}, tọa độ 10.{i}, 106.{i}" for i in range(1, 27))


def _msg(db, direction, body, at, action=ACT_ASKED, files=None):
    row = AgentMessage(chat_id=CHAT, direction=direction, body=body, action=action, created_at=at, files=files)
    db.add(row)
    db.commit()
    return row


# ── 1. Phiên 6 giờ ────────────────────────────────────────────────────────────

def test_cach_63_phut_van_nho_cuoc_tro_chuyen(db):
    t0 = datetime(2026, 10, 19, 12, 30)
    _msg(db, DIR_IN, "tạo 26 sự kiện chưa em", t0)
    _msg(db, DIR_OUT, "Anh ưng thì bảo em tạo đi.", t0 + timedelta(minutes=1), action=ACT_ANSWER)
    now = _msg(db, DIR_IN, "oke tạo đi em", t0 + timedelta(minutes=64))
    turns = core_v2.history(db, CHAT, now.id, now.created_at)
    assert [t["role"] for t in turns] == ["user", "assistant"] and "26 sự kiện" in turns[0]["content"]
    #  Quá 6 giờ thì vẫn là phiên mới (chuyện hôm sau không kéo theo).
    later = _msg(db, DIR_IN, "chào em", now.created_at + core_v2.SESSION_GAP + timedelta(minutes=1))
    assert core_v2.history(db, CHAT, later.id, later.created_at) == []


# ── 2. Đọc lại tệp ────────────────────────────────────────────────────────────

@pytest.fixture
def downloads(monkeypatch):
    store = {"f-plan": PLAN.encode(), "f-old": b"tep cu", "f-long": ("x" * 45_000).encode()}
    calls: list[str] = []

    def download(file_id, *, max_bytes):
        calls.append(file_id)
        if file_id not in store:
            raise service.telegram.TelegramError("file hết hạn")
        return store[file_id], "p"

    monkeypatch.setattr(core_v2.telegram, "download_file", download)
    return calls


def _file(name, fid):
    return [{"kind": "doc", "file_id": fid, "name": name, "mime": "text/markdown"}]


def test_doc_lai_tep_ke_hoach_gui_luc_truoc(db, downloads):
    t0 = datetime(2026, 10, 19, 12, 9)
    _msg(db, DIR_IN, "[tệp cu.md]", t0 - timedelta(hours=25), files=_file("cu.md", "f-old"))       # quá 24 giờ
    _msg(db, DIR_IN, "[tệp ke-hoach.md] em thấy tốt hơn không", t0, files=_file("ke-hoach.md", "f-plan"))
    now = _msg(db, DIR_IN, "oke tạo đi em", t0 + timedelta(minutes=85))
    out = core_v2.read_chat_file(db, CHAT, now)
    assert out["ten"] == "ke-hoach.md" and "Ngày 26" in out["noi_dung"] and out["so_phan"] == 1
    assert "f-old" not in downloads
    assert "error" in core_v2.read_chat_file(db, CHAT, now, "khong-co")
    #  Gọi qua đúng đường công cụ của lõi.
    via = core_v2._run_local(db, CHAT, now, SimpleNamespace(id=1), "read_chat_file", {"ten": "KE-HOACH"})
    assert via["ten"] == "ke-hoach.md"


def test_tep_dai_chia_phan_va_phan_la_khong_vo(db, downloads):
    now = _msg(db, DIR_IN, "[tệp dai.txt]", datetime(2026, 10, 19, 9, 0), files=_file("dai.txt", "f-long"))
    first = core_v2.read_chat_file(db, CHAT, now)
    assert first["so_phan"] == 3 and len(first["noi_dung"]) == core_v2.FILE_PART_CHARS and "phan=2" in first["note"]
    for bad in (0, -5, 99, "abc", None):
        out = core_v2.read_chat_file(db, CHAT, now, "", bad)
        assert 1 <= out["phan"] <= 3, bad


def test_khong_co_tep_hoac_tep_het_han_bao_ro(db, downloads):
    now = _msg(db, DIR_IN, "oke tạo đi", datetime(2026, 10, 19, 13, 0))
    assert "không có tệp" in core_v2.read_chat_file(db, CHAT, now)["error"]
    gone = _msg(db, DIR_IN, "[tệp mat.md]", datetime(2026, 10, 19, 13, 1), files=_file("mat.md", "f-gone"))
    assert "gửi lại" in core_v2.read_chat_file(db, CHAT, gone)["error"]


def test_tep_cua_chat_khac_khong_doc_duoc(db, downloads):
    db.add(AgentMessage(chat_id="999", direction=DIR_IN, body="[tệp bi-mat.md]", action=ACT_ASKED,
                        created_at=datetime(2026, 10, 19, 12, 0), files=_file("bi-mat.md", "f-plan")))
    db.commit()
    now = _msg(db, DIR_IN, "đọc tệp", datetime(2026, 10, 19, 12, 5))
    assert "error" in core_v2.read_chat_file(db, CHAT, now) and not downloads


def test_lich_su_nhac_doc_lai_tep_va_cong_cu_luon_co(db):
    row = _msg(db, DIR_IN, "[tệp ke-hoach.md] xem giúp", datetime(2026, 10, 19, 12, 9), files=_file("k.md", "f"))
    assert core_v2._history_body(row).endswith(core_v2.FILE_HINT)
    assert "read_chat_file" in {t.name for t in core_v2.LOCAL_TOOLS} and "read_chat_file" in core_v2.LOCAL_TOOL_NAMES


def test_tep_kem_cau_hoi_cung_giu_file_id(db, monkeypatch):
    monkeypatch.setattr(service.chat_link, "get_active_link", lambda db, chat_id: SimpleNamespace(user_id=7))
    monkeypatch.setattr(service, "_answer_document", lambda *a, **k: None)
    msg = {"message_id": 5, "document": {"file_id": "f-plan", "file_name": "ke-hoach.md", "mime_type": "text/markdown"}}
    assert service._document_by_message(db, msg, CHAT, "em thấy tốt hơn không")
    row = db.query(AgentMessage).filter(AgentMessage.chat_id == CHAT).order_by(AgentMessage.id.desc()).first()
    assert row.files and row.files[0]["file_id"] == "f-plan"


# ── 3. «sự kiện» nạp nhóm lịch ────────────────────────────────────────────────

def test_cau_su_kien_nap_nhom_lich_google():
    for text in ("tạo 26 sự kiện chưa em", "em tạo rồi thì em xóa sự kiện được ko"):
        assert "google" in tool_router.groups_for(text), text
