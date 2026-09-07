"""SỐ NGÀY TỰ TÍNH — ô buổi ở hai đầu khoảng nghỉ (vá 07/09/2026).

Ô buổi nói **MỐC**, không nói buổi: `from_session` là *nghỉ bắt đầu lúc nào*,
`to_session` là *nghỉ kết thúc lúc nào*. Bản cũ tra CHUNG một bảng
`{Cả ngày: 1, Sáng: .5, Chiều: .5}` cho cả hai đầu, tức đọc ô buổi thành *"buổi
nào của ngày đó được nghỉ"* — mâu thuẫn với chính luật *«chiều → sáng cùng ngày
là khoảng trống»* mà nó đang chặn, và sai ba nhóm ca:

| Ca | Bản cũ | Đúng |
|---|---|---|
| Sáng 05 → hết 07 | 2.5 | **3.0** — bắt đầu buổi sáng là nghỉ trọn ngày 05 |
| Cả ngày 05 → Chiều 07 | 2.5 | **3.0** — kết thúc buổi chiều là nghỉ trọn ngày 07 |
| Cả ngày → Sáng, CÙNG ngày | 1.0 | **0.5** — kết thúc lúc hết buổi sáng |

Hai ca đầu trừ HỤT phép (công ty chịu), ca thứ ba trừ THỪA (người lao động mất
nửa ngày). Cả ba đều im lặng: con số ra vẫn là một số hợp lý.

Bài ở đây quét **đủ 9 tổ hợp** của hai ô buổi, ở cả hai hình dạng (cùng ngày /
nhiều ngày). Quét đủ chứ không chọn vài ca đẹp — đúng ba ca sai kể trên là mấy
ca không ai nghĩ tới khi viết bài kiểm lần đầu.
"""
from datetime import date, timedelta
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.core.leave_codes import same_day_work_credit
from app.modules.document.type_metadata import suggested_days
from app.modules.employee.model import Employee
from app.modules.leave import request_service, workday_service
from app.modules.leave.catalog_model import LeaveType
from app.modules.leave.constants import (SESSION_AFTERNOON, SESSION_FULL,
                                         SESSION_MORNING)
from app.modules.leave.schema import LeaveRequestCreate

#  Thứ Hai 05/01/2026 — cả tuần này không có ngày lễ nào, nên con số ra chỉ phụ
#  thuộc vào ô buổi, không phụ thuộc bộ lịch.
MON = date(2026, 1, 5)
WED = date(2026, 1, 7)

F, M, A = SESSION_FULL, SESSION_MORNING, SESSION_AFTERNOON


def days(db, from_date, to_date, from_session=F, to_session=F):
    return workday_service.count_leave_days(db, from_date, to_date,
                                            from_session, to_session)


# ── 1. Nghỉ gọn trong MỘT ngày — đủ 9 tổ hợp ───────────────────────────────────

@pytest.mark.parametrize("from_session,to_session,expected", [
    (F, F, 1.0),   # trọn ngày
    (F, M, 0.5),   # ⚠️ bản cũ ra 1.0 — người lao động MẤT nửa ngày phép
    (F, A, 1.0),   # bắt đầu đầu ngày, kết thúc hết buổi chiều = trọn ngày
    (M, F, 1.0),   # ⚠️ bản cũ ra 0.5
    (M, M, 0.5),   # chỉ buổi sáng
    (M, A, 1.0),   # ⚠️ bản cũ ra 0.5 — sáng tới hết chiều là trọn ngày
    (A, F, 0.5),   # từ chiều tới hết ngày
    (A, A, 0.5),   # chỉ buổi chiều
])
def test_mot_ngay_du_chin_to_hop(db, from_session, to_session, expected):
    assert days(db, MON, MON, from_session, to_session) == expected


def test_chieu_den_sang_CUNG_NGAY_bi_chan_o_tang_tren(db):
    """Tổ hợp thứ chín: kết thúc TRƯỚC lúc bắt đầu — `check_date_range` chặn.

    Hàm đếm trả `0.0` chứ không trả số âm, để nếu có đường nào lọt qua chốt thì
    nó ra một con số vô hại chứ không phải một con số cộng ngược vào quỹ.
    """
    with pytest.raises(HTTPException) as e:
        request_service.check_date_range(MON, MON, A, M)
    assert "khoảng trống" in e.value.detail
    assert days(db, MON, MON, A, M) == 0.0


# ── 2. Nghỉ NHIỀU ngày — đủ 9 tổ hợp ───────────────────────────────────────────

@pytest.mark.parametrize("from_session,to_session,expected", [
    (F, F, 3.0),
    (F, M, 2.5),   # kết thúc hết buổi sáng ngày cuối
    (F, A, 3.0),   # ⚠️ bản cũ ra 2.5
    (M, F, 3.0),   # ⚠️ bản cũ ra 2.5
    (M, M, 2.5),   # ⚠️ bản cũ ra 2.0
    (M, A, 3.0),   # ⚠️ bản cũ ra 2.0
    (A, F, 2.5),
    (A, M, 2.0),
    (A, A, 2.5),   # ⚠️ bản cũ ra 2.0
])
def test_ba_ngay_du_chin_to_hop(db, from_session, to_session, expected):
    """T2 05/01 → T4 07/01, không lễ, không cuối tuần."""
    assert days(db, MON, WED, from_session, to_session) == expected


def test_ngay_dau_roi_vao_CHU_NHAT_thi_bo_qua_ca_o_buoi(db):
    """CN 04/01 → T3 06/01 khai từ buổi chiều: ngày đầu là Chủ nhật nên biến mất
    hẳn, hai ngày sau tính trọn — 2.0, không phải 2.5."""
    assert days(db, date(2026, 1, 4), date(2026, 1, 6), A, F) == 2.0


# ── 3. Giấy GNP phải ra CÙNG con số ────────────────────────────────────────────
#
#  Hai chỗ tính độc lập nhau (giấy khai tay không có bảng lịch làm việc), nhưng
#  quy ước ô buổi thì phải khớp — lệch là cùng một tờ đơn ra hai con số tùy
#  người nhập qua màn Nghỉ phép hay qua Văn thư.

_DOC_SESSION = {F: "full", M: "morning", A: "afternoon"}


@pytest.mark.parametrize("from_session,to_session", [
    (F, F), (F, M), (F, A), (M, F), (M, M), (M, A), (A, F), (A, A),
])
def test_giay_GNP_khop_don_nghi_phep_khi_khong_vuong_le(db, from_session, to_session):
    """Khoảng T2→T4 không có lễ lẫn cuối tuần, nên hai công thức phải trùng khít."""
    assert suggested_days(MON.isoformat(), WED.isoformat(),
                          _DOC_SESSION[from_session], _DOC_SESSION[to_session]) \
        == days(db, MON, WED, from_session, to_session)


def test_giay_GNP_mot_ngay_cung_khop(db):
    for from_session, to_session, expected in [(F, M, 0.5), (M, A, 1.0), (A, F, 0.5)]:
        assert suggested_days(MON.isoformat(), MON.isoformat(),
                              _DOC_SESSION[from_session], _DOC_SESSION[to_session]) == expected


def test_giay_khai_THEO_GIO_khong_goi_y_con_so_bia():
    """Số ngày của đơn theo giờ không suy ra được từ ô buổi — trả 0 để người
    khai giấy tay tự gõ, thà để trống còn hơn gợi ý bịa."""
    assert same_day_work_credit("hourly", "hourly") == 0.0
    assert suggested_days("2026-01-05", "2026-01-05", "hourly", "hourly") == 0.0


# ── 4. Khoảng ngày DÀI QUÁ TRẦN ────────────────────────────────────────────────

def test_khoang_dai_hon_tran_bi_CHAN_chu_khong_dem_cut(db):
    """⚠️ Vòng lặp ngày dừng ở `MAX_RANGE_DAYS` và trước đây **nuốt im lặng**:
    gõ nhầm năm 2036 (3651 ngày) ra đúng **343 ngày** — một con số trông hoàn
    toàn hợp lý, không có triệu chứng nào cho tới lúc đối chiếu sổ."""
    xa = MON + timedelta(days=3650)
    with pytest.raises(HTTPException) as e:
        request_service.check_date_range(MON, xa, F, F)
    assert "vượt trần" in e.value.detail

    #  Đúng bằng trần thì vẫn qua — thai sản 6 tháng phải nộp được.
    request_service.check_date_range(
        MON, MON + timedelta(days=workday_service.MAX_RANGE_DAYS - 1), F, F)


def test_lap_don_khoang_dai_bi_chan_ngay_o_duong_TAO(db):
    """Chặn phải nằm trên đường đi thật, không chỉ ở hàm rời."""
    lt = LeaveType(code="annual", name="Phép năm", counts_balance=True,
                   annual_quota_days=12.0)
    emp = Employee(code="NV001", full_name="Nguyễn Văn A", company_id=1,
                   department_id=7)
    db.add_all([lt, emp])
    db.flush()

    with pytest.raises(HTTPException) as e:
        request_service.create(db, LeaveRequestCreate(
            leave_type_id=lt.id, from_date=MON, to_date=MON + timedelta(days=3650),
            reason="Gõ nhầm năm"), SimpleNamespace(id=1, employee_id=emp.id))
    assert "vượt trần" in e.value.detail
