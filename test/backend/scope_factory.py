"""Khung dựng dữ liệu cho test PHẠM VI DỮ LIỆU (trục B) — cụm 00.

Vì sao có tệp này: một ca kiểm phạm vi cần 1 công ty, 1–2 phòng ban, 1 nhân sự,
1 tài khoản, 1 vai trò, 1 dòng `Permission`, 0–n dòng `UserScope`, rồi xóa cache
quyền. Viết tay là ~25 dòng cho MỘT ca — đó chính là lý do hôm nay chỉ 2/203 tệp
test chạm tới `UserScope`. Dựng khó quá thì không ai dựng, và phần phân quyền
đông người dùng nhất lại là phần ít test nhất.

    world = build_world(db)
    a = world.grant("a1", "purchase_request", scope="dept", exc_dept=["A.kt"])
    assert a.sees(PurchaseRequest) == {pr1.id}

Ba ràng buộc bắt buộc, thiếu là cả đợt sai lệch mà không biết:

1. **Xóa cache sau MỌI lần đổi vai trò/quyền/phạm vi.** `_PERM_CACHE` sống 60
   giây xuyên các test trong cùng tiến trình pytest. Mọi hàm dựng dữ liệu ở đây
   tự gọi `perm_cache_clear`; ngoài ra `conftest` còn xóa sạch giữa mỗi test.
2. **Nhân sự KHÔNG có tài khoản phải dựng được** — `emp["khongtk"]`. Đó là ca
   hỏng số 1 của cụm 01: `auth.py` bỏ im lặng dòng phạm vi trỏ vào người này.
3. **Một người NHIỀU vai trò** — gọi `grant()` hai lần. `scope_condition` HỢP
   các grant, nên loại trừ của vai trò này bị vai trò kia đè; ca hỏng số 5.

⚠️ Thế giới mẫu CỐ Ý có **hai phòng trùng tên khác pháp nhân** (`A.kt` và `B.kt`
đều tên "Phòng Kế toán"). Đó không phải sơ ý: đường lùi theo tên trong
`_dept_ref_map`/`_dept_match` chỉ lộ ra khi có trùng tên, mà hệ thật có 11 pháp
nhân đặt tên phòng theo khuôn. Test nào muốn tránh nhập nhằng thì dùng ID.
"""
from __future__ import annotations

from app.core.auth import get_perm_profile, perm_cache_clear
from app.core.scoping import apply_scope, get_scoped

# ── Thế giới mẫu: tên cố định để mọi cụm nói cùng một ngôn ngữ ─────────────────
COMPANY_SPECS = [("A", "CTY_A", "Công ty A"), ("B", "CTY_B", "Công ty B")]

# (khóa, công ty, mã, tên)  — B.kt trùng TÊN với A.kt là cố ý, xem docstring.
DEPT_SPECS = [
    ("A.kt", "A", "A_KT", "Phòng Kế toán"),
    ("A.mua", "A", "A_MUA", "Phòng Thu mua"),
    ("B.kt", "B", "B_KT", "Phòng Kế toán"),
    ("B.hc", "B", "B_HC", "Phòng Hành chính"),
]

# (khóa, công ty, phòng, có tài khoản?)
EMPLOYEE_SPECS = [
    ("a1", "A", "A.kt", True),
    ("a2", "A", "A.kt", True),
    ("a3", "A", "A.mua", True),
    ("b1", "B", "B.kt", True),
    ("khongtk", "A", "A.kt", False),   # nhân sự KHÔNG có tài khoản — ca hỏng số 1
    ("khongphong", "A", None, True),   # chưa gắn phòng → nhánh dept phải chặn
    ("khongcty", None, None, True),    # chưa gắn pháp nhân → nhánh company phải chặn
]


# ── Entity → model, cho 22 entity có lọc thật ─────────────────────────────────
#
#  Map này CỐ Ý chỉ sống trong tầng test. `core/` không cần nó: `apply_scope`
#  nhận sẵn model từ nơi gọi. Đưa vào `core/` là dựng thêm một danh sách phải
#  bảo trì song song với `SCOPE_FIELDS` mà không ai được lợi (YAGNI).
#
#  Entity khai `PUBLIC` cố tình vắng mặt — không có gì để đối chiếu cột.
ENTITY_MODEL_PATHS = {
    "purchase_request": ("app.modules.purchase_request.model", "PurchaseRequest"),
    "survey_request": ("app.modules.survey_request.model", "SurveyRequest"),
    "purchase_order": ("app.modules.purchase_order.model", "PurchaseOrder"),
    "goods_receipt": ("app.modules.goods_receipt.model", "GoodsReceipt"),
    "payable": ("app.modules.payable.model", "Payable"),
    "payment_request": ("app.modules.payment_request.model", "PaymentRequest"),
    "contract": ("app.modules.contract.model", "Contract"),
    "inventory": ("app.modules.inventory.model", "Inventory"),
    "survey": ("app.modules.survey.model", "Survey"),
    "employee": ("app.modules.employee.model", "Employee"),
    "user": ("app.modules.user.model", "User"),
    "company": ("app.modules.company.model", "Company"),
    "department": ("app.modules.department.model", "Department"),
    "ticket": ("app.modules.ticket.model", "Ticket"),
    "document": ("app.modules.document.model", "Document"),
    "document_book": ("app.modules.doc_catalog.book_model", "DocumentBook"),
    "approval_flow": ("app.modules.approval.flow_model", "ApprovalFlow"),
    "seal_request": ("app.modules.seal_request.model", "SealRequest"),
    "vehicle_booking": ("app.modules.vehicle_booking.model", "VehicleBooking"),
    "leave_request": ("app.modules.leave.request_model", "LeaveRequest"),
    "leave_balance": ("app.modules.leave.balance_model", "LeaveBalance"),
    "room_booking": ("app.modules.meeting_room.model", "RoomBooking"),
}


def model_of(entity: str):
    """Model của entity — chỉ cho entity có lọc thật. `KeyError` nếu khai PUBLIC."""
    from importlib import import_module

    module, name = ENTITY_MODEL_PATHS[entity]
    return getattr(import_module(module), name)


class Actor:
    """Một tài khoản trong thế giới mẫu, kèm các vai trò đã cấp cho nó."""

    def __init__(self, world: "World", key: str, user, employee):
        self.world = world
        self.key = key
        self.user = user
        self.employee = employee
        self.roles: list = []
        self._entities: set[str] = set()

    # ── cấp quyền ─────────────────────────────────────────────────────────────
    def grant(self, entity: str, scope: str = "all", *, actions=("read",),
              inc_company=(), exc_company=(), inc_dept=(), exc_dept=(),
              inc_employee=(), exc_employee=(), role_code: str | None = None):
        """Thêm MỘT vai trò (= một grant) cho tài khoản này.

        `inc_*`/`exc_*` chính là năm ô của hộp thoại «Phạm vi — <vai trò>»:
        công ty nhận khóa của `world.co`, phòng ban nhận khóa của `world.dept`
        (lưu ID theo CR-086), nhân sự nhận khóa của `world.emp`.

        Gọi nhiều lần = nhiều vai trò. Phạm vi luôn gắn vào ĐÚNG vai trò vừa tạo,
        đúng như câu «Chỉ áp dụng cho vai trò này» trên màn hình.
        """
        from app.modules.role.model import Permission, Role
        from app.modules.user.model import UserRole

        db = self.world.db
        self.world._role_seq += 1
        code = role_code or f"VT{self.world._role_seq}"
        role = Role(code=code, name=f"Vai trò {code}")
        db.add(role)
        db.flush()
        db.add(Permission(role_id=role.id, entity=entity, scope=scope,
                          **{f"can_{a}": True for a in actions}))
        db.add(UserRole(user_id=self.user.id, role_id=role.id))
        db.flush()

        for values, dim, is_exclude in (
            (inc_company, "company", False), (exc_company, "company", True),
            (inc_dept, "department", False), (exc_dept, "department", True),
            (inc_employee, "employee", False), (exc_employee, "employee", True),
        ):
            for v in values:
                self.add_scope_row(role, dim, self.world.resolve(dim, v),
                                   is_exclude=is_exclude)

        self.roles.append(role)
        self._entities.add(entity)
        perm_cache_clear(self.user.id)
        return self

    def add_scope_row(self, role, dim: str, value, *, is_exclude: bool = False,
                      entity: str = ""):
        """Ghi thẳng một dòng `tab_user_scope` — dùng cho ca dữ liệu hỏng.

        `grant()` đã gọi hàm này cho đường bình thường. Gọi trực tiếp khi cần
        dựng thứ giao diện không tạo ra được: giá trị không phải số ở
        `dim=company` (B11), hay `entity` khác rỗng (B12).
        """
        from app.modules.user.model import UserScope

        self.world.db.add(UserScope(user_id=self.user.id, role_id=role.id,
                                    entity=entity, dim=dim, value=str(value),
                                    is_exclude=is_exclude))
        self.world.db.flush()
        perm_cache_clear(self.user.id)
        return self

    def add_department(self, dept_key: str):
        """Kiêm nhiệm thêm một phòng (CR-167) — phạm vi bậc `dept` phải mở đủ cả.

        ⚠️ Tự chèn **phòng CHÍNH** vào bảng kiêm nhiệm ở lần gọi đầu. Không phải
        tiện tay: `departments_of` đọc THUẦN `tab_employee_department`, còn
        `_role_scope_cond` chỉ lùi về `dept_id` của hồ sơ khi bảng đó RỖNG
        (`scoping.py:278`). Ghi mỗi phòng kiêm nhiệm là nhân sự đó **mất phòng
        chính** — một hình dạng dữ liệu không tồn tại ở chạy thật, vì
        `set_departments` luôn ghi cả hai (`department_service.py:55`). Test
        dựng sai hiện trạng thì bắt được lỗi không có thật, và bỏ sót lỗi có thật.
        """
        from app.modules.employee.department_model import EmployeeDepartment

        db = self.world.db
        have = {r.department_id for r in db.query(EmployeeDepartment)
                .filter(EmployeeDepartment.employee_id == self.employee.id).all()}
        if not have and self.employee.department_id:
            db.add(EmployeeDepartment(employee_id=self.employee.id,
                                      department_id=self.employee.department_id,
                                      is_primary=True))
            have.add(self.employee.department_id)
        #  Gọi lại cùng một phòng là không-làm-gì: `uq_employee_department` cấm
        #  trùng, mà mọi phép đếm theo phòng cũng sẽ cộng dư nếu lách được.
        if self.world.dept[dept_key] not in have:
            db.add(EmployeeDepartment(employee_id=self.employee.id,
                                      department_id=self.world.dept[dept_key],
                                      is_primary=False))
        db.flush()
        perm_cache_clear(self.user.id)
        return self

    # ── đọc kết quả ───────────────────────────────────────────────────────────
    def profile(self) -> dict:
        return get_perm_profile(self.world.db, self.user)

    def _entity(self, entity: str | None) -> str:
        if entity:
            return entity
        if len(self._entities) != 1:
            raise AssertionError(
                f"{self.key} có {len(self._entities)} entity — truyền entity= rõ ràng")
        return next(iter(self._entities))

    def sees(self, model, entity: str | None = None, action: str = "read") -> set[int]:
        """Tập id nhìn thấy được sau `apply_scope`. So thẳng set này với set kỳ vọng.

        Trả tập id chứ không trả điều kiện SQL: kiểm "có sinh ra điều kiện" mà
        không chạy nó thì đổi `company_id` thành `id` vẫn xanh.
        """
        db = self.world.db
        q = apply_scope(db.query(model), model, self._entity(entity),
                        self.user, self.profile(), action)
        return {row.id for row in q.all()}

    def can_get(self, model, oid: int, entity: str | None = None,
                action: str = "read") -> bool:
        """Gõ thẳng id vào URL có ra không — đường vòng của cụm 08."""
        return get_scoped(self.world.db, model, self._entity(entity), oid,
                          self.user, self.profile(), action) is not None


class World:
    """Hai pháp nhân × hai phòng × bảy nhân sự, tên cố định."""

    def __init__(self, db):
        self.db = db
        self.co: dict[str, int] = {}
        self.dept: dict[str, int] = {}
        self.emp: dict[str, int] = {}
        self._actors: dict[str, Actor] = {}
        self._role_seq = 0

    def resolve(self, dim: str, value):
        """Khóa thân thiện ("A.kt") → giá trị lưu trong `tab_user_scope`.

        Số truyền thẳng: ca kiểm cần id không tồn tại, hoặc cần chính TÊN phòng
        (đường lùi), thì truyền nguyên giá trị đó.
        """
        if isinstance(value, int):
            return value
        table = {"company": self.co, "department": self.dept, "employee": self.emp}[dim]
        return table.get(value, value)

    def actor(self, key: str) -> Actor:
        return self._actors[key]

    def grant(self, key: str, entity: str, scope: str = "all", **kw) -> Actor:
        return self._actors[key].grant(entity, scope, **kw)

    def user_id(self, key: str) -> int:
        return self._actors[key].user.id


def build_world(db) -> World:
    """Dựng thế giới mẫu. Gọi một lần đầu mỗi test; không phụ thuộc fixture `seed`."""
    from app.modules.company.model import Company
    from app.modules.department.model import Department
    from app.modules.employee.model import Employee
    from app.modules.user.model import User

    world = World(db)

    for key, code, name in COMPANY_SPECS:
        row = Company(code=code, name=name, is_active=True)
        db.add(row)
        db.flush()
        world.co[key] = row.id

    for key, co_key, code, name in DEPT_SPECS:
        row = Department(code=code, name=name, company_id=world.co[co_key], is_active=True)
        db.add(row)
        db.flush()
        world.dept[key] = row.id

    for key, co_key, dept_key, has_account in EMPLOYEE_SPECS:
        emp = Employee(code=key.upper(), full_name=f"Nhân sự {key}",
                       company_id=world.co[co_key] if co_key else 0,
                       department_id=world.dept[dept_key] if dept_key else 0,
                       is_active=True)
        db.add(emp)
        db.flush()
        world.emp[key] = emp.id
        if not has_account:
            continue
        user = User(email=key, employee_id=emp.id, password_hash="x", is_active=True)
        db.add(user)
        db.flush()
        world._actors[key] = Actor(world, key, user, emp)
        perm_cache_clear(user.id)

    db.commit()
    return world
