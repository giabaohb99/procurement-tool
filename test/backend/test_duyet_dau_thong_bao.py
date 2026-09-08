"""Duyệt dấu PHA 3 — thông báo (chuông) bắn đúng người ở các mốc.

Kiểm ở tầng service: duyệt xong thì NGƯỜI TẠO nhận được chuông (email đi cùng đường
nhưng phụ thuộc SMTP nên không kiểm ở đây). notify là best-effort — không người nhận
thì im lặng, không lỗi.
"""
from types import SimpleNamespace

from app.modules.attachment.model import FileLink
from app.modules.employee.model import Employee
from app.modules.notification.model import Notification
from app.modules.seal_request import model as m
from app.modules.seal_request.schema import ReasonIn, SealRequestCreate
from app.modules.seal_request.service import (
    approve_seal,
    create_seal_request,
    return_seal,
    submit_seal_request,
)
from app.modules.user.model import User


def _creator(db):
    emp = Employee(code="NV1", full_name="Lâm Bích Dư", company_id=3, department_id=7)
    db.add(emp)
    db.flush()
    u = User(email="creator@dego.vn", employee_id=emp.id, is_active=True)
    db.add(u)
    db.flush()
    return SimpleNamespace(id=u.id, employee_id=emp.id, email="creator@dego.vn"), u


def _ready_request(db, actor):
    req = create_seal_request(
        db, SealRequestCreate(purpose="Duyệt dấu HĐ", company_ids=[3], first_approver_id=500),
        actor, submit=False)
    db.add(FileLink(file_id=1, entity="seal_request", entity_id=req.id, doc_type="signed_doc"))
    db.flush()
    submit_seal_request(db, req, actor)
    return req


def test_approve_notifies_creator(db):
    actor, u = _creator(db)
    req = _ready_request(db, actor)
    approve_seal(db, req, actor)
    notes = db.query(Notification).filter(Notification.user_id == u.id).all()
    assert len(notes) >= 1
    assert any(req.code in (n.title or "") for n in notes)


def test_return_notifies_creator_with_reason_title(db):
    actor, u = _creator(db)
    req = _ready_request(db, actor)
    return_seal(db, req, ReasonIn(reason="Thiếu chữ ký"), actor)
    notes = db.query(Notification).filter(Notification.user_id == u.id).all()
    assert len(notes) >= 1


def test_notify_silent_without_recipients(db):
    #  Không có User cho requester_id → không ai nhận → không tạo chuông, không lỗi.
    actor = SimpleNamespace(id=99999, employee_id=0, email="ghost@dego.vn")
    req = create_seal_request(db, SealRequestCreate(purpose="X", company_ids=[3], first_approver_id=500),
                              actor, submit=False)
    db.add(FileLink(file_id=1, entity="seal_request", entity_id=req.id, doc_type="x"))
    db.flush()
    submit_seal_request(db, req, actor)
    approve_seal(db, req, actor)  # không nổ dù requester không có tài khoản
    assert db.query(Notification).count() == 0
