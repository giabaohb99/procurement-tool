"""Phân hệ Công việc — CỘT MỐC (B-14) và PHỤ THUỘC việc trước–sau (B-15).

Bốn luật tệp này canh; ba cái đầu là thứ CSDL không giữ hộ được nên nếu service
quên thì API vẫn trả 200 và dữ liệu hỏng âm thầm:

1. **Không có vòng lặp** A→B→C→A. Tài liệu QLDA của Văn thư tự ghi nhận bên đó
   CHƯA chặn (`01-danh-sach-tinh-nang.md` §4b) — đây là chỗ ta không lặp lại.
2. **Một cặp việc chỉ một mũi tên**, và không việc nào nối vào chính nó.
3. **Việc con không có phụ thuộc**: nó không bao giờ hiện trên Gantt (C-05) nên
   mũi tên trỏ vào nó là mũi tên không vẽ ra được.
4. **Đổi việc thường → cột mốc thì gộp ngày về một mốc**: mốc là một điểm, giữ
   lại cả `start_date` là Gantt có hai ngày để vẽ một hình thoi.
"""
import pytest
from fastapi import HTTPException

from app.modules.work import link_service, list_service, schema, task_service
from app.modules.work.link_model import WorkTaskLink
from app.modules.work.membership_service import Actor
from app.modules.work.model import WorkLinkType, WorkTaskKind
from app.modules.work.task_model import WorkTask

COMPANY = 1


@pytest.fixture()
def owner(db):
    return Actor(user_id=1, employee_id=11, company_id=COMPANY)


@pytest.fixture()
def work_list(db, owner):
    return list_service.create_list(db, owner, schema.ListCreate(name="Dự án ERP"))


def _task(db, owner, list_id, title, **kw):
    return task_service.create_task(
        db, owner, schema.TaskCreate(list_id=list_id, title=title, **kw))


def _link(db, owner, before, after, link_type=int(WorkLinkType.FS)):
    return link_service.create_link(db, owner, schema.TaskLinkIn(
        predecessor_id=before, successor_id=after, link_type=link_type))


# ── Vòng lặp ──────────────────────────────────────────────────────────────────

def test_chan_vong_lap_ba_buoc_a_b_c_a(db, owner, work_list):
    a = _task(db, owner, work_list["id"], "Khảo sát")["id"]
    b = _task(db, owner, work_list["id"], "Thiết kế")["id"]
    c = _task(db, owner, work_list["id"], "Lập trình")["id"]
    _link(db, owner, a, b)
    _link(db, owner, b, c)

    with pytest.raises(HTTPException) as err:
        _link(db, owner, c, a)
    assert err.value.status_code == 400
    assert "vòng lặp" in err.value.detail

    #  Cú ghi hỏng KHÔNG được để lại cạnh nào: chặn nửa vời thì lần sau người
    #  dùng thấy mũi tên C→A đã có mà đồ thị vẫn kẹt.
    assert db.query(WorkTaskLink).count() == 2


def test_chan_vong_lap_hai_buoc_nguoc_chieu(db, owner, work_list):
    a = _task(db, owner, work_list["id"], "A")["id"]
    b = _task(db, owner, work_list["id"], "B")["id"]
    _link(db, owner, a, b)

    with pytest.raises(HTTPException):
        _link(db, owner, b, a)


def test_khong_noi_vao_chinh_no(db, owner, work_list):
    a = _task(db, owner, work_list["id"], "A")["id"]
    with pytest.raises(HTTPException) as err:
        _link(db, owner, a, a)
    assert err.value.status_code == 400


def test_hai_nhanh_cung_ve_mot_dich_van_hop_le(db, owner, work_list):
    """Kim cương A→B, A→C, B→D, C→D KHÔNG phải vòng lặp — chặn nhầm nó là chặn
    đúng hình dạng thường gặp nhất của một kế hoạch thật."""
    ids = [_task(db, owner, work_list["id"], t)["id"] for t in "ABCD"]
    a, b, c, d = ids
    _link(db, owner, a, b)
    _link(db, owner, a, c)
    _link(db, owner, b, d)
    _link(db, owner, c, d)
    assert db.query(WorkTaskLink).count() == 4


def test_do_thi_lo_co_vong_san_thi_khong_treo(db, owner, work_list):
    """`creates_cycle` là hàm thuần — ném cho nó một đồ thị đã hỏng sẵn (hai cạnh
    khép kín) thì nó phải TRẢ VỀ, không được quay vòng vô tận."""
    class Edge:
        def __init__(self, p, s):
            self.predecessor_id, self.successor_id = p, s

    assert link_service.creates_cycle([Edge(1, 2), Edge(2, 1)], 3, 1) is False
    assert link_service.creates_cycle([Edge(1, 2), Edge(2, 1)], 1, 2) is True


def test_do_thi_rong_thi_moi_canh_deu_hop_le(db):
    assert link_service.creates_cycle([], 1, 2) is False


# ── Trùng cặp · khác dự án · việc con ─────────────────────────────────────────

def test_mot_cap_viec_chi_mot_mui_ten(db, owner, work_list):
    a = _task(db, owner, work_list["id"], "A")["id"]
    b = _task(db, owner, work_list["id"], "B")["id"]
    _link(db, owner, a, b)

    #  Kể cả khi đổi LOẠI: hai mũi tên chồng nhau giữa một cặp thì nhìn như một,
    #  mà xóa mãi không hết.
    with pytest.raises(HTTPException) as err:
        _link(db, owner, a, b, link_type=int(WorkLinkType.SS))
    assert "đã có phụ thuộc" in err.value.detail


def test_hai_dau_khac_du_an_thi_tu_choi(db, owner, work_list):
    khac = list_service.create_list(db, owner, schema.ListCreate(name="Dự án khác"))
    a = _task(db, owner, work_list["id"], "A")["id"]
    b = _task(db, owner, khac["id"], "B")["id"]
    with pytest.raises(HTTPException) as err:
        _link(db, owner, a, b)
    assert err.value.status_code == 400


def test_viec_con_khong_co_phu_thuoc(db, owner, work_list):
    cha = _task(db, owner, work_list["id"], "Cha")["id"]
    con = task_service.create_task(db, owner, schema.TaskCreate(
        title="Con", parent_id=cha))["id"]
    khac = _task(db, owner, work_list["id"], "Việc khác")["id"]

    with pytest.raises(HTTPException) as err:
        _link(db, owner, khac, con)
    assert "việc con" in err.value.detail


def test_kieu_phu_thuoc_la_thi_tu_choi(db, owner, work_list):
    a = _task(db, owner, work_list["id"], "A")["id"]
    b = _task(db, owner, work_list["id"], "B")["id"]
    with pytest.raises(HTTPException):
        _link(db, owner, a, b, link_type=99)


def test_xoa_viec_thi_mui_ten_di_theo(db, owner, work_list):
    """Xóa MỀM một việc không đụng tới bảng link (khóa ngoại chỉ bắt xóa cứng),
    nên Gantt phải tự bỏ qua mũi tên trỏ vào việc đã xóa — khẳng định ở đây để
    người sửa sau biết hành vi này là CỐ Ý, không phải sót."""
    a = _task(db, owner, work_list["id"], "A")["id"]
    b = _task(db, owner, work_list["id"], "B")["id"]
    _link(db, owner, a, b)
    task_service.delete_task(db, owner, b)

    assert db.query(WorkTaskLink).count() == 1
    board = task_service.board(db, owner, work_list["id"])
    assert [t["id"] for t in board["tasks"]] == [a]
    assert len(board["links"]) == 1


def test_board_tra_ve_mui_ten_cung_mot_luot(db, owner, work_list):
    a = _task(db, owner, work_list["id"], "A")["id"]
    b = _task(db, owner, work_list["id"], "B")["id"]
    _link(db, owner, a, b, link_type=int(WorkLinkType.FF))

    board = task_service.board(db, owner, work_list["id"])
    assert board["links"] == [{
        "id": board["links"][0]["id"], "list_id": work_list["id"],
        "predecessor_id": a, "successor_id": b,
        "link_type": int(WorkLinkType.FF), "lag_days": 0,
    }]


def test_doi_kieu_phu_thuoc(db, owner, work_list):
    a = _task(db, owner, work_list["id"], "A")["id"]
    b = _task(db, owner, work_list["id"], "B")["id"]
    link = _link(db, owner, a, b)

    doi = link_service.update_link(db, owner, link["id"], schema.TaskLinkUpdate(
        link_type=int(WorkLinkType.SS), lag_days=-2))
    assert doi["link_type"] == int(WorkLinkType.SS)
    assert doi["lag_days"] == -2
    #  Hai đầu KHÔNG được đổi theo: đổi đầu là một mũi tên khác hẳn.
    assert (doi["predecessor_id"], doi["successor_id"]) == (a, b)


def test_doi_kieu_khong_dung_thi_tu_choi(db, owner, work_list):
    a = _task(db, owner, work_list["id"], "A")["id"]
    b = _task(db, owner, work_list["id"], "B")["id"]
    link = _link(db, owner, a, b)

    with pytest.raises(HTTPException) as err:
        link_service.update_link(db, owner, link["id"],
                                 schema.TaskLinkUpdate(link_type=0))
    assert err.value.status_code == 400
    #  Từ chối rồi thì KHÔNG được ghi nửa vời — kiểu cũ phải còn nguyên.
    assert db.get(WorkTaskLink, link["id"]).link_type == int(WorkLinkType.FS)


def test_doi_kieu_cua_phu_thuoc_khong_co_thi_404(db, owner):
    with pytest.raises(HTTPException) as err:
        link_service.update_link(db, owner, 999, schema.TaskLinkUpdate(link_type=2))
    assert err.value.status_code == 404


def test_khong_gui_gi_thi_giu_nguyen(db, owner, work_list):
    """`None` = không đổi, đúng quy ước PATCH của cả phân hệ — không được hiểu
    thành "về mặc định" mà âm thầm nắn kiểu về FS."""
    a = _task(db, owner, work_list["id"], "A")["id"]
    b = _task(db, owner, work_list["id"], "B")["id"]
    link = _link(db, owner, a, b, link_type=int(WorkLinkType.FF))

    doi = link_service.update_link(db, owner, link["id"], schema.TaskLinkUpdate())
    assert doi["link_type"] == int(WorkLinkType.FF)
    assert doi["lag_days"] == 0


def test_xoa_phu_thuoc(db, owner, work_list):
    a = _task(db, owner, work_list["id"], "A")["id"]
    b = _task(db, owner, work_list["id"], "B")["id"]
    link = _link(db, owner, a, b)

    link_service.delete_link(db, owner, link["id"])
    assert db.query(WorkTaskLink).count() == 0

    with pytest.raises(HTTPException) as err:
        link_service.delete_link(db, owner, link["id"])
    assert err.value.status_code == 404


# ── Cột mốc (B-14) ────────────────────────────────────────────────────────────

def test_tao_cot_moc(db, owner, work_list):
    t = _task(db, owner, work_list["id"], "Nghiệm thu",
              kind=int(WorkTaskKind.MILESTONE), due_date="2026-10-15")
    assert t["kind"] == int(WorkTaskKind.MILESTONE)


def test_kind_la_thi_ve_viec_thuong_chu_khong_chan_ca_luot_tao(db, owner, work_list):
    t = _task(db, owner, work_list["id"], "A", kind=9)
    assert t["kind"] == int(WorkTaskKind.TASK)


def test_doi_thanh_cot_moc_thi_gop_ngay_ve_mot_moc(db, owner, work_list):
    t = _task(db, owner, work_list["id"], "Kiểm thử",
              start_date="2026-10-01", due_date="2026-10-09")
    task_service.update_task(db, owner, t["id"],
                             schema.TaskUpdate(kind=int(WorkTaskKind.MILESTONE)))

    row = db.get(WorkTask, t["id"])
    assert row.start_date == ""
    assert row.due_date == "2026-10-09"


def test_cot_moc_chi_co_ngay_bat_dau_thi_lay_no_lam_moc(db, owner, work_list):
    """Việc chỉ có ngày bắt đầu mà đổi thành mốc: không được nuốt mất ngày duy
    nhất người dùng đã nhập, nếu không hình thoi biến khỏi biểu đồ."""
    t = _task(db, owner, work_list["id"], "Khởi động", start_date="2026-09-01")
    task_service.update_task(db, owner, t["id"],
                             schema.TaskUpdate(kind=int(WorkTaskKind.MILESTONE)))

    row = db.get(WorkTask, t["id"])
    assert row.due_date == "2026-09-01"
    assert row.start_date == ""


def test_doi_cot_moc_ve_viec_thuong_giu_nguyen_han(db, owner, work_list):
    t = _task(db, owner, work_list["id"], "Mốc",
              kind=int(WorkTaskKind.MILESTONE), due_date="2026-10-15")
    task_service.update_task(db, owner, t["id"],
                             schema.TaskUpdate(kind=int(WorkTaskKind.TASK)))

    row = db.get(WorkTask, t["id"])
    assert row.kind == int(WorkTaskKind.TASK)
    assert row.due_date == "2026-10-15"
