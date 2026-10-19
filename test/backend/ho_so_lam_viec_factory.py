"""Khung dựng dữ liệu cho bài kiểm Hồ sơ cách làm việc (duoc-CR-641) — không phải bài kiểm (tên không bắt đầu `test_`).

Mốc cố định: 05/01/2026 là thứ Hai. Giờ trong DB là UTC naive; VN = UTC+7, nên `vn(day, "09:30")` đổi giờ VN → UTC.
"""
import uuid
from datetime import date, datetime, time, timedelta

from app.core.logging_codes import ACTOR_KIND_USER, SOURCE_API
from app.modules.audit.model import AuditLog
from app.modules.company.model import Company
from app.modules.department.model import Department
from app.modules.employee.model import Employee
from app.modules.login_session.model import LoginSession
from app.modules.request_log.model import RequestLog
from app.modules.user.model import User
from app.modules.usage_profile.model import UiEvent

MON = date(2026, 1, 5)    # thứ Hai
TUE = date(2026, 1, 6)
SAT = date(2026, 1, 10)
SUN = date(2026, 1, 11)
VN = timedelta(hours=7)


def vn(day: date, hhmm: str) -> datetime:
    """Giờ VN `hhmm` của `day` → UTC naive (kiểu lưu DB)."""
    h, m = (int(x) for x in hhmm.split(":"))
    return datetime.combine(day, time(h, m)) - VN


def make_company(db, code="C1") -> Company:
    c = Company(name=f"Cty {code}", code=code, is_active=True)
    db.add(c)
    db.flush()
    return c


def make_dept(db, company, code="D1") -> Department:
    d = Department(code=code, name=f"Phòng {code}", company_id=company.id, is_active=True)
    db.add(d)
    db.flush()
    return d


def make_person(db, code: str, company=None, dept=None, hire: date | None = None, status="official",
                resign: date | None = None, active=True):
    """Nhân sự + tài khoản. Trả (user, employee)."""
    emp = Employee(code=code, full_name=f"Người {code}", is_active=True, status=status, hire_date=hire,
                   resign_date=resign, company_id=company.id if company else 0,
                   department_id=dept.id if dept else 0)
    db.add(emp)
    db.flush()
    user = User(email=f"{code.lower()}@test.vn", employee_id=emp.id, password_hash="x", is_active=active)
    db.add(user)
    db.flush()
    return user, emp


def make_session(db, user, created: datetime, device_type=1, ip="1.1.1.1", os_="Windows", browser="Chrome") -> LoginSession:
    s = LoginSession(user_id=user.id, token_id=uuid.uuid4().hex[:32], ip=ip, device_type=device_type,
                     os=os_, browser=browser, created_at=created)
    db.add(s)
    db.flush()
    return s


def add_request(db, user, at: datetime, method="GET", route="/api/x", status=200, session=None, referer="",
                ip="1.1.1.1") -> RequestLog:
    r = RequestLog(request_id=uuid.uuid4().bytes, source=SOURCE_API, created_at=at, user_id=user.id,
                   session_id=session.id if session else None, ip=ip, method=method, path=route, route=route,
                   http_status=status, referer=referer)
    db.add(r)
    return r


def add_audit(db, user, at: datetime, entity: str, entity_id: int, action: str, group=2, session=None) -> AuditLog:
    a = AuditLog(entity=entity, entity_id=entity_id, action=action, message="", actor_kind=ACTOR_KIND_USER,
                 session_id=session.id if session else None, action_group=group, created_by=user.id,
                 created_at=at)
    db.add(a)
    return a


def add_ui(db, user, at: datetime, etype: int, route="/a", form=0, duration=0, result=None, tab=1, session_id=None):
    e = UiEvent(created_at=at, occurred_at=at, user_id=user.id, session_id=session_id, tab_key=tab,
                event_type=etype, route_pattern=route, form_key=form, duration_ms=duration, result_count=result)
    db.add(e)
    return e
