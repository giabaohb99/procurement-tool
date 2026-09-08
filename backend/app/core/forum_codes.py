"""BỘ MÃ PREFIX chủ đề diễn đàn (F13a) — nhãn hiển thị cho `tab_forum_post.prefix`.

Cột `prefix` lưu SMALLINT theo luật R2 (`ForumPrefix` ở `app/modules/forum/model.py`
là nguồn giá trị). Bộ này chỉ để `scripts/gen_status_ts.py` sinh nhãn tiếng Việt
cho FE — `value` là SỐ VIẾT DƯỚI DẠNG CHUỖI vì khung `status_catalog` dùng mã
chuỗi; FE đọc `String(post.prefix)` rồi tra nhãn.

Tách khỏi `forum/model.py` để giữ `code_sets.py` thuần stdlib: kịch bản sinh TS
chạy được ở máy không cài SQLAlchemy. Hai bên phải cùng dải giá trị — test
`test_forum_board.py` giữ khớp.
"""
from app.core.status_catalog import Code, CodeSet, register

FORUM_PREFIX_SET = register(CodeSet("forum_prefix", "Prefix chủ đề diễn đàn", [
    Code("0", "Không prefix"),
    Code("1", "Thảo luận"),
    Code("2", "Thắc mắc"),
    Code("3", "Kiến thức"),
    Code("4", "Khoe"),
    Code("5", "Đánh giá"),
]))
