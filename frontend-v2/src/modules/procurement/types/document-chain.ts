/**
 * Chuỗi chứng từ của MỘT đơn mua hàng — gom tệp của cả bốn nấc chứng từ.
 *
 * Backend: `GET /api/attachments/chain?entity=purchase_order&entity_id=<id>`
 * (`backend/app/modules/attachment/controller.py`, hàm `_resolve_chain`). Nó lần
 * theo MÃ chứ không theo khóa ngoại: đơn → `pr_code` → `survey_code` → `sr_code`,
 * nhánh nào mã rỗng thì bỏ, nên một đơn nhập tay có thể chỉ có đúng nấc PO.
 */
export interface ChainAttachment {
  /** Id của FileLink — chính là id dùng cho `GET /api/attachments/{id}/download`. */
  link_id: number
  /** Nấc chứng từ: `PO` · `PYC` · `PKS` · `YCKS`. */
  source: string
  /** Mã chứng từ của nấc đó, ví dụ `PO25080001`. */
  source_code: string
  entity: string
  entity_id: number
  doc_type: string
  doc_type_label: string
  filename: string
  /**
   * Đường đọc thẳng kho lưu trữ, KHÔNG qua kiểm quyền — backend để RỖNG với
   * entity riêng tư. Chỗ nào nhận chuỗi rỗng thì không xem trước được, phải tải
   * qua `GET /api/attachments/{link_id}/download`.
   */
  url: string
  content_type: string
  size: number
  sha256: string
}

/** Thứ tự hiện các nấc: đi ngược dòng nghiệp vụ, đơn hàng trước rồi mới tới gốc. */
export const CHAIN_SOURCE_ORDER = ['PO', 'PYC', 'PKS', 'YCKS'] as const

export const CHAIN_SOURCE_LABELS: Record<string, string> = {
  PO: 'Đơn mua hàng',
  PYC: 'Yêu cầu mua hàng',
  PKS: 'Phiếu khảo sát',
  YCKS: 'Yêu cầu báo giá',
}
