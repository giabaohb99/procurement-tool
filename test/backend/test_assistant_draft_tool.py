"""Tool `draft_survey_request` + `draft_purchase_request` — soạn nháp phiếu cho Trợ lý
AI, KHÔNG ghi DB.

Chốt ba điều: (1) không có quyền tạo phiếu thì bị từ chối, (2) args do model điền được
chuẩn hóa phòng thủ (số rác về 0, dòng thiếu tên hàng bị loại, cắt trần số dòng),
(3) kết quả thành công có `total` — provider dùng nó làm `rows` để giao diện biết
tool chạy thật mới hiện nút "Tạo yêu cầu báo giá" / "Tạo yêu cầu mua hàng".
Riêng YCMH thêm khớp mã hàng danh mục: khớp 1 kết quả mới điền mã, mơ hồ thì trả
`unmatched` kèm gợi ý để người dùng tự chọn trên form.
"""
from app.modules.assistant.tools.base import ToolContext
from app.modules.assistant.tools.draft_tool import MAX_LINES, _run, _run_purchase


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


# ── draft_purchase_request (YCMH) ───────────────────────────────────────────────────────

def _them_san_pham(db, code: str, name: str, unit: str = "Cái", group: str = "VPP"):
    from app.modules.product.model import Product

    db.add(Product(code=code, name=name, item_group=group, unit=unit, hh_code=""))
    db.commit()


def test_ycmh_khong_quyen_thi_tu_choi(db, seed, monkeypatch):
    from app.modules.user.model import User

    ctx = _ctx(db, db.get(User, seed.u_req_id), allowed=False, monkeypatch=monkeypatch)
    out = _run_purchase(ctx, {"purpose": "Mua giấy", "lines": [{"product": "Giấy A4"}]})
    assert out.get("denied") is True
    assert "total" not in out


def test_ycmh_thieu_purpose_hoac_lines_bao_loi_mem(db, seed, monkeypatch):
    from app.modules.user.model import User

    ctx = _ctx(db, db.get(User, seed.u_req_id), allowed=True, monkeypatch=monkeypatch)
    assert "error" in _run_purchase(ctx, {"purpose": "", "lines": [{"product": "Giấy"}]})
    assert "error" in _run_purchase(ctx, {"purpose": "Mua", "lines": []})
    # Dòng có nhưng toàn rác (thiếu product) -> cũng lỗi mềm, không nổ exception.
    assert "error" in _run_purchase(ctx, {"purpose": "Mua", "lines": [{}, "rác"]})


def test_ycmh_khop_ma_hang_chinh_xac_dien_ma_va_dvt(db, seed, monkeypatch):
    from app.modules.user.model import User

    _them_san_pham(db, "GIAY-A4", "Giấy A4 Double A", unit="Ram")
    ctx = _ctx(db, db.get(User, seed.u_req_id), allowed=True, monkeypatch=monkeypatch)

    out = _run_purchase(ctx, {"purpose": "Mua văn phòng phẩm", "lines": [
        {"product": "GIAY-A4", "qty": 10, "uom": "cái"},   # ĐVT model điền bị ĐÈ bằng danh mục
    ]})
    assert out["status"] == "ready"
    assert out["total"] == 1
    assert "unmatched" not in out
    line = out["draft"]["lines"][0]
    assert line["product_code"] == "GIAY-A4"
    assert line["product_name"] == "Giấy A4 Double A"
    assert line["unit"] == "Ram"       # ưu tiên ĐVT của danh mục sản phẩm
    assert line["qty"] == 10


def test_ycmh_khop_mo_ta_duy_nhat_moi_dien_ma(db, seed, monkeypatch):
    """Mô tả khớp đúng 1 sản phẩm -> điền mã; khớp nhiều -> để mã rỗng + trả gợi ý."""
    from app.modules.user.model import User

    _them_san_pham(db, "MAN-27", "Màn hình Dell 27 inch")
    _them_san_pham(db, "MAN-24A", "Màn hình LG 24 inch")
    _them_san_pham(db, "MAN-24B", "Màn hình Samsung 24 inch")
    ctx = _ctx(db, db.get(User, seed.u_req_id), allowed=True, monkeypatch=monkeypatch)

    out = _run_purchase(ctx, {"purpose": "Trang bị màn hình", "lines": [
        {"product": "Dell 27"},      # duy nhất -> khớp
        {"product": "Màn hình"},     # 3 ứng viên -> unmatched + gợi ý
    ]})
    assert out["total"] == 2
    lines = out["draft"]["lines"]
    assert lines[0]["product_code"] == "MAN-27"
    assert lines[1]["product_code"] == ""
    assert lines[1]["product_name"] == "Màn hình"   # giữ nguyên mô tả người dùng
    assert len(out["unmatched"]) == 1
    goi_y = {s["code"] for s in out["unmatched"][0]["suggestions"]}
    assert goi_y == {"MAN-27", "MAN-24A", "MAN-24B"}
    # Nhắc model dặn người dùng chọn lại mã trên form.
    assert "chưa khớp" in out["reminder"]


def test_ycmh_khong_khop_gi_van_giu_dong_de_nguoi_dung_tu_dien(db, seed, monkeypatch):
    from app.modules.user.model import User

    ctx = _ctx(db, db.get(User, seed.u_req_id), allowed=True, monkeypatch=monkeypatch)
    out = _run_purchase(ctx, {"purpose": "Mua hàng lạ", "lines": [
        {"product": "Máy chiếu hologram", "qty": "một"},   # số rác -> 0
    ]})
    assert out["total"] == 1
    line = out["draft"]["lines"][0]
    assert line["product_code"] == ""
    assert line["product_name"] == "Máy chiếu hologram"
    assert line["qty"] == 0
    assert out["unmatched"][0]["suggestions"] == []

# ── draft_leave_request (Giấy nghỉ phép) ────────────────────────────────────────────────

def _them_loai_gnp(db, is_active=True):
    from app.modules.doc_catalog.model import DocType

    row = DocType(code="GNP", name="Giấy nghỉ phép", group_code="A", is_personal=True,
                  needs_approval=True, is_active=is_active, created_by=1, updated_by=1)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def test_nghi_phep_khong_quyen_thi_tu_choi(db, seed, monkeypatch):
    from app.modules.assistant.tools.draft_tool import _run_leave
    from app.modules.user.model import User

    _them_loai_gnp(db)
    ctx = _ctx(db, db.get(User, seed.u_req_id), allowed=False, monkeypatch=monkeypatch)
    out = _run_leave(ctx, {"from_date": "2026-09-01", "to_date": "2026-09-01",
                           "reason": "Việc gia đình"})
    assert out.get("denied") is True
    assert "total" not in out


def test_nghi_phep_chua_khai_loai_gnp_bao_loi_mem(db, seed, monkeypatch):
    from app.modules.assistant.tools.draft_tool import _run_leave
    from app.modules.user.model import User

    ctx = _ctx(db, db.get(User, seed.u_req_id), allowed=True, monkeypatch=monkeypatch)
    out = _run_leave(ctx, {"from_date": "2026-09-01", "to_date": "2026-09-01",
                           "reason": "Việc gia đình"})
    assert "error" in out
    assert "total" not in out


def test_nghi_phep_thieu_hoac_sai_ngay_bao_loi_mem(db, seed, monkeypatch):
    from app.modules.assistant.tools.draft_tool import _run_leave
    from app.modules.user.model import User

    _them_loai_gnp(db)
    ctx = _ctx(db, db.get(User, seed.u_req_id), allowed=True, monkeypatch=monkeypatch)

    assert "error" in _run_leave(ctx, {"from_date": "mai", "to_date": "2026-09-01",
                                       "reason": "x"})
    assert "error" in _run_leave(ctx, {"from_date": "2026-09-01", "to_date": "2026-09-01",
                                       "reason": ""})
    #  Đến ngày trước Từ ngày — phải hỏi lại chứ không lẳng lặng soạn đơn ngược.
    assert "error" in _run_leave(ctx, {"from_date": "2026-09-05", "to_date": "2026-09-01",
                                       "reason": "x"})
    #  Chiều -> sáng cùng ngày là khoảng trống (cùng luật với type_metadata backend).
    assert "error" in _run_leave(ctx, {"from_date": "2026-09-01", "to_date": "2026-09-01",
                                       "from_session": "afternoon", "to_session": "morning",
                                       "reason": "x"})


def test_nghi_phep_du_thong_tin_soan_du_ban_nhap(db, seed, monkeypatch):
    """Happy path: điền doc_type_id thật của môi trường, tính số ngày gợi ý cùng công thức
    với form, và tiêu đề mang tên người hỏi."""
    from app.modules.assistant.tools.draft_tool import _run_leave
    from app.modules.user.model import User

    gnp = _them_loai_gnp(db)
    ctx = _ctx(db, db.get(User, seed.u_req_id), allowed=True, monkeypatch=monkeypatch)
    out = _run_leave(ctx, {"from_date": "2026-09-01", "to_date": "2026-09-03",
                           "reason": "Về quê có việc gia đình", "leave_type": "unpaid",
                           "contact_phone": "0900000001"})

    assert out["status"] == "ready"
    assert out["total"] == 1
    draft = out["draft"]
    assert draft["kind"] == "leave_request"
    assert draft["doc_type_id"] == gnp.id
    assert "Người YC" in draft["title"]
    leave = draft["leave"]
    assert leave["leave_type"] == "unpaid"
    assert leave["total_days"] == 3          # 01 -> 03, cả ngày: 1 trọn vẹn + 2 đầu cuối
    assert leave["reason"] == "Về quê có việc gia đình"
    assert leave["contact_phone"] == "0900000001"
    assert "CHƯA được tạo" in out["reminder"]


def test_nghi_phep_gia_tri_ngoai_bo_ma_ve_mac_dinh(db, seed, monkeypatch):
    """Model điền loại nghỉ / buổi bậy thì về mặc định (annual / full) chứ không nổ lỗi —
    các ô này trên form là ô chọn, người dùng rà lại được. Nửa ngày tính 0.5 công."""
    from app.modules.assistant.tools.draft_tool import _run_leave
    from app.modules.user.model import User

    _them_loai_gnp(db)
    ctx = _ctx(db, db.get(User, seed.u_req_id), allowed=True, monkeypatch=monkeypatch)

    out = _run_leave(ctx, {"from_date": "2026-09-01", "to_date": "2026-09-01",
                           "leave_type": "vacation", "from_session": "sáng",
                           "reason": "Khám bệnh"})
    leave = out["draft"]["leave"]
    assert leave["leave_type"] == "annual"
    assert leave["from_session"] == "full"

    nua_ngay = _run_leave(ctx, {"from_date": "2026-09-01", "to_date": "2026-09-01",
                                "from_session": "morning", "to_session": "morning",
                                "reason": "Khám bệnh"})
    assert nua_ngay["draft"]["leave"]["total_days"] == 0.5
