"""CẢNH BÁO KHI HAI LUỒNG MẶC ĐỊNH CÙNG BẬT (19/08/2026).

Ca thật bắt được lúc chạy thử luồng văn thư: hai luồng `document` cùng đang bật
và cùng KHÔNG khai điều kiện — «Ban hành văn bản hành chính» (bước 1 có người dự
phòng) và «Ban hành văn bản (mặc định)» (bước 1 chặn cứng). `chon_luong` lấy
đúng một cái, cái còn lại nằm im vĩnh viễn mà không có gì báo. Hệ quả: văn bản
thiếu người duyệt thì phiếu KẸT, trong khi người khai đinh ninh nó rơi về người
dự phòng như luồng kia khai.

Hệ không cấm khai hai luồng mặc định — có lúc người ta đang dựng dần luồng mới.
Nhưng phải NÓI RA, ngay trên dòng danh sách và ngay lúc bấm lưu.
"""
from app.modules.approval import flow_service
from app.modules.approval.flow_model import ApprovalFlow

ACTOR = 1


def _luong(db, name: str, *, condition: str = "", is_active: bool = True,
           priority: int = 0, company_id=None, entity: str = "document") -> ApprovalFlow:
    flow = ApprovalFlow(entity=entity, code=name[:20], name=name, condition=condition,
                        is_active=is_active, priority=priority, company_id=company_id,
                        created_by=ACTOR, updated_by=ACTOR)
    db.add(flow)
    db.commit()
    db.refresh(flow)
    return flow


def test_mot_luong_mac_dinh_thi_khong_canh_bao_gi(db):
    flow = _luong(db, "Ban hành văn bản")

    assert flow_service.default_overlap_warning(db, flow) == ""


def test_hai_luong_mac_dinh_cung_bat_thi_goi_ten_ca_hai(db):
    thang = _luong(db, "Ban hành văn bản (mặc định)", priority=5)
    bi_che = _luong(db, "Ban hành văn bản hành chính", priority=1)

    warning = flow_service.default_overlap_warning(db, bi_che)

    assert "Ban hành văn bản (mặc định)" in warning
    assert "Ban hành văn bản hành chính" in warning
    #  Phải nói rõ CÁI NÀO chạy, không chỉ "có trùng".
    assert f"chỉ «{thang.name}» chạy" in warning
    #  Cái đang thắng cũng thấy cảnh báo — người mở luồng nào cũng phải biết.
    assert flow_service.default_overlap_warning(db, thang) != ""


def test_luong_co_dieu_kien_khong_tinh_la_trung(db):
    _luong(db, "Ban hành văn bản (mặc định)")
    co_dieu_kien = _luong(db, "Văn bản mật", condition='{"secrecy_level": 3}')

    assert flow_service.default_overlap_warning(db, co_dieu_kien) == ""


def test_luong_da_tat_khong_tinh_la_trung(db):
    _luong(db, "Ban hành văn bản (mặc định)", is_active=False)
    is_enabled = _luong(db, "Ban hành văn bản hành chính")

    assert flow_service.default_overlap_warning(db, is_enabled) == ""


def test_khac_loai_chung_tu_thi_khong_dinh_gi_den_nhau(db):
    _luong(db, "Duyệt YCMH", entity="purchase_request")
    van_ban = _luong(db, "Ban hành văn bản")

    assert flow_service.default_overlap_warning(db, van_ban) == ""


def test_hai_luong_khai_cho_hai_phap_nhan_khac_nhau_thi_khong_trung(db):
    """Luồng khai riêng cho một pháp nhân chỉ va nhau khi CÙNG pháp nhân."""
    _luong(db, "Ban hành — Công ty A", company_id=1)
    cong_ty_b = _luong(db, "Ban hành — Công ty B", company_id=2)

    assert flow_service.default_overlap_warning(db, cong_ty_b) == ""


def test_luong_toan_he_khong_che_luong_rieng_cua_phap_nhan(db):
    """Luồng riêng luôn được xét trước; luồng toàn hệ chỉ là đường lùi."""
    _luong(db, "Ban hành toàn hệ")
    specific = _luong(db, "Ban hành — Công ty A", company_id=1)

    assert flow_service.default_overlap_warning(db, specific) == ""


def test_hai_luong_mac_dinh_cung_phap_nhan_van_canh_bao(db):
    _luong(db, "Ban hành A — cũ", company_id=1, priority=5)
    new = _luong(db, "Ban hành A — mới", company_id=1, priority=1)

    assert flow_service.default_overlap_warning(db, new) != ""
