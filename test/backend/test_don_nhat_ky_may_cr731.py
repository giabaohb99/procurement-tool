"""bao-CR-731 — dọn nhật ký do máy ghi (`system_log/machine_cleanup.py`).

Mỗi luật hai vế: dọn đúng thứ quá hạn, và KHÔNG đụng thứ phải giữ (dòng lỗi, dòng mới nhất mỗi đối tượng của sổ đồng
bộ, dòng kết cục của lô hải quan, chứng cứ thao tác).
"""
from datetime import datetime, timedelta
from types import SimpleNamespace

from app.core.logging_policy import MACHINE_LOG_TABLES, NO_LOG_TABLES
from app.modules.change_log.model import ChangeLog
from app.modules.import_tool.model import ImportBatch, ImportLog, LogLevel
from app.modules.notification.email_log_controller import resend_block_reason
from app.modules.notification.model import EmailLog
from app.modules.request_log.tasks import get_cutoff
from app.modules.sync_log import service as sync_service
from app.modules.sync_log.constants import SyncAction, SyncDirection, SyncGrain, SyncStatus
from app.modules.sync_log.model import SyncLog
from app.modules.system_log import machine_cleanup

NOW = datetime(2026, 11, 20, 4, 0)
OLD = NOW - timedelta(days=200)
_seq = iter(range(1, 10_000))


def _sync(db, status, *, days_ago=200, legacy_id="", job="", grain=SyncGrain.RECORD, run_id=0, content_hash=""):
    created = NOW - timedelta(days=days_ago)
    row = SyncLog(source="datxe", grain=int(grain), job=job, entity="" if job else "vehicle_booking",
                  direction=int(SyncDirection.INBOUND), action=int(SyncAction.CREATE), legacy_id=legacy_id,
                  status=int(status), run_id=run_id, content_hash=content_hash, event_id=f"ev-{next(_seq)}",
                  cursor_to="2026-01-01T00:00:00" if job else "", created_at=created)
    db.add(row)
    db.commit()
    return SimpleNamespace(id=row.id)   # id lấy TRƯỚC khi việc dọn commit (đối tượng đã xóa thì không đọc lại được)


def _run(db, only, dry_run=False):
    return machine_cleanup.run(db, now=NOW, dry_run=dry_run, only={only})


def _alive(db, model, rows):
    ids = [r.id for r in rows]
    db.expire_all()
    return {i for i in ids if db.get(model, i) is not None}


# ---------- sổ đồng bộ ----------
def test_so_dong_bo_don_bo_qua_14_ngay_thanh_cong_90_ngay_giu_loi(db):
    skip_old = _sync(db, SyncStatus.SKIPPED, days_ago=20, job="pull")
    skip_new = _sync(db, SyncStatus.SKIPPED, days_ago=3, job="pull")
    ok_old = _sync(db, SyncStatus.SUCCESS, days_ago=120, legacy_id="dx-1")
    ok_mid = _sync(db, SyncStatus.SUCCESS, days_ago=60, legacy_id="dx-1")
    fail_old = _sync(db, SyncStatus.FAILED, days_ago=300, legacy_id="dx-2")
    pend_old = _sync(db, SyncStatus.PENDING, days_ago=300, legacy_id="dx-3")

    assert _run(db, "sync_log", dry_run=True)["total"] == 2
    _run(db, "sync_log")
    assert _alive(db, SyncLog, [skip_old, skip_new, ok_old, ok_mid, fail_old, pend_old]) == \
        {skip_new.id, ok_mid.id, fail_old.id, pend_old.id}


def test_so_dong_bo_giu_dong_moi_nhat_moi_doi_tuong_du_da_qua_han(db):
    """Ba chỗ đọc ngược sổ: so nội dung lần trước, con trỏ kéo, và chuông lỗi đã vá."""
    ok_only = _sync(db, SyncStatus.SUCCESS, days_ago=200, legacy_id="dx-9", content_hash="h9")
    run_old = _sync(db, SyncStatus.SUCCESS, days_ago=200, job="pull_updated", grain=SyncGrain.RUN)
    run_new = _sync(db, SyncStatus.SUCCESS, days_ago=150, job="pull_updated", grain=SyncGrain.RUN)
    fail = _sync(db, SyncStatus.FAILED, days_ago=250, legacy_id="dx-8")
    healed = _sync(db, SyncStatus.SKIPPED, days_ago=240, legacy_id="dx-8")

    _run(db, "sync_log")
    assert _alive(db, SyncLog, [ok_only, run_old, run_new, fail, healed]) == {ok_only.id, run_new.id, fail.id, healed.id}
    assert sync_service.is_unchanged(db, "datxe", "vehicle_booking", "dx-9", "h9") is True
    assert sync_service.last_successful_run(db, "datxe", "pull_updated").id == run_new.id
    assert fail.id not in {r.id for r in sync_service.find_stale_failures(db, hours=1)}


def test_so_dong_bo_giu_luot_chay_con_dong_loi_tro_toi(db):
    run = _sync(db, SyncStatus.SUCCESS, days_ago=200, job="full_sweep", grain=SyncGrain.RUN)
    _sync(db, SyncStatus.SUCCESS, days_ago=100, job="full_sweep", grain=SyncGrain.RUN)
    _sync(db, SyncStatus.FAILED, days_ago=200, legacy_id="dx-7", run_id=run.id)
    _run(db, "sync_log")
    assert _alive(db, SyncLog, [run]) == {run.id}


# ---------- nhật ký thư ----------
def _mail(db, days_ago, body="<p>noi dung</p>", event="dx_submitted"):
    row = EmailLog(event=event, to_email="an@dego.vn", subject="S", status="sent", html_body=body,
                   created_at=NOW - timedelta(days=days_ago))
    db.add(row)
    db.commit()
    return SimpleNamespace(id=row.id)   # id lấy TRƯỚC khi việc dọn commit (đối tượng đã xóa thì không đọc lại được)


def test_thu_qua_90_ngay_don_noi_dung_giu_dong_va_bao_ly_do(db):
    old, fresh = _mail(db, 100), _mail(db, 10)
    never = _mail(db, 100, body=None, event="password_reset")
    assert _run(db, "email_body", dry_run=True)["total"] == 1
    _run(db, "email_body")
    db.expire_all()
    assert db.get(EmailLog, old.id).html_body == "" and db.get(EmailLog, fresh.id).html_body
    assert db.get(EmailLog, never.id).html_body is None
    reason = resend_block_reason(db.get(EmailLog, old.id), None)
    assert "quá 90 ngày đã dọn nội dung" in reason


def test_thu_qua_16_thang_xoa_dong(db):
    gone, kept = _mail(db, 520, body=None), _mail(db, 400, body=None)
    _run(db, "email_row")
    assert _alive(db, EmailLog, [gone, kept]) == {kept.id}


# ---------- nhật ký nạp tệp ----------
def _ilog(db, level, days_ago, row_status=0, category="survey"):
    row = ImportLog(batch_id=1, level=int(level), category=category, message="m", row_status=row_status,
                    created_at=NOW - timedelta(days=days_ago))
    db.add(row)
    db.commit()
    return SimpleNamespace(id=row.id)   # id lấy TRƯỚC khi việc dọn commit (đối tượng đã xóa thì không đọc lại được)


def test_nap_tep_don_dong_thong_tin_30_ngay_giu_canh_bao_loi_va_dong_ket_cuc(db):
    info_old = _ilog(db, LogLevel.INFO, 40)
    info_new = _ilog(db, LogLevel.INFO, 10)
    warn_old = _ilog(db, LogLevel.WARNING, 400)
    err_old = _ilog(db, LogLevel.ERROR, 400)
    customs_row = _ilog(db, LogLevel.INFO, 400, row_status=5, category="customs_row")   # Ghi đè — luật riêng
    _run(db, "import_info")
    assert _alive(db, ImportLog, [info_old, info_new, warn_old, err_old, customs_row]) == \
        {info_new.id, warn_old.id, err_old.id, customs_row.id}


def test_lo_cu_bao_dong_thong_tin_da_don():
    from app.modules.import_tool.service import pruned_note
    assert pruned_note(ImportBatch(created_at=NOW - timedelta(days=5)), now=NOW) == ""
    assert "đã được dọn" in pruned_note(ImportBatch(created_at=NOW - timedelta(days=45)), now=NOW)


# ---------- nhật ký thay đổi ----------
def test_bang_nhat_ky_may_khong_ghi_change_log_va_dong_cu_bi_xoa(db):
    assert {"tab_sync_log", "tab_email_log", "tab_import_log"} <= MACHINE_LOG_TABLES <= NO_LOG_TABLES
    machine = ChangeLog(table_name="tab_sync_log", row_id=1, op=2, field="status")
    real = ChangeLog(table_name="tab_purchase_order", row_id=1, op=2, field="status")
    db.add_all([machine, real])
    db.commit()
    machine, real = SimpleNamespace(id=machine.id), SimpleNamespace(id=real.id)
    _run(db, "change_machine")
    assert _alive(db, ChangeLog, [machine, real]) == {real.id}


# ---------- nhật ký request ----------
def test_get_30_ngay_nhung_khong_vuot_dau_thang():
    assert get_cutoff(datetime(2026, 11, 20)) == datetime(2026, 10, 21)
    assert get_cutoff(datetime(2026, 12, 31, 4)) == datetime(2026, 12, 1)      # tháng 12 chưa đóng gói thì không xóa


def test_viec_dem_khong_ghi_gi(db):
    _sync(db, SyncStatus.SKIPPED, days_ago=20, job="pull")
    _sync(db, SyncStatus.SKIPPED, days_ago=19, job="pull")
    before = db.query(SyncLog).count()
    out = machine_cleanup.run(db, now=NOW, dry_run=True)
    assert out["status"] == "dry_run" and db.query(SyncLog).count() == before
    assert "request_get" not in {r["key"] for r in out["rules"]}                 # GET có việc riêng


def test_script_dem_roi_don_va_goi_y_optimize(db, monkeypatch, capsys):
    import sys

    from scripts import don_nhat_ky_may as script

    class _Keep:
        def __getattr__(self, name):
            return getattr(db, name)

        def close(self):
            pass

    monkeypatch.setattr(script, "SessionLocal", _Keep)
    _sync(db, SyncStatus.SKIPPED, days_ago=400, job="pull")
    _sync(db, SyncStatus.SKIPPED, days_ago=399, job="pull")
    monkeypatch.setattr(sys, "argv", ["don_nhat_ky_may", "--dry-run"])
    assert script.main() == 0
    out = capsys.readouterr().out
    assert "sync_log" in out and "Chạy thử" in out and db.query(SyncLog).count() == 2
    monkeypatch.setattr(sys, "argv", ["don_nhat_ky_may", "--apply"])
    assert script.main() == 0
    out = capsys.readouterr().out
    assert "OPTIMIZE TABLE tab_sync_log;" in out and db.query(SyncLog).count() == 1
