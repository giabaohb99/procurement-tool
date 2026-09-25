"""duoc_cr477_bo_tu_dung_ngram_van_ban

Sửa CHỖ HỎNG phát hiện lúc kiểm tay MySQL FULLTEXT (bước 7 của phase 07,
duoc-CR-477, xem `frontend-v2/plans/260923-1000-van-ban-thu-muc-nguoi-duyet/
phase-07-tim-kiem-toan-van.md`).

MySQL bật sẵn `innodb_ft_enable_stopword` và áp bảng "từ dừng" MẶC ĐỊNH
(`INFORMATION_SCHEMA.INNODB_FT_DEFAULT_STOPWORD`, 36 từ tiếng Anh — "a", "an",
"are", "as", "at", "be", "by", "com", "de", "en", "for", ...) NGAY CẢ với
parser `ngram`. Với `ngram_token_size=2`, một token ngram khớp ĐÚNG một từ
trong bảng đó bị loại khỏi chỉ mục — và rất nhiều âm tiết tiếng Việt PHỔ BIẾN
sinh ra đúng những ngram 2 ký tự trùng từ dừng tiếng Anh này:
"văn" → ngram "va"+"an", "an" là từ dừng → CẢ TỪ "văn" không lập được chỉ mục;
cùng cảnh: "bản" ("an"), "toàn" ("to" VÀ "an"), "là" (chính là một từ dừng).

Hậu quả xác minh bằng tay trên dữ liệu local: `MATCH(meta_text, body_text,
file_text) AGAINST ('+"van"' IN BOOLEAN MODE)` trả **0 dòng** dù `LIKE
'%van%'` trả đúng dòng có chữ "văn bản" — tức tìm chính TÊN PHÂN HỆ ("văn
bản") gần như luôn ra rỗng. `quy`/`che` (không trùng từ dừng) vẫn khớp bình
thường, nên lỗi chỉ lộ ra khi kiểm TAY trên MySQL thật — bộ pytest chạy SQLite
(nhánh LIKE dự phòng, không đụng FULLTEXT) không bắt được.

⚠️ PHIÊN BẢN ĐẦU của migration này (đã sửa, xem lịch sử) đặt cờ khởi động
`--innodb-ft-enable-stopword=0` ở `docker-compose.yml` dịch vụ `db`, với lý do
"biến GLOBAL cần quyền SUPER". Lý do đó chỉ đúng cho `SET GLOBAL` — **SAI** khi
suy ra là không sửa được từ migration. Đã kiểm tay lại bằng đúng user `app`
(chỉ có `ALL PRIVILEGES` trên một schema, không SUPER):

    SET SESSION innodb_ft_enable_stopword = 0;   -- chạy OK, không lỗi 1227

`innodb_ft_enable_stopword` có phạm vi CẢ Global LẪN Session (MySQL 8.0
Reference Manual §17.14) — set SESSION không đụng tới quyền server-wide.
Test tay dựng bảng tạm + chỉ mục ngram để đo đúng lúc nào giá trị này có tác
dụng, kết quả (khớp báo lỗi công khai #91567 của MySQL — biến "nói chỉ mục sẽ
được dựng thế nào, không nói kết quả truy vấn có lọc hay không"):
  - Chỉ mục dựng lúc session=1 (lọc BẬT) → "an" không tra được, BẤT KỂ session
    lúc TRUY VẤN là 0 hay 1 (0 dòng cả hai trường hợp).
  - Chỉ mục dựng lúc session=0 (lọc TẮT) → "an" tra được, BẤT KỂ session lúc
    TRUY VẤN là 0 hay 1 (1 dòng cả hai trường hợp).
Tức giá trị CHỈ được đọc tại đúng câu lệnh CREATE/ALTER FULLTEXT INDEX, đọc
từ SESSION hiện hành của kết nối đang chạy DDL đó — không phải GLOBAL, và
KHÔNG cần bền theo thời gian (đặt xong, dùng ngay, không cần giữ). Vì vậy
sửa ĐÚNG chỗ và ĐỦ là: `SET SESSION innodb_ft_enable_stopword = 0` ngay
TRONG migration này, ngay trước khi DROP/CREATE lại bốn chỉ mục — không cần
đụng `docker-compose.yml`, không cần cờ khởi động, không cần quyền server-wide,
và do đó chạy được y hệt trên PROD (nơi `docker-compose.production.yml` không
tự chạy MySQL — chỉ proxy sang container `procurement-mysql` ngoài, và user
ứng dụng ở đó cũng chỉ có quyền trên một schema, không có SUPER).

Truy vấn (`search_service.py::_candidate_rows`) KHÔNG cần đặt lại biến này —
đã đo ở trên: giá trị lúc truy vấn không ảnh hưởng gì tới việc lọc từ dừng của
chỉ mục đã dựng sẵn.

⚠️ BỀN VỮNG (M9, rà soát 23/09/2026 — bổ sung SAU migration này, không sửa lại
migration đã chạy trên môi trường khác): cờ này KHÔNG bền theo thời gian —
`mysqldump`/khôi phục bản sao lưu, `OPTIMIZE TABLE`, hay một `ALTER TABLE`
COPY nào khác sau này đều dựng lại 4 chỉ mục FULLTEXT bằng session MẶC ĐỊNH
(lọc BẬT lại), và MySQL không có cách tra ngược "chỉ mục X đang lọc từ dừng
không" — chỉ kiểm được bằng TRUY VẤN THỬ. Guard: `backend/scripts/
reindex_documents.py --check-stopwords` (dựng bảng tạm + chỉ mục ngram, tra
chữ "văn") — chạy định kỳ/lúc khởi động; hỏng thì `--fix-stopwords` dựng lại
đúng 4 chỉ mục này với `SET SESSION innodb_ft_enable_stopword = 0`, không cần
viết migration mới mỗi lần.

Revision ID: 83679db84fd1
Revises: 747c71718181
Create Date: 2026-09-23 12:53:43.580751
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '83679db84fd1'
down_revision: Union[str, None] = '747c71718181'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

#  Khớp ĐÚNG `_FULLTEXT_INDEXES` của migration `747c71718181` — bốn chỉ mục
#  cũ (dựng lúc lọc từ dừng còn BẬT, sai) phải drop/tạo lại y hệt tên + cột.
_FULLTEXT_INDEXES = (
    ("ft_document_search_all", "meta_text, body_text, file_text"),
    ("ft_document_search_meta", "meta_text"),
    ("ft_document_search_body", "body_text"),
    ("ft_document_search_file", "file_text"),
)


def _recreate_indexes() -> None:
    for name, _cols in _FULLTEXT_INDEXES:
        op.execute(f"ALTER TABLE tab_document_search DROP INDEX {name}")
    for name, cols in _FULLTEXT_INDEXES:
        op.execute(
            f"ALTER TABLE tab_document_search "
            f"ADD FULLTEXT INDEX {name} ({cols}) WITH PARSER ngram"
        )


def upgrade() -> None:
    #  SESSION, không GLOBAL — user chạy migration (kể cả user ứng dụng
    #  `app`, không có SUPER) vẫn đặt được, xem giải thích ở docstring.
    #  Chỉ có tác dụng cho đúng 4 câu ALTER...ADD FULLTEXT INDEX ngay sau đây,
    #  chạy trên cùng kết nối.
    op.execute("SET SESSION innodb_ft_enable_stopword = 0")
    _recreate_indexes()
    #  Trả session về mặc định (từ dừng BẬT, đúng mặc định gốc của MySQL) —
    #  không để rò sang các câu lệnh khác lỡ chạy chung kết nối này (vd migration
    #  kế tiếp trong cùng một lượt `alembic upgrade`).
    op.execute("SET SESSION innodb_ft_enable_stopword = DEFAULT")


def downgrade() -> None:
    #  Đặt lại đúng 1 (mặc định gốc, TỪ DỪNG BẬT) để dựng lại chỉ mục ĐÚNG
    #  hành vi lỗi ban đầu của `747c71718181` — downgrade phải trả về trạng
    #  thái TRƯỚC migration này, không phải chạy lại y hệt upgrade.
    op.execute("SET SESSION innodb_ft_enable_stopword = 1")
    _recreate_indexes()
    op.execute("SET SESSION innodb_ft_enable_stopword = DEFAULT")
