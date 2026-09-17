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

`WORK_SYNC_PIC` là mã nhân sự nhận mọi task của sổ (mục nào khai `- pic:` riêng
thì theo mục đó). Để trống thì script không đụng tới người phụ trách.
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


def ensure_list(api: WorkApi, name: str, dry: bool) -> int:
    lists = api.call("GET", "/api/work/lists") or []
    for row in lists:
        if row.get("name") == name:
            return int(row["id"])
    if dry:
        print(f"[dry-run] sẽ tạo dự án '{name}'")
        return 0
    created = api.call("POST", "/api/work/lists",
                       {"name": name,
                        "description": "Sổ task đồng bộ từ nhat-ky-task.md — "
                                       "đừng sửa mô tả task bằng tay."})
    print(f"+ tạo dự án '{name}' (id {created['id']})")
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


def sync(api: WorkApi, list_id: int, entries: list[JournalEntry],
         people: PeopleDirectory, dry: bool) -> None:
    sections = ensure_sections(api, list_id, {e.section_name for e in entries}, dry)
    board = api.call("GET", f"/api/work/lists/{list_id}/board") if list_id else {"tasks": []}
    #  Khớp theo tiền tố "key — " để đổi TIÊU ĐỀ trong sổ không đẻ task mới.
    by_key: dict[str, dict] = {}
    for t in board.get("tasks", []):
        by_key.setdefault(_key_of(t.get("title", "")), t)

    for e in entries:
        target_section = sections.get(e.section_name, 0)
        old = by_key.get(e.key)
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

    #  Người phụ trách: mục nào không khai `- pic:` thì lấy người mặc định,
    #  và việc con đi theo mục cha của nó.
    for e in entries:
        e.pic_codes = e.pic_codes or default_pics
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
        for name, group_entries in by_list.items():
            print(f"-- list '{name}' ({len(group_entries)} mục)")
            list_id = ensure_list(api, name, args.dry_run)
            if not list_id and args.dry_run:
                for e in group_entries:
                    print(f"[dry-run] sẽ tạo task [{e.key}] '{e.display_title}'")
                continue
            sync(api, list_id, group_entries, people, args.dry_run)
    finally:
        #  Kể cả dry-run hay lỗi giữa chừng: phiên mở ra thì phải đóng lại.
        api.logout()
    print("Xong.")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
