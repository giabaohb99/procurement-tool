"""Việc chạy nền của Agent Hub. Lịch beat khai ở `core/celery_app.py`.

Ba việc đầu chạy ở `celery-worker`; `agent.code_task` (bậc 2, ai-CR-011), `agent.publish_task`
(ai-CR-012) và `agent.ask_task` (ai-CR-013) đi hàng đợi `agent_code` và CHỈ service `agent-runner`
nghe hàng đợi đó.

Tất cả đều GÁC CỜ `AGENT_HUB_ENABLED` ở dòng đầu: worker có thể đang chạy trong khi
`.env` chưa bật, và một con bot tự nhắn tin cho người ta vì ai đó quên tắt cờ là loại
lỗi không xin lỗi được.

⚠️ KHÔNG `autoretry_for` ở vòng kéo tin. Kéo hỏng thì 10 giây nữa có lượt mới, còn thử
lại thì lượt cũ và lượt mới cùng đọc một con trỏ và xử trùng một tin.
"""
import logging

import app.core.all_models  # noqa: F401 — đăng ký toàn bộ mapper trước khi mở session
from app.core.celery_app import celery_app
from app.core.config import settings
from app.core.database import SessionLocal

from . import coder, memory, service, telegram
from .constants import (
    CLOSED_STATUSES,
    RUN_ERROR,
    RUN_RUNNING,
    ST_CODE,
    ST_DEPLOYING,
    ST_FAILED,
    ST_PROD,
    ST_REVIEW,
    ST_SCANNING,
    ST_TRIAGE,
    STAGE_DEPLOY,
    STAGE_REVERT,
)
from .model import AgentMessage, AgentRun, AgentTask

log = logging.getLogger("app.agent_hub.tasks")


def _off() -> dict | None:
    if not telegram.is_enabled():
        return {"status": "skipped", "reason": "AGENT_HUB_ENABLED / token / chat_id chưa đủ"}
    return None


@celery_app.task(name="agent.poll_telegram")
def poll_telegram_task() -> dict:
    """Kéo tin Telegram. Chạy mỗi 10 giây — CHỈ khi không có `agent-poller` (ai-CR-008).

    ponytail: không có khóa chống chạy chồng — `celery-worker` đang chạy `-c 1` nên chỉ
    một việc chạy tại một thời điểm. Nâng lên nhiều tiến trình thì phải thêm khóa Redis
    quanh chỗ đọc/ghi con trỏ, không thì hai lượt cùng đọc một offset và xử trùng.
    """
    if (off := _off()) is not None:
        return off
    #  Chốt hai lớp với `celery_app.py`: lịch beat cũ còn trong tệp lịch trên đĩa
    #  (PersistentScheduler) vẫn có thể bắn việc này dù đã bỏ khỏi lịch — poller đang
    #  chạy thì đây phải là việc rỗng, không thì hai bên xử trùng một tin.
    if settings.AGENT_LONG_POLL:
        return {"status": "skipped", "reason": "AGENT_LONG_POLL: agent-poller đang kéo tin"}
    db = SessionLocal()
    try:
        n = service.poll_once(db)
        db.commit()
        return {"status": "success", "updates": n}
    except Exception:
        db.rollback()
        log.exception("agent_hub: vòng kéo tin hỏng")
        return {"status": "error"}
    finally:
        db.close()


@celery_app.task(name="agent.triage_inbox")
def triage_inbox_task() -> dict:
    """Gom tin đã nằm yên đủ lâu thành task. Chạy mỗi phút."""
    if (off := _off()) is not None:
        return off
    db = SessionLocal()
    try:
        n = service.triage_inbox(db)
        db.commit()
        #  Nhặt lại việc mà lượt PLAN chết giữa chừng (ai-CR-016, ca AI-0006).
        resumed = service.resume_stuck_plans(db)
        db.commit()
        return {"status": "success", "tasks": n, "resumed": resumed}
    except Exception:
        db.rollback()
        log.exception("agent_hub: vòng gom hỏng")
        return {"status": "error"}
    finally:
        db.close()


@celery_app.task(name="agent.reindex_docs")
def reindex_docs_task() -> dict:
    """Nạp lại kho tài liệu vào Qdrant. Chạy TAY, không có lịch.

    Cố ý không đặt lịch: tài liệu chỉ đổi khi có người sửa, mà một lượt nạp là vài
    nghìn lượt nhúng.

    ⚠️ Phải chạy TRONG `celery-worker` — `doc/` chỉ mount ở đó, container `api` không
    thấy thư mục ấy. Gọi bằng:
        docker compose exec celery-worker python -c \
          "from app.modules.agent_hub.tasks import reindex_docs_task; print(reindex_docs_task())"
    """
    if not settings.AGENT_GEMINI_API_KEY:
        return {"status": "skipped", "reason": "AGENT_GEMINI_API_KEY chưa khai"}
    return {"status": "success", **memory.reindex()}


#  Trần cứng của Celery đặt CAO HƠN trần `claude` (AGENT_RUN_TIMEOUT_SEC) để lượt clone,
#  pytest và commit sau đó còn chỗ; chạm trần này là worker giết cả tiến trình.
@celery_app.task(name="agent.code_task", time_limit=settings.AGENT_RUN_TIMEOUT_SEC + 900,
                 acks_late=False)
def code_task(task_id: int) -> dict:
    """Bậc 2: sửa mã cho một việc đã duyệt. Chạy TRONG `agent-runner`.

    `acks_late=False` cố ý: việc này không được chạy lại tự động khi worker chết giữa
    chừng — một lượt `claude` nửa vời chạy lại từ đầu là đốt gấp đôi, và đại ca cần biết
    nó chết chứ không cần nó im lặng thử lại.
    """
    if (off := _off()) is not None:
        return off
    if not settings.AGENT_CODER_ENABLED:
        return {"status": "skipped", "reason": "AGENT_CODER_ENABLED=false"}
    db = SessionLocal()
    try:
        task = db.get(AgentTask, task_id)
        if task is None or task.status != ST_CODE:
            return {"status": "skipped",
                    "reason": f"việc {task_id} không ở trạm CODE (đã bỏ hoặc bị giao trùng)"}
        result = coder.run_code_task(db, task)
        db.commit()
        return {"status": "success", **result}
    except Exception as e:  # noqa: BLE001 — mọi lỗi đều phải thành FAILED + một câu Telegram
        db.rollback()
        log.exception("agent_hub: lượt sửa mã hỏng")
        task = db.get(AgentTask, task_id)
        if task is not None and task.status == ST_CODE:
            task.status = ST_FAILED
            task.note = f"Bot sửa mã hỏng: {e}"[:2000]
            db.commit()
            service.reply(db, settings.AGENT_TELEGRAM_CHAT_ID,
                          f"Bot sửa mã <b>{telegram.esc(task.code)}</b> hỏng: "
                          f"{telegram.esc(str(e)[:500])}", task_id=task.id)
            db.commit()
        return {"status": "error", "reason": str(e)[:500]}
    finally:
        db.close()


@celery_app.task(name="agent.publish_task", time_limit=1200, acks_late=False)
def publish_task(task_id: int) -> dict:
    """GĐ2a (ai-CR-012): đẩy nhánh đã commit của một việc ở trạm REVIEW lên GitHub + mở PR.

    Chạy TRONG `agent-runner` (hàng đợi `agent_code`) vì worktree chỉ có ở đó. Hỏng thì việc
    vẫn ở REVIEW, chỉ nhắn lý do + nút đẩy lại — không có gì để quay lui.
    """
    if (off := _off()) is not None:
        return off
    if not settings.AGENT_CODER_ENABLED:
        return {"status": "skipped", "reason": "AGENT_CODER_ENABLED=false"}
    db = SessionLocal()
    try:
        task = db.get(AgentTask, task_id)
        if task is None or task.status != ST_REVIEW:
            return {"status": "skipped", "reason": f"việc {task_id} không ở trạm REVIEW"}
        pr = coder.publish_existing(db, task)
        db.commit()
        return {"status": "success", "task": task.code, "pr": pr.get("url", "")}
    except Exception as e:  # noqa: BLE001 — mọi lỗi đều thành một câu Telegram + nút đẩy lại
        db.rollback()
        log.exception("agent_hub: đẩy GitHub / mở PR hỏng")
        task = db.get(AgentTask, task_id)
        if task is not None:
            service.reply(db, settings.AGENT_TELEGRAM_CHAT_ID,
                          f"Đẩy GitHub cho <b>{telegram.esc(task.code)}</b> hỏng: "
                          f"{telegram.esc(str(e)[:500])}", task_id=task.id,
                          buttons=[("Đẩy GitHub lại", f"pr:{task.id}")])
            db.commit()
        return {"status": "error", "reason": str(e)[:500]}
    finally:
        db.close()


@celery_app.task(name="agent.ask_task", time_limit=coder.ASK_TIMEOUT_SEC + 300, acks_late=False)
def ask_task(task_id: int, message_id: int) -> dict:
    """GĐ2b (ai-CR-013): trả lời câu hỏi của đại ca về bản vá bằng đúng phiên đã sửa việc.

    Chạy TRONG `agent-runner` (phiên + worktree chỉ có ở đó). Câu hỏi đọc lại từ sổ theo id tin,
    không truyền chữ qua hàng đợi. Hỏng thì chỉ nhắn lý do + nút hỏi lại; việc không đổi trạng thái.
    """
    if (off := _off()) is not None:
        return off
    if not settings.AGENT_CODER_ENABLED:
        return {"status": "skipped", "reason": "AGENT_CODER_ENABLED=false"}
    db = SessionLocal()
    try:
        task = db.get(AgentTask, task_id)
        row = db.get(AgentMessage, message_id)
        if task is None or row is None or task.status in CLOSED_STATUSES:
            return {"status": "skipped", "reason": f"việc {task_id} đã đóng hoặc không có câu hỏi"}
        answer = coder.answer_patch_question(db, task, row.body)
        db.commit()
        return {"status": "success", "task": task.code, "chars": len(answer)}
    except Exception as e:  # noqa: BLE001 - mọi lỗi đều thành một câu Telegram + nút hỏi lại
        db.rollback()
        log.exception("agent_hub: hỏi thêm về bản vá hỏng")
        task = db.get(AgentTask, task_id)
        if task is not None:
            service.reply(db, settings.AGENT_TELEGRAM_CHAT_ID,
                          f"Hỏi thêm về <b>{telegram.esc(task.code)}</b> hỏng: "
                          f"{telegram.esc(str(e)[:500])}", task_id=task.id,
                          buttons=[("Hỏi lại", f"ask:{task.id}")])
            db.commit()
        return {"status": "error", "reason": str(e)[:500]}
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Gộp erp-v2 + deploy dev / thu hồi (GĐ2b·2, ai-CR-014) — chạy TRONG agent-runner
# ---------------------------------------------------------------------------
def _run_deploy_stage(task_id: int, run_id: int, *, stage: int, label: str, fn) -> dict:
    """Khung chung cho gộp+deploy và thu hồi: dòng sổ phải còn RUNNING (bấm hủy là bỏ), việc
    chưa đóng, cả hai công tắc bật. `fn` tự xử lý lỗi nghiệp vụ (thẻ + trạm); đây chỉ đỡ lỗi
    bất ngờ: đóng lượt, đặt việc về trạm hợp lý theo việc đã đẩy nhánh nền hay chưa."""
    if (off := _off()) is not None:
        return off
    db = SessionLocal()
    try:
        task = db.get(AgentTask, task_id)
        run = db.get(AgentRun, run_id)
        if task is None or run is None or run.stage != stage or run.status != RUN_RUNNING:
            return {"status": "skipped", "reason": f"lượt {run_id} của việc {task_id} đã hủy hoặc không có"}
        if task.status in CLOSED_STATUSES:
            coder._close_run(run, status=RUN_ERROR, error="việc đã đóng trước khi chạy")
            db.commit()
            return {"status": "skipped", "reason": f"việc {task_id} đã đóng"}
        if not settings.AGENT_CODER_ENABLED or not settings.AGENT_DEPLOY_ENABLED:
            coder._close_run(run, status=RUN_ERROR, error="AGENT_CODER_ENABLED/AGENT_DEPLOY_ENABLED tắt")
            service.reply(db, settings.AGENT_TELEGRAM_CHAT_ID,
                          f"<b>{telegram.esc(task.code)}</b>: {label} bị bỏ vì công tắc đang tắt "
                          "(AGENT_CODER_ENABLED / AGENT_DEPLOY_ENABLED).", task_id=task.id)
            db.commit()
            return {"status": "skipped", "reason": "công tắc tắt"}
        result = fn(db, task, run)
        db.commit()
        return {"task": task.code, **result}
    except Exception as e:  # noqa: BLE001 — lỗi ngoài dự kiến cũng phải thành thẻ + trạm đúng
        db.rollback()
        log.exception("agent_hub: %s hỏng ngoài dự kiến", label)
        task = db.get(AgentTask, task_id)
        run = db.get(AgentRun, run_id)
        if run is not None and run.status == RUN_RUNNING:
            coder._close_run(run, status=RUN_ERROR, error=str(e)[:500])
        if task is not None:
            if task.status == ST_DEPLOYING:
                task.status = ST_PROD if coder.merged_sha_for(db, task) else ST_REVIEW
            service.reply(db, settings.AGENT_TELEGRAM_CHAT_ID,
                          f"{label} cho <b>{telegram.esc(task.code)}</b> hỏng ngoài dự kiến: "
                          f"{telegram.esc(str(e)[:500])}", task_id=task.id,
                          buttons=[("Gộp erp-v2 + deploy dev", f"mg:{task.id}")])
        db.commit()
        return {"status": "error", "reason": str(e)[:500]}
    finally:
        db.close()


@celery_app.task(name="agent.deploy_task", time_limit=coder.DEPLOY_TIMEOUT_SEC + 600, acks_late=False)
def deploy_task(task_id: int, run_id: int) -> dict:
    """Đại ca đã đồng ý (ngay hoặc tới giờ hẹn): gộp vào nhánh nền + đẩy + ssh deploy dev.
    `acks_late=False`: worker chết giữa chừng thì KHÔNG tự chạy lại — gộp/đẩy/deploy chạy hai
    lần là hai bản gộp; dòng sổ còn RUNNING sẽ được `_deploy_blocker` đóng khi quá hạn."""
    return _run_deploy_stage(task_id, run_id, stage=STAGE_DEPLOY, label="Gộp + deploy dev",
                             fn=coder.merge_and_deploy)


@celery_app.task(name="agent.revert_task", time_limit=coder.DEPLOY_TIMEOUT_SEC + 600, acks_late=False)
def revert_task(task_id: int, run_id: int) -> dict:
    return _run_deploy_stage(task_id, run_id, stage=STAGE_REVERT, label="Thu hồi",
                             fn=coder.revert_and_deploy)


@celery_app.task(name="agent.deploy_due")
def deploy_due_task() -> dict:
    """Vòng beat mỗi phút (hàng đợi thường, KHÔNG phải runner): lịch hẹn tới giờ -> giao runner."""
    if (off := _off()) is not None:
        return off
    if not settings.AGENT_DEPLOY_ENABLED:
        return {"status": "skipped", "reason": "AGENT_DEPLOY_ENABLED=false"}
    db = SessionLocal()
    try:
        n = service.dispatch_due_deploys(db)
        return {"status": "success", "dispatched": n}
    except Exception as e:  # noqa: BLE001 — vòng beat không được chết vì một dòng sổ hỏng
        db.rollback()
        log.exception("agent_hub: vòng hẹn giờ deploy hỏng")
        return {"status": "error", "reason": str(e)[:300]}
    finally:
        db.close()


#  Rà soát mã trước kế hoạch (ai-CR-017). Chạy TRONG `agent-runner` (worktree + Claude Code).
#  `acks_late=False` cùng lý do với code_task: chết giữa chừng thì vòng nhặt việc kẹt lo tiếp.
@celery_app.task(name="agent.scan_task", time_limit=coder.SCAN_TIMEOUT_SEC + 900, acks_late=False)
def scan_task(task_id: int) -> dict:
    if (off := _off()) is not None:
        return off
    db = SessionLocal()
    try:
        task = db.get(AgentTask, task_id)
        if task is None or task.status != ST_SCANNING:
            return {"status": "skipped", "reason": f"việc {task_id} không còn ở trạm rà soát"}
        if not settings.AGENT_CODER_ENABLED:
            task.status = ST_TRIAGE
            db.commit()
            service.plan_task(db, task)
            db.commit()
            return {"status": "skipped", "reason": "AGENT_CODER_ENABLED=false, lập kế hoạch theo tài liệu"}
        result = coder.scan_task(db, task)
        db.commit()
        return {"task": task.code, **result}
    except Exception as e:  # noqa: BLE001 — không để việc kẹt ở trạm rà soát
        db.rollback()
        log.exception("agent_hub: rà soát mã hỏng ngoài dự kiến")
        task = db.get(AgentTask, task_id)
        if task is not None and task.status == ST_SCANNING:
            task.status = ST_TRIAGE
            db.commit()
            service.reply(db, settings.AGENT_TELEGRAM_CHAT_ID,
                          f"<b>{telegram.esc(task.code)}</b>: rà soát mã hỏng ngoài dự kiến "
                          f"({telegram.esc(str(e)[:300])}), em lập kế hoạch theo tài liệu.",
                          task_id=task.id)
            service.plan_task(db, task)
            db.commit()
        return {"status": "error", "reason": str(e)[:500]}
    finally:
        db.close()
