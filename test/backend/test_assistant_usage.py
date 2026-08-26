"""Guard chi phí Trợ lý AI (Phase 4) — hạn mức/ngày + tổng hợp token.

CHỈ kiểm phần vừa làm ở `assistant/usage.py`: đếm câu trong ngày, chặn khi chạm
trần, và câu tổng hợp cho admin. Không gọi provider (model thật).

Ghi chú múi giờ: `created_at` mặc định là `func.now()` (UTC trên SQLite) còn
`usage._start_of_today()` theo giờ máy (`datetime.now()`). Nên mọi test dưới đây
đặt `created_at` TƯỜNG MINH để mốc so sánh nhất quán, không phụ thuộc lệch giờ.
"""
from datetime import datetime, timedelta

import pytest

from app.core.config import settings
from app.modules.assistant import usage
from app.modules.assistant.model import AssistantMessage, MessageRole


def _msg(db, user_id, role, created_at, **tokens):
    """Thêm một lượt tin với thời điểm tạo tường minh."""
    db.add(AssistantMessage(
        conversation_id=1, role=role, content="x",
        created_by=user_id, updated_by=user_id, created_at=created_at, **tokens,
    ))


def test_count_today_chi_dem_cau_hoi_cua_chinh_minh_hom_nay(db, seed):
    """Đếm chỉ tin NGƯỜI DÙNG, của đúng user, từ đầu hôm nay — bỏ tin trợ lý,
    tin của người khác, và tin hôm qua."""
    now = datetime.now()
    hom_qua = now - timedelta(days=1)
    _msg(db, seed.u_req_id, MessageRole.USER, now)          # tính
    _msg(db, seed.u_req_id, MessageRole.USER, now)          # tính
    _msg(db, seed.u_req_id, MessageRole.ASSISTANT, now)     # trợ lý -> không tính
    _msg(db, seed.u_req_id, MessageRole.USER, hom_qua)      # hôm qua -> không tính
    _msg(db, seed.u_nstm_id, MessageRole.USER, now)         # người khác -> không tính
    db.commit()

    assert usage.count_today(db, seed.u_req_id) == 2
    assert usage.count_today(db, seed.u_nstm_id) == 1


def test_check_daily_limit_chan_khi_cham_tran(db, seed, monkeypatch):
    """Chạm trần thì ném QuotaExceeded; dưới trần thì im lặng cho qua."""
    from app.modules.user.model import User
    monkeypatch.setattr(settings, "AI_DAILY_MSG_LIMIT", 2)
    user = db.get(User, seed.u_req_id)

    now = datetime.now()
    _msg(db, seed.u_req_id, MessageRole.USER, now)
    db.commit()
    usage.check_daily_limit(db, user)   # mới 1/2 -> không ném

    _msg(db, seed.u_req_id, MessageRole.USER, now)
    db.commit()
    with pytest.raises(usage.QuotaExceeded):
        usage.check_daily_limit(db, user)   # 2/2 -> chặn


def test_check_daily_limit_0_la_khong_gioi_han(db, seed, monkeypatch):
    """Limit <= 0 = tắt hạn mức: có bao nhiêu câu cũng không ném."""
    from app.modules.user.model import User
    monkeypatch.setattr(settings, "AI_DAILY_MSG_LIMIT", 0)
    user = db.get(User, seed.u_req_id)
    now = datetime.now()
    for _ in range(5):
        _msg(db, seed.u_req_id, MessageRole.USER, now)
    db.commit()
    usage.check_daily_limit(db, user)   # không ném


def test_my_quota_tra_dung_con_lai(db, seed, monkeypatch):
    """my_quota: còn lại = trần - đã dùng; trần 0 -> remaining None (không giới hạn)."""
    from app.modules.user.model import User
    user = db.get(User, seed.u_req_id)
    now = datetime.now()
    _msg(db, seed.u_req_id, MessageRole.USER, now)
    _msg(db, seed.u_req_id, MessageRole.USER, now)
    db.commit()

    monkeypatch.setattr(settings, "AI_DAILY_MSG_LIMIT", 5)
    assert usage.my_quota(db, user) == {"limit": 5, "used": 2, "remaining": 3}

    monkeypatch.setattr(settings, "AI_DAILY_MSG_LIMIT", 0)
    assert usage.my_quota(db, user) == {"limit": 0, "used": 2, "remaining": None}


def test_summary_gop_token_va_so_cau_theo_nguoi(db, seed):
    """summary: số câu đếm tin người dùng; token cộng từ tin trợ lý; theo người có tên."""
    now = datetime.now()
    # u_req: 2 câu hỏi + 1 tin trợ lý 100 in / 40 out
    _msg(db, seed.u_req_id, MessageRole.USER, now)
    _msg(db, seed.u_req_id, MessageRole.USER, now)
    _msg(db, seed.u_req_id, MessageRole.ASSISTANT, now, input_tokens=100, output_tokens=40)
    # u_nstm: 1 câu hỏi + 1 tin trợ lý 10 in / 5 out
    _msg(db, seed.u_nstm_id, MessageRole.USER, now)
    _msg(db, seed.u_nstm_id, MessageRole.ASSISTANT, now, input_tokens=10, output_tokens=5)
    db.commit()

    out = usage.summary(db, days=7)
    assert out["totals"]["questions"] == 3
    assert out["totals"]["input_tokens"] == 110
    assert out["totals"]["output_tokens"] == 45

    by_user = {u["user_id"]: u for u in out["by_user"]}
    assert by_user[seed.u_req_id]["questions"] == 2
    assert by_user[seed.u_req_id]["input_tokens"] == 100
    assert by_user[seed.u_req_id]["name"] == "Người YC"   # rơi về tên nhân sự
    # Tốn token nhất lên đầu.
    assert out["by_user"][0]["user_id"] == seed.u_req_id
