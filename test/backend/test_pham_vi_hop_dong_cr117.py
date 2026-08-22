"""CR-117 — HỢP ĐỒNG PHẢI LỌC THEO PHẠM VI DỮ LIỆU.

Lỗ hổng đã có: entity `contract` KHÔNG nằm trong `SCOPE_FIELDS`, nên `_role_scope_cond`
trả `None` — ai có `contract.read` là đọc hợp đồng của MỌI pháp nhân, kể cả khi phạm vi
vai trò đặt là `company` hay `own`. Tệ hơn, `contract/controller.py` không gọi
`apply_scope` ở bất kỳ route nào, nên chỉ khai thêm vào `SCOPE_FIELDS` là chưa đủ.

Bài này chốt hai tầng:

```
tầng lọc      →  apply_scope(Contract, "contract", …) thật sự sinh mệnh đề WHERE
tầng route    →  get/patch/delete/xóa hàng loạt đều đi qua bộ lọc đó, không db.get trần
```

Gọi thẳng hàm chứ không qua HTTP: bài kiểm nhắm vào mệnh đề WHERE và nhánh 403,
đi vòng qua TestClient chỉ thêm lớp xác thực không liên quan.
"""
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.core.scoping import SCOPE_FIELDS, apply_scope
from app.modules.contract import controller as ct
from app.modules.contract.model import Contract

USER_ID = 10
CTY_A, CTY_B = 101, 202

_ACTIONS = ("read", "create", "write", "delete", "approve", "cancel", "print", "export")


def _profile(scope="company", company_id=CTY_A, inc=None, exc=None):
    """Hồ sơ quyền tối thiểu, đúng hình dạng `get_perm_profile` trả về."""
    perms = {a: True for a in _ACTIONS}
    perms["scope"] = scope
    return {
        "grants": [{"role_id": 1, "perms": {"contract": perms},
                    "scope": {"inc": inc or {}, "exc": exc or {}}}],
        "company_id": company_id, "dept_id": 0, "dept_name": "",
        "employee_id": 0, "emp_code": "", "emp_name": "",
    }


def _hd(db, code, company_id, created_by=99):
    c = Contract(code=code, company_id=company_id, party_type="supplier",
                 title=f"Hợp đồng {code}", status="active", created_by=created_by)
    db.add(c)
    db.commit()
    return c


def _thay(db, profile):
    user = SimpleNamespace(id=USER_ID)
    q = apply_scope(db.query(Contract), Contract, "contract", user, profile)
    return sorted(c.code for c in q.all())


@pytest.fixture
def ba_hop_dong(db):
    """A1, A2 của pháp nhân A; B1 của pháp nhân B. A2 do chính người dùng lập."""
    _hd(db, "HD-A1", CTY_A)
    _hd(db, "HD-A2", CTY_A, created_by=USER_ID)
    _hd(db, "HD-B1", CTY_B)
    return db


# ── Tầng lọc ────────────────────────────────────────────────────────────────────
def test_entity_contract_co_trong_bang_khai_pham_vi():
    """Thiếu dòng này là mọi khẳng định bên dưới lặng lẽ xanh mà không lọc gì."""
    assert SCOPE_FIELDS["contract"] == {"company": "company_id", "owner": "created_by"}


def test_pham_vi_cong_ty_chi_thay_hop_dong_phap_nhan_minh(ba_hop_dong):
    assert _thay(ba_hop_dong, _profile(scope="company")) == ["HD-A1", "HD-A2"]
    assert _thay(ba_hop_dong, _profile(scope="company", company_id=CTY_B)) == ["HD-B1"]


def test_pham_vi_cua_toi_chi_thay_hop_dong_minh_lap(ba_hop_dong):
    assert _thay(ba_hop_dong, _profile(scope="own")) == ["HD-A2"]


def test_pham_vi_tat_ca_van_thay_het(ba_hop_dong):
    """Đây là cấu hình hiện hành của cả 6 vai trò — bản vá không được đổi hành vi hôm nay."""
    assert _thay(ba_hop_dong, _profile(scope="all")) == ["HD-A1", "HD-A2", "HD-B1"]


def test_loai_tru_phap_nhan_de_len_ca_pham_vi_tat_ca(ba_hop_dong):
    """Loại trừ đích danh là điều kiện THU HẸP, phải ăn cả khi vai trò để `all`."""
    prof = _profile(scope="all", exc={"company": [CTY_B]})
    assert _thay(ba_hop_dong, prof) == ["HD-A1", "HD-A2"]


def test_khong_grant_nao_co_quyen_thi_khong_thay_gi(ba_hop_dong):
    prof = _profile(scope="all")
    prof["grants"][0]["perms"]["contract"]["read"] = False
    assert _thay(ba_hop_dong, prof) == []


# ── Tầng route ──────────────────────────────────────────────────────────────────
@pytest.fixture
def gia_lap_ho_so(monkeypatch):
    """Thay `get_perm_profile` trong module controller — hàm thật đọc DB và có bộ đệm 60s."""
    def _dat(profile):
        monkeypatch.setattr(ct, "get_perm_profile", lambda db, user: profile)
        return SimpleNamespace(id=USER_ID)
    return _dat


def test_mo_hop_dong_ngoai_pham_vi_tra_403_chu_khong_tra_du_lieu(ba_hop_dong, gia_lap_ho_so):
    user = gia_lap_ho_so(_profile(scope="company", company_id=CTY_A))
    hd_b = ba_hop_dong.query(Contract).filter(Contract.code == "HD-B1").one()

    with pytest.raises(HTTPException) as e:
        ct.get_(hd_b.id, ba_hop_dong, user)
    assert e.value.status_code == 403


def test_hop_dong_khong_ton_tai_van_la_404(ba_hop_dong, gia_lap_ho_so):
    """Phân biệt 'gõ nhầm mã' với 'có nhưng ngoài phạm vi' — gộp thành 403 hết là khó dùng."""
    user = gia_lap_ho_so(_profile(scope="all"))
    with pytest.raises(HTTPException) as e:
        ct.get_(999999, ba_hop_dong, user)
    assert e.value.status_code == 404


def test_sua_hop_dong_ngoai_pham_vi_bi_chan(ba_hop_dong, gia_lap_ho_so):
    from app.modules.contract.schema import ContractUpdate

    user = gia_lap_ho_so(_profile(scope="company", company_id=CTY_A))
    hd_b = ba_hop_dong.query(Contract).filter(Contract.code == "HD-B1").one()

    with pytest.raises(HTTPException) as e:
        ct.update_(hd_b.id, ContractUpdate(title="Đổi trộm"), ba_hop_dong, user)
    assert e.value.status_code == 403
    ba_hop_dong.rollback()
    assert ba_hop_dong.query(Contract).filter(Contract.code == "HD-B1").one().title == "Hợp đồng HD-B1"


def test_xoa_hang_loat_chi_xoa_phan_trong_pham_vi(ba_hop_dong, gia_lap_ho_so):
    """Gửi đại một dãy id từng xóa được hợp đồng của công ty khác — vòng lặp cũ chỉ `db.get`."""
    user = gia_lap_ho_so(_profile(scope="company", company_id=CTY_A))
    ids = ",".join(str(c.id) for c in ba_hop_dong.query(Contract).all())

    ct.bulk_delete_contracts(ids, ba_hop_dong, user)

    assert sorted(c.code for c in ba_hop_dong.query(Contract).all()) == ["HD-B1"]


def test_xoa_hang_loat_toan_id_ngoai_pham_vi_thi_403(ba_hop_dong, gia_lap_ho_so):
    user = gia_lap_ho_so(_profile(scope="company", company_id=CTY_A))
    hd_b = ba_hop_dong.query(Contract).filter(Contract.code == "HD-B1").one()

    with pytest.raises(HTTPException) as e:
        ct.bulk_delete_contracts(str(hd_b.id), ba_hop_dong, user)
    assert e.value.status_code == 403


def test_lap_hop_dong_dung_ten_phap_nhan_khac_bi_chan(ba_hop_dong, gia_lap_ho_so):
    """Phạm vi `company` mà chỉ chặn ĐỌC thì người dùng vẫn tạo được hợp đồng cho pháp nhân
    khác — tạo xong chính họ không thấy lại nó."""
    from app.modules.contract.schema import ContractCreate

    user = gia_lap_ho_so(_profile(scope="company", company_id=CTY_A))
    with pytest.raises(HTTPException) as e:
        ct.create_(ContractCreate(company_id=CTY_B, title="Hợp đồng lậu"), ba_hop_dong, user)
    assert e.value.status_code == 403
    assert ba_hop_dong.query(Contract).filter(Contract.title == "Hợp đồng lậu").first() is None


def test_lap_hop_dong_dung_ten_phap_nhan_minh_thi_qua(ba_hop_dong, gia_lap_ho_so):
    from app.modules.contract.schema import ContractCreate

    user = gia_lap_ho_so(_profile(scope="company", company_id=CTY_A))
    ct.create_(ContractCreate(company_id=CTY_A, title="Hợp đồng thật"), ba_hop_dong, user)
    assert ba_hop_dong.query(Contract).filter(Contract.title == "Hợp đồng thật").first() is not None


# ── Tầng chính sách: mặc định trong seed ────────────────────────────────────────
# Bộ lọc chạy được rồi thì mới tới câu "mặc định nên đặt bao nhiêu". Hợp đồng KHÔNG
# phải danh mục dùng chung: mỗi cái đứng tên một pháp nhân, nên mặc định là 'company'.
_THEO_PHAP_NHAN = ("dept_head", "company_head", "pur_staff", "pur_admin")
_DANH_MUC_DUNG_CHUNG = ("product", "unit", "item_group", "warehouse", "supplier")


def test_mac_dinh_hop_dong_theo_phap_nhan_tru_vai_tro_quan_ly():
    from app.seed import STD_ROLES

    for code in _THEO_PHAP_NHAN:
        actions, scope = STD_ROLES[code]["perms"]["contract"]
        assert scope == "company", code
        assert "read" in actions, code
    # Quản lý thu mua nhìn cả tập đoàn — cố ý giữ 'all'.
    assert STD_ROLES["pur_manager"]["perms"]["contract"][1] == "all"
    # Nhân sự yêu cầu thường không được đụng vào hợp đồng chút nào.
    assert "contract" not in STD_ROLES["employee"]["perms"]


def test_tach_hop_dong_khong_keo_theo_cac_danh_muc_dung_chung():
    """`contract` từng nằm chung trong _CATALOG_READ/_CATALOG_CRUD. Tách ra mà tay trượt là
    hạ luôn phạm vi Kho/ĐVT/Sản phẩm/NCC — những thứ VỐN DĨ phải dùng chung toàn tập đoàn."""
    from app.seed import STD_ROLES

    for code in ("dept_head", "company_head", "pur_staff"):
        for e in _DANH_MUC_DUNG_CHUNG:
            assert STD_ROLES[code]["perms"][e][1] == "all", (code, e)
    for e in (*_DANH_MUC_DUNG_CHUNG, "brand", "category_assignee"):
        assert STD_ROLES["pur_admin"]["perms"][e][1] == "all", e


def test_force_sync_ha_pham_vi_hop_dong_dang_de_all(db, monkeypatch):
    """Seed KHÔNG ghi đè phân quyền đã có trên DB (D-018), nên mọi môi trường đang chạy vẫn
    để contract = 'all' — hồi đó ghi gì cũng không lọc nên không ai để ý. Cần một nhát áp lại."""
    from app import seed
    from app.modules.role.model import Permission, Role

    nv = Role(code="pur_staff", name="Nhân viên thu mua")
    tp = Role(code="dept_head", name="Trưởng phòng")
    db.add_all([nv, tp])
    db.commit()
    db.add_all([
        Permission(role_id=nv.id, entity="contract", can_read=True, scope="all"),
        Permission(role_id=nv.id, entity="warehouse", can_read=True, scope="all"),
        Permission(role_id=tp.id, entity="contract", can_read=True, scope="own"),
    ])
    db.commit()

    monkeypatch.setattr(seed, "FORCE_SYNC", True)
    seed.force_resync_roles(db)

    def _scope(role, entity):
        return db.query(Permission).filter_by(role_id=role.id, entity=entity).one().scope

    assert _scope(nv, "contract") == "company"
    # Danh mục dùng chung không được kéo theo.
    assert _scope(nv, "warehouse") == "all"
    # Vai trò đã chỉnh tay HẸP hơn thì để yên — áp lại không được nới quyền ra.
    assert _scope(tp, "contract") == "own"
