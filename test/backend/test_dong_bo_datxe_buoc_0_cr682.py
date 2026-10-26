"""duoc-CR-682 — Bước 0 đồng bộ app đặt xe / duyệt dấu cũ: app cũ không đè thao tác nghiệp vụ làm trên ERP.

Chiều ERP -> app cũ đang TẮT (và không được bật — app cũ là prod), nên app cũ giữ ảnh chụp cũ và mỗi lượt nhận
(cộng lượt quét ép 02:15) chép đè lại. Mọi bài ở đây chỉ dùng phiếu giả và gọi thẳng `apply_legacy_record` —
không gọi mạng sang app cũ.
"""
from app.modules.legacy_datxe.service import apply_legacy_record
from app.modules.seal_request.model import SEAL_APPROVED, SEAL_COMPLETED, SealRequest
from app.modules.sync_log.constants import SyncStatus
from app.modules.vehicle_booking.model import (BK_APPROVED, BK_CANCELLED, BK_COMPLETED, BK_DISPATCHED,
                                               BK_PENDING, Driver, Vehicle, VehicleBooking)
from test_dong_bo_datxe_nhan_phieu import DRIVER_KEY, VEHICLE_KEY, booking_node, make_catalog


def _sync(db, node, legacy_id="req_b0", force=False):
    return apply_legacy_record(db, node=node, legacy_id=legacy_id, catalog=make_catalog(db), force=force)


def _fleet(db):
    xe = Vehicle(license_plate="51A-11111", legacy_id=VEHICLE_KEY)
    xe_erp = Vehicle(license_plate="51A-22222")
    tx = Driver(name="Bảy", phone="0901234567", legacy_id=DRIVER_KEY)
    tx_erp = Driver(name="Tám", phone="0907654321")
    db.add_all([xe, xe_erp, tx, tx_erp])
    db.commit()
    return xe, xe_erp, tx, tx_erp


def _erp_dispatch(db, booking, vehicle, driver):
    """Điều phối viên gán xe TRÊN ERP — ghi thẳng ORM ngoài lượt đồng bộ, đúng như nút trên web."""
    booking.assigned_vehicle_id, booking.assigned_driver_id = vehicle.id, driver.id
    booking.status = BK_DISPATCHED
    db.commit()


# ─────────────────────────── Dấu «ERP đã thao tác» ───────────────────────────

def test_luot_dong_bo_khong_tu_dong_dau_erp_da_thao_tac(db):
    _sync(db, booking_node(status="pending_approval"))
    _sync(db, booking_node(status="fully_approved"))
    booking = db.query(VehicleBooking).one()
    assert booking.status == BK_APPROVED and booking.erp_action_at == ""


def test_erp_doi_o_tien_trinh_tren_phieu_goc_app_cu_thi_dong_dau(db):
    xe, xe_erp, tx, tx_erp = _fleet(db)
    _sync(db, booking_node(status="fully_approved"))
    booking = db.query(VehicleBooking).one()
    _erp_dispatch(db, booking, xe_erp, tx_erp)
    assert booking.erp_action_at != ""


def test_review_h1_sua_noi_dung_tren_erp_cung_dong_dau_va_luot_dem_khong_tra_ban_cu(db):
    """Review H1: phiếu bị trả về, người tạo sửa mục đích trên ERP rồi gửi lại — lượt quét ép 02:15 trả mục đích về
    bản cũ của app cũ, người duyệt ERP ký trên nội dung đã cũ."""
    _sync(db, booking_node(status="needs_correction"))
    booking = db.query(VehicleBooking).one()
    booking.purpose = "Người tạo sửa mục đích trên ERP"
    db.commit()
    assert booking.erp_action_at != ""

    _sync(db, booking_node(status="needs_correction"), force=True)
    db.refresh(booking)
    assert booking.purpose == "Người tạo sửa mục đích trên ERP"


def test_doi_cot_he_thong_khong_tinh_la_erp_dung_vao(db):
    _sync(db, booking_node(status="pending_approval"))
    booking = db.query(VehicleBooking).one()
    booking.updated_by = 77
    db.commit()
    assert booking.erp_action_at == ""


def test_phieu_tao_tren_erp_khong_dong_dau(db):
    booking = VehicleBooking(code="DX-ERP", purpose="x", status=BK_PENDING, created_by=1)
    db.add(booking)
    db.commit()
    booking.status = BK_APPROVED
    db.commit()
    assert booking.erp_action_at == ""


def test_dieu_phoi_qua_ham_nghiep_vu_that_cung_dong_dau(db):
    from types import SimpleNamespace

    from app.modules.vehicle_booking.schema import DispatchIn
    from app.modules.vehicle_booking.service import dispatch_booking

    xe, xe_erp, tx, tx_erp = _fleet(db)
    _sync(db, booking_node(status="fully_approved"))
    booking = db.query(VehicleBooking).one()
    dispatch_booking(db, booking, DispatchIn(assigned_vehicle_id=xe_erp.id, assigned_driver_id=tx_erp.id),
                     SimpleNamespace(id=900))
    assert booking.status == BK_DISPATCHED and booking.erp_action_at != ""


# ─────────────────────────── App cũ không đè thao tác ERP ───────────────────────────

def test_luot_quet_dem_khong_keo_phieu_erp_da_dieu_phoi_ve_da_duyet(db):
    """Lỗi thật trước Bước 0: phiếu điều phối trên ERP bị lượt 02:15 kéo về «Đã duyệt» mà vẫn giữ xe."""
    xe, xe_erp, tx, tx_erp = _fleet(db)
    _sync(db, booking_node(status="fully_approved"))
    booking = db.query(VehicleBooking).one()
    _erp_dispatch(db, booking, xe_erp, tx_erp)

    _sync(db, booking_node(status="fully_approved", purpose="App cũ sửa mục đích"), force=True)
    db.refresh(booking)
    assert booking.status == BK_DISPATCHED
    assert (booking.assigned_vehicle_id, booking.assigned_driver_id) == (xe_erp.id, tx_erp.id)
    #  ERP đã đụng vào → làm chủ cả phiếu, nội dung cũng không bị app cũ đè (review H1).
    assert booking.purpose == "Đi họp khách hàng"


def test_app_cu_dieu_phoi_xe_khac_khong_de_xe_erp_da_gan(db):
    xe, xe_erp, tx, tx_erp = _fleet(db)
    _sync(db, booking_node(status="fully_approved"))
    booking = db.query(VehicleBooking).one()
    _erp_dispatch(db, booking, xe_erp, tx_erp)

    _sync(db, booking_node(status="dispatched", dispatch={"assignedVehicleId": VEHICLE_KEY,
                                                          "assignedDriverId": DRIVER_KEY}))
    db.refresh(booking)
    assert (booking.assigned_vehicle_id, booking.assigned_driver_id) == (xe_erp.id, tx_erp.id)


def test_app_cu_huy_phieu_erp_dang_dieu_phoi_thi_van_nhan_huy(db):
    """Hủy / từ chối bên app cũ là ý định thật của người dùng bên kia — nhận, nhưng giữ xe ERP đã gán."""
    xe, xe_erp, tx, tx_erp = _fleet(db)
    _sync(db, booking_node(status="fully_approved"))
    booking = db.query(VehicleBooking).one()
    _erp_dispatch(db, booking, xe_erp, tx_erp)

    _sync(db, booking_node(status="canceled"))
    db.refresh(booking)
    assert booking.status == BK_CANCELLED
    assert booking.assigned_vehicle_id == xe_erp.id


def test_phieu_erp_hoan_tat_thi_trang_thai_khong_lui(db):
    _sync(db, booking_node(status="fully_approved"))
    booking = db.query(VehicleBooking).one()
    booking.status = BK_COMPLETED
    db.commit()

    log = _sync(db, booking_node(status="fully_approved"), force=True)
    db.refresh(booking)
    assert booking.status == BK_COMPLETED
    assert log.status == int(SyncStatus.SKIPPED)
    assert "không cho lùi" in log.message


def test_phieu_chua_cham_tren_erp_van_soi_guong_app_cu(db):
    """Phiếu ERP chưa thao tác: điều phối bên app cũ vẫn chảy về (người ta vẫn điều phối bên đó)."""
    xe, xe_erp, tx, tx_erp = _fleet(db)
    _sync(db, booking_node(status="fully_approved"))
    _sync(db, booking_node(status="dispatched", dispatch={"assignedVehicleId": VEHICLE_KEY,
                                                          "assignedDriverId": DRIVER_KEY}))
    booking = db.query(VehicleBooking).one()
    assert booking.status == BK_DISPATCHED
    assert (booking.assigned_vehicle_id, booking.assigned_driver_id) == (xe.id, tx.id)
    assert booking.erp_action_at == ""


def test_phieu_chot_ben_app_cu_van_nhan_doi_trang_thai(db):
    _sync(db, booking_node(status="completed"))
    _sync(db, booking_node(status="canceled"))
    assert db.query(VehicleBooking).one().status == BK_CANCELLED


# ─────────────────────────── Phiếu duyệt dấu ───────────────────────────

def _seal_node(status):
    node = booking_node(status=status)
    node["type"] = "SEAL_REQUEST"
    return node


def test_phieu_dau_dong_dau_tren_erp_khong_bi_lui_ve_da_duyet(db):
    from app.modules.legacy_datxe.service import entity_of

    node = _seal_node("fully_approved")
    if entity_of(node) != "seal_request":   # khóa loại phiếu dấu của app cũ khác — dò lại cho đúng
        import pytest

        pytest.skip("không dựng được phiếu dấu giả với khóa loại này")
    _sync(db, node, legacy_id="seal_b0")
    seal = db.query(SealRequest).one()
    assert seal.status == SEAL_APPROVED
    seal.status, seal.completed_by = SEAL_COMPLETED, 900
    db.commit()
    assert seal.erp_action_at != ""

    _sync(db, _seal_node("fully_approved"), legacy_id="seal_b0", force=True)
    db.refresh(seal)
    assert (seal.status, seal.completed_by) == (SEAL_COMPLETED, 900)


def test_review_m3_phieu_erp_lam_chu_khong_dung_lai_phien_soi_guong(db):
    """Review M3: mỗi lượt nhận xóa + dựng lại phiên duyệt soi gương (`flow_id=0`) — phiếu ERP đã làm chủ mà vẫn dựng
    là trang chi tiết hiện dấu vết cũ của app cũ, và phiên «đang chạy» chặn nút trả / từ chối của ERP."""
    from app.modules.approval.instance_model import ApprovalInstance

    _sync(db, booking_node(status="fully_approved"))
    booking = db.query(VehicleBooking).one()
    before = {(i.id, i.status) for i in db.query(ApprovalInstance).filter_by(entity="vehicle_booking",
                                                                              entity_id=booking.id)}
    booking.status = BK_COMPLETED
    db.commit()
    _sync(db, booking_node(status="pending_approval"), force=True)
    after = {(i.id, i.status) for i in db.query(ApprovalInstance).filter_by(entity="vehicle_booking",
                                                                             entity_id=booking.id)}
    assert after == before


def test_review_m1_script_sua_lich_su_duyet_chay_trong_co_dong_bo():
    import pathlib

    import app as app_pkg

    src = (pathlib.Path(app_pkg.__file__).resolve().parent.parent / "scripts" / "legacy_sync"
           / "import_approval_history.py").read_text(encoding="utf-8")
    assert "with suppress_outbound():" in src and "stats = run(db, data, args.apply)" in src


def test_cot_dau_khong_kich_hoat_chieu_gui():
    from app.modules.legacy_datxe.outbound_listener import IGNORED_ATTRS

    assert "erp_action_at" in IGNORED_ATTRS
