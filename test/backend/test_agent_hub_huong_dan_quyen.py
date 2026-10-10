"""ai-CR-157 — đại ca 10/10/2026: «cập nhật hướng dẫn của các phần này cho bot, họ hỏi hoặc em có thể gợi ý cho để họ có
thể xem hướng dẫn sử dụng hoặc check quyền của họ có thể sử dụng chức năng nào»."""
import pytest

from app.modules.agent_hub import user_guide as ug


@pytest.mark.parametrize("q", ["quyền của tôi", "Quyền của anh?", "kiểm tra quyền của tôi", "tôi có quyền gì",
                               "anh dùng được gì", "tôi làm được những gì", "/quyen", "check quyền của mình"])
def test_nhan_ra_cau_hoi_quyen(q):
    assert ug.is_permission_question(q), q


@pytest.mark.parametrize("q", ["bot làm được gì", "quyền duyệt phiếu YCMH00012 là của ai", "hướng dẫn phiếu",
                               "phân quyền tài khoản ở đâu", ""])
def test_khong_nham_cau_khac(q):
    assert not ug.is_permission_question(q), q


def test_bang_quyen_theo_ma_tran_erp():
    allowed = {("leave_request", "create"), ("leave_request", "write"), ("payable", "read")}
    text = ug.render_permissions(lambda e, a: (e, a) in allowed, who="Nguyễn Văn A")
    assert "Nguyễn Văn A" in text
    assert "• Đơn nghỉ phép: <b>được</b> — <code>xin nghỉ thứ 6 cả ngày</code>" in text
    assert "• Yêu cầu mua hàng (YCMH): <i>chưa được cấp</i>" in text
    assert "Công nợ nhà cung cấp: <b>được</b>" in text and "Phân quyền tài khoản" in text and "«" not in text


def test_huong_dan_co_nhom_tao_phieu_va_sua_phieu():
    phieu = ug.render("phieu")
    assert phieu.startswith("<b>Tạo phiếu nháp</b>") and "thêm vào 1" in phieu and "ghi đè 1" in phieu
    sua = ug.render("sua phieu")
    assert sua.startswith("<b>Sửa, xóa phiếu đã có</b>") and "sửa lý do đơn NP011" in sua and "15 phút" in sua
    full = ug.render()
    assert "quyền của tôi" in full and "hướng dẫn sửa phiếu" in full and len(full) < 3900
    assert "«" not in full
    admin = ug.render("sua ma", admin=True)
    assert "sửa cho xanh AI-0007" in admin and "tự gộp và đưa lên dev" in admin


def test_chat_hoi_quyen_tra_dung_tai_khoan(db, monkeypatch):
    from types import SimpleNamespace

    from app.core.config import settings
    from app.modules.agent_hub import erp, service
    from app.modules.agent_hub.constants import DIR_IN

    monkeypatch.setattr(settings, "AGENT_TELEGRAM_CHAT_ID", "12345")
    sent: list[str] = []
    monkeypatch.setattr(service, "reply", lambda db, chat_id, text, **kw: sent.append(text))
    monkeypatch.setattr(service, "_assistant_user", lambda db, chat_id="": None)
    row = service.log_message(db, DIR_IN, "999", 1, "quyền của tôi")
    db.commit()
    assert service._guide_by_text(db, "999", row, "quyền của tôi") and "chưa đăng nhập ERP" in sent[-1]
    me = SimpleNamespace(id=7)
    monkeypatch.setattr(service, "_assistant_user", lambda db, chat_id="": me)
    monkeypatch.setattr(erp, "describe", lambda db, user: ("Trần B", ""))
    monkeypatch.setattr(erp, "can", lambda db, user, e, a: e == "survey_request")
    assert service._guide_by_text(db, "999", row, "tôi dùng được gì")
    assert "Trần B" in sent[-1] and "Yêu cầu báo giá (YCBG): <b>được</b>" in sent[-1]
    assert "Đơn nghỉ phép: <i>chưa được cấp</i>" in sent[-1]
