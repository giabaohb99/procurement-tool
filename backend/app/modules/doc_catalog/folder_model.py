"""CÂY THƯ MỤC VĂN BẢN — `tab_doc_folder`.

Một cây CHUNG cho toàn hệ. Tầng gốc là THƯ MỤC PHÁP NHÂN (`kind=COMPANY`): mỗi
`Company` một thư mục hệ thống, KHÔNG tạo tay được (sinh LAZY, xem
`folder_root_service.get_or_create_company_root`) và KHÔNG chuyển tay được (là
đỉnh nhánh) — nhưng XÓA ĐƯỢC y hệt thư mục thường khi RỖNG (rà soát 24/09/2026,
`folder_service.delete_folder`); xóa xong thì tự sinh lại đúng lúc có văn bản
cần thư mục mặc định của công ty đó. Tên của nó KHÔNG lưu (`name = ""`), luôn
đọc từ `Company.name` lúc dựng cây để đổi tên pháp nhân là cây đổi theo, khỏi
đồng bộ hai nơi.

Thư mục THƯỜNG (`kind=NORMAL`) chỉ nằm dưới một nhánh pháp nhân — không có thư
mục thường nào đứng ngang hàng gốc (`parent_id = 0` chỉ dành cho `kind=COMPANY`).

`path`/`depth` là ĐƯỜNG DẪN VẬT HÓA (materialized path), dạng `/1/5/9/` (id nối
bằng `/`, có `/` hai đầu). Dùng để:
  * lọc CẢ NHÁNH bằng `path LIKE '<prefix>%'` — một chỉ mục, không đệ quy;
  * chặn VÒNG LẶP lúc chuyển cha — cha mới không được là chính nó hay hậu duệ
    của nó, kiểm bằng `new_parent.path.startswith(folder.path)`;
  * đổi `path`/`depth` của CẢ NHÁNH trong MỘT câu `UPDATE` khi chuyển cha, xem
    `folder_service.move_folder`.

⚠️ Cột `path`/`depth` **CHỈ do `folder_service` ghi** (luật phải giữ ở `plan.md`).
Không FK cho `parent_id`/`company_id` — theo đúng quy ước của các bảng
`doc_catalog` khác (`book_model.py`, không FK), tránh phức tạp lúc `move_folder`
làm UPDATE hàng loạt và tránh lệch hành vi SQLite/MySQL trong bộ test.
"""
from sqlalchemy import BigInteger, Index, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import AuditMixin, Base

from .folder_constants import FolderKind, FolderStatus


class DocFolder(Base, AuditMixin):
    __tablename__ = "tab_doc_folder"
    __table_args__ = (
        Index("ix_doc_folder_company", "company_id", "status"),
        Index("ix_doc_folder_parent", "parent_id"),
        #  Lọc cả nhánh bằng `path LIKE 'prefix%'` — chỉ mục B-Tree trên MySQL
        #  dùng được cho LIKE có tiền tố cố định (không bắt đầu bằng `%`).
        Index("ix_doc_folder_path", "path"),
        #  ⚠️ Chặn HAI gốc pháp nhân cho cùng một công ty dưới tải đồng thời
        #  (M8, rà soát 23/09/2026) — `ensure_company_roots` từng chỉ
        #  check-then-insert, không có gì ở tầng DB ngăn hai request tạo pháp
        #  nhân song song đều thấy "chưa có gốc" rồi đều tự chèn. `NULL` không
        #  đụng UNIQUE (ngữ nghĩa SQL chuẩn — nhiều `NULL` không va nhau), nên
        #  thư mục THƯỜNG (`root_company_id` luôn `NULL`) không bị ảnh hưởng;
        #  chỉ gốc (`kind=COMPANY`, `root_company_id = company_id`) mới bị ép
        #  duy nhất. Cột do TẦNG SERVICE tự gán (`folder_root_service`), không
        #  dùng cột sinh (`GENERATED`) của MySQL để tránh lệch cú pháp với
        #  SQLite (bộ test) — cùng chủ trương "không FK" đã ghi ở đầu tệp.
        Index("ux_doc_folder_root_company", "root_company_id", unique=True),
    )

    #  Pháp nhân của CẢ NHÁNH (gốc kế thừa xuống mọi thư mục con) — chiều lọc
    #  chính của màn Quản lý cây thư mục và của luật "thấy cây theo pháp nhân"
    #  (phase 04).
    company_id: Mapped[int] = mapped_column(BigInteger, default=0)
    #  `company_id` CHỈ khi `kind=COMPANY` (gốc), `NULL` với thư mục thường —
    #  xem chỉ mục UNIQUE `ux_doc_folder_root_company` ở `__table_args__` (M8).
    root_company_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, default=None)
    #  `0` = gốc — CHỈ hợp lệ với `kind=COMPANY`. Thư mục thường luôn > 0.
    parent_id: Mapped[int] = mapped_column(BigInteger, default=0)
    kind: Mapped[int] = mapped_column(SmallInteger, default=int(FolderKind.NORMAL))
    #  Rỗng với `kind=COMPANY` (tên lấy từ `Company.name` lúc đọc). Thư mục
    #  thường thì bắt buộc và duy nhất trong ANH EM — so sánh gập dấu, xem
    #  `folder_service._fold`.
    name: Mapped[str] = mapped_column(String(150), default="")
    code: Mapped[str] = mapped_column(String(50), default="")
    description: Mapped[str] = mapped_column(String(500), default="")
    #  Đường dẫn vật hóa `/1/5/9/` — xem ghi chú đầu tệp.
    #  760 = `PATH_MAX_LENGTH` (folder_constants) — sửa một chỗ phải sửa cả hai.
    path: Mapped[str] = mapped_column(String(760), default="")
    #  1…`MAX_DEPTH` (100), tính cả gốc.
    depth: Mapped[int] = mapped_column(SmallInteger, default=1)
    sort_order: Mapped[int] = mapped_column(BigInteger, default=0)
    status: Mapped[int] = mapped_column(SmallInteger, default=int(FolderStatus.ACTIVE))
    #  Mức quyền NỀN của thư mục — phase 04 dùng (`FolderAccessLevel`). `NULL` =
    #  chưa khai, kế thừa từ tổ tiên gần nhất; số 0-3 = mức đặt tường minh.
    #  Thư mục pháp nhân được gán `COMPANY_ROOT_DEFAULT_ACCESS` lúc tự sinh.
    default_access: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
