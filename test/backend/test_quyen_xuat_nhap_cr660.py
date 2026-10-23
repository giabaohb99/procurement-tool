"""duoc-CR-660 (HR1-1 + NT1-1) — bảo mật XUẤT / NHẬP file danh mục và nhân sự.

Kiểm:
- cổng xuất CSV/XLSX đòi `export` (chỉ có `read` -> 403), dòng xuất bó theo phạm vi của quyền XUẤT;
- cổng nhập CSV của từng danh mục đòi `import` (chỉ có `write`/`create` -> 403);
- `import` nằm trong ACTIONS, ma trận quyền trả cột «Nhập», admin được seed đủ quyền mới;
- cột nhạy cảm của nhân sự bị che (ô rỗng) với người thiếu `employee_sensitive.read`, ở cả CSV, XLSX
  lẫn xuất tập trung; ngoại lệ `self`.
"""
from datetime import date
from io import BytesIO

import openpyxl
import pytest

from app.core.permissions import ACTIONS, ACTION_LABELS
from hdld_factory import client_as  # noqa: F401

CSV = "text/csv"


def _csv_rows(res) -> list[list[str]]:
    import csv
    from io import StringIO
    return list(csv.reader(StringIO(res.content.decode("utf-8-sig"))))


# ── ACTIONS / ma trận / seed ─────────────────────────────────────────────────────────
def test_import_la_hanh_dong_cuoi_va_co_nhan():
    assert ACTIONS[-1] == "import" and ACTION_LABELS["import"] == "Nhập"


def test_ma_tran_quyen_tra_cot_nhap(world, client_as):  # noqa: F811
    world.grant("a1", "role", "all", actions=("read",))
    meta = client_as(world.actor("a1")).get("/api/roles/meta").json()["data"]
    assert {"key": "import", "label": "Nhập"} in meta["actions"]


def test_admin_duoc_seed_du_quyen_nhap(db):
    from app.core.permissions import ENTITIES
    from app.modules.role.model import Permission
    from app.seed import ensure_admin_role

    admin = ensure_admin_role(db)
    rows = db.query(Permission).filter(Permission.role_id == admin.id).all()
    assert len(rows) >= len(ENTITIES) and all(p.can_import and p.can_export for p in rows)


def test_luu_ma_tran_giu_co_nhap(db, world, client_as):  # noqa: F811
    from app.modules.role.model import Permission, Role
    world.grant("a1", "role", "all", actions=("read", "write"))
    world.grant("a1", "unit", "all", actions=("read", "import"))   # không được cấp quyền mình không có
    role = Role(code="VT_NHAP", name="Vai trò nhập")
    db.add(role)
    db.commit()
    body = {"permissions": [{"entity": "unit", "can_read": True, "can_import": True, "scope": "all"}]}
    res = client_as(world.actor("a1")).put(f"/api/roles/{role.id}/permissions", json=body)
    assert res.status_code == 200, res.text
    assert db.query(Permission).filter_by(role_id=role.id, entity="unit").one().can_import is True
    got = client_as(world.actor("a1")).get(f"/api/roles/{role.id}/permissions").json()["data"]
    assert got[0]["can_import"] is True


# ── Cổng xuất: nhân sự ───────────────────────────────────────────────────────────────
@pytest.mark.parametrize("path", ["/api/employees/export/csv", "/api/employees/export/xlsx"])
def test_xuat_nhan_su_chi_co_read_bi_403(world, client_as, path):  # noqa: F811
    world.grant("a1", "employee", "all", actions=("read",))
    assert client_as(world.actor("a1")).get(path).status_code == 403


def test_xuat_csv_nhan_su_chi_ra_dong_trong_pham_vi(world, client_as):  # noqa: F811
    world.grant("a1", "employee", "company", actions=("read", "export"))
    res = client_as(world.actor("a1")).get("/api/employees/export/csv")
    assert res.status_code == 200
    codes = {r[0] for r in _csv_rows(res)[1:]}
    assert "A1" in codes and "B1" not in codes     # b1 thuộc pháp nhân B


def test_pham_vi_xuat_tinh_theo_quyen_xuat_khong_theo_quyen_xem(world, client_as):  # noqa: F811
    """read=toàn bộ nhưng export chỉ phạm vi `own` -> tệp chỉ có dòng của mình, không phình theo `read`."""
    a1 = world.actor("a1")
    a1.grant("employee", "all", actions=("read",))
    a1.grant("employee", "own", actions=("export",))
    codes = {r[0] for r in _csv_rows(client_as(a1).get("/api/employees/export/csv"))[1:]}
    assert "B1" not in codes and "A3" not in codes


def test_xuat_xlsx_nhan_su_chi_ra_dong_trong_pham_vi(world, client_as):  # noqa: F811
    world.grant("a1", "employee", "company", actions=("read", "export"))
    res = client_as(world.actor("a1")).get("/api/employees/export/xlsx")
    assert res.status_code == 200
    codes = {r[0] for r in openpyxl.load_workbook(BytesIO(res.content)).active.iter_rows(min_row=2, values_only=True)}
    assert "A1" in codes and "B1" not in codes


# ── Che cột nhạy cảm khi xuất ────────────────────────────────────────────────────────
def _rows_with_secret(db, world):
    from app.modules.employee.model import Employee
    for key in ("a1", "a2"):
        emp = db.get(Employee, world.emp[key])
        emp.bank_account_no, emp.date_of_birth = f"STK-{key}", date(1990, 1, 2)
    db.commit()


def test_mask_export_rows_che_theo_danh_sach_sensitive_fields(db, world):
    from app.core.scoping import get_perm_profile
    from app.modules.employee.export_mask import mask_export_rows
    from app.modules.employee.sensitive import SENSITIVE_FIELDS

    world.grant("a1", "employee", "all", actions=("read", "export"))
    profile = get_perm_profile(db, world.actor("a1").user)
    row = {f: "x" for f in SENSITIVE_FIELDS} | {"code": "A2", "full_name": "Tên"}
    out = mask_export_rows([row], [world.emp["a2"]], profile)[0]
    assert all(out[f] in ("", None) for f in SENSITIVE_FIELDS), "mọi trường trong SENSITIVE_FIELDS đều che"
    assert out["code"] == "A2" and out["full_name"] == "Tên", "cột thường giữ nguyên"


def test_mask_export_rows_giu_du_voi_nguoi_co_quyen_nhay_cam_va_chinh_chu(db, world):
    from app.core.scoping import get_perm_profile
    from app.modules.employee.export_mask import mask_export_rows

    world.grant("a1", "employee", "all", actions=("read", "export"))       # a1: KHÔNG có quyền nhạy cảm
    world.grant("a2", "employee_sensitive", "all", actions=("read",))      # a2: có
    p1 = get_perm_profile(db, world.actor("a1").user)
    p2 = get_perm_profile(db, world.actor("a2").user)
    mk = lambda: [{"bank_account_no": "S1"}, {"bank_account_no": "S2"}]   # noqa: E731
    ids = [world.emp["a1"], world.emp["a3"]]
    assert [r["bank_account_no"] for r in mask_export_rows(mk(), ids, p1)] == ["S1", ""]   # self giữ, người khác che
    assert [r["bank_account_no"] for r in mask_export_rows(mk(), ids, p2)] == ["S1", "S2"]


def test_doi_tuong_xuat_csv_che_cot_nhay_cam(db, world):
    """`masked_row_objects` (đường CSV): thêm cột nhạy cảm vào bộ cột thì người thiếu quyền nhận ô rỗng."""
    from app.core.scoping import get_perm_profile
    from app.modules.employee import export_mask
    from app.modules.employee.model import Employee
    _rows_with_secret(db, world)
    world.grant("a3", "employee", "company", actions=("read", "export"))   # không có employee_sensitive
    world.grant("a1", "employee", "company", actions=("read", "export"))
    world.grant("a1", "employee_sensitive", "all", actions=("read",))
    items = db.query(Employee).filter(Employee.id.in_([world.emp["a1"], world.emp["a2"]])).order_by(Employee.id).all()
    keys = ["code", "bank_account_no", "date_of_birth"]
    low = export_mask.masked_row_objects(items, keys, get_perm_profile(db, world.actor("a3").user))
    high = export_mask.masked_row_objects(items, keys, get_perm_profile(db, world.actor("a1").user))
    assert [o.bank_account_no for o in low] == ["", ""] and [o.date_of_birth for o in low] == [None, None]
    assert [o.bank_account_no for o in high] == ["STK-a1", "STK-a2"]
    assert [o.code for o in low] == ["A1", "A2"]


def test_xuat_tap_trung_che_cot_nhay_cam(db, world, monkeypatch):
    from app.core.export_xlsx import Col
    from app.modules.export_log import registry, service
    _rows_with_secret(db, world)
    cols = registry.EXPORT_ADAPTERS["employee"]["columns"] + [Col("bank_account_no", "Số TK", width=16)]
    monkeypatch.setitem(registry.EXPORT_ADAPTERS["employee"], "columns", cols)
    monkeypatch.setattr(service, "_store_file", lambda *a, **k: 0)
    world.grant("a3", "employee", "company", actions=("read", "export"))
    world.grant("a1", "employee", "company", actions=("read", "export"))
    world.grant("a1", "employee_sensitive", "all", actions=("read",))

    def stk(key):
        content, *_ = service.run_export(db, world.actor(key).user, "employee", "csv")
        rows = _csv_rows(type("R", (), {"content": content}))
        i = rows[0].index("Số TK")
        return {r[0]: r[i] for r in rows[1:]}

    assert stk("a3")["A2"] == "" and stk("a3")["A1"] == ""
    assert stk("a1")["A2"] == "STK-a2"


# ── Cổng xuất: danh mục viết tay + factory ───────────────────────────────────────────
@pytest.mark.parametrize("entity,path", [
    ("product", "/api/products/export/csv"),
    ("supplier", "/api/suppliers/export/csv"),
    ("department", "/api/departments/export/csv"),
    ("warehouse", "/api/warehouses/export/csv"),       # make_crud_router
])
def test_xuat_danh_muc_chi_co_read_bi_403_co_export_thi_duoc(world, client_as, entity, path):  # noqa: F811
    world.grant("a1", entity, "all", actions=("read",))
    assert client_as(world.actor("a1")).get(path).status_code == 403
    world.grant("a2", entity, "all", actions=("read", "export"))
    assert client_as(world.actor("a2")).get(path).status_code == 200


def test_xuat_phong_ban_chi_ra_dong_trong_pham_vi(world, client_as):  # noqa: F811
    world.grant("a1", "department", "company", actions=("read", "export"))
    res = client_as(world.actor("a1")).get("/api/departments/export/csv")
    from app.modules.department.model import Department
    names = {r[0] for r in _csv_rows(res)[1:]}   # cột 0 = Mã PB (tên có thể trùng giữa hai pháp nhân)
    ten_b = {d.code for d in world.db.query(Department).filter_by(company_id=world.co["B"]).all()}
    ten_a = {d.code for d in world.db.query(Department).filter_by(company_id=world.co["A"]).all()}
    assert ten_a and ten_a <= names and not (ten_b & names), "phòng ban pháp nhân B không lọt vào tệp của người thuộc A"


# ── Cổng nhập ───────────────────────────────────────────────────────────────────────
_CSV_KHO = "Mã,Tên kho,Địa chỉ\nKHO660,Kho CR660,HN\n"


def _upload(client, path, text=_CSV_KHO):
    return client.post(path, files={"file": ("a.csv", text.encode("utf-8"), CSV)})


@pytest.mark.parametrize("entity,path", [
    ("warehouse", "/api/warehouses/import/csv"),
    ("product", "/api/products/import/csv"),
    ("supplier", "/api/suppliers/import/csv"),
    ("department", "/api/departments/import/csv"),
    ("employee", "/api/employees/import/csv"),
])
def test_nhap_csv_co_write_create_ma_thieu_import_bi_403(world, client_as, entity, path):  # noqa: F811
    world.grant("a1", entity, "all", actions=("read", "create", "write", "delete", "export"))
    assert _upload(client_as(world.actor("a1")), path).status_code == 403


def test_nhap_csv_co_import_thi_qua_cong_kho(db, world, client_as):  # noqa: F811
    from app.modules.catalog.model import Warehouse
    world.grant("a1", "warehouse", "all", actions=("import",))      # CHỈ import, không write
    res = _upload(client_as(world.actor("a1")), "/api/warehouses/import/csv")
    assert res.status_code == 200, res.text
    assert db.query(Warehouse).filter_by(code="KHO660").count() == 1


@pytest.mark.parametrize("path", ["/api/products/import/csv", "/api/suppliers/import/csv"])
def test_nhap_csv_san_pham_ncc_co_import_qua_cong(world, client_as, path):  # noqa: F811
    world.grant("a1", "product", "all", actions=("import",))
    world.grant("a1", "supplier", "all", actions=("import",))
    res = _upload(client_as(world.actor("a1")), path, "Mã\n")
    assert res.status_code != 403


@pytest.mark.parametrize("entity,path", [("department", "/api/departments/import/csv"),
                                         ("employee", "/api/employees/import/csv")])
def test_nhap_csv_da_ngung_van_tra_410_khi_du_quyen(world, client_as, entity, path):  # noqa: F811
    world.grant("a1", entity, "all", actions=("import",))
    assert _upload(client_as(world.actor("a1")), path).status_code == 410


def test_nhap_csv_khong_ghi_de_ban_ghi_ngoai_pham_vi_import(db, world, client_as):  # noqa: F811
    """Phạm vi cổng nhập tính theo quyền NHẬP: dòng trỏ vào mã đã có mà ngoài phạm vi thì bị bỏ qua."""
    from app.modules.catalog.model import Warehouse
    db.add(Warehouse(code="KHO660", name="Tên cũ", is_active=True))
    db.commit()
    world.grant("a1", "warehouse", "all", actions=("read", "write"))     # có write nhưng KHÔNG import
    assert _upload(client_as(world.actor("a1")), "/api/warehouses/import/csv").status_code == 403
    assert db.query(Warehouse).filter_by(code="KHO660").one().name == "Tên cũ"


def test_xuat_tap_trung_pham_vi_theo_quyen_xuat(db, world, monkeypatch):
    """`/api/exports/run` gác `export` thì phạm vi cũng phải theo grant `export`, không phình theo `read`."""
    from app.modules.export_log import service
    monkeypatch.setattr(service, "_store_file", lambda *a, **k: 0)
    a1 = world.actor("a1")
    a1.grant("employee", "all", actions=("read",))
    a1.grant("employee", "own", actions=("export",))
    content, *_ = service.run_export(db, a1.user, "employee", "csv")
    codes = {r[0] for r in _csv_rows(type("R", (), {"content": content}))[1:]}
    assert "B1" not in codes and "A3" not in codes


def test_tai_lai_tep_da_xuat_chi_nguoi_xuat_hoac_quyen_xuat_toan_he(db, world):
    """Review H1: tệp lưu là ảnh chụp theo quyền NGƯỜI XUẤT. Trước đây ai có `export` trên BẤT KỲ bảng nào cũng tải lại được
    tệp nhân sự HR xuất phạm vi «tất cả». Nay: người xuất, hoặc `export` toàn hệ trên đúng bảng (+ nhạy cảm toàn hệ với nhân sự)."""
    from types import SimpleNamespace

    from app.core.auth import perm_cache_clear
    from app.modules.export_log import service
    hr, other = world.actor("a1"), world.actor("a2")
    x = SimpleNamespace(created_by=hr.user.id, entity="employee")
    assert service.can_download(db, hr.user, x)                          # người xuất
    other.grant("seal_type", "all", actions=("export",))
    assert not service.can_download(db, other.user, x)                   # export bảng khác: KHÔNG
    other.grant("employee", "own", actions=("export",))
    perm_cache_clear(other.user.id)
    assert not service.can_download(db, other.user, x)                   # export nhân sự hẹp hơn: KHÔNG
    other.grant("employee", "all", actions=("export",))
    perm_cache_clear(other.user.id)
    assert not service.can_download(db, other.user, x)                   # thiếu nhạy cảm toàn hệ: KHÔNG
    other.grant("employee_sensitive", "all", actions=("read",))
    perm_cache_clear(other.user.id)
    assert service.can_download(db, other.user, x)
    assert service.can_download(db, other.user, SimpleNamespace(created_by=hr.user.id, entity="employee_x")) is False
