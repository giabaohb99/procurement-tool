"""Máy sửa mã TỰ CẬP NHẬT cho khớp bản mã của bot (ai-CR-124) — đại ca 08/10/2026: «tự khắc phục lỗi này đi, khỏi cần
thông báo nữa» (thẻ «MÁY SỬA MÃ VÀ BOT LỆCH BẢN» báo hoài sau mỗi lần deploy dev).

Máy sửa mã dựng ảnh từ mã lúc build nên không tự đổi theo dev. Cách tự khắc phục:

  1. Bot ghi dấu vân tay mã của nó vào `tab_agent_cursor` (`bot_fp`) mỗi vòng canh máy (`runners.watch`).
  2. Nhịp tim của máy (30 giây/lần) so với vân tay của chính nó. Lệch quá `SKEW_GRACE_SEC` và máy đang RẢNH thì kéo
     nhánh nền mới nhất (`fetch_base`, có khóa GitHub thì lấy thẳng GitHub), xuất thư mục `backend/` của từng nhánh
     ứng viên ra `/worktrees/.runner-code/<sha>/`, nhánh nào băm ra ĐÚNG vân tay của bot thì ghi `current` = sha đó
     rồi tự tắt êm (SIGTERM); Docker dựng lại container và `start.runner.sh` chạy mã trong thư mục mới.
  3. Không nhánh nào khớp (bot chạy mã chưa đẩy lên GitHub) thì không đổi gì; quá 30 phút vẫn lệch thì thẻ báo cũ mới
     hiện — lúc đó là việc thật cần người xem, không phải chuyện thường mỗi lần deploy.

Mọi bước đụng git / đĩa tách thành hàm riêng để bài kiểm thay được (container kiểm không có git).
"""
from __future__ import annotations

import logging
import os
import shutil
import signal
import subprocess
import tarfile
import time
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings

from . import runners

log = logging.getLogger("app.agent_hub.runner_update")

#  Lệch ít hơn chừng này thì chờ: bot và máy thường lên bản lệch nhau vài phút mỗi lần deploy.
SKEW_GRACE_SEC = 300
#  Thử lại sau lần hỏng / không khớp — đỡ kéo GitHub mỗi 30 giây.
RETRY_SEC = 600
#  Tiến trình con của Celery ghi tệp này lúc đang làm vé, xóa khi xong — nhịp tim (tiến trình chính) đọc để biết rảnh.
BUSY_FILE = Path("/tmp/agent-runner-busy")
KEEP_VERSIONS = 2
EXPORT_TIMEOUT = 300

_state: dict = {"skew_since": None, "next_try": 0.0, "last_bad": ""}


def code_root() -> Path:
    return Path(settings.AGENT_WORKTREE_ROOT) / ".runner-code"


def bot_fingerprint(db: Session) -> str:
    from .model import AgentCursor

    row = db.scalar(select(AgentCursor).where(AgentCursor.name == runners.BOT_FP_CURSOR))
    return f"{int(row.value):012x}" if row is not None and row.value else ""


def is_busy() -> bool:
    return BUSY_FILE.exists()


def mark_busy(on: bool) -> None:
    try:
        if on:
            BUSY_FILE.write_text(str(os.getpid()))
        else:
            BUSY_FILE.unlink(missing_ok=True)
    except OSError:
        pass


def candidate_branches() -> list[str]:
    raw = settings.AGENT_RUNNER_UPDATE_BRANCHES or settings.AGENT_BASE_BRANCH
    return [b.strip() for b in raw.split(",") if b.strip()]


def _base_repo() -> str:
    """Kho base của máy (cùng kho `prepare_worktree` dùng); chưa có thì nhân bản."""
    from . import coder

    root = Path(settings.AGENT_WORKTREE_ROOT)
    base = root / "base"
    if not (base / "HEAD").exists() and not (base / ".git").exists():
        coder._git(str(root), "clone", "--no-checkout", settings.AGENT_REPO_SOURCE, str(base))
    coder.fetch_base(str(base))
    for b in candidate_branches():
        if b != settings.AGENT_BASE_BRANCH and b != settings.AGENT_MAIN_BRANCH:
            try:
                coder._git(str(base), "fetch", "origin", f"+refs/heads/{b}:refs/remotes/origin/{b}")
            except coder.CoderError:
                log.warning("agent_hub.runner_update: không kéo được nhánh %s", b)
    return str(base)


def _rev_parse(base: str, ref: str) -> str:
    from . import coder

    return coder._git(base, "rev-parse", ref, timeout=60).strip()


def _export(base: str, sha: str, dest: Path) -> None:
    """`git archive <sha> backend` → giải nén vào `dest` (chạy quyền root: thư mục `.runner-code` của máy)."""
    tmp = dest.with_name(dest.name + ".tmp")
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True)
    tar_path = tmp / "src.tar"
    with open(tar_path, "wb") as out:
        subprocess.run(["git", "-C", base, "archive", "--format=tar", sha, "backend"], stdout=out, check=True,
                       timeout=EXPORT_TIMEOUT)
    with tarfile.open(tar_path) as tf:
        tf.extractall(tmp, filter="data")
    tar_path.unlink()
    shutil.rmtree(dest, ignore_errors=True)
    tmp.rename(dest)


def _prune(keep: set[str]) -> None:
    root = code_root()
    dirs = sorted((d for d in root.iterdir() if d.is_dir() and d.name not in keep),
                  key=lambda d: d.stat().st_mtime, reverse=True)
    for d in dirs[max(0, KEEP_VERSIONS - len(keep)):]:
        shutil.rmtree(d, ignore_errors=True)


def _restart() -> None:
    """Tắt êm: Celery làm xong (đang rảnh nên không có gì) rồi thoát; `restart: unless-stopped` dựng lại container."""
    os.kill(os.getpid(), signal.SIGTERM)


def install(db: Session, *, bot: str) -> str:
    """Tìm nhánh có mã băm ra đúng vân tay `bot`, xuất ra `.runner-code/<sha>` và chọn làm bản chạy. Trả sha; không
    nhánh nào khớp thì trả ""."""
    base = _base_repo()
    root = code_root()
    root.mkdir(parents=True, exist_ok=True)
    for branch in candidate_branches():
        try:
            sha = _rev_parse(base, f"origin/{branch}")
        except Exception as e:  # noqa: BLE001
            log.warning("agent_hub.runner_update: không đọc được origin/%s: %s", branch, e)
            continue
        dest = root / sha
        if not (dest / "backend" / "app").exists():
            _export(base, sha, dest)
        got = runners.fingerprint_dir(dest / "backend" / "app" / "modules")
        if got == bot:
            (root / "current").write_text(sha)
            _prune({sha})
            return sha
        log.info("agent_hub.runner_update: origin/%s (%s) băm ra %s, bot đang %s — chưa khớp", branch, sha[:10], got, bot)
    return ""


def tick(db: Session, *, now: float | None = None, restart=None) -> str:
    """Gọi trong nhịp tim. Trả mô tả việc đã làm ("" = không làm gì) — để log và bài kiểm đọc."""
    if not settings.AGENT_RUNNER_SELF_UPDATE or not settings.AGENT_RUNNER_NAME:
        return ""
    now = time.monotonic() if now is None else now
    bot = bot_fingerprint(db)
    mine = runners.code_fingerprint()
    if not bot or bot == mine:
        _state["skew_since"] = None
        return ""
    if _state["skew_since"] is None:
        _state["skew_since"] = now
        return "lệch bản, chờ"
    if now - _state["skew_since"] < SKEW_GRACE_SEC or now < _state["next_try"]:
        return "lệch bản, chờ"
    if is_busy():
        return "lệch bản, máy đang làm vé"
    _state["next_try"] = now + RETRY_SEC
    try:
        sha = install(db, bot=bot)
    except Exception as e:  # noqa: BLE001 — tự cập nhật hỏng không được làm chết nhịp tim
        log.warning("agent_hub.runner_update: tự cập nhật hỏng: %s", e)
        return "tự cập nhật hỏng"
    if not sha:
        if _state["last_bad"] != bot:
            _state["last_bad"] = bot
            log.warning("agent_hub.runner_update: không nhánh nào khớp vân tay bot %s", bot)
        return "không nhánh nào khớp"
    log.info("agent_hub.runner_update: chuyển sang mã %s (khớp bot %s), khởi động lại máy", sha[:10], bot)
    (restart or _restart)()
    return f"đã cập nhật {sha[:10]}"
