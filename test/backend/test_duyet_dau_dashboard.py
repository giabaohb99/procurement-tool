"""Tổng quan Duyệt dấu — mỗi vai trò đúng khối của mình, theo phạm vi.

Bắt các nhầm lẫn: người tạo thấy "phiếu của tôi"; TBP thấy hàng chờ duyệt; Văn thư
thấy hàng chờ đóng dấu (Đã duyệt); Giám đốc/Văn thư (company) KHÔNG thấy phiếu nháp
— đúng nhánh phạm vi `company` đặc biệt của seal (chỉ Đã duyệt / Hoàn thành).
"""
from types import SimpleNamespace

from app.modules.employee.model import Employee
from app.modules.seal_request import model as m
from app.modules.seal_request.dashboard_service import build_overview
from app.modules.seal_request.schema import SealRequestCreate
from app.modules.seal_request.service import create_seal_request

CTY, DEPT = 1, 10


def _person(db, cap_quyen, *, uid, dept, company, scope, **actions):
    emp = Employee(code=f"NV{uid}", full_name=f"NV{uid}", email=f"nv{uid}@dego.vn",
                   department_id=dept, company_id=company)
    db.add(emp)
    db.flush()
    cap_quyen(uid, "seal_request", scope=scope, **actions)
    return SimpleNamespace(id=uid, employee_id=emp.id, email=f"nv{uid}@dego.vn")


def _make(db, user, purpose, *, status, company_ids=(CTY,)):
    req = create_seal_request(
        db, SealRequestCreate(purpose=purpose, company_ids=list(company_ids),
                              first_approver_id=500),
        user, submit=False)
    req.status = status
    req.department_id = DEPT
    db.flush()
    return req


def _seed(db, cap_quyen):
    """Người tạo (own) + một bộ phiếu nhiều trạng thái."""
    owner = _person(db, cap_quyen, uid=5001, dept=DEPT, company=CTY, scope="own",
                    read=True, create=True)
    _make(db, owner, "[test] nháp", status=m.SEAL_DRAFT)
    _make(db, owner, "[test] chờ duyệt", status=m.SEAL_PENDING)
    _make(db, owner, "[test] đã duyệt", status=m.SEAL_APPROVED)
    _make(db, owner, "[test] hoàn thành", status=m.SEAL_COMPLETED)
    return owner


def test_nguoi_dung_thay_phieu_cua_toi(db, cap_quyen):
    owner = _seed(db, cap_quyen)
    data = build_overview(db, owner)

    assert data["mine"]["by_status"] == {
        m.SEAL_DRAFT: 1, m.SEAL_PENDING: 1, m.SEAL_APPROVED: 1, m.SEAL_COMPLETED: 1}
    assert "stats" in data  # thống kê theo phạm vi riêng — mọi vai trò đều có
    assert "approve" not in data and "clerk" not in data and "director" not in data


def test_tbp_thay_hang_cho_duyet(db, cap_quyen):
    _seed(db, cap_quyen)
    tbp = _person(db, cap_quyen, uid=5002, dept=DEPT, company=CTY, scope="dept",
                  read=True, approve=True)
    data = build_overview(db, tbp)

    assert data["approve"]["pending"] == 1  # duy nhất phiếu Chờ duyệt trong phòng
    assert "clerk" not in data and "director" not in data
    assert "stats" in data  # thống kê theo phạm vi riêng


def test_van_thu_thay_hang_cho_dong_dau_khong_thay_nhap(db, cap_quyen):
    from app.modules.seal_clerk.model import SealClerk

    _seed(db, cap_quyen)
    clerk = _person(db, cap_quyen, uid=5003, dept=99, company=CTY, scope="company",
                    read=True, write=True)
    #  Cơ chế mới: văn thư thấy phiếu nào là do BẢNG PHÂN CÔNG — phân cho công ty CTY.
    db.add(SealClerk(employee_id=clerk.employee_id, company_id=CTY, is_head=False))
    db.flush()
    data = build_overview(db, clerk)

    # Văn thư (company) chỉ thấy Đã duyệt (chờ đóng) + Hoàn thành — KHÔNG thấy nháp/chờ duyệt.
    assert data["clerk"]["to_stamp"] == 1 and data["clerk"]["completed"] == 1
    total = sum(row["value"] for row in data["stats"]["by_status"])
    assert total == 2  # chỉ APPROVED + COMPLETED lọt qua nhánh company


def test_giam_doc_thay_yeu_cau_da_duyet_va_thong_ke(db, cap_quyen):
    _seed(db, cap_quyen)
    director = _person(db, cap_quyen, uid=5004, dept=99, company=CTY, scope="company",
                       read=True)
    data = build_overview(db, director)

    # Giám đốc (chỉ đọc, phạm vi công ty): khối "đã phê duyệt" = APPROVED + COMPLETED.
    assert data["director"]["count"] == 2
    assert "stats" in data
    assert "mine" not in data and "approve" not in data and "clerk" not in data


def test_thong_ke_theo_cong_ty_va_loc_trang_thai_theo_ngay(db, cap_quyen):
    """Khối thống kê: đếm theo CÔNG TY (bảng nối) + 'theo trạng thái' lọc theo ngày."""
    from datetime import datetime, timedelta

    owner = _person(db, cap_quyen, uid=5011, dept=DEPT, company=CTY, scope="own",
                    read=True, create=True)
    now = datetime.now()
    _make(db, owner, "[test] mới 2 công ty", status=m.SEAL_PENDING, company_ids=[CTY, 2])
    old = _make(db, owner, "[test] cũ", status=m.SEAL_APPROVED)
    old.created_at = now - timedelta(days=100)
    db.flush()

    # Theo công ty: phiếu 2-công-ty +1 cho cả CTY lẫn 2; phiếu cũ +1 cho CTY.
    by_co = {c["id"]: c["value"] for c in build_overview(db, owner)["stats"]["by_company"]}
    assert by_co.get(CTY) == 2 and by_co.get(2) == 1

    # Lọc 30 ngày gần nhất → chỉ phiếu mới (PENDING); phiếu 100 ngày trước bị loại,
    #  và khoảng ngày áp cho CẢ khối "theo công ty".
    frm = (now - timedelta(days=30)).strftime("%Y-%m-%d")
    ranged = build_overview(db, owner, date_from=frm)["stats"]
    st30 = {r["key"]: r["value"] for r in ranged["by_status"]}
    assert st30.get(m.SEAL_PENDING) == 1 and m.SEAL_APPROVED not in st30
    co30 = {c["id"]: c["value"] for c in ranged["by_company"]}
    assert co30.get(CTY) == 1 and co30.get(2) == 1  # phiếu cũ (chỉ CTY) đã bị loại

    # Bỏ lọc (tất cả) → thấy cả hai trạng thái.
    st_all = {r["key"] for r in build_overview(db, owner)["stats"]["by_status"]}
    assert {m.SEAL_PENDING, m.SEAL_APPROVED} <= st_all


def test_khoi_dashboard_phan_theo_grant_khong_theo_write_toan_cuc(db, cap_quyen):
    """Khối Chờ đóng dấu / Giám đốc phân theo GRANT (write company vs read company),
    không theo `can(write)` toàn cục — nếu không mọi nhân sự (own-write) đều thấy khối
    đóng dấu và Giám đốc thì không bao giờ hiện."""
    from app.modules.seal_clerk.model import SealClerk

    owner = _person(db, cap_quyen, uid=5101, dept=DEPT, company=CTY, scope="own",
                    read=True, create=True)
    _make(db, owner, "[t] đã duyệt", status=m.SEAL_APPROVED)
    _make(db, owner, "[t] hoàn thành", status=m.SEAL_COMPLETED)

    # (1) Nhân sự thường (own r/c/w): có 'mine', KHÔNG có 'clerk'/'director'.
    staff = _person(db, cap_quyen, uid=5102, dept=DEPT, company=CTY, scope="own",
                    read=True, create=True, write=True)
    d = build_overview(db, staff)
    assert "mine" in d and "clerk" not in d and "director" not in d

    # (2) Văn thư: own (nền) + write company + được phân công → có 'clerk'.
    emp_c = Employee(code="VTd", full_name="VT", email="vtd@dego.vn",
                     department_id=99, company_id=CTY)
    db.add(emp_c)
    db.flush()
    cap_quyen(5103, "seal_request", scope="own", read=True, create=True, write=True)
    cap_quyen(5103, "seal_request", scope="company", read=True, write=True)
    db.add(SealClerk(employee_id=emp_c.id, company_id=CTY, is_head=False))
    db.flush()
    clerk = SimpleNamespace(id=5103, employee_id=emp_c.id, email="vtd@dego.vn")
    d = build_overview(db, clerk)
    assert "clerk" in d and "director" not in d

    # (3) Giám đốc: own (nền) + read company → có 'director', KHÔNG 'clerk'.
    emp_d = Employee(code="GDd", full_name="GD", email="gdd@dego.vn",
                     department_id=99, company_id=CTY)
    db.add(emp_d)
    db.flush()
    cap_quyen(5104, "seal_request", scope="own", read=True, create=True, write=True)
    cap_quyen(5104, "seal_request", scope="company", read=True)
    director = SimpleNamespace(id=5104, employee_id=emp_d.id, email="gdd@dego.vn")
    d = build_overview(db, director)
    assert "director" in d and "clerk" not in d


def test_khong_co_quyen_doc_thi_khong_co_khoi_nao(db, cap_quyen):
    _seed(db, cap_quyen)
    emp = Employee(code="NV5005", full_name="NV5005", email="nv5005@dego.vn",
                   department_id=DEPT, company_id=CTY)
    db.add(emp)
    db.flush()
    user = SimpleNamespace(id=5005, employee_id=emp.id, email="nv5005@dego.vn")
    data = build_overview(db, user)

    assert set(data) == {"can"}
    assert data["can"]["seal_request"] is False
