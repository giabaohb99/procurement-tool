"""bao-CR-466 — GỬI DUYỆT PHẢI CÓ PHÒNG BAN VÀ TRƯỞNG BỘ PHẬN.

Luật đại ca chốt 23/09/2026. Lý do không phải cho đủ ô: phạm vi `dept` lọc theo
`department_id`, chuông và thư cũng định tuyến theo cùng cột đó — nên phiếu thiếu
phòng ban gửi đi là nằm chết, không ai nhìn thấy. Trước CR này không chỗ nào chặn:
người lập nhận câu «Đã gửi duyệt» rồi chờ một người sẽ không bao giờ thấy phiếu.

Thứ tự hai nhịp mới là phần đáng canh, không phải câu chặn:

```
CHỮA trước  ->  ô rỗng thì tra lại từ hồ sơ nhân sự + danh mục phòng ban
CHẶN sau    ->  chữa xong vẫn rỗng mới báo lỗi
```

Đảo thứ tự thì ca thường gặp nhất — phiếu lập lúc tài khoản chưa gắn phòng, quản trị
gắn phòng sau — biến thành khóa cứng: người lập không sửa được vì ô Phòng ban là ô chỉ
xem, và phiếu kẹt vĩnh viễn ở Nháp.

⚠️ Bài kiểm này KHÔNG được biến thành điều kiện DUYỆT. `head_of_dept_id` vẫn thuần túy
là người đứng tên trên bản in (CR-071) — ai có quyền `approve` và phiếu trong phạm vi
của họ thì vẫn duyệt được.
"""
import pytest
from fastapi import HTTPException

from app.modules.department.model import Department
from app.modules.employee.model import Employee
from app.modules.purchase_request.model import PurchaseRequest
from app.modules.purchase_request.service import ensure_submit_ready


@pytest.fixture
def dept_with_head(db, seed):
    dep = db.get(Department, seed.dept_id)
    dep.manager_id = seed.emp_tp_id
    db.commit()
    return dep


def _draft(db, seed, **kw):
    pr = PurchaseRequest(code="PYCTEST01", company_id=seed.company_id, status="draft",
                         created_by=seed.u_req_id, **kw)
    db.add(pr)
    db.commit()
    return pr


# ── Nhịp CHỮA ───────────────────────────────────────────────────────────────────
def test_phieu_rong_phong_ban_duoc_chua_roi_cho_qua(db, seed, dept_with_head):
    """Ca thường gặp nhất: phiếu ra đời lúc chưa có phòng, nay hồ sơ đã có."""
    pr = _draft(db, seed, requester_id=seed.emp_req_id, department="", department_id=0)

    ensure_submit_ready(db, pr, seed.u_req_id)   # không được ném

    assert pr.department_id == seed.dept_id
    assert pr.department == "Phòng Test"
    assert pr.head_of_dept_id == seed.emp_tp_id


def test_phong_vua_duoc_gan_truong_thi_tra_lai_chu_khong_chan(db, seed, dept_with_head):
    """Phiếu lập lúc phòng chưa có trưởng; quản trị gán trưởng sau."""
    pr = _draft(db, seed, requester_id=seed.emp_req_id, department="Phòng Test",
                department_id=seed.dept_id, head_of_dept_id=0)

    ensure_submit_ready(db, pr, seed.u_req_id)

    assert pr.head_of_dept_id == seed.emp_tp_id
    assert pr.head_of_dept == "Trưởng Phòng"


# ── Nhịp CHẶN ───────────────────────────────────────────────────────────────────
def test_chua_khong_ra_phong_ban_thi_chan(db, seed, dept_with_head):
    """Nhân sự chưa gắn phòng → chặn, và câu lỗi phải chỉ ra việc cần làm."""
    emp = Employee(code="NODEPT2", full_name="Chưa Gắn Phòng",
                   company_id=seed.company_id, department_id=0, is_active=True)
    db.add(emp)
    db.commit()
    pr = _draft(db, seed, requester_id=emp.id, department="", department_id=0)

    with pytest.raises(HTTPException) as e:
        ensure_submit_ready(db, pr, 0)

    assert e.value.status_code == 400
    assert "Phòng ban" in e.value.detail
    assert "gắn phòng ban" in e.value.detail      # nói việc cần làm, không chỉ nêu triệu chứng
    assert pr.status == "draft"                    # phiếu KHÔNG được nhích trạng thái


def test_phong_chua_gan_truong_thi_chan(db, seed):
    """Có phòng nhưng phòng chưa có trưởng → vẫn chặn, câu lỗi nêu đúng tên phòng."""
    pr = _draft(db, seed, requester_id=seed.emp_req_id, department="Phòng Test",
                department_id=seed.dept_id, head_of_dept_id=0)

    with pytest.raises(HTTPException) as e:
        ensure_submit_ready(db, pr, seed.u_req_id)

    assert e.value.status_code == 400
    assert "Trưởng bộ phận" in e.value.detail
    assert "Phòng Test" in e.value.detail


def test_ten_phong_khong_khop_danh_muc_thi_noi_dung_ly_do_do(db, seed):
    """Tên phòng không tra ra id — câu lỗi phải nói đúng chuyện đó, đừng đổ cho «chưa có phòng»."""
    pr = _draft(db, seed, requester_id=0, department="Phòng Đã Đổi Tên", department_id=0)

    with pytest.raises(HTTPException) as e:
        ensure_submit_ready(db, pr, 0)

    assert "không khớp phòng ban nào" in e.value.detail
    assert "Phòng Đã Đổi Tên" in e.value.detail


def test_chua_duoc_phan_nao_thi_ghi_xuong_phan_do_truoc_khi_nem(db, seed):
    """Chữa được phòng ban nhưng phòng chưa có trưởng: phần đã chữa PHẢI được lưu.

    Không lưu thì lần bấm sau dò lại từ đầu, và người đi sửa dữ liệu mở phiếu ra vẫn
    thấy ô Phòng ban trống — họ sẽ đi chữa nhầm chỗ.
    """
    pr = _draft(db, seed, requester_id=seed.emp_req_id, department="", department_id=0)

    with pytest.raises(HTTPException):
        ensure_submit_ready(db, pr, seed.u_req_id)

    db.expire(pr)
    assert pr.department_id == seed.dept_id       # đã ghi xuống DB dù lượt gọi ném lỗi
    assert pr.head_of_dept_id == 0
