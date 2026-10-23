"""duoc-CR-675 — ép tải duoc-CR-674 (sổ nhật ký task khai loại việc, hạn, giờ ước lượng / thực tế).

- KHỐI LƯỢNG: sổ 3000 mục × 5 việc con, đủ bốn dòng khai báo mới — đọc trong trần thời gian.
- DÒ NGẪU NHIÊN ô giờ: chuỗi nào sổ NHẬN thì khuôn `Hours` của máy chủ cũng phải nhận, cùng giá trị — lệch là
  script gửi lên một con số máy chủ trả 422 giữa chừng lượt đồng bộ.
- ĐỒNG BỘ 300 mục × 3 việc con qua một API GIẢ CÓ TRẠNG THÁI: mọi gói gửi đi phải qua đúng khuôn
  `TaskCreate` / `TaskUpdate`, giờ thực tế chỉ lọt khi task đã xong (y luật máy chủ); chạy lần hai KHÔNG gửi gì;
  danh mục loại việc chỉ tải một lần.
"""
import importlib.util
import pathlib
import random
import re
import sys
import time
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.modules.work import schema


@pytest.fixture(scope="module")
def mod():
    import app as app_pkg
    path = pathlib.Path(app_pkg.__file__).resolve().parent.parent / "scripts" / "sync_task_journal.py"
    spec = importlib.util.spec_from_file_location("sync_task_journal", path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = m
    spec.loader.exec_module(m)
    return m


TYPES = [{"id": 7, "company_id": 0, "code": "CODE", "name": "Viết mã"},
         {"id": 8, "company_id": 0, "code": "DOC", "name": "Viết tài liệu"},
         {"id": 9, "company_id": 0, "code": "TEST", "name": "Kiểm thử"}]


def _journal(n_parent: int, n_child: int) -> str:
    rnd = random.Random(674)
    out = []
    for i in range(n_parent):
        done = i % 3 != 0
        out.append(f"## duoc-CR-{i} | Việc {i}\n- status: {'xong' if done else 'dang-lam'}\n- date: 2026-10-01\n"
                   f"- loai: {TYPES[i % 3]['code']}\n- han: 2026-10-{1 + i % 28:02d}\n"
                   f"- gio-uoc: {rnd.randint(0, 40)},{rnd.randint(0, 99):02d}\n"
                   + (f"- gio-thuc: {rnd.randint(1, 60)}.5\n" if done else "")
                   + "**Bối cảnh:** thử khối lượng.\n")
        for j in range(n_child):
            out.append(f"### duoc-CR-{i}-{j} | Con {j}\n- status: {'xong' if j % 2 else 'dang-lam'}\n"
                       f"- loai: {TYPES[j % 3]['name']}\n- gio-uoc: {j}\n"
                       + (f"- gio-thuc: {j}.25\n" if j % 2 else "") + "Mô tả con.\n")
    return "\n".join(out)


def test_doc_so_3000_muc_x5_viec_con_trong_tran_thoi_gian(mod, tmp_path):
    p = tmp_path / "so.md"
    p.write_text(_journal(3000, 5), encoding="utf-8")
    t0 = time.perf_counter()
    entries = mod.parse_journal(p)
    took = time.perf_counter() - t0
    assert len(entries) == 3000 and sum(len(e.children) for e in entries) == 15000
    assert all(e.task_type and e.due_date and e.estimate_hours for e in entries)
    #  Trước duoc-CR-675 kiểm trùng key bằng `list.count` trong vòng lặp: ~2,8 giây. Sau: dưới 1 giây.
    assert took < 1.5, f"đọc 18 000 mục mất {took:.2f}s"


def test_kiem_trung_key_khong_bac_hai(mod, tmp_path):
    """`parse_journal` kiểm key trùng — 18 000 mục mà kiểm bằng `list.count` trong vòng lặp là 3,2 tỉ phép so."""
    p = tmp_path / "so.md"
    p.write_text(_journal(3000, 5) + "\n## duoc-CR-7 | Trùng\n- status: xong\n", encoding="utf-8")
    t0 = time.perf_counter()
    with pytest.raises(SystemExit, match="Key trùng trong sổ: duoc-CR-7"):
        mod.parse_journal(p)
    assert time.perf_counter() - t0 < 1.5


_ALPHABET = "0123456789.,-+ eE_abc"


def test_do_ngau_nhien_o_gio_so_nhan_thi_may_chu_cung_nhan(mod):
    rnd = random.Random(675)
    #  «999.5» / «999.99»: khớp regex nhưng vượt trần 999 của máy chủ — lỗi thật bài này tìm ra (duoc-CR-675).
    samples = {"0", "999", "999.5", "999.99", "1000", "1,5", "01.5", "1.", ".5", "1.234", "-1", "1e2", "١٢"}
    samples |= {"".join(rnd.choice(_ALPHABET) for _ in range(rnd.randint(1, 7))) for _ in range(3000)}
    accepted = 0
    for raw in samples:
        try:
            hours = mod._parse_hours("k", "gio-uoc", raw)
        except SystemExit:
            continue
        accepted += 1
        assert re.fullmatch(r"\d{1,3}\.\d{2}", hours), (raw, hours)
        try:
            got = schema.TaskUpdate(estimate_hours=hours).estimate_hours
        except ValidationError as e:   # pragma: no cover — chính là lỗi bài này canh
            pytest.fail(f"sổ nhận «{raw}» → «{hours}» nhưng máy chủ từ chối: {e}")
        assert got == Decimal(raw.replace(",", ".")), (raw, got)
    assert accepted >= 20, "bộ mẫu quá ít chuỗi hợp lệ — bài dò mất nghĩa"


class _StatefulApi:
    """Phân hệ Dự án thu nhỏ: nhớ task / việc con giữa các lượt, ép đúng khuôn và luật giờ của máy chủ."""

    BLANK = {"status": 1, "start_date": "", "due_date": "", "task_type_id": 0, "estimate_hours": None,
             "actual_hours": None, "description": "", "section_id": None, "assignees": [], "labels": []}

    def __init__(self):
        self.tasks: dict[int, dict] = {}
        self.seq = 1000
        self.writes = 0
        self.type_loads = 0

    def _new(self, body: dict, parent_id=None) -> dict:
        self.seq += 1
        t = {**self.BLANK, **{k: v for k, v in body.items() if k in self.BLANK or k == "title"},
             "id": self.seq, "parent_id": parent_id}
        self.tasks[t["id"]] = t
        return dict(t)

    def call(self, method, path, body=None):
        if method == "GET" and path.startswith("/api/work/task-types?"):
            self.type_loads += 1
            return {"items": TYPES}
        if method == "GET" and path == "/api/work/lists/1/board":
            return {"sections": [{"id": 5, "name": "Đang làm"}, {"id": 6, "name": "Xong"}],
                    "tasks": [dict(t) for t in self.tasks.values() if t["parent_id"] is None]}
        m = re.fullmatch(r"/api/work/tasks/(\d+)", path)
        if method == "GET" and m:
            pid = int(m.group(1))
            return {**self.tasks[pid], "subtasks": [dict(t) for t in self.tasks.values() if t["parent_id"] == pid]}
        self.writes += 1
        if method == "POST" and path == "/api/work/tasks":
            schema.TaskCreate.model_validate(body)
            return self._new(body)
        m_sub = re.fullmatch(r"/api/work/tasks/(\d+)/subtasks", path)
        if method == "POST" and m_sub:
            schema.TaskCreate.model_validate({**body, "parent_id": int(m_sub.group(1))})
            return self._new(body, parent_id=int(m_sub.group(1)))
        if method == "PATCH" and m:
            data = schema.TaskUpdate.model_validate(body)
            t = self.tasks[int(m.group(1))]
            for k, v in data.model_dump(exclude_none=True).items():
                t[k] = str(v) if isinstance(v, Decimal) else v
            #  Luật máy chủ (`apply_effort_fields`): trạng thái áp TRƯỚC, giờ thực tế > 0 chỉ khi đã xong.
            if data.actual_hours and t["status"] != 2:
                raise AssertionError(f"422: giờ thực tế cho task chưa xong — gói {body}")
            return dict(t)
        raise AssertionError(f"không mong chờ {method} {path}")


def test_dong_bo_300_muc_khop_khuon_may_chu_va_lan_hai_khong_gui_gi(mod, tmp_path):
    p = tmp_path / "so.md"
    p.write_text(_journal(300, 3), encoding="utf-8")
    entries = mod.parse_journal(p)
    api = _StatefulApi()
    types = mod.TaskTypeDirectory(api)

    mod.sync(api, 1, entries, people=None, dry=False, types=types)
    first = api.writes
    assert len(api.tasks) == 300 * 4, "đủ task cha + việc con"
    by_title = {t["title"].split(" — ")[0]: t for t in api.tasks.values()}
    for e in entries:
        for x in (e, *e.children):
            t = by_title[x.key]
            assert t["status"] == x.task_status
            assert t["task_type_id"] == types.id_of(x.task_type)
            assert Decimal(t["estimate_hours"]) == Decimal(x.estimate_hours)
            if x.actual_hours:
                assert Decimal(t["actual_hours"]) == Decimal(x.actual_hours)
    #  Mỗi task tạo mới: 1 POST + tối đa 1 PATCH — trạng thái và bốn trường đi chung.
    assert first <= 2 * len(api.tasks), first

    api.writes = 0
    mod.sync(api, 1, mod.parse_journal(p), people=None, dry=False, types=types)
    assert api.writes == 0, f"lần hai vẫn gửi {api.writes} lượt ghi"
    assert api.type_loads == 1, "danh mục loại việc tải đúng một lần cho cả hai lượt"
