"""TRƯỜNG RIÊNG CỦA TỪNG HỒ SƠ — `tab_dossier.custom_fields` (17/09/2026).

Người lập hồ sơ khai thêm ô ngay tại chỗ (tên · kiểu · bắt buộc · giá trị) mà
không đụng vào khuôn của loại.

⚠️ **HAI NGUỒN KHAI, MỘT KHO GIÁ TRỊ.** Khai báo nằm ở hai chỗ —
`tab_dossier_type.field_schema` (dùng chung mọi hồ sơ cùng loại) và
`tab_dossier.custom_fields` (riêng tờ này) — nhưng giá trị thì cùng đổ vào
`tab_dossier.extra_fields`. Đó là chỗ dễ thủng nhất của cả tính năng:

  * trùng khóa giữa hai nguồn = hai ô cùng ghi một chỗ, biểu mẫu hiện đủ hai mà
    chỉ một giá trị sống sót — im lặng tuyệt đối;
  * `PATCH` không gửi `custom_fields` mà lấy danh sách rỗng = mọi ô riêng bỗng
    thành «không còn khai báo», mất luôn chốt bắt buộc của chúng.

Bộ kiểm giá trị (`field_values.py`) đã có tệp riêng; ở đây chỉ soi phần GỘP.
"""
import pytest
from fastapi import HTTPException

from app.modules.dossier import service
from app.modules.dossier.model import Dossier
from app.modules.dossier.schema import DossierCreate, DossierUpdate
from app.modules.dossier.type_model import DossierType


def _def(key, label, **over):
    return {"key": key, "label": label, "type": "text", "required": False,
            "options": [], "hint": "", **over}


@pytest.fixture
def loai(db):
    """Loại hồ sơ khai sẵn hai ô dùng chung."""
    row = DossierType(code="PLGP", name="Pháp lý & Giấy phép", field_schema=[
        _def("so_giay_phep", "Số giấy phép", required=True),
        _def("co_quan_cap", "Cơ quan cấp"),
    ])
    db.add(row)
    db.flush()
    return row


# ── Khai báo ────────────────────────────────────────────────────────────────
def test_khai_truong_rieng_qua_schema(db):
    """Cùng luật kiểm với bộ trường của loại — dùng lại `validate_field_schema`."""
    data = DossierCreate(name="x", dossier_type_id=1,
                         custom_fields=[_def("So QD", "Số quyết định")])
    #  Mã được chuẩn hoá y như bên loại: chữ thường, gạch dưới.
    assert data.custom_fields[0]["key"] == "so_qd"

    with pytest.raises(Exception):
        DossierCreate(name="x", dossier_type_id=1,
                      custom_fields=[_def("số_qđ", "Số quyết định")])


def test_khong_khai_gi_van_hop_le(db):
    """Phần lớn hồ sơ chỉ dùng ô của loại — ép khai là ép bịa ra ô."""
    assert DossierCreate(name="x", dossier_type_id=1).custom_fields == []
    assert DossierUpdate().custom_fields is None


# ── Gộp hai nguồn ───────────────────────────────────────────────────────────
def test_gia_tri_cua_CA_HAI_nguon_deu_duoc_kiem(db, loai):
    """Ô của loại và trường riêng cùng đi qua một bộ kiểm.

    Thiếu vế sau thì trường riêng khai `type: number` mà nhận chữ vẫn lọt xuống
    DB — khai kiểu để đó cho vui.
    """
    values = {
        "dossier_type_id": loai.id,
        "custom_fields": [_def("gia_tri", "Giá trị", type="number")],
        "extra_fields": {"so_giay_phep": "GP-01", "gia_tri": "không phải số"},
    }
    with pytest.raises(HTTPException, match="Giá trị"):
        service.apply_extra_fields(db, values)


def test_o_bat_buoc_cua_TRUONG_RIENG_cung_bi_doi(db, loai):
    values = {
        "dossier_type_id": loai.id,
        "custom_fields": [_def("so_qd", "Số quyết định", required=True)],
        "extra_fields": {"so_giay_phep": "GP-01", "so_qd": ""},
    }
    with pytest.raises(HTTPException) as exc:
        service.apply_extra_fields(db, values)
    #  ⚠️ Câu chặn KHÔNG được nói «của loại hồ sơ này» — trường này là của tờ hồ
    #  sơ, nói sai nguồn thì người dùng đi mở màn Loại hồ sơ tìm một ô không có ở đó.
    assert "loại hồ sơ" not in str(exc.value.detail)
    assert "Số quyết định" in str(exc.value.detail)


def test_TRUNG_KHOA_voi_o_cua_loai_bi_chan(db, loai):
    """⚠️ Bài kiểm CỐT LÕI — ca hỏng im lặng nhất của cả tính năng.

    Hai nguồn khai cùng đổ vào `extra_fields`, nên trùng khóa là hai ô cùng ghi
    một chỗ: biểu mẫu hiện đủ hai, người dùng gõ hai giá trị khác nhau, và chỉ
    một cái sống sót. Không lỗi, không cảnh báo, không cách nào biết.
    """
    values = {
        "dossier_type_id": loai.id,
        "custom_fields": [_def("so_giay_phep", "Số GP riêng")],
        "extra_fields": {"so_giay_phep": "GP-01"},
    }
    with pytest.raises(HTTPException, match="so_giay_phep"):
        service.apply_extra_fields(db, values)


def test_chot_trung_khoa_chay_ca_khi_KHONG_gui_gia_tri(db, loai):
    """Gửi riêng `custom_fields` là đường lách hiển nhiên — phải bịt.

    Chốt trùng khóa nằm sau nhánh «không gửi gì thì thôi»; đặt nhánh đó chặn cả
    `custom_fields` là khai được một trường riêng trùng tên ô của loại mà không
    ai kiểm, rồi lần lưu sau mới lộ ra.
    """
    values = {"dossier_type_id": loai.id,
              "custom_fields": [_def("co_quan_cap", "Cơ quan")]}
    with pytest.raises(HTTPException, match="co_quan_cap"):
        service.apply_extra_fields(db, values)


def test_PATCH_khong_gui_khai_bao_thi_lay_cua_ban_ghi_cu(db, loai):
    """⚠️ Không lấy danh sách rỗng khi payload không nhắc tới `custom_fields`.

    Lấy rỗng thì một `PATCH` đổi mỗi ghi chú cũng làm mọi trường riêng thành
    «không còn khai báo» — mất chốt bắt buộc, và giá trị của chúng rơi xuống
    nhánh khoan dung dành cho khóa mồ côi.
    """
    cur = Dossier(code="HS1", name="x", dossier_type_id=loai.id,
                  custom_fields=[_def("so_qd", "Số quyết định", required=True)])
    db.add(cur)
    db.flush()

    #  Chỉ gửi giá trị, bỏ trống ô bắt buộc riêng -> vẫn phải chặn.
    values = {"extra_fields": {"so_giay_phep": "GP-01", "so_qd": ""}}
    with pytest.raises(HTTPException, match="Số quyết định"):
        service.apply_extra_fields(db, values, cur)


def test_doi_LOAI_thi_o_cua_loai_cu_thanh_khoa_mo_coi(db, loai):
    """Đổi loại thì ô của loại cũ không còn ai khai — giữ giá trị, không ném lỗi.

    Đây là nhánh khoan dung đã có ở `field_values.py`; bài này chốt rằng việc
    gộp thêm `custom_fields` không phá nó.
    """
    khac = DossierType(code="DHHD", name="Đặt hàng", field_schema=[_def("so_hd", "Số HĐ")])
    db.add(khac)
    db.flush()

    values = {
        "dossier_type_id": khac.id,
        "custom_fields": [],
        "extra_fields": {"so_hd": "HD-01", "so_giay_phep": "giá trị của loại cũ"},
    }
    service.apply_extra_fields(db, values)
    assert values["extra_fields"]["so_giay_phep"] == "giá trị của loại cũ"


# ── Ghi xuống DB ────────────────────────────────────────────────────────────
def test_cot_NULL_doc_ra_danh_sach_rong(db, loai):
    """Hồ sơ lập trước khi có cột này mang `NULL` — không để `None` ra tới API."""
    from app.modules.dossier.schema import DossierResponse

    row = Dossier(code="HS1", name="x", dossier_type_id=loai.id)
    db.add(row)
    db.flush()

    assert row.custom_fields is None
    assert row.custom_field_defs == []
    assert DossierResponse.model_validate(row).custom_fields == []
