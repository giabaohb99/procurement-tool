"""Cây thư mục văn bản mở lên 100 cấp + tối ưu ô TÌM THƯ MỤC (26/09/2026).

- `path` nới lên 760 ký tự; chốt `PATH_MAX_LENGTH` phải báo 400 TRƯỚC khi MySQL
  nổ 500. SQLite của bộ test KHÔNG ép độ dài `VARCHAR` nên chỉ kiểm được chốt ở
  tầng service — ghi xuống DB rồi khẳng định là xanh giả.
- `search_folders` nạp bảng thư mục đúng một lần: số truy vấn KHÔNG phình theo
  số kết quả hay độ sâu cây; kết quả xếp hạng trùng hẳn > bắt đầu bằng > chứa.
"""
import pytest
from fastapi import HTTPException
from sqlalchemy import event

from app.modules.doc_catalog import folder_move_service, folder_root_service, folder_service, folder_tree_service
from app.modules.doc_catalog.folder_constants import MAX_DEPTH, PATH_MAX_LENGTH
from app.modules.doc_catalog.folder_model import DocFolder
from app.modules.doc_catalog.folder_schema import FolderCreate
from scope_factory import build_world  # noqa: F401 — fixture `world` dùng nó


@pytest.fixture()
def roots(db, world):
    created = folder_root_service.ensure_company_roots(db)
    return {f.company_id: f for f in created}


def _mk(db, parent, name):
    return folder_service.create_folder(db, FolderCreate(parent_id=parent.id, name=name), 0)


def _count_queries(db, fn):
    count = {"n": 0}

    def _before(*_a, **_k):
        count["n"] += 1

    engine = db.get_bind()
    event.listen(engine, "before_cursor_execute", _before)
    try:
        result = fn()
    finally:
        event.remove(engine, "before_cursor_execute", _before)
    return count["n"], result


def test_tran_cay_la_100_cap_va_duong_dan_du_cho(db, world, roots):
    #  Từng là 7 — đừng hạ về mà không hỏi đại ca (26/09/2026).
    assert MAX_DEPTH == 100
    #  100 cấp × id 6 chữ số phải lọt cột `path`, không thì trần 100 là trần giả.
    assert 1 + MAX_DEPTH * len("999999/") <= PATH_MAX_LENGTH
    assert DocFolder.__table__.c.path.type.length == PATH_MAX_LENGTH


def test_tao_thu_muc_con_bao_400_khi_path_vuot_cot(db, world, roots):
    parent = _mk(db, roots[world.co["A"]], "Cha")
    #  Giả lập một nhánh đã dài sát trần (id lớn / cây rất sâu).
    parent.path = "/" + "9" * (PATH_MAX_LENGTH - 2) + "/"
    db.commit()
    before = db.query(DocFolder).count()
    with pytest.raises(HTTPException) as exc:
        _mk(db, parent, "Con")
    assert exc.value.status_code == 400
    #  Không để lại dòng mồ côi có `path` rỗng sau khi chặn.
    assert db.query(DocFolder).count() == before


def test_chuyen_thu_muc_bao_400_khi_path_nhanh_vuot_cot(db, world, roots):
    root = roots[world.co["A"]]
    target = _mk(db, root, "Đích")
    branch = _mk(db, root, "Nhánh")
    child = _mk(db, branch, "Con của nhánh")
    #  Đích dài `PATH_MAX_LENGTH - 2` → nhánh chuyển vào thêm hai đoạn "id/"
    #  (chính nó + con, mỗi đoạn ≥ 2 ký tự) là chắc chắn vượt.
    target.path = "/" + "8" * (PATH_MAX_LENGTH - 4) + "/"
    db.commit()
    with pytest.raises(HTTPException) as exc:
        folder_move_service.move_folder(db, branch, target.id, 0)
    assert exc.value.status_code == 400
    db.refresh(child)
    assert child.path.startswith(branch.path)


def test_tim_thu_muc_xep_trung_han_truoc_roi_bat_dau_roi_chua(db, world, roots):
    root = roots[world.co["A"]]
    contains = _mk(db, root, "Lưu trữ hợp đồng")
    prefix = _mk(db, root, "Hợp đồng mua bán")
    exact_deep = _mk(db, _mk(db, root, "Pháp chế"), "Hợp đồng")
    world.grant("a1", "document", scope="company", actions=("read",))
    results = folder_tree_service.search_folders(db, world.actor("a1").user, "hop dong")
    order = [r["id"] for r in results]
    #  Trùng hẳn tên thắng dù nằm sâu hơn — trước đây không sắp gì cả nên trần
    #  50 kết quả có thể cắt mất đúng thư mục người dùng đang tìm.
    assert order.index(exact_deep.id) < order.index(prefix.id) < order.index(contains.id)


def test_tim_thu_muc_so_truy_van_khong_phinh_theo_do_sau(db, world, roots):
    world.grant("a1", "document", scope="company", actions=("read",))
    user = world.actor("a1").user
    root = roots[world.co["A"]]

    node = root
    for i in range(3):
        node = _mk(db, node, f"Hồ sơ {i}")
    #  Làm ấm bộ nhớ đệm quyền (`get_perm_profile`) — không thì lần đo đầu
    #  đếm dôi mấy câu nạp vai trò, chẳng liên quan gì tới search.
    folder_tree_service.search_folders(db, user, "ho so")
    shallow, _ = _count_queries(db, lambda: folder_tree_service.search_folders(db, user, "ho so"))

    for i in range(3, 40):
        node = _mk(db, node, f"Hồ sơ {i}")
    #  Tạo thư mục là commit → `user` hết hạn, lần đọc sau nạp lại người dùng.
    #  Làm ấm lại để hai lần đo cùng điều kiện.
    folder_tree_service.search_folders(db, user, "ho so")
    deep, results = _count_queries(db, lambda: folder_tree_service.search_folders(db, user, "ho so"))

    assert len(results) == 40
    #  Bản cũ: 40 kết quả × tới 40 tổ tiên trong một câu `IN`, cộng hai lượt
    #  nạp lại. Nay nạp cây đúng một lần — số câu SQL đứng yên.
    assert deep == shallow


def test_tim_thu_muc_breadcrumb_du_chuoi_o_cay_sau(db, world, roots):
    world.grant("a1", "document", scope="company", actions=("read",))
    root = roots[world.co["A"]]
    node = root
    chain = []
    for i in range(45):
        node = _mk(db, node, f"Cấp {i}")
        chain.append(node.id)
    leaf = _mk(db, node, "Đích sâu")
    results = folder_tree_service.search_folders(db, world.actor("a1").user, "dich sau")
    assert [r["id"] for r in results] == [leaf.id]
    crumb_ids = [c["id"] for c in results[0]["breadcrumb"]]
    #  Đủ từ nhóm «Công ty» → pháp nhân → 45 cấp → chính nó, đúng thứ tự.
    assert crumb_ids[-47:] == [root.id, *chain, leaf.id]
    assert results[0]["path_display"].endswith("Cấp 44 / Đích sâu")
