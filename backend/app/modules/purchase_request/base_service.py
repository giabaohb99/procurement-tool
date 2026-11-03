"""Hằng và hàm đọc nền của YCMH — mọi tệp nghiệp vụ con dùng chung, KHÔNG import tệp anh em (bao-CR-715)."""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.status_codes import PR_LINE_STATUS

from .model import PurchaseRequest, PurchaseRequestItem


# request_date/received_date/need_date nằm trong whitelist để bộ lọc điều kiện lọc theo ngày;
# lọc khoảng kiểu cũ (<field>_from/_to) vẫn do apply_range_filters lo.
FILTERABLE = ["code", "status", "requester", "department", "is_urgent", "request_date",
              "received_date", "need_date",
              "department_id", "head_of_dept_id", "requester_id", "company_id", "purpose"]
ENTITY = "purchase_request"


def sla_base_date(pr) -> str:
    """bao-CR-316 — MỐC ĐẾM hạn của phiếu: Ngày tiếp nhận nếu đã có, chưa có thì Ngày lập.

    Thời gian quy định có hàng phải đếm từ lúc thu mua THẬT SỰ nhận việc (bao-CR-293); phiếu
    chưa được điều phối thì tạm đếm từ ngày lập, để cảnh báo trễ hạn có hiệu lực ngay lúc lập
    phiếu chứ không đợi tới bước điều phối.

    Mọi chỗ tính hạn (`regulated_date`, `urgent_reasons`) phải đi qua hàm này, đừng đọc thẳng
    cột: trước CR-316 hai nghĩa nằm chung một cột nên đọc `request_date` thế nào cũng đúng,
    tách rồi thì đọc thẳng là sai một trong hai nhóm phiếu."""
    if pr is None:
        return ""
    return ((getattr(pr, "received_date", "") or "").strip()
            or (getattr(pr, "request_date", "") or "").strip())

# B-06: cột `line_status` lưu MÃ cố định, xem PR_LINE_STATUS trong app/core/status_codes.py.
# CR-074: tách bạch "chưa ai lập ĐMH" với "đã có ĐMH nhưng chưa bấm đặt hàng". Trước đây hai
# tình huống này chung một nhãn nên người yêu cầu không biết NSTM đã bắt tay làm chưa.
LINE_STATUS_NO_PO = "no_po"             # mặc định của dòng mới
LINE_STATUS_NOT_ORDERED = "not_ordered"  # đã có dòng ĐMH (kể cả đơn Nháp), chưa bấm đặt
LINE_STATUS_ORDERED = "ordered"
LINE_STATUS_RECEIVED = "received"
LINE_STATUS_COMPLETED = "completed"
LINE_STATUS_CANCELLED = "cancelled"
# Nhóm "chưa động tới" — dùng để suy trạng thái phiếu; thêm giá trị mới phải nhớ chỗ này.
# bao-CR-292: recompute_status không dùng LINE_STATUS_IDLE nữa (mốc rời 'dispatched'
# nay là "đã có ĐMH" = khác LINE_STATUS_NO_PO), giữ lại làm tài liệu cho nơi khác tham chiếu.
LINE_STATUS_IDLE = (LINE_STATUS_NO_PO, LINE_STATUS_NOT_ORDERED)
# Điểm cuối của một dòng: không còn gì để làm nữa (đủ điều kiện đóng phiếu).
LINE_STATUS_DONE = (LINE_STATUS_COMPLETED, LINE_STATUS_CANCELLED)

# Trạng thái xử lý theo DÒNG hàng (rút gọn — CR-007 #3): gộp 2 mức chứng từ kế toán của ĐMH
# (`doc_pending`/`doc_sent`) vào `received`; bỏ `paused`.
# Sinh từ bộ mã dùng chung (B-06) để danh sách này không tự trôi khỏi PR_LINE_STATUS.
LINE_STATUS = [c.value for c in PR_LINE_STATUS.codes]


def items_of(db: Session, pr_id: int):
    return db.query(PurchaseRequestItem).filter(PurchaseRequestItem.pr_id == pr_id).all()


def get_pr(db: Session, pid: int) -> PurchaseRequest:
    obj = db.query(PurchaseRequest).filter(
        PurchaseRequest.id == pid,
        PurchaseRequest.is_deleted == False,
    ).first()
    if not obj:
        raise HTTPException(404, "Không tìm thấy yêu cầu mua")
    return obj
