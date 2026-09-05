"""Cụm 06 — Nhân sự · Hành chính · Nghỉ phép · Phòng họp · Đặt xe (trục B).

Cụm này khác mấy cụm chứng từ ở HẬU QUẢ. Lỗ ở cụm 03 là thấy nhầm một đơn
hàng; lỗ ở đây là đọc được lý do nghỉ ốm của đồng nghiệp, xem quỹ phép người
khác, hoặc **đi vòng qua chính bộ máy phân quyền** — vì hồ sơ nhân sự là nơi
`get_perm_profile` lấy `company_id` / `dept_ids` ra để dựng phạm vi.

Bốn nhóm:

* **A — nghỉ phép.** `leave_request` là entity DUY NHẤT cố ý nới rộng ngoài
  `apply_scope` (CR-260). Nhóm này soi đúng chỗ nới: nới cho một tờ đơn khi
  đang treo việc, KHÔNG nới cho danh sách, KHÔNG nới cho đường ghi, và đóng
  lại ngay khi ký xong. Kèm ranh giới `leave_balance` — khóa ghi được nghĩa là
  tặng ngày phép cho bất kỳ ai.
* **B — phòng họp + đặt xe.** Hai entity khai `owner` + `self`/`assigned`.
* **C — nhân sự · tài khoản · phòng ban · pháp nhân.** Nhóm tìm được ba lỗ
  thật, xem `# 🔴` trong nhóm này.
* **D — ba chốt gán phòng ban (L1/L2/L3) + tự nới phạm vi.** Gán phòng ban là
  thao tác NHẠY VỀ QUYỀN: thêm một phòng cho ai đó = mở rộng tầm nhìn dữ liệu
  của họ, đúng bằng tick thêm một ô trong ma trận quyền.

⚠️ Mọi khẳng định so bằng **set id cụ thể** trên dữ liệu có thật trong bảng.

Không lặp lại phần đã có nơi khác: `can_read_request` mức hàm và hai tab hộp
việc nằm ở `test_nghi_phep_hop_viec_duyet.py`; ba chốt L1/L2/L3 mức *service*
với hồ sơ quyền giả nằm ở `test_kiem_nhiem_phong_ban.py`; dọn `UserScope` khi
xóa tài khoản nằm ở `test_user_cleanup.py`. Ở đây là mức **controller với
grant thật**, tức đúng tư thế người dùng thật ngồi trước màn hình.
"""
from datetime import date, datetime, timedelta

import pytest
from fastapi import HTTPException

from scope_factory import build_world  # noqa: F401 — fixture `world` dùng nó

TODAY = date(2026, 3, 2)


# ══════════════════════════════════════════════════════════════════════════════
#  Dựng dữ liệu — mỗi hàm một loại chứng từ, tên tiếng Anh dạng ĐỘNG TỪ
# ══════════════════════════════════════════════════════════════════════════════

def create_leave_request(db, *, code, company_id, department_id, employee_id,
                         created_by, status=2):
    """Một đơn nghỉ tối thiểu — chỉ điền cột mà `SCOPE_FIELDS` nhìn tới."""
    from app.modules.leave.request_model import LeaveRequest

    row = LeaveRequest(code=code, company_id=company_id, department_id=department_id,
                       employee_id=employee_id, leave_type_id=1,
                       from_date=TODAY, to_date=TODAY + timedelta(days=1),
                       total_days=2.0, reason="Về quê", status=status,
                       created_by=created_by)
    db.add(row)
    db.flush()
    return row


def create_pending_task(db, entity, entity_id, assignee_employee_id):
    """Một phiên duyệt ĐANG CHẠY kèm một việc ĐANG TREO cho người này.

    Ghi thẳng hai bảng thay vì chạy cả bộ máy: `has_pending_task` đọc đúng hai
    bảng này, và ca kiểm cần điều khiển được trạng thái việc theo từng bước.
    """
    from app.modules.approval.instance_model import (INSTANCE_RUNNING,
                                                     TASK_PENDING,
                                                     ApprovalInstance,
                                                     ApprovalTask)

    instance = ApprovalInstance(entity=entity, entity_id=entity_id, flow_id=1,
                                status=INSTANCE_RUNNING, current_seq=1,
                                started_at=datetime.now())
    db.add(instance)
    db.flush()
    task = ApprovalTask(instance_id=instance.id, node_seq=1, node_name="Chặng 1",
                        assignee_employee_id=assignee_employee_id,
                        status=TASK_PENDING)
    db.add(task)
    db.flush()
    return instance, task


def create_balance(db, *, employee_id, company_id, year=2026, allocated=12.0):
    from app.modules.leave.balance_model import LeaveBalance

    row = LeaveBalance(employee_id=employee_id, company_id=company_id, year=year,
                       leave_type_id=1, allocated_days=allocated)
    db.add(row)
    db.flush()
    return row


def create_room_booking(db, *, code, company_id, department_id,
                        requester_employee_id, created_by, room_id=1):
    from app.modules.meeting_room.model import RoomBooking

    row = RoomBooking(code=code, room_id=room_id, company_id=company_id,
                      department_id=department_id,
                      requester_employee_id=requester_employee_id,
                      title="Họp tuần",
                      start_at=datetime(2026, 3, 2, 9, 0),
                      end_at=datetime(2026, 3, 2, 10, 0),
                      created_by=created_by)
    db.add(row)
    db.flush()
    return row


def create_meeting_room(db, *, code, company_id):
    from app.modules.meeting_room.model import MeetingRoom

    row = MeetingRoom(code=code, name=f"Phòng {code}", company_id=company_id,
                      is_active=True)
    db.add(row)
    db.flush()
    return row


def create_vehicle_booking(db, *, code, company_id, department_id, created_by,
                           assigned_driver_id=0):
    from app.modules.vehicle_booking.model import VehicleBooking

    row = VehicleBooking(code=code, company_id=company_id,
                         department_id=department_id, created_by=created_by,
                         assigned_driver_id=assigned_driver_id, purpose="Đi công tác")
    db.add(row)
    db.flush()
    return row


def create_driver(db, *, name, user_id):
    from app.modules.vehicle_booking.model import Driver

    row = Driver(name=name, user_id=user_id)
    db.add(row)
    db.flush()
    return row


def model_of(entity: str):
    from scope_factory import model_of as _model_of

    return _model_of(entity)


# ══════════════════════════════════════════════════════════════════════════════
#  A. NGHỈ PHÉP — nới quyền có kiểm soát + ranh giới quỹ phép
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture()
def leave_ids(world) -> dict[str, int]:
    """Bốn đơn nghỉ trải đủ hai pháp nhân, hai phòng, và cả ô nhân sự BỎ TRỐNG.

    `khuyet_nhan_su` (employee_id = 0) là dòng canh nhánh `rid` của
    `_role_scope_cond`: thiếu chốt đó thì `employee_id == 0` trúng nó và phạm
    vi «của mình» hóa ra RỘNG hơn ý định.
    """
    db = world.db
    uid = {k: world.actor(k).user.id for k in ("a1", "a2", "a3", "b1")}
    rows = {
        #  a3 (hành chính) lập HỘ cho a1 — a1 là NGƯỜI NGHỈ, không phải người lập.
        "a1_nghi": (world.co["A"], world.dept["A.kt"], world.emp["a1"], uid["a3"]),
        #  a1 lập hộ a2 — a1 là NGƯỜI LẬP, không phải người nghỉ.
        "a1_lap_ho": (world.co["A"], world.dept["A.kt"], world.emp["a2"], uid["a1"]),
        "a2_tu_nop": (world.co["A"], world.dept["A.kt"], world.emp["a2"], uid["a2"]),
        "b1_tu_nop": (world.co["B"], world.dept["B.kt"], world.emp["b1"], uid["b1"]),
        "khuyet_nhan_su": (world.co["A"], world.dept["A.mua"], 0, uid["a2"]),
    }
    out = {}
    for key, (co, dept, emp, owner) in rows.items():
        out[key] = create_leave_request(db, code=f"NP_{key}", company_id=co,
                                        department_id=dept, employee_id=emp,
                                        created_by=owner).id
    db.commit()
    return out


def pick(ids: dict[str, int], *keys: str) -> set[int]:
    return {ids[k] for k in keys}


def get_leave_or_404(db, rid: int, user, action: str = "read"):
    from app.modules.leave import request_controller

    return request_controller._get_or_404(db, rid, user, action)


def test_a1_nguoi_dang_phai_ky_doc_duoc_don_ngoai_pham_vi_du_lieu(world, leave_ids):
    """Người duyệt chặng 2 thường là Trưởng phòng Nhân sự, mà phạm vi dữ liệu
    của họ không với tới đơn của nhân viên phòng khác — `apply_scope` MỘT MÌNH
    không đủ (CR-260).

    Hỏng thì hỏng theo kiểu ngớ ngẩn nhất: bộ máy giao việc cho họ, gửi thông
    báo cho họ, rồi chặn họ mở tờ đơn ra đọc. Họ phải ký một thứ không được
    phép nhìn, và không ai gỡ được bằng cách khai lại quyền.
    """
    b1 = world.grant("b1", "leave_request", scope="own")
    rid = leave_ids["a1_nghi"]

    #  Vế đối chứng TRƯỚC: chưa có việc thì đúng là không đọc được.
    with pytest.raises(HTTPException) as err:
        get_leave_or_404(world.db, rid, b1.user)
    assert err.value.status_code == 404

    create_pending_task(world.db, "leave_request", rid, world.emp["b1"])
    world.db.commit()

    assert get_leave_or_404(world.db, rid, b1.user).id == rid


def test_a2_ky_xong_thi_quyen_doc_them_do_dong_lai(world, leave_ids):
    """Nới đúng LÚC TREO, không nới cho «đã từng ký».

    Nới rộng hơn thì mỗi lượt ký lại thêm VĨNH VIỄN một tờ đơn vào tầm nhìn của
    một người, và phạm vi dữ liệu phình dần theo thời gian mà không ai rà lại
    được. Xem lại phiếu mình đã ký thì vào tab «Tôi đã duyệt», nơi dữ liệu vốn
    đã lọc theo chính họ.
    """
    from app.modules.approval.instance_model import TASK_APPROVED

    b1 = world.grant("b1", "leave_request", scope="own")
    rid = leave_ids["a1_nghi"]
    _, task = create_pending_task(world.db, "leave_request", rid, world.emp["b1"])
    world.db.commit()
    assert get_leave_or_404(world.db, rid, b1.user).id == rid   # đang treo: đọc được

    task.status = TASK_APPROVED
    task.decided_at = datetime.now()
    world.db.commit()

    with pytest.raises(HTTPException) as err:
        get_leave_or_404(world.db, rid, b1.user)
    assert err.value.status_code == 404, "ký xong mà vẫn đọc được là phạm vi phình ra"


def test_a3_nguoi_cung_phong_nhung_khong_duoc_giao_viec_van_bi_chan(world, leave_ids):
    """Nới theo VIỆC ĐƯỢC GIAO, không nới theo chỗ ngồi.

    a2 ngồi cùng phòng A.kt với a1 nhưng phạm vi của a2 là «của mình». Cho a2
    đọc vì «cùng phòng» thì lý do nghỉ ốm thành thứ cả phòng đọc được — mà
    người khai quyền tưởng mình đã bó bằng phạm vi `own`.
    """
    a2 = world.grant("a2", "leave_request", scope="own")
    create_pending_task(world.db, "leave_request", leave_ids["a1_nghi"], world.emp["b1"])
    world.db.commit()

    with pytest.raises(HTTPException) as err:
        get_leave_or_404(world.db, leave_ids["a1_nghi"], a2.user)
    assert err.value.status_code == 404


def test_a4_noi_dung_mot_to_don_khong_noi_ca_danh_sach(world, leave_ids):
    """Chỗ nới nằm ở `_get_or_404`, KHÔNG nằm trong `apply_scope`.

    Đây là ranh giới quan trọng nhất của cả cơ chế: nới ở tầng danh sách thì
    người duyệt một tờ đơn bỗng nhìn thấy mọi đơn của phòng đó trong màn danh
    sách, tab «Đơn của tôi» lẫn sang đơn người khác, và bản xuất CSV kéo theo.
    """
    from app.modules.leave.request_model import LeaveRequest

    b1 = world.grant("b1", "leave_request", scope="own")
    create_pending_task(world.db, "leave_request", leave_ids["a1_nghi"], world.emp["b1"])
    world.db.commit()

    assert b1.sees(LeaveRequest, "leave_request") == pick(leave_ids, "b1_tu_nop"), (
        "danh sách chỉ được có đơn trong phạm vi, không có tờ đơn đang phải ký")
    assert get_leave_or_404(world.db, leave_ids["a1_nghi"], b1.user).id == \
        leave_ids["a1_nghi"], "nhưng mở thẳng tờ đơn đó thì vẫn được"


def test_a4b_duoc_giao_ky_khong_keo_theo_quyen_sua_xoa_huy(world, leave_ids):
    """Nới CHỈ cho `read`. Được giao ký không có nghĩa là được sửa đơn người khác.

    `_get_or_404` chỉ gọi `_readable_by_approver` khi `action == "read"`. Bỏ
    điều kiện đó đi thì người duyệt sửa được ngày nghỉ trên tờ đơn rồi mới ký,
    và người nộp không có cách nào biết.
    """
    b1 = world.grant("b1", "leave_request", scope="own",
                     actions=("read", "write", "delete", "cancel"))
    rid = leave_ids["a1_nghi"]
    create_pending_task(world.db, "leave_request", rid, world.emp["b1"])
    world.db.commit()

    for action in ("write", "delete", "cancel"):
        with pytest.raises(HTTPException) as err:
            get_leave_or_404(world.db, rid, b1.user, action)
        assert err.value.status_code == 404, f"đường ghi «{action}» không được nới"


def test_a5_pham_vi_cua_minh_gom_ca_nguoi_lap_ho_lan_nguoi_nghi(world, leave_ids):
    """`leave_request` là entity ĐẦU TIÊN khai cả `owner` lẫn `self`.

    Một tờ đơn có hai người dính tới nó. Chỉ khai `owner` thì người nghỉ ở phạm
    vi `own` không thấy đơn của CHÍNH MÌNH (hành chính lập hộ); chỉ khai `self`
    thì người lập hộ nộp xong là mất dấu tờ đơn.

    Dòng `khuyet_nhan_su` (employee_id = 0) canh chốt `rid`: `employee_id == 0`
    mà không chặn thì nó trúng mọi dòng chưa gắn nhân sự — phạm vi «của mình»
    hóa ra RỘNG hơn, đúng chiều nguy hiểm.
    """
    from app.modules.leave.request_model import LeaveRequest

    a1 = world.grant("a1", "leave_request", scope="own")
    assert a1.sees(LeaveRequest, "leave_request") == pick(leave_ids, "a1_nghi",
                                                          "a1_lap_ho")


def test_a5b_tai_khoan_chua_gan_nhan_su_khong_vo_don_khuyet_nhan_su(world, leave_ids):
    """Vế đối chứng của chốt `rid`, dựng bằng người thật.

    `khongcty` chưa gắn pháp nhân lẫn phòng ban, `employee_id` của họ có thật
    nên `rid` khác 0 — nhưng không đơn nào mang id đó. Nếu ai gỡ chốt `rid` ở
    `_role_scope_cond` thì dòng `employee_id = 0` sẽ lọt vào đây, và ca này đỏ.
    """
    from app.modules.leave.request_model import LeaveRequest

    khongcty = world.grant("khongcty", "leave_request", scope="own")
    assert khongcty.sees(LeaveRequest, "leave_request") == set()


def test_a6_quyen_ghi_don_nghi_khong_keo_theo_quyen_cham_quy_phep(world):
    """🔒 Ranh giới tồn tại của khóa `leave_balance`: ghi được = **tặng thêm
    ngày phép cho bất kỳ ai** qua cột «điều chỉnh tay».

    Đó là lý do nó tách khỏi `leave_request` chứ không đi chung một khóa. Ca
    này ghim rằng hai khóa thật sự tách: `leave_request.write` phạm vi *tất cả*
    không chạm được một dòng quỹ nào.
    """
    from app.modules.leave.balance_model import LeaveBalance

    db = world.db
    quy_a1 = create_balance(db, employee_id=world.emp["a1"], company_id=world.co["A"])
    quy_b1 = create_balance(db, employee_id=world.emp["b1"], company_id=world.co["B"])
    db.commit()
    assert {quy_a1.id, quy_b1.id} == {r.id for r in db.query(LeaveBalance).all()}

    a1 = world.grant("a1", "leave_request", scope="all", actions=("read", "write"))
    assert a1.sees(LeaveBalance, "leave_balance") == set(), "không grant nào trên quỹ"
    assert a1.can_get(LeaveBalance, quy_a1.id, "leave_balance", "write") is False


def test_a6b_quy_phep_pham_vi_cong_ty_khong_cham_quy_phap_nhan_khac(world):
    """Cấp `leave_balance.write` phạm vi *pháp nhân* rồi thì phải dừng đúng ở đó.

    `SCOPE_FIELDS["leave_balance"]` khai `company` + `self`, KHÔNG khai `owner`
    (`created_by` là người Nhân sự bấm nút cấp phát — lấy đó làm «của mình» thì
    nhân viên xem quỹ của chính họ lại không ra dòng nào).
    """
    from app.modules.leave.balance_model import LeaveBalance

    db = world.db
    quy_a1 = create_balance(db, employee_id=world.emp["a1"], company_id=world.co["A"])
    quy_a2 = create_balance(db, employee_id=world.emp["a2"], company_id=world.co["A"])
    quy_b1 = create_balance(db, employee_id=world.emp["b1"], company_id=world.co["B"])
    db.commit()

    a1 = world.grant("a1", "leave_balance", scope="company", actions=("read", "write"))
    assert a1.sees(LeaveBalance, "leave_balance") == {quy_a1.id, quy_a2.id}
    assert a1.can_get(LeaveBalance, quy_b1.id, "leave_balance", "write") is False


def test_a6c_quy_phep_pham_vi_cua_minh_la_quy_CUA_TOI_khong_phai_quy_toi_cap(world):
    """`own` trên quỹ phép nghĩa là «quỹ của tôi», neo bằng `self`.

    Nếu ai đó thêm `owner: created_by` vào khai báo cho «nhất quán» thì người
    Nhân sự bấm nút cấp phát bỗng thành chủ sở hữu quỹ của cả công ty, còn nhân
    viên mở màn «Quỹ phép của tôi» thì trắng bóc. Ca này ghim cả hai chiều.
    """
    from app.modules.leave.balance_model import LeaveBalance

    db = world.db
    nhan_su = world.actor("a3").user.id     # người bấm nút cấp phát
    quy_a1 = create_balance(db, employee_id=world.emp["a1"], company_id=world.co["A"])
    quy_a2 = create_balance(db, employee_id=world.emp["a2"], company_id=world.co["A"])
    quy_a1.created_by = nhan_su
    quy_a2.created_by = nhan_su
    db.commit()

    a1 = world.grant("a1", "leave_balance", scope="own")
    assert a1.sees(LeaveBalance, "leave_balance") == {quy_a1.id}

    a3 = world.grant("a3", "leave_balance", scope="own")
    assert a3.sees(LeaveBalance, "leave_balance") == set(), (
        "người CẤP PHÁT không phải chủ quỹ")


def test_a6d_duong_my_balance_bo_theo_pham_vi_quy_phep(world):
    """CANH KHÔNG TÁI PHÁT — `GET /api/leave-requests/tools/my-balance`.

    Lỗ cũ: route gác bằng `require("leave_request", "read")` rồi nạp người nghỉ
    bằng `request_service.resolve_leave_taker` = `db.get(Employee, ...)` trần —
    không `apply_scope`, không `get_scoped`. Bất kỳ ai có `leave_request.read`
    **phạm vi hẹp nhất** chỉ cần truyền `employee_id` lên URL là đọc được
    `total_days` / `used_days` / `remaining_days` của bất kỳ nhân sự nào trong
    hệ, kể cả pháp nhân khác. Đó là đúng dữ liệu mà khóa `leave_balance` sinh ra
    để gác, và ca A6/A6b ở trên chứng minh khóa ấy gác đúng ở ĐƯỜNG CHÍNH
    (`GET /api/leave-balances`) — đường này đi vòng qua nó.

    Vá 05/09/2026 (`_ensure_balance_in_scope`, `request_controller.py:271-297`):
    quỹ của NGƯỜI KHÁC phải nằm trong phạm vi khóa **`leave_balance`**, không thì
    404. Cố ý KHÔNG bó bằng `employee` — dữ liệu bị lộ là quỹ phép, nên hỏi đúng
    khóa gác quỹ phép. Quỹ của CHÍNH MÌNH thì không đòi thêm khóa nào: ai nộp
    được đơn cũng phải thấy số còn lại, bắt cấp thêm một khóa nữa là chắc chắn có
    người quên cấp rồi ô đó hiện 0 vĩnh viễn.

    ⚠️ Bản vá còn `db.rollback()` trước khi ném: `ensure_balance` **tự cấp phát**
    một dòng quỹ khi chưa có, nên không hoàn tác thì một lượt dò id cũng ghi được
    vào sổ quỹ. Ca này đo cả điều đó.

    Ba vế: chặn người ngoài phạm vi · KHÔNG chặn quỹ của chính mình · KHÔNG chặn
    hành chính có `leave_balance` trong phạm vi.
    """
    import json

    import pytest
    from fastapi import HTTPException

    from app.modules.leave import request_controller
    from app.modules.leave.balance_model import LeaveBalance
    from app.modules.leave.catalog_model import LeaveType

    db = world.db
    loai = LeaveType(code="annual", name="Phép năm", counts_balance=True,
                     annual_quota_days=12.0, is_active=True)
    db.add(loai)
    db.flush()
    quy_b1 = create_balance(db, employee_id=world.emp["b1"], company_id=world.co["B"])
    quy_b1.leave_type_id = loai.id
    quy_b1.used_days = 3.0
    quy_a1 = create_balance(db, employee_id=world.emp["a1"], company_id=world.co["A"])
    quy_a1.leave_type_id = loai.id
    quy_a1.used_days = 1.0
    quy_a2 = create_balance(db, employee_id=world.emp["a2"], company_id=world.co["A"])
    quy_a2.leave_type_id = loai.id
    quy_a2.used_days = 2.0
    db.commit()
    truoc = {r.id for r in db.query(LeaveBalance).all()}

    def goi(actor, employee_id):
        return json.loads(request_controller.my_balance(
            leave_type_id=loai.id, year=2026, employee_id=employee_id,
            db=db, user=actor.user).body)["data"]

    #  ── Vế CHẶN: chỉ có `leave_request.read` phạm vi hẹp nhất ────────────────
    a1 = world.grant("a1", "leave_request", scope="own")
    assert a1.can_get(LeaveBalance, quy_b1.id, "leave_balance") is False, (
        "đường chính vẫn chặn đúng")

    with pytest.raises(HTTPException) as err:
        goi(a1, world.emp["b1"])
    assert err.value.status_code == 404, "404 chứ không 403 — đừng xác nhận quỹ có thật"
    assert {r.id for r in db.query(LeaveBalance).all()} == truoc, (
        "một lượt dò id không được để lại dòng quỹ mới")

    #  ── Vế KHÔNG CHẶN NHẦM 1: quỹ CỦA CHÍNH MÌNH, không cần khóa `leave_balance` ─
    cua_toi = goi(a1, 0)                       # bỏ trống ô ⇒ chính người đang gọi
    assert cua_toi["employee_id"] == world.emp["a1"]
    assert (cua_toi["used_days"], cua_toi["total_days"]) == (1.0, 12.0)
    assert goi(a1, world.emp["a1"])["used_days"] == 1.0, "gõ đúng id mình cũng vậy"

    #  ── Vế KHÔNG CHẶN NHẦM 2: hành chính lập hộ, có `leave_balance` bậc pháp nhân ─
    hc = world.grant("a3", "leave_request", scope="own")
    hc.grant("leave_balance", scope="company")
    doc_ho = goi(hc, world.emp["a2"])
    assert (doc_ho["employee_id"], doc_ho["used_days"]) == (world.emp["a2"], 2.0), (
        "người trong phạm vi quỹ vẫn phải xem hộ được — bản vá không được khóa việc thật")

    with pytest.raises(HTTPException) as err:
        goi(hc, world.emp["b1"])
    assert err.value.status_code == 404, "…nhưng dừng đúng ở ranh giới pháp nhân"


def test_a7_don_nghi_pham_vi_phong_ban_dung_hai_chieu_phap_nhan_va_phong(world, leave_ids):
    """Bậc `dept` của đơn nghỉ = pháp nhân AND phòng — hai chiều, không phải một.

    Bỏ vế pháp nhân thì phòng trùng tên ở pháp nhân khác lọt vào (thế giới mẫu
    cố ý có `A.kt` và `B.kt` cùng tên «Phòng Kế toán»); bỏ vế phòng thì trưởng
    phòng đọc trọn đơn nghỉ của cả công ty.
    """
    from app.modules.leave.request_model import LeaveRequest

    a1 = world.grant("a1", "leave_request", scope="dept")
    assert a1.sees(LeaveRequest, "leave_request") == pick(
        leave_ids, "a1_nghi", "a1_lap_ho", "a2_tu_nop")


def test_a8_o_loai_tru_nhan_su_tren_don_nghi_cat_theo_NGUOI_LAP(world, leave_ids):
    """Chiều `employee` của năm ô khớp `SCOPE_FIELDS[...]["owner"]` = `created_by`.

    Trên đơn nghỉ phép chuyện đó dễ hiểu nhầm nhất trong cả hệ: người dùng tick
    tên ông X ở ô «Loại trừ nhân sự» và tưởng mình vừa giấu ĐƠN NGHỈ CỦA ông X,
    trong khi hệ giấu ĐƠN DO ông X LẬP. Với một phòng hành chính lập hộ cả công
    ty thì hai tập đó gần như rời nhau.

    # QUYẾT ĐỊNH CHỜ: entity khai cả `owner` lẫn `self` thì ô «Loại trừ nhân
    # sự» nên cắt theo cột nào — người lập (nay), người nghỉ, hay cả hai? Hộp
    # thoại hiện không nói ra nó đang cắt theo cột nào.
    """
    from app.modules.leave.request_model import LeaveRequest

    a1 = world.grant("a1", "leave_request", scope="all", exc_employee=["a2"])
    thay = a1.sees(LeaveRequest, "leave_request")

    assert leave_ids["a1_lap_ho"] in thay, "đơn NGHỈ của a2 vẫn thấy (a1 lập)"
    assert leave_ids["a2_tu_nop"] not in thay, "đơn a2 TỰ LẬP thì bị cắt"
    assert thay == pick(leave_ids, "a1_nghi", "a1_lap_ho", "b1_tu_nop")


# ══════════════════════════════════════════════════════════════════════════════
#  B. ĐẶT PHÒNG HỌP + ĐẶT XE
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture()
def booking_ids(world) -> dict[str, int]:
    db = world.db
    uid = {k: world.actor(k).user.id for k in ("a1", "a2", "a3", "b1")}
    rows = {
        #  Thư ký a3 đặt HỘ a1 — a1 là người chủ trì.
        "a1_chu_tri": (world.co["A"], world.dept["A.kt"], world.emp["a1"], uid["a3"]),
        #  a1 đặt hộ a2 — a1 là người lập.
        "a1_lap_ho": (world.co["A"], world.dept["A.kt"], world.emp["a2"], uid["a1"]),
        "a2_tu_dat": (world.co["A"], world.dept["A.kt"], world.emp["a2"], uid["a2"]),
        "b1_tu_dat": (world.co["B"], world.dept["B.kt"], world.emp["b1"], uid["b1"]),
    }
    out = {}
    for key, (co, dept, emp, owner) in rows.items():
        out[key] = create_room_booking(db, code=f"PH_{key}", company_id=co,
                                       department_id=dept,
                                       requester_employee_id=emp,
                                       created_by=owner).id
    db.commit()
    return out


def test_b1_nguoi_dat_ho_va_nguoi_chu_tri_deu_thay_o_pham_vi_cua_minh(world, booking_ids):
    """Cùng lẽ với đơn nghỉ phép: một phiếu có hai người dính tới nó.

    Thư ký đặt hộ sếp là việc hằng ngày. Chỉ khai `owner` thì sếp không thấy
    cuộc họp của chính mình; chỉ khai `self` thì thư ký đặt xong mất dấu phiếu
    và không sửa lại được giờ.
    """
    from app.modules.meeting_room.model import RoomBooking

    a1 = world.grant("a1", "room_booking", scope="own")
    assert a1.sees(RoomBooking, "room_booking") == pick(booking_ids, "a1_chu_tri",
                                                        "a1_lap_ho")


def test_b2_nguoi_dang_phai_ky_phieu_dat_phong_doc_duoc_no(world, booking_ids):
    """Đặt phòng họp dùng lại đúng khuôn nới của nghỉ phép
    (`meeting_room/controller._get_or_404` + `approval_bridge.can_read_booking`).

    Hai bản chép tay của một luật thì sớm muộn lệch nhau — ca này canh cho bản
    của phòng họp không bị bỏ quên khi bản của nghỉ phép được sửa.
    """
    from app.modules.meeting_room import controller as room_controller

    b1 = world.grant("b1", "room_booking", scope="own")
    bid = booking_ids["a1_chu_tri"]

    with pytest.raises(HTTPException) as err:
        room_controller._get_or_404(world.db, bid, b1.user)
    assert err.value.status_code == 404

    create_pending_task(world.db, "room_booking", bid, world.emp["b1"])
    world.db.commit()
    assert room_controller._get_or_404(world.db, bid, b1.user).id == bid


def test_b2b_ky_xong_thi_phieu_dat_phong_cung_dong_lai(world, booking_ids):
    """Đối xứng với A2. Bịt một bên mà quên bên kia là bịt nửa lỗ."""
    from app.modules.approval.instance_model import TASK_APPROVED
    from app.modules.meeting_room import controller as room_controller

    b1 = world.grant("b1", "room_booking", scope="own")
    bid = booking_ids["a1_chu_tri"]
    _, task = create_pending_task(world.db, "room_booking", bid, world.emp["b1"])
    world.db.commit()
    assert room_controller._get_or_404(world.db, bid, b1.user).id == bid

    task.status = TASK_APPROVED
    world.db.commit()
    with pytest.raises(HTTPException) as err:
        room_controller._get_or_404(world.db, bid, b1.user)
    assert err.value.status_code == 404


def test_b3_danh_muc_phong_hop_la_public_nen_nam_o_pham_vi_khong_co_tac_dung(world):
    """`meeting_room` khai `PUBLIC` CÓ CHỦ Ý: `company_id = 0` nghĩa là *phòng
    dùng chung mọi pháp nhân* (toà nhà chung), mà lọc `company_id == <của tôi>`
    thì cắt mất đúng những phòng dùng chung ấy.

    Hệ quả là năm ô trong hộp thoại «Phạm vi» thành trang trí trên màn Danh mục
    phòng họp — người khai quyền tick, bấm Lưu, nhận «Đã lưu phạm vi», và không
    có gì thay đổi. Đây không phải lỗi của `scoping.py`; đó là lỗ hổng của
    MÀN HÌNH: nó không nói ra.

    # QUYẾT ĐỊNH CHỜ: hộp thoại có nên tắt năm ô kèm câu «Danh mục này dùng
    # chung mọi pháp nhân — phạm vi dữ liệu không áp dụng» cho entity PUBLIC?
    # (Cùng câu hỏi với B4 cụm 01 — nên trả lời một lần cho mọi entity PUBLIC.)
    """
    from app.modules.meeting_room.model import MeetingRoom

    db = world.db
    ids = {create_meeting_room(db, code="P.A", company_id=world.co["A"]).id,
           create_meeting_room(db, code="P.B", company_id=world.co["B"]).id,
           create_meeting_room(db, code="P.CHUNG", company_id=0).id}
    db.commit()
    assert len(ids) == 3, "phải có dữ liệu thật rồi mới khẳng định"

    a1 = world.grant("a1", "meeting_room", scope="own", inc_company=["A"],
                     inc_dept=["A.kt"], exc_dept=["A.kt"], exc_employee=["a2"])
    assert a1.sees(MeetingRoom, "meeting_room") == ids


def test_b3b_lich_phong_gop_phong_dung_chung_voi_phong_cua_phap_nhan_minh(world):
    """Lọc đúng nằm ở `service.list_availability`, KHÔNG ở `apply_scope`.

    Đây là lý do `meeting_room` được khai `PUBLIC` chứ không khai `company`:
    câu hỏi thật là *«phòng của pháp nhân tôi HỢP phòng dùng chung»*, không
    diễn đạt được bằng khuôn một-cột. Ca này ghim rằng câu HỢP đó có thật —
    thiếu nó thì toà nhà chung không đặt được phòng nào.
    """
    from app.modules.meeting_room import service as room_service

    db = world.db
    p_a = create_meeting_room(db, code="P.A", company_id=world.co["A"])
    p_b = create_meeting_room(db, code="P.B", company_id=world.co["B"])
    p_chung = create_meeting_room(db, code="P.CHUNG", company_id=0)
    db.commit()

    ket_qua = room_service.list_availability(db, datetime(2026, 3, 2, 9, 0),
                                             datetime(2026, 3, 2, 10, 0),
                                             world.co["A"])
    assert {r["room_id"] for r in ket_qua} == {p_a.id, p_chung.id}
    assert p_b.id not in {r["room_id"] for r in ket_qua}


def test_b3c_lich_phong_khong_truyen_phap_nhan_thi_bay_ca_hai_ben(world, booking_ids):
    """🟡 `company_id` của `/availability` là THAM SỐ NGƯỜI GỌI, không lấy từ hồ
    sơ quyền — bỏ trống là ra phòng của mọi pháp nhân, kèm **tiêu đề cuộc họp**
    của phiếu đang giữ phòng.

    Ghim HÀNH VI HIỆN TẠI, không kết luận là lỗ: màn hình gọi kèm pháp nhân, và
    ô `bookings` cố ý trả cả phiếu bận để người đặt biết «P301 bận vì PH012 tới
    10:30» mà đi xin hoặc dời giờ. Nhưng đường này gọi tay được, và tiêu đề
    cuộc họp thì `apply_scope` không hề chạm tới.

    # QUYẾT ĐỊNH CHỜ: lịch phòng là thứ CỐ Ý công khai xuyên pháp nhân hay
    # không? Nếu có thì ô `bookings` nên bỏ `title` khi phiếu nằm ngoài phạm vi
    # người xem (giữ khung giờ, bỏ nội dung) — «bận» là thông tin cần, «họp về
    # việc gì» thì không.
    """
    from app.modules.meeting_room import service as room_service
    from app.modules.meeting_room.constants import RB_APPROVED
    from app.modules.meeting_room.model import RoomBooking

    db = world.db
    p_a = create_meeting_room(db, code="P.A", company_id=world.co["A"])
    p_b = create_meeting_room(db, code="P.B", company_id=world.co["B"])
    phieu_b = db.get(RoomBooking, booking_ids["b1_tu_dat"])
    phieu_b.room_id = p_b.id
    phieu_b.status = RB_APPROVED
    phieu_b.title = "Họp giá vốn quý 1"
    db.commit()

    ket_qua = room_service.list_availability(db, datetime(2026, 3, 2, 9, 0),
                                             datetime(2026, 3, 2, 10, 0), 0)
    assert {r["room_id"] for r in ket_qua} == {p_a.id, p_b.id}
    o_phong_b = next(r for r in ket_qua if r["room_id"] == p_b.id)
    assert o_phong_b["available"] is False
    assert o_phong_b["bookings"][0]["title"] == "Họp giá vốn quý 1"


def test_b4_tai_xe_thay_phieu_duoc_phan_cho_minh_va_khong_thay_phieu_khac(world):
    """Bậc `assigned` của `vehicle_booking` nối qua `Driver.user_id`.

    Nhờ nhánh đó nút Chấp nhận / Bắt đầu / Hoàn tất mới tới được đúng tài xế.
    Thiếu nó thì tài xế nội bộ đăng nhập vào thấy trắng, và người điều phối
    phải gọi điện báo từng chuyến.
    """
    from app.modules.vehicle_booking.model import VehicleBooking

    db = world.db
    tai_xe_a3 = create_driver(db, name="Tài xế a3", user_id=world.actor("a3").user.id)
    tai_xe_khac = create_driver(db, name="Tài xế khác", user_id=world.actor("b1").user.id)

    duoc_phan = create_vehicle_booking(db, code="DX_PHAN", company_id=world.co["A"],
                                       department_id=world.dept["A.kt"],
                                       created_by=world.actor("b1").user.id,
                                       assigned_driver_id=tai_xe_a3.id)
    tu_dat = create_vehicle_booking(db, code="DX_TU", company_id=world.co["A"],
                                    department_id=world.dept["A.mua"],
                                    created_by=world.actor("a3").user.id)
    cua_nguoi_khac = create_vehicle_booking(db, code="DX_KHAC", company_id=world.co["A"],
                                            department_id=world.dept["A.kt"],
                                            created_by=world.actor("a2").user.id,
                                            assigned_driver_id=tai_xe_khac.id)
    db.commit()
    assert len({b.id for b in db.query(VehicleBooking).all()}) == 3

    a3 = world.grant("a3", "vehicle_booking", scope="assigned")
    assert a3.sees(VehicleBooking, "vehicle_booking") == {duoc_phan.id, tu_dat.id}
    assert a3.can_get(VehicleBooking, cua_nguoi_khac.id, "vehicle_booking") is False


def test_b5_dieu_phoi_doi_tai_xe_thi_tai_xe_cu_mat_phieu(world):
    """Phạm vi phải theo dữ liệu HIỆN TẠI, không đóng băng lúc phân chuyến.

    Đổi tài xế mà người cũ vẫn đọc được phiếu thì họ vẫn thấy điểm đón, số điện
    thoại người đi và lịch trình của một chuyến không còn là của mình. Ca này
    cũng chứng minh điều kiện là truy vấn con trên `tab_driver` chứ không phải
    một giá trị chép sẵn vào hồ sơ quyền.
    """
    from app.modules.vehicle_booking.model import VehicleBooking

    db = world.db
    tai_xe_cu = create_driver(db, name="Tài xế cũ", user_id=world.actor("a3").user.id)
    tai_xe_moi = create_driver(db, name="Tài xế mới", user_id=world.actor("a2").user.id)
    phieu = create_vehicle_booking(db, code="DX_DOI", company_id=world.co["A"],
                                   department_id=world.dept["A.kt"],
                                   created_by=world.actor("b1").user.id,
                                   assigned_driver_id=tai_xe_cu.id)
    db.commit()

    a3 = world.grant("a3", "vehicle_booking", scope="assigned")
    a2 = world.grant("a2", "vehicle_booking", scope="assigned")
    assert a3.sees(VehicleBooking, "vehicle_booking") == {phieu.id}
    assert a2.sees(VehicleBooking, "vehicle_booking") == set()

    phieu.assigned_driver_id = tai_xe_moi.id
    db.commit()

    assert a3.sees(VehicleBooking, "vehicle_booking") == set(), "tài xế cũ phải mất phiếu"
    assert a2.sees(VehicleBooking, "vehicle_booking") == {phieu.id}


def test_b6_phieu_ho_tro_khong_co_chieu_phong_ban_nen_hai_o_do_cam(world):
    """`ticket` khai `company` + `owner`, KHÔNG có `dept_id`/`dept_name`.

    `_explicit_cond` gặp cột `None` thì `continue` — bỏ qua, không log, không
    lỗi. Nghĩa là ô «Loại trừ phòng ban» trên màn Phiếu hỗ trợ là một ô câm, và
    người khai quyền không có cách nào biết.

    Vế đối chứng bên dưới cho thấy sự vô hiệu ấy RIÊNG của chiều phòng ban:
    chiều pháp nhân vẫn cắt đúng.

    # QUYẾT ĐỊNH CHỜ: cùng câu hỏi với B6/B7 cụm 01 — `_explicit_cond` nên dùng
    # chung `_chan(...)` khi ô phạm vi trỏ vào chiều entity không có, thay vì
    # `continue` im lặng?
    """
    from app.modules.ticket.model import Ticket

    db = world.db
    t_a = Ticket(code="HT_A", subject="Máy in hỏng", company_id=world.co["A"],
                 created_by=world.actor("a1").user.id)
    t_b = Ticket(code="HT_B", subject="Mất mạng", company_id=world.co["B"],
                 created_by=world.actor("b1").user.id)
    db.add_all([t_a, t_b])
    db.commit()
    assert len({t.id for t in db.query(Ticket).all()}) == 2

    a1 = world.grant("a1", "ticket", scope="all", exc_dept=["A.kt"])
    assert a1.sees(Ticket, "ticket") == {t_a.id, t_b.id}, "ô phòng ban vô hiệu"

    a2 = world.grant("a2", "ticket", scope="company")
    assert a2.sees(Ticket, "ticket") == {t_a.id}, "chiều pháp nhân vẫn cắt đúng"


def test_b7_duyet_dau_khai_du_pham_vi_du_chua_co_controller_nao(world):
    """`seal_request` nằm trong `SCOPE_FIELDS` với đủ ba chiều nhưng CHƯA có API.

    Ghi vào danh sách trắng: ngày ai đó dựng controller cho nó thì khai báo
    phạm vi đã sẵn sàng và đúng. Ca này chạy `apply_scope` thật trên dữ liệu
    thật để lời hứa đó không phải chỉ là một dòng trong bảng — thêm entity vào
    `ENTITIES` mà khai sai cột thì đây là chỗ đỏ lên.
    """
    from app.modules.seal_request.model import SealRequest

    db = world.db
    s_akt = SealRequest(code="DD_AKT", seal_type_id=1, company_id=world.co["A"],
                        department_id=world.dept["A.kt"],
                        created_by=world.actor("a2").user.id)
    s_amua = SealRequest(code="DD_AMUA", seal_type_id=1, company_id=world.co["A"],
                         department_id=world.dept["A.mua"],
                         created_by=world.actor("a3").user.id)
    s_b = SealRequest(code="DD_B", seal_type_id=1, company_id=world.co["B"],
                      department_id=world.dept["B.kt"],
                      created_by=world.actor("b1").user.id)
    db.add_all([s_akt, s_amua, s_b])
    db.commit()

    a1 = world.grant("a1", "seal_request", scope="dept")
    assert a1.sees(SealRequest, "seal_request") == {s_akt.id}

    a2 = world.grant("a2", "seal_request", scope="company")
    assert a2.sees(SealRequest, "seal_request") == {s_akt.id, s_amua.id}


# ══════════════════════════════════════════════════════════════════════════════
#  C. NHÂN SỰ · TÀI KHOẢN · PHÒNG BAN · PHÁP NHÂN
# ══════════════════════════════════════════════════════════════════════════════

def test_c1_tai_khoan_chi_khai_self_nen_bac_phong_ban_va_phap_nhan_chan_sach(world):
    """`tab_user` KHÔNG có cột pháp nhân — chiều đó nằm ở hồ sơ nhân sự gắn kèm.

    `SCOPE_FIELDS["user"]` vì thế chỉ khai `self`, và `_role_scope_cond` cho
    `dept`/`company` rơi vào `_chan(...)` → `false()` + WARNING. Đúng ý: người
    xem hẹp không duyệt danh sách tài khoản toàn hệ.

    ⚠️ Hệ quả vận hành phải nhớ: cấp `user` phạm vi *phòng ban* cho một vai trò
    là màn Tài khoản của họ TRẮNG BÓC chứ không phải «hẹp lại». Kiểm seed trước
    khi khai, đừng để người dùng đi báo lỗi hộ.
    """
    from app.modules.user.model import User

    db = world.db
    moi_tai_khoan = {u.id for u in db.query(User).all()}
    assert len(moi_tai_khoan) == 6, "a1 a2 a3 b1 khongphong khongcty — trừ khongtk"

    a1_own = world.grant("a1", "user", scope="own")
    assert a1_own.sees(User, "user") == {world.actor("a1").user.id}

    a2_dept = world.grant("a2", "user", scope="dept")
    assert a2_dept.sees(User, "user") == set(), "bậc phòng ban chặn sạch"

    a3_company = world.grant("a3", "user", scope="company")
    assert a3_company.sees(User, "user") == set(), "bậc pháp nhân cũng chặn sạch"


def test_c2_ho_so_nhan_su_co_self_khong_co_owner_nen_hai_o_nhan_su_cam(world):
    """`SCOPE_FIELDS["employee"]` khai `company` + `dept_id` + `self`, không `owner`.

    Nên `own` nghĩa là «hồ sơ của chính tôi» (đúng), còn hai ô nhân sự trong
    hộp thoại «Phạm vi» thì không có cột nào để so và bị `continue` im lặng.
    Người khai quyền tick «Loại trừ nhân sự: ông X» trên màn Nhân sự và tưởng
    mình vừa giấu hồ sơ ông X.
    """
    from app.modules.employee.model import Employee

    db = world.db
    tat_ca = {e.id for e in db.query(Employee).all()}
    assert len(tat_ca) == 7

    a1_own = world.grant("a1", "employee", scope="own")
    assert a1_own.sees(Employee, "employee") == {world.emp["a1"]}

    a2 = world.grant("a2", "employee", scope="all", exc_employee=["a3"])
    assert a2.sees(Employee, "employee") == tat_ca, "ô loại trừ nhân sự vô hiệu"


def test_c3_phap_nhan_loc_theo_cot_id_chu_khong_phai_company_id(world):
    """Chiều pháp nhân của chính bảng pháp nhân là `id`.

    Khai nhầm thành `company_id` thì `Company` không có cột đó và cả màn Công ty
    nổ 500 — hoặc tệ hơn, ai đó thêm cột cho «hết lỗi» và bộ lọc im lặng trượt.
    """
    from app.modules.company.model import Company

    db = world.db
    tat_ca = {c.id for c in db.query(Company).all()}
    assert tat_ca == {world.co["A"], world.co["B"]}

    a1 = world.grant("a1", "company", scope="company")
    assert a1.sees(Company, "company") == {world.co["A"]}
    assert a1.can_get(Company, world.co["B"], "company") is False


def test_c4_phong_ban_neo_theo_phap_nhan_chinh_khong_theo_bang_phuc_vu(world):
    """`department.company_id` chỉ là pháp nhân CHÍNH.

    `tab_department_company` cho một phòng phục vụ nhiều pháp nhân, nhưng bậc
    `company` KHÔNG đọc bảng đó — cố ý, vì nới nó ra là mở danh mục phòng ban
    xuyên pháp nhân cho mọi người.
    """
    from app.modules.department.model import Department, DepartmentCompany

    db = world.db
    db.add(DepartmentCompany(department_id=world.dept["B.hc"],
                             company_id=world.co["A"], is_active=True))
    db.commit()

    a1 = world.grant("a1", "department", scope="company")
    assert a1.sees(Department, "department") == {world.dept["A.kt"], world.dept["A.mua"]}, (
        "bảng phục vụ nhiều pháp nhân KHÔNG nới bậc company")


def test_c4b_hai_o_phong_ban_cam_han_tren_chinh_danh_muc_phong_ban(world):
    """🟡 Ghi chú của `SCOPE_FIELDS` bảo *«ai cần thấy phòng của mọi pháp nhân
    mình phục vụ thì dùng phần chọn đích danh (`_dept_include_cond`)»* — nhưng
    đường đó KHÔNG chạy trên chính entity `department`.

    ```python
    "department": {"company": "company_id", "owner": "created_by"},   # scoping.py:77
    ```

    Không có `dept_id` lẫn `dept_name`, mà `_dept_include_cond` và
    `_dept_match` đều đọc đúng hai khóa ấy. Nên cả ô «Phòng ban được xem» (cộng
    thêm) lẫn ô «Loại trừ phòng ban» (thu hẹp) đều **câm** trên màn Danh mục
    phòng ban — người khai quyền tick, bấm Lưu, và không có gì đổi.

    Ghim HÀNH VI HIỆN TẠI, và ghi lại rằng lời khuyên trong ghi chú của
    `scoping.py:74-76` hiện không thực hiện được.

    # QUYẾT ĐỊNH CHỜ: `SCOPE_FIELDS["department"]` có nên khai `dept_id: "id"`
    # (chiều của chính nó, cùng lẽ với `company: "id"` của pháp nhân)? Làm vậy
    # thì hai ô phòng ban chạy đúng như ghi chú hứa; không làm thì phải sửa
    # ghi chú, vì nó đang chỉ người đọc sang một đường không tồn tại.
    """
    from app.modules.department.model import Department

    a1 = world.grant("a1", "department", scope="company", inc_dept=["B.hc"])
    assert a1.sees(Department, "department") == {world.dept["A.kt"], world.dept["A.mua"]}, (
        "ô «Phòng ban được xem» không cộng thêm được gì")

    a2 = world.grant("a2", "department", scope="company", exc_dept=["A.kt"])
    assert a2.sees(Department, "department") == {world.dept["A.kt"], world.dept["A.mua"]}, (
        "ô «Loại trừ phòng ban» cũng không cắt được gì")


def test_c5_sua_ho_so_nhan_su_ngoai_pham_vi_qua_cua_phong_ban_bi_chan(world):
    """Cửa `PUT /employees/{id}/departments` đi qua `_employee_in_scope` trước.

    Đây là vế ĐÚNG, dựng để ca C6 bên dưới có chỗ đối chiếu: cùng một màn hình,
    một cửa xét phạm vi và một cửa không.
    """
    from app.modules.employee import controller as employee_controller

    a1 = world.grant("a1", "employee", scope="own", actions=("read", "write"))

    with pytest.raises(HTTPException) as err:
        employee_controller.set_employee_departments(
            world.emp["b1"], employee_controller.ExtraDepartmentsIn(extra_department_ids=[]),
            world.db, a1.user)
    assert err.value.status_code == 404


def test_c6_sua_ho_so_nhan_su_ngoai_pham_vi_qua_cua_PATCH_KHONG_bi_chan(world):
    """🔴 LỖ THẬT — `employee/controller.py:188-204`.

    ```python
    if data.department_id is not None:          # dòng 198
        profile = get_perm_profile(db, user)
        department_service.block_edit_own_department(db, eid, user)
        department_service.block_out_of_scope_departments(db, [data.department_id], user, profile)

    obj = service.update_employee(db, eid, data, user.id)   # dòng 203
    ```

    Chỉ nhánh `department_id` được gác. Không gửi ô đó thì `update_employee` đi
    thẳng vào `service.get_employee` = `db.get(Employee, eid)` — **không xét
    phạm vi một lần nào**. Người có `employee.write` phạm vi *của mình* sửa
    được họ tên, email, trạng thái và `is_active` của bất kỳ ai trong hệ, kể cả
    pháp nhân khác.

    Đối chiếu: cửa kiêm nhiệm ngay bên cạnh (`set_employee_departments`, ca C5)
    gọi `_employee_in_scope` trước. Hai cửa cùng một màn hình, hai luật khác nhau.

    Ghim HÀNH VI HIỆN TẠI để bản vá làm ca này đỏ lên có chủ đích.

    # QUYẾT ĐỊNH CHỜ: `PATCH /employees/{eid}` có nên gọi `_employee_in_scope(
    # db, eid, user, profile, "write")` ở đầu hàm, không phụ thuộc vào việc lần
    # lưu này có đụng `department_id` hay không?
    """
    from app.modules.employee import controller as employee_controller
    from app.modules.employee.model import Employee
    from app.modules.employee.schema import EmployeeUpdate

    a1 = world.grant("a1", "employee", scope="own", actions=("read", "write"))
    assert a1.sees(Employee, "employee") == {world.emp["a1"]}, "phạm vi đúng là hẹp"

    employee_controller.update_employee(world.emp["b1"],
                                        EmployeeUpdate(full_name="Bị sửa trộm"),
                                        world.db, a1.user)

    assert world.db.get(Employee, world.emp["b1"]).full_name == "Bị sửa trộm"


def test_c7_doi_phap_nhan_cua_CHINH_MINH_khong_qua_chot_nao(world, leave_ids):
    """🔴 LỖ THẬT, và là đường LEO THANG — cùng gốc C6.

    L1 (`block_edit_own_department`) chỉ chạy trong nhánh `department_id`. Mà
    `EmployeeUpdate` còn có ô `company_id`, và `get_perm_profile` lấy
    `company_id` **thẳng từ `tab_employee`** (`core/auth.py:191`). Nên:

        PATCH /api/employees/<hồ sơ của chính tôi>  {"company_id": <pháp nhân khác>}

    là tự dời mình sang pháp nhân khác, và mọi phạm vi bậc `company` chạy theo.
    Không cần đụng màn Phân quyền, không cần ai duyệt. Chốt L1 sinh ra đúng để
    chặn cảnh này ở chiều PHÒNG BAN, nhưng chiều PHÁP NHÂN thì bỏ ngỏ — mà
    pháp nhân là chiều rộng hơn.

    Nhịp duy nhất còn cản là `_PERM_CACHE` 60 giây (`update_employee` không gọi
    `perm_cache_clear`), tức là chậm chứ không phải chặn.

    Ghim HÀNH VI HIỆN TẠI.

    # QUYẾT ĐỊNH CHỜ: `block_edit_own_department` nên đổi thành «không tự sửa
    # PHẠM VI của chính mình» và chạy khi lần lưu đụng `department_id` HOẶC
    # `company_id`? Kèm `perm_cache_clear` cho hồ sơ vừa đổi pháp nhân.
    """
    from app.core.auth import perm_cache_clear
    from app.modules.employee import controller as employee_controller
    from app.modules.employee.schema import EmployeeUpdate
    from app.modules.leave.request_model import LeaveRequest

    a1 = world.grant("a1", "employee", scope="own", actions=("read", "write"))
    a1.grant("leave_request", scope="company")
    assert a1.sees(LeaveRequest, "leave_request") == pick(
        leave_ids, "a1_nghi", "a1_lap_ho", "a2_tu_nop", "khuyet_nhan_su")

    #  Tự dời mình sang pháp nhân B — không ô nào bị chặn.
    employee_controller.update_employee(world.emp["a1"],
                                        EmployeeUpdate(company_id=world.co["B"]),
                                        world.db, a1.user)
    perm_cache_clear(a1.user.id)   # thay cho 60 giây cache tự hết hạn

    assert a1.sees(LeaveRequest, "leave_request") == pick(leave_ids, "b1_tu_nop"), (
        "phạm vi đã chạy theo pháp nhân mới — tự đổi được tầm nhìn dữ liệu")


def test_c8_dat_mat_khau_qua_cua_nhan_su_phai_theo_pham_vi(world):
    """Bài giữ của lỗ nặng nhất cụm — **đã vá 05/09/2026**.

    Trước bản vá, `POST /employees/{eid}/set-password` chỉ có
    `require("employee", "write")`: kiểm **có quyền hay không**, không kiểm
    **trên ai**. Cửa song sinh `POST /users/{id}/reset-password`
    (`user/controller.py:69-76`) thì có `_block_out_of_scope`. Nghĩa là chốt của
    màn Tài khoản đi vòng được qua màn Nhân sự — ai có `employee.write` phạm vi
    *own*, phạm vi hẹp nhất tồn tại, đặt lại mật khẩu tài khoản quản trị rồi
    đăng nhập bằng chính nó.

    Đó là **chiếm tài khoản**, không phải rò dữ liệu, nên CR-158 và ba chốt của
    CR-167 đều không đụng tới: chúng canh việc tự nâng quyền cho **chính mình**,
    còn đây không có dòng phân quyền nào thay đổi.

    Bài này khẳng định cả hai chiều — chặn người ngoài phạm vi, và **không**
    chặn nhầm người trong phạm vi. Thiếu vế sau thì bản vá "an toàn" bằng cách
    khóa sạch cũng xanh.
    """
    from fastapi import HTTPException

    from app.modules.employee import controller as employee_controller
    from app.modules.user.model import User

    a1 = world.grant("a1", "employee", scope="own", actions=("read", "write"))
    nan_nhan = world.actor("b1").user
    mat_khau_cu = nan_nhan.password_hash

    with pytest.raises(HTTPException) as loi:
        employee_controller.set_password(world.emp["b1"],
                                         employee_controller.SetPasswordIn(password="doi-trom"),
                                         world.db, a1.user)
    assert loi.value.status_code == 404, "người ngoài phạm vi phải 404 như id không tồn tại"
    assert world.db.get(User, nan_nhan.id).password_hash == mat_khau_cu

    #  Vế đối chứng: phạm vi `own` vẫn đặt được mật khẩu của CHÍNH MÌNH.
    cua_minh = a1.user.password_hash
    employee_controller.set_password(world.emp["a1"],
                                     employee_controller.SetPasswordIn(password="cua-toi"),
                                     world.db, a1.user)
    assert world.db.get(User, a1.user.id).password_hash != cua_minh


def test_c8b_hanh_chinh_pham_vi_phap_nhan_van_dat_duoc_mat_khau_trong_cong_ty(world):
    """Bản vá không được cắt việc thật: hành chính phạm vi *công ty* vẫn làm được.

    Đây là vế dễ bỏ quên nhất khi siết một cổng. Đặt lại mật khẩu hộ người cùng
    pháp nhân là việc hằng ngày của hành chính — chặn nhầm thì bản vá bị gỡ ra
    ngay tuần sau, và lỗ quay lại nguyên vẹn.
    """
    from app.modules.employee import controller as employee_controller
    from app.modules.user.model import User

    hanh_chinh = world.grant("a1", "employee", scope="company", actions=("read", "write"))
    dong_nghiep = world.actor("a2").user   # cùng pháp nhân A, khác phòng thì cũng vậy
    mat_khau_cu = dong_nghiep.password_hash

    employee_controller.set_password(world.emp["a2"],
                                     employee_controller.SetPasswordIn(password="ho-tro"),
                                     world.db, hanh_chinh.user)
    assert world.db.get(User, dong_nghiep.id).password_hash != mat_khau_cu

    #  …nhưng vẫn không với sang pháp nhân B.
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as loi:
        employee_controller.set_password(world.emp["b1"],
                                         employee_controller.SetPasswordIn(password="khong-duoc"),
                                         world.db, hanh_chinh.user)
    assert loi.value.status_code == 404


def test_c9_xem_ho_so_nhan_su_theo_id_bo_qua_pham_vi(world):
    """🔴 LỖ THẬT — `employee/controller.py:36-38`.

    ```python
    @router.get("/{eid}")
    def get_employee(eid: int, db=..., user=Depends(require("employee", "read"))):
        return success(EmployeeDetailOut.model_validate(service.get_employee(db, eid)).model_dump())
    ```

    `service.get_employee` là `db.get` trần. Danh sách nhân sự lọc đúng phạm vi
    (dòng 27) và bản xuất CSV cũng đã vá (dòng 297), nhưng đường lấy MỘT hồ sơ
    thì không — gõ id lên URL là đọc trọn hồ sơ người ngoài phạm vi. Chính
    `_employee_in_scope` ngay bên dưới (dòng 207-225) đã ghi nhận điều này
    trong docstring của nó, và vẫn chưa ai gắn vào cửa `GET`.

    Ghim HÀNH VI HIỆN TẠI.

    # QUYẾT ĐỊNH CHỜ: `GET /api/employees/{eid}` có nên đi qua
    # `_employee_in_scope(..., "read")`? Rủi ro cần đo trước: nhiều màn đang gọi
    # nó để hiện TÊN người trên chứng từ ngoài phạm vi — bịt thô là các màn đó
    # hiện «Không tìm thấy nhân viên» thay cho một cái tên.
    """
    from app.modules.employee import controller as employee_controller
    import json

    a1 = world.grant("a1", "employee", scope="own")
    ket_qua = json.loads(employee_controller.get_employee(world.emp["b1"], world.db,
                                                          a1.user).body)

    assert ket_qua["data"]["id"] == world.emp["b1"]
    assert ket_qua["data"]["full_name"] == "Nhân sự b1"


def test_c10_doi_phong_ban_thi_pham_vi_doi_theo_NGAY_khong_doi_60_giay(world, leave_ids):
    """`set_departments` gọi `perm_cache_clear` cho mọi tài khoản của nhân sự đó.

    Thiếu dòng đó thì Nhân sự chuyển người sang phòng khác, người đó F5 vẫn
    nhìn bằng tầm cũ suốt một phút — và cách «sửa» tự nhiên nhất lúc ấy là đi
    cấp thêm quyền cho rộng ra.

    Ca này hâm nóng cache TRƯỚC khi đổi, nếu không thì cache rỗng và bài kiểm
    xanh dù có xóa hay không.
    """
    from app.modules.employee.department_service import set_departments
    from app.modules.employee.model import Employee
    from app.modules.leave.request_model import LeaveRequest

    a1 = world.grant("a1", "leave_request", scope="dept")
    assert a1.sees(LeaveRequest, "leave_request") == pick(
        leave_ids, "a1_nghi", "a1_lap_ho", "a2_tu_nop")   # hâm nóng cache

    set_departments(world.db, world.db.get(Employee, world.emp["a1"]),
                    [world.dept["A.mua"]], actor=1)
    world.db.commit()

    assert a1.sees(LeaveRequest, "leave_request") == pick(leave_ids, "khuyet_nhan_su")


def test_c11_kiem_nhiem_mo_pham_vi_du_ca_hai_phong(world, leave_ids):
    """Bậc `dept` đọc `dept_ids` (danh sách), không đọc `dept_id` (một số).

    Đó là cả lý do CR-167 tồn tại: trưởng bộ phận phụ trách hai phòng phải thấy
    phiếu của cả hai. Lùi về một phòng thì họ mất sạch phiếu phòng thứ hai mà
    không có thông báo nào.
    """
    from app.modules.leave.request_model import LeaveRequest

    a1 = world.grant("a1", "leave_request", scope="dept")
    a1.add_department("A.mua")

    assert a1.sees(LeaveRequest, "leave_request") == pick(
        leave_ids, "a1_nghi", "a1_lap_ho", "a2_tu_nop", "khuyet_nhan_su")


# ══════════════════════════════════════════════════════════════════════════════
#  D. BA CHỐT GÁN PHÒNG BAN (L1/L2/L3) + tự nới phạm vi
#
#  Đây là nhóm quan trọng nhất của cụm. `test_kiem_nhiem_phong_ban.py` đã kiểm
#  ba chốt ở mức *service* với hồ sơ quyền GIẢ; ở đây gọi qua CONTROLLER với
#  grant thật, tức đúng đường mà một người ngồi trước màn hình đi qua.
# ══════════════════════════════════════════════════════════════════════════════

def set_extra_departments_via_api(world, actor, employee_id: int, dept_keys):
    from app.modules.employee import controller as employee_controller

    ids = [world.dept[k] if isinstance(k, str) else k for k in dept_keys]
    return employee_controller.set_employee_departments(
        employee_id, employee_controller.ExtraDepartmentsIn(extra_department_ids=ids),
        world.db, actor.user)


def test_d1_L1_khong_tu_them_phong_cho_chinh_minh(world):
    """L1 — vai trò `employee.write` phạm vi *own* là CÓ THẬT (tự sửa hồ sơ mình).

    Không có chốt này thì tự thêm một phòng cho mình là xong: phạm vi dữ liệu
    bậc *phòng ban* đọc thẳng `tab_employee_department`, nên đó đúng bằng tick
    thêm một ô trong ma trận quyền, chỉ là qua một cửa trông hiền lành hơn.

    So theo `user.employee_id` chứ không theo `user.id` — cùng một con người,
    hai định danh ở hai bảng. Nhầm hai cái đó thì chốt không bao giờ nổ.
    """
    a1 = world.grant("a1", "employee", scope="all", actions=("read", "write"))

    with pytest.raises(HTTPException) as err:
        set_extra_departments_via_api(world, a1, world.emp["a1"], ["A.mua"])
    assert err.value.status_code == 403
    assert "chính mình" in err.value.detail


def test_d1b_L1_chi_chan_dung_chieu_tu_minh(world):
    """CẶP ĐỐI CHỨNG. Chặn cả chiều gán cho người khác là hỏng nghiệp vụ hằng
    ngày của phòng Nhân sự — và người ta sẽ đi cấp phạm vi *tất cả* để gỡ."""
    from app.modules.employee.department_service import departments_of

    a1 = world.grant("a1", "employee", scope="all", actions=("read", "write"))
    set_extra_departments_via_api(world, a1, world.emp["a2"], ["A.mua"])

    assert set(departments_of(world.db, world.emp["a2"])) == {world.dept["A.kt"],
                                                              world.dept["A.mua"]}


def test_d2_L2_khong_gan_duoc_phong_minh_khong_nhin_thay(world):
    """L2 — người quản lý phạm vi *phòng ban* không được dựng ra một người có
    tầm nhìn rộng hơn mình rồi nhờ người đó xem hộ.

    ⚠️ Thước đo là phạm vi trên entity **`employee`** (thứ đang bị ghi), KHÔNG
    phải trên `department`: `SCOPE_FIELDS["department"]` nói về quyền quản lý
    DANH MỤC phòng ban và không có chiều phòng ban, nên lấy nó làm thước thì
    người quản lý nhân sự phòng Kế toán không gán nổi chính phòng Kế toán.
    """
    a1 = world.grant("a1", "employee", scope="dept", actions=("read", "write"))

    with pytest.raises(HTTPException) as err:
        set_extra_departments_via_api(world, a1, world.emp["a2"], ["A.mua"])
    assert err.value.status_code == 403
    assert "Phòng Thu mua" in err.value.detail, "câu lỗi phải kể tên phòng bị vướng"


def test_d2b_L2_van_gan_duoc_dung_phong_cua_chinh_minh(world):
    """CẶP ĐỐI CHỨNG của L2 — chặn nhầm ca này là chốt vô dụng ngay ngày đầu."""
    from app.modules.employee.department_service import departments_of

    a1 = world.grant("a1", "employee", scope="dept", actions=("read", "write"))
    a1.add_department("A.mua")   # nay a1 có chân ở cả hai phòng

    set_extra_departments_via_api(world, a1, world.emp["a2"], ["A.mua"])
    assert set(departments_of(world.db, world.emp["a2"])) == {world.dept["A.kt"],
                                                              world.dept["A.mua"]}


def test_d2c_L2_tinh_ca_phong_duoc_cap_them_dich_danh_o_man_phan_quyen(world):
    """Ô «Phòng ban được xem» cấp thêm phòng cho một tài khoản — phải tính vào tầm.

    Bỏ sót thì quản trị cấp thêm phòng cho một người, người đó vẫn không gán
    được ai vào phòng ấy, và không có câu lỗi nào giải thích vì sao.
    """
    from app.modules.employee.department_service import departments_of

    a1 = world.grant("a1", "employee", scope="dept", actions=("read", "write"),
                     inc_dept=["A.mua"])

    set_extra_departments_via_api(world, a1, world.emp["a2"], ["A.mua"])
    assert world.dept["A.mua"] in departments_of(world.db, world.emp["a2"])


def test_d3_L3_phong_khong_ton_tai_va_phong_khac_phap_nhan_deu_bi_chan(world):
    """L3 — `tab_employee` và `tab_department` không có khóa ngoại.

    Id rác ghi vào được và nằm im ở đó (không hiện trên giao diện, nhưng mọi
    phép đếm theo phòng vẫn đếm nó). Gán sang phòng của pháp nhân khác thì tệ
    hơn: mở dữ liệu xuyên pháp nhân bằng đúng một dòng.
    """
    a1 = world.grant("a1", "employee", scope="all", actions=("read", "write"))

    with pytest.raises(HTTPException) as err:
        set_extra_departments_via_api(world, a1, world.emp["a2"], [999999])
    assert err.value.status_code == 400
    assert "không tồn tại" in err.value.detail

    with pytest.raises(HTTPException) as err:
        set_extra_departments_via_api(world, a1, world.emp["a2"], ["B.hc"])
    assert err.value.status_code == 400
    assert "pháp nhân khác" in err.value.detail


def test_d3b_L3_chan_TRUOC_khi_ghi_khong_de_lai_nua_vien(world):
    """`set_departments` XÓA SẠCH rồi ghi lại — kiểm sau khi xóa là mất dữ liệu.

    `_check_departments_exist` chạy ở đầu hàm, trước câu `DELETE`. Đảo thứ tự
    đó thì một lần bấm hỏng là nhân sự đó rơi khỏi mọi phòng, mất luôn phạm vi
    dữ liệu, và không có gì nói cho ai biết.
    """
    from app.modules.employee.department_service import departments_of

    a1 = world.grant("a1", "employee", scope="all", actions=("read", "write"))
    set_extra_departments_via_api(world, a1, world.emp["a2"], ["A.mua"])
    truoc = set(departments_of(world.db, world.emp["a2"]))
    assert truoc == {world.dept["A.kt"], world.dept["A.mua"]}

    with pytest.raises(HTTPException):
        set_extra_departments_via_api(world, a1, world.emp["a2"], ["A.mua", 999999])

    world.db.rollback()
    assert set(departments_of(world.db, world.emp["a2"])) == truoc


def test_d4_khong_tu_noi_pham_vi_du_lieu_cua_chinh_minh(world, leave_ids):
    """Kế hoạch cụm 06 đánh dấu ca này 🔴 «chưa có chốt» — ĐỌC MÃ THÌ ĐÃ CÓ.

    `user/controller.py:140-147` gọi `privilege_escalation.block_edit_own_permissions(
    user_id, user)` ngay sau `_block_out_of_scope`, kèm ghi chú «Phạm vi dữ
    liệu cũng là quyền: tự đặt cho mình `all` là thấy toàn bộ hệ». Ca này chốt
    lại để không ai gỡ nhầm dòng đó khi dọn mã.
    """
    from app.modules.user import controller as user_controller
    from app.modules.user.schema import ScopeUpdate

    a1 = world.grant("a1", "user", scope="own", actions=("read", "write"))
    a1.grant("leave_request", scope="company")

    with pytest.raises(HTTPException) as err:
        user_controller.set_scope(a1.user.id, a1.roles[1].id,
                                  ScopeUpdate(companies=[world.co["B"]]),
                                  world.db, a1.user)
    assert err.value.status_code == 403
    assert "chính mình" in err.value.detail


def test_d5_khong_tu_gan_them_vai_tro_cho_chinh_minh_qua_man_nhan_su(world):
    """Cửa vòng: màn Nhân sự tự tạo tài khoản khi nhân sự chưa có
    (`set_password` → `provision_user`), nên phải kiểm nó KHÔNG cấp quyền gì thêm.

    `provision_user(role_ids=[])` chỉ gán vai trò mặc định «Nhân sự». Nếu ngày
    nào đó ai đó truyền `role_ids` từ hồ sơ nhân sự vào đây thì đó là một cửa
    gán vai trò KHÔNG đi qua `block_role_escalation` — ca này canh chỗ đó.
    """
    from app.modules.employee import controller as employee_controller
    from app.modules.employee.model import Employee
    from app.modules.role.model import Permission
    from app.modules.user.model import User, UserRole

    db = world.db
    khongtk = db.get(Employee, world.emp["khongtk"])
    khongtk.email = "khongtk@dego.vn"
    db.commit()

    a1 = world.grant("a1", "employee", scope="all", actions=("read", "write"))
    employee_controller.set_password(khongtk.id,
                                     employee_controller.SetPasswordIn(password="1234"),
                                     db, a1.user)

    tai_khoan_moi = db.query(User).filter(User.employee_id == khongtk.id).first()
    assert tai_khoan_moi is not None
    role_ids = [r.role_id for r in db.query(UserRole)
                .filter(UserRole.user_id == tai_khoan_moi.id).all()]
    cap_quyen = {(p.entity, a) for p in db.query(Permission)
                 .filter(Permission.role_id.in_(role_ids or [0])).all()
                 for a in ("write", "delete", "approve")
                 if getattr(p, f"can_{a}", False)}
    assert cap_quyen == set(), "tài khoản tự tạo không được có quyền ghi nào"
