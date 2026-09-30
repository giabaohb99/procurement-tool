"""Bộ ô ký cụm «XÉT DUYỆT» trên bản in Phiếu đề xuất mua hàng — bao-CR-531, đổi luật ở bao-CR-536/539.

Đây là chỗ DUY NHẤT quyết định phiếu in ra mấy ô ký, ô nào mang tên + chữ ký của ai. Hai giao
diện (`frontend/` và `frontend-v2/`) chỉ vẽ lại danh sách `print_signature_cells` và áp hai chế
độ phía máy khách: «Không chữ ký» (bỏ cả ảnh lẫn tên — đó là nút người dùng tự bấm để ẩn) và
«Mẫu thuế» (để trống hết).

Luật bao-CR-536 (đại ca chốt 30/09/2026, thay luật «bỏ ô trùng» của bao-CR-531):
  1. CÔNG TY: LUÔN đủ 4 ô «Giám đốc · TP/BP mua hàng · TP/BP đề xuất · Người lập», không bỏ ô
     nào. Người đại diện pháp luật (`Company.legal_representative_id`, id NHÂN SỰ) trùng người ở
     «TP/BP đề xuất» và/hoặc «TP/BP mua hàng» thì tên + chữ ký người đó in ở ô «Giám đốc», còn ô
     trùng GIỮ NGUYÊN nhưng để TRỐNG (không tên, không chữ ký). Không trùng: «Giám đốc» trống.
  2. HỘ KINH DOANH (`Company.company_type = 2`): 4 ô y như công ty, CHỈ KHÁC NHÃN ô đầu —
     «Chủ hộ · TP/BP mua hàng · TP/BP đề xuất · Người lập» (bao-CR-539; đại ca: «còn thiếu phần
     TP bên thu mua rồi bạn, tới 4 chữ ký lận á» — bản 536 bỏ ô mua hàng là sai). IN TÊN + chữ ký.
     «Chủ hộ» = người đại diện của hộ, gộp ĐÚNG luật «Giám đốc» (trùng đề xuất và/hoặc mua hàng
     thì in ở «Chủ hộ», ô trùng giữ nhưng trống).
  So bằng id NHÂN SỰ, không so tên (trùng tên là chuyện thường). Id chưa biết (0) thì KHÔNG gộp.

Ví dụ thật trên prod: ICARE có người đại diện Lê Phước Hữu, cũng là TP/BP đề xuất của
PYC29092603 → phiếu in bốn ô: Giám đốc (Lê Phước Hữu + chữ ký) · TP/BP mua hàng ·
TP/BP đề xuất (trống) · Người lập.
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
    """Danh sách ô ký theo luật ở đầu tệp, xếp trái → phải như trên giấy.

    `company` = bản ghi `Company` của phiếu (None khi phiếu chưa gắn pháp nhân → coi là công ty,
    không có người đại diện). `signers` = kết quả `_approval_signers` của controller: cần
    `approver_name/_signature`, `proposer_employee_id`, `purchasing_head_name/_signature`,
    `purchasing_head_employee_id`.
    """
    #  Hộ kinh doanh chỉ khác NHÃN ô đầu (bao-CR-539) — bộ ô và luật gộp y như công ty.
    household = int(getattr(company, "company_type", 0) or CompanyType.COMPANY) == CompanyType.HOUSEHOLD
    representative_id = int(getattr(company, "legal_representative_id", 0) or 0)

    proposer = _cell("proposer", ROLE_PROPOSER, signers.get("approver_name", ""),
                     signers.get("approver_signature", ""))
    purchasing = _cell("purchasing_head", ROLE_PURCHASING_HEAD, signers.get("purchasing_head_name", ""),
                       signers.get("purchasing_head_signature", ""))
    proposer_id = int(signers.get("proposer_employee_id", 0) or 0)
    purchasing_id = int(signers.get("purchasing_head_employee_id", 0) or 0)
    merge_proposer = bool(representative_id) and proposer_id == representative_id
    merge_purchasing = bool(representative_id) and purchasing_id == representative_id

    head = _cell("household_owner", ROLE_HOUSEHOLD_OWNER) if household else _cell("director", ROLE_DIRECTOR)
    #  Cùng một người nên tên như nhau; lấy ô đang có tên (ô đề xuất trước) — ô đề xuất còn
    #  trống khi phiếu chưa duyệt (bao-CR-521) thì lấy ô mua hàng nếu cũng trùng.
    if merge_proposer and proposer["name"]:
        source = proposer
    elif merge_purchasing:
        source = purchasing
    else:
        source = proposer if merge_proposer else None
    if source is not None:
        head["name"], head["signature"] = source["name"], source["signature"]
    #  Ô trùng GIỮ chỗ nhưng để trống — người đó đã ký ở ô đầu, ký lại ở ô sau là ký hai lần.
    if merge_proposer:
        proposer["name"], proposer["signature"] = "", ""
    if merge_purchasing:
        purchasing["name"], purchasing["signature"] = "", ""

    preparer = _cell("preparer", ROLE_PREPARER, requester_name, requester_signature)
    return [head, purchasing, proposer, preparer]
