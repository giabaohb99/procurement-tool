"""DANH MỤC CHỨC VỤ — `tab_job_position` (duoc-CR-320, 08/09/2026).

Trước đợt này ô «Vị trí / Chức vụ» của hồ sơ nhân sự là **chữ gõ tay**, nên mỗi
người gõ một kiểu — «Trưởng phòng», «TP.», «truong phong», «Trưởng Phòng » (thừa
dấu cách). Hệ quả không nằm ở chỗ nhìn xấu: cột đó đi thẳng vào bản in phiếu
(YCMH, YCBG, đề nghị thanh toán), vào tệp xuất Excel và vào hồ sơ mà trợ lý AI
đọc — bốn nơi cùng hiện bốn cách viết của một chức vụ.

⚠️ **Đây là DANH MỤC, không phải bộ mã.** R2/QĐ-11 nói cột mang nghĩa *phân
loại · cấp bậc · tình trạng* thì lưu `SMALLINT` + `IntEnum`; chức vụ KHÔNG phải
loại đó — nó là danh sách người dùng tự thêm bớt trên giao diện, như phòng ban
hay phòng họp. Đừng đóng băng nó vào một `IntEnum` trong mã nguồn.

⚠️ **Khác `Employee.job_level` (Cấp bậc).** Cấp bậc là thang bậc CỐ ĐỊNH bảy mức
(`constants.JOB_LEVEL_LABELS`) dùng để lọc và làm báo cáo cơ cấu; chức vụ là
chức danh CỤ THỂ trên phiếu ("Trưởng phòng Mua hàng"). Hai cột, hai vòng đời —
gộp lại thì hoặc mất chi tiết chức danh, hoặc thang bậc đẻ ra vô số mức.
"""
from sqlalchemy import BigInteger, Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import AuditMixin, Base


class JobPosition(Base, AuditMixin):
    """Một chức vụ — nguồn duy nhất của ô chọn «Vị trí / Chức vụ» trên hồ sơ."""

    __tablename__ = "tab_job_position"

    #  Mã ngắn, duy nhất toàn hệ. Có mã vì danh mục này rồi sẽ đi vào tệp nhập
    #  CSV và vào phiếu in; đối chiếu bằng tên tiếng Việt có dấu là đúng thứ vừa
    #  gây ra mớ dữ liệu phải dọn.
    code: Mapped[str] = mapped_column(String(30), unique=True)
    #  ⚠️ `String(100)` phải KHỚP `Employee.position` — tên chức vụ được chép
    #  sang cột đó làm nhãn hiển thị (xem `position_service.sync_label`). Khai
    #  rộng hơn là chép xong bị MySQL cắt cụt, và không chỗ nào báo.
    name: Mapped[str] = mapped_column(String(100))

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    #  Thứ tự bày trong ô chọn. Số nhỏ lên trước; chức vụ hay dùng để số nhỏ.
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    note: Mapped[str] = mapped_column(String(500), default="")

    #  Phòng ban thường giữ chức vụ này. `0` = dùng chung mọi phòng ban — cùng
    #  quy ước `company_id = 0` của `tab_meeting_room`. CHỈ để gợi ý và lọc danh
    #  mục cho gọn; **không** chặn gán chức vụ cho người phòng khác, vì thực tế
    #  có "Trưởng phòng" ở mọi phòng và "Trợ lý Tổng giám đốc" không thuộc phòng
    #  nào. Chặn ở đây là đẻ ra một luật mà Nhân sự phải lách hằng tuần.
    department_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
