"""DANH MỤC LOẠI HỒ SƠ — `tab_dossier_type` (phân hệ Hồ sơ, 16/09/2026).

Nguồn của ô chọn «Loại hồ sơ» trên màn hồ sơ, và là chỗ khai **hạn hiệu lực mặc
định** của từng loại giấy tờ (giấy phép con 36 tháng, hồ sơ dự thầu 3 tháng…).

⚠️ **Đây là DANH MỤC, không phải bộ mã.** R2/QĐ-11 bắt cột mang nghĩa *phân loại
· cấp bậc · tình trạng* lưu `SMALLINT` + `IntEnum`; loại hồ sơ KHÔNG thuộc nhóm
đó — nó là danh sách người dùng tự thêm bớt trên giao diện, như chức vụ hay
phòng họp. Đóng băng vào `IntEnum` là mỗi lần công ty phát sinh một loại giấy tờ
lại phải sửa mã nguồn và chạy lại migration. Cùng lý lẽ đã ghi ở
`employee/position_model.py`.

Từ 16/09/2026 nó còn là **khuôn biểu mẫu**: mỗi loại tự khai bộ ô nhập riêng
(`field_schema`), và màn lập hồ sơ dựng form theo loại đang chọn. Xem
`field_schema.py`.

Bảng HỒ SƠ (`tab_dossier`, `model.py`) nối vào đây bằng `dossier_type_id` **và**
giữ thêm một cột nhãn chép sẵn, vì bản in với tệp Excel đọc thẳng cột chữ (bài
học duoc-CR-320). Hai chốt đi kèm nằm ở `type_controller.py`: `before_delete`
chặn xóa loại đang có hồ sơ dùng, `before_update` chép tên mới sang hồ sơ cũ.
"""
from sqlalchemy import JSON, Boolean, Integer, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import AuditMixin, Base


class DossierType(Base, AuditMixin):
    """Một loại hồ sơ."""

    __tablename__ = "tab_dossier_type"

    #  Mã ngắn, duy nhất toàn hệ. Có mã vì danh mục này sẽ đi vào tệp nhập/xuất
    #  CSV; đối chiếu bằng tên tiếng Việt có dấu là mời gọi đúng mớ dữ liệu bẩn
    #  mà danh mục Chức vụ đã phải dọn.
    code: Mapped[str] = mapped_column(String(30), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(String(500), default="")

    #  Hạn hiệu lực mặc định tính bằng THÁNG kể từ ngày lập hồ sơ.
    #
    #  `0` = loại hồ sơ **vô thời hạn**; đó là một lựa chọn thật (giấy chứng nhận
    #  đăng ký doanh nghiệp, quyết định bổ nhiệm), không phải ô chưa ai nhập. Hai
    #  nghĩa đó không tách được bằng `NULL` vì cột `NOT NULL` có mặc định — nên
    #  giao diện phải nói thành lời «Vô thời hạn» thay vì hiện số 0 trần.
    #
    #  `SmallInteger` đủ (trần 1200 tháng = 100 năm, chặn ở schema).
    default_valid_months: Mapped[int] = mapped_column(SmallInteger, default=0)

    #  Ngừng dùng thì biến khỏi ô chọn của hồ sơ MỚI, nhưng hồ sơ đang mang loại
    #  vẫn giữ nguyên — cùng luật với `JobPosition.is_active`. Đây là đường thay
    #  cho việc xóa: xóa để lại hồ sơ trỏ vào một loại không còn tồn tại.
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    #  BỘ TRƯỜNG TÙY BIẾN — danh sách khai báo ô nhập riêng của loại này, để màn
    #  lập hồ sơ dựng biểu mẫu theo loại đang chọn. Cấu trúc + trần kích thước ở
    #  `field_schema.py`; giá trị người dùng điền nằm ở `tab_dossier.extra_fields`.
    #
    #  ⚠️ `NULL` = chưa khai ô nào, và đó là trạng thái HỢP LỆ: loại hồ sơ chỉ cần
    #  mã, tên, hạn là đủ dùng. Đọc ra `[]` qua `field_defs` — trả `None` thì mọi
    #  chỗ dùng phải tự `or []`, và chỗ nào quên thì nổ đúng lúc ai đó mở một loại
    #  khai từ trước khi có cột này.
    field_schema: Mapped[list | None] = mapped_column(JSON, nullable=True)

    #  Thứ tự bày trong ô chọn; số nhỏ lên trước, loại hay dùng để số nhỏ.
    #  ⚠️ Cột này CỐ Ý không lên giao diện — «thứ tự» là khái niệm của người dựng
    #  hệ thống, bày ra bảng thì người dùng thấy toàn 10·20·130 không ai giải
    #  nghĩa (bài học duoc-CR-321). Ô chọn loại vì thế phải khai `sort_by`, đừng
    #  để mặc định `id desc` của bộ sinh CRUD.
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    @property
    def field_defs(self) -> list:
        """`field_schema` luôn đọc ra một danh sách, kể cả khi cột đang `NULL`."""
        return self.field_schema if isinstance(self.field_schema, list) else []

    @property
    def field_count(self) -> int:
        """Số ô tùy biến — bày trên bảng danh mục để biết loại nào đã khai khuôn."""
        return len(self.field_defs)
