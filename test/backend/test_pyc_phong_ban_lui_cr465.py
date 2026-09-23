"""bao-CR-465 — YCMH LẬP MỚI KHÔNG ĐƯỢC PHÉP RỖNG PHÒNG BAN.

Phòng ban trên phiếu không phải chữ để in: `core/scoping.py` khai phạm vi `dept` của
`purchase_request` lọc theo cột `department_id`, nên phiếu mang `department_id = 0`
KHÔNG lọt vào tầm nhìn của bất kỳ trưởng phòng nào — không ai duyệt được, và
`find_dept_head_id` cũng trả 0 nên không ai nhận được thư. Lỗi câm hoàn toàn: người
lập bấm Gửi duyệt thành công rồi ngồi chờ một người sẽ không bao giờ thấy phiếu.

Trên prod đã dính ba phiếu đúng kiểu đó (132 · 135 · 164). Nguyên nhân ở giao diện cũ
là một cuộc đua: danh sách nhân sự và danh sách phòng ban nạp song song, mã màn hình
tra tên phòng trong danh sách phòng ban nhưng chỉ chờ cờ của danh sách nhân sự. Bài
kiểm này canh CHỐT BACKEND — lớp che cho mọi đường vào, kể cả khi màn hình lại hỏng
lần nữa hoặc có người gọi thẳng API.

Bốn điều được chốt:

```
gửi rỗng phòng ban          -> lùi về phòng của nhân sự ĐỨNG TÊN yêu cầu
không suy ra được           -> để rỗng, KHÔNG đoán bừa một phòng
đã chọn phòng ban rồi       -> giữ nguyên, người lập nói tiếng nói cuối
lùi xong                    -> trưởng phòng được điền theo phòng đó
```
"""
import pytest

from app.modules.department.model import Department
from app.modules.employee.model import Employee
from app.modules.purchase_request.schema import PRCreate
from app.modules.purchase_request.service import create_pr


@pytest.fixture
def dept_head(db, seed):
    """Gán Trưởng Phòng làm trưởng của «Phòng Test» — nguồn duy nhất của ô TBP."""
    dep = db.get(Department, seed.dept_id)
    dep.manager_id = seed.emp_tp_id
    db.commit()
    return dep


def test_rong_phong_ban_thi_lui_ve_phong_cua_nguoi_yeu_cau(db, seed, dept_head):
    """Đúng ca đã vỡ trên prod: giao diện gửi lên phiếu không có phòng ban."""
    pr = create_pr(db, PRCreate(company_id=seed.company_id, requester="Người YC",
                                requester_id=seed.emp_req_id, department="",
                                department_id=0, request_date="2026-09-23"),
                   user_id=seed.u_req_id)

    assert pr.department_id == seed.dept_id
    assert pr.department == "Phòng Test"
    # Lùi được phòng thì phải lùi luôn cả người duyệt, không thì vá nửa vời
    assert pr.head_of_dept_id == seed.emp_tp_id
    assert pr.head_of_dept == "Trưởng Phòng"


def test_khong_co_nguoi_yeu_cau_thi_lui_ve_nguoi_bam_nut(db, seed, dept_head):
    """Phiếu không khai người yêu cầu — lùi tiếp một nấc về tài khoản đang lập."""
    pr = create_pr(db, PRCreate(company_id=seed.company_id, requester_id=0,
                                department="", department_id=0,
                                request_date="2026-09-23"),
                   user_id=seed.u_req_id)

    assert pr.department_id == seed.dept_id
    assert pr.department == "Phòng Test"


def test_khong_suy_ra_duoc_thi_de_rong_chu_khong_doan(db, seed):
    """Nhân sự chưa gắn phòng → phiếu rỗng phòng ban, KHÔNG gán đại một phòng nào.

    Đoán bừa còn tệ hơn để trống: phiếu sẽ hiện ra trước mắt một trưởng phòng không
    liên quan, và người đó có quyền duyệt nó.
    """
    emp = Employee(code="NODEPT", full_name="Chưa Gắn Phòng",
                   company_id=seed.company_id, department_id=0, is_active=True)
    db.add(emp)
    db.commit()

    pr = create_pr(db, PRCreate(company_id=seed.company_id, requester_id=emp.id,
                                department="", department_id=0,
                                request_date="2026-09-23"),
                   user_id=0)

    assert pr.department_id == 0
    assert pr.department == ""


def test_da_chon_phong_ban_thi_giu_nguyen(db, seed, dept_head):
    """Chốt lùi CHỈ chạy khi phiếu rỗng — không được đè lên lựa chọn của người lập.

    Hành chính lập hộ cho phòng khác là chuyện bình thường; đè theo hồ sơ nhân sự
    của người bấm nút thì phiếu chạy sai phòng mà không báo gì.
    """
    other = Department(code="DEPT02", name="Phòng Khác",
                       company_id=seed.company_id, is_active=True)
    db.add(other)
    db.commit()

    pr = create_pr(db, PRCreate(company_id=seed.company_id, requester="Người YC",
                                requester_id=seed.emp_req_id,
                                department="Phòng Khác", department_id=other.id,
                                request_date="2026-09-23"),
                   user_id=seed.u_req_id)

    assert pr.department_id == other.id
    assert pr.department == "Phòng Khác"
