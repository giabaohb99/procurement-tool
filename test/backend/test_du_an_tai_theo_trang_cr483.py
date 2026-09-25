"""bao-CR-483 — Bảng công việc tải THEO TRANG: `board(per_section, light)` + `section_tasks`.

Đo trên dev 24/09/2026: mở một dự án 177 việc kéo 545 KB một lượt, 88% là phần mô
tả mà thẻ kanban không vẽ tới, cột «Xong» chứa 160 thẻ. Nay bảng có chế độ NHẸ:
mỗi cột tối đa `per_section` việc, không mô tả, phần dư ghi ở `remaining` để giao
diện tải tiếp theo cột. Bốn thứ tệp này canh:

1. Cắt ĐÚNG THỨ TỰ kanban (`sort_order, id`) và cắt THEO CỘT, không cắt toàn bảng —
   cắt toàn bảng thì cột cuối trống trơn dù có việc.
2. `remaining[cột] = {count, next_task_id}` với `next_task_id` là việc đầu tiên CHƯA
   tải: giao diện neo cú thả «xuống cuối cột» vào nó. Sai một thẻ là thẻ vừa thả
   biến khỏi màn hình sau khi nạp lại.
3. `section_tasks` nối tiếp đúng từ `offset`, `section_id = 0` là «Chưa phân cột»,
   người ngoài dự án ăn 403 y như bảng.
4. `light` bỏ mô tả nhưng giữ cờ `has_description`; chế độ đầy đủ KHÔNG đổi gì so
   với trước (Gantt, tìm kiếm, bộ lọc vẫn ăn đủ dữ liệu).
"""
import pytest
from fastapi import HTTPException

from app.modules.work import list_config_service as cfg
from app.modules.work import list_service, schema, task_service
from app.modules.work.membership_service import Actor
from app.modules.work.task_model import WorkTask

COMPANY = 1


@pytest.fixture()
def owner(db):
    return Actor(user_id=1, employee_id=11, company_id=COMPANY)


@pytest.fixture()
def stranger(db):
    return Actor(user_id=2, employee_id=12, company_id=COMPANY)


@pytest.fixture()
def work_list(db, owner):
    return list_service.create_list(db, owner, schema.ListCreate(name="ERP v2"))


@pytest.fixture()
def sections(db, owner, work_list):
    return [c["id"] for c in cfg.get_sections(db, owner, work_list["id"])]


def _fill(db, owner, list_id, section_id, n, prefix="V"):
    """Tạo n việc nối đuôi vào một cột; trả id theo đúng thứ tự tạo (= thứ tự bảng).

    `create_task` tự gán cột đầu tiên khi không truyền cột, nên «Chưa phân cột»
    phải gỡ cột trực tiếp dưới DB — đúng cảnh dữ liệu cũ / cột đã xóa.
    """
    ids = [task_service.create_task(db, owner, schema.TaskCreate(
        list_id=list_id, title=f"{prefix}{i}", section_id=section_id,
        description=f"mô tả {i}"))["id"] for i in range(n)]
    if section_id is None:
        for i in ids:
            db.get(WorkTask, i).section_id = None
        db.commit()
    return ids


def _ids_of(board, section_id):
    return [t["id"] for t in board["tasks"] if t["section_id"] == section_id]


# ── Chế độ đầy đủ không đổi ───────────────────────────────────────────────────

def test_full_mode_is_unchanged_and_keeps_description(db, owner, work_list, sections):
    _fill(db, owner, work_list["id"], sections[0], 3)
    board = task_service.board(db, owner, work_list["id"])
    assert len(board["tasks"]) == 3
    assert board["remaining"] == {} and board["light"] is False
    assert board["tasks"][0]["description"] == "mô tả 0"
    assert board["tasks"][0]["has_description"] is True


# ── Chế độ nhẹ: cắt theo cột, đúng thứ tự ─────────────────────────────────────

def test_light_mode_slices_each_section_and_reports_next_unloaded_task(db, owner, work_list, sections):
    a = _fill(db, owner, work_list["id"], sections[0], 5, "A")
    b = _fill(db, owner, work_list["id"], sections[1], 2, "B")
    c = _fill(db, owner, work_list["id"], None, 4, "C")   # chưa phân cột

    board = task_service.board(db, owner, work_list["id"], per_section=3, light=True)

    assert board["light"] is True
    assert _ids_of(board, sections[0]) == a[:3], "cắt theo thứ tự bảng, không phải ngẫu nhiên"
    assert _ids_of(board, sections[1]) == b, "cột ít hơn trần thì đủ nguyên"
    assert _ids_of(board, None) == c[:3], "«Chưa phân cột» cũng được cắt, khóa 0"
    assert board["remaining"] == {
        sections[0]: {"count": 2, "next_task_id": a[3]},
        0: {"count": 1, "next_task_id": c[3]},
    }, "cột đủ thì KHÔNG có khóa; next_task_id = việc đầu tiên chưa tải"
    assert all(t["description"] == "" for t in board["tasks"]), "nhẹ = không gửi mô tả"
    assert all(t["has_description"] is True for t in board["tasks"]), "nhưng cờ có/không thì giữ"


def test_light_mode_slice_follows_manual_reorder(db, owner, work_list, sections):
    """Kéo thẻ cuối lên đầu cột thì trang đầu phải chứa nó — cắt theo `sort_order`, không theo id."""
    a = _fill(db, owner, work_list["id"], sections[0], 4, "A")
    task_service.move_task(db, owner, a[3], sections[0], a[0])   # a3 lên trước a0

    board = task_service.board(db, owner, work_list["id"], per_section=2, light=True)
    assert _ids_of(board, sections[0]) == [a[3], a[0]]
    assert board["remaining"][sections[0]] == {"count": 2, "next_task_id": a[1]}


def test_per_section_is_capped_at_backend_max(db, owner, work_list, sections):
    _fill(db, owner, work_list["id"], sections[0], 2)
    board = task_service.board(db, owner, work_list["id"], per_section=10_000, light=True)
    assert len(board["tasks"]) == 2 and board["remaining"] == {}


# ── Trang kế của một cột ───────────────────────────────────────────────────────

def test_section_tasks_continues_from_offset_and_counts_remaining(db, owner, work_list, sections):
    a = _fill(db, owner, work_list["id"], sections[0], 7, "A")

    page = task_service.section_tasks(db, owner, work_list["id"], sections[0], offset=3, limit=2)
    assert [t["id"] for t in page["tasks"]] == a[3:5]
    assert page["remaining"] == 2
    assert page["next_task_id"] == a[5]
    assert page["tasks"][0]["description"] == "", "trang kế mặc định cũng nhẹ"

    last = task_service.section_tasks(db, owner, work_list["id"], sections[0], offset=5, limit=2)
    assert [t["id"] for t in last["tasks"]] == a[5:7]
    assert last["remaining"] == 0 and last["next_task_id"] is None

    beyond = task_service.section_tasks(db, owner, work_list["id"], sections[0], offset=99, limit=2)
    assert beyond["tasks"] == [] and beyond["remaining"] == 0


def test_section_tasks_zero_means_unsectioned_and_ignores_other_sections(db, owner, work_list, sections):
    _fill(db, owner, work_list["id"], sections[0], 2, "A")
    c = _fill(db, owner, work_list["id"], None, 3, "C")
    page = task_service.section_tasks(db, owner, work_list["id"], 0, offset=1, limit=5)
    assert [t["id"] for t in page["tasks"]] == c[1:]
    assert page["remaining"] == 0


def test_section_tasks_excludes_subtasks_like_the_board(db, owner, work_list, sections):
    a = _fill(db, owner, work_list["id"], sections[0], 1, "A")
    task_service.create_task(db, owner, schema.TaskCreate(title="con", parent_id=a[0]))
    page = task_service.section_tasks(db, owner, work_list["id"], sections[0])
    assert [t["id"] for t in page["tasks"]] == a, "việc con không thành thẻ (C-05), trang kế cũng vậy"


def test_section_tasks_requires_membership(db, owner, stranger, work_list, sections):
    _fill(db, owner, work_list["id"], sections[0], 1)
    with pytest.raises(HTTPException) as e:
        task_service.section_tasks(db, stranger, work_list["id"], sections[0])
    assert e.value.status_code == 403
