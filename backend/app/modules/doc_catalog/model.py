"""Danh mục nền của phân hệ VĂN THƯ.

Hai bảng, đều là danh mục **dùng chung cho mọi pháp nhân** nên cố ý KHÔNG có cột
`company_id`: loại "Công văn" ở DEGO và ở công ty con là cùng một loại, tách theo
pháp nhân thì 13 nơi khai 13 lần rồi lệch nhau.

Thiết kế cột theo `van-thu/04` mục 4.1 và 4.5, với ba chỗ lệch cố ý — ghi rõ tại
chỗ để lần sau đọc không tưởng là làm sai tài liệu.
"""
from sqlalchemy import (Boolean, BigInteger, Index, Integer, SmallInteger, String,
                        Text)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import AuditMixin, Base


class DocType(Base, AuditMixin):
    """LOẠI VĂN BẢN — bảng gốc của cả phân hệ (dự kiến 32 dòng).

    Mỗi văn bản khi tạo chọn một loại ở đây; loại quyết định kiểu định danh, mức
    mật mặc định, lúc nào cấp số, có phải kèm Quyết định ban hành không.

    Lệch so với `van-thu/04` mục 4.1:
      - **Không đặt một `template_id` duy nhất trên loại** — mỗi loại có thể có
        nhiều mẫu soạn thẳng trên web ở `tab_document_template`, không dùng tệp
        mẫu Word.
      - **Thêm `needs_approval` và `needs_signature`** — hai cờ này tài liệu để
        ngầm trong `default_flow_id` và bảng `tab_signature`, nhưng bộ máy duyệt
        chưa làm, mà màn hình đang cần khai "loại này có phải duyệt / ký không".
      - **Không có cột `prefix`.** Tiền tố số hiệu CHÍNH LÀ `code`. Hai cột luôn
        phải bằng nhau thì sớm muộn cũng lệch nhau.
    """

    __tablename__ = "tab_doc_type"
    #  Màn danh mục luôn mở theo nhóm A–F và chỉ hiện loại đang dùng.
    __table_args__ = (Index("ix_doc_type_group", "group_code", "is_active"),)

    code: Mapped[str] = mapped_column(String(10), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    #  Nhóm A–F theo danh mục 32 loại. Rỗng = chưa xếp nhóm.
    group_code: Mapped[str] = mapped_column(String(1), default="")
    description: Mapped[str] = mapped_column(Text, default="")

    # 1 = mã tài liệu bất biến (DEGO-QC-012, không đếm lại theo năm)
    # 2 = số hiệu theo sổ (08/2026/TB-NS-DEGO, đếm lại từ 1 mỗi năm)
    id_scheme: Mapped[int] = mapped_column(SmallInteger, default=2)
    # 1 = cấp số lúc tạo nháp · 2 = cấp số lúc được duyệt (mặc định, nên giữ)
    number_when: Mapped[int] = mapped_column(SmallInteger, default=2)

    # Mức mật mặc định 1 Công khai · 2 Nội bộ · 3 Mật · 4 Tuyệt mật
    default_secrecy: Mapped[int] = mapped_column(SmallInteger, default=2)
    # Cả loại là loại bảo mật — mọi văn bản thuộc loại mặc định ở mức cao
    #
    # ⚠️ Cột này CHỈ đặt mức mật mặc định lúc tạo (`document/service.py`). Nó
    # KHÔNG gác quyền đọc — `secrecy_level` hiện chỉ là nhãn hiển thị, không chỗ
    # nào trong `access_service` nhìn tới nó. Muốn giấu thật thì dùng
    # `is_personal` ngay dưới.
    is_confidential_type: Mapped[bool] = mapped_column(Boolean, default=False)

    #  VĂN BẢN CÁ NHÂN — đơn nghỉ phép, đơn từ chức, phiếu lương…
    #
    #  Loại bật cờ này thì văn bản của nó **không đi theo phạm vi vai trò** nữa.
    #  Người có `document.read` phạm vi *công ty* vốn đọc được mọi văn bản trong
    #  pháp nhân; với đơn nghỉ phép thì đó là cả công ty đọc được đơn xin nghỉ
    #  ốm của từng người. Chỉ những người CÓ CHÂN trong tờ đơn mới thấy: người
    #  nghỉ · người tạo · người đang/đã duyệt · người được chia đích danh · vai
    #  trò phạm vi *tất cả* (HR/quản trị).
    #
    #  Luật đầy đủ ở `document/access_service.dieu_kien_van_ban_ca_nhan`.
    is_personal: Mapped[bool] = mapped_column(Boolean, default=False)

    #  DUYỆT XONG CÓ TỰ BAN HÀNH KHÔNG (26/08/2026).
    #
    #  `True` (mặc định) = giữ nguyên hành vi đang chạy: ký hết các bước là bộ
    #  máy duyệt ban hành luôn — cấp số, khóa phiên bản, chuyển hiệu lực.
    #
    #  `False` = ký xong văn bản dừng ở **Chờ ban hành**; người SOẠN THẢO phải mở
    #  ra, chọn hộp thư gửi thông báo rồi bấm *Ban hành*. Dựng cho ca thông báo
    #  toàn công ty: người ký duyệt nội dung, nhưng người chịu trách nhiệm phát
    #  hành mới là người quyết định gửi đi lúc nào và danh nghĩa địa chỉ nào.
    #
    #  Mặc định `True` là cố ý: bật cờ này cho tất cả các loại đang chạy nghĩa là
    #  mọi phiếu đang duyệt dở bỗng dừng lại chờ một cú bấm mà chưa ai biết là
    #  phải bấm. Loại nào cần thì bật riêng loại đó.
    auto_issue_after_approval: Mapped[bool] = mapped_column(Boolean, default=True)

    needs_approval: Mapped[bool] = mapped_column(Boolean, default=False)
    needs_signature: Mapped[bool] = mapped_column(Boolean, default=False)
    # Ban hành phải kèm một Quyết định. Kiểm ở mức PHIÊN BẢN, không phải mức văn
    # bản: mỗi lần sửa lớn phải có một Quyết định mới.
    needs_decision: Mapped[bool] = mapped_column(Boolean, default=False)
    # Phải có yêu cầu được duyệt mới soạn được. Bản 1 luôn False (quyết định 7),
    # giữ cột để bật lại sau mà không phải sửa bảng.
    needs_request: Mapped[bool] = mapped_column(Boolean, default=False)

    # 0 = không rà định kỳ
    review_cycle_months: Mapped[int] = mapped_column(SmallInteger, default=0)
    retention_months: Mapped[int] = mapped_column(SmallInteger, default=0)
    # Luồng duyệt mặc định — bộ máy duyệt làm sau, cột khai sẵn để khỏi ALTER.
    default_flow_id: Mapped[int] = mapped_column(BigInteger, default=0)

    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class ExternalParty(Base, AuditMixin):
    """ĐƠN VỊ GỬI NHẬN BÊN NGOÀI — nơi gửi của văn bản đến, nơi nhận của văn bản đi.

    Cố ý tách khỏi `tab_supplier` của Thu mua: bên đó là pháp nhân mua bán (mã số
    thuế, VAT, hợp đồng), còn ở đây phần lớn là cơ quan nhà nước, ngân hàng, đơn
    vị nội bộ — trùng nhau rất ít.
    """

    __tablename__ = "tab_external_party"
    __table_args__ = (Index("ix_external_party_kind", "kind", "is_active"),)

    code: Mapped[str] = mapped_column(String(30), unique=True)
    name: Mapped[str] = mapped_column(String(300))
    # 1 cơ quan nhà nước · 2 đối tác · 3 khách hàng · 4 đơn vị nội bộ · 5 khác
    kind: Mapped[int] = mapped_column(SmallInteger, default=1)
    contact_person: Mapped[str] = mapped_column(String(200), default="")
    phone: Mapped[str] = mapped_column(String(50), default="")
    email: Mapped[str] = mapped_column(String(150), default="")
    address: Mapped[str] = mapped_column(Text, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
