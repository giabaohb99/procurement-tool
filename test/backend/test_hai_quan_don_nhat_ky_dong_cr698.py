"""bao-CR-698 — dọn nhật ký từng dòng của lô nạp hải quan.

Canh:
  - xóa đúng nhóm: Thêm mới / Đã có / Trùng của category customs_row cũ hơn N ngày;
  - giữ đúng nhóm: Lỗi, Ghi đè, Xóa, Bỏ qua, dòng Thêm mới "nghi sửa giá", dòng còn trong hạn, category khác;
  - N = 0 (cấu hình) thì không xóa gì; xóa theo lô có trần số lô;
  - đầu hộp Nhật ký lô: số hụt sau khi dọn lấy lại từ lô, kèm cờ pruned + câu ghi chú;
  - việc nền có trong lịch beat.
"""
import json
from datetime import datetime, timedelta

from app.core import app_settings
from app.modules.customs import row_log, row_log_cleanup
from app.modules.import_tool.model import ImportBatch, ImportLog, ImportModule, ImportRowStatus, LogLevel

S = ImportRowStatus
NOW = datetime(2026, 10, 30, 2, 45)
OLD = NOW - timedelta(days=45)
FRESH = NOW - timedelta(days=5)


def _batch(db) -> ImportBatch:
    b = ImportBatch(module=int(ImportModule.CUSTOMS_DECLARATION), filename="gtt02.xlsx", created_count=3,
                    sheet_info=json.dumps({"existing_rows": 2, "duplicate_rows": 1}), total_rows=7)
    db.add(b)
    db.flush()
    return b


def _log(db, batch, status, message="x", *, when=OLD, category=row_log.CATEGORY) -> ImportLog:
    row = ImportLog(batch_id=batch.id, sheet=row_log.SHEET, row_no=1, level=int(LogLevel.INFO), category=category,
                    message=message, row_status=int(status), created_at=when)
    db.add(row)
    db.flush()
    return row


def _seed(db):
    b = _batch(db)
    gone = [_log(db, b, S.NEW, "Thêm mới"), _log(db, b, S.NEW, "Thêm mới"), _log(db, b, S.EXISTING, "Đã có"),
            _log(db, b, S.EXISTING, "Đã có"), _log(db, b, S.DUPLICATE, "Giống hệt dòng 3")]
    kept = [_log(db, b, S.ERROR, "Không đọc được Ngày đăng ký"), _log(db, b, S.UPDATED, "Ghi đè ID 5"),
            _log(db, b, S.DELETED, "Xóa ID 6"), _log(db, b, S.IGNORED, "Xóa: ô ID trống — bỏ qua"),
            _log(db, b, S.NEW, "Thêm mới — nghi sửa giá/số lượng so với dòng đã có ở lô #3, cần rà"),
            _log(db, b, S.NEW, "Thêm mới", when=FRESH),
            _log(db, _batch(db), S.EXISTING, "Đã có", category="customs")]      # nhóm nhật ký khác, lô khác
    db.commit()
    return b, {r.id for r in gone}, {r.id for r in kept}


def _ids(db) -> set[int]:
    db.expire_all()
    return {r.id for r in db.query(ImportLog.id)}


def test_xoa_dung_nhom_giu_dung_nhom(db):
    _b, gone, kept = _seed(db)
    out = row_log_cleanup.cleanup(db, now=NOW, days=30)
    assert out["status"] == "success" and out["deleted"] == len(gone)
    assert _ids(db) == kept


def test_n_bang_0_khong_xoa(db, monkeypatch):
    _b, gone, kept = _seed(db)
    monkeypatch.setattr(app_settings, "get", lambda key: 0 if key == "customs_row_log_keep_days" else None)
    assert row_log_cleanup.cleanup(db, now=NOW) == {"status": "disabled", "deleted": 0}
    assert _ids(db) == gone | kept
    monkeypatch.setattr(app_settings, "get", lambda key: 30 if key == "customs_row_log_keep_days" else None)
    assert row_log_cleanup.cleanup(db, now=NOW)["deleted"] == len(gone)


def test_tran_so_lo_moi_dem(db, monkeypatch):
    _b, gone, _kept = _seed(db)
    monkeypatch.setattr(row_log_cleanup, "CLEANUP_BATCH_SIZE", 2)
    first = row_log_cleanup.cleanup(db, now=NOW, days=30, max_batches=1)
    assert (first["status"], first["deleted"]) == ("partial", 2)
    rest = row_log_cleanup.cleanup(db, now=NOW, days=30)
    assert rest["deleted"] == len(gone) - 2


def test_dau_hop_lay_so_cua_lo_khi_da_don(db):
    b, _gone, _kept = _seed(db)
    before = row_log.count_rows(db, b.id, b)
    assert before["pruned"] is False and (before["new"], before["existing"], before["duplicate"]) == (4, 2, 1)
    row_log_cleanup.cleanup(db, now=NOW, days=30)
    after = row_log.count_rows(db, b.id, b)
    #  Nhật ký còn 2 dòng Thêm mới (nghi sửa giá + còn hạn) nhưng lô ghi 3 → lấy số lô; Đã có / Trùng cũng vậy.
    assert (after["new"], after["existing"], after["duplicate"]) == (3, 2, 1)
    assert after["pruned"] is True and "đã được dọn" in after["pruned_note"]
    assert after["total"] == sum(after[k] for k in ("new", "error", "duplicate", "existing", "updated", "deleted",
                                                     "ignored"))
    assert "pruned" not in row_log.count_rows(db, b.id)          # gọi không kèm lô: giữ dạng cũ


def test_viec_nen_co_trong_lich():
    from app.core.celery_app import celery_app

    entry = celery_app.conf.beat_schedule["cleanup-customs-row-logs"]
    assert entry["task"] == "customs.cleanup_row_logs"
    import app.modules.customs.tasks  # noqa: F401

    assert "customs.cleanup_row_logs" in celery_app.tasks
