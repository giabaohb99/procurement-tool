"""bao-CR-718 — lô XUẤT TOÀN BỘ Tra cứu thị trường chạy nền, chia nhiều tệp.

Canh: báo ngay tổng dòng + số tệp dự kiến; mỗi người một lô đang chạy; đọc theo khối id tăng dần (không sót, không lặp,
đúng bộ lọc, không lọt dòng nạp sau lúc tạo); mỗi tệp lưu kho + một dòng nhật ký xuất; xong thì chuông và nhả lượt; dừng
được giữa chừng; dọn lô kẹt và lô quá hạn; các đường API gác bằng `customs_price.export`.
"""
import inspect
import io
from datetime import date, datetime, timedelta
from decimal import Decimal

import openpyxl
import pytest
from fastapi import HTTPException
from fastapi.routing import APIRoute

from app.modules.customs import line_export
from app.modules.customs.constants import CustomsExportStatus
from app.modules.customs.model import CustomsExportBatch, CustomsLine
from app.modules.export_log.model import ExportLog
from app.modules.notification.model import Notification

F = {k: "" for k in line_export.FILTER_LABELS}
F.update({"importer_id": [], "partner_id": [], "batch_id": [], "product_kind": []})
USER, OTHER = 7, 8


@pytest.fixture
def store(monkeypatch):
    """Kho giả: giữ nội dung tệp theo khóa, không ghi ra đĩa / R2; bỏ nghỉ giữa khối; cỡ tệp 3 dòng, khối 2 dòng."""
    saved = {}

    def upload(fh, key, media=""):
        saved[key] = fh.read()
        return f"/u/{key}"
    monkeypatch.setattr(line_export, "upload_fileobj", upload)
    monkeypatch.setattr(line_export, "delete_key", lambda key: saved.pop(key, None))
    monkeypatch.setattr(line_export, "EXPORT_ROWS_PER_FILE", 3)
    monkeypatch.setattr(line_export, "EXPORT_CHUNK_ROWS", 2)
    monkeypatch.setattr(line_export, "EXPORT_CHUNK_PAUSE_SECONDS", 0)
    return saved


def _lines(db, names):
    for i, name in enumerate(names):
        db.add(CustomsLine(reg_date=date(2026, 1, 1) + timedelta(days=i), product_name=name, unit_code="KGM",
                           price_usd=Decimal("1"), quantity=Decimal("1"), hs_code="38089319"))
    db.commit()


def _run_all(db, batch_id):
    parts = 0
    while line_export.run_next_part(db, batch_id, sleep=lambda s: None):
        parts += 1
        assert parts < 50
    db.expire_all()
    return db.get(CustomsExportBatch, batch_id)


def _ids_in(store, batch):
    out = []
    for x in batch.files:
        key = next(k for k in store if x["filename"].rsplit(".", 1)[0].split("-tep-")[0] in k and
                   x["filename"].split("-tep-")[1].split(".")[0] in k.split("-tep-")[-1])
        ws = openpyxl.load_workbook(io.BytesIO(store[key])).active
        out += [r[0] for r in ws.iter_rows(min_row=2, values_only=True)]
    return out


def test_create_reports_totals_and_expected_files(db, store):
    _lines(db, [f"ABAMECTIN {i}" for i in range(7)] + ["GLYPHOSATE"])
    b = line_export.create_batch(db, {**F, "q": "abamectin"}, USER)
    assert (b.total_rows, b.file_count, b.rows_per_file) == (7, 3, 3)
    assert b.status == CustomsExportStatus.QUEUED and b.active_user_id == USER
    assert b.filters == {"q": "abamectin"} and b.filter_summary == "Tên hàng: abamectin"


def test_one_running_batch_per_user_and_empty_filter_rejected(db, store):
    _lines(db, ["ABAMECTIN"])
    line_export.create_batch(db, F, USER)
    with pytest.raises(HTTPException) as e:
        line_export.create_batch(db, F, USER)
    assert e.value.status_code == 409
    assert line_export.create_batch(db, F, OTHER).active_user_id == OTHER, "người khác vẫn xuất được"
    with pytest.raises(HTTPException) as e:
        line_export.create_batch(db, {**F, "q": "khongco"}, 9)
    assert e.value.status_code == 400


def test_parts_cover_every_matching_row_once_and_skip_rows_added_later(db, store):
    _lines(db, [f"ABAMECTIN {i}" for i in range(7)] + ["GLYPHOSATE"])
    want = [r.id for r in db.query(CustomsLine).filter(CustomsLine.product_name.like("ABAMECTIN%"))
            .order_by(CustomsLine.id)]
    b = line_export.create_batch(db, {**F, "q": "abamectin"}, USER)
    _lines(db, ["ABAMECTIN NẠP SAU"])                       # id > max_id lúc tạo — không được lọt vào
    b = _run_all(db, b.id)
    assert b.status == CustomsExportStatus.DONE and b.active_user_id is None
    assert [x["rows"] for x in b.files] == [3, 3, 1] and b.files_done == 3 and b.rows_done == 7
    assert _ids_in(store, b) == want
    logs = db.query(ExportLog).filter(ExportLog.entity == "customs_line").order_by(ExportLog.id).all()
    assert [x.row_count for x in logs] == [3, 3, 1] and all(x.file_id and x.created_by == USER for x in logs)
    assert "Lô xuất #" in logs[0].filter_summary
    note = db.query(Notification).filter(Notification.user_id == USER).one()
    assert note.link == f"/procurement/customs-prices/exports/{b.id}" and "3 tệp" in note.title
    assert b.expires_at is not None


def test_exact_multiple_does_not_schedule_an_empty_file(db, store):
    _lines(db, [f"ABAMECTIN {i}" for i in range(6)])
    b = _run_all(db, line_export.create_batch(db, F, USER).id)
    assert [x["rows"] for x in b.files] == [3, 3] and b.file_count == 2


def test_cancel_stops_and_frees_the_user(db, store):
    _lines(db, [f"ABAMECTIN {i}" for i in range(7)])
    b = line_export.create_batch(db, F, USER)
    assert line_export.run_next_part(db, b.id, sleep=lambda s: None) is True
    line_export.cancel(db, b, USER)
    assert line_export.run_next_part(db, b.id, sleep=lambda s: None) is False
    db.expire_all()
    b = db.get(CustomsExportBatch, b.id)
    assert b.status == CustomsExportStatus.CANCELLED and b.files_done == 1 and b.active_user_id is None
    with pytest.raises(HTTPException):
        line_export.cancel(db, b, USER)
    line_export.create_batch(db, F, USER)       # nhả lượt: tạo lô mới được


def test_cleanup_fails_stuck_batches_and_expires_old_files(db, store):
    _lines(db, [f"ABAMECTIN {i}" for i in range(4)])
    done = _run_all(db, line_export.create_batch(db, F, USER).id)
    stuck = line_export.create_batch(db, F, OTHER)
    db.query(CustomsExportBatch).filter(CustomsExportBatch.id == stuck.id).update(
        {"updated_at": datetime.now() - timedelta(hours=3), "created_at": datetime.now() - timedelta(hours=3)})
    db.commit()
    assert len(store) == 2
    res = line_export.cleanup(db, now=done.expires_at + timedelta(minutes=1))
    assert res["stale"] == 1 and res["files_removed"] == 2 and not store
    db.expire_all()
    assert db.get(CustomsExportBatch, done.id).status == CustomsExportStatus.EXPIRED
    assert db.get(CustomsExportBatch, stuck.id).status == CustomsExportStatus.FAILED
    assert db.get(CustomsExportBatch, stuck.id).active_user_id is None
    assert all(x.file_id == 0 for x in db.query(ExportLog).filter(ExportLog.entity == "customs_line"))
    out = line_export.batch_out(db.get(CustomsExportBatch, done.id))
    assert out["status_label"] == "Hết hạn" and not any(f["available"] for f in out["files"])


def test_failed_batch_notifies_and_frees_the_user(db, store):
    _lines(db, ["ABAMECTIN"])
    b = line_export.create_batch(db, F, USER)
    line_export.mark_failed(db, b.id, "hỏng thử")
    db.expire_all()
    b = db.get(CustomsExportBatch, b.id)
    assert b.status == CustomsExportStatus.FAILED and b.active_user_id is None and b.error == "hỏng thử"
    assert db.query(Notification).filter(Notification.user_id == USER).one().title.endswith("bị lỗi")


def test_export_batch_routes_require_customs_export():
    from app.main import app
    seen = {}
    for r in app.routes:
        if isinstance(r, APIRoute) and r.path.startswith("/api/customs/export-batches"):
            perms = set()
            for d in r.dependant.dependencies:
                nl = inspect.getclosurevars(d.call).nonlocals if callable(d.call) else {}
                if "entity" in nl and "action" in nl:
                    perms.add(f"{nl['entity']}.{nl['action']}")
            for m in r.methods:
                seen[f"{m} {r.path}"] = perms
    assert set(seen) == {"POST /api/customs/export-batches", "GET /api/customs/export-batches",
                         "GET /api/customs/export-batches/{bid}", "POST /api/customs/export-batches/{bid}/cancel",
                         "GET /api/customs/export-batches/{bid}/files/{part}"}
    assert all(p == {"customs_price.export"} for p in seen.values()), seen
