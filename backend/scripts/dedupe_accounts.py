"""Gom tài khoản trùng email về MỘT bản ghi — luôn giữ id NHỎ NHẤT.

Đại ca chốt 16/09/2026: "nếu có tk trùng trên erp thì luôn lấy id nhỏ nhất".
Đây là luật chung của ERP, không riêng việc đồng bộ app đặt xe — nên script nằm
ở `scripts/` chứ không ở `scripts/legacy_sync/`.

VÌ SAO id nhỏ nhất lại đúng chứ không chỉ là một quy ước cho dễ nhớ: cả ba đường
đăng nhập đều kết bằng `.first()` — `auth_service.authenticate` tra `User.email`,
`google_login` tra `Employee.email` — nên khi trùng thì người dùng rơi vào bản
ghi nào là do thứ tự bản ghi quyết định. Trên InnoDB thứ tự đó gần như luôn là
khóa chính tăng dần, tức bản ghi CŨ NHẤT. Giữ id nhỏ nhất = giữ đúng cái bản ghi
mà hệ thống vẫn đang dùng, và cũng là bản ghi đã tích lũy lịch sử thao tác.

BA VIỆC CHO MỖI BẢN GHI THỪA (không xóa gì cả):

1. Xóa TRỐNG email của hồ sơ nhân sự thừa. Không làm bước này thì `ensure_email_unique`
   (bao-CR-368) vẫn thấy hai hồ sơ cùng email: người giữ hồ sơ được giữ lại mở ra
   sửa một ô bất kỳ rồi bấm Lưu là ăn ngay "Email này đã thuộc về nhân sự NSUxxx",
   dù hồ sơ kia đã tắt. Tắt hoạt động KHÔNG nhả email ra.
2. Tắt hoạt động hồ sơ nhân sự thừa, qua `employee_service.update_employee` chứ
   không `setattr` thẳng — để dây bao-CR-400 chạy đủ: khóa mọi tài khoản gắn với
   hồ sơ, đá phiên đăng nhập (`force_relogin`), xóa cache quyền, ghi nhật ký.
3. Dời `legacy_id` xuống bản ghi được giữ nếu nó đang nằm trên bản ghi thừa.
   Hai bên cùng có `legacy_id` khác nhau thì script DỪNG — đó là hai người thật
   bị gộp nhầm thành một cụm, không phải bản trùng.

CỐ Ý KHÔNG LÀM:

- KHÔNG đặt `status = "resigned"`. Người đó vẫn đang đi làm; thứ bị bỏ là tờ hồ
  sơ thừa, không phải con người. Ghi "nghỉ việc" là nói sai một điều về người thật.
- KHÔNG xóa cứng, KHÔNG dời tham chiếu. Script chỉ ĐẾM và in ra chỗ nào còn trỏ
  vào bản ghi thừa; dời hay không là việc phải có người đọc rồi quyết.

    python -m scripts.dedupe_accounts
    python -m scripts.dedupe_accounts --cluster ntktrang.idagroup@gmail.com --apply
"""

import argparse
import collections
import sys

from sqlalchemy import func, select, text

import app.core.all_models  # noqa: F401  nạp đủ model trước khi hỏi metadata
from app.core.all_models import Base
from app.core.database import SessionLocal
from app.modules.employee import service as employee_service
from app.modules.employee.model import Employee
from app.modules.employee.schema import EmployeeUpdate
from app.modules.user.model import User

SYSTEM_ACTOR_ID = 0

#  Lý do đá phiên, khớp bộ mã của `login_session`: 6 = hồ sơ nhân sự ngừng hoạt
#  động (bao-CR-400). Truyền thẳng vào `update_employee` không được — nó tự chọn
#  lý do — nên hằng này chỉ để ghi chú, xem `has_left_company`.
REASON_EMPLOYEE_INACTIVE = 6

#  Cột trỏ tới tab_user: `created_by` / `updated_by` của AuditMixin là ID TÀI KHOẢN.
USER_COLUMN_NAMES = {"user_id", "created_by", "updated_by", "revoked_by", "actor_user_id"}
USER_COLUMN_SUFFIX = "_user_id"

#  Cột trỏ tới tab_employee. Danh sách đuôi `_employee_id` bắt được gần hết; mấy
#  cột dưới đây là ngoại lệ đặt tên không theo đuôi đó — chúng là ID NHÂN SỰ chứ
#  không phải ID tài khoản, dù tên cột không nói ra (xem ghi chú `assignee_id`
#  trong doc). Thiếu một cột ở đây thì số đếm THẤP HƠN sự thật, nên bản in luôn
#  kèm câu nhắc là danh sách này khai tay.
EMPLOYEE_COLUMN_NAMES = {"employee_id", "assignee_id", "requester_id", "manager_id",
                         "approver_id", "handover_to_id", "on_behalf_of_id"}
EMPLOYEE_COLUMN_SUFFIX = "_employee_id"


def _scan_columns(kind: str) -> list[tuple[str, str]]:
    """Liệt kê (bảng, cột) có khả năng trỏ tới tab_user hoặc tab_employee."""
    names = USER_COLUMN_NAMES if kind == "user" else EMPLOYEE_COLUMN_NAMES
    suffix = USER_COLUMN_SUFFIX if kind == "user" else EMPLOYEE_COLUMN_SUFFIX
    found = []
    for table in Base.metadata.tables.values():
        for col in table.columns:
            if col.name in names or col.name.endswith(suffix):
                found.append((table.name, col.name))
    return sorted(found)


def count_refs(db, kind: str, value: int) -> list[tuple[str, str, int]]:
    """Đếm số dòng đang trỏ vào `value`, bỏ qua chính bảng chủ của nó."""
    own_table = "tab_user" if kind == "user" else "tab_employee"
    hits = []
    for table, col in _scan_columns(kind):
        if table == own_table and col in ("id",):
            continue
        n = db.execute(text(f"SELECT COUNT(*) FROM `{table}` WHERE `{col}` = :v"),
                       {"v": value}).scalar()
        if n:
            hits.append((table, col, n))
    return hits


def find_clusters(db) -> dict[str, list[User]]:
    """Gom tài khoản theo email (bỏ hoa/thường).

    Chỉ đếm tài khoản ĐANG HOẠT ĐỘNG. Email rỗng không tính trùng — nhiều người
    chưa có email và họ đăng nhập bằng mã nhân viên. Tài khoản đã khóa cũng không
    tính: mọi đường đăng nhập đều lọc `is_active` trước nên nó không giành chỗ
    với ai nữa, và tính vào thì lượt chạy sau lại bày ra đúng cụm vừa dọn xong.
    """
    rows = db.execute(select(User).where(func.trim(User.email) != "",
                                         User.is_active.is_(True))
                      .order_by(User.id)).scalars().all()
    groups = collections.defaultdict(list)
    for u in rows:
        groups[(u.email or "").strip().lower()].append(u)
    return {k: v for k, v in sorted(groups.items()) if len(v) > 1}


def _employee_line(db, emp: Employee | None) -> str:
    if emp is None:
        return "(khong gan ho so nhan su)"
    return (f"ho so {emp.id} [{emp.code}] {emp.full_name} "
            f"email={emp.email!r} active={emp.is_active} legacy={emp.legacy_id!r}")


def retire_one(db, loser: User, keeper: User, apply: bool) -> bool:
    """Bỏ một tài khoản thừa. Trả về True nếu làm được (hoặc xem trước được)."""
    loser_emp = db.get(Employee, loser.employee_id) if loser.employee_id else None
    keeper_emp = db.get(Employee, keeper.employee_id) if keeper.employee_id else None

    print(f"  BO     tai khoan {loser.id} -> giu tai khoan {keeper.id}")
    print(f"         thua : {_employee_line(db, loser_emp)}")
    print(f"         giu  : {_employee_line(db, keeper_emp)}")

    for kind, value in (("user", loser.id),
                        ("employee", loser_emp.id if loser_emp else 0)):
        if not value:
            continue
        hits = count_refs(db, kind, value)
        total = sum(n for _, _, n in hits)
        label = "tai khoan" if kind == "user" else "ho so"
        print(f"         {label} {value} con {total} cho tro toi"
              f"{':' if hits else ' (khong con gi)'}")
        for table, col, n in hits:
            print(f"           {table}.{col} = {n}")

    #  legacy_id chỉ có MỘT cột, không diễn đạt được nhiều-về-một. Hai bên cùng có
    #  dấu mà khác nhau nghĩa là cụm này gom nhầm hai người thật.
    move_legacy = ""
    if loser_emp is not None and keeper_emp is not None:
        lo, ke = (loser_emp.legacy_id or ""), (keeper_emp.legacy_id or "")
        if lo and ke and lo != ke:
            print(f"         LOI: hai ho so mang hai legacy_id khac nhau "
                  f"({ke!r} va {lo!r}) — day khong phai ban trung, bo qua cum nay.")
            return False
        if lo and not ke:
            move_legacy = lo
            print(f"         doi legacy_id {lo!r} tu ho so {loser_emp.id} "
                  f"sang ho so {keeper_emp.id}")

    if not apply:
        return True

    if loser_emp is not None:
        if move_legacy:
            keeper_emp.legacy_id = move_legacy
            loser_emp.legacy_id = ""
            db.flush()
        #  Một lượt lưu làm cả hai việc: nhả email ra và tắt hoạt động. Đi qua
        #  service để dây bao-CR-400 (khóa tài khoản + đá phiên + nhật ký) chạy đủ.
        employee_service.update_employee(
            db, loser_emp.id, EmployeeUpdate(email="", is_active=False), SYSTEM_ACTOR_ID)
        db.refresh(loser)
        print(f"         da tat ho so {loser_emp.id}, tai khoan {loser.id} "
              f"active={loser.is_active}")
    else:
        #  Tài khoản mồ côi: không có hồ sơ nào để đi qua service, khóa thẳng.
        from app.modules.user import service as user_service
        user_service.set_active(db, loser.id, False, SYSTEM_ACTOR_ID)
        print(f"         tai khoan mo coi {loser.id} da khoa")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cluster", action="append", default=[],
                        help="chi xu ly email nay (lap lai duoc); bo qua thi xem het")
    parser.add_argument("--apply", action="store_true",
                        help="ghi that; bo qua thi chi xem truoc")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        clusters = find_clusters(db)
        only = {c.strip().lower() for c in args.cluster}
        if only:
            clusters = {k: v for k, v in clusters.items() if k in only}
            for miss in only - set(clusters):
                print(f"CANH BAO: {miss!r} khong phai mot cum trung, bo qua")

        print(f"=== TAI KHOAN TRUNG EMAIL — {len(clusters)} cum ===")
        print(f"  (quet {len(_scan_columns('user'))} cot tro toi tai khoan, "
              f"{len(_scan_columns('employee'))} cot tro toi ho so; danh sach cot "
              f"khai tay trong ma nguon, thieu cot thi so dem thap hon su that)")
        if not clusters:
            print("  khong con cum nao.")
            return 0

        n_done = 0
        for email, users in clusters.items():
            keeper, losers = users[0], users[1:]
            print(f"\n{email}  ->  giu id {keeper.id}, bo {[u.id for u in losers]}")
            for loser in losers:
                if retire_one(db, loser, keeper, args.apply):
                    n_done += 1
        if args.apply:
            db.commit()
            print(f"\n  da bo {n_done} tai khoan thua. DA GHI VAO DB.")
        else:
            print(f"\n  se bo {n_done} tai khoan thua.")
            print("  MOI CHI XEM TRUOC — them --apply de ghi that.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
