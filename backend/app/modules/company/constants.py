"""BỘ MÃ SỐ CỦA DANH MỤC CÔNG TY — theo R2/QĐ-11 (bao-CR-531, 30/09/2026).

`tab_company.company_type` lưu `SMALLINT` + `IntEnum`; tiếng Việt chỉ sống trong
`COMPANY_TYPE_LABELS` và ở tầng hiển thị. Bản TypeScript gõ tay ở
`frontend-v2/src/modules/hr/types/company.ts` (`gen_status_ts.py` chỉ sinh bộ mã CHUỖI).

Bộ mã này KHÔNG có `0`: mọi pháp nhân đều biết mình là công ty hay hộ kinh doanh
ngay lúc tạo, mặc định là công ty. Hệ quả chính của «Hộ kinh doanh» nằm ở bản in
Phiếu đề xuất mua hàng — xem `purchase_request/print_signature_cells.py`.
"""
from enum import IntEnum


class CompanyType(IntEnum):
    """Loại hình pháp nhân."""

    COMPANY = 1      # Công ty (doanh nghiệp) — ô ký «Giám đốc» = người đại diện pháp luật
    HOUSEHOLD = 2    # Hộ kinh doanh — bản in chỉ còn «Chủ hộ» + «Người lập», để trống ký tay


COMPANY_TYPE_LABELS = {
    CompanyType.COMPANY: "Công ty",
    CompanyType.HOUSEHOLD: "Hộ kinh doanh",
}

COMPANY_TYPE_VALUES = tuple(int(t) for t in CompanyType)
