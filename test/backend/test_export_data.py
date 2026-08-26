"""Test Đ-13b — Xuất dữ liệu tập trung + ghi nhật ký.

Gọi thẳng `export_log.service` trên DB SQLite in-memory: liệt kê bảng theo quyền,
chạy xuất CSV/XLSX (đếm dòng + ghi ExportLog), và khẳng định `apply_scope` chặn khi
không có grant.
"""
from types import SimpleNamespace

from app.modules.company.model import Company
from app.modules.employee.model import Employee
from app.modules.export_log import service
from app.modules.export_log.model import ExportLog


def test_available_entities_chi_hien_bang_co_quyen_export(db, seed, cap_quyen):
    user = SimpleNamespace(id=seed.u_req_id)
    cap_quyen(seed.u_req_id, "department", scope="all", export=True)
    avail = service.available_entities(db, user)
    assert [a["entity"] for a in avail] == ["department"]
    assert avail[0]["label"] == "Phòng ban"


def test_run_export_csv_ghi_log_va_dem_dung(db, seed, cap_quyen):
    user = SimpleNamespace(id=seed.u_req_id)
    cap_quyen(seed.u_req_id, "employee", scope="all", read=True, export=True)
    total_emp = db.query(Employee).count()

    content, filename, media, n = service.run_export(db, user, "employee", "csv")

    assert content[:3] == b"\xef\xbb\xbf"   # BOM utf-8-sig để Excel mở đúng tiếng Việt
    assert n == total_emp and n > 0
    assert filename.endswith(".csv") and "csv" in media

    logs = db.query(ExportLog).filter(ExportLog.entity == "employee").all()
    assert len(logs) == 1
    assert logs[0].fmt == "csv"
    assert logs[0].row_count == total_emp
    assert logs[0].created_by == seed.u_req_id
    assert logs[0].file_size == len(content)


def test_run_export_xlsx_tra_file_hop_le(db, seed, cap_quyen):
    user = SimpleNamespace(id=seed.u_req_id)
    cap_quyen(seed.u_req_id, "company", scope="all", read=True, export=True)

    content, filename, _media, _n = service.run_export(db, user, "company", "xlsx")

    assert content[:2] == b"PK"   # .xlsx là zip, bắt đầu bằng 'PK'
    assert filename.endswith(".xlsx")
    assert db.query(Company).count() >= 1


def test_registry_du_bang_va_gom_dung_phan_he(db):
    from app.modules.export_log.registry import EXPORT_ADAPTERS
    # 3 hr + 3 thu mua + 4 sản xuất + 1 kho = 11 (CR-174)
    assert len(EXPORT_ADAPTERS) == 11
    mods = {a["module"] for a in EXPORT_ADAPTERS.values()}
    assert mods == {"hr", "procurement", "production", "inventory"}
    # Bảng nào cũng phải khai model + scope + ít nhất một cột.
    for e, a in EXPORT_ADAPTERS.items():
        assert a["model"] is not None and a["scope"] and a["columns"], e


def test_scope_chan_khi_khong_co_grant_tren_bang_do(db, seed, cap_quyen):
    # Có quyền trên company nhưng KHÔNG có grant nào trên employee → apply_scope
    # trả về rỗng (chặn hết), nên xuất ra 0 dòng — không rò dữ liệu ngoài phạm vi.
    user = SimpleNamespace(id=seed.u_req_id)
    cap_quyen(seed.u_req_id, "company", scope="all", read=True, export=True)

    _c, _f, _m, n = service.run_export(db, user, "employee", "csv")
    assert n == 0
