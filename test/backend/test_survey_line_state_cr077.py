"""CR-077 — một bộ nhãn tiến độ dòng DUY NHẤT cho cả hai màn.

Trước đây màn chi tiết Yêu cầu báo giá tự tính 5 nhãn ở FE, màn Tiến độ báo giá tính 9 nhãn ở
BE — cùng một dòng hiện hai chữ khác nhau. Nay `survey_request/line_state.py` là nguồn duy nhất,
backend nhét sẵn `progress_state` vào payload để FE khỏi tính lại.
"""
from app.modules.survey_progress import export as ex
from app.modules.survey_request import line_state as ls
from app.modules.survey_request.model import (SurveyRequest, SurveyRequestLine,
                                              SurveyRequestOption)


def _line(**kw) -> SurveyRequestLine:
    base = dict(survey_request_id=1, item_group="Bao bì", assignee="DEMONV",
                received_date="", result_due_date="", result_date="",
                line_status="", no_option=False, pr_code="")
    base.update(kw)
    return SurveyRequestLine(**base)


def test_hai_man_dung_chung_dung_mot_ham():
    """Màn Tiến độ báo giá phải DÙNG LẠI hàm gốc, không được tự chép một bản riêng —
    chép một bản là y như cũ: sửa một bên, bên kia lệch."""
    assert ex.progress_state is ls.progress_state
    assert ex.STATES == ls.STATES


def test_moi_nhan_deu_co_mau_hop_le():
    """Nhãn nào cũng phải có tông màu, và tông phải nằm trong bộ class badge có thật của FE."""
    assert set(ls.STATE_TONE) == set(ls.STATES)
    assert set(ls.STATE_TONE.values()) <= {"ok", "warn", "err", "gray", "info"}


def test_payload_chi_tiet_ycbg_co_san_nhan(db, seed):
    """`_out` phải kèm `progress_state`/`progress_tone` — đây là thứ FE hiển thị thẳng."""
    from app.modules.survey_request.controller import _out

    s = SurveyRequest(code="YCBG77", status="processing", company_id=1)
    db.add(s); db.flush()
    db.add(_line(survey_request_id=s.id, pr_code="PYC77", line_status="completed"))
    db.commit()

    out = _out(db, s)
    dong = out["lines"][0]
    assert dong["progress_state"] == ls.STATE_DONE      # hoàn thành thắng "đã tạo YCMH"
    assert dong["progress_tone"] == "ok"


def test_dong_da_tao_ycmh_khong_con_bi_goi_nham_la_hoan_thanh(db):
    """Lỗi cũ của FE: coi `is_completed` = Hoàn thành, trong khi cờ đó chỉ nghĩa "đã TỪNG tạo
    YCMH" (service.create_prs bật lên). Hậu quả: mọi dòng vừa tạo YCMH đều bị gắn nhãn Hoàn
    thành, dù người yêu cầu chưa hề chốt."""
    ln = _line(pr_code="PYC78", is_completed=True, line_status="")
    assert ls.progress_state(ln, True, 1) == ls.STATE_PR_CREATED


def test_nhan_cua_dong_chua_ai_nhan(db):
    assert ls.progress_state(_line(assignee=""), False, 0) == ls.STATE_NOT_RECEIVED
    assert ls.progress_state(_line(), False, 0) == ls.STATE_RECEIVED
