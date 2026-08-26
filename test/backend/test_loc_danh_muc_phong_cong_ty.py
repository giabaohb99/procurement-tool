"""Ô CHỌN trên thanh công cụ của hai màn danh mục: Phòng ban và Công ty.

Hai chuyện khác nhau nên gom một chỗ vì cùng một bài học:

1. **Công ty — `level`.** Chạy qua `apply_filters`, mà hàm đó chỉ so khớp chính xác cho
   `id` / `*_id`; cột số khác rơi vào nhánh `LIKE %val%`. Hôm nay cấp chỉ có 1..3 nên trông
   vẫn đúng, thêm cấp thứ 10 là lọc "cấp 1" kéo theo luôn cấp 10, 11, 21 — sai âm thầm.
   Nay MỌI cột số so khớp chính xác.

2. **Phòng ban — `kind` / `company_id`.** Endpoint này KHÔNG chạy qua `apply_filters` (nó tự
   đọc `q` để tìm chung tên phòng HOẶC tên trưởng bộ phận), nên thả tên cột vào `FILTERABLE`
   là param rơi vào khoảng không — đúng vết xe của `department_id` ở màn Nhân sự.

Gọi thẳng hàm lọc chứ không qua HTTP: bài kiểm nhắm vào mệnh đề WHERE sinh ra.
"""
from starlette.datastructures import QueryParams

from app.core.base_controller import apply_filters
from app.modules.company import service as company_service
from app.modules.company.model import Company
from app.modules.department import service as dept_service
from app.modules.department.model import Department, DepartmentCompany


class _Req:
    def __init__(self, **params):
        self.query_params = QueryParams(params)


PG = {"offset": 0, "limit": 50}


# ── Công ty: cột SỐ phải so khớp chính xác ───────────────────────────────────────
def _cty(db, code, *, level=2, is_active=True, name=None):
    c = Company(code=code, name=name or f"Cty {code}", level=level, is_active=is_active)
    db.add(c)
    db.commit()
    return c


def _loc_cty(db, **params):
    q = apply_filters(db.query(Company), Company, _Req(**params), company_service.FILTERABLE)
    return sorted(c.code for c in q.all())


def _park_seed_company(db, level=77):
    """Công ty của fixture `seed` mặc định `level=2`, nên nó lọt vào mọi phép lọc cấp 2.

    Đẩy nó sang một cấp không ai kiểm, để khẳng định đọc thẳng ra ý đồ thay vì phải kèm
    đuôi "…và CT01" ở từng dòng.
    """
    db.query(Company).filter(Company.code == "CT01").update({"level": level})
    db.commit()


def test_cap_phap_nhan_khong_vo_lay_cap_hai_chu_so(db, seed):
    """Đây là cái bẫy: `LIKE %1%` khớp luôn 10, 11, 21. Hệ mới chỉ có ba cấp nên hôm nay
    chưa lộ, nhưng cột `level` là SMALLINT — thêm cấp là vỡ mà không ai biết."""
    _cty(db, "C1", level=1)
    _cty(db, "C10", level=10)
    _cty(db, "C11", level=11)
    _cty(db, "C21", level=21)

    assert _loc_cty(db, level="1") == ["C1"]
    assert _loc_cty(db, level="10") == ["C10"]


def test_cap_loc_dung_ba_cap_that(db, seed):
    _park_seed_company(db)
    _cty(db, "TAP-DOAN", level=1)
    _cty(db, "THANH-VIEN-A", level=2)
    _cty(db, "THANH-VIEN-B", level=2)
    _cty(db, "TRUC-THUOC", level=3)

    assert _loc_cty(db, level="2") == ["THANH-VIEN-A", "THANH-VIEN-B"]
    assert _loc_cty(db, level="3") == ["TRUC-THUOC"]


def test_cap_rac_thi_bo_qua_chu_khong_vo_trang(db, seed):
    """Người dùng sửa tay URL là chuyện thường. Sai kiểu -> bỏ param, KHÔNG raise và cũng
    không được âm thầm trả về rỗng (rỗng thì người dùng tưởng không có dữ liệu)."""
    _cty(db, "C-A", level=1)
    _cty(db, "C-B", level=2)
    tat_ca = sorted([c.code for c in db.query(Company).all()])

    assert _loc_cty(db, level="abc") == tat_ca
    assert _loc_cty(db, level="") == tat_ca          # rỗng -> không lọc (nhánh có sẵn)
    assert _loc_cty(db, level="1.5") == tat_ca       # không phải số nguyên -> bỏ qua
    assert _loc_cty(db, level="  ") == tat_ca        # toàn khoảng trắng
    assert _loc_cty(db, level="1e2") == tat_ca
    assert _loc_cty(db, level="-") == tat_ca


def test_cap_so_am_va_so_khong_van_la_loc_that(db, seed):
    """`0` và số âm là GIÁ TRỊ hợp lệ về cú pháp, không phải "bỏ trống" — phải lọc thật
    (ra rỗng cũng được), đừng lẳng lặng biến thành "không lọc"."""
    _cty(db, "C-0", level=0)
    _cty(db, "C-AM", level=-1)
    _cty(db, "C-2", level=2)

    assert _loc_cty(db, level="0") == ["C-0"]
    assert _loc_cty(db, level="-1") == ["C-AM"]
    assert _loc_cty(db, level="99") == []


def test_cap_cat_khoang_trang_thua(db, seed):
    """`apply_filters` strip param trước khi so — giữ nguyên hành vi đó cho cột số."""
    _park_seed_company(db)
    _cty(db, "C-2", level=2)
    assert _loc_cty(db, level=" 2 ") == ["C-2"]


def test_cap_ket_hop_voi_trang_thai_va_ten(db, seed):
    """Ba ô lọc nối bằng AND. Cột chữ vẫn LIKE, cột số đã exact, cột bool vẫn bool."""
    _park_seed_company(db)
    _cty(db, "C-ON", level=2, is_active=True, name="Dego Miền Nam")
    _cty(db, "C-OFF", level=2, is_active=False, name="Dego Miền Bắc")
    _cty(db, "C-KHAC", level=1, is_active=True, name="Dego Miền Trung")

    assert _loc_cty(db, level="2", is_active="true") == ["C-ON"]
    assert _loc_cty(db, level="2", name="Miền") == ["C-OFF", "C-ON"]
    assert _loc_cty(db, level="2", is_active="false", name="Bắc") == ["C-OFF"]


def test_cot_chu_van_LIKE_nhu_cu(db, seed):
    """Không được "sửa cột số" xong làm luôn cột chữ thành exact — ô tìm kiếm sống bằng LIKE."""
    _cty(db, "C-X", name="Công ty Cổ phần ABC")
    assert _loc_cty(db, name="Cổ phần") == ["C-X"]


# ── Phòng ban: kind + company_id ─────────────────────────────────────────────────
def _phong(db, code, *, name=None, kind=1, company_id=0, is_active=True, manager_id=0):
    d = Department(code=code, name=name or f"Phòng {code}", kind=kind,
                   company_id=company_id, is_active=is_active, manager_id=manager_id)
    db.add(d)
    db.commit()
    return d


def _gan_phap_nhan(db, dept_id, company_id, is_active=True):
    db.add(DepartmentCompany(department_id=dept_id, company_id=company_id, is_active=is_active))
    db.commit()


def _loc_phong(db, **kw):
    total, items = dept_service.list_departments(db, kw.pop("q", None), PG, **kw)
    ma = sorted(d.code for d in items)
    assert total == len(ma), "total phải đếm SAU khi lọc, nếu không số trang lệch số dòng"
    return ma


def test_loai_don_vi_loc_dung(db, seed):
    _phong(db, "P-CN", kind=1)
    _phong(db, "P-KD", kind=2)
    _phong(db, "P-DA", kind=3)

    assert _loc_phong(db, kind=2) == ["P-KD"]
    assert _loc_phong(db, kind=3) == ["P-DA"]


def test_loai_don_vi_bo_trong_thi_khong_loc(db, seed):
    """`None` = ô chọn đang ở "Tất cả loại đơn vị". `0` cũng vậy: không có loại 0, mà để nó
    lọc thật thì màn hình trắng trơn — người dùng tưởng mất dữ liệu."""
    _phong(db, "P-CN", kind=1)
    _phong(db, "P-KD", kind=2)

    assert "P-KD" in _loc_phong(db, kind=None)
    assert "P-KD" in _loc_phong(db)
    assert "P-KD" in _loc_phong(db, kind=0)


def test_loai_don_vi_khong_ton_tai_thi_rong(db, seed):
    _phong(db, "P-CN", kind=1)
    assert _loc_phong(db, kind=9) == []


def test_phap_nhan_loc_theo_phap_nhan_GOC(db, seed):
    khac = _cty(db, "CT-KHAC")
    _phong(db, "P-GOC", company_id=seed.company_id)
    _phong(db, "P-KHAC", company_id=khac.id)

    assert "P-GOC" in _loc_phong(db, company_id=seed.company_id)
    assert "P-KHAC" not in _loc_phong(db, company_id=seed.company_id)


def test_phap_nhan_thay_ca_phong_DUNG_CHUNG_qua_bang_anh_xa(db, seed):
    """A06: một phòng hiện diện ở nhiều pháp nhân qua `tab_department_company`, còn
    `Department.company_id` chỉ là pháp nhân GỐC. Chỉ lọc theo cột gốc là 12 pháp nhân kia
    coi như không có phòng đó — đúng thứ khối phạm vi văn bản đã phải gộp hai nguồn."""
    khac = _cty(db, "CT-KHAC")
    chung = _phong(db, "P-DUNG-CHUNG", company_id=seed.company_id)
    _gan_phap_nhan(db, chung.id, khac.id)

    assert "P-DUNG-CHUNG" in _loc_phong(db, company_id=khac.id)
    assert "P-DUNG-CHUNG" in _loc_phong(db, company_id=seed.company_id)


def test_dong_anh_xa_da_TAT_thi_khong_tinh(db, seed):
    """Gỡ phòng khỏi một pháp nhân = tắt dòng ánh xạ. Vẫn đếm nó là "hiện diện" thì việc gỡ
    thành ra không có tác dụng gì."""
    khac = _cty(db, "CT-KHAC")
    chung = _phong(db, "P-DA-GO", company_id=seed.company_id)
    _gan_phap_nhan(db, chung.id, khac.id, is_active=False)

    assert _loc_phong(db, company_id=khac.id) == []


def test_vua_o_goc_vua_co_anh_xa_thi_KHONG_nhan_doi_dong(db, seed):
    """Nếu lỡ viết bằng JOIN thay vì `IN (subquery)` thì phòng có hai dòng ánh xạ sẽ hiện
    hai lần, và `total` đếm thừa — phân trang lệch ngay trang đầu."""
    chung = _phong(db, "P-CA-HAI", company_id=seed.company_id)
    _gan_phap_nhan(db, chung.id, seed.company_id)

    assert _loc_phong(db, company_id=seed.company_id).count("P-CA-HAI") == 1


def test_phap_nhan_khong_ton_tai_thi_rong(db, seed):
    _phong(db, "P-A", company_id=seed.company_id)
    assert _loc_phong(db, company_id=999999) == []


def test_phap_nhan_bo_trong_thi_khong_loc(db, seed):
    """`0` là "chưa gán pháp nhân" ở cột `company_id`, KHÔNG phải một pháp nhân có thật —
    coi như ô chọn đang để "Tất cả pháp nhân"."""
    _phong(db, "P-CHUA-GAN", company_id=0)
    _phong(db, "P-CO-GAN", company_id=seed.company_id)

    assert "P-CHUA-GAN" in _loc_phong(db, company_id=None)
    assert "P-CHUA-GAN" in _loc_phong(db, company_id=0)


def test_bon_o_loc_cua_phong_ban_noi_bang_AND(db, seed):
    """Ô tìm kiếm + Loại đơn vị + Pháp nhân + Trạng thái cùng bật một lúc."""
    khac = _cty(db, "CT-KHAC")
    _phong(db, "P-DUNG", name="Phòng Kinh doanh", kind=2, company_id=seed.company_id)
    _phong(db, "P-SAI-LOAI", name="Phòng Kinh doanh", kind=1, company_id=seed.company_id)
    _phong(db, "P-SAI-CTY", name="Phòng Kinh doanh", kind=2, company_id=khac.id)
    _phong(db, "P-SAI-TEN", name="Phòng Kho vận", kind=2, company_id=seed.company_id)
    _phong(db, "P-DA-AN", name="Phòng Kinh doanh", kind=2, company_id=seed.company_id,
           is_active=False)

    assert _loc_phong(db, q="Kinh doanh", kind=2, company_id=seed.company_id,
                      is_active=True) == ["P-DUNG"]


def test_o_tim_kiem_theo_TRUONG_BO_PHAN_van_chay_cung_cac_select_moi(db, seed):
    """`q` khớp tên phòng HOẶC tên trưởng bộ phận (join sang bảng nhân sự). Thêm hai select
    mới mà lỡ đặt sau `count()` hoặc làm hỏng join là ô tìm kiếm chết theo."""
    _phong(db, "P-CO-TRUONG", name="Phòng Không Trùng Tên", kind=2,
           company_id=seed.company_id, manager_id=seed.emp_tp_id)
    _phong(db, "P-KHONG", name="Phòng Khác", kind=2, company_id=seed.company_id)

    assert _loc_phong(db, q="Trưởng Phòng", kind=2) == ["P-CO-TRUONG"]


def test_phan_trang_dem_dung_sau_khi_loc(db, seed):
    """`total` phải là số dòng SAU khi lọc; đếm trước là người dùng thấy "Tổng 30" rồi bấm
    sang trang 2 thì trống trơn."""
    for i in range(5):
        _phong(db, f"P-KD-{i}", kind=2, company_id=seed.company_id)
    _phong(db, "P-CN", kind=1, company_id=seed.company_id)

    total, items = dept_service.list_departments(db, None, {"offset": 0, "limit": 2},
                                                 kind=2, company_id=seed.company_id)
    assert total == 5
    assert len(items) == 2


def test_hai_cot_moi_van_nam_trong_whitelist_bo_loc_dieu_kien(db, seed):
    """`kind`/`company_id` vẫn phải dùng được ở BỘ LỌC NÂNG CAO (`kind__eq=2`) — hai đường
    khác nhau, đừng sửa đường này làm rụng đường kia."""
    assert "kind" in dept_service.FILTERABLE
    assert "company_id" in dept_service.FILTERABLE
    assert "level" in company_service.FILTERABLE

    _phong(db, "P-KD", kind=2)
    _phong(db, "P-CN", kind=1)

    total, items = dept_service.list_departments(db, None, PG, request=_Req(kind__eq="2"))
    assert [d.code for d in items] == ["P-KD"] and total == 1
