"""bao-CR-405 — chính sách mật khẩu dùng chung (BM-016).

Trước CR này hệ thống không có chính sách nào: ba cửa khai `password: str` trần,
cửa tự đổi mật khẩu chỉ đếm đủ 6 ký tự, cửa đặt mật khẩu từ hồ sơ nhân sự đòi 4.
Đặt mật khẩu `1` là nhận — mà **tên đăng nhập chính là mã nhân viên**, ai cầm danh
bạ cũng đọc được.

Bài kiểm chia hai tầng:

* Tầng luật — `core/password_policy.validate_password` đứng riêng, không cần DB.
* Tầng cửa — năm chỗ ghi `password_hash` phải thật sự gọi luật đó. Ca cuối cùng
  (`test_moi_cua_bam_mat_khau_deu_di_qua_chinh_sach`) quét AST toàn `app/modules`:
  ai thêm cửa thứ sáu mà quên chính sách thì **nổ ở đây**, không nổ trên màn khách.

⚠️ `test/backend` chạy SQLite — DB không ép độ dài `VARCHAR` nên khẳng định ở tầng
DB sẽ xanh giả. Mọi khẳng định dưới đây đều đứng ở tầng hàm/lược đồ.
"""
import ast
from pathlib import Path

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

import app as app_package
from app.core.auth import create_reset_token, hash_password, verify_password
from app.core.password_policy import MAX_BYTES, MIN_LENGTH, validate_password
from app.modules.auth import controller as auth_controller
from app.modules.auth.schema import ChangePasswordInput, ResetPasswordInput
from app.modules.employee.controller import SetPasswordIn
from app.modules.employee.controller import set_password as employee_set_password
from app.modules.employee.model import Employee
from app.modules.user import service as user_service
from app.modules.user.model import User
from app.modules.user.schema import UserProvision

ACTOR = 1
GOOD = "Thumua2026xyz"


# ── 1. Tầng luật ────────────────────────────────────────────────────────────────

def test_mat_khau_dat_chuan_tra_ve_nguyen_chuoi():
    assert validate_password(GOOD, username="TESTREQ", email="testreq@degoholding.vn") == GOOD


def test_mat_khau_ngan_hon_muc_toi_thieu_bi_tu_choi():
    with pytest.raises(HTTPException) as e:
        validate_password("a" * (MIN_LENGTH - 2) + "1")
    assert e.value.status_code == 400
    assert str(MIN_LENGTH) in e.value.detail
    # Mốc đúng bằng MIN_LENGTH thì qua — chặn lệch một ký tự.
    assert validate_password("a" * (MIN_LENGTH - 1) + "1")


def test_mat_khau_thieu_chu_hoac_thieu_so_bi_tu_choi():
    for raw in ("matkhaudai", "1234512345"):
        with pytest.raises(HTTPException) as e:
            validate_password(raw)
        assert "chữ và số" in e.value.detail


def test_mat_khau_vuot_72_byte_bi_tu_choi_vi_bcrypt_cat_am_tham():
    #  Đúng 72 byte thì qua; thêm một ký tự là bcrypt bắt đầu cắt âm thầm, tức hai
    #  mật khẩu khác nhau lại đăng nhập được vào nhau.
    assert validate_password("a" * (MAX_BYTES - 1) + "1")
    with pytest.raises(HTTPException) as e:
        validate_password("a" * MAX_BYTES + "1")
    assert "byte" in e.value.detail

    #  Tiếng Việt có dấu tốn 3 byte mỗi ký tự — 30 chữ cái mà đã quá trần.
    with pytest.raises(HTTPException):
        validate_password("ườ" * 30 + "1")


def test_khoang_trang_dau_cuoi_bi_tu_choi():
    for raw in (" matkhau1", "matkhau1 ", " matkhau1 "):
        with pytest.raises(HTTPException) as e:
            validate_password(raw)
        assert "khoảng trắng" in e.value.detail
    #  Khoảng trắng GIỮA vẫn hợp lệ — mật khẩu dạng câu là thứ nên khuyến khích.
    assert validate_password("mat khau dai 1")


def test_mat_khau_rong_bi_tu_choi():
    for raw in ("", "   ", None):
        with pytest.raises(HTTPException):
            validate_password(raw)


def test_mat_khau_pho_bien_bi_tu_choi():
    with pytest.raises(HTTPException) as e:
        validate_password("Password1")
    assert "phổ biến" in e.value.detail


def test_khong_duoc_chua_ma_nhan_vien_du_khac_hoa_thuong_va_dau():
    for raw in ("TESTREQ123", "xxtestreq99", "xxTeStReQ99"):
        with pytest.raises(HTTPException) as e:
            validate_password(raw, username="TESTREQ")
        assert "tên đăng nhập" in e.value.detail
    #  Bỏ dấu rồi mới so: `Nguyễn` và `nguyen` là cùng một chuỗi.
    with pytest.raises(HTTPException):
        validate_password("nguyen2026a", username="Nguyễn")


def test_khong_duoc_chua_email_hoac_phan_truoc_a_cong():
    with pytest.raises(HTTPException):
        validate_password("baotran2026", email="baotran@degoholding.vn")
    with pytest.raises(HTTPException):
        validate_password("xbaotran@degoholding.vn1", email="baotran@degoholding.vn")


def test_chuoi_ngu_canh_ngan_hon_3_ky_tu_khong_chan_nham():
    #  Mã nhân viên hai ký tự mà đem cấm-chứa thì bắt nhầm gần hết mật khẩu hợp lệ.
    assert validate_password("ab" + "cdef123", username="ab", email="a@x.vn")


# ── 2. Tầng cửa ─────────────────────────────────────────────────────────────────

def _new_employee(db, code="NEWEMP01", email="newemp01@degoholding.vn"):
    emp = Employee(code=code, full_name="Nhân Sự Mới", email=email, is_active=True)
    db.add(emp)
    db.flush()
    return emp


def test_cua_cap_tai_khoan_tu_choi_mat_khau_yeu(db, seed):
    emp = _new_employee(db)
    with pytest.raises(HTTPException) as e:
        user_service.provision_user(
            db, UserProvision(employee_id=emp.id, email=emp.email, password="123"), ACTOR)
    assert e.value.status_code == 400
    assert db.query(User).filter(User.employee_id == emp.id).first() is None

    #  Mật khẩu trùng ĐÚNG mã nhân viên — kiểu đặt của các tài khoản demo, và cũng
    #  chính là tên đăng nhập.
    with pytest.raises(HTTPException):
        user_service.provision_user(
            db, UserProvision(employee_id=emp.id, email=emp.email, password=emp.code + "2026"), ACTOR)

    user = user_service.provision_user(
        db, UserProvision(employee_id=emp.id, email=emp.email, password=GOOD), ACTOR)
    assert verify_password(GOOD, user.password_hash)


def test_cua_quan_tri_dat_lai_tu_choi_mat_khau_trung_ma_nhan_vien(db, seed):
    user = db.get(User, seed.u_req_id)
    truoc = user.password_hash

    with pytest.raises(HTTPException) as e:
        user_service.reset_password(db, user.id, "testreq2026", ACTOR)
    assert "tên đăng nhập" in e.value.detail
    db.refresh(user)
    assert user.password_hash == truoc

    user_service.reset_password(db, user.id, GOOD, ACTOR)
    db.refresh(user)
    assert verify_password(GOOD, user.password_hash)


def test_cua_tu_doi_mat_khau_tu_choi_mat_khau_yeu(db, seed):
    user = db.get(User, seed.u_req_id)
    user.password_hash = hash_password("Matkhaucu2026")
    db.commit()

    with pytest.raises(HTTPException) as e:
        auth_controller.change_password(
            ChangePasswordInput(old_password="Matkhaucu2026", new_password="abc123"), user, db)
    assert str(MIN_LENGTH) in e.value.detail
    db.refresh(user)
    assert verify_password("Matkhaucu2026", user.password_hash)

    auth_controller.change_password(
        ChangePasswordInput(old_password="Matkhaucu2026", new_password=GOOD), user, db)
    db.refresh(user)
    assert verify_password(GOOD, user.password_hash)


def test_cua_tu_doi_mat_khau_khong_con_cat_khoang_trang_am_tham(db, seed):
    #  Bản cũ `.strip()` mật khẩu mới: người dùng gõ dư một dấu cách sẽ nhận một mật
    #  khẩu khác cái họ vừa gõ, rồi lần sau dán lại y hệt là sai. Nay từ chối thẳng.
    user = db.get(User, seed.u_req_id)
    user.password_hash = hash_password("Matkhaucu2026")
    db.commit()

    with pytest.raises(HTTPException) as e:
        auth_controller.change_password(
            ChangePasswordInput(old_password="Matkhaucu2026", new_password=GOOD + " "), user, db)
    assert "khoảng trắng" in e.value.detail


def test_cua_tu_doi_mat_khau_da_co_luoc_do_thay_cho_dict_tran():
    #  Bản cũ nhận `dict`: thiếu trường thì `.get()` trả `None`, lỗi hiện ra thành
    #  "Mật khẩu hiện tại không đúng" — sai hẳn nguyên nhân.
    with pytest.raises(ValidationError):
        ChangePasswordInput(old_password="Matkhaucu2026")


def test_cua_dat_lai_qua_ve_email_tu_choi_mat_khau_yeu(db, seed):
    user = db.get(User, seed.u_req_id)
    user.password_hash = hash_password("Matkhaucu2026")
    db.commit()
    token = create_reset_token(user.id)
    #  Gỡ lớp `@limiter.limit` — trần tần suất không phải thứ ca này đo.
    endpoint = getattr(auth_controller.reset_password, "__wrapped__", auth_controller.reset_password)

    with pytest.raises(HTTPException) as e:
        endpoint(None, ResetPasswordInput(token=token, new_password="1"), db)
    assert e.value.status_code == 400
    db.refresh(user)
    assert verify_password("Matkhaucu2026", user.password_hash)

    endpoint(None, ResetPasswordInput(token=token, new_password=GOOD), db)
    db.refresh(user)
    assert verify_password(GOOD, user.password_hash)


def test_cua_dat_mat_khau_tu_ho_so_nhan_su_tu_choi_mat_khau_yeu(db, seed, cap_quyen):
    cap_quyen(seed.u_req_id, "employee", scope="all", read=True, write=True)
    actor = db.get(User, seed.u_req_id)
    emp = _new_employee(db, code="NEWEMP02", email="newemp02@degoholding.vn")

    with pytest.raises(HTTPException) as e:
        employee_set_password(emp.id, SetPasswordIn(password="abcd"), db, actor)
    assert str(MIN_LENGTH) in e.value.detail
    assert db.query(User).filter(User.employee_id == emp.id).first() is None

    employee_set_password(emp.id, SetPasswordIn(password=GOOD), db, actor)
    created = db.query(User).filter(User.employee_id == emp.id).first()
    assert created is not None and verify_password(GOOD, created.password_hash)


# ── 3. Không cửa nào lọt ────────────────────────────────────────────────────────

def test_moi_cua_bam_mat_khau_deu_di_qua_chinh_sach():
    """Hàm nào gọi `hash_password` thì phải gọi cả `validate_password`.

    Đây là cái chốt: BM-016 sống lâu vì luật nằm rải ở từng cửa, thêm cửa mới là
    quên. Nay quên sẽ đỏ ở đây. Chỉ quét `app/modules` — các script seed CỐ Ý đứng
    ngoài chính sách (đặt mật khẩu demo bằng mã tài khoản để dựng dữ liệu thử).
    """
    modules_dir = Path(app_package.__file__).resolve().parent / "modules"
    assert modules_dir.is_dir()

    thieu = []
    for path in sorted(modules_dir.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            goi = {c.func.id for c in ast.walk(node)
                   if isinstance(c, ast.Call) and isinstance(c.func, ast.Name)}
            if "hash_password" in goi and "validate_password" not in goi:
                thieu.append(f"{path.name}:{node.lineno} {node.name}")

    assert thieu == [], "Cửa đặt mật khẩu không đi qua chính sách: " + ", ".join(thieu)
