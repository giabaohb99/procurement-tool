"""VĂN BẢN — bảng xương sống của phân hệ Văn thư.

Trục của bảng này là **loại văn bản × pháp nhân ban hành × phiên bản**, KHÔNG
phải sổ đến/đi. Nội dung không nằm ở đây mà ở `tab_document_version`: một văn
bản có nhiều phiên bản, `current_version_id` trỏ tới bản đang có hiệu lực.

Ba cái bẫy, đọc trước khi sửa (`van-thu/05`, `02` mục 6):

1. **`origin` phân ba loại bản ghi** — 1 nội bộ · 2 văn bản pháp luật ngoài ·
   3 văn bản đến. Mọi truy vấn danh sách / tìm kiếm / thống kê phải lọc
   `origin = 1`, và chỗ ép việc đó là `query.documents_query()`, không phải từng
   controller tự nhớ.
2. **`status` của văn bản khác `status` của phiên bản.** Quy chế lên bản 2.0 thì
   `tab_document.status` VẪN là 4 có hiệu lực; chỉ dòng phiên bản 1.0 chuyển
   sang 4 bị thay thế. Nhầm chỗ này là cả công ty thấy quy chế lương biến mất.
3. **Số hiệu cấp một lần, không cấp lại.** Hủy văn bản thì số của nó nằm lại
   trong sổ, không trả về cho văn bản sau (`van-thu` D05).
"""
from datetime import date, datetime

from sqlalchemy import (JSON, BigInteger, Boolean, CheckConstraint, Date,
                        DateTime, Index, Integer, SmallInteger, String, Text,
                        UniqueConstraint)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import AuditMixin, Base

#  Nguồn gốc bản ghi. Bản 1 chỉ sinh ra loại 1; hai loại kia khai sẵn để sau
#  nạp văn bản pháp luật / văn bản đến vào cùng bảng mà không phải ALTER nóng.
ORIGIN_INTERNAL = 1
ORIGIN_LEGAL = 2
ORIGIN_INCOMING = 3

#  Vòng đời văn bản (`01` J01). Số chứ không phải chuỗi: mọi so sánh "đã hiệu
#  lực chưa" đều là so sánh khoảng, mà chuỗi tiếng Việt thì không so được.
STATUS_DRAFT = 1        # nháp — đang soạn
STATUS_SUBMITTED = 2    # đang duyệt
STATUS_APPROVED = 3     # đã duyệt, CHƯA tới ngày hiệu lực
STATUS_EFFECTIVE = 4    # có hiệu lực
STATUS_REPLACED = 5     # đã bị thay thế bởi văn bản khác
STATUS_EXPIRED = 6      # hết hiệu lực theo ngày
STATUS_REVOKED = 7      # bãi bỏ
STATUS_ARCHIVED = 8     # lưu trữ
#  Hai nhịp KẾT THÚC PHIÊN DUYỆT, tách khỏi Nháp từ 24/08/2026.
#
#  Trước đó cả «trả lại», «từ chối» và «rút phiếu» đều kéo văn bản về Nháp (1).
#  Mở văn bản ra thì nó trông y như bản chưa từng gửi duyệt: người soạn không
#  biết nó VỪA BỊ TRẢ, mà lý do thì nằm trong `change_reason` và dấu vết tab Phê
#  duyệt — hai chỗ không ai mở khi chỉ liếc trạng thái.
#
#  Hai mã này khác nhau ở chỗ CÒN ĐƯỜNG ĐI hay không, nên không gộp được:
#    * Trả về      → sửa rồi GỬI DUYỆT LẠI trên chính văn bản đó;
#    * Đã từ chối  → hết đường, khóa sửa; muốn làm lại thì *Sao chép* ra bản mới.
#  Rút phiếu vẫn về Nháp: người nộp tự rút thì chẳng ai trả gì cho ai.
STATUS_RETURNED = 9     # bị trả về — sửa được, gửi duyệt lại được
STATUS_REJECTED = 10    # đã từ chối — KHÓA, muốn làm lại thì sao chép

STATUS_LABELS = {
    STATUS_DRAFT: "Nháp",
    STATUS_SUBMITTED: "Đang duyệt",
    STATUS_APPROVED: "Đã duyệt",
    STATUS_EFFECTIVE: "Có hiệu lực",
    STATUS_REPLACED: "Đã thay thế",
    STATUS_EXPIRED: "Hết hiệu lực",
    STATUS_REVOKED: "Bãi bỏ",
    STATUS_ARCHIVED: "Lưu trữ",
    STATUS_RETURNED: "Trả về",
    STATUS_REJECTED: "Đã từ chối",
}

#  Trạng thái mà văn bản còn SỬA ĐƯỢC và còn GỬI DUYỆT được. Dùng một hằng chứ
#  không so `== STATUS_DRAFT` rải rác: bỏ sót một chỗ là văn bản bị trả về không
#  gửi lại được, mà lỗi đó chỉ lộ ra khi có người thật bị trả phiếu.
EDITABLE_STATUSES = (STATUS_DRAFT, STATUS_RETURNED)

#  ── Cơ chế áp dụng cho pháp nhân con (F13) ──────────────────────────────────
#
#  Hai cách KHÔNG mâu thuẫn nhau — chúng dùng cho hai tình huống khác nhau
#  (`van-thu/00` mục 2.2):
#
#    * nội dung giống hệt cho mọi công ty con (thông báo nghỉ Tết, quy chế bảo
#      mật) → MỘT văn bản gắn phạm vi: một số hiệu, một nơi sửa, sửa một lần là
#      13 công ty thấy bản mới ngay;
#    * pháp luật buộc pháp nhân con tự đứng tên, hoặc nội dung phải khác (hạn
#      mức khác, ngành nghề khác) → CLONE thành bản nháp riêng: mỗi công ty một
#      số hiệu, người ký, hiệu lực riêng.
#
#  Phạm vi là MẶC ĐỊNH; clone là nút bấm có điều kiện.
APPLY_MODE_SCOPE = 1
APPLY_MODE_CLONE = 2

APPLY_MODE_LABELS = {
    APPLY_MODE_SCOPE: "Một văn bản, gắn phạm vi áp dụng",
    APPLY_MODE_CLONE: "Clone thành bản nháp riêng cho từng pháp nhân con",
}

#  Trạng thái coi là "còn sống" — dùng cho gợi ý văn bản trùng (B05) và cho
#  danh sách chọn văn bản cha ở P2-T19.
ALIVE_STATUSES = (STATUS_APPROVED, STATUS_EFFECTIVE)


class Document(Base, AuditMixin):
    __tablename__ = "tab_document"
    __table_args__ = (
        #  Văn bản nội bộ BẮT BUỘC có loại và pháp nhân ban hành. Ba cột này để
        #  rỗng được là vì `origin = 2` (văn bản pháp luật ngoài) không có pháp
        #  nhân ban hành nào của mình — nhưng đừng để lọt bản ghi nội bộ thiếu.
        CheckConstraint(
            "origin <> 1 OR (doc_type_id IS NOT NULL AND company_id IS NOT NULL"
            " AND owner_employee_id IS NOT NULL)",
            name="ck_document_internal_required",
        ),
        #  Mã tài liệu bất biến (`DEGO-QC-012`) là duy nhất toàn hệ. Cột cho phép
        #  rỗng vì văn bản sự vụ không có mã này; MySQL cho nhiều NULL trong
        #  UNIQUE nên không vướng.
        UniqueConstraint("doc_code", name="uq_document_doc_code"),
        #  Số hiệu theo sổ: (pháp nhân × năm × loại × số thứ tự) chỉ có một.
        #  Đây là lớp chặn trùng số THỨ HAI, sau khóa dòng ở `next_number()`.
        UniqueConstraint(
            "company_id", "issue_year", "doc_type_id", "numbering_rule_id", "seq_no",
            name="uq_document_issue_seq",
        ),
        #  Một pháp nhân con chỉ nhận MỘT bản clone từ cùng một văn bản gốc.
        UniqueConstraint("source_document_id", "company_id", name="uq_document_clone"),
        Index("ix_document_list", "origin", "company_id", "doc_type_id", "status"),
        Index("ix_document_effective", "origin", "status", "effective_date"),
        Index("ix_document_issue_number", "issue_number"),
        Index("ix_document_legacy_code", "legacy_code"),
        Index("ix_document_clone", "source_document_id", "clone_status"),
    )

    # ── Định danh ────────────────────────────────────────────────────────────
    origin: Mapped[int] = mapped_column(SmallInteger, default=ORIGIN_INTERNAL)
    #  `DEGO-QC-012` — mã tài liệu bất biến, cấp cho loại `id_scheme = 1`.
    doc_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    #  `08/2026/TB-NS-DEGO` — số hiệu theo sổ, cấp cho loại `id_scheme = 2`.
    issue_number: Mapped[str] = mapped_column(String(100), default="")
    #  Ba cột dưới là phần THÔ của `issue_number`, giữ riêng để lọc và để ép
    #  UNIQUE — tách chuỗi ra mà lọc thì không dùng được chỉ mục nào.
    seq_no: Mapped[int | None] = mapped_column(Integer, nullable=True)
    issue_year: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    #  0 là cách cấp số mặc định cũ; số dương là quy tắc đã áp dụng. Cột này
    #  nằm trong khóa duy nhất để hai quy tắc có bộ đếm độc lập không va nhau.
    numbering_rule_id: Mapped[int] = mapped_column(BigInteger, default=0)
    #  Số hiệu của bản GIẤY trước khi lên hệ thống (C12). Tìm kiếm chấp nhận số
    #  này: người cũ vẫn tra theo số họ đã quen.
    legacy_code: Mapped[str] = mapped_column(String(100), default="")
    #  NƠI LƯU TRỮ CỨNG — bản giấy có chữ ký tươi đang nằm ở đâu ("Tủ A2 · Kệ 3
    #  · Bìa 12"). Ô chữ tự do chứ không phải danh mục: mỗi pháp nhân sắp kho
    #  một kiểu, ép vào một bảng danh mục là đẻ ra màn khai báo mà không ai duy
    #  trì. Gợi ý lúc nhập lấy từ chính các giá trị đã gõ (`/storage-locations`),
    #  đó là thứ giữ cho dữ liệu đỡ mỗi người một kiểu.
    #
    #  Tìm kiếm chấp nhận cột này: lý do có nó là "sau này tìm lại bản giấy".
    storage_location: Mapped[str] = mapped_column(String(200), default="")

    # ── Bộ trường chung C01 ──────────────────────────────────────────────────
    doc_type_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    #  Pháp nhân BAN HÀNH — không phải pháp nhân của người ngồi nhập.
    company_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    #  Phòng chủ trì.
    department_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    #  Người chịu trách nhiệm NỘI DUNG — người trả lời khi có ai hỏi về văn bản
    #  này, khác `drafter_employee_id` (người ngồi gõ) và `created_by` (tài khoản).
    owner_employee_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    drafter_employee_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    signer_employee_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    title: Mapped[str] = mapped_column(String(500))
    summary: Mapped[str] = mapped_column(Text, default="")
    #  Từ khóa tra cứu, ngăn bằng dấu phẩy. Không tách bảng: bản 1 chỉ cần tìm
    #  bằng LIKE, tách bảng là thêm một phép nối cho mọi câu truy vấn.
    keywords: Mapped[str] = mapped_column(String(500), default="")

    #  1 Công khai · 2 Nội bộ · 3 Mật · 4 Tuyệt mật (`van-thu/04` 5.2).
    #  ⚠️ Cột đã có từ phase này nhưng LỚP KIỂM chưa làm (thuộc P5) — trong lúc
    #  chưa có, không đưa văn bản mật thật vào hệ thống.
    secrecy_level: Mapped[int] = mapped_column(SmallInteger, default=2)
    #  1 thường · 2 khẩn · 3 hỏa tốc. Độc lập hoàn toàn với mức mật.
    urgency: Mapped[int] = mapped_column(SmallInteger, default=1)

    status: Mapped[int] = mapped_column(SmallInteger, default=STATUS_DRAFT)
    #  Ngày hiệu lực của bản ĐANG DÙNG — chép từ phiên bản hiện hành để danh
    #  sách lọc được mà không phải nối bảng phiên bản.
    effective_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    expire_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    #  Thời điểm KÝ BAN HÀNH, khác `effective_date`: ký hôm nay, áp dụng từ đầu
    #  tháng sau là chuyện thường. Sổ văn bản đi sắp theo cột này.
    issued_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    #  Hạn rà soát định kỳ. Chưa có màn nhắc — thuộc phase sau.
    next_review_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    #  XEM TỆP ĐÍNH KÈM TỚI NGÀY NÀO. Quá ngày này thì mọi tệp đính kèm của văn
    #  bản **không mở ra và không tải về được nữa** — dùng cho tài liệu chỉ cho
    #  xem trong một khoảng (bảng lương kỳ này, hồ sơ thầu tới ngày mở thầu).
    #
    #  Đặt trên VĂN BẢN chứ không trên từng tệp: người dùng nghĩ theo "tài liệu
    #  này chỉ cho xem tới ngày X", không nghĩ theo từng tệp một. Rỗng = không
    #  đặt hạn, xem như trước.
    #
    #  ⚠️ Đây KHÔNG phải `expire_date` (ngày văn bản hết hiệu lực): văn bản hết
    #  hiệu lực vẫn phải tra lại được, còn cái này là hạn xem TỆP.
    attachment_view_until: Mapped[date | None] = mapped_column(Date, nullable=True)
    #  CẦN RÀ LẠI — bật khi văn bản CHA đổi (lên phiên bản mới hoặc bị bãi bỏ) và
    #  quy tắc quan hệ khai `on_parent_* = 2`. Hệ thống chỉ ĐÁNH DẤU, tuyệt đối
    #  không tự sửa nội dung con: người sửa quyết định, quyết định đó vào nhật ký.
    needs_review: Mapped[bool] = mapped_column(Boolean, default=False)
    #  Vì sao cần rà lại — câu này hiện thẳng trên băng cảnh báo nên phải đọc
    #  được một mình, không cần tra thêm bảng nào.
    needs_review_note: Mapped[str] = mapped_column(String(300), default="")
    current_version_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    # ── Bước xin phép (đã cắt khỏi bản 1 — quyết định 7) ─────────────────────
    #  LUÔN NULL. Giữ cột để sau bật lại bước xin phép mà không phải ALTER một
    #  bảng đã vài chục nghìn dòng.
    document_request_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    # ── Clone xuống pháp nhân con (P4 — khai sẵn, bản 1 không dùng) ──────────
    #  Bảy cột này chưa có màn hình nào chạm tới. Khai ngay từ lúc tạo bảng vì
    #  thêm cột vào bảng trống mất một phút, vào bảng đang chạy thì phải canh
    #  giờ dừng hệ thống.
    source_document_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    #  0 chưa đụng · 1 đã sinh nháp · 2 đã ban hành · 3 lệch bản so với gốc.
    clone_status: Mapped[int] = mapped_column(SmallInteger, default=0)
    #  Bản clone đang bám theo phiên bản nào của gốc — để bảng theo dõi F-46
    #  chỉ ra được nơi nào còn dùng bản cũ.
    clone_source_version_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    #  Cơ chế áp dụng, chọn LÚC BAN HÀNH (F13). Xem `APPLY_MODE_LABELS`.
    apply_mode: Mapped[int] = mapped_column(SmallInteger, default=1)
    cloned_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    cloned_by: Mapped[int] = mapped_column(BigInteger, default=0)
    clone_note: Mapped[str] = mapped_column(String(500), default="")
    #  Ba cột giao việc cho pháp nhân nhận (`04` mục 5.2): ai chịu trách nhiệm
    #  bản clone, hạn xử lý, lúc xử lý xong.
    clone_assignee_employee_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    clone_due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    clone_handled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # ── Văn bản pháp luật ngoài (`origin = 2`) ───────────────────────────────
    #  Nghị định / thông tư gom vào chính bảng này thay vì `tab_legal_reference`
    #  riêng (`04` mục 9.3): quan hệ "căn cứ theo" trỏ khóa ngoại vào
    #  `tab_document`, nên một dòng ở bảng riêng không bao giờ làm đích được.
    legal_issuer: Mapped[str] = mapped_column(String(300), default="")
    legal_url: Mapped[str] = mapped_column(String(1000), default="")

    # ── Báo cáo sổ văn bản đi (`04` mục 9.1 — báo cáo, không phải bảng) ──────
    #  Sổ đi là một truy vấn trên chính bảng này: lọc `origin = 1`, đã ban hành,
    #  theo pháp nhân và năm, sắp theo `seq_no`. Ba cột dưới là phần sổ giấy có
    #  mà bảng chưa có.
    recipient_summary: Mapped[str] = mapped_column(String(500), default="")
    copies: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    register_note: Mapped[str] = mapped_column(String(500), default="")

    # ── Sổ đến / đi (nhóm S — chờ câu A1, bản 1 không ghi) ───────────────────
    #  Sổ văn bản đã dựng xong ở `doc_catalog/book_model.py` nhưng việc gắn văn
    #  bản vào sổ thuộc phase 9. Ba cột khai sẵn, luôn rỗng ở bản 1.
    book_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    book_seq_no: Mapped[int | None] = mapped_column(Integer, nullable=True)
    book_year: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)

    # ── Thông tin RIÊNG CỦA TỪNG LOẠI văn bản ────────────────────────────────
    #  Đơn nghỉ phép cần: người nghỉ, loại nghỉ, từ/đến ngày kèm buổi, số ngày,
    #  lý do, người bàn giao, số liên lạc. Hợp đồng sẽ cần bộ khác. Thêm mỗi loại
    #  một cụm cột là bảng này phình ra và 90% cột luôn NULL với 90% văn bản.
    #
    #  ⚠️ Đây KHÔNG phải chỗ đổ dữ liệu tùy tiện. Hình dạng của nó do loại văn
    #  bản quy định (`document/type_metadata.py`), backend kiểm trước khi ghi, và
    #  khóa lạ bị loại bỏ chứ không lưu — nếu không thì sáu tháng nữa không ai
    #  biết trong đó có gì và module Nghỉ phép đọc ra rác.
    #
    #  ⚠️ TÊN THUỘC TÍNH PYTHON PHẢI KHÁC `metadata`. SQLAlchemy declarative giữ
    #  riêng tên đó cho `Base.metadata`; khai trùng là nổ ngay lúc nạp module,
    #  không phải lúc chạy truy vấn. Nên cột dưới CSDL tên `metadata` (đúng thứ
    #  khách yêu cầu, và API cũng trả ra tên đó), còn trong mã gọi là `meta`.
    meta: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
