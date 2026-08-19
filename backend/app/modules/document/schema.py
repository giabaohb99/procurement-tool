"""Schema VĂN BẢN và PHIÊN BẢN.

Bộ trường của văn bản là **bộ chung cố định `C01`, khai trong mã**. Bản 1 không
có trường nhập động và không nhập tệp mẫu Word; thư viện mẫu trên web chỉ chép
`content_html` vào phiên bản đầu tiên. Muốn thêm ô thì sửa ở đây, sửa model, sửa
form; đổi lấy sự đơn giản là mọi văn bản đều cùng một hình dạng, tra cứu và báo
cáo được.
"""
from datetime import date

from pydantic import BaseModel, Field

from .model import STATUS_DRAFT
from .version_model import (CHANGE_MAJOR, MARGIN_LEFT_MAX_MM,
                            MARGIN_LEFT_MIN_MM, MARGIN_RIGHT_MAX_MM,
                            MARGIN_RIGHT_MIN_MM)


class DocumentBase(BaseModel):
    """Bộ trường chung C01 — người soạn khai được, không có cột nào hệ tự đặt."""

    doc_type_id: int
    company_id: int
    department_id: int | None = None
    #  SỔ VĂN BẢN chứa văn bản này. Không bắt buộc, nhưng vào sổ thì được thêm
    #  hai thứ: một số vào sổ riêng, và **quyền theo sổ** — mọi thành viên của sổ
    #  đọc được (người quản lý sổ sửa được), khỏi phải chia tay từng văn bản.
    book_id: int | None = None
    owner_employee_id: int
    drafter_employee_id: int | None = None
    signer_employee_id: int | None = None

    title: str = Field(min_length=1, max_length=500)
    summary: str = ""
    keywords: str = Field(default="", max_length=500)

    #  Bỏ trống thì service lấy `default_secrecy` của loại văn bản.
    secrecy_level: int | None = Field(default=None, ge=1, le=4)
    urgency: int = Field(default=1, ge=1, le=3)

    effective_date: date | None = None
    expire_date: date | None = None
    #  Số hiệu bản GIẤY trước khi lên hệ thống (C12) — người cũ vẫn tra theo số này.
    legacy_code: str = Field(default="", max_length=100)


class DocumentCreate(DocumentBase):
    """Tạo văn bản.

    Không nhận `doc_code` / `issue_number`: số hiệu do backend cấp trong cùng
    transaction với việc ghi bản ghi (`numbering.assign`). Nhận số từ client là
    mở đường cho hai người cùng gửi một số.
    """

    #  PHÒNG CHỦ TRÌ bắt buộc khi TẠO (19/08/2026), dù bộ trường chung vẫn cho
    #  rỗng vì văn bản cũ và văn bản pháp luật ngoài không có phòng nào.
    #
    #  Lý do: bước đầu của luồng duyệt là «trưởng bộ phận của phòng chủ trì».
    #  Không có phòng thì không tìm ra người duyệt, phiên duyệt chốt ở trạng thái
    #  KẸT ngay khi vừa gửi, và văn bản không đi tiếp được bằng đường nào —
    #  đã dựng lại được đúng ca đó ngày 19/08. Chặn ở lúc tạo rẻ hơn nhiều so với
    #  gỡ một phiếu đã kẹt.
    department_id: int

    #  Nội dung của phiên bản 1.0. Để trống rồi gõ sau ở màn soạn thảo cũng được.
    content_html: str = ""


class DocumentUpdate(BaseModel):
    """Sửa từng phần bộ trường chung. Số hiệu và trạng thái không sửa qua đây."""

    doc_type_id: int | None = None
    company_id: int | None = None
    department_id: int | None = None
    book_id: int | None = None
    owner_employee_id: int | None = None
    drafter_employee_id: int | None = None
    signer_employee_id: int | None = None

    title: str | None = Field(default=None, min_length=1, max_length=500)
    summary: str | None = None
    keywords: str | None = Field(default=None, max_length=500)
    secrecy_level: int | None = Field(default=None, ge=1, le=4)
    urgency: int | None = Field(default=None, ge=1, le=3)
    effective_date: date | None = None
    expire_date: date | None = None
    legacy_code: str | None = Field(default=None, max_length=100)


class ManualIssueNumberUpdate(BaseModel):
    """Sửa chuỗi số hiệu đã cấp, chỉ khi quy tắc đã bật quyền cho văn thư."""

    issue_number: str = Field(min_length=1, max_length=100)
    reason: str = Field(min_length=1, max_length=1000)


class DocumentOut(DocumentBase):
    id: int
    origin: int
    doc_code: str | None = None
    issue_number: str = ""
    seq_no: int | None = None
    issue_year: int | None = None
    allow_manual_number: bool = False
    status: int = STATUS_DRAFT
    status_label: str = ""
    current_version_id: int | None = None
    #  Số vào sổ — cấp từ bộ đếm RIÊNG của sổ, độc lập với `issue_number`.
    book_seq_no: int | None = None
    book_year: int | None = None
    book_name: str = ""
    book_number_display: str = ""

    #  Phần dựng thêm lúc đọc, không có cột nào tương ứng trong bảng.
    doc_type_name: str = ""
    doc_type_code: str = ""
    company_name: str = ""
    department_name: str = ""
    owner_name: str = ""
    drafter_name: str = ""
    signer_name: str = ""
    #  Số hiệu hiện ra trên bảng: mã bất biến nếu có, không thì số theo sổ.
    display_code: str = ""
    version_no: str = ""
    version_count: int = 0
    attachment_count: int = 0
    created_at: str = ""

    model_config = {"from_attributes": True}


# ── Phiên bản ────────────────────────────────────────────────────────────────
class ReviewedIn(BaseModel):
    """Kết luận sau khi rà soát — bắt buộc, xem `service.xac_nhan_da_ra_soat`."""

    ket_luan: str = Field(min_length=3, max_length=300)


class VersionCreate(BaseModel):
    """Mở phiên bản MỚI trên một văn bản đã có bản được duyệt.

    `change_summary` bắt buộc: mở bản mới mà không nói sửa gì thì ba tháng sau
    không ai dựng lại được vì sao có bản đó (C05, C13).
    """

    change_kind: int = Field(default=CHANGE_MAJOR, ge=1, le=2)
    change_summary: str = Field(min_length=1, max_length=500)
    change_reason: str = ""
    effective_from: date | None = None
    #  Bỏ trống thì theo `change_kind` (sửa lớn → bắt xác nhận lại).
    requires_reconfirm: bool | None = None


class VersionContentUpdate(BaseModel):
    """Ghi nội dung bản nháp — đường mà tự động lưu gọi liên tục theo nhịp gõ.

    `content_html` để trống được: kéo thước lề cũng gọi vào đây, và lúc đó chỉ
    có hai số lề đi kèm. Bắt gửi kèm cả thân văn bản chỉ để đổi 5mm lề là bắt
    đẩy lên vài trăm KB cho mỗi nhịp kéo chuột.
    """

    content_html: str | None = None
    change_summary: str | None = Field(default=None, max_length=500)
    change_reason: str | None = None
    effective_from: date | None = None
    #  Lề ngang (mm) — xem `version_model.MARGIN_LEFT_MIN_MM`.
    margin_left_mm: int | None = Field(default=None, ge=MARGIN_LEFT_MIN_MM,
                                       le=MARGIN_LEFT_MAX_MM)
    margin_right_mm: int | None = Field(default=None, ge=MARGIN_RIGHT_MIN_MM,
                                        le=MARGIN_RIGHT_MAX_MM)
    #  Bật/tắt đánh số mục tự động cho tiêu đề.
    auto_heading_number: bool | None = None
    #  Đầu trang / chân trang — chuỗi ngắn, có thể chứa thẻ `{{trang}}`…
    header_left: str | None = Field(default=None, max_length=200)
    header_right: str | None = Field(default=None, max_length=200)
    footer_left: str | None = Field(default=None, max_length=200)
    footer_right: str | None = Field(default=None, max_length=200)


class VersionOut(BaseModel):
    id: int
    document_id: int
    version_no: str = ""
    major: int
    minor: int
    status: int
    status_label: str = ""
    is_locked: bool
    change_kind: int
    change_summary: str = ""
    change_reason: str = ""
    requires_reconfirm: bool = False
    effective_from: date | None = None
    content_sha256: str = ""
    #  Thể thức trang của chính bản này (mm) — bản in dùng đúng bộ số này.
    margin_left_mm: int = 30
    margin_right_mm: int = 20
    auto_heading_number: bool = False
    header_left: str = ""
    header_right: str = ""
    footer_left: str = ""
    footer_right: str = ""
    prev_version_id: int | None = None
    approved_at: str = ""
    approved_by_name: str = ""
    created_by_name: str = ""
    created_at: str = ""
    #  Bản đang được văn bản dùng — băng cảnh báo "đã bị thay thế" dựa vào đây.
    is_current: bool = False

    model_config = {"from_attributes": True}


class VersionDetailOut(VersionOut):
    """Chỉ trang soạn thảo mới cần nội dung — danh sách phiên bản thì không.

    Nội dung một văn bản dài cỡ vài trăm KB; trả kèm ở danh sách là mỗi lần mở
    tab phiên bản tải về vài MB không ai đọc.
    """

    content_html: str = ""


class ApproveIn(BaseModel):
    """F13 — cơ chế áp dụng, chốt lúc ban hành.

    Bỏ trống thì giữ nguyên giá trị đang có trên bản ghi (mặc định là *gắn phạm
    vi*). Không bắt buộc để đường gọi cũ và bài kiểm cũ không phải sửa.
    """

    apply_mode: int | None = Field(default=None, ge=1, le=2)


class RejectIn(BaseModel):
    """Trả lại bản nháp. Lý do BẮT BUỘC — `van-thu` I09."""

    reason: str = Field(min_length=1, max_length=1000)


# ── Quyền trên từng văn bản ──────────────────────────────────────────────────
class AccessGrant(BaseModel):
    """Một dòng chia sẻ / cấm trên một văn bản.

    `can_read` không tắt được khi đã cho phép: cho sửa mà không cho đọc là vô
    nghĩa. Ngược lại ở chiều CẤM, `can_read = true` nghĩa là cấm luôn cả việc
    nhìn thấy — văn bản biến mất khỏi danh sách của người đó.
    """

    #  1 người (id NHÂN SỰ) · 2 phòng ban · 3 pháp nhân · 4 vai trò.
    subject_kind: int = Field(ge=1, le=4)
    subject_id: int = Field(gt=0)
    #  1 cho phép · 2 cấm. Cấm thắng cho phép.
    effect: int = Field(default=1, ge=1, le=2)

    can_read: bool = True
    can_write: bool = False
    can_delete: bool = False

    valid_from: date | None = None
    #  Trống = không hạn.
    valid_to: date | None = None
    reason: str = Field(default="", max_length=500)


class AccessRevokeIn(BaseModel):
    reason: str = Field(default="", max_length=500)


class AccessOut(AccessGrant):
    id: int
    document_id: int
    subject_kind_label: str = ""
    effect_label: str = ""
    #  Tên đối tượng dựng lúc đọc — bảng chia sẻ mà chỉ hiện id thì không ai đọc được.
    subject_name: str = ""
    is_active: bool = True
    revoked_at: str = ""
    revoked_by_name: str = ""
    revoke_reason: str = ""
    granted_by_name: str = ""
    created_at: str = ""

    model_config = {"from_attributes": True}
