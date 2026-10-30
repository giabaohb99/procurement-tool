"""bao-CR-699 — gộp dòng hàng hải quan trùng (cùng tờ khai + giá + lượng, không xung đột) + chống trùng lúc nạp.

Canh:
  - gộp đúng nhóm: giữ dòng cũ nhất, điền bù ô trống (Nước nhận hàng) từ dòng bị xóa, tính lại mã băm;
  - KHÔNG đụng: nhóm khác giá / lượng, nhóm xung đột ô có chữ (đếm theo cột), nhóm có lịch sử sửa / ghi đè;
  - chạy thử chỉ đếm, không ghi; chạy thật xong chạy lại không còn gì để gộp;
  - nạp lại tệp cũ (dòng khác mã băm nhưng cùng tờ khai + giá + lượng) → Đã có, không sinh dòng thừa;
    trùng trong cùng tệp → Trùng; khớp mà xung đột → vẫn Thêm, ghi chú cần rà;
  - việc nền có lịch ngày 1 và 16, công tắc tắt thì bỏ qua.
"""
from app.modules.customs import line_change, line_merge, tasks
from app.modules.customs.constants import CustomsLineChangeAction, CustomsLineChangeSource
from app.modules.customs.model import CustomsLine
from app.modules.import_tool.model import ImportLog, ImportRowStatus

from app.modules.customs import importer
from test_hai_quan_luu_bo_loc_log_dong_cr496 import _batch, _row, _statuses, _xlsx

COPY_SKIP = {"id"}


def _lines(db):
    db.expire_all()
    return db.query(CustomsLine).order_by(CustomsLine.id).all()


def _clone(db, line: CustomsLine, **over) -> CustomsLine:
    """Chép một dòng đã lưu sang "lô khác" — giả dữ liệu nạp trước bao-CR-699 (khác mã băm, cùng tờ khai)."""
    values = {c.name: getattr(line, c.name) for c in CustomsLine.__table__.c if c.name not in COPY_SKIP}
    values.update(batch_id=line.batch_id + 1000, row_hash="x" * 40, **over)
    row = CustomsLine(**values)
    db.add(row)
    db.commit()
    return row


def _seed(db):
    """Lô đầu nạp 3 dòng (Nước nhận hàng trống) rồi chép thêm 4 dòng như đã từng nạp lại."""
    b = _batch(db)
    importer.run(db, b, _xlsx([_row(import_country=None), _row(line_no=2, import_country=None),
                               _row(line_no=3, import_country=None)]), apply=True)
    one, two, three = _lines(db)
    fill = _clone(db, one, import_country="VN")                    # gộp được — điền bù Nước nhận hàng
    other_price = _clone(db, two, price_usd=99)                     # khác giá → không cùng nhóm
    clash = _clone(db, two, contract_no="KHAC-1")                   # xung đột Số hợp đồng → để nguyên
    history = _clone(db, three)                                     # nhóm có lịch sử sửa → để nguyên
    line_change.record_snapshots(db, [three], CustomsLineChangeAction.UPDATE, CustomsLineChangeSource.MANUAL,
                                 batch_id=0, user_id=1)
    db.commit()
    return one, fill, other_price, clash, history


def test_chay_thu_chi_dem_va_phan_bo_xung_dot(db):
    _seed(db)
    before = len(_lines(db))
    out = line_merge.merge_duplicates(db, dry_run=True)
    assert out["status"] == "dry_run" and len(_lines(db)) == before
    assert (out["candidate_groups"], out["merged_groups"], out["matched_rows"]) == (3, 1, 1)
    assert (out["conflict_groups"], out["history_groups"], out["filled_rows"]) == (1, 1, 1)
    assert out["conflict_by_field"] == {"contract_no": 1}


def test_gop_giu_dong_cu_dien_bu_va_khong_dung_nhom_khac(db):
    one, fill, other_price, clash, history = _seed(db)
    old_hash = one.row_hash
    out = line_merge.merge_duplicates(db, dry_run=False)
    assert (out["status"], out["merged_groups"], out["deleted_rows"]) == ("success", 1, 1)
    ids = {x.id for x in _lines(db)}
    assert fill.id not in ids and {one.id, other_price.id, clash.id, history.id} <= ids
    kept = db.get(CustomsLine, one.id)
    assert kept.import_country == "VN" and kept.row_hash != old_hash and len(kept.row_hash) == 40
    again = line_merge.merge_duplicates(db, dry_run=True)
    assert (again["merged_groups"], again["matched_rows"]) == (0, 0)


def test_nap_lai_tep_cu_khong_sinh_dong_thua(db):
    first = _batch(db)
    importer.run(db, first, _xlsx([_row(import_country=None)]), apply=True)
    #  Tệp sau có thêm Nước nhận hàng (khác mã băm) + một dòng lặp trong tệp + một dòng xung đột Số hợp đồng.
    second = _batch(db)
    importer.run(db, second, _xlsx([_row(import_country="VN"), _row(line_no=2), _row(line_no=2, import_country=None),
                                    _row(contract_no="KHAC-2")]), apply=True)
    assert _statuses(db, second.id) == [(2, ImportRowStatus.EXISTING), (3, ImportRowStatus.NEW),
                                        (4, ImportRowStatus.DUPLICATE), (5, ImportRowStatus.NEW)]
    message = db.query(ImportLog).filter(ImportLog.batch_id == second.id, ImportLog.row_no == 5,
                                         ImportLog.row_status != 0).one().message
    assert "Số hợp đồng" in message and "cần rà" in message
    assert len(_lines(db)) == 3 and second.created_count == 2


def test_viec_nen_co_lich_va_cong_tac(db, monkeypatch):
    from app.core import app_settings
    from app.core.celery_app import celery_app

    entry = celery_app.conf.beat_schedule["merge-customs-duplicate-lines"]
    assert entry["task"] == "customs.merge_duplicate_lines"
    assert entry["schedule"].day_of_month == {1, 16} and entry["schedule"].hour == {3}
    monkeypatch.setattr(app_settings, "get", lambda key: False if key == "customs_line_merge_enabled" else None)
    assert tasks.merge_duplicate_lines_task.run() == {"status": "disabled"}
