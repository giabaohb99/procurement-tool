"""Đại ca 09/10/2026: «có những trường cần thiết nhưng nó không hỏi lại, xác nhận lại để đủ thông tin hơn … bỏ kí tự «
này rồi mà». Ca thật: «tạo đơn nghỉ việc vào ngày thứ 2 tuần sau cho anh nhé» → bot soạn luôn loại Phép năm (mặc định
ngầm) + lý do «Việc cá nhân» (model tự nghĩ)."""
import pytest

from app.modules.assistant.tools import confirm_fields as cf

CA_THAT = "tạo đơn nghỉ việc vào ngày thứ 2 tuần sau cho anh nhé"


def _ctx(db, user, monkeypatch):
    from app.modules.assistant.tools.base import ToolContext

    ctx = ToolContext(db=db, user=user)
    monkeypatch.setattr(ToolContext, "can", lambda self, entity, action="read": True)
    return ctx


def _loai_nghi(db):
    from app.modules.leave.catalog_model import LeaveType

    rows = [LeaveType(code="ANNUAL", name="Phép năm", counts_balance=True, is_active=True, sort_order=1),
            LeaveType(code="UNPAID", name="Nghỉ không lương", counts_balance=False, is_active=True, sort_order=2)]
    db.add_all(rows)
    db.commit()
    return rows


def test_gia_tri_nguoi_dung_chua_noi_thi_khong_tinh():
    text = cf._fold(CA_THAT)
    assert not cf.stated(text, "Việc cá nhân")            # «việc» có trong câu nhưng cụm «việc cá nhân» thì không
    assert cf.stated(cf._fold("nghỉ thứ 2 vì đi khám bệnh"), "Khám bệnh")
    assert cf.stated("", "bất kỳ")                         # không có lời người dùng (gọi thẳng) → tin model
    assert not cf.stated(text, "")
    assert cf.mentions(cf._fold("xin nghỉ buổi chiều mai"), "buoi chieu") and not cf.mentions(text, "buoi chieu")


def test_don_nghi_ca_that_hoi_lai_ly_do_va_loai_nghi(db, seed, monkeypatch):
    from app.modules.assistant.tools.draft_tool import _run_leave
    from app.modules.user.model import User

    _loai_nghi(db)
    ctx = _ctx(db, db.get(User, seed.u_req_id), monkeypatch)
    out = _run_leave(ctx, {"from_date": "2026-10-12", "to_date": "2026-10-12", "reason": "Việc cá nhân",
                           cf.USER_TEXT_ARG: CA_THAT})
    assert "draft" not in out and "need_info" in out
    fields = {x["field"]: x for x in out["need_info"]}
    assert set(fields) == {"reason", "leave_type"}
    assert fields["leave_type"]["options"] == ["Phép năm", "Nghỉ không lương"]
    #  Người dùng trả lời: lần gọi sau đủ thông tin → soạn, «nghỉ cả ngày» là điều em TỰ HIỂU, ghi ra để xác nhận.
    out = _run_leave(ctx, {"from_date": "2026-10-12", "to_date": "2026-10-12", "reason": "đưa con đi khám",
                           "leave_type": "ANNUAL",
                           cf.USER_TEXT_ARG: CA_THAT + "\nphép năm, đưa con đi khám"})
    assert out["status"] == "ready" and out["draft"]["reason"] == "đưa con đi khám"
    assert out["draft"]["assumptions"] == ["nghỉ cả ngày"]
    #  Người dùng bảo «không cần lý do» → Trợ lý gọi lại với asked_fields, tool không hỏi lần hai.
    out = _run_leave(ctx, {"from_date": "2026-10-12", "to_date": "2026-10-12", "leave_type": "ANNUAL",
                           "asked_fields": ["reason"], cf.USER_TEXT_ARG: CA_THAT + "\nkhông cần lý do"})
    assert out["status"] == "ready" and any("lý do" in a for a in out["draft"]["assumptions"])
    #  Tham số ẩn không lọt vào bản nháp.
    assert cf.USER_TEXT_ARG not in str(out["draft"])


def test_ycmh_thieu_muc_dich_so_luong_ngay_kho_thi_hoi_mot_luot(db, seed, monkeypatch):
    from app.modules.assistant.tools.draft_tool import _run_purchase
    from app.modules.catalog.model import Warehouse
    from app.modules.user.model import User

    db.add(Warehouse(code="K1", name="Kho Cần Thơ", is_active=True))
    db.commit()
    ctx = _ctx(db, db.get(User, seed.u_req_id), monkeypatch)
    out = _run_purchase(ctx, {"purpose": "Phục vụ sản xuất", "lines": [{"product": "giấy A4"}],
                              cf.USER_TEXT_ARG: "lên phiếu mua giấy A4 giúp anh"})
    fields = {x["field"] for x in out["need_info"]}
    assert fields == {"purpose", "qty", "need_date", "warehouse"}
    assert {"field": "warehouse", "question": "Nhận hàng ở kho nào?", "options": ["Kho Cần Thơ"]} in out["need_info"]
    out = _run_purchase(ctx, {"purpose": "in hợp đồng", "need_date": "2026-10-20",
                              "lines": [{"product": "giấy A4", "qty": 10, "uom": "ram", "warehouse": "Kho Cần Thơ"}],
                              cf.USER_TEXT_ARG: "lên phiếu mua giấy A4 giúp anh\n10 ram, để in hợp đồng, cần 20/10, "
                                                "kho Cần Thơ"})
    assert out["status"] == "ready"


def test_giao_viec_chua_noi_giao_ai_thi_hoi(db, seed, monkeypatch):
    from app.modules.assistant.tools.work_tool import _draft_work_task
    from app.modules.user.model import User

    ctx = _ctx(db, db.get(User, seed.u_req_id), monkeypatch)
    out = _draft_work_task(ctx, {"title": "Gọi NCC Hòa Phát", cf.USER_TEXT_ARG: "lên task gọi NCC Hòa Phát"})
    assert out["need_info"][0]["field"] == "assignees"


def test_tro_ly_chen_loi_nguoi_dung_chi_cho_tool_soan_nhap():
    from app.modules.assistant.service import _with_user_text

    hist = [{"role": "user", "content": "xin nghỉ thứ 2"}, {"role": "assistant", "content": "lý do?"}]
    args = _with_user_text("draft_leave_request", {"from_date": "x"}, "đi khám", hist)
    assert args[cf.USER_TEXT_ARG] == "xin nghỉ thứ 2\nđi khám" and "lý do?" not in args[cf.USER_TEXT_ARG]
    assert cf.USER_TEXT_ARG not in _with_user_text("payable_lookup", {"supplier": "x"}, "đi khám", hist)


def test_the_nhap_khong_con_ngoac_va_hien_dieu_tu_hieu():
    from app.modules.agent_hub.service import draft_card

    card = draft_card("leave", {"from_date": "2026-10-12", "to_date": "2026-10-12", "from_session": 1, "to_session": 1,
                                "reason": "đưa con đi khám", "lines": [{"leave_type": "Phép năm", "days": 1.0}],
                                "assumptions": ["nghỉ cả ngày"]})
    assert "«" not in card and "»" not in card
    assert "<b>BẢN NHÁP ĐƠN NGHỈ PHÉP</b>" in card and "<b>Ngày nghỉ:</b> 12/10/2026 (thứ hai)" in card
    assert "<b>Loại nghỉ:</b> Phép năm · 1 ngày" in card
    assert "Em đang hiểu là" in card and "• nghỉ cả ngày" in card
    assert "<code>tạo và gửi duyệt</code>" in card


@pytest.mark.parametrize("raw,expected", [
    ("Nhắn «tạo» để lưu", "Nhắn <b>tạo</b> để lưu"),
    ("«a» và «b»", "<b>a</b> và <b>b</b>"),
    ("<code>«giữ»</code> ngoài «đổi»", "<code>«giữ»</code> ngoài <b>đổi</b>"),
    ("lẻ « không đóng", "lẻ  không đóng"),
    ("không có gì", "không có gì"),
])
def test_moi_tin_gui_di_bo_ngoac(raw, expected):
    from app.modules.agent_hub.telegram import polish

    assert polish(raw) == expected
