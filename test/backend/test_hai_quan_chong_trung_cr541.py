"""bao-CR-541 — Tra cứu thị trường: chống trùng dòng khi nạp GTT02 bằng mã băm.

Đại ca chốt 01/10/2026: nguồn xuất ra là đổ vào luôn, người nạp không biết tệp nào chồng tệp
nào → hệ thống tự so. Trùng thì BỎ QUA; không ghi đè; bỏ hẳn «thay theo khoảng ngày».

Bẫy được canh ở đây đều IM LẶNG nếu vỡ:
  · mã tính từ dòng trong tệp phải BẰNG mã tính lại từ dòng đã lưu — lệch là chống trùng
    thủng mà không ai hay (số làm tròn theo số lẻ của cột, doanh nghiệp quy về mã số thuế);
  · tệp mới xuất thiếu dòng KHÔNG được xóa dữ liệu cũ (rủi ro R1 của luật cũ);
  · dòng khác giá nhưng trùng cột nhận diện vẫn THÊM (đa số là lô thật), chỉ ghi chú nghi sửa giá.
"""
from decimal import Decimal

from app.modules.customs import dedupe, importer, row_log
from app.modules.customs.model import CustomsLine
from app.modules.import_tool import service as import_service
from app.modules.import_tool.model import ImportLog, ImportMode, ImportRowStatus, ImportStatus

from test_hai_quan_luu_bo_loc_log_dong_cr496 import _batch, _row, _statuses, _xlsx


def _lines(db):
    return db.query(CustomsLine).order_by(CustomsLine.id).all()


def _message(db, bid, row_no):
    return db.query(ImportLog).filter(ImportLog.batch_id == bid, ImportLog.row_no == row_no,
                                      ImportLog.row_status != 0).one().message


# ── Mã băm ──────────────────────────────────────────────────────────────────

def test_canonical_value_keeps_null_zero_and_blank_apart():
    assert len({dedupe.canonical_value("price_usd", None), dedupe.canonical_value("price_usd", 0),
                dedupe.canonical_value("office_code", "")}) == 3


def test_canonical_value_rounds_to_column_scale_and_folds_text():
    #  price_usd là Numeric(16, 4): 17.38974 và 17.3897 lưu xuống là MỘT số.
    assert dedupe.canonical_value("price_usd", Decimal("17.38974")) == dedupe.canonical_value("price_usd", 17.3897)
    assert dedupe.canonical_value("product_name", "  Atrazine   97% TECH ") == \
        dedupe.canonical_value("product_name", "ATRAZINE 97% TECH")


def test_hash_from_file_equals_hash_recomputed_from_stored_row(db):
    """Nạp xong, xóa mã trong DB rồi tính lại từ dòng đã lưu — phải ra đúng mã lúc nạp."""
    b = _batch(db)
    importer.run(db, b, _xlsx([_row(price_usd=17.38974, tax_vat=19961918.5924), _row(line_no=2)]),
                 apply=True)
    stamped = {x.id: x.row_hash for x in _lines(db)}
    assert all(len(h) == 40 for h in stamped.values())

    db.query(CustomsLine).update({CustomsLine.row_hash: ""})
    db.commit()
    index = dedupe.load_existing(db, min(x.reg_date for x in _lines(db)), max(x.reg_date for x in _lines(db)))
    db.commit()
    assert set(index.by_hash) == set(stamped.values())
    assert {x.id: x.row_hash for x in _lines(db)} == stamped, "dòng cũ chưa có mã phải được ghi lại mã"


# ── Luật nạp ────────────────────────────────────────────────────────────────

def test_reimport_skips_existing_rows_and_names_origin_batch(db):
    first = _batch(db)
    importer.run(db, first, _xlsx([_row(), _row(line_no=2)]), apply=True)
    second = _batch(db)
    importer.run(db, second, _xlsx([_row(), _row(line_no=3)]), apply=True)

    assert len(_lines(db)) == 3
    assert _statuses(db, second.id) == [(2, ImportRowStatus.EXISTING), (3, ImportRowStatus.NEW)]
    assert f"lô #{first.id}" in _message(db, second.id, 2)
    assert second.created_count == 1
    assert row_log.count_rows(db, second.id) == {"total": 2, "new": 1, "error": 0, "duplicate": 0,
                                                 "existing": 1, "updated": 0, "deleted": 0, "ignored": 0}


def test_new_file_missing_rows_never_deletes_old_data(db):
    """Rủi ro R1 của luật cũ: tệp mới phủ cùng khoảng ngày nhưng xuất thiếu dòng."""
    first = _batch(db)
    importer.run(db, first, _xlsx([_row(reg_date="13-01-2026"), _row(reg_date="20-01-2026"),
                                   _row(reg_date="27-01-2026")]), apply=True)
    partial = _batch(db)
    importer.run(db, partial, _xlsx([_row(reg_date="13-01-2026", line_no=5), _row(reg_date="27-01-2026")]),
                 apply=True)

    assert len(_lines(db)) == 4
    assert partial.deleted_count == 0 and partial.created_count == 1


def test_same_identity_different_price_is_added_with_suspect_note(db):
    """Không ghi đè: dòng trùng cột nhận diện mà khác giá vẫn thêm, kèm câu nghi sửa giá."""
    first = _batch(db)
    importer.run(db, first, _xlsx([_row(price_usd=17.3897)]), apply=True)
    second = _batch(db)
    importer.run(db, second, _xlsx([_row(price_usd=18.5)]), apply=True)

    assert [float(x.price_usd) for x in _lines(db)] == [17.3897, 18.5]
    assert _statuses(db, second.id) == [(2, ImportRowStatus.NEW)]
    assert "nghi sửa giá" in _message(db, second.id, 2) and f"lô #{first.id}" in _message(db, second.id, 2)
    assert '"suspect_rows": 1' in second.sheet_info


def test_same_tax_code_different_importer_spelling_is_the_same_row(db):
    """DB chỉ giữ một tên cho mỗi mã số thuế → khóa so trùng dùng mã số thuế, không dùng tên."""
    first = _batch(db)
    importer.run(db, first, _xlsx([_row(importer_name="CôNG TY TNHH BAYER VIệT NAM")]), apply=True)
    second = _batch(db)
    importer.run(db, second, _xlsx([_row(importer_name="Công ty TNHH Bayer Việt Nam")]), apply=True)
    assert len(_lines(db)) == 1 and second.created_count == 0


def test_dry_run_reports_existing_without_writing(db):
    first = _batch(db)
    importer.run(db, first, _xlsx([_row()]), apply=True)
    trial = _batch(db, ImportMode.DRY_RUN)
    importer.run(db, trial, _xlsx([_row(), _row(line_no=2), _row(line_no=2)]), apply=False)

    assert len(_lines(db)) == 1
    assert trial.created_count == 1
    assert row_log.count_rows(db, trial.id) == {"total": 3, "new": 1, "error": 0, "duplicate": 1,
                                                "existing": 1, "updated": 0, "deleted": 0, "ignored": 0}


def test_old_rows_without_hash_are_recognised_on_next_import(db):
    """Dữ liệu nạp trước bao-CR-541 chưa có mã: lần nạp sau chạm khoảng ngày của nó tự tính."""
    first = _batch(db)
    importer.run(db, first, _xlsx([_row()]), apply=True)
    db.query(CustomsLine).update({CustomsLine.row_hash: ""})
    db.commit()

    second = _batch(db)
    importer.run(db, second, _xlsx([_row()]), apply=True)
    assert len(_lines(db)) == 1 and _lines(db)[0].row_hash
    assert _statuses(db, second.id) == [(2, ImportRowStatus.EXISTING)]


def test_new_batch_can_always_be_reverted(db):
    """Lô mới chỉ thêm dòng của chính nó → hoàn tác không đụng dòng của lô khác."""
    first = _batch(db)
    importer.run(db, first, _xlsx([_row()]), apply=True)
    second = _batch(db)
    importer.run(db, second, _xlsx([_row(), _row(line_no=2)]), apply=True)

    res = import_service.revert_batch(db, second, user_id=1)
    assert res["ok"] and second.status == ImportStatus.REVERTED
    assert [x.batch_id for x in _lines(db)] == [first.id]


# ── Script dọn dữ liệu cũ ───────────────────────────────────────────────────

def test_backfill_then_find_surplus_keeps_smallest_id_per_group(db):
    """Dựng lại tình trạng prod: dòng trùng đã ghi (luật 496), chưa có mã."""
    b = _batch(db)
    importer.run(db, b, _xlsx([_row(), _row(line_no=2)]), apply=True)
    keep = _lines(db)
    keep_ids = [x.id for x in keep]
    clone = {c.name: getattr(keep[0], c.name) for c in CustomsLine.__table__.c if c.name != "id"}
    db.add_all([CustomsLine(**clone), CustomsLine(**clone)])
    db.flush()
    db.query(CustomsLine).update({CustomsLine.row_hash: ""})
    db.commit()

    assert dedupe.backfill_hashes(db, chunk=2) == 4
    groups, surplus = dedupe.find_surplus_ids(db)
    assert groups == 1 and len(surplus) == 2
    assert not set(keep_ids) & set(surplus)
