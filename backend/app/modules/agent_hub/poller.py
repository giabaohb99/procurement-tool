"""Tiến trình kéo tin Telegram RIÊNG, giữ kết nối chờ (long-polling) — ai-CR-008.

Vì sao tách khỏi celery-worker: worker chạy `-c 1`, nên vòng kéo trong đó chỉ dám hỏi
Telegram "có gì không" rồi về ngay, mỗi 10 giây một lần — đại ca nhắn xong phải chờ
0-10 giây bot mới THẤY tin, chưa tính thời gian trả lời. Tiến trình này không có việc
nào khác nên ôm kết nối 25 giây được: tin tới là Telegram thả ngay, bot thấy tức thì.

Chạy bằng `python -m app.modules.agent_hub.poller` (service `agent-poller` trong
`docker-compose.agent.yml`). Khi nó chạy thì vòng beat `agent.poll_telegram` PHẢI tắt
(`AGENT_LONG_POLL=true` ở celery-beat + celery-worker) — hai bên cùng đọc một con trỏ là
xử trùng một tin.

Hỏng thì ngủ vài giây rồi kéo tiếp, không bao giờ tự chết: Telegram sập, DB sập, hay
mất mạng đều là chuyện tạm thời, và bot chết im lặng thì đại ca tưởng nó "bị chậm".
"""
import logging
import signal
import time
from collections.abc import Callable

log = logging.getLogger("app.agent_hub.poller")

#  Chưa bật cầu dao thì ngủ lâu, khỏi quay vòng vô ích.
IDLE_SLEEP = 30
#  Hỏng (Telegram/DB) thì nghỉ ngắn rồi thử lại — đủ để không dội lỗi liên tục.
ERROR_SLEEP = 3


def run(*, session_factory: Callable, should_stop: Callable[[], bool] = lambda: False,
        sleep: Callable[[float], None] = time.sleep, timeout: int | None = None) -> int:
    """Vòng kéo. Trả số lượt đã chạy (để kiểm thử đếm được).

    Mọi thứ ngoài mạng/DB đều tiêm được (`session_factory`, `should_stop`, `sleep`) để
    bài kiểm chạy vòng này mà không cần Telegram thật.
    """
    from . import service, telegram

    poll_timeout = telegram.LONG_POLL_TIMEOUT if timeout is None else timeout
    rounds = 0
    while not should_stop():
        rounds += 1
        if not telegram.is_enabled():
            sleep(IDLE_SLEEP)
            continue
        db = session_factory()
        try:
            service.poll_once(db, timeout=poll_timeout)
            db.commit()
        except Exception:  # noqa: BLE001 - vòng kéo không được chết vì một lượt hỏng
            db.rollback()
            log.exception("agent_hub: lượt kéo tin hỏng, nghỉ %ss rồi kéo tiếp", ERROR_SLEEP)
            sleep(ERROR_SLEEP)
        finally:
            db.close()
    return rounds


def main() -> None:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    import app.core.all_models  # noqa: F401 — đăng ký toàn bộ mapper trước khi mở session
    from app.core.database import SessionLocal

    from . import telegram

    stopping = False

    def _stop(signum, _frame):
        nonlocal stopping
        stopping = True
        log.info("agent_hub poller: nhận tín hiệu %s, xong lượt này thì dừng", signum)

    #  SIGTERM là cái `docker stop` gửi. Đặt cờ chứ không thoát ngay: lượt đang kéo hoặc
    #  đang xử tin thì để nó xong, cursor chốt xong mới dừng.
    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)

    log.info("agent_hub poller: bắt đầu, giữ kết nối %ss/lượt, cầu dao %s",
             telegram.LONG_POLL_TIMEOUT, "BẬT" if telegram.is_enabled() else "TẮT")
    run(session_factory=SessionLocal, should_stop=lambda: stopping)
    log.info("agent_hub poller: đã dừng")


if __name__ == "__main__":
    main()
