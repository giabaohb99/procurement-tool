"""CR-260 — HỘP VIỆC DUYỆT của màn Đơn nghỉ phép + luồng duyệt dạng ngang.

Ba thứ tệp này chốt, và cả ba đều là chỗ dễ hỏng âm thầm:

1. **Quyền đọc nới đúng mức.** Người duyệt chặng 2 phải mở được tờ đơn họ đang
   phải ký, dù phạm vi dữ liệu không với tới. Nới quá tay thì lý do nghỉ — thứ
   riêng tư nhất trong cả hệ — phơi ra cho người ngoài; nới thiếu thì bộ máy
   giao việc rồi chặn chính người được giao.
2. **Dải chấm nói đúng phiếu đang ở đâu.** Đây là thứ người dùng nhìn để quyết
   xem có phải bấm gì không. Nói sai một chặng là họ tưởng đã ký rồi.
3. **Không N+1.** Cả tệp `steps_service` sinh ra vì lý do đó; bài cuối đếm số
   truy vấn thật để nó không lặng lẽ quay lại.
"""
from datetime import date, timedelta
from types import SimpleNamespace

import pytest

from app.modules.approval import action_service, instance_service, steps_service
from app.modules.approval.flow_model import (APPROVER_EMPLOYEE, ApprovalFlow,
                                             ApprovalNode, ApprovalSwitch)
from app.modules.employee.model import Employee
from app.modules.leave import approval_bridge, request_service
from app.modules.leave.catalog_model import LeaveType
from app.modules.leave.schema import LeaveRequestCreate

ACTOR = 1
ENTITY = "leave_request"
MONDAY = date(2026, 1, 5)


@pytest.fixture()
def leave_type(db):
    obj = LeaveType(code="annual", name="Phép năm", counts_balance=True,
                    annual_quota_days=12.0)
    db.add(obj)
    db.flush()
    return obj


def _employee(db, code, dept=7):
    obj = Employee(code=code, full_name=f"NV {code}", company_id=1,
                   department_id=dept, is_active=True)
    db.add(obj)
    db.flush()
    return obj


@pytest.fixture()
def submitter(db):
    return _employee(db, "NOP")


@pytest.fixture()
def approver1(db):
    return _employee(db, "DUYET1")


@pytest.fixture()
def approver2(db):
    return _employee(db, "DUYET2", dept=9)


@pytest.fixture()
def flow_2_buoc(db, approver1, approver2):
    row = ApprovalFlow(entity=ENTITY, code="NP-2B", name="Duyệt nghỉ phép",
                       is_active=True, created_by=ACTOR, updated_by=ACTOR)
    db.add(row)
    db.flush()
    for seq, emp in enumerate((approver1, approver2), start=1):
        db.add(ApprovalNode(flow_id=row.id, seq=seq, name=f"Chặng {seq}",
                            approver_kind=APPROVER_EMPLOYEE, approver_ref=str(emp.id),
                            created_by=ACTOR, updated_by=ACTOR))
    db.add(ApprovalSwitch(entity=ENTITY, is_enabled=True,
                          created_by=ACTOR, updated_by=ACTOR))
    db.commit()
    db.refresh(row)
    return row


def _user(employee, uid=1):
    return SimpleNamespace(id=uid, employee_id=employee.id)


def _submit(db, leave_type, employee, days=2, start=MONDAY):
    user = _user(employee)
    obj = request_service.create(db, LeaveRequestCreate(
        leave_type_id=leave_type.id, from_date=start,
        to_date=start + timedelta(days=days - 1), reason="Về quê"), user)
    emp, lt = request_service.prepare_submit(db, obj, user)
    instance_id = approval_bridge.start_approval(db, obj, user)
    return request_service.mark_submitted(db, obj, emp, lt, user, instance_id)


def _instance(db, obj):
    return instance_service.running_instance(db, ENTITY, obj.id)


def _steps(db, obj):
    return steps_service.steps_of_entities(db, ENTITY, [obj.id]).get(obj.id)


# ══════════════════════════════════════════════════════════════════════════════
#  1. Dải chấm nói đúng phiếu đang ở đâu
# ══════════════════════════════════════════════════════════════════════════════

def test_vua_gui_duyet_thi_chang_1_sang_chang_2_con_cho(db, flow_2_buoc, leave_type,
                                                        submitter, approver1):
    obj = _submit(db, leave_type, submitter)
    flow = _steps(db, obj)

    assert [s["seq"] for s in flow["steps"]] == [1, 2]
    assert [s["state"] for s in flow["steps"]] == [steps_service.STEP_CURRENT,
                                                   steps_service.STEP_TODO]
    #  Tên người đang giữ phiếu phải có — đó là thứ dòng danh sách hiện ra để
    #  người xem biết đang chờ AI, không phải chờ chung chung.
    assert flow["steps"][0]["assignees"][0]["name"] == approver1.full_name
    assert flow["summary"] == f"Đang ở chặng 1/2 · {approver1.full_name}"


def test_ky_xong_chang_1_thi_cham_do_tat_va_chang_2_sang_len(db, flow_2_buoc, leave_type,
                                                             submitter, approver1,
                                                             approver2):
    obj = _submit(db, leave_type, submitter)
    action_service.approve(db, _instance(db, obj), approver1.id, ACTOR, {})

    flow = _steps(db, obj)
    assert [s["state"] for s in flow["steps"]] == [steps_service.STEP_DONE,
                                                   steps_service.STEP_CURRENT]
    assert flow["summary"] == f"Đang ở chặng 2/2 · {approver2.full_name}"


def test_duyet_het_thi_moi_chang_deu_xong(db, flow_2_buoc, leave_type, submitter,
                                          approver1, approver2):
    obj = _submit(db, leave_type, submitter)
    action_service.approve(db, _instance(db, obj), approver1.id, ACTOR, {})
    action_service.approve(db, _instance(db, obj), approver2.id, ACTOR, {})

    flow = _steps(db, obj)
    assert {s["state"] for s in flow["steps"]} == {steps_service.STEP_DONE}
    assert flow["summary"] == "Đã duyệt đủ 2/2 chặng"


def test_bi_tu_choi_thi_chi_ra_DUNG_chang_phieu_chet(db, flow_2_buoc, leave_type,
                                                     submitter, approver1, approver2):
    """Chặng bị từ chối phải nổi lên, không được lẫn vào đám «đã hủy».

    Khi phiếu dừng, bộ máy dọn những việc còn treo thành «đã hủy». Xét «đã hủy»
    trước «bị từ chối» thì chặng chết lại đọc thành chặng bị hủy, và dải chấm
    mất đúng thông tin người xem cần nhất — phiếu chết ở đâu.
    """
    obj = _submit(db, leave_type, submitter)
    action_service.approve(db, _instance(db, obj), approver1.id, ACTOR, {})
    action_service.reject(db, _instance(db, obj), approver2.id, ACTOR, "Nhân sự mỏng")

    flow = _steps(db, obj)
    assert flow["steps"][0]["state"] == steps_service.STEP_DONE
    assert flow["steps"][1]["state"] == steps_service.STEP_REJECTED
    assert flow["summary"] == "Dừng ở chặng 2/2 · bị từ chối"


def test_tra_ve_KHAC_bi_rut(db, flow_2_buoc, leave_type, submitter, approver1):
    """Hai kết cục đều làm việc treo thành «đã hủy», chỉ trạng thái phiên phân biệt.

    Đọc nhầm thì người nộp thấy «đã rút» cho tờ đơn họ không hề rút.
    """
    tra_ve = _submit(db, leave_type, submitter)
    action_service.send_back(db, _instance(db, tra_ve), approver1.id, ACTOR, "Sửa", {})
    assert _steps(db, tra_ve)["summary"] == "Đã trả về người nộp để chỉnh sửa"

    rut = _submit(db, leave_type, submitter, start=MONDAY + timedelta(days=14))
    action_service.withdraw(db, _instance(db, rut), submitter.id, ACTOR, "Đổi ý")
    assert _steps(db, rut)["summary"] == "Người nộp đã rút phiếu"


def test_don_CHUA_vao_bo_may_thi_khong_co_khoa(db, leave_type, submitter):
    """Trả bản ghi rỗng thay vì bỏ khóa thì màn hình vẽ ra một dải chấm trống,
    đọc như luồng hỏng."""
    obj = _submit(db, leave_type, submitter)   # chưa khai luồng
    assert obj.approval_instance_id == 0
    assert steps_service.steps_of_entities(db, ENTITY, [obj.id]) == {}


def test_nop_lai_sau_khi_bi_tra_ve_thi_doc_phien_MOI(db, flow_2_buoc, leave_type,
                                                     submitter, approver1):
    """Một đơn có nhiều phiên qua thời gian — dải chấm phải nói phiên ĐANG chạy.

    Đọc phiên cũ thì đơn vừa nộp lại vẫn hiện «đã trả về», và người duyệt bỏ qua
    nó vì tưởng bóng đang ở sân người nộp.
    """
    obj = _submit(db, leave_type, submitter)
    phien_cu = obj.approval_instance_id
    action_service.send_back(db, _instance(db, obj), approver1.id, ACTOR, "Sửa", {})
    db.refresh(obj)

    obj = _submit(db, leave_type, submitter)
    flow = _steps(db, obj)

    assert flow["instance_id"] != phien_cu
    assert flow["steps"][0]["state"] == steps_service.STEP_CURRENT


def test_danh_sach_rong_hoac_id_rac_khong_no(db):
    assert steps_service.steps_of_entities(db, ENTITY, []) == {}
    assert steps_service.steps_of_entities(db, ENTITY, [0, 0]) == {}
    assert steps_service.steps_of_entities(db, ENTITY, [999999]) == {}


# ══════════════════════════════════════════════════════════════════════════════
#  2. Quyền đọc — nới đúng lúc đang có việc treo
# ══════════════════════════════════════════════════════════════════════════════

def test_nguoi_dang_phai_ky_thi_doc_duoc_don_ngoai_pham_vi(db, flow_2_buoc, leave_type,
                                                           submitter, approver1):
    """Không có luật này thì bộ máy giao việc cho người ta rồi chặn họ đọc.

    `approver1` không có grant nào trên `leave_request` nên `apply_scope` chặn
    sạch — đúng cảnh Trưởng phòng Nhân sự duyệt đơn của nhân viên phòng khác.
    """
    obj = _submit(db, leave_type, submitter)
    user = _user(approver1, uid=9)

    assert approval_bridge.can_read_request(db, obj.id, user) is True


def test_ky_XONG_thi_quyen_doc_them_do_DONG_lai(db, flow_2_buoc, leave_type,
                                                submitter, approver1):
    """Nới theo «đã từng ký» thì mỗi lượt ký lại thêm vĩnh viễn một tờ đơn vào
    tầm nhìn của một người, và phạm vi dữ liệu phình dần mà không ai rà lại."""
    obj = _submit(db, leave_type, submitter)
    user = _user(approver1, uid=9)
    action_service.approve(db, _instance(db, obj), approver1.id, ACTOR, {})

    assert approval_bridge.can_read_request(db, obj.id, user) is False


def test_nguoi_o_chang_SAU_chua_toi_luot_thi_chua_doc_duoc(db, flow_2_buoc, leave_type,
                                                           submitter, approver2):
    """Việc của họ đang ở «chưa tới lượt», không phải «đang chờ».

    Cho đọc sớm nghĩa là mọi người trong mọi luồng đọc được mọi đơn ngay khi nó
    vừa gửi đi — nới thành gần như không còn phạm vi.
    """
    obj = _submit(db, leave_type, submitter)
    assert approval_bridge.can_read_request(db, obj.id, _user(approver2, uid=9)) is False


def test_nguoi_ngoai_cuoc_van_bi_chan(db, flow_2_buoc, leave_type, submitter):
    obj = _submit(db, leave_type, submitter)
    outsider = SimpleNamespace(id=999, employee_id=888)
    assert approval_bridge.can_read_request(db, obj.id, outsider) is False


def test_tai_khoan_chua_gan_nhan_su_khong_lot_qua(db, flow_2_buoc, leave_type, submitter):
    """`employee_id` rỗng mà lọt thì `has_pending_task` so `NULL = NULL`, và
    tùy cơ sở dữ liệu điều đó có thể trúng mọi dòng."""
    obj = _submit(db, leave_type, submitter)
    assert steps_service.has_pending_task(db, ENTITY, obj.id, 0) is False
    khong_ho_so = SimpleNamespace(id=777, employee_id=None)
    assert approval_bridge.can_read_request(db, obj.id, khong_ho_so) is False


# ══════════════════════════════════════════════════════════════════════════════
#  3. Hai tab của hộp việc duyệt
# ══════════════════════════════════════════════════════════════════════════════

def _payload(response):
    """Controller trả `JSONResponse` — bóc lấy phần `data` của phong bì chuẩn."""
    import json

    return json.loads(response.body)["data"]


def _to_approve(db, employee):
    from app.modules.leave import inbox_controller

    return _payload(inbox_controller.to_approve(db=db, user=_user(employee, uid=9)))


def _handled(db, employee):
    from app.modules.leave import inbox_controller

    return _payload(inbox_controller.handled(db=db, user=_user(employee, uid=9)))


def test_tab_can_toi_duyet_chi_hien_don_DANG_cho_chinh_toi(db, flow_2_buoc, leave_type,
                                                           submitter, approver1,
                                                           approver2):
    """Người chặng 2 chưa tới lượt thì tab của họ phải RỖNG.

    Hiện sớm nghĩa là họ mở ra bấm duyệt và ăn lỗi "không có việc nào đang chờ"
    — lỗi đúng nhưng vô nghĩa với thao tác họ vừa làm.
    """
    obj = _submit(db, leave_type, submitter)

    cua_chang1 = _to_approve(db, approver1)
    assert [i["id"] for i in cua_chang1["items"]] == [obj.id]
    assert _to_approve(db, approver2)["items"] == []

    #  Ký xong chặng 1 → bóng chuyển sang chặng 2, và ĐỔI CHIỀU cả hai tab.
    action_service.approve(db, _instance(db, obj), approver1.id, ACTOR, {})
    assert _to_approve(db, approver1)["items"] == []
    assert [i["id"] for i in _to_approve(db, approver2)["items"]] == [obj.id]


def test_dong_trong_tab_mang_du_thong_tin_de_quyet_ngay(db, flow_2_buoc, leave_type,
                                                        submitter, approver1):
    """Thiếu ô nào là người duyệt phải mở tờ đơn ra mới quyết được, và cả tính
    năng «duyệt ngay trên dòng» mất hết ý nghĩa."""
    obj = _submit(db, leave_type, submitter)
    row = _to_approve(db, approver1)["items"][0]

    assert row["employee_name"] == submitter.full_name
    assert row["leave_type_name"] == leave_type.name
    assert row["total_days"] == 2.0
    assert row["reason"] == "Về quê"
    #  `instance_id` là thứ nút Duyệt gọi tới — thiếu nó thì giao diện phải đi
    #  hỏi lại phiên duyệt cho từng dòng.
    assert row["task"]["instance_id"] == obj.approval_instance_id
    assert row["flow"]["steps"][0]["state"] == steps_service.STEP_CURRENT


def test_dong_trong_tab_mang_theo_NGUOI_BAN_GIAO(db, flow_2_buoc, leave_type,
                                                 submitter, approver1):
    """Người nhận bàn giao phải đi kèm ngay trên dòng, kể cả khi RỖNG.

    *Thiếu người bàn giao* là lý do trả đơn phổ biến nhất, tức chính là thứ
    quyết định người duyệt bấm Duyệt hay Trả về. Bắt họ mở tờ đơn ra mới thấy
    thì cả tính năng «duyệt ngay trên dòng» mất lý do tồn tại.
    """
    from app.modules.leave.request_model import LeaveHandover

    nguoi_nhan = _employee(db, "NHAN")
    obj = _submit(db, leave_type, submitter)
    db.add(LeaveHandover(request_id=obj.id, employee_id=nguoi_nhan.id,
                         content="Trực tổng đài", sort_order=1))
    db.commit()

    row = _to_approve(db, approver1)["items"][0]

    assert [h["employee_name"] for h in row["handovers"]] == [nguoi_nhan.full_name]
    assert row["handovers"][0]["content"] == "Trực tổng đài"


def test_khong_ban_giao_thi_tra_DANH_SACH_RONG_chu_khong_thieu_khoa(db, flow_2_buoc,
                                                                    leave_type,
                                                                    submitter, approver1):
    """Thiếu hẳn khóa thì giao diện đọc `undefined` và phải tự đoán — mà đoán sai
    một nhịp là mục bàn giao biến mất, đúng lỗi vừa vá ở màn chi tiết."""
    _submit(db, leave_type, submitter)
    row = _to_approve(db, approver1)["items"][0]

    assert row["handovers"] == []


def test_tab_toi_da_duyet_hien_don_vua_quyet(db, flow_2_buoc, leave_type,
                                             submitter, approver1):
    obj = _submit(db, leave_type, submitter)
    assert _handled(db, approver1)["items"] == []

    action_service.approve(db, _instance(db, obj), approver1.id, ACTOR, {})
    da_duyet = _handled(db, approver1)["items"]

    assert [i["id"] for i in da_duyet] == [obj.id]
    #  Người duyệt cuối phải thấy ĐƯỜNG ĐI trước đó — chặng 1 đã xong, đang ở 2.
    assert da_duyet[0]["flow"]["steps"][0]["state"] == steps_service.STEP_DONE


def test_ky_HAI_CHANG_cua_cung_mot_don_van_chi_MOT_dong(db, flow_2_buoc, leave_type,
                                                        submitter, approver1, approver2):
    """`handled_tasks` trả theo dấu vết nên một người ký hai chặng ra hai bản ghi.

    Trên màn «Tôi đã duyệt» hai dòng đó giống hệt nhau — cùng số đơn, cùng người
    nghỉ, cùng ngày, cùng trạng thái — và đọc ra như lỗi trùng dữ liệu. Dựng lại
    được ngay lần chạy thử đầu tiên (NP011, 03/09/2026).
    """
    from app.modules.approval.instance_model import TASK_PENDING

    obj = _submit(db, leave_type, submitter)
    action_service.approve(db, _instance(db, obj), approver1.id, ACTOR, {})

    #  Chuyển việc chặng 2 về CHÍNH người vừa ký chặng 1 — chuyện thường khi
    #  Nhân sự vừa là trưởng bộ phận vừa là người duyệt cuối, hoặc khi có bàn
    #  giao lúc ai đó nghỉ phép.
    instance = _instance(db, obj)
    task = next(t for t in instance_service.tasks_of_instance(db, instance.id)
                if t.status == TASK_PENDING)
    task.assignee_employee_id = approver1.id
    db.commit()
    action_service.approve(db, _instance(db, obj), approver1.id, ACTOR, {})

    da_duyet = _handled(db, approver1)["items"]
    assert [i["id"] for i in da_duyet] == [obj.id], "Một tờ đơn ra hai dòng giống hệt nhau"


def test_don_bi_xoa_mem_thi_BO_HAN_khoi_tab(db, flow_2_buoc, leave_type,
                                            submitter, approver1):
    """Trả một dòng trống thì người dùng bấm vào chỉ ăn 404, mà con số đếm trên
    tab vẫn tính nó — tab báo "1 việc" trong khi mở ra không có gì."""
    obj = _submit(db, leave_type, submitter)
    obj.is_deleted = True
    db.commit()

    ket_qua = _to_approve(db, approver1)
    assert ket_qua == {"total": 0, "items": []}


def test_tai_khoan_chua_gan_nhan_su_thi_tab_rong_chu_khong_no(db, flow_2_buoc,
                                                              leave_type, submitter):
    from app.modules.leave import inbox_controller

    khong_ho_so = SimpleNamespace(id=777, employee_id=None)
    assert _payload(inbox_controller.to_approve(db=db, user=khong_ho_so))["items"] == []
    assert _payload(inbox_controller.handled(db=db, user=khong_ho_so))["items"] == []


# ══════════════════════════════════════════════════════════════════════════════
#  4. Không N+1 — lý do tồn tại của cả `steps_service`
# ══════════════════════════════════════════════════════════════════════════════

def test_hoi_muoi_don_van_chi_ba_truy_van(db, flow_2_buoc, leave_type, submitter):
    """Số truy vấn phải KHÔNG đổi theo số dòng.

    Mười dòng × (1 phiên + 1 việc + n tên) là hơn ba mươi lượt cho một lần mở
    trang, và nó chỉ lộ ra trên dữ liệu thật chứ không lộ khi chạy thử với hai
    dòng. Con số 3 ở đây là trần cứng: thêm dữ liệu gì vào dải chấm thì cũng
    không được đặt truy vấn trong vòng lặp.
    """
    from sqlalchemy import event

    #  Loại nghỉ KHÔNG trừ quỹ: bài này đo số truy vấn, không đo luật quỹ phép.
    #  Dùng «Phép năm» thì đơn thứ bảy đã ăn "không đủ phép" và bài chết vì một
    #  lý do chẳng liên quan gì tới thứ nó định kiểm.
    khong_tru_quy = LeaveType(code="unpaid", name="Nghỉ không lương",
                              counts_balance=False)
    db.add(khong_tru_quy)
    db.flush()

    ids = [_submit(db, khong_tru_quy, submitter, start=MONDAY + timedelta(days=7 * i)).id
           for i in range(10)]

    dem = []
    def _ghi(conn, cursor, statement, *args):
        dem.append(statement)

    event.listen(db.get_bind(), "before_cursor_execute", _ghi)
    try:
        rows = steps_service.steps_of_entities(db, ENTITY, ids)
    finally:
        event.remove(db.get_bind(), "before_cursor_execute", _ghi)

    assert len(rows) == 10
    assert len(dem) <= 3, f"Đã quay lại N+1: {len(dem)} truy vấn cho 10 dòng"
