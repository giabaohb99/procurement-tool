"""BỘ TRƯỜNG TÙY BIẾN của loại hồ sơ — phần «metadata» của phân hệ Hồ sơ.

Đây là chỗ mềm dẻo nhất của cả phân hệ, nên cũng là chỗ dễ thủng nhất: người
dùng tự khai ô nhập, và giá trị họ điền nằm trong một cột JSON mà không ràng
buộc nào của MySQL với tới. Mọi chốt chặn vì thế phải nằm ở tầng schema.

⚠️ **SQLite của bộ test không ép gì trên cột JSON** — ghi xuống DB rồi khẳng
định là xanh giả. Kiểm thẳng bằng `pytest.raises`.

Bài kiểm ở đây đi theo bốn nhóm, thứ tự từ *hỏng ồn ào* tới *hỏng im lặng*:

1. Khai báo ô sai → 422 (ồn, dễ thấy)
2. Giá trị sai kiểu → 422
3. **Khóa trùng / khóa không còn khai** → hỏng IM LẶNG nếu không chặn
4. Trần kích thước → không chặn thì MySQL nuốt hết và màn hình đứng về sau
"""
import pytest
from pydantic import ValidationError

from app.modules.dossier.field_schema import (MAX_FIELDS, MAX_OPTIONS,
                                              MAX_SCHEMA_BYTES,
                                              DossierFieldDef,
                                              parse_field_defs,
                                              validate_field_schema)
from app.modules.dossier.field_values import (MAX_TOTAL_BYTES, MAX_VALUE_LEN,
                                              validate_extra_values)
from app.modules.dossier.type_schema import DossierTypeCreate


def _defs(*items) -> list[DossierFieldDef]:
    return [DossierFieldDef.model_validate(x) for x in items]


# ── 1. Khai báo ô ───────────────────────────────────────────────────────────
@pytest.mark.parametrize("raw,expected", [
    ("So Giay Phep", "so_giay_phep"),
    ("  SO_GP  ", "so_gp"),
    ("so-giay-phep", "so_giay_phep"),
])
def test_ma_truong_luon_ve_chu_thuong_gach_duoi(raw, expected):
    """Mã trường đi vào JSON, vào tiêu đề cột Excel, và vào tên ô react-hook-form.

    Chuẩn hóa một lần ở schema chứ không ở giao diện: mã còn vào hệ qua đường
    nhập CSV và qua bất kỳ ai gọi thẳng API.
    """
    assert DossierFieldDef(key=raw, label="x").key == expected


@pytest.mark.parametrize("key", ["số_giấy_phép", "so giay.phep", "1_so_gp", "", "   "])
def test_ma_truong_co_dau_hoac_dau_cham_bi_chan(key):
    """Dấu CHẤM là ca nguy hiểm nhất, và nó im lặng.

    react-hook-form cắt tên ô theo dấu chấm để hiểu là đường dẫn lồng nhau, nên
    một khóa `a.b` làm ô đó ghi vào `{a: {b: ...}}` thay vì `{"a.b": ...}` —
    người dùng gõ, bấm Lưu, hệ báo thành công, và giá trị nằm ở một chỗ khác.

    Chữ có dấu thì hỏng ở đường khác: khóa JSON tiếng Việt sống được dưới MySQL
    nhưng vỡ ngay khi ai đó xuất ra CSV hoặc gõ nó vào một câu truy vấn.
    """
    with pytest.raises(ValidationError):
        DossierFieldDef(key=key, label="x")


def test_o_chon_phai_khai_it_nhat_mot_muc():
    """Ô chọn rỗng hiện ra một danh sách không bấm được gì — người dùng tưởng hỏng."""
    with pytest.raises(ValueError, match="ít nhất một mục"):
        validate_field_schema([{"key": "pt", "label": "Phương thức", "type": "select"}])


def test_muc_trung_nhau_trong_o_chon_bi_chan():
    """Hai mục cùng chữ thì bấm dòng nào cũng ra một giá trị — đọc như lỗi bấm nhầm."""
    with pytest.raises(ValidationError):
        DossierFieldDef(key="pt", label="x", type="select",
                        options=["Đường biển", "Đường biển"])


def test_ma_truong_trung_nhau_bi_chan():
    """⚠️ Ca hỏng NGẦM nhất của cả bộ trường.

    Hai ô khai cùng khóa thì biểu mẫu vẫn hiện đủ hai ô, người dùng gõ hai giá
    trị khác nhau, và chỉ một cái sống sót trong `extra_fields` — không lỗi,
    không cảnh báo, không cách nào biết mình vừa mất gì.
    """
    with pytest.raises(ValueError, match="trùng"):
        validate_field_schema([
            {"key": "so_gp", "label": "Số giấy phép"},
            {"key": "so_gp", "label": "Số GP (cũ)"},
        ])


def test_kieu_o_la_bi_chan():
    """Tập kiểu là ĐÓNG và phải khớp `CrudFormField['type']` của giao diện.

    Kiểu lạ lọt xuống thì màn hình không biết vẽ ô gì — người dùng mất trắng ô
    đó mà không có gì báo.
    """
    with pytest.raises(ValidationError):
        DossierFieldDef(key="x", label="x", type="richtext")


# ── 2. Trần kích thước của bộ khai báo ──────────────────────────────────────
def test_qua_nhieu_o_bi_chan():
    too_many = [{"key": f"o{i}", "label": f"Ô {i}"} for i in range(MAX_FIELDS + 1)]
    with pytest.raises(ValueError, match=str(MAX_FIELDS)):
        validate_field_schema(too_many)
    #  Đúng bằng trần thì phải LỌT — chặn thừa cũng là lỗi.
    validate_field_schema(too_many[:MAX_FIELDS])


def test_qua_nhieu_muc_chon_bi_chan():
    with pytest.raises(ValidationError):
        DossierFieldDef(key="x", label="x", type="select",
                        options=[f"m{i}" for i in range(MAX_OPTIONS + 1)])


def test_tong_kich_thuoc_bo_truong_bi_chan():
    """Bốn chốt trên vẫn để lọt 20 ô × 30 mục × 100 ký tự tiếng Việt.

    Không có chốt tổng thì MySQL nhận hết (cột JSON chứa tới 1GB) và không gì
    nổ — chỉ là mọi màn đọc loại hồ sơ đó về sau đều nặng thêm, và không ai truy
    ra vì sao.
    """
    fat = [{"key": f"o{i}", "label": "Tên ô rất dài " * 6, "type": "select",
            "options": [f"mục chọn khá dài số {j}" for j in range(MAX_OPTIONS)]}
           for i in range(MAX_FIELDS)]
    with pytest.raises(ValueError, match=str(MAX_SCHEMA_BYTES)):
        validate_field_schema(fat)


def test_bo_truong_rong_la_hop_le():
    """Nhiều loại giấy tờ chỉ cần mã, tên, hạn — ép khai ô là ép bịa ra ô."""
    assert validate_field_schema([]) == []
    assert validate_field_schema(None) == []
    assert DossierTypeCreate(code="HD", name="Hợp đồng").field_schema == []


# ── 3. Đường ĐỌC khoan dung, ngược với đường GHI ────────────────────────────
def test_dong_khai_hong_duoi_db_khong_lam_vo_ca_man_hinh():
    """Một dòng hỏng (bản cũ, hay ai đó sửa tay) không được thành mất cả phân hệ.

    ⚠️ Cố ý ngược với `validate_field_schema`: đường GHI thì nghiêm, đường ĐỌC
    thì bỏ qua dòng hỏng. Nghiêm ở cả hai đường nghĩa là hỏng một ô làm 500 cả
    màn danh sách hồ sơ.
    """
    defs = parse_field_defs([
        {"key": "so_gp", "label": "Số giấy phép"},
        {"key": "", "label": "hỏng"},           # mã rỗng
        {"key": "x", "label": "y", "type": "richtext"},   # kiểu lạ
        "không phải dict",
    ])
    assert [d.key for d in defs] == ["so_gp"]


# ── 4. GIÁ TRỊ người dùng điền ──────────────────────────────────────────────
def test_o_bat_buoc_bo_trong_bi_chan():
    defs = _defs({"key": "so_gp", "label": "Số giấy phép", "required": True})
    with pytest.raises(ValueError, match="Số giấy phép"):
        validate_extra_values(defs, {})
    assert validate_extra_values(defs, {"so_gp": "GP-01"}) == {"so_gp": "GP-01"}


def test_cong_tac_tat_van_la_mot_cau_tra_loi():
    """`False` KHÁC ô bỏ trống.

    Chốt «bắt buộc» mà viết `if not value` thì một ô công tắc bắt buộc không
    bao giờ tắt được — người dùng bấm tắt, bấm Lưu, và bị đòi điền một ô đang
    hiện rõ câu trả lời.
    """
    defs = _defs({"key": "da_tq", "label": "Đã thông quan", "type": "switch",
                  "required": True})
    assert validate_extra_values(defs, {"da_tq": False}) == {"da_tq": False}


@pytest.mark.parametrize("raw,expected", [
    ("false", False), ("0", False), ("true", True), ("có", True), (1, True), (0, False),
])
def test_chuoi_false_khong_bien_thanh_true(raw, expected):
    """`bool("false")` trong Python ra `True` — bẫy kinh điển của đường JSON.

    Biểu mẫu luôn gửi bool thật, nhưng đường nhập CSV và người gọi thẳng API thì
    không, và một ô «Đã thông quan» lật ngược thì không ai đọc ra là sai.
    """
    defs = _defs({"key": "c", "label": "c", "type": "switch"})
    assert validate_extra_values(defs, {"c": raw}) == {"c": expected}


@pytest.mark.parametrize("raw", ["abc", "12abc", float("nan"), float("inf")])
def test_o_so_nhan_rac_thi_422(raw):
    defs = _defs({"key": "gt", "label": "Giá trị", "type": "number"})
    with pytest.raises(ValueError, match="Giá trị"):
        validate_extra_values(defs, {"gt": raw})


def test_so_tron_tra_ve_so_nguyen():
    """«2026.0» ở chỗ đáng lẽ là một năm thì đọc ra như dữ liệu hỏng."""
    defs = _defs({"key": "nam", "label": "Năm", "type": "number"})
    assert validate_extra_values(defs, {"nam": "2026"}) == {"nam": 2026}
    assert validate_extra_values(defs, {"nam": 2026.5}) == {"nam": 2026.5}


@pytest.mark.parametrize("raw", ["16/09/2026", "2026-13-01", "hôm qua"])
def test_o_ngay_sai_dinh_dang_bi_chan(raw):
    defs = _defs({"key": "ngay", "label": "Ngày đến", "type": "date"})
    with pytest.raises(ValueError, match="Ngày đến"):
        validate_extra_values(defs, {"ngay": raw})


def test_o_chon_chi_nhan_muc_da_khai():
    """Giá trị ngoài danh sách lọt xuống thì ô chọn hiện TRỐNG như chưa ai điền.

    Radix `Select` không tìm được mục khớp thì rơi về chữ gợi ý — người dùng
    tưởng dữ liệu bị mất, chọn đại một mục khác, và giá trị thật bị ghi đè.
    """
    defs = _defs({"key": "pt", "label": "Phương thức", "type": "select",
                  "options": ["Đường biển", "Đường bộ"]})
    with pytest.raises(ValueError, match="Đường biển"):
        validate_extra_values(defs, {"pt": "Tàu ngầm"})
    assert validate_extra_values(defs, {"pt": ""}) == {"pt": ""}


def test_khoa_khong_con_khai_van_duoc_giu():
    """⚠️ Luật đổi lấy, đọc kỹ trước khi nới.

    Quản trị bỏ một ô khỏi loại hồ sơ thì hàng trăm hồ sơ cũ vẫn mang giá trị
    của ô đó. Ném 422 là khóa chết việc sửa chúng (đụng ô nào cũng không lưu
    nổi); xóa lặng là mất dữ liệu thật mà không ai kịp thấy.
    """
    defs = _defs({"key": "moi", "label": "Ô mới"})
    out = validate_extra_values(defs, {"moi": "a", "o_cu": "giá trị cũ"})
    assert out == {"moi": "a", "o_cu": "giá trị cũ"}


def test_khoa_khong_con_khai_van_phai_la_gia_tri_don():
    """Giữ lại KHÔNG có nghĩa là để chúng phình ra vô hạn.

    Không chặn thì đường duy nhất nhét được một cây JSON khổng lồ vào cột này là
    khai một ô, gửi giá trị, rồi xóa ô đó đi.
    """
    with pytest.raises(ValueError, match="giá trị đơn"):
        validate_extra_values([], {"o_cu": {"lồng": {"nhau": [1, 2, 3]}}})


def test_chuoi_qua_dai_bi_chan_theo_tung_o():
    defs = _defs({"key": "t", "label": "Tên", "type": "text"})
    with pytest.raises(ValueError, match=str(MAX_VALUE_LEN)):
        validate_extra_values(defs, {"t": "x" * (MAX_VALUE_LEN + 1)})
    validate_extra_values(defs, {"t": "x" * MAX_VALUE_LEN})


def test_o_nhieu_dong_rong_hon_o_mot_dong():
    """Ô nhiều dòng sinh ra để chứa đoạn văn (điều khoản, kết quả thẩm định)."""
    defs = _defs({"key": "dk", "label": "Điều khoản", "type": "textarea"})
    validate_extra_values(defs, {"dk": "x" * (MAX_VALUE_LEN + 1)})


def test_tong_kich_thuoc_gia_tri_bi_chan():
    """Chốt cuối — ba chốt trên vẫn để lọt 20 khóa × 2000 ký tự."""
    defs = _defs(*[{"key": f"o{i}", "label": f"Ô {i}", "type": "textarea"}
                   for i in range(MAX_FIELDS)])
    fat = {f"o{i}": "đoạn văn dài " * 150 for i in range(MAX_FIELDS)}
    with pytest.raises(ValueError, match=str(MAX_TOTAL_BYTES)):
        validate_extra_values(defs, fat)


def test_gia_tri_khong_phai_doi_tuong_bi_chan():
    with pytest.raises(ValueError, match="đối tượng"):
        validate_extra_values([], ["không", "phải", "dict"])
