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


def _nhan_su_khong_co_quyen(db, seed, ma: str):
    """Một người có tài khoản nhưng KHÔNG được cấp vai trò nào — đúng như
    `DEMO_MANAGER` trên dữ liệu thật, người đang gánh bước 1 của mọi luồng mẫu."""
    employee = Employee(code=ma, full_name=f"Người duyệt {ma}", company_id=seed.company_id,
                        department_id=seed.dept_id, is_active=True)
    db.add(employee)
    db.flush()
    user = User(email=f"{ma.lower()}@test.local", employee_id=employee.id,
                password_hash="x", is_active=True)
    db.add(user)
    db.flush()
    return employee, user


@pytest.fixture()
def canh(db, seed):
    doc_type = DocType(code="QC", name="Quy chế", id_scheme=1, number_when=2)
    db.add(doc_type)
    db.flush()

    nguoi_duyet, tk_duyet = _nhan_su_khong_co_quyen(db, seed, "DUYET")
    nguoi_la, tk_la = _nhan_su_khong_co_quyen(db, seed, "NGUOILA")

    db.add(ApprovalSwitch(entity=ENTITY, is_enabled=True, created_by=ACTOR, updated_by=ACTOR))
    flow = ApprovalFlow(entity=ENTITY, code="VB-01", name="Duyệt quy chế",
                        is_active=True, created_by=ACTOR, updated_by=ACTOR)
    db.add(flow)
    db.flush()
    db.add(ApprovalNode(flow_id=flow.id, seq=1, name="Trưởng bộ phận duyệt",
                        approver_kind=APPROVER_EMPLOYEE, approver_ref=str(nguoi_duyet.id),
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


def test_nguoi_dang_giu_viec_doc_duoc_van_ban(db, canh):
    assert _doc_duoc(db, canh["doc"], canh["tk_duyet"]) is True


def test_nguoi_khong_lien_quan_van_khong_doc_duoc(db, canh):
    """Ngoại lệ mở đúng một khe, không mở toang cửa cho mọi người đăng nhập."""
    assert _doc_duoc(db, canh["doc"], canh["tk_la"]) is False
    with pytest.raises(HTTPException) as loi:
        access_service.ensure_can(db, canh["doc"], canh["tk_la"],
                                  get_perm_profile(db, canh["tk_la"]), "read")
    assert loi.value.status_code == 404


def test_ky_xong_roi_van_mo_lai_duoc(db, canh):
    """Chữ ký vào một tờ giấy không xem lại được thì là chữ ký mù ở thì quá khứ."""
    from app.modules.approval import action_service, instance_service

    phien = instance_service.phien_dang_chay(db, ENTITY, canh["doc"].id)
    action_service.duyet(db, phien, canh["tk_duyet"].employee_id, ACTOR, {})

    assert _doc_duoc(db, canh["doc"], canh["tk_duyet"]) is True


def test_nguoi_duyet_KHONG_duoc_sua_hay_ban_hanh(db, canh):
    """Việc của người duyệt là xem xét rồi ký, không phải sửa bài người khác."""
    for hanh_dong in ("write", "delete"):
        assert _doc_duoc(db, canh["doc"], canh["tk_duyet"]) is True   # đọc thì được
        assert access_service.can(db, canh["doc"], canh["tk_duyet"],
                                  get_perm_profile(db, canh["tk_duyet"]),
                                  hanh_dong) is False, hanh_dong


def test_van_ban_khac_thi_khong_theo_lay(db, canh, seed):
    """Có việc ở phiếu A không mở được phiếu B."""
    doc_type = db.query(DocType).first()
    khac = service.create_document(db, DocumentCreate(
        doc_type_id=doc_type.id, company_id=seed.company_id, department_id=seed.dept_id,
        owner_employee_id=seed.emp_req_id, title="Quy chế khác hẳn",
        content_html="<p>Nội dung.</p>",
    ), ACTOR)

    assert _doc_duoc(db, khac, canh["tk_duyet"]) is False
