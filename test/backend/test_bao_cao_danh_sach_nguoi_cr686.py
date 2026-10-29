"""duoc-CR-686 — helper «bấm số ra danh sách người» (`core/report_drilldown.py`) và
`valid_department_id`. Bài của từng báo cáo nằm ở tệp `test_bao_cao_*_cr686.py` riêng."""
from datetime import date
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.core.report_aggregate import OTHER_GROUP_KEY, DimensionSpec
from app.core.report_drilldown import ROWS_LIMIT, Col, filter_group, parse_rows_params, rows_response
from app.core.report_keys import REPORT_META, ReportKey
from app.modules.report.procurement_summary_rows import valid_department_id

ALLOWED = {"new_hires": "Vào mới", "departures": "Nghỉ việc"}
DEPT = DimensionSpec("department", "Phòng ban",
                     key_of=lambda r: [(r.dept, f"P{r.dept}")] if r.dept else [])


class TestThamSo:
    def test_metric_hop_le(self):
        assert parse_rows_params({"metric": "new_hires"}, ALLOWED) == ("new_hires", None, None)

    def test_metric_thieu_hoac_la_422(self):
        for params in ({}, {"metric": ""}, {"metric": "salary"}):
            with pytest.raises(HTTPException) as e:
                parse_rows_params(params, ALLOWED)
            assert e.value.status_code == 422

    def test_nhom_gop_422(self):
        with pytest.raises(HTTPException) as e:
            parse_rows_params({"metric": "new_hires", "group_by": "department",
                               "group_key": OTHER_GROUP_KEY}, ALLOWED)
        assert e.value.status_code == 422

    def test_group_by_none_bo_qua_group_key(self):
        assert parse_rows_params({"metric": "new_hires", "group_by": "none", "group_key": "3"},
                                 ALLOWED) == ("new_hires", None, None)

    def test_group_key_rong_la_nhom_chua_gan(self):
        assert parse_rows_params({"metric": "new_hires", "group_by": "department", "group_key": ""},
                                 ALLOWED) == ("new_hires", "department", "")


class TestLocNhom:
    rows = [SimpleNamespace(dept=1), SimpleNamespace(dept=2), SimpleNamespace(dept=0)]

    def test_khop_dung_khoa_cua_dim(self):
        assert [r.dept for r in filter_group(self.rows, DEPT, "2")] == [2]

    def test_nhom_chua_gan(self):
        assert [r.dept for r in filter_group(self.rows, DEPT, "")] == [0]

    def test_khong_loc_khi_khong_co_nhom(self):
        assert len(filter_group(self.rows, DEPT, None)) == 3
        assert len(filter_group(self.rows, None, "2")) == 3


class TestPhanHoi:
    def test_cat_tran_nhung_total_la_so_that(self):
        rows = [{"code": f"NV{i}", "hire_date": date(2026, 1, 1)} for i in range(ROWS_LIMIT + 7)]
        data = rows_response("new_hires", "Vào mới", [Col("code", "Mã NV"), Col("hire_date", "Vào", "date")], rows)
        assert data["total"] == ROWS_LIMIT + 7
        assert data["truncated"] is True
        assert len(data["rows"]) == ROWS_LIMIT
        assert data["rows"][0]["hire_date"] == "2026-01-01"
        assert data["columns"][1] == {"key": "hire_date", "label": "Vào", "kind": "date"}

    def test_kind_la_bi_chan(self):
        with pytest.raises(ValueError):
            Col("x", "X", "percent")


class TestPhongBan:
    def test_rong_va_all_la_khong_loc(self):
        assert valid_department_id(None) is None
        assert valid_department_id("") is None
        assert valid_department_id("all") is None

    def test_so_hop_le(self):
        assert valid_department_id(" 12 ") == 12

    def test_khong_phai_so_422(self):
        #  «²» là chữ số Unicode: `isdigit()` nhận nhưng `int()` ném lỗi — từng lộ 500 (review CR-686).
        for raw in ("abc", "²", "-1", "1.5"):
            with pytest.raises(HTTPException) as e:
                valid_department_id(raw)
            assert e.value.status_code == 422


def test_hai_khoa_moi_thuoc_nhom_nhan_su():
    assert REPORT_META[ReportKey.LABOR_CONTRACT] == ("Hợp đồng lao động", "Nhân sự")
    assert REPORT_META[ReportKey.HR_PROFILE_GAPS] == ("Hồ sơ & tài khoản còn thiếu", "Nhân sự")
    assert int(ReportKey.LABOR_CONTRACT) == 17 and int(ReportKey.HR_PROFILE_GAPS) == 18
