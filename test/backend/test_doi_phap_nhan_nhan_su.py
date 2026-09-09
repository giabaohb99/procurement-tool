"""ĐỔI PHÁP NHÂN của một hồ sơ nhân sự (duoc-CR-342).

Ô «Công ty» ở màn chi tiết nhân sự trước đây KHÓA. Mở nó ra thì lộ một cái bẫy
do hai luật cũ ghép lại, và bẫy đó làm việc đổi pháp nhân **không làm được** chứ
không phải chỉ bất tiện:

1. `_sync_primary_department` đổi phòng chính thì **hạ phòng cũ xuống kiêm
   nhiệm** chứ không xóa — kể cả khi phòng chính mới là "không có". Nên xóa ô
   «Phòng ban» ở giao diện KHÔNG gỡ người đó khỏi phòng cũ.
2. Chốt L3 (`_check_departments_exist`) chặn mọi phòng khác pháp nhân.

Ghép lại: đổi pháp nhân xong là ăn 400 trỏ vào chính cái phòng vừa bỏ. Mà giao
diện cũng không cứu được — thẻ «Kiêm nhiệm» chỉ quản lý phòng PHỤ, còn phòng
đang vướng lại là phòng CHÍNH vừa bị hạ xuống.

`detach_other_company_departments` là chốt gỡ bẫy đó. Bài kiểm ở đây canh cả hai
chiều: **gỡ đúng thứ phải gỡ**, và **KHÔNG gỡ thứ không được phép gỡ**.
"""
import pytest
from fastapi import HTTPException

from app.modules.department.model import Department
from app.modules.employee import department_service as dv
from app.modules.employee.department_model import EmployeeDepartment
from app.modules.employee.model import Employee
from app.modules.employee.schema import EmployeeUpdate
from app.modules.employee.service import update_employee

ACTOR = 1
#  Pháp nhân thứ hai — chỉ cần một id KHÁC `seed.company_id`, không cần bản ghi
#  thật: mọi luật ở đây so sánh bằng số.
OTHER_COMPANY = 777


@pytest.fixture()
def san(db, seed):
    """Một người ở pháp nhân A, giữ 3 phòng: chính + kiêm nhiệm + phòng dùng chung."""
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
    for key, primary in (("A_CHINH", True), ("A_KIEM", False), ("CHUNG", False)):
        db.add(EmployeeDepartment(employee_id=person.id, department_id=department[key],
                                  is_primary=primary, created_by=ACTOR, updated_by=ACTOR))
    db.commit()
    return {"phong": department, "nguoi": person}


# ── Chiều THUẬN: đổi được ───────────────────────────────────────────────────

def test_doi_phap_nhan_va_bo_phong_ban_thi_luu_duoc(db, san):
    """Đúng thao tác giao diện làm: đổi công ty + xóa ô phòng ban.

    Trước khi có chốt, chính ca này ném 400 «Phòng ban thuộc pháp nhân khác»
    trỏ vào cái phòng người dùng vừa xóa.
    """
    person = san["nguoi"]
    update_employee(db, person.id,
                    EmployeeUpdate(company_id=OTHER_COMPANY, department_id=0), ACTOR)

    db.refresh(person)
    assert person.company_id == OTHER_COMPANY
    #  Hai phòng của pháp nhân CŨ phải biến mất khỏi bảng kiêm nhiệm, không chỉ
    #  khỏi cột `department_id`.
    assert san["phong"]["A_CHINH"] not in dv.departments_of(db, person.id)
    assert san["phong"]["A_KIEM"] not in dv.departments_of(db, person.id)

    #  ⚠️ `department_id` KHÔNG về 0 dù người dùng xóa ô «Phòng ban»: phòng dùng
    #  chung sống sót, và một bản ghi có phòng thì phải có phòng CHÍNH —
    #  `set_departments` luôn cử phần tử đầu làm phòng chính. Đây đúng là luật
    #  sẵn có của `_sync_primary_department` (xóa phòng chính trong khi còn kiêm
    #  nhiệm thì kiêm nhiệm lên thay), không phải luật riêng của đường đổi pháp
    #  nhân — dựng luật khác ở đây là hai đường ghi cùng một bảng nói hai kiểu.
    assert person.department_id == san["phong"]["CHUNG"]


def test_giu_lai_phong_vua_chon_trong_cung_lan_luu(db, san):
    """Đổi pháp nhân VÀ chọn luôn phòng của pháp nhân mới — phải giữ phòng đó.

    ⚠️ `set_departments` ghi đè `department_id` theo danh sách truyền vào, nên
    quên phòng vừa chọn là xóa trắng đúng lựa chọn người dùng vừa bấm — âm thầm,
    vì lệnh lưu vẫn trả về 200.
    """
    person = san["nguoi"]
    update_employee(db, person.id,
                    EmployeeUpdate(company_id=OTHER_COMPANY,
                                   department_id=san["phong"]["B_MOI"]), ACTOR)

    db.refresh(person)
    assert person.department_id == san["phong"]["B_MOI"]
    assert dv.departments_of(db, person.id)[0] == san["phong"]["B_MOI"]


def test_phong_dung_chung_khong_bi_go(db, san):
    """`company_id = 0` là phòng KHÔNG thuộc pháp nhân nào — đổi pháp nhân
    không đụng tới nó. Gỡ luôn cho gọn là xóa dữ liệu đúng mà L3 vẫn cho phép."""
    person = san["nguoi"]
    update_employee(db, person.id,
                    EmployeeUpdate(company_id=OTHER_COMPANY, department_id=0), ACTOR)

    assert san["phong"]["CHUNG"] in dv.departments_of(db, person.id)


def test_go_xong_phai_ghi_vao_dau_vet(db, san):
    """Gỡ âm thầm thì tháng sau không ai tra được vì sao một người mất phòng ban."""
    from app.modules.audit.model import AuditLog

    person = san["nguoi"]
    update_employee(db, person.id,
                    EmployeeUpdate(company_id=OTHER_COMPANY, department_id=0), ACTOR)

    messages = [row.message for row in
                db.query(AuditLog).filter(AuditLog.entity == "employee",
                                          AuditLog.entity_id == person.id).all()]
    assert any("Phòng Kế toán A" in (m or "") and "Phòng Kho vận A" in (m or "")
               for m in messages)


# ── Chiều NGƯỢC: không được nới tay ─────────────────────────────────────────

def test_khong_doi_phap_nhan_thi_khong_go_gi(db, san):
    """Lưu hồ sơ mà không đụng tới công ty thì mọi phòng ban còn nguyên.

    Chốt này chạy trên MỌI lượt lưu hồ sơ, nên nới điều kiện một chút là mỗi lần
    ai đó sửa số điện thoại lại mất một phòng kiêm nhiệm.
    """
    person = san["nguoi"]
    truoc = dv.departments_of(db, person.id)

    update_employee(db, person.id, EmployeeUpdate(phone="0900000000"), ACTOR)

    assert dv.departments_of(db, person.id) == truoc


def test_gui_lai_dung_phap_nhan_cu_khong_go_gi(db, san):
    """Gửi `company_id` y nguyên giá trị cũ = KHÔNG đổi pháp nhân.

    Màn hồ sơ gửi lại đủ mọi ô mỗi lần lưu, nên `"company_id" in fields` luôn
    đúng — điều kiện phải so GIÁ TRỊ, không phải so sự có mặt của khóa.
    """
    person = san["nguoi"]
    truoc = dv.departments_of(db, person.id)

    update_employee(db, person.id,
                    EmployeeUpdate(company_id=person.company_id,
                                   department_id=person.department_id), ACTOR)

    assert dv.departments_of(db, person.id) == truoc


def test_van_chan_khi_chon_phong_sai_phap_nhan(db, san):
    """Chốt L3 KHÔNG được nới: đổi sang pháp nhân B mà chọn phòng của A thì vẫn
    phải chặn. Gỡ phòng cũ là một chuyện, cho gán phòng sai là chuyện khác."""
    person = san["nguoi"]
    with pytest.raises(HTTPException) as loi:
        update_employee(db, person.id,
                        EmployeeUpdate(company_id=OTHER_COMPANY,
                                       department_id=san["phong"]["A_CHINH"]), ACTOR)
    assert loi.value.status_code == 400


def test_ve_phap_nhan_rong_thi_khong_go(db, san):
    """`company_id = 0` (gỡ pháp nhân) thì không có "pháp nhân mới" để so —
    giữ nguyên phòng ban, cùng luật với L3 "chỉ chặn khi cả hai bên đều khai"."""
    person = san["nguoi"]
    truoc = dv.departments_of(db, person.id)

    update_employee(db, person.id, EmployeeUpdate(company_id=0), ACTOR)

    assert dv.departments_of(db, person.id) == truoc
