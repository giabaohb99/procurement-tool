"""Dời dữ liệu đợt 4 + gieo dữ liệu gợi ý cho kế hoạch nhân sự theo kỳ (duoc-CR-690). Gọi từ migration `hcplan02`.

Dùng bảng nhẹ `sa.table(...)` (KHÔNG import model) để migration không vỡ khi model đổi về sau; nhận một `Connection`
nên bài kiểm chạy được trên SQLite. Cả hai hàm đều IDEMPOTENT. Tiếng Việt đi qua tham số SQLAlchemy (không `mysql -e`).
"""
import sqlalchemy as sa

from app.core.headcount_plan_codes import ActualSource, CostAppliesTo, CostCalcMethod

_AUDIT = ("created_by", "updated_by")


def _t(name: str, *cols: sa.Column) -> sa.TableClause:
    return sa.table(name, sa.column("id"), *cols)


PLAN = _t("tab_headcount_plan", sa.column("planned_headcount"), sa.column("planned_payroll_monthly"))
LINE = _t("tab_headcount_plan_line", sa.column("plan_id"), sa.column("position_id"), sa.column("headcounts", sa.JSON),
          sa.column("amounts", sa.JSON), sa.column("note"), *map(sa.column, _AUDIT))
_ITEM_COLS = ("code", "name", "group_id", "calc_method", "rate", "factor", "cap_amount", "amount", "applies_to",
              "actual_source", "sort_order")
_ITEM_JSON = ("base_codes", "position_ids", "months")


def _item_table(name: str, parent: str) -> sa.TableClause:
    return _t(name, sa.column(parent), *map(sa.column, _ITEM_COLS), *(sa.column(c, sa.JSON) for c in _ITEM_JSON),
              *map(sa.column, _AUDIT))


PLAN_ITEM = _item_table("tab_headcount_plan_cost_item", "plan_id")
TEMPLATE_ITEM = _item_table("tab_hr_cost_template_item", "template_id")
GROUP = _t("tab_hr_cost_group", sa.column("name"), sa.column("sort_order"), sa.column("is_active"), *map(sa.column, _AUDIT))
TEMPLATE = _t("tab_hr_cost_template", sa.column("name"), sa.column("note"), sa.column("is_active"), *map(sa.column, _AUDIT))

LEGACY_ITEM_CODE = "QUY_LUONG"
LEGACY_ITEM_NAME = "Quỹ lương (nhập tổng)"
SUGGESTED_GROUPS = ("Quỹ lương", "Bắt buộc theo luật", "Phúc lợi", "Khác")
SUGGESTED_TEMPLATE = "Mẫu gợi ý"
SUGGESTED_CAP = 46_800_000   # trần lương đóng BHXH nửa đầu 2026; người dùng tự cập nhật khi luật đổi


def _is_empty(conn: sa.Connection, table: sa.TableClause) -> bool:
    return conn.execute(sa.select(sa.func.count()).select_from(table)).scalar() == 0


def seed_suggestions(conn: sa.Connection) -> None:
    """Nhóm gợi ý + «Mẫu gợi ý» — mỗi loại chỉ gieo khi bảng còn RỖNG (xóa / sửa thoải mái, không gieo lại)."""
    if _is_empty(conn, GROUP):
        conn.execute(GROUP.insert(), [{"name": n, "sort_order": (i + 1) * 10, "is_active": True, "created_by": 0,
                                       "updated_by": 0} for i, n in enumerate(SUGGESTED_GROUPS)])
    if not _is_empty(conn, TEMPLATE):
        return
    gid = dict(conn.execute(sa.select(GROUP.c.name, GROUP.c.id)).all())
    conn.execute(TEMPLATE.insert(), {"name": SUGGESTED_TEMPLATE, "is_active": True, "created_by": 0, "updated_by": 0,
                                     "note": "Bộ khoản gợi ý — sửa tự do; con số (tỷ lệ, trần) do người dùng cập nhật khi luật đổi"})
    tid = conn.execute(sa.select(TEMPLATE.c.id).where(TEMPLATE.c.name == SUGGESTED_TEMPLATE)).scalar()
    M, A, S = CostCalcMethod, CostAppliesTo, ActualSource
    wage, law, welfare = gid.get("Quỹ lương", 0), gid.get("Bắt buộc theo luật", 0), gid.get("Phúc lợi", 0)

    def item(code, name, group, method, sort, **kw):
        return {"template_id": tid, "code": code, "name": name, "group_id": group, "calc_method": int(method),
                "rate": 0, "factor": 0, "cap_amount": 0, "amount": 0, "base_codes": [], "position_ids": [],
                "months": [], "applies_to": int(A.ALL_POSITIONS), "actual_source": int(S.NONE), "sort_order": sort,
                "created_by": 0, "updated_by": 0, **kw}

    def insurance(code, name, rate, sort):
        return item(code, name, law, M.PERCENT_OF, sort, rate=rate, base_codes=["LUONG", "PC_BH"],
                    cap_amount=SUGGESTED_CAP, actual_source=int(S.PERCENT_OF_INSURANCE_SALARY))

    conn.execute(TEMPLATE_ITEM.insert(), [
        item("LUONG", "Lương vị trí", wage, M.PER_HEAD_MONTH, 10, actual_source=int(S.BASE_SALARY)),
        item("PC_BH", "PC đóng BH", wage, M.PER_HEAD_MONTH, 20, actual_source=int(S.ALLOWANCE)),
        item("PC_KHONG_BH", "PC không đóng BH", wage, M.PER_HEAD_MONTH, 30),
        insurance("BHXH", "BHXH công ty 17,5%", 17.5, 40),
        insurance("BHYT", "BHYT công ty 3%", 3, 50),
        insurance("BHTN", "BHTN công ty 1%", 1, 60),
        insurance("KPCD", "Kinh phí công đoàn 2%", 2, 70),
        item("THUONG_13", "Thưởng tháng 13", welfare, M.MONTHS_OF, 80, factor=1, base_codes=["LUONG"], months=[12]),
    ])


def move_legacy_rows(conn: sa.Connection) -> int:
    """Mỗi kế hoạch đợt 4 (một dòng năm × pháp nhân × phòng) → kế hoạch loại Năm có: một dòng «Không theo vị trí» với
    định biên 4 quý bằng nhau, và khoản «Quỹ lương (nhập tổng)» cách tính 5 = 12 × quỹ lương / tháng cũ (chia đều 12
    tháng). Chỉ đụng kế hoạch CHƯA có dòng vị trí nào (chạy lại không nhân đôi). Trả số kế hoạch đã dời."""
    has_line = sa.select(LINE.c.plan_id).distinct()
    rows = conn.execute(sa.select(PLAN.c.id, PLAN.c.planned_headcount, PLAN.c.planned_payroll_monthly)
                        .where(PLAN.c.id.not_in(has_line))).all()
    group_id = conn.execute(sa.select(GROUP.c.id).where(GROUP.c.name == SUGGESTED_GROUPS[0])).scalar() or 0
    for plan_id, headcount, payroll in rows:
        n = int(headcount or 0)
        conn.execute(LINE.insert(), {"plan_id": plan_id, "position_id": 0, "headcounts": [n, n, n, n], "amounts": {},
                                     "note": "", "created_by": 0, "updated_by": 0})
        conn.execute(PLAN_ITEM.insert(), {
            "plan_id": plan_id, "code": LEGACY_ITEM_CODE, "name": LEGACY_ITEM_NAME, "group_id": group_id,
            "calc_method": int(CostCalcMethod.LUMP_SUM), "rate": 0, "factor": 0, "cap_amount": 0,
            "amount": 12 * int(payroll or 0), "base_codes": [], "position_ids": [], "months": [],
            "applies_to": int(CostAppliesTo.WHOLE_DEPARTMENT), "actual_source": int(ActualSource.NONE),
            "sort_order": 10, "created_by": 0, "updated_by": 0})
    return len(rows)
