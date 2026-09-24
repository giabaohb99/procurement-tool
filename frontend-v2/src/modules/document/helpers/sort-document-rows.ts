import type { DocumentRecord } from '../types/document-record'

/**
 * Sắp xếp văn bản trong khung nội dung thư mục (đặc tả §B) — CHẠY PHÍA CLIENT
 * trên đúng trang đang nạp (không gọi lại API): `/api/documents` không nhận
 * tham số `sort_by`/`sort_dir` cho khung này, và trang chỉ vài chục dòng nên
 * sắp tay không đáng lo hiệu năng.
 *
 * ⚠️ `DocumentRecord` KHÔNG có cột "ngày sửa cuối" (`updated_at`) — backend
 * chỉ trả `created_at`. Nhãn vì vậy là «Ngày tạo», không phải «Ngày sửa» như
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

/** Hàm THUẦN — không sửa mảng đầu vào (`[...rows]` trước khi `sort`). */
export function sortDocumentRows(
  rows: readonly DocumentRecord[],
  field: DocumentSortField,
  dir: SortDirection,
): DocumentRecord[] {
  const factor = dir === 'asc' ? 1 : -1
  return [...rows].sort((a, b) => {
    switch (field) {
      case DOCUMENT_SORT_FIELD.type:
        return factor * a.doc_type_name.localeCompare(b.doc_type_name, 'vi')
      case DOCUMENT_SORT_FIELD.createdAt:
        return factor * a.created_at.localeCompare(b.created_at)
      case DOCUMENT_SORT_FIELD.name:
      default:
        return factor * a.title.localeCompare(b.title, 'vi')
    }
  })
}
