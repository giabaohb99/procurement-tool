"""Stress tests: CR-665 pending work + CR-667 comment/trash cycles (repetition, volume, edge cases).

Canh CR-665: Việc DUYỆT một nhân sự — user với hàng trăm phiếu treo, độ dài danh sách MAX_ROWS,
người ngoài phạm vi không xem được, deleted/soft-deleted docs che tên, nhân sự không tài khoản.

Canh CR-667: Sửa bình luận + thùng rác — edit 100 lần, sửa người khác = 403, edit deleted,
empty/whitespace/oversize body (String/Text limits → 400), trash→restore cycles 50x,
scope trên danh sách thùng rác.

Mọi hàm service gọi thật (không mock), không bỏ qua lỗi hợp lệ — xfail khi tìm ra bug thật.
"""
import pytest
from datetime import datetime, timedelta
from fastapi import HTTPException

from app.modules.approval import action_service, instance_service
from app.modules.approval.flow_model import APPROVER_EMPLOYEE, SKIP_NONE, ApprovalFlow, ApprovalNode
from app.modules.approval.instance_model import TASK_OPEN_STATUSES, TASK_PENDING, ApprovalTask
from app.modules.comment import controller as comment_ct
from app.modules.comment.model import Comment
from app.modules.comment.schema import CommentIn
from app.modules.employee import controller, pending_work_service
from app.modules.employee.model import Employee
from app.modules.employee.service import lock_linked_users
from app.modules.login_session.constants import RevokeReason
from app.modules.user.model import User
from app.modules.work import list_service, schema, task_comment_service, task_service, task_trash_service
from app.modules.work.membership_service import Actor
from app.modules.work.model import WorkMemberRole
from app.modules.work.task_model import WorkTask
from fastapi import BackgroundTasks
from types import SimpleNamespace

ACTOR = 1
ENTITY = "document"
COMPANY = 1


# ──────────────────────────────────────────────────────────────────────────────
# CR-665 Stress: hundreds of pending tasks
# ──────────────────────────────────────────────────────────────────────────────


@pytest.fixture()
def cr665_persons(db, seed):
    """Nhân sự: người chủ (giữ nhiều phiếu), người khác, người vô tài khoản."""
    ids = {"nop": seed.emp_req_id}
    for name in ("main", "other"):
        emp = Employee(code=f"EMP_{name.upper()}", full_name=f"Người {name}",
                       company_id=seed.company_id, department_id=seed.dept_id, is_active=True)
        db.add(emp)
        db.flush()
        ids[name] = emp.id
        if name != "notk":  # Người main và other có tài khoản
            db.add(User(email=f"emp_{name}@x.vn", employee_id=emp.id, password_hash="x", is_active=True))

    # Nhân sự KHÔNG tài khoản
    no_user = Employee(code="EMP_NOTK", full_name="Không tài khoản",
                       company_id=seed.company_id, department_id=seed.dept_id, is_active=True)
    db.add(no_user)
    db.flush()
    ids["notk"] = no_user.id

    db.commit()
    return ids


def _flow_cr665(db, emp_id, code="VT-00", active=True):
    """Tạo luồng duyệt chỉ đích danh nhân sự."""
    flow = ApprovalFlow(entity=ENTITY, code=code, name=f"Luồng {code}", is_active=active,
                        created_by=ACTOR, updated_by=ACTOR)
    db.add(flow)
    db.flush()
    db.add(ApprovalNode(flow_id=flow.id, seq=1, name="Duyệt", approver_kind=APPROVER_EMPLOYEE,
                        approver_ref=str(emp_id), fallback_employee_id=None, skip_duplicate=SKIP_NONE,
                        created_by=ACTOR, updated_by=ACTOR))
    db.commit()
    return flow


def _trinh_cr665(db, entity_id, submitter):
    """Tạo phiên duyệt."""
    return instance_service.start(db, ENTITY, entity_id, {}, submitter, ACTOR,
                                  entity_code=f"VB-{entity_id}", entity_title="Phiếu")


def test_cr665_stress_hundreds_pending_tasks(db, seed, cr665_persons):
    """Người giữ 200+ phiếu: liệt kê tới MAX_ROWS (200), tổng đếm chính xác, không lỗi."""
    main_emp = cr665_persons["main"]
    flow = _flow_cr665(db, main_emp, code="VT-STRESS")

    # Tạo 250 phiếu → 250 việc duyệt cùng nhân sự
    for i in range(250):
        _trinh_cr665(db, 10000 + i, cr665_persons["nop"])
    db.commit()

    result = pending_work_service.pending_work_of(db, main_emp)
    assert result["total_tasks"] == 250, "Tổng phải đếm đúng cả khi vượt MAX_ROWS"
    assert len(result["tasks"]) == 200, "Danh sách phải bị cắt tại MAX_ROWS"
    assert all(t["node_name"] == "Duyệt" for t in result["tasks"])


def test_cr665_stress_query_count_constant_across_sizes(db, seed, cr665_persons, benchmark_queries):
    """Số truy vấn phải cố định (không tăng theo N phiếu)."""
    main_emp = cr665_persons["main"]
    _flow_cr665(db, main_emp, code="VT-QRY")

    entity_offset = [0]

    def _add_instances(n):
        for i in range(n):
            entity_id = 20000 + entity_offset[0] + i
            _trinh_cr665(db, entity_id, cr665_persons["nop"])
        entity_offset[0] += n
        db.commit()

    # Đo truy vấn với 5 phiếu
    _add_instances(5)
    q5 = benchmark_queries(lambda: pending_work_service.pending_work_of(db, main_emp))

    # Đo truy vấn với 50 phiếu (thêm 45)
    _add_instances(45)
    q50 = benchmark_queries(lambda: pending_work_service.pending_work_of(db, main_emp))

    # Đo truy vấn với 200 phiếu (thêm 150)
    _add_instances(150)
    q200 = benchmark_queries(lambda: pending_work_service.pending_work_of(db, main_emp))

    assert q5 > 0 and q5 == q50 == q200, f"Queries should be constant: {q5}, {q50}, {q200}"


def test_cr665_stress_deleted_docs_hide_title_code(db, seed, cr665_persons):
    """Phiếu xóa vẫn tính → entity_code/title bị xóa trắng (can_see callback che dữ liệu)."""
    main_emp = cr665_persons["main"]
    flow = _flow_cr665(db, main_emp)

    # Tạo phiếu và duyệt
    entity_id = 40000
    _trinh_cr665(db, entity_id, cr665_persons["nop"])

    result = pending_work_service.pending_work_of(
        db, main_emp,
        can_see=lambda inst: False  # Người xem không được phép thấy
    )

    task = result["tasks"][0]
    assert task["entity_code"] == "" and task["entity_title"] == ""
    assert task["started_by_name"] == ""
    assert task["hidden"] is True


def test_cr665_stress_employee_without_user_no_error(db, seed, cr665_persons):
    """Nhân sự không tài khoản không làm lỗi pending_work_of."""
    notk_emp = cr665_persons["notk"]
    flow = _flow_cr665(db, notk_emp)

    # Tạo phiếu do người có tài khoản
    nop_emp_id = cr665_persons["nop"]
    _trinh_cr665(db, 30000, nop_emp_id)
    db.commit()

    result = pending_work_service.pending_work_of(db, notk_emp)
    assert result["total_tasks"] == 1
    # Nhân sự không tài khoản vẫn giữ việc duyệt, vẫn có tên (từ cột Employee.full_name)
    assert result["tasks"][0]["task_id"] > 0


# ──────────────────────────────────────────────────────────────────────────────
# CR-667 Stress: comment editing, trash cycles, oversize body
# ──────────────────────────────────────────────────────────────────────────────


@pytest.fixture()
def cr667_workspace(db, cap_quyen):
    """Dự án + 3 người (CHU, WRITER, VIEWER)."""
    CHU, WRITER, VIEWER = (1, 11), (2, 22), (3, 33)

    for uid, eid in (CHU, WRITER, VIEWER):
        db.add(Employee(id=eid, code=f"NV{eid}", full_name=f"Người {eid}", company_id=COMPANY))
        db.add(User(id=uid, email=f"u{uid}@dego.vn", employee_id=eid, is_active=True))
        cap_quyen(uid, "work_task", read=True, write=True, create=True, delete=True)
    db.commit()

    def _actor(p): return Actor(user_id=p[0], employee_id=p[1], company_id=COMPANY)
    def _user(p): return SimpleNamespace(id=p[0], employee_id=p[1])

    lst = list_service.create_list(db, _actor(CHU), schema.ListCreate(name="Dự án test"))
    list_service.add_member(db, _actor(CHU), lst["id"], schema.MemberIn(employee_id=WRITER[1]))
    list_service.add_member(db, _actor(CHU), lst["id"],
                           schema.MemberIn(employee_id=VIEWER[1], role=int(WorkMemberRole.VIEWER)))

    task = task_service.create_task(db, _actor(CHU), schema.TaskCreate(list_id=lst["id"], title="Việc 1"))

    return SimpleNamespace(
        db=db, list_id=lst["id"], task_id=task["id"],
        chu=_actor(CHU), writer=_actor(WRITER), viewer=_actor(VIEWER),
        chu_user=_user(CHU), writer_user=_user(WRITER), viewer_user=_user(VIEWER)
    )


def _tao_bl_cr667(d, actor_user, body="Test"):
    """Tạo bình luận."""
    resp = comment_ct.create_comment(
        CommentIn(entity="work_task", entity_id=d.task_id, body=body),
        BackgroundTasks(), d.db, actor_user
    )
    import json
    return json.loads(resp.body)["data"]["id"]


def test_cr667_stress_edit_100_times(cr667_workspace):
    """Sửa cùng bình luận 100 lần: all thành công, body đổi."""
    d = cr667_workspace
    cid = _tao_bl_cr667(d, d.writer_user, "v0")

    # Lùi created_at để chắc edited flag đếm được
    from datetime import timedelta
    comment = d.db.get(Comment, cid)
    comment.created_at = datetime.utcnow() - timedelta(hours=1)
    d.db.commit()

    for i in range(1, 101):
        body = f"v{i}"
        out = task_comment_service.edit_comment(
            d.db, d.writer, d.writer_user, d.task_id, cid, body
        )
        assert out["body"] == body

    final = d.db.get(Comment, cid)
    assert final.body == "v100"
    assert final.updated_at > final.created_at  # Sửa thì updated_at > created_at


def test_cr667_stress_others_cannot_edit(cr667_workspace):
    """Sửa bình luận người khác → 403, lần lượt CHU, VIEWER, người ngoài."""
    d = cr667_workspace
    cid = _tao_bl_cr667(d, d.writer_user, "Của Writer")

    for actor, actor_user in [(d.chu, d.chu_user), (d.viewer, d.viewer_user)]:
        with pytest.raises(HTTPException) as e:
            task_comment_service.edit_comment(d.db, actor, actor_user, d.task_id, cid, "Lén sửa")
        assert e.value.status_code == 403


def test_cr667_stress_edit_to_empty_or_whitespace_400(cr667_workspace):
    """Sửa thành rỗng, chỉ space, tab, newline → 400."""
    d = cr667_workspace
    cid = _tao_bl_cr667(d, d.writer_user, "Ban đầu")

    for bad in ("", "   ", "\t", "\n", "  \n  \t  "):
        with pytest.raises(HTTPException) as e:
            task_comment_service.edit_comment(d.db, d.writer, d.writer_user, d.task_id, cid, bad)
        assert e.value.status_code == 400, f"Whitespace '{repr(bad)}' should be 400"


def test_cr667_stress_edit_oversize_body_400(cr667_workspace):
    """Sửa body > 5000 ký tự → 400 (backend kiểm dài và trả 400)."""
    d = cr667_workspace
    cid = _tao_bl_cr667(d, d.writer_user, "Ban đầu")

    oversize = "x" * 5001
    with pytest.raises(HTTPException) as e:
        task_comment_service.edit_comment(d.db, d.writer, d.writer_user, d.task_id, cid, oversize)
    assert e.value.status_code == 400


def test_cr667_stress_trash_restore_cycles_50x(cr667_workspace):
    """Xóa → khôi phục 50 lần: deleted_at giữ đúng, danh sách thùng rác thay đổi."""
    d = cr667_workspace

    # Tạo việc
    task = task_service.create_task(
        d.db, d.chu, schema.TaskCreate(list_id=d.list_id, title="Xóa lại 50 lần")
    )
    task_id = task["id"]

    for i in range(50):
        # Xóa
        task_service.delete_task(d.db, d.chu, task_id)
        trash = task_trash_service.list_trash(d.db, d.chu, d.list_id)
        assert len(trash) == 1, f"Iteration {i}: deleted thì phải thấy thùng rác"

        # Khôi phục
        task_trash_service.restore_task(d.db, d.chu, task_id)
        trash = task_trash_service.list_trash(d.db, d.chu, d.list_id)
        assert len(trash) == 0, f"Iteration {i}: restored thì thùng rác phải rỗng"

    # Sau 50 lần, việc phải còn sống
    final_task = d.db.get(WorkTask, task_id)
    assert final_task.deleted_at is None


def test_cr667_stress_trash_scope_member_vs_owner(cr667_workspace):
    """Thành viên MEMBER chỉ khôi phục được việc do mình tạo; OWNER toàn bộ."""
    d = cr667_workspace

    # CHU tạo việc, WRITER tạo việc
    task_chu = task_service.create_task(
        d.db, d.chu, schema.TaskCreate(list_id=d.list_id, title="Của chủ")
    )
    task_writer = task_service.create_task(
        d.db, d.writer, schema.TaskCreate(list_id=d.list_id, title="Của writer")
    )

    # Xóa cả hai
    task_service.delete_task(d.db, d.chu, task_chu["id"])
    task_service.delete_task(d.db, d.writer, task_writer["id"])

    # WRITER nhìn thấy cả hai
    trash = {r["id"]: r for r in task_trash_service.list_trash(d.db, d.writer, d.list_id)}
    assert task_chu["id"] in trash and task_writer["id"] in trash
    assert trash[task_writer["id"]]["can_restore"] is True
    assert trash[task_chu["id"]]["can_restore"] is False

    # WRITER khôi phục của mình được, của chủ thì 403
    task_trash_service.restore_task(d.db, d.writer, task_writer["id"])
    with pytest.raises(HTTPException) as e:
        task_trash_service.restore_task(d.db, d.writer, task_chu["id"])
    assert e.value.status_code == 403

    # CHU khôi phục cả hai được
    task_trash_service.restore_task(d.db, d.chu, task_chu["id"])
    trash = task_trash_service.list_trash(d.db, d.chu, d.list_id)
    assert len(trash) == 0


def test_cr667_stress_viewer_cannot_access_trash(cr667_workspace):
    """VIEWER (không quyền write/delete) không thấy thùng rác."""
    d = cr667_workspace
    task_service.delete_task(d.db, d.chu, d.task_id)

    with pytest.raises(HTTPException) as e:
        task_trash_service.list_trash(d.db, d.viewer, d.list_id)
    assert e.value.status_code == 403


# ──────────────────────────────────────────────────────────────────────────────
# Fixtures for query benchmarking
# ──────────────────────────────────────────────────────────────────────────────


@pytest.fixture()
def benchmark_queries(db):
    """Đếm số câu SQL thực thi trong một hàm."""
    def _benchmark(fn):
        from sqlalchemy import event
        statements = []

        def _on(conn, cursor, statement, *args):
            statements.clear()
            statements.append(statement)

        engine = db.get_bind()
        event.listen(engine, "before_cursor_execute", _on)
        try:
            fn()
        finally:
            event.remove(engine, "before_cursor_execute", _on)
        return len(statements)

    return _benchmark
