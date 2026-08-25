"""KIÊM NHIỆM PHÒNG BAN — một nhân sự thuộc nhiều phòng (CR-167).

Hai nửa của tệp này, và nửa sau mới là nửa nguy hiểm:

**Nửa CHỨC NĂNG** — kiêm nhiệm phải mở đúng phạm vi dữ liệu. Người phụ trách hai
bộ phận mà chỉ thấy phiếu của một bộ phận thì tính năng vô nghĩa.

**Nửa CHỐNG VƯỢT QUYỀN** — gán phòng ban KHÔNG phải thao tác hành chính vô hại.
Phạm vi dữ liệu bậc *phòng ban* đọc thẳng từ bảng này, nên thêm một phòng cho ai
đó là **mở rộng tầm nhìn dữ liệu của họ** — đúng bằng việc tick thêm một ô trong
ma trận quyền, chỉ là qua một cửa trông hiền lành hơn.

Mỗi chốt chặn đều có **cặp đối chứng** ở chiều ngược: chặn sạch thì bài nào cũng
xanh mà tính năng thì chết.
"""
import pytest
from fastapi import HTTPException

from app.core.auth import get_perm_profile, perm_cache_clear
from app.modules.department.model import Department
from app.modules.employee import department_service as dv
from app.modules.employee.department_model import EmployeeDepartment
from app.modules.employee.model import Employee
from app.modules.user.model import User

ACTOR = 1


@pytest.fixture()
def san(db, seed):
    """Ba phòng cùng pháp nhân + một phòng của pháp nhân KHÁC."""
    phong = {}
    for ma, ten, company_id in (("P_KT", "Phòng Kế toán", seed.company_id),
                                ("P_IT", "Phòng CNTT", seed.company_id),
                                ("P_NS", "Phòng Nhân sự", seed.company_id),
                                ("P_LA", "Phòng của pháp nhân khác", seed.company_id + 99)):
        row = Department(code=ma, name=ten, company_id=company_id, is_active=True)
        db.add(row)
        db.flush()
        phong[ma] = row.id

    nguoi = Employee(code="KN_A", full_name="Người kiêm nhiệm",
                     company_id=seed.company_id, department_id=phong["P_KT"],
                     is_active=True)
    db.add(nguoi)
    db.flush()
    tai_khoan = User(email="kn_a@test.local", employee_id=nguoi.id,
                     password_hash="x", is_active=True)
    db.add(tai_khoan)
    db.flush()
    db.add(EmployeeDepartment(employee_id=nguoi.id, department_id=phong["P_KT"],
                              is_primary=True, created_by=ACTOR, updated_by=ACTOR))
    db.commit()
    return {"phong": phong, "nguoi": nguoi, "tai_khoan": tai_khoan}


# ── Đọc / ghi ───────────────────────────────────────────────────────────────

def test_phong_chinh_luon_dung_dau_danh_sach(db, san):
    """Thứ tự có nghĩa: nơi nào chỉ dùng được MỘT phòng thì lấy phần tử đầu."""
    dv.dat_phong_ban(db, san["nguoi"],
                     [san["phong"]["P_IT"], san["phong"]["P_KT"], san["phong"]["P_NS"]],
                     ACTOR, phong_chinh=san["phong"]["P_NS"])
    db.commit()

    assert dv.phong_ban_cua(db, san["nguoi"].id)[0] == san["phong"]["P_NS"]


def test_cot_cu_department_id_luon_khop_phong_chinh(db, san):
    """12 chỗ trong mã còn đọc `tab_employee.department_id`.

    Hai nguồn lệch nhau là bối cảnh phiếu, thông báo cho trưởng phòng và dấu vết
    cùng chỉ sai một lúc — mà không chỗ nào báo.
    """
    dv.dat_phong_ban(db, san["nguoi"], [san["phong"]["P_IT"], san["phong"]["P_KT"]], ACTOR)
    db.commit()

    assert san["nguoi"].department_id == san["phong"]["P_IT"]


def test_dat_lai_thi_THAY_THE_chu_khong_cong_don(db, san):
    dv.dat_phong_ban(db, san["nguoi"], [san["phong"]["P_IT"], san["phong"]["P_NS"]], ACTOR)
    db.commit()
    dv.dat_phong_ban(db, san["nguoi"], [san["phong"]["P_KT"]], ACTOR)
    db.commit()

    assert dv.phong_ban_cua(db, san["nguoi"].id) == [san["phong"]["P_KT"]]


def test_khai_trung_mot_phong_hai_lan_chi_luu_mot(db, san):
    dv.dat_phong_ban(db, san["nguoi"],
                     [san["phong"]["P_KT"], san["phong"]["P_KT"]], ACTOR)
    db.commit()

    assert dv.phong_ban_cua(db, san["nguoi"].id) == [san["phong"]["P_KT"]]


def test_go_khoi_moi_phong_van_hop_le(db, san):
    """Nhân sự chưa phân công là trạng thái có thật, không phải lỗi."""
    dv.dat_phong_ban(db, san["nguoi"], [], ACTOR)
    db.commit()

    assert dv.phong_ban_cua(db, san["nguoi"].id) == []
    assert san["nguoi"].department_id == 0


def test_nhan_su_cua_phong_tinh_ca_nguoi_KIEM_NHIEM(db, san):
    """Truy vấn cũ lọc `Employee.department_id == X` nên bỏ sót người kiêm nhiệm.

    Hệ quả: thông báo gửi cho «trưởng phòng CNTT» không tới người kiêm nhiệm
    phòng đó, và quân số phòng đếm thiếu.
    """
    dv.dat_phong_ban(db, san["nguoi"], [san["phong"]["P_KT"], san["phong"]["P_IT"]], ACTOR)
    db.commit()

    assert san["nguoi"].id in dv.nhan_su_cua_phong(db, san["phong"]["P_IT"])


# ── L3: phòng phải có thật, cùng pháp nhân ──────────────────────────────────

def test_phong_khong_ton_tai_bi_chan(db, san):
    """`tab_employee_department` không có khóa ngoại — id rác ghi vào được."""
    with pytest.raises(HTTPException) as loi:
        dv.dat_phong_ban(db, san["nguoi"], [999999], ACTOR)
    assert loi.value.status_code == 400


def test_phong_cua_PHAP_NHAN_KHAC_bi_chan(db, san):
    """Gán chéo pháp nhân là mở dữ liệu xuyên pháp nhân bằng một dòng."""
    with pytest.raises(HTTPException) as loi:
        dv.dat_phong_ban(db, san["nguoi"],
                         [san["phong"]["P_KT"], san["phong"]["P_LA"]], ACTOR)
    assert loi.value.status_code == 400
    assert "pháp nhân khác" in str(loi.value.detail)


# ── L1: không tự sửa phòng ban của chính mình ───────────────────────────────

def test_khong_tu_doi_phong_ban_cua_chinh_minh(db, san):
    """Vai trò `employee.write` phạm vi *own* là có thật (tự sửa hồ sơ mình).

    Không có chốt này thì tự thêm phòng cho mình là xong — không cần đụng tới
    màn Phân quyền. Cùng tinh thần với `core/privilege_escalation` (CR-158).
    """
    with pytest.raises(HTTPException) as loi:
        dv.chan_tu_sua_phong_ban_cua_minh(db, san["nguoi"].id, san["tai_khoan"])
    assert loi.value.status_code == 403


def test_van_sua_duoc_cho_NGUOI_KHAC(db, san):
    """Chốt trên chỉ chặn đúng chiều tự-mình."""
    dv.chan_tu_sua_phong_ban_cua_minh(db, san["nguoi"].id + 999, san["tai_khoan"])


# ── L2: chỉ gán được phòng trong tầm của mình ───────────────────────────────

def _profile_gia(bac: str, dept_ids=None, company_id=0, cap_them=None):
    """Hồ sơ quyền tối thiểu — `chan_gan_phong_ngoai_tam` chỉ đọc mấy khóa này."""
    return {
        "grants": [{"role_id": 1,
                    "perms": {"employee": {"write": True, "read": True, "scope": bac}},
                    "scope": {"inc": {"department": cap_them or []}, "exc": {}}}],
        "company_id": company_id,
        "dept_ids": dept_ids or [],
        "dept_id": (dept_ids or [0])[0],
    }


def test_pham_vi_TAT_CA_thi_gan_duoc_moi_phong(db, san):
    dv.chan_gan_phong_ngoai_tam(db, list(san["phong"].values()), None,
                                _profile_gia("all"))


def test_pham_vi_PHONG_BAN_chi_gan_duoc_phong_cua_chinh_minh(db, san):
    """Không có chốt này thì người quản lý phạm vi *phòng ban* dựng ra được một
    người có tầm nhìn rộng hơn mình, rồi nhờ người đó xem hộ."""
    profile = _profile_gia("dept", dept_ids=[san["phong"]["P_KT"]])

    with pytest.raises(HTTPException) as loi:
        dv.chan_gan_phong_ngoai_tam(db, [san["phong"]["P_NS"]], None, profile)
    assert loi.value.status_code == 403


def test_pham_vi_PHONG_BAN_VAN_gan_duoc_phong_cua_minh(db, san):
    """CẶP ĐỐI CHỨNG — chặn nhầm ca này là người quản lý nhân sự phòng Kế toán
    không gán nổi chính phòng Kế toán, và họ sẽ đòi gỡ chốt."""
    dv.chan_gan_phong_ngoai_tam(db, [san["phong"]["P_KT"]], None,
                                _profile_gia("dept", dept_ids=[san["phong"]["P_KT"]]))


def test_phong_duoc_CAP_THEM_dich_danh_cung_gan_duoc(db, san):
    """Màn Phân quyền cấp thêm phòng cho một tài khoản — phải tính vào tầm."""
    profile = _profile_gia("dept", dept_ids=[san["phong"]["P_KT"]],
                           cap_them=[san["phong"]["P_NS"]])
    dv.chan_gan_phong_ngoai_tam(db, [san["phong"]["P_NS"]], None, profile)


def test_pham_vi_CONG_TY_gan_duoc_moi_phong_trong_phap_nhan(db, san, seed):
    profile = _profile_gia("company", company_id=seed.company_id)
    dv.chan_gan_phong_ngoai_tam(db, [san["phong"]["P_NS"], san["phong"]["P_IT"]],
                                None, profile)

    with pytest.raises(HTTPException):
        dv.chan_gan_phong_ngoai_tam(db, [san["phong"]["P_LA"]], None, profile)


def test_khong_co_quyen_ghi_thi_khong_gan_duoc_gi(db, san):
    profile = {"grants": [], "company_id": 0, "dept_ids": [], "dept_id": 0}
    with pytest.raises(HTTPException):
        dv.chan_gan_phong_ngoai_tam(db, [san["phong"]["P_KT"]], None, profile)


# ── Hồ sơ quyền: kiêm nhiệm mở đúng phạm vi ─────────────────────────────────

def test_ho_so_quyen_liet_ke_DU_cac_phong(db, san):
    dv.dat_phong_ban(db, san["nguoi"],
                     [san["phong"]["P_KT"], san["phong"]["P_IT"]], ACTOR)
    db.commit()
    perm_cache_clear(san["tai_khoan"].id)

    profile = get_perm_profile(db, san["tai_khoan"])
    assert set(profile["dept_ids"]) == {san["phong"]["P_KT"], san["phong"]["P_IT"]}
    assert profile["dept_id"] == san["phong"]["P_KT"], "số ít vẫn là phòng CHÍNH"
    assert len(profile["dept_names"]) == 2


def test_chua_co_dong_kiem_nhiem_thi_LUI_ve_phong_chinh(db, san):
    """Hồ sơ tạo trước migration, hoặc dữ liệu nhập tay thẳng vào `tab_employee`.

    Thiếu nhánh lùi này là những người đó mất SẠCH phạm vi phòng ban — hỏng nặng
    hơn hẳn thứ đang thêm.
    """
    db.query(EmployeeDepartment).filter(
        EmployeeDepartment.employee_id == san["nguoi"].id).delete()
    db.commit()
    perm_cache_clear(san["tai_khoan"].id)

    profile = get_perm_profile(db, san["tai_khoan"])
    assert profile["dept_ids"] == [san["phong"]["P_KT"]]


def test_doi_phong_ban_thi_XOA_CACHE_quyen(db, san):
    """Hồ sơ quyền nhớ 60 giây. Không xóa là người vừa được thêm phòng vẫn nhìn
    bằng tầm cũ suốt một phút, còn người vừa bị gỡ thì vẫn đọc được."""
    perm_cache_clear()
    get_perm_profile(db, san["tai_khoan"])          # nạp vào cache

    dv.dat_phong_ban(db, san["nguoi"],
                     [san["phong"]["P_KT"], san["phong"]["P_IT"]], ACTOR)
    db.commit()

    profile = get_perm_profile(db, san["tai_khoan"])
    assert set(profile["dept_ids"]) == {san["phong"]["P_KT"], san["phong"]["P_IT"]}


def test_chia_van_ban_theo_phong_tinh_ca_phong_kiem_nhiem(db, san):
    """Chia văn bản cho «phòng Kế toán» thì người kiêm nhiệm phòng đó phải nhận,
    dù phòng CHÍNH của họ là phòng khác."""
    from app.modules.document.access_model import SUBJECT_DEPARTMENT
    from app.modules.document.access_service import subject_pairs

    dv.dat_phong_ban(db, san["nguoi"],
                     [san["phong"]["P_IT"], san["phong"]["P_KT"]], ACTOR)
    db.commit()
    perm_cache_clear(san["tai_khoan"].id)

    pairs = subject_pairs(get_perm_profile(db, san["tai_khoan"]))
    theo_phong = {sid for kind, sid in pairs if kind == SUBJECT_DEPARTMENT}
    assert theo_phong == {san["phong"]["P_IT"], san["phong"]["P_KT"]}


# ── Hai nguồn ghi phòng ban không được trôi khỏi nhau ────────────────────────

def test_doi_department_id_qua_man_ho_so_thi_bang_kiem_nhiem_theo_kip(db, san):
    """⚠️ Có HAI nguồn ghi phòng ban: cửa riêng, và cột `department_id` mà màn hồ
    sơ / CSV import / seed vẫn ghi thẳng.

    Không nối hai nguồn thì chúng trôi khỏi nhau — hồ sơ hiện một phòng, phạm vi
    dữ liệu chạy theo phòng khác, mà không chỗ nào báo.
    """
    from app.modules.employee import service as emp_service
    from app.modules.employee.schema import EmployeeUpdate

    emp_service.update_employee(
        db, san["nguoi"].id,
        EmployeeUpdate(department_id=san["phong"]["P_IT"]), ACTOR)

    assert dv.phong_ban_cua(db, san["nguoi"].id)[0] == san["phong"]["P_IT"]


def test_doi_phong_chinh_KHONG_lam_mat_phong_kiem_nhiem(db, san):
    """Đổi phòng chính là đổi một dòng, không phải dựng lại cả danh sách."""
    from app.modules.employee import service as emp_service
    from app.modules.employee.schema import EmployeeUpdate

    dv.dat_phong_ban(db, san["nguoi"],
                     [san["phong"]["P_KT"], san["phong"]["P_NS"]], ACTOR)
    db.commit()

    emp_service.update_employee(
        db, san["nguoi"].id,
        EmployeeUpdate(department_id=san["phong"]["P_IT"]), ACTOR)

    con_lai = dv.phong_ban_cua(db, san["nguoi"].id)
    assert con_lai[0] == san["phong"]["P_IT"], "phòng chính đổi theo"
    assert san["phong"]["P_NS"] in con_lai, "phòng kiêm nhiệm phải còn"


def test_tao_moi_nhan_su_co_luon_dong_kiem_nhiem(db, seed, san):
    """Không sinh dòng lúc tạo thì người mới không có phạm vi phòng ban nào."""
    from app.modules.employee import service as emp_service
    from app.modules.employee.schema import EmployeeCreate

    moi = emp_service.create_employee(db, EmployeeCreate(
        code="KN_MOI", full_name="Người mới", company_id=seed.company_id,
        department_id=san["phong"]["P_KT"]), ACTOR)

    assert dv.phong_ban_cua(db, moi.id) == [san["phong"]["P_KT"]]
