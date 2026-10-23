"""duoc-CR-674 — sổ nhật ký task khai thêm loại việc, hạn, giờ ước lượng, giờ thực tế.

Luật cần giữ: sổ chỉ gửi trường nó KHAI (không khai = không đụng giá trị người dùng nhập trên ERP) · giờ cùng
khuôn máy chủ (0..999, 2 số lẻ) · `gio-thuc` chỉ khi `status: xong` · tra loại việc theo mã rồi theo tên, trùng mã
nhiều pháp nhân thì ưu tiên loại dùng chung · giờ thực tế đi CÙNG lượt PATCH với trạng thái (máy chủ áp trạng thái
trước) · chạy lại không sinh PATCH thừa.
"""
import importlib.util
import pathlib
import sys
from decimal import Decimal

import pytest

from app.modules.work import list_service, schema, task_service
from app.modules.work import task_type_service as types_svc
from app.modules.work.membership_service import Actor
from app.modules.work.model import WorkTaskStatus


def _load_sync_script():
    #  Neo theo gói `app` (trong container `backend/` là `/app`) — cùng cách test_du_an_nhom_cr482.
    import app as app_pkg
    path = pathlib.Path(app_pkg.__file__).resolve().parent.parent / "scripts" / "sync_task_journal.py"
    spec = importlib.util.spec_from_file_location("sync_task_journal", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def mod():
    return _load_sync_script()


def _parse(mod, tmp_path, body: str):
    p = tmp_path / "so.md"
    p.write_text(body, encoding="utf-8")
    return mod.parse_journal(p)


class _TypesApi:
    """Giả `GET /api/work/task-types` — đếm số lần gọi để canh bộ nhớ đệm."""

    def __init__(self, items):
        self.items, self.calls = items, 0

    def call(self, method, path, body=None):
        assert method == "GET" and path.startswith("/api/work/task-types?"), path
        assert "is_active=true" in path, "chỉ tra loại đang dùng"
        self.calls += 1
        return {"total": len(self.items), "items": self.items}


TYPES = [
    {"id": 7, "company_id": 0, "code": "CODE", "name": "Viết mã"},
    {"id": 8, "company_id": 0, "code": "DOC", "name": "Viết tài liệu"},
    {"id": 9, "company_id": 2, "code": "DOC", "name": "Tài liệu riêng công ty 2"},
    {"id": 10, "company_id": 2, "code": "REV", "name": "Rà mã"},
    {"id": 11, "company_id": 3, "code": "REV", "name": "Rà mã công ty 3"},
]


# ── Đọc sổ ──────────────────────────────────────────────────────────────────────────

def test_doc_du_bon_dong_moi_ca_o_viec_con_va_chuan_hoa_gio(mod, tmp_path):
    [e] = _parse(mod, tmp_path, """
## duoc-CR-1 | Việc cha
- status: xong
- date: 2026-10-20
- loai: CODE
- han: 2026-10-25
- gio-uoc: 4
- gio-thuc: 3,5
Mô tả.

### duoc-CR-1-1 | Việc con
- status: dang-lam
- loai: Viết tài liệu
- gio-uoc: 0.25
""")
    assert (e.task_type, e.due_date, e.estimate_hours, e.actual_hours) == ("CODE", "2026-10-25", "4.00", "3.50")
    assert e.desc_lines == ["Mô tả."], "bốn dòng khai báo không lọt vào mô tả"
    [c] = e.children
    assert (c.task_type, c.estimate_hours, c.actual_hours, c.due_date) == ("Viết tài liệu", "0.25", "", "")


def test_khong_khai_thi_de_trong(mod, tmp_path):
    [e] = _parse(mod, tmp_path, "## k | t\n- status: dang-lam\n")
    assert (e.task_type, e.due_date, e.estimate_hours, e.actual_hours) == ("", "", "", "")


@pytest.mark.parametrize("line, msg", [
    ("- han: 25/10/2026", "han phải là YYYY-MM-DD"),
    ("- gio-uoc: 1000", "gio-uoc phải là số giờ"),
    ("- gio-uoc: 1.234", "gio-uoc phải là số giờ"),
    ("- gio-uoc: -1", "gio-uoc phải là số giờ"),
    ("- gio-thuc: abc", "gio-thuc phải là số giờ"),
])
def test_tu_choi_gia_tri_sai_khuon(mod, tmp_path, line, msg):
    with pytest.raises(SystemExit, match=msg):
        _parse(mod, tmp_path, f"## k | t\n- status: xong\n{line}\n")


def test_gio_thuc_chi_khi_xong_ke_ca_khi_status_dung_sau(mod, tmp_path):
    with pytest.raises(SystemExit, match="gio-thuc chỉ khai khi status: xong"):
        _parse(mod, tmp_path, "## k | t\n- gio-thuc: 2\n- status: dang-lam\n")
    #  Việc con đang làm cũng bị chặn, dù cha đã xong.
    with pytest.raises(SystemExit, match=r"\[k-1\] gio-thuc"):
        _parse(mod, tmp_path, "## k | t\n- status: xong\n### k-1 | c\n- gio-thuc: 1\n")
    #  Giờ 0 là xóa giờ — máy chủ nhận ở mọi trạng thái nên sổ cũng không chặn.
    [e] = _parse(mod, tmp_path, "## k | t\n- status: dang-lam\n- gio-thuc: 0\n")
    assert e.actual_hours == "0.00"


def test_han_khong_duoc_truoc_ngay_bat_dau(mod, tmp_path):
    with pytest.raises(SystemExit, match="đứng trước date"):
        _parse(mod, tmp_path, "## k | t\n- date: 2026-10-20\n- han: 2026-10-19\n")


# ── Tra loại việc ───────────────────────────────────────────────────────────────────

def test_tra_loai_viec_theo_ma_roi_theo_ten_va_nho_ket_qua(mod):
    api = _TypesApi(TYPES)
    d = mod.TaskTypeDirectory(api)
    assert d.id_of("code") == 7, "mã không phân biệt hoa thường"
    assert d.id_of(" Viết mã ") == 7, "không khớp mã thì khớp tên"
    assert d.id_of("DOC") == 8, "trùng mã nhiều pháp nhân → ưu tiên loại dùng chung"
    assert d.id_of("") == 0
    assert api.calls == 1, "tải danh mục một lần cho cả lượt chạy"


def test_tra_loai_viec_mo_ho_hoac_khong_co_thi_dung(mod):
    d = mod.TaskTypeDirectory(_TypesApi(TYPES))
    with pytest.raises(SystemExit, match="nhiều pháp nhân"):
        d.id_of("REV")
    with pytest.raises(SystemExit, match="Đang có: CODE, DOC, DOC, REV, REV"):
        d.id_of("KHONG_CO")


# ── Dựng PATCH ──────────────────────────────────────────────────────────────────────

def _entry(mod, **kw):
    e = mod.JournalEntry(key="k", title="t", status_word="xong")
    for k, v in kw.items():
        setattr(e, k, v)
    return e


def test_effort_patch_chi_gui_truong_co_khai_va_dang_khac(mod):
    d = mod.TaskTypeDirectory(_TypesApi(TYPES))
    task = {"task_type_id": 0, "due_date": "", "estimate_hours": None, "actual_hours": "1.00"}
    e = _entry(mod, task_type="CODE", due_date="2026-10-25", estimate_hours="2.50")
    assert mod.effort_patch(e, task, d) == {"task_type_id": 7, "due_date": "2026-10-25", "estimate_hours": "2.50"}, \
        "giờ thực tế sổ không khai thì giữ giá trị người dùng đã nhập"
    same = {"task_type_id": 7, "due_date": "2026-10-25", "estimate_hours": "2.5", "actual_hours": None}
    assert mod.effort_patch(e, same, d) == {}, "so giờ bằng số, «2.5» = «2.50»"
    assert mod.effort_patch(_entry(mod), task, d) == {}, "không khai gì thì không đụng gì"


class _SyncApi:
    """Giả đủ các đường `sync()` gọi cho MỘT task mới có một việc con — ghi lại mọi POST / PATCH."""

    def __init__(self):
        self.writes = []
        self.next_id = 100

    def call(self, method, path, body=None):
        if path.startswith("/api/work/task-types?"):
            return {"items": TYPES}
        if method == "GET" and path == "/api/work/lists/1/board":
            return {"sections": [{"id": 5, "name": "Đang làm"}, {"id": 6, "name": "Xong"}], "tasks": []}
        if method == "GET" and path.startswith("/api/work/lists/1/label-fields"):
            return []
        if method == "GET" and path.startswith("/api/work/tasks/"):
            return {"subtasks": []}
        if method in ("POST", "PATCH"):
            self.writes.append((method, path, body))
            self.next_id += 1
            return {"id": self.next_id, "task_type_id": 0, "due_date": "", "estimate_hours": None,
                    "actual_hours": None, "assignees": [], "labels": []}
        raise AssertionError(f"không mong chờ {method} {path}")


def test_sync_tao_moi_gui_trang_thai_va_gio_trong_mot_luot_patch(mod, tmp_path):
    entries = _parse(mod, tmp_path, """
## k | Cha
- status: xong
- loai: CODE
- gio-thuc: 2
### k-1 | Con
- status: xong
- loai: DOC
- han: 2026-10-30
""")
    api = _SyncApi()
    mod.sync(api, 1, entries, people=None, dry=False)
    patches = [(p, b) for m, p, b in api.writes if m == "PATCH"]
    assert patches == [
        ("/api/work/tasks/101", {"status": 2, "task_type_id": 7, "actual_hours": "2.00"}),
        ("/api/work/tasks/103", {"status": 2, "task_type_id": 8, "due_date": "2026-10-30"}),
    ], "mỗi task đúng một PATCH, trạng thái và giờ thực tế đi chung"


# ── Máy chủ nhận đúng dữ liệu script gửi ────────────────────────────────────────────

def test_may_chu_nhan_patch_cua_so_ca_gio_thuc_cung_luot_xong(db, mod):
    owner = Actor(user_id=1, employee_id=11, company_id=1)
    lst = list_service.create_list(db, owner, schema.ListCreate(name="ERP v2"))
    t_type = types_svc.create_type(db, 1, schema.TaskTypeCreate(company_id=0, code="CODE", name="Viết mã"))
    task = task_service.create_task(db, owner, schema.TaskCreate(list_id=lst["id"], title="k — Cha"))

    d = mod.TaskTypeDirectory(_TypesApi([{"id": t_type["id"], "company_id": 0, "code": "CODE", "name": "Viết mã"}]))
    e = _entry(mod, task_type="CODE", due_date="2026-10-30", estimate_hours="4.00", actual_hours="3.50")
    patch = {"status": e.task_status} | mod.effort_patch(e, task, d)
    #  Đi đúng đường của API: JSON → khuôn TaskUpdate → service.
    out = task_service.update_task(db, owner, task["id"], schema.TaskUpdate.model_validate(patch))

    assert out["status"] == int(WorkTaskStatus.DONE)
    assert out["task_type_id"] == t_type["id"]
    assert (out["due_date"], out["estimate_hours"], out["actual_hours"]) == ("2026-10-30", "4.00", "3.50")
    assert mod.effort_patch(e, out, d) == {}, "chạy lại lần hai không còn gì để gửi"
    assert Decimal(out["actual_hours"]) == Decimal("3.5")
