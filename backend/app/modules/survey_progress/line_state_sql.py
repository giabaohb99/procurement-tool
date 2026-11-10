"""Bản SQL của cột TÍNH "Tiến độ dòng" (`survey_request.line_state.progress_state`).

Cột này không nằm trong DB nên muốn LỌC hay SẮP XẾP tại server thì phải dịch luật suy nhãn
thành điều kiện SQL. Hai việc dùng chung một bản dịch ở đây, kẻo lọc theo một luật mà xếp theo
luật khác.
"""
from sqlalchemy import and_, case, exists, func, select

from app.modules.survey_request.model import (LS_COMPLETED, LS_RESURVEY, SurveyRequestLine,
                                              SurveyRequestOption)

from . import export as ex


def state_condition(state: str):
    """Dịch nhãn cột TÍNH "Tiến độ dòng" thành điều kiện SQL để lọc được tại server.

    Phải bám đúng thứ tự ưu tiên của `export.progress_state`: mỗi nhãn = "khớp mốc của mình
    VÀ không khớp mốc nào xa hơn". Bỏ vế sau là lọc ra thừa — ví dụ chọn "Đang khảo sát" sẽ
    kéo về cả những dòng đã chốt xong từ lâu, vì chúng cũng có phương án.

    Trả None với nhãn lạ (người dùng sửa URL) — coi như không lọc, hơn là trả bảng rỗng khó hiểu.
    """
    L = SurveyRequestLine
    chosen = exists(select(SurveyRequestOption.id)
                    .where(SurveyRequestOption.survey_request_line_id == L.id,
                           SurveyRequestOption.is_chosen.is_(True)))
    any_opt = exists(select(SurveyRequestOption.id)
                     .where(SurveyRequestOption.survey_request_line_id == L.id))
    line_st = func.coalesce(L.line_status, "")
    no_pr = func.coalesce(L.pr_code, "") == ""
    answered = func.coalesce(L.result_date, "") != ""

    # CR-077: HOÀN THÀNH là mốc xa nhất, đứng TRÊN "Đã tạo YCMH".
    if state == ex.STATE_DONE:
        return line_st == LS_COMPLETED
    not_done = line_st != LS_COMPLETED
    if state == ex.STATE_PR_CREATED:
        return and_(not_done, func.coalesce(L.pr_code, "") != "")
    r1 = and_(not_done, no_pr)                                # chưa hoàn thành, chưa tạo YCMH
    if state == ex.STATE_RESURVEY:
        return and_(r1, line_st == LS_RESURVEY)
    r2 = and_(r1, line_st != LS_RESURVEY)
    if state == ex.STATE_CHOSEN:
        return and_(r2, chosen)
    r3 = and_(r2, ~chosen)
    if state == ex.STATE_NO_OPTION:
        return and_(r3, L.no_option.is_(True))
    r4 = and_(r3, L.no_option.is_(False))
    if state == ex.STATE_ANSWERED:
        return and_(r4, answered)
    r5 = and_(r4, ~answered)
    if state == ex.STATE_SURVEYING:
        return and_(r5, any_opt)
    r6 = and_(r5, ~any_opt)
    if state == ex.STATE_RECEIVED:
        return and_(r6, func.coalesce(L.assignee, "") != "")
    if state == ex.STATE_NOT_RECEIVED:
        return and_(r6, func.coalesce(L.assignee, "") == "")
    return None


def state_rank_expression():
    """Số thứ tự DÒNG ĐỜI (0 = Chưa tiếp nhận … 8 = Hoàn thành) của nhãn tiến độ, để xếp cột.

    Xếp theo dòng đời chứ không theo chữ cái: "Chốt rỗng" đứng trước "Chưa tiếp nhận" theo
    bảng chữ cái là thứ tự vô nghĩa với người theo dõi tiến độ. Các điều kiện của
    `state_condition` loại trừ nhau nên mỗi dòng rơi đúng một nhánh.
    """
    whens = [(state_condition(st), rank) for rank, st in enumerate(ex.STATES)]
    return case(*whens, else_=len(ex.STATES))
