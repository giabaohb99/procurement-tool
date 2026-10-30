"""ai-CR-191 — sổ tham chiếu của LUỒNG DUYỆT (`approval_flow`).

Luồng có phiếu duyệt trỏ tới (kể cả phiếu ĐÃ XONG — lịch sử phê duyệt còn đọc tên luồng / phiên bản) hay
đang là luồng mặc định của một loại văn bản thì KHÔNG xóa, chỉ ngưng dùng (bỏ "Đang dùng"). Chốt cũ
`_block_while_running` (chỉ đếm phiếu đang chạy) vẫn giữ — nó báo câu riêng rõ hơn cho ca đó.

Ủy quyền (`delegation_controller`) không cần: nút xóa ở đó đã là TẮT (`is_active = False`) từ trước.
`flow_controller.delete_flow` gọi `reference_guard.ensure_deletable(db, "approval_flow", flow)`.
"""
from app.core.reference_guard import Reference, register
from app.modules.doc_catalog.model import DocType

from .instance_model import ApprovalInstance

register("approval_flow", "Luồng duyệt", [
    Reference(ApprovalInstance, "flow_id", "phiếu duyệt (kể cả đã xong)"),
    Reference(DocType, "default_flow_id", "loại văn bản lấy làm luồng mặc định"),
])
