"""Trợ lý AI / cổng MCP khớp thay đổi Nhân sự 29/10/2026 (duoc-CR-692 … 694).

Canh:
  - LƯƠNG trên hồ sơ (CR-693) không ra khỏi `employee_lookup` — kể cả khi người hỏi là CHÍNH CHỦ (chủ trương: trợ lý
    không đọc lương) — và tool không có tham số lọc / sắp xếp nào chạm tới lương;
  - không bộ dữ liệu `dataset_query` nào đọc bảng nhân sự (đường lọc / gom theo lương);
  - `report_summary`: khóa 21 Quỹ lương ĐÓNG, khóa 25 (đã bỏ, CR-692) không còn; gọi bằng số / tên trả `denied` kèm lý do;
  - số điện thoại khác (CR-694) trả kèm `phone`, chỉ hai khóa `number` / `label`, tìm được theo số phụ;
  - cẩm nang `60-nhan-su-ho-so.md` nói đúng ba điều trên.
"""
from app.core.report_keys import RETIRED_REPORT_KEYS, ReportKey
from app.modules.assistant import tools as T
from app.modules.assistant.tools import employee_tool as et
from app.modules.assistant.tools import report_summary_tool as rs
from app.modules.employee.model import Employee
from app.modules.user.model import User


def _luong(db, emp_id: int, salary: int = 25_000_000, allowance: int = 3_000_000) -> Employee:
    emp = db.get(Employee, emp_id)
    emp.salary_monthly = salary
    emp.allowance_monthly = allowance
    db.commit()
    return emp


# ── Lương (CR-693) ────────────────────────────────────────────────────────────

def test_danh_sach_trang_khong_co_truong_luong():
    assert not set(et.NEVER_FIELDS) & set(et._OUT_FIELDS)
    props = set(et.EMPLOYEE_LOOKUP_SPEC.parameters["properties"])
    assert props == {"query", "department_id", "active_only", "limit"}   # không lọc / sắp xếp theo lương


def test_chinh_chu_hoi_cung_khong_ra_luong(db, seed, cap_quyen):
    """Người hỏi tra ĐÚNG hồ sơ của mình: `sensitive.mask` sẽ mở lương cho chính chủ, nhưng tool không chép trường đó."""
    cap_quyen(seed.u_req_id, "employee", scope="all", read=True)
    _luong(db, seed.emp_req_id)
    out = T.run_tool(db, db.get(User, seed.u_req_id), "employee_lookup", {"query": seed.emp_req_code})
    assert out["total"] == 1
    row = out["items"][0]
    for f in et.NEVER_FIELDS:
        assert f not in row
    assert "25000000" not in str(out) and "3000000" not in str(out)


def test_nguoi_khac_khong_ra_luong(db, seed, cap_quyen):
    cap_quyen(seed.u_req_id, "employee", scope="all", read=True)
    cap_quyen(seed.u_req_id, "employee_sensitive", scope="all", read=True)
    _luong(db, seed.emp_nstm_id, salary=31_000_000)
    out = T.run_tool(db, db.get(User, seed.u_req_id), "employee_lookup", {"query": seed.emp_nstm_code})
    assert out["total"] == 1 and "31000000" not in str(out)


def test_khong_bo_du_lieu_nao_doc_bang_nhan_su():
    from app.modules.assistant.datasets import registry

    assert all(ds.model is not Employee for ds in registry().values())


# ── Báo cáo (CR-688 / 692 / 693) ──────────────────────────────────────────────

def test_quy_luong_dong_va_khoa_25_da_bo():
    assert ReportKey.PAYROLL_FUND in rs.CLOSED_FOR_AI
    assert ReportKey.PAYROLL_FUND not in {r.key for r in rs.REPORTS.values()}
    assert 25 in RETIRED_REPORT_KEYS and 25 not in {int(k) for k in ReportKey}
    assert "Quỹ lương" not in rs.REPORT_SUMMARY_SPEC.description
    assert "payroll_fund" not in rs.REPORT_SUMMARY_SPEC.parameters["properties"]["report_key"]["enum"]
    for raw in ("21", 21, "payroll_fund", "25"):
        assert rs.resolve_report_key(raw) is None


def test_goi_khoa_dong_tra_denied_kem_ly_do(db, seed):
    user = db.get(User, seed.u_req_id)
    out = T.run_tool(db, user, "report_summary", {"report_key": "21"})
    assert out["denied"] is True and "Quỹ lương" in out["error"] and "không đọc lương" in out["error"]
    out = T.run_tool(db, user, "report_summary", {"report_key": "payroll_fund"})
    assert out["denied"] is True
    out = T.run_tool(db, user, "report_summary", {"report_key": 25})
    assert out["denied"] is True and "ngừng dùng" in out["error"]


# ── Nhiều số điện thoại (CR-694) ──────────────────────────────────────────────

def test_tra_so_phu_kem_nhan_va_tim_theo_so_phu(db, seed, cap_quyen):
    cap_quyen(seed.u_req_id, "employee", scope="all", read=True)
    emp = db.get(Employee, seed.emp_nstm_id)
    emp.phone = "0900000001"
    emp.phone_label = "Cá nhân"
    emp.extra_phones = [{"number": "0912 345 678", "label": "Zalo", "rac": "x"}, {"number": "", "label": "rỗng"}]
    db.commit()
    user = db.get(User, seed.u_req_id)

    out = T.run_tool(db, user, "employee_lookup", {"query": "0912 345"})
    assert [r["code"] for r in out["items"]] == [seed.emp_nstm_code]
    row = out["items"][0]
    assert row["phone"] == "0900000001" and row["phone_label"] == "Cá nhân"
    assert row["extra_phones"] == [{"number": "0912 345 678", "label": "Zalo"}]

    #  Từ khóa chữ không quét JSON số phụ (chữ «label» / «Zalo» nằm trong chính JSON).
    assert T.run_tool(db, user, "employee_lookup", {"query": "Zalo"})["total"] == 0


def test_mo_ta_cong_cu_noi_ro_so_phu_va_luong():
    desc = et.EMPLOYEE_LOOKUP_SPEC.description
    assert "extra_phones" in desc and "phone_label" in desc and "chính người hỏi" in desc


# ── Cẩm nang ──────────────────────────────────────────────────────────────────

def test_cam_nang_nhan_su_khop_chu_truong():
    from app.modules.ai_skill.handbook_seed import seed_files

    body = next(b for slug, _t, _s, b in seed_files() if slug == "nhan-su-ho-so")
    assert "kể cả của chính người hỏi" in body
    assert "chỉ chính nhân sự đó xem được" in body
    assert "Nhiều số điện thoại" in body and "extra_phones" in body
    assert "Kế hoạch nhân sự — ĐÃ BỎ" in body
