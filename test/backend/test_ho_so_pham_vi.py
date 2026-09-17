"""PHẠM VI DỮ LIỆU của HỒ SƠ — `apply_scope` trên `tab_dossier` (16/09/2026).

Đây là bài kiểm mà dòng miễn trừ BB-4 của `dossier/controller.py` trỏ tới. Tệp
controller đó chỉ có đúng một lời gọi `make_crud_router`, nên grep không thấy
`apply_scope` và luật bất biến BB-4 phải bỏ qua nó — **bù lại thì chỗ này phải
chứng minh phạm vi có chạy thật**, bằng cách đọc ra tập id chứ không bằng cách
khẳng định "có sinh ra điều kiện".

Hồ sơ khai BỐN chiều, và mỗi chiều hỏng theo một kiểu riêng:

    company  → company_id          bật đa pháp nhân thì rò ngang
    dept_id  → department_id       hành chính phòng này đọc giấy tờ phòng kia
    owner    → created_by          người NHẬP HỘ mất dấu hồ sơ mình vừa nhập
    self     → owner_employee_id   người ĐƯỢC GIAO theo dõi không mở được hồ sơ

⚠️ Hai chiều cuối là cặp — xem ghi chú dài ở `core/scoping.py`. Bỏ một trong hai
thì bài kiểm `test_own_hop_ca_nguoi_lap_lan_nguoi_phu_trach` đỏ.
"""
import pytest

from app.modules.dossier.model import Dossier


@pytest.fixture
def ho_so(db, world):
    """Bốn bộ hồ sơ trải đủ bốn chiều, trả về {nhãn: id}."""
    rows = {
        #  Của phòng Kế toán công ty A, a1 lập, a1 phụ trách.
        "A.kt/a1": Dossier(code="HS1", name="Giấy phép A-KT", dossier_type_id=1,
                           company_id=world.co["A"], department_id=world.dept["A.kt"],
                           created_by=world.user_id("a1"),
                           owner_employee_id=world.emp["a1"]),
        #  Cùng công ty A nhưng PHÒNG KHÁC.
        "A.mua/a3": Dossier(code="HS2", name="Giấy phép A-Mua", dossier_type_id=1,
                            company_id=world.co["A"], department_id=world.dept["A.mua"],
                            created_by=world.user_id("a3"),
                            owner_employee_id=world.emp["a3"]),
        #  Công ty B.
        "B.kt/b1": Dossier(code="HS3", name="Giấy phép B-KT", dossier_type_id=1,
                           company_id=world.co["B"], department_id=world.dept["B.kt"],
                           created_by=world.user_id("b1"),
                           owner_employee_id=world.emp["b1"]),
        #  ⚠️ Ca hỏng quan trọng nhất: hồ sơ CHƯA GẮN ai cả. `owner_employee_id`
        #  và `department_id` đều `0` — đúng giá trị mà một điều kiện `== 0`
        #  viết ẩu sẽ trúng.
        "chuagan": Dossier(code="HS4", name="Hồ sơ chưa gắn ai", dossier_type_id=1,
                           company_id=0, department_id=0, created_by=0,
                           owner_employee_id=0),
    }
    db.add_all(rows.values())
    db.flush()
    return {k: v.id for k, v in rows.items()}


def test_all_thay_het(world, ho_so):
    a1 = world.grant("a1", "dossier", scope="all")
    assert a1.sees(Dossier) == set(ho_so.values())


def test_company_chi_thay_phap_nhan_minh(world, ho_so):
    """Rò ngang giữa hai pháp nhân là ca lộ nghiêm trọng nhất của phân hệ này."""
    a1 = world.grant("a1", "dossier", scope="company")
    assert a1.sees(Dossier) == {ho_so["A.kt/a1"], ho_so["A.mua/a3"]}
    assert a1.can_get(Dossier, ho_so["B.kt/b1"]) is False, "gõ id vào URL không được lọt"


def test_dept_chi_thay_phong_minh(world, ho_so):
    """Hành chính phòng Kế toán không đọc giấy tờ phòng Thu mua."""
    a1 = world.grant("a1", "dossier", scope="dept")
    assert a1.sees(Dossier) == {ho_so["A.kt/a1"]}
    assert a1.can_get(Dossier, ho_so["A.mua/a3"]) is False


def test_own_hop_ca_nguoi_lap_lan_nguoi_phu_trach(db, world, ho_so):
    """⚠️ Lý do `dossier` khai CẢ `owner` LẪN `self`.

    Một bộ hồ sơ có HAI người dính tới nó. Khai thiếu `self` thì người được giao
    theo dõi hồ sơ **không mở được chính hồ sơ ấy** — bộ máy giao việc cho người
    ta rồi chặn đúng người được giao. Khai thiếu `owner` thì hành chính nhập hộ
    xong mất dấu thứ mình vừa nhập.
    """
    #  a2 không lập tờ nào, nhưng được giao phụ trách một tờ do a1 lập.
    giao = Dossier(code="HS9", name="a1 lập, a2 phụ trách", dossier_type_id=1,
                   company_id=world.co["A"], department_id=world.dept["A.kt"],
                   created_by=world.user_id("a1"), owner_employee_id=world.emp["a2"])
    db.add(giao)
    db.flush()

    a2 = world.grant("a2", "dossier", scope="own")
    assert a2.sees(Dossier) == {giao.id}, "người phụ trách phải thấy hồ sơ được giao"

    a1 = world.grant("a1", "dossier", scope="own")
    assert a1.sees(Dossier) == {ho_so["A.kt/a1"], giao.id}, "người lập vẫn thấy tờ mình nhập"


def test_own_khong_vo_tay_om_moi_ho_so_chua_gan_ai(world, ho_so):
    """⚠️ Bẫy `== 0` — thứ nhánh `own` của `_role_scope_cond` sinh ra để chặn.

    `owner_employee_id = 0` là giá trị của MỌI hồ sơ chưa gắn người phụ trách.
    Điều kiện `owner_employee_id == <employee_id của tôi>` mà `employee_id` cũng
    bằng 0 (tài khoản chưa gắn hồ sơ nhân sự) thì nó trúng hết — tức là **mở
    rộng** phạm vi thay vì thu hẹp, đúng ngược ý người đặt phạm vi `own`.
    """
    #  `khongcty` có tài khoản nhưng KHÔNG gắn pháp nhân — vẫn có employee_id
    #  thật, nên nhánh `self` so đúng và không trúng dòng `0`.
    kc = world.grant("khongcty", "dossier", scope="own")
    assert ho_so["chuagan"] not in kc.sees(Dossier)
    assert kc.sees(Dossier) == set(), "chưa lập tờ nào thì không thấy tờ nào"


def test_dept_chua_gan_phong_thi_chan_chu_khong_mo(world, ho_so):
    """Thiếu dữ liệu thì CHẶN, đúng tinh thần B-07 — không nới ra."""
    kp = world.grant("khongphong", "dossier", scope="dept")
    assert kp.sees(Dossier) == set()
    assert ho_so["chuagan"] not in kp.sees(Dossier), (
        "hồ sơ department_id = 0 không được coi là 'cùng phòng' với người chưa gắn phòng"
    )


def test_hai_vai_tro_thi_HOP_pham_vi(world, ho_so):
    """Nhiều grant trên cùng entity phải HỢP (OR), không phải GIAO."""
    a1 = world.grant("a1", "dossier", scope="dept")
    assert a1.sees(Dossier) == {ho_so["A.kt/a1"]}
    a1.grant("dossier", scope="company")
    assert a1.sees(Dossier) == {ho_so["A.kt/a1"], ho_so["A.mua/a3"]}


def test_khong_co_grant_thi_khong_thay_gi(world, ho_so):
    """Người chưa được cấp khóa `dossier` không đọc được hồ sơ nào."""
    b1 = world.grant("b1", "dossier_type", scope="all")   # khóa KHÁC
    assert b1.sees(Dossier, entity="dossier") == set()


def test_sua_va_xoa_cung_chiu_pham_vi(world, ho_so):
    """Phạm vi phải áp cho CẢ ba hành động, không riêng `read`.

    Lọt một cửa là đủ: đọc bị chặn nhưng `PATCH`/`DELETE` bằng id vẫn lọt thì
    người ta sửa được hồ sơ mình không được xem.
    """
    a1 = world.grant("a1", "dossier", scope="dept", actions=("read", "write", "delete"))
    ngoai = ho_so["A.mua/a3"]
    for action in ("read", "write", "delete"):
        assert a1.can_get(Dossier, ngoai, action=action) is False, (
            f"hành động '{action}' lọt qua phạm vi"
        )
