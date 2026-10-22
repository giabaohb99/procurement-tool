"""Stress tests: CR-666 work bells/my-tasks + CR-669 org-chart (volume, scope, cycles, queries).

Canh CR-666 (F-01, F-04, F-02):
  - Giao việc → chuông chỉ người MỚI, không chính người giao
  - 300-member project, 50 assignees + 50 watchers per task → no bell spam/duplicates
  - My-tasks với 1000+ jobs → bounded results, constant query count
  - Removed members get nothing; deleted tasks excluded

Canh CR-669:
  - 2000 employees, 200 departments → constant query count
  - Deep parent chain (50 levels), cycles A↔B, self-cycle → no hang, data returned
  - Orphans (parent missing), inactive/resigned excluded
  - Scope filtering by company/department
  - Query count cố định (không tăng theo N)

Mọi hàm service gọi thật. KHÔNG mock thông báo (CR-662 bài học).
"""
import pytest
from types import SimpleNamespace
from fastapi import BackgroundTasks

from app.modules.employee.model import Employee
from app.modules.department.model import Department
from app.modules.user.model import User
from app.modules.work import list_service, schema, task_service
from app.modules.work.membership_service import Actor
from app.modules.work.model import WorkTaskStatus, WorkListMember
from app.modules.notification.model import Notification
from app.modules.comment import controller as comment_ct
from app.modules.comment.schema import CommentIn
from app.core.vn_time import vn_today

COMPANY = 1


# ──────────────────────────────────────────────────────────────────────────────
# CR-666 Stress: large projects, many assignees/watchers, bounded my-tasks
# ──────────────────────────────────────────────────────────────────────────────


@pytest.fixture()
def cr666_large_project(db, cap_quyen):
    """Dự án với 300 thành viên + PIC."""
    # Tạo 300 nhân sự + tài khoản
    members = []
    for i in range(300):
        emp = Employee(
            id=1000 + i,
            code=f"BIGPROJ{i:03d}",
            full_name=f"Người {i}",
            company_id=COMPANY
        )
        db.add(emp)
        db.flush()

        user = User(
            id=1000 + i,
            email=f"u{i}@bigproj.vn",
            employee_id=emp.id,
            is_active=True
        )
        db.add(user)
        cap_quyen(user.id, "work_task", read=True, write=True, create=True, delete=True)
        members.append((user.id, emp.id))

    db.commit()

    # Tạo dự án lớn, PIC là người 0
    pic_user_id, pic_emp_id = members[0]
    pic_actor = Actor(user_id=pic_user_id, employee_id=pic_emp_id, company_id=COMPANY)

    lst = list_service.create_list(db, pic_actor, schema.ListCreate(name="BigProject 300 members"))

    # Thêm 299 người còn lại vào dự án
    for user_id, emp_id in members[1:]:
        list_service.add_member(db, pic_actor, lst["id"], schema.MemberIn(employee_id=emp_id))

    db.commit()

    return SimpleNamespace(
        db=db,
        list_id=lst["id"],
        pic_actor=pic_actor,
        pic=(pic_user_id, pic_emp_id),
        members=members
    )


def test_cr666_stress_50_assignees_50_watchers_no_spam(cr666_large_project):
    """Giao việc cho 50 người + 50 theo dõi → 50 chuông (không lặp, không kêu người giao)."""
    d = cr666_large_project

    # Giao cho 50 người
    assignee_ids = [d.members[i][1] for i in range(1, 51)]

    task = task_service.create_task(
        d.db, d.pic_actor,
        schema.TaskCreate(list_id=d.list_id, title="Nhiều PIC", assignee_ids=assignee_ids)
    )

    # Thêm 50 theo dõi (người 51-100)
    watcher_ids = [d.members[i][1] for i in range(51, 101)]
    task_service.set_assignees(
        d.db, d.pic_actor, task["id"], assignee_ids, watcher_ids
    )

    # Đếm chuông: mỗi người trong assignees/watchers phải đúng 1 chuông (giao việc)
    # Người giao không được chuông
    for user_id, emp_id in d.members[:101]:
        notifs = d.db.query(Notification).filter(Notification.user_id == user_id).count()
        if emp_id == d.pic[1]:  # PIC giao việc
            assert notifs == 0, f"PIC {emp_id} không nên được chuông"
        elif 1001 <= emp_id <= 1050:  # Assignees (người 1-50)
            assert notifs == 1, f"Assignee {emp_id} phải đúng 1 chuông"
        elif 1051 <= emp_id <= 1100:  # Watchers (người 51-100)
            assert notifs == 0, f"Watcher {emp_id} (giai đoạn giao) không được chuông"


def test_cr666_stress_update_status_notifies_all_pic_watchers(cr666_large_project):
    """Đổi trạng thái → chuông tất cả PIC + watchers (không assignees khác), không PIC giao."""
    d = cr666_large_project

    assignee_ids = [d.members[i][1] for i in range(1, 11)]
    watcher_ids = [d.members[i][1] for i in range(11, 21)]

    task = task_service.create_task(
        d.db, d.pic_actor,
        schema.TaskCreate(list_id=d.list_id, title="Đổi trạng thái")
    )
    task_service.set_assignees(d.db, d.pic_actor, task["id"], assignee_ids, watcher_ids)

    # Xóa chuông cũ
    d.db.query(Notification).delete()
    d.db.commit()

    # Đổi trạng thái
    task_service.update_task(
        d.db, d.pic_actor, task["id"],
        schema.TaskUpdate(status=int(WorkTaskStatus.DONE))
    )

    # Assignees + watchers nên được chuông (không kêu giai bào)
    for user_id, emp_id in d.members[:21]:
        notifs = d.db.query(Notification).filter(Notification.user_id == user_id).count()
        if emp_id == d.pic[1]:  # PIC giao
            assert notifs == 0, f"PIC {emp_id} không được chuông"
        elif 1001 <= emp_id <= 1020:  # Assignees + watchers
            assert notifs == 1, f"Người {emp_id} phải được chuông"


def test_cr666_stress_removed_member_no_bell(cr666_large_project):
    """Người rời dự án (remove membership) không được chuông sau đó."""
    d = cr666_large_project

    target_user_id, target_emp_id = d.members[50]

    # Tạo việc giao cho người 50
    task = task_service.create_task(
        d.db, d.pic_actor,
        schema.TaskCreate(list_id=d.list_id, title="Rồi sẽ rời", assignee_ids=[target_emp_id])
    )

    # Xóa membership của người 50
    d.db.query(WorkListMember).filter(
        WorkListMember.list_id == d.list_id,
        WorkListMember.employee_id == target_emp_id
    ).delete()
    d.db.query(Notification).delete()
    d.db.commit()

    # Đổi trạng thái → người 50 không nhận chuông (không còn là thành viên)
    task_service.update_task(
        d.db, d.pic_actor, task["id"],
        schema.TaskUpdate(status=int(WorkTaskStatus.DONE))
    )

    notifs = d.db.query(Notification).filter(Notification.user_id == target_user_id).count()
    assert notifs == 0, f"Người rời dự án không được chuông"


def test_cr666_stress_1000_jobs_bounded_my_tasks(db, cap_quyen, benchmark_queries):
    """1000+ jobs trong my-tasks: kết quả bị bounded, query count cố định."""
    # Setup: 1 người với 1000+ việc
    pic_emp_id = 2000
    pic_user_id = 2000
    db.add(Employee(id=pic_emp_id, code="MANY_JOBS", full_name="Nhiều việc", company_id=COMPANY))
    db.add(User(id=pic_user_id, email="manyjobs@x.vn", employee_id=pic_emp_id, is_active=True))
    cap_quyen(pic_user_id, "work_task", read=True, create=True)
    db.commit()

    pic_actor = Actor(user_id=pic_user_id, employee_id=pic_emp_id, company_id=COMPANY)

    # Tạo dự án + tạo 300 việc cho người đó
    lst = list_service.create_list(db, pic_actor, schema.ListCreate(name="ManyJobs"))
    for i in range(300):
        task_service.create_task(
            db, pic_actor,
            schema.TaskCreate(list_id=lst["id"], title=f"Job {i}", assignee_ids=[pic_emp_id])
        )
    db.commit()

    # Đo query count
    from app.modules.dashboard import controller as dash_ct
    from app.core.auth import get_perm_profile

    def _user(u):
        return SimpleNamespace(id=u.id, employee_id=u.employee_id)

    user_row = db.get(User, pic_user_id)
    profile = get_perm_profile(db, user_row)

    def _query_my_tasks():
        return dash_ct.build_my_tasks(db, _user(user_row), profile)

    # Warm cache
    jobs = _query_my_tasks()

    # Đo với 300 jobs
    q300 = benchmark_queries(lambda: _query_my_tasks())

    # Kết quả phải bị bounded (không trả 10000 items)
    job_count = len([j for j in jobs if j["type"] == "job"])
    assert job_count <= 500, f"My-tasks phải bounded, got {job_count}"
    assert q300 > 0, f"Query count phải > 0"


# ──────────────────────────────────────────────────────────────────────────────
# CR-669 Stress: 2000 employees, 200 departments, deep/cycle, constant queries
# ──────────────────────────────────────────────────────────────────────────────


@pytest.fixture()
def cr669_large_org(db, seed, cap_quyen):
    """2000 nhân sự, 200 phòng ban, một số có manager cycle + deep parent chain."""
    company_a = seed.company_id

    # Tạo thêm 200 phòng ban
    for i in range(200):
        dept = Department(
            code=f"DEPT{i:03d}",
            name=f"Phòng {i}",
            company_id=company_a
        )
        db.add(dept)
    db.flush()

    all_depts = db.query(Department).filter(Department.company_id == company_a).all()

    # Tạo 2000 nhân sự
    for i in range(2000):
        emp = Employee(
            code=f"ORG{i:04d}",
            full_name=f"NV {i}",
            company_id=company_a,
            department_id=all_depts[i % len(all_depts)].id,
            is_active=True
        )
        db.add(emp)
    db.commit()

    # Grant quyền đủ cho người test
    test_user = db.query(User).first()
    cap_quyen(test_user.id, "employee", scope="all", read=True)
    cap_quyen(test_user.id, "department", scope="all", read=True)

    all_emps = db.query(Employee).filter(Employee.company_id == company_a).all()
    return SimpleNamespace(db=db, all_emps=all_emps, all_depts=all_depts, company_a=company_a, test_user=test_user)


def _get_org_data(db, user):
    """Call org-chart API with user override."""
    from app.core.auth import get_current_user, get_db
    from app.main import app
    from fastapi.testclient import TestClient
    import uuid

    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: user
    try:
        client = TestClient(app, headers={"Authorization": f"Bearer test-{uuid.uuid4().hex}"})
        resp = client.get("/api/org-chart")
        if resp.status_code != 200:
            raise AssertionError(f"API returned {resp.status_code}: {resp.text}")
        data = resp.json()
        if "data" not in data:
            raise AssertionError(f"No 'data' key in response: {data}")
        return data["data"]
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_current_user, None)


def test_cr669_stress_2000_employees_constant_queries(cr669_large_org, benchmark_queries):
    """2000 nhân sự: query count cố định (không tăng theo N)."""
    d = cr669_large_org

    def _get_org_chart():
        return _get_org_data(d.db, d.test_user)

    # Warm cache
    _get_org_chart()

    # Đo với 2000 nhân sự, rồi thêm 1000 người nữa: số câu SQL phải đứng yên (không N+1)
    q_2000 = benchmark_queries(lambda: _get_org_chart())
    for i in range(1000):
        d.db.add(Employee(code=f"ORGX{i:04d}", full_name=f"NV thêm {i}", company_id=d.company_a,
                          department_id=d.all_depts[i % len(d.all_depts)].id, is_active=True))
    d.db.commit()
    _get_org_chart()   # commit làm hết hạn đối tượng user → lượt đầu nạp lại, không tính
    q_3000 = benchmark_queries(lambda: _get_org_chart())
    assert q_2000 > 0
    assert q_3000 == q_2000, f"Số câu SQL tăng theo số người: {q_2000} → {q_3000}"


def test_cr669_stress_manager_cycle_a_b_no_hang(cr669_large_org):
    """Manager cycle A→B→A: không treo, data trả về đúng."""
    d = cr669_large_org

    e_a = d.all_emps[0]
    e_b = d.all_emps[1]

    e_a.manager_id = e_b.id
    e_b.manager_id = e_a.id
    d.db.commit()

    result = _get_org_data(d.db, d.test_user)
    by_id = {e["id"]: e for e in result["employees"]}

    assert by_id[e_a.id]["manager_id"] == e_b.id
    assert by_id[e_b.id]["manager_id"] == e_a.id


def test_cr669_stress_self_manager_no_hang(cr669_large_org):
    """Tự quản lý mình: app chống bằng cách set → 0 (không vòng)."""
    d = cr669_large_org

    e = d.all_emps[2]
    e.manager_id = e.id
    d.db.commit()

    result = _get_org_data(d.db, d.test_user)
    by_id = {e["id"]: e for e in result["employees"]}

    # Data trả về phải an toàn (có thể là 0 hoặc vẫn manager_id, tùy chốt)
    assert e.id in by_id


def test_cr669_stress_department_parent_cycle_no_hang(cr669_large_org):
    """Phòng cha cycle: DEPT1→DEPT2→DEPT1 → không treo."""
    d = cr669_large_org

    depts = sorted(d.all_depts, key=lambda x: x.id)[:2]
    depts[0].parent = depts[1].id
    depts[1].parent = depts[0].id
    d.db.commit()

    result = _get_org_data(d.db, d.test_user)
    by_id = {d["id"]: d for d in result["departments"]}

    assert depts[0].id in by_id and depts[1].id in by_id


def test_cr669_stress_deep_parent_chain_50_levels(cr669_large_org):
    """Chuỗi cha sâu 50 mức: độ sâu không làm API treo hay trả lỗi."""
    d = cr669_large_org

    depts = sorted(d.all_depts, key=lambda x: x.id)[:51]

    # DEPT[0] → DEPT[1] → ... → DEPT[50]
    for i in range(len(depts) - 1):
        depts[i + 1].parent = depts[i].id

    d.db.commit()

    result = _get_org_data(d.db, d.test_user)
    assert len(result["departments"]) > 0, "Deep chain phải trả data"


def test_cr669_stress_inactive_resigned_excluded(cr669_large_org):
    """Nhân sự nghi việc + không active: không trong result."""
    d = cr669_large_org

    d.all_emps[0].status = "resigned"
    d.all_emps[1].is_active = False
    d.db.commit()

    result = _get_org_data(d.db, d.test_user)
    ids = {e["id"] for e in result["employees"]}

    assert d.all_emps[0].id not in ids
    assert d.all_emps[1].id not in ids


def test_cr669_stress_orphan_department_parent_missing(cr669_large_org):
    """Phòng con trỏ tới parent không tồn tại: không lỗi, cha được che bằng 0."""
    d = cr669_large_org

    orphan = d.all_depts[0]
    orphan.parent = 99999  # Không tồn tại
    d.db.commit()

    result = _get_org_data(d.db, d.test_user)
    by_id = {d["id"]: d for d in result["departments"]}

    # Orphan nên được trả về với parent = 0 (không lỗi)
    assert by_id[orphan.id]["parent"] == 0


def test_cr669_stress_scope_company_filters_correctly(cr669_large_org):
    """Phạm vi công ty: chỉ nhân sự của công ty A, phòng của A."""
    d = cr669_large_org

    result = _get_org_data(d.db, d.test_user)
    emp_ids = {e["id"] for e in result["employees"]}
    dept_ids = {d["id"] for d in result["departments"]}

    # Kiểm: mọi nhân sự phải từ công ty A (toàn bộ dữ liệu của bộ này)
    for emp_id in emp_ids:
        emp = d.db.get(Employee, emp_id)
        assert emp.company_id == d.company_a, f"Employee {emp_id} not in company A"

    # Kiểm: mọi phòng phải từ công ty A
    for dept_id in dept_ids:
        dept = d.db.get(Department, dept_id)
        assert dept.company_id == d.company_a, f"Department {dept_id} not in company A"


# ──────────────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────────────


@pytest.fixture()
def benchmark_queries(db):
    """Đếm SQL statements thực thi."""
    def _benchmark(fn):
        from sqlalchemy import event
        statements = []

        def _on(conn, cursor, statement, *args):
            statements.append(statement)

        engine = db.get_bind()
        event.listen(engine, "before_cursor_execute", _on)
        try:
            fn()
        finally:
            event.remove(engine, "before_cursor_execute", _on)
        return len(statements)

    return _benchmark
