"""duoc-CR-675 — ép tải duoc-CR-660 (cổng xuất / nhập, che cột nhạy cảm khi xuất nhân sự).

Bài kiểm CR-660 phủ đúng / sai từng cổng đã biết. Tệp này đánh vào chỗ chúng chưa đụng:
- QUÉT HẾT `app.routes`: người có mọi quyền TRỪ Xuất / Nhập gọi MỌI đường `…/export/csv|xlsx` và
  `…/import/csv` → phải 403. Thêm danh mục mới mà quên gác thì bài này đỏ, không cần ai nhớ thêm dòng.
- KHỐI LƯỢNG: xuất vài nghìn hồ sơ — số truy vấn cố định (không N+1), che đúng từng dòng, chỉ dòng
  của chính người xuất là đủ, thời gian trong trần.
"""
import time
from datetime import date

import pytest
from fastapi.routing import APIRoute
from sqlalchemy import event

from app.core.permissions import ACTIONS, ENTITIES
from app.main import app
from hdld_factory import client_as  # noqa: F401

NON_EXPORT_ACTIONS = tuple(a for a in ACTIONS if a not in ("export", "import"))


def _routes(method: str, suffixes: tuple[str, ...]) -> list[str]:
    out = []
    for r in app.routes:
        if isinstance(r, APIRoute) and method in r.methods and r.path.endswith(suffixes) and "{" not in r.path:
            out.append(r.path)
    return sorted(set(out))


EXPORT_PATHS = _routes("GET", ("/export/csv", "/export/xlsx"))
IMPORT_PATHS = _routes("POST", ("/import/csv",))


def test_quet_duoc_du_so_duong_khong_rong():
    #  Chốt đáy: bộ lọc tên đường hỏng (đổi quy ước đặt tên) thì hai bài quét bên dưới xanh rỗng.
    assert len(EXPORT_PATHS) >= 25 and len(IMPORT_PATHS) >= 15, (len(EXPORT_PATHS), len(IMPORT_PATHS))
    assert "/api/employees/export/csv" in EXPORT_PATHS and "/api/products/import/csv" in IMPORT_PATHS


@pytest.fixture
def full_but_export(db, world):
    """a1 có MỌI hành động trừ Xuất / Nhập, phạm vi «tất cả», trên MỌI bảng — một vai trò duy nhất."""
    from app.core.auth import perm_cache_clear
    from app.modules.role.model import Permission, Role
    from app.modules.user.model import UserRole

    actor = world.actor("a1")
    role = Role(code="VT_DU_TRU_XUAT", name="Đủ quyền trừ xuất nhập")
    db.add(role)
    db.flush()
    for entity in ENTITIES:
        db.add(Permission(role_id=role.id, entity=entity, scope="all",
                          **{f"can_{a}": True for a in NON_EXPORT_ACTIONS}))
    db.add(UserRole(user_id=actor.user.id, role_id=role.id))
    db.commit()
    perm_cache_clear(actor.user.id)
    return actor


def test_moi_duong_xuat_deu_doi_quyen_xuat(full_but_export, client_as):  # noqa: F811
    c = client_as(full_but_export)
    leaks = {p: r.status_code for p in EXPORT_PATHS if (r := c.get(p)).status_code != 403}
    assert not leaks, f"đường xuất KHÔNG đòi quyền Xuất: {leaks}"


def test_moi_duong_nhap_csv_deu_doi_quyen_nhap(full_but_export, client_as):  # noqa: F811
    c = client_as(full_but_export)
    files = {"file": ("x.csv", "Mã,Tên\nX675,Thử\n".encode("utf-8"), "text/csv")}
    leaks = {p: r.status_code for p in IMPORT_PATHS if (r := c.post(p, files=files)).status_code != 403}
    assert not leaks, f"đường nhập CSV KHÔNG đòi quyền Nhập: {leaks}"


# ── Khối lượng: xuất nhân sự vài nghìn dòng ──────────────────────────────────────────

def _bulk_employees(db, world, n: int, start: int = 0):
    from app.modules.employee.model import Employee
    co = world.co[next(iter(world.co))]
    db.add_all([Employee(code=f"KL{start + i:05d}", full_name=f"Khối lượng {start + i}", company_id=co,
                         department_id=0, is_active=True, bank_account_no=f"STK{start + i}",
                         date_of_birth=date(1990, 1, 1)) for i in range(n)])
    db.commit()


def _count_queries(db, fn) -> int:
    seen = []

    def on(conn, cursor, statement, *a):  # noqa: ARG001
        seen.append(statement)

    engine = db.get_bind()
    event.listen(engine, "before_cursor_execute", on)
    try:
        fn()
    finally:
        event.remove(engine, "before_cursor_execute", on)
    return len(seen)


def _csv(res) -> list[list[str]]:
    import csv
    from io import StringIO
    return list(csv.reader(StringIO(res.content.decode("utf-8-sig"))))


@pytest.mark.parametrize("path", ["/api/employees/export/csv", "/api/employees/export/xlsx",
                                  "/api/exports/run?entity=employee&format=csv"])
def test_xuat_nhan_su_so_truy_van_co_dinh_khi_tang_dong(db, world, client_as, monkeypatch, path):  # noqa: F811
    """Cột «Phòng ban» / «Công ty» đọc qua quan hệ: không nạp trước thì MỖI dòng một truy vấn (2000 dòng = 2000 lượt
    hỏi DB cho một lần bấm Xuất). Số truy vấn phải bằng nhau dù 50 hay 2000 dòng."""
    from app.modules.export_log import service
    monkeypatch.setattr(service, "_store_file", lambda *a, **k: 0)
    world.grant("a1", "employee", "all", actions=("read", "export"))
    c = client_as(world.actor("a1"))
    assert c.get(path).status_code == 200                 # làm nóng cache hồ sơ quyền
    _bulk_employees(db, world, 50)
    q50 = _count_queries(db, lambda: c.get(path))
    _bulk_employees(db, world, 1950, start=50)
    q2000 = _count_queries(db, lambda: c.get(path))
    assert q50 == q2000, f"N+1: {q50} truy vấn với 50 dòng, {q2000} với 2000 dòng"


def test_xuat_tap_trung_2000_dong_che_dung_tung_dong_va_trong_tran_thoi_gian(db, world, monkeypatch):
    """Cột nhạy cảm (Số TK) được thêm vào bộ xuất: người thiếu quyền nhạy cảm nhận ô rỗng ở MỌI dòng trừ dòng của
    chính mình; người có quyền nhận đủ. Đo luôn thời gian để thấy chốt che không đội giá lên."""
    from app.core.export_xlsx import Col
    from app.modules.employee.model import Employee
    from app.modules.export_log import registry, service

    cols = registry.EXPORT_ADAPTERS["employee"]["columns"] + [Col("bank_account_no", "Số TK", width=16)]
    monkeypatch.setitem(registry.EXPORT_ADAPTERS["employee"], "columns", cols)
    monkeypatch.setattr(service, "_store_file", lambda *a, **k: 0)
    _bulk_employees(db, world, 2000)
    me = world.actor("a3")
    db.get(Employee, me.employee.id).bank_account_no = "STK-CUA-TOI"
    db.commit()
    world.grant("a3", "employee", "all", actions=("read", "export"))
    world.grant("a1", "employee", "all", actions=("read", "export"))
    world.grant("a1", "employee_sensitive", "all", actions=("read",))

    def stk(key) -> tuple[dict[str, str], float]:
        t0 = time.perf_counter()
        content, *_ = service.run_export(db, world.actor(key).user, "employee", "csv")
        took = time.perf_counter() - t0
        rows = _csv(type("R", (), {"content": content}))
        i = rows[0].index("Số TK")
        return {r[0]: r[i] for r in rows[1:]}, took

    low, t_low = stk("a3")
    high, t_high = stk("a1")
    assert len(low) >= 2000 and len(high) == len(low)
    filled = {code: v for code, v in low.items() if v}
    assert filled == {me.employee.code: "STK-CUA-TOI"}, "chỉ dòng của chính người xuất còn số tài khoản"
    assert all(high[f"KL{i:05d}"] == f"STK{i}" for i in range(2000)), "người có quyền nhạy cảm nhận đủ"
    #  Trần rộng (SQLite trong container, máy yếu) — mục đích là bắt chốt che chạy theo bậc hai, không phải đo tinh.
    assert t_low < 10 and t_high < 10, (t_low, t_high)
    assert t_low < t_high * 3 + 1, f"che cột làm chậm bất thường: {t_low:.2f}s so với {t_high:.2f}s"


def test_xuat_excel_dat_xe_pham_vi_theo_quyen_xuat(db, world, client_as):  # noqa: F811
    """Xem «tất cả» nhưng Xuất chỉ «của tôi» → tệp chỉ có phiếu của mình, không phình theo quyền Xem."""
    import io

    import openpyxl
    from app.modules.vehicle_booking.model import VehicleBooking

    a1, a2 = world.actor("a1"), world.actor("a2")
    for actor, code in ((a1, "DX-A1"), (a2, "DX-A2")):
        db.add(VehicleBooking(code=code, requester_id=actor.user.id, purpose="Thử CR-675", created_by=actor.user.id))
    db.commit()
    a1.grant("vehicle_booking", "all", actions=("read",))
    a1.grant("vehicle_booking", "own", actions=("export",))
    res = client_as(a1).get("/api/vehicle-bookings/export/xlsx")
    assert res.status_code == 200, res.text
    ws = openpyxl.load_workbook(io.BytesIO(res.content)).active
    codes = {r[0] for r in ws.iter_rows(min_row=2, values_only=True) if r and r[0]}
    assert "DX-A1" in codes and "DX-A2" not in codes, codes
