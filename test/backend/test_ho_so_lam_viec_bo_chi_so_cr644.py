"""duoc-CR-644 — GET /api/usage-profiles/metrics (danh mục chỉ số + trạng thái đo của tuần mới nhất)."""
from sqlalchemy.orm.attributes import flag_modified

from app.core.report_keys import ReportKey
from app.core.subject_match import SUBJECT_ROLE
from app.modules.usage_profile.metric_catalog import DEFERRED_METRICS, METRIC_CATALOG
from app.modules.usage_profile.model import UserUsageSnapshot

from test_ho_so_lam_viec_api_cr641 import ROOT, admin, client_as, seeded  # noqa: F401  (fixture dùng chung)
from ho_so_lam_viec_factory import make_person
from lich_lam_viec_factory import count_queries

URL = f"{ROOT}/metrics"


def _set_values(db, key, values, reason=None):
    """Ghi đè giá trị `key` của từng snapshot theo danh sách (None = không đo, kèm mã lý do)."""
    snaps = db.query(UserUsageSnapshot).order_by(UserUsageSnapshot.id).all()
    for snap, v in zip(snaps, values):
        m = snap.metrics
        m["metrics"].pop(key, None)
        m["unmeasured"].pop(key, None)
        if v is None:
            m["unmeasured"][key] = reason
        else:
            m["metrics"][key] = {"v": v, "med": None, "p75": None, "trend": [v]}
        flag_modified(snap, "metrics")
    db.commit()


def test_khong_co_setting_read_403(db, client_as):
    user, _ = make_person(db, "NV644")
    assert client_as(user).get(URL).status_code == 403


def test_co_setting_read_chua_gan_khoa_14_403(db, cap_quyen, client_as):
    user, _ = make_person(db, "MGR644")
    cap_quyen(user.id, "setting", scope="all", read=True)
    assert client_as(user).get(URL).status_code == 403


def test_metrics_khong_bi_duong_user_id_nuot(db, admin, client_as):
    #  Nếu khai sau `/{user_id}` thì «metrics» vào tham số int → 422.
    r = client_as(admin).get(URL)
    assert r.status_code == 200, r.text
    assert r.json()["data"]["metrics"]


def test_chua_co_snapshot_tra_tuan_none_va_du_khoa(db, admin, client_as):
    data = client_as(admin).get(URL).json()["data"]
    assert data["week"] is None
    assert {m["key"] for m in data["metrics"]} == set(METRIC_CATALOG)
    assert all(m["measured_users"] == 0 and m["total_users"] == 0 and m["company_median"] is None
               and m["unmeasured_reason"] is None for m in data["metrics"])
    assert data["deferred"] == list(DEFERRED_METRICS)


def test_tong_hop_so_nguoi_do_duoc_va_trung_vi(db, admin, client_as):
    seeded(db, n=5, tag="M1")
    _set_values(db, "logins", [2, 4, 10, None, None], reason=3)
    _set_values(db, "imports", [None] * 5, reason=2)
    _set_values(db, "active_after_resign", [False, False, True, False, False])
    data = client_as(admin).get(URL).json()["data"]
    by = {m["key"]: m for m in data["metrics"]}
    assert data["week"] and by["logins"]["total_users"] == 5
    assert by["logins"]["measured_users"] == 3 and by["logins"]["company_median"] == 4
    assert by["logins"]["unmeasured_reason"] is None        # có người đo được → không báo lý do
    assert by["imports"]["measured_users"] == 0 and by["imports"]["company_median"] is None
    assert by["imports"]["unmeasured_reason"] == 2
    assert by["active_after_resign"]["measured_users"] == 5 and by["active_after_resign"]["company_median"] == 0
    meta = METRIC_CATALOG["logins"]
    assert (by["logins"]["unit"], by["logins"]["section"], by["logins"]["phase"], by["logins"]["direction"]) == \
        (meta.unit, meta.section, meta.phase, meta.direction)


def test_khong_co_chu_viet_mo_ta_trong_phan_hoi(db, admin, client_as):
    seeded(db, n=2, tag="M2")
    item = client_as(admin).get(URL).json()["data"]["metrics"][0]
    assert set(item) == {"key", "section", "unit", "phase", "direction", "measured_users", "total_users",
                         "company_median", "unmeasured_reason"}


def test_so_truy_van_hang_so_theo_so_nguoi(db, admin, client_as):
    c = client_as(admin)
    seeded(db, n=2, tag="Q1")
    _, few = count_queries(db, lambda: c.get(URL))
    seeded(db, n=12, tag="Q2")
    _, many = count_queries(db, lambda: c.get(URL))
    pick = lambda sql: [s for s in sql if "tab_user_usage_snapshot" in s]
    assert len(pick(few)) == len(pick(many)) == 2
