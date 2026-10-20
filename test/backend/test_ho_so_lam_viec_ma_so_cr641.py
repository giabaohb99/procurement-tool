"""duoc-CR-641 phase 01 — bộ mã, chuẩn hóa route, công tắc, ReportKey 14, nhãn đủ."""
import pytest

from app.core import app_settings, code_sets, status_catalog  # noqa: F401
from app.core.report_keys import REPORT_META, ReportKey
from app.core.usage_codes import (COHORT_KIND_LABELS, UI_EVENT_TYPE_LABELS, UI_FORM_LABELS,
                                  UNMEASURED_REASON_LABELS, USAGE_STYLE_LABELS, CohortKind, PeriodKind,
                                  UiEventType, UiForm, UnmeasuredReason, UsageStyle)
from app.modules.usage_profile.route_pattern import MAX_ROUTE_LEN, normalize_route


def test_gia_tri_so_co_dinh_khong_doi():
    assert [int(x) for x in UiEventType] == [1, 2, 3, 4, 5, 6, 7, 8]
    assert [int(x) for x in UiForm] == list(range(1, 14))
    assert [int(x) for x in UsageStyle] == list(range(1, 11))
    assert UsageStyle.BATCH_WORKER == 1 and UsageStyle.LOW_USAGE == 10
    assert [int(x) for x in CohortKind] == [1, 2, 3]
    assert [int(x) for x in UnmeasuredReason] == [1, 2, 3]
    assert int(PeriodKind.WEEK) == 1


@pytest.mark.parametrize("enum,labels", [(UiEventType, UI_EVENT_TYPE_LABELS), (UiForm, UI_FORM_LABELS),
                                         (UsageStyle, USAGE_STYLE_LABELS), (CohortKind, COHORT_KIND_LABELS),
                                         (UnmeasuredReason, UNMEASURED_REASON_LABELS)])
def test_nhan_tieng_viet_du(enum, labels):
    assert set(labels) == set(enum)
    assert all(isinstance(v, str) and v for v in labels.values())


def test_bo_ma_co_trong_so_dang_ky():
    names = set(status_catalog.all_sets())
    assert {"ui_event_type", "ui_form", "usage_style", "usage_cohort_kind", "usage_unmeasured_reason"} <= names
    assert [c.value for c in status_catalog.get("usage_style").codes][:3] == ["1", "2", "3"]


def test_report_key_14_co_nhan_va_nhom():
    assert ReportKey.USAGE_PROFILE == 14
    assert REPORT_META[ReportKey.USAGE_PROFILE] == ("Hồ sơ cách làm việc", "Quản trị")
    assert max(int(k) for k in ReportKey) >= 14   # CR-655 thêm 15; D1 sẽ thêm 16


def test_cong_tac_mac_dinh_bat_va_tat_duoc():
    assert app_settings.get("usage_tracking_enabled") is True
    app_settings._cache["usage_tracking_enabled"] = "false"
    assert app_settings.get("usage_tracking_enabled") is False
    app_settings._cache["usage_tracking_enabled"] = "true"
    assert app_settings.get("usage_tracking_enabled") is True


def test_cong_tac_co_trong_man_cau_hinh():
    from app.modules.setting.service import FIELDS
    field = next(f for f in FIELDS if f["key"] == "usage_tracking_enabled")
    assert field["type"] == "bool" and "hồ sơ cách làm việc" in field["label"]
    assert "thông báo nhân viên" in field["hint"]


@pytest.mark.parametrize("raw,expected", [
    ("/procurement/purchase-orders/129?q=abc#x", "/procurement/purchase-orders/:id"),
    ("/x/123/y/550e8400-e29b-41d4-a716-446655440000?q=nguyen", "/x/:id/y/:id"),
    ("/purchase-orders/PO2026001/edit", "/purchase-orders/:id/edit"),
    ("https://erp.dego.vn/hr/employees/7?tab=a", "/hr/employees/:id"),
    ("", "/"), (None, "/"), ("//a//b/", "/a/b"), ("/help/faq", "/help/faq"),
    ("/procurement/purchase-orders", "/procurement/purchase-orders"),
])
def test_normalize_route(raw, expected):
    assert normalize_route(raw) == expected


def test_normalize_route_cat_120():
    out = normalize_route("/" + "a" * 500)
    assert len(out) == MAX_ROUTE_LEN


def test_normalize_route_khong_giu_tu_khoa_tim_kiem():
    assert "nguyen" not in normalize_route("/search?q=nguyen#frag")
