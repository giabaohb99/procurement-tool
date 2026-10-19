"""ai-CR-192 (16.5 đợt 2, 13/10 16:27 anh Được thấy chậm): «hello» 70 s vì (1) bước đọc ý định chờ Gemini quá tải đủ 25 s
mới đổi model, (2) câu xã giao vẫn nạp đủ 73 công cụ + 7 gói tri thức (56k token). Nay: trần chờ theo lượt cho bước ý định;
xã giao → nhóm lõi + không gói; câu không khớp nhóm → đủ công cụ nhưng không gói chủ đề, model xin thêm được."""
from app.modules.assistant import tool_router as tr
from app.modules.assistant.provider import base


def test_nhan_cau_xa_giao():
    for t in ("hello", "Hi", "chào em", "Chào Lạc Lạc", "cảm ơn em nhé", "ok", "alo", "test"):
        assert tr.is_smalltalk(t), t
    for t in ("chào em, công nợ Hòa Phát còn bao nhiêu", "giá vàng hôm nay", "ok tạo luôn", "hello anh muốn hỏi về nghỉ phép"):
        assert not tr.is_smalltalk(t), t


def test_tran_cho_theo_luot():
    assert base.request_timeout(60) == 60
    with base.with_timeout(10):
        assert base.request_timeout(60) == 10
        assert base.request_timeout(5) == 5                 # không vượt trần của provider
    assert base.request_timeout(60) == 60



def test_khong_khop_nhom_thi_du_cong_cu_va_doc_cam_nang_bang_tool(db, seed, monkeypatch):
    """ai-CR-220 (K7) thay bài «câu không khớp nhóm → đủ công cụ nhưng không gói, xin thêm được»: gói tri thức đã bỏ, nên
    không còn đường «xin thêm gói». Câu không khớp nhóm nào → gửi ĐỦ công cụ MỘT lần (không hỏi lại), lời nhắc mang danh
    mục cẩm nang và có sẵn read_skill để model tự đọc."""
    from app.modules.ai_skill.handbook_seed import ensure_system_handbook
    from app.modules.assistant import service
    from app.modules.assistant.provider.base import ChatResult
    from app.modules.user.model import User

    ensure_system_handbook(db)
    calls: list[tuple[set, str]] = []

    class P:
        name = "fake"
        supports_tools = True

        def run_tools(self, msgs, *, tools, execute, system, **kw):
            calls.append(({t.name for t in tools}, system))
            return ChatResult(text="xong", provider="fake", model="m")

    monkeypatch.setattr(service, "get_provider", lambda name=None: P())
    out = service.ask("cho anh hỏi cái này được không", db=db, user=db.get(User, seed.u_req_id))
    assert len(calls) == 1 and out["usage"]["tools_retried"] is False
    names, system = calls[0]
    assert len(names) > 40 and {"read_skill", "list_skills"} <= names
    assert "- nha-may-he-thong-cong-viec:" in system and "Bản cô đọng để trợ lý AI tra cứu nhanh" not in system
