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


def test_phan_loai_bia_bi_bo_trong_va_tra_danh_muc(db, seed, monkeypatch):
    """Model bịa phân loại ngoài danh mục ("Thiết bị văn phòng / IT") đổ vào ô CHỌN làm
    form lỗi (khách bắt được khi test 26/08/2026). Không khớp thì BỎ TRỐNG + trả danh sách
    hợp lệ để model nêu cho người dùng chọn; khớp lệch hoa thường thì lấy chính tả danh mục."""
    from app.modules.catalog.model import ItemGroup
    from app.modules.user.model import User

    db.add(ItemGroup(code="TBIT", name="Thiết bị IT", is_active=True))
    db.commit()

    ctx = _ctx(db, db.get(User, seed.u_req_id), allowed=True, monkeypatch=monkeypatch)
    out = _run(ctx, {"purpose": "Trang bị màn hình", "lines": [
        {"requirement_detail": "Màn 27 inch", "request_qty": 2,
         "item_group": "thiết bị it"},                          # lệch hoa thường -> khớp
        {"requirement_detail": "Bàn phím", "request_qty": 1,
         "item_group": "Thiết bị văn phòng / IT"},              # bịa -> bỏ trống
    ]})
    assert out["status"] == "ready"
    lines = out["draft"]["lines"]
    assert lines[0]["item_group"] == "Thiết bị IT"
    assert lines[1]["item_group"] == ""
    assert out["invalid_item_groups"] == ["Thiết bị văn phòng / IT"]
    assert "Thiết bị IT" in out["item_groups"]
    assert "KHÔNG có trong danh mục" in out["reminder"]


def test_thieu_so_luong_thi_nhac_bo_sung(db, seed, monkeypatch):
    """Người dùng chưa nói số lượng thì qty=0 vẫn soạn được (YCBG khảo sát giá là hợp lệ),
    nhưng reminder phải dặn model nhắc bổ sung số lượng trên form."""
    from app.modules.user.model import User

    ctx = _ctx(db, db.get(User, seed.u_req_id), allowed=True, monkeypatch=monkeypatch)

    missing = _run(ctx, {"purpose": "Mua màn hình", "lines": [
        {"requirement_detail": "Màn 27 inch"},
    ]})
    assert missing["status"] == "ready"
    assert "chưa có số lượng" in missing["reminder"]

    du = _run(ctx, {"purpose": "Mua màn hình", "lines": [
        {"requirement_detail": "Màn 27 inch", "request_qty": 2},
    ]})
    assert "chưa có số lượng" not in du["reminder"]


def _them_cong_ty(db, code: str, name: str, short_name: str = ""):
    from app.modules.company.model import Company

    row = Company(code=code, name=name, short_name=short_name, is_active=True)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def test_cong_ty_khac_khop_danh_muc_thi_de_vao_nhap(db, seed, monkeypatch):
    """Người dùng nói mua cho pháp nhân KHÁC -> model điền `company`; khớp danh mục (không
    phân biệt hoa thường, nhận cả tên gọi tắt/mã) thì đè company_id vào bản nháp để form
    đổi khỏi công ty mặc định của người hỏi."""
    from app.modules.user.model import User

    cty = _them_cong_ty(db, "DGF", "Công ty TNHH DEGO Farm", short_name="DEGO Farm")
    ctx = _ctx(db, db.get(User, seed.u_req_id), allowed=True, monkeypatch=monkeypatch)

    out = _run(ctx, {"purpose": "Mua phân bón", "company": "dego farm", "lines": [
        {"requirement_detail": "Phân NPK", "request_qty": 100},
    ]})
    assert out["status"] == "ready"
    assert out["draft"]["company_id"] == cty.id
    assert out["draft"]["company_name"] == "Công ty TNHH DEGO Farm"
    assert "Công ty TNHH DEGO Farm" in out["reminder"]


def test_cong_ty_khong_khop_thi_giu_mac_dinh_va_tra_danh_sach(db, seed, monkeypatch):
    """Tên công ty lạ thì KHÔNG đè (form giữ công ty của người hỏi) + trả danh sách hợp lệ
    để model nêu cho người dùng chọn — cùng khuôn với phân loại ngoài danh mục."""
    from app.modules.user.model import User

    _them_cong_ty(db, "DGF", "Công ty TNHH DEGO Farm")
    ctx = _ctx(db, db.get(User, seed.u_req_id), allowed=True, monkeypatch=monkeypatch)

    out = _run(ctx, {"purpose": "Mua phân bón", "company": "Công ty lạ hoắc", "lines": [
        {"requirement_detail": "Phân NPK", "request_qty": 100},
    ]})
    assert out["status"] == "ready"
    assert "company_id" not in out["draft"]
    assert out["invalid_company"] == "Công ty lạ hoắc"
    assert "Công ty TNHH DEGO Farm" in out["companies"]
    assert "KHÔNG khớp danh mục" in out["reminder"]


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
    # qty=0 vẫn soạn được nhưng phải nhắc bổ sung số lượng (cùng luật với YCBG).
    assert "chưa có số lượng" in out["reminder"]


def test_ycmh_cong_ty_khac_cung_khop_theo_ma(db, seed, monkeypatch):
    """YCMH đi cùng đường `_apply_company` với YCBG — khớp được cả theo MÃ công ty."""
    from app.modules.user.model import User

    cty = _them_cong_ty(db, "DGF", "Công ty TNHH DEGO Farm")
    ctx = _ctx(db, db.get(User, seed.u_req_id), allowed=True, monkeypatch=monkeypatch)

    out = _run_purchase(ctx, {"purpose": "Mua giấy", "company": "dgf", "lines": [
        {"product": "Giấy A4", "qty": 5},
    ]})
    assert out["status"] == "ready"
    assert out["draft"]["company_id"] == cty.id
    assert out["draft"]["company_name"] == "Công ty TNHH DEGO Farm"

# ── draft_leave_request (ĐƠN nghỉ phép ở phân hệ Nhân sự) ───────────────────────────────
#
#  ⚠️ Bộ test này viết lại ngày 12/09/2026 (bao-CR-387). Bản cũ kiểm việc tool soạn một
#  *Giấy nghỉ phép* VĂN BẢN ở Văn thư (`DocType` mã GNP, gác `document.create`) — đúng thứ
#  gói tri thức `40-nghi-phep.md` cấm, vì giấy đó hệ TỰ SINH sau khi đơn được duyệt. Đừng
#  khôi phục các khẳng định `doc_type_id` / `draft["leave"]` của bản cũ.

def _them_loai_nghi(db, code="ANNUAL", name="Phép năm", counts_balance=True,
                    max_days_per_request=0.0, is_active=True):
    from app.modules.leave.catalog_model import LeaveType

    row = LeaveType(code=code, name=name, counts_balance=counts_balance,
                    max_days_per_request=max_days_per_request, is_active=is_active)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def test_leave_without_permission_is_denied(db, seed, monkeypatch):
    from app.modules.assistant.tools.draft_tool import _run_leave
    from app.modules.user.model import User

    _them_loai_nghi(db)
    ctx = _ctx(db, db.get(User, seed.u_req_id), allowed=False, monkeypatch=monkeypatch)
    out = _run_leave(ctx, {"from_date": "2026-09-01", "to_date": "2026-09-01",
                           "reason": "Việc gia đình"})
    assert out.get("denied") is True
    assert "total" not in out


def test_leave_without_leave_type_catalog_returns_soft_error(db, seed, monkeypatch):
    """Danh mục Loại nghỉ trống thì báo mềm, không nổ — và tuyệt đối không tự tạo loại."""
    from app.modules.assistant.tools.draft_tool import _run_leave
    from app.modules.user.model import User

    ctx = _ctx(db, db.get(User, seed.u_req_id), allowed=True, monkeypatch=monkeypatch)
    out = _run_leave(ctx, {"from_date": "2026-09-01", "to_date": "2026-09-01",
                           "reason": "Việc gia đình"})
    assert "error" in out
    assert "total" not in out


def test_leave_with_bad_dates_returns_soft_error(db, seed, monkeypatch):
    from app.modules.assistant.tools.draft_tool import _run_leave
    from app.modules.user.model import User

    _them_loai_nghi(db)
    ctx = _ctx(db, db.get(User, seed.u_req_id), allowed=True, monkeypatch=monkeypatch)

    assert "error" in _run_leave(ctx, {"from_date": "mai", "to_date": "2026-09-01",
                                       "reason": "x"})
    assert "error" in _run_leave(ctx, {"from_date": "2026-09-01", "to_date": "2026-09-01",
                                       "reason": ""})
    #  Đến ngày trước Từ ngày — phải hỏi lại chứ không lẳng lặng soạn đơn ngược.
    assert "error" in _run_leave(ctx, {"from_date": "2026-09-05", "to_date": "2026-09-01",
                                       "reason": "x"})
    #  Chiều -> sáng cùng ngày là khoảng trống (cùng luật `request_service.check_date_range`).
    assert "error" in _run_leave(ctx, {"from_date": "2026-09-01", "to_date": "2026-09-01",
                                       "from_session": "afternoon", "to_session": "morning",
                                       "reason": "x"})
    #  Model gõ nhầm năm -> khoảng nghỉ dài hơn một tờ đơn được phép, chặn ngay.
    assert "error" in _run_leave(ctx, {"from_date": "2026-09-01", "to_date": "2029-09-01",
                                       "reason": "x"})


def test_leave_draft_is_ready_with_full_payload(db, seed, monkeypatch):
    """Happy path: khớp loại nghỉ THẬT trong danh mục, số ngày tính bằng `workday_service`
    (không phải công thức riêng), và bản nháp mang hình dạng form đơn nghỉ phép."""
    from app.modules.assistant.tools.draft_tool import _run_leave
    from app.modules.leave.constants import SESSION_FULL
    from app.modules.user.model import User

    _them_loai_nghi(db)
    khong_luong = _them_loai_nghi(db, code="UNPAID", name="Nghỉ không lương",
                                  counts_balance=False)
    ctx = _ctx(db, db.get(User, seed.u_req_id), allowed=True, monkeypatch=monkeypatch)
    out = _run_leave(ctx, {"from_date": "2026-09-01", "to_date": "2026-09-03",
                           "reason": "Về quê có việc gia đình", "leave_type": "unpaid",
                           "contact_phone": "0900000001"})

    assert out["status"] == "ready"
    assert out["total"] == 1
    draft = out["draft"]
    assert draft["kind"] == "leave_request"
    #  ⚠️ CỐ Ý không có `employee_id`: form mặc định người nghỉ là chính người lập đơn.
    #  Có khóa đó là mở đường nộp đơn HỘ người khác qua chat.
    assert "employee_id" not in draft
    assert draft["lines"] == [{"leave_type_id": khong_luong.id,
                               "leave_type": "Nghỉ không lương", "days": 3}]
    assert draft["from_session"] == SESSION_FULL and draft["to_session"] == SESSION_FULL
    assert draft["from_time"] == "" and draft["to_time"] == ""
    assert draft["reason"] == "Về quê có việc gia đình"
    assert draft["contact_phone"] == "0900000001"
    #  Loại không trừ quỹ thì không đi hỏi số ngày còn lại.
    assert out["remaining_days"] is None
    assert out["warnings"] == []
    assert "CHƯA được tạo" in out["reminder"]


def test_leave_falls_back_to_balance_type_for_unknown_code(db, seed, monkeypatch):
    """Model gõ loại nghỉ ngoài danh mục / buổi bậy thì về mặc định chứ không nổ lỗi —
    các ô này trên form là ô chọn, người dùng rà lại được. Nửa ngày tính 0.5 công."""
    from app.modules.assistant.tools.draft_tool import _run_leave
    from app.modules.leave.constants import SESSION_FULL
    from app.modules.user.model import User

    phep_nam = _them_loai_nghi(db)
    _them_loai_nghi(db, code="UNPAID", name="Nghỉ không lương", counts_balance=False)
    ctx = _ctx(db, db.get(User, seed.u_req_id), allowed=True, monkeypatch=monkeypatch)

    out = _run_leave(ctx, {"from_date": "2026-09-01", "to_date": "2026-09-01",
                           "leave_type": "vacation", "from_session": "sáng",
                           "reason": "Khám bệnh"})
    #  Lùi về loại TRỪ QUỸ (phép năm), không lùi về dòng đầu danh mục cho xong chuyện.
    assert out["draft"]["lines"][0]["leave_type_id"] == phep_nam.id
    assert out["draft"]["from_session"] == SESSION_FULL

    nua_ngay = _run_leave(ctx, {"from_date": "2026-09-01", "to_date": "2026-09-01",
                                "from_session": "morning", "to_session": "morning",
                                "reason": "Khám bệnh"})
    assert nua_ngay["draft"]["lines"][0]["days"] == 0.5


def test_leave_matches_type_by_name_too(db, seed, monkeypatch):
    """Người dùng nói "nghỉ không lương" nên model hay điền TÊN thay vì mã."""
    from app.modules.assistant.tools.draft_tool import _run_leave
    from app.modules.user.model import User

    _them_loai_nghi(db)
    khong_luong = _them_loai_nghi(db, code="UNPAID", name="Nghỉ không lương",
                                  counts_balance=False)
    ctx = _ctx(db, db.get(User, seed.u_req_id), allowed=True, monkeypatch=monkeypatch)
    out = _run_leave(ctx, {"from_date": "2026-09-01", "to_date": "2026-09-01",
                           "leave_type": "Nghỉ KHÔNG lương", "reason": "x"})
    assert out["draft"]["lines"][0]["leave_type_id"] == khong_luong.id


def test_leave_hourly_requires_both_times(db, seed, monkeypatch):
    from app.modules.assistant.tools.draft_tool import _run_leave
    from app.modules.leave.constants import SESSION_HOURLY
    from app.modules.user.model import User

    _them_loai_nghi(db)
    ctx = _ctx(db, db.get(User, seed.u_req_id), allowed=True, monkeypatch=monkeypatch)

    assert "error" in _run_leave(ctx, {"from_date": "2026-09-01", "to_date": "2026-09-01",
                                       "from_session": "hourly", "to_session": "hourly",
                                       "reason": "Khám bệnh"})
    out = _run_leave(ctx, {"from_date": "2026-09-01", "to_date": "2026-09-01",
                           "from_session": "hourly", "to_session": "full",
                           "from_time": "08:00", "to_time": "10:00", "reason": "Khám bệnh"})
    #  Khai theo giờ thì CẢ HAI ô buổi phải là «Theo giờ», nếu không backend chặn lúc lưu.
    assert out["draft"]["from_session"] == SESSION_HOURLY
    assert out["draft"]["to_session"] == SESSION_HOURLY
    assert out["draft"]["from_time"] == "08:00" and out["draft"]["to_time"] == "10:00"


def test_leave_warns_on_overlap_and_short_balance(db, seed, monkeypatch):
    """Hai chốt backend sẽ CHẶN lúc lưu — nói trước ở đây để người dùng khỏi điền xong
    form mới ăn câu chặn. Chỉ cảnh báo, KHÔNG tự sửa: quyết định là của họ."""
    from datetime import date

    from app.modules.assistant.tools.draft_tool import _run_leave
    from app.modules.leave.constants import LR_PENDING
    from app.modules.leave.request_model import LeaveRequest
    from app.modules.user.model import User

    phep_nam = _them_loai_nghi(db)
    db.add(LeaveRequest(code="NP-2026-0009", company_id=seed.company_id,
                        department_id=seed.dept_id, employee_id=seed.emp_req_id,
                        leave_type_id=phep_nam.id, from_date=date(2026, 9, 2),
                        to_date=date(2026, 9, 2), total_days=1, status=LR_PENDING,
                        reason="Đơn cũ", created_by=seed.u_req_id))
    db.commit()

    ctx = _ctx(db, db.get(User, seed.u_req_id), allowed=True, monkeypatch=monkeypatch)
    out = _run_leave(ctx, {"from_date": "2026-09-01", "to_date": "2026-09-03",
                           "reason": "Về quê"})

    assert out["status"] == "ready"          # cảnh báo KHÔNG chặn soạn nháp
    assert out["remaining_days"] == 0.0      # chưa ai cấp quỹ năm 2026
    assert any("NP-2026-0009" in w for w in out["warnings"])
    assert any("CHƯA được cấp" in w for w in out["warnings"])


def test_leave_warns_when_over_max_days_per_request(db, seed, monkeypatch):
    from app.modules.assistant.tools.draft_tool import _run_leave
    from app.modules.user.model import User

    _them_loai_nghi(db, code="WEDDING", name="Nghỉ cưới", counts_balance=False,
                    max_days_per_request=3)
    ctx = _ctx(db, db.get(User, seed.u_req_id), allowed=True, monkeypatch=monkeypatch)
    out = _run_leave(ctx, {"from_date": "2026-09-01", "to_date": "2026-09-07",
                           "leave_type": "wedding", "reason": "Cưới"})
    assert any("tối đa 3.0 ngày" in w for w in out["warnings"])


def test_leave_without_employee_profile_returns_soft_error(db, seed, monkeypatch):
    """Tài khoản chưa gắn hồ sơ nhân sự thì không nộp đơn được — báo mềm, đừng soạn một
    tờ đơn họ không lưu nổi."""
    from app.modules.assistant.tools.draft_tool import _run_leave
    from app.modules.user.model import User

    _them_loai_nghi(db)
    user = db.get(User, seed.u_req_id)
    user.employee_id = 0
    db.commit()
    ctx = _ctx(db, user, allowed=True, monkeypatch=monkeypatch)
    out = _run_leave(ctx, {"from_date": "2026-09-01", "to_date": "2026-09-01",
                           "reason": "Việc gia đình"})
    assert "error" in out
    assert "total" not in out


# ── tool_defs(db): gắn enum danh mục thật vào khai báo tool ─────────────────────────────

def test_tool_defs_gan_enum_danh_muc_that(db, seed):
    """Có db thì khai báo 3 tool soạn nháp mang enum danh mục THẬT (phân loại + công ty +
    loại nghỉ) để model thấy trước danh sách hợp lệ thay vì bịa; không db giữ khai báo
    tĩnh. Enum tuyệt đối không được rò vào dict `_PARAMS` dùng chung (deepcopy) — rò là
    mọi request sau dính danh mục của request trước."""
    from app.modules.assistant import tools as tool_layer
    from app.modules.assistant.tools.draft_tool import (_LEAVE_PARAMS, _PARAMS,
                                                        _PR_PARAMS)

    _them_cong_ty(db, "DGF", "Công ty TNHH DEGO Farm")
    _them_loai_nghi(db)
    _them_loai_nghi(db, code="UNPAID", name="Nghỉ không lương", counts_balance=False)

    defs = {d.name: d for d in tool_layer.tool_defs(db)}
    ycbg = defs["draft_survey_request"].parameters
    assert "Công ty TNHH DEGO Farm" in ycbg["properties"]["company"]["enum"]
    #  Seed đã có sẵn 2 phân loại "Nhãn"/"Thùng" — enum phải mang danh mục của môi trường.
    assert "Nhãn" in ycbg["properties"]["lines"]["items"]["properties"]["item_group"]["enum"]
    ycmh = defs["draft_purchase_request"].parameters
    assert "Công ty TNHH DEGO Farm" in ycmh["properties"]["company"]["enum"]
    #  Dòng YCMH không có ô item_group (phân loại lấy theo danh mục sản phẩm) — không gắn.
    assert "item_group" not in ycmh["properties"]["lines"]["items"]["properties"]
    #  Loại nghỉ gắn bằng MÃ, và TÊN đi kèm trong mô tả để model biết mã nào là gì.
    nghi_phep = defs["draft_leave_request"].parameters["properties"]["leave_type"]
    assert nghi_phep["enum"] == ["ANNUAL", "UNPAID"]
    assert "Nghỉ không lương" in nghi_phep["description"]

    tinh = {d.name: d for d in tool_layer.tool_defs()}
    assert "enum" not in tinh["draft_survey_request"].parameters["properties"]["company"]
    assert "enum" not in tinh["draft_leave_request"].parameters["properties"]["leave_type"]
    assert "enum" not in _PARAMS["properties"]["company"]
    assert "enum" not in _PR_PARAMS["properties"]["company"]
    assert "enum" not in _LEAVE_PARAMS["properties"]["leave_type"]
