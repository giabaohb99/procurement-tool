"""Nhập hàng loạt danh mục Đặt xe (Xe · Tài xế) + Duyệt dấu (Loại con dấu).

Chạy thẳng `catalog_import.run` + `service.revert_batch` trên SQLite in-memory,
phủ: apply tạo mới, dedupe cập nhật (Xe theo biển số, Tài xế theo SĐT, Loại con dấu
theo tên), dry-run không ghi, revert xoá bản ghi mới.
"""
from app.modules.company.model import Company
from app.modules.import_tool import catalog_import, doc_import, service
from app.modules.import_tool.model import (ImportBatch, ImportChange, ImportMode,
                                           ImportModule, ImportStatus)
from app.modules.seal_request.model import SealRequest, SealType
from app.modules.seal_request.service import get_company_ids
from app.modules.vehicle_booking.model import Driver, Vehicle, VehicleBooking


def _wb(module: int, rows_by_attr):
    import openpyxl
    adapter = catalog_import.ADAPTERS[module]
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = adapter["sheet"]
    for i, f in enumerate(adapter["fields"], start=1):
        ws.cell(row=1, column=i, value=f["header"])
    for ri, row in enumerate(rows_by_attr, start=2):
        for i, f in enumerate(adapter["fields"], start=1):
            if f["attr"] in row:
                ws.cell(row=ri, column=i, value=row[f["attr"]])
    return wb


def _batch(db, module, mode=ImportMode.APPLY):
    b = ImportBatch(module=module, mode=mode, filename="t.xlsx", file_id=0,
                    status=ImportStatus.QUEUED, created_by=1, updated_by=1)
    db.add(b); db.commit(); db.refresh(b)
    return b


def test_import_vehicle_creates_and_dedupes_by_plate(db):
    wb = _wb(ImportModule.VEHICLE, [
        {"license_plate": "51A-111.11", "model": "Vios", "type": "Xe con", "capacity": 4},
        {"license_plate": "51C-222.22", "model": "Transit", "type": "Xe tải", "capacity": 1.5},
    ])
    b = _batch(db, ImportModule.VEHICLE)
    catalog_import.run(db, b, wb, apply=True)
    assert b.status == ImportStatus.DONE and b.created_count == 2
    assert db.query(Vehicle).filter(Vehicle.license_plate == "51A-111.11").one().model == "Vios"

    # Cùng biển số → CẬP NHẬT, không tạo trùng.
    wb2 = _wb(ImportModule.VEHICLE, [{"license_plate": "51A-111.11", "model": "Vios 2024"}])
    b2 = _batch(db, ImportModule.VEHICLE)
    catalog_import.run(db, b2, wb2, apply=True)
    assert b2.updated_count == 1
    assert db.query(Vehicle).filter(Vehicle.license_plate == "51A-111.11").count() == 1
    assert db.query(Vehicle).filter(Vehicle.license_plate == "51A-111.11").one().model == "Vios 2024"


def test_import_driver_dedupes_by_phone(db):
    wb = _wb(ImportModule.DRIVER, [{"phone": "0909000001", "name": "Nguyễn Văn A", "license_class": "B2"}])
    b = _batch(db, ImportModule.DRIVER)
    catalog_import.run(db, b, wb, apply=True)
    assert b.created_count == 1
    wb2 = _wb(ImportModule.DRIVER, [{"phone": "0909000001", "name": "Nguyễn Văn A", "license_class": "C"}])
    b2 = _batch(db, ImportModule.DRIVER)
    catalog_import.run(db, b2, wb2, apply=True)
    assert b2.updated_count == 1
    assert db.query(Driver).filter(Driver.phone == "0909000001").one().license_class == "C"


def test_import_seal_type_dry_run_keeps_no_row(db):
    wb = _wb(ImportModule.SEAL_TYPE, [{"name": "Dấu tròn công ty", "description": "Dấu pháp nhân"}])
    b = _batch(db, ImportModule.SEAL_TYPE, ImportMode.DRY_RUN)
    catalog_import.run(db, b, wb, apply=False)
    assert b.status == ImportStatus.DONE and b.created_count == 1
    assert db.query(SealType).filter(SealType.name == "Dấu tròn công ty").count() == 0  # thử → không ghi


def test_revert_vehicle_deletes_new_rows(db):
    wb = _wb(ImportModule.VEHICLE, [{"license_plate": "51A-999.99", "model": "X"}])
    b = _batch(db, ImportModule.VEHICLE)
    catalog_import.run(db, b, wb, apply=True)
    assert db.query(Vehicle).filter(Vehicle.license_plate == "51A-999.99").count() == 1
    assert db.query(ImportChange).filter(ImportChange.batch_id == b.id).count() == 1

    service.revert_batch(db, b, user_id=1)
    assert db.query(Vehicle).filter(Vehicle.license_plate == "51A-999.99").count() == 0
    assert b.status == ImportStatus.REVERTED


# ── Chứng từ header-only (Yêu cầu đặt xe / đóng dấu) qua doc_import ────────────
def _doc_wb(module, rows):
    import openpyxl
    adapter = doc_import.DOC_ADAPTERS[module]
    fields = [adapter["code"], *adapter["header_fields"], *adapter.get("line_fields", [])]
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = adapter["sheet"]
    for i, f in enumerate(fields, start=1):
        ws.cell(row=1, column=i, value=f["header"])
    for ri, row in enumerate(rows, start=2):
        for i, f in enumerate(fields, start=1):
            if f["attr"] in row:
                ws.cell(row=ri, column=i, value=row[f["attr"]])
    return wb


def test_import_vehicle_booking_document(db):
    wb = _doc_wb(ImportModule.VEHICLE_BOOKING,
                 [{"code": "DX900", "purpose": "Đi họp khách", "request_type": 1, "start_location": "VP"}])
    b = _batch(db, ImportModule.VEHICLE_BOOKING)
    doc_import.run(db, b, wb, apply=True)
    assert b.created_count == 1
    bk = db.query(VehicleBooking).filter(VehicleBooking.code == "DX900").one()
    assert bk.purpose == "Đi họp khách"
    assert bk.status == 5   # mặc định Hoàn thành (dữ liệu lịch sử)


def test_import_seal_request_document_sets_company_link(db):
    co = Company(code="CT1", name="Công ty 1")
    db.add(co)
    db.flush()
    wb = _doc_wb(ImportModule.SEAL_REQUEST,
                 [{"code": "DD900", "purpose": "Đóng dấu HĐ", "company_id": "CT1"}])
    b = _batch(db, ImportModule.SEAL_REQUEST)
    doc_import.run(db, b, wb, apply=True)
    req = db.query(SealRequest).filter(SealRequest.code == "DD900").one()
    assert req.company_id == co.id
    #  post_apply đã ghi BẢNG NỐI công ty → Văn thư/Giám đốc lọc đúng phạm vi.
    assert get_company_ids(db, req.id) == [co.id]


def test_import_document_dedupe_skips_existing_code(db):
    db.add(VehicleBooking(code="DX901", purpose="giữ nguyên", status=5))
    db.flush()
    wb = _doc_wb(ImportModule.VEHICLE_BOOKING, [{"code": "DX901", "purpose": "đè mới"}])
    b = _batch(db, ImportModule.VEHICLE_BOOKING)
    doc_import.run(db, b, wb, apply=True)
    assert b.skipped_count >= 1   # mã đã tồn tại → bỏ qua cả phiếu, KHÔNG đè
    assert db.query(VehicleBooking).filter(VehicleBooking.code == "DX901").one().purpose == "giữ nguyên"


def test_revert_document_deletes_new(db):
    wb = _doc_wb(ImportModule.VEHICLE_BOOKING, [{"code": "DX902", "purpose": "z"}])
    b = _batch(db, ImportModule.VEHICLE_BOOKING)
    doc_import.run(db, b, wb, apply=True)
    assert db.query(VehicleBooking).filter(VehicleBooking.code == "DX902").count() == 1
    service.revert_batch(db, b, user_id=1)
    assert db.query(VehicleBooking).filter(VehicleBooking.code == "DX902").count() == 0
    assert b.status == ImportStatus.REVERTED
