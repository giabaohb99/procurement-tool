"""bao-CR-716 — ô Phạm vi vô hiệu với danh mục dùng chung (entity khai PUBLIC trong SCOPE_FIELDS).

Sự cố: vai trò Nhân sự được tick Xem nhà cung cấp với phạm vi Của mình nhưng vẫn thấy toàn bộ NCC, vì `supplier` là
danh mục dùng chung mọi pháp nhân — phạm vi không lọc, muốn giấu thì tắt quyền. Backend trả danh sách `public_entities`
trong `/api/roles/meta` để màn Phân quyền khóa ô Phạm vi của những dòng đó.
"""
from app.core.permissions import ENTITIES
from app.core.scoping import PUBLIC, SCOPE_FIELDS
from hdld_factory import client_as  # noqa: F401


def test_meta_tra_danh_sach_entity_cong_khai(world, client_as):  # noqa: F811
    world.grant("a1", "role", "all", actions=("read",))
    meta = client_as(world.actor("a1")).get("/api/roles/meta").json()["data"]
    public = meta["public_entities"]
    #  Đúng những entity khai PUBLIC, theo thứ tự của ENTITIES; không lẫn entity có cột lọc.
    assert public == [e for e in ENTITIES if SCOPE_FIELDS.get(e) is PUBLIC]
    assert {"supplier", "product", "warehouse"} <= set(public)
    assert not {"purchase_request", "employee", "contract"} & set(public)
    #  Mọi mục đều là entity thật của ma trận (gõ sai tên thì FE khóa nhầm dòng không tồn tại).
    assert set(public) <= {e["key"] for e in meta["entities"]}


def test_pham_vi_cua_minh_khong_loc_duoc_nha_cung_cap(world, client_as):  # noqa: F811
    """Chứng cớ của sự cố: phạm vi Của mình với NCC vẫn thấy toàn bộ — nên ô Phạm vi phải bị khóa trên màn."""
    from app.modules.supplier.model import Supplier

    db = world.db
    for i in range(3):
        db.add(Supplier(code=f"NCC716{i}", name=f"NCC dùng chung {i}", created_by=0))
    db.commit()
    world.grant("a1", "supplier", "own", actions=("read",))
    res = client_as(world.actor("a1")).get("/api/suppliers?page_size=100")
    assert res.status_code == 200
    codes = {r["code"] for r in res.json()["data"]["items"]}
    assert {"NCC7160", "NCC7161", "NCC7162"} <= codes
