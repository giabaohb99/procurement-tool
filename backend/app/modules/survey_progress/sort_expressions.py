"""Biểu thức SẮP XẾP tại server cho các cột KHÔNG nằm thẳng trong DB của màn Tiến độ báo giá.

`controller._sort_map()` chỉ giữ cột thật (và cũng là whitelist của bộ lọc điều kiện). Các cột
dưới đây trước kia bị khóa sắp xếp vì "giá trị không nằm trong DB" — người dùng bấm tiêu đề
Trễ / Tiến độ dòng / Đơn giá báo… không có gì xảy ra. Nay dựng lại giá trị bằng SQL để xếp
được trên CẢ TẬP (đúng qua phân trang, và file Xuất Excel ra cùng thứ tự), không xếp riêng
trang đang xem.

Cố ý KHÔNG nhét vào `_sort_map()`: map đó mở luôn bộ lọc điều kiện, mà lọc theo các biểu
thức con này vừa chậm vừa không ai cần.
"""
from sqlalchemy import String, and_, case, cast, func, literal, select
from sqlalchemy.orm import Session

from app.core.code_rank_sql import build_value_rank_expression
from app.modules.company.model import Company
from app.modules.survey_request.export import LINE_STATUS_LABEL, STATUS_LABEL
from app.modules.survey_request.model import (SurveyRequest, SurveyRequestLine,
                                              SurveyRequestOption)
from app.modules.work.report_sql_date import date_diff_days

from .line_state_sql import state_rank_expression

#  Cột của phương án ĐÃ CHỐT (cùng nguồn với `survey_request.export.opt_cells`).
_CHOSEN_OPTION_COLUMNS = {
    #  Nhãn trống thì ô lùi về "Option <số>" (`opt_cells`) — xếp theo đúng chữ đang hiện.
    "opt_label": func.coalesce(
        func.nullif(SurveyRequestOption.display_label, ""),
        literal("Option ", String) + cast(SurveyRequestOption.public_id, String)),
    "opt_supplier_code": SurveyRequestOption.supplier_code,
    "opt_supplier_name": SurveyRequestOption.supplier_name,
    "opt_internal_code": SurveyRequestOption.snap_internal_code,
    "opt_product_code": SurveyRequestOption.system_product_code,
    "opt_product_name": SurveyRequestOption.snap_product_name,
    "opt_spec": SurveyRequestOption.snap_spec,
    "opt_origin": SurveyRequestOption.snap_origin,
    "opt_quote_unit": SurveyRequestOption.snap_quote_unit,
    "opt_moq": SurveyRequestOption.snap_moq,
    "opt_price": SurveyRequestOption.snap_price_by_volume,
    "opt_volume_range": SurveyRequestOption.snap_volume_range,
    "opt_vat": SurveyRequestOption.snap_vat,
    "opt_delivery_time": SurveyRequestOption.snap_delivery_time,
    "opt_delivery_place": SurveyRequestOption.snap_delivery_place,
    "opt_shipping_cost": SurveyRequestOption.snap_shipping_cost,
    "opt_sample_ready": SurveyRequestOption.snap_sample_ready,
    "opt_lab_result": SurveyRequestOption.snap_lab_result,
    "opt_note": SurveyRequestOption.nstm_note,
}


def _chosen_option_value(column):
    """Giá trị một cột của phương án đã chốt; dòng chưa chốt ra NULL.

    `_decorate` lấy phương án chốt cuối cùng nạp được nên ở đây cũng lấy id lớn nhất — dữ liệu
    đúng thì mỗi dòng chỉ có một phương án chốt, hai nơi khớp nhau.
    """
    O = SurveyRequestOption
    return (select(column)
            .where(O.survey_request_line_id == SurveyRequestLine.id, O.is_chosen.is_(True))
            .order_by(O.id.desc())
            .limit(1)
            .scalar_subquery())


def _days_late(db: Session, today: str):
    """Bản SQL của `export._days_late`: trễ > 0 ngày thì ra số, còn lại (không hạn, đúng
    hạn, trả sớm) ra NULL — khớp ô trống trên bảng."""
    L = SurveyRequestLine
    due = func.coalesce(L.result_due_date, "")
    result = func.coalesce(L.result_date, "")
    mark = case((result != "", result), else_=literal(today))
    late = date_diff_days(db, mark, due)
    return case((and_(due != "", late > 0), late), else_=None)


def _handling_days(db: Session):
    """Bản SQL của `export._handling_days`: thiếu một trong hai mốc thì NULL."""
    L = SurveyRequestLine
    received = func.coalesce(L.received_date, "")
    result = func.coalesce(L.result_date, "")
    return case((and_(received != "", result != ""), date_diff_days(db, result, received)),
                else_=None)


def get_computed_sort_expression(db: Session, key: str, today: str):
    """Biểu thức xếp cho cột `key`; None nếu cột này không xếp được (để controller bỏ qua).

    `today` là chuỗi 'YYYY-MM-DD' giờ VN — cột Trễ của dòng chưa trả kết quả đo tới hôm nay.
    Luật che cột NCC nằm ở controller, không ở đây.
    """
    if key in _CHOSEN_OPTION_COLUMNS:
        return _chosen_option_value(_CHOSEN_OPTION_COLUMNS[key])
    if key == "company":
        #  Xếp theo TÊN công ty như chữ đang hiện; `company_id` thì ra thứ tự số vô nghĩa.
        return (select(Company.name).where(Company.id == SurveyRequest.company_id)
                .limit(1).scalar_subquery())
    if key == "status":
        #  Cột lưu MÃ, ô bày nhãn: xếp theo dòng đời của phiếu (thứ tự khai ở `STATUS_LABEL`,
        #  Nháp -> Hoàn thành, rồi Bị trả lại / Đã từ chối), không theo chữ cái của mã.
        return build_value_rank_expression(SurveyRequest.status, list(STATUS_LABEL))
    if key == "line_status":
        return build_value_rank_expression(SurveyRequestLine.line_status, list(LINE_STATUS_LABEL))
    if key == "requirement_detail":
        return SurveyRequestLine.requirement_detail
    if key == "other_requirement":
        return SurveyRequestLine.other_requirement
    if key == "option_count":
        return (select(func.count(SurveyRequestOption.id))
                .where(SurveyRequestOption.survey_request_line_id == SurveyRequestLine.id)
                .scalar_subquery())
    if key == "progress_state":
        return state_rank_expression()
    if key == "days_late":
        return _days_late(db, today)
    if key == "handling_days":
        return _handling_days(db)
    return None
