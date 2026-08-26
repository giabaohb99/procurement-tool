"""Tool loại B `search_docs`: tra HDSD + FAQ bằng tìm ngữ nghĩa để trợ lý tư vấn tự do.

Khác tool loại A (tra dữ liệu nghiệp vụ có phân quyền theo dòng), nội dung này là CÔNG KHAI với
mọi người đăng nhập — cùng thứ họ đọc được ở Trung tâm HDSD — nên KHÔNG gác `ctx.can` theo dòng.

Tool này chỉ có mặt khi AI_RAG_ENABLED=true (xem `tools/__init__.py`): môi trường chưa dựng Qdrant
sẽ không quảng cáo một tool gọi vào là hỏng.
"""
from ..rag.search import DEFAULT_LIMIT, MAX_LIMIT, search_docs
from .base import ToolContext, ToolSpec

_PARAMS = {
    "type": "object",
    "properties": {
        "query": {
            "type": "string",
            "description": "Câu hỏi hoặc từ khóa cần tra trong tài liệu hướng dẫn / câu hỏi thường gặp.",
        },
        "limit": {
            "type": "integer",
            "description": f"Số đoạn trả về (tối đa {MAX_LIMIT}). Mặc định {DEFAULT_LIMIT}.",
        },
    },
    "required": ["query"],
}

_DESC = (
    "Tra cứu tài liệu HƯỚNG DẪN SỬ DỤNG và câu hỏi thường gặp (FAQ) của hệ thống bằng tìm kiếm "
    "ngữ nghĩa. Dùng khi người dùng hỏi CÁCH LÀM, quy trình, ý nghĩa chức năng — những câu trả lời "
    "bằng văn bản hướng dẫn, không phải bằng số liệu nghiệp vụ. Trả các đoạn tài liệu kèm nguồn và "
    "đường dẫn để trích dẫn. Không có kết quả nghĩa là tài liệu chưa đề cập — đừng bịa."
)


def _run(ctx: ToolContext, args: dict) -> dict:
    query = str(args.get("query") or "").strip()
    if not query:
        return {"items": [], "total": 0}
    limit = args.get("limit")
    limit = DEFAULT_LIMIT if not isinstance(limit, int) else limit
    items = search_docs(query, limit=limit)
    return {"items": items, "total": len(items)}


SEARCH_DOCS_SPEC = ToolSpec(
    name="search_docs",
    description=_DESC,
    parameters=_PARAMS,
    handler=_run,
)
