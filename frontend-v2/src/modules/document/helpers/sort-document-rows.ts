import { sortRowsBy } from '@/shared/utils/compare-sort-values'
import type { DocumentRecord } from '../types/document-record'

/**
 * Sắp xếp văn bản trong khung nội dung thư mục (đặc tả §B) — CHẠY PHÍA CLIENT
 * trên đúng trang đang nạp (không gọi lại API): `/api/documents` không nhận
 * tham số `sort_by`/`sort_dir` cho khung này, và trang chỉ vài chục dòng nên
 * sắp tay không đáng lo hiệu năng.
 *
 * ⚠️ `DocumentRecord` KHÔNG có cột "ngày sửa cuối" (`updated_at`) — backend
 * chỉ trả `created_at`. Nhãn vì vậy là "Ngày tạo", không phải "Ngày sửa" như
 * chữ trong đặc tả gốc; bịa ra một cột không có thật còn tệ hơn đặt nhãn khác
 * chữ đặc tả một chút.
 */
export const DOCUMENT_SORT_FIELD = { name: 'name', createdAt: 'createdAt', type: 'type' } as const

export type DocumentSortField = (typeof DOCUMENT_SORT_FIELD)[keyof typeof DOCUMENT_SORT_FIELD]

export const DOCUMENT_SORT_FIELD_LABELS: Record<DocumentSortField, string> = {
  [DOCUMENT_SORT_FIELD.name]: 'Tên',
  [DOCUMENT_SORT_FIELD.createdAt]: 'Ngày tạo',
  [DOCUMENT_SORT_FIELD.type]: 'Loại',
}

export type SortDirection = 'asc' | 'desc'

function documentSortValue(row: DocumentRecord, field: DocumentSortField): string {
  switch (field) {
    case DOCUMENT_SORT_FIELD.type:
      return row.doc_type_name
    case DOCUMENT_SORT_FIELD.createdAt:
      return row.created_at
    case DOCUMENT_SORT_FIELD.name:
    default:
      return row.title
  }
}

/**
 * Hàm THUẦN — không sửa mảng đầu vào. So bằng bộ so chung (`shared/utils/compare-sort-values.ts`): ô trống
 * (vd văn bản chưa gán loại) xuống cuối ở cả hai chiều, không phân biệt hoa thường, hiểu số trong chữ.
 * Bằng nhau thì giữ thứ tự gốc.
 */
export function sortDocumentRows(
  rows: readonly DocumentRecord[],
  field: DocumentSortField,
  dir: SortDirection,
): DocumentRecord[] {
  return sortRowsBy(rows, (row) => documentSortValue(row, field), dir)
}
