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
import re
import sys
from pathlib import Path
from urllib.parse import unquote

def find_root() -> Path:
    """Gốc repo: biến `KIEM_TAI_LIEU_ROOT` (container api mount repo chỉ-đọc ở /repo), không có thì dò thư mục cha có
    cả `doc/` và `CLAUDE.md`."""
    env = os.environ.get("KIEM_TAI_LIEU_ROOT")
    if env and (Path(env) / "doc").is_dir():
        return Path(env)
    for cand in Path(__file__).resolve().parents:
        if (cand / "doc").is_dir() and (cand / "CLAUDE.md").is_file():
            return cand
    return Path(__file__).resolve().parents[2]


ROOT = find_root()
BASELINE = Path(__file__).with_name("kiem_tai_lieu_nen.txt")
#  Sổ không sửa lùi: liên kết trong các dòng lịch sử miễn kiểm.
LEDGERS = {"change-log.md", "change-log-bao.md", "change-log-ai.md", "nhat-ky-task.md"}
DOC = ROOT / "doc"
INDEX = DOC / "tai-lieu-ky-thuat" / "quy-dinh" / "README.md"
#  Sổ giữ nguyên tên (luật 7) và tệp quy ước công cụ.
NAME_EXEMPT = {"README.md", "CLAUDE.md", "AGENTS.md", "SKILL.md"}
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9.\-]*$")
LINK_RE = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
TICK_RE = re.compile(r"`((?:doc|plans|frontend-v2/plans)/[^`\s*<>{}]+)`")
SKIP_DIRS = {"node_modules", ".git", "__pycache__"}


def md_files(base: Path):
    for p in base.rglob("*.md"):
        if not SKIP_DIRS.intersection(p.parts):
            yield p


def rel(p: Path) -> str:
    return p.relative_to(ROOT).as_posix()


def check_links(files) -> list[str]:
    out = []
    for f in files:
        if f.name in LEDGERS:
            continue
        text = f.read_text(encoding="utf-8", errors="replace")
        text = re.sub(r"```.*?```", "", text, flags=re.S)       # bỏ khối mã
        for target in LINK_RE.findall(text):
            if re.match(r"^[a-z]+:", target) or target.startswith("#"):
                continue
            path = unquote(target.split("#", 1)[0])
            if not path:
                continue
            dest = (ROOT / path.lstrip("/")) if path.startswith("/") else (f.parent / path)
            if not dest.exists():
                out.append(f"{rel(f)} → {target}")
    return out


def check_backtick_paths(files) -> list[str]:
    out = []
    for f in files:
        for target in TICK_RE.findall(f.read_text(encoding="utf-8", errors="replace")):
            path = target.rstrip(".,;:)")
            if any(ch in path for ch in "?|") or "<" in path or "..." in path or "…" in path:   # mẫu, không phải tệp
                continue
            if not (ROOT / path).exists() and not (ROOT / path.rstrip("/")).exists():
                out.append(f"{rel(f)} → `{path}`")
    return out


def check_names() -> list[str]:
    out = []
    for p in DOC.rglob("*"):
        if SKIP_DIRS.intersection(p.parts) or p.name in NAME_EXEMPT or rel(p).startswith("doc/v1/"):
            continue
        if not NAME_RE.match(p.name):
            out.append(rel(p) + ("/" if p.is_dir() else ""))
    return out


#  Bốn tài liệu BẮT BUỘC của mỗi phân hệ (người chủ chốt 03/11/2026, `.claude/rules/chung-tai-lieu.md`).
REQUIRED = ("chuc-nang/01-yeu-cau-chuc-nang.md", "chuc-nang/02-yeu-cau-phi-chuc-nang.md", "tai-lieu-ky-thuat/api.md")
#  Thư mục cấp `doc/erp/` không phải phân hệ (dùng chung / đang chờ tách ở P3).
NOT_MODULES = {"nghien-cuu", "tham-khao-hrm"}


def erp_modules() -> list[Path]:
    erp = DOC / "erp"
    return [d for d in sorted(erp.iterdir()) if d.is_dir() and d.name not in NOT_MODULES] if erp.exists() else []


def check_readmes() -> list[str]:
    return [rel(d) + "/" for d in erp_modules() if not (d / "README.md").exists()]


def check_required() -> list[str]:
    out = []
    for d in erp_modules():
        missing = [f for f in REQUIRED if not (d / f).exists()]
        if missing:
            out.append(f"{rel(d)}/: thiếu {', '.join(missing)}")
    return out


def check_stray() -> list[str]:
    return [rel(p) for p in sorted(DOC.iterdir()) if p.is_file() and p.name != "README.md"]


def check_index() -> list[str]:
    if not INDEX.exists():
        return [f"thiếu {rel(INDEX)}"]
    text = INDEX.read_text(encoding="utf-8")
    items = []
    items += [(p.name, f".claude/skills/{p.name}") for p in (ROOT / ".claude" / "skills").iterdir() if p.is_dir()]
    items += [(p.stem, rel(p)) for p in (ROOT / ".claude" / "agents").glob("*.md")]
    items += [(p.name, rel(p)) for p in (ROOT / ".claude" / "rules").glob("*.md")]
    items += [(f"frontend-v2/.claude/rules/{p.name}", rel(p)) for p in (ROOT / "frontend-v2" / ".claude" / "rules").glob("*.md")]
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
    top = [ROOT / "CLAUDE.md", ROOT / "AGENTS.md", *md_files(ROOT / ".claude"),
           *md_files(ROOT / "frontend-v2" / ".claude"), DOC / "README.md"]
    top = [p for p in top if p.exists()]
    files = [*md_files(DOC), *top]
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
