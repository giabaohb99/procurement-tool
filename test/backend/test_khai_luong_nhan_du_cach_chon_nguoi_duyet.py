"""Ô CHỌN BÀY RA CÁI GÌ THÌ LƯU ĐƯỢC CÁI ĐÓ (lỗi 26/08/2026).

Khách khai bước duyệt cho luồng Văn bản, chọn *«Trưởng bộ phận của phòng ban chỉ
định»* rồi bấm lưu và nhận đúng một dòng đỏ:

    Dữ liệu không hợp lệ (approver_kind: Input should be less than or equal to 6)

Nguyên nhân: `NodeIn.approver_kind` khai biên bằng tay `le=6`, còn
`APPROVER_KIND_LABELS` — cái mà `/options` đổ thẳng ra ô chọn — đã có bảy dòng từ
lúc thêm `APPROVER_DEPT_HEAD_OF = 7`. Ô chọn bày lựa chọn thứ bảy, validator chặn
nó, và không có đường nào khai được.

Nên bài kiểm không đi hỏi "7 có hợp lệ không" (hỏi thế thì lần sau thêm giá trị
thứ tám lại lọt y hệt). Nó hỏi **mọi giá trị `/options` bày ra đều lưu được**, và
ngược lại giá trị không có trong danh sách thì phải bị chặn.
"""
import pytest
from pydantic import ValidationError

from app.modules.approval.flow_controller import NodeIn
from app.modules.approval.flow_model import (APPROVER_DEPT_HEAD_OF,
                                             APPROVER_KIND_LABELS,
                                             MULTI_MODE_LABELS,
                                             NODE_KIND_LABELS,
                                             NO_APPROVER_CHOICES, ROLE_LABELS,
                                             SKIP_MODE_LABELS)


@pytest.mark.parametrize("kind", sorted(APPROVER_KIND_LABELS))
def test_moi_cach_chon_nguoi_duyet_bay_ra_deu_khai_duoc(kind):
    assert NodeIn(seq=1, approver_kind=kind).approver_kind == kind


def test_truong_bo_phan_cua_phong_ban_chi_dinh_khai_duoc(kind=APPROVER_DEPT_HEAD_OF):
    """Chính cái lựa chọn khách bấm lúc gặp lỗi."""
    assert NodeIn(seq=1, approver_kind=kind, approver_ref="12").approver_kind == kind


@pytest.mark.parametrize("value", [0, -1, 99, max(APPROVER_KIND_LABELS) + 1])
def test_cach_chon_khong_co_trong_danh_sach_thi_chan(value):
    with pytest.raises(ValidationError):
        NodeIn(seq=1, approver_kind=value)


@pytest.mark.parametrize("o,bang", [
    ("node_kind", NODE_KIND_LABELS),
    ("flow_role", ROLE_LABELS),
    ("multi_mode", MULTI_MODE_LABELS),
    ("skip_duplicate", SKIP_MODE_LABELS),
])
def test_cac_o_chon_khac_cung_khop_bang_nhan(o, bang):
    """Cùng một cái bẫy, bốn ô còn lại — `node_kind` và `flow_role` trước đây
    KHÔNG kiểm gì cả, tức khai số 99 cũng lưu được rồi hỏng lúc chạy luồng."""
    for value in bang:
        assert getattr(NodeIn(seq=1, **{o: value}), o) == value
    with pytest.raises(ValidationError):
        NodeIn(seq=1, **{o: max(bang) + 1})


def test_khong_khai_moi_duoc_lua_chon_da_bo():
    """«Đẩy lên cấp trên» (2) còn nhãn để đọc dữ liệu cũ nhưng đã bỏ từ CR-114 —
    nhãn còn không có nghĩa là khai mới được."""
    for code in NO_APPROVER_CHOICES:
        assert NodeIn(seq=1, on_no_approver=code).on_no_approver == code
    with pytest.raises(ValidationError):
        NodeIn(seq=1, on_no_approver=2)
