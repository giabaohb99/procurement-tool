"""duoc-CR-641 phase 03 — dọn `tab_ui_event` 90 ngày theo lô và dọn số gom 3 năm."""
from datetime import date, datetime, timedelta

from app.modules.usage_profile.model import UiEvent, UsageDaily, UserUsageLabel, UserUsageSnapshot
from app.modules.usage_profile.tasks_cleanup import cleanup_summaries, cleanup_ui_events

from ho_so_lam_viec_factory import add_ui, make_person

NOW = datetime(2026, 4, 1, 12, 0)


def test_xoa_91_ngay_giu_10_ngay(db):
    user, _ = make_person(db, "C1")
    for i in range(3):
        add_ui(db, user, NOW - timedelta(days=91, hours=i), 1)
    for i in range(2):
        add_ui(db, user, NOW - timedelta(days=10, hours=i), 1)
    db.commit()
    res = cleanup_ui_events(db, now=NOW)
    assert res["deleted"] == 3
    assert db.query(UiEvent).count() == 2


def test_dry_run_chi_dem(db):
    user, _ = make_person(db, "C2")
    add_ui(db, user, NOW - timedelta(days=100), 1)
    db.commit()
    assert cleanup_ui_events(db, now=NOW, dry_run=True) == {
        "status": "dry_run", "cutoff": (NOW - timedelta(days=90)).isoformat(), "matched": 1}
    assert db.query(UiEvent).count() == 1


def test_lo_nho_van_xoa_het(db, monkeypatch):
    user, _ = make_person(db, "C3")
    for i in range(5):
        add_ui(db, user, NOW - timedelta(days=95, minutes=i), 1)
    db.commit()
    calls = []
    import app.modules.usage_profile.tasks_cleanup as mod
    real = mod.delete

    def spy(*a, **k):
        calls.append(1)
        return real(*a, **k)

    monkeypatch.setattr(mod, "delete", spy)
    res = cleanup_ui_events(db, now=NOW, batch_size=2)
    assert res["deleted"] == 5 and len(calls) == 3      # 2 + 2 + 1


def test_so_gom_snapshot_nhan_giu_3_nam(db):
    user, _ = make_person(db, "C4")
    today = date(2026, 4, 1)
    old, new = today - timedelta(days=3 * 365 + 5), today - timedelta(days=30)
    for d in (old, new):
        db.add(UsageDaily(user_id=user.id, day=d))
        snap = UserUsageSnapshot(user_id=user.id, period_start=d, metrics={})
        db.add(snap)
        db.flush()
        db.add(UserUsageLabel(snapshot_id=snap.id, user_id=user.id, period_start=d, label=1, score=0.5))
    db.commit()
    res = cleanup_summaries(db, today=today)
    assert res == {"daily": 1, "labels": 1, "snapshots": 1}
    assert [r.day for r in db.query(UsageDaily)] == [new]
    assert db.query(UserUsageSnapshot).count() == 1 and db.query(UserUsageLabel).count() == 1
