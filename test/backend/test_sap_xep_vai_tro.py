"""CR-172 — thứ tự hiện của vai trò trên màn Phân quyền (kéo thả).

Kiểm ba thứ dễ vỡ nhất:
- `list_roles_query` xếp theo `sort_order` rồi mới tới `id`;
- `sap_xep_vai_tro` ghi đúng dãy nhận được, và không gục vì một id lạ;
- route `/order` không bị route `/{rid}` nuốt mất.
"""
import pytest
from fastapi import HTTPException

from app.modules.role import service
from app.modules.role.model import Role
from app.modules.role.schema import RoleCreate


def _role(db, code: str, sort_order: int = 0) -> Role:
    obj = Role(code=code, name=f"Vai trò {code}", description="",
               sort_order=sort_order, created_by=1, updated_by=1)
    db.add(obj)
    db.flush()
    return obj


def test_chua_xep_thi_giu_nguyen_thu_tu_theo_id(db):
    """Mọi vai trò cùng `sort_order = 0` (mặc định) thì `id` quyết định.

    Nếu không có khóa phụ này, MySQL trả về thứ tự tùy hứng và danh sách nhảy
    lung tung giữa hai lần nạp — người dùng mất dấu vai trò vừa bấm.
    """
    a, b, c = _role(db, "aaa"), _role(db, "bbb"), _role(db, "ccc")
    db.commit()

    ids = [r.id for r in service.list_roles_query(db).all()]
    assert ids == sorted(ids)
    assert ids.index(a.id) < ids.index(b.id) < ids.index(c.id)


def test_sap_xep_ghi_dung_day_nhan_duoc(db):
    a, b, c = _role(db, "aaa"), _role(db, "bbb"), _role(db, "ccc")
    db.commit()

    service.reorder_roles(db, [c.id, a.id, b.id], user_id=1)

    assert [r.code for r in service.list_roles_query(db).all()] == ["ccc", "aaa", "bbb"]
    assert (c.sort_order, a.sort_order, b.sort_order) == (1, 2, 3)


def test_sap_xep_bat_dau_tu_1_de_khong_lan_voi_vai_tro_chua_xep(db):
    """Vai trò chưa xếp mang `sort_order = 0` nên phải đứng TRƯỚC nhóm đã xếp.

    Đánh số từ 0 thì dòng vừa kéo lên đầu lại hòa với đám chưa xếp, và `id` mới
    là thứ quyết định — tức là cú kéo không có tác dụng gì.
    """
    a, b = _role(db, "aaa"), _role(db, "bbb")
    db.commit()
    service.reorder_roles(db, [b.id], user_id=1)

    assert b.sort_order == 1
    assert a.sort_order == 0
    assert [r.code for r in service.list_roles_query(db).all()] == ["aaa", "bbb"]


def test_id_la_thi_bo_qua_chu_khong_vut_ca_luot(db):
    """Ai đó vừa xóa một vai trò trong lúc mình đang kéo.

    Chặn cả lượt vì một dòng đã biến mất là vứt luôn công sắp xếp của người dùng.
    """
    a, b = _role(db, "aaa"), _role(db, "bbb")
    db.commit()

    service.reorder_roles(db, [b.id, 999_999, a.id], user_id=1)

    assert b.sort_order == 1
    assert a.sort_order == 3      # giữ nguyên vị trí trong dãy, không dồn lên
    assert [r.code for r in service.list_roles_query(db).all()] == ["bbb", "aaa"]


def test_day_rong_khong_doi_gi(db):
    a = _role(db, "aaa", sort_order=5)
    db.commit()
    service.reorder_roles(db, [], user_id=1)
    assert a.sort_order == 5


def test_doi_ten_khong_dung_toi_thu_tu(db):
    """Đổi tên và xếp thứ tự là hai việc rời nhau — sửa cái này không được đụng cái kia."""
    from app.modules.role.schema import RoleUpdate

    a = _role(db, "aaa", sort_order=7)
    db.commit()

    service.update_role(db, a.id, RoleUpdate(name="Tên mới"), user_id=1)

    assert a.name == "Tên mới"
    assert a.sort_order == 7


def test_vai_tro_moi_tao_khong_can_khai_sort_order(db):
    """Người gọi KHÔNG phải tự tính `sort_order` — service tự đặt.

    Cột NOT NULL mà không ai điền là mọi lệnh tạo vai trò đều đỏ. Vị trí cụ thể
    (cuối danh sách) do hai bài `test_vai_tro_moi_*` bên dưới giữ.
    """
    obj = service.create_role(db, RoleCreate(code="moi", name="Mới"), user_id=1)
    assert obj.sort_order is not None and obj.sort_order >= 1


def test_route_order_khai_truoc_route_id():
    """`PUT /api/roles/order` phải đứng TRƯỚC mọi route `/{rid}`.

    Không thì "order" bị đọc thành id vai trò — đúng cái bẫy đã dính ở
    `/api/documents/export/xlsx`.
    """
    from app.modules.role.controller import router

    route = [getattr(r, "path", "") for r in router.routes]
    assert "/api/roles/order" in route
    assert route.index("/api/roles/order") < route.index("/api/roles/{rid}")


def test_khong_tim_thay_vai_tro_thi_404(db):
    with pytest.raises(HTTPException) as e:
        service.get_role(db, 999_999)
    assert e.value.status_code == 404


def test_vai_tro_moi_xuong_CUOI_danh_sach_da_xep(db):
    """Ép ra được 25/08/2026 khi ép thử CR-172.

    Người quản trị xếp tay 17 vai trò xong thêm một vai trò mới; nó mang
    `sort_order = 0` mặc định nên **nhảy lên đứng đầu**, trên cả «Quản trị hệ
    thống» — phá đúng cái thứ tự họ vừa dựng.
    """
    a, b = _role(db, "aaa"), _role(db, "bbb")
    db.commit()
    service.reorder_roles(db, [a.id, b.id], user_id=1)

    new = service.create_role(db, RoleCreate(code="moi", name="Mới"), user_id=1)

    assert new.sort_order == 3
    assert [r.code for r in service.list_roles_query(db).all()][-1] == "moi"


def test_danh_sach_chua_ai_xep_thi_vai_tro_moi_van_nam_cuoi(db):
    """Mọi vai trò cũ đều `sort_order = 0`; vai trò mới nhận 1 nên vẫn đứng cuối."""
    _role(db, "aaa"), _role(db, "bbb")
    db.commit()

    new = service.create_role(db, RoleCreate(code="moi", name="Mới"), user_id=1)

    assert new.sort_order == 1
    assert [r.code for r in service.list_roles_query(db).all()][-1] == "moi"


# ── Ràng buộc tên / mã ─────────────────────────────────────────────────────────
#  Cả ba ca dưới đây LỌT trước 25/08/2026. Trước CR-172 không ai đổi tên vai trò
#  từ giao diện được nên chưa ai chạm tới; nay có nút bút chì nên nó thành cửa
#  thật, phải đóng.
@pytest.mark.parametrize("name", ["", "   ", "\t\n"])
def test_ten_rong_bi_chan(name):
    """Vai trò không tên = một dòng TRẮNG trong cột trái màn Phân quyền."""
    from pydantic import ValidationError

    from app.modules.role.schema import RoleUpdate
    with pytest.raises(ValidationError):
        RoleUpdate(name=name)


def test_ten_dai_hon_cot_bi_chan_o_tang_schema():
    """Cột `name` chỉ 100 ký tự. Không chặn ở schema thì vỡ dưới MySQL và người
    dùng nhận **500 internal_error** thay vì một câu nói rõ sai chỗ nào."""
    from pydantic import ValidationError

    from app.modules.role.schema import RoleCreate as RC, RoleUpdate
    with pytest.raises(ValidationError):
        RoleUpdate(name="X" * 101)
    with pytest.raises(ValidationError):
        RC(code="ma", name="X" * 101)
    with pytest.raises(ValidationError):
        RC(code="M" * 51, name="Tên")


def test_ten_bi_cat_khoang_trang_thua():
    from app.modules.role.schema import RoleUpdate
    assert RoleUpdate(name="  Văn thư  ").name == "Văn thư"


def test_ten_dung_tran_100_ky_tu_van_qua():
    from app.modules.role.schema import RoleUpdate
    assert len(RoleUpdate(name="X" * 100).name) == 100
