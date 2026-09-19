"""DỮ LIỆU MẪU CHO MÀN QUỸ PHÉP NĂM — CHỈ DÙNG Ở MÁY LẬP TRÌNH.

    docker compose exec api python -m app.seed_quy_phep_mau
    docker compose exec api python -m app.seed_quy_phep_mau --xoa   # dọn sạch

Vì sao cần: trên CSDL mẫu, **chỉ mỗi «Phép năm» bật «trừ vào quỹ phép»**, nên
nút *Cấp quỹ năm* tạo đúng MỘT dòng cho mỗi người. Màn Quỹ phép vì thế ra 261
hàng giống hệt nhau — không hàng nào có loại nghỉ thứ hai để gom nhóm, không
hàng nào có ngày chờ duyệt, không hàng nào hết phép. Nhìn vào đó không nghiệm
thu được gì: mọi nhánh hiển thị của màn đều nằm ngoài tầm mắt.

Tệp này dựng **sáu ca mẫu**, mỗi ca nhắm đúng một nhánh mà màn hình phải xử
khác đi (xem `CA_MAU`). Số ngày cố ý có ca lẻ nửa ngày và ca điều chỉnh ÂM.

⚠️ **KHÔNG nằm trong `app/seed.py`** và tuyệt đối không được gọi từ
`seed_prod.py` — đây là dữ liệu bịa, nó ghi đè quỹ phép của người thật.

⚠️ **GHI ĐÈ, khác mọi seed khác trong dự án.** Các seed kia chỉ THÊM vì chúng
chạy trên môi trường thật; tệp này là đồ thử nên chạy lại phải ra đúng một bộ
số, nếu không thì thử hai lần ra hai kết quả và không ai biết nhánh nào đúng.
Đổi lại: nó chỉ đụng vào (sáu người đầu × bốn loại nghỉ khai ở đây) của năm
hiện tại, và `--xoa` gỡ đúng chừng ấy dòng.
"""
import sys
from datetime import date

import app.core.all_models  # noqa: F401  — nạp đủ model để mapper cấu hình được
from app.core.database import SessionLocal
from app.modules.employee.model import Employee
from app.modules.leave.balance_model import LeaveBalance
from app.modules.leave.catalog_model import LeaveType

ACTOR = 1

#  Mã loại nghỉ dùng trong bộ mẫu — phải có sẵn trong danh mục
#  (`app.seed_nghi_phep` nạp chúng). Không tự đẻ loại mới: thêm một loại rác vào
#  danh mục là thứ người dùng thật nhìn thấy, còn dòng quỹ bịa thì không.
ANNUAL, COMP_OFF, SICK, UNPAID = "annual", "comp_off", "sick", "unpaid"

#  Mỗi phần tử: (mô tả ca, [(mã loại nghỉ, các cột số)]).
#
#  Cột số khai theo đúng tên cột của `LeaveBalance`; bỏ trống = 0. Công thức:
#      còn lại = allocated + seniority + carried + adjusted
#                − used − pending − carried_out
CA_MAU = [
    (
        "Một loại nghỉ, còn nhiều — hàng ĐƠN, không có mũi tên bung",
        [(ANNUAL, dict(allocated_days=12, used_days=2))],
    ),
    (
        "Một loại nghỉ, HẾT PHÉP — «còn lại 0» phải tô ĐỎ",
        [(ANNUAL, dict(allocated_days=12, used_days=12))],
    ),
    (
        "Ba loại nghỉ — hàng NHÓM có mũi tên; kèm ngày chờ duyệt (hổ phách) "
        "và một loại 0-không-quỹ để đối chiếu với 0-hết-phép",
        [
            #  12 + 2 thâm niên − 3 đã nghỉ − 1.5 giữ chỗ = 9.5  (số LẺ, cố ý)
            (ANNUAL, dict(allocated_days=12, seniority_days=2,
                          used_days=3, pending_days=1.5)),
            #  Có quỹ mà tiêu hết -> 0 ĐỎ
            (SICK, dict(allocated_days=5, used_days=5)),
            #  Không cấp hạn mức bao giờ -> 0 MỜ. Hai số 0 nằm cạnh nhau trong
            #  cùng một nhóm là chỗ dễ thấy nhất để kiểm luật `hasQuota`.
            (COMP_OFF, dict()),
        ],
    ),
    (
        "Có ngày chuyển từ năm trước và một phần đã HẾT HẠN — "
        "bật cột «Chuyển năm trước» + «Hết hạn» trong menu Cột để xem",
        #  ⚠️ Bản đầu cho thêm một dòng «Nghỉ không lương» đã nghỉ 2 ngày ở đây,
        #  và màn hình ra «Còn lại −2». Đó là một trạng thái KHÔNG THỂ CÓ THẬT:
        #  `balance_service.consume/reserve` thoát ngay ở đầu hàm khi loại nghỉ
        #  có `counts_balance = False`, nên `used_days` của loại không trừ quỹ
        #  vĩnh viễn bằng 0. Dữ liệu mẫu bịa ra cảnh sản phẩm không dựng nổi thì
        #  người nghiệm thu đi soi một lỗi không tồn tại.
        [(ANNUAL, dict(allocated_days=12, carried_days=3,
                       carried_expired_days=1, used_days=4))],
    ),
    (
        "Bị TRỪ TAY 2 ngày — cột «Điều chỉnh tay» là cột duy nhất mang số âm",
        [(ANNUAL, dict(allocated_days=12, adjusted_days=-2, used_days=1))],
    ),
    (
        "Đã kết sổ: 4 ngày đã mang sang năm sau — «Đã chuyển đi» giải thích "
        "vì sao số dư tụt mà không ai nghỉ thêm ngày nào. Hai loại nghỉ nên "
        "đây là hàng NHÓM thứ hai, để so cảnh thu gọn với cảnh đang bung",
        [
            (ANNUAL, dict(allocated_days=12, used_days=3, carried_out_days=4)),
            (SICK, dict(allocated_days=3, used_days=1)),
        ],
    ),
]

#  Mọi mã loại nghỉ mà bộ mẫu đụng tới — dùng cho cả nhánh `--xoa`.
#
#  ⚠️ Có `unpaid` dù bộ mẫu KHÔNG dựng dòng nào cho nó: bản đầu của tệp này có,
#  và `--xoa` phải quét được cả những dòng bản đó đã để lại.
MA_LOAI_DUNG = {ANNUAL, COMP_OFF, SICK, UNPAID}


def _nhan_su_mau(db, so_luong: int) -> list[Employee]:
    """Lấy `so_luong` nhân sự đang làm việc, sắp theo id cho chạy lại ra y hệt."""
    return (db.query(Employee)
            .filter(Employee.is_active.is_(True))
            .order_by(Employee.id)
            .limit(so_luong)
            .all())


def _loai_nghi(db) -> dict[str, LeaveType]:
    rows = db.query(LeaveType).filter(LeaveType.code.in_(MA_LOAI_DUNG)).all()
    return {row.code: row for row in rows}


def nap(db, year: int) -> tuple[int, int]:
    """Dựng bộ mẫu. Trả về (số dòng thêm mới, số dòng ghi đè)."""
    types = _loai_nghi(db)
    thieu = MA_LOAI_DUNG - set(types)
    if thieu:
        raise SystemExit(
            f"Danh mục thiếu loại nghỉ {sorted(thieu)} — "
            "chạy `python -m app.seed_nghi_phep` trước."
        )

    employees = _nhan_su_mau(db, len(CA_MAU))
    if len(employees) < len(CA_MAU):
        raise SystemExit(
            f"Cần ít nhất {len(CA_MAU)} nhân sự đang làm việc, CSDL chỉ có "
            f"{len(employees)} — chạy `python -m app.seed` trước."
        )

    them, de = 0, 0
    for employee, (mo_ta, dong_quy) in zip(employees, CA_MAU):
        print(f"  · {employee.full_name} — {mo_ta}")
        for ma_loai, cot_so in dong_quy:
            leave_type = types[ma_loai]
            row = (db.query(LeaveBalance)
                   .filter(LeaveBalance.employee_id == employee.id,
                           LeaveBalance.year == year,
                           LeaveBalance.leave_type_id == leave_type.id)
                   .first())
            if row is None:
                row = LeaveBalance(employee_id=employee.id, year=year,
                                   leave_type_id=leave_type.id,
                                   created_by=ACTOR)
                db.add(row)
                them += 1
            else:
                de += 1

            #  Đặt LẠI trọn bộ cột số, kể cả cột không khai trong ca mẫu: ghi đè
            #  nửa vời thì chạy lần hai trên một dòng cũ ra số lai giữa hai bộ.
            row.company_id = employee.company_id or 0
            row.allocated_days = 0.0
            row.seniority_days = 0.0
            row.carried_days = 0.0
            row.adjusted_days = 0.0
            row.used_days = 0.0
            row.pending_days = 0.0
            row.carried_out_days = 0.0
            row.carried_expired_days = 0.0
            for cot, gia_tri in cot_so.items():
                setattr(row, cot, float(gia_tri))
            row.note = f"Dữ liệu mẫu để thử màn Quỹ phép — {mo_ta}"
            row.updated_by = ACTOR

    db.commit()
    return them, de


def xoa(db, year: int) -> int:
    """Gỡ đúng những dòng bộ mẫu đã dựng — không đụng dòng của người khác."""
    types = _loai_nghi(db)
    employees = _nhan_su_mau(db, len(CA_MAU))
    if not types or not employees:
        return 0

    so = (db.query(LeaveBalance)
          .filter(LeaveBalance.year == year,
                  LeaveBalance.employee_id.in_([e.id for e in employees]),
                  LeaveBalance.leave_type_id.in_([t.id for t in types.values()]))
          .delete(synchronize_session=False))
    db.commit()
    return so


def run() -> int:
    year = date.today().year
    don_dep = "--xoa" in sys.argv

    db = SessionLocal()
    try:
        if don_dep:
            so = xoa(db, year)
            print(f"Đã gỡ {so} dòng quỹ mẫu của năm {year}.")
            return 0

        print(f"Dựng dữ liệu mẫu cho màn Quỹ phép năm {year}:")
        them, de = nap(db, year)
        print(f"\nXong — thêm {them} dòng, ghi đè {de} dòng.")
        print("Mở http://localhost:8083/hr/leave-balances (hoặc cổng dev của bạn).")
        print("Gỡ đi: python -m app.seed_quy_phep_mau --xoa")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(run())
