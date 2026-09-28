"""Bản GOM Ở SQL của `service.report_rows_in_range` — dùng cho `/survey-report/summary`
(+ `/summary/export`) khi KHÔNG có tham số `q` (P06, review hiệu năng 28/09/2026).

Vì sao tách khỏi `q`: `_filter_report_rows` tìm `q` trên 10 cột trải cả header phiếu lẫn
dòng NCC/SP (mã YCBG, mã PYC, MST...) — dựng lại portable y hệt bằng SQL (chạy giống nhau
trên SQLite của bộ test và MySQL của prod) là việc lớn cho một ô tìm kiếm phụ, ít người
dùng cùng lúc với biểu đồ theo kỳ. Có `q` → controller lùi về `service.report_rows_in_range`
(đường CŨ, đã có sẵn/đã kiểm), tệp này chỉ lo phần KHÔNG có `q`.

Ý tưởng cốt lõi: `report_aggregate.aggregate()` chỉ CỘNG `MetricSpec.value_of(r)` qua mọi
hàng — không quan tâm một "hàng" đại diện 1 DÒNG hay N DÒNG đã gộp sẵn. Nên GROUP BY ở SQL
theo đúng bộ khóa mà `report_summary_service.build_spec()` dùng làm CHIỀU (nspt, item_group,
line_approve, kind) + NGÀY THÔ (để Python tự gom lại theo tuần/tháng, xem `report_period`),
rồi trả COUNT(*) làm "cnt" — `report_summary_service` đọc `r.get("cnt", 1)` nên một hàng gộp
N dòng cộng ra đúng N, mà một hàng CŨ (không có "cnt") vẫn cộng ra 1 như trước (tương thích
ngược, không cần tách spec riêng cho hai đường).

Thứ tự hàng trả về CỐ Ý xếp theo (kind: NCC trước SP, rồi MIN(id) dòng tăng dần) — đúng
thứ tự "lần đầu xuất hiện" mà `report_rows_in_range` (dòng NCC theo id rồi dòng SP theo id)
từng tạo ra. `report_compute.bucket_rows`/`merge_groups_by_key` sắp `groups`/`breakdowns`
theo hạng rồi DÙNG THỨ TỰ NÀY LÀM TIÊU CHÍ PHỤ khi hai nhóm hòa điểm (Python `sort` ổn
định) — gộp hàng mà không giữ đúng thứ tự này thì hai nhóm hòa điểm có thể tráo chỗ nhau
trong JSON trả về, phá vỡ yêu cầu "output y hệt" dù TỔNG số vẫn đúng.
"""
from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.orm import Session

from .model import Survey, SurveyProductLine, SurveySupplierLine

CHUA_DUYET = "Chờ duyệt"


def _survey_subquery(base_survey_query):
    """Phiếu trong phạm vi (đã `apply_scope`) — chỉ lấy 4 cột cần cho JOIN + chiều gom nhóm."""
    return base_survey_query.with_entities(
        Survey.id, Survey.nspt, Survey.item_group, Survey.received_date).subquery()


def _grouped_for_line_model(db: Session, survey_sub, line_model, d_from: str, d_to: str, *,
                            item_group: str | None, supplier: str | None, nspt: str | None) -> list:
    """GROUP BY (ngày hiệu lực, nspt, nhóm hàng, kết quả duyệt ĐÃ chuẩn hóa) cho MỘT bảng dòng —
    hai nhánh y hệt `service._lines_in_range` (ngày liên hệ trong kỳ / ngày liên hệ rỗng lùi về
    ngày nhận của phiếu), CỘNG bằng SQL GROUP BY thay vì nạp từng dòng vào Python.

    `min_id` chỉ dùng để SẮP THỨ TỰ đầu ra (xem docstring đầu tệp), không lọt vào hàng trả về.
    """
    approve_expr = func.coalesce(func.nullif(line_model.line_approve, ""), CHUA_DUYET)

    def _base(date_col):
        q = (db.query(date_col.label("date"), survey_sub.c.nspt.label("nspt"),
                     survey_sub.c.item_group.label("item_group"),
                     approve_expr.label("line_approve"),
                     func.count().label("cnt"), func.min(line_model.id).label("min_id"))
             .join(survey_sub, line_model.survey_id == survey_sub.c.id))
        if item_group:
            q = q.filter(survey_sub.c.item_group == item_group)
        if supplier:
            q = q.filter(func.lower(line_model.supplier_code).like(f"%{supplier.lower()}%"))
        if nspt:
            q = q.filter(func.lower(survey_sub.c.nspt).like(f"%{nspt.lower()}%"))
        return q

    with_date = (_base(line_model.contact_date)
                 .filter(line_model.contact_date >= d_from, line_model.contact_date <= d_to)
                 .group_by(line_model.contact_date, survey_sub.c.nspt, survey_sub.c.item_group,
                          approve_expr)
                 .all())
    fallback = (_base(survey_sub.c.received_date)
                .filter(line_model.contact_date == "", survey_sub.c.received_date >= d_from,
                       survey_sub.c.received_date <= d_to)
                .group_by(survey_sub.c.received_date, survey_sub.c.nspt, survey_sub.c.item_group,
                         approve_expr)
                .all())
    #  Hai nhánh RỜI NHAU (contact_date rỗng/khác rỗng) nên min_id không trùng giữa hai vế —
    #  gộp rồi sắp lại theo min_id là đủ tái tạo đúng thứ tự "lần đầu xuất hiện" của bản gốc.
    return sorted(with_date + fallback, key=lambda r: r.min_id)


def grouped_report_rows_in_range(db: Session, base_survey_query, d_from: str, d_to: str, *,
                                 kind: str | None = None, item_group: str | None = None,
                                 supplier: str | None = None, nspt: str | None = None) -> list[dict]:
    """Bản GOM Ở SQL của `service.report_rows_in_range` — dùng khi KHÔNG có `q` (xem đầu tệp).

    `kind`/`item_group`/`supplier`/`nspt` lọc Y HỆT `controller._filter_report_rows` (kind bỏ
    hẳn bảng dòng không khớp; item_group so khớp CHÍNH XÁC; supplier/nspt so khớp CHỨA, không
    phân biệt hoa/thường). Cột `q` KHÔNG lọc ở đây — controller tự chọn đường cũ khi có `q`.
    """
    survey_sub = _survey_subquery(base_survey_query)
    out: list[dict] = []
    if not kind or kind == "supplier":
        for r in _grouped_for_line_model(db, survey_sub, SurveySupplierLine, d_from, d_to,
                                         item_group=item_group, supplier=supplier, nspt=nspt):
            out.append({"kind": "supplier", "date": r.date, "nspt": r.nspt,
                       "item_group": r.item_group, "line_approve": r.line_approve, "cnt": r.cnt})
    if not kind or kind == "product":
        for r in _grouped_for_line_model(db, survey_sub, SurveyProductLine, d_from, d_to,
                                         item_group=item_group, supplier=supplier, nspt=nspt):
            out.append({"kind": "product", "date": r.date, "nspt": r.nspt,
                       "item_group": r.item_group, "line_approve": r.line_approve, "cnt": r.cnt})
    return out
