"""duoc-CR-756 — cột "Kiêm nhiệm" của danh sách nhân sự `GET /api/employees` (trường `concurrent_roles`).

Chốt ba điều:
  1. Mỗi dòng trả các dòng kiêm nhiệm CÒN HIỆU LỰC (hết hạn / sắp tới không có; tắt công tắc tính phạm vi vẫn có),
     câu theo `describe_concurrent` (loại Phòng ban "Phòng X (Chức vụ)", loại Công ty "Công ty B (Chức vụ)"),
     xếp ổn định (loại, tên);
  2. nạp GOM: số truy vấn của cả trang KHÔNG tăng theo số nhân sự / số dòng kiêm nhiệm;
  3. chỉ để HIỂN THỊ: lọc theo công ty / phòng ban và tổng vẫn chỉ ra người làm chính ở đó, không cộng người kiêm nhiệm.

Đi qua HTTP thật (TestClient) nên phạm vi `apply_scope` và phong bì chạy đúng đường của giao diện.
"""
import pytest
from sqlalchemy import event

from app.core.auth import perm_cache_clear
from hdld_factory import client_as  # noqa: F401
from kiem_nhiem_factory import DAY, TODAY, add_employee, build_kn_world, kc, kn

URL = "/api/employees"


@pytest.fixture()
def w(world):
    return build_kn_world(world)


def _list(client, qs: str = "") -> dict:
    res = client.get(f"{URL}?page_size=100&{qs}")
    assert res.status_code == 200, res.text
    return res.json()["data"]


def _items_by_id(data: dict) -> dict[int, list[dict]]:
    return {row["id"]: row["concurrent_roles"] for row in data["items"]}


def _roles_by_id(data: dict) -> dict[int, list[str]]:
    """Chỉ phần câu (`text`) của mỗi mục — hình `{kind, text}` kiểm riêng ở bài đầu."""
    return {eid: [item["text"] for item in items] for eid, items in _items_by_id(data).items()}


@pytest.fixture()
def viewer(w, client_as):  # noqa: F811
    """a1 đọc nhân sự phạm vi tất cả."""
    w.grant("a1", "employee", "all")
    return client_as(w.actor("a1").user)


def test_dong_hieu_luc_hai_loai_ra_dung_cau_va_xep_loai_roi_ten(w, viewer):
    kc(w, "a2", "C", position_label="Cố vấn")
    kc(w, "a2", "B", position_label="Giám đốc")
    kn(w, "a2", "A.mua", position_label="Phó phòng")
    kn(w, "a2", "A.kt")
    roles = _roles_by_id(_list(viewer))[w.emp["a2"]]
    assert roles == [
        "Phòng Kế toán",                  # loại 1 trước, tên phòng tăng dần, không chức vụ thì không ngoặc
        "Phòng Thu mua (Phó phòng)",
        "Công ty B (Giám đốc)",           # loại 2 sau, tên công ty tăng dần
        "Công ty C (Cố vấn)",
    ]


def test_moi_muc_la_kind_va_text_kind_1_phong_ban_2_cong_ty(w, viewer):
    kn(w, "a2", "A.mua", position_label="Phó phòng")
    kc(w, "a2", "B")
    assert _items_by_id(_list(viewer))[w.emp["a2"]] == [
        {"kind": 1, "text": "Phòng Thu mua (Phó phòng)"},
        {"kind": 2, "text": "Công ty B"},
    ]


def test_het_han_va_sap_toi_khong_hien_tat_cong_tac_van_hien(w, viewer):
    kn(w, "a2", "A.kt", to_date=TODAY - DAY)                       # hết hạn hôm qua
    kc(w, "a2", "C", from_date=TODAY + DAY)                        # sắp tới ngày mai
    kn(w, "a2", "A.mua", counts_scope=False)                       # đang hiệu lực, tắt công tắc: VẪN hiện
    kc(w, "a2", "B", to_date=TODAY)                                # hết hạn đúng hôm nay: còn hiệu lực
    assert _roles_by_id(_list(viewer))[w.emp["a2"]] == ["Phòng Thu mua", "Công ty B"]


def test_nguoi_khong_kiem_nhiem_ra_danh_sach_rong_khong_thieu_khoa(w, viewer):
    kn(w, "a2", "A.mua")
    by_id = _roles_by_id(_list(viewer))
    assert by_id[w.emp["a3"]] == []
    assert by_id[w.emp["a2"]] == ["Phòng Thu mua"]


def test_loc_cong_ty_phong_ban_va_tong_khong_doi_khi_them_kiem_nhiem(w, viewer):
    """Người kiêm nhiệm công ty B / phòng A.mua KHÔNG lọt vào kết quả lọc B / A.mua; tổng giữ nguyên."""
    before_b = _list(viewer, f"company_id={w.co['B']}")
    before_mua = _list(viewer, f"department_id={w.dept['A.mua']}")
    before_all = _list(viewer)["total"]

    kc(w, "a2", "B")
    kn(w, "a2", "A.mua")

    after_b = _list(viewer, f"company_id={w.co['B']}")
    after_mua = _list(viewer, f"department_id={w.dept['A.mua']}")
    assert after_b["total"] == before_b["total"]
    assert after_mua["total"] == before_mua["total"]
    assert _list(viewer)["total"] == before_all
    assert w.emp["a2"] not in _roles_by_id(after_b)
    assert w.emp["a2"] not in _roles_by_id(after_mua)
    assert sorted(_roles_by_id(after_b)) == sorted(_roles_by_id(before_b))


def test_pham_vi_nguoi_xem_khong_mo_rong_nho_kiem_nhiem_cua_nguoi_khac(w, client_as):  # noqa: F811
    """Người xem bậc phòng của mình: dòng kiêm nhiệm của người ngoài phạm vi không kéo họ vào danh sách."""
    w.grant("a3", "employee", "own")
    kc(w, "a2", "B")
    data = _list(client_as(w.actor("a3").user))
    assert set(_roles_by_id(data)) == {w.emp["a3"]}


def _count_queries(w, fn) -> int:
    """Số truy vấn của lượt `fn()` thứ hai (lượt đầu nạp lại đối tượng hết hạn sau `commit`)."""
    perm_cache_clear()
    fn()
    perm_cache_clear()
    n: list[int] = []
    listener = lambda *a, **k: n.append(1)  # noqa: E731
    engine = w.db.get_bind()
    event.listen(engine, "before_cursor_execute", listener)
    try:
        fn()
    finally:
        event.remove(engine, "before_cursor_execute", listener)
    return len(n)


def test_dem_truy_van_khong_tang_theo_so_nhan_su_va_so_dong_kiem_nhiem(w, viewer):
    #  Mức nền: MỘT người có đủ hai loại dòng (để cả truy vấn tên phòng lẫn tên công ty đều chạy).
    kn(w, "a2", "A.mua", position_label="Phó phòng")
    kc(w, "a2", "B")
    base = _count_queries(w, lambda: _list(viewer))

    #  Thêm nhiều nhân sự, mỗi người nhiều dòng thuộc nhiều phòng / công ty khác nhau.
    for i in range(12):
        key = f"nv{i}"
        add_employee(w, key, "A", "A.kt")
    w.db.commit()
    for i in range(12):
        key = f"nv{i}"
        kn(w, key, "A.mua", position_label=f"Chức vụ {i}")
        kn(w, key, "SH")
        kc(w, key, "B", position_label="Giám đốc")
        kc(w, key, "C")
    many = _count_queries(w, lambda: _list(viewer))

    assert many == base, f"N+1: 1 người kiêm nhiệm tốn {base} truy vấn, 13 người tốn {many}"
    #  Đối chứng: dữ liệu thật sự ra (tránh bài rỗng vì danh sách trống).
    assert len(_roles_by_id(_list(viewer))[w.emp["nv11"]]) == 4
