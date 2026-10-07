"""Đồng bộ sổ nhật ký task (.md) lên phân hệ Dự án (modules/work) qua API.

Chạy trên MÁY NGOÀI (host), không cần Docker — chỉ dùng stdlib:

    python backend/scripts/sync_task_journal.py                # đọc .task_sync.env
    python backend/scripts/sync_task_journal.py --dry-run      # xem sẽ làm gì, không ghi
    python backend/scripts/sync_task_journal.py --base-url https://erp.degoholding.vn \
        --username BOT --password ...

Sổ nguồn mặc định: doc/tai-lieu-ky-thuat/nhat-ky-task.md (định dạng ghi ngay
đầu tệp đó). Idempotent: mỗi mục khớp task trên ERP theo `key` ở đầu tiêu đề
(`<key> — <tiêu đề>`), có rồi thì PATCH, chưa có thì POST — chạy lại vô hại.

Cấu hình đọc theo thứ tự: CLI > biến môi trường > tệp env (mặc định
backend/scripts/.task_sync.env, dạng KEY=VALUE, KHÔNG commit tệp này):

    WORK_SYNC_BASE_URL=http://localhost:8000
    WORK_SYNC_USER=TESTREQ
    WORK_SYNC_PASS=...
    WORK_SYNC_LIST=Nhật ký task
    WORK_SYNC_PIC=NSU209
    WORK_SYNC_PIC_BY_PREFIX=bao=NSU209,duoc=NSU231,giang=NSU199,ai=NSU209   # tùy chọn
    WORK_SYNC_TAG_BY_PREFIX=bao=Bảo,duoc=Được,giang=Giang,ai=Bot AI          # tùy chọn, "-" = tắt
    WORK_SYNC_ROUTE=1                                                        # 0 = không chia dự án theo từ khóa

`WORK_SYNC_PIC` là mã nhân sự nhận mọi task của sổ (mục nào khai `- pic:` riêng
thì theo mục đó). Để trống thì script không đụng tới người phụ trách.

bao-CR-604 (07/10/2026) — ba luật thêm để bảng dự án đọc được ai làm gì:
- NGƯỜI PHỤ TRÁCH theo TIỀN TỐ key: `duoc-CR-…` → Được (NSU231), `giang-CR-…` →
  Giang, `bao-CR-…` và `ai-CR-…` → Bảo; mục khai `- pic:` thì vẫn theo mục.
- NHÃN «Tag» theo tiền tố (Bảo / Được / Giang / Bot AI) — trường «Tag» chọn nhiều
  có sẵn ở mọi list, thiếu thì tạo; giá trị gán CỘNG THÊM, không gỡ tag người
  dùng tự gán. Mục khai `- tag: A, B` thì thêm cả A, B.
- CHIA DỰ ÁN theo từ khóa trong key + tiêu đề (`LIST_RULES`): văn thư → «Công cụ
  văn thư», đặt xe / duyệt dấu → «Duyệt dấu, Đặt xe», bot / Agent Hub → «Công cụ
  Ai»… Mục khai `- list:` thì theo mục. Task ĐÃ có ở dự án khác thì giữ nguyên
  và báo; chạy `--move` mới xóa chỗ cũ (vào thùng rác) rồi tạo ở dự án đúng —
  API không có đường chuyển task giữa hai list.
Đẩy lên PROD: đổi `WORK_SYNC_BASE_URL` sang https://erp.degoholding.vn và tài
khoản prod (có quyền `work_task` create/write + đọc hồ sơ nhân sự), chạy
`--dry-run` xem trước; nhóm «DX» chưa có thì script tự tạo.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
DEFAULT_JOURNAL = REPO_ROOT / "doc" / "tai-lieu-ky-thuat" / "nhat-ky-task.md"
DEFAULT_ENV_FILE = SCRIPT_DIR / ".task_sync.env"
DEFAULT_LIST_NAME = "ERP v2"

#  bao-CR-604: mặc định theo TIỀN TỐ key (`bao-CR-…`, `duoc-CR-…`, `giang-CR-…`, `ai-CR-…`).
#  Mã nhân sự giống nhau ở local / dev / prod nên để thẳng ở đây; đổi bằng env
#  `WORK_SYNC_PIC_BY_PREFIX` / `WORK_SYNC_TAG_BY_PREFIX` (dạng `k=v,k=v`; "-" = tắt).
DEFAULT_PIC_BY_PREFIX = {"bao": "NSU209", "duoc": "NSU231", "giang": "NSU199", "ai": "NSU209"}
DEFAULT_TAG_BY_PREFIX = {"bao": "Bảo", "duoc": "Được", "giang": "Giang", "ai": "Bot AI"}
TAG_FIELD_NAME = "Tag"
#  Chia vào DỰ ÁN theo từ khóa trong KEY + TIÊU ĐỀ (không soi mô tả — mô tả nhắc
#  đủ thứ phân hệ). Luật đầu khớp thắng; không khớp thì về list mặc định.
LIST_RULES: list[tuple[str, str]] = [
    (r"văn thư|văn bản|doc_folder|thư mục văn bản|sổ văn bản", "Công cụ văn thư"),
    (r"đặt xe|duyệt dấu|đóng dấu|dấu mộc|app cũ|datxe|vehicle_booking|seal_request", "Duyệt dấu, Đặt xe"),
    (r"diễn đàn|forum", "Diễn đàn"),
    (r"^ai-cr|agent hub|bot telegram|đậu đậu|trợ lý ai|assistant|agent_hub", "Công cụ Ai"),
    (r"nhật ký hệ thống|system_log", "Nhật ký hệ thống"),
]


def key_prefix(key: str) -> str:
    m = re.match(r"^([a-z]+)-CR-", key, re.IGNORECASE)
    return m.group(1).lower() if m else ""


def route_list(entry: "JournalEntry") -> str:
    text = f"{entry.key} {entry.title}".lower()
    for pattern, name in LIST_RULES:
        if re.search(pattern, text):
            return name
    return ""


def parse_map(raw: str, default: dict[str, str]) -> dict[str, str]:
    """`k=v,k=v` → dict; rỗng = mặc định; "-" = tắt hẳn."""
    raw = (raw or "").strip()
    if not raw:
        return dict(default)
    if raw == "-":
        return {}
    out = {}
    for part in re.split(r"[,;]", raw):
        if "=" in part:
            k, v = part.split("=", 1)
            out[k.strip().lower()] = v.strip()
    return out

#  Trạng thái trong sổ → (cột kanban, WorkTaskStatus). Bộ số khớp
#  app/modules/work/model.py: OPEN=1, DONE=2, CANCELLED=3.
STATUS_MAP = {
    "dang-lam": ("Đang làm", 1),
    "danglam": ("Đang làm", 1),
    "doing": ("Đang làm", 1),
    "open": ("Đang làm", 1),
    "xong": ("Xong", 2),
    "done": ("Xong", 2),
    "huy": ("Xong", 3),
    "cancel": ("Xong", 3),
    "cancelled": ("Xong", 3),
}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@dataclass
class JournalEntry:
    key: str
    title: str
    status_word: str = "dang-lam"
    start_date: str = ""
    desc_lines: list[str] = field(default_factory=list)
    #  Việc con — mục `###` nằm dưới mục `##` cha trong sổ. Chỉ một cấp,
    #  đúng trần của module (C-05: việc con không ra kanban, không thuộc cột).
    children: list["JournalEntry"] = field(default_factory=list)
    #  Task list đích của mục (`- list:`). Rỗng = list mặc định trong config.
    list_name: str = ""
    #  Mã nhân sự của người phụ trách (`- pic:`, nhiều mã cách nhau bằng dấu
    #  phẩy). Rỗng = lấy theo cấu hình `WORK_SYNC_PIC`; việc con theo cha.
    pic_codes: list[str] = field(default_factory=list)
    #  Nhãn «Tag» cần có trên task (`- tag:` + tag theo tiền tố, bao-CR-604).
    tag_names: list[str] = field(default_factory=list)

    @property
    def display_title(self) -> str:
        return f"{self.key} — {self.title}" if self.title else self.key

    @property
    def description(self) -> str:
        return "\n".join(self.desc_lines).strip()

    @property
    def section_name(self) -> str:
        return STATUS_MAP[self.status_word][0]

    @property
    def task_status(self) -> int:
        return STATUS_MAP[self.status_word][1]


def _split_heading(head: str) -> tuple[str, str]:
    if "|" in head:
        key, title = (p.strip() for p in head.split("|", 1))
    else:
        key, title = head, head
    return key, title


def parse_journal(path: Path) -> list[JournalEntry]:
    """Bóc các mục `## key | tiêu đề` (và việc con `### key | tiêu đề` ngay
    dưới) — dòng `- status:`/`- date:`/`- list:`/`- pic:` là khai báo, mọi dòng
    khác trong thân là mô tả giữ nguyên văn."""
    entries: list[JournalEntry] = []
    parent: JournalEntry | None = None   # mục `##` gần nhất
    current: JournalEntry | None = None  # mục đang nhận metadata/mô tả (cha hoặc con)
    in_fence = False
    for raw in path.read_text(encoding="utf-8").splitlines():
        #  Khối ``` (ví dụ định dạng trong phần hướng dẫn) không phải dữ liệu.
        if raw.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if raw.startswith("### "):
            if parent is None:
                raise SystemExit(f"Mục con '{raw.strip()}' phải nằm dưới một mục `##` cha")
            key, title = _split_heading(raw[4:].strip())
            current = JournalEntry(key=key, title=title)
            parent.children.append(current)
            continue
        if raw.startswith("## "):
            key, title = _split_heading(raw[3:].strip())
            parent = current = JournalEntry(key=key, title=title)
            entries.append(parent)
            continue
        if current is None:
            continue  # phần hướng dẫn trước mục đầu tiên
        m = re.match(r"^-\s*(status|trang-thai)\s*:\s*(\S+)", raw, re.IGNORECASE)
        if m:
            word = m.group(2).lower()
            if word not in STATUS_MAP:
                raise SystemExit(
                    f"[{current.key}] status '{word}' không hợp lệ — dùng: "
                    + ", ".join(sorted(set(STATUS_MAP)))
                )
            current.status_word = word
            continue
        m = re.match(r"^-\s*(date|ngay)\s*:\s*(\S+)", raw, re.IGNORECASE)
        if m:
            if not DATE_RE.match(m.group(2)):
                raise SystemExit(f"[{current.key}] date phải là YYYY-MM-DD")
            current.start_date = m.group(2)
            continue
        m = re.match(r"^-\s*(list|du-an)\s*:\s*(.+)", raw, re.IGNORECASE)
        if m:
            if current is not parent:
                raise SystemExit(f"[{current.key}] việc con đi theo list của cha — "
                                 "đừng khai `- list:` trong mục ###")
            current.list_name = m.group(2).strip()
            continue
        m = re.match(r"^-\s*(pic|nguoi-phu-trach)\s*:\s*(.+)", raw, re.IGNORECASE)
        if m:
            current.pic_codes = [c.strip().upper()
                                 for c in re.split(r"[,;]", m.group(2)) if c.strip()]
            continue
        m = re.match(r"^-\s*(tag|nhan)\s*:\s*(.+)", raw, re.IGNORECASE)
        if m:
            current.tag_names = [c.strip() for c in re.split(r"[,;]", m.group(2)) if c.strip()]
            continue
        if raw.strip():
            current.desc_lines.append(raw.rstrip())
    #  Key phải duy nhất TOÀN SỔ (kể cả việc con) — nó là mỏ neo idempotent.
    all_keys = [e.key for e in entries] + [c.key for e in entries for c in e.children]
    dup = sorted({k for k in all_keys if all_keys.count(k) > 1})
    if dup:
        raise SystemExit(f"Key trùng trong sổ: {', '.join(dup)} — mỗi key một mục")
    return entries


class WorkApi:
    """Client tối giản cho /api/work — phong bì {success, message, data}."""

    def __init__(self, base_url: str, token: str = ""):
        self.base_url = base_url.rstrip("/")
        self.token = token

    def call(self, method: str, path: str, payload: dict | None = None) -> dict:
        req = urllib.request.Request(self.base_url + path, method=method)
        req.add_header("Content-Type", "application/json")
        #  Cloudflare trước deverp/erp chặn UA mặc định của urllib (lỗi 1010).
        #  Chuỗi phải có `python-urllib` để `core/device_fingerprint.py` xếp vào
        #  họ `tool` → tab Tài khoản hiện "Công cụ dòng lệnh" thay vì "Không rõ
        #  thiết bị".
        req.add_header("User-Agent", "sync_task_journal/1.0 (python-urllib)")
        if self.token:
            req.add_header("Authorization", f"Bearer {self.token}")
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        try:
            with urllib.request.urlopen(req, data=body, timeout=30) as resp:
                out = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:500]
            raise SystemExit(f"API {method} {path} -> HTTP {e.code}: {detail}") from e
        except urllib.error.URLError as e:
            raise SystemExit(f"Không nối được {self.base_url}: {e.reason}") from e
        if not out.get("success"):
            raise SystemExit(f"API {method} {path} báo lỗi: {out}")
        return out.get("data")

    def login(self, username: str, password: str) -> None:
        data = self.call("POST", "/api/auth/login",
                         {"username": username, "password": password})
        self.token = data["access_token"]

    def logout(self) -> None:
        """Đóng phiên vừa mở. Mỗi lần đăng nhập là một dòng `tab_login_session`
        sống tới khi vé refresh hết hạn — không gọi thì chạy 30 lần là người
        chạy thấy 30 "thiết bị đang đăng nhập" ở tab Tài khoản."""
        if not self.token:
            return
        try:
            self.call("POST", "/api/auth/logout")
        except SystemExit as e:
            #  Đăng xuất hỏng không được che kết quả đồng bộ đã in ở trên.
            print(f"(không đăng xuất được: {e})")
        self.token = ""


class PeopleDirectory:
    """Tra mã nhân sự (ví dụ `NSU209`) ra id hồ sơ nhân sự.

    Người phụ trách task lưu bằng **id hồ sơ nhân sự**, không phải id tài
    khoản — nên sổ khai mã nhân sự (bất biến, đọc được) rồi script tự tra, chứ
    đừng ghi số id vào sổ: id ở local, dev và prod khác nhau.
    """

    def __init__(self, api: WorkApi):
        self.api = api
        self._by_code: dict[str, int] = {}
        self._me: dict | None = None

    def me(self) -> dict:
        if self._me is None:
            self._me = self.api.call("GET", "/api/auth/me") or {}
        return self._me

    def id_of(self, code: str) -> int:
        code = code.strip().upper()
        if not code:
            return 0
        if code not in self._by_code:
            self._by_code[code] = self._find(code)
        return self._by_code[code]

    def _find(self, code: str) -> int:
        #  Tra chính tài khoản đang chạy script TRƯỚC: ca hay gặp nhất là gán
        #  cho chính mình, và đường này không đòi quyền đọc hồ sơ nhân sự.
        me = self.me()
        if str(me.get("emp_code") or "").upper() == code:
            return int(me.get("employee_id") or 0)
        query = urllib.parse.urlencode({"search": code, "page_size": 50})
        data = self.api.call("GET", f"/api/employees?{query}") or {}
        for row in data.get("items") or []:
            if str(row.get("code") or "").upper() == code:
                return int(row.get("id") or 0)
        raise SystemExit(
            f"Không tra ra nhân sự mã '{code}'. Kiểm lại mã trong sổ (hoặc "
            "WORK_SYNC_PIC), và kiểm tài khoản chạy script có quyền đọc hồ sơ "
            "nhân sự không.")


def sync_pic(api: WorkApi, task: dict, entry: JournalEntry,
             people: PeopleDirectory, dry: bool, indent: str = "") -> None:
    """Gán người phụ trách cho một task theo `- pic:` của mục.

    Mục không khai người nào thì KHÔNG đụng tới danh sách đang có trên ERP —
    sổ chỉ sở hữu những gì sổ nói ra.
    """
    if not entry.pic_codes:
        return
    want = sorted({people.id_of(c) for c in entry.pic_codes} - {0})
    have = sorted({int(a.get("employee_id") or 0)
                   for a in (task.get("assignees") or [])
                   if int(a.get("kind") or 1) == 1} - {0})
    if want == have:
        return
    if dry:
        print(f"[dry-run] {indent}sẽ gán [{entry.key}] cho "
              + ", ".join(entry.pic_codes))
        return
    api.call("PUT", f"/api/work/tasks/{task['id']}/assignees",
             {"pic_ids": want, "follower_ids": []})
    print(f"{indent}@ [{entry.key}] giao cho " + ", ".join(entry.pic_codes))


#  bao-CR-482: dự án mà sổ tự tạo phải nằm TRONG nhóm cha (mặc định «DX»), không đứng
#  lẻ — «Nhật ký hệ thống» từng sinh ra ngoài nhóm nên màn liệt kê và cây bên trái
#  không xếp nó cùng chỗ với các dự án khác. Đặt `WORK_SYNC_GROUP=` (rỗng) để tắt.
DEFAULT_GROUP_NAME = "DX"


def find_group_id(api: WorkApi, name: str) -> int | None:
    """Id nhóm theo TÊN (nhóm cấp 1 rồi tới nhóm con); không thấy thì `None`."""
    if not name:
        return None
    tree = api.call("GET", "/api/work/groups") or {}
    stack = list(tree.get("groups") or [])
    while stack:
        g = stack.pop(0)
        if (g.get("name") or "").strip().lower() == name.strip().lower():
            return int(g["id"])
        stack.extend(g.get("children") or [])
    return None


def ensure_list(api: WorkApi, name: str, dry: bool) -> int:
    lists = api.call("GET", "/api/work/lists") or []
    #  Trùng tên thì ưu tiên dự án NẰM TRONG NHÓM — «Nhật ký hệ thống» trên dev từng có
    #  một bản đứng ngoài nhóm (sinh trước bao-CR-482) cạnh bản trong «DX».
    same = [row for row in lists if row.get("name") == name]
    for row in sorted(same, key=lambda r: (not r.get("group_id"), int(r["id"]))):
        return int(row["id"])
    group_name = os.environ.get("WORK_SYNC_GROUP", DEFAULT_GROUP_NAME)
    group_id = find_group_id(api, group_name)
    if group_name and not group_id and not dry:
        #  bao-CR-604: prod chưa có nhóm «DX» — tạo luôn, kẻo dự án đứng lẻ ngoài cây.
        created = api.call("POST", "/api/work/groups", {"name": group_name})
        group_id = int(created["id"])
        print(f"+ tạo nhóm '{group_name}' (id {group_id})")
    if dry:
        print(f"[dry-run] sẽ tạo dự án '{name}'"
              + (f" trong nhóm '{group_name}'" if group_id else f" (và nhóm '{group_name}')" if group_name else " (đứng ngoài nhóm)"))
        return 0
    body = {"name": name,
            "description": "Sổ task đồng bộ từ nhat-ky-task.md — đừng sửa mô tả task bằng tay."}
    if group_id:
        body["group_id"] = group_id
    created = api.call("POST", "/api/work/lists", body)
    print(f"+ tạo dự án '{name}' (id {created['id']})"
          + (f" trong nhóm '{group_name}'" if group_id else ""))
    return int(created["id"])


def ensure_sections(api: WorkApi, list_id: int, names: set[str], dry: bool) -> dict[str, int]:
    board = api.call("GET", f"/api/work/lists/{list_id}/board")
    have = {s["name"]: int(s["id"]) for s in board.get("sections", [])}
    for name in names:
        if name in have:
            continue
        if dry:
            print(f"[dry-run] sẽ tạo cột '{name}'")
            continue
        created = api.call("POST", f"/api/work/lists/{list_id}/sections", {"name": name})
        have[name] = int(created["id"])
        print(f"+ tạo cột '{name}'")
    return have


def ensure_tag_options(api: WorkApi, list_id: int, names: set[str], dry: bool) -> tuple[int, dict[str, int]]:
    """Trường «Tag» (chọn nhiều) của list + id từng giá trị cần có; thiếu thì tạo.
    Trả `(field_id, {tên: option_id})`; `field_id = 0` khi dry-run chưa có trường."""
    if not names:
        return 0, {}
    fields = api.call("GET", f"/api/work/lists/{list_id}/label-fields") or []
    tag = next((f for f in fields
                if (f.get("name") or "").strip().lower() == TAG_FIELD_NAME.lower()
                and int(f.get("field_type") or 1) == 2), None)
    if tag is None:
        if dry:
            print(f"[dry-run] sẽ tạo trường '{TAG_FIELD_NAME}' (chọn nhiều) cho list {list_id}")
            return 0, {}
        tag = api.call("POST", f"/api/work/lists/{list_id}/label-fields",
                       {"name": TAG_FIELD_NAME, "field_type": 2})
        tag["options"] = []
        print(f"+ tạo trường '{TAG_FIELD_NAME}' (chọn nhiều)")
    opts = {(o.get("name") or "").strip().lower(): int(o["id"]) for o in tag.get("options") or []}
    out: dict[str, int] = {}
    for name in sorted(names):
        oid = opts.get(name.lower())
        if oid is None:
            if dry:
                print(f"[dry-run] sẽ thêm giá trị tag '{name}'")
                continue
            created = api.call("POST", f"/api/work/label-fields/{tag['id']}/options", {"name": name})
            oid = int(created["id"])
            print(f"+ thêm giá trị tag '{name}'")
        out[name] = oid
    return int(tag["id"]), out


def sync_tags(api: WorkApi, task: dict, entry: JournalEntry, field_id: int,
              option_ids: dict[str, int], dry: bool, indent: str = "") -> None:
    """Gán tag cho task — CỘNG THÊM vào giá trị đang có, không gỡ tag người dùng tự gán."""
    want = {option_ids[n] for n in entry.tag_names if n in option_ids}
    if not want or not field_id:
        return
    have = {int(lb.get("option_id") or 0) for lb in (task.get("labels") or [])
            if int(lb.get("field_id") or 0) == field_id}
    if want <= have:
        return
    if dry:
        print(f"[dry-run] {indent}sẽ gán tag [{entry.key}]: " + ", ".join(entry.tag_names))
        return
    api.call("PUT", f"/api/work/tasks/{task['id']}/label",
             {"field_id": field_id, "value": sorted(have | want)})
    print(f"{indent}# [{entry.key}] tag " + ", ".join(entry.tag_names))


def _key_of(title: str) -> str:
    return title.split(" — ", 1)[0] if " — " in title else title


def sync_children(api: WorkApi, parent_id: int, parent: JournalEntry,
                  people: PeopleDirectory, dry: bool) -> None:
    """Upsert việc con của một mục `##`. Việc con không có cột kanban (C-05),
    nên chỉ so tiêu đề / mô tả / trạng thái / ngày bắt đầu."""
    if not parent.children:
        return
    detail = api.call("GET", f"/api/work/tasks/{parent_id}")
    by_key: dict[str, dict] = {}
    for t in detail.get("subtasks") or []:
        by_key.setdefault(_key_of(t.get("title", "")), t)

    for c in parent.children:
        old = by_key.get(c.key)
        if old is None:
            if dry:
                print(f"[dry-run]   sẽ tạo việc con [{c.key}] của [{parent.key}]")
                continue
            created = api.call("POST", f"/api/work/tasks/{parent_id}/subtasks", {
                "title": c.display_title,
                "description": c.description,
                "start_date": c.start_date,
            })
            if c.task_status != 1:
                api.call("PATCH", f"/api/work/tasks/{created['id']}",
                         {"status": c.task_status})
            print(f"  + con [{c.key}] của [{parent.key}]")
            sync_pic(api, created, c, people, dry, indent="  ")
            continue
        patch: dict = {}
        if old.get("title") != c.display_title:
            patch["title"] = c.display_title
        if (old.get("description") or "") != c.description:
            patch["description"] = c.description
        if old.get("status") != c.task_status:
            patch["status"] = c.task_status
        if c.start_date and (old.get("start_date") or "") != c.start_date:
            patch["start_date"] = c.start_date
        if not patch:
            print(f"  = con [{c.key}] không đổi")
        elif dry:
            print(f"[dry-run]   sẽ cập nhật việc con [{c.key}]: {', '.join(patch)}")
        else:
            api.call("PATCH", f"/api/work/tasks/{old['id']}", patch)
            print(f"  ~ con [{c.key}]: {', '.join(patch)}")
        sync_pic(api, old, c, people, dry, indent="  ")


def index_all_tasks(api: WorkApi) -> dict[str, tuple[int, str, dict]]:
    """`{key: (list_id, tên list, task)}` của MỌI dự án — để biết một mục đang nằm
    ở dự án khác (bao-CR-604) chứ không tạo thêm bản nữa."""
    out: dict[str, tuple[int, str, dict]] = {}
    for row in api.call("GET", "/api/work/lists") or []:
        board = api.call("GET", f"/api/work/lists/{row['id']}/board") or {}
        for t in board.get("tasks", []):
            out.setdefault(_key_of(t.get("title", "")), (int(row["id"]), row.get("name") or "", t))
    return out


def sync(api: WorkApi, list_id: int, entries: list[JournalEntry],
         people: PeopleDirectory, dry: bool,
         elsewhere: dict[str, tuple[int, str, dict]] | None = None,
         move: bool = False) -> None:
    sections = ensure_sections(api, list_id, {e.section_name for e in entries}, dry)
    board = api.call("GET", f"/api/work/lists/{list_id}/board") if list_id else {"tasks": []}
    #  Khớp theo tiền tố "key — " để đổi TIÊU ĐỀ trong sổ không đẻ task mới.
    by_key: dict[str, dict] = {}
    for t in board.get("tasks", []):
        by_key.setdefault(_key_of(t.get("title", "")), t)
    tag_field, tag_opts = ensure_tag_options(
        api, list_id, {n for e in entries for n in e.tag_names}, dry) if list_id else (0, {})

    for e in entries:
        target_section = sections.get(e.section_name, 0)
        old = by_key.get(e.key)
        if old is None and elsewhere and e.key in elsewhere and elsewhere[e.key][0] != list_id:
            other_list_id, other_name, other_task = elsewhere[e.key]
            if not move:
                print(f"! [{e.key}] đang ở dự án '{other_name}' — giữ nguyên "
                      f"(chạy --move để chuyển sang đây)")
                continue
            if dry:
                print(f"[dry-run] sẽ chuyển [{e.key}] từ '{other_name}' sang đây (xóa chỗ cũ, tạo lại)")
                continue
            api.call("DELETE", f"/api/work/tasks/{other_task['id']}")
            print(f"- [{e.key}] bỏ khỏi '{other_name}' (vào thùng rác), tạo lại ở dự án này")
        if old is None:
            if dry:
                print(f"[dry-run] sẽ tạo task [{e.key}] '{e.display_title}'")
                for c in e.children:
                    print(f"[dry-run]   sẽ tạo việc con [{c.key}] của [{e.key}]")
                continue
            created = api.call("POST", "/api/work/tasks", {
                "list_id": list_id,
                "section_id": target_section or None,
                "title": e.display_title,
                "description": e.description,
                "start_date": e.start_date,
            })
            if e.task_status != 1:
                api.call("PATCH", f"/api/work/tasks/{created['id']}",
                         {"status": e.task_status})
            print(f"+ tạo [{e.key}] ({e.section_name})")
            sync_pic(api, created, e, people, dry)
            sync_tags(api, created, e, tag_field, tag_opts, dry)
            sync_children(api, int(created["id"]), e, people, dry)
            continue

        patch: dict = {}
        if old.get("title") != e.display_title:
            patch["title"] = e.display_title
        if (old.get("description") or "") != e.description:
            patch["description"] = e.description
        if target_section and old.get("section_id") != target_section:
            patch["section_id"] = target_section
        if old.get("status") != e.task_status:
            patch["status"] = e.task_status
        if e.start_date and (old.get("start_date") or "") != e.start_date:
            patch["start_date"] = e.start_date
        if not patch:
            print(f"= [{e.key}] không đổi")
        elif dry:
            print(f"[dry-run] sẽ cập nhật [{e.key}]: {', '.join(patch)}")
        else:
            api.call("PATCH", f"/api/work/tasks/{old['id']}", patch)
            print(f"~ cập nhật [{e.key}]: {', '.join(patch)}")
        sync_pic(api, old, e, people, dry)
        sync_tags(api, old, e, tag_field, tag_opts, dry)
        sync_children(api, int(old["id"]), e, people, dry)


def load_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    out = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip()
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Đồng bộ nhat-ky-task.md lên phân hệ Dự án")
    ap.add_argument("--journal", default=str(DEFAULT_JOURNAL))
    ap.add_argument("--env-file", default=str(DEFAULT_ENV_FILE))
    ap.add_argument("--base-url")
    ap.add_argument("--username")
    ap.add_argument("--password")
    ap.add_argument("--list-name")
    ap.add_argument("--pic", help="Mã nhân sự nhận mọi task chưa khai `- pic:`")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--move", action="store_true",
                    help="Mục đã có ở dự án khác thì xóa chỗ cũ (thùng rác) rồi tạo ở dự án đúng")
    args = ap.parse_args()

    env = {**load_env_file(Path(args.env_file)), **{
        k: v for k, v in os.environ.items() if k.startswith("WORK_SYNC_")}}
    base_url = args.base_url or env.get("WORK_SYNC_BASE_URL", "http://localhost:8000")
    username = args.username or env.get("WORK_SYNC_USER", "")
    password = args.password or env.get("WORK_SYNC_PASS", "")
    list_name = args.list_name or env.get("WORK_SYNC_LIST", DEFAULT_LIST_NAME)
    default_pics = [c.strip().upper() for c in re.split(
        r"[,;]", args.pic or env.get("WORK_SYNC_PIC", "")) if c.strip()]
    if not username or not password:
        raise SystemExit("Thiếu tài khoản: đặt WORK_SYNC_USER/WORK_SYNC_PASS "
                         f"(trong {args.env_file}) hoặc --username/--password")

    journal = Path(args.journal)
    if not journal.exists():
        raise SystemExit(f"Không thấy sổ: {journal}")
    entries = parse_journal(journal)
    if not entries:
        print("Sổ chưa có mục nào — không có gì để đồng bộ.")
        return

    #  bao-CR-604: người phụ trách + tag theo TIỀN TỐ key, chia dự án theo từ khóa.
    pic_by_prefix = parse_map(env.get("WORK_SYNC_PIC_BY_PREFIX", ""), DEFAULT_PIC_BY_PREFIX)
    tag_by_prefix = parse_map(env.get("WORK_SYNC_TAG_BY_PREFIX", ""), DEFAULT_TAG_BY_PREFIX)
    route = env.get("WORK_SYNC_ROUTE", "1").strip() != "0"
    #  Người phụ trách: mục nào không khai `- pic:` thì theo tiền tố, rồi tới người
    #  mặc định; việc con đi theo mục cha của nó.
    for e in entries:
        prefix = key_prefix(e.key)
        if not e.pic_codes and prefix in pic_by_prefix:
            e.pic_codes = [pic_by_prefix[prefix].upper()]
        e.pic_codes = e.pic_codes or default_pics
        if prefix in tag_by_prefix and tag_by_prefix[prefix] not in e.tag_names:
            e.tag_names.append(tag_by_prefix[prefix])
        if route and not e.list_name:
            e.list_name = route_list(e)
        for c in e.children:
            c.pic_codes = c.pic_codes or e.pic_codes

    #  Gom mục theo task list đích (`- list:`; rỗng = list mặc định) —
    #  giữ thứ tự xuất hiện trong sổ.
    by_list: dict[str, list[JournalEntry]] = {}
    for e in entries:
        by_list.setdefault(e.list_name or list_name, []).append(e)
    print(f"Sổ có {len(entries)} mục / {len(by_list)} task list; đích: {base_url}")

    api = WorkApi(base_url)
    api.login(username, password)
    people = PeopleDirectory(api)
    try:
        if default_pics:
            print("Người phụ trách mặc định: " + ", ".join(default_pics))
        elsewhere = index_all_tasks(api)
        for name, group_entries in by_list.items():
            print(f"-- list '{name}' ({len(group_entries)} mục)")
            list_id = ensure_list(api, name, args.dry_run)
            if not list_id and args.dry_run:
                for e in group_entries:
                    if e.key in elsewhere:
                        print(f"[dry-run] [{e.key}] đang ở '{elsewhere[e.key][1]}'"
                              + (" — sẽ chuyển" if args.move else " — giữ nguyên (cần --move)"))
                    else:
                        print(f"[dry-run] sẽ tạo task [{e.key}] '{e.display_title}'")
                continue
            sync(api, list_id, group_entries, people, args.dry_run, elsewhere, args.move)
    finally:
        #  Kể cả dry-run hay lỗi giữa chừng: phiên mở ra thì phải đóng lại.
        api.logout()
    print("Xong.")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
