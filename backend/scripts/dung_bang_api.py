# -*- coding: utf-8 -*-
"""Dựng lại bảng mục 1 của mọi `doc/erp/<phan-he>/tai-lieu-ky-thuat/api.md` từ mã (td-0311, 05/11/2026).

Chạy lại bao nhiêu lần cũng được (idempotent). Cần nạp được `app.main` nên chạy trong ảnh api, gắn cả kho mã vào:

    docker run --rm -e PYTHONPATH=/app -v <kho>/backend:/app -v <kho>:/repo -w /app procurement-tool-api:latest \\
        python scripts/dung_bang_api.py --repo /repo            # ghi thẳng các api.md
    ... python scripts/dung_bang_api.py --repo /repo --kiem     # chỉ báo tệp nào lệch, không ghi (exit 1 nếu lệch)

Phân hệ nhận đường nào: đọc dòng ``Mã backend:`` ở đầu từng api.md (tên gói `app.modules.<x>` và các tiền tố dựng bằng
`make_crud_router`). Đường không thuộc phân hệ nào được in ra cuối để người viết tài liệu gán.

Cột nào lấy từ đâu:
- *Mục đích*: dòng đầu docstring của hàm đường (hay `summary`). Không có thì giữ chữ đang ghi tay; chưa có gì thì tên hàm.
  Muốn đổi câu thì sửa docstring trong mã, đừng sửa tay ở đây (lần chạy sau sẽ ghi đè).
- *Quyền*: `require(entity, action)` và `require_report` gắn trên đường; chỉ có `get_current_user` thì ghi *đăng nhập*;
  không gác gì thì *công khai*.
- *Phạm vi*: ghi tay được giữ nguyên; trống thì tự điền khi thấy `apply_scope` / `get_scoped` / `scope_condition` trong
  thân hàm đường (trống vẫn nghĩa là **chưa soát** — có thể lọc ở tầng dịch vụ).
- *Ai gọi*: ghi tay được giữ nguyên; trống hoặc đang mang tiền tố *tự dò:* thì dò lại từ `frontend-v2/src` (thay hằng
  `const X = '/api/...'` trong cùng tệp rồi so mẫu đường) và từ cổng MCP (`agent_hub/mcp.py`, `assistant/tools`).
"""
import argparse
import glob
import inspect
import io
import os
import re
import sys
from collections import defaultdict
from datetime import date

AUTO = "tự dò: "
SCOPE_TOKENS = ("apply_scope", "get_scoped", "scope_condition")
METHOD_ORDER = {"GET": 0, "POST": 1, "PUT": 2, "PATCH": 3, "DELETE": 4}
HEADER = "| Phương thức | Đường | Mục đích | Quyền (`entity.action`) | Phạm vi | Ai gọi |"
NOTE_RE = re.compile(r"^> Bảng mục 1 dựng TỰ ĐỘNG.*$", re.M)
NOTE = ("> Bảng mục 1 dựng TỰ ĐỘNG từ `app.routes` bằng `backend/scripts/dung_bang_api.py` (lần cuối {d}): *Mục đích* = "
        "dòng đầu docstring (không có thì tên hàm — sửa docstring trong mã, đừng sửa tay); *Quyền* = `require(entity, "
        "action)` / `require_report` gắn trên đường; *Phạm vi* và *Ai gọi* ghi tay được giữ, chữ *tự dò:* là máy dò từ "
        "frontend-v2 và cổng MCP. *Phạm vi* trống nghĩa là **chưa soát** (có thể lọc ở service).")


def _norm(path: str) -> str:
    return re.sub(r"\{[^}]+\}", "{}", path.rstrip("/")) or "/"


def _cell(text: str) -> str:
    return " ".join(str(text).replace("|", "\\|").split())


# ── Đọc mã ──────────────────────────────────────────────────────────────────────────────────────────────────────────

def _deps(dependant, seen=None):
    seen = seen if seen is not None else set()
    for sub in dependant.dependencies:
        if id(sub) in seen:
            continue
        seen.add(id(sub))
        yield sub.call
        yield from _deps(sub, seen)


def _permission(route) -> str:
    from app.core.auth import get_current_user

    perms, login = [], False
    for call in _deps(route.dependant):
        if call is None:
            continue
        key = getattr(call, "report_key", None)
        if key is not None:
            perms.append(f"`báo cáo {int(key)}`")
            continue
        if call is get_current_user:
            login = True
            continue
        if inspect.isfunction(call):
            nl = inspect.getclosurevars(call).nonlocals
            if isinstance(nl.get("entity"), str) and isinstance(nl.get("action"), str):
                perms.append(f"`{nl['entity']}.{nl['action']}`")
    perms = list(dict.fromkeys(perms))
    if perms:
        return ", ".join(perms)
    return "đăng nhập" if login else "công khai"


def _scope(endpoint) -> str:
    try:
        src = inspect.getsource(endpoint)
    except (OSError, TypeError):
        return ""
    return ", ".join(f"`{t}`" for t in SCOPE_TOKENS if t + "(" in src)


def _purpose(route) -> tuple[str, str]:
    """(câu mô tả, dòng đầu thô). Câu mô tả = câu đầu của đoạn đầu docstring (docstring hay xuống dòng giữa câu).
    Dòng đầu thô là thứ bản dựng 03/11 đã ghi — dùng để nhận ra ô nào là chữ máy, ô nào là chữ người viết tay."""
    doc = inspect.cleandoc(route.endpoint.__doc__ or "") or (route.summary or "")
    if not doc:
        return "", ""
    para = " ".join(doc.split("\n\n")[0].split())
    first = re.split(r"(?<=[.!?])\s+(?=[A-ZĐÀ-Ỹ`(])", para)[0]
    if len(first) > 220:
        first = first[:217].rsplit(" ", 1)[0] + "…"
    return _cell(first), _cell(doc.split("\n")[0])


def collect_routes():
    from app.core.route_iter import iter_api_routes
    from app.main import app

    out = []
    for r in iter_api_routes(app):
        ep = r.endpoint
        for m in sorted((r.methods or set()) - {"HEAD", "OPTIONS"}):
            out.append({
                "module": ep.__module__, "path": r.path, "method": m, "name": ep.__name__,
                "purpose": _purpose(r)[0], "purpose_raw": _purpose(r)[1], "perm": _permission(r), "scope": _scope(ep),
            })
    return out


# ── Dò ai gọi ───────────────────────────────────────────────────────────────────────────────────────────────────────

STR_RE = re.compile(r"[`'\"]((?:/api/|\$\{[A-Za-z_][A-Za-z0-9_]*\})[^`'\"\s]*)[`'\"]")
CONST_RE = re.compile(r"const\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*[`'\"](/api/[^`'\"$\s]*)[`'\"]")


def frontend_callers(repo: str) -> dict:
    """{đường chuẩn hóa: {nhóm gọi}} — nhóm là tên phân hệ v2 (`src/modules/<x>`) hay *dùng chung*."""
    found = defaultdict(set)
    root = os.path.join(repo, "frontend-v2", "src")
    for f in glob.glob(os.path.join(root, "**", "*.ts*"), recursive=True):
        if re.search(r"\.(test|spec)\.tsx?$", f):
            continue
        src = io.open(f, encoding="utf-8").read()
        if "/api/" not in src:
            continue
        rel = os.path.relpath(f, root).replace("\\", "/").split("/")
        who = f"v2 `{rel[1]}`" if rel[0] == "modules" and len(rel) > 2 else "v2 dùng chung"
        consts = dict(CONST_RE.findall(src))
        for raw in STR_RE.findall(src):
            for name, val in consts.items():
                raw = raw.replace("${" + name + "}", val)
            if not raw.startswith("/api/"):
                continue
            raw = raw.split("?")[0].split("${qs")[0]
            path = re.sub(r"\$\{[^}]*\}", "{}", raw)
            path = re.sub(r"\{\}\{\}", "{}", path)
            found[_norm(path)].add(who)
    return found


def mcp_callers(repo: str) -> set:
    paths = set()
    for f in [os.path.join(repo, "backend/app/modules/agent_hub/mcp.py"),
              *glob.glob(os.path.join(repo, "backend/app/modules/assistant/tools/*.py"))]:
        if os.path.exists(f):
            for p in re.findall(r"[\"'](/api/[^\"'\s]+)[\"']", io.open(f, encoding="utf-8").read()):
                paths.add(_norm(re.sub(r"\{[^}]*\}", "{}", p)))
    return paths


# ── Ghi tài liệu ────────────────────────────────────────────────────────────────────────────────────────────────────

def _owners(api_md: str):
    m = re.search(r"^Mã backend:(.*)$", api_md, re.M)
    if not m or "chưa có" in m.group(1):
        return set(), []
    line = m.group(1)
    crud = []
    if "make_crud_router" in line:
        line, tail = line.split("make_crud_router", 1)
        crud = re.findall(r"`(/api/[^`]+)`", tail)
    return set(re.findall(r"`([a-z_0-9]+)`", line)), crud


def _belongs(route, mods, crud) -> bool:
    mod = route["module"]
    if mod.startswith("app.modules."):
        return mod.split(".")[2] in mods
    if mod == "app.core.crud":
        return any(route["path"] == p or route["path"].startswith(p + "/") for p in crud)
    return False


def _old_rows(api_md: str) -> dict:
    rows = {}
    for line in api_md.split("\n"):
        if re.match(r"^\| *(GET|POST|PUT|PATCH|DELETE) ", line):
            c = [x.strip() for x in re.split(r"(?<!\\)\|", line)[1:-1]]
            if len(c) >= 6:
                rows[(c[0], c[1].strip("`"))] = c
    return rows


def build_table(routes, old: dict, fe: dict, mcp: set) -> list:
    lines = [HEADER, "|---|---|---|---|---|---|"]
    for r in sorted(routes, key=lambda x: (x["path"], METHOD_ORDER.get(x["method"], 9))):
        prev = old.get((r["method"], r["path"]))
        fallback = r["name"].replace("_", " ")
        prev_purpose = prev[2] if prev else ""
        #  Có docstring thì docstring thắng (mã là nguồn sự thật, sửa docstring là bảng tự theo). Chưa có docstring thì
        #  giữ câu đang ghi tay; không có gì thì tên hàm. Chi tiết dài (tham số, CR) ghi ở mục 2 của api.md.
        purpose = r["purpose"] or (prev_purpose if prev_purpose and prev_purpose != fallback else fallback)
        prev_scope = prev[4] if prev else ""
        auto_scope = re.fullmatch(r"(`(%s)`(, )?)+" % "|".join(SCOPE_TOKENS), prev_scope or "-")
        scope = prev_scope if prev_scope and not auto_scope else r["scope"]
        caller_manual = prev[5] if prev and prev[5] and not prev[5].startswith(AUTO.strip()) else ""
        if caller_manual:
            caller = caller_manual
        else:
            who = sorted(fe.get(_norm(r["path"]), set()))
            if _norm(r["path"]) in mcp:
                who.append("cổng MCP")
            caller = AUTO + ", ".join(who) if who else ""
        lines.append(f"| {r['method']} | `{r['path']}` | {purpose} | {r['perm']} | {scope} | {caller} |")
    return lines


def rewrite(api_md: str, table: list) -> str:
    start = api_md.index("## 1. Bảng đường API")
    head_i = api_md.index(HEADER, start)
    nxt = api_md.find("\n## ", head_i)
    end = nxt if nxt != -1 else len(api_md)
    body = api_md[head_i:end]
    tail_lines = body.split("\n")
    i = 0
    while i < len(tail_lines) and tail_lines[i].startswith("|"):
        i += 1
    rest = "\n".join(tail_lines[i:])
    return api_md[:head_i] + "\n".join(table) + ("\n" + rest if rest else "\n") + api_md[end:]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--repo", required=True, help="gốc kho mã (thư mục chứa doc/, frontend-v2/)")
    ap.add_argument("--kiem", action="store_true", help="chỉ báo lệch, không ghi")
    a = ap.parse_args()
    routes = collect_routes()
    fe, mcp = frontend_callers(a.repo), mcp_callers(a.repo)
    claimed, changed = set(), []
    today = date.today().strftime("%d/%m/%Y")
    for f in sorted(glob.glob(os.path.join(a.repo, "doc", "erp", "*", "tai-lieu-ky-thuat", "api.md"))):
        s = io.open(f, encoding="utf-8").read()
        mods, crud = _owners(s)
        if not mods and not crud or "## 1. Bảng đường API" not in s or HEADER not in s:
            continue
        mine = [r for r in routes if _belongs(r, mods, crud)]
        claimed.update(id(r) for r in mine)
        new = rewrite(s, build_table(mine, _old_rows(s), fe, mcp))
        old_note = NOTE_RE.search(s)
        #  Ngày trong ghi chú chỉ đổi khi bảng đổi — chạy lại khi mã không đổi thì tệp giữ y nguyên.
        if old_note and (new != s or "dung_bang_api.py" not in old_note.group(0)):
            new = NOTE_RE.sub(lambda _m: NOTE.format(d=today), new, count=1)
        if new != s:
            changed.append(os.path.relpath(f, a.repo))
            if not a.kiem:
                io.open(f, "w", encoding="utf-8", newline="\n").write(new)
    orphan = sorted({(r["module"], r["path"]) for r in routes if id(r) not in claimed})
    verb = "lệch" if a.kiem else "đã ghi"
    print(f"{len(routes)} cặp phương thức + đường; {verb} {len(changed)} tệp api.md")
    for c in changed:
        print("  ", c)
    if orphan:
        print(f"{len(orphan)} đường chưa thuộc phân hệ nào (thêm gói vào dòng Mã backend: của api.md tương ứng):")
        for mod, p in orphan:
            print(f"   {mod:40s} {p}")
    return 1 if a.kiem and changed else 0


if __name__ == "__main__":
    sys.exit(main())
