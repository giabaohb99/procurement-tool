"""CR-157 — mỗi MÀN HÌNH danh mục Văn thư một khóa quyền riêng.

Trước 25/08/2026 bốn màn (Loại văn bản · Thư viện mẫu · Quy tắc đánh số · Quy tắc
quan hệ) dùng chung khóa `doc_type`, nên cho ai sửa quy tắc đánh số là cho họ sửa
luôn loại văn bản. Ba việc do ba người khác nhau làm mà không tách được.

Bài kiểm ở đây giữ hai chiều:
  · **tách rồi thì phải tách thật** — không controller nào còn gác bằng khóa cũ;
  · **tách xong không ai mất quyền** — người soạn văn bản vẫn đọc được thư viện mẫu.
"""
import re
from pathlib import Path

import pytest

from app.core.permissions import ENTITIES, ENTITY_LABELS
from app.core.scoping import PUBLIC, SCOPE_FIELDS

#  Lấy đường dẫn từ chính gói `app` đã nạp, đừng dựng lại từ vị trí tệp test:
#  trong container mã nằm ở `/app`, ngoài host nằm ở `backend/app` — dựng tay là
#  đúng một chỗ và sai chỗ kia.
import app as _goi_app  # noqa: E402

GOC = Path(_goi_app.__file__).resolve().parent / "modules"

KHOA_MOI = ("doc_template", "doc_numbering_rule", "doc_link_rule")

#  Tệp controller → khóa mà nó PHẢI gác bằng.
CHU_CUA_MAN = {
    "doc_catalog/numbering_rule_controller.py": "doc_numbering_rule",
    #  Cấp/đốt số hiệu là việc của màn Quy tắc đánh số, không phải của Loại văn bản.
    "doc_catalog/issue_code_controller.py": "doc_numbering_rule",
    "doc_catalog/link_rule_controller.py": "doc_link_rule",
    "document/template_controller.py": "doc_template",
}


def _khoa_trong(duong_dan: str) -> set[str]:
    noi_dung = (GOC / duong_dan).read_text(encoding="utf-8")
    return set(re.findall(r'require\(\s*"([a-z_]+)"', noi_dung))


# ── Khai báo ────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("khoa", KHOA_MOI)
def test_khoa_moi_co_mat_du_ba_noi(khoa):
    """Thiếu một trong ba là khóa chết: gác được nhưng không ai tick cho được."""
    assert khoa in ENTITIES, "chưa khai ở core/permissions.ENTITIES"
    assert khoa in ENTITY_LABELS, "chưa có nhãn — màn Phân quyền hiện mã trần"
    assert khoa in SCOPE_FIELDS, "chưa khai phạm vi — apply_scope sẽ chặn sạch"


@pytest.mark.parametrize("khoa", KHOA_MOI)
def test_danh_muc_nen_khong_loc_theo_phap_nhan(khoa):
    """Ba danh mục này dùng chung cho mọi pháp nhân, cùng lẽ với `doc_type`.

    Khai nhầm thành có chiều lọc thì `_role_scope_cond` không dựng nổi điều kiện
    và **chặn tất cả** (luật B-07), tức là màn danh mục trống trơn với mọi người.
    """
    assert SCOPE_FIELDS[khoa] is PUBLIC


def test_nhan_doc_theo_duong_menu_khong_theo_ten_bang():
    """Người khai quyền tìm theo thứ họ BẤM trên màn hình.

    Nhãn cũ («Loại văn bản (Văn thư)») bắt họ tự biết ba dòng nào gộp lại thành
    một mục menu, còn dòng nào trải ra ba mục — đó chính là chỗ khách kêu.
    """
    van_thu = ("doc_type", *KHOA_MOI, "external_party", "security_level",
               "document_book", "document")
    for khoa in van_thu:
        assert ENTITY_LABELS[khoa].startswith("Văn thư › "), ENTITY_LABELS[khoa]


# ── Controller gác đúng khóa ────────────────────────────────────────────────

@pytest.mark.parametrize("tep,khoa", sorted(CHU_CUA_MAN.items()))
def test_controller_gac_bang_khoa_cua_chinh_man_do(tep, khoa):
    dang_dung = _khoa_trong(tep)
    assert khoa in dang_dung, f"{tep} chưa gác bằng {khoa}"
    assert "doc_type" not in dang_dung, (
        f"{tep} vẫn còn gác bằng doc_type — tách khóa mà không đổi chỗ gác thì "
        "không tách được gì, chỉ thêm một khóa không ai dùng")


def test_loai_van_ban_van_giu_doc_type():
    """Chốt chiều ngược: đừng dọn tay quá đà rồi cuốn luôn màn Loại văn bản."""
    assert _khoa_trong("doc_catalog/controller.py") == set(), (
        "danh mục nền dùng make_crud_router, không khai require() thẳng")


# ── Không ai mất quyền ──────────────────────────────────────────────────────

def test_nguoi_soan_van_ban_van_doc_duoc_thu_vien_mau():
    """Ô «Dùng mẫu» ở bước 1 màn Tạo văn bản gọi `/api/document-templates`.

    Khóa của nó vừa tách khỏi `doc_type`, nên vai trò soạn thảo phải được khai
    lại tường minh — thiếu là người soạn ăn toast 403 ngay lúc mở màn, ở một ô
    họ còn chưa bấm tới. Cùng cái bẫy đã dính với `security_level` (xem ghi chú
    ở `STD_ROLES`).
    """
    from app.seed import STD_ROLES

    quyen = STD_ROLES["vanban_sua"]["perms"]
    assert "doc_template" in quyen, "vai trò soạn thảo chưa được khai doc_template"
    hanh_dong, _pham_vi = quyen["doc_template"]
    assert "read" in hanh_dong
