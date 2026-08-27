"""Danh mục MỨC MẬT / ĐỘ KHẨN — thêm sửa xóa được (22/08/2026).

Trọng tâm là CHỐT CHẶN LÚC XÓA. Bảng này không có khóa ngoại nào trỏ vào
(`tab_document.secrecy_level` chỉ là số trần), nên nếu chốt chặn hỏng thì không
còn lớp nào đỡ: xóa xong là văn bản mang một con số không tra ra tên, và tệ hơn
— luồng duyệt khai "mức ≥ 3 thì thêm bước Giám đốc ký" lặng lẽ thôi khớp.
"""
import json

import pytest
from fastapi import HTTPException

from app.modules.approval.flow_model import ApprovalFlow, ApprovalNode
from app.modules.doc_catalog.model import DocType
from app.modules.doc_catalog.security_level_guard import (before_create,
                                                          before_delete)
from app.modules.doc_catalog.security_level_model import (KIND_CONFIDENTIAL,
                                                          KIND_URGENCY,
                                                          SecurityLevel)
from app.modules.doc_catalog.security_level_service import (ensure_valid, label,
                                                            label_maps,
                                                            value_of_code)
from app.modules.document.model import Document


#  ⚠️ `conftest._nap_muc_mat` đã nạp sẵn BẢY bậc gốc cho mọi test — giống hệt
#  chạy thật. Nên ở đây TRA RA dùng lại chứ không tạo mới: tạo lại là đụng ràng
#  buộc duy nhất trên `code`, mà quan trọng hơn — test sẽ chạy trên một danh mục
#  không giống thứ người dùng thật đang có.
def _pay(db, code) -> SecurityLevel:
    return db.query(SecurityLevel).filter(SecurityLevel.code == code).one()


def _bac_moi(db, kind, value, code, name="Bậc thử"):
    row = SecurityLevel(kind=kind, value=value, code=code, name=name,
                        description="", is_active=True, created_by=1, updated_by=1)
    db.add(row)
    db.flush()
    return row


@pytest.fixture
def confidential(db):
    """Mức Mật (bậc 3) — bậc dùng để thử mọi chốt chặn."""
    return _pay(db, "MAT")


def _van_ban(db, **kw):
    doc = Document(doc_type_id=1, company_id=1, title="Thử", owner_employee_id=1,
                   created_by=1, updated_by=1, **kw)
    db.add(doc)
    db.flush()
    return doc


# ── Thêm ──────────────────────────────────────────────────────────────────────
def test_mot_thang_khong_duoc_co_hai_bac_trung_so(db, confidential):
    """Trùng số trong cùng thang thì `secrecy_level = 3` đọc ra hai mức khác nhau
    tùy ai tra — chính là thứ danh mục sinh ra để tránh."""
    with pytest.raises(HTTPException) as e:
        before_create(db, SecurityLevel(kind=KIND_CONFIDENTIAL, value=3, code="MAT2",
                                        name="Mật cấp 2"))
    assert "đã có bậc số 3" in e.value.detail


def test_hai_thang_khac_nhau_dung_chung_so_thi_khong_sao(db):
    """Công khai và Thường cùng là bậc 1 — đây là lý do khóa duy nhất phải là
    cặp `(kind, value)` chứ không phải riêng `value`.

    Mức mật đã có bậc 4 (Tuyệt mật), độ khẩn thì chưa — thêm bậc 4 cho độ khẩn
    phải chạy. Khóa duy nhất đặt nhầm lên riêng `value` là ca này đỏ."""
    before_create(db, SecurityLevel(kind=KIND_URGENCY, value=4, code="SIEUTOC",
                                    name="Siêu tốc"))


# ── Xóa ───────────────────────────────────────────────────────────────────────
def test_con_van_ban_dang_o_bac_do_thi_khong_xoa_duoc(db, confidential):
    _van_ban(db, secrecy_level=3)

    with pytest.raises(HTTPException) as e:
        before_delete(db, confidential)
    assert "1 văn bản" in e.value.detail


def test_do_khan_dem_dung_cot_urgency_chu_khong_phai_secrecy(db):
    """Bẫy dễ dính: hai thang chung một hàm đếm. Đếm nhầm cột thì bậc Khẩn tưởng
    như không ai dùng và xóa được ngay, trong khi văn bản đang mang nó."""
    urgency = _pay(db, "KHAN")
    _van_ban(db, secrecy_level=2, urgency=2)

    with pytest.raises(HTTPException) as e:
        before_delete(db, urgency)
    assert "1 văn bản" in e.value.detail


def test_loai_van_ban_dang_lay_lam_mac_dinh_thi_khong_xoa_duoc(db, confidential):
    db.add(DocType(code="QC", name="Quy chế", default_secrecy=3,
                   created_by=1, updated_by=1))
    db.flush()

    with pytest.raises(HTTPException) as e:
        before_delete(db, confidential)
    assert "mức mật mặc định" in e.value.detail


def test_khong_con_ai_dung_thi_xoa_duoc(db, confidential):
    _van_ban(db, secrecy_level=2)          # văn bản ở bậc KHÁC
    before_delete(db, confidential)                  # không ném gì cả


# ── Xóa: điều kiện luồng duyệt (chỗ nguy hiểm nhất) ───────────────────────────
def _luong(db, condition, name="Luồng ban hành"):
    row = ApprovalFlow(name=name, entity="document", condition=json.dumps(condition),
                       created_by=1, updated_by=1)
    db.add(row)
    db.flush()
    return row


def test_luong_duyet_dang_tro_toi_thi_khong_xoa_duoc(db, confidential):
    """Đây là ca không có lớp nào khác đỡ: điều kiện lưu dạng CHUỖI JSON, không
    khóa ngoại, không truy vấn ngược được. Xóa xong luồng không báo lỗi — nó chỉ
    thôi khớp, và văn bản mật từ đó đi thẳng qua không cần ai ký."""
    _luong(db, {"field": "secrecy_level", "op": "gte", "value": 3})

    with pytest.raises(HTTPException) as e:
        before_delete(db, confidential)
    assert "điều kiện phê duyệt" in e.value.detail
    assert "Luồng ban hành" in e.value.detail


def test_bat_duoc_ca_dieu_kien_long_nhieu_tang(db, confidential):
    _luong(db, {"all": [{"field": "doc_type_id", "op": "eq", "value": 5},
                        {"any": [{"field": "secrecy_level", "op": "eq", "value": 3}]}]})

    with pytest.raises(HTTPException):
        before_delete(db, confidential)


def test_bat_duoc_khi_so_nam_trong_danh_sach_cua_phep_in(db, confidential):
    _luong(db, {"field": "secrecy_level", "op": "in", "value": [3, 4]})

    with pytest.raises(HTTPException):
        before_delete(db, confidential)


def test_khong_bat_nham_bac_khac_cung_thang(db, confidential):
    """Luồng trỏ bậc 4; xóa bậc 3 phải chạy. Nếu so bằng chuỗi thô kiểu
    `LIKE '%3%'` thì ca này đỏ."""
    _luong(db, {"field": "secrecy_level", "op": "gte", "value": 4})

    before_delete(db, confidential)


def test_khong_bat_nham_so_dai_hon_chua_chu_so_do(db, confidential):
    """`value: 30` KHÔNG phải là bậc 3. Đây là lý do phải đọc JSON chứ không
    dò chuỗi."""
    _luong(db, {"field": "secrecy_level", "op": "gte", "value": 30})

    before_delete(db, confidential)


def test_khong_bat_nham_truong_khac_cung_con_so(db, confidential):
    """Luồng lọc theo `urgency = 3` (Hỏa tốc), không liên quan mức mật bậc 3."""
    _luong(db, {"field": "urgency", "op": "eq", "value": 3})

    before_delete(db, confidential)


def test_bat_ca_dieu_kien_khai_o_tung_nut_khong_chi_o_luong(db, confidential):
    """Điều kiện rẽ nhánh hay nằm ở NÚT chứ không ở luồng — bỏ sót bảng này là
    chốt chặn thủng một nửa."""
    flow = _luong(db, {"field": "doc_type_id", "op": "eq", "value": 1})
    db.add(ApprovalNode(flow_id=flow.id, name="Giám đốc ký", seq=2,
                        condition=json.dumps({"field": "secrecy_level", "op": "gte",
                                              "value": 3}),
                        created_by=1, updated_by=1))
    db.flush()

    with pytest.raises(HTTPException) as e:
        before_delete(db, confidential)
    assert "Giám đốc ký" in e.value.detail


# ── Kiểm giá trị khi lưu văn bản ──────────────────────────────────────────────
def test_bac_moi_them_vao_danh_muc_thi_luu_van_ban_duoc_ngay(db):
    """Chính là điều `ge=1, le=4` cũ chặn mất: thêm bậc 5 vào danh mục xong vẫn
    không lưu nổi văn bản mang bậc đó."""
    _bac_moi(db, KIND_CONFIDENTIAL, 5, "TOIMAT", "Tối mật")

    ensure_valid(db, KIND_CONFIDENTIAL, 5)


def test_bac_khong_co_trong_danh_muc_thi_bi_tu_choi(db, confidential):
    with pytest.raises(HTTPException) as e:
        ensure_valid(db, KIND_CONFIDENTIAL, 9)
    assert "không có bậc 9" in e.value.detail


def test_bac_da_ngung_dung_thi_khong_chon_moi_duoc(db, confidential):
    confidential.is_active = False
    db.flush()

    with pytest.raises(HTTPException):
        ensure_valid(db, KIND_CONFIDENTIAL, 3)


def test_bo_trong_thi_khong_kiem_gi(db):
    """Bỏ trống là "để service lấy mặc định của loại văn bản", không phải lỗi."""
    ensure_valid(db, KIND_CONFIDENTIAL, None)


# ── Nhãn cho Excel ────────────────────────────────────────────────────────────
def test_doi_ten_bac_thi_file_excel_in_theo_ten_moi(db, confidential):
    """Trước đây `export.py` giữ bản chép riêng của bảy cái nhãn, nên đổi tên
    trên màn hình xong file Excel vẫn in chữ cũ."""
    confidential.name = "Mật — hạn chế"
    db.flush()

    security_labels, _ = label_maps(db)
    assert label(security_labels, 3) == "Mật — hạn chế"


def test_bac_da_ngung_dung_van_tra_ra_ten(db, confidential):
    """Văn bản cũ vẫn mang con số đó. Lọc `is_active` lúc tra nhãn là bản in cũ
    tự dưng mất chữ."""
    confidential.is_active = False
    db.flush()

    security_labels, _ = label_maps(db)
    assert label(security_labels, 3) == "Mật"


def test_so_la_thi_in_ra_chinh_con_so(db, confidential):
    security_labels, _ = label_maps(db)
    assert label(security_labels, 9) == "9"


def test_tra_bac_theo_ma_chu_khong_theo_so(db, confidential):
    """`is_confidential_type` kéo mức lên "ít nhất Mật" — bám vào mã `MAT`, nên
    đổi tên hiển thị không ảnh hưởng."""
    confidential.name = "Mật — hạn chế"
    db.flush()

    assert value_of_code(db, "MAT") == 3


def test_khong_co_ma_do_thi_tra_mac_dinh(db):
    """Nơi triển khai không có bậc mang mã đó thì bỏ sàn, không dựng đứng luồng
    tạo văn bản."""
    assert value_of_code(db, "KHONG_CO_MA_NAY") == 1
