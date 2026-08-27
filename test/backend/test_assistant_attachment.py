"""Tệp đính kèm chat Trợ lý AI (CR-204) — kiểm loại, quyền sở hữu, và cửa sổ nạp lại.

KHÔNG đụng storage thật: `upload_fileobj` / `download_bytes` được monkeypatch ngay trong
namespace của module `attachments` (nơi chúng được import vào). KHÔNG gọi model thật:
`service.ask` thay bằng hàm giả như bộ test_assistant_conversation.
"""
import base64
import json

import pytest
from pydantic import ValidationError

from app.core.config import settings
from app.modules.assistant import attachments as attach
from app.modules.assistant import conversation as convo
from app.modules.assistant.model import (
    AssistantConversation,
    AssistantMessage,
    MessageRole,
)
from app.modules.assistant.provider.claude import _wire_content
from app.modules.assistant.provider.gemini import GeminiProvider
from app.modules.assistant.schema import AskIn
from app.modules.attachment.model import StoredFile
from app.modules.user.model import User

#  Vài byte đầu quyết định loại — phần đuôi là rác cho có độ dài.
PNG = b"\x89PNG\r\n\x1a\n" + b"x" * 16
JPEG = b"\xff\xd8\xff\xe0" + b"x" * 16
WEBP = b"RIFF" + b"\x00\x00\x00\x00" + b"WEBP" + b"x" * 8
PDF = b"%PDF-1.7\n" + b"x" * 16


def _fake_upload(monkeypatch):
    """Chặn đường ra storage; trả list các key đã 'tải lên' để test soi."""
    keys: list[str] = []
    monkeypatch.setattr(attach, "upload_fileobj", lambda fobj, key, ctype: keys.append(key))
    return keys


def _stored_png(db, user_id: int, *, key_dir: str = attach.KEY_CATEGORY) -> StoredFile:
    """Một StoredFile PNG nằm sẵn trong DB, key đúng (hoặc cố tình sai) thư mục chat."""
    sf = StoredFile(
        filename="anh.png", file_key=f"test/{key_dir}/2026/08/anh.png", url="",
        content_type="image/png", size=len(PNG), created_by=user_id, updated_by=user_id,
    )
    db.add(sf)
    db.commit()
    return sf


# ── detect_type: magic bytes, không tin content-type client ─────────────────────────────

def test_detect_type_theo_magic_bytes():
    assert attach.detect_type(PNG) == "image/png"
    assert attach.detect_type(JPEG) == "image/jpeg"
    assert attach.detect_type(WEBP) == "image/webp"
    assert attach.detect_type(PDF) == "application/pdf"
    #  Đổi đuôi .exe thành .png cũng không lọt — nội dung không phải ảnh là None.
    assert attach.detect_type(b"MZ\x90\x00" + b"x" * 16) is None
    assert attach.detect_type(b"PK\x03\x04xlsx-la-zip") is None


# ── store_upload: từ chối rõ lý do, nhận thì lưu đúng khuôn ─────────────────────────────

def test_store_upload_tu_choi_tep_rong_va_sai_loai(db, seed):
    user = db.get(User, seed.u_req_id)
    with pytest.raises(ValueError, match="Tệp rỗng"):
        attach.store_upload(db, user, "a.png", b"")
    with pytest.raises(ValueError, match="JPG/PNG/WebP hoặc PDF"):
        attach.store_upload(db, user, "bang.xlsx", b"PK\x03\x04noi-dung-zip")


def test_store_upload_tu_choi_qua_tran_dung_luong(db, seed):
    """Ảnh quá 5MB là TỪ CHỐI (thỏa thuận CR-204), không nén hộ."""
    user = db.get(User, seed.u_req_id)
    oversized = PNG + b"\x00" * (5 * attach.MB)
    with pytest.raises(ValueError, match="Ảnh tối đa 5MB"):
        attach.store_upload(db, user, "to-qua.png", oversized)


def test_store_upload_luu_dung_khuon_va_tra_metadata(db, seed, monkeypatch):
    keys = _fake_upload(monkeypatch)
    user = db.get(User, seed.u_req_id)

    meta = attach.store_upload(db, user, "man hinh.png", PNG)

    assert meta["content_type"] == "image/png"
    assert meta["size"] == len(PNG)
    sf = db.get(StoredFile, meta["id"])
    #  Key phải nằm trong thư mục chat — đó là dấu resolve_owned dùng để kiểm quyền.
    assert attach.KEY_MARK in sf.file_key
    assert keys == [sf.file_key]
    assert sf.created_by == user.id


# ── resolve_owned: chỉ chính chủ + đúng thư mục chat ────────────────────────────────────

def test_resolve_owned_chan_tep_nguoi_khac_va_tep_ngoai_thu_muc_chat(db, seed):
    user = db.get(User, seed.u_req_id)
    cua_nguoi_khac = _stored_png(db, seed.u_nstm_id)
    #  Tệp CỦA MÌNH nhưng key ở thư mục khác (vd đính kèm chứng từ) cũng không lấy được.
    sai_thu_muc = _stored_png(db, user.id, key_dir="po-attachment")

    with pytest.raises(PermissionError):
        attach.resolve_owned(db, user, [cua_nguoi_khac.id])
    with pytest.raises(PermissionError):
        attach.resolve_owned(db, user, [sai_thu_muc.id])
    with pytest.raises(PermissionError):
        attach.resolve_owned(db, user, [999999])  # id không tồn tại


def test_resolve_owned_gioi_han_3_tep_va_bo_id_trung(db, seed):
    user = db.get(User, seed.u_req_id)
    sf = _stored_png(db, user.id)

    with pytest.raises(ValueError, match="Tối đa 3 tệp"):
        attach.resolve_owned(db, user, [1, 2, 3, 4])
    #  Gửi trùng id thì chỉ tính một — không nhét đôi cùng một ảnh vào lượt gọi model.
    files = attach.resolve_owned(db, user, [sf.id, sf.id])
    assert [f.id for f in files] == [sf.id]


# ── build_blocks + ánh xạ sang định dạng dây của từng provider ──────────────────────────

def test_build_blocks_va_anh_xa_claude_gemini(db, seed, monkeypatch):
    user = db.get(User, seed.u_req_id)
    sf = _stored_png(db, user.id)
    monkeypatch.setattr(attach, "download_bytes", lambda key: PNG)

    blocks = attach.build_blocks([sf])
    assert blocks == [{
        "type": "file", "media_type": "image/png",
        "data_b64": base64.b64encode(PNG).decode("ascii"), "filename": "anh.png",
    }]

    content = blocks + [{"type": "text", "text": "ảnh này là gì?"}]
    #  Claude: ảnh -> image, PDF -> document (đều source base64); text giữ nguyên.
    wired = _wire_content(content)
    assert wired[0] == {"type": "image", "source": {
        "type": "base64", "media_type": "image/png", "data": blocks[0]["data_b64"],
    }}
    assert wired[1] == {"type": "text", "text": "ảnh này là gì?"}
    pdf_block = [{"type": "file", "media_type": "application/pdf", "data_b64": "QQ==", "filename": "a.pdf"}]
    assert _wire_content(pdf_block)[0]["type"] == "document"
    #  Chuỗi trơn đi thẳng, không bọc block — giữ tương thích các lượt không tệp.
    assert _wire_content("hỏi chay") == "hỏi chay"

    #  Gemini: mọi mime chung khuôn inline_data.
    parts = GeminiProvider._parts_of(content)
    assert parts[0] == {"inline_data": {"mime_type": "image/png", "data": blocks[0]["data_b64"]}}
    assert parts[1] == {"text": "ảnh này là gì?"}
    assert GeminiProvider._parts_of("hỏi chay") == [{"text": "hỏi chay"}]


# ── _recent_history: cửa sổ nạp lại tệp thật vs dòng thế chỗ ───────────────────────────

def test_recent_history_tin_cu_the_cho_tin_moi_nap_tep_that(db, seed, monkeypatch):
    """Chỉ ATTACH_REPLAY_WINDOW tin cuối được nạp lại tệp thật — tin cũ hơn thay bằng
    "[Đã gửi kèm tệp: ...]" để hội thoại dài không đốt token nạp lại ảnh base64 mãi."""
    user = db.get(User, seed.u_req_id)
    sf = _stored_png(db, user.id)
    monkeypatch.setattr(attach, "download_bytes", lambda key: PNG)
    meta_json = json.dumps([{"id": sf.id, "filename": "anh.png",
                             "content_type": "image/png", "size": len(PNG)}])

    conv = AssistantConversation(title="t", created_by=user.id, updated_by=user.id)
    db.add(conv)
    db.flush()
    #  6 tin: user(có tệp) / bot / user / bot / user(có tệp) / bot.
    #  Cửa sổ 4 tin cuối phủ idx 2..5 -> tin đầu (idx 0) rơi ra ngoài.
    rows = [
        (MessageRole.USER, "ảnh cũ", meta_json),
        (MessageRole.ASSISTANT, "đáp 1", ""),
        (MessageRole.USER, "hỏi chay", ""),
        (MessageRole.ASSISTANT, "đáp 2", ""),
        (MessageRole.USER, "ảnh mới", meta_json),
        (MessageRole.ASSISTANT, "đáp 3", ""),
    ]
    for role, content, att in rows:
        db.add(AssistantMessage(conversation_id=conv.id, role=role, content=content,
                                attachments=att, created_by=user.id, updated_by=user.id))
    db.commit()

    history = convo._recent_history(db, conv.id)

    assert len(history) == 6
    #  Tin cũ: chuỗi thường kèm dòng thế chỗ, KHÔNG có block base64.
    assert history[0]["content"] == "ảnh cũ\n[Đã gửi kèm tệp: anh.png]"
    #  Tin mới: list block — tệp trước, chữ sau.
    fresh = history[4]["content"]
    assert isinstance(fresh, list)
    assert fresh[0]["type"] == "file"
    assert fresh[1] == {"type": "text", "text": "ảnh mới"}


def test_recent_history_tep_da_xoa_khoi_storage_roi_ve_the_cho(db, seed, monkeypatch):
    """Storage đọc hỏng (tệp bị dọn) thì rơi về dòng thế chỗ, KHÔNG sập cả lượt chat."""
    user = db.get(User, seed.u_req_id)
    sf = _stored_png(db, user.id)

    def _boom(key):
        raise RuntimeError("mất kết nối R2")

    monkeypatch.setattr(attach, "download_bytes", _boom)
    conv = AssistantConversation(title="t", created_by=user.id, updated_by=user.id)
    db.add(conv)
    db.flush()
    db.add(AssistantMessage(
        conversation_id=conv.id, role=MessageRole.USER, content="",
        attachments=json.dumps([{"id": sf.id, "filename": "anh.png"}]),
        created_by=user.id, updated_by=user.id,
    ))
    db.commit()

    history = convo._recent_history(db, conv.id)
    assert history[0]["content"] == "[Đã gửi kèm tệp: anh.png]"


# ── chat(): xâu cả chuỗi — kiểm quyền, truyền block cho service, lưu JSON vào tin ──────

def test_chat_gui_moi_tep_khong_kem_chu(db, seed, monkeypatch):
    monkeypatch.setattr(settings, "AI_DAILY_MSG_LIMIT", 0)
    monkeypatch.setattr(attach, "download_bytes", lambda key: PNG)
    captured: dict = {}

    def _fake_ask(message, **kwargs):
        captured["message"] = message
        captured["attachments"] = kwargs.get("attachments")
        return {"text": "Đó là ảnh một dòng Excel.", "provider": "claude", "model": "m",
                "kind": "general", "tool_calls": [], "usage": {}}

    monkeypatch.setattr(convo.service, "ask", _fake_ask)
    user = db.get(User, seed.u_req_id)
    sf = _stored_png(db, user.id)

    out = convo.chat(db, user, AskIn(message="", attachment_ids=[sf.id]))

    #  Block tệp phải tới được service.ask (đầu vào của provider).
    assert captured["attachments"][0]["type"] == "file"
    assert captured["attachments"][0]["filename"] == "anh.png"
    #  Không có chữ -> tiêu đề hội thoại lấy theo tên tệp cho danh sách còn đọc được.
    assert out["title"] == "Tệp: anh.png"
    msgs = (
        db.query(AssistantMessage)
        .filter(AssistantMessage.conversation_id == out["conversation_id"])
        .order_by(AssistantMessage.id).all()
    )
    #  Tin user lưu metadata JSON để lịch sử vẽ lại chip + nạp lại tệp về sau.
    saved = json.loads(msgs[0].attachments)
    assert saved[0]["id"] == sf.id
    assert msgs[1].attachments == ""  # tin trợ lý không mang tệp


def test_chat_chan_tep_cua_nguoi_khac(db, seed, monkeypatch):
    monkeypatch.setattr(settings, "AI_DAILY_MSG_LIMIT", 0)

    def _boom(*a, **k):
        raise AssertionError("service.ask không được gọi khi tệp không phải của mình")

    monkeypatch.setattr(convo.service, "ask", _boom)
    user = db.get(User, seed.u_req_id)
    cua_nguoi_khac = _stored_png(db, seed.u_nstm_id)

    with pytest.raises(PermissionError):
        convo.chat(db, user, AskIn(message="đọc hộ", attachment_ids=[cua_nguoi_khac.id]))


# ── endpoint xem lại tệp: bấm chip trong lịch sử ───────────────────────────────────────

def test_view_chat_attachment_chinh_chu_mo_duoc_nguoi_khac_an_404(db, seed, monkeypatch):
    from fastapi import HTTPException

    from app.modules.assistant import controller

    monkeypatch.setattr(settings, "AI_ENABLED", True)
    monkeypatch.setattr(attach, "download_bytes", lambda key: PNG)
    user = db.get(User, seed.u_req_id)
    sf = _stored_png(db, user.id)

    resp = controller.view_chat_attachment(sf.id, user=user, db=db)
    assert resp.body == PNG
    assert resp.media_type == "image/png"
    #  `inline` để trình duyệt hiện thẳng ảnh/PDF trong tab, không ép tải về.
    assert resp.headers["Content-Disposition"].startswith("inline")

    ke_khac = db.get(User, seed.u_nstm_id)
    with pytest.raises(HTTPException) as err:
        controller.view_chat_attachment(sf.id, user=ke_khac, db=db)
    assert err.value.status_code == 404


def test_askin_doi_hoi_co_chu_hoac_co_tep():
    with pytest.raises(ValidationError):
        AskIn(message="   ")
    #  Có tệp thì chữ được phép rỗng — ca "gửi mỗi ảnh".
    assert AskIn(message="", attachment_ids=[1]).attachment_ids == [1]
