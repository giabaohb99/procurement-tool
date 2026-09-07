"""ÉP TẢI (07/09/2026) — đơn nghỉ phép gặp một LUỒNG DUYỆT BỊ SỬA GIỮA CHỪNG.

`test_nghi_phep_qua_bo_may_duyet.py` chạy vòng đời đẹp: một chặng, một người
duyệt, không ai đụng vào luồng. Tệp này chạy phần XẤU — những thứ xảy ra thật
trên hệ đang chạy vì quản trị sửa luồng trong lúc phiếu đang bay:

    nhiều chặng · song song · trùng người · ĐỔI người duyệt giữa chừng ·
    TẮT người duyệt · sửa luồng khi phiếu đã đóng · tắt cờ bộ máy

**Sợi chỉ xuyên suốt: SỔ QUỸ PHÉP.** Luồng duyệt hỏng kiểu gì thì cũng chỉ có
ba kết cục đúng cho quỹ, và mọi bài dưới đây đo đúng ba cái đó:

    còn treo   →  giữ chỗ nguyên vẹn      (`pending_days` không nhúc nhích)
    duyệt xong →  trừ THẬT, đúng MỘT lần  (`used_days` cộng một lần duy nhất)
    không duyệt→  trả lại ĐỦ, đúng MỘT lần

Trừ hai lần và trả hai lần đều **không có triệu chứng** cho tới khi ai đó cộng
tay lại sổ cuối năm — nên chỗ này phải có bài canh, không thể trông vào việc
người dùng sẽ báo.
"""
from datetime import date, timedelta
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.modules.approval import (action_service, flow_sync_service,
                                  instance_service)
from app.modules.approval.flow_model import (APPROVER_DEPT_HEAD,
                                             APPROVER_EMPLOYEE, MULTI_ALL,
                                             MULTI_ANY, MULTI_SEQUENTIAL,
                                             NO_APPROVER_BLOCK,
                                             NO_APPROVER_FALLBACK, SKIP_NONE,
                                             SKIP_ADJACENT, ApprovalFlow,
                                             ApprovalNode, ApprovalSwitch)
from app.modules.approval.instance_model import (INSTANCE_APPROVED,
                                                 INSTANCE_BLOCKED,
                                                 INSTANCE_REJECTED,
                                                 INSTANCE_RUNNING,
                                                 TASK_APPROVED,
                                                 TASK_CANCELLED, TASK_PENDING,
                                                 TASK_SKIPPED_DUPLICATE,
                                                 TASK_WAITING)
from app.modules.employee.model import Employee
from app.modules.leave import approval_bridge, balance_service, request_service
from app.modules.leave.catalog_model import LeaveType
from app.modules.leave.constants import (LR_APPROVED, LR_CANCELLED, LR_PENDING,
                                         LR_REJECTED)
from app.modules.leave.balance_model import LeaveBalance
from app.modules.leave.schema import LeaveRequestCreate, LeaveRequestUpdate

ACTOR = 1
ENTITY = "leave_request"
MONDAY = date(2026, 1, 5)
YEAR = 2026


# ── Dựng cảnh ───────────────────────────────────────────────────────────────

@pytest.fixture()
def leave_type(db):
    obj = LeaveType(code="annual", name="Phép năm", counts_balance=True,
                    annual_quota_days=12.0)
    db.add(obj)
    db.flush()
    return obj


def _employee(db, code, name, department_id=7, active=True):
    obj = Employee(code=code, full_name=name, company_id=1,
                   department_id=department_id, is_active=active)
    db.add(obj)
    db.flush()
    return obj


@pytest.fixture()
def submitter(db):
    return _employee(db, "NV_NOP", "Người nộp")


@pytest.fixture()
def sep(db):
    """Ba người duyệt dùng chung cho mọi cảnh — đặt tên theo VAI, không theo số."""
    return SimpleNamespace(
        a=_employee(db, "NV_A", "Duyệt A"),
        b=_employee(db, "NV_B", "Duyệt B"),
        c=_employee(db, "NV_C", "Duyệt C"),
    )


@pytest.fixture()
def flow(db):
    """Luồng RỖNG, cờ đã bật. Mỗi bài tự khai bước của riêng nó."""
    row = ApprovalFlow(entity=ENTITY, code="NP-STRESS", name="Ép tải nghỉ phép",
                       is_active=True, created_by=ACTOR, updated_by=ACTOR)
    db.add(row)
    db.add(ApprovalSwitch(entity=ENTITY, is_enabled=True,
                          created_by=ACTOR, updated_by=ACTOR))
    db.flush()
    return row


def _node(db, flow, seq, name, *, employees=None, kind=APPROVER_EMPLOYEE,
          multi_mode=MULTI_ANY, skip_duplicate=SKIP_NONE,
          on_no_approver=NO_APPROVER_BLOCK, fallback=None):
    node = ApprovalNode(
        flow_id=flow.id, seq=seq, name=name,
        approver_kind=kind,
        approver_ref=",".join(str(e.id) for e in (employees or [])),
        multi_mode=multi_mode, skip_duplicate=skip_duplicate,
        on_no_approver=on_no_approver,
        fallback_employee_id=fallback.id if fallback else None,
        created_by=ACTOR, updated_by=ACTOR)
    db.add(node)
    db.flush()
    return node


def _user(employee: Employee, uid: int = ACTOR):
    return SimpleNamespace(id=uid, employee_id=employee.id)


def _submit(db, leave_type, employee, days=2):
    """Lập đơn rồi gửi duyệt qua đúng đường controller đi."""
    user = _user(employee)
    obj = request_service.create(db, LeaveRequestCreate(
        leave_type_id=leave_type.id,
        from_date=MONDAY, to_date=MONDAY + timedelta(days=days - 1),
        reason="Về quê"), user)
    emp = request_service.prepare_submit(db, obj, user)
    instance_id = approval_bridge.start_approval(db, obj, user)
    obj = request_service.mark_submitted(db, obj, emp, user, instance_id)
    return obj, instance_service.running_instance(db, ENTITY, obj.id)


def _sync(db, node):
    """Sửa bước xong thì đẩy xuống phiếu đang chạy — đúng thứ controller làm."""
    return flow_sync_service.sync_after_step_edit(
        db, node, ACTOR, lambda entity, entity_id: {})


def _book(db, employee, leave_type):
    """Ba con số của sổ quỹ: (giữ chỗ, đã dùng, còn lại)."""
    row = balance_service.get_balance(db, employee.id, YEAR, leave_type.id)
    return (row.pending_days, row.used_days, row.remaining_days)


def _tasks(db, instance, *, seq=None):
    rows = instance_service.tasks_of_instance(db, instance.id)
    return [t for t in rows if seq is None or t.node_seq == seq]


def _states(db, instance, seq=None):
    return sorted((t.assignee_employee_id, t.status) for t in _tasks(db, instance, seq=seq))


# ── 1. NHIỀU BƯỚC tuần tự ───────────────────────────────────────────────────

def test_hai_chang_thi_ky_chang_mot_KHONG_tru_quy(db, flow, leave_type, submitter, sep):
    """Ký nửa chừng mà đã trừ thật là sổ lệch suốt thời gian phiếu còn bay."""
    _node(db, flow, 1, "Trưởng bộ phận", employees=[sep.a])
    _node(db, flow, 2, "Trưởng nhân sự", employees=[sep.b])
    obj, instance = _submit(db, leave_type, submitter)

    action_service.approve(db, instance, sep.a.id, ACTOR, {})
    db.refresh(obj)

    assert obj.status == LR_PENDING
    assert _book(db, submitter, leave_type) == (2.0, 0.0, 10.0)
    #  Chặng 2 phải MỞ ra ngay, không đợi ai bấm gì thêm.
    assert [t.status for t in _tasks(db, instance, seq=2)] == [TASK_PENDING]


def test_ky_du_hai_chang_thi_tru_dung_MOT_lan(db, flow, leave_type, submitter, sep):
    _node(db, flow, 1, "Trưởng bộ phận", employees=[sep.a])
    _node(db, flow, 2, "Trưởng nhân sự", employees=[sep.b])
    obj, instance = _submit(db, leave_type, submitter)

    action_service.approve(db, instance, sep.a.id, ACTOR, {})
    action_service.approve(db, instance, sep.b.id, ACTOR, {})
    db.refresh(obj)
    db.refresh(instance)

    assert (obj.status, instance.status) == (LR_APPROVED, INSTANCE_APPROVED)
    assert _book(db, submitter, leave_type) == (0.0, 2.0, 10.0)


def test_nguoi_chang_SAU_khong_ky_vuot_chang_truoc(db, flow, leave_type, submitter, sep):
    """Ký vượt là đơn có hiệu lực mà chặng đầu chưa ai xem."""
    _node(db, flow, 1, "Trưởng bộ phận", employees=[sep.a])
    _node(db, flow, 2, "Trưởng nhân sự", employees=[sep.b])
    obj, instance = _submit(db, leave_type, submitter)

    with pytest.raises(HTTPException) as caught:
        action_service.approve(db, instance, sep.b.id, ACTOR, {})
    assert "không có việc nào đang chờ" in caught.value.detail
    assert _book(db, submitter, leave_type) == (2.0, 0.0, 10.0)


def test_tu_choi_o_chang_HAI_tra_lai_du_quy(db, flow, leave_type, submitter, sep):
    _node(db, flow, 1, "Trưởng bộ phận", employees=[sep.a])
    _node(db, flow, 2, "Trưởng nhân sự", employees=[sep.b])
    obj, instance = _submit(db, leave_type, submitter)

    action_service.approve(db, instance, sep.a.id, ACTOR, {})
    action_service.reject(db, instance, sep.b.id, ACTOR, "Cuối năm nhiều việc")
    db.refresh(obj)
    db.refresh(instance)

    assert (obj.status, instance.status) == (LR_REJECTED, INSTANCE_REJECTED)
    #  Chữ ký chặng 1 vẫn còn nguyên trong dấu vết — từ chối không xóa lịch sử.
    assert _book(db, submitter, leave_type) == (0.0, 0.0, 12.0)
    assert (sep.a.id, TASK_APPROVED) in _states(db, instance)


# ── 2. SONG SONG trong một chặng ────────────────────────────────────────────

def test_song_song_TAT_CA_phai_ky(db, flow, leave_type, submitter, sep):
    _node(db, flow, 1, "Ban giám đốc", employees=[sep.a, sep.b], multi_mode=MULTI_ALL)
    obj, instance = _submit(db, leave_type, submitter)

    #  Cả hai việc mở CÙNG LÚC — đó là điểm khác của song song với lần lượt.
    assert _states(db, instance) == sorted(
        [(sep.a.id, TASK_PENDING), (sep.b.id, TASK_PENDING)])

    action_service.approve(db, instance, sep.a.id, ACTOR, {})
    db.refresh(obj)
    assert obj.status == LR_PENDING
    assert _book(db, submitter, leave_type) == (2.0, 0.0, 10.0)

    action_service.approve(db, instance, sep.b.id, ACTOR, {})
    db.refresh(obj)
    assert obj.status == LR_APPROVED
    assert _book(db, submitter, leave_type) == (0.0, 2.0, 10.0)


def test_song_song_MOT_NGUOI_la_du_thi_viec_con_lai_bi_HUY(db, flow, leave_type,
                                                            submitter, sep):
    """Việc thừa phải đóng lại. Để treo thì người kia mở hộp việc ra vẫn thấy
    một tờ đơn đã duyệt xong nằm chờ chữ ký của mình."""
    _node(db, flow, 1, "Ban giám đốc", employees=[sep.a, sep.b], multi_mode=MULTI_ANY)
    obj, instance = _submit(db, leave_type, submitter)

    action_service.approve(db, instance, sep.a.id, ACTOR, {})
    db.refresh(obj)

    assert obj.status == LR_APPROVED
    assert (sep.b.id, TASK_CANCELLED) in _states(db, instance)
    assert _book(db, submitter, leave_type) == (0.0, 2.0, 10.0)


def test_song_song_MOT_NGUOI_TU_CHOI_thi_ca_phieu_dung(db, flow, leave_type,
                                                        submitter, sep):
    _node(db, flow, 1, "Ban giám đốc", employees=[sep.a, sep.b], multi_mode=MULTI_ALL)
    obj, instance = _submit(db, leave_type, submitter)

    action_service.reject(db, instance, sep.b.id, ACTOR, "Trùng lịch dự án")
    db.refresh(obj)

    assert obj.status == LR_REJECTED
    #  Trả lại ĐÚNG MỘT LẦN, dù chặng có hai việc.
    assert _book(db, submitter, leave_type) == (0.0, 0.0, 12.0)


def test_lan_luot_thi_nguoi_sau_CHUA_TOI_luot(db, flow, leave_type, submitter, sep):
    _node(db, flow, 1, "Ký nháy rồi ký chính", employees=[sep.a, sep.b],
          multi_mode=MULTI_SEQUENTIAL)
    obj, instance = _submit(db, leave_type, submitter)

    assert _states(db, instance) == sorted(
        [(sep.a.id, TASK_PENDING), (sep.b.id, TASK_WAITING)])

    action_service.approve(db, instance, sep.a.id, ACTOR, {})
    #  Người thứ hai mới được mở ra sau khi người thứ nhất ký.
    assert _states(db, instance) == sorted(
        [(sep.a.id, TASK_APPROVED), (sep.b.id, TASK_PENDING)])
    db.refresh(obj)
    assert obj.status == LR_PENDING


# ── 3. NHIỀU BƯỚC CHUNG MỘT NGƯỜI ───────────────────────────────────────────

def test_trung_nguoi_o_chang_lien_truoc_thi_TU_QUA(db, flow, leave_type, submitter, sep):
    """Bắt một người ký hai lần cho cùng tờ đơn là thao tác vô nghĩa với họ."""
    _node(db, flow, 1, "Trưởng bộ phận", employees=[sep.a])
    _node(db, flow, 2, "Trưởng nhân sự", employees=[sep.a], skip_duplicate=SKIP_ADJACENT)
    obj, instance = _submit(db, leave_type, submitter)

    action_service.approve(db, instance, sep.a.id, ACTOR, {})
    db.refresh(obj)

    assert obj.status == LR_APPROVED
    #  ⚠️ Bước tự qua ghi TRẠNG THÁI RIÊNG, không ghi thành "đã duyệt": bản in
    #  phải phân biệt *người này đã ký* với *bước này tự qua vì trùng người*.
    assert [t.status for t in _tasks(db, instance, seq=2)] == [TASK_SKIPPED_DUPLICATE]
    #  Và quỹ vẫn chỉ trừ một lần, dù đi qua hai chặng.
    assert _book(db, submitter, leave_type) == (0.0, 2.0, 10.0)


def test_trung_nguoi_nhung_khai_KHONG_BO_QUA_thi_van_phai_ky(db, flow, leave_type,
                                                              submitter, sep):
    _node(db, flow, 1, "Trưởng bộ phận", employees=[sep.a])
    _node(db, flow, 2, "Trưởng nhân sự", employees=[sep.a], skip_duplicate=SKIP_NONE)
    obj, instance = _submit(db, leave_type, submitter)

    action_service.approve(db, instance, sep.a.id, ACTOR, {})
    db.refresh(obj)
    assert obj.status == LR_PENDING

    action_service.approve(db, instance, sep.a.id, ACTOR, {})
    db.refresh(obj)
    assert obj.status == LR_APPROVED
    assert _book(db, submitter, leave_type) == (0.0, 2.0, 10.0)


def test_NGUOI_NOP_la_nguoi_duyet_thi_bi_loai_khoi_chang(db, flow, leave_type, sep):
    """I08 — không ai tự duyệt đơn của chính mình.

    Người nộp ở đây CHÍNH là trưởng phòng, và bước khai «trưởng phòng người
    nộp» nên máy tính ra đúng tên họ. Bước rỗng người → phiếu KẸT, chứ tuyệt
    đối không tự đi tiếp.
    """
    truong_phong = _employee(db, "NV_TP", "Trưởng phòng")
    from app.modules.department.model import Department
    db.add(Department(id=7, code="P7", name="Phòng 7", manager_id=truong_phong.id))
    db.flush()

    _node(db, flow, 1, "Trưởng bộ phận duyệt", kind=APPROVER_DEPT_HEAD)

    #  ĐỐI CHỨNG trước: nhân viên thường nộp thì bước tính ra đúng trưởng phòng
    #  và phiếu chạy. Không có vế này thì bài dưới xanh cả khi cơ chế «trưởng
    #  phòng người nộp» hỏng hoàn toàn — kẹt vì lý do khác mà vẫn kẹt.
    nhan_vien = _employee(db, "NV_TX", "Nhân viên")
    _, chay = _submit(db, leave_type, nhan_vien)
    assert chay.status == INSTANCE_RUNNING
    assert _states(db, chay) == [(truong_phong.id, TASK_PENDING)]

    obj, instance = _submit(db, leave_type, truong_phong)
    db.refresh(instance)

    assert instance.status == INSTANCE_BLOCKED
    assert obj.status == LR_PENDING
    #  ⚠️ Kẹt thì quỹ vẫn GIỮ CHỖ: đơn chưa hỏng, nó chỉ đang chờ người sửa
    #  luồng. Trả quỹ ở đây là mở đường nộp chồng đơn trong lúc chờ.
    assert _book(db, truong_phong, leave_type) == (2.0, 0.0, 10.0)


# ── 4. ĐỔI NGƯỜI DUYỆT giữa chừng (CR-114) ──────────────────────────────────

def test_doi_nguoi_duyet_chang_DANG_CHO_thi_viec_sang_tay_nguoi_moi(db, flow, leave_type,
                                                                     submitter, sep):
    node = _node(db, flow, 1, "Trưởng bộ phận", employees=[sep.a])
    obj, instance = _submit(db, leave_type, submitter)

    node.approver_ref = str(sep.b.id)
    db.flush()
    assert _sync(db, node) == 1
    db.commit()

    assert _states(db, instance) == sorted(
        [(sep.a.id, TASK_CANCELLED), (sep.b.id, TASK_PENDING)])
    #  Đổi người không phải là đổi quỹ.
    assert _book(db, submitter, leave_type) == (2.0, 0.0, 10.0)


def test_nguoi_duyet_CU_khong_ky_duoc_nua(db, flow, leave_type, submitter, sep):
    """Việc đã hủy mà vẫn ký được thì đổi người duyệt chỉ là trang trí."""
    node = _node(db, flow, 1, "Trưởng bộ phận", employees=[sep.a])
    obj, instance = _submit(db, leave_type, submitter)

    node.approver_ref = str(sep.b.id)
    db.flush()
    _sync(db, node)
    db.commit()

    with pytest.raises(HTTPException) as caught:
        action_service.approve(db, instance, sep.a.id, ACTOR, {})
    assert "không có việc nào đang chờ" in caught.value.detail
    db.refresh(obj)
    assert obj.status == LR_PENDING


def test_nguoi_duyet_MOI_ky_thi_don_duyet_va_tru_dung_mot_lan(db, flow, leave_type,
                                                               submitter, sep):
    node = _node(db, flow, 1, "Trưởng bộ phận", employees=[sep.a])
    obj, instance = _submit(db, leave_type, submitter)

    node.approver_ref = str(sep.b.id)
    db.flush()
    _sync(db, node)
    db.commit()

    action_service.approve(db, instance, sep.b.id, ACTOR, {})
    db.refresh(obj)

    assert obj.status == LR_APPROVED
    assert _book(db, submitter, leave_type) == (0.0, 2.0, 10.0)


def test_doi_nguoi_khi_chang_SONG_SONG_da_ky_MOT_NUA(db, flow, leave_type,
                                                       submitter, sep):
    """⚠️ LỖI THẬT, bắt được bằng chính bộ ép tải này (07/09/2026).

    Chặng «cả hai phải duyệt» của A và B. A ký xong, B chưa. Quản trị đổi
    B → C. Bản cũ tính lại danh sách người duyệt ra `[A, C]` rồi mở việc mới
    cho **cả hai** — tức A bị đòi ký lần thứ hai cho đúng cái chặng vừa ký, và
    chặng đứng im chờ chữ ký đó. Một lượt sửa luồng nhằm GỠ tắc lại đẻ ra tắc
    mới, không báo gì. A mà đã nghỉ việc thì phiếu chết hẳn.

    Đúng phải là: chữ ký của A giữ nguyên, chỉ B bị thay bằng C, và C ký là
    xong chặng.
    """
    node = _node(db, flow, 1, "Ban giám đốc", employees=[sep.a, sep.b],
                 multi_mode=MULTI_ALL)
    obj, instance = _submit(db, leave_type, submitter)
    action_service.approve(db, instance, sep.a.id, ACTOR, {})

    node.approver_ref = f"{sep.a.id},{sep.c.id}"
    db.flush()
    _sync(db, node)
    db.commit()

    assert _states(db, instance) == sorted([
        (sep.a.id, TASK_APPROVED),    # chữ ký cũ còn nguyên, KHÔNG bị đòi lại
        (sep.b.id, TASK_CANCELLED),
        (sep.c.id, TASK_PENDING),
    ])

    action_service.approve(db, instance, sep.c.id, ACTOR, {})
    db.refresh(obj)
    db.refresh(instance)

    assert (obj.status, instance.status) == (LR_APPROVED, INSTANCE_APPROVED)
    assert _book(db, submitter, leave_type) == (0.0, 2.0, 10.0)


def test_sua_VO_HAI_tren_chang_da_ky_mot_nua_khong_da_van_viec_con_lai(
        db, flow, leave_type, submitter, sep):
    """Đổi tên bước thì không được đụng vào việc người ta đang mở dở.

    Cùng gốc với bài trên: `old` chỉ có B (người còn treo) trong khi danh sách
    tính ra là [A, B], hai vế không bằng nhau nên rơi vào nhánh dựng lại — dù
    người duyệt chẳng đổi gì.
    """
    node = _node(db, flow, 1, "Ban giám đốc", employees=[sep.a, sep.b],
                 multi_mode=MULTI_ALL)
    obj, instance = _submit(db, leave_type, submitter)
    action_service.approve(db, instance, sep.a.id, ACTOR, {})
    task_b = [t for t in _tasks(db, instance) if t.assignee_employee_id == sep.b.id][0]

    node.name = "Ban giám đốc (đổi tên)"
    db.flush()
    _sync(db, node)
    db.commit()

    still = [t for t in _tasks(db, instance) if t.assignee_employee_id == sep.b.id]
    assert [(t.id, t.status) for t in still] == [(task_b.id, TASK_PENDING)]


def test_doi_nguoi_o_buoc_CHUA_TOI_thi_khong_dung_viec_dang_treo(db, flow, leave_type,
                                                                  submitter, sep):
    """Bản chụp vá là đủ; tới lượt nó sẽ tự tính theo người mới."""
    _node(db, flow, 1, "Trưởng bộ phận", employees=[sep.a])
    node2 = _node(db, flow, 2, "Trưởng nhân sự", employees=[sep.b])
    obj, instance = _submit(db, leave_type, submitter)

    node2.approver_ref = str(sep.c.id)
    db.flush()
    _sync(db, node2)
    db.commit()

    assert _states(db, instance, seq=1) == [(sep.a.id, TASK_PENDING)]
    assert _tasks(db, instance, seq=2) == []

    action_service.approve(db, instance, sep.a.id, ACTOR, {})
    #  Chặng 2 mở ra theo NGƯỜI MỚI, không theo bản chụp lúc gửi duyệt.
    assert _states(db, instance, seq=2) == [(sep.c.id, TASK_PENDING)]


def test_doi_nguoi_thanh_ĐUNG_NGUOI_CU_thi_khong_dung_gi(db, flow, leave_type,
                                                          submitter, sep):
    """Sửa tên bước / hạn xử lý không được đá văng việc người ta đang mở dở."""
    node = _node(db, flow, 1, "Trưởng bộ phận", employees=[sep.a])
    obj, instance = _submit(db, leave_type, submitter)
    task_id = _tasks(db, instance)[0].id

    node.name = "Trưởng bộ phận (đổi tên)"
    db.flush()
    _sync(db, node)
    db.commit()

    rows = _tasks(db, instance)
    assert [(t.id, t.status) for t in rows] == [(task_id, TASK_PENDING)]


def test_sua_luong_khi_phieu_DA_DONG_thi_khong_de_viec_mo_coi(db, flow, leave_type,
                                                               submitter, sep):
    """Việc treo trên phiên đã đóng = người đó giữ quyền ĐỌC tờ đơn vĩnh viễn.

    Hộp việc không bày nó ra (`my_tasks` lọc phiên đóng) nhưng
    `steps_service.has_pending_task` thì có đọc — nên nó không lộ ra ở đâu cả.
    """
    node = _node(db, flow, 1, "Trưởng bộ phận", employees=[sep.a])
    obj, instance = _submit(db, leave_type, submitter)
    action_service.approve(db, instance, sep.a.id, ACTOR, {})

    node.approver_ref = str(sep.b.id)
    db.flush()
    assert _sync(db, node) == 0
    db.commit()

    assert not [t for t in _tasks(db, instance) if t.status == TASK_PENDING]
    assert _book(db, submitter, leave_type) == (0.0, 2.0, 10.0)


# ── 5. TẮT NGƯỜI DUYỆT — phiếu kẹt và đường gỡ ──────────────────────────────

def test_go_het_nguoi_duyet_thi_phieu_KET_chu_khong_tu_di_tiep(db, flow, leave_type,
                                                                submitter, sep):
    """Bước không ai duyệt mà vẫn qua = đơn có hiệu lực, không ai chịu trách nhiệm."""
    node = _node(db, flow, 1, "Trưởng bộ phận", employees=[sep.a])
    obj, instance = _submit(db, leave_type, submitter)

    node.approver_ref = ""
    db.flush()
    _sync(db, node)
    db.commit()
    db.refresh(instance)
    db.refresh(obj)

    assert instance.status == INSTANCE_BLOCKED
    assert obj.status == LR_PENDING
    assert instance.finish_reason
    #  Kẹt KHÔNG được trả quỹ: đơn chưa hỏng, nó đang chờ người sửa luồng.
    assert _book(db, submitter, leave_type) == (2.0, 0.0, 10.0)


def test_nhan_su_NGHI_VIEC_cung_lam_phieu_ket(db, flow, leave_type, submitter, sep):
    """Giao việc cho người đã tắt trạng thái là phiếu nằm im vĩnh viễn — không
    ai đăng nhập được vào tài khoản đó để bấm."""
    node = _node(db, flow, 1, "Trưởng bộ phận", employees=[sep.a])
    obj, instance = _submit(db, leave_type, submitter)

    sep.a.is_active = False
    db.flush()
    _sync(db, node)   # bất kỳ lượt sửa bước nào cũng tính lại người duyệt
    db.commit()
    db.refresh(instance)

    assert instance.status == INSTANCE_BLOCKED
    assert _book(db, submitter, leave_type) == (2.0, 0.0, 10.0)


def test_khai_lai_nguoi_duyet_thi_phieu_ket_HOI_SINH(db, flow, leave_type,
                                                      submitter, sep):
    """Đường gỡ kẹt bằng CẤU HÌNH, khỏi phải sửa tay dưới cơ sở dữ liệu."""
    node = _node(db, flow, 1, "Trưởng bộ phận", employees=[sep.a])
    obj, instance = _submit(db, leave_type, submitter)

    node.approver_ref = ""
    db.flush()
    _sync(db, node)
    db.commit()
    db.refresh(instance)
    assert instance.status == INSTANCE_BLOCKED

    node.approver_ref = str(sep.c.id)
    db.flush()
    _sync(db, node)
    db.commit()
    db.refresh(instance)

    assert instance.status == INSTANCE_RUNNING
    assert instance.finish_reason == ""
    assert _states(db, instance, seq=1) == sorted(
        [(sep.a.id, TASK_CANCELLED), (sep.c.id, TASK_PENDING)])

    action_service.approve(db, instance, sep.c.id, ACTOR, {})
    db.refresh(obj)
    assert obj.status == LR_APPROVED
    #  Đi qua kẹt rồi hồi sinh vẫn chỉ trừ MỘT lần.
    assert _book(db, submitter, leave_type) == (0.0, 2.0, 10.0)


def test_nguoi_du_phong_do_phieu_khi_khong_tim_duoc_ai(db, flow, leave_type, sep):
    """Nhánh «chuyển cho người dự phòng» — lối thoát khai sẵn trong luồng."""
    truong_phong = _employee(db, "NV_TP", "Trưởng phòng")
    from app.modules.department.model import Department
    db.add(Department(id=7, code="P7", name="Phòng 7", manager_id=truong_phong.id))
    db.flush()

    _node(db, flow, 1, "Trưởng bộ phận duyệt", kind=APPROVER_DEPT_HEAD,
          on_no_approver=NO_APPROVER_FALLBACK, fallback=sep.c)
    obj, instance = _submit(db, leave_type, truong_phong)
    db.refresh(instance)

    assert instance.status == INSTANCE_RUNNING
    assert _states(db, instance) == [(sep.c.id, TASK_PENDING)]

    action_service.approve(db, instance, sep.c.id, ACTOR, {})
    db.refresh(obj)
    assert obj.status == LR_APPROVED


def test_huy_don_dang_KET_van_tra_lai_du_quy(db, flow, leave_type, submitter, sep):
    """Kẹt là trạng thái người dùng gặp thật; họ phải rút được đơn ra khỏi đó."""
    node = _node(db, flow, 1, "Trưởng bộ phận", employees=[sep.a])
    obj, instance = _submit(db, leave_type, submitter)

    node.approver_ref = ""
    db.flush()
    _sync(db, node)
    db.commit()

    obj = approval_bridge.cancel_request(db, obj, "Đổi kế hoạch", _user(submitter))

    assert obj.status == LR_CANCELLED
    assert instance_service.running_instance(db, ENTITY, obj.id) is None
    assert _book(db, submitter, leave_type) == (0.0, 0.0, 12.0)


# ── 6. Cờ bộ máy bị TẮT giữa chừng ──────────────────────────────────────────

def test_tat_co_giua_chung_KHONG_bo_roi_phieu_dang_bay(db, flow, leave_type,
                                                        submitter, sep):
    """Cờ chỉ gác lượt MỞ phiên mới; phiếu đã bay vẫn ký được tới cùng.

    Nếu cờ gác cả đường ký thì mọi phiếu đang chạy chết cứng ngay lúc quản trị
    gạt công tắc, và cách duy nhất để gỡ là bật lại — không ai đoán ra.
    """
    _node(db, flow, 1, "Trưởng bộ phận", employees=[sep.a])
    obj, instance = _submit(db, leave_type, submitter)

    switch = db.query(ApprovalSwitch).filter(ApprovalSwitch.entity == ENTITY).first()
    switch.is_enabled = False
    db.commit()

    action_service.approve(db, instance, sep.a.id, ACTOR, {})
    db.refresh(obj)

    assert obj.status == LR_APPROVED
    assert _book(db, submitter, leave_type) == (0.0, 2.0, 10.0)


def test_tat_co_roi_thi_don_MOI_di_duong_duyet_thang(db, flow, leave_type,
                                                      submitter, sep):
    _node(db, flow, 1, "Trưởng bộ phận", employees=[sep.a])
    switch = db.query(ApprovalSwitch).filter(ApprovalSwitch.entity == ENTITY).first()
    switch.is_enabled = False
    db.commit()

    obj, instance = _submit(db, leave_type, submitter)

    assert instance is None
    assert obj.approval_instance_id == 0
    #  Vẫn giữ chỗ như thường — đường duyệt thẳng dùng chung sổ quỹ.
    assert _book(db, submitter, leave_type) == (2.0, 0.0, 10.0)


# ── 7. Đơn NHIỀU LOẠI NGHỈ chạy qua luồng ───────────────────────────────────

def test_don_nhieu_loai_tru_dung_hai_so_khac_nhau(db, flow, leave_type, submitter, sep):
    """Trừ tổng vào loại chính = cộng ngày không lương vào quỹ phép năm."""
    khong_luong = LeaveType(code="unpaid", name="Nghỉ không lương",
                            counts_balance=False, annual_quota_days=0.0)
    db.add(khong_luong)
    db.flush()
    _node(db, flow, 1, "Trưởng bộ phận", employees=[sep.a])

    user = _user(submitter)
    obj = request_service.create(db, LeaveRequestCreate(
        from_date=MONDAY, to_date=MONDAY + timedelta(days=3), reason="Việc nhà",
        lines=[{"leave_type_id": leave_type.id, "days": 3},
               {"leave_type_id": khong_luong.id, "days": 1}]), user)
    emp = request_service.prepare_submit(db, obj, user)
    instance_id = approval_bridge.start_approval(db, obj, user)
    obj = request_service.mark_submitted(db, obj, emp, user, instance_id)

    assert _book(db, submitter, leave_type) == (3.0, 0.0, 9.0)

    instance = instance_service.running_instance(db, ENTITY, obj.id)
    action_service.approve(db, instance, sep.a.id, ACTOR, {})
    db.refresh(obj)

    assert obj.status == LR_APPROVED
    #  Phép năm trừ 3; ngày không lương KHÔNG chạm vào quỹ phép năm.
    assert _book(db, submitter, leave_type) == (0.0, 3.0, 9.0)


# ── 8. Ca hiếm nhưng có thật ────────────────────────────────────────────────

def test_khai_DICH_DANH_nguoi_nop_lam_nguoi_duyet_thi_HO_TU_DUYET_DUOC(db, flow,
                                                                        leave_type,
                                                                        submitter):
    """GHIM một quyết định CỐ Ý, không phải mô tả một lỗi.

    I08 («không ai duyệt đơn của chính mình») chỉ cắt ở chỗ người duyệt được
    SUY RA — trưởng bộ phận, vai trò, lên N cấp… Khi quản trị gõ thẳng TÊN một
    người vào bước thì bộ máy tôn trọng khai báo (`_exclude_submitter`, sửa
    05/09/2026): gạt đi thì bước rỗng và phiếu chết giữa đường, đã trả giá hai
    lần bằng CR-113 và NP022.

    Với NGHỈ PHÉP điều đó nghĩa là: trưởng phòng được khai đích danh làm người
    duyệt thì **họ tự ký đơn nghỉ của chính họ**, dấu vết ghi bình thường. Ai
    thấy không chấp nhận được thì phải khai bước theo vai trò / trưởng bộ phận,
    hoặc thêm một chặng thứ hai — chứ đừng sửa `_exclude_submitter`, nó sẽ dựng
    lại đúng hai sự cố cũ.
    """
    _node(db, flow, 1, "Trưởng bộ phận", employees=[submitter])
    obj, instance = _submit(db, leave_type, submitter)

    assert _states(db, instance) == [(submitter.id, TASK_PENDING)]
    action_service.approve(db, instance, submitter.id, ACTOR, {})
    db.refresh(obj)

    assert obj.status == LR_APPROVED
    assert _book(db, submitter, leave_type) == (0.0, 2.0, 10.0)


def test_nghi_VAT_QUA_NAM_tru_het_vao_quy_nam_BAT_DAU(db, flow, leave_type,
                                                       submitter, sep):
    """Nghỉ 30/12 → 02/01: cả bốn ngày ăn quỹ của năm BẮT ĐẦU.

    Sổ quỹ khóa theo (người × NĂM × loại), còn tờ đơn chỉ có một mốc năm —
    `obj.from_date.year`. Hệ quả có thật mỗi dịp Tết dương lịch: hai ngày thuộc
    năm mới vẫn trừ vào quỹ năm cũ. Có lợi khi quỹ cũ sắp hết hạn, và chặn oan
    khi quỹ cũ đã cạn trong lúc quỹ mới còn nguyên.

    Bài này GHIM hành vi hiện tại để nó không đổi âm thầm. Muốn chia ngày theo
    năm thì phải sửa cả bốn nhịp giữ chỗ / trừ / trả / hoàn — không phải một
    dòng.
    """
    _node(db, flow, 1, "Trưởng bộ phận", employees=[sep.a])
    user = _user(submitter)
    obj = request_service.create(db, LeaveRequestCreate(
        leave_type_id=leave_type.id,
        from_date=date(2026, 12, 30), to_date=date(2027, 1, 2),
        reason="Nghỉ Tết dương lịch"), user)
    emp = request_service.prepare_submit(db, obj, user)
    instance_id = approval_bridge.start_approval(db, obj, user)
    obj = request_service.mark_submitted(db, obj, emp, user, instance_id)

    assert obj.total_days == 4.0
    rows = (db.query(LeaveBalance)
            .filter(LeaveBalance.employee_id == submitter.id).all())
    assert [(r.year, r.pending_days) for r in rows] == [(2026, 4.0)]


def test_nop_don_cho_ngay_nghi_NAM_SAU_thi_quy_nam_sau_tu_cap(db, flow, leave_type,
                                                               submitter, sep):
    """Tháng 12 xin nghỉ tháng 3 năm sau — quỹ năm sau chưa ai cấp.

    `ensure_balance` cấp lúc chạm nên đơn không bị chặn oan. Nếu nó chặn thì cả
    công ty không đăng ký được lịch nghỉ đầu năm cho tới khi Nhân sự bấm nút
    cấp quỹ.
    """
    _node(db, flow, 1, "Trưởng bộ phận", employees=[sep.a])
    user = _user(submitter)
    obj = request_service.create(db, LeaveRequestCreate(
        leave_type_id=leave_type.id,
        from_date=date(2027, 3, 1), to_date=date(2027, 3, 3),
        reason="Đặt trước"), user)
    emp = request_service.prepare_submit(db, obj, user)
    instance_id = approval_bridge.start_approval(db, obj, user)
    request_service.mark_submitted(db, obj, emp, user, instance_id)

    row = balance_service.get_balance(db, submitter.id, 2027, leave_type.id)
    assert (row.allocated_days, row.pending_days) == (12.0, 3.0)


def test_tra_ve_roi_RUT_NGAN_don_thi_giu_cho_theo_so_ngay_MOI(db, flow, leave_type,
                                                               submitter, sep):
    """Trả lại rồi giữ chỗ lại — hai nhịp phải khớp nhau, nếu không quỹ trôi."""
    _node(db, flow, 1, "Trưởng bộ phận", employees=[sep.a])
    obj, instance = _submit(db, leave_type, submitter, days=3)
    assert _book(db, submitter, leave_type) == (3.0, 0.0, 9.0)

    action_service.send_back(db, instance, sep.a.id, ACTOR, "Sửa lại ngày", {})
    assert _book(db, submitter, leave_type) == (0.0, 0.0, 12.0)

    user = _user(submitter)
    db.refresh(obj)
    request_service.update(db, obj, LeaveRequestUpdate(
        from_date=MONDAY, to_date=MONDAY + timedelta(days=1)), user)
    emp = request_service.prepare_submit(db, obj, user)
    instance_id = approval_bridge.start_approval(db, obj, user)
    obj = request_service.mark_submitted(db, obj, emp, user, instance_id)

    assert obj.total_days == 2.0
    assert _book(db, submitter, leave_type) == (2.0, 0.0, 10.0)


def test_khong_xoa_duoc_BUOC_ma_phieu_dang_dung_o_do(db, flow, leave_type,
                                                      submitter, sep):
    """Xóa cả luồng đã bị chặn từ lâu; xóa MỘT BƯỚC thì trước 07/09/2026 không.

    Mà xóa bước nguy hơn vì nó lặng lẽ: phiếu vẫn ký được (đi theo bản chụp),
    nhưng `flow_sync_service` bám theo BƯỚC — bước không còn thì mất luôn đường
    đổi người duyệt cho những phiếu đang đứng ở đó. Người duyệt nghỉ việc là
    phiếu chết hẳn, gỡ bằng script chạy tay.
    """
    from app.modules.approval.flow_controller import _block_delete_step_in_use

    node1 = _node(db, flow, 1, "Trưởng bộ phận", employees=[sep.a])
    node2 = _node(db, flow, 2, "Trưởng nhân sự", employees=[sep.b])
    _submit(db, leave_type, submitter)

    with pytest.raises(HTTPException) as caught:
        _block_delete_step_in_use(db, flow.id, node1)
    assert "đang dừng ở bước" in caught.value.detail

    #  Bước CHƯA TỚI thì xóa thoải mái — bản chụp của phiếu vẫn giữ bản của nó.
    _block_delete_step_in_use(db, flow.id, node2)
