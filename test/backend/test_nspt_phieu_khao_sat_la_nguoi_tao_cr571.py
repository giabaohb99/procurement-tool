"""bao-CR-571 — «NSPT phụ trách (người tạo)» của phiếu khảo sát là NGƯỜI TẠO, backend tự gán.

Lỗi có thật 02/10/2026: nháp F5 của màn tạo phiếu lưu chung trên trình duyệt, tài khoản Quyên
mở «Tạo phiếu» nạp nguyên nháp của chị Phương — và backend lưu đúng cái tên giao diện gửi lên.
"""
from app.modules.employee.model import Employee
from app.modules.survey import service as sv_service
from app.modules.survey.schema import SurveyCreate
from app.modules.user.model import User


def _account(db, code, name, email):
    emp = Employee(code=code, full_name=name, email=email)
    db.add(emp)
    db.flush()
    user = User(email=email, employee_id=emp.id, password_hash="x", is_active=True)
    db.add(user)
    db.commit()
    return user


def test_create_ignores_nspt_sent_by_the_form(db):
    quyen = _account(db, "NSU222", "Trần Nguyễn Phương Quyên", "quyen@x.vn")
    s = sv_service.create_survey(db, SurveyCreate(main_content="NCC vận chuyển", nspt="Trần Diễm Phương"), quyen.id)
    assert s.nspt == "Trần Nguyễn Phương Quyên"
    assert s.created_by == quyen.id


def test_create_fills_nspt_when_form_sends_nothing(db):
    quyen = _account(db, "NSU222", "Trần Nguyễn Phương Quyên", "quyen@x.vn")
    s = sv_service.create_survey(db, SurveyCreate(main_content="x"), quyen.id)
    assert s.nspt == "Trần Nguyễn Phương Quyên"


def test_account_without_employee_profile_falls_back_to_email(db):
    user = User(email="khong.ho.so@x.vn", employee_id=0, password_hash="x", is_active=True)
    db.add(user)
    db.commit()
    s = sv_service.create_survey(db, SurveyCreate(main_content="x", nspt="Người khác"), user.id)
    assert s.nspt == "khong.ho.so@x.vn"


def test_unknown_creator_keeps_whatever_was_sent(db):
    #  Tài khoản không tồn tại (đường gọi nội bộ, user_id = 0): không có ai để gán, giữ nguyên.
    s = sv_service.create_survey(db, SurveyCreate(main_content="x", nspt="Nhập tay"), 0)
    assert s.nspt == "Nhập tay"


def test_copy_belongs_to_whoever_copies_it(db):
    phuong = _account(db, "NSU012", "Trần Diễm Phương", "phuong@x.vn")
    quyen = _account(db, "NSU222", "Trần Nguyễn Phương Quyên", "quyen@x.vn")
    src = sv_service.create_survey(db, SurveyCreate(main_content="Bao bì"), phuong.id)
    copy = sv_service.copy_survey(db, src.id, quyen.id)
    assert src.nspt == "Trần Diễm Phương"
    assert copy.nspt == "Trần Nguyễn Phương Quyên"
    assert copy.main_content == "Bao bì"
