"""ĐỔI PHÁP NHÂN của một hồ sơ nhân sự (duoc-CR-342, viết lại cho kiêm nhiệm bảng riêng ở duoc-CR-755).

Ô "Công ty" ở màn chi tiết nhân sự trước đây KHÓA. Mở nó ra thì phát sinh hai việc phải làm đúng:

1. Phòng CHÍNH vẫn là phòng của công ty cũ -> chốt L3 (`_check_departments_exist`) chặn 400 trỏ vào chính cái phòng
   đó; người dùng chọn phòng của công ty mới hoặc bỏ trống ô phòng ban.
2. Dòng KIÊM NHIỆM ở công ty cũ (`tab_employee_concurrent`) phải KẾT THÚC (đến ngày = hôm qua), chứ không bị xóa;
   dòng ở công ty KHÁC công ty cũ thì không bao giờ bị đụng (Q4).

Bài kiểm ở đây canh cả hai chiều: **kết thúc đúng thứ phải kết thúc**, và **KHÔNG đụng thứ không được phép đụng**.
Chi tiết tham số giữ dòng / nhập Excel / hoàn tác: `test_kiem_nhiem_luong_ghi_cr755.py`.
"""
import pytest
from datetime import timedelta

from fastapi import HTTPException

from app.core.vn_time import vn_today
from app.modules.department.model import Department
from app.modules.employee import department_service as dv
from app.modules.employee.concurrent_model import EmployeeConcurrent
from app.modules.employee.department_model import EmployeeDepartment
from app.modules.employee.model import Employee
from app.modules.employee.schema import EmployeeUpdate
from app.modules.employee.service import update_employee

ACTOR = 1
#  Hai pháp nhân khác — chỉ cần id KHÁC `seed.company_id`, không cần bản ghi thật: mọi luật ở đây so sánh bằng số.
OTHER_COMPANY = 777
THIRD_COMPANY = 888


@pytest.fixture()
def san(db, seed):
    """Một người ở pháp nhân A: phòng chính + hai dòng kiêm nhiệm ở A (riêng + dùng chung) + một dòng ở pháp nhân C."""
    def make_department(code, name, company_id):
        row = Department(code=code, name=name, company_id=company_id, is_active=True)
        db.add(row)
        db.flush()
        return row.id

    department = {
        "A_CHINH": make_department("A1", "Phòng Kế toán A", seed.company_id),
        "A_KIEM": make_department("A2", "Phòng Kho vận A", seed.company_id),
        #  `company_id = 0` = phòng DÙNG CHUNG, không thuộc pháp nhân nào.
        "CHUNG": make_department("C0", "Phòng Hành chính chung", 0),
        "B_MOI": make_department("B1", "Phòng Kế toán B", OTHER_COMPANY),
    }

    person = Employee(code="DPN_A", full_name="Người sắp chuyển pháp nhân",
                      company_id=seed.company_id, department_id=department["A_CHINH"],
                      is_active=True)
    db.add(person)
    db.flush()
    db.add(EmployeeDepartment(employee_id=person.id, department_id=department["A_CHINH"],
                              is_primary=True, created_by=ACTOR, updated_by=ACTOR))
    start = vn_today() - timedelta(days=10)
    rows = {}
    for key, dept, company in (("A_KIEM", "A_KIEM", seed.company_id), ("A_CHUNG", "CHUNG", seed.company_id),
                               ("C_CHUNG", "CHUNG", THIRD_COMPANY)):
        rows[key] = EmployeeConcurrent(employee_id=person.id, company_id=company, department_id=department[dept],
                                       from_date=start, counts_scope=True, created_by=ACTOR, updated_by=ACTOR)
        db.add(rows[key])
    db.commit()
    return {"phong": department, "nguoi": person, "dong": rows}


def _to_date(db, row):
    db.expire_all()
    return db.get(EmployeeConcurrent, row.id).to_date


# ── Chiều THUẬN: đổi được ───────────────────────────────────────────────────

def test_doi_phap_nhan_va_bo_phong_ban_thi_luu_duoc(db, san):
    """Đúng thao tác giao diện làm: đổi công ty + xóa ô phòng ban.

    Phòng chính về 0; hai dòng kiêm nhiệm ở công ty CŨ kết thúc hôm qua (kể cả dòng phòng dùng chung - kết
    thúc theo CÔNG TY, không theo phòng); dòng ở công ty C nguyên vẹn.
    """
    person = san["nguoi"]
    update_employee(db, person.id,
                    EmployeeUpdate(company_id=OTHER_COMPANY, department_id=0), ACTOR)

    db.refresh(person)
    assert person.company_id == OTHER_COMPANY
    assert person.department_id == 0
    assert dv.departments_of(db, person.id) == []
    yesterday = vn_today() - timedelta(days=1)
    assert _to_date(db, san["dong"]["A_KIEM"]) == yesterday
    assert _to_date(db, san["dong"]["A_CHUNG"]) == yesterday


def test_giu_lai_phong_vua_chon_trong_cung_lan_luu(db, san):
    """Đổi pháp nhân VÀ chọn luôn phòng của pháp nhân mới — phải giữ phòng đó.

    ⚠️ Quên phòng vừa chọn là xóa trắng đúng lựa chọn người dùng vừa bấm — âm thầm, vì lệnh lưu vẫn trả về 200.
    """
    person = san["nguoi"]
    update_employee(db, person.id,
                    EmployeeUpdate(company_id=OTHER_COMPANY,
                                   department_id=san["phong"]["B_MOI"]), ACTOR)

    db.refresh(person)
    assert person.department_id == san["phong"]["B_MOI"]
    assert dv.departments_of(db, person.id) == [san["phong"]["B_MOI"]]


def test_dong_o_cong_ty_khac_khong_bi_dung(db, san):
    """Dòng kiêm nhiệm ở công ty C (khác công ty cũ A) không bao giờ bị đụng, kể cả cùng phòng dùng chung."""
    person = san["nguoi"]
    update_employee(db, person.id,
                    EmployeeUpdate(company_id=OTHER_COMPANY, department_id=0), ACTOR)

    assert _to_date(db, san["dong"]["C_CHUNG"]) is None


def test_go_xong_phai_ghi_vao_dau_vet(db, san):
    """Kết thúc âm thầm thì tháng sau không ai tra được vì sao một người mất kiêm nhiệm."""
    from app.modules.audit.model import AuditLog

    person = san["nguoi"]
    update_employee(db, person.id,
                    EmployeeUpdate(company_id=OTHER_COMPANY, department_id=0), ACTOR)

    messages = [row.message for row in
                db.query(AuditLog).filter(AuditLog.entity == "employee",
                                          AuditLog.entity_id == person.id).all()]
    assert any("kiêm nhiệm ở công ty cũ" in (m or "") and "Phòng Kho vận A" in (m or "")
               and "Phòng Hành chính chung" in (m or "") for m in messages)


# ── Chiều NGƯỢC: không được nới tay ─────────────────────────────────────────

def test_khong_doi_phap_nhan_thi_khong_go_gi(db, san):
    """Lưu hồ sơ mà không đụng tới công ty thì mọi dòng kiêm nhiệm còn nguyên.

    Chốt này chạy trên MỌI lượt lưu hồ sơ, nên nới điều kiện một chút là mỗi lần
    ai đó sửa số điện thoại lại mất một dòng kiêm nhiệm.
    """
    person = san["nguoi"]

    update_employee(db, person.id, EmployeeUpdate(phone="0900000000"), ACTOR)

    assert all(_to_date(db, row) is None for row in san["dong"].values())
    assert dv.departments_of(db, person.id) == [san["phong"]["A_CHINH"]]


def test_gui_lai_dung_phap_nhan_cu_khong_go_gi(db, san):
    """Gửi `company_id` y nguyên giá trị cũ = KHÔNG đổi pháp nhân.

    Màn hồ sơ gửi lại đủ mọi ô mỗi lần lưu, nên `"company_id" in fields` luôn
    đúng — điều kiện phải so GIÁ TRỊ, không phải so sự có mặt của khóa.
    """
    person = san["nguoi"]

    update_employee(db, person.id,
                    EmployeeUpdate(company_id=person.company_id,
                                   department_id=person.department_id), ACTOR)

    assert all(_to_date(db, row) is None for row in san["dong"].values())


def test_van_chan_khi_chon_phong_sai_phap_nhan(db, san):
    """Chốt L3 KHÔNG được nới: đổi sang pháp nhân B mà chọn phòng của A thì vẫn
    phải chặn — và dòng kiêm nhiệm không bị kết thúc dở dang (lỗi thì lùi cả lượt)."""
    person = san["nguoi"]
    with pytest.raises(HTTPException) as loi:
        update_employee(db, person.id,
                        EmployeeUpdate(company_id=OTHER_COMPANY,
                                       department_id=san["phong"]["A_CHINH"]), ACTOR)
    assert loi.value.status_code == 400
    assert _to_date(db, san["dong"]["A_KIEM"]) is None


def test_doi_cong_ty_ma_phong_chinh_van_cua_cong_ty_cu_thi_chan(db, san):
    """Không gửi ô phòng ban mà phòng chính vẫn là phòng riêng của A -> 400 (người dùng phải chọn phòng mới)."""
    person = san["nguoi"]
    with pytest.raises(HTTPException) as loi:
        update_employee(db, person.id, EmployeeUpdate(company_id=OTHER_COMPANY), ACTOR)
    assert loi.value.status_code == 400
    assert "pháp nhân khác" in str(loi.value.detail)


def test_ve_phap_nhan_rong_thi_khong_go(db, san):
    """`company_id = 0` (gỡ pháp nhân) thì không có "pháp nhân mới" để so —
    giữ nguyên phòng ban và kiêm nhiệm, cùng luật với L3 "chỉ chặn khi cả hai bên đều khai"."""
    person = san["nguoi"]

    update_employee(db, person.id, EmployeeUpdate(company_id=0), ACTOR)

    assert dv.departments_of(db, person.id) == [san["phong"]["A_CHINH"]]
    assert all(_to_date(db, row) is None for row in san["dong"].values())
