"""BÃI BỎ THU HỒI LUÔN QUYỀN XEM (24/08/2026).

Trước đợt này, bãi bỏ chỉ đổi `status` và **không hàm phân quyền nào đọc tới cột
đó**: ai đọc được văn bản trước khi bãi bỏ thì sau vẫn đọc, vẫn mở chi tiết, vẫn
xuất Word — cả phòng tiếp tục làm theo một văn bản đã chết.

Luật mới: chỉ còn bốn nhóm xem được — người tạo · người chịu trách nhiệm nội
dung · người bãi bỏ · người giữ sổ (quyền đọc phạm vi công ty/toàn hệ). Bài kiểm
ở đây canh đúng bốn nhóm đó và canh cả chiều ngược lại: người ngoài phải mất
quyền, và **văn bản chưa bãi bỏ thì không được đụng gì tới** (luật mới không
được siết nhầm văn bản đang sống).
"""
from types import SimpleNamespace

import pytest

from app.modules.document import revoke_access
from app.modules.document.model import STATUS_EFFECTIVE, STATUS_REVOKED, Document

NGUOI_TAO = 11
NGUOI_BAI_BO = 22
NGUOI_NGOAI = 33
NHAN_SU_NCTN = 77


def _user(user_id: int, employee_id: int | None = None) -> SimpleNamespace:
    """Bản dựng tối thiểu của `user` — hai hàm đang kiểm chỉ đọc hai thuộc tính này."""
    return SimpleNamespace(id=user_id, employee_id=employee_id)


def _profile(scope: str | None = None, action: str = "read") -> dict:
    """Hồ sơ quyền theo mô hình GRANT của `core/auth.get_perm_profile`."""
    if scope is None:
        return {"grants": []}
    return {"grants": [{"role_id": 1, "perms": {"document": {action: True, "scope": scope}}}]}


@pytest.fixture()
def doc_da_bai_bo():
    return Document(
        id=1, title="Quy chế thử", status=STATUS_REVOKED,
        created_by=NGUOI_TAO, updated_by=NGUOI_BAI_BO,
        owner_employee_id=NHAN_SU_NCTN,
    )


def test_nguoi_tao_van_xem_duoc(doc_da_bai_bo):
    assert revoke_access.still_visible(doc_da_bai_bo, _user(NGUOI_TAO), _profile()) is True


def test_nguoi_bai_bo_van_xem_duoc(doc_da_bai_bo):
    """Người vừa bấm bãi bỏ mà mở lại không được thì không ai kiểm tra lại được việc mình vừa làm."""
    assert revoke_access.still_visible(doc_da_bai_bo, _user(NGUOI_BAI_BO), _profile()) is True


def test_nguoi_chiu_trach_nhiem_noi_dung_van_xem_duoc(doc_da_bai_bo):
    """Khớp theo `owner_employee_id` — nhân sự, không phải tài khoản."""
    person = _user(NGUOI_NGOAI, employee_id=NHAN_SU_NCTN)
    assert revoke_access.still_visible(doc_da_bai_bo, person, _profile()) is True


@pytest.mark.parametrize("scope", ["company", "all"])
def test_nguoi_giu_so_van_xem_duoc(doc_da_bai_bo, scope):
    """Quản trị và văn thư: Sổ văn bản phải tra ra được, không thì sổ thủng một lỗ."""
    person = _user(NGUOI_NGOAI, employee_id=999)
    assert revoke_access.still_visible(doc_da_bai_bo, person, _profile(scope)) is True


@pytest.mark.parametrize("scope", [None, "own", "dept", "proc", "assigned"])
def test_nguoi_ngoai_mat_quyen_xem(doc_da_bai_bo, scope):
    """Phạm vi hẹp hơn công ty thì không phải người giữ sổ — mất quyền xem."""
    person = _user(NGUOI_NGOAI, employee_id=999)
    assert revoke_access.still_visible(doc_da_bai_bo, person, _profile(scope)) is False


def test_quyen_giu_so_phai_DUNG_HANH_DONG_doc(doc_da_bai_bo):
    """Có `write` phạm vi công ty nhưng không có `read` thì không tính là giữ sổ.

    Bắt lỗi kiểu "quét thấy chữ company là cho qua": hai cột quyền khác nhau.
    """
    person = _user(NGUOI_NGOAI, employee_id=999)
    ho_so = _profile("company", action="write")
    assert revoke_access.still_visible(doc_da_bai_bo, person, ho_so) is False


def test_van_ban_chua_bai_bo_thi_ai_cung_qua():
    """Luật mới không được siết nhầm văn bản đang sống — chỗ gọi chỉ hỏi MỘT câu."""
    doc = Document(id=2, title="Còn hiệu lực", status=STATUS_EFFECTIVE,
                   created_by=NGUOI_TAO, updated_by=NGUOI_TAO, owner_employee_id=NHAN_SU_NCTN)
    assert revoke_access.still_visible(doc, _user(NGUOI_NGOAI, employee_id=999), _profile()) is True


def test_giu_so_thi_khong_can_loc_gi_them():
    """`None` = không cộng điều kiện nào vào truy vấn danh sách."""
    assert revoke_access.filter_condition(_user(NGUOI_NGOAI), _profile("all")) is None


def test_nguoi_thuong_thi_co_dieu_kien_loc():
    assert revoke_access.filter_condition(_user(NGUOI_NGOAI, 999), _profile("dept")) is not None


#  ── Đường bãi bỏ THỨ HAI: ban hành văn bản mang quan hệ «bãi bỏ» ──────────────
#
#  LỖI THẬT bắt được lúc kiểm trên dữ liệu đang chạy (24/08/2026): `apply_supersede`
#  đổi `status` sang bãi bỏ nhưng KHÔNG ghi `updated_by`. Mà luật quyền xem coi
#  cột đó là "người bãi bỏ" — nên người SỬA CUỐI CÙNG trước đó giữ nguyên quyền
#  xem một văn bản lẽ ra đã bị giấu khỏi họ. Dựng lại đúng ca: văn bản 339 do
#  admin tạo, DEMO_MANAGER sửa lần cuối, bãi bỏ theo quan hệ xong DEMO_MANAGER
#  vẫn đọc được.
def test_bai_bo_theo_quan_he_ghi_dung_nguoi_bai_bo(db, seed):
    from app.modules.doc_catalog.link_rule_model import RELATION_REVOKE
    from app.modules.doc_catalog.model import DocType
    from app.modules.document.link_model import DocumentLink
    from app.modules.document.model import STATUS_EFFECTIVE
    from app.modules.document.supersede_service import apply_supersede

    doc_type = DocType(code="TB", name="Thông báo", id_scheme=1, number_when=2)
    db.add(doc_type)
    db.commit()

    NGUOI_SUA_CUOI = 4
    NGUOI_BAN_HANH = 2

    old = Document(doc_type_id=doc_type.id, company_id=seed.company_id,
                  department_id=seed.dept_id, title="Văn bản cũ",
                  owner_employee_id=seed.emp_req_id,
                  status=STATUS_EFFECTIVE, created_by=NGUOI_BAN_HANH,
                  updated_by=NGUOI_SUA_CUOI)
    new = Document(doc_type_id=doc_type.id, company_id=seed.company_id,
                   department_id=seed.dept_id, title="Văn bản mới bãi bỏ cái cũ",
                   owner_employee_id=seed.emp_req_id,
                   status=STATUS_EFFECTIVE, created_by=NGUOI_BAN_HANH,
                   updated_by=NGUOI_BAN_HANH)
    db.add_all([old, new])
    db.commit()
    db.add(DocumentLink(source_document_id=new.id, target_document_id=old.id,
                        relation=RELATION_REVOKE, created_by=NGUOI_BAN_HANH,
                        updated_by=NGUOI_BAN_HANH))
    db.commit()

    revoked_docs = apply_supersede(db, new, NGUOI_BAN_HANH)
    db.commit()

    assert [d.id for d in revoked_docs] == [old.id], "phải trả về văn bản bị bãi bỏ để chỗ gọi đi báo"
    assert old.status == STATUS_REVOKED
    assert old.expire_date is not None, "bãi bỏ phải đóng ngày hết hiệu lực, y như nút «Bãi bỏ»"
    assert old.updated_by == NGUOI_BAN_HANH, "cột «người bãi bỏ» phải là người ban hành văn bản mới"

    #  Và hệ quả của nó: người sửa cuối cùng trước đó KHÔNG còn xem được.
    ho_so = _profile("own")
    assert revoke_access.still_visible(old, _user(NGUOI_SUA_CUOI, 4), ho_so) is False
    assert revoke_access.still_visible(old, _user(NGUOI_BAN_HANH, 2), ho_so) is True
