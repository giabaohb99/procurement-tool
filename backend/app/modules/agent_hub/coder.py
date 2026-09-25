"""Bậc 2 của Agent Hub (ai-CR-011): bấm Duyệt là bot SỬA MÃ THẬT bằng Claude Code.

Đường đi của một việc sau khi đại ca bấm «Duyệt» trên thẻ kế hoạch:

  service.handle_callback("ok")
      -> approve_gate()      chốt trước khi giao: có phạm vi tệp chưa, có đụng tệp cấm không
      -> dispatch()          ném `agent.code_task` vào hàng đợi `agent_code`
  tasks.code_task  (chạy TRONG service `agent-runner`, không phải celery-worker thường)
      -> run_code_task()
           prepare_worktree  clone `base` một lần, cắt nhánh `bot/<mã việc>-<slug>` từ origin/erp-v2
           build_brief       đề bài = thẻ kế hoạch + tài liệu đã tra + luật C1..C10 + §D
           run_claude        `claude -p` đọc đề bài từ stdin, trả JSON, môi trường SẠCH
           check_drift       luật C1: tệp cấm / quá trần / lệch >30% so với kế hoạch -> leo thang
           run_gate          pytest ĐÚNG các bài kiểm vừa đụng (luật C6)
           commit            trên nhánh của việc, trong volume của runner
           send_review_card  thẻ kết quả + tệp .diff, việc chuyển sang REVIEW

Giai đoạn 2a (ai-CR-012): `_try_publish` đẩy nhánh lên GitHub + mở PR vào erp-v2, hoặc nút trên thẻ.
Giai đoạn 2b phần 1 (ai-CR-013): nút «Hỏi thêm về bản vá» -> tin kế của đại ca -> `agent.ask_task`
-> `answer_patch_question` chạy `claude -p --resume` đúng phiên, chỉ đọc, trả lời lên Telegram.
Phiên CLI cất ở `<AGENT_WORKTREE_ROOT>/.claude` (CLAUDE_CONFIG_DIR) để sống qua recreate container.
Giai đoạn 2b phần 2 (ai-CR-014): nút «Gộp erp-v2 + deploy dev» -> thẻ hỏi -> đại ca đồng ý (ngay
hoặc hẹn giờ) -> `agent.deploy_task` -> `merge_and_deploy`: merge --no-ff vào nhánh nền, push
(không --force), ssh lên VPS reset về origin/erp-v2 + build lại đúng service, chờ health 200.
Thu hồi = `revert_and_deploy` (git revert -m 1 bản gộp rồi deploy lại). Xem khối cuối tệp.

Ba ranh giới cố ý, đừng nới khi chưa đọc §E bộ quy tắc (doc/agent-hub/02):
  - `claude` chỉ nhận môi trường do `build_env` dựng: PATH/HOME/PYTHONPATH và ĐÚNG MỘT khóa
    `CLAUDE_CODE_OAUTH_TOKEN` đọc từ `os.environ` ngay lúc spawn (không qua `settings`).
    Khóa Telegram, Gemini, DB của tiến trình cha KHÔNG đi xuống tiến trình con.
  - Tiến trình con hạ xuống người dùng `AGENT_RUNNER_USER` (worker chạy root) nên không đọc
    được `/proc/<pid>/environ` của cha — đây là chốt thật, chốt trên chỉ là phép lịch sự.
  - Không có `ANTHROPIC_API_KEY` ở đâu cả (QĐ-AI-3): bot chạy bằng gói thuê bao qua CLI.
"""
from __future__ import annotations

import fnmatch
import hashlib
import json
import logging
import os
import re
import shutil
import subprocess
import tempfile
import time
import uuid
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import settings

from . import memory, playbook, telegram
from .timeutil import now_local
from .constants import (
    BOT_NAME,
    ACT_PATCH_ANSWER,
    RISK_HIGH,
    RUN_ERROR,
    RUN_OK,
    RUN_RUNNING,
    ST_DEPLOYING,
    ST_NEEDS_INPUT,
    ST_PROD,
    ST_REVIEW,
    STAGE_ASK,
    STAGE_CODE,
    STAGE_DEPLOY,
    STAGE_PLAN,
    STAGE_REVERT,
    STAGE_SCAN,
    ST_TRIAGE,
)
from .model import AgentMessage, AgentRun, AgentTask

log = logging.getLogger("app.agent_hub.coder")

PROVIDER = "claude_code"
DEFAULT_MODEL = "claude-code"

#  Tệp bot KHÔNG ĐƯỢC ĐỤNG (luật C3, C4, §E, §G). So bằng fnmatch trên cả đường dẫn đầy đủ
#  lẫn tên tệp. Mở rộng danh sách này thì sửa cả bài kiểm `test_tep_cam_thi_leo_thang`.
BANNED_PATTERNS = (
    ".env", ".env.*",
    "*.pem", "*.key", "*.p12",
    "backend/app/seed_prod.py",
    "backend/migrations/versions/*",          # C3: không migration
    ".github/workflows/*",                    # C4
    "docker-compose.production.yml",          # C4
    "backend/app/core/permissions.py",        # C4: không đụng phân quyền
    "backend/app/core/scoping.py",
    "CLAUDE.md", "*/CLAUDE.md",               # §G: không tự sửa luật của mình
    ".claude/*", "*/.claude/*",
    "doc/agent-hub/02-bo-quy-tac-bot.md",
    "doc/agent-hub/03-so-quyet-dinh.md",      # ai-CR-015: sổ chỉ ghi qua nút đại ca duyệt
)

#  Bài kiểm không tính vào tỷ lệ lệch kế hoạch (luật C5 bắt bot viết test, mà thẻ kế hoạch
#  hiếm khi liệt kê tệp test).
_TEST_FILE_PATTERNS = ("test/*", "*/test_*.py", "test_*.py", "*.test.ts", "*.test.tsx")

#  Công cụ Claude Code được phép. Bash chỉ mở đúng mấy lệnh đọc + chạy test; lệnh khác bị
#  từ chối ngay trong `-p` (không có ai ngồi bấm Cho phép) và bot phải tự xoay.
ALLOWED_TOOLS = ",".join([
    "Read", "Edit", "Write", "MultiEdit", "Glob", "Grep",
    #  Cả `python` lẫn `python3`: lượt chạy thật đầu tiên (AI-0005, 22/09/2026) bot gõ
    #  `python3 -m pytest`, bị chặn vì mẫu chỉ khớp `python`, rồi đốt hơn 50 lượt thử lại
    #  và giao bản vá "chưa chạy được bài kiểm" dù cổng kiểm của runner sau đó xanh.
    "Bash(python -m pytest:*)", "Bash(python3 -m pytest:*)", "Bash(pytest:*)",
    "Bash(python -m py_compile:*)", "Bash(python3 -m py_compile:*)",
    "Bash(git diff:*)", "Bash(git status:*)", "Bash(git log:*)",
    #  ai-CR-019: tự kiểm frontend-v2. `run test -- src/` ép có đường dẫn — không quét cả ~3200 bài.
    "Bash(npm --prefix frontend-v2 run typecheck:*)",
    #  ai-CR-034: tự kiểm `frontend/` (bản cũ) — chỉ có typescript, không có lint/vitest.
    "Bash(npm --prefix frontend exec -- tsc --noEmit -p frontend:*)",
    #  Lệnh vitest KHÔNG khai ở đây: Claude Code so mẫu theo NGUYÊN TỪ nên `… -- src/:*` không khớp
    #  `… -- src/modules/finance` — AI-0007 bị chặn cả hai lần chạy (ai-CR-026). Khai theo từng thư
    #  mục có thật trong worktree ở `allowed_tools()`.
])


def allowed_tools(worktree: str) -> str:
    """ALLOWED_TOOLS + một mẫu vitest cho MỖI thư mục phân hệ / khu dùng chung có thật (ai-CR-026).
    Chỉ cho chạy vitest theo đúng một thư mục — không có mẫu nào chạy được cả bộ ~3200 bài."""
    src = Path(worktree) / FE_DIR / "src"
    extra = []
    for root in ("modules", "shared", "core", "app"):
        base = src / root
        if base.is_dir():
            extra += [f"Bash(npm --prefix {FE_DIR} run test -- src/{root}/{d.name}:*)"
                      for d in sorted(base.iterdir()) if d.is_dir()]
    return ",".join([ALLOWED_TOOLS, *extra]) if extra else ALLOWED_TOOLS

DRIFT_RATIO = 0.30          # luật C1: quá 30% tệp ngoài kế hoạch là dừng
GIT_TIMEOUT = 900           # clone lần đầu kho vài trăm MB
GATE_TIMEOUT = 600
GATE_TAIL = 3000
CARD_BUDGET = 3500          # chừa chỗ dưới telegram.MAX_TEXT cho dòng ghi chú cuối


class CoderError(RuntimeError):
    """Lỗi mà runner không tự xử được: thiếu khóa, CLI trả lỗi, git hỏng."""


class MaxTurnsError(CoderError):
    """`claude -p` hết `--max-turns` khi đang làm dở (ai-CR-023). KHÔNG phải thất bại: phần đã sửa
    còn nguyên trong worktree và phiên còn nguyên — nút «Làm tiếp» nối đúng phiên đó."""

    def __init__(self, message: str, data: dict):
        super().__init__(message)
        self.data = data


#  Số lượt cho một lần «Làm tiếp» (ai-CR-023).
CONTINUE_MAX_TURNS = 60


# ---------------------------------------------------------------------------
# Chốt TRƯỚC khi giao (chạy trong poller, lúc đại ca bấm Duyệt)
# ---------------------------------------------------------------------------
def is_banned_path(path: str) -> bool:
    p = path.replace("\\", "/").strip()
    #  KHÔNG dùng `.lstrip("./")` — nó xén cả dấu chấm đầu tên và `.env` thành `env`.
    while p.startswith("./"):
        p = p[2:]
    p = p.lstrip("/")
    name = p.rsplit("/", 1)[-1]
    return any(fnmatch.fnmatch(p, pat) or fnmatch.fnmatch(name, pat) for pat in BANNED_PATTERNS)


def approve_gate(task: AgentTask) -> str:
    """Trả lý do KHÔNG giao được, rỗng nếu giao được.

    Kiểm ở đây rẻ và tức thì; kiểm sau khi bot chạy xong 20 phút thì đã đốt tiền rồi.
    """
    files = [f for f in (task.plan_files or []) if isinstance(f, str) and f.strip()]
    if not files:
        return "kế hoạch chưa có phạm vi tệp (luật B2) — bấm Sửa lại rồi /gom để lập lại"
    banned = [f for f in files if is_banned_path(f)]
    if banned:
        return ("kế hoạch đụng tệp bot bị cấm sửa (luật C3/C4/§E): "
                + ", ".join(banned[:5]) + " — phần này là việc tay")
    return ""


def queue_for(task_id: int) -> str:
    """Hàng đợi của MÁY giữ việc này (ai-CR-054): dính máy cũ, không thì chọn máy đang bật; sổ máy trống thì
    hàng đợi cũ `agent_code`. Mở session riêng vì các hàm dispatch không cầm `db`."""
    from app.core.database import SessionLocal

    from . import runners

    db = SessionLocal()
    try:
        return runners.queue_for_task(db, task_id)
    finally:
        db.close()


def dispatch(task_id: int) -> None:
    """Đưa việc vào hàng đợi của máy sửa mã. Import muộn để poller không kéo Celery lúc nạp."""
    from app.core.celery_app import celery_app

    celery_app.send_task("agent.code_task", args=[task_id], queue=queue_for(task_id))


# ---------------------------------------------------------------------------
# Môi trường + tiến trình con
# ---------------------------------------------------------------------------
def build_env(worktree: str, *, with_token: bool = True) -> dict[str, str]:
    """Môi trường SẠCH cho tiến trình con. Cố ý dựng từ rỗng, không `os.environ.copy()`.

    Chỉ đúng một khóa đi xuống: `CLAUDE_CODE_OAUTH_TOKEN`, và chỉ cho lượt `claude`
    (`with_token=False` cho git/pytest — chúng không cần và bài kiểm do bot viết chạy
    trong pytest thì không nên thấy khóa đó).
    """
    home = f"/home/{settings.AGENT_RUNNER_USER}" if settings.AGENT_RUNNER_USER else os.environ.get("HOME", "/tmp")
    env = {
        "PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"),
        "HOME": home,
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "PYTHONPATH": str(Path(worktree) / "backend"),
        "PYTHONDONTWRITEBYTECODE": "1",
        "DISABLE_AUTOUPDATER": "1",
        #  Phiên/cấu hình của CLI nằm trong volume worktree, không ở ~/.claude của container
        #  (ai-CR-013): recreate container là mất phiên, mà «Hỏi thêm» cần --resume đúng phiên.
        "CLAUDE_CONFIG_DIR": claude_config_dir(),
    }
    if with_token:
        token = os.environ.get("CLAUDE_CODE_OAUTH_TOKEN", "").strip()
        if not token:
            raise CoderError(
                "CLAUDE_CODE_OAUTH_TOKEN chưa khai trong .env của stack agenthub "
                "(lấy bằng `claude setup-token` trên máy đã đăng nhập, dán tay vào .env)")
        env["CLAUDE_CODE_OAUTH_TOKEN"] = token
    return env


def _drop_privileges_kwargs() -> dict:
    """Tham số `user`/`group` cho subprocess: chỉ khi đang là root và có khai người dùng."""
    user = settings.AGENT_RUNNER_USER
    geteuid = getattr(os, "geteuid", None)
    if not user or geteuid is None or geteuid() != 0:
        return {}
    return {"user": user, "group": user}


def _git(cwd: str, *args: str, timeout: int = GIT_TIMEOUT,
         extra_env: dict[str, str] | None = None) -> str:
    """`extra_env` chỉ dùng cho `git push` (ai-CR-012): biến GIT_CONFIG_* mang khóa GitHub."""
    proc = subprocess.run(
        ["git", *args], cwd=cwd, env={**build_env(cwd, with_token=False), **(extra_env or {})},
        capture_output=True, text=True, timeout=timeout, **_drop_privileges_kwargs(),
    )
    if proc.returncode != 0:
        raise CoderError(f"git {' '.join(args[:2])} lỗi: {(proc.stderr or proc.stdout).strip()[:800]}")
    return proc.stdout


def slugify(text: str, limit: int = 40) -> str:
    """Tên nhánh chỉ còn a-z0-9 và gạch nối; tiếng Việt bỏ dấu thô (đủ để đọc, không cần đẹp)."""
    import unicodedata

    ascii_text = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode()
    ascii_text = ascii_text.replace("đ", "d").replace("Đ", "d").lower()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text).strip("-")
    return slug[:limit].strip("-") or "viec"


def branch_name_for(task: AgentTask) -> str:
    """`bot/ai-0007-<slug>` — theo MÃ VIỆC, không theo số CR.

    Lệch luật C2 (`bot/ai-CR-<số>-<slug>`) một cách cố ý: số CR cấp bằng cách grep hai tệp
    change-log, mà hai phiên cùng cấp là trùng số (đã xảy ra với CR-129). Bot không được
    tự cấp; đại ca đặt số CR lúc gộp, mã việc thì đã duy nhất sẵn.
    """
    return f"bot/{task.code.lower()}-{slugify(task.title)}"


def fetch_base(base: str) -> None:
    """Kéo nhánh nền MỚI NHẤT về `refs/remotes/origin/<nền>` của kho base (ai-CR-017).

    Kho base nhân bản từ `.git` trên máy đại ca (`AGENT_REPO_SOURCE`), nên `origin/erp-v2` của nó
    là nhánh erp-v2 Ở MÁY — đo 23/09/2026 chậm 7 commit so với GitHub: bot đọc và sửa trên mã cũ,
    còn lượt gộp thì bị GitHub từ chối vì không fast-forward. Có khóa GitHub thì lấy thẳng từ
    GitHub (ép cập nhật ref, `+`); không có khóa hoặc GitHub lỗi thì lùi về bản ở máy như cũ.
    """
    branch = settings.AGENT_BASE_BRANCH
    #  ai-CR-018: kéo cả nhánh chạy thật (main) để lượt rà soát so được — việc sửa lỗi thường
    #  làm ở main trước rồi mới gộp sang erp-v2 (ca AI-0006: bao-CR-465 đã ở main, bot không thấy).
    branches = [branch] + [b for b in (settings.AGENT_MAIN_BRANCH,) if b and b != branch]
    if os.environ.get("AGENT_GITHUB_TOKEN", "").strip():
        try:
            _git(base, "fetch", _repo_url(),
                 *[f"+refs/heads/{b}:refs/remotes/origin/{b}" for b in branches],
                 timeout=600, extra_env=_push_env())
            return
        except CoderError as e:
            log.warning("agent_hub.coder: kéo %s từ GitHub hỏng, dùng bản ở máy: %s", branches, e)
    _git(base, "fetch", "--prune", "origin", branch)
    for extra in branches[1:]:
        try:
            _git(base, "fetch", "origin", extra)
        except CoderError:
            log.warning("agent_hub.coder: bản ở máy không có nhánh %s", extra)


def prepare_worktree(task: AgentTask) -> tuple[str, str]:
    """Trả (đường dẫn worktree, tên nhánh). Worktree cũ cùng mã việc thì bỏ, cắt lại từ đầu."""
    root = Path(settings.AGENT_WORKTREE_ROOT)
    base = root / "base"
    if not (base / "HEAD").exists() and not (base / ".git").exists():
        #  `--no-checkout`: base chỉ giữ object + ref, không cần cây làm việc; worktree
        #  của từng việc mới có cây.
        _git(str(root), "clone", "--no-checkout", settings.AGENT_REPO_SOURCE, str(base))
    fetch_base(str(base))

    wt = root / task.code
    if wt.exists():
        try:
            _git(str(base), "worktree", "remove", "--force", str(wt), timeout=120)
        except CoderError:
            shutil.rmtree(wt, ignore_errors=True)
    _git(str(base), "worktree", "prune", timeout=120)
    branch = branch_name_for(task)
    _git(str(base), "worktree", "add", "-B", branch, str(wt),
         f"origin/{settings.AGENT_BASE_BRANCH}", timeout=300)
    return str(wt), branch


# ---------------------------------------------------------------------------
# Đề bài
# ---------------------------------------------------------------------------
_RULES_BRIEF = """\
## Luật bắt buộc (bộ quy tắc bot, doc/agent-hub/02 — bản rút gọn)
C1. Chỉ sửa trong phạm vi tệp ở trên. Cần đụng thêm tệp thì được, nhưng quá 30% số tệp ngoài \
kế hoạch hoặc quá {max_files} tệp là DỪNG, không làm nữa, ghi rõ lý do trong tổng kết. Tệp bài kiểm \
và tài liệu `.md` không tính vào 30% đó — sửa tài liệu cho khớp mã là nên làm.
C3. KHÔNG tạo migration Alembic, KHÔNG sửa model kéo theo đổi cấu trúc bảng.
C4. KHÔNG đụng phân quyền (core/permissions.py, core/scoping.py, seed_prod.py), \
.github/workflows, docker-compose.production.yml, CLAUDE.md, thư mục .claude/.
C5. Viết bài kiểm cho phần vừa sửa, gồm ít nhất một ca phủ định (đầu vào sai phải bị chặn).
C6. Chỉ chạy bài kiểm của phần vừa sửa: `python -m pytest test/backend/<tệp> -q -p no:cacheprovider` \
(PYTHONPATH đã trỏ backend/). KHÔNG chạy cả test/backend. Ở đây KHÔNG có Docker: các lệnh \
`docker compose exec ...` trong CLAUDE.md không chạy được, đừng thử — gọi thẳng `python`/`python3`. \
Lệnh nào bị báo "requires approval" là ngoài danh sách cho phép, thử lại cũng vậy, đừng lặp. \
Sửa `frontend-v2/` thì tự kiểm bằng ĐÚNG hai lệnh: `npm --prefix frontend-v2 run typecheck` và \
`npm --prefix frontend-v2 run test -- src/modules/<phân hệ vừa sửa>` (luôn kèm đường dẫn, KHÔNG chạy \
cả bộ). Sửa `frontend/` (bản cũ) thì kiểm kiểu bằng `npm --prefix frontend exec -- tsc --noEmit -p frontend`; \
bản cũ có sẵn vài lỗi kiểu ở tệp khác, chỉ cần tệp bạn sửa không có lỗi.
C7. Theo đúng phong cách mã quanh chỗ sửa; đọc CLAUDE.md và backend/.claude/rules/ trước khi viết. \
Tên hàm/biến/hằng tiếng Anh, chuỗi và chú thích tiếng Việt, không emoji.
C8. Không dọn dẹp, không đổi tên, không định dạng lại thứ không liên quan tới việc này.
C9. Tổng kết TRUNG THỰC: chưa chạy được thì nói chưa chạy, test đỏ thì nói đỏ.
C10. KHÔNG commit, KHÔNG git push, KHÔNG git merge, KHÔNG đổi nhánh — runner tự commit sau.

## Khi nào phải dừng và ghi lý do thay vì cố làm (§D)
Kế hoạch mâu thuẫn với mã thật · phải đụng tệp cấm ở C4 · cần migration · cần thay đổi \
hợp đồng API đang có màn hình dùng · bài kiểm cũ đỏ vì thay đổi cần thiết · làm xong thì vượt \
trần tệp{hard_extra}. Gặp một trong các ca đó: dừng, KHÔNG sửa nửa chừng, viết tổng kết nêu rõ \
ca nào và cần đại ca quyết gì.
{soft_rule}

## Cuối cùng, in ra một mục Markdown tên "TỔNG KẾT" gồm đúng bốn phần, rồi MỘT dòng TÓM TẮT
1. Từng tệp đã sửa: đường dẫn + giải thích ngắn vì sao sửa và sửa gì.
2. Bài kiểm đã chạy: lệnh nguyên văn + kết quả (số xanh/đỏ).
3. Tệp ngoài kế hoạch (nếu có) + lý do.
4. Tự quyết không hỏi (mỗi dòng mở đầu «Theo QĐ-xx:» hoặc «Em giả định:») · chưa làm được / \
cần đại ca quyết (nếu có).
Dòng CUỐI CÙNG mở đầu đúng chữ `TÓM TẮT:` rồi 1-3 câu cho đại ca đọc trên điện thoại: đã sửa LOGIC gì \
(không liệt kê tệp), đã kiểm gì, đánh giá rủi ro. Đại ca chỉ đọc dòng này; muốn chi tiết sẽ hỏi.
"""


# ---------------------------------------------------------------------------
# Ảnh chụp đại ca gửi kèm (ai-CR-035)
# ---------------------------------------------------------------------------
def task_images(db: Session, task: AgentTask) -> list[str]:
    """Đường dẫn ảnh (còn trên đĩa) của mọi tin đã gắn vào việc này."""
    rows = (db.query(AgentMessage).filter(AgentMessage.task_id == task.id).order_by(AgentMessage.id).all())
    paths: list[str] = []
    for r in rows:
        for f in r.files or []:
            p = str((f or {}).get("path") or "")
            if p and p not in paths and Path(p).is_file():
                paths.append(p)
    return paths


def image_block(images: list[str]) -> list[str]:
    if not images:
        return []
    return ["## Ảnh chụp đại ca gửi kèm",
            "Mở TỪNG ảnh bằng công cụ Read trước khi kết luận — ảnh cho thấy màn hình và lỗi thật, "
            "chữ mô tả có thể thiếu:",
            *[f"- `{p}`" for p in images], ""]


def _with_files_dir(cmd: list[str]) -> list[str]:
    """Mở thư mục ảnh cho Read của Claude Code (nằm ngoài worktree nên phải khai thêm)."""
    files_dir = settings.AGENT_FILES_DIR
    if files_dir and Path(files_dir).is_dir():
        cmd += ["--add-dir", files_dir]
    return cmd


def build_brief(task: AgentTask, docs: list[dict], *, from_scan: bool = False,
                images: list[str] | None = None) -> str:
    """Đề bài sửa mã. `from_scan=True` (ai-CR-024): đề bài đi TIẾP trong phiên rà soát — bỏ trích
    đoạn tài liệu và đoạn rà soát (đã nằm trong phiên), dặn dùng lại những gì đã đọc."""
    lines = [
        f"# Việc {task.code}: {task.title}", "",
        f"Bạn là {BOT_NAME}, bot sửa mã của Agent Hub (tự xưng «em», gọi người đọc tổng kết là «đại ca»), "
        "đang đứng trong một worktree sạch cắt từ nhánh "
        f"`{settings.AGENT_BASE_BRANCH}` của kho procurement-tool (ERP nội bộ DEGO). "
        "Làm đúng kế hoạch đã được duyệt dưới đây, rồi in tổng kết.", "",
    ]
    lines += image_block(images or [])
    if from_scan:
        lines += [
            "## Tiếp theo lượt rà soát",
            "Bạn ĐÃ rà soát việc này ở lượt trước trong chính phiên này và đã đọc các tệp liên quan. "
            "Lượt rà soát chỉ được đọc; từ lượt này bạn được SỬA theo kế hoạch đã duyệt. Dùng lại hiểu "
            "biết đó — KHÔNG đọc lại tệp đã đọc trừ phần sắp sửa, không rà lại thư viện dùng chung.", "",
        ]
    lines += [
        "## Yêu cầu gốc", task.summary or "(không có)", "",
        "## Kế hoạch đã duyệt", task.plan or "(không có)", "",
        "## Phạm vi tệp",
        *[f"- {f}" for f in (task.plan_files or [])],
        "",
    ]
    if task.test_plan:
        lines += ["## Kiểm thử dự kiến", task.test_plan, ""]
    if task.related_docs:
        lines += ["## Tài liệu bot quản lý đã tra (đọc trước khi sửa)"]
        lines += [f"- {d.get('path', '')}" for d in task.related_docs if isinstance(d, dict)]
        lines += [""]
    if docs and not from_scan:
        lines += ["## Trích đoạn tài liệu liên quan"]
        for d in docs[:4]:
            lines += [f"### {d.get('path', '')} — {d.get('title', '')}",
                      (d.get("text") or "")[:1500], ""]
    if not from_scan and (review := scan_message_for(task)):
        lines += ["## Kết quả rà soát mã trước khi lập kế hoạch (chính bạn đã đọc, ai-CR-017)",
                  review[:4000], ""]
    #  Sổ quyết định (ai-CR-015). Việc rủi ro cao không nạp sổ và giữ hai ca dừng cũ (luật 3).
    strict = int(task.risk_level or 0) >= RISK_HIGH
    book = "" if strict else playbook.prompt_block(task.risk_level)
    if book:
        lines += ["## Sổ quyết định của đại ca (tra TRƯỚC khi dừng để hỏi)", book, ""]
    if strict:
        hard_extra, soft_rule = (" · không tái hiện được lỗi · thiếu dữ liệu để quyết", "Việc này RỦI RO "
                                 "CAO: không tự giả định điều gì, chưa rõ là dừng và hỏi.")
    else:
        hard_extra, soft_rule = "", (
            "Không tái hiện được lỗi, hay thiếu dữ liệu để quyết, KHÔNG còn là lý do dừng: tra sổ quyết "
            "định ở trên, có mục khớp thì làm theo và ghi «Theo QĐ-xx: …»; không có thì chọn cách an "
            "toàn nhất, dễ đảo lại, và ghi «Em giả định: …». Trừ khi chỗ đó dính tiền, công nợ, phân "
            "quyền — thì dừng và hỏi.")
    lines += [_RULES_BRIEF.format(max_files=settings.AGENT_MAX_FILES_TOUCHED, hard_extra=hard_extra,
                                  soft_rule=soft_rule)]
    #  ai-CR-023: AI-0007 tiêu 61/80 lượt vào đọc thư viện dùng chung và màn khác rồi hết lượt.
    lines += ["", "## Ngân sách lượt",
              f"Bạn có tối đa {settings.AGENT_CODER_MAX_TURNS} lượt công cụ. Kết quả rà soát ở trên đã chỉ "
              "tệp và nguyên nhân: đọc thẳng các tệp đó (đọc cả tệp một lần, đừng đọc từng đoạn), KHÔNG rà "
              "thư viện dùng chung hay màn khác trừ khi thật cần. Sửa xong mới chạy kiểm."]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Gọi Claude Code
# ---------------------------------------------------------------------------
def parse_cli_json(stdout: str) -> dict:
    """Bóc JSON kết quả từ stdout của `claude -p --output-format json`.

    Stdout có thể lẫn dòng cảnh báo trước/sau khối JSON, nên lấy từ `{` đầu tới `}` cuối.
    """
    start, end = stdout.find("{"), stdout.rfind("}")
    if start < 0 or end <= start:
        raise CoderError(f"claude không trả JSON: {stdout.strip()[:500]}")
    try:
        data = json.loads(stdout[start:end + 1])
    except json.JSONDecodeError as e:
        raise CoderError(f"JSON của claude hỏng: {e}") from e
    if data.get("subtype") == "error_max_turns":
        raise MaxTurnsError(f"claude hết {data.get('num_turns') or '?'} lượt khi đang làm dở", data)
    if data.get("is_error") or str(data.get("subtype", "")).startswith("error"):
        status = data.get("api_error_status")
        hint = " (401: khóa CLAUDE_CODE_OAUTH_TOKEN hết hạn hoặc sai — chạy lại `claude setup-token`)" \
            if status == 401 else ""
        raise CoderError(f"claude báo lỗi [{data.get('subtype')}]: "
                         f"{str(data.get('result', ''))[:600]}{hint}")
    return data


def run_claude_continue(worktree: str, *, session_id: str, timeout: int) -> dict:
    """«Làm tiếp» (ai-CR-023): nối ĐÚNG phiên đã hết lượt, cùng quyền sửa, thêm CONTINUE_MAX_TURNS lượt."""
    cmd = [
        settings.AGENT_CODER_CMD, "-p",
        "--output-format", "json",
        "--permission-mode", "acceptEdits",
        "--allowedTools", allowed_tools(worktree),
        "--resume", session_id,
        "--max-turns", str(CONTINUE_MAX_TURNS),
    ]
    return _run_cli(_with_files_dir(cmd), _CONTINUE_BRIEF, worktree, timeout)


#  Vòng «Sửa cho xanh» (ai-CR-026): lỗi cổng kiểm đưa thẳng vào đúng phiên đã sửa.
FIX_GATE_MAX_TURNS = 40


def build_fix_gate_brief(gate: dict) -> str:
    parts = []
    if gate.get("backend", gate.get("status")) == "fail":
        parts.append(gate.get("output") or "")
    for key in ("frontend", "frontend_v1"):
        fe = gate.get(key) or {}
        if fe.get("status") == "fail":
            parts.append(fe.get("output") or "")
    failed = "\n\n".join(p for p in parts if p)[-6000:]
    return "\n".join([
        "Cổng kiểm của runner báo ĐỎ cho bản vá bạn vừa làm trong phiên này. Nguyên văn phần đỏ:",
        "```", failed or "(không có đuôi log)", "```",
        "Sửa cho XANH: nếu bài kiểm viết sai với hành vi đã duyệt thì sửa bài kiểm, nếu mã sai thì sửa "
        "mã — không xóa bài kiểm cho qua, không đổi phạm vi việc. Chạy lại đúng lệnh kiểm của phần đỏ "
        "(vitest theo thư mục: `npm --prefix frontend-v2 run test -- src/modules/<phân hệ>`), rồi in "
        "đúng mục TỔNG KẾT bốn phần như luật ở đề bài đầu.",
    ])


def run_claude_fix(worktree: str, brief: str, *, session_id: str, timeout: int) -> dict:
    cmd = [
        settings.AGENT_CODER_CMD, "-p",
        "--output-format", "json",
        "--permission-mode", "acceptEdits",
        "--allowedTools", allowed_tools(worktree),
        "--resume", session_id,
        "--max-turns", str(FIX_GATE_MAX_TURNS),
    ]
    return _run_cli(_with_files_dir(cmd), brief, worktree, timeout)


def dispatch_fix_gate(task_id: int) -> None:
    from app.core.celery_app import celery_app

    celery_app.send_task("agent.code_task", args=[task_id], kwargs={"fix_gate": True}, queue=queue_for(task_id))


_CONTINUE_BRIEF = (
    "Lượt trước hết lượt khi bạn đang sửa dở. Mọi thay đổi đã làm vẫn nằm trong worktree (xem bằng "
    "`git status` / `git diff`). Làm NỐT phần còn thiếu của kế hoạch đã duyệt, đừng đọc lại những gì đã "
    "đọc, chạy kiểm phần vừa sửa, rồi in đúng mục TỔNG KẾT bốn phần như luật ở đề bài đầu."
)


def run_claude(worktree: str, brief: str, *, session_id: str, timeout: int,
               resume: bool = False) -> dict:
    """Một lượt `claude -p`. Đề bài đi qua stdin (không lộ ở `ps`). Trả JSON đã bóc.
    `resume=True` (ai-CR-024): đi tiếp phiên có sẵn (phiên rà soát) thay vì mở phiên mới."""
    cmd = [
        settings.AGENT_CODER_CMD, "-p",
        "--output-format", "json",
        "--permission-mode", "acceptEdits",
        "--allowedTools", allowed_tools(worktree),
        "--resume" if resume else "--session-id", session_id,
        "--max-turns", str(settings.AGENT_CODER_MAX_TURNS),
    ]
    return _run_cli(_with_files_dir(cmd), brief, worktree, timeout)


def _run_cli(cmd: list[str], stdin: str, worktree: str, timeout: int) -> dict:
    """Spawn `claude` với môi trường sạch, đọc JSON. Dùng chung cho lượt sửa và lượt hỏi thêm."""
    _ensure_claude_config_dir()
    proc = subprocess.run(
        cmd, input=stdin, cwd=worktree, env=build_env(worktree),
        capture_output=True, text=True, timeout=timeout, **_drop_privileges_kwargs(),
    )
    if proc.stderr:
        #  stderr hay có dòng `[claude-code:unrecognized_model]` vô hại — ghi log, không coi là lỗi.
        log.info("agent_hub.coder: stderr claude: %s", proc.stderr.strip()[:500])
    if proc.returncode != 0 and not proc.stdout.strip():
        raise CoderError(f"claude thoát mã {proc.returncode}: {proc.stderr.strip()[:600]}")
    return parse_cli_json(proc.stdout)


# ---------------------------------------------------------------------------
# Luật C1 — lệch kế hoạch
# ---------------------------------------------------------------------------
def _is_test_file(path: str) -> bool:
    name = path.rsplit("/", 1)[-1]
    return any(fnmatch.fnmatch(path, p) or fnmatch.fnmatch(name, p) for p in _TEST_FILE_PATTERNS)


def is_in_plan(path: str, plan_files: list[str]) -> bool:
    for pf in plan_files:
        pf = pf.replace("\\", "/").strip().rstrip("/")
        while pf.startswith("./"):
            pf = pf[2:]
        if not pf:
            continue
        if path == pf or path.startswith(pf + "/") or fnmatch.fnmatch(path, pf):
            return True
    return False


def check_drift(touched: list[str], plan_files: list[str], *, max_files: int) -> str:
    """Trả lý do leo thang, rỗng nếu trong phạm vi cho phép."""
    banned = [f for f in touched if is_banned_path(f)]
    if banned:
        return "bot đã đụng tệp cấm: " + ", ".join(banned[:5])
    if len(touched) > max_files:
        return f"bot đụng {len(touched)} tệp, vượt trần {max_files} (luật C1)"
    #  Tệp bài kiểm và tài liệu `.md` không tính vào tỷ lệ lệch (QĐ-02 của sổ quyết định,
    #  ai-CR-015): sửa tài liệu cho khớp mã là việc nên làm, không phải đi lạc. Trần tổng số
    #  tệp ở trên vẫn đếm chúng. CLAUDE.md và .claude/ đã bị chặn ở bước tệp cấm phía trên.
    counted = [f for f in touched if not _is_test_file(f) and not f.lower().endswith(".md")]
    outside = [f for f in counted if not is_in_plan(f, plan_files or [])]
    if counted and len(outside) / len(counted) > DRIFT_RATIO:
        return (f"{len(outside)}/{len(counted)} tệp ngoài kế hoạch (>30%, luật C1): "
                + ", ".join(outside[:5]))
    return ""


# ---------------------------------------------------------------------------
# Cổng kiểm (luật C6)
# ---------------------------------------------------------------------------
def run_gate(worktree: str, touched: list[str], *, fe_note: str = "") -> dict:
    """Cổng kiểm của runner: pytest phần backend vừa đụng + (ai-CR-019) frontend-v2 nếu có đụng.

    Trả {status, tests, output, frontend}. status gộp: "fail" nếu một bên đỏ; "pass" nếu có bên
    xanh và không bên nào đỏ; "none" nếu không bên nào chạy. Frontend không cài được thư viện thì
    KHÔNG tính là xanh — thẻ nói rõ «chưa kiểm được».
    """
    backend = _run_backend_gate(worktree, touched)
    frontend = run_fe_gate(worktree, touched, note=fe_note)
    v1 = run_fe_v1_gate(worktree, touched)
    states = {backend["status"], frontend["status"], v1["status"]}
    status = "fail" if "fail" in states else ("pass" if "pass" in states else "none")
    output = backend["output"]
    for part in (frontend, v1):
        if part["status"] == "fail":
            output = (output + "\n\n" if output else "") + part["output"]
    return {"status": status, "tests": backend["tests"], "output": output[-GATE_TAIL:],
            "backend": backend["status"], "frontend": frontend, "frontend_v1": v1}


def _run_backend_gate(worktree: str, touched: list[str]) -> dict:
    tests = sorted(f for f in touched
                   if f.startswith("test/backend/") and f.rsplit("/", 1)[-1].startswith("test_")
                   and f.endswith(".py"))
    if not tests:
        return {"status": "none", "tests": [], "output": ""}
    cmd = ["python", "-m", "pytest", *tests, "-q", "-p", "no:cacheprovider"]
    try:
        proc = subprocess.run(
            cmd, cwd=worktree, env=build_env(worktree, with_token=False),
            capture_output=True, text=True, timeout=GATE_TIMEOUT, **_drop_privileges_kwargs(),
        )
    except subprocess.TimeoutExpired:
        return {"status": "fail", "tests": tests, "output": f"pytest quá {GATE_TIMEOUT}s, đã giết"}
    out = (proc.stdout + "\n" + proc.stderr).strip()
    return {"status": "pass" if proc.returncode == 0 else "fail",
            "tests": tests, "output": out[-GATE_TAIL:]}


# ---------------------------------------------------------------------------
# Cổng kiểm frontend-v2 (ai-CR-019)
# ---------------------------------------------------------------------------
#  Luật đại ca 17/09/2026: typecheck + lint cả cây là cổng nhẹ, vitest CHỈ theo thư mục vừa sửa.
#  Lint ở đây chỉ chạy trên tệp vừa đụng — lint cả cây thì lỗi cũ của người khác làm đỏ việc này.
FE_DIR = "frontend-v2"
FE_INSTALL_TIMEOUT = 1500
FE_TYPECHECK_TIMEOUT = 900
FE_LINT_TIMEOUT = 300
FE_VITEST_TIMEOUT = 900
FE_DEPS_KEEP = 2            # giữ bấy nhiêu bộ thư viện (theo lockfile) trong volume, cũ hơn thì xóa
#  ai-CR-057: thêm `src/app/` (components, pages, router…) — AI-0001 sửa `src/app/components/profile/…` mà cổng
#  kiểm bỏ qua vitest và Claude Code bị từ chối lệnh vì thư mục đó không có trong danh sách.
_FE_TEST_ROOTS = ("src/modules/", "src/shared/", "src/core/", "src/app/")


def _fe_deps_root() -> Path:
    return Path(settings.AGENT_WORKTREE_ROOT) / ".deps"


def _fe_env(worktree: str) -> dict[str, str]:
    env = build_env(worktree, with_token=False)
    env.update({
        "CI": "1",
        "npm_config_cache": str(_fe_deps_root() / ".npm-cache"),
        "npm_config_update_notifier": "false",
        #  tsc trên cả cây frontend-v2 ăn hơn 1 GB; mặc định của Node có thể không đủ.
        "NODE_OPTIONS": "--max-old-space-size=2048",
    })
    return env


def _chown_runner(path: Path) -> None:
    kwargs = _drop_privileges_kwargs()
    if kwargs:
        shutil.chown(path, user=kwargs["user"], group=kwargs["group"])


def ensure_fe_deps(worktree: str, fe_dir: str = FE_DIR) -> Path:
    """Thư mục `node_modules` đã cài cho lockfile của worktree này. Cài MỘT lần cho mỗi phiên bản
    `package-lock.json` (theo mã băm), các việc sau dùng lại. Ném CoderError nếu cài hỏng.
    `fe_dir` = `frontend-v2` (mặc định) hoặc `frontend` (bản cũ, ai-CR-034) — mỗi bên một bộ riêng."""
    lock = Path(worktree) / fe_dir / "package-lock.json"
    pkg = Path(worktree) / fe_dir / "package.json"
    if not lock.is_file() or not pkg.is_file():
        raise CoderError(f"worktree không có {fe_dir}/package-lock.json")
    digest = hashlib.sha256(lock.read_bytes()).hexdigest()[:16]
    root = _fe_deps_root()
    tag = _deps_tag(fe_dir)
    target = root / f"{tag}-{digest}"
    marker = target / "node_modules" / ".agent-hub-ok"
    if marker.exists():
        return target / "node_modules"
    for d in (root, root / ".npm-cache", target):
        d.mkdir(parents=True, exist_ok=True)
        _chown_runner(d)
    shutil.copyfile(pkg, target / "package.json")
    shutil.copyfile(lock, target / "package-lock.json")
    for f in ("package.json", "package-lock.json"):
        _chown_runner(target / f)
    try:
        proc = subprocess.run(
            ["npm", "ci", "--no-audit", "--no-fund", "--prefer-offline"], cwd=str(target),
            env=_fe_env(worktree), capture_output=True, text=True, timeout=FE_INSTALL_TIMEOUT,
            **_drop_privileges_kwargs(),
        )
    except subprocess.TimeoutExpired:
        raise CoderError(f"cài thư viện {fe_dir} quá {FE_INSTALL_TIMEOUT // 60} phút") from None
    if proc.returncode != 0:
        raise CoderError(f"cài thư viện {fe_dir} hỏng: " + (proc.stderr or proc.stdout).strip()[-600:])
    marker.write_text(digest, encoding="utf-8")
    _prune_fe_deps(keep=target, tag=tag)
    return target / "node_modules"


def _deps_tag(fe_dir: str) -> str:
    return "fe-v2" if fe_dir == FE_DIR else "fe-v1"


def _prune_fe_deps(*, keep: Path, tag: str = "fe-v2") -> None:
    """Xóa bộ thư viện cũ, mỗi bộ vài trăm MB. Giữ bộ vừa cài + mới nhất còn lại."""
    sets = sorted((p for p in _fe_deps_root().glob(f"{tag}-*") if p.is_dir() and p != keep),
                  key=lambda p: p.stat().st_mtime, reverse=True)
    for old in sets[max(FE_DEPS_KEEP - 1, 0):]:
        shutil.rmtree(old, ignore_errors=True)


def link_fe_deps(worktree: str, fe_dir: str = FE_DIR) -> str:
    """Gắn `<fe_dir>/node_modules` của worktree vào bộ thư viện dùng chung. Trả lý do nếu
    KHÔNG gắn được (rỗng = ổn). Không bao giờ ném lỗi: thiếu thư viện chỉ làm cổng frontend
    báo «chưa kiểm được», không được làm hỏng cả lượt sửa mã."""
    if not (Path(worktree) / fe_dir / "package.json").is_file():
        return f"worktree không có {fe_dir}"
    try:
        modules = ensure_fe_deps(worktree, fe_dir)
        link = Path(worktree) / fe_dir / "node_modules"
        if not link.exists() and not link.is_symlink():
            os.symlink(modules, link, target_is_directory=True)
        #  `.gitignore` của frontend-v2 đã có `node_modules` (khớp cả liên kết), nhưng khóa thêm
        #  ở exclude của chính worktree: lỡ ai sửa .gitignore thì `git add -A` cũng không nuốt nó.
        exclude = Path(_git(worktree, "rev-parse", "--git-path", "info/exclude", timeout=60).strip())
        if not exclude.is_absolute():
            exclude = Path(worktree) / exclude
        exclude.parent.mkdir(parents=True, exist_ok=True)
        line = f"/{fe_dir}/node_modules"
        current = exclude.read_text(encoding="utf-8") if exclude.exists() else ""
        if line not in current.splitlines():
            with exclude.open("a", encoding="utf-8") as fh:
                fh.write(("" if current.endswith("\n") or not current else "\n") + line + "\n")
        return ""
    except (CoderError, OSError) as e:
        log.warning("agent_hub.coder: không gắn được thư viện %s: %s", fe_dir, e)
        return str(e)[:400]


def fe_vitest_targets(touched: list[str]) -> list[str]:
    """Thư mục vitest cần chạy: phân hệ / khu dùng chung chứa tệp vừa đụng (luật 17/09)."""
    targets: list[str] = []
    for f in touched:
        if not f.startswith(FE_DIR + "/"):
            continue
        rel = f[len(FE_DIR) + 1:]
        for root in _FE_TEST_ROOTS:
            if rel.startswith(root):
                part = rel[len(root):].split("/", 1)[0]
                if part and "." not in part:
                    t = root + part
                    if t not in targets:
                        targets.append(t)
    return targets


def run_fe_gate(worktree: str, touched: list[str], *, note: str = "") -> dict:
    """typecheck cả cây · eslint tệp vừa đụng · vitest thư mục vừa đụng. Trả {status, steps, output}.

    status: "none" (không đụng frontend-v2) · "pass" · "fail" · "skip" (không kiểm được — thiếu
    thư viện; `output` nói lý do).
    """
    fe_files = [f for f in touched if f.startswith(FE_DIR + "/")]
    if not fe_files:
        return {"status": "none", "steps": [], "output": ""}
    fe_dir = Path(worktree) / FE_DIR
    if note or not (fe_dir / "node_modules").exists():
        return {"status": "skip", "steps": [],
                "output": note or "chưa có thư viện frontend-v2 trong worktree"}
    bin_dir = "node_modules/.bin/"
    lintable = [f[len(FE_DIR) + 1:] for f in fe_files
                if f.endswith((".ts", ".tsx")) and (Path(worktree) / f).exists()]
    targets = fe_vitest_targets(fe_files)
    plan = [("typecheck", [bin_dir + "tsc", "--noEmit"], FE_TYPECHECK_TIMEOUT)]
    if lintable:
        plan.append((f"lint {len(lintable)} tệp", [bin_dir + "eslint", *lintable], FE_LINT_TIMEOUT))
    if targets:
        plan.append(("vitest " + " ".join(targets), [bin_dir + "vitest", "run", *targets],
                     FE_VITEST_TIMEOUT))
    steps, outputs, failed = [], [], False
    for name, cmd, timeout in plan:
        try:
            proc = subprocess.run(cmd, cwd=str(fe_dir), env=_fe_env(worktree), capture_output=True,
                                  text=True, timeout=timeout, **_drop_privileges_kwargs())
            ok = proc.returncode == 0
            out = (proc.stdout + "\n" + proc.stderr).strip()
        except subprocess.TimeoutExpired:
            ok, out = False, f"{name} quá {timeout // 60} phút, đã giết"
        steps.append({"name": name, "ok": ok})
        if not ok:
            failed = True
            outputs.append(f"[{name}]\n{out[-1500:]}")
    return {"status": "fail" if failed else "pass", "steps": steps,
            "output": "\n\n".join(outputs)[-GATE_TAIL:]}


# ---------------------------------------------------------------------------
# Cổng kiểm `frontend/` bản cũ (ai-CR-034)
# ---------------------------------------------------------------------------
#  Bản cũ chỉ có typescript (không eslint, không vitest) và sẵn vài lỗi kiểu cũ. Câu Q4 để trống nên
#  em chọn: chạy tsc cả cây, CHỈ đỏ khi có lỗi nằm trong tệp bot vừa sửa; lỗi ở tệp khác ghi số đếm
#  («có thể là lỗi cũ») chứ không chặn.
V1_DIR = "frontend"
_TSC_ERROR = re.compile(r"^(?P<file>[^\s(][^(]*)\((?P<line>\d+),(?P<col>\d+)\): error TS\d+", re.MULTILINE)


def v1_files(paths: list[str]) -> list[str]:
    return [f for f in paths if f.startswith(V1_DIR + "/")]


def run_fe_v1_gate(worktree: str, touched: list[str]) -> dict:
    """tsc --noEmit trên `frontend/`, đỏ khi lỗi nằm trong tệp vừa đụng. Trả {status, steps, output, other}."""
    files = v1_files(touched)
    if not files:
        return {"status": "none", "steps": [], "output": ""}
    note = link_fe_deps(worktree, V1_DIR)
    fe_dir = Path(worktree) / V1_DIR
    if note or not (fe_dir / "node_modules").exists():
        return {"status": "skip", "steps": [], "output": note or "chưa có thư viện frontend/"}
    try:
        proc = subprocess.run(["node_modules/.bin/tsc", "--noEmit"], cwd=str(fe_dir), env=_fe_env(worktree),
                              capture_output=True, text=True, timeout=FE_TYPECHECK_TIMEOUT,
                              **_drop_privileges_kwargs())
        out = (proc.stdout + "\n" + proc.stderr).strip()
    except subprocess.TimeoutExpired:
        return {"status": "fail", "steps": [{"name": "typecheck", "ok": False}],
                "output": f"typecheck frontend/ quá {FE_TYPECHECK_TIMEOUT // 60} phút, đã giết"}
    mine = {f[len(V1_DIR) + 1:] for f in files}
    lines = out.splitlines()
    own, other = [], 0
    for ln in lines:
        m = _TSC_ERROR.match(ln)
        if not m:
            continue
        if m.group("file").replace("\\", "/") in mine:
            own.append(ln)
        else:
            other += 1
    ok = not own
    return {"status": "pass" if ok else "fail", "steps": [{"name": "typecheck tệp vừa sửa", "ok": ok}],
            "output": "[typecheck frontend/]\n" + "\n".join(own)[-1500:] if own else "", "other": other}


def fe_gate_line(gate: dict, *, html: bool) -> str:
    """Một dòng mô tả cổng frontend cho thẻ kết quả / thân PR. Rỗng nếu không đụng frontend-v2."""
    fe = gate.get("frontend") or {}
    status = fe.get("status")
    if status in (None, "none"):
        return ""
    b = (lambda t: f"<b>{t}</b>") if html else (lambda t: f"**{t}**")
    names = " · ".join(s["name"] for s in fe.get("steps") or [])
    if status == "pass":
        return f"Frontend v2: {b('XANH')} ({names})"
    if status == "fail":
        bad = " · ".join(s["name"] for s in fe.get("steps") or [] if not s["ok"])
        return f"Frontend v2: {b('ĐỎ')} ở {bad}"
    return f"Frontend v2: {b('CHƯA kiểm được')} ({fe.get('output', '')[:200]})"


def fe_v1_gate_line(gate: dict, *, html: bool) -> str:
    """Dòng cổng `frontend/` bản cũ (ai-CR-034). Rỗng nếu không đụng bản cũ."""
    v1 = gate.get("frontend_v1") or {}
    status = v1.get("status")
    if status in (None, "none"):
        return ""
    b = (lambda t: f"<b>{t}</b>") if html else (lambda t: f"**{t}**")
    other = int(v1.get("other") or 0)
    tail = f"; {other} lỗi kiểu ở tệp khác, có thể là lỗi cũ" if other else ""
    if status == "pass":
        return f"Frontend v1: {b('XANH')} (typecheck tệp vừa sửa{tail})"
    if status == "fail":
        return f"Frontend v1: {b('ĐỎ')} ở typecheck tệp vừa sửa{tail}"
    return f"Frontend v1: {b('CHƯA kiểm được')} ({v1.get('output', '')[:200]})"


# ---------------------------------------------------------------------------
# GĐ2a (ai-CR-012): đẩy nhánh lên GitHub + mở PR vào nhánh nền
# ---------------------------------------------------------------------------
def github_token() -> str:
    """Đọc PAT GitHub thẳng từ `os.environ` lúc cần, cùng nguyên tắc với khóa Claude (không qua Settings)."""
    token = os.environ.get("AGENT_GITHUB_TOKEN", "").strip()
    if not token:
        raise CoderError(
            "AGENT_GITHUB_TOKEN chưa khai trong .env của stack agenthub "
            "(PAT chi tiết: Contents + Pull requests, Read and write, chỉ kho "
            f"{settings.AGENT_GITHUB_REPO}; dán tay vào .env rồi --force-recreate agent-runner)")
    return token


def _repo_url() -> str:
    return f"https://github.com/{settings.AGENT_GITHUB_REPO}.git"


def _push_env() -> dict[str, str]:
    """Khóa đi vào `git push` bằng biến GIT_CONFIG_* (git >= 2.31): không nằm trên dòng lệnh
    nên không lộ qua `/proc/<pid>/cmdline`, và không ghi vào .git/config của worktree."""
    import base64

    basic = base64.b64encode(f"x-access-token:{github_token()}".encode()).decode()
    return {
        "GIT_CONFIG_COUNT": "1",
        "GIT_CONFIG_KEY_0": "http.extraheader",
        "GIT_CONFIG_VALUE_0": f"AUTHORIZATION: basic {basic}",
        "GIT_TERMINAL_PROMPT": "0",
    }


def push_branch(worktree: str, branch: str) -> None:
    """Đẩy HEAD của worktree lên `refs/heads/<branch>` của kho GitHub, ĐÈ (`--force`).

    Nhánh `bot/*` là của bot: chạy lại cùng một việc là cắt lại nhánh từ đầu nên lịch sử
    khác hẳn, không đè thì không bao giờ đẩy được lần hai. Đại ca không sửa tay trên nhánh
    bot — muốn sửa thì sửa sau khi merge, hoặc bấm Sửa để bot làm lại.
    """
    _git(worktree, "push", "--force", _repo_url(), f"HEAD:refs/heads/{branch}",
         timeout=300, extra_env=_push_env())


def github_request(method: str, path: str, payload: dict | None = None) -> tuple[int, dict | list]:
    """Một lượt gọi REST GitHub. Trả (mã HTTP, JSON). Bài kiểm chặn ở đây."""
    import requests

    resp = requests.request(
        method, f"{settings.AGENT_GITHUB_API_URL.rstrip('/')}{path}", json=payload, timeout=60,
        headers={"Authorization": f"Bearer {github_token()}",
                 "Accept": "application/vnd.github+json",
                 "X-GitHub-Api-Version": "2022-11-28"},
    )
    try:
        body = resp.json() if resp.content else {}
    except ValueError:
        body = {"raw": resp.text[:500]}
    return resp.status_code, body


def build_pr_body(task: AgentTask, *, files: list[dict], gate: dict, report: str,
                  session_id: str) -> str:
    """Mô tả PR bằng Markdown GitHub: việc · kế hoạch đã duyệt · tệp · cổng kiểm · tổng kết bot."""
    lines = ["## Việc", f"**{task.code}** · {task.title}", ""]
    if task.summary:
        lines += [task.summary.strip(), ""]
    if task.plan:
        lines += ["## Kế hoạch đã duyệt trên Telegram", task.plan.strip(), ""]
    if files:
        lines += ["## Tệp đã sửa"]
        for f in files:
            mark = "" if f["in_plan"] else " — NGOÀI kế hoạch"
            lines += [f"- `{f['path']}` +{f['added']}/−{f['deleted']}{mark}"]
        lines += [""]
    lines += ["## Cổng kiểm của runner (phần vừa sửa)"]
    backend = gate.get("backend", gate["status"])
    if backend == "pass":
        lines += [f"Backend XANH — {len(gate['tests'])} tệp bài kiểm: "
                  + ", ".join(f"`{t}`" for t in gate["tests"])]
    elif backend == "fail":
        lines += ["Backend ĐỎ", "```", gate["output"][-1500:], "```"]
    else:
        lines += ["Không có bài kiểm backend nào bị đụng."]
    if fe_line := fe_gate_line(gate, html=False):
        lines += [fe_line]
        if (gate.get("frontend") or {}).get("status") == "fail":
            lines += ["```", gate["frontend"]["output"][-1500:], "```"]
    if v1_line := fe_v1_gate_line(gate, html=False):
        lines += [v1_line]
        if (gate.get("frontend_v1") or {}).get("status") == "fail":
            lines += ["```", gate["frontend_v1"]["output"][-1500:], "```"]
    lines += [""]
    if report:
        lines += ["## Bot tổng kết", report[:20000], ""]
    lines += ["---",
              f"Nhánh do bot Agent Hub cắt từ `origin/{settings.AGENT_BASE_BRANCH}`, "
              f"phiên Claude Code `{session_id}`. Bot KHÔNG tự merge — đại ca đọc rồi merge tay.",
              "",
              "Generated with [Claude Code](https://claude.com/claude-code)"]
    return "\n".join(lines)


def open_pull_request(task: AgentTask, branch: str, *, body: str) -> dict:
    """Mở PR `branch` → nhánh nền. Đã có PR mở cho nhánh đó thì trả PR cũ thay vì lỗi 422."""
    repo = settings.AGENT_GITHUB_REPO
    owner = repo.split("/", 1)[0]
    title = f"{task.code}: {task.title}"[:250]
    status, data = github_request("POST", f"/repos/{repo}/pulls", {
        "title": title, "head": branch, "base": settings.AGENT_BASE_BRANCH, "body": body,
        "maintainer_can_modify": True,
    })
    if status == 201 and isinstance(data, dict):
        return {"url": data.get("html_url", ""), "number": int(data.get("number") or 0), "created": True}
    if status == 422:
        status2, found = github_request("GET", f"/repos/{repo}/pulls?head={owner}:{branch}&state=open")
        if status2 == 200 and isinstance(found, list) and found:
            first = found[0]
            return {"url": first.get("html_url", ""), "number": int(first.get("number") or 0),
                    "created": False}
    detail = data.get("message") if isinstance(data, dict) else ""
    raise CoderError(f"GitHub trả {status} khi mở PR: {str(detail or data)[:300]}")


def publish_branch(task: AgentTask, worktree: str, branch: str, *, files: list[dict], gate: dict,
                   report: str, session_id: str) -> dict:
    """Đẩy nhánh + mở PR, ghi `pr_url` vào việc. Ném CoderError nếu hỏng; người gọi quyết làm gì."""
    push_branch(worktree, branch)
    pr = open_pull_request(task, branch, body=build_pr_body(
        task, files=files, gate=gate, report=report, session_id=session_id))
    task.pr_url = (pr.get("url") or "")[:255]
    return pr


def _try_publish(task: AgentTask, worktree: str, branch: str, **kw) -> dict:
    """Bọc `publish_branch` cho lượt sửa mã: đẩy hỏng thì KHÔNG làm hỏng cả việc — commit đã có
    trong runner, thẻ kết quả ghi lý do và cho nút đẩy lại."""
    if not settings.AGENT_PR_ENABLED:
        return {"status": "off"}
    try:
        pr = publish_branch(task, worktree, branch, **kw)
    except Exception as e:  # noqa: BLE001 — mạng/GitHub hỏng cũng chỉ là "chưa đẩy được"
        log.exception("agent_hub.coder: đẩy GitHub / mở PR hỏng")
        return {"status": "error", "error": str(e)[:500]}
    return {"status": "ok", **pr}


def dispatch_publish(task_id: int) -> None:
    """Nút «Gửi link PR để anh tự merge» trên thẻ kết quả: việc vào hàng đợi của runner (chỗ có worktree)."""
    from app.core.celery_app import celery_app

    celery_app.send_task("agent.publish_task", args=[task_id], queue=queue_for(task_id))


def publish_existing(db: Session, task: AgentTask) -> dict:
    """Đẩy nhánh ĐÃ COMMIT của một việc đang ở trạm REVIEW (GĐ1 để lại trong volume runner).

    Tệp/cổng kiểm/tổng kết lấy lại từ `artifact` của lượt CODE gần nhất để mô tả PR giống hệt
    lượt tự đẩy. Chạy trong `agent-runner` vì chỉ nó nhìn thấy `/worktrees`.
    """
    from . import service

    chat_id = settings.AGENT_TELEGRAM_CHAT_ID
    worktree = str(Path(settings.AGENT_WORKTREE_ROOT) / task.code)
    branch = task.branch_name or branch_name_for(task)
    if not Path(worktree).exists():
        raise CoderError(f"worktree {worktree} không còn trong runner — bấm Sửa để bot làm lại")
    head_branch = _git(worktree, "rev-parse", "--abbrev-ref", "HEAD", timeout=60).strip()
    if head_branch != branch:
        raise CoderError(f"worktree đang ở nhánh {head_branch}, không phải {branch}")
    run = latest_code_run(db, task)
    art = (run.artifact if run is not None and isinstance(run.artifact, dict) else {}) or {}
    pr = publish_branch(task, worktree, branch,
                        files=art.get("files") or [],
                        gate=art.get("gate") or {"status": "none", "tests": [], "output": ""},
                        report=art.get("report") or "", session_id=art.get("session_id") or "")
    if run is not None:
        run.artifact = {**art, "pr": {"status": "ok", **pr}}
    db.commit()
    esc = telegram.esc
    verb = "Đã mở PR" if pr.get("created") else "PR đã có sẵn"
    service.reply(db, chat_id,
                  f"<b>{esc(task.code)}</b>: đã đẩy nhánh <code>{esc(branch)}</code> lên GitHub. "
                  f"{verb} #{pr.get('number')} vào <code>{esc(settings.AGENT_BASE_BRANCH)}</code>.",
                  task_id=task.id, buttons=[("Mở PR trên GitHub", pr.get("url") or "")])
    return pr


# ---------------------------------------------------------------------------
# Hỏi thêm về bản vá (GĐ2b phần 1, ai-CR-013)
# ---------------------------------------------------------------------------
#  Lượt hỏi thêm CHỈ ĐỌC: không Edit/Write, không pytest. Câu hỏi là để hiểu bản vá; muốn
#  đổi bản vá thì đại ca bấm Sửa, bot làm lại theo kế hoạch mới — hai đường không trộn.
ASK_TOOLS = ",".join([
    "Read", "Glob", "Grep",
    "Bash(git diff:*)", "Bash(git status:*)", "Bash(git log:*)",
])
ASK_MAX_TURNS = 15
ASK_TIMEOUT_SEC = 600


def claude_config_dir() -> str:
    """Chỗ Claude Code cất phiên (`projects/<cwd>/<session>.jsonl`), cấu hình và cache.

    Mặc định là `~/.claude` của người dùng `runner` — nằm trong LỚP GHI của container, mất
    sạch mỗi lần `up --force-recreate` (đổi .env là phải recreate). Phiên của AI-0005 mất
    đúng kiểu đó trước khi có nút hỏi thêm. Trỏ sang volume worktree để phiên sống cùng nhánh.
    """
    return str(Path(settings.AGENT_WORKTREE_ROOT) / ".claude")


def _ensure_claude_config_dir() -> None:
    path = Path(claude_config_dir())
    path.mkdir(parents=True, exist_ok=True)
    kwargs = _drop_privileges_kwargs()
    if kwargs:
        #  Worker là root, `claude` chạy dưới `runner`: thư mục phải thuộc runner, không thì
        #  CLI không ghi được phiên và lượt hỏi thêm sau đó báo "không có phiên".
        shutil.chown(path, user=kwargs["user"], group=kwargs["group"])


def build_question_brief(task: AgentTask, question: str) -> str:
    return "\n".join([
        f"Đại ca hỏi thêm về bản vá của việc {task.code} ({task.title}) mà bạn vừa làm trong "
        "phiên này. Trả lời bằng tiếng Việt, ngắn gọn, đi thẳng vào câu hỏi.",
        "Định dạng: Markdown đơn giản — chữ đậm, gạch đầu dòng, `mã` — KHÔNG bảng, KHÔNG tiêu "
        "đề, vì câu trả lời hiện trên Telegram.",
        "KHÔNG sửa tệp, KHÔNG chạy bài kiểm: lượt này chỉ đọc và giải thích. Nếu câu hỏi thực "
        "chất là yêu cầu đổi bản vá thì nói rõ điều đó và bảo đại ca bấm «Sửa» trên thẻ kế "
        "hoạch để bot làm lại, đừng tự sửa.",
        "",
        "Câu hỏi:",
        question.strip(),
    ])


def run_claude_resume(worktree: str, question: str, *, session_id: str, timeout: int) -> dict:
    """Một lượt `claude -p --resume <phiên>` chỉ đọc. Câu hỏi đi qua stdin như đề bài."""
    cmd = [
        settings.AGENT_CODER_CMD, "-p",
        "--output-format", "json",
        "--allowedTools", ASK_TOOLS,
        "--resume", session_id,
        "--max-turns", str(ASK_MAX_TURNS),
    ]
    return _run_cli(_with_files_dir(cmd), question, worktree, timeout)


def latest_code_run(db: Session, task: AgentTask) -> AgentRun | None:
    """Lượt CODE gần nhất đã xong của việc — nơi giữ `session_id`, tệp, cổng kiểm, tổng kết."""
    return (db.query(AgentRun)
            .filter(AgentRun.task_id == task.id, AgentRun.stage == STAGE_CODE,
                    AgentRun.status == RUN_OK)
            .order_by(AgentRun.id.desc()).first())


def session_id_for(db: Session, task: AgentTask) -> str:
    run = latest_code_run(db, task)
    art = (run.artifact if run is not None and isinstance(run.artifact, dict) else {}) or {}
    return str(art.get("session_id") or "")


def dispatch_question(task_id: int, message_id: int) -> None:
    """Câu hỏi về bản vá vào hàng đợi của runner (chỗ có worktree + phiên)."""
    from app.core.celery_app import celery_app

    celery_app.send_task("agent.ask_task", args=[task_id, message_id], queue=queue_for(task_id))


def answer_patch_question(db: Session, task: AgentTask, question: str) -> str:
    """Đưa câu hỏi của đại ca vào đúng phiên đã sửa việc, gửi câu trả lời lên Telegram.

    Ghi một dòng `tab_agent_run` trạm STAGE_ASK (token, chi phí ước, câu hỏi + câu trả lời).
    Câu trả lời gửi dạng Markdown -> HTML (`reply(markdown=True)`), sổ giữ bản Markdown gốc.
    """
    from . import service

    chat_id = settings.AGENT_TELEGRAM_CHAT_ID
    session_id = session_id_for(db, task)
    if not session_id:
        raise CoderError("việc này chưa có phiên sửa mã nào để hỏi")
    worktree = str(Path(settings.AGENT_WORKTREE_ROOT) / task.code)
    if not Path(worktree).exists():
        raise CoderError(f"worktree {worktree} không còn trong runner — bấm Sửa để bot làm lại")

    run = AgentRun(task_id=task.id, stage=STAGE_ASK, provider=PROVIDER, model=DEFAULT_MODEL,
                   status=RUN_RUNNING, started_at=datetime.now())
    db.add(run)
    db.commit()
    telegram.send_chat_action(chat_id)
    try:
        data = run_claude_resume(worktree, build_question_brief(task, question),
                                 session_id=session_id, timeout=ASK_TIMEOUT_SEC)
    except subprocess.TimeoutExpired:
        _close_run(run, status=RUN_ERROR, error=f"claude trả lời quá {ASK_TIMEOUT_SEC}s, đã giết")
        db.commit()
        raise CoderError(f"phiên trả lời quá {ASK_TIMEOUT_SEC // 60} phút, đã dừng") from None
    except CoderError as e:
        msg = str(e)
        if "No conversation found" in msg:
            msg = ("phiên Claude Code của việc này không còn trong runner (container dựng lại "
                   "trước khi có chỗ lưu phiên bền) — bấm Sửa để bot làm lại từ đầu")
        _close_run(run, status=RUN_ERROR, error=msg)
        db.commit()
        raise CoderError(msg) from None

    answer = str(data.get("result") or "").strip() or "(phiên không trả lời gì)"
    _close_run(run, status=RUN_OK, data=data, artifact={
        "session_id": session_id, "question": question[:4000], "answer": answer[:8000],
        "num_turns": data.get("num_turns"), "duration_ms": data.get("duration_ms"),
    })
    db.commit()
    service.reply(db, chat_id,
                  f"**{task.code}** — {answer}\n\n"
                  f"(Nhắn tiếp trong {int(service.FOLLOW_UP_WINDOW.total_seconds() // 60)} phút "
                  "là hỏi tiếp về bản vá này.)",
                  task_id=task.id, markdown=True, action=ACT_PATCH_ANSWER,
                  buttons=[("Hỏi tiếp", f"ask:{task.id}")])
    return answer


# ---------------------------------------------------------------------------
# Toàn bộ một lượt sửa mã (chạy trong `agent.code_task`)
# ---------------------------------------------------------------------------
def _start_run(db: Session, task_id: int) -> AgentRun:
    run = AgentRun(task_id=task_id, stage=STAGE_CODE, provider=PROVIDER, model=DEFAULT_MODEL,
                   status=RUN_RUNNING, started_at=datetime.now())
    db.add(run)
    db.flush()
    return run


def _close_run(run: AgentRun, *, status: int, error: str = "", data: dict | None = None,
               artifact: dict | None = None) -> None:
    run.finished_at = datetime.now()
    run.duration_ms = int((run.finished_at - run.started_at).total_seconds() * 1000)
    run.status = status
    if error:
        run.error = error[:2000]
    if data:
        usage = data.get("usage") or {}
        run.input_tokens = int(usage.get("input_tokens") or 0)
        run.output_tokens = int(usage.get("output_tokens") or 0)
        models = data.get("modelUsage") or {}
        if isinstance(models, dict) and models:
            run.model = str(next(iter(models)))[:80]
        #  Gói thuê bao không xuất hóa đơn theo lượt; số này là ƯỚC của CLI, ghi để so tương đối.
        run.cost_usd = float(data.get("total_cost_usd") or 0.0)
    if artifact is not None:
        run.artifact = artifact


def _parse_numstat(raw: str) -> dict[str, tuple[int, int]]:
    stats: dict[str, tuple[int, int]] = {}
    for line in raw.splitlines():
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        a, d, path = parts
        stats[path] = (int(a) if a.isdigit() else 0, int(d) if d.isdigit() else 0)
    return stats


#  Phiên rà soát cũ hơn chừng này thì không nối nữa: nhánh nền có thể đã đổi nhiều (ai-CR-024).
SCAN_REUSE_MAX_AGE_SEC = 6 * 3600


def scan_session_to_reuse(db: Session, task: AgentTask) -> str:
    """Phiên rà soát để lượt sửa mã đi tiếp (ai-CR-024), hoặc rỗng nếu không nên nối: không có lượt
    rà soát thành công, quá cũ, worktree không còn, hoặc worktree đã bẩn (có thay đổi lạ)."""
    run = latest_scan_run(db, task)
    art = run.artifact if run is not None and isinstance(run.artifact, dict) else {}
    sid = str(art.get("session_id") or "")
    if not sid or run.finished_at is None:
        return ""
    if (datetime.now() - run.finished_at).total_seconds() > SCAN_REUSE_MAX_AGE_SEC:
        return ""
    worktree = Path(settings.AGENT_WORKTREE_ROOT) / task.code
    if not worktree.exists():
        return ""
    try:
        dirty = _git(str(worktree), "status", "--porcelain", timeout=60).strip()
    except CoderError:
        return ""
    return "" if dirty else sid


def resumable_session(db: Session, task: AgentTask) -> str:
    """Phiên của lượt sửa mã gần nhất đã HẾT LƯỢT (còn nối được), hoặc rỗng."""
    run = (db.query(AgentRun).filter(AgentRun.task_id == task.id, AgentRun.stage == STAGE_CODE)
           .order_by(AgentRun.id.desc()).first())
    art = run.artifact if run is not None and isinstance(run.artifact, dict) else {}
    return str(art.get("session_id") or "") if art.get("stopped") == "max_turns" else ""


def dispatch_continue(task_id: int) -> None:
    from app.core.celery_app import celery_app

    celery_app.send_task("agent.code_task", args=[task_id], kwargs={"resume": True}, queue=queue_for(task_id))


def _stop_at_max_turns(db: Session, task: AgentTask, run: AgentRun, worktree: str, session_id: str,
                       err: MaxTurnsError) -> dict:
    """Hết lượt: giữ phần đã sửa + phiên, việc về «Đang hỏi lại», thẻ có nút «Làm tiếp» (ai-CR-023)."""
    from . import service

    _close_run(run, status=RUN_ERROR, error=str(err), data=err.data,
               artifact={"session_id": session_id, "stopped": "max_turns"})
    _git(worktree, "add", "-A", timeout=120)
    numstat = _parse_numstat(_git(worktree, "diff", "--cached", "--numstat", timeout=120))
    _git(worktree, "reset", "-q", timeout=120)
    added = sum(a for a, _d in numstat.values())
    deleted = sum(d for _a, d in numstat.values())
    task.status = ST_NEEDS_INPUT
    task.note = f"Hết lượt khi đang sửa dở ({len(numstat)} tệp đã sửa); bấm «Làm tiếp» để nối phiên."
    db.commit()
    esc = telegram.esc
    service.reply(db, settings.AGENT_TELEGRAM_CHAT_ID,
                  f"<b>{esc(task.code)}</b>: em hết lượt khi đang sửa dở — đã sửa {len(numstat)} tệp "
                  f"(+{added}/−{deleted} dòng), chưa xong hẳn. Phần đã sửa vẫn giữ nguyên. Bấm «Làm tiếp» "
                  f"để em nối đúng phiên cũ (thêm tối đa {CONTINUE_MAX_TURNS} lượt)."
                  + cmd_hint(f"Nhắn «làm tiếp {esc(task.code)}» để em làm tiếp, hoặc «bỏ {esc(task.code)}»."),
                  task_id=task.id, buttons=[("Làm tiếp", f"cont:{task.id}"), ("Bỏ việc này", f"no:{task.id}")])
    return {"task": task.code, "status": task.status, "files": len(numstat), "escalation": "max_turns"}


def run_code_task(db: Session, task: AgentTask, *, resume: bool = False, fix_gate: bool = False) -> dict:
    """Chạy trọn một lượt sửa mã cho `task` (đang ở ST_CODE). Tự ghi sổ, tự nhắn Telegram.

    `resume=True` (ai-CR-023): nối phiên đã hết lượt, trên đúng worktree đang dở, không cắt lại.
    Ném lỗi ra ngoài chỉ khi không tự xử được — `tasks.code_task` bắt và đóng FAILED.
    """
    from . import service  # import muộn: service import coder ở đầu tệp

    chat_id = settings.AGENT_TELEGRAM_CHAT_ID
    previous = resumable_session(db, task) if resume else ""
    if resume and not previous:
        raise CoderError("không còn phiên hết lượt nào để làm tiếp")
    fix_brief = ""
    if fix_gate:
        #  «Sửa cho xanh» (ai-CR-026): nối phiên của lượt sửa vừa xong, đưa kèm lỗi cổng kiểm.
        last = latest_code_run(db, task)
        art = (last.artifact if last is not None and isinstance(last.artifact, dict) else {}) or {}
        previous = str(art.get("session_id") or "")
        if not previous or (art.get("gate") or {}).get("status") != "fail":
            raise CoderError("không có lượt sửa mã nào đang đỏ để sửa cho xanh")
        if merged_sha_for(db, task):
            raise CoderError("bản vá đã gộp vào nhánh nền — sửa tiếp phải làm việc mới")
        fix_brief = build_fix_gate_brief(art["gate"])
    #  ai-CR-024: nối phiên rà soát (Claude đã đọc mã) thay vì mở phiên mới đọc lại từ đầu.
    scan_sid = "" if previous else scan_session_to_reuse(db, task)
    run = _start_run(db, task.id)
    session_id = previous or scan_sid or str(uuid.uuid4())
    #  Ghi phiên NGAY, trước lượt claude: hỏng hay hết lượt giữa chừng vẫn biết phiên nào để nối.
    run.artifact = {"session_id": session_id, "resumed": bool(previous), "from_scan": bool(scan_sid)}
    db.commit()

    if previous or scan_sid:
        #  Dùng lại ĐÚNG worktree phiên đã đọc: cắt lại thì mọi tệp bị coi là «đổi sau khi đọc» và
        #  Claude phải đọc lại hết — mất đúng cái lợi của việc nối phiên.
        worktree = str(Path(settings.AGENT_WORKTREE_ROOT) / task.code)
        if not Path(worktree).exists():
            raise CoderError(f"worktree {worktree} không còn — bấm Sửa để bot làm lại từ đầu")
        branch = task.branch_name or branch_name_for(task)
        task.branch_name = branch[:120]
        db.commit()
        if fix_gate:
            #  Gỡ commit cũ của bot, GIỮ thay đổi đã stage: vòng này commit lại trọn bản vá một lần,
            #  nhánh bot vẫn đúng một commit và tệp .diff vẫn là cả bản vá.
            subject = _git(worktree, "log", "-1", "--format=%s", timeout=60).strip()
            if subject.startswith(f"{task.code}:"):
                _git(worktree, "reset", "--soft", "HEAD~1", timeout=60)
    else:
        worktree, branch = prepare_worktree(task)
        task.branch_name = branch[:120]
        db.commit()
    #  ai-CR-019: thư viện frontend-v2 có sẵn TRƯỚC lượt claude, để nó tự chạy typecheck/vitest.
    fe_note = link_fe_deps(worktree)
    if v1_files(list(task.plan_files or [])):
        link_fe_deps(worktree, V1_DIR)     # ai-CR-034: kế hoạch đụng bản cũ thì cho nó tự kiểm được

    try:
        if fix_gate:
            data = run_claude_fix(worktree, fix_brief, session_id=session_id,
                                  timeout=settings.AGENT_RUN_TIMEOUT_SEC)
        elif previous:
            data = run_claude_continue(worktree, session_id=session_id,
                                       timeout=settings.AGENT_RUN_TIMEOUT_SEC)
        else:
            docs = memory.recall(f"{task.title}\n{task.summary}")
            images = task_images(db, task)
            try:
                data = run_claude(worktree, build_brief(task, docs, from_scan=bool(scan_sid), images=images),
                                  session_id=session_id, timeout=settings.AGENT_RUN_TIMEOUT_SEC,
                                  resume=bool(scan_sid))
            except CoderError as e:
                if not scan_sid or isinstance(e, MaxTurnsError) or "No conversation found" not in str(e):
                    raise
                #  Phiên rà soát đã mất: lùi về phiên mới như trước ai-CR-024, không hỏng việc.
                log.warning("agent_hub.coder: phiên rà soát %s mất, mở phiên mới", scan_sid)
                session_id = str(uuid.uuid4())
                run.artifact = {"session_id": session_id, "resumed": False, "from_scan": False}
                db.commit()
                data = run_claude(worktree, build_brief(task, docs, images=images), session_id=session_id,
                                  timeout=settings.AGENT_RUN_TIMEOUT_SEC)
    except MaxTurnsError as e:
        return _stop_at_max_turns(db, task, run, worktree, session_id, e)
    except subprocess.TimeoutExpired:
        _close_run(run, status=RUN_ERROR,
                   error=f"claude chạy quá {settings.AGENT_RUN_TIMEOUT_SEC}s, đã giết")
        db.commit()
        raise CoderError(f"bot sửa mã quá {settings.AGENT_RUN_TIMEOUT_SEC // 60} phút, đã dừng; "
                         "nhánh dở nằm trong runner, không commit") from None
    except CoderError as e:
        _close_run(run, status=RUN_ERROR, error=str(e))
        db.commit()
        raise

    report = str(data.get("result") or "").strip()
    _git(worktree, "add", "-A", timeout=120)
    touched = [ln.strip() for ln in _git(worktree, "diff", "--cached", "--name-only", timeout=120)
               .splitlines() if ln.strip()]
    numstat = _parse_numstat(_git(worktree, "diff", "--cached", "--numstat", timeout=120))
    patch = _git(worktree, "diff", "--cached", timeout=120)
    files = [{"path": f, "added": numstat.get(f, (0, 0))[0], "deleted": numstat.get(f, (0, 0))[1],
              "in_plan": is_in_plan(f, task.plan_files or []) or _is_test_file(f)}
             for f in touched]

    escalation = ""
    if not touched:
        escalation = "bot không sửa tệp nào — đọc tổng kết để biết nó vướng gì"
    else:
        escalation = check_drift(touched, task.plan_files or [],
                                 max_files=settings.AGENT_MAX_FILES_TOUCHED)

    gate = {"status": "none", "tests": [], "output": ""}
    pr: dict = {"status": "none"}
    if escalation:
        #  Leo thang: KHÔNG commit (luật C1). Bỏ stage nhưng giữ thay đổi trên đĩa cho ai muốn xem.
        _git(worktree, "reset", "-q", timeout=120)
        task.status = ST_NEEDS_INPUT
        task.note = f"Bot dừng: {escalation}"[:2000]
    else:
        gate = run_gate(worktree, touched, fe_note=fe_note)
        _git(worktree,
             "-c", "user.name=Agent Hub bot", "-c", "user.email=agent-hub@degoholding.vn",
             "commit", "-q", "-m",
             f"{task.code}: {task.title}\n\nPhiên Claude Code: {session_id}\n\n"
             "Co-Authored-By: Claude <noreply@anthropic.com>", timeout=120)
        task.status = ST_REVIEW
        pr = _try_publish(task, worktree, branch, files=files, gate=gate, report=report,
                          session_id=session_id)

    _close_run(run, status=RUN_OK, data=data, artifact={
        "session_id": session_id, "branch": branch, "files": files, "gate": gate,
        "escalation": escalation, "report": report[:8000], "pr": pr,
        "num_turns": data.get("num_turns"), "duration_ms": data.get("duration_ms"),
    })
    db.commit()

    send_review_card(db, task, run, files=files, gate=gate, escalation=escalation,
                     report=report, data=data, pr=pr)
    if patch.strip() and not settings.AGENT_TG_COMPACT:     # ai-CR-027: gọn thì không gửi .diff
        try:
            telegram.send_document(chat_id, f"{task.code}.diff", patch.encode("utf-8"),
                                   caption=f"Bản vá {telegram.esc(task.code)} · {len(files)} tệp",
                                   content_type="text/x-diff")
        except telegram.TelegramError:
            log.exception("agent_hub.coder: gửi tệp diff hỏng")
    return {"task": task.code, "status": task.status, "files": len(files), "escalation": escalation}


# ---------------------------------------------------------------------------
# Đo thời gian một việc (ai-CR-032)
# ---------------------------------------------------------------------------
#  Đại ca thấy AI-0007 mất ~33 phút mà không biết chậm ở đâu. Sổ lượt chạy đã có giờ bắt đầu/kết
#  thúc từng bước; dòng này cộng lại: bot chạy bao lâu ở từng bước, và phần còn lại là thời gian
#  nằm chờ (đại ca duyệt, runner bận việc khác, chờ hẹn giờ).
_TIMING_GROUPS = ((STAGE_SCAN, "rà soát"), (STAGE_PLAN, "kế hoạch"), (STAGE_CODE, "sửa mã"),
                  (STAGE_DEPLOY, "gộp/deploy"), (STAGE_REVERT, "thu hồi"), (STAGE_ASK, "hỏi thêm"))


def fmt_minutes(ms: int) -> str:
    """Số phút dạng Việt: «45 giây» · «6,6 phút» · «33 phút»."""
    sec = max(int(ms // 1000), 0)
    if sec < 60:
        return f"{sec} giây"
    minutes = sec / 60
    return (f"{minutes:.1f}".replace(".", ",") if minutes < 10 else f"{round(minutes)}") + " phút"


def timing_line(db: Session, task: AgentTask, *, now: datetime | None = None) -> str:
    """«Thời gian: 33 phút từ lúc nhận việc; bot chạy 24 phút (rà soát 6,6 · …); chờ 9 phút.»"""
    runs = (db.query(AgentRun).filter(AgentRun.task_id == task.id).order_by(AgentRun.id).all())
    now = now or datetime.now()
    per: dict[int, int] = {}
    for r in runs:
        ms = int(r.duration_ms or 0)
        if not ms and r.status == RUN_RUNNING and r.started_at:
            ms = int((now - r.started_at).total_seconds() * 1000)
        per[r.stage] = per.get(r.stage, 0) + max(ms, 0)
    parts = [f"{label} {fmt_minutes(per[stage])}" for stage, label in _TIMING_GROUPS if per.get(stage)]
    if not parts or task.created_at is None:
        return ""
    bot_ms = sum(per.get(stage, 0) for stage, _l in _TIMING_GROUPS)
    end = task.closed_at or now
    total_ms = max(int((end - task.created_at).total_seconds() * 1000), bot_ms)
    wait_ms = total_ms - bot_ms
    line = (f"Thời gian: {fmt_minutes(total_ms)} từ lúc nhận việc; bot chạy {fmt_minutes(bot_ms)} "
            f"({' · '.join(parts)})")
    if wait_ms >= 60_000:
        line += f"; chờ duyệt/hàng đợi {fmt_minutes(wait_ms)}"
    return line + "."


def cmd_hint(text: str) -> str:
    """Dòng gợi ý lệnh gõ bằng chữ, chỉ khi ở chế độ gọn (ai-CR-027; thẻ cũ đã có nút)."""
    return f"\n{text}" if settings.AGENT_TG_COMPACT else ""


_SUMMARY = re.compile(r"(?im)^\W*tóm tắt\W*:\s*(.+)$")


def report_summary(report: str) -> str:
    """Dòng «TÓM TẮT:» cuối tổng kết của bot (ai-CR-027); không có thì lấy đoạn đầu, cắt ngắn."""
    hits = _SUMMARY.findall(report or "")
    if hits:
        return hits[-1].strip().strip("*").strip()
    body = re.sub(r"(?m)^#+.*$|^\W*tổng kết\W*$", "", report or "", flags=re.IGNORECASE).strip()
    first = body.split("\n\n", 1)[0].strip()
    return first[:280] + ("…" if len(first) > 280 else "")


def _gate_brief(gate: dict) -> str:
    """Một dòng «đã kiểm gì» cho thẻ gọn."""
    parts = []
    backend = gate.get("backend", gate.get("status"))
    if backend == "pass":
        parts.append(f"backend XANH ({len(gate.get('tests') or [])} tệp bài kiểm)")
    elif backend == "fail":
        parts.append("backend ĐỎ")
    fe = gate.get("frontend") or {}
    if fe.get("status") == "pass":
        parts.append("giao diện v2 XANH (" + " · ".join(s["name"] for s in fe.get("steps") or []) + ")")
    elif fe.get("status") == "fail":
        parts.append("giao diện v2 ĐỎ ở " + " · ".join(s["name"] for s in fe.get("steps") or [] if not s["ok"]))
    elif fe.get("status") == "skip":
        parts.append("giao diện v2 CHƯA kiểm được")
    v1 = gate.get("frontend_v1") or {}
    if v1.get("status") == "pass":
        parts.append("giao diện v1 XANH (typecheck tệp vừa sửa)")
    elif v1.get("status") == "fail":
        parts.append("giao diện v1 ĐỎ ở typecheck tệp vừa sửa")
    elif v1.get("status") == "skip":
        parts.append("giao diện v1 CHƯA kiểm được")
    return "; ".join(parts) or "không có bài kiểm nào bị đụng"


def send_compact_review_card(db: Session, task: AgentTask, *, gate: dict, escalation: str,
                             report: str, pr: dict) -> None:
    """Thẻ kết quả GỌN (ai-CR-027): đã sửa logic gì · đã kiểm gì · đánh giá · lệnh nhắn tiếp."""
    from . import service

    esc = telegram.esc
    code = esc(task.code)
    lines = [f"<b>{code}</b> · {esc(task.title)}"]
    if escalation:
        lines += [f"<b>Em dừng, chưa commit:</b> {esc(escalation)}",
                  f"Nhắn «chi tiết {code}» để xem em vướng gì, hoặc «bỏ {code}»."]
    else:
        if summary := report_summary(report):
            lines += [service._card_md(summary, limit=900)]
        lines += [f"Đã kiểm: {esc(_gate_brief(gate))}."]
        if timing := timing_line(db, task):
            lines += [esc(timing)]
        if pr.get("status") == "ok" and pr.get("url"):
            lines += [f"PR: {esc(pr['url'])}"]
        if gate.get("status") == "fail":
            lines += [f"Nhắn «sửa cho xanh {code}» để em sửa cho qua cổng kiểm, «chi tiết {code}» để xem."]
        else:
            lines += [f"Nhắn «gộp {code}» để gộp vào <code>{esc(settings.AGENT_BASE_BRANCH)}</code> (chưa lên "
                      f"dev) · «gộp và deploy dev {code}» để làm cả hai · «chi tiết {code}» để xem kỹ."]
    service.reply(db, settings.AGENT_TELEGRAM_CHAT_ID, "\n".join(lines), task_id=task.id)


def send_review_card(db: Session, task: AgentTask, run: AgentRun, *, files: list[dict],
                     gate: dict, escalation: str, report: str, data: dict,
                     pr: dict | None = None) -> None:
    from . import service

    esc = telegram.esc
    pr = pr or {"status": "none"}
    if settings.AGENT_TG_COMPACT:
        send_compact_review_card(db, task, gate=gate, escalation=escalation, report=report, pr=pr)
        return
    added = sum(f["added"] for f in files)
    deleted = sum(f["deleted"] for f in files)
    minutes = round((data.get("duration_ms") or run.duration_ms or 0) / 60000, 1)
    head = [f"<b>{esc(task.code)}</b> · {esc(task.title)}"]
    if escalation:
        head += [f"<b>BOT DỪNG, KHÔNG COMMIT:</b> {esc(escalation)}"]
    else:
        head += [f"Nhánh <code>{esc(task.branch_name or '')}</code> đã commit trong runner."]
        if pr["status"] == "ok":
            head += [f"Đã đẩy GitHub, PR #{pr.get('number')} vào "
                     f"<code>{esc(settings.AGENT_BASE_BRANCH)}</code>: {esc(pr.get('url') or '')}"]
        elif pr["status"] == "error":
            head += [f"<b>Đẩy GitHub / mở PR HỎNG:</b> {esc(pr.get('error') or '')} — "
                     "sửa nguyên nhân rồi bấm nút đẩy lại bên dưới."]
        else:
            head += ["Chưa đẩy GitHub (AGENT_PR_ENABLED=false) — bấm nút bên dưới để đẩy + mở PR."]
    head += [f"{len(files)} tệp · +{added}/−{deleted} dòng · {data.get('num_turns') or '?'} lượt · "
             f"{minutes} phút · ~${float(data.get('total_cost_usd') or 0):.2f} (ước của CLI)", ""]
    if files:
        head += ["<b>Tệp đã sửa:</b>"]
        for f in files[:25]:
            mark = "" if f["in_plan"] else " — NGOÀI kế hoạch"
            head += [f"• <code>{esc(f['path'])}</code> +{f['added']}/−{f['deleted']}{mark}"]
        head += [""]
    backend = gate.get("backend", gate["status"])
    if backend == "pass":
        head += [f"Cổng kiểm: <b>XANH</b> ({len(gate['tests'])} tệp bài kiểm)"]
    elif backend == "fail":
        head += ["Cổng kiểm: <b>ĐỎ</b>", f"<pre>{esc(gate['output'][-700:])}</pre>"]
    else:
        head += ["Cổng kiểm: không có bài kiểm backend nào bị đụng"]
    #  ai-CR-019: dòng riêng cho frontend-v2 (typecheck · lint tệp vừa đụng · vitest thư mục vừa đụng).
    if fe_line := fe_gate_line(gate, html=True):
        head += [fe_line]
        if (gate.get("frontend") or {}).get("status") == "fail":
            head += [f"<pre>{esc(gate['frontend']['output'][-700:])}</pre>"]
    if v1_line := fe_v1_gate_line(gate, html=True):
        head += [v1_line]
        if (gate.get("frontend_v1") or {}).get("status") == "fail":
            head += [f"<pre>{esc(gate['frontend_v1']['output'][-700:])}</pre>"]
    if timing := timing_line(db, task):
        head += [esc(timing)]
    tail = ["", "Bấm «Hỏi thêm» rồi nhắn câu hỏi: em đưa cho đúng phiên đã sửa việc này trả lời."]
    room = CARD_BUDGET - len("\n".join(head)) - len("\n".join(tail)) - 40
    body = []
    if report and room > 200:
        clipped = report if len(report) <= room else report[:room] + "…"
        #  Tổng kết của bot là Markdown (tiêu đề, `**đậm**`, danh sách): đổi sang HTML Telegram
        #  như câu trả lời của Trợ lý AI, thay vì in thô dấu sao (ai-CR-013). Thẻ HTML làm
        #  chuỗi dài ra chút; vượt quá chỗ chừa thì lùi về bản chữ thường đã thoát.
        rendered = telegram.md_to_html(clipped)
        if len(rendered) > room + 300:
            rendered = esc(clipped)
        body = ["", "<b>Bot tổng kết:</b>", rendered]
    buttons: list[tuple[str, str]] = []
    if not escalation and gate.get("status") == "fail":
        #  ai-CR-026: cổng đỏ thì lối đầu tiên là để bot tự sửa cho xanh trong đúng phiên đó.
        buttons.append(("Sửa cho xanh", f"fixg:{task.id}"))
    if not escalation:
        #  Đại ca chốt 23/09: đường MẶC ĐỊNH là bot gộp theo lệnh (nút này chỉ mở thẻ hỏi, gộp
        #  thật cần bấm đồng ý ở thẻ đó); link PR chỉ gửi khi đại ca muốn tự bấm merge trên GitHub.
        if settings.AGENT_DEPLOY_ENABLED:
            buttons.append(("Gộp erp-v2 + deploy dev", f"mg:{task.id}"))
        if pr["status"] == "ok" and pr.get("url"):
            buttons.append(("Mở PR trên GitHub", pr["url"]))
        elif pr["status"] == "error":
            buttons.append(("Đẩy GitHub lại", f"pr:{task.id}"))
        else:
            buttons.append(("Gửi link PR để anh tự merge", f"pr:{task.id}"))
    #  Có phiên là hỏi được, kể cả khi bot dừng vì lệch kế hoạch — lúc đó càng cần hỏi vì sao.
    buttons.append(("Hỏi thêm về bản vá", f"ask:{task.id}"))
    buttons.append(("Bỏ việc này", f"no:{task.id}"))
    service.reply(db, settings.AGENT_TELEGRAM_CHAT_ID, "\n".join(head + body + tail),
                  task_id=task.id, buttons=buttons)


# ---------------------------------------------------------------------------
# Gộp vào nhánh nền + deploy thử lên dev VPS (GĐ2b·2, ai-CR-014)
# ---------------------------------------------------------------------------
#  Đại ca chốt 22/09/2026 bốn điều: (1) bot đẩy nhánh của mình xong thì HỎI, đồng ý mới gộp
#  thẳng vào erp-v2 + deploy dev, đổi ý thì thu hồi; (2) dùng đúng khóa SSH đang có trên máy,
#  mount vào runner; (3) "hỏi trước một tiếng" nghĩa là hỏi để xác nhận — đồng ý thì chạy ngay,
#  hoặc đại ca hẹn giờ; (4) branch protection để nguyên, gộp là phải hỏi.
#
#  Ba ranh giới của khối này:
#    - `ssh` chạy bằng CHÍNH tiến trình worker (root), KHÔNG hạ xuống `runner`: khóa nằm dưới
#      /root (0700) để tiến trình `claude` (uid 1000) không đọc được. Đây là ngoại lệ có chủ ý
#      của luật hạ quyền, và là lý do lệnh gửi lên VPS là chuỗi CỐ ĐỊNH dựng từ settings, không
#      có một chữ nào từ bản vá hay từ Telegram lọt vào.
#    - Đẩy nhánh nền KHÔNG --force; bị từ chối (ai đó vừa đẩy) thì báo và để đại ca bấm lại.
#    - Không có gì chạy nếu không có dòng sổ STAGE_DEPLOY do nút bấm/giờ hẹn tạo ra.
DEPLOY_TIMEOUT_SEC = 1500        # fetch + build lại api/erp trên VPS thường 5-12 phút
SSH_CONNECT_TIMEOUT = 20
HEALTH_ATTEMPTS = 12
HEALTH_DELAY_SEC = 10
MERGE_BRANCH = "agent-merge"     # worktree riêng để gộp; không đụng worktree của việc
_DEPLOY_SERVICES_BY_PREFIX = (
    ("backend/", ("api", "celery-worker", "celery-beat")),
    ("frontend-v2/", ("erp",)),
    ("frontend/", ("web",)),
    ("help-center/", ("help",)),
)
#  Danh tính commit gộp/thu hồi đi bằng biến môi trường (không `-c` trên dòng lệnh) để
#  `_git` báo lỗi vẫn đọc ra "git merge lỗi" thay vì "git -c lỗi".
_GIT_IDENTITY_ENV = {
    "GIT_AUTHOR_NAME": "Agent Hub bot", "GIT_AUTHOR_EMAIL": "agent-hub@degoholding.vn",
    "GIT_COMMITTER_NAME": "Agent Hub bot", "GIT_COMMITTER_EMAIL": "agent-hub@degoholding.vn",
}


def deploy_services_for(paths: list[str]) -> list[str]:
    """Đụng thư mục nào thì build lại service đó (bảng ánh xạ §C quy trình deploy). Thứ tự cố định."""
    picked: list[str] = []
    for prefix, services in _DEPLOY_SERVICES_BY_PREFIX:
        if any(p.startswith(prefix) for p in paths):
            picked.extend(s for s in services if s not in picked)
    return picked


def _ssh_key_path() -> str:
    path = Path(settings.AGENT_VPS_SSH_KEY_PATH)
    try:
        head = path.read_text(encoding="utf-8", errors="replace")[:200]
    except OSError:
        head = ""
    if "PRIVATE KEY" not in head:
        raise CoderError(
            f"khóa SSH chưa mount vào runner ({path}): khai AGENT_VPS_SSH_KEY_FILE trong .env rồi "
            "`up -d --force-recreate --no-deps agent-runner`")
    return str(path)


@contextmanager
def _ssh_key_file():
    """Bản chép 0600 tạm của khóa: bind mount từ Windows là 0644/0755, ssh từ chối khóa rộng quyền.
    Xóa ngay sau lượt ssh, kể cả khi hỏng. Đổi CRLF -> LF vì tệp đi từ máy Windows."""
    src = _ssh_key_path()
    data = Path(src).read_bytes().replace(b"\r\n", b"\n")
    fd, tmp = tempfile.mkstemp(prefix="agent-vps-", dir="/root" if os.path.isdir("/root") else None)
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
        os.chmod(tmp, 0o600)
        yield tmp
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass


def _ssh_cmd(key: str) -> list[str]:
    if not settings.AGENT_VPS_HOST or not settings.AGENT_VPS_USER:
        raise CoderError("chưa khai AGENT_VPS_HOST / AGENT_VPS_USER trong .env")
    known = str(Path(settings.AGENT_WORKTREE_ROOT) / ".known_hosts")
    return [
        "ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=accept-new",
        "-o", f"UserKnownHostsFile={known}", "-o", f"ConnectTimeout={SSH_CONNECT_TIMEOUT}",
        "-p", str(settings.AGENT_VPS_PORT), "-i", key,
        f"{settings.AGENT_VPS_USER}@{settings.AGENT_VPS_HOST}", "bash", "-s",
    ]


def run_ssh(script: str, *, timeout: int = DEPLOY_TIMEOUT_SEC) -> str:
    """Chạy `script` bằng `bash -s` trên VPS, script đi qua stdin (không lên dòng lệnh, không lên
    lịch sử shell của VPS). Chạy bằng tiến trình worker (root), môi trường sạch, KHÔNG hạ quyền
    — xem chú thích đầu khối. Trả stdout+stderr; rc != 0 thì ném CoderError kèm đuôi output."""
    env = {"PATH": "/usr/local/bin:/usr/bin:/bin", "HOME": "/root", "LANG": "C.UTF-8"}
    with _ssh_key_file() as key:
        proc = subprocess.run(_ssh_cmd(key), input=script, env=env, capture_output=True,
                              text=True, timeout=timeout)
    out = (proc.stdout or "") + (("\n" + proc.stderr) if proc.stderr else "")
    if proc.returncode != 0:
        raise CoderError(f"ssh/deploy lỗi (rc={proc.returncode}): {out.strip()[-1200:]}")
    return out


def deploy_script(services: list[str]) -> str:
    """Kịch bản deploy dev y hệt §C quy trình: reset cứng về origin/<nhánh nền> rồi build lại đúng
    service. Mọi mảnh đều từ settings — không nhận chữ từ bản vá hay Telegram."""
    base = settings.AGENT_BASE_BRANCH
    lines = [
        "set -euo pipefail",
        f"cd {settings.AGENT_VPS_DEV_DIR}",
        "git fetch origin",
        f"git reset --hard origin/{base}",
        'echo "HEAD=$(git rev-parse HEAD)"',
    ]
    if services:
        lines.append(f"docker compose {settings.AGENT_VPS_DEV_COMPOSE_ARGS} up -d --build "
                     + " ".join(services))
    else:
        lines.append('echo "Không có service nào cần build lại (chỉ đổi doc/test)."')
    return "\n".join(lines) + "\n"


def _parse_head(output: str) -> str:
    m = re.search(r"^HEAD=([0-9a-f]{7,40})\s*$", output, re.MULTILINE)
    return m.group(1) if m else ""


def wait_dev_health() -> int:
    """Gõ health URL tới khi 200 hoặc hết lượt. Trả mã HTTP cuối (0 = không nối được). Không ném:
    deploy đã chạy rồi, health đỏ là thông tin cho thẻ, không phải lý do quay lui."""
    url = settings.AGENT_DEV_HEALTH_URL
    if not url:
        return -1
    import requests

    code = 0
    for _ in range(HEALTH_ATTEMPTS):
        try:
            code = requests.get(url, timeout=10).status_code
        except requests.RequestException:
            code = 0
        if code == 200:
            return code
        time.sleep(HEALTH_DELAY_SEC)
    return code


def _merge_worktree() -> str:
    """Worktree `agent-merge` cắt lại từ origin/<nền> mỗi lượt — sạch, không dính lượt trước."""
    root = Path(settings.AGENT_WORKTREE_ROOT)
    base = root / "base"
    if not (base / "HEAD").exists() and not (base / ".git").exists():
        raise CoderError("runner chưa có kho base — chưa có việc nào chạy qua bậc 2")
    fetch_base(str(base))
    wt = root / "merge"
    if wt.exists():
        try:
            _git(str(base), "worktree", "remove", "--force", str(wt), timeout=120)
        except CoderError:
            shutil.rmtree(wt, ignore_errors=True)
    _git(str(base), "worktree", "prune", timeout=120)
    _git(str(base), "worktree", "add", "-B", MERGE_BRANCH, str(wt),
         f"origin/{settings.AGENT_BASE_BRANCH}", timeout=300)
    return str(wt)


def _push_base_branch(worktree: str) -> None:
    """Đẩy HEAD lên nhánh nền, KHÔNG --force: nhánh nền là của cả đội, bị từ chối thì thôi."""
    _git(worktree, "push", _repo_url(), f"HEAD:refs/heads/{settings.AGENT_BASE_BRANCH}",
         timeout=300, extra_env=_push_env())


def merge_into_base(task: AgentTask) -> str:
    """merge --no-ff nhánh của việc vào nhánh nền rồi đẩy. Trả sha bản gộp. Xung đột -> abort + lỗi."""
    branch = task.branch_name or branch_name_for(task)
    wt = _merge_worktree()
    try:
        _git(wt, "rev-parse", "--verify", "--quiet", f"refs/heads/{branch}", timeout=60)
    except CoderError:
        raise CoderError(f"runner không còn nhánh {branch} — bấm Sửa để bot làm lại") from None
    msg = (f"Gộp {branch} vào {settings.AGENT_BASE_BRANCH} ({task.code}: {task.title})\n\n"
           "Đại ca đồng ý trên Telegram; bot Agent Hub gộp (ai-CR-014).")
    try:
        _git(wt, "merge", "--no-ff", "--no-edit", "-m", msg, branch, timeout=300,
             extra_env=_GIT_IDENTITY_ENV)
    except CoderError as e:
        try:
            _git(wt, "merge", "--abort", timeout=120)
        except CoderError:
            pass
        raise CoderError(f"gộp {branch} vào {settings.AGENT_BASE_BRANCH} bị xung đột, cần đại ca "
                         f"gộp tay: {str(e)[:400]}") from None
    sha = _git(wt, "rev-parse", "HEAD", timeout=60).strip()
    _push_base_branch(wt)
    return sha


def changed_paths_of_head(worktree: str) -> list[str]:
    """Tệp khác nhau giữa HEAD và cha thứ nhất — đúng phần bản gộp (hoặc bản thu hồi) mang vào."""
    raw = _git(worktree, "diff", "--name-only", "HEAD^1", "HEAD", timeout=120)
    return [p.strip() for p in raw.splitlines() if p.strip()]


def merged_sha_for(db: Session, task: AgentTask) -> str:
    """Sha bản gộp đang SỐNG trên nhánh nền của việc này, hoặc "" nếu chưa gộp / đã thu hồi.
    Quét sổ lượt chạy từ mới về cũ: gặp thu hồi OK trước là hết, gặp lượt deploy có `merged` là nó."""
    from sqlalchemy import select

    runs = db.scalars(
        select(AgentRun).where(AgentRun.task_id == task.id,
                               AgentRun.stage.in_((STAGE_DEPLOY, STAGE_REVERT)))
        .order_by(AgentRun.id.desc())
    ).all()
    for run in runs:
        art = run.artifact if isinstance(run.artifact, dict) else {}
        if run.stage == STAGE_REVERT and run.status == RUN_OK:
            return ""
        if run.stage == STAGE_DEPLOY and art.get("merged") and art.get("merge_sha"):
            return str(art["merge_sha"])
    return ""


def pending_deploy_run(db: Session, task: AgentTask) -> AgentRun | None:
    """Lượt gộp/thu hồi đang chờ hoặc đang chạy của việc (mỗi việc tối đa một lượt sống)."""
    from sqlalchemy import select

    return db.scalar(
        select(AgentRun).where(AgentRun.task_id == task.id, AgentRun.status == RUN_RUNNING,
                               AgentRun.stage.in_((STAGE_DEPLOY, STAGE_REVERT)))
        .order_by(AgentRun.id.desc()).limit(1)
    )


def _fail_deploy(db: Session, task: AgentTask, run: AgentRun, err: str, *, pushed: bool) -> dict:
    """Đóng lượt hỏng và đặt việc về đúng trạm: chưa đẩy nhánh nền -> REVIEW (như chưa có gì);
    đã đẩy -> PROD nhưng `deployed_dev_at` trống (mã đã ở erp-v2, VPS chưa lên) + nút chạy lại/thu hồi."""
    from . import service

    esc = telegram.esc
    _close_run(run, status=RUN_ERROR, error=err)
    art = run.artifact if isinstance(run.artifact, dict) else {}
    if pushed:
        task.status = ST_PROD
        task.deployed_dev_at = None
        text = (f"<b>{esc(task.code)}</b>: đã gộp vào <code>{esc(settings.AGENT_BASE_BRANCH)}</code> "
                f"(bản gộp <code>{esc(str(art.get('merge_sha') or '')[:10])}</code>) nhưng deploy dev "
                f"HỎNG: {esc(err[:700])}\n\nBấm «Deploy dev lại» sau khi sửa nguyên nhân, hoặc «Thu hồi» "
                "để bot revert bản gộp và deploy lại bản trước."
                + cmd_hint(f"Nhắn «deploy dev {esc(task.code)}» để deploy lại, «thu hồi {esc(task.code)}» "
                           "để revert."))
        buttons = [("Deploy dev lại", f"mgok:{task.id}"), ("Thu hồi khỏi erp-v2 + dev", f"rv:{task.id}")]
    else:
        task.status = ST_REVIEW
        text = (f"<b>{esc(task.code)}</b>: chưa gộp được vào "
                f"<code>{esc(settings.AGENT_BASE_BRANCH)}</code>: {esc(err[:700])}\n\n"
                "Nhánh nền không đổi. Sửa nguyên nhân rồi bấm gộp lại, hoặc đi đường PR."
                + cmd_hint(f"Nhắn «gộp {esc(task.code)}» để thử lại, «mở PR {esc(task.code)}» để đi "
                           "đường PR."))
        buttons = [("Gộp erp-v2 + deploy dev", f"mg:{task.id}"), ("Gửi link PR để anh tự merge", f"pr:{task.id}")]
    db.commit()
    service.reply(db, settings.AGENT_TELEGRAM_CHAT_ID, text, task_id=task.id, buttons=buttons)
    return {"status": "error", "reason": err[:500], "pushed": pushed}


def merge_and_deploy(db: Session, task: AgentTask, run: AgentRun) -> dict:
    """Một lượt: gộp (nếu chưa) -> đẩy -> [ssh deploy -> health] -> thẻ. Mọi lỗi thành thẻ + trạm đúng.

    Cờ `deploy` trong dòng sổ (ai-CR-029): đại ca nhắn «gộp» là CHỈ gộp vào nhánh nền, không lên dev;
    «deploy dev» / «gộp và deploy dev» mới SSH. Thiếu cờ (nút bấm cũ ghi «Gộp + deploy dev») = cả hai.

    Bước gộp + đẩy chỉ chạy khi việc CHƯA có bản gộp sống (`merged_sha_for`): «Deploy dev lại» sau
    một lượt deploy hỏng thì đi thẳng tới ssh. `run.artifact["merged"]` được ghi và commit NGAY sau
    khi đẩy, trước khi ssh — hỏng giữa chừng vẫn biết mã đã lên nhánh nền.
    """
    from . import service

    art = dict(run.artifact) if isinstance(run.artifact, dict) else {}
    deploy = art.get("deploy", True)
    task.status = ST_DEPLOYING
    db.commit()
    sha = merged_sha_for(db, task)
    pushed = bool(sha)
    merged_now = False
    try:
        if not pushed:
            sha = merge_into_base(task)
            art.update(merged=True, merge_sha=sha)
            run.artifact = art
            db.commit()
            pushed = merged_now = True
        if not deploy:
            task.status = ST_PROD
            task.deployed_dev_at = None
            _close_run(run, status=RUN_OK, artifact={**art, "merged": True, "merge_sha": sha})
            db.commit()
            send_merge_card(db, task, sha=sha)
            return {"status": "ok", "merge_sha": sha, "deployed": False}
        if merged_now:
            wt = str(Path(settings.AGENT_WORKTREE_ROOT) / "merge")
            try:
                paths = changed_paths_of_head(wt)
            except CoderError:
                paths = [f["path"] for f in _code_artifact(db, task).get("files") or []]
        else:
            #  Gộp từ lượt trước, nay mới deploy: HEAD của worktree gộp không còn là bản gộp này.
            paths = [f["path"] for f in _code_artifact(db, task).get("files") or []]
        services = deploy_services_for(paths)
        out = run_ssh(deploy_script(services))
        head = _parse_head(out)
        if head and not sha.startswith(head) and not head.startswith(sha):
            if merged_now:
                raise CoderError(f"VPS đang ở {head[:10]}, không phải bản vừa gộp {sha[:10]} — "
                                 "nhánh nền có bản đẩy khác chen vào?")
            #  Deploy sau: nhánh nền được phép đi tiếp, miễn còn chứa bản gộp của việc này.
            _require_ancestor(sha, head)
        health = wait_dev_health()
    except (CoderError, subprocess.TimeoutExpired, OSError) as e:
        err = str(e) if not isinstance(e, subprocess.TimeoutExpired) else \
            f"deploy quá {DEPLOY_TIMEOUT_SEC // 60} phút chưa xong"
        return _fail_deploy(db, task, run, err, pushed=pushed)

    task.status = ST_PROD
    task.deployed_dev_at = datetime.now()
    _close_run(run, status=RUN_OK, artifact={
        **art, "merged": True, "merge_sha": sha, "services": services, "health": health,
        "deployed_head": head, "ssh_tail": out[-1500:],
    })
    db.commit()
    send_deploy_card(db, task, sha=sha, services=services, health=health, reverted=False)
    return {"status": "ok", "merge_sha": sha, "services": services, "health": health}


def _require_ancestor(sha: str, head: str) -> None:
    wt = _merge_worktree()
    try:
        _git(wt, "merge-base", "--is-ancestor", sha, head, timeout=60)
    except CoderError:
        raise CoderError(f"VPS đang ở {head[:10]} mà bản này không chứa bản gộp {sha[:10]} "
                         "(ai đó đã revert/reset nhánh nền?)") from None


def send_merge_card(db: Session, task: AgentTask, *, sha: str) -> None:
    """Thẻ «chỉ gộp, chưa lên dev» (ai-CR-029)."""
    from . import service

    esc = telegram.esc
    code = esc(task.code)
    service.reply(db, settings.AGENT_TELEGRAM_CHAT_ID, "\n".join([
        f"<b>{code}</b> · {esc(task.title)}",
        f"Đã gộp vào <code>{esc(settings.AGENT_BASE_BRANCH)}</code> (bản gộp <code>{esc(sha[:10])}</code>). "
        "Dev CHƯA deploy.",
        f"Muốn lên dev thì nhắn «deploy dev {code}»; gộp nhầm thì «thu hồi {code}».",
    ]), task_id=task.id)


def _code_artifact(db: Session, task: AgentTask) -> dict:
    run = latest_code_run(db, task)
    return (run.artifact if run is not None and isinstance(run.artifact, dict) else {}) or {}


def revert_and_deploy(db: Session, task: AgentTask, run: AgentRun) -> dict:
    """Thu hồi: `git revert -m 1 <bản gộp>` trên nhánh nền -> đẩy -> deploy dev lại -> việc về
    «Đang hỏi lại» (đường tiếp là đại ca nói sửa gì rồi /gom; git không gộp lại cùng nhánh sau revert)."""
    sha = merged_sha_for(db, task)
    if not sha:
        return _fail_deploy(db, task, run, "việc này không có bản gộp nào đang sống trên nhánh nền",
                            pushed=False)
    task.status = ST_DEPLOYING
    db.commit()
    pushed = False
    try:
        wt = _merge_worktree()
        try:
            _git(wt, "merge-base", "--is-ancestor", sha, "HEAD", timeout=60)
        except CoderError:
            raise CoderError(f"bản gộp {sha[:10]} không còn trên {settings.AGENT_BASE_BRANCH} "
                             "(ai đó đã reset/revert tay?) — không có gì để thu hồi") from None
        try:
            _git(wt, "revert", "--no-edit", "-m", "1", sha, timeout=300, extra_env=_GIT_IDENTITY_ENV)
        except CoderError as e:
            try:
                _git(wt, "revert", "--abort", timeout=120)
            except CoderError:
                pass
            raise CoderError(f"revert bị xung đột (có bản đẩy sau chồng lên), cần đại ca gỡ tay: "
                             f"{str(e)[:400]}") from None
        revert_sha = _git(wt, "rev-parse", "HEAD", timeout=60).strip()
        _push_base_branch(wt)
        pushed = True
        #  Dev chưa từng lên bản này (chỉ gộp, ai-CR-029) thì thu hồi cũng chỉ ở nhánh nền.
        if task.deployed_dev_at:
            services = deploy_services_for(changed_paths_of_head(wt))
            out = run_ssh(deploy_script(services))
            health = wait_dev_health()
        else:
            services, out, health = [], "", -2
    except (CoderError, subprocess.TimeoutExpired, OSError) as e:
        err = str(e) if not isinstance(e, subprocess.TimeoutExpired) else \
            f"deploy quá {DEPLOY_TIMEOUT_SEC // 60} phút chưa xong"
        #  Thu hồi hỏng: bản gộp vẫn sống (chưa đẩy) hoặc đã revert nhưng VPS chưa lên — cả hai
        #  đều là "mã ở nhánh nền, dev lệch", nên để ở PROD với nút thu hồi lại.
        return _fail_deploy(db, task, run, "thu hồi: " + err, pushed=True)

    task.status = ST_NEEDS_INPUT
    task.deployed_dev_at = None
    task.note = (f"Đã thu hồi bản gộp {sha[:10]} khỏi {settings.AGENT_BASE_BRANCH} "
                 f"({now_local():%d/%m %H:%M}). Muốn làm lại thì nhắn sửa gì rồi /gom.")
    _close_run(run, status=RUN_OK, artifact={
        "merge_sha": sha, "revert_sha": revert_sha, "services": services, "health": health,
        "ssh_tail": out[-1500:],
    })
    db.commit()
    send_deploy_card(db, task, sha=revert_sha, services=services, health=health, reverted=True)
    return {"status": "ok", "revert_sha": revert_sha, "services": services, "health": health}


def send_deploy_card(db: Session, task: AgentTask, *, sha: str, services: list[str], health: int,
                     reverted: bool) -> None:
    from . import service

    esc = telegram.esc
    base = esc(settings.AGENT_BASE_BRANCH)
    if health == 200:
        health_line = "Health dev: <b>200 OK</b>"
    elif health == -1:
        health_line = "Health dev: không kiểm (AGENT_DEV_HEALTH_URL trống)"
    else:
        health_line = (f"Health dev: <b>CHƯA XANH</b> (mã {health or 'không nối được'} sau "
                       f"{HEALTH_ATTEMPTS * HEALTH_DELAY_SEC // 60} phút) — xem log trên VPS")
    svc = ", ".join(f"<code>{esc(s)}</code>" for s in services) or "không có (chỉ doc/test)"
    if reverted and health == -2:
        head = [f"<b>{esc(task.code)}</b> · {esc(task.title)}",
                f"Đã THU HỒI khỏi <code>{base}</code> bằng bản revert <code>{esc(sha[:10])}</code>. "
                "Dev chưa từng lên bản này nên không deploy lại.", "",
                "Việc về «Đang hỏi lại»: nhắn cần sửa gì rồi /gom để bot làm lại từ đầu."]
        buttons = [("Hỏi thêm về bản vá", f"ask:{task.id}"), ("Bỏ việc này", f"no:{task.id}")]
    elif reverted:
        head = [f"<b>{esc(task.code)}</b> · {esc(task.title)}",
                f"Đã THU HỒI khỏi <code>{base}</code> bằng bản revert <code>{esc(sha[:10])}</code> "
                "và deploy lại dev bản trước.",
                f"Build lại: {svc}", health_line, "",
                "Việc về «Đang hỏi lại»: nhắn cần sửa gì rồi /gom để bot làm lại từ đầu."]
        buttons = [("Hỏi thêm về bản vá", f"ask:{task.id}"), ("Bỏ việc này", f"no:{task.id}")]
    else:
        ui = settings.AGENT_DEV_UI_URL
        head = [f"<b>{esc(task.code)}</b> · {esc(task.title)}",
                f"Đã gộp vào <code>{base}</code> (bản gộp <code>{esc(sha[:10])}</code>) và deploy dev.",
                f"Build lại: {svc}", health_line]
        if timing := timing_line(db, task):
            head += [esc(timing)]
        if ui:
            head += [f"Thử ở: {esc(ui)}"]
        if settings.AGENT_TG_COMPACT:
            head += ["", f"Thử xong: ổn thì nhắn «xong {esc(task.code)}»; không ổn thì «thu hồi "
                         f"{esc(task.code)}» — em revert bản gộp và deploy lại bản trước."]
        else:
            head += ["", "Thử xong: ổn thì bấm «Xong»; không ổn thì «Thu hồi» — bot revert bản gộp "
                         "và deploy lại bản trước, hoặc nhắn sửa gì để bot làm tiếp."]
        buttons = [("Thu hồi khỏi erp-v2 + dev", f"rv:{task.id}"),
                   ("Hỏi thêm về bản vá", f"ask:{task.id}"), ("Xong, đóng việc", f"done:{task.id}")]
    service.reply(db, settings.AGENT_TELEGRAM_CHAT_ID, "\n".join(head), task_id=task.id,
                  buttons=buttons)


def dispatch_deploy(task_id: int, run_id: int) -> None:
    from app.core.celery_app import celery_app

    celery_app.send_task("agent.deploy_task", args=[task_id, run_id], queue=queue_for(task_id))


def dispatch_revert(task_id: int, run_id: int) -> None:
    from app.core.celery_app import celery_app

    celery_app.send_task("agent.revert_task", args=[task_id, run_id], queue=queue_for(task_id))


# ---------------------------------------------------------------------------
# Dọn nhánh sau khi việc đóng (ai-CR-033)
# ---------------------------------------------------------------------------
#  Đại ca để trống câu «xóa lúc gộp hay lúc xong»; em chọn lúc việc ĐÓNG («xong» hoặc «bỏ»): sau
#  gộp vẫn còn «thu hồi» và «hỏi thêm về bản vá» cần worktree + phiên. Bản gộp trên nhánh nền giữ
#  nguyên lịch sử nên xóa nhánh bot không mất gì. Chỉ đụng nhánh bắt đầu bằng `bot/`.
def dispatch_cleanup(task_id: int) -> None:
    from app.core.celery_app import celery_app

    celery_app.send_task("agent.cleanup_task", args=[task_id], queue=queue_for(task_id))


def cleanup_task_branch(db: Session, task: AgentTask) -> dict:
    """Gỡ worktree, xóa nhánh `bot/*` trong runner và trên GitHub. Không bao giờ ném lỗi nghiệp vụ."""
    branch = task.branch_name or ""
    if not branch.startswith("bot/"):
        return {"status": "skip", "reason": "việc không có nhánh bot"}
    root = Path(settings.AGENT_WORKTREE_ROOT)
    base = root / "base"
    wt = root / task.code
    done: list[str] = []
    if wt.exists():
        try:
            _git(str(base), "worktree", "remove", "--force", str(wt), timeout=120)
        except CoderError:
            shutil.rmtree(wt, ignore_errors=True)
        done.append("worktree")
    if (base / "HEAD").exists() or (base / ".git").exists():
        try:
            _git(str(base), "worktree", "prune", timeout=120)
            _git(str(base), "branch", "-D", branch, timeout=60)
            done.append("nhánh trong runner")
        except CoderError as e:
            log.info("agent_hub.coder: không xóa được nhánh %s trong runner: %s", branch, e)
        if github_token():
            try:
                _git(str(base), "push", _repo_url(), "--delete", f"refs/heads/{branch}", timeout=120,
                     extra_env=_push_env())
                done.append("nhánh trên GitHub")
            except CoderError as e:
                #  Nhánh chưa từng đẩy lên (không mở PR) thì GitHub báo không có ref — bình thường.
                if "remote ref does not exist" not in str(e):
                    log.warning("agent_hub.coder: xóa nhánh %s trên GitHub hỏng: %s", branch, e)
    if done:
        task.note = ((task.note + "\n") if task.note else "") + \
            f"Đã dọn nhánh {branch} ({', '.join(done)}) {now_local():%d/%m %H:%M}."
        db.commit()
    return {"status": "ok", "removed": done}


# ---------------------------------------------------------------------------
# Rà soát mã thật trước khi lập kế hoạch (ai-CR-017)
# ---------------------------------------------------------------------------
#  Đại ca 23/09/2026: "mọi việc đều rà soát". Ca AI-0006 là lý do: bước lập kế hoạch chỉ đọc tài
#  liệu nên đề xuất sửa lại đúng chỗ màn v1 đã sửa từ bao-CR-376, và ghi tên tệp thiếu đường dẫn.
SCAN_TOOLS = ",".join([
    "Read", "Glob", "Grep",
    "Bash(git diff:*)", "Bash(git status:*)", "Bash(git log:*)", "Bash(git show:*)",
])
SCAN_MAX_TURNS = 40
SCAN_TIMEOUT_SEC = 900
SCAN_MESSAGE_MAX = 3200
_SCAN_JSON = re.compile(r"```json\s*(\{.*?\})\s*```", re.DOTALL)


def local_docs_dir() -> str:
    """Thư mục `doc/` ở máy đại ca đã mount vào runner, hoặc rỗng nếu không có (ai-CR-018)."""
    path = (settings.AGENT_LOCAL_DOCS_DIR or "").strip()
    return path if path and Path(path).is_dir() else ""


def build_scan_brief(task: AgentTask, docs: list[dict], head: str, main_head: str = "",
                     images: list[str] | None = None) -> str:
    lines = [
        f"# Rà soát việc {task.code}: {task.title}", "",
        f"Bạn là {BOT_NAME}, trợ lý lập trình của DEGO (tự xưng «em», gọi người đọc là «đại ca»). Bạn "
        f"đang đứng trong một worktree cắt từ nhánh `{settings.AGENT_BASE_BRANCH}` MỚI NHẤT trên "
        f"GitHub (commit `{head[:10]}`) của kho procurement-tool (ERP nội bộ).",
        "Lượt này CHỈ ĐỌC: không sửa tệp, không chạy bài kiểm. Mục đích là hiểu đúng việc trước "
        "khi lập kế hoạch sửa.", "",
        "## Yêu cầu của đại ca", task.summary or task.title, "",
        *image_block(images or []),
        "## Việc cần làm",
        "1. Đọc phần liên quan của CLAUDE.md, rồi tìm đúng màn hình / API / tệp dính tới yêu cầu "
        "trong MÃ THẬT (đừng tin tài liệu hơn mã).",
        "2. Xem đã có ai sửa chưa: đọc mã hiện tại, `git log --oneline -S<chuỗi>` hoặc `git log "
        "--grep`. Việc dính giao diện thì so cả `frontend/` (v1) lẫn `frontend-v2/` (v2): bản nào "
        "đã có, bản nào chưa.",
        "3. Chỉ ra nguyên nhân khả dĩ nhất, có dẫn chứng `tệp:dòng`. Chưa chắc thì nói chưa chắc.",
        "4. Đề xuất hướng sửa ngắn gọn và các tệp sẽ phải đụng (đường dẫn ĐẦY ĐỦ từ gốc repo).",
        "5. Câu cần đại ca quyết: chỉ hỏi về NGHIỆP VỤ, không hỏi đường dẫn tệp hay tên hàm.", "",
    ]
    main = settings.AGENT_MAIN_BRANCH
    if main_head:
        lines += [
            f"## Nhánh `{main}` (bản đang chạy thật, commit `{main_head[:10]}`)",
            f"`origin/{main}` có sẵn trong kho. Lỗi thường được sửa ở `{main}` TRƯỚC rồi mới gộp sang "
            f"`{settings.AGENT_BASE_BRANCH}`. Bắt buộc chạy `git log --oneline "
            f"origin/{settings.AGENT_BASE_BRANCH}..origin/{main}` (commit có ở {main} mà chưa gộp) và "
            f"dò trong đó (`git show <commit>`, `git log origin/{main} -S<chuỗi>`). Việc đã được sửa ở "
            f"{main} mà chưa gộp thì ghi vào `already_fixed` kèm mã commit/CR và nói ngay ở Kết luận.", "",
        ]
    if local := local_docs_dir():
        lines += [
            "## Tài liệu mới nhất ở máy đại ca (chỉ đọc)",
            f"`{local}` là thư mục `doc/` trên máy đại ca, GỒM CẢ PHẦN CHƯA COMMIT. Tra ở đó trước "
            "khi kết luận, nhất là sổ thay đổi và nhật ký: "
            f"`{local}/tai-lieu-ky-thuat/change-log-bao.md`, `{local}/tai-lieu-ky-thuat/change-log.md`, "
            f"`{local}/tai-lieu-ky-thuat/nhat-ky-task.md`, `{local}/tai-lieu-chuc-nang/`. Tài liệu "
            "trong worktree có thể cũ hơn; mã thì tin worktree.", "",
        ]
    if docs:
        lines += ["## Tài liệu dự án có thể liên quan (có thể cũ, đối chiếu với mã)"]
        lines += [f"- {d.get('path', '')}" for d in docs[:6]]
        lines += [""]
    lines += [
        "## Định dạng trả lời (bắt buộc)",
        "Phần 1 là tin nhắn gửi đại ca trên Telegram: tiếng Việt, như một đồng nghiệp báo cáo sau "
        "khi đã đọc mã; dòng ĐẦU TIÊN bắt đầu bằng `**Kết luận:**` (không câu dẫn kiểu «giờ trả "
        "lời»); TỐI ĐA 12 dòng — chỉ kết luận, dẫn chứng chính và hướng sửa, bỏ phần kể lể; "
        "Markdown đơn giản (chữ đậm, gạch đầu dòng, `mã`), KHÔNG "
        "bảng, KHÔNG tiêu đề `#`. Câu cần đại ca quyết thì đưa vào `questions` của khối JSON.",
        "Phần 2, ở CUỐI CÙNG, đúng MỘT khối ```json gồm: "
        '{"already_fixed": "chỗ nào đã sửa rồi, hoặc rỗng", "root_cause": "một câu", '
        '"files": ["đường/dẫn/đầy/đủ"], "risk_level": 1, "questions": []}. '
        "`risk_level` = 3 nếu dính tiền, công nợ, phân quyền, cấu trúc cơ sở dữ liệu.",
    ]
    return "\n".join(lines)


def run_claude_scan(worktree: str, brief: str, *, session_id: str, timeout: int) -> dict:
    """Một lượt `claude -p` chỉ đọc (không `acceptEdits`, công cụ chỉ đọc) trên phiên mới."""
    cmd = [
        settings.AGENT_CODER_CMD, "-p",
        "--output-format", "json",
        "--allowedTools", SCAN_TOOLS,
        "--session-id", session_id,
        "--max-turns", str(SCAN_MAX_TURNS),
    ]
    if local := local_docs_dir():
        #  Read của Claude Code chỉ với tới thư mục làm việc; thư mục tài liệu ở máy phải mở thêm.
        cmd += ["--add-dir", local]
    return _run_cli(_with_files_dir(cmd), brief, worktree, timeout)


def parse_scan(text: str) -> tuple[str, dict]:
    """Tách (tin nhắn cho đại ca, JSON cuối). Không có JSON thì info rỗng, cả chữ là tin nhắn."""
    text = (text or "").strip()
    matches = list(_SCAN_JSON.finditer(text))
    if not matches:
        return text, {}
    last = matches[-1]
    try:
        info = json.loads(last.group(1))
    except json.JSONDecodeError:
        info = {}
    message = (text[:last.start()] + text[last.end():]).strip()
    #  Lượt thật đầu tiên (AI-0006) mở bằng câu nói với chính nó: "Đã xác minh… Giờ trả lời."
    #  Có dòng Kết luận ở gần đầu thì cắt mọi thứ trước nó.
    at = message.find("**Kết luận")
    if 0 < at <= 300:
        message = message[at:]
    if not isinstance(info, dict):
        info = {}
    info["questions"] = [str(q).strip() for q in info.get("questions") or [] if str(q).strip()]
    files = [str(f).strip() for f in info.get("files") or [] if str(f).strip()]
    info["files"] = [f for f in files if not is_banned_path(f)]
    return message, info


def latest_scan_run(db: Session, task: AgentTask) -> AgentRun | None:
    return (db.query(AgentRun)
            .filter(AgentRun.task_id == task.id, AgentRun.stage == STAGE_SCAN,
                    AgentRun.status == RUN_OK)
            .order_by(AgentRun.id.desc()).first())


def scan_message_for(task: AgentTask) -> str:
    """Đoạn rà soát (tin nhắn + tệp) để nhét vào lời nhắc PLAN và đề bài sửa mã; rỗng nếu chưa có."""
    from sqlalchemy.orm import object_session

    db = object_session(task)
    run = latest_scan_run(db, task) if db is not None else None
    art = run.artifact if run is not None and isinstance(run.artifact, dict) else {}
    if not art.get("message"):
        return ""
    info = art.get("info") or {}
    extra = []
    if info.get("files"):
        extra.append("Tệp liên quan (đường dẫn đầy đủ): " + ", ".join(info["files"]))
    if info.get("already_fixed"):
        extra.append("Đã sửa sẵn: " + str(info["already_fixed"]))
    if info.get("root_cause"):
        extra.append("Nguyên nhân nghi ngờ: " + str(info["root_cause"]))
    if info.get("questions") and not art.get("answered"):
        extra.append("Câu nghiệp vụ rà soát nêu, đại ca CHƯA trả lời: "
                     + " | ".join(str(q) for q in info["questions"]))
    return "\n".join([str(art["message"]), *extra])


def dispatch_scan(task_id: int) -> None:
    from app.core.celery_app import celery_app

    celery_app.send_task("agent.scan_task", args=[task_id], queue=queue_for(task_id))


def scan_task(db: Session, task: AgentTask) -> dict:
    """Rà soát (chỉ đọc) -> nhắn đại ca đoạn phân tích -> lập kế hoạch dựa trên nó.

    Hỏng ở đâu cũng KHÔNG được bỏ rơi việc: nhắn một câu lý do rồi vẫn lập kế hoạch theo tài liệu
    như trước ai-CR-017. Việc về trạm TRIAGE trước khi gọi `plan_task` để vòng nhặt việc kẹt thấy.
    """
    from . import service

    chat_id = settings.AGENT_TELEGRAM_CHAT_ID
    run = AgentRun(task_id=task.id, stage=STAGE_SCAN, provider=PROVIDER, model=DEFAULT_MODEL,
                   status=RUN_RUNNING, started_at=datetime.now())
    db.add(run)
    db.commit()
    session_id = str(uuid.uuid4())
    try:
        wt, branch = prepare_worktree(task)
        #  Ghi nhánh ngay: lượt sửa mã đi tiếp phiên rà soát dùng lại đúng worktree + nhánh này.
        task.branch_name = branch[:120]
        head = _git(wt, "rev-parse", "HEAD", timeout=60).strip()
        try:
            main_head = _git(wt, "rev-parse", f"origin/{settings.AGENT_MAIN_BRANCH}", timeout=60).strip()
        except CoderError:
            main_head = ""
        docs = memory.recall(f"{task.title}\n{task.summary}")
        telegram.send_chat_action(chat_id)
        data = run_claude_scan(wt, build_scan_brief(task, docs, head, main_head, images=task_images(db, task)),
                               session_id=session_id, timeout=SCAN_TIMEOUT_SEC)
        message, info = parse_scan(str(data.get("result") or ""))
        if not message:
            raise CoderError("phiên rà soát không trả lời gì")
    except (CoderError, subprocess.TimeoutExpired, OSError) as e:
        err = str(e) if not isinstance(e, subprocess.TimeoutExpired) else \
            f"rà soát quá {SCAN_TIMEOUT_SEC // 60} phút, đã dừng"
        _close_run(run, status=RUN_ERROR, error=err)
        task.status = ST_TRIAGE
        db.commit()
        service.reply(db, chat_id, f"<b>{telegram.esc(task.code)}</b>: em chưa rà soát được mã "
                      f"({telegram.esc(err[:300])}), em lập kế hoạch theo tài liệu.", task_id=task.id)
        service.plan_task(db, task)
        return {"status": "error", "reason": err[:500]}

    _close_run(run, status=RUN_OK, data=data, artifact={
        "session_id": session_id, "head": head, "message": message[:8000], "info": info,
        "num_turns": data.get("num_turns"),
    })
    task.status = ST_TRIAGE
    db.commit()
    shown = message if len(message) <= SCAN_MESSAGE_MAX else message[:SCAN_MESSAGE_MAX] + "…"
    #  Câu cần đại ca quyết KHÔNG liệt kê ở đây nữa (ai-CR-021, đại ca thấy hỏi hai lần quá dài):
    #  thẻ kế hoạch ngay sau là chỗ DUY NHẤT hỏi — `service.plan_task` bảo đảm câu nào cũng lên đó.
    service.reply(db, chat_id,
                  f"**{task.code}** · em đã đọc mã trên `{settings.AGENT_BASE_BRANCH}` "
                  f"(`{head[:8]}`):\n\n{shown}\n\nKế hoạch sửa em gửi ngay sau đây.",
                  task_id=task.id, markdown=True)
    service.plan_task(db, task)
    return {"status": "ok", "files": info.get("files") or [], "head": head}
