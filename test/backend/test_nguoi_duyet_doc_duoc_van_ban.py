"""NGƯỜI DUYỆT PHẢI ĐỌC ĐƯỢC THỨ MÌNH KÝ.

Lỗi thật, bắt được trên trình duyệt ngày 18/08/2026: trưởng bộ phận mở «Việc của
tôi», thấy dòng việc, bấm sang văn bản — nhận **404 Không tìm thấy văn bản**. Họ
chỉ còn cái tiêu đề trên dòng việc để mà ký. Nguyên nhân: người duyệt trong luồng
thường không có vai trò nào ở phân hệ Văn bản, mà bộ máy duyệt lại chỉ hỏi "anh
có việc ở phiếu này không" — hai hệ hỏi hai câu khác nhau về cùng một người.

Ranh giới của ngoại lệ này quan trọng ngang bản thân nó: **chỉ mở quyền ĐỌC**, và
chỉ cho người thật sự có chân trong phiên duyệt của đúng văn bản đó.
"""
import pytest

from app.core.auth import get_perm_profile
from app.modules.approval.flow_model import (APPROVER_EMPLOYEE, SKIP_NONE,
                                             ApprovalFlow, ApprovalNode,
                                             ApprovalSwitch)
from app.modules.doc_catalog.model import DocType
from app.modules.document import access_service, service
from app.modules.document.schema import DocumentCreate
from app.modules.employee.model import Employee
from app.modules.user.model import User
from fastapi import HTTPException

ACTOR = 1
ENTITY = "document"


def _nhan_su_khong_co_quyen(db, seed, code: str):
    """Một người có tài khoản nhưng KHÔNG được cấp vai trò nào — đúng như
    `DEMO_MANAGER` trên dữ liệu thật, người đang gánh bước 1 của mọi luồng mẫu."""
    employee = Employee(code=code, full_name=f"Người duyệt {code}", company_id=seed.company_id,
                        department_id=seed.dept_id, is_active=True)
    db.add(employee)
    db.flush()
    user = User(email=f"{code.lower()}@test.local", employee_id=employee.id,
                password_hash="x", is_active=True)
    db.add(user)
    db.flush()
    return employee, user


@pytest.fixture()
def align(db, seed):
    doc_type = DocType(code="QC", name="Quy chế", id_scheme=1, number_when=2)
    db.add(doc_type)
    db.flush()

    approvers, tk_duyet = _nhan_su_khong_co_quyen(db, seed, "DUYET")
    nguoi_la, tk_la = _nhan_su_khong_co_quyen(db, seed, "NGUOILA")

    db.add(ApprovalSwitch(entity=ENTITY, is_enabled=True, created_by=ACTOR, updated_by=ACTOR))
    flow = ApprovalFlow(entity=ENTITY, code="VB-01", name="Duyệt quy chế",
                        is_active=True, created_by=ACTOR, updated_by=ACTOR)
    db.add(flow)
    db.flush()
    db.add(ApprovalNode(flow_id=flow.id, seq=1, name="Trưởng bộ phận duyệt",
                        approver_kind=APPROVER_EMPLOYEE, approver_ref=str(approvers.id),
                        skip_duplicate=SKIP_NONE, created_by=ACTOR, updated_by=ACTOR))
    db.commit()

    doc = service.create_document(db, DocumentCreate(
        doc_type_id=doc_type.id, company_id=seed.company_id, department_id=seed.dept_id,
        owner_employee_id=seed.emp_req_id, title="Quy chế bảo mật thông tin",
        content_html="<p>Điều 1. Nội dung.</p>",
    ), ACTOR)
    doc = service.submit(db, doc, ACTOR)
    return {"doc": doc, "tk_duyet": tk_duyet, "tk_la": tk_la}


def _doc_duoc(db, doc, user) -> bool:
    return access_service.can(db, doc, user, get_perm_profile(db, user), "read")


def test_nguoi_dang_giu_viec_doc_duoc_van_ban(db, align):
    assert _doc_duoc(db, align["doc"], align["tk_duyet"]) is True


def test_nguoi_khong_lien_quan_van_khong_doc_duoc(db, align):
    """Ngoại lệ mở đúng một khe, không mở toang cửa cho mọi người đăng nhập."""
    assert _doc_duoc(db, align["doc"], align["tk_la"]) is False
    with pytest.raises(HTTPException) as error:
        access_service.ensure_can(db, align["doc"], align["tk_la"],
                                  get_perm_profile(db, align["tk_la"]), "read")
    assert error.value.status_code == 404


def test_ky_xong_roi_van_mo_lai_duoc(db, align):
    """Chữ ký vào một tờ giấy không xem lại được thì là chữ ký mù ở thì quá khứ."""
    from app.modules.approval import action_service, instance_service

    instance = instance_service.running_instance(db, ENTITY, align["doc"].id)
    action_service.approve(db, instance, align["tk_duyet"].employee_id, ACTOR, {})

    assert _doc_duoc(db, align["doc"], align["tk_duyet"]) is True


def test_nguoi_duyet_KHONG_duoc_sua_hay_ban_hanh(db, align):
    """Việc của người duyệt là xem xét rồi ký, không phải sửa bài người khác."""
    for action in ("write", "delete"):
        assert _doc_duoc(db, align["doc"], align["tk_duyet"]) is True   # đọc thì được
        assert access_service.can(db, align["doc"], align["tk_duyet"],
                                  get_perm_profile(db, align["tk_duyet"]),
                                  action) is False, action


def test_van_ban_khac_thi_khong_theo_lay(db, align, seed):
    """Có việc ở phiếu A không mở được phiếu B."""
    doc_type = db.query(DocType).first()
    other = service.create_document(db, DocumentCreate(
        doc_type_id=doc_type.id, company_id=seed.company_id, department_id=seed.dept_id,
        owner_employee_id=seed.emp_req_id, title="Quy chế khác hẳn",
        content_html="<p>Nội dung.</p>",
    ), ACTOR)

    assert _doc_duoc(db, other, align["tk_duyet"]) is False


# ── Chiều ngược: KHÔNG đọc được văn bản thì cũng không đọc được PHIẾU của nó ──

def test_nguoi_la_khong_doc_duoc_phien_duyet_va_khong_ghi_duoc_y_kien(db, align):
    """Lỗ bắt được 25/08/2026 khi chịu tải bốn nút của hộp «Duyệt / Trả lại».

    Văn thư pháp nhân khác mở `/api/documents/507` ăn **404**, nhưng
    `/api/approvals/of/document/507` trả **200** kèm tên văn bản, tên luồng, tên
    người đang duyệt — và `/comment` cho họ ghi thẳng vào dấu vết phiếu, thứ sẽ
    nằm trên bản in phê duyệt.

    Bộ máy duyệt cố ý không biết đọc bảng văn bản, nên nó hỏi ngược qua
    `entity_hooks.doc_duoc` — hàm mà module Văn bản tự khai.
    """
    from app.modules.approval import entity_hooks, instance_service

    instance = instance_service.running_instance(db, ENTITY, align["doc"].id)

    assert entity_hooks.can_read(db, instance, align["tk_duyet"]) is True
    assert entity_hooks.can_read(db, instance, align["tk_la"]) is False


def test_loai_chung_tu_chua_khai_ham_kiem_thi_khong_bi_khoa_oan(db, align):
    """Siết ở bộ máy duyệt không được lặng lẽ khóa phiếu của phân hệ khác.

    Thu mua chưa khai hàm kiểm quyền đọc, nên phiếu của nó phải chạy y như cũ.
    """
    from app.modules.approval import entity_hooks, instance_service

    instance = instance_service.running_instance(db, ENTITY, align["doc"].id)
    instance.entity = "purchase_request"      # loại chưa khai `_READERS`

    assert entity_hooks.can_read(db, instance, align["tk_la"]) is True


def test_khong_ghi_duoc_y_kien_vao_phien_DA_KET_THUC(db, align):
    """Ý kiến nằm chung bảng với quyết định và đi thẳng lên bản in dấu vết —
    cho ghi tiếp sau khi phiếu đóng nghĩa là tờ giấy đã ký vẫn dài thêm được."""
    from app.modules.approval import action_service, instance_service

    instance = instance_service.running_instance(db, ENTITY, align["doc"].id)
    action_service.give_comment(db, instance, align["tk_duyet"].employee_id, ACTOR, "Còn mở thì ghi được")

    action_service.approve(db, instance, align["tk_duyet"].employee_id, ACTOR, {})

    with pytest.raises(HTTPException) as error:
        action_service.give_comment(db, instance, align["tk_duyet"].employee_id, ACTOR, "Ghi thêm sau khi đóng")
    assert error.value.status_code == 400
