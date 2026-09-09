"""bao-CR-313 — ba chốt bổ sung cho `_guard` của `/api/audit-logs` (chuyển từ `main`).

Bản vá 05/09/2026 đã gác được lối duyệt toàn hệ và lối widget (xem
`test_va_nhat_ky_thao_tac.py`). Ba khe còn lại, phát hiện khi đóng BM-001 trên prod:

1. quản trị hệ thống LỌC theo một entity kỹ thuật (`entity=auth` — đúng màn nhật ký
   đăng nhập cần dùng nhất) lại ăn 403, vì `auth` không phải khóa quyền nên
   `user_has_permission` luôn False: lọc khắt khe hơn không lọc;
2. entity không nằm trong `ENTITIES` bị chặn bằng luật NGẦM (tra quyền trả False)
   thay vì một câu lệnh đọc được;
3. FAQ của Help Center ghi dấu vết dưới `faq` nhưng gác bằng `help_article`, nên
   sau khi gác thì màn "Lịch sử" của Help Center mất sạch phần FAQ.
"""
import pytest
from fastapi import HTTPException

from app.core.audit import record

from test_va_nhat_ky_thao_tac import make_two_contracts, read_logs


def test_quan_tri_loc_theo_entity_ky_thuat_van_doc_duoc(world):
    """Chốt 1 — người đọc được TOÀN HỆ thì đọc được từng phần của nó."""
    quan_tri = world.grant("a2", "setting", scope="all", actions=("read",))
    record(world.db, 1, "auth", 0, "login_failed",
           "Đăng nhập thất bại: tài khoản 'x' (IP 1.2.3.4)")
    world.db.commit()

    dong = read_logs(world.db, quan_tri.user, entity="auth")
    assert [r["action_label"] for r in dong] == ["Đăng nhập thất bại"]


def test_entity_ngoai_bang_quyen_thi_403(world):
    """Chốt 2 — có quyền đọc hợp đồng không mở được nhật ký của thứ khác."""
    a1 = world.grant("a1", "contract", scope="all")
    record(world.db, 1, "auth", 0, "login", "Đăng nhập")
    world.db.commit()

    for entity in ("auth", "khong_ton_tai"):
        with pytest.raises(HTTPException) as loi:
            read_logs(world.db, a1.user, entity=entity)
        assert loi.value.status_code == 403

    #  Vế đối chứng: khóa thật thì vẫn qua.
    make_two_contracts(world)
    assert len(read_logs(world.db, a1.user, entity="contract")) == 2


def test_faq_di_bang_khoa_help_article(world):
    """Chốt 3 — bí danh entity -> khóa quyền."""
    a3 = world.actor("a3")
    record(world.db, 1, "faq", 7, "create", "Tạo câu hỏi thường gặp")
    world.db.commit()

    with pytest.raises(HTTPException) as loi:
        read_logs(world.db, a3.user, entity="faq", entity_id=7)
    assert loi.value.status_code == 403

    world.grant("a3", "help_article", scope="all", actions=("read",))
    assert [r["entity_id"] for r in read_logs(world.db, a3.user, entity="faq")] == [7]
