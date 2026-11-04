// bao-CR-718 — hàm thuần cho nút "Xuất toàn bộ theo bộ lọc (chạy nền)" của Tra cứu thị trường.
//
// Số tệp dự kiến và câu mô tả bộ lọc ở hộp xác nhận phải khớp cách backend chia tệp
// (`backend/app/modules/customs/line_export.py`: `EXPORT_ROWS_PER_FILE`, `describe_filters`) — lệch
// một chút là người dùng đọc "7 tệp" trên hộp mà chuông báo "8 tệp".
import { formatDateTime } from '@/shared/utils/format-date'

import { CUSTOMS_EXPORT_STATUS, type CustomsExportBatch } from '../types/customs'

/** Mỗi tệp tối đa 50.000 dòng — khớp `EXPORT_ROWS_PER_FILE` của backend và trần nút "Xuất ngay". */
export const CUSTOMS_EXPORT_ROWS_PER_FILE = 50_000

/**
 * Số ngày giữ tệp mặc định (`customs_export_keep_days`). Hộp xác nhận chưa hỏi được cấu hình thật
 * trước khi tạo lô, nên ghi theo mặc định; màn chi tiết lô luôn hiện hạn THẬT (`expires_at`).
 */
export const CUSTOMS_EXPORT_KEEP_DAYS = 7

/** Số tệp dự kiến = làm tròn LÊN (tổng dòng / 50.000). 0 dòng (hoặc số hỏng) = 0 tệp. */
export function estimateExportFileCount(totalRows: number): number {
  if (!Number.isFinite(totalRows) || totalRows <= 0) return 0
  return Math.ceil(totalRows / CUSTOMS_EXPORT_ROWS_PER_FILE)
}

/** Nhãn ô lọc — cùng chữ với `FILTER_LABELS` của backend để hộp xác nhận và lô ghi giống nhau. */
const FILTER_LABELS: [key: string, label: string][] = [
  ['q', 'Tên hàng'],
  ['hs_code', 'Mã HS'],
  ['formulation', 'Dạng'],
  ['origin', 'Xuất xứ'],
  ['unit', 'Đơn vị'],
  ['importer_id', 'Doanh nghiệp'],
  ['partner_id', 'Đối tác'],
  ['batch_id', 'Lô nạp'],
  ['currency', 'Nguyên tệ'],
  ['incoterm', 'Điều kiện giao'],
  ['price_min', 'Giá từ'],
  ['price_max', 'Giá đến'],
  ['qty_min', 'Lượng từ'],
  ['qty_max', 'Lượng đến'],
  ['rate_min', 'Tỷ giá từ'],
  ['rate_max', 'Tỷ giá đến'],
  ['date_from', 'Từ ngày'],
  ['date_to', 'Đến ngày'],
  ['product_kind', 'Loại hàng'],
]

/** Khớp `ProductKind` backend (1 Thành phẩm · 2 Nguyên liệu). */
const PRODUCT_KIND_LABELS: Record<string, string> = { '1': 'Thành phẩm', '2': 'Nguyên liệu' }

/**
 * Câu mô tả bộ lọc đang áp cho hộp xác nhận, vd "Tên hàng: abamectin · Mã HS: 3808". Bỏ trống mọi ô
 * thì "Toàn bộ dữ liệu". Doanh nghiệp / đối tác trên URL là DÃY ID — có tên kèm theo (`names`) thì
 * hiện tên cho người đọc hiểu, không thì giữ id.
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
      value = value
        .split(',')
        .map((code) => PRODUCT_KIND_LABELS[code.trim()] ?? code.trim())
        .filter(Boolean)
        .join(', ')
    }
    parts.push(`${label}: ${value}`)
  }
  return parts.join(' · ') || 'Toàn bộ dữ liệu'
}

/** Câu thân hộp xác nhận "Xuất toàn bộ theo bộ lọc" — nhiều dòng (`whitespace-pre-line`). */
export function buildFullExportConfirmMessage(totalRows: number, filterSummary: string): string {
  const files = estimateExportFileCount(totalRows)
  const rows = totalRows.toLocaleString('vi-VN')
  return [
    `Bộ lọc: ${filterSummary}`,
    `Số dòng: ${rows} — dự kiến ${files} tệp Excel (mỗi tệp tối đa ${CUSTOMS_EXPORT_ROWS_PER_FILE.toLocaleString('vi-VN')} dòng).`,
    `Hệ thống xuất chạy nền trong vài phút, xong sẽ báo chuông. Tệp được giữ ${CUSTOMS_EXPORT_KEEP_DAYS} ngày rồi tự xóa.`,
  ].join('\n')
}

/** Phần trăm tiến độ 0..100 theo số dòng đã ghi (mịn hơn đếm tệp); tổng 0 thì 0, không chia cho 0. */
export function exportProgressPercent(batch: Pick<CustomsExportBatch, 'rows_done' | 'total_rows' | 'status'>): number {
  if (batch.status === CUSTOMS_EXPORT_STATUS.done) return 100
  if (!batch.total_rows || batch.total_rows <= 0) return 0
  return Math.min(100, Math.max(0, Math.round((batch.rows_done / batch.total_rows) * 100)))
}

/** Hạn giữ tệp của lô: `null` = giữ mãi (cấu hình số ngày giữ = 0). */
export function formatExportExpiry(expiresAt: string | null): string {
  return expiresAt ? formatDateTime(expiresAt) : 'Giữ mãi'
}
