"""BOT SỬA MÃ ĐƯỢC ĐỔI CẤU TRÚC DB — có trình bày, đại ca duyệt (ai-CR-076).

Đại ca chốt 05/10/2026: *"làm tính năng thì buộc nhiều khi cũng phải thêm xóa sửa cấu trúc db, thì nó trình bày, a duyệt
thì lên thôi không sao"*. Luật C3 cũ («không tự sinh migration, dừng và leo thang») đổi thành: được viết migration, nhưng

  1. Đề bài cho Claude ghi sẵn ĐẦU migration hiện tại của nhánh nền → `down_revision` phải nối đúng vào đó.
  2. Cổng kiểm: tệp migration phải dịch được (cú pháp) và cả kho chỉ còn ĐÚNG MỘT đầu. Hai đầu = đỏ (vụ dev sập 25/09
     chính là hai nhánh cùng đẻ migration).
  3. Thẻ kết quả có mục «CÓ ĐỔI CẤU TRÚC DB» liệt kê từng thay đổi; thay đổi làm mất dữ liệu (xóa bảng/cột, đổi kiểu,
     đổi tên, chạy SQL tay) in đậm kèm cảnh báo. Đại ca đọc rồi mới «gộp».
  4. Lúc gộp: kiểm lại một đầu SAU khi gộp vào nhánh nền (có thể ai đó vừa đẩy migration khác) — hai đầu thì không đẩy.
  5. Trước khi deploy dev bản có migration: sao lưu CẢ DB dev; sao lưu hỏng thì không deploy.

Đọc tệp migration bằng biểu thức chính quy, KHÔNG import (không chạy mã bot vừa viết trong tiến trình runner).
"""
from __future__ import annotations

import re
from pathlib import Path

MIGRATIONS_DIR = "backend/migrations/versions"

_REV = re.compile(r"^\s*revision\s*(?::[^=\n]+)?=\s*['\"]([^'\"]+)['\"]", re.MULTILINE)
_DOWN = re.compile(r"^\s*down_revision\s*(?::[^=\n]+)?=\s*(\([^)]*\)|[^\n]+)", re.MULTILINE)
_UPGRADE = re.compile(r"def upgrade\(\)[^:]*:(.*?)(?=^def |\Z)", re.MULTILINE | re.DOTALL)
_OP_START = re.compile(r"\bop\.(\w+)\(")
_FIRST_ARG = re.compile(r"\s*(?:op\.f\()?\s*['\"]([A-Za-z0-9_]*)['\"]\)?\s*,?\s*")
_COL_NAME = re.compile(r"sa\.Column\(\s*['\"]([A-Za-z0-9_]+)['\"]")
_COL_ARG = re.compile(r"^\s*['\"]([A-Za-z0-9_]+)['\"]")

#  (tên lệnh alembic, nhãn tiếng Việt, mất dữ liệu?)
_OPS = {
    "create_table": ("tạo bảng", False),
    "add_column": ("thêm cột", False),
    "create_index": ("thêm chỉ mục", False),
    "bulk_insert": ("nạp dữ liệu vào bảng", False),
    "create_unique_constraint": ("thêm ràng buộc duy nhất", False),
    "create_foreign_key": ("thêm khóa ngoại", False),
    "drop_index": ("bỏ chỉ mục", False),
    "drop_table": ("XÓA BẢNG", True),
    "drop_column": ("XÓA CỘT", True),
    "alter_column": ("ĐỔI CỘT", True),
    "rename_table": ("ĐỔI TÊN BẢNG", True),
    "execute": ("CHẠY SQL TAY", True),
    "drop_constraint": ("bỏ ràng buộc", False),
}


def is_migration(path: str) -> bool:
    return path.startswith(MIGRATIONS_DIR + "/") and path.endswith(".py")


def migration_heads(root: str) -> list[str]:
    """Các revision không bị revision nào khác trỏ làm `down_revision` = các ĐẦU. Đúng ra chỉ có một."""
    vdir = Path(root) / MIGRATIONS_DIR
    revs: set[str] = set()
    downs: set[str] = set()
    for f in vdir.glob("*.py"):
        text = f.read_text(encoding="utf-8", errors="replace")
        m = _REV.search(text)
        if not m:
            continue
        revs.add(m.group(1))
        d = _DOWN.search(text)
        if d:
            downs.update(re.findall(r"['\"]([^'\"]+)['\"]", d.group(1)))
    return sorted(revs - downs)


def summarize(text: str) -> list[dict]:
    """Thay đổi trong `upgrade()` của một tệp migration → [{label, target, destructive}]."""
    body = _UPGRADE.search(text or "")
    if not body:
        return []
    out = []
    src = body.group(1)
    starts = list(_OP_START.finditer(src))
    for i, m in enumerate(starts):
        name = m.group(1)
        if name not in _OPS:
            continue
        #  Đọc từ sau «op.x(» tới lệnh op kế tiếp — không để lệnh này nuốt mất lệnh sau.
        seg = src[m.end():starts[i + 1].start() if i + 1 < len(starts) else len(src)]
        fa = _FIRST_ARG.match(seg)
        first = fa.group(1) if fa else ""
        rest = seg[fa.end():] if fa else seg
        label, destructive = _OPS[name]
        target = first
        if name == "add_column":
            col = _COL_NAME.search(rest)
            target = f"{first}.{col.group(1)}" if col else first
        elif name in ("drop_column", "alter_column"):
            col = _COL_ARG.match(rest)
            target = f"{first}.{col.group(1)}" if col else first
        elif name == "create_index":
            tbl = _COL_ARG.match(rest)
            target = f"{first} trên {tbl.group(1)}" if tbl else first
        out.append({"label": label, "target": target or "(xem tệp migration)", "destructive": destructive})
    return out


def check(worktree: str, touched: list[str]) -> dict:
    """Phần migration của cổng kiểm. {status: none|pass|fail, files: [{path, changes}], heads, output}."""
    files = [p for p in touched if is_migration(p)]
    if not files:
        return {"status": "none", "files": [], "heads": [], "output": ""}
    problems: list[str] = []
    found = []
    for p in files:
        path = Path(worktree) / p
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue          # tệp bị xóa trong bản vá — chỉ đếm đầu
        try:
            compile(text, p, "exec")
        except SyntaxError as e:
            problems.append(f"{p}: lỗi cú pháp dòng {e.lineno}: {e.msg}")
        if not _REV.search(text) or not _DOWN.search(text):
            problems.append(f"{p}: thiếu `revision` hoặc `down_revision`")
        found.append({"path": p, "changes": summarize(text)})
    heads = migration_heads(worktree)
    if len(heads) != 1:
        problems.append(f"kho có {len(heads)} đầu migration ({', '.join(heads) or 'không có'}) — phải đúng MỘT: "
                        "`down_revision` của migration mới phải là đầu hiện tại của nhánh nền")
    return {"status": "fail" if problems else "pass", "files": found, "heads": heads,
            "output": "\n".join(problems)}


def card_lines(schema: dict, esc) -> list[str]:
    """Mục «CÓ ĐỔI CẤU TRÚC DB» cho thẻ kết quả (HTML Telegram)."""
    if not schema or not schema.get("files"):
        return []
    lines = ["<b>CÓ ĐỔI CẤU TRÚC DB</b> (migration):"]
    risky = False
    for f in schema["files"]:
        changes = f.get("changes") or []
        if not changes:
            lines.append(f"• <code>{esc(f['path'].rsplit('/', 1)[-1])}</code> (không đọc ra thay đổi)")
        for c in changes[:12]:
            if c.get("destructive"):
                risky = True
                lines.append(f"• <b>{esc(c['label'])}</b> {esc(c['target'])} — <i>có thể mất dữ liệu</i>")
            else:
                lines.append(f"• {esc(c['label'])} {esc(c['target'])}")
    if schema.get("status") == "fail":
        lines.append(f"<b>Migration chưa đạt:</b> {esc(schema.get('output', '')[:400])}")
    lines.append("<i>Trước khi lên dev em sao lưu cả DB dev" + (" — thay đổi in đậm ở trên không tự hoàn tác được bằng "
                                                                 "cách deploy lại bản cũ" if risky else "") + ".</i>")
    return lines
