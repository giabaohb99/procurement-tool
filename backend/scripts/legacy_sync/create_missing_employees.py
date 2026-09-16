"""Tạo hồ sơ nhân sự (+ tài khoản) cho người app cũ chưa có bên ERP.

Đại ca chốt 16/09: "26 người không có hồ sơ nào bên ERP thì tạo người dùng +
employee". Script này làm đúng nhóm đó — nhóm `khong_thay` của `sync_users`:
email không tra ra hồ sơ nào, VÀ tên cũng không gợi ra hồ sơ nào. Người nào chỉ
lệch email mà tên trùng thì nằm ở nhóm khác và KHÔNG tạo mới ở đây — tạo là đẻ
thêm một bản trùng nữa, đúng thứ bệnh ERP đang có (hồ sơ 38/201).

Hồ sơ mới đi qua `employee_service.create_employee` chứ không `db.add` thẳng, để
được sinh mã `NSUxxx`, kiểm trùng email, dựng `tab_employee_department` và ghi
nhật ký y như người bấm trên giao diện.

HAI CHỖ CỐ Ý KHÔNG ĐOÁN:

- `status` để `official` cho tất cả. App cũ không có khái niệm tình trạng làm
  việc, chỉ có bật/tắt tài khoản — không suy ra được ai đã nghỉ việc. Ai nghỉ
  thật thì đại ca sửa lại trên màn hồ sơ.
- Người `isActive = false` bên app cũ thì hồ sơ tạo ra ở trạng thái TẮT và
  KHÔNG cấp tài khoản. Mở đường đăng nhập cho người mà chính app cũ đã khóa là
  việc phải có người quyết, không phải mặc định của script.

MẬT KHẨU: sinh ngẫu nhiên từng người, ghi ra tệp `--password-out`. Tệp đó là
danh sách mật khẩu thật của người thật — ĐỂ NGOÀI KHO MÃ, giao xong thì xóa.
Script từ chối ghi đè tệp đã có. Ai đăng nhập bằng Google thì không cần tới nó:
`auth_service` tra tài khoản theo email nên tài khoản mới nhận Google ngay.

CHẠY ĐƯỢC NHIỀU LẦN: người đã có `legacy_id` thì bỏ qua, không đẻ bản thứ hai.
Mặc định chỉ xem trước, `--apply` mới ghi.

    python -m scripts.legacy_sync.create_missing_employees --export /tmp/fb-export.json
    python -m scripts.legacy_sync.create_missing_employees --export /tmp/fb-export.json \
        --apply --password-out /tmp/mat-khau-moi.txt
"""

import argparse
import collections
import json
import os
import secrets
import string
import sys

from sqlalchemy import select

import app.core.all_models  # noqa: F401  nạp đủ model để SQLAlchemy dựng xong quan hệ
from app.core.database import SessionLocal
from app.modules.department.model import Department
from app.modules.employee import service as employee_service
from app.modules.employee.model import Employee
from app.modules.employee.schema import EmployeeCreate
from app.modules.user import service as user_service
from app.modules.user.schema import UserProvision
from scripts.legacy_sync.sync_users import classify_users

#  Người tạo ra các hồ sơ này trong nhật ký thao tác. `0` = hệ thống, giống cách
#  seed ghi — không mượn danh một người thật cho việc máy làm.
SYSTEM_ACTOR_ID = 0

PASSWORD_LENGTH = 16


def _load_export(path: str) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _make_password() -> str:
    """Sinh mật khẩu ngẫu nhiên chắc chắn qua được `validate_password`.

    Ghép cố định một chữ hoa, một chữ thường, một chữ số rồi mới bốc ngẫu nhiên
    phần còn lại — bốc hết bằng `choice` thì có xác suất ra chuỗi toàn chữ, và
    lỗi đó chỉ nổ ở lần chạy thứ n với đúng một người trong danh sách.
    """
    pool = string.ascii_letters + string.digits
    body = [secrets.choice(string.ascii_uppercase),
            secrets.choice(string.ascii_lowercase),
            secrets.choice(string.digits)]
    body += [secrets.choice(pool) for _ in range(PASSWORD_LENGTH - len(body))]
    #  `SystemRandom.shuffle` chứ không `random.shuffle`: cùng một nguồn ngẫu
    #  nhiên với `secrets`, không để lẫn bộ sinh giả vào giữa.
    secrets.SystemRandom().shuffle(body)
    return "".join(body)


def _index_departments_by_legacy(db) -> dict[str, Department]:
    return {d.legacy_id: d for d in db.execute(select(Department)).scalars()
            if d.legacy_id}


def _count_tickets_by_user(requests: dict) -> collections.Counter:
    return collections.Counter(r.get("createdBy") for r in requests.values()
                               if isinstance(r, dict))


def _already_stamped(db) -> set[str]:
    return {e.legacy_id for e in db.execute(select(Employee)).scalars()
            if e.legacy_id}


def create_one(db, uid: str, node: dict, departments: dict[str, Department],
               apply: bool) -> tuple[bool, Employee | None, str]:
    """Tạo một hồ sơ.

    Trả về (làm được không, hồ sơ, mật khẩu). Lượt xem trước vẫn trả `True` —
    con số cuối bản xem trước phải là con số sẽ xảy ra khi `--apply`, không thì
    xem trước xong vẫn không biết sắp tạo mấy hồ sơ.
    """
    name = (node.get("displayName") or "").strip()
    email = (node.get("email") or "").strip()
    live = bool(node.get("isActive"))
    dept = departments.get(node.get("departmentId") or "")
    if dept is None:
        print(f"  LOI    {name}: phong ban {node.get('departmentId')!r} "
              f"chua tra ra ben ERP, bo qua")
        return False, None, ""

    label = "on " if live else "off"
    print(f"  TAO    {label} {name:<26} {email:<36} pb {dept.id:<3} {dept.name}")
    if not apply:
        if not live:
            print("         (app cu da khoa — se tao ho so TAT, khong cap tai khoan)")
        return True, None, ""

    emp = employee_service.create_employee(db, EmployeeCreate(
        full_name=name,
        email=email,
        phone=(node.get("phone") or "").strip(),
        company_id=0,       # dùng chung mọi pháp nhân, như 237 hồ sơ sẵn có
        department_id=dept.id,
        status="official",  # app cũ không có khái niệm này, xem docstring
        is_active=live,
    ), SYSTEM_ACTOR_ID)
    emp.legacy_id = uid
    db.commit()

    if not live:
        print(f"         ma {emp.code}  ho so id {emp.id}  (app cu da khoa tai "
              f"khoan nay — ho so TAT, khong cap tai khoan)")
        return True, emp, ""

    password = _make_password()
    user = user_service.provision_user(db, UserProvision(
        employee_id=emp.id, email=email, password=password,
    ), SYSTEM_ACTOR_ID)
    print(f"         ma {emp.code}  ho so id {emp.id}  tai khoan id {user.id}")
    return True, emp, password


def _open_password_file(path: str):
    if os.path.exists(path):
        print(f"LOI: {path} da ton tai. Script khong ghi de len danh sach mat "
              f"khau cu — doi ten tep hoac chon duong dan khac.")
        return None
    return open(path, "w", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export", required=True,
                        help="duong dan ban ket xuat JSON tu Firebase")
    parser.add_argument("--apply", action="store_true",
                        help="ghi that; bo qua thi chi xem truoc")
    parser.add_argument("--password-out",
                        help="tep nhan danh sach mat khau moi (bat buoc khi --apply)")
    args = parser.parse_args()

    if args.apply and not args.password_out:
        print("LOI: --apply phai di kem --password-out, khong thi mat khau vua "
              "sinh ra khong ai doc duoc va 26 nguoi khong dang nhap duoc.")
        return 1

    data = _load_export(args.export)
    for node in ("users", "requests"):
        if node not in data:
            print(f"LOI: ban ket xuat thieu nut {node!r}")
            return 1
    tickets = _count_tickets_by_user(data["requests"])

    db = SessionLocal()
    out = None
    try:
        buckets = classify_users(db, data["users"])
        stamped = _already_stamped(db)
        todo = [(uid, node) for uid, node, _ in buckets["khong_thay"]
                if uid not in stamped]

        print(f"=== TAO HO SO MOI — {len(todo)} nguoi, "
              f"{sum(tickets.get(u, 0) for u, _ in todo)} phieu ===")
        if len(todo) < len(buckets["khong_thay"]):
            print(f"  (bo qua {len(buckets['khong_thay']) - len(todo)} nguoi da "
                  f"co ho so tu luot chay truoc)")
        if not todo:
            print("  khong con ai de tao.")
            return 0

        departments = _index_departments_by_legacy(db)
        if args.apply:
            out = _open_password_file(args.password_out)
            if out is None:
                return 1
            out.write("# Mat khau tai khoan ERP moi cap cho nguoi dung app dat "
                      "xe cu.\n# Giao xong thi XOA TEP NAY. Dang nhap bang ma "
                      "nhan vien hoac email.\n\n")

        n_emp = n_user = 0
        #  Xếp theo số phiếu giảm dần để dòng đáng chú ý nằm trên đầu.
        for uid, node in sorted(todo, key=lambda r: -tickets.get(r[0], 0)):
            ok, emp, password = create_one(db, uid, node, departments, args.apply)
            if not ok:
                continue
            n_emp += 1
            if node.get("isActive"):
                n_user += 1
            if password:
                out.write(f"{emp.code:<10} {emp.full_name:<28} "
                          f"{emp.email:<36} {password}\n")

        print(f"\n  ho so tao moi   : {n_emp}")
        print(f"  tai khoan cap   : {n_user}")
        if args.apply:
            print(f"  mat khau ghi o  : {args.password_out}")
            print("\n  DA GHI VAO DB.")
        else:
            print("\n  MOI CHI XEM TRUOC — them --apply --password-out de ghi that.")
    except Exception:
        db.rollback()
        raise
    finally:
        if out is not None:
            out.close()
        db.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
