from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

engine = create_engine(settings.db_url, pool_pre_ping=True, future=True)
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
