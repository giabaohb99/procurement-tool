"""Endpoint Trợ lý AI.

Phase 1: gọi model qua lớp provider (Claude/Gemini), chưa có tool loại A / vector loại B —
những phần đó ở P2/P3.

Phân quyền: cờ AI_ENABLED + quyền `assistant.read` (chỉ ban lãnh đạo: admin, pur_manager,
company_head — xem seed.py). Bot LUÔN chạy dưới danh tính người hỏi (JWT của họ), không có tài
khoản dịch vụ đặc quyền — để mọi tool loại A về sau vẫn đi qua apply_scope của chính user.
"""
from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile
from sqlalchemy.orm import Session

from app.core.auth import require
from app.core.config import settings
from app.core.database import get_db
from app.core.response import success

from . import conversation as convo
from . import usage as usage_layer
from .provider import ProviderError, configured_providers
from .schema import AskIn, ConfirmUpdateIn
from .usage import QuotaExceeded

router = APIRouter(prefix="/api/assistant", tags=["assistant"])


def _guard():
    if not settings.AI_ENABLED:
        raise HTTPException(status_code=403, detail="Trợ lý AI chưa được bật (AI_ENABLED)")


@router.get("/providers")
def list_providers(user=Depends(require("assistant", "read"))):
    """Danh sách nhà cung cấp + model mặc định + đã cấu hình key chưa."""
    _guard()
    return success({
        "providers": configured_providers(),
        "default_provider": settings.AI_DEFAULT_PROVIDER,
    })


@router.post("/chat")
def chat(body: AskIn, user=Depends(require("assistant", "read")),
         db: Session = Depends(get_db)):
    """Gửi một câu hỏi, nhận trả lời + LƯU vào hội thoại (mở mới nếu chưa có id).

    Phase 1: gọi model kèm gói tri thức (AI-1), chưa có tool loại A / vector loại B.
    """
    _guard()
    try:
        result = convo.chat(db, user, body)
    except QuotaExceeded as e:
        # 429 Too Many Requests: hết hạn mức hỏi trong ngày (guard chi phí).
        raise HTTPException(status_code=429, detail=str(e)) from e
    except PermissionError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except ValueError as e:
        # Vi phạm luật đính kèm (quá số tệp/tin...) — lỗi của REQUEST, trả 400.
        raise HTTPException(status_code=400, detail=str(e)) from e
    except ProviderError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
    return success(result)


@router.post("/confirm-update")
def confirm_document_update(body: ConfirmUpdateIn,
                            user=Depends(require("assistant", "read")),
                            db: Session = Depends(get_db)):
    """Bước 2 của tầng GHI có xác nhận (CR-218): NGƯỜI DÙNG bấm 'Xác nhận sửa' trên thẻ
    đề xuất do tool `propose_document_update` sinh ra.

    Backend kiểm lại TOÀN BỘ tại thời điểm bấm (token hợp lệ + đúng chủ + quyền write +
    phạm vi + trạng thái phiếu + whitelist trường) rồi ghi qua đúng service của form —
    xem `tools/update_tool.confirm_update`. Gác `assistant.read` vì đây là nút của giao
    diện chat; quyền GHI thật (`<entity>.write`) kiểm bên trong.
    """
    _guard()
    from .tools.update_tool import confirm_update

    result = confirm_update(db, user, body.token)
    fields = ", ".join(result["updated_fields"])
    return success(result, message=f"Đã sửa phiếu {result['code']}: {fields}")


@router.post("/uploads")
def upload_chat_attachment(file: UploadFile = File(...),
                           user=Depends(require("assistant", "read")),
                           db: Session = Depends(get_db)):
    """Tải MỘT tệp đính kèm chat (CR-204): ảnh JPG/PNG/WebP <= 5MB hoặc PDF <= 10MB.

    FE tải TRƯỚC khi gửi tin (khuôn tải-trước-gắn-sau) rồi truyền `attachment_ids` vào
    `/chat`. Loại tệp nhận diện theo magic bytes, không tin content-type client; tệp
    thuộc về người tải (created_by) — chỉ chính chủ gắn được vào tin của mình.
    """
    _guard()
    from .attachments import MAX_UPLOAD_BYTES, store_upload

    # Đọc dư 1 byte quá trần lớn nhất để biết "quá to" mà không nuốt nguyên file khổng lồ.
    data = file.file.read(MAX_UPLOAD_BYTES + 1)
    try:
        meta = store_upload(db, user, file.filename or "tep-dinh-kem", data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return success(meta)


@router.get("/uploads/{file_id}")
def view_chat_attachment(file_id: int, user=Depends(require("assistant", "read")),
                         db: Session = Depends(get_db)):
    """Mở XEM LẠI một tệp đã đính kèm chat (bấm chip trong lịch sử hội thoại).

    Cùng luật sở hữu với lúc gắn tệp (resolve_owned): chỉ chính chủ + key thuộc thư mục
    `assistant-upload/`. Trả `inline` để trình duyệt hiện thẳng ảnh/PDF trong tab.
    """
    _guard()
    from urllib.parse import quote

    from . import attachments as attach

    try:
        f = attach.resolve_owned(db, user, [file_id])[0]
    except PermissionError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    data = attach.download_bytes(f.file_key)
    return Response(content=data, media_type=f.content_type or "application/octet-stream",
                    headers={"Content-Disposition":
                             f"inline; filename*=UTF-8''{quote(f.filename)}"})


@router.get("/usage/mine")
def my_usage(user=Depends(require("assistant", "read")),
             db: Session = Depends(get_db)):
    """Hạn mức hỏi HÔM NAY của chính người dùng — để giao diện hiện 'còn N câu'."""
    _guard()
    return success(usage_layer.my_quota(db, user))


@router.get("/usage")
def usage_summary(days: int = 30, user=Depends(require("assistant", "export")),
                  db: Session = Depends(get_db)):
    """Tổng hợp token/số câu theo ngày & theo người — soi chi phí. Chỉ admin.

    `assistant.export` chỉ admin có (ensure_admin_role tự cấp mọi action), nên
    endpoint này thực chất là cổng ADMIN — người khác ăn 403.
    """
    _guard()
    return success(usage_layer.summary(db, days=days))


@router.get("/conversations")
def list_conversations(user=Depends(require("assistant", "read")),
                       db: Session = Depends(get_db)):
    """Danh sách hội thoại của chính người dùng (mới trước)."""
    _guard()
    items = [convo.serialize_conversation(c) for c in convo.list_conversations(db, user)]
    return success({"items": items})


@router.get("/conversations/{conv_id}")
def get_conversation(conv_id: int, user=Depends(require("assistant", "read")),
                     db: Session = Depends(get_db)):
    """Chi tiết hội thoại + toàn bộ tin (chỉ chủ hội thoại xem được)."""
    _guard()
    conv = convo.get_owned(db, user, conv_id)
    if conv is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy hội thoại")
    data = convo.serialize_conversation(conv)
    data["messages"] = [convo.serialize_message(m) for m in convo.get_messages(db, conv_id)]
    return success(data)


@router.delete("/conversations/{conv_id}")
def delete_conversation(conv_id: int, user=Depends(require("assistant", "read")),
                        db: Session = Depends(get_db)):
    """Xóa hội thoại của chính mình."""
    _guard()
    if not convo.delete_conversation(db, user, conv_id):
        raise HTTPException(status_code=404, detail="Không tìm thấy hội thoại")
    return success(None, message="Đã xóa hội thoại")


@router.get("/files/{file_id}/download")
def download_report_file(file_id: int, user=Depends(require("assistant", "read")),
                         db: Session = Depends(get_db)):
    """Tải file báo cáo do tool `export_report_file` sinh ra — CHỈ chủ file tải được.

    Không đi qua module attachment vì file này không có FileLink (không gắn chứng từ nào);
    quyền ở đây là quyền SỞ HỮU: `created_by` phải là chính người đang hỏi. Kiểm thêm key
    thuộc thư mục `assistant-report/` để endpoint không thành lối tải chung cho mọi file
    người đó từng đính kèm nơi khác.
    """
    _guard()
    from urllib.parse import quote

    from app.core.storage import download_bytes
    from app.modules.attachment.model import StoredFile

    f = db.get(StoredFile, file_id)
    if not f or f.created_by != user.id or "/assistant-report/" not in (f.file_key or ""):
        raise HTTPException(status_code=404, detail="Không tìm thấy tệp")
    data = download_bytes(f.file_key)
    return Response(content=data, media_type=f.content_type or "application/octet-stream",
                    headers={"Content-Disposition":
                             f"attachment; filename*=UTF-8''{quote(f.filename)}"})


@router.post("/rag/reindex")
def rag_reindex(user=Depends(require("help_article", "write"))):
    """Dựng lại toàn bộ chỉ mục vector loại B (HDSD + FAQ) — đường A, chạy NỀN.

    Gác bằng quyền GHI TÀI LIỆU (`help_article.write`) chứ không phải `assistant` — người quản
    nội dung HDSD mới là người cần bấm nạp lại. Dùng khi mới bật RAG, đổi model nhúng, hoặc nghi
    chỉ mục lệch với dữ liệu.

    Chỉ XẾP HÀNG cho celery-worker rồi trả ngay (không chờ nhúng xong) — nạp toàn bộ có thể gọi
    Gemini nhiều lần, đồng bộ sẽ treo request / timeout. Kết quả xem ở log worker.
    """
    _guard()
    if not settings.AI_RAG_ENABLED:
        raise HTTPException(status_code=400, detail="Tìm kiếm vector chưa được bật (AI_RAG_ENABLED)")
    from .rag.tasks import rebuild_all_task
    try:
        async_result = rebuild_all_task.delay()
    except Exception as e:  # noqa: BLE001 - lỗi broker báo về cho người bấm, không để 500 trơ
        raise HTTPException(status_code=502, detail=f"Xếp hàng nạp lại chỉ mục thất bại: {e}") from e
    return success({"task_id": async_result.id}, message="Đã xếp hàng nạp lại chỉ mục tài liệu")
