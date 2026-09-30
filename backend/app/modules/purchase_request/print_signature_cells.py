"""Bộ ô ký cụm «XÉT DUYỆT» trên bản in Phiếu đề xuất mua hàng — bao-CR-531 (đại ca chốt 30/09/2026).

Đây là chỗ DUY NHẤT quyết định phiếu in ra mấy ô ký, ô nào mang tên + chữ ký của ai. Hai giao
diện (`frontend/` và `frontend-v2/`) chỉ vẽ lại danh sách `print_signature_cells` và áp hai chế
độ phía máy khách: «Không chữ ký» (bỏ cả ảnh lẫn tên) và «Mẫu thuế» (để trống hết).

Luật:
  1. Pháp nhân là HỘ KINH DOANH (`Company.company_type = 2`): chỉ hai ô «Chủ hộ» + «Người lập»,
     KHÔNG tên, KHÔNG ảnh — ở mọi chế độ. Bỏ «TP/BP mua hàng» và «TP/BP đề xuất».
  2. Pháp nhân là CÔNG TY: ô «Giám đốc» = người đại diện pháp luật
     (`Company.legal_representative_id`, id NHÂN SỰ). Người đó trùng NHÂN SỰ ở ô «TP/BP đề xuất»
     và/hoặc «TP/BP mua hàng» thì bỏ ô trùng, dời tên + chữ ký người đó sang ô «Giám đốc».
     Không trùng thì «Giám đốc» để trống ký tay như trước.
     So bằng id NHÂN SỰ, không so tên (trùng tên là chuyện thường). Id chưa biết (0) thì KHÔNG gộp.

Ví dụ thật trên prod: ICARE có người đại diện Lê Phước Hữu, cũng là TP/BP đề xuất của
PYC29092604 → phiếu in ba ô: Giám đốc (Lê Phước Hữu + chữ ký) · TP/BP mua hàng · Người lập.
"""
from app.modules.company.constants import CompanyType

ROLE_DIRECTOR = "Giám đốc"
ROLE_PURCHASING_HEAD = "TP/BP mua hàng"
ROLE_PROPOSER = "TP/BP đề xuất"
ROLE_PREPARER = "Người lập"
ROLE_HOUSEHOLD_OWNER = "Chủ hộ"


def _cell(key: str, role: str, name: str = "", signature: str = "") -> dict:
    return {"key": key, "role": role, "name": name or "", "signature": signature or ""}


def build_print_signature_cells(company, signers: dict, requester_name: str,
                                requester_signature: str) -> list[dict]:
    """Danh sách ô ký đã rút gọn theo luật ở đầu tệp, xếp trái → phải như trên giấy.

    `company` = bản ghi `Company` của phiếu (None khi phiếu chưa gắn pháp nhân → coi là công ty,
    không có người đại diện). `signers` = kết quả `_approval_signers` của controller: cần
    `approver_name/_signature`, `proposer_employee_id`, `purchasing_head_name/_signature`,
    `purchasing_head_employee_id`.
    """
    company_type = int(getattr(company, "company_type", 0) or CompanyType.COMPANY)
    if company_type == CompanyType.HOUSEHOLD:
        return [_cell("household_owner", ROLE_HOUSEHOLD_OWNER), _cell("preparer", ROLE_PREPARER)]

    director_id = int(getattr(company, "legal_representative_id", 0) or 0)
    proposer = _cell("proposer", ROLE_PROPOSER, signers.get("approver_name", ""),
                     signers.get("approver_signature", ""))
    purchasing = _cell("purchasing_head", ROLE_PURCHASING_HEAD, signers.get("purchasing_head_name", ""),
                       signers.get("purchasing_head_signature", ""))
    proposer_id = int(signers.get("proposer_employee_id", 0) or 0)
    purchasing_id = int(signers.get("purchasing_head_employee_id", 0) or 0)
    merge_proposer = bool(director_id) and proposer_id == director_id
    merge_purchasing = bool(director_id) and purchasing_id == director_id

    director = _cell("director", ROLE_DIRECTOR)
    #  Cùng một người nên tên như nhau; lấy ô đang có tên (ô đề xuất trước) — ô đề xuất còn
    #  trống khi phiếu chưa duyệt (bao-CR-521) thì «Giám đốc» cũng trống theo, chỉ bớt ô.
    source = proposer if merge_proposer and proposer["name"] else purchasing if merge_purchasing else proposer
    if merge_proposer or merge_purchasing:
        director["name"], director["signature"] = source["name"], source["signature"]

    cells = [director]
    if not merge_purchasing:
        cells.append(purchasing)
    if not merge_proposer:
        cells.append(proposer)
    cells.append(_cell("preparer", ROLE_PREPARER, requester_name, requester_signature))
    return cells
