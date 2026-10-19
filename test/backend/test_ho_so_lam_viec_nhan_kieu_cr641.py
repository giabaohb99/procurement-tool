"""duoc-CR-641 phase 04 — luật nhận «kiểu làm việc»: mỗi luật 3 ca (trúng · sát dưới ngưỡng · thiếu dữ liệu tối thiểu)."""
import pytest

from app.core.usage_codes import UsageStyle
from app.modules.usage_profile import label_thresholds as T
from app.modules.usage_profile.label_rules import RULES, LabelContext, evaluate_labels

S = UsageStyle


def ctx(v=None, med=None, p75=None, counts=None, tenure=None):
    return LabelContext(v=v or {}, med=med or {}, p75=p75 or {}, counts=counts or {}, tenure_days=tenure)


def codes(c):
    return {l["code"] for l in evaluate_labels(c)}


CASES = {
    # (nhãn): (ca trúng, ca sát dưới ngưỡng, ca thiếu dữ liệu tối thiểu)
    S.BATCH_WORKER: (
        ctx({"month_end_create_share": 0.4}, counts={"docs_created": 10}),
        ctx({"month_end_create_share": 0.39}, counts={"docs_created": 10}),
        ctx({"month_end_create_share": 0.9}, counts={"docs_created": 9})),
    S.APPROVAL_BOTTLENECK: (
        ctx({"approval_wait_p50_h": 16}, {"approval_wait_p50_h": 8}, counts={"tasks_decided": 5}),
        ctx({"approval_wait_p50_h": 15.9}, {"approval_wait_p50_h": 8}, counts={"tasks_decided": 5}),
        ctx({"approval_wait_p50_h": 40}, {"approval_wait_p50_h": 8}, counts={"tasks_decided": 4})),
    S.EXCEL_PARALLEL: (
        ctx({"exports": 12, "export_per_list_view": 0.3}),
        ctx({"exports": 11, "export_per_list_view": 0.3}),                     # 11/4 = 2,75 < 3 / tuần
        ctx({"exports": 2, "export_per_list_view": 5})),                       # < 3 lượt xuất
    S.NEWCOMER_STUCK: (
        ctx({"http_403": 5, "help_views": 3, "workdays_net": 5}, tenure=30),
        ctx({"http_403": 5, "help_views": 2, "workdays_net": 5}, tenure=30),   # chỉ 1 tín hiệu
        ctx({"http_403": 5, "help_views": 3, "workdays_net": 4}, tenure=30)),  # < 5 ngày làm việc ròng
    S.POWER_USER: (
        ctx({"saved_prefs": 1, "http_422_per_100_writes": 1, "distinct_screens_30d": 20},
            {"http_422_per_100_writes": 2}, {"distinct_screens_30d": 20}, {"active_days": 10}),
        ctx({"saved_prefs": 1, "http_422_per_100_writes": 1, "distinct_screens_30d": 19},
            {"http_422_per_100_writes": 2}, {"distinct_screens_30d": 20}, {"active_days": 10}),
        ctx({"saved_prefs": 1, "http_422_per_100_writes": 1, "distinct_screens_30d": 20},
            {"http_422_per_100_writes": 2}, {"distinct_screens_30d": 20}, {"active_days": 9})),
    S.WANDERER: (
        ctx({"http_403": 6}, {"http_403": 2}, counts={"views": 50, "forbidden": 6}),
        ctx({"http_403": 4}, {"http_403": 1}, counts={"views": 50, "forbidden": 4}),
        ctx({"loop_share": 0.5}, counts={"views": 49, "forbidden": 4})),
    S.MOBILE_FIRST: (
        ctx({"mobile_write_share": 0.6}, counts={"api_writes": 20}),
        ctx({"mobile_write_share": 0.59}, counts={"api_writes": 20}),
        ctx({"mobile_write_share": 1.0}, counts={"api_writes": 19})),
    S.LOW_QUALITY_DOCS: (
        ctx({"edits_after_submit_share": 0.3}, counts={"submitted_chain": 5}),
        ctx({"edits_after_submit_share": 0.29}, counts={"submitted_chain": 5}),
        ctx({"edits_after_submit_share": 1.0}, counts={"submitted_chain": 4})),
    S.PROXY_DEPENDENT: (
        ctx({"proxy_share": 0.5}, counts={"proxy_docs": 5}),
        ctx({"proxy_share": 0.49}, counts={"proxy_docs": 5}),
        ctx({"proxy_share": 1.0}, counts={"proxy_docs": 4})),
    S.LOW_USAGE: (
        ctx({"active_ratio": 0.3, "workdays_net": 8}, {"active_ratio": 0.7}),
        ctx({"active_ratio": 0.4, "workdays_net": 8}, {"active_ratio": 0.7}),
        ctx({"active_ratio": 0.1, "workdays_net": 7}, {"active_ratio": 0.7})),
}


def test_moi_luat_deu_co_bo_ca_kiem():
    assert set(CASES) == set(RULES) == set(UsageStyle)


@pytest.mark.parametrize("style", list(CASES))
def test_ca_trung_gan_nhan_co_bang_chung(style):
    hit, _, _ = CASES[style]
    out = {l["code"]: l for l in evaluate_labels(hit)}
    assert int(style) in out
    assert out[int(style)]["evidence"] and 0 <= out[int(style)]["score"] <= 1


@pytest.mark.parametrize("style", list(CASES))
def test_sat_duoi_nguong_khong_gan_nhan(style):
    assert int(style) not in codes(CASES[style][1])


@pytest.mark.parametrize("style", list(CASES))
def test_thieu_du_lieu_toi_thieu_khong_gan_nhan(style):
    assert int(style) not in codes(CASES[style][2])


def test_nut_that_duyet_chap_nhan_pending_tu_10_khong_can_du_viec_xong():
    c = ctx({"pending_now": T.BOTTLENECK_PENDING})
    assert int(S.APPROVAL_BOTTLENECK) in codes(c)


def test_nut_that_can_ca_gap_doi_trung_vi_va_8_gio():
    base = {"approval_wait_p50_h": 7.9}
    assert int(S.APPROVAL_BOTTLENECK) not in codes(ctx(base, {"approval_wait_p50_h": 1}, counts={"tasks_decided": 9}))
    assert int(S.APPROVAL_BOTTLENECK) not in codes(ctx({"approval_wait_p50_h": 9}, {"approval_wait_p50_h": 5},
                                                       counts={"tasks_decided": 9}))     # 9 < 2×5


def test_ngay_duoc_bam_ho_tinh_la_co_lam_nen_khong_bi_gan_it_dung():
    c = ctx({"active_ratio": 0.3, "proxied_days_ratio": 0.2, "workdays_net": 10}, {"active_ratio": 0.9})
    assert int(S.LOW_USAGE) not in codes(c)


def test_ket_qua_sap_theo_score_giam_dan():
    c = ctx({"mobile_write_share": 1.0, "proxy_share": 0.55}, counts={"api_writes": 50, "proxy_docs": 9})
    scores = [l["score"] for l in evaluate_labels(c)]
    assert scores == sorted(scores, reverse=True) and len(scores) == 2
