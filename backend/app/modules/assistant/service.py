"""Tầng dịch vụ Trợ lý AI — điều phối provider + routing theo loại câu hỏi.

- Phase 1: gọi model kèm GÓI TRI THỨC (AI-1) nhồi vào `system` + prompt caching.
- Phase 2: tool loại A. Khi có `db`+`user` và nhà cung cấp hỗ trợ, đưa danh sách tool cho
  model tự chọn gọi; tool chạy DƯỚI danh tính người hỏi (`tools.run_tool`) rồi trả số thật.

Routing quyết định: bật/tắt suy nghĩ + trần token + có mở tool hay không theo loại câu.
"""
from datetime import date

from app.core.config import settings

from . import tools as tool_layer
from .knowledge import build_system
from .provider import ChatMessage, get_provider

# kind câu hỏi -> cấu hình sinh. 'lookup' = loại A (tra cứu, rẻ, không cần suy nghĩ);
# 'advice' = loại B (tư vấn quy trình, cần suy nghĩ); 'general' = mặc định.
# `tools`: có mở lớp tool cho model không. advice BẬT tool để model gọi được `search_docs`
# (tra HDSD + FAQ thật) — trước đây tắt vì chưa có tool loại B, khiến câu tư vấn quy trình
# phải trả lời chay theo gói tri thức + suy đoán, dễ bịa sai bước (vd "gửi báo giá cho NCC").
ROUTING: dict[str, dict] = {
    "lookup":  {"thinking": False, "max_tokens": 1024, "temperature": 0.2, "tools": True},
    "advice":  {"thinking": True,  "max_tokens": 2048, "temperature": 0.4, "tools": True},
    "general": {"thinking": False, "max_tokens": 1536, "temperature": 0.3, "tools": True},
}

# Hướng dẫn khi bật tool — bản đồ NĂNG LỰC + chiến lược gọi tool, để model tự chọn/kết hợp
# công cụ và biết nói gì khi câu hỏi nằm ngoài phạm vi (thay vì chỉ xin lỗi).
TOOL_GUIDE = """\
Bạn có bộ CÔNG CỤ tra dữ liệu thu mua thật (đã lọc theo quyền của người hỏi). Khi câu hỏi cần
số liệu, HÃY GỌI CÔNG CỤ thay vì đoán. Bộ công cụ trả lời được các nhóm câu:

- Hợp đồng NCC: còn hạn / hết hạn, đếm theo trạng thái, hợp đồng của một NCC cụ thể.
- Giá & lịch sử mua theo MÃ HÀNG: giá tốt nhất, lịch sử mua, các NCC từng bán mã đó.
- Tổng hợp toàn hệ: lần mua gần nhất, NCC mua nhiều nhất, đơn mua hàng (PO) gần nhất kèm giá
  trị, báo cáo chi tiêu (tổng, theo tháng, top mã hàng).
- Thống kê TÙY BIẾN (analytics_query): kết hợp CHỈ SỐ (chi tiêu / số lần mua / số lượng / đơn
  giá trung bình) theo CHIỀU (nhà cung cấp / mã hàng / tháng) trong một khoảng ngày, lọc theo
  NCC hoặc mã hàng. Dùng cho câu KHÔNG khớp các công cụ chuyên biệt ở trên, ví dụ "chi tiêu
  của NCC X theo từng tháng", "số lượng mã Y đã mua trong quý 1", "đơn giá trung bình mã Z".
- Tra danh mục: product_search / supplier_search để đổi MÔ TẢ sang mã.
- Phê duyệt & văn bản: approval_flow_lookup tra LUỒNG PHÊ DUYỆT của một loại văn bản —
  "đơn nghỉ phép do ai duyệt", "người phê duyệt nghỉ phép của tôi là ai" (kết quả có cả
  quy tắc lẫn tên người duyệt cụ thể cho chính người hỏi trong `approvers_for_me`);
  my_documents liệt kê VĂN BẢN đang áp dụng cho chính người hỏi ("văn bản nào áp dụng
  lên tôi"); document_search TÌM văn bản trong kho theo từ khóa ("tìm quy định về công
  tác phí", "văn bản số 15/QĐ là gì"); document_read ĐỌC NỘI DUNG một văn bản cụ thể —
  câu hỏi về nội dung bên trong ("quy định X nói gì về Y", mức chi, điều kiện...) thì
  tìm ra văn bản rồi BẮT BUỘC gọi document_read và trả lời bám theo toàn văn, nêu số
  hiệu; văn bản dài thì đọc tiếp bằng part, đừng suy đoán phần chưa đọc. Các câu này
  GỌI TOOL chứ đừng trả lời chay theo gói tri thức.
- Hộp việc phê duyệt của CHÍNH người hỏi: my_approval_tasks trả việc ĐANG CHỜ HỌ ký
  ("tôi có phải duyệt gì không", "việc gì đang chờ tôi") — kèm hạn xử lý, cờ quá hạn và
  ai trình; my_requests_status trả trạng thái phiếu DO HỌ TRÌNH ("phiếu của tôi tới đâu",
  "ai đang giữ văn bản tôi gửi", "vì sao phiếu tôi bị trả lại") — phiếu đang chạy có bước
  hiện tại + tên người đang giữ, phiếu bị trả/từ chối có lý do. Hai chiều NGƯỢC nhau,
  đừng lẫn: chờ tôi KÝ -> my_approval_tasks; tôi ĐÃ GỬI -> my_requests_status.
- Kết quả tool có trường `url` / `inbox_url` là ĐƯỜNG DẪN MÀN HÌNH trong ứng dụng: khi
  nhắc tới phiếu/văn bản đó, gắn luôn link Markdown lên mã hoặc tiêu đề của nó, vd
  [15/QĐ-DEGO](/document/documents/12) — người dùng bấm là mở đúng màn, đừng bắt họ tự
  tìm. KHÔNG tự bịa đường dẫn ngoài giá trị tool trả về.
- HDSD & quy trình: search_docs tra tài liệu hướng dẫn + FAQ. Câu hỏi CÁCH LÀM, quy trình,
  ý nghĩa chức năng, "phải lập phiếu gì / gửi cho ai" -> GỌI search_docs TRƯỚC rồi trả lời
  bám theo tài liệu, KHÔNG tự bịa các bước hay tên phiếu. Không có kết quả thì nói chưa có
  tài liệu, gợi ý hỏi bộ phận phụ trách.
- Giúp lập phiếu: người dùng muốn được soạn hộ / điền hộ chứng từ -> HỎI ĐỦ TRƯỚC rồi mới
  soạn: mặt hàng, SỐ LƯỢNG + đơn vị tính, mục đích, thông số/yêu cầu khác nếu có. Thiếu gì
  thì gom hết câu hỏi vào MỘT lượt (đừng hỏi nhỏ giọt nhiều lượt), người dùng trả lời xong
  mới BẮT BUỘC gọi đúng tool soạn nháp ngay trong lượt đó. KHÔNG tự bịa giá trị người dùng
  chưa nói (số lượng, thông số, ngày cần hàng...); họ nói chưa biết số lượng thì mới để 0.
  Phân loại VTBB/NL là Ô CHỌN theo danh mục hệ thống — chỉ điền khi chắc chắn đúng tên
  trong danh mục, không chắc thì bỏ trống (tool sẽ tự bỏ tên sai và trả về danh sách hợp lệ
  để bạn nêu cho người dùng chọn). search_docs chỉ tra CÁCH DÙNG, không thay được tool soạn
  phiếu. Chọn tool theo
  loại phiếu: xin BÁO GIÁ / khảo sát giá -> draft_survey_request; đề nghị MUA hàng ->
  draft_purchase_request; xin NGHỈ PHÉP / lập đơn nghỉ phép -> draft_leave_request (cần tối
  thiểu ngày nghỉ từ-đến và lý do; ngày tương đối tự quy ra YYYY-MM-DD theo hôm nay). Nút
  "Tạo yêu cầu báo giá" / "Tạo yêu cầu mua hàng" / "Tạo đơn nghỉ phép" trên giao diện
  CHỈ xuất hiện khi tool tương ứng được gọi; chưa gọi mà bảo người dùng bấm nút là nói dối —
  họ không có nút nào để bấm. Tool KHÔNG tạo phiếu — nó chuẩn bị bản đề xuất để giao diện
  hiện nút mở form đã điền sẵn; người dùng tự rà và bấm Tạo. Đừng bao giờ nói phiếu "đã được
  tạo". Người dùng không nói rõ loại phiếu thì hỏi lại một câu (mua luôn hay chỉ xin báo
  giá) trước khi soạn.

Chiến lược gọi công cụ:
- Người hỏi mô tả sản phẩm/NCC bằng lời -> gọi product_search / supplier_search lấy mã TRƯỚC,
  rồi mới gọi công cụ cần mã. Được phép gọi NHIỀU công cụ nối tiếp trong một câu, cứ gọi tiếp
  đến khi đủ dữ liệu để trả lời.
- Câu có mốc thời gian ("năm nay", "quý 1", "tháng trước") -> tự quy ra ngày YYYY-MM-DD dựa
  vào ngày hôm nay ở trên rồi điền date_from/date_to.
- Kết quả rỗng hoặc bị từ chối (denied) -> nói thẳng là không có dữ liệu / không đủ quyền,
  KHÔNG bịa. Nếu câu hỏi nằm NGOÀI các nhóm trên, đừng chỉ xin lỗi: nêu ngắn gọn bạn tra được
  những gì (vài nhóm ở trên) để người hỏi hỏi lại đúng hướng.

Trả lời gọn, nêu con số cụ thể, ghi rõ nguồn là số liệu hệ thống. KHÔNG in tên trường
kỹ thuật của tool (`waiting_on`, `entity_label`, `inbox_url`...) vào câu trả lời — diễn
đạt bằng lời tiếng Việt tự nhiên."""


def _extra_system(tool_on: bool, caller: str | None) -> str | None:
    parts = []
    if tool_on:
        # Ngày hôm nay đặt TRƯỚC guide để model quy đổi "năm nay/quý 1/..." sang date_from/date_to.
        parts.append(f"Hôm nay là {date.today().isoformat()} (định dạng YYYY-MM-DD).")
        parts.append(TOOL_GUIDE)
    if caller:
        parts.append(caller)
    return "\n\n".join(parts) if parts else None


def ask(
    message: str,
    *,
    db=None,
    user=None,
    provider: str | None = None,
    model: str | None = None,
    kind: str = "general",
    system: str | None = None,
    history: list[dict] | None = None,
) -> dict:
    """Hỏi một câu, trả về dict đã chuẩn hóa (dùng cho endpoint /chat).

    Có `db`+`user` (đi từ endpoint) thì mở lớp tool loại A; gọi trực tiếp không kèm ngữ cảnh
    người dùng (vd test provider) thì lùi về đường không tool.
    """
    cfg = ROUTING.get(kind, ROUTING["general"])
    prov = get_provider(provider)

    # Guard chi phí: câu tra cứu / mặc định có thể chạy model RẺ hơn (nếu admin khai
    # AI_LOOKUP_MODEL); câu tư vấn (advice) giữ model mặc định, thông minh hơn. Caller
    # chỉ định model tường minh thì tôn trọng, không đè.
    if model is None and settings.AI_LOOKUP_MODEL and kind in ("lookup", "general"):
        model = settings.AI_LOOKUP_MODEL

    tool_on = bool(cfg["tools"] and db is not None and user is not None and prov.supports_tools)

    # `system` của caller KHÔNG ghi đè định nghĩa/rào an toàn — chỉ chèn THÊM vào cuối.
    full_system = build_system(extra=_extra_system(tool_on, system))

    msgs: list[ChatMessage] = []
    for h in history or []:
        role = h.get("role")
        content = h.get("content", "")
        if role in ("user", "assistant") and content:
            msgs.append(ChatMessage(role=role, content=content))
    msgs.append(ChatMessage(role="user", content=message))

    common = {
        "model": model,
        "system": full_system,
        "max_tokens": cfg["max_tokens"],
        "temperature": cfg["temperature"],
        "thinking": cfg["thinking"],
        "cache_system": True,   # gói tri thức đứng yên -> cache prefix, lượt sau rẻ
    }

    if tool_on:
        result = prov.run_tools(
            msgs,
            tools=tool_layer.tool_defs(),
            execute=lambda name, args: tool_layer.run_tool(db, user, name, args),
            **common,
        )
    else:
        result = prov.ask(msgs, **common)

    return {
        "text": result.text,
        "provider": result.provider,
        "model": result.model,
        "kind": kind,
        "tool_calls": result.tool_calls,
        "usage": {
            "input_tokens": result.input_tokens,
            "output_tokens": result.output_tokens,
            "thinking_tokens": result.thinking_tokens,
            "cache_write_tokens": result.cache_write_tokens,
            "cache_read_tokens": result.cache_read_tokens,
        },
    }
