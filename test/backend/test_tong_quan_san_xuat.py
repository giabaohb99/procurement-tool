"""Tổng quan phân hệ Sản xuất (`/api/dashboard/production`) — gác theo QUYỀN.

Route chỉ đòi đăng nhập rồi gác từng khối bằng `can(entity)`. Hai lối hỏng mà
bài này canh:

  - **Lộ số của danh mục mình không được xem.** Người chỉ có `supplier.read` mà
    vẫn nhận `product_total` là rò rỉ thầm lặng — không ai ăn 403 để mà phát hiện.
  - **Đếm nhầm hợp đồng vô thời hạn thành "sắp hết hạn".** `end_date` là VARCHAR,
    hợp đồng không đặt hạn lưu chuỗi rỗng, và `"" <= "2026-09-30"` là ĐÚNG trong
    phép so chuỗi. Thiếu `end_date != ""` thì con số cảnh báo phồng lên vô nghĩa.
"""
import json
from datetime import datetime, timedelta

from app.modules.catalog.model import ItemGroup, Unit
from app.modules.contract.model import Contract
from app.modules.dashboard.controller import production_overview
from app.modules.product.model import Product
from app.modules.supplier.model import Supplier
from app.modules.user.model import User


def _tong_quan(db, user):
    """`success()` trả `JSONResponse` chứ không trả dict — phải bóc thân phản hồi."""
    return json.loads(production_overview(db=db, user=user).body)["data"]


def _ngay(offset_days: int) -> str:
    return (datetime.now().date() + timedelta(days=offset_days)).strftime("%Y-%m-%d")


# Fixture `seed` đã dựng sẵn 1 NCC hàng hóa ("NX") và 2 phân loại (Nhãn, Thùng).
# Cộng thêm ở đây chứ không viết số cứng — sửa `seed` là biết ngay bài nào lệch.
SEED_SUPPLIERS = 1
SEED_ITEM_GROUPS = 2


def _ncc(db, code, name, supplier_type="goods", is_active=True):
    db.add(Supplier(code=code, name=name, supplier_type=supplier_type, is_active=is_active))


def _san_pham(db, code, name, item_group="", is_active=True):
    db.add(Product(code=code, name=name, item_group=item_group, is_active=is_active))


def _hop_dong(db, code, end_date, status="active", signed=True):
    db.add(Contract(code=code, end_date=end_date, status=status, signed=signed,
                    party_type="supplier", party_code="NCC_A", party_name="Nhà cung cấp A"))


def test_dem_ncc_tach_hang_hoa_va_van_chuyen(db, seed, cap_quyen):
    user = db.get(User, seed.u_req_id)
    cap_quyen(user.id, "supplier", scope="all", read=True)

    _ncc(db, "NCC_A", "Nhà cung cấp A")
    _ncc(db, "NCC_B", "Nhà cung cấp B")
    _ncc(db, "VC_A", "Vận chuyển A", supplier_type="transport")
    _ncc(db, "NCC_C", "Nhà cung cấp C", is_active=False)
    db.commit()

    kpi = _tong_quan(db, user)["kpi"]

    assert kpi["supplier_total"] == SEED_SUPPLIERS + 4
    assert kpi["supplier_goods"] == SEED_SUPPLIERS + 3   # NCC ngừng dùng vẫn là hàng hóa
    assert kpi["supplier_transport"] == 1
    assert kpi["supplier_inactive"] == 1


def test_chi_co_quyen_ncc_thi_khong_lo_so_cua_danh_muc_khac(db, seed, cap_quyen):
    """Khối bị gác phải BỎ HẲN khóa, không trả 0 — 0 là "đếm được, không có dòng"."""
    user = db.get(User, seed.u_req_id)
    cap_quyen(user.id, "supplier", scope="all", read=True)

    _ncc(db, "NCC_A", "Nhà cung cấp A")
    _san_pham(db, "SP01", "Thùng carton", item_group="Bao bì")
    _hop_dong(db, "HD01", _ngay(10))
    db.add(Unit(code="DVT01", name="Cái"))
    db.add(ItemGroup(code="PLO01", name="Bao bì"))
    db.commit()

    data = _tong_quan(db, user)

    assert data["kpi"]["supplier_total"] == SEED_SUPPLIERS + 1
    for khoa in ("product_total", "unit_total", "item_group_total", "contract_total"):
        assert khoa not in data["kpi"]
    assert data["product_groups"] == []
    assert data["expiring_contracts"] == []
    assert data["can"] == {"supplier": True, "product": False, "unit": False,
                           "item_group": False, "contract": False}


def test_khong_co_quyen_nao_thi_tra_ve_rong_chu_khong_no(db, seed, cap_quyen):
    """Người dùng trơ (không grant nào) vẫn phải nhận phản hồi hợp lệ, rỗng."""
    user = db.get(User, seed.u_req_id)

    _ncc(db, "NCC_A", "Nhà cung cấp A")
    _san_pham(db, "SP01", "Thùng carton")
    db.commit()

    data = _tong_quan(db, user)

    assert data["kpi"] == {}
    assert data["product_groups"] == []
    assert data["expiring_contracts"] == []
    assert not any(data["can"].values())


def test_gom_san_pham_theo_phan_loai_va_don_duoi_vao_khac(db, seed, cap_quyen):
    """Bảy phân loại: sáu nhóm lớn đứng riêng, phần đuôi gộp thành "Khác"."""
    user = db.get(User, seed.u_req_id)
    cap_quyen(user.id, "product", scope="all", read=True)

    # Số lượng giảm dần để thứ tự sắp xếp có thể khẳng định được.
    for so_luong, ten in enumerate(["G1", "G2", "G3", "G4", "G5", "G6", "G7"]):
        for i in range(7 - so_luong):
            _san_pham(db, f"SP_{ten}_{i}", f"Sản phẩm {ten} {i}", item_group=ten)
    db.commit()

    groups = _tong_quan(db, user)["product_groups"]

    assert [g["name"] for g in groups] == ["G1", "G2", "G3", "G4", "G5", "G6", "Khác"]
    assert [g["value"] for g in groups] == [7, 6, 5, 4, 3, 2, 1]


def test_san_pham_chua_dat_phan_loai_van_duoc_dem(db, seed, cap_quyen):
    """`item_group` rỗng là chuyện thường trên dữ liệu thật — không được rơi mất."""
    user = db.get(User, seed.u_req_id)
    cap_quyen(user.id, "product", scope="all", read=True)

    _san_pham(db, "SP01", "Thùng carton", item_group="")
    _san_pham(db, "SP02", "Băng keo", item_group="")
    _san_pham(db, "SP03", "Màng PE", item_group="Bao bì", is_active=False)
    db.commit()

    data = _tong_quan(db, user)

    assert data["kpi"]["product_total"] == 3
    assert data["kpi"]["product_inactive"] == 1
    assert {g["name"]: g["value"] for g in data["product_groups"]} == {
        "(Chưa phân loại)": 2, "Bao bì": 1,
    }


def test_dvt_va_phan_loai_dem_doc_lap_theo_tung_quyen(db, seed, cap_quyen):
    """Hai danh mục nhỏ nhất cũng là hai khối riêng — có quyền cái này không kéo theo cái kia."""
    user = db.get(User, seed.u_req_id)
    cap_quyen(user.id, "item_group", scope="all", read=True)

    db.add(Unit(code="DVT01", name="Cái"))
    db.add(ItemGroup(code="PLO01", name="Bao bì"))
    db.commit()

    kpi = _tong_quan(db, user)["kpi"]

    assert kpi["item_group_total"] == SEED_ITEM_GROUPS + 1
    assert "unit_total" not in kpi


def test_hop_dong_vo_thoi_han_khong_bi_dem_la_sap_het_han(db, seed, cap_quyen):
    """Lỗi so chuỗi: `"" <= "<ngày>"` là ĐÚNG, nên thiếu `end_date != ""` là đếm sai."""
    user = db.get(User, seed.u_req_id)
    cap_quyen(user.id, "contract", scope="all", read=True)

    _hop_dong(db, "HD_VO_HAN", "")           # không đặt hạn
    _hop_dong(db, "HD_SAP_HET", _ngay(10))   # trong 30 ngày tới
    _hop_dong(db, "HD_CON_DAI", _ngay(200))
    _hop_dong(db, "HD_HET_HAN", _ngay(-5))
    db.commit()

    kpi = _tong_quan(db, user)["kpi"]

    assert kpi["contract_total"] == 4
    assert kpi["contract_expiring"] == 1
    assert kpi["contract_expired"] == 1


def test_hop_dong_da_thanh_ly_khong_con_canh_bao(db, seed, cap_quyen):
    user = db.get(User, seed.u_req_id)
    cap_quyen(user.id, "contract", scope="all", read=True)

    _hop_dong(db, "HD01", _ngay(10), status="liquidated")
    _hop_dong(db, "HD02", _ngay(10), status="cancelled")
    _hop_dong(db, "HD03", _ngay(10), signed=False)
    db.commit()

    data = _tong_quan(db, user)

    assert data["kpi"]["contract_total"] == 3
    assert data["kpi"]["contract_live"] == 1
    assert data["kpi"]["contract_expiring"] == 1
    assert data["kpi"]["contract_unsigned"] == 1
    assert [c["code"] for c in data["expiring_contracts"]] == ["HD03"]


def test_hop_dong_sap_het_han_xep_theo_han_gan_nhat_va_cat_ngon(db, seed, cap_quyen):
    """Danh sách chỉ lấy 8 dòng — phải là 8 dòng GẤP NHẤT, không phải 8 dòng đầu bảng."""
    user = db.get(User, seed.u_req_id)
    cap_quyen(user.id, "contract", scope="all", read=True)

    # Thêm theo thứ tự hạn XA -> GẦN để `id` đi ngược với `end_date`.
    for i in range(10, 0, -1):
        _hop_dong(db, f"HD{i:02d}", _ngay(i))
    db.commit()

    rows = _tong_quan(db, user)["expiring_contracts"]

    assert len(rows) == 8
    assert [r["code"] for r in rows] == [f"HD{i:02d}" for i in range(1, 9)]
    assert rows[0]["party_name"] == "Nhà cung cấp A"
