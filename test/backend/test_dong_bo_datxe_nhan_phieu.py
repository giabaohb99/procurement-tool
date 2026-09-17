"""Cửa nhận phiếu từ app đặt xe cũ: bộ tra danh mục ba nấc + `apply_legacy_record`.

Chạy trên SQLite in-memory của `conftest.py`, KHÔNG đụng Firebase: bộ tra nhận
`fetch_node` thay thế, nên nấc 2 và nấc 3 kiểm được mà không cần mạng.
"""
import pytest

from app.modules.company.model import Company
from app.modules.department.model import Department
from app.modules.legacy_datxe import resolver as resolver_mod
from app.modules.legacy_datxe.resolver import (
    WARN_AUTO_CREATED,
    WARN_STAMPED_BY_NAME,
    LegacyCatalog,
    normalize_phone,
    normalize_plate,
)
from app.modules.legacy_datxe.service import (
    WARN_CLOSED_LOCKED,
    apply_legacy_record,
)
from app.modules.sync_log.constants import SyncAction, SyncStatus
from app.modules.vehicle_booking.model import (
    BK_COMPLETED,
    BK_DISPATCHED,
    BK_PENDING,
    Driver,
    Vehicle,
    VehicleBooking,
)

VEHICLE_KEY = "veh_aaa"
DRIVER_KEY = "drv_bbb"
BRAND_KEY = "brand_ccc"

#: Nhánh Firebase giả lập. `LegacyCatalog` hỏi theo đường dẫn `<nhánh>/<khóa>`.
FAKE_NODES = {
    f"vehicles/{VEHICLE_KEY}": {"licensePlate": "51D-465.49", "model": "Innova",
                                "type": "7 chỗ", "capacity": 7},
    f"drivers/{DRIVER_KEY}": {"name": "Trần Văn Bảy", "phone": "+84901234567",
                              "licenseNumber": "B2-123"},
    f"brands/{BRAND_KEY}": {"name": "Công ty DEGO"},
}


def fake_fetch(path: str):
    return FAKE_NODES.get(path)


def make_catalog(db, **kw) -> LegacyCatalog:
    return LegacyCatalog(db, fetch_node=fake_fetch, **kw)


def booking_node(status: str = "pending_approval", **details) -> dict:
    node = {
        "type": "CAR_BOOKING",
        "createdAt": 1_757_000_000_000,
        "createdBy": "uid_khong_co_trong_erp",
        "approval": {"overallStatus": status, "history": []},
        "details": {
            "purpose": "Đi họp khách hàng",
            "startLocation": "Văn phòng",
            "endLocation": "Nhà khách",
            "passengerCount": 2,
            "brandId": [BRAND_KEY],
        },
    }
    node["details"].update(details)
    return node


# ---------------------------------------------------------------------------
# Chuẩn hóa
# ---------------------------------------------------------------------------

def test_chuan_hoa_bien_so_bo_dau_cham_va_gach():
    assert normalize_plate("51D-465.49") == normalize_plate("51d 465 49") == "51d46549"


def test_chuan_hoa_dien_thoai_lay_chin_so_cuoi():
    assert normalize_phone("+84901234567") == normalize_phone("0901234567") == "901234567"
    assert normalize_phone("123") == ""


# ---------------------------------------------------------------------------
# Nấc 1: dấu legacy_id
# ---------------------------------------------------------------------------

def test_nac_1_tra_theo_dau_legacy_id(db):
    xe = Vehicle(license_plate="51A-00001", legacy_id=VEHICLE_KEY)
    db.add(xe)
    db.commit()

    catalog = make_catalog(db)
    assert catalog.vehicles.get(VEHICLE_KEY, 0) == xe.id
    #  Nấc 1 ăn thì không có cảnh báo nào — đó là đường bình thường.
    assert catalog.warnings == []


# ---------------------------------------------------------------------------
# Nấc 2: đặc điểm tự nhiên + đóng dấu
# ---------------------------------------------------------------------------

def test_nac_2_khop_bien_so_roi_dong_dau_len_hang_co_san(db):
    #  Cùng một chiếc xe, gõ biển số theo kiểu khác và chưa đeo dấu nào.
    xe = Vehicle(license_plate="51D46549", legacy_id="")
    db.add(xe)
    db.commit()

    catalog = make_catalog(db)
    assert catalog.vehicles.get(VEHICLE_KEY, 0) == xe.id
    assert xe.legacy_id == VEHICLE_KEY
    assert WARN_STAMPED_BY_NAME in catalog.warnings


def test_nac_2_khong_de_len_dau_cua_khoa_khac(db):
    xe = Vehicle(license_plate="51D-465.49", legacy_id="veh_khac")
    db.add(xe)
    db.commit()

    catalog = make_catalog(db)
    assert catalog.vehicles.get(VEHICLE_KEY, 0) == xe.id
    #  Trả đúng hàng nhưng KHÔNG cướp dấu của khóa kia.
    assert xe.legacy_id == "veh_khac"


def test_nac_2_ten_trung_hai_hang_thi_khong_dam_ghep(db):
    db.add_all([Department(code="KD1", name="Phòng Kinh doanh"),
                Department(code="KD2", name="phòng kinh doanh")])
    db.commit()

    catalog = LegacyCatalog(db, fetch_node=lambda path: {"name": "Phòng Kinh doanh"})
    assert catalog.departments.get("dep_x", 0) == 0


def test_nac_2_khop_tai_xe_theo_dien_thoai_khac_dinh_dang(db):
    tx = Driver(name="Tên khác hẳn", phone="0901234567", legacy_id="")
    db.add(tx)
    db.commit()

    catalog = make_catalog(db)
    assert catalog.drivers.get(DRIVER_KEY, 0) == tx.id
    assert tx.legacy_id == DRIVER_KEY


# ---------------------------------------------------------------------------
# Nấc 3: tự tạo
# ---------------------------------------------------------------------------

def test_nac_3_tat_thi_khong_tao_gi(db):
    catalog = make_catalog(db, allow_create=False)
    assert catalog.vehicles.get(VEHICLE_KEY, 0) == 0
    assert db.query(Vehicle).count() == 0


def test_nac_3_bat_thi_tao_xe_va_gan_co_can_soat(db):
    catalog = make_catalog(db, allow_create=True)
    vid = catalog.vehicles.get(VEHICLE_KEY, 0)

    xe = db.get(Vehicle, vid)
    assert xe.license_plate == "51D-465.49"
    assert xe.legacy_id == VEHICLE_KEY
    assert WARN_AUTO_CREATED in catalog.warnings


def test_nac_3_khong_bao_gio_tao_cong_ty_hay_phong_ban(db):
    catalog = make_catalog(db, allow_create=True)
    assert catalog.companies.get(BRAND_KEY, 0) == 0
    assert catalog.departments.get("dep_moi", 0) == 0
    assert db.query(Company).count() == 0
    assert db.query(Department).count() == 0


def test_tra_truot_chi_hoi_firebase_mot_lan(db, monkeypatch):
    dem = {"n": 0}

    def dem_fetch(path):
        dem["n"] += 1
        return None

    catalog = LegacyCatalog(db, fetch_node=dem_fetch)
    for _ in range(3):
        catalog.vehicles.get("veh_khong_co", 0)
    assert dem["n"] == 1


def test_mac_dinh_doc_thang_firebase(db, monkeypatch):
    """Không truyền `fetch_node` thì bộ tra phải dùng đúng bộ đọc Firebase."""
    catalog = LegacyCatalog(db)
    assert catalog.fetch_node is resolver_mod.read_node


# ---------------------------------------------------------------------------
# Nhận phiếu: tạo mới
# ---------------------------------------------------------------------------

def test_tao_phieu_moi_sinh_ma_sau_chu_so(db):
    catalog = make_catalog(db)
    log = apply_legacy_record(db, node=booking_node(), legacy_id="req_001",
                              catalog=catalog)

    phieu = db.query(VehicleBooking).one()
    assert phieu.code == f"DX{phieu.id:06d}"
    assert phieu.legacy_id == "req_001"
    assert phieu.status == BK_PENDING
    assert log.status == int(SyncStatus.SUCCESS)
    assert log.action == int(SyncAction.CREATE)
    assert log.local_id == phieu.id


def test_loai_phieu_la_thi_bao_loi_chu_khong_nuot(db):
    with pytest.raises(ValueError):
        apply_legacy_record(db, node={"type": "KHONG_BIET"}, legacy_id="req_x",
                            catalog=make_catalog(db))


def test_noi_dung_y_het_lan_truoc_thi_khong_ghi_them_dong_so(db):
    node = booking_node()
    apply_legacy_record(db, node=node, legacy_id="req_002", catalog=make_catalog(db))
    lai = apply_legacy_record(db, node=node, legacy_id="req_002",
                              catalog=make_catalog(db))
    assert lai is None
    assert db.query(VehicleBooking).count() == 1


# ---------------------------------------------------------------------------
# Nhận phiếu: cập nhật
# ---------------------------------------------------------------------------

def test_cap_nhat_ghi_de_o_da_doi(db):
    apply_legacy_record(db, node=booking_node(), legacy_id="req_003",
                        catalog=make_catalog(db))
    log = apply_legacy_record(db, node=booking_node(purpose="Đổi sang đi sân bay"),
                              legacy_id="req_003", catalog=make_catalog(db))

    phieu = db.query(VehicleBooking).one()
    assert phieu.purpose == "Đổi sang đi sân bay"
    assert log.status == int(SyncStatus.SUCCESS)
    assert "purpose" in log.message


def test_app_cu_tra_rong_thi_giu_nguyen_gia_tri_erp(db):
    apply_legacy_record(db, node=booking_node(attendees="Anh Ba, chị Tư"),
                        legacy_id="req_004", catalog=make_catalog(db))
    #  Lần hai app cũ không trả ô đó nữa — luật §9.4: ghi rỗng KHÔNG đè lên
    #  giá trị đang có.
    apply_legacy_record(db, node=booking_node(purpose="Đi họp lần hai"),
                        legacy_id="req_004", catalog=make_catalog(db))

    assert db.query(VehicleBooking).one().attendees == "Anh Ba, chị Tư"


def test_khong_co_gi_doi_thi_ghi_dong_bo_qua(db):
    node = booking_node()
    apply_legacy_record(db, node=node, legacy_id="req_005", catalog=make_catalog(db))
    #  Đổi một ô mà ERP KHÔNG giữ: băm khác đi nên vẫn chạy qua cửa, nhưng bên
    #  ERP không có gì phải sửa.
    node_khac = booking_node()
    node_khac["updatedAt"] = 1_757_999_999_999
    log = apply_legacy_record(db, node=node_khac, legacy_id="req_005",
                              catalog=make_catalog(db))

    assert log.status == int(SyncStatus.SKIPPED)


# ---------------------------------------------------------------------------
# Nhận phiếu: phiếu đã chốt
# ---------------------------------------------------------------------------

def test_phieu_da_chot_khong_nhan_noi_dung(db):
    apply_legacy_record(db, node=booking_node(status="completed"),
                        legacy_id="req_006", catalog=make_catalog(db))
    log = apply_legacy_record(db, node=booking_node(status="completed",
                                                    purpose="Sửa sau khi đã xong"),
                              legacy_id="req_006", catalog=make_catalog(db))

    phieu = db.query(VehicleBooking).one()
    assert phieu.purpose == "Đi họp khách hàng"
    assert log.status == int(SyncStatus.SKIPPED)
    assert WARN_CLOSED_LOCKED in (log.warnings or "")


def test_phieu_da_chot_van_nhan_doi_trang_thai(db):
    apply_legacy_record(db, node=booking_node(status="completed"),
                        legacy_id="req_007", catalog=make_catalog(db))
    log = apply_legacy_record(db, node=booking_node(status="canceled"),
                              legacy_id="req_007", catalog=make_catalog(db))

    phieu = db.query(VehicleBooking).one()
    assert phieu.status != BK_COMPLETED
    assert log.action == int(SyncAction.STATUS_CHANGE)
    assert log.status == int(SyncStatus.SUCCESS)


# ---------------------------------------------------------------------------
# Nhận phiếu: điều phối
# ---------------------------------------------------------------------------

def test_dieu_phoi_ben_app_cu_ghi_duoc_xuong_erp(db):
    xe = Vehicle(license_plate="51A-00002", legacy_id=VEHICLE_KEY)
    tx = Driver(name="Bảy", phone="0901234567", legacy_id=DRIVER_KEY)
    db.add_all([xe, tx])
    db.commit()

    node = booking_node(status="dispatched", dispatch={
        "assignedVehicleId": VEHICLE_KEY,
        "assignedDriverId": DRIVER_KEY,
        "driverStatus": "accepted",
    })
    apply_legacy_record(db, node=node, legacy_id="req_008", catalog=make_catalog(db))

    phieu = db.query(VehicleBooking).one()
    assert phieu.assigned_vehicle_id == xe.id
    assert phieu.assigned_driver_id == tx.id
    assert phieu.status == BK_DISPATCHED


def test_tra_xe_khong_ra_thi_khong_xoa_xe_dang_co(db):
    """Đúng đường mất dữ liệu mà luật 'ghi rỗng không đè' sinh ra để chặn."""
    xe = Vehicle(license_plate="51A-00003", legacy_id=VEHICLE_KEY)
    db.add(xe)
    db.commit()

    da_gan = booking_node(status="dispatched",
                          dispatch={"assignedVehicleId": VEHICLE_KEY})
    apply_legacy_record(db, node=da_gan, legacy_id="req_009", catalog=make_catalog(db))

    #  Lần sau bộ tra trượt (xe bị gỡ dấu, Firebase không trả về gì).
    xe.legacy_id = ""
    db.commit()
    lan_sau = booking_node(status="dispatched",
                           dispatch={"assignedVehicleId": VEHICLE_KEY},
                           purpose="Đi họp lần ba")
    catalog = LegacyCatalog(db, fetch_node=lambda path: None)
    apply_legacy_record(db, node=lan_sau, legacy_id="req_009", catalog=catalog)

    assert db.query(VehicleBooking).one().assigned_vehicle_id == xe.id


def test_co_canh_bao_khong_lan_sang_phieu_khac(db):
    """Bộ tra dùng chung cả vòng quét, cờ của phiếu này không được dính phiếu kia."""
    catalog = make_catalog(db, allow_create=True)
    dau = apply_legacy_record(db, node=booking_node(
        status="dispatched", dispatch={"assignedVehicleId": VEHICLE_KEY}),
        legacy_id="req_010", catalog=catalog)
    sau = apply_legacy_record(db, node=booking_node(purpose="Phiếu sạch sẽ"),
                              legacy_id="req_011", catalog=catalog)

    assert WARN_AUTO_CREATED in (dau.warnings or "")
    assert WARN_AUTO_CREATED not in (sau.warnings or "")
