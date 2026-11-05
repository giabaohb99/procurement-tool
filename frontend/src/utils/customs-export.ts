// bao-CR-728 — hàm thuần cho lô XUẤT TOÀN BỘ chạy nền của Tra cứu thị trường (bản cũ), bê từ
// `frontend-v2/src/modules/procurement/utils/customs-export.ts` (bao-CR-718).
//
// Số tệp dự kiến và câu mô tả bộ lọc ở hộp xác nhận phải khớp cách backend chia tệp
// (`backend/app/modules/customs/line_export.py`: `EXPORT_ROWS_PER_FILE`, `describe_filters`).

/** Mỗi tệp tối đa 50.000 dòng — khớp `EXPORT_ROWS_PER_FILE` của backend và trần nút "Xuất ngay". */
export const CUSTOMS_EXPORT_ROWS_PER_FILE = 50_000

/** Số ngày giữ tệp mặc định (`customs_export_keep_days`); màn chi tiết lô luôn hiện hạn THẬT (`expires_at`). */
export const CUSTOMS_EXPORT_KEEP_DAYS = 7

/** Trạng thái lô xuất — khớp `CustomsExportStatus` backend (SMALLINT). Nhãn lấy `status_label` của API. */
export const CUSTOMS_EXPORT_STATUS = {
  queued: 1,
  running: 2,
  done: 3,
  failed: 4,
  cancelled: 5,
  expired: 6,
} as const

/** Đường màn lô xuất của bản cũ. Chuông backend trỏ `/procurement/customs-prices/exports/<id>` (đường v2) —
 *  App.tsx có route cùng đường đó chuyển thẳng sang đây. */
export const CUSTOMS_EXPORTS_PATH = '/customs-prices/exports'
export const customsExportPath = (id: number | string) => `${CUSTOMS_EXPORTS_PATH}/${id}`

export type CustomsExportFile = { part: number; filename: string; rows: number; size: number; available: boolean }
export type CustomsExportBatch = {
  id: number
  status: number
  status_label: string
  filter_summary: string
  total_rows: number
  rows_per_file: number
  file_count: number
  files_done: number
  rows_done: number
  error: string
  files: CustomsExportFile[]
  created_at: string
  started_at: string | null
  finished_at: string | null
  expires_at: string | null
  active: boolean
}

/** Số tệp dự kiến = làm tròn LÊN (tổng dòng / 50.000). 0 dòng (hoặc số hỏng) = 0 tệp. */
export function estimateExportFileCount(totalRows: number): number {
  if (!Number.isFinite(totalRows) || totalRows <= 0) return 0
  return Math.ceil(totalRows / CUSTOMS_EXPORT_ROWS_PER_FILE)
}

/** Nhãn ô lọc — cùng chữ với `FILTER_LABELS` của backend. */
const FILTER_LABELS: [key: string, label: string][] = [
  ['q', 'Tên hàng'], ['hs_code', 'Mã HS'], ['formulation', 'Dạng'], ['origin', 'Xuất xứ'], ['unit', 'Đơn vị'],
  ['importer_id', 'Doanh nghiệp'], ['partner_id', 'Đối tác'], ['batch_id', 'Lô nạp'], ['currency', 'Nguyên tệ'],
  ['incoterm', 'Điều kiện giao'], ['price_min', 'Giá từ'], ['price_max', 'Giá đến'], ['qty_min', 'Lượng từ'],
  ['qty_max', 'Lượng đến'], ['rate_min', 'Tỷ giá từ'], ['rate_max', 'Tỷ giá đến'], ['date_from', 'Từ ngày'],
  ['date_to', 'Đến ngày'], ['product_kind', 'Loại hàng'],
]

/** Khớp `ProductKind` backend (1 Thành phẩm · 2 Nguyên liệu). */
const PRODUCT_KIND_LABELS: Record<string, string> = { '1': 'Thành phẩm', '2': 'Nguyên liệu' }

/**
 * Câu mô tả bộ lọc đang áp cho hộp xác nhận, vd "Tên hàng: abamectin · Mã HS: 3808". Bỏ trống mọi ô thì
 * "Toàn bộ dữ liệu". Doanh nghiệp / đối tác là DÃY ID — có tên kèm theo thì hiện tên cho dễ đọc.
 */
export function describeCustomsFilters(
  params: Record<string, string>,
  names: { importer?: string; partner?: string } = {},
): string {
  const parts: string[] = []
  for (const [key, label] of FILTER_LABELS) {
    let value = (params[key] ?? '').trim()
    if (!value) continue
    if (key === 'importer_id' && names.importer?.trim()) value = names.importer.trim()
    if (key === 'partner_id' && names.partner?.trim()) value = names.partner.trim()
    if (key === 'product_kind') {
      value = value.split(',').map((c) => PRODUCT_KIND_LABELS[c.trim()] ?? c.trim()).filter(Boolean).join(', ')
    }
    parts.push(`${label}: ${value}`)
  }
  return parts.join(' · ') || 'Toàn bộ dữ liệu'
}

/** Câu thân hộp xác nhận "Xuất toàn bộ theo bộ lọc". */
export function buildFullExportConfirmMessage(totalRows: number, filterSummary: string): string {
  const files = estimateExportFileCount(totalRows)
  return [
    `Bộ lọc: ${filterSummary}.`,
    `Số dòng: ${totalRows.toLocaleString('vi-VN')}, dự kiến ${files} tệp Excel (mỗi tệp tối đa `
      + `${CUSTOMS_EXPORT_ROWS_PER_FILE.toLocaleString('vi-VN')} dòng).`,
    `Hệ thống xuất chạy nền trong vài phút, xong sẽ báo chuông. Tệp được giữ ${CUSTOMS_EXPORT_KEEP_DAYS} ngày rồi tự xóa.`,
  ].join(' ')
}

/** Phần trăm tiến độ 0..100 theo số dòng đã ghi; tổng 0 thì 0, không chia cho 0. */
export function exportProgressPercent(b: Pick<CustomsExportBatch, 'rows_done' | 'total_rows' | 'status'>): number {
  if (b.status === CUSTOMS_EXPORT_STATUS.done) return 100
  if (!b.total_rows || b.total_rows <= 0) return 0
  return Math.min(100, Math.max(0, Math.round((b.rows_done / b.total_rows) * 100)))
}

/** Lớp `.badge` theo trạng thái lô (bảng màu chung của bản cũ). */
export function exportStatusBadgeClass(status: number): string {
  switch (status) {
    case CUSTOMS_EXPORT_STATUS.queued: return 'badge warn'
    case CUSTOMS_EXPORT_STATUS.running: return 'badge info'
    case CUSTOMS_EXPORT_STATUS.done: return 'badge ok'
    case CUSTOMS_EXPORT_STATUS.failed: return 'badge err'
    default: return 'badge gray'
  }
}

/** Dung lượng tệp: "12,84 MB". */
export function formatFileSize(n: number): string {
  if (!n) return '—'
  if (n < 1024) return `${n} B`
  if (n < 1024 * 1024) return `${(n / 1024).toLocaleString('vi-VN', { maximumFractionDigits: 1 })} KB`
  return `${(n / 1024 / 1024).toLocaleString('vi-VN', { maximumFractionDigits: 2 })} MB`
}
