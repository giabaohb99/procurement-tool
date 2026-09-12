"""Tool danh bạ nhân sự của Trợ lý AI — `employee_lookup` (T45).

Đây là tool ĐẦU TIÊN đọc hồ sơ của NGƯỜI KHÁC, nên ba lớp chặn đều phải có bài kiểm:
khóa `employee.read` · `apply_scope` theo phạm vi người hỏi · danh sách trắng trường ra.
Lớp thứ ba là lớp dễ mục nhất theo thời gian — thêm cột vào `Employee` là nó có thể lọt
ra, nên test khẳng định THEO TÊN TRƯỜNG chứ không chỉ đếm.
"""
from app.modules.assistant import tools as T
from app.modules.employee.model import Employee
from app.modules.employee.sensitive import SENSITIVE_FIELDS
from app.modules.user.model import User


def _them_ho_so_nhay_cam(db, seed):
    """Nhét dữ liệu nhạy cảm thật vào hồ sơ để test chứng minh nó KHÔNG ra khỏi tool."""
    emp = db.get(Employee, seed.emp_nstm_id)
    emp.position = "Nhân viên thu mua"
    emp.email = "nstm@dego.vn"
    emp.phone = "0900000001"
    emp.id_number = "079123456789"
    emp.bank_account_no = "1234567890"
    emp.bank_name = "Vietcombank"
    emp.permanent_address = "123 Trần Hưng Đạo"
    db.commit()
    return emp


def test_missing_permission_is_denied(db, seed):
    out = T.run_tool(db, db.get(User, seed.u_req_id), "employee_lookup", {"query": "NSTM"})
    assert out.get("denied") is True
    assert "items" not in out


def test_returns_contact_fields_only(db, seed, cap_quyen):
    cap_quyen(seed.u_req_id, "employee", scope="all", read=True)
    _them_ho_so_nhay_cam(db, seed)

    out = T.run_tool(db, db.get(User, seed.u_req_id), "employee_lookup",
                     {"query": "NSTM Chính"})
    assert out["total"] == 1
    row = out["items"][0]
    assert row["full_name"] == "NSTM Chính"
    assert row["code"] == seed.emp_nstm_code
    assert row["position"] == "Nhân viên thu mua"
    assert row["department_name"] == "Phòng Test"
    assert row["email"] == "nstm@dego.vn"
    #  Danh sách trắng: KHÔNG một trường nhạy cảm nào có mặt, kể cả dưới dạng ô rỗng.
    for f in SENSITIVE_FIELDS:
        assert f not in row
    assert "1234567890" not in str(row)


def test_search_matches_code_email_and_position(db, seed, cap_quyen):
    cap_quyen(seed.u_req_id, "employee", scope="all", read=True)
    _them_ho_so_nhay_cam(db, seed)
    user = db.get(User, seed.u_req_id)

    theo_ma = T.run_tool(db, user, "employee_lookup", {"query": seed.emp_nstm_code})
    assert [r["code"] for r in theo_ma["items"]] == [seed.emp_nstm_code]

    theo_chuc_vu = T.run_tool(db, user, "employee_lookup", {"query": "thu mua"})
    assert [r["code"] for r in theo_chuc_vu["items"]] == [seed.emp_nstm_code]

    khong_co = T.run_tool(db, user, "employee_lookup", {"query": "Nguyễn Không Tồn Tại"})
    assert khong_co["total"] == 0
    assert khong_co["items"] == []


def test_scope_own_sees_only_self(db, seed, cap_quyen):
    """Phạm vi `own` của entity `employee` là chính hồ sơ mình (`self: id`) — người khác
    không ra, dù tên khớp từ khóa."""
    cap_quyen(seed.u_req_id, "employee", scope="own", read=True)
    _them_ho_so_nhay_cam(db, seed)

    out = T.run_tool(db, db.get(User, seed.u_req_id), "employee_lookup", {})
    assert [r["code"] for r in out["items"]] == [seed.emp_req_code]


def test_department_zero_is_a_real_filter_not_all(db, seed, cap_quyen):
    """`department_id = 0` nghĩa là nhóm CHƯA GẮN phòng ban, không phải 'tất cả'."""
    cap_quyen(seed.u_req_id, "employee", scope="all", read=True)
    db.add(Employee(code="LEDANG", full_name="Người Chưa Gắn Phòng", company_id=seed.company_id,
                    department_id=0, is_active=True))
    db.commit()
    user = db.get(User, seed.u_req_id)

    chua_gan = T.run_tool(db, user, "employee_lookup", {"department_id": 0})
    assert [r["code"] for r in chua_gan["items"]] == ["LEDANG"]

    trong_phong = T.run_tool(db, user, "employee_lookup", {"department_id": seed.dept_id})
    assert "LEDANG" not in [r["code"] for r in trong_phong["items"]]


def test_inactive_hidden_by_default_and_limit_is_clamped(db, seed, cap_quyen):
    cap_quyen(seed.u_req_id, "employee", scope="all", read=True)
    db.add(Employee(code="DANGHI", full_name="Người Đã Nghỉ", company_id=seed.company_id,
                    department_id=seed.dept_id, is_active=False))
    db.commit()
    user = db.get(User, seed.u_req_id)

    mac_dinh = T.run_tool(db, user, "employee_lookup", {"query": "Đã Nghỉ"})
    assert mac_dinh["total"] == 0

    ca_nguoi_nghi = T.run_tool(db, user, "employee_lookup",
                               {"query": "Đã Nghỉ", "active_only": False})
    assert [r["code"] for r in ca_nguoi_nghi["items"]] == ["DANGHI"]

    #  limit rác từ model -> mặc định, không nổ.
    assert "items" in T.run_tool(db, user, "employee_lookup", {"limit": "vài người"})
    assert T.run_tool(db, user, "employee_lookup", {"limit": 1})["total"] == 1
