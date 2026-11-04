"""Bài kiểm tài liệu (bao-CR-712, luật 10 của `.claude/rules/chung-tai-lieu.md`) — CHẶN LỖI MỚI (P5).

Chạy ở gốc repo (máy hay container có đủ repo; chỉ cần Python 3.10+, không cần cài gì):

    python backend/scripts/kiem_tai_lieu.py                  # lỗi trong tệp nền chỉ báo; lỗi MỚI → thoát 1
    python backend/scripts/kiem_tai_lieu.py --chi-bao        # in hết, luôn thoát 0
    python backend/scripts/kiem_tai_lieu.py --cap-nhat-nen   # sửa xong lỗi nào thì gỡ nó khỏi nền (CHỈ BỚT, không thêm)
    python backend/scripts/kiem_tai_lieu.py --only lien-ket,ten

Tệp nền `kiem_tai_lieu_nen.txt` (cạnh script): lỗi đã có lúc bật chế độ chặn (03/11/2026, 79 dòng). Nền chỉ giảm dần —
thêm dòng vào nền bằng tay là lách luật. Miễn hẳn: luật tên cho `doc/v1/` (lưu trữ nguyên trạng) và liên kết trong sổ
`change-log*.md` / `nhat-ky-task.md` (sổ không sửa lùi các dòng lịch sử).

Năm nhóm:
  lien-ket       liên kết markdown `[..](đường)` trong doc/, CLAUDE.md, AGENTS.md, .claude/ trỏ tới tệp không tồn tại;
  duong-dan      đường dẫn trong backtick (`doc/...`, `plans/...`) ở CLAUDE.md / AGENTS.md / .claude/ không tồn tại;
  ten            tệp / thư mục trong doc/ sai luật đặt tên (chữ thường, không dấu, gạch ngang);
  readme         thư mục phân hệ `doc/erp/<phan-he>/` thiếu README.md;
  bat-buoc       phân hệ thiếu chuc-nang/01-yeu-cau-chuc-nang.md, 02-yeu-cau-phi-chuc-nang.md, tai-lieu-ky-thuat/api.md;
  tep-le         tệp lẻ ở cấp `doc/` (chỉ README.md được đứng đó);
  muc-luc        skill / agent / luật chưa có dòng trong `doc/tai-lieu-ky-thuat/quy-dinh/README.md`.
"""
import argparse
import os
import posixpath
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote


def find_root() -> Path:
    """Gốc repo: biến `KIEM_TAI_LIEU_ROOT` (container api mount repo chỉ-đọc ở /repo), không có thì thư mục cách script
    hai cấp (`backend/scripts/` → gốc). KHÔNG dò ngược "thư mục cha có doc/ + CLAUDE.md": `backend/` cũng có
    `CLAUDE.md`, và checkout nào lỡ có `backend/doc/` thì gốc thành `backend/` — mọi tệp báo thiếu (lỗi 03/11/2026)."""
    env = os.environ.get("KIEM_TAI_LIEU_ROOT")
    if env and (Path(env) / "doc").is_dir():
        return Path(env)
    return Path(__file__).resolve().parents[2]


ROOT = find_root()
BASELINE = Path(__file__).with_name("kiem_tai_lieu_nen.txt")
#  Sổ không sửa lùi: liên kết trong các dòng lịch sử miễn kiểm.
LEDGERS = {"change-log.md", "change-log-bao.md", "change-log-ai.md", "nhat-ky-task.md"}
INDEX_REL = "doc/tai-lieu-ky-thuat/quy-dinh/README.md"
#  Sổ giữ nguyên tên (luật 7) và tệp quy ước công cụ.
NAME_EXEMPT = {"README.md", "CLAUDE.md", "AGENTS.md", "SKILL.md"}
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9.\-]*$")
LINK_RE = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
TICK_RE = re.compile(r"`((?:doc|plans|frontend-v2/plans)/[^`\s*<>{}]+)`")
#  Khi KHÔNG có git (container api): đi cây thư mục, bỏ các thư mục này. `.claude/worktrees/` = worktree của agent nằm
#  TRONG repo — mỗi cái là một bản sao nguyên repo, quét vào là hàng chục lỗi giả và chậm gấp nhiều lần (03/11/2026).
SKIP_DIRS = {"node_modules", ".git", "__pycache__", ".venv", "venv", ".pytest_cache", ".ruff_cache", ".mypy_cache",
             "dist", "build", "uploads", "graphify-out"}
SKIP_PREFIXES = (".claude/worktrees",)


def _git_files() -> list[str] | None:
    """Tệp git theo dõi (đường dẫn tương đối, dấu /); None khi không có git / không phải repo."""
    try:
        run = subprocess.run(["git", "-C", str(ROOT), "-c", "core.quotepath=off", "ls-files", "-z"],
                             capture_output=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return None
    if run.returncode != 0:
        return None
    return [x for x in run.stdout.decode("utf-8", "replace").split("\0") if x]


def _walk_files() -> list[str]:
    out = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        base = Path(dirpath).relative_to(ROOT).as_posix()
        base = "" if base == "." else base + "/"
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not (base + d).startswith(SKIP_PREFIXES)]
        out += [base + name for name in filenames]
    return out


def _load_paths() -> tuple[list[str], set[str]]:
    """Mọi tệp của repo nạp MỘT lần: có git thì chỉ tệp git theo dõi, không thì đi cây (bỏ `SKIP_DIRS`). Tra tồn tại
    trong bộ nhớ thay vì gọi ổ cho từng liên kết — trong container ổ là thư mục gắn từ Windows, mỗi lần hỏi rất chậm."""
    files = _git_files()
    if files is None:
        files = _walk_files()
    files = [p for p in files if not p.startswith(SKIP_PREFIXES)]
    known = set(files)
    for p in files:
        parent = posixpath.dirname(p)
        while parent and parent not in known:
            known.add(parent)
            parent = posixpath.dirname(parent)
    return sorted(files), known


FILES, KNOWN = _load_paths()
FILES_SET = set(FILES)


def exists(rel_path: str) -> bool:
    """Có trong tập đã nạp thì có; trượt mới hỏi ổ (liên kết tới tệp chưa theo dõi / nằm ngoài repo)."""
    p = posixpath.normpath(rel_path).rstrip("/")
    if p in KNOWN or p in ("", "."):
        return True
    return (ROOT / p).exists()


def read(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding="utf-8", errors="replace")


def md_files(prefix: str) -> list[str]:
    return [p for p in FILES if p.startswith(prefix) and p.endswith(".md")]


def check_links(files) -> list[str]:
    out = []
    for f in files:
        if posixpath.basename(f) in LEDGERS:
            continue
        text = re.sub(r"```.*?```", "", read(f), flags=re.S)       # bỏ khối mã
        for target in LINK_RE.findall(text):
            if re.match(r"^[a-z]+:", target) or target.startswith("#"):
                continue
            path = unquote(target.split("#", 1)[0])
            if not path:
                continue
            dest = path.lstrip("/") if path.startswith("/") else posixpath.join(posixpath.dirname(f), path)
            if not exists(dest):
                out.append(f"{f} → {target}")
    return out


def check_backtick_paths(files) -> list[str]:
    out = []
    for f in files:
        for target in TICK_RE.findall(read(f)):
            path = target.rstrip(".,;:)")
            if any(ch in path for ch in "?|") or "<" in path or "..." in path or "…" in path:   # mẫu, không phải tệp
                continue
            if not exists(path):
                out.append(f"{f} → `{path}`")
    return out


def check_names() -> list[str]:
    out = []
    for p in sorted(k for k in KNOWN if k.startswith("doc/") and not k.startswith("doc/v1/")):
        name = posixpath.basename(p)
        if name in NAME_EXEMPT or set(p.split("/")) & SKIP_DIRS:
            continue
        if not NAME_RE.match(name):
            out.append(p + ("" if p in FILES_SET else "/"))
    return out


#  Bốn tài liệu BẮT BUỘC của mỗi phân hệ (người chủ chốt 03/11/2026, `.claude/rules/chung-tai-lieu.md`).
REQUIRED = ("chuc-nang/01-yeu-cau-chuc-nang.md", "chuc-nang/02-yeu-cau-phi-chuc-nang.md", "tai-lieu-ky-thuat/api.md")
#  Thư mục cấp `doc/erp/` không phải phân hệ (dùng chung / đang chờ tách ở P3).
NOT_MODULES = {"nghien-cuu", "tham-khao-hrm"}


def _children(prefix: str, dirs: bool) -> list[str]:
    """Con trực tiếp của `prefix/` — thư mục (`dirs=True`) hoặc tệp."""
    head = prefix + "/"
    return sorted(k for k in KNOWN
                  if k.startswith(head) and "/" not in k[len(head):] and (k not in FILES_SET) == dirs)


def erp_modules() -> list[str]:
    return [d for d in _children("doc/erp", dirs=True) if posixpath.basename(d) not in NOT_MODULES]


def check_readmes() -> list[str]:
    return [d + "/" for d in erp_modules() if f"{d}/README.md" not in FILES_SET]


def check_required() -> list[str]:
    out = []
    for d in erp_modules():
        missing = [f for f in REQUIRED if f"{d}/{f}" not in FILES_SET]
        if missing:
            out.append(f"{d}/: thiếu {', '.join(missing)}")
    return out


def check_stray() -> list[str]:
    return [p for p in _children("doc", dirs=False) if posixpath.basename(p) != "README.md"]


def check_index() -> list[str]:
    if INDEX_REL not in FILES_SET:
        return [f"thiếu {INDEX_REL}"]
    text = read(INDEX_REL)
    items = [(posixpath.basename(d), d) for d in _children(".claude/skills", dirs=True)]
    items += [(posixpath.basename(p)[:-3], p) for p in _children(".claude/agents", dirs=False) if p.endswith(".md")]
    items += [(posixpath.basename(p), p) for p in _children(".claude/rules", dirs=False) if p.endswith(".md")]
    items += [(f"frontend-v2/.claude/rules/{posixpath.basename(p)}", p)
              for p in _children("frontend-v2/.claude/rules", dirs=False) if p.endswith(".md")]
    return [where for name, where in sorted(items) if name not in text]


CHECKS = {
    "lien-ket": lambda files, top: check_links(files),
    "duong-dan": lambda files, top: check_backtick_paths(top),
    "ten": lambda files, top: check_names(),
    "readme": lambda files, top: check_readmes(),
    "bat-buoc": lambda files, top: check_required(),
    "tep-le": lambda files, top: check_stray(),
    "muc-luc": lambda files, top: check_index(),
}
TITLES = {"lien-ket": "Liên kết hỏng", "duong-dan": "Đường dẫn trong backtick không tồn tại",
          "ten": "Tên sai luật (chữ thường, không dấu, gạch ngang)", "readme": "Phân hệ thiếu README.md",
          "bat-buoc": "Phân hệ thiếu tài liệu bắt buộc (01 / 02 / api.md)",
          "tep-le": "Tệp lẻ ở cấp doc/", "muc-luc": "Skill / agent / luật chưa có trong mục lục quy định"}


def collect(only: list[str]) -> dict[str, list[str]]:
    top = [p for p in ("CLAUDE.md", "AGENTS.md", *md_files(".claude/"), *md_files("frontend-v2/.claude/"),
                       "doc/README.md") if p in FILES_SET]
    files = [*md_files("doc/"), *[p for p in top if not p.startswith("doc/")]]
    return {key: CHECKS[key](files, top) for key in only}


def read_baseline() -> set[str]:
    if not BASELINE.exists():
        return set()
    return {ln.rstrip("\n") for ln in BASELINE.read_text(encoding="utf-8").splitlines() if ln and not ln.startswith("#")}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--chi-bao", action="store_true", help="chỉ báo, luôn thoát 0")
    ap.add_argument("--cap-nhat-nen", action="store_true", help="gỡ khỏi nền các lỗi đã hết (chỉ bớt)")
    ap.add_argument("--only", default="")
    ap.add_argument("--limit", type=int, default=0, help="tối đa bao nhiêu dòng mỗi nhóm (0 = hết)")
    args = ap.parse_args()
    only = [x for x in args.only.split(",") if x] or list(CHECKS)
    found = collect(only)
    baseline = read_baseline()
    current = {f"{k}\t{line}" for k, lines in found.items() for line in lines}
    if args.cap_nhat_nen:
        if args.only:
            print("--cap-nhat-nen phải chạy đủ mọi nhóm (bỏ --only).")
            return 2
        kept = sorted(baseline & current)
        head = [ln for ln in BASELINE.read_text(encoding="utf-8").splitlines() if ln.startswith("#")]
        BASELINE.write_text("\n".join(head + kept) + "\n", encoding="utf-8", newline="\n")
        print(f"Nền: {len(baseline)} → {len(kept)} dòng (gỡ {len(baseline) - len(kept)}).")
        return 0
    new_total = old_total = 0
    for key in only:
        lines = found[key]
        new = [ln for ln in lines if f"{key}\t{ln}" not in baseline]
        new_total += len(new)
        old_total += len(lines) - len(new)
        print(f"\n## {TITLES[key]} — {len(lines)} ({len(new)} mới)")
        shown = new + ([] if args.limit else [ln for ln in lines if ln not in new])
        for line in shown[: args.limit or None]:
            print(f"- {'MỚI ' if line in new else ''}{line}")
    gone = len(baseline - current) if not args.only else 0
    print(f"\nTổng: {new_total + old_total} lỗi — {new_total} MỚI, {old_total} trong nền"
          + (f"; {gone} dòng nền đã hết, chạy --cap-nhat-nen để gỡ." if gone else "."))
    if new_total and not args.chi_bao:
        print("CHẶN: có lỗi tài liệu mới — sửa theo `.claude/rules/chung-tai-lieu.md` (không thêm vào nền).")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
