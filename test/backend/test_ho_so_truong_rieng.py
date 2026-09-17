"""TRƯỜNG RIÊNG CỦA TỪNG HỒ SƠ — `tab_dossier.custom_fields` (17/09/2026).

Người lập hồ sơ khai thêm ô ngay tại chỗ (tên · kiểu · bắt buộc · giá trị) mà
không đụng vào khuôn của loại.

⚠️ **MỘT NGUỒN KHAI DUY NHẤT: `tab_dossier.custom_fields`.** Bộ trường của LOẠI
(`tab_dossier_type.field_schema`) tụt xuống thành **KHUÔN** (17/09/2026) — màn
lập hồ sơ đổ nó vào bảng trường riêng khi chọn loại, rồi người lập sửa/xóa tự
do. Giữ cả hai như trước thì mọi dòng vừa đổ ra đều trùng khóa với chính cái
khuôn đẻ ra nó, và không hồ sơ nào lưu nổi.

Chỗ dễ thủng còn lại: **`PATCH` không gửi `custom_fields`** mà lấy danh sách
rỗng = mọi ô riêng bỗng thành «không còn khai báo», mất luôn chốt bắt buộc.

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
def test_kieu_cua_truong_rieng_duoc_kiem_that(db, loai):
    """Khai `type: number` mà nhận chữ thì phải chặn — không thì khai kiểu cho vui."""
    values = {
        "dossier_type_id": loai.id,
        "custom_fields": [_def("gia_tri", "Giá trị", type="number")],
        "extra_fields": {"gia_tri": "không phải số"},
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


def test_bo_truong_cua_LOAI_khong_con_tu_ap_cho_ho_so(db, loai):
    """⚠️ Luật đổi 17/09/2026 — loại tụt xuống thành **KHUÔN**, không còn là luật.

    Trước đó `apply_extra_fields` gộp `field_schema` của loại với
    `custom_fields` của hồ sơ. Nay màn lập hồ sơ ĐỔ khuôn vào chính bảng trường
    riêng, nên giữ cả hai nguồn là mọi dòng vừa đổ ra đều trùng khóa với chính
    cái khuôn đẻ ra nó — và không hồ sơ nào lưu nổi.

    Hệ quả phải biết: ô `required` khai ở LOẠI **không tự áp** cho hồ sơ nữa. Nó
    chỉ có hiệu lực nếu dòng tương ứng còn nằm trong `custom_fields` của tờ đó,
    tức đúng như người lập đã chốt trên màn hình. Muốn ép cứng cả công ty thì
    phải là một CỘT THẬT.
    """
    #  Loại khai `so_giay_phep` BẮT BUỘC, nhưng hồ sơ không khai dòng nào.
    values = {"dossier_type_id": loai.id, "custom_fields": [], "extra_fields": {}}
    service.apply_extra_fields(db, values)      # không ném
    assert values["extra_fields"] == {}


def test_khoa_trung_ten_o_cua_loai_KHONG_con_bi_chan(db, loai):
    """Không còn hai nguồn thì không có gì để mà trùng.

    Chốt cũ («Trường riêng trùng tên với ô sẵn có của loại») đã gỡ — giữ lại là
    chặn đúng cái việc mà khuôn sinh ra để làm.
    """
    values = {
        "dossier_type_id": loai.id,
        "custom_fields": [_def("so_giay_phep", "Số giấy phép", required=True)],
        "extra_fields": {"so_giay_phep": "GP-01"},
    }
    service.apply_extra_fields(db, values)      # không ném
    assert values["extra_fields"] == {"so_giay_phep": "GP-01"}


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


# ── Ô «Chọn từ danh mục» (`reference`) ──────────────────────────────────────
def test_reference_phai_khai_danh_muc(db):
    """Không khai danh mục thì ô giá trị không bấm được gì — chặn ngay ở schema."""
    from app.modules.dossier.field_schema import validate_field_schema

    with pytest.raises(ValueError, match="danh mục"):
        validate_field_schema([_def("ns", "Nhân sự", type="reference")])


def test_reference_chi_nhan_danh_muc_trong_DANH_SACH_TRANG(db):
    """⚠️ Chốt CHỐNG DÒ ENDPOINT, không phải chuyện gõ đúng chính tả.

    Nếu ô này nhận URL (hay một khóa tùy ý) từ máy khách thì bất kỳ ai sửa được
    bộ trường đều bắt giao diện đi đọc một đường dẫn bất kỳ của hệ — biến ô chọn
    thành cửa dò. Danh sách trắng theo KHÓA là thứ chặn việc đó.
    """
    from app.modules.dossier.field_schema import validate_field_schema

    validate_field_schema([_def("ns", "Nhân sự", type="reference", source="employee")])

    for bad in ("/api/users", "user", "role", "setting"):
        with pytest.raises(ValueError, match="không có thật"):
            validate_field_schema([_def("x", "X", type="reference", source=bad)])


@pytest.mark.parametrize("raw,expected", [
    (42, 42), ("42", 42), ("", ""), (None, ""), (0, ""), ("0", ""),
])
def test_reference_luu_ID_chu_khong_luu_ten(raw, expected):
    """Khách chốt lưu ID (17/09/2026) — tên luôn đọc theo danh mục.

    Đổi tên nhân sự thì mọi hồ sơ đổi theo; lưu tên thì không làm được điều đó.
    """
    from app.modules.dossier.field_schema import DossierFieldDef
    from app.modules.dossier.field_values import validate_extra_values

    d = DossierFieldDef.model_validate(
        _def("ns", "Nhân sự", type="reference", source="employee"))
    assert validate_extra_values([d], {"ns": raw}) == {"ns": expected}


@pytest.mark.parametrize("bad", ["Nguyễn Văn A", "abc", -5])
def test_reference_khong_nhan_rac(bad):
    from app.modules.dossier.field_schema import DossierFieldDef
    from app.modules.dossier.field_values import validate_extra_values

    d = DossierFieldDef.model_validate(
        _def("ns", "Nhân sự", type="reference", source="employee"))
    with pytest.raises(ValueError, match="Nhân sự"):
        validate_extra_values([d], {"ns": bad})


def test_reference_ID_khong_co_that_bi_CHAN(db, loai, world):
    """⚠️ Bài kiểm quan trọng nhất của kiểu này.

    ID trỏ vào hư không thì màn hình hiện **trống trơn** — nhìn y hệt ô chưa ai
    nhập. Không lỗi, không cảnh báo, và hồ sơ mất dữ liệu mà không ai biết. Một
    câu 422 lúc lưu rẻ hơn nhiều so với việc đó.
    """
    values = {
        "dossier_type_id": loai.id,
        "custom_fields": [_def("ns", "Nhân sự", type="reference", source="employee")],
        "extra_fields": {"ns": 999999},
    }
    with pytest.raises(HTTPException, match="không còn tồn tại"):
        service.apply_extra_fields(db, values)

    #  ID có thật thì lọt.
    values["extra_fields"] = {"ns": world.emp["a1"]}
    service.apply_extra_fields(db, values)
    assert values["extra_fields"]["ns"] == world.emp["a1"]


def test_hai_danh_sach_trang_KHOP_nhau_giua_hai_dau():
    """Khóa ở backend và ở TypeScript phải khớp từng chữ.

    Lệch một khóa thì người dùng khai được một danh mục mà backend chặn khi bấm
    Lưu — hoặc ngược lại, một danh mục backend nhận mà giao diện không bày ra.
    Không dòng nào đỏ lên nếu không có bài kiểm này.
    """
    import re
    from pathlib import Path

    from app.modules.dossier.reference_sources import REFERENCE_MODELS

    #  `./frontend-v2/src` được mount sẵn vào `/app/fe-src` (xem `docker-compose.yml`)
    #  đúng cho loại bài kiểm chéo hai đầu này. Đường lùi là cây mã nguồn thật,
    #  cho ai chạy pytest ngoài container.
    ts = next(
        (p for p in (
            Path("/app/fe-src/modules/dossier/types/dossier-reference-sources.ts"),
            Path(__file__).resolve().parents[2]
            / "frontend-v2/src/modules/dossier/types/dossier-reference-sources.ts",
        ) if p.exists()),
        None,
    )
    #  ⚠️ KHÔNG `skip` khi thiếu tệp: bài kiểm lặng lẽ skip là mất luôn cái nó
    #  canh, đúng lúc CI cần nó nhất (bài học `_modules_dir` ở
    #  `test_pham_vi_luat_bat_bien.py`). Thiếu thì đỏ, và đi sửa chỗ mount.
    assert ts is not None, (
        "không thấy `dossier-reference-sources.ts` — kiểm lại mount "
        "`./frontend-v2/src:/app/fe-src` trong docker-compose.yml"
    )

    #  ⚠️ Cắt từ dòng KHAI BÁO tới dấu `}` đầu tiên đứng một mình ở cột 0. Bản
    #  đầu cắt bằng `split("REFERENCE_SOURCES")[-1]` và rơi vào khúc SAU hàm
    #  `referenceSource()` cuối tệp — khúc đó không có khóa nào, nên bài kiểm
    #  đọc ra danh sách RỖNG.
    text = ts.read_text(encoding="utf-8")
    block = text[text.index("export const REFERENCE_SOURCES") :].split("\n}\n", 1)[0]
    keys = set(re.findall(r"^  (\w+): \{", block, re.M))
    #  Bắt được 0 khóa nghĩa là cách đọc tệp đã hỏng (đổi thụt lề, Prettier ngắt
    #  dòng khác…), không phải frontend xóa hết danh mục. Nói thẳng ra, đừng để
    #  người sau đi tìm khóa bị mất ở một chỗ không có lỗi nào.
    assert keys, f"không đọc được khóa nào trong `REFERENCE_SOURCES` — kiểm lại cách cắt khối ở {ts}"
    assert keys == set(REFERENCE_MODELS), (
        f"danh sách trắng lệch nhau — chỉ backend: {sorted(set(REFERENCE_MODELS) - keys)}, "
        f"chỉ frontend: {sorted(keys - set(REFERENCE_MODELS))}"
    )
