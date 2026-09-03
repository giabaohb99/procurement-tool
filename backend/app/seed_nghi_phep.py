"""NẠP DỮ LIỆU NỀN CHO PHÂN HỆ NGHỈ PHÉP (CR-259, đợt P-07) — CHẠY LẠI ĐƯỢC.

    docker compose exec api python -m app.seed_nghi_phep

Nạp bốn thứ, mỗi thứ chỉ khi nó chưa có:
  1. 7 loại nghỉ, ĐÚNG bộ mã chuỗi mà giấy GNP đang dùng (`core/leave_codes.py`);
  2. bậc thâm niên của Phép năm — luật *5 năm +1 ngày*, khai bằng DỮ LIỆU;
  3. lịch ngày lễ 2026 theo Bộ luật Lao động;
  4. luồng duyệt cho `leave_request` + bật bộ máy duyệt cho nó.

⚠️ Cùng nguyên tắc với `seed_luong_nghi_phep`: **chỉ THÊM, không xóa, không ghi
đè**. Chạy trên môi trường thật thì mọi thứ người ta đã sửa tay ở màn danh mục
phải còn nguyên. Chạy mười lần cũng ra một bộ.

⚠️ **Không nằm trong `app/seed.py`** nên `start.sh` không tự chạy. Có chủ ý: nạp
7 loại nghỉ + luồng duyệt vào một môi trường chưa dùng phân hệ này là bày ra
danh mục rác. Chạy tay khi bật phân hệ.
"""
import json
from datetime import date

import app.core.all_models  # noqa: F401  — nạp đủ model để mapper cấu hình được
from app.core.database import SessionLocal
from app.modules.approval.flow_model import (APPROVER_DEPT_HEAD,
                                             APPROVER_DEPT_HEAD_OF, MULTI_ANY,
                                             NO_APPROVER_BLOCK,
                                             NO_APPROVER_FALLBACK,
                                             NODE_APPROVAL, ROLE_APPROVE,
                                             ApprovalFlow, ApprovalNode,
                                             ApprovalSwitch)
from app.modules.company.model import Company
from app.modules.leave.catalog_model import Holiday, LeaveType, LeaveTypeSeniority
from app.modules.leave.constants import GENDER_FEMALE
from app.seed_luong_nghi_phep import find_hr_department

ACTOR = 1
ENTITY = "leave_request"
FLOW_CODE = "NP_DON_NGHI_PHEP"
#  Cao hơn mọi luồng mẫu khác để không phải đoán thứ tự xét.
PRIORITY = 30

#  `code` PHẢI khớp `core/leave_codes.LEAVE_TYPE_SET` — đó là mã ghi sang
#  metadata của giấy GNP. Lệch một ký tự là giấy sinh ra mang loại nghỉ vô nghĩa.
LEAVE_TYPES = [
    #  (code, tên, có lương, trừ quỹ, hạn mức năm, trần/lần, giới tính,
    #   báo trước, cần đính kèm, trừ lễ+cuối tuần, thứ tự)
    ("annual",    "Phép năm",           True,  True,  12.0, 0.0, 0, 3, False, True,  10),
    ("unpaid",    "Nghỉ không lương",   False, False,  0.0, 0.0, 0, 3, False, True,  20),
    #  Nghỉ ốm: KHÔNG báo trước được — không ai biết mai mình ốm. Cần giấy khám.
    ("sick",      "Nghỉ ốm đau",        True,  False,  0.0, 0.0, 0, 0, True,  True,  30),
    #  Thai sản: nghỉ 6 tháng LIÊN TỤC nên KHÔNG trừ cuối tuần / lễ.
    ("maternity", "Nghỉ thai sản",      True,  False,  0.0, 0.0,
     GENDER_FEMALE, 15, True,  False, 40),
    ("wedding",   "Nghỉ cưới hỏi",      True,  False,  0.0, 3.0, 0, 7, False, True,  50),
    ("funeral",   "Nghỉ tang chế",      True,  False,  0.0, 3.0, 0, 0, False, True,  60),
    ("comp_off",  "Nghỉ bù",            True,  False,  0.0, 0.0, 0, 1, False, True,  70),
]

#  Luật *cứ 5 năm thâm niên thì thêm 1 ngày phép*. Khai bằng DỮ LIỆU chứ không
#  bằng `years // 5` trong mã — công ty đổi thành bậc không đều là sửa bảng,
#  không sửa mã và deploy. Lấy bậc CAO NHẤT khớp được, không cộng dồn.
ANNUAL_TIERS = [
    (5, 10, 1.0, "Từ 5 năm: +1 ngày"),
    (10, 15, 2.0, "Từ 10 năm: +2 ngày"),
    (15, 20, 3.0, "Từ 15 năm: +3 ngày"),
    (20, 0, 4.0, "Từ 20 năm trở lên: +4 ngày"),
]

#  Ngày lễ 2026. `is_recurring=True` cho những ngày CỐ ĐỊNH theo dương lịch;
#  Tết Âm và Giỗ Tổ trôi theo lịch âm nên phải nhập lại mỗi năm.
HOLIDAYS_2026 = [
    (date(2026, 1, 1),  "Tết Dương lịch",            True),
    (date(2026, 2, 16), "Tết Nguyên đán (29 Tết)",   False),
    (date(2026, 2, 17), "Tết Nguyên đán (mùng 1)",   False),
    (date(2026, 2, 18), "Tết Nguyên đán (mùng 2)",   False),
    (date(2026, 2, 19), "Tết Nguyên đán (mùng 3)",   False),
    (date(2026, 2, 20), "Tết Nguyên đán (mùng 4)",   False),
    (date(2026, 4, 26), "Giỗ Tổ Hùng Vương",         False),
    (date(2026, 4, 30), "Ngày Giải phóng miền Nam",  True),
    (date(2026, 5, 1),  "Ngày Quốc tế Lao động",     True),
    (date(2026, 9, 2),  "Quốc khánh",                True),
    (date(2026, 9, 3),  "Quốc khánh (nghỉ thêm)",    False),
]


def seed_leave_types(db) -> int:
    """Thêm loại nghỉ còn thiếu. Loại đã có thì KHÔNG đụng vào — người ta đã sửa."""
    added = 0
    for (code, name, is_paid, counts, quota, cap, gender,
         notice, attach, exclude, order) in LEAVE_TYPES:
        if db.query(LeaveType).filter(LeaveType.code == code).first():
            continue
        db.add(LeaveType(
            code=code, name=name, is_paid=is_paid, counts_balance=counts,
            annual_quota_days=quota, max_days_per_request=cap, gender=gender,
            min_notice_days=notice, require_attachment=attach,
            exclude_holiday=exclude, sort_order=order,
            created_by=ACTOR, updated_by=ACTOR,
        ))
        added += 1
    db.flush()
    return added


def seed_seniority_tiers(db) -> int:
    """Bậc thâm niên của Phép năm. Bỏ qua nếu loại đó đã có bậc nào."""
    annual = db.query(LeaveType).filter(LeaveType.code == "annual").first()
    if annual is None:
        return 0
    if db.query(LeaveTypeSeniority).filter(
            LeaveTypeSeniority.leave_type_id == annual.id).count():
        return 0

    for years_from, years_to, extra, note in ANNUAL_TIERS:
        db.add(LeaveTypeSeniority(
            leave_type_id=annual.id, years_from=years_from, years_to=years_to,
            extra_days=extra, note=note, created_by=ACTOR, updated_by=ACTOR))
    db.flush()
    return len(ANNUAL_TIERS)


def seed_holidays(db) -> int:
    """Lịch lễ dùng chung (`company_id = 0`). Trùng ngày thì bỏ qua."""
    added = 0
    for day, name, recurring in HOLIDAYS_2026:
        if db.query(Holiday).filter(Holiday.company_id == 0,
                                    Holiday.date == day).first():
            continue
        db.add(Holiday(company_id=0, date=day, name=name, is_recurring=recurring,
                       created_by=ACTOR, updated_by=ACTOR))
        added += 1
    db.flush()
    return added


def seed_flow(db) -> str:
    """Luồng duyệt của ĐƠN nghỉ phép — hai chặng, cùng hình dạng với luồng GNP.

    Khác luồng `VB_NGHI_PHEP` ở đúng một chỗ: entity là `leave_request` chứ
    không phải `document`. Hai luồng cùng tồn tại là ĐÚNG — đơn chạy trước, giấy
    GNP sinh ra sau khi đơn đã duyệt và không đi vào luồng nào nữa (xem
    `leave/approval_bridge.create_leave_document`).

    ⚠️ Cả hai chặng đều phải có người DỰ PHÒNG: luật I08 bỏ người nộp ra khỏi
    danh sách người duyệt, nên trưởng phòng tự xin nghỉ thì chặng 1 rỗng, và
    trưởng phòng Nhân sự xin nghỉ thì chặng 2 rỗng. Không khai dự phòng là những
    đơn đó KẸT — mà quản lý thì cũng phải nghỉ phép.
    """
    if db.query(ApprovalFlow).filter(ApprovalFlow.entity == ENTITY,
                                     ApprovalFlow.code == FLOW_CODE).first():
        return "đã có"

    hr_dept = find_hr_department(db)
    if hr_dept is None:
        return ("BỎ QUA — không tìm ra phòng Nhân sự. Khai phòng đó rồi chạy lại, "
                "hoặc tự khai luồng trên màn Luồng duyệt.")

    representative = (db.query(Company.legal_representative_id)
                      .filter(Company.id == hr_dept.company_id).scalar())

    flow = ApprovalFlow(
        entity=ENTITY, code=FLOW_CODE, name="Duyệt đơn nghỉ phép",
        description=("Đơn nghỉ phép: trưởng bộ phận của người xin nghỉ duyệt trước, "
                     "rồi tới trưởng phòng Nhân sự. Chặng 2 trỏ vào GHẾ trưởng phòng "
                     "Nhân sự nên đổi người ngồi ghế thì luồng tự đi theo."),
        #  KHÔNG khai điều kiện: mọi đơn nghỉ phép đều đi đường này. Luồng riêng
        #  cho loại nghỉ nào đó thì khai thêm luồng `priority` cao hơn, kèm điều
        #  kiện `leave_type_id in [...]` — bối cảnh đã đưa sẵn ô đó ra.
        condition=json.dumps([]),
        priority=PRIORITY, is_active=True,
        created_by=ACTOR, updated_by=ACTOR,
    )
    db.add(flow)
    db.flush()

    db.add(ApprovalNode(
        flow_id=flow.id, seq=1, branch_key="", name="Trưởng bộ phận duyệt",
        node_kind=NODE_APPROVAL, flow_role=ROLE_APPROVE,
        approver_kind=APPROVER_DEPT_HEAD, approver_ref="",
        multi_mode=MULTI_ANY, sla_hours=24,
        fallback_employee_id=hr_dept.manager_id or None,
        on_no_approver=NO_APPROVER_FALLBACK if hr_dept.manager_id else NO_APPROVER_BLOCK,
        created_by=ACTOR, updated_by=ACTOR,
    ))
    db.add(ApprovalNode(
        flow_id=flow.id, seq=2, branch_key="", name=f"Trưởng {hr_dept.name} duyệt",
        node_kind=NODE_APPROVAL, flow_role=ROLE_APPROVE,
        approver_kind=APPROVER_DEPT_HEAD_OF, approver_ref=str(hr_dept.id),
        multi_mode=MULTI_ANY, sla_hours=24,
        fallback_employee_id=representative or None,
        on_no_approver=NO_APPROVER_FALLBACK if representative else NO_APPROVER_BLOCK,
        created_by=ACTOR, updated_by=ACTOR,
    ))

    #  Bật bộ máy cho entity này, không thì `start()` trả None và mọi đơn rơi về
    #  đường duyệt thẳng — luồng vừa khai nằm im.
    if db.query(ApprovalSwitch).filter(ApprovalSwitch.entity == ENTITY).first() is None:
        db.add(ApprovalSwitch(entity=ENTITY, is_enabled=True,
                              created_by=ACTOR, updated_by=ACTOR))
    db.flush()
    return f"đã khai (id={flow.id})"


def run() -> int:
    db = SessionLocal()
    try:
        types_added = seed_leave_types(db)
        tiers_added = seed_seniority_tiers(db)
        holidays_added = seed_holidays(db)
        flow_status = seed_flow(db)
        db.commit()

        print(f"Loại nghỉ:      thêm {types_added} (tổng {db.query(LeaveType).count()})")
        print(f"Bậc thâm niên:  thêm {tiers_added}")
        print(f"Ngày lễ 2026:   thêm {holidays_added}")
        print(f"Luồng duyệt:    {flow_status}")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(run())
