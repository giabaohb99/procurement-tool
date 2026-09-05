"""Cụm 07 — PHẠM VI DỮ LIỆU của hạ tầng dùng chung.

Bộ máy duyệt · thông báo · nhật ký · xuất/nhập · công việc · diễn đàn · trợ lý AI.

Cả cụm này **không sở hữu chứng từ nào** — nó *nói về* chứng từ của module khác.
Nên lỗ ở đây không lộ một bảng dữ liệu, nó lộ **siêu dữ liệu**: tên phiếu, tên
luồng, tên người đang duyệt, ai vừa sửa gì, ai vừa xuất bảng nào. Đúng thứ đã
thủng một lần 25/08/2026 (`instance_controller._load` — bốn đường đọc phiếu chỉ
đòi đăng nhập, nên người của pháp nhân khác đọc được tên văn bản + tên người
đang giữ phiếu, dù mở chính văn bản đó thì ăn 404).

Ba loại bài trong tệp này, cố ý trộn lẫn theo chủ đề chứ không tách:

* **bài nghiệp vụ** — dựng dữ liệu thật rồi so tập id cụ thể;
* **bài BẤT BIẾN** (cùng khuôn BB-1 của `test_pham_vi_luat_bat_bien.py`) — không
  hỏi "người X thấy phiếu Y không" mà hỏi "có ai vừa thêm thứ mới mà quên khai
  không". Chỗ duy nhất bắt được nhóm lỗi *thêm-rồi-quên*;
* **bài GHIM hành vi** — chỗ mã đang xử sự theo một cách mà chưa ai quyết là
  đúng hay sai. Ghim lại kèm `# QUYẾT ĐỊNH CHỜ:` để lần sau ai đổi thì phải đọc
  câu hỏi trước khi sửa test cho xanh.

Không sửa `app/core/` trong đợt này, và không đổi mặc định `can_read` thành
`False` (xem BB-1: đổi thế sẽ khóa im lặng module nào lỡ quên).
"""
import json
from datetime import date, datetime, timedelta

import pytest
from fastapi import HTTPException

from scope_factory import build_world  # noqa: F401 — fixture `world` dùng nó

# ── Hằng dùng chung ────────────────────────────────────────────────────────────
ACTOR = 1
MONDAY = date(2026, 1, 5)


# ══════════════════════════════════════════════════════════════════════════════
#  Helper — tên tiếng Anh, là ĐỘNG TỪ (backend/.claude/rules/naming.md)
# ══════════════════════════════════════════════════════════════════════════════

def read_envelope(response) -> dict:
    """Bóc phong bì `{success, message, data}` ra khỏi `JSONResponse`.

    `core.response.success(...)` trả về một `JSONResponse` chứ không trả dict,
    nên gọi thẳng hàm controller trong test thì phải giải mã thân phản hồi —
    đây đúng là những byte đi ra dây, không phải một đối tượng trung gian.
    """
    return json.loads(response.body)

def make_leave_request(db, world, emp_key: str, code: str):
    """Một tờ đơn nghỉ phép thật, gắn đúng pháp nhân/phòng của nhân sự đó.

    Dùng `leave_request` làm phương tiện cho cả cụm A vì ba lý do: nó có reader
    đăng ký ở `entity_hooks`, nó khai đủ cột phạm vi trong `SCOPE_FIELDS`, và nó
    mang đúng loại dữ liệu mà rò rỉ siêu dữ liệu gây đau nhất (tên người nghỉ +
    lý do nghỉ).
    """
    from app.modules.employee.model import Employee
    from app.modules.leave.request_model import LeaveRequest

    emp = db.get(Employee, world.emp[emp_key])
    row = LeaveRequest(
        code=code, company_id=emp.company_id, department_id=emp.department_id,
        employee_id=emp.id, leave_type_id=0,
        from_date=MONDAY, to_date=MONDAY, total_days=1.0,
        reason="Việc riêng", created_by=ACTOR, updated_by=ACTOR,
    )
    db.add(row)
    db.flush()
    return row


def make_instance(db, entity: str, entity_id: int, *, code: str = "",
                  title: str = "", started_by: int | None = None, status: int | None = None):
    """Một phiên duyệt trơ — đủ cho mọi câu hỏi về QUYỀN ĐỌC phiếu."""
    from app.modules.approval.instance_model import (INSTANCE_RUNNING,
                                                     ApprovalInstance)

    row = ApprovalInstance(
        entity=entity, entity_id=entity_id, entity_code=code, entity_title=title,
        flow_id=0, flow_version=1, flow_snapshot="",
        status=INSTANCE_RUNNING if status is None else status,
        current_seq=1, started_by_employee_id=started_by,
        created_by=ACTOR, updated_by=ACTOR,
    )
    db.add(row)
    db.flush()
    return row


def open_task_for(db, instance, employee_id: int, *, seq: int = 1, name: str = "Chặng 1"):
    """Một việc ĐANG CHỜ người này trên phiếu đó."""
    from app.modules.approval.instance_model import TASK_PENDING, ApprovalTask

    row = ApprovalTask(instance_id=instance.id, node_seq=seq, node_name=name,
                       order_no=1, assignee_employee_id=employee_id,
                       status=TASK_PENDING, created_by=ACTOR, updated_by=ACTOR)
    db.add(row)
    db.flush()
    return row


def make_work_list(db, world, company_key: str, name: str, *, group_id=None):
    from app.modules.work.model import WorkList

    row = WorkList(company_id=world.co[company_key], group_id=group_id, name=name,
                   created_by=ACTOR, updated_by=ACTOR)
    db.add(row)
    db.flush()
    return row


def add_list_member(db, work_list, employee_id: int, role: int | None = None):
    from app.modules.work.model import WorkListMember, WorkMemberRole

    row = WorkListMember(company_id=work_list.company_id, list_id=work_list.id,
                         employee_id=employee_id,
                         role=int(WorkMemberRole.MEMBER) if role is None else role,
                         created_by=ACTOR, updated_by=ACTOR)
    db.add(row)
    db.flush()
    return row


def make_work_task(db, work_list, title: str, creator_employee_id: int = 0):
    from app.modules.work.task_model import WorkTask

    row = WorkTask(company_id=work_list.company_id, list_id=work_list.id, title=title,
                   creator_employee_id=creator_employee_id,
                   created_by=ACTOR, updated_by=ACTOR)
    db.add(row)
    db.flush()
    return row


def make_actor_of(db, world, key: str):
    """`work.membership_service.Actor` của một tài khoản trong thế giới mẫu."""
    from app.modules.work.membership_service import resolve_actor

    return resolve_actor(db, world.actor(key).user)


def list_work_routes():
    """Mọi route của `app/modules/work/` kèm hàm xử lý. Đọc từ app THẬT.

    Không liệt kê tay: danh sách gõ tay hết hạn ngay lần thêm route kế tiếp, mà
    đó chính là lúc bài kiểm này cần chạy.
    """
    import app.main as main_module
    from app.modules.work import controller as work_controller
    from app.modules.work import task_controller as work_task_controller

    modules = {work_controller.__name__: work_controller,
               work_task_controller.__name__: work_task_controller}
    out = []
    for route in main_module.app.routes:
        endpoint = getattr(route, "endpoint", None)
        if endpoint is None or getattr(endpoint, "__module__", "") not in modules:
            continue
        for method in sorted((route.methods or set()) - {"HEAD", "OPTIONS"}):
            out.append((method, route.path, endpoint, modules[endpoint.__module__]))
    return out


def find_service_calls(endpoint, controller_module):
    """[(tên gọi, hàm)] — những hàm SERVICE của phân hệ Công việc mà route gọi.

    Đọc bằng `ast` chứ không bằng grep chuỗi: grep đếm được cả tên nằm trong
    docstring, mà đợt trước đã có bốn báo động giả vì đúng kiểu đó.
    """
    import ast
    import inspect

    tree = ast.parse(inspect.getsource(endpoint).lstrip())
    found = []
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)):
            continue
        alias = getattr(controller_module, node.func.value.id, None)
        if alias is None or not inspect.ismodule(alias):
            continue
        if not alias.__name__.startswith("app.modules.work"):
            continue
        target = getattr(alias, node.func.attr, None)
        if target is not None:
            found.append((f"{node.func.value.id}.{node.func.attr}", target))
    return found


#  Bốn cửa gác của phân hệ Công việc. Tất cả nằm ở `membership_service` (hoặc
#  bọc lại nó), và tất cả đều quy về tư cách THÀNH VIÊN của list.
WORK_GUARDS = ("get_list_or_403", "_get_group_or_403", "get_task_or_403",
               "visible_list_ids", "group_role")


def find_guards_in(func) -> set[str]:
    import inspect

    try:
        source = inspect.getsource(func)
    except (OSError, TypeError):
        return set()
    return {guard for guard in WORK_GUARDS if guard in source}


# ══════════════════════════════════════════════════════════════════════════════
#  A. BỘ MÁY DUYỆT
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture()
def don_hai_phap_nhan(db, world):
    """Hai tờ đơn nghỉ + hai phiên duyệt: một của pháp nhân A, một của B."""
    don_a = make_leave_request(db, world, "a1", "NP-A-001")
    don_b = make_leave_request(db, world, "b1", "NP-B-001")
    phien_a = make_instance(db, "leave_request", don_a.id, code="NP-A-001",
                            title="Nghỉ phép — Nhân sự a1", started_by=world.emp["a1"])
    phien_b = make_instance(db, "leave_request", don_b.id, code="NP-B-001",
                            title="Nghỉ phép — Nhân sự b1", started_by=world.emp["b1"])
    db.commit()
    return {"don_a": don_a, "don_b": don_b, "phien_a": phien_a, "phien_b": phien_b}


def test_a1_mo_phien_duyet_cua_chung_tu_ngoai_pham_vi_bi_404(db, world, don_hai_phap_nhan):
    """`GET /approval/instances/{id}` — 404 chứ không phải 200 kèm tên người nghỉ.

    Hỏng thì hỏng thế nào: người của pháp nhân A mở `/api/leave-requests/<id của
    B>` ăn 404, nhưng `/api/approvals/<id phiên của B>` trả 200 kèm
    `entity_title` = «Nghỉ phép — Nhân sự b1». Không lộ bảng, lộ đúng cái tên.
    """
    from app.modules.approval import instance_controller

    a1 = world.grant("a1", "leave_request", scope="company")
    phien_a = don_hai_phap_nhan["phien_a"]
    phien_b = don_hai_phap_nhan["phien_b"]

    assert instance_controller._load(db, phien_a.id, a1.user).id == phien_a.id

    with pytest.raises(HTTPException) as loi:
        instance_controller._load(db, phien_b.id, a1.user)
    assert loi.value.status_code == 404, "phải 404 — nói 403 là đã xác nhận có phiếu"


def test_a2_ban_in_dau_vet_cung_di_qua_dung_mot_chot_load(db, world, don_hai_phap_nhan):
    """`/trail` là **bản in** — nó mang tên người ký và ý kiến trên phiếu.

    Bài này không lặp A1: nó chốt rằng `trail` gọi `_load` CÓ truyền `user`.
    Bỏ tham số đó đi thì A1 vẫn xanh còn bản in vẫn rò — đúng hình dạng lỗ
    25/08/2026, nơi bốn đường dùng chung một hàm nạp mà chỉ một đường kiểm.
    """
    import ast
    import inspect

    from app.modules.approval import instance_controller

    for ten_ham in ("get_instance", "trail", "comment"):
        cay = ast.parse(inspect.getsource(getattr(instance_controller, ten_ham)).lstrip())
        goi_load = [node for node in ast.walk(cay)
                    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                    and node.func.id == "_load"]
        assert goi_load, f"{ten_ham} không gọi `_load` — nó tự nạp phiếu ở đâu?"
        assert all(len(node.args) >= 3 for node in goi_load), (
            f"`_load` trong {ten_ham} thiếu tham số `user` → bỏ luôn kiểm quyền đọc "
            "chứng từ. Xem docstring của `_load`.")

    # Và chốt đó chạy thật, không chỉ có mặt trong mã.
    a1 = world.grant("a1", "leave_request", scope="company")
    with pytest.raises(HTTPException):
        instance_controller._load(db, don_hai_phap_nhan["phien_b"].id, a1.user)


def test_a3_hoi_phien_duyet_theo_chung_tu_tra_null_chu_khong_403(db, world, don_hai_phap_nhan):
    """`/of/{entity}/{id}` — không đọc được thì trả `null`, y như chứng từ chưa
    vào bộ máy. Trả 403 là tự khai «có phiếu nhưng anh không được xem»."""
    from app.modules.approval import instance_controller

    a1 = world.grant("a1", "leave_request", scope="company")
    don_b = don_hai_phap_nhan["don_b"]
    don_a = don_hai_phap_nhan["don_a"]

    ket_qua_b = read_envelope(instance_controller.instances_of_entity(
        "leave_request", don_b.id, db=db, user=a1.user))
    assert ket_qua_b["data"] is None
    assert ket_qua_b["success"] is True, "không được 403 — 403 đã là một câu trả lời"

    ket_qua_a = read_envelope(instance_controller.instances_of_entity(
        "leave_request", don_a.id, db=db, user=a1.user))
    assert ket_qua_a["data"]["id"] == don_hai_phap_nhan["phien_a"].id


def test_a4_loai_chung_tu_chua_khai_reader_thi_can_read_cho_qua_tat(db, world):
    """Ghim FAIL-OPEN của `entity_hooks.can_read` (`entity_hooks.py:122-124`).

    Không có `_READERS[entity]` → `True`. Hôm nay bốn bridge đều khai đủ nên
    chưa thủng; module thứ năm quên khai thì lộ cho **mọi người đăng nhập**.

    ⚠️ Bài này CỐ Ý không sửa mặc định thành `False` — xem BB-1 ở
    `test_pham_vi_luat_bat_bien.py`, nơi luật `_HOOKS ⊆ _READERS` canh việc đó.
    Ở đây chỉ chứng minh hậu quả để BB-1 có nghĩa với người đọc.
    """
    from app.modules.approval import entity_hooks
    from app.modules.approval.instance_model import ApprovalInstance

    assert "khong_ai_khai_bao" not in entity_hooks._READERS
    phien_ma = ApprovalInstance()
    phien_ma.entity = "khong_ai_khai_bao"
    phien_ma.entity_id = 999
    phien_ma.id = 0

    khach = world.actor("a1")   # KHÔNG cấp một grant nào
    assert khach.profile()["grants"] == []
    assert entity_hooks.can_read(db, phien_ma, khach.user) is True, (
        "hành vi hiện tại: chưa khai reader = cho qua tất. BB-1 canh việc khai đủ.")

    # Loại ĐÃ khai thì vẫn chặn đúng — chốt rằng fail-open chỉ áp cho loại chưa khai.
    don_b = make_leave_request(db, world, "b1", "NP-B-777")
    phien_b = make_instance(db, "leave_request", don_b.id)
    db.commit()
    world.grant("a1", "leave_request", scope="company")
    assert entity_hooks.can_read(db, phien_b, khach.user) is False


def test_a5_khong_co_viec_dang_cho_thi_khong_bam_duyet_duoc(db, world, don_hai_phap_nhan):
    """`approve/reject/return/withdraw` CỐ Ý không dùng `require(...)`.

    Quyền ở đây là «có việc đang chờ mình», do `action_service.pending_task_of`
    xét. Kiểm cả hai chiều: gắn thêm `require` thì người được giao việc không
    bấm được nữa; bỏ chốt này thì ai đăng nhập cũng ký được phiếu bất kỳ.
    """
    from app.modules.approval import action_service

    phien_a = don_hai_phap_nhan["phien_a"]

    #  Chiều CHẶN: a2 không có việc nào trên phiếu.
    with pytest.raises(HTTPException) as loi:
        action_service.pending_task_of(db, phien_a, world.emp["a2"])
    assert loi.value.status_code == 403
    assert "không có việc" in loi.value.detail.lower()

    #  Chiều CHO QUA: giao việc cho a2 thì chính a2 bấm được — không cần grant nào.
    viec = open_task_for(db, phien_a, world.emp["a2"])
    db.commit()
    assert world.actor("a2").profile()["grants"] == [], "cố ý: quyền là VIỆC, không phải vai trò"
    task, uy_quyen = action_service.pending_task_of(db, phien_a, world.emp["a2"])
    assert (task.id, uy_quyen) == (viec.id, None)

    #  Người khác vẫn không lọt, kể cả khi phiếu đã có việc đang treo.
    with pytest.raises(HTTPException):
        action_service.pending_task_of(db, phien_a, world.emp["a3"])


def test_a6_hop_viec_va_lich_su_chi_ra_viec_cua_chinh_minh(db, world, don_hai_phap_nhan):
    """`/my-tasks` + `/my-history` — dữ liệu của CHÍNH người đăng nhập.

    Hai đường này cố ý 0 `require`: đây là hộp việc của họ. Nhưng «của họ» phải
    lọc bằng `assignee_employee_id`, không phải bằng phạm vi — nên bài này so
    tập id cụ thể chứ không chỉ đếm.
    """
    from app.modules.approval import task_service

    phien_a = don_hai_phap_nhan["phien_a"]
    phien_b = don_hai_phap_nhan["phien_b"]
    viec_a2 = open_task_for(db, phien_a, world.emp["a2"])
    open_task_for(db, phien_b, world.emp["b1"])
    db.commit()

    cua_a2 = task_service.my_tasks(db, world.emp["a2"])
    assert {row["id"] for row in cua_a2} == {viec_a2.id}
    assert {row["entity_id"] for row in cua_a2} == {don_hai_phap_nhan["don_a"].id}

    assert task_service.my_tasks(db, world.emp["a3"]) == []
    #  Tài khoản chưa gắn nhân sự: rỗng, không nổ.
    assert task_service.my_tasks(db, 0) == []
    assert task_service.handled_tasks(db, 0) == []


def test_a7_hoi_luong_duyet_nhieu_id_mot_luot_chi_tra_phan_trong_pham_vi(
        db, world, don_hai_phap_nhan):
    """`/steps` gom nhiều chứng từ một lượt — trộn id trong/ngoài phạm vi.

    Hỏng thì hỏng thế nào: dải chấm mang TÊN CHẶNG và TÊN NGƯỜI DUYỆT. Không lọc
    thì một lần mở trang danh sách là dựng lại được cả sơ đồ ký duyệt của pháp
    nhân khác, và biết luôn ai đang xin nghỉ.
    """
    from app.modules.approval import instance_controller

    a1 = world.grant("a1", "leave_request", scope="company")
    don_a, don_b = don_hai_phap_nhan["don_a"], don_hai_phap_nhan["don_b"]
    open_task_for(db, don_hai_phap_nhan["phien_a"], world.emp["a2"], name="TP duyệt")
    open_task_for(db, don_hai_phap_nhan["phien_b"], world.emp["b1"], name="TP duyệt")
    db.commit()

    ket_qua = read_envelope(instance_controller.steps_of_many(
        entity="leave_request", ids=f"{don_a.id},{don_b.id}", db=db, user=a1.user))
    assert set(ket_qua["data"]) == {str(don_a.id)}, "id của pháp nhân B phải rụng khỏi kết quả"


def test_a8_a9_a10_ba_cong_toan_he_deu_dung_has_global_scope(db, world):
    """Bàn giao · ủy quyền hộ · công tắc bộ máy — cùng một cổng, ghim lại một chỗ.

    Ba chỗ này KHÔNG có `flow_id`/`instance_id` để mà lọc theo phạm vi, nên
    chúng phải hỏi `has_global_scope(...)`. Hành vi nghiệp vụ đầy đủ đã có ở
    `test_bo_may_duyet_chiem_quyen.py`; bài này chốt phần *phạm vi*: quyền hành
    động (`approval_flow.write`) mà phạm vi HẸP thì vẫn không phải quản trị.
    """
    from app.core.scoping import has_global_scope
    from app.modules.approval import delegation_controller, instance_controller

    hep = world.grant("a1", "approval_flow", scope="company", actions=("read", "write", "create"))
    rong = world.grant("a2", "approval_flow", scope="all", actions=("read", "write", "create"))

    assert has_global_scope(hep.profile(), "approval_flow", "write") is False
    assert has_global_scope(rong.profile(), "approval_flow", "write") is True

    #  Phạm vi hẹp → tầng dịch vụ nhận `employee_id` thật, nên nó chặn được việc
    #  «lập hộ / bàn giao hộ». Phạm vi toàn hệ → `None` = miễn kiểm.
    assert instance_controller._acting_employee_id(db, hep.user, "write") == world.emp["a1"]
    assert instance_controller._acting_employee_id(db, rong.user, "write") is None
    assert delegation_controller._acting_employee_id(db, hep.user, "create") == world.emp["a1"]
    assert delegation_controller._acting_employee_id(db, rong.user, "create") is None


def test_a10_cong_tac_bat_bo_may_doi_pham_vi_toan_he(db, world):
    """`PUT /approval-flows/switches` lật một cờ áp cho **cả 13 pháp nhân**.

    Chỉ `require("approval_flow","write")` thôi thì văn thư một pháp nhân con
    tắt được bộ máy duyệt của toàn hệ, và nhật ký chỉ ghi một dòng.
    """
    from app.modules.approval import flow_controller
    from app.modules.approval.flow_controller import SwitchIn

    hep = world.grant("a1", "approval_flow", scope="company", actions=("read", "write"))
    with pytest.raises(HTTPException) as loi:
        flow_controller.set_switch(SwitchIn(entity="leave_request", is_enabled=False),
                                   db=db, user=hep.user)
    assert loi.value.status_code == 403

    rong = world.grant("a2", "approval_flow", scope="all", actions=("read", "write"))
    ket_qua = read_envelope(flow_controller.set_switch(
        SwitchIn(entity="leave_request", is_enabled=False), db=db, user=rong.user))
    assert ket_qua["data"] == {"entity": "leave_request", "is_enabled": False}


def test_a_phien_duyet_chi_ra_luong_cua_phap_nhan_minh(db, world):
    """`ApprovalFlow` có `company_id` → là dữ liệu của từng pháp nhân, không phải
    cấu hình toàn hệ. Chốt bằng tập id, vì `list_flows` là màn duy nhất bày ra
    toàn bộ đường ký duyệt của một tổ chức."""
    from app.modules.approval.flow_model import ApprovalFlow

    db.add_all([
        ApprovalFlow(entity="leave_request", code="L-A", name="Luồng A",
                     company_id=world.co["A"], created_by=ACTOR, updated_by=ACTOR),
        ApprovalFlow(entity="leave_request", code="L-B", name="Luồng B",
                     company_id=world.co["B"], created_by=ACTOR, updated_by=ACTOR),
    ])
    db.commit()
    ids = {row.code: row.id for row in db.query(ApprovalFlow).all()}

    a1 = world.grant("a1", "approval_flow", scope="company")
    assert a1.sees(ApprovalFlow) == {ids["L-A"]}
    assert a1.can_get(ApprovalFlow, ids["L-B"]) is False


# ══════════════════════════════════════════════════════════════════════════════
#  B. THÔNG BÁO
# ══════════════════════════════════════════════════════════════════════════════

def test_b1_thu_cua_nguoi_khac_go_thang_id_van_khong_doc_duoc(db, world):
    """`notification` 0 `require` — cổng của nó là `user_id`, không phải phạm vi.

    Hỏng thì hỏng thế nào: thư báo duyệt mang `title` = tên văn bản/tên phiếu.
    Đọc được hộp thư người khác là đọc được danh mục việc họ đang giữ.
    """
    from app.modules.notification.controller import (delete_one,
                                                     list_notifications,
                                                     mark_read)
    from app.modules.notification.model import Notification

    a1, a2 = world.actor("a1"), world.actor("a2")
    db.add_all([
        Notification(user_id=a1.user.id, title="Thư của a1", body="x", link="/a"),
        Notification(user_id=a2.user.id, title="Thư của a2", body="y", link="/b"),
    ])
    db.commit()
    ids = {row.title: row.id for row in db.query(Notification).all()}

    class _Request:
        query_params: dict = {}

    ket_qua = read_envelope(list_notifications(_Request(), db=db, user=a1.user))
    assert {item["id"] for item in ket_qua["data"]["items"]} == {ids["Thư của a1"]}

    #  Gõ thẳng id thư của a2: không nổ, nhưng cũng KHÔNG đụng được vào dòng đó.
    mark_read(ids["Thư của a2"], db=db, user=a1.user)
    delete_one(ids["Thư của a2"], db=db, user=a1.user)
    con_lai = db.get(Notification, ids["Thư của a2"])
    assert con_lai is not None and con_lai.is_read is False


#  ── B2: LUẬT BẤT BIẾN, cùng khuôn BB-1 ────────────────────────────────────────
#
#  Loại chứng từ vào bộ máy duyệt mà thiếu tên ở `ENTITY_LABELS`/`ENTITY_LINKS`
#  thì thư báo vẫn gửi, nhưng ghi «Phiếu NP009» và `link` RỖNG — bấm vào không
#  đi đâu cả. Mà `notify_new_tasks` NUỐT LỖI (có chủ ý: mất thư còn hơn mất
#  phiếu), nên không một chỗ nào đỏ lên.
#
#  Danh sách dưới đây là các khoảng TRỐNG ĐANG CÓ, ghim lại để:
#    * thêm entity mới mà quên khai → đỏ ngay (giá trị chính của bài kiểm);
#    * ai vá xong khoảng trống cũ → cũng đỏ, buộc phải rút tên ra khỏi đây.
#  RỖNG từ 05/09/2026 — `vehicle_booking` đã được khai đủ hai bảng. Giữ hằng số
#  lại (chứ không xóa) vì nó là chỗ để ghi ngoại lệ CÓ LÝ DO nếu sau này có loại
#  chứng từ cố ý không báo qua chuông. Rỗng là trạng thái đúng, không phải thiếu sót.
B2_THIEU_NHAN_DA_BIET: dict[str, str] = {}


def test_b2_moi_entity_vao_bo_may_duyet_deu_phai_co_nhan_va_duong_dan():
    """LUẬT BẤT BIẾN — `_HOOKS ⊆ (ENTITY_LABELS ∩ ENTITY_LINKS)`, trừ danh sách ghim.

    Cùng họ với BB-1: không hỏi "thư này đúng chưa", hỏi "có ai vừa nối một loại
    chứng từ vào bộ máy duyệt mà quên khai chỗ dịch tên không".
    """
    import app.main  # noqa: F401 — nạp mọi bridge để chúng tự đăng ký
    from app.modules.approval.entity_hooks import _HOOKS
    from app.modules.approval.task_notification import (ENTITY_LABELS,
                                                        ENTITY_LINKS)

    assert _HOOKS, "chưa module nào đăng ký hook — kiểm lại việc nạp app.main"
    thieu = sorted(set(_HOOKS) - (set(ENTITY_LABELS) & set(ENTITY_LINKS)))
    assert thieu == sorted(B2_THIEU_NHAN_DA_BIET), (
        f"chênh lệch so với bản ghim: {thieu}. Loại chứng từ vào bộ máy duyệt phải có "
        "tên ở CẢ `ENTITY_LABELS` lẫn `ENTITY_LINKS` của `approval/task_notification.py` "
        "— thiếu thì thư ghi «Phiếu <mã>» và bấm vào không đi đâu, mà `notify_new_tasks` "
        "nuốt lỗi nên không chỗ nào đỏ. Vá xong thì rút tên khỏi B2_THIEU_NHAN_DA_BIET."
    )


def test_b2_thu_bao_viec_goi_dung_ten_va_bam_vao_di_dung_cho(db, world):
    """Không nói suông: dựng thư THẬT rồi đọc lại dòng đó trong bảng.

    Đây là phần làm cho luật bất biến ở trên có nghĩa. Trước 05/09/2026 ca này
    ghim khoảng trống của `vehicle_booking`: thư ghi «Phiếu XE009» và `link`
    RỖNG — bấm vào không đi đâu cả. Nay khẳng định chiều ngược lại.

    Vì sao phải dựng thư thật chứ không đọc hai bảng hằng số: `notify_new_tasks`
    **nuốt lỗi** (có chủ ý — mất thư còn hơn mất phiếu), nên đường từ hằng số
    tới nội dung thư là chỗ duy nhất có thể đứt mà không ai biết.
    """
    from app.modules.approval import task_notification
    from app.modules.notification.model import Notification

    phien = make_instance(db, "vehicle_booking", 9, code="XE009", title="Đặt xe đi Cần Thơ")
    viec = open_task_for(db, phien, world.emp["a2"])
    db.commit()

    so_thu = task_notification.notify_new_tasks(db, phien, [viec])
    db.commit()
    assert so_thu == 1, "phải có thư thật trong bảng rồi mới khẳng định"

    thu = db.query(Notification).filter(
        Notification.user_id == world.actor("a2").user.id).one()
    assert thu.link == "/vehicle-booking/9", "khớp `app-routes.ts:327` của frontend-v2"
    assert thu.body.startswith("Phiếu đặt xe XE009"), (
        "thiếu ENTITY_LABELS thì thư gọi mọi thứ là «Phiếu»")

    #  Đối chứng: loại khai từ trước vẫn nói đúng tên và có đường dẫn.
    don = make_leave_request(db, world, "a1", "NP-B2-001")
    phien_np = make_instance(db, "leave_request", don.id, code="NP009", title="Nghỉ phép a1")
    viec_np = open_task_for(db, phien_np, world.emp["a3"])
    db.commit()
    task_notification.notify_new_tasks(db, phien_np, [viec_np])
    db.commit()
    thu_np = db.query(Notification).filter(
        Notification.user_id == world.actor("a3").user.id).one()
    assert thu_np.link == f"/hr/leave-requests/{don.id}"
    assert thu_np.body.startswith("Đơn nghỉ phép NP009")


def test_b3_thu_bao_viec_chi_mang_ma_va_tieu_de_do_bo_may_tu_giu(db, world):
    """Nội dung thư không được lộ thứ người nhận chưa có quyền xem.

    Thư dựng từ `instance.entity_code` / `entity_title` / `node_name` — đúng ba
    thứ người nhận **buộc phải biết** để đi ký. Nó KHÔNG đọc bảng chứng từ, nên
    không có đường nào để lý do nghỉ hay số tiền lọt vào thư.
    """
    from app.modules.approval import task_notification
    from app.modules.notification.model import Notification

    don = make_leave_request(db, world, "a1", "NP-B3-001")
    don.reason = "Đi khám bệnh viện tâm thần"   # thứ riêng tư nhất trên tờ đơn
    phien = make_instance(db, "leave_request", don.id, code="NP-B3-001",
                          title="Nghỉ phép — Nhân sự a1")
    viec = open_task_for(db, phien, world.emp["b1"], name="Trưởng phòng duyệt")
    db.commit()

    task_notification.notify_new_tasks(db, phien, [viec])
    db.commit()
    thu = db.query(Notification).filter(
        Notification.user_id == world.actor("b1").user.id).one()
    assert "tâm thần" not in thu.body and "tâm thần" not in thu.title
    assert thu.body == "Đơn nghỉ phép NP-B3-001 đang chờ bạn ở «Trưởng phòng duyệt»."


def test_b4_quyen_khai_hop_thu_khac_quyen_dung_hop_thu(db, world):
    """`mailbox` khai `PUBLIC` — nhưng đó là quyền KHAI, không phải quyền GỬI.

    Ai gửi được bằng hộp thư nào nằm ở `tab_mailbox_member`. Lẫn hai thứ này là
    cấp quyền quản trị danh mục cho ai đó rồi họ gửi thư đại diện pháp nhân khác.
    """
    from app.core.scoping import PUBLIC, SCOPE_FIELDS
    from app.modules.notification import mailbox_service
    from app.modules.notification.mailbox_model import Mailbox, MailboxMember

    assert SCOPE_FIELDS["mailbox"] is PUBLIC

    hop_a = Mailbox(code="HT_A", name="Hộp thư A", email="a@x.vn",
                    company_id=world.co["A"], created_by=ACTOR, updated_by=ACTOR)
    hop_b = Mailbox(code="HT_B", name="Hộp thư B", email="b@x.vn",
                    company_id=world.co["B"], created_by=ACTOR, updated_by=ACTOR)
    db.add_all([hop_a, hop_b])
    db.flush()
    db.add(MailboxMember(mailbox_id=hop_a.id, employee_id=world.emp["a1"],
                         created_by=ACTOR, updated_by=ACTOR))
    db.commit()

    #  Quyền KHAI: PUBLIC nên `apply_scope` không cắt gì — thấy cả hai hộp.
    a1 = world.grant("a1", "mailbox", scope="company")
    assert a1.sees(Mailbox, "mailbox") == {hop_a.id, hop_b.id}

    #  Quyền DÙNG: chỉ hộp mình là thành viên.
    assert mailbox_service.can_use(db, hop_a.id, world.emp["a1"]) is True
    assert mailbox_service.can_use(db, hop_b.id, world.emp["a1"]) is False
    assert [row.id for row in mailbox_service.for_employee(db, world.emp["a1"])] == [hop_a.id]
    assert mailbox_service.for_employee(db, world.emp["a2"]) == []


def test_b5_cau_hinh_gui_thu_la_toan_he_va_ghim_la_co_y():
    """`email_exclusion` + `email_template` — cấu hình TOÀN HỆ, cố ý không lọc.

    Ghim thành lời để lần sau không ai đi "sửa lỗ" ở đây: hai bảng này không có
    cột pháp nhân, và một mẫu thư/một địa chỉ loại trừ áp cho cả hệ theo thiết
    kế. Cổng của chúng là `require("setting", ...)`, tức là QUYỀN chứ không phải
    phạm vi.
    """
    from app.modules.notification.email_exclusion_model import EmailExclusion
    from app.modules.notification.email_template_model import EmailTemplate

    for model in (EmailExclusion, EmailTemplate):
        cot = set(model.__table__.columns.keys())
        assert "company_id" not in cot and "department_id" not in cot, (
            f"{model.__name__} nay CÓ cột pháp nhân → phải khai phạm vi, "
            "không còn là cấu hình toàn hệ nữa")


# ══════════════════════════════════════════════════════════════════════════════
#  C. NHẬT KÝ · XUẤT · NHẬP
# ══════════════════════════════════════════════════════════════════════════════

def test_c1_nhat_ky_he_thong_khong_con_cho_nguoi_khong_grant_doc_het(db, world):
    """Bài giữ của lỗ C1 — **đã vá 05/09/2026**.

    Trước bản vá, `GET /api/audit-logs` chỉ có `user=Depends(get_current_user)`:
    không `require(...)`, không `apply_scope`, và `audit` không có tên trong
    `core/permissions.ENTITIES` nên cũng không có khóa nào để gác.

    Bảng `tab_audit_log` KHÔNG lưu `before`/`after` (chỉ `entity`, `entity_id`,
    `action`, `message` — `audit/model.py:7-16`; bản kế hoạch cụm 07 ghi có
    before/after là **sai**, đã đối chiếu mã). Nhưng `message` là chữ do người
    gọi soạn, và đủ để đọc ra siêu dữ liệu của pháp nhân khác — với
    `entity=assistant` thì là **nguyên văn tham số mọi câu hỏi gửi Trợ lý AI**
    (`assistant/tools/__init__.py:_audit`).

    Cách vá đã chọn (không thêm khóa `audit` vào `ENTITIES`): cắt theo đúng HAI
    chế độ sẵn có của chính route — lối duyệt toàn hệ đòi khóa quản trị, lối
    widget lịch sử đòi quyền đọc entity đó cộng phạm vi của chính bản ghi đó.
    Chi tiết và vế đối chứng ở `test_va_nhat_ky_thao_tac.py`.
    """
    from app.core.permissions import ENTITIES
    from app.core.audit import record
    from app.modules.audit.controller import list_logs

    assert "audit" not in ENTITIES, "đã thêm khóa `audit` → cập nhật bài kiểm này"

    record(db, world.actor("b1").user.id, "leave_request", 77, "approve",
           "Duyệt phiếu NP-B-001 của Nhân sự b1")
    record(db, world.actor("b1").user.id, "assistant", 0, "tool:payable_lookup",
           '{"args": {"supplier": "NCC bí mật của pháp nhân B"}, "rows": 3}')

    khach = world.actor("a1")
    assert khach.profile()["grants"] == [], "không một grant nào"

    def duyet_toan_he():
        return list_logs(
            entity=None, entity_id=None, action=None, search=None, created_by=None,
            from_date=None, to_date=None, page=None, page_size=20, limit=100,
            db=db, user=khach.user)

    with pytest.raises(HTTPException) as loi:
        duyet_toan_he()
    assert loi.value.status_code == 403

    #  Và cũng không lách được bằng cách hỏi đích danh loại chứng từ.
    with pytest.raises(HTTPException) as loi:
        list_logs(entity="assistant", entity_id=None, action=None, search=None,
                  created_by=None, from_date=None, to_date=None, page=None,
                  page_size=20, limit=100, db=db, user=khach.user)
    assert loi.value.status_code == 403


def test_c2_danh_sach_bang_duoc_xuat_loc_theo_quyen_export_tung_bang(db, world):
    """`/api/exports/entities` **không** gọi `_guard_view` (`export_log/controller.py:52-55`).

    Soi mã trước khi gọi là lỗ: `service.available_entities` lọc từng bảng bằng
    `user_has_permission(db, user, e, "export")` (`service.py:39-45`), nên người
    không có quyền xuất gì nhận về danh sách RỖNG. **Không phải lỗ** — đây là
    một cái ô chọn, và nó tự rỗng.
    """
    from app.modules.export_log import service as export_service

    khach = world.actor("a1")
    assert export_service.available_entities(db, khach.user) == []

    world.grant("a1", "employee", scope="company", actions=("read", "export"))
    duoc_xuat = {row["entity"] for row in export_service.available_entities(db, khach.user)}
    assert duoc_xuat == {"employee"}, "chỉ đúng bảng có quyền export, không hơn"


def test_c5_tep_xuat_ra_chi_chua_dong_trong_pham_vi_nguoi_xuat(db, world, monkeypatch):
    """`run_export` đi qua `apply_scope` (`export_log/service.py:88`) — chốt bằng
    NỘI DUNG tệp, không phải bằng "có gọi hàm".

    Kiểm bằng nội dung vì đây là chỗ dữ liệu rời khỏi máy chủ thành một tệp nằm
    trên máy người dùng: gọi đúng hàm mà truyền nhầm entity thì test đếm-lời-gọi
    vẫn xanh.
    """
    from app.modules.export_log import service as export_service

    monkeypatch.setattr(export_service, "_store_file",
                        lambda db, content, filename, media, user_id: 0)

    a1 = world.grant("a1", "employee", scope="company", actions=("read", "export"))
    noi_dung, _ten, _media, so_dong = export_service.run_export(db, a1.user, "employee", "csv")
    van_ban = noi_dung.decode("utf-8-sig")

    ma_trong_tep = {dong.split(",")[0] for dong in van_ban.strip().split("\n")[1:]}
    assert "B1" not in ma_trong_tep, "nhân sự pháp nhân B lọt vào tệp xuất"
    #  `KHONGPHONG` (chưa gắn phòng) VẪN phải có: phạm vi ở đây là `company`, mà
    #  người đó thuộc pháp nhân A. Thiếu họ nghĩa là điều kiện đang lọc nhầm chiều.
    assert ma_trong_tep == {"A1", "A2", "A3", "KHONGTK", "KHONGPHONG"}
    assert so_dong == 5


def test_c6_ai_co_quyen_xuat_MOT_bang_deu_doc_duoc_nhat_ky_xuat_cua_nguoi_khac(db, world):
    """🔴 GHIM HÀNH VI — `_guard_view` không hỏi AI xuất, chỉ hỏi CÓ QUYỀN XUẤT GÌ KHÔNG.

    `export_log/controller.py:36-38`: qua cửa nếu `can_view_any` (có `export`
    trên **bất kỳ** bảng nào) **hoặc** `setting.read`. Sau cửa đó, `list_exports`
    và `get_export` không lọc theo `created_by` và không lọc theo phạm vi
    (`service.py:125-147`).

    Hậu quả cụ thể: người chỉ có `product.export` (một danh mục PUBLIC ai cũng
    xem được) đọc được nhật ký xuất của kế toán trưởng, và `GET /{bid}/file`
    (`controller.py:83-101`) trả lại **đúng tệp đã xuất** — một ảnh chụp toàn bộ
    công nợ của pháp nhân khác, ở thời điểm nó được xuất.

    # QUYẾT ĐỊNH CHỜ: nhật ký Xuất là sổ KIỂM TOÁN (thì phải tách một khóa riêng
    # và bỏ nhánh `can_view_any` đi), hay là "lịch sử xuất CỦA TÔI" (thì phải lọc
    # `created_by == user.id`, chỉ người có khóa kiểm toán mới xem của người
    # khác)? Riêng `/{bid}/file` thì dù chọn đường nào cũng phải chặt hơn danh
    # sách: tệp đã xuất KHÔNG còn được `apply_scope` che nữa.
    """
    from app.core.base_controller import pagination
    from app.modules.export_log import service as export_service
    from app.modules.export_log.controller import _guard_view
    from app.modules.export_log.model import ExportLog

    ke_toan = world.actor("b1")
    db.add(ExportLog(entity="payable", fmt="xlsx", row_count=812,
                     filename="xuat-payable-05092026.xlsx", file_size=99_000, file_id=7,
                     created_by=ke_toan.user.id, updated_by=ke_toan.user.id))
    db.commit()
    ban_ghi = db.query(ExportLog).one()

    #  Người chỉ có quyền xuất DANH MỤC SẢN PHẨM.
    nguoi_kho = world.grant("a1", "product", scope="all", actions=("read", "export"))
    assert export_service.can_view_any(db, nguoi_kho.user) is True
    _guard_view(db, nguoi_kho.user)   # không ném → qua cửa

    trang = {"offset": 0, "limit": 20}
    tong, dong = export_service.list_exports(db, None, None, None, None, None, trang)
    assert tong == 1 and {row.id for row in dong} == {ban_ghi.id}, (
        "hành vi HIỆN TẠI: thấy cả lần xuất của người khác")
    assert export_service.get_export(db, ban_ghi.id).file_id == 7, (
        "hành vi HIỆN TẠI: lấy được `file_id` → `/exports/{id}/file` tải được tệp đó")

    #  Người KHÔNG có quyền xuất gì, cũng không có `setting.read` → vẫn bị chặn.
    with pytest.raises(HTTPException) as loi:
        _guard_view(db, world.actor("a2").user)
    assert loi.value.status_code == 403
    assert callable(pagination)


def test_c3_nhap_du_lieu_gac_bang_quyen_hanh_dong_va_khong_loc_phap_nhan(db, world):
    """`import` khai `PUBLIC` — ai có `import.create` nhập cho MỌI pháp nhân.

    Soi mã: cả 9 route của `import_tool/controller.py` đều gọi
    `_guard`/`_guard_view` → `user_has_permission(db, user, "import", ...)`
    (`controller.py:30-37`). **Không phải lỗ quyền**, nhưng cũng **không có
    tầng lọc theo dòng**: tệp nhập vào tự khai `company_id`/mã pháp nhân của nó.

    # QUYẾT ĐỊNH CHỜ: `import` cố ý là quyền HÀNH ĐỘNG toàn hệ (đã ghi ở
    # BB3_PUBLIC_CO_LY_DO), hay phải chặn dòng nhập ra ngoài pháp nhân của người
    # nhập? Hôm nay chỉ vài người có khóa này nên rủi ro thấp, nhưng đây là
    # đường GHI, không phải đường đọc — hậu quả không cuộn lại được bằng
    # `apply_scope`.
    """
    from app.core.auth import user_has_permission
    from app.core.scoping import PUBLIC, SCOPE_FIELDS
    from app.modules.import_tool.controller import _guard, _guard_view

    assert SCOPE_FIELDS["import"] is PUBLIC

    khach = world.actor("a2")
    for ham in (_guard_view,):
        with pytest.raises(HTTPException) as loi:
            ham(db, khach.user)
        assert loi.value.status_code == 403
    with pytest.raises(HTTPException):
        _guard(db, khach.user, "create")

    nguoi_nhap = world.grant("a1", "import", scope="own",
                             actions=("read", "create", "delete"))
    assert user_has_permission(db, nguoi_nhap.user, "import", "create") is True
    _guard(db, nguoi_nhap.user, "create")     # qua, dù phạm vi khai là `own`
    _guard_view(db, nguoi_nhap.user)


def test_c3_duong_don_du_lieu_dev_chi_song_khi_bat_co_dev_mode(db, world):
    """`DELETE /api/imports/dev/surveys` xóa phiếu khảo sát hàng loạt.

    Nó KHÔNG gọi `_guard` — cổng duy nhất là cờ `DEV_MODE`
    (`import_tool/controller.py:140-141`), mặc định `False`
    (`core/config.py:24`). Bài này chốt hai điều: mặc định là tắt, và khi tắt
    thì bất kỳ ai gọi cũng ăn 403 trước khi chạm vào bảng.
    """
    from app.core.config import settings
    from app.modules.import_tool.controller import dev_delete_surveys

    assert settings.DEV_MODE is False, (
        "DEV_MODE đang BẬT — đường xóa phiếu khảo sát hàng loạt đang mở. "
        "Kiểm `.env` của môi trường đang chạy test.")
    with pytest.raises(HTTPException) as loi:
        dev_delete_surveys(ids="1,2", all_imported=False, db=db,
                           user=world.actor("a1").user)
    assert loi.value.status_code == 403


def test_c4_sao_luu_la_quyen_hanh_dong_toan_he_va_ghim_la_co_y():
    """`backup` — 4 route đều `require("backup", ...)`, không có bảng để lọc.

    Ghim thành lời: bản sao lưu là ảnh chụp **cả cơ sở dữ liệu**, nên khái niệm
    "phạm vi" không áp được lên nó. Ai được cầm bản sao lưu là câu hỏi của cổng
    QUYỀN, và câu trả lời phải là "rất ít người".
    """
    import ast
    import inspect

    from app.core.scoping import PUBLIC, SCOPE_FIELDS
    from app.modules.backup import controller as backup_controller

    assert SCOPE_FIELDS["backup"] is PUBLIC
    nguon = inspect.getsource(backup_controller)
    cay = ast.parse(nguon)
    so_route = sum(
        1 for node in ast.walk(cay) if isinstance(node, ast.FunctionDef)
        and any(isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute)
                and d.func.attr in ("get", "post", "delete", "put", "patch")
                for d in node.decorator_list))
    assert so_route >= 4
    assert nguon.count('require("backup"') >= so_route, (
        "có route sao lưu không đi qua `require(\"backup\", ...)`")


# ══════════════════════════════════════════════════════════════════════════════
#  D. CÔNG VIỆC & DIỄN ĐÀN
# ══════════════════════════════════════════════════════════════════════════════

#  ── D1: 44 route của phân hệ Công việc ────────────────────────────────────────
#
#  `work_task` khai `PUBLIC` KÈM NGHĨA VỤ tự lọc (`core/scoping.py:145-152`).
#  `apply_scope` không cắt gì cho entity này, nên toàn bộ bảo mật nằm ở chỗ MỌI
#  route phải đi qua `membership_service`. Route nào quên là lộ sạch việc của cả
#  công ty — đó là lý do `scoping.py` viết sẵn cảnh báo ở đúng dòng khai PUBLIC.
#
#  Bài kiểm đọc route từ app THẬT rồi lần theo `ast` xuống hàm service, nên nó
#  tự cập nhật: thêm route mới mà quên gác thì đỏ, không cần ai nhớ sửa danh sách.

def test_d1_moi_route_cua_phan_he_cong_viec_deu_qua_cua_thanh_vien():
    """44/44 route phải chứng minh được đường lọc, không nói suông.

    Hai điều kiện, thiếu một là đỏ:
      1. route gọi `_actor(db, user)` — quy người bấm về trục NHÂN SỰ và chặn
         luôn tài khoản không gắn hồ sơ (`membership_service.require_employee`);
      2. mọi hàm service mà route gọi phải chứa một trong bốn cửa gác
         (`get_list_or_403` · `_get_group_or_403` · `get_task_or_403` ·
         `visible_list_ids`/`group_role`).
    """
    import inspect

    routes = list_work_routes()
    assert len(routes) >= 44, f"chỉ thấy {len(routes)} route — kiểm lại việc nạp app.main"

    thieu = []
    for method, path, endpoint, module in routes:
        nguon = inspect.getsource(endpoint)
        if "_actor(db, user)" not in nguon:
            thieu.append(f"{method} {path} — không gọi `_actor(db, user)`")
            continue
        goi = find_service_calls(endpoint, module)
        if not goi:
            thieu.append(f"{method} {path} — không gọi hàm service nào của work/")
            continue
        for ten, ham in goi:
            if not find_guards_in(ham):
                thieu.append(f"{method} {path} → {ten}() không có cửa gác thành viên")

    assert thieu == [], (
        "route của phân hệ Công việc KHÔNG chứng minh được đường lọc:\n  "
        + "\n  ".join(thieu)
        + "\n`work_task` khai PUBLIC nên `apply_scope` không cắt gì — route quên gác "
          "là mở toang việc của cả công ty. Đọc `doc/erp/cong-viec/04-phan-quyen.md` §2."
    )


def test_d1_khong_endpoint_nao_tu_truy_van_bang_cong_viec():
    """Luật đi kèm: controller KHÔNG được tự `db.query(WorkTask/WorkList/...)`.

    Gác đúng ở service mà controller lại tự hỏi thẳng bảng thì bài kiểm trên vẫn
    xanh (nó chỉ soi những hàm service được gọi) còn dữ liệu vẫn ra ngoài.
    """
    import ast
    import inspect

    from app.modules.work import controller as work_controller
    from app.modules.work import task_controller as work_task_controller

    for module in (work_controller, work_task_controller):
        #  Đọc bằng `ast`, không grep chuỗi: chính docstring của hai tệp này có
        #  câu «KHÔNG endpoint nào tự `db.query(...)`», nên grep tự bắt được
        #  lời dặn rồi báo động giả.
        cay = ast.parse(inspect.getsource(module))
        goi_truy_van = [
            node for node in ast.walk(cay)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            and node.func.attr == "query"
            and isinstance(node.func.value, ast.Name) and node.func.value.id == "db"
        ]
        assert goi_truy_van == [], (
            f"{module.__name__} tự truy vấn bảng — mọi đường phải đi qua service, "
            "nơi đã kiểm tư cách thành viên.")


def test_d2_nguoi_ngoai_list_khong_doc_khong_ghi_khong_thay_trong_danh_sach(db, world):
    """Dữ liệu thật + so tập id: người ngoài list thấy đúng RỖNG."""
    from app.modules.work import list_service, task_service
    from app.modules.work.membership_service import visible_list_ids

    du_an = make_work_list(db, world, "A", "Dự án Nhà máy")
    add_list_member(db, du_an, world.emp["a1"])
    viec = make_work_task(db, du_an, "Ký hợp đồng thầu", world.emp["a1"])
    db.commit()

    trong = make_actor_of(db, world, "a1")
    ngoai = make_actor_of(db, world, "a2")

    assert visible_list_ids(db, trong.employee_id, trong.company_id) == {du_an.id}
    assert visible_list_ids(db, ngoai.employee_id, ngoai.company_id) == set()

    assert {row["id"] for row in list_service.get_lists(db, trong)} == {du_an.id}
    assert list_service.get_lists(db, ngoai) == []

    assert task_service.get_task(db, trong, viec.id)["id"] == viec.id
    for goi in (lambda: task_service.get_task(db, ngoai, viec.id),
                lambda: list_service.get_list(db, ngoai, du_an.id),
                lambda: task_service.board(db, ngoai, du_an.id)):
        with pytest.raises(HTTPException) as loi:
            goi()
        assert loi.value.status_code == 403


def test_d2_moi_cheo_phap_nhan_van_khong_lot(db, world):
    """`visible_list_ids` lọc thêm một lớp theo pháp nhân.

    Mời nhầm người của pháp nhân khác vào list là chuyện có thật (ô chọn nhân sự
    không phải lúc nào cũng lọc). Dòng thành viên đó tồn tại nhưng phải vô hiệu.
    """
    from app.modules.work.membership_service import visible_list_ids
    from app.modules.work.model import WorkListMember

    du_an = make_work_list(db, world, "A", "Dự án riêng của A")
    add_list_member(db, du_an, world.emp["b1"])   # mời chéo pháp nhân
    db.commit()

    assert db.query(WorkListMember).count() == 1, "dòng mời chéo phải có thật trong bảng"
    b1 = make_actor_of(db, world, "b1")
    assert visible_list_ids(db, b1.employee_id, b1.company_id) == set()


def test_d3_bon_o_pham_vi_khong_co_tac_dung_len_cong_viec(db, world):
    """Người khai quyền cần biết: hộp thoại «Phạm vi — vai trò» KHÔNG áp cho Công việc.

    `work_task` là `PUBLIC`, nên bốn ô include/exclude không sinh ra điều kiện
    nào. Ai thấy dự án nào hoàn toàn do bảng thành viên quyết. Bài này ghim cả
    hai chiều để không ai đi khai phạm vi rồi tưởng đã chặn xong.
    """
    from app.core.scoping import PUBLIC, SCOPE_FIELDS, apply_scope
    from app.modules.work.membership_service import visible_list_ids
    from app.modules.work.task_model import WorkTask

    assert SCOPE_FIELDS["work_task"] is PUBLIC

    du_an_a = make_work_list(db, world, "A", "Dự án A")
    du_an_b = make_work_list(db, world, "B", "Dự án B")
    viec_a = make_work_task(db, du_an_a, "Việc của A")
    viec_b = make_work_task(db, du_an_b, "Việc của B")
    add_list_member(db, du_an_a, world.emp["a2"])
    db.commit()

    #  Chiều 1: phạm vi khai CHẶT hết mức vẫn không cắt được gì ở `apply_scope`.
    chat = world.grant("a1", "work_task", scope="own",
                       exc_company=["A", "B"], exc_dept=["A.kt", "A.mua"])
    thay = {row.id for row in apply_scope(db.query(WorkTask), WorkTask, "work_task",
                                          chat.user, chat.profile())}
    assert thay == {viec_a.id, viec_b.id}, (
        "apply_scope KHÔNG lọc work_task — mọi chốt nằm ở tầng thành viên")

    #  Chiều 2: phạm vi khai RỘNG hết mức cũng không mở được gì ở tầng thành viên.
    a1 = make_actor_of(db, world, "a1")
    assert visible_list_ids(db, a1.employee_id, a1.company_id) == set()

    #  Và người KHÔNG có grant nào nhưng LÀ thành viên thì vẫn thấy dự án đó.
    a2 = make_actor_of(db, world, "a2")
    assert world.actor("a2").profile()["grants"] == []
    assert visible_list_ids(db, a2.employee_id, a2.company_id) == {du_an_a.id}


def test_d4_bai_dien_dan_cua_phap_nhan_khac_khong_lot_vao_feed(db, world):
    """Luật audience — phòng ban / pháp nhân / công khai, ĐÓNG BĂNG trên từng bài.

    Đóng băng là điểm dễ quên nhất: `dept_id`/`company_id` chép vào bài lúc đăng
    (`forum/service.create_post`), nên người đổi phòng KHÔNG kéo theo bài cũ.
    """
    from app.modules.forum.model import ForumAudience, ForumPost
    from app.modules.forum.service import can_view, list_posts

    a1, b1 = world.actor("a1"), world.actor("b1")
    bai = {}
    for khoa, chu, doi_tuong, cong_ty, phong in (
        ("public", a1, ForumAudience.PUBLIC, world.co["A"], world.dept["A.kt"]),
        ("cty_A", a1, ForumAudience.COMPANY, world.co["A"], world.dept["A.kt"]),
        ("cty_B", b1, ForumAudience.COMPANY, world.co["B"], world.dept["B.kt"]),
        ("phong_A_kt", a1, ForumAudience.DEPT, world.co["A"], world.dept["A.kt"]),
        ("phong_B_kt", b1, ForumAudience.DEPT, world.co["B"], world.dept["B.kt"]),
    ):
        row = ForumPost(body=f"Bài {khoa}", audience=int(doi_tuong),
                        company_id=cong_ty, dept_id=phong,
                        created_by=chu.user.id, updated_by=chu.user.id)
        db.add(row)
        db.flush()
        bai[khoa] = row.id
    db.commit()

    feed_a1 = {row.id for row in list_posts(db, a1.user, a1.profile(), limit=50)}
    assert feed_a1 == {bai["public"], bai["cty_A"], bai["phong_A_kt"]}
    assert bai["cty_B"] not in feed_a1 and bai["phong_B_kt"] not in feed_a1

    feed_b1 = {row.id for row in list_posts(db, b1.user, b1.profile(), limit=50)}
    assert feed_b1 == {bai["public"], bai["cty_B"], bai["phong_B_kt"]}

    #  ⚠️ A.kt và B.kt TRÙNG TÊN «Phòng Kế toán», khác pháp nhân. Nếu luật
    #  audience lỡ so theo TÊN phòng thì hai bài phòng ban trộn vào nhau.
    assert can_view(db, a1.user, db.get(ForumPost, bai["phong_B_kt"])) is False
    assert can_view(db, b1.user, db.get(ForumPost, bai["phong_A_kt"])) is False


def test_d4_doi_phong_ban_khong_keo_theo_bai_cu(db, world):
    """Đóng băng: chuyển a1 sang phòng khác thì bài cũ vẫn thuộc phòng cũ."""
    from app.core.auth import perm_cache_clear
    from app.modules.employee.model import Employee
    from app.modules.forum.model import ForumAudience, ForumPost
    from app.modules.forum.service import can_view

    a1 = world.actor("a1")
    bai = ForumPost(body="Thông báo phòng Kế toán", audience=int(ForumAudience.DEPT),
                    company_id=world.co["A"], dept_id=world.dept["A.kt"],
                    created_by=a1.user.id, updated_by=a1.user.id)
    db.add(bai)
    db.commit()

    a3 = world.actor("a3")   # phòng A.mua — không thấy
    assert can_view(db, a3.user, bai) is False

    emp = db.get(Employee, a3.employee.id)
    emp.department_id = world.dept["A.kt"]
    db.commit()
    perm_cache_clear(a3.user.id)
    assert can_view(db, a3.user, bai) is True, "chuyển về đúng phòng thì thấy"

    #  Ngược lại: tác giả chuyển phòng, bài KHÔNG đi theo.
    emp_a1 = db.get(Employee, a1.employee.id)
    emp_a1.department_id = world.dept["A.mua"]
    db.commit()
    perm_cache_clear(a1.user.id)
    db.refresh(bai)
    assert bai.dept_id == world.dept["A.kt"], "dept_id trên bài phải ĐÓNG BĂNG"
    assert can_view(db, a1.user, bai) is True, "tác giả luôn thấy bài mình"


def test_d5_an_va_xoa_bai_chi_danh_cho_vai_tro_kiem_duyet(db, world):
    """`forum_admin` = người duy nhất có grant `forum_post` (xem seed).

    Người thường KHÔNG cần grant để đăng/đọc — luật audience lo việc đó. Nên
    `can_moderate` phải là cổng DUY NHẤT mở thêm tầm nhìn, và nó đúng bằng
    `user_has_permission(forum_post, read)`.
    """
    from app.modules.forum.model import (ForumAudience, ForumPost,
                                         ForumPostStatus)
    from app.modules.forum.service import can_moderate, can_view, list_posts

    bai_b = ForumPost(body="Bài nội bộ pháp nhân B", audience=int(ForumAudience.COMPANY),
                      company_id=world.co["B"], dept_id=world.dept["B.kt"],
                      created_by=world.actor("b1").user.id,
                      updated_by=world.actor("b1").user.id)
    bai_an = ForumPost(body="Bài đã bị ẩn", audience=int(ForumAudience.PUBLIC),
                       status=int(ForumPostStatus.HIDDEN),
                       company_id=world.co["A"], dept_id=world.dept["A.kt"],
                       created_by=world.actor("b1").user.id,
                       updated_by=world.actor("b1").user.id)
    db.add_all([bai_b, bai_an])
    db.commit()

    thuong = world.actor("a1")
    assert can_moderate(db, thuong.user) is False
    assert can_view(db, thuong.user, bai_b) is False
    assert can_view(db, thuong.user, bai_an) is False

    kiem_duyet = world.grant("a2", "forum_post", scope="all", actions=("read", "write", "delete"))
    assert can_moderate(db, kiem_duyet.user) is True
    assert can_view(db, kiem_duyet.user, bai_b) is True
    assert {row.id for row in list_posts(db, kiem_duyet.user, kiem_duyet.profile(), limit=50)} \
        == {bai_b.id, bai_an.id}, "người kiểm duyệt phải thấy hết mới dọn được"


# ══════════════════════════════════════════════════════════════════════════════
#  E. TRỢ LÝ AI
# ══════════════════════════════════════════════════════════════════════════════

def test_e1_bot_hoi_ho_nguoi_dung_van_bi_pham_vi_cat(db, world):
    """Bot đọc dữ liệu **dưới danh tính người hỏi**, qua tool đã `apply_scope`.

    Hỏng thì hỏng thế nào: `assistant` là khóa cấp cho ban lãnh đạo. Nếu tool
    quên `apply_scope` thì bật Trợ lý AI cho một giám đốc pháp nhân con là mở
    luôn dữ liệu 13 pháp nhân — bằng tiếng Việt, tóm tắt sẵn.
    """
    from app.modules.assistant.tools import run_tool
    from app.modules.payable.model import Payable

    db.add_all([
        Payable(company_id=world.co["A"], supplier_code="NCC-A", supplier_name="NCC của A",
                total=1000, remaining=1000, status="unpaid",
                created_by=ACTOR, updated_by=ACTOR),
        Payable(company_id=world.co["B"], supplier_code="NCC-B", supplier_name="NCC của B",
                total=7777, remaining=7777, status="unpaid",
                created_by=ACTOR, updated_by=ACTOR),
    ])
    db.commit()

    #  Chưa có quyền `payable` → tool từ chối, không trả nửa dữ liệu.
    khach = world.actor("a1")
    assert run_tool(db, khach.user, "payable_lookup", {})["denied"] is True

    a1 = world.grant("a1", "payable", scope="company")
    ket_qua = run_tool(db, a1.user, "payable_lookup", {})
    assert {row["supplier_code"] for row in ket_qua["items"]} == {"NCC-A"}
    assert ket_qua["summary"]["remaining"] == 1000.0, "tổng cũng phải nằm trong phạm vi"

    #  Quản trị toàn hệ thì thấy cả hai — chốt rằng phạm vi mới là thứ cắt, không
    #  phải một bộ lọc cứng nào đó nằm trong tool.
    toan_he = world.grant("a2", "payable", scope="all")
    assert {row["supplier_code"] for row in run_tool(db, toan_he.user, "payable_lookup", {})["items"]} \
        == {"NCC-A", "NCC-B"}


#  ── E2: LUẬT BẤT BIẾN cho lớp tool ────────────────────────────────────────────
#
#  Mỗi tool là một đường đọc dữ liệu MỚI, nằm ngoài mọi controller — nên nó
#  không được `require(...)` nào che, và cũng không lọt vào bài kiểm BB-4
#  (danh sách đó chỉ soi tệp `*controller*.py`). Bảng dưới là chỗ khai *tool này
#  gác bằng gì*; thêm tool mà quên khai thì đỏ.
E2_CUA_GAC_CUA_TUNG_TOOL = {
    # (a) đọc bảng nghiệp vụ → BẮT BUỘC apply_scope/get_scoped
    "payable_lookup": "apply_scope(Payable, 'payable')",
    "payment_request_read": "apply_scope(PaymentRequest, 'payment_request')",
    "draft_payment_request": "apply_scope + ctx.can(payment_request, create)",
    "procurement_doc_read": "apply_scope theo entity của chứng từ",
    "pending_procurement_approvals": "apply_scope + ctx.can(entity, approve)",
    "my_procurement_requests": "apply_scope + lọc chính chủ",
    "propose_document_update": "get_scoped(action='write') — đường GHI",
    "document_search": "access_service.visible_condition + giấu bản riêng",
    "document_read": "access_service.visible_condition",
    "my_documents": "văn bản của CHÍNH người hỏi",
    "approval_flow_lookup": "ctx.can(approval_flow) — cấu hình, không phải chứng từ",
    "contract_list_by_expiry": "apply_scope qua `catalog._scoped_contracts`",
    "contract_count_by_status": "apply_scope qua `catalog._scoped_contracts`",
    "supplier_contracts": "apply_scope qua `catalog._scoped_contracts`",
    "recent_purchase_orders": "apply_scope(PurchaseOrder, 'purchase_order')",
    # (a-bis) đọc `tab_purchase_history` — bảng LỊCH SỬ GIÁ, không có khóa phạm vi
    #  ⚠️ Bảng này CÓ `company_id` nhưng `purchase_history` không nằm trong
    #  `ENTITIES`, nên không entity nào để `apply_scope`. Cổng duy nhất là
    #  `ctx.can("product")` (+ `ctx.can("supplier")` khi câu trả lời nêu tên
    #  NCC) — hai khóa của danh mục PUBLIC. Giống hệt màn «Lịch sử mua hàng»
    #  của giao diện, nên đây KHÔNG phải lỗ riêng của Trợ lý AI.
    #  # QUYẾT ĐỊNH CHỜ: giá mua theo pháp nhân có phải dữ liệu dùng chung
    #  # toàn tập đoàn không? Xem báo cáo cụm 07 mục E2.
    "product_search": "danh mục PUBLIC — cổng là ctx.can(product)",
    "supplier_search": "danh mục PUBLIC — cổng là ctx.can(supplier)",
    "product_purchase_history": "ctx.can(product) (+supplier để hiện tên NCC) — bảng lịch sử giá",
    "product_best_price": "ctx.can(product) + ctx.can(supplier) — bảng lịch sử giá",
    "suppliers_for_product": "ctx.can(product) + ctx.can(supplier) — bảng lịch sử giá",
    "recent_purchases": "ctx.can(product) (+supplier để hiện tên NCC) — bảng lịch sử giá",
    "top_suppliers_by_purchase": "ctx.can(supplier) — bảng lịch sử giá, số gộp",
    "purchase_report": "ctx.can(product) (+supplier) — bảng lịch sử giá, số gộp",
    "analytics_query": "ctx.can(product); chiều `supplier` đòi thêm ctx.can(supplier)",
    # (b) dữ liệu của CHÍNH người hỏi — lọc bằng employee_id/user_id, không phải phạm vi
    "my_approval_tasks": "task_service.my_tasks(employee_id) — hộp việc của chính mình",
    "my_requests_status": "lọc theo started_by_employee_id — phiếu chính mình trình",
    "my_tickets": "lọc theo created_by/requester_id + ctx.can(ticket, read)",
    # (c) đường GHI mới, không đọc gì của người khác
    "ticket_create": "ctx.can(ticket, create)",
    "draft_survey_request": "ctx.can(survey_request, create) — chỉ soạn nháp",
    "draft_purchase_request": "ctx.can(purchase_request, create) — chỉ soạn nháp",
    "draft_leave_request": "ctx.can(leave_request, create) — chỉ soạn nháp",
    # (d) không tra thêm dữ liệu nào
    "export_report_file": "dựng tệp từ kết quả tool khác (đã qua apply_scope)",
    "export_excel_file": "cùng lý do export_report_file",
    "search_docs": "bài Trung tâm HDSD — nội dung mọi người đăng nhập đều đọc được",
}


def test_e2_moi_tool_cua_tro_ly_ai_deu_phai_khai_cua_gac():
    """Thêm một tool = mở một đường đọc dữ liệu nằm ngoài mọi controller.

    Bài kiểm DANH SÁCH TRẮNG (cùng khuôn BB-4): nó không tự biết tool nào cần
    lọc, việc nó làm được là **không cho ai lặng lẽ thêm một đường đọc mới**.
    """
    from app.core.config import settings
    from app.modules.assistant.tools import _active_specs

    rag_cu = settings.AI_RAG_ENABLED
    settings.AI_RAG_ENABLED = True   # bật để `search_docs` cũng nằm trong bài kiểm
    try:
        dang_bat = {spec.name for spec in _active_specs()}
    finally:
        settings.AI_RAG_ENABLED = rag_cu

    chua_khai = sorted(dang_bat - set(E2_CUA_GAC_CUA_TUNG_TOOL))
    assert chua_khai == [], (
        f"{len(chua_khai)} tool chưa khai cửa gác: {chua_khai}. Thêm vào "
        "E2_CUA_GAC_CUA_TUNG_TOOL kèm MỘT CÂU nói rõ nó lọc bằng gì "
        "(apply_scope / dữ liệu của chính người hỏi / chỉ ghi). Soi mã trước.")
    het_han = sorted(set(E2_CUA_GAC_CUA_TUNG_TOOL) - dang_bat)
    assert het_han == [], f"tool đã bỏ nhưng còn tên trong bảng: {het_han}"


def test_e2_tool_doc_bang_nghiep_vu_deu_co_apply_scope_trong_ma():
    """Nhóm (a) của bảng trên: chứng minh bằng MÃ, không bằng lời khai.

    Bảng khai là ý định; bài này kiểm ý định đó có nằm trong tệp thật không.
    Chỉ soi nhóm đọc bảng nghiệp vụ — nhóm "dữ liệu của chính mình" cố ý không
    dùng `apply_scope` (dùng thì người nghỉ phép không xem được đơn của mình).
    """
    import inspect

    from app.modules.assistant.tools import (catalog, document_tool,
                                             payable_tool,
                                             procurement_doc_tool, update_tool)

    for module, dau_hieu in (
        (payable_tool, "apply_scope"),
        (procurement_doc_tool, "apply_scope"),
        (catalog, "apply_scope"),
        (update_tool, "get_scoped"),
        (document_tool, "visible_condition"),
    ):
        nguon = inspect.getsource(module)
        assert dau_hieu in nguon, (
            f"{module.__name__} không còn `{dau_hieu}` — tool này đọc bảng nghiệp vụ "
            "nên phải lọc theo phạm vi người hỏi.")


def test_e3_goi_tri_thuc_di_vao_moi_cau_hoi_khong_phan_biet_phap_nhan():
    """🔴 GHIM HÀNH VI — `packs/` là MỘT gói dùng chung cho mọi người đăng nhập.

    `knowledge.load_pack()` ghép mọi tệp `.md` trong `packs/` và `build_system()`
    **không nhận** `user`/`company` (`assistant/knowledge.py:38-60`), nên mọi
    người nhận đúng một gói. Chính README của thư mục ghi «Quyền theo gói … là
    việc của Phase sau».

    Hôm nay gói đó có `nhamay-tri-thuc-co-dong.md` — tri thức nội bộ của **một**
    pháp nhân (Nhà máy DEGO Organic, Cần Thơ): tên Giám đốc/Phó Giám đốc, quyết
    định của Ban điều hành tạm, mã văn bản nội bộ.

    # QUYẾT ĐỊNH CHỜ: nội dung này có được xem là dùng chung toàn tập đoàn không?
    # Nếu không thì phải tách gói theo pháp nhân (thêm tham số vào `build_system`)
    # — chứ không phải xóa tệp, vì đúng những người ở nhà máy đó đang cần nó.
    """
    import inspect

    from app.modules.assistant import knowledge

    tham_so = set(inspect.signature(knowledge.build_system).parameters)
    assert tham_so == {"extra"}, (
        "`build_system` nay có tham số mới — nếu là `user`/`company_id` thì gói tri thức "
        "đã tách theo pháp nhân, cập nhật lại bài kiểm này.")

    goi = knowledge.load_pack()
    assert goi, "gói tri thức rỗng — kiểm lại đường dẫn `packs/`"
    assert "DEGO Organic" in goi, (
        "hành vi HIỆN TẠI: gói dùng chung đang chứa tri thức nội bộ của một pháp nhân")

    #  Không có dãy 10–13 chữ số: đó là hình dạng của MÃ SỐ THUẾ và SỐ TÀI
    #  KHOẢN. Gói này đi vào MỌI câu hỏi của MỌI người, nên một số định danh lọt
    #  vào đây là lộ cho toàn hệ, không cách nào thu lại.
    #
    #  Ngưỡng 10 chứ không phải 9: mã phiếu của hệ là 9 chữ số
    #  (`YCBG260826001` — ngày + số thứ tự), nó là VÍ DỤ MINH HỌA trong tài liệu
    #  quy trình, không phải dữ liệu thật của ai.
    import re

    so_dai = sorted(set(re.findall(r"\d{10,13}", goi)))
    assert so_dai == [], (
        f"gói tri thức chứa dãy số dài {so_dai} — nghi mã số thuế / số tài khoản. "
        "Gói này đi vào MỌI câu hỏi của MỌI người, không đưa số định danh vào đây.")


def test_e3_khoa_assistant_la_cong_quyen_khong_phai_cong_pham_vi():
    """`assistant` khai `PUBLIC` — cố ý, và đây là chỗ ghi lý do thành lời.

    Bot không có bảng nào của riêng nó để lọc; mọi dữ liệu nó chạm đều đi qua
    `apply_scope` của từng tool (bài E1/E2). Khóa `assistant` chỉ trả lời câu
    «ai được dùng Trợ lý AI».
    """
    from app.core.permissions import ENTITIES
    from app.core.scoping import PUBLIC, SCOPE_FIELDS

    assert "assistant" in ENTITIES
    assert SCOPE_FIELDS["assistant"] is PUBLIC


# ══════════════════════════════════════════════════════════════════════════════
#  Bài tự kiểm của tệp — dữ liệu thật, không phải `is not None`
# ══════════════════════════════════════════════════════════════════════════════

def test_khung_du_lieu_cua_cum_07_dung_duoc(db, world):
    """Hỏng khung dựng thì mọi ca ở trên đỏ/xanh vì lý do sai."""
    from app.modules.approval.instance_model import TASK_PENDING, ApprovalTask
    from app.modules.leave.request_model import LeaveRequest

    don = make_leave_request(db, world, "b1", "NP-TU-KIEM")
    phien = make_instance(db, "leave_request", don.id, code="NP-TU-KIEM")
    viec = open_task_for(db, phien, world.emp["a1"])
    db.commit()

    assert db.query(LeaveRequest).count() == 1
    assert don.company_id == world.co["B"] and don.department_id == world.dept["B.kt"]
    assert db.get(ApprovalTask, viec.id).status == TASK_PENDING
    assert phien.status == 1 and phien.entity_id == don.id
    assert isinstance(datetime.now() - timedelta(days=1), datetime)
