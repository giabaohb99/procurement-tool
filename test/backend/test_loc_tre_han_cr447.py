"""bao-CR-447 — ô "Trễ hạn" của màn Tiến độ báo giá phải có ĐỦ HAI VẾ.

Ô lọc trên giao diện có ba mục: *Tất cả* · *Trễ hạn* · *Đúng hạn*. Mục thứ ba gửi
xuống `late=0`, mà backend chỉ bắt `1/true/yes` — `late=0` rơi vào khoảng trống,
không khớp nhánh nào nên câu lệnh KHÔNG lọc gì cả: người dùng chọn "Đúng hạn" và
nhận về cả dòng trễ lẫn dòng đúng hạn, không chỗ nào báo.

Bốn chốt:

1. `late=1` ra đúng hai kiểu trễ — đã trả SAU hạn, và chưa trả mà hạn đã qua.
2. `late=0` ra phần BÙ của nó (trong số dòng có hạn), không phải "cả bảng".
3. Hai vế **không chồng nhau và không bỏ sót**: hợp của chúng = mọi dòng CÓ hạn.
4. Dòng **chưa có hạn trả** đứng ngoài cả hai vế — không biết nó sớm hay muộn so
   với cái gì; để lọt vào "Đúng hạn" là báo cáo nói dối theo hướng có lợi.
"""
from datetime import date
from types import SimpleNamespace

import pytest
from starlette.datastructures import QueryParams

from app.core.auth import get_perm_profile
from app.modules.survey_progress import controller as sp
from app.modules.survey_request.model import SurveyRequest, SurveyRequestLine
from app.modules.user.model import User

TODAY = date(2026, 9, 21)


def req(qs: str):
    """Request giả — `_build_query` chỉ đụng tới `.query_params`."""
    return SimpleNamespace(query_params=QueryParams(qs))


@pytest.fixture(autouse=True)
def fixed_today(monkeypatch):
    """"Hôm nay" phải cố định: vế "chưa trả mà quá hạn" so với ngày chạy máy."""
    monkeypatch.setattr(sp, "_today", lambda: TODAY)


@pytest.fixture
def viewer(db, cap_quyen):
    user = User(email="late446@test.local", employee_id=0, is_active=True)
    db.add(user)
    db.flush()
    cap_quyen(user.id, "survey_request", scope="all", read=True)
    db.commit()
    return user


@pytest.fixture
def six_lines(db):
    """Sáu dòng phủ đủ ranh giới quanh mốc 21/09/2026.

    Hai dòng trễ (trả muộn · chưa trả mà quá hạn), ba dòng đúng hạn (trả sớm ·
    trả ĐÚNG ngày hạn · chưa trả mà còn hạn) và một dòng CHƯA CÓ HẠN.
    """
    data = [
        # mã,          hạn trả,        ngày trả thật
        ("LATE-ANSWER", "2026-09-01", "2026-09-10"),   # trả sau hạn
        ("LATE-SILENT", "2026-09-01", ""),             # chưa trả, hạn đã qua
        ("OK-EARLY", "2026-09-30", "2026-09-15"),      # trả trước hạn
        ("OK-EXACT", "2026-09-10", "2026-09-10"),      # trả ĐÚNG ngày hạn
        ("OK-WAITING", "2026-09-30", ""),              # chưa trả, còn hạn
        ("NO-DUE", "", ""),                            # chưa khai hạn trả
    ]
    for code, due, result in data:
        s = SurveyRequest(code=code, status="processing", company_id=1)
        db.add(s)
        db.flush()
        db.add(SurveyRequestLine(survey_request_id=s.id, item_group="Bao bì",
                                 assignee="NV01", received_date="2026-08-01",
                                 result_due_date=due, result_date=result,
                                 line_status="", no_option=False, pr_code=""))
    db.commit()


def _codes(db, user, qs: str) -> set[str]:
    prof = get_perm_profile(db, user)
    q = sp._build_query(req(qs), db, user, prof, True)
    return {s.code for s, _ln in q.all()}


# ── 1. Vế TRỄ HẠN ────────────────────────────────────────────────────────────────
def test_late_covers_both_shapes_of_being_late(db, viewer, six_lines):
    assert _codes(db, viewer, "late=1") == {"LATE-ANSWER", "LATE-SILENT"}


def test_late_accepts_the_word_forms_too(db, viewer, six_lines):
    """Đường dẫn đã lưu và người gọi API thẳng hay gửi `true`/`yes`."""
    assert _codes(db, viewer, "late=true") == {"LATE-ANSWER", "LATE-SILENT"}
    assert _codes(db, viewer, "late=yes") == {"LATE-ANSWER", "LATE-SILENT"}


# ── 2. Vế ĐÚNG HẠN ───────────────────────────────────────────────────────────────
def test_on_time_is_the_complement_not_the_whole_table(db, viewer, six_lines):
    """Đây chính là lỗi được vá: trước đây `late=0` trả về cả sáu dòng."""
    assert _codes(db, viewer, "late=0") == {"OK-EARLY", "OK-EXACT", "OK-WAITING"}


def test_on_time_accepts_the_word_forms_too(db, viewer, six_lines):
    assert _codes(db, viewer, "late=false") == {"OK-EARLY", "OK-EXACT", "OK-WAITING"}
    assert _codes(db, viewer, "late=no") == {"OK-EARLY", "OK-EXACT", "OK-WAITING"}


def test_answering_exactly_on_the_due_date_counts_as_on_time(db, viewer, six_lines):
    """Ranh giới: `>` chứ không `>=`. Trả đúng ngày hạn mà bị tính trễ thì mọi
    thước đo hiệu suất của tổ khảo sát lệch đi một ngày."""
    assert "OK-EXACT" in _codes(db, viewer, "late=0")
    assert "OK-EXACT" not in _codes(db, viewer, "late=1")


def test_unanswered_but_still_within_the_deadline_is_on_time(db, viewer, six_lines):
    """Dòng chưa trả kết quả KHÔNG mặc nhiên là trễ — nó chỉ trễ khi hạn đã qua."""
    assert "OK-WAITING" in _codes(db, viewer, "late=0")


# ── 3. Hai vế khít nhau ──────────────────────────────────────────────────────────
def test_the_two_halves_do_not_overlap_and_leave_no_gap(db, viewer, six_lines):
    late = _codes(db, viewer, "late=1")
    on_time = _codes(db, viewer, "late=0")
    assert late & on_time == set()
    # Hợp của hai vế = mọi dòng CÓ hạn trả. Thiếu một dòng nghĩa là có thứ không
    # lọt vào vế nào, và nó sẽ biến mất khỏi cả hai báo cáo.
    assert late | on_time == {"LATE-ANSWER", "LATE-SILENT",
                              "OK-EARLY", "OK-EXACT", "OK-WAITING"}


def test_a_line_without_a_deadline_belongs_to_neither_half(db, viewer, six_lines):
    assert "NO-DUE" not in _codes(db, viewer, "late=1")
    assert "NO-DUE" not in _codes(db, viewer, "late=0")
    # Nhưng vẫn phải còn nguyên khi KHÔNG lọc — nó là việc thật, chỉ là chưa khai hạn.
    assert "NO-DUE" in _codes(db, viewer, "")


# ── 4. Giá trị rác ───────────────────────────────────────────────────────────────
def test_a_junk_value_filters_nothing_instead_of_emptying_the_table(db, viewer, six_lines):
    """Sửa tay URL không được làm vỡ trang — nết chung của mọi ô lọc ở đây."""
    everything = {"LATE-ANSWER", "LATE-SILENT", "OK-EARLY", "OK-EXACT",
                  "OK-WAITING", "NO-DUE"}
    assert _codes(db, viewer, "late=khong-biet") == everything
    assert _codes(db, viewer, "late=") == everything
