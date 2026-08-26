"""Tool `draft_survey_request` — soạn nháp YCBG cho Trợ lý AI, KHÔNG ghi DB.

Chốt ba điều: (1) không có quyền tạo YCBG thì bị từ chối, (2) args do model điền được
chuẩn hóa phòng thủ (số rác về 0, dòng thiếu tên hàng bị loại, cắt trần số dòng),
(3) kết quả thành công có `total` — provider dùng nó làm `rows` để giao diện biết
tool chạy thật mới hiện nút "Tạo yêu cầu báo giá".
"""
from app.modules.assistant.tools.base import ToolContext
from app.modules.assistant.tools.draft_tool import MAX_LINES, _run


def _ctx(db, user, allowed: bool, monkeypatch) -> ToolContext:
    monkeypatch.setattr(ToolContext, "can", lambda self, entity, action="read": allowed)
    return ToolContext(db=db, user=user)


def test_khong_quyen_tao_ycbg_thi_tu_choi(db, seed, monkeypatch):
    from app.modules.user.model import User

    ctx = _ctx(db, db.get(User, seed.u_req_id), allowed=False, monkeypatch=monkeypatch)
    out = _run(ctx, {"purpose": "Mua màn hình", "lines": [{"requirement_detail": "Màn 27 inch"}]})
    assert out.get("denied") is True
    assert "total" not in out   # denied không được mang total, kẻo FE tưởng thành công


def test_chuan_hoa_args_model_dien(db, seed, monkeypatch):
    from app.modules.user.model import User

    ctx = _ctx(db, db.get(User, seed.u_req_id), allowed=True, monkeypatch=monkeypatch)
    out = _run(ctx, {
        "purpose": "  Trang bị màn hình  ",
        "note": "Giao trong tháng",
        "lines": [
            {"requirement_detail": ""},                                    # loại: thiếu tên hàng
            {"requirement_detail": " Màn 27 inch ", "request_qty": "hai",  # số rác -> 0
             "proposed_price": -5, "uom": "cái"},
        ],
    })
    assert out["status"] == "ready"
    assert out["total"] == 1
    draft = out["draft"]
    assert draft["purpose"] == "Trang bị màn hình"
    line = draft["lines"][0]
    assert line["requirement_detail"] == "Màn 27 inch"
    assert line["request_qty"] == 0
    assert line["proposed_price"] == 0
    assert line["uom"] == "cái"


def test_chuan_hoa_dvt_theo_danh_muc(db, seed, monkeypatch):
    """Model hay điền "cái" thường trong khi danh mục là "Cái" — ô chọn ĐVT trên form khớp
    đúng chuỗi nên hiện trống dù dữ liệu có (lỗi bắt được khi test UI 26/08/2026)."""
    from app.modules.catalog.model import Unit
    from app.modules.user.model import User

    db.add(Unit(code="CAI", name="Cái", is_active=True))
    db.commit()

    ctx = _ctx(db, db.get(User, seed.u_req_id), allowed=True, monkeypatch=monkeypatch)
    out = _run(ctx, {"purpose": "Mua màn hình", "lines": [
        {"requirement_detail": "Màn 27 inch", "uom": "cái"},   # khớp -> lấy chính tả danh mục
        {"requirement_detail": "Bàn phím", "uom": "chiếc"},    # không khớp -> giữ nguyên
    ]})
    assert out["draft"]["lines"][0]["uom"] == "Cái"
    assert out["draft"]["lines"][1]["uom"] == "chiếc"


def test_cat_tran_so_dong_va_bao_loi_khi_thieu(db, seed, monkeypatch):
    from app.modules.user.model import User

    ctx = _ctx(db, db.get(User, seed.u_req_id), allowed=True, monkeypatch=monkeypatch)

    # Quá trần -> chỉ giữ MAX_LINES dòng đầu.
    many = [{"requirement_detail": f"Hàng {i}"} for i in range(MAX_LINES + 5)]
    out = _run(ctx, {"purpose": "Mua nhiều", "lines": many})
    assert out["total"] == MAX_LINES

    # Thiếu purpose / lines -> lỗi mềm để model hỏi lại, không nổ exception.
    assert "error" in _run(ctx, {"purpose": "", "lines": many})
    assert "error" in _run(ctx, {"purpose": "Mua", "lines": []})
    assert "error" in _run(ctx, {"purpose": "Mua", "lines": [{}]})
