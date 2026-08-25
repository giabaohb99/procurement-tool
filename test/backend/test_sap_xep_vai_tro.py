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


def _vai_tro(db, code: str, sort_order: int = 0) -> Role:
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
    a, b, c = _vai_tro(db, "aaa"), _vai_tro(db, "bbb"), _vai_tro(db, "ccc")
    db.commit()

    ids = [r.id for r in service.list_roles_query(db).all()]
    assert ids == sorted(ids)
    assert ids.index(a.id) < ids.index(b.id) < ids.index(c.id)


def test_sap_xep_ghi_dung_day_nhan_duoc(db):
    a, b, c = _vai_tro(db, "aaa"), _vai_tro(db, "bbb"), _vai_tro(db, "ccc")
    db.commit()

    service.sap_xep_vai_tro(db, [c.id, a.id, b.id], user_id=1)

    assert [r.code for r in service.list_roles_query(db).all()] == ["ccc", "aaa", "bbb"]
    assert (c.sort_order, a.sort_order, b.sort_order) == (1, 2, 3)


def test_sap_xep_bat_dau_tu_1_de_khong_lan_voi_vai_tro_chua_xep(db):
    """Vai trò chưa xếp mang `sort_order = 0` nên phải đứng TRƯỚC nhóm đã xếp.

    Đánh số từ 0 thì dòng vừa kéo lên đầu lại hòa với đám chưa xếp, và `id` mới
    là thứ quyết định — tức là cú kéo không có tác dụng gì.
    """
    a, b = _vai_tro(db, "aaa"), _vai_tro(db, "bbb")
    db.commit()
    service.sap_xep_vai_tro(db, [b.id], user_id=1)

    assert b.sort_order == 1
    assert a.sort_order == 0
    assert [r.code for r in service.list_roles_query(db).all()] == ["aaa", "bbb"]


def test_id_la_thi_bo_qua_chu_khong_vut_ca_luot(db):
    """Ai đó vừa xóa một vai trò trong lúc mình đang kéo.

    Chặn cả lượt vì một dòng đã biến mất là vứt luôn công sắp xếp của người dùng.
    """
    a, b = _vai_tro(db, "aaa"), _vai_tro(db, "bbb")
    db.commit()

    service.sap_xep_vai_tro(db, [b.id, 999_999, a.id], user_id=1)

    assert b.sort_order == 1
    assert a.sort_order == 3      # giữ nguyên vị trí trong dãy, không dồn lên
    assert [r.code for r in service.list_roles_query(db).all()] == ["bbb", "aaa"]


def test_day_rong_khong_doi_gi(db):
    a = _vai_tro(db, "aaa", sort_order=5)
    db.commit()
    service.sap_xep_vai_tro(db, [], user_id=1)
    assert a.sort_order == 5


def test_doi_ten_khong_dung_toi_thu_tu(db):
    """Đổi tên và xếp thứ tự là hai việc rời nhau — sửa cái này không được đụng cái kia."""
    from app.modules.role.schema import RoleUpdate

    a = _vai_tro(db, "aaa", sort_order=7)
    db.commit()

    service.update_role(db, a.id, RoleUpdate(name="Tên mới"), user_id=1)

    assert a.name == "Tên mới"
    assert a.sort_order == 7


def test_vai_tro_moi_tao_khong_can_khai_sort_order(db):
    """Cột NOT NULL mà không có mặc định phía Python là mọi lệnh tạo vai trò đều đỏ."""
    obj = service.create_role(db, RoleCreate(code="moi", name="Mới"), user_id=1)
    assert obj.sort_order == 0


def test_route_order_khai_truoc_route_id():
    """`PUT /api/roles/order` phải đứng TRƯỚC mọi route `/{rid}`.

    Không thì "order" bị đọc thành id vai trò — đúng cái bẫy đã dính ở
    `/api/documents/export/xlsx`.
    """
    from app.modules.role.controller import router

    duong = [getattr(r, "path", "") for r in router.routes]
    assert "/api/roles/order" in duong
    assert duong.index("/api/roles/order") < duong.index("/api/roles/{rid}")


def test_khong_tim_thay_vai_tro_thi_404(db):
    with pytest.raises(HTTPException) as e:
        service.get_role(db, 999_999)
    assert e.value.status_code == 404
