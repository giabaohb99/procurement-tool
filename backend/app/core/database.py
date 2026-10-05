from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

#  Gói A1 (hiệu năng báo cáo, 01/10/2026) — pool TƯỜNG MINH thay cho mặc định SQLAlchemy
#  (pool_size=5 + max_overflow=10 = 15 kết nối/engine). Load-test
#  `fullstack-developer-261001-1103-load-test-8-bao-cao-moi.md` §4 bắt được: Trang Tổng quan
#  báo cáo bắn 13 lời gọi `/summary` song song, mỗi lời GIỮ kết nối 10-20+ giây (cả truy vấn
#  lẫn gom nhóm Python) — chỉ 3 người dùng mở Tổng quan CÙNG LÚC (`--workers 2` x 15 = 30 kết
#  nối) đã vỡ pool, trả 500 `QueuePool limit ... timeout 30.00`.
#
#  Ngân sách (MySQL `max_connections=151`): MỖI tiến trình import tệp này tự tạo MỘT ENGINE
#  (một pool riêng — không chia sẻ kết nối giữa các tiến trình). Prod chạy `uvicorn --workers 2`
#  (`start.prod.sh`) + 1 `celery-worker` (`-c 2`, prefork — tối đa 2 tiến trình con tự dựng
#  engine sau khi fork) + 1 `celery-beat` = tối đa 5 engine đang sống song song. Trần LÝ THUYẾT
#  (mọi engine dùng HẾT pool CÙNG MỘT LÚC — hiếm, vì `max_overflow` là kết nối TẠM, trả về pool
#  là đóng ngay, không giữ lại):
#     5 engine × (pool_size=10 + max_overflow=15) = 125 kết nối, chừa 26 dưới trần 151 cho
#  `mysql` CLI/Adminer/`mysqldump`/sao lưu chạy xen giữa (bản đầu đặt overflow=20 → 150/151, gần
#  như không còn chỗ — hạ xuống khi rà lại 01/10). ĐỪNG tăng `DB_POOL_SIZE`/`DB_MAX_OVERFLOW` mà
#  không nâng `max_connections` của MySQL song song. `pool_timeout=30`: hết chỗ thì ĐỢI rồi báo lỗi rõ ràng (đúng lỗi load-test
#  đã thấy), không treo vô hạn. `pool_recycle=1800` (30 phút): bỏ kết nối cũ trước khi hạ tầng
#  (MySQL/proxy) tự cắt kết nối "ngủ", tránh lỗi "MySQL server has gone away" ngắt quãng.
#
#  Hai số có thể đổi theo môi trường qua `.env` (`DB_POOL_SIZE`/`DB_MAX_OVERFLOW`, xem
#  `core/config.py`). Guard `_is_sqlite`: `db_url` hiện LUÔN là MySQL (`Settings.db_url` hard-code
#  `mysql+pymysql://...`), và bộ test (`test/backend/conftest.py`) tự dựng engine SQLite RIÊNG
#  (không đi qua biến `engine` ở đây) — nhưng giữ guard phòng khi `db_url` đổi dạng, vì
#  `pool_size`/`max_overflow` là tham số của `QueuePool`, SQLite in-memory dùng `StaticPool`
#  (không nhận hai tham số này, `create_engine` ném `TypeError` ngay lúc import).
_is_sqlite = settings.db_url.startswith("sqlite")
_engine_kwargs: dict = {"pool_pre_ping": True, "future": True}
if not _is_sqlite:
    _engine_kwargs.update(pool_size=settings.DB_POOL_SIZE, max_overflow=settings.DB_MAX_OVERFLOW,
                          pool_timeout=30, pool_recycle=1800)

engine = create_engine(settings.db_url, **_engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception:
        #  bao-CR-538: lỗi nào đi ngang qua đây (kể cả MySQL 1406 «Data too long») thì
        #  rollback trước khi trả kết nối — không để giao dịch hỏng dính sang lượt sau.
        #  Rollback hỏng (mất kết nối) thì bỏ qua — lỗi GỐC mới là thứ cần nổi lên.
        try:
            db.rollback()
        except Exception:
            pass
        raise
    finally:
        db.close()


#  bao-CR-402 (P4): gắn bộ nghe sự kiện ORM ngay tại đây, KHÔNG ở `main.py`.
#  Lý do: việc nền Celery, script nhập liệu và `python -m app.seed` đều không đi
#  qua `main.py` nhưng đều đi qua tệp này — treo ở `main.py` thì lớp ghi
#  trước/sau chỉ chạy cho lượt gọi HTTP, và chỗ sửa dữ liệu hàng loạt nhất lại
#  là chỗ không có dấu vết. Bộ nghe tự tắt khi không có `RequestContext`, nên
#  nó không đổi gì với mã đang chạy hay với test.
from app.core.change_tracker import install_change_tracker  # noqa: E402

install_change_tracker()

#  bao-CR-596 (P3): bộ nghe chiều ERP -> app đặt xe cũ, gắn cùng chỗ và cùng lý do: việc
#  nền Celery (tài xế bấm qua chiều nhận, vòng duyệt tự động…) cũng phải được nghe. Công tắc
#  `sync_datxe_outbound_enabled` tắt thì bộ nghe chỉ gom id rồi bỏ, không giao việc gì.
from app.modules.legacy_datxe.outbound_listener import install_outbound_listener  # noqa: E402

install_outbound_listener()
