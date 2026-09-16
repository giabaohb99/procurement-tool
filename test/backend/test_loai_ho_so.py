"""DANH MỤC LOẠI HỒ SƠ — `tab_dossier_type` (phân hệ Hồ sơ, 16/09/2026).

Bài kiểm ở đây chốt ba nhóm, theo thứ tự dễ vỡ:

1. **Ràng buộc kích thước nằm ở SCHEMA, không ở MySQL** (bài học duoc-CR-316).
   ⚠️ SQLite của bộ test **không ép độ dài `VARCHAR`** — bài nào ghi xuống DB
   rồi khẳng định là *xanh giả*. Phải kiểm thẳng bằng `pytest.raises`.
2. **Chuẩn hóa mã** — mã luôn CHỮ HOA, cắt khoảng trắng. Không chuẩn hóa thì
   `hd` và `HD` là một dòng trên MySQL (đối chiếu không phân biệt hoa thường)
   nhưng là hai dòng trong test SQLite.
3. **Nối vào hệ phân quyền** — entity mới phải có mặt ở `ENTITIES`, có nhãn
   tiếng Việt, và khai `SCOPE_FIELDS`. Thiếu khai `SCOPE_FIELDS` thì
   `apply_scope` **chặn tất** (B-07) và màn danh mục rỗng trơn mà không ai hiểu
   vì sao.
"""
import pytest
from pydantic import ValidationError

from app.core.permissions import ENTITIES, ENTITY_LABELS
from app.core.scoping import PUBLIC, SCOPE_FIELDS
from app.modules.dossier.type_model import DossierType
from app.modules.dossier.type_schema import (DossierTypeCreate,
                                             DossierTypeUpdate)


# ── 1. Ràng buộc kích thước (tầng schema) ──────────────────────────────────
@pytest.mark.parametrize("field,limit", [
    ("code", 30),
    ("name", 100),
    ("description", 500),
])
def test_chuoi_qua_dai_bi_chan_o_schema(field, limit):
    """Quá `String(n)` một ký tự là 422, không phải 500 từ MySQL.

    Con số ở đây phải khớp ĐÚNG `String(n)` trong `type_model.py`. Đổi độ dài
    cột mà quên sửa một trong hai chỗ thì hoặc chặn hụt (500 quay lại), hoặc
    chặn thừa (người dùng không dùng hết được ô).
    """
    values = {"code": "HD", "name": "Hợp đồng"}
    values[field] = "x" * (limit + 1)
    with pytest.raises(ValidationError):
        DossierTypeCreate(**values)

    #  Đúng bằng trần thì phải LỌT — chặn thừa cũng là lỗi.
    values[field] = "x" * limit
    DossierTypeCreate(**values)


@pytest.mark.parametrize("months", [-1, 1201, 99999])
def test_han_hieu_luc_ngoai_dai_bi_chan(months):
    """`SMALLINT` tràn ở 32768; trần 1200 tháng (100 năm) chặn sớm hơn nhiều.

    Không có trần thì một lần gõ nhầm `99999` đi thẳng xuống cột và MySQL là chỗ
    đầu tiên phản đối — người dùng nhận «mã sự cố» cho một ô nhập số.
    """
    with pytest.raises(ValidationError):
        DossierTypeCreate(code="HD", name="Hợp đồng", default_valid_months=months)


def test_han_vo_thoi_han_la_gia_tri_hop_le():
    """`0` = vô thời hạn, một lựa chọn THẬT chứ không phải ô bỏ trống."""
    assert DossierTypeCreate(code="HD", name="Hợp đồng").default_valid_months == 0


def test_o_bat_buoc_khong_duoc_rong_hay_toan_khoang_trang():
    """Tên rỗng thì ô chọn loại hồ sơ hiện một mục trắng không bấm trúng."""
    for name in ("", "   ", "\t\n"):
        with pytest.raises(ValidationError):
            DossierTypeCreate(code="HD", name=name)
    for code in ("", "   "):
        with pytest.raises(ValidationError):
            DossierTypeCreate(code=code, name="Hợp đồng")

    #  Sửa cũng vậy: gửi `name=""` là cố tình xóa tên, không phải bỏ qua ô đó.
    with pytest.raises(ValidationError):
        DossierTypeUpdate(name="  ")
    #  Còn `None` nghĩa là "không đụng tới ô này" — phải lọt.
    assert DossierTypeUpdate(name=None).name is None


# ── 2. Chuẩn hóa mã ────────────────────────────────────────────────────────
@pytest.mark.parametrize("raw,expected", [
    ("hd", "HD"),
    ("  hd  ", "HD"),
    ("Hd", "HD"),
    ("atld", "ATLD"),
])
def test_ma_luon_chu_hoa_va_cat_khoang_trang(raw, expected):
    """Ép ở SCHEMA chứ không ở giao diện.

    Mã còn vào hệ qua đường nhập CSV và qua bất kỳ ai gọi thẳng API — vá mỗi ô
    nhập thì hai đường kia vẫn đẻ ra mã thường, và chốt trùng mã của bộ sinh CRUD
    (so bằng `==`) sẽ cho `hd` lọt qua bên cạnh `HD` đã có.
    """
    assert DossierTypeCreate(code=raw, name="X").code == expected


def test_ma_khong_sua_duoc_sau_khi_tao():
    """`DossierTypeUpdate` KHÔNG khai `code` — mã là thứ CSV và các màn khác trỏ tới."""
    assert "code" not in DossierTypeUpdate.model_fields


# ── 3. Nối vào hệ phân quyền ───────────────────────────────────────────────
def test_entity_khai_du_ba_cho():
    """Thiếu một trong ba chỗ là hỏng theo ba kiểu khác nhau, đều im lặng.

    Vắng `ENTITIES` → màn Phân quyền không có dòng nào để tick, không ai cấp
    được quyền. Vắng `ENTITY_LABELS` → dòng đó hiện tên kỹ thuật `dossier_type`.
    Vắng `SCOPE_FIELDS` → `apply_scope` **chặn tất** (B-07), danh sách rỗng trơn.
    """
    assert "dossier_type" in ENTITIES
    assert ENTITY_LABELS.get("dossier_type")
    assert SCOPE_FIELDS.get("dossier_type") is PUBLIC


def test_quan_ly_thu_mua_chi_doc_duoc_danh_muc_ho_so():
    """`_PUR_MANAGER_PERMS` quét cả `ENTITIES` **trừ** `_SYS_ENTITIES`.

    Quên loại trừ là Quản lý thu mua tự nhiên xóa được loại hồ sơ pháp lý của
    phòng Hành chính — cùng bẫy đã bắt được với `employee_sensitive`.

    ⚠️ Đừng khẳng định `"dossier_type" not in _PUR_MANAGER_PERMS`: vai trò
    `pur_manager` dùng **chính đối tượng dict đó** làm `perms`, nên vòng
    `setdefault` cấp `read` cho mọi vai trò ở cuối `seed.py` cũng ghi thẳng vào
    nó. Cái cần canh là BỘ HÀNH ĐỘNG, không phải sự có mặt của khóa.
    """
    from app.seed import STD_ROLES

    actions, scope = STD_ROLES["pur_manager"]["perms"]["dossier_type"]
    assert actions == ["read"], "Quản lý thu mua không được sửa danh mục loại hồ sơ"
    assert scope == "all"

    #  Chiều ngược lại: MỌI vai trò phải đọc được, kẻo ô chọn loại hồ sơ rỗng
    #  sạch với người dùng thường và họ đọc ra "công ty chưa khai loại nào".
    for code, info in STD_ROLES.items():
        actions, scope = info["perms"]["dossier_type"]
        assert "read" in actions, f"vai trò {code} thiếu quyền đọc danh mục loại hồ sơ"
        assert scope == "all"

    #  Vai trò mẫu để giao cho Hành chính — sửa được, không cần quyền quản trị.
    assert "write" in STD_ROLES["dossier_admin"]["perms"]["dossier_type"][0]


# ── Ghi xuống DB: kiểm mặc định, KHÔNG kiểm độ dài (SQLite không ép) ───────
def test_mac_dinh_cua_ban_ghi_moi(db):
    """Loại mới: còn dùng, vô thời hạn, mô tả rỗng — không cột nào ra `None`.

    Cột `default=` chỉ áp lúc INSERT, nên bản ghi CHƯA flush vẫn đọc ra `None`.
    Bài này flush rồi mới đọc, đúng như đường đi của endpoint.
    """
    row = DossierType(code="HD", name="Hợp đồng")
    db.add(row)
    db.flush()

    assert row.is_active is True
    assert row.default_valid_months == 0
    assert row.description == ""
    assert row.sort_order == 0
