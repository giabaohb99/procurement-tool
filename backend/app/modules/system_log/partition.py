"""Phân vùng bốn bảng nhật ký theo NĂM — bỏ cả một năm bằng `DROP PARTITION` (bao-CR-454, CR-312 P6 đợt 2).

Đợt 1 (`bao-CR-448`) dọn bằng `DELETE` theo từng tháng, lô 2.000 dòng, trần 500
lô một đêm. Cách đó đúng nhưng có trần: `tab_request_log` ghi ~3.000 dòng mỗi
ngày, nên một năm quá hạn là hơn một triệu dòng, tức **hơn 500 lô** — đêm nào
cũng chạm trần, đêm nào cũng còn dư, và mỗi lô là một giao dịch xóa trên đúng
bảng mà mọi lượt gọi API đang ghi vào.

`DROP PARTITION` bỏ cả năm trong một thao tác siêu dữ liệu: MySQL gỡ tệp của
phân vùng, không đi qua từng dòng. Đổi lại, bảng phải được chia sẵn theo năm —
việc đó làm một lần ở migration `f2c5b9d71a48`.

Tệp này **chỉ biết DDL**, cố ý không biết gì về R2. Luật «gói xong mới xóa»
nằm ở `retention.py`, nơi đã có `archive_marker_key` và `ARCHIVE_TABLES`; để
chiều phụ thuộc một hướng (`retention` → `partition`) thì không tệp nào phải
import ngược lại tệp kia.

Bẫy. Mọi lệnh ở đây ghép tên bảng thẳng vào chuỗi SQL — DDL của MySQL không
nhận tham số cho tên đối tượng. Nên `check_table_name` là **cửa duy nhất**: tên
nào không khớp khuôn định danh thì ném lỗi ngay, đừng nới nó ra.

Tài liệu gốc: `doc/tai-lieu-ky-thuat/nhat-ky-va-phien-dang-nhap.md` §9.
"""
import logging
import re
from collections.abc import Iterable

from sqlalchemy import text
from sqlalchemy.orm import Session

log = logging.getLogger("app.system_log.partition")

#  Phân vùng hứng mọi năm chưa có phân vùng riêng. Luôn phải tồn tại: thiếu nó
#  thì dòng của năm mới **bị MySQL từ chối** — nhật ký ngừng ghi lúc giao thừa.
MAX_PARTITION = "pmax"

_IDENTIFIER = re.compile(r"^[a-z_][a-z0-9_]{0,63}$")


def check_table_name(table: str) -> str:
    """Chốt chặn duy nhất trước khi tên bảng đi vào chuỗi DDL."""
    if not _IDENTIFIER.match(table or ""):
        raise ValueError(f"Tên bảng không hợp lệ cho lệnh phân vùng: {table!r}")
    return table


def build_partition_name(year: int) -> str:
    return f"p{int(year)}"


def read_partition_year(name: str) -> int | None:
    """Đọc ngược `p2025` ra `2025`; `pmax` và tên lạ trả về `None`."""
    if not name or not name.startswith("p") or not name[1:].isdigit():
        return None
    return int(name[1:])


def build_partition_clause(years: Iterable[int]) -> str:
    """Mệnh đề `PARTITION BY RANGE` cho danh sách năm, kèm `pmax` chốt đuôi.

    `VALUES LESS THAN (year + 1)` chứ không phải `(year)`: ranh giới của RANGE
    là cận TRÊN hở, nên phân vùng của 2025 phải nhận mọi giá trị nhỏ hơn 2026.
    """
    sorted_years = sorted({int(y) for y in years})
    if not sorted_years:
        raise ValueError("Phải có ít nhất một năm để dựng mệnh đề phân vùng")
    parts = [f"PARTITION {build_partition_name(y)} VALUES LESS THAN ({y + 1})"
             for y in sorted_years]
    parts.append(f"PARTITION {MAX_PARTITION} VALUES LESS THAN MAXVALUE")
    return "PARTITION BY RANGE (YEAR(created_at)) (\n    " + ",\n    ".join(parts) + "\n)"


def supports_partition(db: Session) -> bool:
    """Chỉ MySQL. Bộ test chạy SQLite, và SQLite không có phân vùng."""
    return db.get_bind().dialect.name == "mysql"


def list_partition_years(db: Session, table: str) -> list[int]:
    """Những năm ĐANG có phân vùng riêng. Bảng chưa phân vùng trả về danh sách rỗng."""
    if not supports_partition(db):
        return []
    rows = db.execute(
        text("SELECT PARTITION_NAME FROM information_schema.PARTITIONS "
             "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = :t "
             "AND PARTITION_NAME IS NOT NULL"),
        {"t": check_table_name(table)},
    ).scalars().all()
    years = [read_partition_year(name) for name in rows]
    return sorted(y for y in years if y is not None)


def ensure_year_partitions(db: Session, table: str, through_year: int) -> list[int]:
    """Bảo đảm có phân vùng riêng cho MỌI năm tới `through_year`. Trả về năm vừa tạo.

    Tách từ `pmax` ra bằng `REORGANIZE` chứ không `ADD PARTITION`: `ADD` chỉ nối
    được vào đuôi, mà đuôi đang là `MAXVALUE` nên không còn chỗ nối.

    ⚠️ **Phải lấp KÍN mọi năm còn thiếu, không nhảy cóc.** Có sẵn tới 2026 mà chỉ
    tạo `p2028` thì `p2028` mang nghĩa *"nhỏ hơn 2029"*, tức nó nuốt luôn cả 2027
    — và ngày bỏ phân vùng đó là bỏ nhầm thêm một năm không ai định bỏ.
    """
    if not supports_partition(db):
        return []
    years = list_partition_years(db, table)
    if not years:
        #  Bảng chưa phân vùng (migration chưa chạy, hoặc cố ý để nguyên). Không
        #  tự ý phân vùng ở đây: đó là thao tác dựng lại cả bảng, phải đi qua
        #  migration để còn có đường lùi.
        return []
    missing = list(range(max(years) + 1, int(through_year) + 1))
    if not missing:
        return []
    name = check_table_name(table)
    parts = ", ".join(f"PARTITION {build_partition_name(y)} VALUES LESS THAN ({y + 1})"
                      for y in missing)
    db.execute(text(f"ALTER TABLE {name} REORGANIZE PARTITION {MAX_PARTITION} INTO "
                    f"({parts}, PARTITION {MAX_PARTITION} VALUES LESS THAN MAXVALUE)"))
    db.commit()
    log.info("Đã tạo phân vùng %s cho bảng %s.", missing, name)
    return missing


def drop_year_partition(db: Session, table: str, year: int) -> bool:
    """Bỏ phân vùng của một năm. Không hoàn tác được — người gọi phải kiểm gói trước.

    Trả `False` khi năm đó không có phân vùng riêng: dòng của nó đang nằm trong
    `pmax` chung với năm khác, bỏ `pmax` là bỏ cả nhật ký đang chạy.
    """
    if not supports_partition(db):
        return False
    if int(year) not in list_partition_years(db, table):
        return False
    name = check_table_name(table)
    db.execute(text(f"ALTER TABLE {name} DROP PARTITION {build_partition_name(year)}"))
    db.commit()
    log.warning("Đã bỏ phân vùng năm %s của bảng %s (không hoàn tác được).", year, name)
    return True
