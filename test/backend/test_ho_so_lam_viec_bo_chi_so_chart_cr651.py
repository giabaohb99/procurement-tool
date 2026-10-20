"""duoc-CR-651 — biểu đồ «Bộ chỉ số đánh giá»: `histogram` (tuần mới nhất) + `trend` (trung vị ≤ 8 tuần) trong /metrics."""
from datetime import date, timedelta

from app.core.usage_codes import PeriodKind
from app.modules.usage_profile.metric_chart_service import build_histogram, build_trend
from app.modules.usage_profile.model import UserUsageSnapshot

from test_ho_so_lam_viec_api_cr641 import ROOT, admin, client_as, seeded  # noqa: F401  (fixture dùng chung)
from ho_so_lam_viec_factory import make_person
from lich_lam_viec_factory import count_queries

URL = f"{ROOT}/metrics"


def _doc(key, v):
    return {"metrics": {key: {"v": v, "med": None, "p75": None, "trend": [v]}}, "unmeasured": {}}


def _latest(db):
    return db.query(UserUsageSnapshot.period_start).order_by(UserUsageSnapshot.period_start.desc()).first()[0]


def _uids(db, n):
    return [uid for (uid,) in db.query(UserUsageSnapshot.user_id).order_by(UserUsageSnapshot.id).limit(n).all()]


def _add_week(db, user_ids, week, key, values):
    """Thêm snapshot tuần `week` cho từng user id (giá trị None = không đo)."""
    for uid, v in zip(user_ids, values):
        doc = _doc(key, v) if v is not None else {"metrics": {}, "unmeasured": {key: 2}}
        db.add(UserUsageSnapshot(user_id=uid, period_kind=int(PeriodKind.WEEK), period_start=week, metrics=doc))
    db.commit()


def _by_key(client, admin_user):
    return {m["key"]: m for m in client(admin_user).get(URL).json()["data"]["metrics"]}


# ── cột phân phối theo đơn vị ───────────────────────────────────────────────

def test_rong_khi_khong_ai_do():
    for unit in ("ratio", "count", "flag", "minute_of_day", "ms"):
        assert build_histogram(unit, []) == []


def test_minute_of_day_24_cot_theo_gio():
    h = build_histogram("minute_of_day", [0, 59, 60, 8 * 60 + 30, 1439])
    assert len(h) == 24 and (h[0]["lo"], h[0]["hi"]) == (0, 60) and h[23]["hi"] == 1440
    assert [h[i]["count"] for i in (0, 1, 8, 23)] == [2, 1, 1, 1] and sum(c["count"] for c in h) == 5


def test_ratio_10_cot_va_100_phan_tram_vao_cot_cuoi():
    h = build_histogram("ratio", [0.0, 0.05, 0.1, 0.95, 1.0, 1.2])
    assert len(h) == 10 and (h[0]["lo"], h[0]["hi"], h[9]["hi"]) == (0, 0.1, 1.0)
    assert [c["count"] for c in h] == [2, 1, 0, 0, 0, 0, 0, 0, 0, 3]


def test_flag_hai_cot():
    h = build_histogram("flag", [0, 0, 1, 0])
    assert [(c["lo"], c["hi"], c["count"]) for c in h] == [(0, 1, 3), (1, 2, 1)]


def test_count_cot_dep_toi_p95_va_cot_tran():
    values = list(range(0, 20)) + [500]            # 1 ngoại lệ
    h = build_histogram("count", values)
    assert h[0]["lo"] == 0 and h[-1]["hi"] is None and h[-1]["count"] >= 1
    assert sum(c["count"] for c in h) == len(values)
    steps = {round(c["hi"] - c["lo"], 4) for c in h[:-1]}
    assert len(steps) == 1 and steps.pop() in (1, 2, 5)          # bước «đẹp», đếm thì ≥ 1
    assert len(h) <= 11


def test_count_toan_so_khong_mot_cot():
    assert build_histogram("count", [0, 0, 0]) == [{"lo": 0, "hi": 1, "count": 3}]


def test_min_h_ms_dung_cung_quy_tac():
    for unit in ("min", "h", "ms"):
        h = build_histogram(unit, [10, 20, 30, 40, 50, 60, 70, 80, 90, 100])
        assert sum(c["count"] for c in h) == 10 and h[0]["lo"] == 0


def test_trend_tang_dan_va_cat_8_tuan():
    weeks = [(f"2026-0{i}-01", [float(i)]) for i in range(1, 10)]
    out = build_trend(weeks)
    assert len(out) == 8 and out[0]["week"] == "2026-02-01" and out[-1] == {"week": "2026-09-01", "median": 9, "measured": 1}


# ── qua API ─────────────────────────────────────────────────────────────────

def test_null_khong_vao_phan_phối_va_moc_trung_vi_khop(db, admin, client_as):
    people, _ = seeded(db, n=5, tag="C1")
    snaps = db.query(UserUsageSnapshot).order_by(UserUsageSnapshot.id).all()
    for s, v in zip(snaps, [0.1, 0.3, 0.5, None, None]):
        m = dict(s.metrics)
        m["metrics"] = {k: x for k, x in m.get("metrics", {}).items() if k != "active_ratio"}
        m["unmeasured"] = {k: x for k, x in m.get("unmeasured", {}).items() if k != "active_ratio"}
        if v is None:
            m["unmeasured"]["active_ratio"] = 3
        else:
            m["metrics"]["active_ratio"] = {"v": v}
        s.metrics = m
    db.commit()
    item = _by_key(client_as, admin)["active_ratio"]
    assert sum(c["count"] for c in item["histogram"]) == item["measured_users"] == 3
    med = item["company_median"]
    hit = [c for c in item["histogram"] if c["lo"] <= med < c["hi"] or (med == 1 and c["hi"] == 1)]
    assert len(hit) == 1 and hit[0]["count"] >= 1


def test_trend_tang_dan_tuan_thieu_bi_bo_qua(db, admin, client_as):
    people, _ = seeded(db, n=3, tag="C2")
    users, latest = _uids(db, 3), _latest(db)
    w1, w3 = latest - timedelta(weeks=1), latest - timedelta(weeks=3)   # thiếu tuần -2
    _add_week(db, users, w1, "logins", [2, 4, 6])
    _add_week(db, users, w3, "logins", [10, None, None])
    tr = _by_key(client_as, admin)["logins"]["trend"]
    weeks = [t["week"] for t in tr]
    assert weeks == sorted(weeks) and weeks[-1] == latest.isoformat()
    assert (latest - timedelta(weeks=2)).isoformat() not in weeks
    assert {t["week"]: (t["median"], t["measured"]) for t in tr}[w1.isoformat()] == (4, 3)
    assert {t["week"]: (t["median"], t["measured"]) for t in tr}[w3.isoformat()] == (10, 1)


def test_trend_toi_da_8_diem(db, admin, client_as):
    people, _ = seeded(db, n=2, tag="C3")
    latest = _latest(db)
    for i in range(1, 11):
        _add_week(db, _uids(db, 2), latest - timedelta(weeks=i), "logins", [i, i])
    tr = _by_key(client_as, admin)["logins"]["trend"]
    assert len(tr) == 8 and [t["week"] for t in tr] == sorted(t["week"] for t in tr)


def test_chi_so_khong_ai_do_khong_co_bieu_do(db, admin, client_as):
    seeded(db, n=2, tag="C4")
    items = _by_key(client_as, admin)
    unmeasured = [m for m in items.values() if m["measured_users"] == 0]
    assert unmeasured and all(m["histogram"] == [] and m["trend"] == [] for m in unmeasured)


def test_chua_co_snapshot_khong_bieu_do(db, admin, client_as):
    data = client_as(admin).get(URL).json()["data"]
    assert all(m["histogram"] == [] and m["trend"] == [] for m in data["metrics"])


def test_so_truy_van_hang_so_theo_so_nguoi_va_so_tuan(db, admin, client_as):
    c = client_as(admin)
    people, _ = seeded(db, n=2, tag="C5")
    _, few = count_queries(db, lambda: c.get(URL))
    latest, ids = _latest(db), _uids(db, 2)
    for i in range(1, 7):
        _add_week(db, ids, latest - timedelta(weeks=i), "logins", [i, i])
    seeded(db, n=10, tag="C6")
    _, many = count_queries(db, lambda: c.get(URL))
    pick = lambda sql: [s for s in sql if "tab_user_usage_snapshot" in s]
    assert len(pick(few)) == len(pick(many)) == 2


def test_gac_quyen_khong_doi(db, client_as):
    user, _ = make_person(db, "NV651")
    assert client_as(user).get(URL).status_code == 403
