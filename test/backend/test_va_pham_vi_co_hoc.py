"""Năm lỗ CƠ HỌC của trục phạm vi dữ liệu — #34 · #21 · #28 · #40 · #41.

Gọi là "cơ học" vì không lỗ nào là câu hỏi chính sách: mỗi cái đều là một dòng
mã nghĩ ngược với dòng mã bên cạnh nó, và bản vá chỉ là làm cho hai dòng nghĩ
giống nhau. Xếp hạng gốc ở
`plans/260905-0931-stress-test-pham-vi-phan-quyen/reports/00-tong-hop-xep-hang.md`.

| # | Hỏng thế nào trước bản vá |
|---|---|
| 34 | `_explicit_cond` gọi `int(v)` trần → một dòng `tab_user_scope` rác làm **500 mọi màn danh sách** của riêng người đó |
| 21 | nhánh `self` đơn độc thiếu chốt `rid` → tài khoản chưa gắn nhân sự thấy **mọi** tài khoản chưa gắn nhân sự |
| 28 | đổi `company_id` của nhân sự không xóa cache quyền → thu hồi tầm nhìn **chậm 60 giây** |
| 40 | `vehicle_booking` thiếu ở `ENTITY_LABELS`/`ENTITY_LINKS` → thư ghi "Phiếu XE009", `link` **rỗng** |
| 41 | `set_line_status_` định nghĩa **hai lần** → thuộc tính module bị đè, ai `import` lấy nhầm bản |

Ca #21 chính (entity `user`) sửa tại chỗ trong
`test_pham_vi_cap_bac_ma_tran.py::test_own_tren_entity_chi_khai_self_chan_nguoi_chua_gan_nhan_su`;
ở đây chỉ thêm entity thứ hai dính cùng nhánh — `leave_balance`.

Mỗi bản vá kiểm **hai chiều**: chặn/đổi đúng ca hỏng, VÀ không làm hỏng ca hợp
lệ ngay bên cạnh. Chỉ kiểm một chiều thì `return false()` vô điều kiện cũng xanh.
"""
from __future__ import annotations

import logging
from types import SimpleNamespace

import pytest

from scope_factory import Actor


# ══════════════════════════════════════════════════════════════════════════════
#  #34 — `int(v)` trần trong `_explicit_cond`
# ══════════════════════════════════════════════════════════════════════════════
#
#  `auth.py:151` CỐ Ý giữ nguyên chuỗi khi giá trị `dim=company` không phải số:
#      int(s.value) if (s.value or "").isdigit() else s.value
#  rồi `scoping._explicit_cond` lại gọi `int(v)` trần trên đúng danh sách đó.
#  Hai dòng mã nghĩ ngược nhau, và bên thua là người dùng: `ValueError` bay lên
#  tận controller ⇒ 500 ở MỌI màn danh sách của riêng họ. Không tự gỡ được, vì
#  màn Phân quyền cũng là một màn danh sách.

def _mot_pyc_moi_cong_ty(world) -> dict[str, int]:
    """Hai YCMH, mỗi pháp nhân một phiếu — đủ để phân biệt lọc đúng / chặn hết."""
    from app.modules.purchase_request.model import PurchaseRequest

    rows = {
        key: PurchaseRequest(code=f"PR-{key}", company_id=world.co[key],
                             status="approved", created_by=world.user_id("b1"),
                             requester_id=world.emp["b1"])
        for key in ("A", "B")
    }
    world.db.add_all(rows.values())
    world.db.flush()
    return {k: v.id for k, v in rows.items()}


def test_34_o_chon_cong_ty_toan_rac_khong_con_no_500_va_chan_lai(db, world, caplog):
    """Dòng `dim=company` giá trị KHÔNG PHẢI SỐ: không nổ nữa, và chặn chứ không nới.

    Chặn chứ không bỏ qua: ô «Công ty được xem» là ô THU HẸP. Bỏ qua nó thì phạm
    vi nở ra đúng bằng bậc vai trò — người khai quyền tick vào một công ty rồi
    nhận về nhiều hơn lúc chưa tick, đúng loại lỗ mà B-07 sinh ra để chặn.
    """
    from app.modules.purchase_request.model import PurchaseRequest

    _mot_pyc_moi_cong_ty(world)
    a1 = world.actor("a1")
    a1.grant("purchase_request", scope="all")
    a1.add_scope_row(a1.roles[-1], "company", "CTY_A")   # rác: tên mã, không phải id

    caplog.clear()
    with caplog.at_level(logging.WARNING, logger="app.scoping"):
        thay = a1.sees(PurchaseRequest)      # trước bản vá: ValueError → 500

    assert thay == set(), "ô chọn không dựng nổi điều kiện thì phải chặn, không được nới"
    assert [r for r in caplog.records if r.name == "app.scoping"], (
        "bỏ qua dữ liệu rác mà KHÔNG ghi log thì không có cách nào đi tìm dòng hỏng")


def test_34_o_chon_lan_lon_so_va_rac_van_loc_dung_phan_dung_duoc(db, world):
    """CHIỀU NGƯỢC LẠI — giá trị hợp lệ trong cùng ô vẫn ăn nguyên.

    Ca hay gặp nhất ở dữ liệu thật: một dòng cũ còn ghi tên, những dòng sau đã
    ghi id. Vá kiểu "gặp rác thì chặn cả ô" là cắt luôn quyền hợp lệ của họ.
    """
    from app.modules.purchase_request.model import PurchaseRequest

    ids = _mot_pyc_moi_cong_ty(world)
    a1 = world.actor("a1")
    a1.grant("purchase_request", scope="all", inc_company=["A"])
    a1.add_scope_row(a1.roles[-1], "company", "khong-phai-so")

    assert a1.sees(PurchaseRequest) == {ids["A"]}


def test_34_rac_o_o_loai_tru_bi_bo_qua_chu_khong_chan(db, world):
    """Ô LOẠI TRỪ toàn rác thì BỎ QUA — khác hẳn ô chọn, và cố ý khác.

    Cột `company_id` là số; một chuỗi rác không bao giờ khớp dòng nào, nên giữ
    hay bỏ điều kiện loại trừ ấy đều không loại được phiếu nào. Chặn ở đây là
    dựng ra một hạn chế mà người khai quyền chưa từng gõ.
    """
    from app.modules.purchase_request.model import PurchaseRequest

    ids = _mot_pyc_moi_cong_ty(world)
    a1 = world.actor("a1")
    a1.grant("purchase_request", scope="all")
    a1.add_scope_row(a1.roles[-1], "company", "rac-hoan-toan", is_exclude=True)

    assert a1.sees(PurchaseRequest) == set(ids.values())


def test_34_loai_tru_lan_lon_so_va_rac_van_loai_dung_cong_ty_so(db, world):
    """CHIỀU NGƯỢC LẠI của ca trên — phần loại trừ hợp lệ vẫn phải cắt."""
    from app.modules.purchase_request.model import PurchaseRequest

    ids = _mot_pyc_moi_cong_ty(world)
    a1 = world.actor("a1")
    a1.grant("purchase_request", scope="all", exc_company=["B"])
    a1.add_scope_row(a1.roles[-1], "company", "rac", is_exclude=True)

    assert a1.sees(PurchaseRequest) == {ids["A"]}


# ══════════════════════════════════════════════════════════════════════════════
#  #21 — nhánh `self` đơn độc, entity thứ hai: `leave_balance`
# ══════════════════════════════════════════════════════════════════════════════

def _tai_khoan_khong_ho_so(world, key: str) -> Actor:
    """Tài khoản chưa gắn hồ sơ nhân sự — `employee_id = 0`. Có thật trên hệ chạy."""
    from app.core.auth import perm_cache_clear
    from app.modules.user.model import User

    user = User(email=key, employee_id=0, password_hash="x", is_active=True)
    world.db.add(user)
    world.db.flush()
    actor = Actor(world, key, user, None)
    world._actors[key] = actor
    perm_cache_clear(user.id)
    return actor


def _quy_phep(world) -> dict[str, int]:
    """Quỹ phép của a1 và a2 — hai người khác nhau, cùng pháp nhân A."""
    from app.modules.leave.balance_model import LeaveBalance

    rows = {
        key: LeaveBalance(employee_id=world.emp[key], company_id=world.co["A"],
                          year=2026, leave_type_id=1, allocated_days=12.0)
        for key in ("a1", "a2")
    }
    world.db.add_all(rows.values())
    world.db.flush()
    return {k: v.id for k, v in rows.items()}


def test_21_quy_phep_own_chan_tai_khoan_chua_gan_ho_so_nhan_su(db, world, caplog):
    """`leave_balance` khai MỖI `self`, nên dính đúng nhánh của #21.

    Trước bản vá điều kiện là `LeaveBalance.employee_id == 0` — không trúng dòng
    nào ở thế giới mẫu này, nhưng trúng SẠCH mọi dòng quỹ chưa gắn nhân sự trên
    hệ thật, mà quỹ phép là chỗ *"ai được nghỉ bao nhiêu ngày"*. Nay chặn thẳng,
    kèm log.
    """
    from app.modules.leave.balance_model import LeaveBalance

    _quy_phep(world)
    khong_ho_so = _tai_khoan_khong_ho_so(world, "hethongqp")
    khong_ho_so.grant("leave_balance", scope="own")
    assert khong_ho_so.profile()["employee_id"] == 0

    caplog.clear()
    with caplog.at_level(logging.WARNING, logger="app.scoping"):
        thay = khong_ho_so.sees(LeaveBalance)

    assert thay == set()
    assert [r for r in caplog.records if r.name == "app.scoping"]


def test_21_quy_phep_own_van_cho_nguoi_da_gan_ho_so_thay_quy_cua_minh(db, world):
    """CHIỀU NGƯỢC LẠI — người đã gắn hồ sơ thấy ĐÚNG quỹ của mình, không hơn không kém."""
    from app.modules.leave.balance_model import LeaveBalance

    ids = _quy_phep(world)
    a1 = world.actor("a1")
    a1.grant("leave_balance", scope="own")

    assert a1.sees(LeaveBalance) == {ids["a1"]}


# ══════════════════════════════════════════════════════════════════════════════
#  #28 — đổi pháp nhân của nhân sự phải XÓA CACHE QUYỀN
# ══════════════════════════════════════════════════════════════════════════════
#
#  `get_perm_profile` giữ `company_id`/`dept_id` trong `_PERM_CACHE` 60 giây, mà
#  hai giá trị đó CHÍNH là phạm vi dữ liệu. Cửa «đổi phòng ban» xóa cache từ
#  CR-167 (`department_service.set_departments`), cửa «đổi công ty» ngay cạnh nó
#  trên cùng một màn thì quên — thu hồi tầm nhìn chậm trọn một phút.

def _lam_nong_cache(db, actor: Actor) -> None:
    from app.core.auth import _PERM_CACHE, get_perm_profile

    get_perm_profile(db, actor.user)
    assert actor.user.id in _PERM_CACHE, "ca này vô nghĩa nếu cache không được nạp"


def test_28_doi_phap_nhan_cua_nhan_su_xoa_cache_quyen(db, world):
    """Đổi `company_id` ⇒ hồ sơ quyền cache phải biến mất NGAY, không đợi 60 giây."""
    from app.core.auth import _PERM_CACHE
    from app.modules.employee import service as employee_service
    from app.modules.employee.schema import EmployeeUpdate

    a1 = world.actor("a1")
    _lam_nong_cache(db, a1)

    employee_service.update_employee(db, a1.employee.id,
                                     EmployeeUpdate(company_id=world.co["B"]), 1)

    assert a1.user.id not in _PERM_CACHE, (
        "đổi pháp nhân mà giữ cache = người này còn nhìn bằng tầm cũ tới 60 giây")
    assert a1.profile()["company_id"] == world.co["B"]


def test_28_doi_phong_ban_qua_man_ho_so_cung_xoa_cache_quyen(db, world):
    """Cửa `department_id` trên màn hồ sơ — cùng một nghĩa vụ, kiểm cho đủ cặp."""
    from app.core.auth import _PERM_CACHE
    from app.modules.employee import service as employee_service
    from app.modules.employee.schema import EmployeeUpdate

    a1 = world.actor("a1")
    _lam_nong_cache(db, a1)

    employee_service.update_employee(db, a1.employee.id,
                                     EmployeeUpdate(department_id=world.dept["A.mua"]), 1)

    assert a1.user.id not in _PERM_CACHE
    assert world.dept["A.mua"] in a1.profile()["dept_ids"]


def test_28_sua_o_khong_lien_quan_thi_khong_dong_toi_cache(db, world):
    """CHIỀU NGƯỢC LẠI — đổi số điện thoại KHÔNG đổi phạm vi, đừng xóa cache bừa.

    Xóa mọi lúc thì hàm vẫn "đúng", nhưng `_PERM_CACHE` sinh ra để chặn việc dựng
    lại hồ sơ quyền ở MỌI request; biến nó thành vô dụng là một cách hỏng khác.
    """
    from app.core.auth import _PERM_CACHE
    from app.modules.employee import service as employee_service
    from app.modules.employee.schema import EmployeeUpdate

    a1 = world.actor("a1")
    _lam_nong_cache(db, a1)

    employee_service.update_employee(db, a1.employee.id,
                                     EmployeeUpdate(phone="0900000001"), 1)

    assert a1.user.id in _PERM_CACHE


def test_28_nhan_su_chua_co_tai_khoan_doi_phap_nhan_khong_no(db, world):
    """Nhân sự KHÔNG có tài khoản đăng nhập — không có gì để xóa, và không được nổ.

    `emp["khongtk"]` là ca có thật (hồ sơ nhập trước khi cấp tài khoản). Vá kiểu
    `perm_cache_clear(user.id)` sau một `db.query(...).first()` là `None.id`.
    """
    from app.modules.employee import service as employee_service
    from app.modules.employee.schema import EmployeeUpdate

    emp = employee_service.update_employee(db, world.emp["khongtk"],
                                           EmployeeUpdate(company_id=world.co["B"]), 1)
    assert emp.company_id == world.co["B"]


# ══════════════════════════════════════════════════════════════════════════════
#  #40 — `vehicle_booking` thiếu nhãn + đường dẫn trong thư báo việc duyệt
# ══════════════════════════════════════════════════════════════════════════════
#
#  `vehicle_booking/approval_bridge.py` đăng ký ĐỦ hook (`register_hooks` +
#  `register_subject` + `register_reader`) nên phiếu đặt xe chạy qua bộ máy duyệt
#  bình thường — chỉ hai bảng tra trong `task_notification.py` là quên nó. Kết
#  quả: thư ghi «Phiếu XE009» (mất tên loại chứng từ) và `link` RỖNG (bấm vào
#  không đi đâu). `notify_new_tasks` nuốt lỗi có chủ ý nên không chỗ nào đỏ lên
#  — bài kiểm này là thứ duy nhất phát hiện ra.

MA_PHIEU_XE = "XE009"


@pytest.fixture()
def nguoi_duyet(db):
    from app.modules.employee.model import Employee
    from app.modules.user.model import User

    employee = Employee(code="DPX", full_name="Điều phối xe", company_id=1,
                        department_id=7, is_active=True)
    db.add(employee)
    db.flush()
    user = User(email="dpx@demo.com", password_hash="x",
                employee_id=employee.id, is_active=True)
    db.add(user)
    db.flush()
    return employee, user


def _bao_viec(db, entity: str, entity_id: int, employee_id: int):
    """Chạy `notify_new_tasks` trên một phiên duyệt dựng tay, trả thư vừa ghi.

    Phiên/việc để TRẠNG THÁI TẠM (không `add` vào session): `notify_new_tasks`
    chỉ đọc thuộc tính của chúng, nên khỏi phải dựng cả luồng duyệt thật chỉ để
    kiểm hai bảng tra chuỗi.
    """
    from app.modules.approval.instance_model import (TASK_PENDING,
                                                     ApprovalInstance,
                                                     ApprovalTask)
    from app.modules.approval.task_notification import notify_new_tasks
    from app.modules.notification.model import Notification

    instance = ApprovalInstance(entity=entity, entity_id=entity_id,
                                entity_code=MA_PHIEU_XE,
                                entity_title="Đi công tác Bình Dương",
                                flow_id=1, status=1, updated_by=1)
    task = ApprovalTask(instance_id=1, node_seq=1, node_name="Điều phối duyệt",
                        order_no=1, assignee_employee_id=employee_id,
                        status=TASK_PENDING, due_at=None)
    written = notify_new_tasks(db, instance, [task])
    db.flush()
    return written, db.query(Notification).order_by(Notification.id.desc()).first()


def test_40_thu_bao_dat_xe_co_ten_loai_chung_tu_va_link_mo_duoc(db, nguoi_duyet):
    """Thư của phiếu đặt xe phải nói ĐÂY LÀ GÌ và bấm được vào đâu."""
    employee, user = nguoi_duyet

    written, thu = _bao_viec(db, "vehicle_booking", 9, employee.id)

    assert written == 1
    assert thu.user_id == user.id
    assert "Phiếu đặt xe" in thu.body, (
        f"thiếu nhãn → thư mở đầu bằng «Phiếu {MA_PHIEU_XE}», người duyệt không "
        f"biết sắp mở cái gì. Nhận: {thu.body}")
    #  `/vehicle-booking` nằm trong `V2_PREFIXES` của `notification-link.ts` nên
    #  `toAppPath()` cho đi thẳng — link này mở đúng màn chi tiết phiếu đặt xe.
    assert thu.link == "/vehicle-booking/9", (
        "link rỗng/sai = bấm vào thông báo không đi đâu cả, mà lỗi thì bị nuốt")


def test_40_moi_entity_co_hook_duyet_deu_phai_co_nhan_va_duong_dan(db):
    """CHIỀU NGƯỢC LẠI — chốt cho mọi loại chứng từ, không riêng đặt xe.

    Đây mới là bài kiểm giữ được: thêm phân hệ thứ tám chạy qua bộ máy duyệt mà
    quên hai bảng tra thì đỏ ngay, thay vì đợi người dùng báo «bấm không đi đâu».
    Nguồn sự thật là danh sách hook đã đăng ký, không phải một danh sách chép tay.
    """
    import app.main  # noqa: F401 — nạp mọi module để các bridge kịp đăng ký hook
    from app.modules.approval import entity_hooks
    from app.modules.approval.task_notification import (ENTITY_LABELS,
                                                        ENTITY_LINKS)

    #  Đọc thẳng sổ đăng ký (`_HOOKS`) chứ không chép danh sách sang đây: chép là
    #  đẻ ra bản thứ hai phải bảo trì song song, đúng thứ bài kiểm này đi bắt.
    da_dang_ky = set(entity_hooks._HOOKS)
    assert "vehicle_booking" in da_dang_ky, "ca này mất nghĩa nếu bridge chưa đăng ký"

    thieu_nhan = sorted(da_dang_ky - set(ENTITY_LABELS))
    thieu_link = sorted(da_dang_ky - set(ENTITY_LINKS))
    assert not thieu_nhan, f"thiếu nhãn ⇒ thư ghi «Phiếu <mã>»: {thieu_nhan}"
    assert not thieu_link, f"thiếu đường dẫn ⇒ link rỗng, bấm không đi đâu: {thieu_link}"

    for entity, mau in ENTITY_LINKS.items():
        assert "{id}" in mau, f"{entity}: mẫu đường dẫn không có chỗ ghép id"


# ══════════════════════════════════════════════════════════════════════════════
#  #41 — `set_line_status_` định nghĩa hai lần trong `survey_request/controller.py`
# ══════════════════════════════════════════════════════════════════════════════

def test_41_hai_route_doi_trang_thai_dong_khong_con_trung_ten_ham():
    """Hai việc KHÁC NHAU nên phải mang hai tên khác nhau.

    `PATCH /{sid}/lines/{line_id}/status`      → cột `is_completed` (Tình trạng dòng)
    `PATCH /{sid}/lines/{line_id}/line-status` → cột `line_status`  (Trạng thái dòng)

    FastAPI đăng ký theo decorator nên cả hai route vẫn chạy đúng kể cả lúc trùng
    tên — đó chính là lý do lỗi này sống lâu. Cái hỏng nằm ở tầng module: bản
    định nghĩa SAU đè lên bản trước, nên `controller.set_line_status_` trỏ vào
    route `/line-status`, còn route `/status` thì không còn tên nào gọi tới.
    """
    from app.modules.survey_request import controller

    assert hasattr(controller, "set_line_completed_")
    assert hasattr(controller, "set_line_status_")
    assert controller.set_line_completed_ is not controller.set_line_status_

    duong_dan = {r.path: r.endpoint.__name__ for r in controller.router.routes
                 if getattr(r, "endpoint", None) is not None}
    #  CẢ HAI route phải còn đăng ký — bản vá là đổi tên, không phải xóa bớt.
    assert duong_dan["/api/survey-requests/{sid}/lines/{line_id}/status"] == \
        "set_line_completed_"
    assert duong_dan["/api/survey-requests/{sid}/lines/{line_id}/line-status"] == \
        "set_line_status_"


def test_41_khong_con_ten_ham_nao_bi_dinh_nghia_trung_trong_controller():
    """CHIỀU NGƯỢC LẠI — quét cả tệp, không chỉ một cặp đã biết.

    Đọc bằng `ast` chứ không bằng `dir(module)`: đúng cái hỏng ở đây là tên trùng
    BIẾN MẤT khỏi module sau khi bị đè, nên soi module thì không bao giờ thấy.
    """
    import ast
    import collections
    import pathlib

    from app.modules.survey_request import controller

    cay = ast.parse(pathlib.Path(controller.__file__).read_text(encoding="utf-8"))
    ten = collections.Counter(
        node.name for node in cay.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)))
    trung = sorted(k for k, n in ten.items() if n > 1)
    assert not trung, f"hàm cùng tên ở tầng module — bản sau đè bản trước: {trung}"
