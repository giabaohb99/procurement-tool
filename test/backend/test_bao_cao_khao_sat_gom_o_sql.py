"""P06 (review hiệu năng 28/09/2026) — `survey.report_grouped_fetch`: bản GOM Ở SQL của
`service.report_rows_in_range`, dùng cho `/survey-report/summary` (+ `/export`) khi KHÔNG có
tham số `q`. Canh:

  - Kết quả CỘNG DỒN (qua `report_aggregate.aggregate`) khớp Y HỆT đường CŨ (nạp từng dòng) —
    kể cả khi `line_approve` rỗng (chuẩn hóa "Chờ duyệt") và khi dòng dùng NHÁNH LÙI (ngày
    liên hệ rỗng, lấy ngày nhận của phiếu);
  - Bốn bộ lọc trang (kind/item_group/supplier/nspt) lọc ĐÚNG như `_filter_report_rows`;
  - Phạm vi (`apply_scope`) vẫn chặn: chỉ dòng của phiếu nằm trong `base_survey_query`;
  - Controller lùi về đường CŨ khi có tham số `q` (không kiểm ở đây — xem
    `TestCheDoKepConLaiSurveyProgressVaSurveyReport` của `test_bao_cao_thu_mua_theo_ky.py`
    cho luồng hai chế độ qua route thật).
"""
import itertools

from app.core.report_aggregate import aggregate
from app.modules.survey import service
from app.modules.survey.controller import _filter_report_rows
from app.modules.survey.model import Survey, SurveyProductLine, SurveySupplierLine
from app.modules.survey.report_grouped_fetch import grouped_report_rows_in_range
from app.modules.survey.report_summary_service import build_spec

SPEC = build_spec()
_seq = itertools.count(1)


def _survey(db, **kw) -> Survey:
    #  `code` unique -> tự sinh mã tăng dần, khỏi va nhau khi một test dựng NHIỀU phiếu.
    base = dict(code=f"KS{next(_seq):04d}", survey_type="combined", status="approved",
               item_group="", nspt="")
    base.update(kw)
    s = Survey(**base)
    db.add(s)
    db.flush()
    return s


def _base_query(db, survey_ids=None):
    q = db.query(Survey)
    if survey_ids is not None:
        q = q.filter(Survey.id.in_(survey_ids))
    return q


def _legacy_rows(db, base, d_from, d_to, **filters):
    ranged = service.report_rows_in_range(db, base, d_from, d_to)
    return _filter_report_rows(ranged, **filters)


def _assert_same_aggregate(db, base, d_from, d_to, group_by, **filters):
    """So khớp TOÀN BỘ `aggregate()` (totals/trend/groups/breakdowns) giữa đường CŨ (nạp từng
    dòng) và đường MỚI (gom ở SQL) — đây là phép kiểm mạnh nhất: sai một chỗ nhỏ (chuẩn hóa
    "Chờ duyệt", nhánh lùi ngày, thứ tự hòa điểm...) đều lộ ra thành hai dict khác nhau."""
    from datetime import date as _date

    legacy = _legacy_rows(db, base, d_from, d_to, **filters)
    grouped = grouped_report_rows_in_range(db, base, d_from, d_to,
                                           kind=filters.get("kind"), item_group=filters.get("item_group"),
                                           supplier=filters.get("supplier"), nspt=filters.get("nspt"))
    d0, d1 = _date.fromisoformat(d_from), _date.fromisoformat(d_to)
    got_legacy = aggregate(legacy, SPEC, d0, d1, "day", group_by)
    got_grouped = aggregate(grouped, SPEC, d0, d1, "day", group_by)
    assert got_grouped == got_legacy
    return got_grouped


class TestGomONhomKhopDuongCu:
    def test_tong_hop_khop_bao_gom_line_approve_rong_va_nhanh_lui_ngay(self, db):
        """1 phiếu, 3 dòng: một dòng NCC đã duyệt, một dòng NCC line_approve RỖNG (-> "Chờ
        duyệt"), một dòng SP KHÔNG có ngày liên hệ (-> lùi về `received_date` của phiếu)."""
        s = _survey(db, item_group="Nhãn", nspt="NSPT A", received_date="2026-09-01")
        db.add_all([
            SurveySupplierLine(survey_id=s.id, supplier_code="NCC001", contact_date="2026-09-05",
                              line_approve="Đã duyệt"),
            SurveySupplierLine(survey_id=s.id, supplier_code="NCC002", contact_date="2026-09-06",
                              line_approve=""),
            SurveyProductLine(survey_id=s.id, supplier_code="NCC003", contact_date="",
                              line_approve="Không duyệt"),
        ])
        db.commit()
        base = _base_query(db)

        for group_by in (None, "line_approve", "nspt", "item_group", "kind"):
            got = _assert_same_aggregate(db, base, "2026-09-01", "2026-09-10", group_by)
            assert got["totals"]["lines"] == 3
            assert got["totals"]["lines_supplier"] == 2 and got["totals"]["lines_product"] == 1
            assert got["totals"]["approved"] == 1

        # Dòng rỗng phải gom vào ĐÚNG nhãn "Chờ duyệt", không tự thành một nhóm rỗng riêng.
        by_approve = _assert_same_aggregate(db, base, "2026-09-01", "2026-09-10", "line_approve")
        keys = {g["key"] for g in by_approve["groups"]}
        assert "Chờ duyệt" in keys and "" not in keys

    def test_nhieu_phieu_nhieu_to_hop_chieu_khop_ca_breakdown(self, db):
        """2 phiếu khác nhóm hàng/NSPT — kiểm breakdown Top (không chỉ `groups`)."""
        s1 = _survey(db, item_group="Nhãn", nspt="NSPT A", received_date="2026-09-01")
        s2 = _survey(db, item_group="Thùng", nspt="NSPT B", received_date="2026-09-02")
        db.add_all([
            SurveyProductLine(survey_id=s1.id, supplier_code="NCC001", contact_date="2026-09-03",
                              line_approve="Đã duyệt"),
            SurveyProductLine(survey_id=s1.id, supplier_code="NCC001", contact_date="2026-09-04",
                              line_approve="Đã duyệt"),
            SurveyProductLine(survey_id=s2.id, supplier_code="NCC002", contact_date="2026-09-05",
                              line_approve="Không duyệt"),
        ])
        db.commit()
        base = _base_query(db)

        got = _assert_same_aggregate(db, base, "2026-09-01", "2026-09-10", "item_group")
        by_group = {g["key"]: g["values"]["lines"] for g in got["groups"]}
        assert by_group == {"Nhãn": 2, "Thùng": 1}
        by_bd = {b["key"]: b["value"] for b in got["breakdowns"]["item_group"]}
        assert by_bd == {"Nhãn": 2, "Thùng": 1}


class TestBonBoLocTrang:
    def _setup(self, db):
        s1 = _survey(db, item_group="Nhãn", nspt="Phu Trach A", received_date="2026-09-01")
        s2 = _survey(db, item_group="Thùng", nspt="Phu Trach B", received_date="2026-09-01")
        db.add_all([
            SurveySupplierLine(survey_id=s1.id, supplier_code="NCC-XYZ-001", contact_date="2026-09-05",
                              line_approve="Đã duyệt"),
            SurveyProductLine(survey_id=s2.id, supplier_code="NCC-ABC-002", contact_date="2026-09-06",
                              line_approve="Đã duyệt"),
        ])
        db.commit()
        return _base_query(db)

    def test_loc_kind_bo_han_bang_khong_khop(self, db):
        base = self._setup(db)
        rows = grouped_report_rows_in_range(db, base, "2026-09-01", "2026-09-10", kind="supplier")
        assert rows and all(r["kind"] == "supplier" for r in rows)
        assert sum(r["cnt"] for r in rows) == 1

    def test_loc_item_group_so_khop_chinh_xac(self, db):
        base = self._setup(db)
        rows = grouped_report_rows_in_range(db, base, "2026-09-01", "2026-09-10", item_group="Thùng")
        assert sum(r["cnt"] for r in rows) == 1 and rows[0]["item_group"] == "Thùng"

    def test_loc_supplier_chua_khong_phan_biet_hoa_thuong(self, db):
        base = self._setup(db)
        rows = grouped_report_rows_in_range(db, base, "2026-09-01", "2026-09-10", supplier="xyz")
        assert sum(r["cnt"] for r in rows) == 1
        rows_upper = grouped_report_rows_in_range(db, base, "2026-09-01", "2026-09-10", supplier="XYZ")
        assert sum(r["cnt"] for r in rows_upper) == 1

    def test_loc_nspt_chua_khong_phan_biet_hoa_thuong(self, db):
        base = self._setup(db)
        rows = grouped_report_rows_in_range(db, base, "2026-09-01", "2026-09-10", nspt="trach a")
        assert sum(r["cnt"] for r in rows) == 1
        assert rows[0]["nspt"] == "Phu Trach A"


class TestPhamViKhongLotHang:
    def test_pham_vi_chi_lay_phieu_trong_base_query(self, db):
        s_trong = _survey(db, code="KS-TRONG", received_date="2026-09-01")
        s_ngoai = _survey(db, code="KS-NGOAI", received_date="2026-09-01")
        db.add_all([
            SurveySupplierLine(survey_id=s_trong.id, supplier_code="A", contact_date="2026-09-02"),
            SurveySupplierLine(survey_id=s_ngoai.id, supplier_code="B", contact_date="2026-09-02"),
        ])
        db.commit()
        base = _base_query(db, survey_ids=[s_trong.id])   # mô phỏng apply_scope đã chặn s_ngoai

        rows = grouped_report_rows_in_range(db, base, "2026-09-01", "2026-09-10")
        assert sum(r["cnt"] for r in rows) == 1

    def test_khong_co_phieu_trong_pham_vi_thi_tra_rong(self, db):
        base = _base_query(db, survey_ids=[])
        assert grouped_report_rows_in_range(db, base, "2026-09-01", "2026-09-10") == []
