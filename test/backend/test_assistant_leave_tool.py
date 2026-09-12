"""Tool nghỉ phép của Trợ lý AI — `my_leave_summary` (T35).

Bốn điều phải đúng, mỗi điều là một lỗ nếu sai:
- Gác `leave_request.read` (cùng khóa với `GET /leave-requests/tools/my-balance`).
- CHỈ đơn của chính người hỏi theo `employee_id`; đơn mình LẬP HỘ người khác KHÔNG lọt
  ra — đó là dữ liệu nghỉ phép của người ta, mà tool này không đi qua `apply_scope`.
- Số còn lại lấy từ `LeaveBalance.remaining_days`, có trừ `pending_days` (giữ chỗ).
- Đơn nhiều loại nghỉ phải trả THEO DÒNG; `total_days` đầu đơn là số dẫn xuất.
"""
from datetime import date

from app.modules.assistant import tools as T
from app.modules.leave.balance_model import LeaveBalance
from app.modules.leave.catalog_model import LeaveType
from app.modules.leave.constants import LR_APPROVED, LR_PENDING
from app.modules.leave.request_model import LeaveRequest, LeaveRequestLine
from app.modules.user.model import User

YEAR = 2026


def _tao_du_lieu_nghi_phep(db, seed):
    """2 loại nghỉ · quỹ phép của người hỏi · 3 đơn (2 của mình, 1 lập hộ người khác)."""
    phep_nam = LeaveType(code="ANNUAL", name="Phép năm", is_paid=True, counts_balance=True,
                         annual_quota_days=12, is_active=True)
    khong_luong = LeaveType(code="UNPAID", name="Nghỉ không lương", is_paid=False,
                            counts_balance=True, annual_quota_days=0, is_active=True)
    db.add_all([phep_nam, khong_luong])
    db.flush()

    db.add(LeaveBalance(employee_id=seed.emp_req_id, year=YEAR, leave_type_id=phep_nam.id,
                        company_id=seed.company_id, allocated_days=12, used_days=3,
                        pending_days=2))
    #  Quỹ của NGƯỜI KHÁC cùng năm — không được lọt vào kết quả.
    db.add(LeaveBalance(employee_id=seed.emp_nstm_id, year=YEAR, leave_type_id=phep_nam.id,
                        company_id=seed.company_id, allocated_days=12, used_days=9))

    don_1 = LeaveRequest(code="NP-2026-0001", company_id=seed.company_id,
                         department_id=seed.dept_id, employee_id=seed.emp_req_id,
                         leave_type_id=phep_nam.id, from_date=date(YEAR, 3, 2),
                         to_date=date(YEAR, 3, 4), total_days=3, status=LR_APPROVED,
                         reason="Việc gia đình", created_by=seed.u_req_id)
    don_2 = LeaveRequest(code="NP-2026-0002", company_id=seed.company_id,
                         department_id=seed.dept_id, employee_id=seed.emp_req_id,
                         leave_type_id=phep_nam.id, from_date=date(YEAR, 4, 6),
                         to_date=date(YEAR, 4, 8), total_days=3, status=LR_PENDING,
                         reason="Về quê", created_by=seed.u_req_id)
    #  Người hỏi LẬP HỘ người khác — đơn này là của người ta, không phải "của tôi".
    don_ho = LeaveRequest(code="NP-2026-0003", company_id=seed.company_id,
                          department_id=seed.dept_id, employee_id=seed.emp_nstm_id,
                          leave_type_id=phep_nam.id, from_date=date(YEAR, 5, 4),
                          to_date=date(YEAR, 5, 4), total_days=1, status=LR_PENDING,
                          reason="Khám bệnh", created_by=seed.u_req_id)
    db.add_all([don_1, don_2, don_ho])
    db.flush()

    #  Đơn 2 khai HAI loại nghỉ — hai cột đầu đơn là dẫn xuất.
    db.add_all([
        LeaveRequestLine(request_id=don_2.id, leave_type_id=phep_nam.id, days=2, sort_order=1),
        LeaveRequestLine(request_id=don_2.id, leave_type_id=khong_luong.id, days=1,
                         sort_order=2),
    ])
    db.commit()
    return phep_nam, khong_luong, don_2


def test_missing_permission_is_denied(db, seed):
    _tao_du_lieu_nghi_phep(db, seed)
    out = T.run_tool(db, db.get(User, seed.u_req_id), "my_leave_summary", {"year": YEAR})
    assert out.get("denied") is True
    assert "balances" not in out


def test_balance_is_per_leave_type_and_subtracts_pending(db, seed, cap_quyen):
    cap_quyen(seed.u_req_id, "leave_request", scope="all", read=True)
    _tao_du_lieu_nghi_phep(db, seed)

    out = T.run_tool(db, db.get(User, seed.u_req_id), "my_leave_summary", {"year": YEAR})
    quy = {b["leave_type"]: b for b in out["balances"]}
    assert quy["Phép năm"]["total_days"] == 12
    assert quy["Phép năm"]["used_days"] == 3
    assert quy["Phép năm"]["pending_days"] == 2
    assert quy["Phép năm"]["remaining_days"] == 7      # 12 - 3 - 2, KHÔNG tự cộng trừ chỗ khác
    #  Loại chưa ai cấp quỹ vẫn phải hiện ra, kèm cờ — im lặng bỏ qua thì người
    #  hỏi tưởng công ty không có loại nghỉ đó.
    assert quy["Nghỉ không lương"]["allocated"] is False
    assert quy["Nghỉ không lương"]["remaining_days"] == 0.0


def test_only_own_requests_not_ones_filed_for_others(db, seed, cap_quyen):
    """Quyền scope=all vẫn KHÔNG kéo được đơn của người khác — kể cả đơn chính mình lập hộ."""
    cap_quyen(seed.u_req_id, "leave_request", scope="all", read=True)
    _tao_du_lieu_nghi_phep(db, seed)

    out = T.run_tool(db, db.get(User, seed.u_req_id), "my_leave_summary", {"year": YEAR})
    assert [r["code"] for r in out["requests"]] == ["NP-2026-0002", "NP-2026-0001"]
    assert out["total"] == 2


def test_request_returns_status_code_label_and_type_lines(db, seed, cap_quyen):
    cap_quyen(seed.u_req_id, "leave_request", scope="all", read=True)
    _, _, don_2 = _tao_du_lieu_nghi_phep(db, seed)

    out = T.run_tool(db, db.get(User, seed.u_req_id), "my_leave_summary", {"year": YEAR})
    moi_nhat = out["requests"][0]
    assert moi_nhat["status"] == LR_PENDING          # R2/QĐ-11: cả số...
    assert moi_nhat["status_label"] == "Chờ duyệt"   # ...lẫn nhãn
    assert moi_nhat["url"] == f"/hr/leave-requests/{don_2.id}"
    assert [(d["leave_type"], d["days"]) for d in moi_nhat["lines"]] == [
        ("Phép năm", 2), ("Nghỉ không lương", 1)]


def test_status_filter_and_junk_arguments(db, seed, cap_quyen):
    cap_quyen(seed.u_req_id, "leave_request", scope="all", read=True)
    _tao_du_lieu_nghi_phep(db, seed)
    user = db.get(User, seed.u_req_id)

    da_duyet = T.run_tool(db, user, "my_leave_summary",
                          {"year": YEAR, "status": LR_APPROVED})
    assert [r["code"] for r in da_duyet["requests"]] == ["NP-2026-0001"]

    #  Tham số rác từ model: bỏ lọc / về mặc định, không được nổ.
    rac = T.run_tool(db, user, "my_leave_summary",
                     {"year": "năm nay", "status": "cho-duyet", "limit": "mười"})
    assert rac["year"] != YEAR or rac["total"] == 2
    assert "balances" in rac

    assert T.run_tool(db, user, "my_leave_summary", {"year": YEAR, "limit": 1})["total"] == 1


def test_account_without_employee_profile_gets_soft_error(db, seed, cap_quyen):
    """Tài khoản kỹ thuật chưa gắn nhân sự: báo bằng lời, KHÔNG trả quỹ của `employee_id = 0`."""
    admin = User(email="ADMIN01", employee_id=0, password_hash="x", is_active=True)
    db.add(admin)
    db.commit()
    cap_quyen(admin.id, "leave_request", scope="all", read=True)
    _tao_du_lieu_nghi_phep(db, seed)

    out = T.run_tool(db, admin, "my_leave_summary", {"year": YEAR})
    assert "error" in out
    assert "balances" not in out
