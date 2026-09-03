"""STRESS TEST — đơn nghỉ phép × bộ máy phê duyệt, quét đủ 6 trạng thái.

Khác ba tệp nghỉ phép còn lại:

* `test_nghi_phep_don_va_duyet.py` gọi thẳng bốn hook để chốt luật trừ quỹ;
* `test_nghi_phep_qua_bo_may_duyet.py` chạy một luồng MỘT bước cho đủ vòng đời;
* tệp này đi tìm chỗ **hỏng**, không đi xác nhận chỗ chạy được.

Ba câu hỏi nó đặt ra:

1. **Ma trận trạng thái × hành động.** Sáu trạng thái (Nháp · Chờ duyệt · Đã
   duyệt · Từ chối · Trả về · Đã hủy) nhân với các thao tác. Phần lớn ô trong ma
   trận đó là ô CẤM, và ô cấm là chỗ không ai viết bài kiểm — người ta kiểm
   đường đi đúng rồi coi như xong. Nhưng một ô cấm hở ra thì quỹ phép sai, mà
   quỹ sai không kêu: nó chỉ lặng lẽ cho ai đó nghỉ thừa mấy ngày.
2. **Quỹ có RÒ qua nhiều vòng không.** Mỗi vòng nộp–rút–nộp–trả về–nộp–duyệt–hủy
   động vào `pending_days`/`used_days` đúng bốn lần. Sai một dấu ở một nhánh thì
   một vòng lệch 0.0 mà mười vòng lệch hẳn mấy ngày.
3. **Luồng NHIỀU bước.** Luồng một bước che mất mọi lỗi về "duyệt giữa chừng":
   duyệt bước 1 xong đơn vẫn phải là *Chờ duyệt* và quỹ vẫn phải đang giữ chỗ,
   chứ không được trừ sớm.

⚠️ Bài ở đây cố tình đi vào đường CẤM. Bài nào đỏ thì đọc lại luật trước, đừng
nới khẳng định cho nó xanh.
"""
from datetime import date, timedelta
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.modules.approval import action_service, instance_service
from app.modules.approval.flow_model import (APPROVER_EMPLOYEE, ApprovalFlow,
                                             ApprovalNode, ApprovalSwitch)
from app.modules.approval.instance_model import (INSTANCE_APPROVED,
                                                 INSTANCE_REJECTED,
                                                 INSTANCE_RETURNED,
                                                 INSTANCE_RUNNING,
                                                 INSTANCE_WITHDRAWN,
                                                 TASK_PENDING)
from app.modules.employee.model import Employee
from app.modules.leave import approval_bridge, balance_service, request_service
from app.modules.leave.catalog_model import LeaveType
from app.modules.leave.constants import (LR_APPROVED, LR_CANCELLED, LR_DRAFT,
                                         LR_PENDING, LR_REJECTED, LR_RETURNED)
from app.modules.leave.schema import LeaveRequestCreate

ACTOR = 1
ENTITY = "leave_request"
#  Thứ hai — mọi khoảng ngày dưới đây bắt đầu từ đây để số ngày công đếm được
#  không phụ thuộc vào hôm chạy test là thứ mấy.
MONDAY = date(2026, 1, 5)
QUOTA = 12.0


# ── Dựng cảnh ───────────────────────────────────────────────────────────────

@pytest.fixture()
def leave_type(db):
    obj = LeaveType(code="annual", name="Phép năm", counts_balance=True,
                    annual_quota_days=QUOTA)
    db.add(obj)
    db.flush()
    return obj


@pytest.fixture()
def submitter(db):
    obj = Employee(code="NV_NOP", full_name="Người nộp", company_id=1,
                   department_id=7, is_active=True)
    db.add(obj)
    db.flush()
    return obj


@pytest.fixture()
def approver(db):
    obj = Employee(code="NV_DUYET", full_name="Trưởng bộ phận", company_id=1,
                   department_id=7, is_active=True)
    db.add(obj)
    db.flush()
    return obj


@pytest.fixture()
def director(db):
    obj = Employee(code="NV_GD", full_name="Giám đốc", company_id=1,
                   department_id=7, is_active=True)
    db.add(obj)
    db.flush()
    return obj


def _make_flow(db, *approvers, code="NP-TEST"):
    """Luồng N bước, mỗi người duyệt một chặng, khai đích danh."""
    row = ApprovalFlow(entity=ENTITY, code=code, name="Duyệt nghỉ phép (thử)",
                       is_active=True, created_by=ACTOR, updated_by=ACTOR)
    db.add(row)
    db.flush()
    for seq, emp in enumerate(approvers, start=1):
        db.add(ApprovalNode(flow_id=row.id, seq=seq, name=f"Chặng {seq}",
                            approver_kind=APPROVER_EMPLOYEE, approver_ref=str(emp.id),
                            created_by=ACTOR, updated_by=ACTOR))
    db.add(ApprovalSwitch(entity=ENTITY, is_enabled=True,
                          created_by=ACTOR, updated_by=ACTOR))
    db.commit()
    db.refresh(row)
    return row


@pytest.fixture()
def flow(db, approver):
    return _make_flow(db, approver)


@pytest.fixture()
def flow_2_buoc(db, approver, director):
    return _make_flow(db, approver, director)


def _user(employee: Employee, uid: int = 1):
    return SimpleNamespace(id=uid, employee_id=employee.id)


def _create(db, leave_type, employee, days=2, start=MONDAY):
    user = _user(employee)
    return request_service.create(db, LeaveRequestCreate(
        leave_type_id=leave_type.id,
        from_date=start, to_date=start + timedelta(days=days - 1),
        reason="Về quê"), user)


def _submit(db, obj, employee):
    """Gửi duyệt qua đúng ba bước mà controller đi."""
    user = _user(employee)
    emp, lt = request_service.prepare_submit(db, obj, user)
    instance_id = approval_bridge.start_approval(db, obj, user)
    return request_service.mark_submitted(db, obj, emp, lt, user, instance_id)


def _create_and_submit(db, leave_type, employee, days=2, start=MONDAY):
    return _submit(db, _create(db, leave_type, employee, days, start), employee)


def _quy(db, employee, leave_type):
    """(giữ chỗ, đã dùng) — hai con số mà mọi nhịp nghiệp vụ động vào."""
    row = balance_service.get_balance(db, employee.id, 2026, leave_type.id)
    return (row.pending_days, row.used_days)


def _kiem_quy(db, employee, leave_type, pending: float, used: float):
    """Khẳng định quỹ, và chốt luôn RÀNG BUỘC giữa ba cột.

    `remaining_days` là một cột LƯU chứ không phải số tính lúc đọc, nên nó trôi
    được: một nhánh quên cập nhật nó thì `pending`/`used` vẫn đúng mà con số
    người dùng nhìn thấy trên màn Quỹ phép lại sai. Ràng buộc phải luôn đúng là
    `còn lại = quỹ − giữ chỗ − đã dùng`; kiểm nó ở mọi nhịp thì nhánh nào quên
    sẽ đỏ ngay tại nhịp đó thay vì lộ ra ở một bài khác cách xa nguyên nhân.
    """
    row = balance_service.get_balance(db, employee.id, 2026, leave_type.id)

    if row is None:
        #  Dòng quỹ chỉ sinh ra ở nhịp GỬI DUYỆT đầu tiên (`ensure_balance`), nên
        #  một tờ đơn còn Nháp thì chưa có dòng nào — và đó là đúng: lập đơn
        #  không được phép động vào quỹ của ai.
        #  Ở đây `remaining()` trả **0.0 chứ không phải 12.0**. Chưa cấp phát và
        #  hết phép nhìn giống hệt nhau ở con số này; phân biệt là việc của màn
        #  Quỹ phép, nơi có chỗ giải thích (xem docstring `balance_service.remaining`).
        assert (pending, used) == (0.0, 0.0), "Quỹ đã đổi mà dòng quỹ chưa hề tồn tại"
        assert balance_service.remaining(db, employee.id, 2026, leave_type.id) == 0.0
        return

    assert (row.pending_days, row.used_days) == (pending, used)
    assert row.remaining_days == QUOTA - pending - used
    assert balance_service.remaining(db, employee.id, 2026, leave_type.id) == row.remaining_days


def _instance(db, obj):
    return instance_service.running_instance(db, ENTITY, obj.id)


# ══════════════════════════════════════════════════════════════════════════════
#  1. LUỒNG NHIỀU BƯỚC — duyệt giữa chừng không được coi là xong
# ══════════════════════════════════════════════════════════════════════════════

def test_duyet_buoc_1_cua_luong_2_buoc_thi_don_VAN_cho_duyet(db, flow_2_buoc, leave_type,
                                                             submitter, approver):
    """Trừ quỹ ở bước giữa là cho nghỉ trước khi giám đốc ký.

    Luồng một bước che mất hẳn lỗi này: ở đó bước 1 cũng là bước cuối nên "duyệt
    xong thì trừ" luôn đúng một cách tình cờ.
    """
    obj = _create_and_submit(db, leave_type, submitter)
    action_service.approve(db, _instance(db, obj), approver.id, ACTOR, {})
    db.refresh(obj)

    assert obj.status == LR_PENDING, "Duyệt bước giữa mà đơn đã chốt"
    _kiem_quy(db, submitter, leave_type, 2.0, 0.0)
    instance = _instance(db, obj)
    assert instance is not None and instance.status == INSTANCE_RUNNING


def test_duyet_du_hai_buoc_moi_tru_quy_dung_mot_lan(db, flow_2_buoc, leave_type,
                                                    submitter, approver, director):
    obj = _create_and_submit(db, leave_type, submitter)
    action_service.approve(db, _instance(db, obj), approver.id, ACTOR, {})
    action_service.approve(db, _instance(db, obj), director.id, ACTOR, {})
    db.refresh(obj)

    assert obj.status == LR_APPROVED
    #  Trừ ĐÚNG MỘT LẦN: hai bước ký nhưng chỉ một lần chuyển giữ-chỗ → đã-dùng.
    _kiem_quy(db, submitter, leave_type, 0.0, 2.0)


def test_tu_choi_o_buoc_cuoi_van_tra_lai_du_giu_cho(db, flow_2_buoc, leave_type,
                                                    submitter, approver, director):
    """Bước 1 đã ký rồi mới bị bác — quỹ phải về nguyên, không kẹt nửa vời."""
    obj = _create_and_submit(db, leave_type, submitter)
    action_service.approve(db, _instance(db, obj), approver.id, ACTOR, {})
    action_service.reject(db, _instance(db, obj), director.id, ACTOR, "Nhân sự mỏng")
    db.refresh(obj)

    assert obj.status == LR_REJECTED
    _kiem_quy(db, submitter, leave_type, 0.0, 0.0)
    assert "Nhân sự mỏng" in obj.decision_note


def test_da_co_nguoi_ky_thi_khong_rut_duoc_nua(db, flow_2_buoc, leave_type,
                                               submitter, approver):
    """Chữ ký đã đặt không được biến mất khỏi quy trình.

    Và khi bộ máy chặn thì tờ đơn phải NGUYÊN VẸN: chặn ở giữa mà quỹ đã trả rồi
    là trạng thái rách — đơn còn chờ duyệt nhưng ngày phép đã về túi.
    """
    obj = _create_and_submit(db, leave_type, submitter)
    action_service.approve(db, _instance(db, obj), approver.id, ACTOR, {})

    with pytest.raises(HTTPException):
        approval_bridge.cancel_request(db, obj, "Đổi ý", _user(submitter))

    db.refresh(obj)
    assert obj.status == LR_PENDING
    _kiem_quy(db, submitter, leave_type, 2.0, 0.0)


def test_tra_ve_tu_buoc_2_thi_buoc_1_phai_ky_lai(db, flow_2_buoc, leave_type,
                                                 submitter, approver, director):
    """Nội dung sắp sửa khác nội dung người ký trước đã ký."""
    obj = _create_and_submit(db, leave_type, submitter)
    action_service.approve(db, _instance(db, obj), approver.id, ACTOR, {})
    action_service.send_back(db, _instance(db, obj), director.id, ACTOR, "Thiếu bàn giao", {})
    db.refresh(obj)

    assert obj.status == LR_RETURNED
    _kiem_quy(db, submitter, leave_type, 0.0, 0.0)
    request_service.check_editable(obj)   # không ném = sửa được

    #  Nộp lại → phiên MỚI, và việc treo lại rơi về CHẶNG 1.
    obj = _submit(db, obj, submitter)
    tasks = [t for t in instance_service.tasks_of_instance(db, obj.approval_instance_id)
             if t.status == TASK_PENDING]
    assert [t.node_seq for t in tasks] == [1]


# ══════════════════════════════════════════════════════════════════════════════
#  2. MA TRẬN trạng thái × hành động — phần lớn là ô CẤM
# ══════════════════════════════════════════════════════════════════════════════

def _dua_ve(db, flow_unused, leave_type, submitter, approver, status: int):
    """Đưa một tờ đơn về đúng trạng thái yêu cầu, đi qua đường thật."""
    if status == LR_DRAFT:
        return _create(db, leave_type, submitter)

    obj = _create_and_submit(db, leave_type, submitter)
    if status == LR_PENDING:
        return obj
    if status == LR_APPROVED:
        action_service.approve(db, _instance(db, obj), approver.id, ACTOR, {})
    elif status == LR_REJECTED:
        action_service.reject(db, _instance(db, obj), approver.id, ACTOR, "Bác")
    elif status == LR_RETURNED:
        action_service.send_back(db, _instance(db, obj), approver.id, ACTOR, "Sửa", {})
    elif status == LR_CANCELLED:
        approval_bridge.cancel_request(db, obj, "Đổi ý", _user(submitter))
    db.refresh(obj)
    return obj


ALL_STATUSES = [LR_DRAFT, LR_PENDING, LR_APPROVED, LR_REJECTED, LR_RETURNED, LR_CANCELLED]


@pytest.mark.parametrize("status", ALL_STATUSES)
def test_dua_ve_dung_trang_thai_va_quy_luon_khop(db, flow, leave_type, submitter,
                                                 approver, status):
    """Bài NỀN cho cả mục này, và tự nó cũng là một khẳng định.

    Nếu `_dua_ve` không đưa được đơn tới đúng trạng thái thì mọi bài dưới đây
    đang kiểm nhầm ô của ma trận mà vẫn xanh. Kèm luôn luật quỹ: chỉ đúng MỘT
    trạng thái được giữ chỗ (Chờ duyệt) và đúng MỘT trạng thái được trừ thật
    (Đã duyệt); bốn trạng thái còn lại quỹ phải sạch.
    """
    obj = _dua_ve(db, flow, leave_type, submitter, approver, status)
    assert obj.status == status

    _kiem_quy(db, submitter, leave_type,
              2.0 if status == LR_PENDING else 0.0,
              2.0 if status == LR_APPROVED else 0.0)


@pytest.mark.parametrize("status", [LR_PENDING, LR_APPROVED, LR_REJECTED, LR_CANCELLED])
def test_chi_NHAP_va_TRA_VE_moi_sua_duoc(db, flow, leave_type, submitter, approver, status):
    """Sửa được đơn đang chờ duyệt = đổi nội dung dưới chân người sắp ký."""
    obj = _dua_ve(db, flow, leave_type, submitter, approver, status)
    with pytest.raises(HTTPException) as e:
        request_service.check_editable(obj)
    assert e.value.status_code == 400


@pytest.mark.parametrize("status", [LR_DRAFT, LR_RETURNED])
def test_NHAP_va_TRA_VE_thi_sua_duoc(db, flow, leave_type, submitter, approver, status):
    obj = _dua_ve(db, flow, leave_type, submitter, approver, status)
    request_service.check_editable(obj)   # không ném


@pytest.mark.parametrize("status", [LR_PENDING, LR_APPROVED, LR_REJECTED, LR_CANCELLED])
def test_khong_gui_duyet_lai_don_da_chot(db, flow, leave_type, submitter, approver, status):
    """Gửi duyệt lại đơn ĐÃ DUYỆT là trừ quỹ lần hai cho cùng mấy ngày nghỉ."""
    obj = _dua_ve(db, flow, leave_type, submitter, approver, status)
    truoc = _quy(db, submitter, leave_type)

    with pytest.raises(HTTPException):
        request_service.prepare_submit(db, obj, _user(submitter))

    assert _quy(db, submitter, leave_type) == truoc, "Chặn rồi mà quỹ vẫn đổi"


def test_gui_duyet_lai_don_BI_TRA_VE_thi_duoc(db, flow, leave_type, submitter, approver):
    """Đây chính là điều phân biệt «Trả về» với «Từ chối» — đừng chặn nhầm."""
    obj = _dua_ve(db, flow, leave_type, submitter, approver, LR_RETURNED)
    obj = _submit(db, obj, submitter)

    assert obj.status == LR_PENDING
    _kiem_quy(db, submitter, leave_type, 2.0, 0.0)


@pytest.mark.parametrize("status", [LR_DRAFT, LR_PENDING, LR_APPROVED, LR_REJECTED,
                                    LR_RETURNED])
def test_moi_trang_thai_chua_huy_deu_huy_duoc_va_quy_ve_sach(db, flow, leave_type,
                                                             submitter, approver, status):
    """Hủy là lối thoát cuối — không trạng thái nào được kẹt lại.

    Kèm luật quỹ: hủy xong quỹ phải SẠCH dù trước đó đang giữ chỗ (Chờ duyệt),
    đã trừ thật (Đã duyệt) hay chưa động gì (Nháp).
    """
    obj = _dua_ve(db, flow, leave_type, submitter, approver, status)
    obj = approval_bridge.cancel_request(db, obj, "Đổi kế hoạch", _user(submitter))

    assert obj.status == LR_CANCELLED
    _kiem_quy(db, submitter, leave_type, 0.0, 0.0)
    assert _instance(db, obj) is None


def test_huy_don_DA_HUY_la_thao_tac_lap_lai_duoc(db, flow, leave_type, submitter, approver):
    """Bấm Hủy hai lần (mạng chậm, người dùng bấm lại) không được trả quỹ hai lần.

    Trả hai lần thì `refund_used` cộng thêm 2 ngày KHÔNG có thật vào quỹ — và
    triệu chứng chỉ lộ ra ở kỳ nghỉ sau, khi ai đó nghỉ thừa.
    """
    obj = _dua_ve(db, flow, leave_type, submitter, approver, LR_APPROVED)
    approval_bridge.cancel_request(db, obj, "Đổi ý", _user(submitter))
    approval_bridge.cancel_request(db, obj, "Đổi ý", _user(submitter))

    assert obj.status == LR_CANCELLED
    _kiem_quy(db, submitter, leave_type, 0.0, 0.0)


@pytest.mark.parametrize("status", [LR_DRAFT, LR_APPROVED, LR_REJECTED, LR_RETURNED,
                                    LR_CANCELLED])
def test_khong_co_phien_chay_thi_duyet_thang_khong_bi_chan(db, flow, leave_type,
                                                           submitter, approver, status):
    """`block_legacy_path` chỉ chặn khi phiên CÒN chạy.

    Chặn cả lúc phiên đã đóng thì Nhân sự không bao giờ chốt được đơn của môi
    trường chưa khai luồng — mà câu báo lỗi lại nói về «luồng nhiều bước».
    """
    obj = _dua_ve(db, flow, leave_type, submitter, approver, status)
    approval_bridge.block_legacy_path(db, obj)   # không ném


def test_dang_cho_duyet_thi_duyet_thang_bi_chan(db, flow, leave_type, submitter, approver):
    obj = _dua_ve(db, flow, leave_type, submitter, approver, LR_PENDING)
    with pytest.raises(HTTPException) as e:
        approval_bridge.block_legacy_path(db, obj)
    assert "luồng phê duyệt nhiều bước" in e.value.detail


# ══════════════════════════════════════════════════════════════════════════════
#  3. Trạng thái PHIÊN DUYỆT phải khớp trạng thái ĐƠN
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("dat_trang_thai, don, phien", [
    ("approve", LR_APPROVED, INSTANCE_APPROVED),
    ("reject", LR_REJECTED, INSTANCE_REJECTED),
    ("send_back", LR_RETURNED, INSTANCE_RETURNED),
    ("withdraw", LR_DRAFT, INSTANCE_WITHDRAWN),
])
def test_don_va_phien_khong_bao_gio_lech_nhau(db, flow, leave_type, submitter,
                                              approver, dat_trang_thai, don, phien):
    """Hai bảng, hai nguồn sự thật — lệch nhau là màn hình nói một đằng, phiếu
    duyệt nói một nẻo, và không ai biết bên nào đúng."""
    obj = _create_and_submit(db, leave_type, submitter)
    instance = _instance(db, obj)

    if dat_trang_thai == "approve":
        action_service.approve(db, instance, approver.id, ACTOR, {})
    elif dat_trang_thai == "reject":
        action_service.reject(db, instance, approver.id, ACTOR, "Bác")
    elif dat_trang_thai == "send_back":
        action_service.send_back(db, instance, approver.id, ACTOR, "Sửa", {})
    else:
        action_service.withdraw(db, instance, submitter.id, ACTOR, "Đổi ý")

    db.refresh(obj)
    db.refresh(instance)
    assert (obj.status, instance.status) == (don, phien)
    #  Phiên đã chốt thì không còn "đang chạy" — nếu còn, người duyệt vẫn thấy
    #  việc treo và ký được lần nữa.
    assert _instance(db, obj) is None


def test_rut_roi_nop_lai_thi_don_tro_ve_phien_MOI(db, flow, leave_type, submitter):
    """Nộp lại mà bám vào phiên cũ đã rút thì hook bắn vào một phiên chết."""
    obj = _create_and_submit(db, leave_type, submitter)
    phien_cu = obj.approval_instance_id
    action_service.withdraw(db, _instance(db, obj), submitter.id, ACTOR, "Đổi ý")
    db.refresh(obj)

    obj = _submit(db, obj, submitter)
    assert obj.approval_instance_id != phien_cu
    assert _instance(db, obj).id == obj.approval_instance_id


# ══════════════════════════════════════════════════════════════════════════════
#  4. Quỹ phép qua NHIỀU VÒNG — chỗ số lệch tích lại
# ══════════════════════════════════════════════════════════════════════════════

def test_muoi_vong_nop_rut_khong_lam_ro_quy(db, flow, leave_type, submitter):
    """Nộp rồi rút mười lần. Quỹ phải y hệt lúc chưa làm gì.

    Một vòng lệch 0.0 thì không ai thấy; mười vòng lệch thì con số trên màn hình
    sai hẳn mấy ngày và không ai truy được vòng nào gây ra.
    """
    obj = _create(db, leave_type, submitter)
    for _ in range(10):
        obj = _submit(db, obj, submitter)
        action_service.withdraw(db, _instance(db, obj), submitter.id, ACTOR, "Đổi ý")
        db.refresh(obj)
        assert obj.status == LR_DRAFT

    _kiem_quy(db, submitter, leave_type, 0.0, 0.0)


def test_vong_doi_du_bay_chang_quy_van_khop(db, flow, leave_type, submitter, approver):
    """Một tờ đơn đi hết mọi ngã: nộp → rút → nộp → trả về → nộp → duyệt → hủy.

    Bảy nhịp, mỗi nhịp động vào quỹ. Kiểm sau TỪNG nhịp chứ không chỉ kiểm cuối:
    hai lỗi ngược dấu ở giữa sẽ triệt tiêu nhau và bài kiểm-cuối vẫn xanh.
    """
    obj = _create(db, leave_type, submitter)
    _kiem_quy(db, submitter, leave_type, 0.0, 0.0)

    obj = _submit(db, obj, submitter)
    _kiem_quy(db, submitter, leave_type, 2.0, 0.0)

    action_service.withdraw(db, _instance(db, obj), submitter.id, ACTOR, "Đổi ý")
    db.refresh(obj)
    _kiem_quy(db, submitter, leave_type, 0.0, 0.0)

    obj = _submit(db, obj, submitter)
    action_service.send_back(db, _instance(db, obj), approver.id, ACTOR, "Sửa", {})
    db.refresh(obj)
    _kiem_quy(db, submitter, leave_type, 0.0, 0.0)

    obj = _submit(db, obj, submitter)
    action_service.approve(db, _instance(db, obj), approver.id, ACTOR, {})
    db.refresh(obj)
    _kiem_quy(db, submitter, leave_type, 0.0, 2.0)

    approval_bridge.cancel_request(db, obj, "Đổi kế hoạch", _user(submitter))
    _kiem_quy(db, submitter, leave_type, 0.0, 0.0)


def test_nop_lien_tay_nhieu_don_deu_bi_GIU_CHO_tru_dan(db, flow, leave_type, submitter):
    """`pending_days` là cột BẮT BUỘC, không phải tối ưu.

    Thiếu nhịp giữ chỗ thì nộp liền tay sáu đơn 2 ngày đều lọt hết, tổng 12 ngày
    trong khi quỹ chỉ có 12 và chưa ai duyệt gì — tới lúc duyệt mới vỡ.
    """
    ngay = MONDAY
    for lan in range(1, 7):
        #  Khoảng ngày không chồng nhau: `check_overlap` chặn trùng, mà bài này
        #  đang kiểm quỹ chứ không kiểm trùng lịch.
        _create_and_submit(db, leave_type, submitter, days=2, start=ngay)
        ngay += timedelta(days=7)
        _kiem_quy(db, submitter, leave_type, 2.0 * lan, 0.0)

    #  Quỹ đã cạn — đơn thứ bảy phải bị chặn ngay lúc gửi duyệt.
    obj = _create(db, leave_type, submitter, days=2, start=ngay)
    with pytest.raises(HTTPException) as e:
        request_service.prepare_submit(db, obj, _user(submitter))
    assert e.value.status_code == 400

    _kiem_quy(db, submitter, leave_type, 12.0, 0.0)


def test_huy_mot_don_giua_chum_thi_tra_dung_phan_cua_no(db, flow, leave_type, submitter):
    """Trả quá tay ở đây là tặng ngày phép cho người khác trong cùng chùm đơn."""
    don = [_create_and_submit(db, leave_type, submitter, days=2,
                              start=MONDAY + timedelta(days=7 * i)) for i in range(3)]
    _kiem_quy(db, submitter, leave_type, 6.0, 0.0)

    approval_bridge.cancel_request(db, don[1], "Đổi ý", _user(submitter))

    _kiem_quy(db, submitter, leave_type, 4.0, 0.0)
    #  Hai đơn còn lại KHÔNG bị đụng tới.
    for obj in (don[0], don[2]):
        db.refresh(obj)
        assert obj.status == LR_PENDING


# ══════════════════════════════════════════════════════════════════════════════
#  5. Người không phận sự
# ══════════════════════════════════════════════════════════════════════════════

def test_nguoi_khong_duoc_giao_thi_khong_ky_duoc(db, flow, leave_type, submitter,
                                                 director):
    """`director` không nằm trong luồng một bước — ký được là ai cũng ký được."""
    obj = _create_and_submit(db, leave_type, submitter)
    with pytest.raises(HTTPException):
        action_service.approve(db, _instance(db, obj), director.id, ACTOR, {})

    db.refresh(obj)
    assert obj.status == LR_PENDING
    _kiem_quy(db, submitter, leave_type, 2.0, 0.0)


def test_nguoi_duyet_buoc_2_khong_ky_thay_buoc_1(db, flow_2_buoc, leave_type,
                                                 submitter, director):
    """Ký vượt cấp = bỏ qua chữ ký của trưởng bộ phận."""
    obj = _create_and_submit(db, leave_type, submitter)
    with pytest.raises(HTTPException):
        action_service.approve(db, _instance(db, obj), director.id, ACTOR, {})

    db.refresh(obj)
    assert obj.status == LR_PENDING


def test_tu_choi_KHONG_ghi_ly_do_thi_bi_chan(db, flow, leave_type, submitter, approver):
    """Từ chối không lý do là để người nộp mở đơn ra thấy đỏ mà không biết vì sao.

    Và khi bị chặn thì tờ đơn phải nguyên vẹn — chặn nửa chừng sau khi đã trả
    quỹ là trạng thái rách.
    """
    obj = _create_and_submit(db, leave_type, submitter)
    with pytest.raises(HTTPException):
        action_service.reject(db, _instance(db, obj), approver.id, ACTOR, "   ")

    db.refresh(obj)
    assert obj.status == LR_PENDING
    _kiem_quy(db, submitter, leave_type, 2.0, 0.0)
