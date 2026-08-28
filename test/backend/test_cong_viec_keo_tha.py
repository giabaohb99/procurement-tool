"""Phân hệ Công việc — KÉO THẢ kanban: `move_task` + số thứ tự trong cột.

Ba lỗi tệp này canh, đều là lỗi âm thầm (API trả 200, thẻ nằm sai chỗ):

1. **Task mới mang `sort_order = 0`** nên cả cột trùng số. Kiểu chèn "lấy số ở
   giữa hai thẻ" hết khe ngay từ thẻ thứ hai và mọi cú thả vào GIỮA cột đều rơi
   xuống đáy. Nay task mới nối vào cuối bằng `_next_sort_order`.
2. **Không đánh số lại cột đích**, để client tự tính. Bảng đang lọc thì client
   chỉ thấy một phần cột, tự tính là ném hết thẻ đang ẩn lên đầu.
3. **Mốc lạ / mốc là chính nó** — người khác vừa kéo thẻ mốc đi nơi khác thì cú
   thả của mình không được phép quăng thẻ về đầu cột.

Bản sao phía giao diện: `frontend-v2/src/modules/work/utils/kanban-drop.test.ts`.
"""
import pytest
from fastapi import HTTPException

from app.modules.work import list_config_service as cfg
from app.modules.work import list_service, schema, task_service
from app.modules.work.membership_service import Actor
from app.modules.work.task_model import WorkTask

COMPANY = 1
STEP = task_service.SORT_STEP


@pytest.fixture()
def owner(db):
    return Actor(user_id=1, employee_id=11, company_id=COMPANY)


@pytest.fixture()
def work_list(db, owner):
    return list_service.create_list(db, owner, schema.ListCreate(name="Thu mua"))


@pytest.fixture()
def sections(db, owner, work_list):
    """Ba cột mặc định: «Cần làm» · «Đang làm» · «Hoàn thành»."""
    return [c["id"] for c in cfg.get_sections(db, owner, work_list["id"])]


def _create_task(db, owner, list_id, title, section_id=None):
    return task_service.create_task(db, owner, schema.TaskCreate(
        list_id=list_id, title=title, section_id=section_id))


def _order_of(db, owner, list_id, section_id):
    """Id các thẻ của một cột, đúng thứ tự bảng kanban vẽ ra."""
    board = task_service.board(db, owner, list_id)
    return [t["id"] for t in board["tasks"] if t["section_id"] == section_id]


def _sort_orders(db, ids):
    return [db.get(WorkTask, i).sort_order for i in ids]


# ── Số thứ tự lúc TẠO ──────────────────────────────────────────────────────────

def test_viec_moi_noi_vao_cuoi_cot_chu_khong_deu_mang_so_khong(db, owner, work_list, sections):
    """Cả cột cùng `sort_order = 0` là không còn khe để chèn vào giữa — mọi cú
    kéo thả vào giữa cột sẽ rơi xuống đáy."""
    ids = [_create_task(db, owner, work_list["id"], f"V{i}", sections[0])["id"] for i in range(5)]
    orders = _sort_orders(db, ids)
    assert orders == sorted(orders) and len(set(orders)) == 5
    assert 0 not in orders
    assert _order_of(db, owner, work_list["id"], sections[0]) == ids


def test_moi_cot_dem_so_rieng_khong_an_theo_cot_ben_canh(db, owner, work_list, sections):
    a = _create_task(db, owner, work_list["id"], "A", sections[0])
    b = _create_task(db, owner, work_list["id"], "B", sections[1])
    assert db.get(WorkTask, a["id"]).sort_order == db.get(WorkTask, b["id"]).sort_order


def test_viec_con_xep_theo_cha_chu_khong_theo_cot(db, owner, work_list, sections):
    parent = _create_task(db, owner, work_list["id"], "Cha", sections[0])
    child = [task_service.create_task(db, owner, schema.TaskCreate(
        list_id=work_list["id"], title=f"Con {i}", parent_id=parent["id"]))["id"] for i in range(3)]
    orders = _sort_orders(db, child)
    assert orders == [STEP, 2 * STEP, 3 * STEP]


# ── Kéo trong CÙNG một cột ─────────────────────────────────────────────────────

def test_keo_len_va_keo_xuong_trong_mot_cot(db, owner, work_list, sections):
    ids = [_create_task(db, owner, work_list["id"], f"V{i}", sections[0])["id"] for i in range(4)]
    a, b, c, d = ids

    task_service.move_task(db, owner, a, sections[0], d)          # A xuống ngay trước D
    assert _order_of(db, owner, work_list["id"], sections[0]) == [b, c, a, d]

    task_service.move_task(db, owner, d, sections[0], b)          # D lên đầu-nhì
    assert _order_of(db, owner, work_list["id"], sections[0]) == [d, b, c, a]

    task_service.move_task(db, owner, d, sections[0], None)       # D xuống cuối
    assert _order_of(db, owner, work_list["id"], sections[0]) == [b, c, a, d]


def test_chen_vao_giua_cot_ma_ca_cot_trung_so_khong(db, owner, work_list, sections):
    """Đúng cảnh dữ liệu cũ: mọi thẻ `sort_order = 0`. Kiểu "lấy số ở giữa" cho
    ra `0 + 1`, lớn hơn tất cả, nên thẻ rơi xuống ĐÁY thay vì vào giữa."""
    ids = [_create_task(db, owner, work_list["id"], f"V{i}", sections[0])["id"] for i in range(4)]
    for i in ids:
        db.get(WorkTask, i).sort_order = 0
    db.commit()
    a, b, c, d = ids

    task_service.move_task(db, owner, d, sections[0], b)
    assert _order_of(db, owner, work_list["id"], sections[0]) == [a, d, b, c]
    assert _sort_orders(db, [a, d, b, c]) == [STEP, 2 * STEP, 3 * STEP, 4 * STEP]


def test_moi_cu_tha_deu_danh_so_lai_nen_khong_bao_gio_het_khe(db, owner, work_list, sections):
    """Chèn 30 lần liên tiếp vào GIỮA cột. Kiểu chia đôi khoảng sẽ cạn khe sau
    ~10 lần rồi im lặng xếp sai."""
    ids = [_create_task(db, owner, work_list["id"], f"V{i}", sections[0])["id"] for i in range(6)]
    for _ in range(30):
        current = _order_of(db, owner, work_list["id"], sections[0])
        task_service.move_task(db, owner, current[-1], sections[0], current[2])
        after = _order_of(db, owner, work_list["id"], sections[0])
        assert after[2] == current[-1]
        assert sorted(after) == sorted(ids)
        orders = _sort_orders(db, after)
        assert orders == sorted(orders) and len(set(orders)) == len(ids)


def test_tha_dung_cho_cu_thi_thu_tu_khong_doi(db, owner, work_list, sections):
    ids = [_create_task(db, owner, work_list["id"], f"V{i}", sections[0])["id"] for i in range(3)]
    task_service.move_task(db, owner, ids[1], sections[0], ids[2])
    assert _order_of(db, owner, work_list["id"], sections[0]) == ids


def test_moc_la_chinh_no_thi_dung_yen_chu_khong_roi_xuong_day(db, owner, work_list, sections):
    """Client cũ có thể bắn `before = chính nó` khi child trỏ rê ngang thẻ gốc."""
    ids = [_create_task(db, owner, work_list["id"], f"V{i}", sections[0])["id"] for i in range(4)]
    for i in ids:
        task_service.move_task(db, owner, i, sections[0], i)
        assert _order_of(db, owner, work_list["id"], sections[0]) == ids


def test_moc_khong_con_trong_cot_thi_xuong_cuoi(db, owner, work_list, sections):
    """Người khác vừa kéo thẻ mốc sang cột khác. Thà lệch một chỗ còn hơn ném
    thẻ về đầu cột."""
    a = _create_task(db, owner, work_list["id"], "A", sections[0])["id"]
    b = _create_task(db, owner, work_list["id"], "B", sections[0])["id"]
    elsewhere = _create_task(db, owner, work_list["id"], "Ngoài", sections[1])["id"]

    task_service.move_task(db, owner, a, sections[0], elsewhere)
    assert _order_of(db, owner, work_list["id"], sections[0]) == [b, a]

    task_service.move_task(db, owner, a, sections[0], 999_999)
    assert _order_of(db, owner, work_list["id"], sections[0]) == [b, a]


def test_cot_mot_the_va_cot_hai_the_khong_lam_hong_phep_dem(db, owner, work_list, sections):
    a = _create_task(db, owner, work_list["id"], "A", sections[0])["id"]
    task_service.move_task(db, owner, a, sections[0], None)
    assert _sort_orders(db, [a]) == [STEP]

    b = _create_task(db, owner, work_list["id"], "B", sections[0])["id"]
    task_service.move_task(db, owner, b, sections[0], a)
    assert _order_of(db, owner, work_list["id"], sections[0]) == [b, a]


# ── Kéo SANG CỘT KHÁC ──────────────────────────────────────────────────────────

def test_keo_sang_cot_rong(db, owner, work_list, sections):
    """Cột «Hoàn thành» rỗng — đúng cái cột trong ảnh báo lỗi, thả vào không ăn."""
    a = _create_task(db, owner, work_list["id"], "A", sections[0])["id"]
    b = _create_task(db, owner, work_list["id"], "B", sections[0])["id"]

    task_service.move_task(db, owner, a, sections[2], None)
    assert _order_of(db, owner, work_list["id"], sections[2]) == [a]
    assert _order_of(db, owner, work_list["id"], sections[0]) == [b]
    assert _sort_orders(db, [a]) == [STEP]


def test_keo_sang_cot_khac_chen_dung_truoc_moc(db, owner, work_list, sections):
    x = _create_task(db, owner, work_list["id"], "X", sections[1])["id"]
    y = _create_task(db, owner, work_list["id"], "Y", sections[1])["id"]
    a = _create_task(db, owner, work_list["id"], "A", sections[0])["id"]

    task_service.move_task(db, owner, a, sections[1], y)
    assert _order_of(db, owner, work_list["id"], sections[1]) == [x, a, y]
    assert _order_of(db, owner, work_list["id"], sections[0]) == []


def test_danh_so_lai_cot_dich_khong_dung_toi_cot_khac(db, owner, work_list, sections):
    untouched = [_create_task(db, owner, work_list["id"], f"Y{i}", sections[2])["id"] for i in range(3)]
    before = _sort_orders(db, untouched)
    a = _create_task(db, owner, work_list["id"], "A", sections[0])["id"]

    task_service.move_task(db, owner, a, sections[1], None)
    assert _sort_orders(db, untouched) == before


def test_the_da_xoa_mem_khong_chiem_cho_trong_cot(db, owner, work_list, sections):
    a = _create_task(db, owner, work_list["id"], "A", sections[0])["id"]
    b = _create_task(db, owner, work_list["id"], "B", sections[0])["id"]
    c = _create_task(db, owner, work_list["id"], "C", sections[0])["id"]
    task_service.delete_task(db, owner, b)

    task_service.move_task(db, owner, c, sections[0], a)
    assert _order_of(db, owner, work_list["id"], sections[0]) == [c, a]
    assert _sort_orders(db, [c, a]) == [STEP, 2 * STEP]


# ── Chặn ───────────────────────────────────────────────────────────────────────

def test_khong_keo_duoc_sang_cot_cua_list_khac(db, owner, work_list, sections):
    """Cột của list B không có nghĩa gì ở list A — nhận bừa là thẻ mất tích."""
    other_list = list_service.create_list(db, owner, schema.ListCreate(name="Kho"))
    other_section = cfg.get_sections(db, owner, other_list["id"])[0]["id"]
    a = _create_task(db, owner, work_list["id"], "A", sections[0])["id"]

    with pytest.raises(HTTPException) as e:
        task_service.move_task(db, owner, a, other_section, None)
    assert e.value.status_code == 400
    assert db.get(WorkTask, a).section_id == sections[0]


def test_khong_keo_duoc_viec_con_len_bang(db, owner, work_list, sections):
    """Việc child `section_id` luôn NULL; cho nó vào cột là nó lọt ra kanban (C-05)."""
    parent = _create_task(db, owner, work_list["id"], "Cha", sections[0])["id"]
    child = task_service.create_task(db, owner, schema.TaskCreate(
        list_id=work_list["id"], title="Con", parent_id=parent))["id"]

    with pytest.raises(HTTPException) as e:
        task_service.move_task(db, owner, child, sections[0], None)
    assert e.value.status_code == 400
    assert db.get(WorkTask, child).section_id is None


def test_khong_keo_duoc_cot_khong_co_that(db, owner, work_list, sections):
    a = _create_task(db, owner, work_list["id"], "A", sections[0])["id"]
    with pytest.raises(HTTPException) as e:
        task_service.move_task(db, owner, a, 999_999, None)
    assert e.value.status_code == 400


def test_nguoi_ngoai_khong_keo_duoc_the_cua_list_khong_tham_gia(db, owner, work_list, sections):
    a = _create_task(db, owner, work_list["id"], "A", sections[0])["id"]
    elsewhere = Actor(user_id=2, employee_id=22, company_id=COMPANY)
    with pytest.raises(HTTPException) as e:
        task_service.move_task(db, elsewhere, a, sections[1], None)
    assert e.value.status_code == 403


def test_list_luu_tru_thi_khoa_keo_tha(db, owner, work_list, sections):
    a = _create_task(db, owner, work_list["id"], "A", sections[0])["id"]
    list_service.update_list(db, owner, work_list["id"], schema.ListUpdate(is_archived=1))
    with pytest.raises(HTTPException):
        task_service.move_task(db, owner, a, sections[1], None)


# ── Sức chịu ───────────────────────────────────────────────────────────────────

def test_cot_hai_tram_the_keo_cuoi_len_dau_van_du_va_khong_trung_sort_orders(db, owner, work_list, sections):
    ids = [_create_task(db, owner, work_list["id"], f"V{i}", sections[0])["id"] for i in range(200)]

    task_service.move_task(db, owner, ids[-1], sections[0], ids[0])
    after = _order_of(db, owner, work_list["id"], sections[0])
    assert after == [ids[-1]] + ids[:-1]
    orders = _sort_orders(db, after)
    assert orders == sorted(orders) and len(set(orders)) == 200
    assert orders[-1] == 200 * STEP
