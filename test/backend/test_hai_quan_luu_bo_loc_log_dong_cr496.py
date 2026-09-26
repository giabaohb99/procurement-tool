"""bao-CR-496 — lưu bộ lọc riêng từng người (F07) + nhật ký TỪNG DÒNG khi nạp (F01, ghi chú 25/09).

Đại ca chốt 25/09/2026:
  · bộ lọc lưu RIÊNG từng tài khoản, cột dùng chung có sẵn nhưng tắt; người A không thấy /
    không xóa được của B (404 như không có); trần 50 bộ / người; tên dài → 422 ở SCHEMA
    (SQLite không ép độ dài VARCHAR nên kiểm ở DB là xanh giả — duoc-CR-316);
  · log từng dòng chỉ ba kết cục Thêm mới · Lỗi · Trùng trong lô — KHÔNG có «Cập nhật»
    (nguồn không có số tờ khai); dòng trùng chỉ ĐÁNH DẤU, vẫn ghi vào bảng giá, luật đếm
    của bộ đọc giữ nguyên.
"""
import io
from datetime import datetime

import openpyxl
import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.modules.customs import importer, row_log
from app.modules.customs import saved_filter_service as SF
from app.modules.customs.constants import COLUMNS
from app.modules.customs.model import CustomsLine, CustomsSavedFilter
from app.modules.customs.schema import SavedFilterCreate, SavedFilterUpdate
from app.modules.import_tool import service as import_service
from app.modules.import_tool.model import (ImportBatch, ImportLog, ImportMode, ImportModule,
                                           ImportRowStatus, ImportStatus, LogLevel)

A, B = 11, 22   # hai tài khoản


# ── Việc 1: bộ lọc đã lưu ──────────────────────────────────────────────────────────────────

def test_saved_filters_are_private_per_account(db):
    mine = SF.create(db, A, "Abamectin 3.6 EC", "q=abamectin+3.6&tab=lines")
    SF.create(db, B, "Của B", "hs_code=3808")

    assert [f.name for f in SF.list_for(db, A)] == ["Abamectin 3.6 EC"]
    assert [f.name for f in SF.list_for(db, B)] == ["Của B"]
    assert mine.is_shared is False, "cột dùng chung có sẵn nhưng mặc định TẮT"

    other = SF.list_for(db, B)[0]
    with pytest.raises(HTTPException) as e:
        SF.get_own(db, A, other.id)
    assert e.value.status_code == 404, "của người khác = không tồn tại, không lộ 403"
    with pytest.raises(HTTPException):
        SF.delete(db, A, other.id)
    with pytest.raises(HTTPException):
        SF.update(db, A, other.id, "Đổi tên", None)
    assert db.get(CustomsSavedFilter, other.id) is not None, "không xóa được của B"


def test_shared_flag_reserved_for_later_and_listing_can_include_it(db):
    SF.create(db, B, "Chung", "q=x")
    shared = SF.list_for(db, B)[0]
    shared.is_shared = True
    db.commit()
    assert SF.list_for(db, A) == [], "mặc định chỉ của tôi — chưa mở bộ lọc chung"
    assert [f.name for f in SF.list_for(db, A, include_shared=True)] == ["Chung"], \
        "nhánh đọc bộ lọc chung chừa sẵn, bật là chạy không đổi API"


def test_update_renames_or_overwrites_params_and_blocks_duplicate_names(db):
    f = SF.create(db, A, "Tên cũ", "q=a")
    SF.create(db, A, "Tên đã có", "q=b")
    SF.update(db, A, f.id, None, "q=a&hs_code=3808")
    assert db.get(CustomsSavedFilter, f.id).params == "q=a&hs_code=3808" and f.name == "Tên cũ"
    SF.update(db, A, f.id, "Tên mới", None)
    assert db.get(CustomsSavedFilter, f.id).name == "Tên mới"
    with pytest.raises(HTTPException) as e:
        SF.update(db, A, f.id, "Tên đã có", None)
    assert e.value.status_code == 400
    with pytest.raises(HTTPException):
        SF.create(db, A, "Tên mới", "q=z")


def test_cap_fifty_per_account(db):
    for i in range(SF.MAX_PER_USER):
        SF.create(db, A, f"Bộ {i}", "q=x")
    with pytest.raises(HTTPException) as e:
        SF.create(db, A, "Bộ thứ 51", "q=x")
    assert e.value.status_code == 400 and "50" in e.value.detail
    SF.create(db, B, "B vẫn lưu được", "q=x")


def test_schema_rejects_long_or_blank_names_before_db():
    with pytest.raises(ValidationError):
        SavedFilterCreate(name="x" * 121, params="")
    with pytest.raises(ValidationError):
        SavedFilterCreate(name="   ", params="")
    with pytest.raises(ValidationError):
        SavedFilterCreate(name="ok", params="q=" + "x" * 5000)
    assert SavedFilterCreate(name="  Abamectin   3.6  ", params="").name == "Abamectin 3.6"
    assert SavedFilterUpdate(name=None, params=None).name is None
    with pytest.raises(ValidationError):
        SavedFilterUpdate(name="")


# ── Việc 2: nhật ký từng dòng ──────────────────────────────────────────────────────────────

def _row(**over):
    base = {
        "reg_date": "13-01-2026", "office_code": "HQHPKV3", "importer_tax_code": "'0500590269",
        "importer_name": "Công Ty TNHH Thú Y Toàn Cầu", "partner_name": "NOVADAN APS",
        "hs_code": "'38089990", "line_no": 1, "product_name": "ATRAZINE 97% TECH",
        "price_usd": 17.3897, "price_nt": 14.9, "adj_price_usd": None, "adj_price_nt": None,
        "currency": "EUR", "fx_rate": 30448.32, "usd_rate": 26089, "quantity": 880,
        "unit_code": "KGM", "origin_country": "DK", "contract_no": "770710",
        "contract_date": datetime(2025, 11, 20), "incoterm": "CIF",
        "transport_mode": "2-Đường biển (container)", "rate_import": 0, "rate_excise": 0,
        "rate_vat": 5, "rate_safeguard": 0, "tax_import": 0, "tax_excise": 0,
        "tax_vat": 19961918.592, "tax_environment": 0, "tax_safeguard": 0, "import_country": "VN",
    }
    base.update(over)
    return base


def _xlsx(rows) -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append([label for _, label in COLUMNS])
    for r in rows:
        ws.append([r[key] for key, _ in COLUMNS])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _batch(db, mode=ImportMode.APPLY) -> ImportBatch:
    b = ImportBatch(module=ImportModule.CUSTOMS_DECLARATION, mode=mode, filename="gtt02.xlsx",
                    sheet_info="", error_summary="", status=ImportStatus.RUNNING, created_by=A)
    db.add(b)
    db.commit()
    return b


def _statuses(db, bid):
    return [(x.row_no, x.row_status) for x in
            db.query(ImportLog).filter(ImportLog.batch_id == bid, ImportLog.row_status != 0)
            .order_by(ImportLog.row_no).all()]


def test_every_data_row_gets_exactly_one_status_line(db):
    """Tệp 4 dòng: dòng 2 OK · dòng 3 hỏng ngày · dòng 4 giống hệt dòng 2 · dòng 5 OK khác."""
    b = _batch(db)
    importer.run(db, b, _xlsx([_row(), _row(reg_date="không phải ngày"), _row(), _row(line_no=2)]),
                 apply=True)

    assert _statuses(db, b.id) == [(2, ImportRowStatus.NEW), (3, ImportRowStatus.ERROR),
                                   (4, ImportRowStatus.DUPLICATE), (5, ImportRowStatus.NEW)]
    dup = db.query(ImportLog).filter(ImportLog.batch_id == b.id, ImportLog.row_no == 4).one()
    assert "dòng 2" in dup.message and dup.ref_key == "ATRAZINE 97% TECH"
    assert row_log.count_rows(db, b.id) == {"total": 4, "new": 2, "error": 1, "duplicate": 1}


def test_duplicate_is_marked_but_still_written_and_counters_unchanged(db):
    """Đại ca chốt: KHÔNG xóa dòng trùng — có thể là hai lô hàng thật. Luật đếm bộ đọc giữ nguyên."""
    b = _batch(db)
    importer.run(db, b, _xlsx([_row(), _row(), _row()]), apply=True)

    assert db.query(CustomsLine).filter(CustomsLine.batch_id == b.id).count() == 3
    assert b.created_count == 3 and b.skipped_count == 0 and b.error_count == 0
    assert '"duplicate_rows": 2' in b.sheet_info
    assert [s for _, s in _statuses(db, b.id)] == [ImportRowStatus.NEW, ImportRowStatus.DUPLICATE,
                                                   ImportRowStatus.DUPLICATE]


def test_any_of_the_32_columns_differing_is_not_a_duplicate(db):
    """So trùng trên giá trị SAU chuẩn hóa của bộ đọc: lệch lượng hay lệch chữ là dòng khác,
    nhưng chỉ lệch khoảng trắng cuối tên (bộ đọc đã cắt) thì vẫn là cùng một dòng."""
    b = _batch(db)
    importer.run(db, b, _xlsx([_row(), _row(quantity=881), _row(product_name="ATRAZINE 97% TC"),
                               _row(product_name="ATRAZINE 97% TECH ")]), apply=True)
    assert [s for _, s in _statuses(db, b.id)] == [ImportRowStatus.NEW] * 3 + [ImportRowStatus.DUPLICATE]


def test_dry_run_also_writes_row_statuses_without_touching_lines(db):
    b = _batch(db, ImportMode.DRY_RUN)
    importer.run(db, b, _xlsx([_row(), _row()]), apply=False)
    assert db.query(CustomsLine).count() == 0
    assert row_log.count_rows(db, b.id) == {"total": 2, "new": 1, "error": 0, "duplicate": 1}


def test_list_rows_filters_by_status_and_pages_in_file_order(db):
    b = _batch(db)
    importer.run(db, b, _xlsx([_row(reg_date="x"), _row(), _row(), _row(line_no=9)]), apply=True)

    total, items = row_log.list_rows(db, b.id, None, {"offset": 0, "limit": 2})
    assert total == 4 and [i["row_no"] for i in items] == [2, 3]
    assert items[0]["row_status_label"] == "Lỗi" and items[1]["row_status_label"] == "Thêm mới"

    total, items = row_log.list_rows(db, b.id, int(ImportRowStatus.DUPLICATE), {"offset": 0, "limit": 50})
    assert total == 1 and items[0]["row_no"] == 4 and items[0]["product_name"] == "ATRAZINE 97% TECH"

    #  Dòng cảnh báo / thông báo thường của lô (row_status = 0) KHÔNG lẫn vào danh sách dòng.
    plain = db.query(ImportLog).filter(ImportLog.batch_id == b.id, ImportLog.row_status == 0).count()
    assert plain >= 1


def test_batch_notes_stay_readable_and_do_not_drown_in_row_statuses(db):
    """Chiều ngược của bài trên — và là chỗ bài trên không canh.

    Mỗi dòng dữ liệu đẻ một dòng kết cục trong CÙNG bảng `tab_import_log` (tệp GTT02 thật cỡ
    18.000 dòng). Đường nhật ký cũ (`import_service.get_logs`) phục vụ HAI màn — hộp «Nhật ký
    lô» của hải quan và màn Quản lý Import chung — và trước khi vá nó không lọc `row_status`:
    lô sạch vẫn trả về hàng nghìn dòng, câu «Không có ghi chú nào» không bao giờ hiện nữa, và
    ghi chú lỗi thật nằm giữa hàng trăm trang «Thêm mới».
    """
    b = _batch(db)
    importer.run(db, b, _xlsx([_row(), _row(line_no=2), _row(line_no=3)]), apply=True)
    assert row_log.count_rows(db, b.id)["total"] == 3

    total, items = import_service.get_logs(db, b.id, None, {"offset": 0, "limit": 500})
    assert all(i.row_status == 0 for i in items), "dòng kết cục lọt vào nhật ký thường"
    assert total == len(items) and total < 3, "lô sạch 3 dòng mà nhật ký thường lại có ≥ 3 dòng"

    #  Lỗi thật của một dòng vẫn phải còn trong nhật ký thường — lọc bỏ dòng kết cục chứ không
    #  lọc bỏ lỗi. Bộ đọc ghi lỗi ngày của dòng 2 thành một dòng nhật ký thường mức ERROR.
    b2 = _batch(db)
    importer.run(db, b2, _xlsx([_row(reg_date="không phải ngày"), _row()]), apply=True)
    _, items2 = import_service.get_logs(db, b2.id, None, {"offset": 0, "limit": 500})
    assert any(i.row_no == 2 and i.level == LogLevel.ERROR for i in items2)
    assert all(i.row_status == 0 for i in items2)


def test_row_status_enum_has_no_update_state():
    assert {s.name for s in ImportRowStatus} == {"NONE", "NEW", "ERROR", "DUPLICATE"}, \
        "GTT02 không có số tờ khai → không có kết cục «Cập nhật» (đại ca chốt 25/09/2026)"
