"""Đăng ký chứng từ cho phép bình luận (CR-029).

Mỗi entity bình luận → (entity CHA để kiểm quyền, nhãn hiển thị, đường dẫn FE của trang chi tiết).
Entity không có trong bảng này sẽ bị TỪ CHỐI — chống entity rác, đúng khuôn `FILE_POLICY`
của đính kèm (`core/file_registry.py`).

Muốn mở bình luận cho một phân hệ mới: thêm 1 dòng ở đây + 1 nhánh ở `doc_model()`,
không phải đụng tới model/bảng.
"""

COMMENT_POLICY: dict[str, tuple[str, str, str]] = {
    "purchase_request": ("purchase_request", "Yêu cầu mua hàng", "/purchase-requests"),
    "survey_request":   ("survey_request",   "Yêu cầu báo giá",  "/survey-requests"),
    "survey":           ("survey",           "Phiếu khảo sát",   "/surveys"),
    "purchase_order":   ("purchase_order",   "Đơn mua hàng",     "/purchase-orders"),
    # Diễn đàn (F1): entity cha chỉ để ĐẶT TÊN — `resolve_doc` rẽ nhánh riêng kiểm
    # theo luật audience của bài, KHÔNG kiểm RBAC (người thường không có grant nào).
    # Route ghi THẲNG dạng v2 (khuôn Văn thư): diễn đàn chỉ có trên `frontend-v2`,
    # ghi "/posts" thì `notification-link.toAppPath` bên FE trả null — chuông câm.
    "forum_post":       ("forum_post",       "Bài viết diễn đàn", "/forum/posts"),
}


def policy(entity: str):
    """(entity cha, nhãn, route FE) — None nếu entity không được phép bình luận."""
    return COMMENT_POLICY.get(entity)


def doc_model(entity: str):
    """Model của chứng từ, để kiểm phạm vi dữ liệu.

    Import bên trong hàm để tránh vòng import với các module nghiệp vụ.
    """
    if entity == "purchase_request":
        from app.modules.purchase_request.model import PurchaseRequest
        return PurchaseRequest
    if entity == "survey_request":
        from app.modules.survey_request.model import SurveyRequest
        return SurveyRequest
    if entity == "survey":
        from app.modules.survey.model import Survey
        return Survey
    if entity == "purchase_order":
        from app.modules.purchase_order.model import PurchaseOrder
        return PurchaseOrder
    if entity == "forum_post":
        from app.modules.forum.model import ForumPost
        return ForumPost
    return None
