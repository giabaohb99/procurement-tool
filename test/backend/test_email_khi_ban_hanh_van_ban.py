"""Email ban hành dùng đúng phạm vi và dẫn vào màn chỉ đọc."""
from datetime import date

import pytest

from app.modules.company.model import Company
from app.modules.department.model import Department
from app.modules.doc_catalog.model import DocType
from app.modules.document import access_service, issue_notification, service
from app.modules.document.access_model import (EFFECT_DENY, SUBJECT_EMPLOYEE,
                                                DocumentAccess)
from app.modules.document.model import STATUS_EFFECTIVE, Document
from app.modules.document.scope_model import (DIM_COMPANY, DIM_DEPARTMENT,
                                              DIM_EMPLOYEE, MODE_EXCLUDE,
                                              MODE_INCLUDE, DocumentScope)
from app.modules.document.version_model import VERSION_APPROVED, DocumentVersion
from app.modules.document.schema import DocumentCreate
from app.modules.employee.model import Employee
from app.modules.notification.model import EmailLog, Notification
from app.modules.notification.tasks import send_email_task
from app.modules.user.model import User


@pytest.fixture()
def du_lieu(db, monkeypatch):
    company = Company(code="MAIL-A", name="Pháp nhân A", issue_code="A", is_active=True)
    other_company = Company(code="MAIL-B", name="Pháp nhân B", issue_code="B", is_active=True)
    db.add_all([company, other_company])
    db.flush()
    excluded_department = Department(
        code="MAIL-PB-1", name="Phòng bị loại", company_id=company.id, is_active=True)
    other_department = Department(
        code="MAIL-PB-2", name="Phòng còn lại", company_id=company.id, is_active=True)
    foreign_department = Department(
        code="MAIL-PB-3", name="Phòng pháp nhân B", company_id=other_company.id, is_active=True)
    doc_type = DocType(code="MAIL", name="Thông báo nội bộ", id_scheme=2, number_when=2)
    db.add_all([excluded_department, other_department, foreign_department, doc_type])
    db.flush()

    specs = [
        ("MAIL-NV-1", "Người ngoại lệ", company.id, excluded_department.id),
        ("MAIL-NV-2", "Người cùng phòng", company.id, excluded_department.id),
        ("MAIL-NV-3", "Người phòng khác", company.id, other_department.id),
        ("MAIL-NV-4", "Người pháp nhân B", other_company.id, foreign_department.id),
    ]
    employees = []
    users = []
    for index, (code, full_name, company_id, department_id) in enumerate(specs, 1):
        employee = Employee(
            code=code,
            full_name=full_name,
            email=f"member{index}@example.test",
            company_id=company_id,
            department_id=department_id,
            is_active=True,
        )
        db.add(employee)
        db.flush()
        user = User(
            email=code,
            employee_id=employee.id,
            password_hash="x",
            is_active=True,
        )
        db.add(user)
        employees.append(employee)
        users.append(user)

    db.flush()
    doc = Document(
        doc_type_id=doc_type.id,
        company_id=company.id,
        department_id=other_department.id,
        owner_employee_id=employees[2].id,
        title="Quy định thử email ban hành",
        summary="Nội dung tóm tắt để người nhận nhận biết văn bản.",
        issue_number="01/2026/TB-A",
        status=STATUS_EFFECTIVE,
        effective_date=date(2026, 8, 21),
    )
    db.add(doc)
    db.flush()
    version = DocumentVersion(
        document_id=doc.id,
        major=1,
        minor=0,
        status=VERSION_APPROVED,
        is_locked=True,
        effective_from=date(2026, 8, 21),
        content_html="<p>Nội dung</p>",
    )
    db.add(version)
    db.commit()

    queued = []
    monkeypatch.setattr(send_email_task, "delay", lambda *args: queued.append(args))
    return {
        "company": company,
        "excluded_department": excluded_department,
        "employees": employees,
        "users": users,
        "doc": doc,
        "version": version,
        "queued": queued,
    }


def _scope(db, doc, *, dim, mode, company_id=None, department_id=None, employee_id=None):
    db.add(DocumentScope(
        document_id=doc.id,
        dim=dim,
        mode=mode,
        company_id=company_id,
        department_id=department_id,
        employee_id=employee_id,
    ))


@pytest.mark.parametrize(
    ("case", "expected_indexes"),
    [
        pytest.param("mac_dinh_phap_nhan", [0, 1, 2], id="mac-dinh-cung-phap-nhan"),
        pytest.param("loai_ca_nhan", [1, 2], id="loai-mot-thanh-vien"),
        pytest.param("loai_phong", [2], id="loai-mot-phong-ban"),
        pytest.param("cho_lai_ca_nhan", [0, 2], id="loai-phong-cho-lai-mot-nguoi"),
    ],
)
def test_gui_chuong_va_email_dung_pham_vi(db, du_lieu, case, expected_indexes):
    company = du_lieu["company"]
    department = du_lieu["excluded_department"]
    employees = du_lieu["employees"]
    doc = du_lieu["doc"]

    if case != "mac_dinh_phap_nhan":
        _scope(db, doc, dim=DIM_COMPANY, mode=MODE_INCLUDE, company_id=company.id)
    if case == "loai_ca_nhan":
        _scope(db, doc, dim=DIM_EMPLOYEE, mode=MODE_EXCLUDE, employee_id=employees[0].id)
    if case in {"loai_phong", "cho_lai_ca_nhan"}:
        _scope(
            db,
            doc,
            dim=DIM_DEPARTMENT,
            mode=MODE_EXCLUDE,
            company_id=company.id,
            department_id=department.id,
        )
    if case == "cho_lai_ca_nhan":
        _scope(db, doc, dim=DIM_EMPLOYEE, mode=MODE_INCLUDE, employee_id=employees[0].id)
    db.commit()

    count = issue_notification.notify_document_issued(
        db, doc, du_lieu["version"], actor=du_lieu["users"][2].id)

    expected_user_ids = {du_lieu["users"][index].id for index in expected_indexes}
    notices = db.query(Notification).filter(Notification.title.like("[Văn bản mới]%")).all()
    logs = db.query(EmailLog).filter(EmailLog.event == "document_issued").all()
    assert count == len(expected_indexes)
    assert {row.user_id for row in notices} == expected_user_ids
    assert {row.to_email for row in logs} == {
        du_lieu["employees"][index].email for index in expected_indexes
    }
    assert len(du_lieu["queued"]) == len(expected_indexes)
    assert all(row.link == f"/document/documents/{doc.id}?readonly=1" for row in notices)
    assert all("?readonly=1" in args[3] for args in du_lieu["queued"])
    assert all("XEM VĂN BẢN (CHỈ ĐỌC)" in args[3] for args in du_lieu["queued"])
    assert all("Pháp nhân A" in args[3] for args in du_lieu["queued"])


def test_nguoi_thuoc_pham_vi_duoc_doc_nhung_khong_duoc_sua(db, du_lieu):
    user = du_lieu["users"][0]
    employee = du_lieu["employees"][0]
    doc = du_lieu["doc"]
    profile = {"employee_id": employee.id, "company_id": 0, "dept_id": 0, "grants": []}

    assert access_service.can(db, doc, user, profile, "read") is True
    assert access_service.can(db, doc, user, profile, "write") is False

    # Cấm đích danh vẫn thắng quyền đọc sinh từ phạm vi áp dụng.
    db.add(DocumentAccess(
        document_id=doc.id,
        subject_kind=SUBJECT_EMPLOYEE,
        subject_id=employee.id,
        effect=EFFECT_DENY,
        can_read=True,
    ))
    db.commit()
    assert access_service.can(db, doc, user, profile, "read") is False


def test_loi_hang_doi_khong_lam_hong_thong_bao(db, du_lieu, monkeypatch):
    def queue_failed(*_args):
        raise RuntimeError("Redis tạm ngắt")

    monkeypatch.setattr(send_email_task, "delay", queue_failed)
    count = issue_notification.notify_document_issued(
        db, du_lieu["doc"], du_lieu["version"], actor=du_lieu["users"][2].id)

    assert count == 3
    assert db.query(Notification).count() == 3
    logs = db.query(EmailLog).filter(EmailLog.event == "document_issued").all()
    assert len(logs) == 3
    assert all(row.status == "failed" for row in logs)
    assert all("Redis tạm ngắt" in row.error for row in logs)


def test_trich_yeu_dai_khong_lam_tran_tieu_de_thong_bao(db, du_lieu):
    du_lieu["doc"].title = "Văn bản có trích yếu dài " + ("x" * 500)
    db.commit()

    issue_notification.notify_document_issued(
        db, du_lieu["doc"], du_lieu["version"], actor=du_lieu["users"][2].id)

    assert all(len(row.title) <= 255 for row in db.query(Notification).all())
    assert all(len(row.subject) <= 255 for row in db.query(EmailLog).all())


def test_ban_hanh_goi_thong_bao_sau_khi_chot_phien_ban(db, seed, monkeypatch):
    doc_type = DocType(
        code="MAIL-HOOK", name="Thông báo hook", id_scheme=2, number_when=2)
    db.add(doc_type)
    db.commit()
    doc = service.create_document(db, DocumentCreate(
        doc_type_id=doc_type.id,
        company_id=seed.company_id,
        department_id=seed.dept_id,
        owner_employee_id=seed.emp_nstm_id,
        title="Văn bản kiểm tra hook email",
        content_html="<p>Nội dung đã hoàn tất.</p>",
    ), seed.u_nstm_id)
    service.submit(db, doc, seed.u_nstm_id)

    calls = []

    def capture(_db, issued_doc, issued_version, actor):
        calls.append((issued_doc.status, issued_version.status, issued_version.is_locked, actor))
        return 0

    monkeypatch.setattr(issue_notification, "notify_document_issued", capture)
    service.approve(db, doc, seed.u_nstm_id)

    assert calls == [(STATUS_EFFECTIVE, VERSION_APPROVED, True, seed.u_nstm_id)]


def test_loi_tao_email_khong_lam_that_bai_viec_ban_hanh(db, seed, monkeypatch):
    doc_type = DocType(
        code="MAIL-SAFE", name="Thông báo an toàn", id_scheme=2, number_when=2)
    db.add(doc_type)
    db.commit()
    doc = service.create_document(db, DocumentCreate(
        doc_type_id=doc_type.id,
        company_id=seed.company_id,
        department_id=seed.dept_id,
        owner_employee_id=seed.emp_nstm_id,
        title="Văn bản vẫn ban hành khi kênh mail lỗi",
        content_html="<p>Nội dung đã hoàn tất.</p>",
    ), seed.u_nstm_id)
    service.submit(db, doc, seed.u_nstm_id)

    def fail(*_args):
        raise RuntimeError("Kênh email tạm lỗi")

    monkeypatch.setattr(issue_notification, "notify_document_issued", fail)
    issued = service.approve(db, doc, seed.u_nstm_id)

    assert issued.status == STATUS_EFFECTIVE
    assert db.get(Document, doc.id).status == STATUS_EFFECTIVE
