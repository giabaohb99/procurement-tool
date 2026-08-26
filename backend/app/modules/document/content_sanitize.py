"""Làm sạch NỘI DUNG văn bản trước khi lưu — chống XSS lưu trữ.

`content_html` được vẽ lại bằng `dangerouslySetInnerHTML` trên bản in, nên bất cứ
`onerror` / `<script>` / `javascript:` nào lọt vào cột này sẽ chạy trong phiên
của NGƯỜI MỞ bản in — thường là cấp trên đi duyệt, không phải kẻ soạn. Kẻ tấn
công chỉ cần quyền soạn một văn bản rồi trình lên.

Dùng chung bộ lọc với đường import văn thư (`help_center.import_service`) — nó đã
bỏ mọi handler `on*`, chặn `javascript:`/`vbscript:`/`data:` (trừ `data:image`),
xóa cả `<script>`/`<style>` lẫn nội dung, và không cho `srcdoc`. Không viết bộ
lọc thứ hai: hai bộ lọc XSS là hai chỗ để quên vá một nửa.

Đặt hàm ở đây thay vì gọi thẳng để MỌI đường ghi `content_html` chỉ đi qua một
cửa, và để chỗ gọi không phải biết bộ lọc nằm ở phân hệ khác.
"""
from app.modules.help_center.import_service import sanitize_html


def sanitize_document_html(html: str | None) -> str:
    """`content_html` đã lọc. `None`/rỗng trả chuỗi rỗng.

    Chỉ gọi khi content_html được GỬI LÊN (khác `None`) — kéo thước lề gửi thiếu
    trường này thì đừng đụng vào nội dung đang có (xem `save_content`).
    """
    if not html:
        return ""
    return sanitize_html(html)
