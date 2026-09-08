from sqlalchemy import BigInteger, Boolean, Index, Integer, Numeric, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import Base, AuditMixin
from app.modules.purchase_request.constants import PR_OPT_SURVEY


class PurchaseRequest(Base, AuditMixin):
    """Yêu cầu mua (PYC) — header."""

    __tablename__ = "tab_purchase_request"
    # created_by nằm ở AuditMixin — index qua __table_args__ (apply_scope lọc theo cột này ở MỌI list)
    __table_args__ = (Index("ix_pr_created_by", "created_by"),)

    code: Mapped[str] = mapped_column(String(50), unique=True, default="")
    company_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)  # pháp nhân nhận hóa đơn — apply_scope lọc theo cột này
    requester: Mapped[str] = mapped_column(String(255), default="")        # người yêu cầu
    requester_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)   # id nhân sự người yêu cầu (để so scope)
    requester_position: Mapped[str] = mapped_column(String(100), default="")  # chức vụ
    # CR-086: phòng ban neo bằng ID. `department_id` là NGUỒN SỰ THẬT (phân quyền, lọc, thông báo);
    # cột `department` bên dưới hạ xuống làm BẢN CHỤP TÊN lúc lập phiếu — chỉ để in và để đối chiếu
    # phiếu cũ, KHÔNG được khớp nghiệp vụ bằng nó nữa. 0 = phiếu cũ chưa điền lùi được (xem N-006).
    department_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    department: Mapped[str] = mapped_column(String(255), default="")       # BẢN CHỤP tên phòng ban (sẽ xóa — N-008)
    head_of_dept: Mapped[str] = mapped_column(String(255), default="")     # trưởng bộ phận (TÊN — dùng để in)
    # CR-071: TBP trên phiếu CHỌN được (phòng có phó phòng / quyền trưởng phòng cùng ký), neo
    # bằng id nhân sự chứ không bằng tên. Ô này CHỈ để lưu + in, KHÔNG khóa quyền duyệt của ai.
    # Cột `head_of_dept` ở trên GIỮ LẠI làm bản chụp tên lúc lập phiếu (phiếu cũ không có id).
    head_of_dept_id: Mapped[int] = mapped_column(BigInteger, default=0)    # id NHÂN SỰ (tab_employee)
    purpose: Mapped[str] = mapped_column(String(255), default="")          # mục đích mua hàng
    # bao-CR-316: HAI mốc ngày, hai cột, mỗi cột một nghĩa duy nhất. Trước CR này chỉ có
    # `request_date` và `dispatch_pr` ghi đè nó lúc điều phối (bao-CR-293), nên cùng một cột
    # lúc thì là ngày lập lúc thì là ngày tiếp nhận — bộ lọc và báo cáo trộn hai loại ngày,
    # còn ngày lập gốc thì mất hẳn. Đừng gộp lại.
    request_date: Mapped[str] = mapped_column(String(10), default="")      # ngày LẬP phiếu (YYYY-MM-DD)
    # Rỗng = thu mua CHƯA tiếp nhận. Chỉ `dispatch_pr` được ghi, người dùng không sửa tay.
    received_date: Mapped[str] = mapped_column(String(10), default="")     # ngày TIẾP NHẬN (YYYY-MM-DD)
    need_date: Mapped[str] = mapped_column(String(10), default="")         # ngày cần hàng
    status: Mapped[str] = mapped_column(String(30), default="draft")       # draft|submitted|approved|rejected
    is_urgent: Mapped[bool] = mapped_column(Boolean, default=False)
    vat_rate: Mapped[float] = mapped_column(Numeric(5, 4), default=0.08)
    assignee_id: Mapped[int] = mapped_column(BigInteger, default=0)
    note: Mapped[str] = mapped_column(Text, default="")

    # New columns for suggested supplier and print options
    show_code_on_print: Mapped[bool] = mapped_column(Boolean, default=True)
    suggested_supplier: Mapped[str] = mapped_column(String(255), default="")
    suggested_supplier_tax_code: Mapped[str] = mapped_column(String(50), default="")
    suggested_supplier_contact: Mapped[str] = mapped_column(String(255), default="")
    quote_filename: Mapped[str] = mapped_column(String(255), default="")
    quote_file_url: Mapped[str] = mapped_column(String(1000), default="")
    # Task 4: NCC lưu 2 cụm dạng JSON {"req":{name,tax_code,contact}, "pur":{...}, "from_survey":bool}
    #   req = NCC do BỘ PHẬN yêu cầu đề xuất (người yêu cầu tự điền, KHÔNG cần quyền supplier.read)
    #   pur = NCC từ khảo sát/thu mua (chỉ supplier.read mới thấy, supplier.write mới sửa)
    # Các cột suggested_supplier* ở trên GIỮ LẠI = "NCC hiệu lực" (đồng bộ để ĐMH/list/in cũ dùng).
    supplier_info: Mapped[str] = mapped_column(Text, default="")

    # Soft delete
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)


class PurchaseRequestItem(Base, AuditMixin):
    """Dòng hàng của yêu cầu mua (theo Sheet: giá đề xuất, kho, NSPT, trạng thái...)."""

    __tablename__ = "tab_purchase_request_item"

    pr_id: Mapped[int] = mapped_column(BigInteger, index=True)
    product_code: Mapped[str] = mapped_column(String(50), default="")
    product_name: Mapped[str] = mapped_column(String(255))
    item_group: Mapped[str] = mapped_column(String(100), default="")       # phân loại
    group_desc: Mapped[str] = mapped_column(String(255), default="")       # mô tả phân loại (vd thời gian SX)
    qty: Mapped[float] = mapped_column(Numeric(18, 3), default=0)
    unit: Mapped[str] = mapped_column(String(25), default="")
    price: Mapped[float] = mapped_column(Numeric(18, 4), default=0)        # giá đề xuất (chưa VAT) — đơn giá giữ 4 số lẻ
    vat_pct: Mapped[float] = mapped_column(Numeric(5, 2), default=0)       # % VAT theo dòng (Task 4)
    amount: Mapped[float] = mapped_column(Numeric(18, 2), default=0)       # thành tiền = qty*price*(1+vat_pct%)
    warehouse: Mapped[str] = mapped_column(String(100), default="")        # kho nhận
    required_date: Mapped[str] = mapped_column(String(10), default="")     # ngày cần hàng (theo dòng)
    expected_date: Mapped[str] = mapped_column(String(10), default="")     # thời gian dự kiến có hàng (NSTM cập nhật; đổi giá trị đã có phải kèm lý do)
    assignee: Mapped[str] = mapped_column(String(100), default="", index=True)  # NSTM phụ trách (mã NV) — scope "được giao" lọc theo cột này
    # CR-074: dòng mới chưa có ĐMH nào -> `no_po` (xem service.LINE_STATUS_NO_PO)
    # MÃ cố định, xem PR_LINE_STATUS trong app/core/status_codes.py (B-06):
    # no_po | not_ordered | ordered | received | completed | cancelled.
    line_status: Mapped[str] = mapped_column(String(30), default="no_po")
    qty_ordered: Mapped[float] = mapped_column(Numeric(18, 3), default=0)   # tổng SL đã đặt (đồng bộ từ ĐMH liên kết)
    qty_received: Mapped[float] = mapped_column(Numeric(18, 3), default=0)  # tổng SL đã nhận (đồng bộ từ ĐMH liên kết)
    progress_note: Mapped[str] = mapped_column(Text, default="")           # chi tiết tiến độ
    note: Mapped[str] = mapped_column(String(255), default="")


class PurchaseRequestItemOption(Base, AuditMixin):
    """PHƯƠNG ÁN mua gắn vào 1 dòng YCMH (bao-CR-310) — NCC + giá do NSTM đề xuất.

    Vì sao có bảng này: trước đây muốn có giá thật thì phải đi vòng qua Yêu cầu báo giá
    (YCBG) — dòng YCMH chỉ mang `price` là GIÁ ĐỀ XUẤT của người yêu cầu. Nay NSTM gắn
    thẳng phương án lên dòng YCMH rồi chốt và lên ĐMH, không phải lập thêm chứng từ.
    YCBG giữ nguyên, không đụng tới: ai quen luồng cũ vẫn đi luồng cũ.

    ⚠️ **Bảng RIÊNG, cố ý không dùng lại `tab_survey_request_option`.** Bảng kia khai rõ
    trong docstring là "bảng trung tâm cho cơ chế ẩn NCC" của YCBG và neo bằng
    `survey_request_line_id`; nhét thêm chủ thứ hai vào đó là đẻ ra cột nghĩa kép
    (một trong hai khóa luôn = 0), đúng cái bẫy hệ này đã dính vài lần.

    ⚠️ **Không có cột "đã chốt phương án chưa" trên dòng YCMH** — suy từ chính bảng này
    (`is_chosen`). Thêm cột là tạo nguồn sự thật thứ hai, rồi lệch (bài học: số phép còn
    lại của Nghỉ phép cũng cố ý không lưu thành cột).

    Ẩn NCC: các cột `supplier_*` + `snap_internal_code` CHỈ trả cho người có quyền
    `supplier.read`, bám đúng luật cụm `pur` của Task 4 (xem controller `_out_item`).
    Snapshot thông số + giá thì người yêu cầu ĐƯỢC thấy — giống hệt phương án bên YCBG.
    """

    __tablename__ = "tab_purchase_request_item_option"

    pr_item_id: Mapped[int] = mapped_column(BigInteger, index=True)   # dòng YCMH sở hữu
    # Nguồn phương án — xem PR_OPT_* trong constants.py. Nhập tay thì không truy được
    # về phiếu khảo sát nào, nên phải phân biệt để soát và để báo cáo không trộn.
    source: Mapped[int] = mapped_column(SmallInteger, default=PR_OPT_SURVEY)
    product_survey_line_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    public_id: Mapped[int] = mapped_column(Integer, default=0)        # số hiệu ẩn danh (Phương án 1, 2…) trong 1 dòng
    display_label: Mapped[str] = mapped_column(String(50), default="")
    is_chosen: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    chosen_by: Mapped[int] = mapped_column(BigInteger, default=0)

    # SNAPSHOT — chép tại thời điểm gắn, KHÔNG đọc lại phiếu khảo sát về sau. Phiếu khảo
    # sát sửa giá sau đó không được phép làm đổi phương án đã chốt của một YCMH đang chạy.
    snap_product_name: Mapped[str] = mapped_column(String(255), default="")
    snap_spec: Mapped[str] = mapped_column(Text, default="")
    snap_origin: Mapped[str] = mapped_column(String(100), default="")
    snap_quote_unit: Mapped[str] = mapped_column(String(25), default="")
    snap_moq: Mapped[float] = mapped_column(Numeric(18, 3), default=0)
    snap_price_by_volume: Mapped[float] = mapped_column(Numeric(18, 4), default=0)  # đơn giá giữ 4 số lẻ
    snap_volume_range: Mapped[str] = mapped_column(String(100), default="")
    snap_vat: Mapped[float] = mapped_column(Numeric(5, 2), default=0)
    snap_delivery_time: Mapped[str] = mapped_column(String(100), default="")
    snap_delivery_place: Mapped[str] = mapped_column(String(255), default="")
    snap_shipping_cost: Mapped[float] = mapped_column(Numeric(18, 2), default=0)
    snap_sample_ready: Mapped[bool] = mapped_column(Boolean, default=False)
    snap_lab_result: Mapped[str] = mapped_column(String(20), default="")

    # ----- NỘI BỘ NSTM: backend LỌC, không trả cho người thiếu quyền supplier.read -----
    snap_internal_code: Mapped[str] = mapped_column(String(50), default="")  # mã SP theo NCC
    supplier_code: Mapped[str] = mapped_column(String(50), default="", index=True)
    supplier_name: Mapped[str] = mapped_column(String(255), default="")
    supplier_survey_id: Mapped[int] = mapped_column(BigInteger, default=0)
    nstm_note: Mapped[str] = mapped_column(Text, default="")   # lý do NSTM chọn — HIỆN cho người YC (CR-147)
