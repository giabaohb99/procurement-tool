"""LÊN BẢN MỚI KHI SỬA LUỒNG — không được đâm vào luồng cùng mã.

Lỗi khách báo 25/08/2026: mở luồng duyệt, bấm **Thêm bước** → toast đỏ «Request
failed with status code 500», bước vừa khai biến mất.

Nguyên nhân: `tab_approval_flow` có `UNIQUE(entity, code, version_no)` mà `code`
**được phép bỏ trống**, nên hai luồng khác nhau cùng mã rỗng là chuyện thường
trên dữ liệu thật. Mỗi lần sửa luồng thì `version_no += 1`; luồng B lên bản 2
đâm vào luồng A đang giữ bản 2 →
`Duplicate entry 'document--2' for key 'uq_approval_flow_code_version'`.
"""
from app.modules.approval.flow_controller import _ban_ke_tiep
from app.modules.approval.flow_model import ApprovalFlow

ACTOR = 1
ENTITY = "document"


def _luong(db, code: str, version_no: int, name: str) -> ApprovalFlow:
    flow = ApprovalFlow(entity=ENTITY, code=code, name=name, version_no=version_no,
                        is_active=True, created_by=ACTOR, updated_by=ACTOR)
    db.add(flow)
    db.commit()
    return flow


def test_ma_rong_trung_nhau_thi_NHAY_QUA_ban_da_co_nguoi_giu(db):
    """Đúng ca đã nổ 500: hai luồng cùng mã rỗng, một cái đang giữ bản 2."""
    _luong(db, "", 2, "Luồng A")
    b = _luong(db, "", 1, "Luồng B")

    assert _ban_ke_tiep(db, b) == 3


def test_nhay_qua_NHIEU_ban_lien_tiep(db):
    _luong(db, "", 2, "A")
    _luong(db, "", 3, "B")
    _luong(db, "", 4, "C")
    d = _luong(db, "", 1, "D")

    assert _ban_ke_tiep(db, d) == 5


def test_khac_MA_thi_khong_dung_toi_nhau(db):
    """Ràng buộc tính theo (entity, code) — khác mã thì trùng số bản là hợp lệ."""
    _luong(db, "VB_A", 2, "A")
    b = _luong(db, "VB_B", 1, "B")

    assert _ban_ke_tiep(db, b) == 2


def test_khac_LOAI_CHUNG_TU_cung_khong_dung_toi_nhau(db):
    _luong(db, "", 2, "Của văn bản")
    khac = ApprovalFlow(entity="purchase_request", code="", name="Của YCMH", version_no=1,
                        is_active=True, created_by=ACTOR, updated_by=ACTOR)
    db.add(khac)
    db.commit()

    assert _ban_ke_tiep(db, khac) == 2


def test_luong_don_le_van_tang_deu_nhu_cu(db):
    """Vá xong không được đổi hành vi bình thường: không ai giữ chỗ thì +1."""
    a = _luong(db, "VB_RIENG", 7, "A")

    assert _ban_ke_tiep(db, a) == 8


def test_ban_ke_tiep_chi_DOC_khong_sua_luong_khac(db):
    """Chỉ tính số — không được lặng lẽ dời bản của luồng đang giữ chỗ."""
    a = _luong(db, "", 2, "A")
    b = _luong(db, "", 1, "B")

    _ban_ke_tiep(db, b)

    db.refresh(a)
    assert a.version_no == 2
