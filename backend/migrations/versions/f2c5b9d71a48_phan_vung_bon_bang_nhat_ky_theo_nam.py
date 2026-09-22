"""phan_vung_bon_bang_nhat_ky_theo_nam

Chia bốn bảng nhật ký thành **phân vùng theo năm** (`PARTITION BY RANGE
(YEAR(created_at))`) để dọn một năm quá hạn bằng `DROP PARTITION` thay vì xóa
từng dòng — bao-CR-454, CR-312 P6 đợt 2, §9 của
`doc/tai-lieu-ky-thuat/nhat-ky-va-phien-dang-nhap.md`.

⚠️ **Phải đổi khóa trước khi chia được.** MySQL đòi mọi khóa DUY NHẤT của bảng
phân vùng phải chứa đủ cột trong biểu thức chia. Nên:

- khóa chính của cả bốn bảng: `(id)` → **`(id, created_at)`**;
- `tab_request_log.request_id` và `tab_login_session.token_id`: khóa duy nhất
  một cột → **hai cột, cột định danh đứng trước**.

Cột định danh vẫn đứng đầu khóa nên mọi câu `WHERE request_id = ?` /
`WHERE token_id = ?` vẫn đi bằng chỉ mục, không đổi một dòng mã nào. Phần nới
ra là ràng buộc duy nhất: về lý, hai dòng cùng `token_id` mà khác `created_at`
nay lọt. Cả hai giá trị đều là UUID4 sinh tại chỗ, nên xác suất đó không phải
thứ đáng đem cân với việc dọn nổi một triệu dòng.

⚠️ **KHÔNG tách `DROP PRIMARY KEY` ra một lệnh riêng.** `id` là AUTO_INCREMENT,
mà MySQL đòi cột AUTO_INCREMENT luôn là cột đầu của MỘT khóa nào đó — bỏ khóa
chính xong chưa kịp thêm lại là lỗi 1075 và migration chết giữa chừng. Bỏ và
thêm phải nằm trong CÙNG một câu `ALTER`.

⚠️ `ALTER TABLE ... PARTITION BY` **dựng lại toàn bộ bảng**. Trên máy hôm nay
bốn bảng cộng lại chưa tới 14.000 dòng nên chạy trong tích tắc; chạy ở nơi đã
bật ghi nhật ký đầy đủ thì canh giờ thấp điểm.

SQLite (bộ test) không có phân vùng — migration tự bỏ qua, và model vẫn khai
khóa chính một cột để `create_all` của pytest dựng được bảng.

Revision ID: f2c5b9d71a48
Revises: e82871ec2852
Create Date: 2026-09-21
"""
from datetime import datetime
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text

revision: str = 'f2c5b9d71a48'
down_revision: Union[str, None] = 'e82871ec2852'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

#  (bảng, tên khóa duy nhất phụ, cột của khóa đó). `None` = bảng chỉ có khóa chính.
LOG_TABLES = (
    ("tab_audit_log", None, None),
    ("tab_request_log", "request_id", "request_id"),
    ("tab_change_log", None, None),
    ("tab_login_session", "token_id", "token_id"),
)

MAX_PARTITION = "pmax"


def _is_partitioned(bind, table: str) -> bool:
    return bool(bind.execute(
        text("SELECT COUNT(*) FROM information_schema.PARTITIONS "
             "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = :t "
             "AND PARTITION_NAME IS NOT NULL"), {"t": table}).scalar())


def _partition_years(bind, table: str) -> list[int]:
    """Dải năm cần dựng: từ năm cũ nhất đang có dữ liệu tới năm sau năm nay.

    Có sẵn phân vùng của năm sau thì lúc giao thừa không phải chờ việc nền —
    và trong lúc chờ thì dòng mới rơi vào `pmax`, nơi không bỏ riêng năm được.
    """
    now_year = datetime.now().year
    oldest = bind.execute(text(f"SELECT MIN(YEAR(created_at)) FROM {table}")).scalar()
    start = int(oldest) if oldest else now_year
    return list(range(min(start, now_year), now_year + 2))


def _partition_clause(years: list[int]) -> str:
    parts = [f"PARTITION p{y} VALUES LESS THAN ({y + 1})" for y in years]
    parts.append(f"PARTITION {MAX_PARTITION} VALUES LESS THAN MAXVALUE")
    return "PARTITION BY RANGE (YEAR(created_at)) (" + ", ".join(parts) + ")"


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "mysql":
        return
    for table, index_name, column in LOG_TABLES:
        if _is_partitioned(bind, table):
            continue
        if index_name:
            #  Bỏ rồi thêm lại trong CÙNG một câu: giữa hai câu riêng lẻ thì cột
            #  đó mất chỉ mục, và mọi lượt tra phiên trong khoảng ấy quét cả bảng.
            bind.execute(text(
                f"ALTER TABLE {table} DROP INDEX {index_name}, "
                f"ADD UNIQUE KEY {index_name} ({column}, created_at)"))
        bind.execute(text(
            f"ALTER TABLE {table} DROP PRIMARY KEY, ADD PRIMARY KEY (id, created_at)"))
        bind.execute(text(f"ALTER TABLE {table} {_partition_clause(_partition_years(bind, table))}"))


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "mysql":
        return
    for table, index_name, column in LOG_TABLES:
        if _is_partitioned(bind, table):
            #  Gộp mọi phân vùng lại thành một bảng thường. KHÔNG mất dòng nào —
            #  `REMOVE PARTITIONING` chỉ dựng lại bảng, khác hẳn `DROP PARTITION`.
            bind.execute(text(f"ALTER TABLE {table} REMOVE PARTITIONING"))
        bind.execute(text(f"ALTER TABLE {table} DROP PRIMARY KEY, ADD PRIMARY KEY (id)"))
        if index_name:
            bind.execute(text(
                f"ALTER TABLE {table} DROP INDEX {index_name}, "
                f"ADD UNIQUE KEY {index_name} ({column})"))
