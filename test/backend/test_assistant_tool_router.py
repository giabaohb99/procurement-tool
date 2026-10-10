"""ai-CR-161 (phase 16.2 + 16.3) — nạp công cụ theo nhu cầu: nhóm lõi + nhóm câu hỏi chạm tới; không khớp → gửi đủ;
model báo thiếu → hỏi lại một lần với đủ công cụ."""
import pytest

from app.modules.assistant import tool_router as tr


def test_moi_cong_cu_deu_co_nhom(db):
    """Thêm công cụ mới mà quên xếp nhóm thì nó chỉ còn được gửi khi câu hỏi không khớp nhóm nào — ĐỎ ở đây."""
    from app.core.config import settings
    from app.modules.assistant import tools as T

    old = settings.AI_RAG_ENABLED
    settings.AI_RAG_ENABLED = True
    try:
        names = {d.name for d in T.tool_defs()}
    finally:
        settings.AI_RAG_ENABLED = old
    missing = sorted(names - tr.ALL_GROUPED)
    assert missing == [], f"công cụ chưa xếp nhóm ở tool_router.GROUPS: {missing}"
    assert sorted(tr.ALL_GROUPED - names) == [], "tool_router còn khai công cụ không tồn tại"


@pytest.mark.parametrize("q,must", [
    ("công nợ Hòa Phát còn bao nhiêu", {"payable_lookup"}),
    ("3 đơn mua hàng gần nhất", {"recent_purchase_orders"}),
    ("phiếu nào đang chờ anh duyệt", {"my_approval_tasks"}),
    ("xin nghỉ thứ 6 cả ngày", {"draft_leave_request"}),
    ("lên phiếu mua 10 ram giấy A4", {"draft_purchase_request"}),
    ("sửa lý do đơn NP011 thành đi khám", {"propose_document_update"}),
    ("xóa phiếu YCMH00012", {"propose_document_delete"}),
    ("giá nhập khẩu phân bón tháng này", {"customs_price_stats"}),
    ("lịch hôm nay của anh", {"my_calendar_events"}),
    ("nhóm Kế toán hôm nay bàn gì", {"read_group_messages"}),
    ("biên bản vừa rồi gửi lại anh", {"latest_meeting_report"}),
    ("tháng này anh chi tiêu bao nhiêu", {"list_personal_items"}),
    ("tắt bản tin 2", {"manage_briefs"}),
    ("lên task gọi NCC Hòa Phát cho anh Được", {"draft_work_task"}),
])
def test_chon_dung_nhom(q, must):
    picked = tr.select(q)
    assert picked is not None and must <= picked, (q, sorted(must - (picked or set())))
    assert tr.CORE <= picked and len(picked) < 40


def test_khong_khop_nhom_thi_gui_du_va_cau_noi_tiep_giu_nhom_cu():
    assert tr.select("chào em") is None
    assert tr.select("ok cảm ơn nhé") is None
    follow = tr.select("xuất Excel giúp anh", recent_tools=["payable_lookup"])
    assert {"export_excel_file", "payable_lookup"} <= follow


def test_model_bao_thieu_cong_cu_thi_hoi_lai_voi_du(db, seed, monkeypatch):
    from app.modules.assistant import service
    from app.modules.assistant.provider.base import ChatResult
    from app.modules.user.model import User

    calls: list[tuple[int, str]] = []

    class P:
        name = "fake"
        supports_tools = True

        def run_tools(self, msgs, *, tools, execute, system, **kw):
            calls.append((len(tools), system))
            text = tr.NEED_MORE_TOOLS if len(calls) == 1 else "Đây là câu trả lời"
            return ChatResult(text=text, provider="fake", model="m", input_tokens=10, output_tokens=1)

    monkeypatch.setattr(service, "get_provider", lambda name=None: P())
    out = service.ask("công nợ Hòa Phát còn bao nhiêu", db=db, user=db.get(User, seed.u_req_id))
    assert len(calls) == 2 and calls[0][0] < calls[1][0]
    assert tr.ROUTED_NOTE in calls[0][1] and tr.ROUTED_NOTE not in calls[1][1]
    assert out["text"] == "Đây là câu trả lời" and out["usage"]["tools_retried"] is True
    assert out["usage"]["tools_offered"] == calls[1][0]
    calls.clear()
    out = service.ask("chào em", db=db, user=db.get(User, seed.u_req_id))
    assert len(calls) == 1 and tr.ROUTED_NOTE not in calls[0][1] and out["usage"]["tools_retried"] is False


def test_thu_tu_loi_dan_co_dinh_truoc_thay_doi_sau():
    from app.modules.assistant.service import _extra_system

    text = _extra_system(True, "LOI DAN KENH", "CHAN DUNG", "THUAT NGU CAU NAY", routed_note=True)
    assert text.index("CHAN DUNG") < text.index("LOI DAN KENH") < text.index("THUAT NGU CAU NAY") \
        < text.index(tr.NEED_MORE_TOOLS)
